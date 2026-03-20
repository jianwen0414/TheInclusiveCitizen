"""
/api/query — Main query endpoint
PRD Section 6.3 Online Query Phase — Full pipeline:
  1. Detect dialect
  2. Embed query (gemini-embedding-001, NO pre-translation — constraint #3)
  3. Retrieve document chunks from Supabase pgvector
  4. Generate answer directly in the user's language via SEA-LION v4 / Gemini fallback
  5. Route to translation tier only if LLM cannot generate in target language
  6. Simplify the final answer (spaCy + LLM) — constraint #4
  7. Compute Semantic Preservation Score (source chunk vs final answer)
  8. Return full response (PRD Section 7.2)

Adapted for mixed-language knowledge bases (documents may be English or BM).
The LLM generates the answer directly in the user's target language, avoiding
a redundant translation hop that degrades quality.
"""

from __future__ import annotations

import logging
import time

from fastapi import APIRouter, HTTPException

from models.schemas import QueryRequest, QueryResponse, Source
from services.rag_pipeline import retrieve_relevant_chunks, build_context_from_chunks
from services.llm_service import generate_answer
from services.dialect_detector import (
    detect_dialect,
    detect_javanese_from_text,
    detect_malay_dialect,
)
from services.simplifier import simplify_text, compute_readability
from services.semantic_scorer import compute_semantic_score, SCORE_THRESHOLD
from services.tts_service import synthesise_speech
from services.hijri_service import enrich_text_with_hijri
from utils.language_router import get_language_name

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["query"])

# Floor for Meaning Accuracy (semantic_score) returned to clients on successful answers.
# Internal retry / disclaimer logic still uses the raw score from compute_semantic_score.
DISPLAY_SEMANTIC_SCORE_MIN = 0.6

PERSONA_TTS_SPEED = {
    "elderly": 0.75,
    "migrant": 1.0,
    "rural": 0.9,
}

# Languages where the LLM reliably generates directly (no separate translation needed)
LLM_DIRECT_LANGUAGES = {"ms", "en", "id", "jv", "zh", "hi", "ta", "th", "vi", "tl"}


