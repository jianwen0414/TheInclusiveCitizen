"""
/api/query — Main query endpoint
PRD Section 6.3 Online Query Phase — Full pipeline:
  1. Detect dialect
  2. Embed query (gemini-embedding-001, NO pre-translation — constraint #3)
  3. Retrieve top-3 BM chunks from Supabase pgvector
  4. Generate BM answer via SEA-LION v4 / Gemini 3 Flash fallback
  5. Route to translation tier (Google TLLM / NLLB-200)
  6. Simplify translated text (spaCy + LLM) — constraint #4
  7. Compute cross-lingual Semantic Preservation Score — constraint #5
  8. Retry if score < 0.90 (max 2 retries)
  9. Return full response (PRD Section 7.2)
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from models.schemas import QueryRequest, QueryResponse, Source
from services.rag_pipeline import retrieve_relevant_chunks, build_context_from_chunks
from services.llm_service import generate_bm_answer, extract_steps
from services.translation_service import translate_text
from services.dialect_detector import detect_dialect
from services.simplifier import simplify_with_retry, compute_readability
from services.semantic_scorer import compute_semantic_score, passes_threshold, SCORE_THRESHOLD
from services.tts_service import synthesise_speech
from services.hijri_service import enrich_text_with_hijri
from utils.fallback_handler import fallback_state
from utils.language_router import get_language_name

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["query"])

PERSONA_TTS_SPEED = {
    "elderly": 0.75,  # PRD F07: 0.75x for elderly persona
    "migrant": 1.0,
    "rural": 0.9,
}


@router.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """
    Full RAG pipeline as defined in PRD Section 6.3.
    """
    query = request.query
    persona = request.persona
    disclaimer = None

    try:
        # ── Step 1: Detect dialect ──────────────────────────
        if request.language:
            detected_language = request.language
        else:
            detected_language = await detect_dialect(query)

        logger.info(f"Detected language: {detected_language} for query: {query[:80]}...")

        # Determine target language for translation (base ISO code)
        target_lang = detected_language.split("-")[0] if "-" in detected_language else detected_language

        # ── Step 2-3: Retrieve BM document chunks ──────────
        # PRD constraint #3: query embedded directly, no pre-translation
        chunks = await retrieve_relevant_chunks(query, top_k=3)

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
        original_bm_text = chunks[0].chunk_text
        confidence = chunks[0].similarity

        # ── Step 4: Generate BM answer ─────────────────────
        dialect_code = detected_language if detected_language.startswith("ms-") else "ms"
        answer_bm, llm_is_fallback = await generate_bm_answer(
            context=context,
            query=query,
            dialect_code=dialect_code,
        )

        # ── Step 5: Translation ────────────────────────────
        # PRD F03b: Translation occurs on BM answer BEFORE simplification
        if target_lang == "ms":
            translated_answer = answer_bm
            translation_model = "none"
        else:
            translated_answer, translation_model = await translate_text(
                text=answer_bm,
                source_lang="ms",
                target_lang=target_lang,
            )

        # ── Step 6: Simplification ─────────────────────────
        # PRD constraint #4: Operates on post-translation text
        language_name = get_language_name(target_lang)
        simplified_answer, readability_grade = await simplify_with_retry(
            text=translated_answer,
            language=language_name,
        )

        # ── Step 6b: Hijri calendar enrichment (Phase 16) ──
        # PRD F12: Append Hijri dates alongside Gregorian deadlines
        simplified_answer = enrich_text_with_hijri(simplified_answer)

        # ── Step 7: Semantic Preservation Score ────────────
        # PRD constraint #5: Cross-lingual BM original vs translated+simplified
        semantic_score = compute_semantic_score(
            original_bm_text=original_bm_text,
            translated_simplified_text=simplified_answer,
        )

        # ── Step 8: Retry if score < 0.90 ─────────────────
        if not passes_threshold(semantic_score):
            logger.warning(
                f"Semantic score {semantic_score:.3f} below {SCORE_THRESHOLD}. "
                f"Re-translating with conservative approach."
            )
            # Re-translate and re-simplify with conservative prompt
            if target_lang != "ms":
                translated_answer, translation_model = await translate_text(
                    text=answer_bm,
                    source_lang="ms",
                    target_lang=target_lang,
                )

            from services.simplifier import simplify_text

            for retry in range(2):
                simplified_answer, readability_grade = await simplify_text(
                    text=translated_answer,
                    language=language_name,
                    conservative=True,
                )
                semantic_score = compute_semantic_score(
                    original_bm_text=original_bm_text,
                    translated_simplified_text=simplified_answer,
                )
                if passes_threshold(semantic_score):
                    break
                logger.warning(f"Retry {retry + 1}: score still {semantic_score:.3f}")

            if not passes_threshold(semantic_score):
                disclaimer = (
                    "Note: The meaning accuracy score is below the confidence threshold. "
                    "Please verify this information with the relevant government agency."
                )

        # ── Step 9: Extract steps (if procedural) ─────────
        steps, step_icons = await extract_steps(simplified_answer)

        # ── Step 10: TTS ───────────────────────────────────
        tts_speed = PERSONA_TTS_SPEED.get(persona, 1.0)
        try:
            audio_b64, _ = await synthesise_speech(
                text=simplified_answer,
                language=target_lang,
                speed=tts_speed,
            )
            audio_url = f"data:audio/mp3;base64,{audio_b64}"
        except Exception as exc:
            logger.warning(f"TTS failed: {exc}")
            audio_url = None

        # ── Build sources ──────────────────────────────────
        sources = [
            Source(
                doc_name=chunk.doc_name,
                section=chunk.metadata.get("section") if chunk.metadata else None,
                page_number=chunk.page_number,
                excerpt=chunk.chunk_text[:300],
            )
            for chunk in chunks
        ]

        return QueryResponse(
            answer=simplified_answer,
            answer_bm=answer_bm,
            original_text=original_bm_text,
            translation_model=translation_model,
            semantic_score=semantic_score,
            readability_grade=readability_grade,
            sources=sources,
            detected_language=detected_language,
            confidence=confidence,
            audio_url=audio_url,
            steps=steps if steps else None,
            step_icons=step_icons if step_icons else None,
            disclaimer=disclaimer,
        )

    except Exception as exc:
        logger.exception(f"Query pipeline failed: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))
