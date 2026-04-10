# NOTE: Genkit orchestration has migrated to genkit-server/ (TypeScript).
# This file is retained as logic reference and documentation only.
# The FastAPI endpoints called by the Genkit TS tools are in genkit-server/src/tools/.
"""
backend/flows/query_flow.py

inclusive_citizen_query_flow — Genkit flow orchestrating the full query pipeline.

All business logic stays in backend/services/. This module orchestrates only.
The existing /api/query request/response schema (QueryRequest / QueryResponse) is
preserved exactly — the FastAPI router shrinks to a single flow call.

Pipeline order (mirrors routers/query.py exactly):
  0. [Optional] Transcribe audio if audio_base64 provided
  1. Detect dialect / language
  2–3. RAG retrieval (embed → pgvector similarity search → build context)
  4. Generate answer with LLM (Gemini primary, SEA-LION fallback)
  5. [Conditional] Translate if target_lang not in LLM_DIRECT_LANGUAGES
  6. Simplify to Grade 5–7 + Hijri date enrichment
  7. Compute cross-lingual semantic preservation score
  8. [Conditional] Conservative retry if score < 0.45 for ms/en/id
  9. TTS synthesis (non-fatal — failure yields audio_url=None)

Streaming:
  ctx.send_chunk("step:<name>") emits progress strings on the side channel.
  Frontend SSE integration is a future task — see GENKIT_NOTES.md.
  To stream from FastAPI, replace `await flow(input)` with
  `flow.stream(input)` and iterate `.stream` with StreamingResponse.
"""
from __future__ import annotations

import logging
from typing import Optional

from pydantic import BaseModel
from genkit import ActionRunContext

from genkit_config import ai
from models.schemas import QueryResponse, Source
from services.semantic_scorer import SCORE_THRESHOLD
from utils.language_router import get_language_name

# Import every tool module so their @ai.tool() decorators fire and the tools
# are registered with the Genkit registry before the flow is defined.
from tools import (  # noqa: F401
    transcribe_audio,
    detect_dialect,
    retrieve_documents,
    generate_bm_answer,
    translate_answer,
    simplify_answer,
    compute_semantic_score,
    synthesise_speech,
)
from tools.transcribe_audio import transcribe_audio_tool, TranscribeAudioInput
from tools.detect_dialect import detect_dialect_tool, DetectDialectInput
from tools.retrieve_documents import retrieve_documents_tool, RetrieveDocumentsInput
from tools.generate_bm_answer import generate_bm_answer_tool, GenerateBmAnswerInput
from tools.translate_answer import translate_answer_tool, TranslateAnswerInput
from tools.simplify_answer import simplify_answer_tool, SimplifyAnswerInput
from tools.compute_semantic_score import (
    compute_semantic_score_tool,
    ComputeSemanticScoreInput,
)
from tools.synthesise_speech import synthesise_speech_tool, SynthesiseSpeechInput

logger = logging.getLogger(__name__)

# ── Constants (mirror routers/query.py) ─────────────────────────────────────

DISPLAY_SEMANTIC_SCORE_MIN = 0.6

# Languages where Gemini generates reliably in the target language directly.
# Translation is skipped for these — avoids a redundant round-trip.
LLM_DIRECT_LANGUAGES = {"ms", "en", "id", "jv", "zh", "hi", "ta", "th", "vi", "tl"}

# Languages where the semantic scorer has meaningful cross-lingual alignment.
# Only these are eligible for the conservative retry and disclaimer.
SCORE_CHECK_LANGUAGES = {"ms", "en", "id"}

# TTS speaking rate per persona (PRD Section 3.2)
PERSONA_TTS_SPEED = {"elderly": 0.75, "migrant": 1.0, "rural": 0.9}


# ── Flow input schema ────────────────────────────────────────────────────────

class QueryFlowInput(BaseModel):
    query: str
    persona: str = "elderly"
    language: Optional[str] = None       # pre-detected ISO code (e.g. from /api/transcribe)
    audio_base64: Optional[str] = None   # future: direct audio → flow (currently unused)


# ── Flow definition ──────────────────────────────────────────────────────────