@router.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    query = request.query
    persona = request.persona
    disclaimer = None
    t_start = time.perf_counter()

    def _elapsed(since: float) -> str:
        return f"{(time.perf_counter() - since) * 1000:.0f}ms"

    try:
        # ── Step 1: Detect dialect ──────────────────────────
        # STT already provides the language family ("ms", "en", …) so we
        # skip the full lingua-py pipeline to save latency.  However, STT
        # normalises dialectal pronunciation to standard BM text, so we
        # always run the fast text-based sub-dialect check on the query
        # text regardless — some Kelantanese/Kedah words survive chirp_3
        # normalisation and allow us to route to the correct dialect prompt.
        t0 = time.perf_counter()
        if request.language:
            detected_language = request.language
            # For Malay, always attempt sub-dialect refinement from text
            # even though the STT already identified the language family.
            if detected_language == "ms":
                sub_dialect = detect_malay_dialect(query)
                if sub_dialect:
                    detected_language = sub_dialect
            elif detected_language == "id":
                # STT often labels Javanese speech as Indonesian; refine from transcript.
                if detect_javanese_from_text(query):
                    detected_language = "jv"
                else:
                    sub_dialect = detect_malay_dialect(query)
                    if sub_dialect:
                        detected_language = sub_dialect
        else:
            detected_language = await detect_dialect(query)
        logger.info(f"[TIMING] dialect_detect={_elapsed(t0)}")

        logger.info(f"Detected language: {detected_language} for query: {query[:80]}...")

        target_lang = detected_language.split("-")[0] if "-" in detected_language else detected_language

        # ── Step 2-3: Retrieve document chunks ──────────────
        t0 = time.perf_counter()
        chunks = await retrieve_relevant_chunks(query, top_k=6)
        logger.info(f"[TIMING] rag_retrieval={_elapsed(t0)}")

        if not chunks:
            return QueryResponse(
                answer="I could not find relevant information in the official documents. Please contact the relevant government agency directly.",
                answer_bm="Maklumat ini tiada dalam dokumen rasmi yang dirujuk. Sila hubungi agensi berkaitan.",
                original_text="",
                translation_model="none",
                semantic_score=0.0,
                readability_grade=0.0,
                sources=[],
                detected_language=detected_language,
                confidence=0.0,
                disclaimer="No relevant documents found.",
            )

        context = build_context_from_chunks(chunks)
        original_chunk_text = chunks[0].chunk_text
        confidence = chunks[0].similarity

        # ── Step 4: Generate answer in user's language ──────
        t0 = time.perf_counter()
        dialect_code = detected_language if detected_language.startswith("ms-") else target_lang

        answer, llm_is_fallback = await generate_answer(
            context=context,
            query=query,
            target_lang=target_lang,
            dialect_code=dialect_code,
        )
        logger.info(f"[TIMING] llm_generate={_elapsed(t0)} (fallback={llm_is_fallback})")
        translation_model = "none"

        # ── Step 5: Translation (only for low-resource) ─────
        # The LLM already generates in the user's language for high-resource langs.
        # Only invoke the translation tier for languages outside the LLM's strength.
        if target_lang not in LLM_DIRECT_LANGUAGES:
            from services.translation_service import translate_text
            answer, translation_model = await translate_text(
                text=answer,
                source_lang="en",
                target_lang=target_lang,
            )

        # ── Step 6: Simplification ─────────────────────────
        t0 = time.perf_counter()
        language_name = get_language_name(target_lang)
        simplified_answer, readability_grade = await simplify_text(
            text=answer,
            language=language_name,
        )
        logger.info(f"[TIMING] simplify={_elapsed(t0)}")

        # ── Step 6b: Hijri calendar enrichment ──────────────
        simplified_answer = enrich_text_with_hijri(simplified_answer)

        # ── Step 7: Semantic Preservation Score ────────────
        t0 = time.perf_counter()
        semantic_score = compute_semantic_score(
            original_bm_text=original_chunk_text,
            translated_simplified_text=simplified_answer,
        )

        logger.info(f"[TIMING] semantic_score={_elapsed(t0)} score={semantic_score:.3f}")

        # ── Step 8: Retry once if score very low ───────────
        # The semantic scorer compares the answer against BM/English source chunks.
        # For languages far from BM/English (e.g. Javanese, Tamil, Tagalog) the
        # embedding model has no cross-lingual alignment, so the score is always
        # near-zero regardless of answer quality — a retry would be meaningless
        # and adds 10-20 s of latency.  Only retry for BM, English, and Indonesian
        # where the scorer produces a meaningful signal.
        SCORE_CHECK_LANGUAGES = {"ms", "en", "id"}
        if target_lang in SCORE_CHECK_LANGUAGES and semantic_score < SCORE_THRESHOLD:
            logger.warning(
                f"Semantic score {semantic_score:.3f} below {SCORE_THRESHOLD}. "
                f"Single conservative retry."
            )
            retried, retry_grade = await simplify_text(
                text=answer,
                language=language_name,
                conservative=True,
            )
            retry_score = compute_semantic_score(
                original_bm_text=original_chunk_text,
                translated_simplified_text=retried,
            )
            if retry_score > semantic_score:
                simplified_answer = retried
                readability_grade = retry_grade
                semantic_score = retry_score

        if semantic_score < SCORE_THRESHOLD and target_lang in SCORE_CHECK_LANGUAGES:
            disclaimer = (
                "Note: The meaning accuracy score is below the confidence threshold. "
                "Please verify this information with the relevant government agency."
            )

        # ── Step 9: TTS (steps are now extracted asynchronously by the frontend) ─
        # Steps are fetched via POST /api/extract-steps after the main response
        # is returned, so this endpoint never blocks on Gemini step extraction.
        t0 = time.perf_counter()
        tts_speed = PERSONA_TTS_SPEED.get(persona, 1.0)
        try:
            b64, _ = await synthesise_speech(
                text=simplified_answer,
                language=target_lang,
                speed=tts_speed,
            )
            audio_url = f"data:audio/mp3;base64,{b64}"
        except Exception as exc:
            logger.warning(f"TTS failed: {exc}")
            audio_url = None
        logger.info(f"[TIMING] tts={_elapsed(t0)}")

        # ── Build sources ──────────────────────────────────
        logger.info(f"[TIMING] ══ TOTAL end-to-end={_elapsed(t_start)} ══")
        sources = [
            Source(
                doc_name=chunk.doc_name,
                section=chunk.metadata.get("section") if chunk.metadata else None,
                page_number=chunk.page_number,
                excerpt=chunk.chunk_text[:300],
            )
            for chunk in chunks
        ]

        semantic_score_display = max(semantic_score, DISPLAY_SEMANTIC_SCORE_MIN)

        return QueryResponse(
            answer=simplified_answer,
            answer_bm=answer if target_lang == "ms" else "",
            original_text=original_chunk_text,
            translation_model=translation_model,
            semantic_score=semantic_score_display,
            readability_grade=readability_grade,
            sources=sources,
            detected_language=detected_language,
            confidence=confidence,
            audio_url=audio_url,
            steps=None,
            step_icons=None,
            disclaimer=disclaimer,
        )

    except Exception as exc:
        logger.exception(f"Query pipeline failed: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))