@ai.flow()
async def inclusive_citizen_query_flow(
    input: QueryFlowInput,
    ctx: ActionRunContext,
) -> QueryResponse:
    """
    Full query pipeline as a Genkit flow.
    Each step emits a progress chunk for future SSE streaming integration.
    """
    query = input.query
    persona = input.persona
    disclaimer = None

    # ── Step 0 (optional): Transcribe audio ─────────────────────────────────
    if input.audio_base64:
        ctx.send_chunk("step:transcribe_audio")
        r = await transcribe_audio_tool(TranscribeAudioInput(
            audio_base64=input.audio_base64,
            audio_format="webm",
        ))
        query = r.text
        if not input.language:
            input = input.model_copy(update={"language": r.detected_language})

    # ── Step 1: Detect dialect ───────────────────────────────────────────────
    ctx.send_chunk("step:detect_dialect")
    dr = await detect_dialect_tool(DetectDialectInput(
        query=query,
        language_hint=input.language,
    ))
    detected_language = dr.detected_language
    target_lang = dr.target_lang
    # dialect_code drives the system prompt selection in the LLM service
    dialect_code = (
        detected_language if detected_language.startswith("ms-") else target_lang
    )
    logger.info(f"[FLOW] dialect={detected_language} target_lang={target_lang}")

    # ── Steps 2–3: RAG retrieval ─────────────────────────────────────────────
    ctx.send_chunk("step:retrieve_documents")
    rag = await retrieve_documents_tool(RetrieveDocumentsInput(query=query))

    if not rag.chunks:
        return QueryResponse(
            answer=(
                "I could not find relevant information in the official documents. "
                "Please contact the relevant government agency directly."
            ),
            answer_bm=(
                "Maklumat ini tiada dalam dokumen rasmi yang dirujuk. "
                "Sila hubungi agensi berkaitan."
            ),
            original_text="",
            translation_model="none",
            llm_model="none",
            semantic_score=0.0,
            readability_grade=0.0,
            sources=[],
            detected_language=detected_language,
            confidence=0.0,
            disclaimer="No relevant documents found.",
        )

    # ── Step 4: LLM answer generation ───────────────────────────────────────
    ctx.send_chunk("step:generate_answer")
    llm = await generate_bm_answer_tool(GenerateBmAnswerInput(
        context=rag.context,
        query=query,
        target_lang=target_lang,
        dialect_code=dialect_code,
    ))
    answer = llm.answer
    llm_model = llm.llm_model
    translation_model = "none"

    # ── Step 5 (conditional): Translation ───────────────────────────────────
    # Skip for high-resource languages — LLM already generated in target language.
    if target_lang not in LLM_DIRECT_LANGUAGES:
        ctx.send_chunk("step:translate_answer")
        tr = await translate_answer_tool(TranslateAnswerInput(
            text=answer,
            source_lang="en",
            target_lang=target_lang,
        ))
        answer = tr.translated_text
        translation_model = tr.translation_model

    # ── Step 6: Simplify + Hijri enrichment ─────────────────────────────────
    ctx.send_chunk("step:simplify_answer")
    language_name = get_language_name(target_lang)
    simp = await simplify_answer_tool(SimplifyAnswerInput(
        text=answer,
        language=language_name,
        conservative=False,
        enrich_hijri=True,   # Hijri enrichment only on the first pass
    ))
    simplified_answer = simp.simplified_text
    readability_grade = simp.readability_grade

    # ── Step 7: Semantic preservation score ─────────────────────────────────
    ctx.send_chunk("step:compute_semantic_score")
    sc = await compute_semantic_score_tool(ComputeSemanticScoreInput(
        original_bm_text=rag.original_chunk_text,
        translated_simplified_text=simplified_answer,
    ))
    semantic_score = sc.score

    # ── Step 8: Conservative retry if score too low ──────────────────────────
    # Retry uses `answer` (pre-simplification text) — NOT simplified_answer.
    # Hijri enrichment is NOT applied on the retry (matches original query.py).
    if target_lang in SCORE_CHECK_LANGUAGES and semantic_score < SCORE_THRESHOLD:
        ctx.send_chunk("step:simplify_answer_retry")
        logger.warning(
            f"[FLOW] score={semantic_score:.3f} < {SCORE_THRESHOLD}, "
            "conservative retry"
        )
        retry = await simplify_answer_tool(SimplifyAnswerInput(
            text=answer,
            language=language_name,
            conservative=True,
            enrich_hijri=False,
        ))
        retry_sc = await compute_semantic_score_tool(ComputeSemanticScoreInput(
            original_bm_text=rag.original_chunk_text,
            translated_simplified_text=retry.simplified_text,
        ))
        if retry_sc.score > semantic_score:
            simplified_answer = retry.simplified_text
            readability_grade = retry.readability_grade
            semantic_score = retry_sc.score

    if semantic_score < SCORE_THRESHOLD and target_lang in SCORE_CHECK_LANGUAGES:
        disclaimer = (
            "Note: The meaning accuracy score is below the confidence threshold. "
            "Please verify this information with the relevant government agency."
        )

    # ── Step 9: TTS synthesis (non-blocking) ────────────────────────────────
    ctx.send_chunk("step:synthesise_speech")
    audio_url = None
    try:
        tts = await synthesise_speech_tool(SynthesiseSpeechInput(
            text=simplified_answer,
            language=target_lang,
            speed=PERSONA_TTS_SPEED.get(persona, 1.0),
        ))
        audio_url = f"data:audio/mp3;base64,{tts.audio_base64}"
    except Exception as exc:
        logger.warning(f"[FLOW] TTS failed (non-fatal): {exc}")

    # ── Build sources list ───────────────────────────────────────────────────
    sources = [
        Source(
            doc_name=c.doc_name,
            section=c.metadata.get("section") if c.metadata else None,
            page_number=c.page_number,
            excerpt=c.chunk_text[:300],
        )
        for c in rag.chunks
    ]

    return QueryResponse(
        answer=simplified_answer,
        answer_bm=answer if target_lang == "ms" else "",
        original_text=rag.original_chunk_text,
        translation_model=translation_model,
        llm_model=llm_model,
        semantic_score=max(semantic_score, DISPLAY_SEMANTIC_SCORE_MIN),
        readability_grade=readability_grade,
        sources=sources,
        detected_language=detected_language,
        confidence=rag.confidence,
        audio_url=audio_url,
        steps=None,
        step_icons=None,
        disclaimer=disclaimer,
    )
