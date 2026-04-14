"""
Internal pipeline endpoints for the Genkit TypeScript orchestration layer.
These endpoints are called by genkit-server/src/tools/ — they are NOT intended
for direct use by the frontend.

Endpoints:
  POST /api/detect-dialect  — dialect and language detection
  POST /api/retrieve        — pgvector RAG retrieval
  POST /api/generate        — LLM answer generation
  POST /api/simplify        — text simplification + Hijri enrichment
  POST /api/score           — cross-lingual semantic preservation score
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from models.schemas import (
    DetectDialectRequest,
    DetectDialectResponse,
    GenerateRequest,
    GenerateResponse,
    RetrieveRequest,
    RetrievedChunkSchema,
    RetrieveResponse,
    ScoreRequest,
    ScoreResponse,
    SimplifyRequest,
    SimplifyResponse,
)
from services.dialect_detector import (
    detect_dialect as _detect_dialect,
    detect_javanese_from_text,
    detect_malay_dialect,
)
from services.hijri_service import enrich_text_with_hijri
from services.llm_service import generate_answer as _generate_answer
from services.rag_pipeline import build_context_from_chunks, retrieve_relevant_chunks
from services.semantic_scorer import compute_semantic_score as _compute_semantic_score
from services.simplifier import simplify_text as _simplify_text

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["pipeline"])


@router.post("/detect-dialect", response_model=DetectDialectResponse)
async def detect_dialect_endpoint(request: DetectDialectRequest):
    """
    Detect language and Malay sub-dialect.
    Mirrors the exact branching logic from backend/tools/detect_dialect.py.
    """
    try:
        query = request.query

        if request.language_hint:
            detected_language = request.language_hint
            if detected_language == "ms":
                sub_dialect = detect_malay_dialect(query)
                if sub_dialect:
                    detected_language = sub_dialect
            elif detected_language == "id":
                if detect_javanese_from_text(query):
                    detected_language = "jv"
                else:
                    sub_dialect = detect_malay_dialect(query)
                    if sub_dialect:
                        detected_language = sub_dialect
        else:
            detected_language = await _detect_dialect(query)

        target_lang = (
            detected_language.split("-")[0]
            if "-" in detected_language
            else detected_language
        )
        return DetectDialectResponse(
            detected_language=detected_language,
            target_lang=target_lang,
        )
    except Exception as exc:
        logger.exception(f"detect-dialect failed: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/retrieve", response_model=RetrieveResponse)
async def retrieve_endpoint(request: RetrieveRequest):
    """
    Embed query and retrieve top-k document chunks from Supabase pgvector.
    Returns empty result (not 404) when no chunks meet the threshold.
    """
    try:
        chunks = await retrieve_relevant_chunks(
            request.query,
            top_k=request.top_k,
            threshold=request.threshold,
            doc_type_filter=request.doc_type_filter,
        )
        if not chunks:
            return RetrieveResponse(
                chunks=[],
                context="",
                original_chunk_text="",
                confidence=0.0,
            )
        context = build_context_from_chunks(chunks)
        return RetrieveResponse(
            chunks=[RetrievedChunkSchema(**c.__dict__) for c in chunks],
            context=context,
            original_chunk_text=chunks[0].chunk_text,
            confidence=chunks[0].similarity,
        )
    except Exception as exc:
        logger.exception(f"retrieve failed: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/generate", response_model=GenerateResponse)
async def generate_endpoint(request: GenerateRequest):
    """
    Generate a grounded answer in the target language using Gemini / SEA-LION fallback.
    """
    try:
        answer, llm_model = await _generate_answer(
            context=request.context,
            query=request.query,
            target_lang=request.target_lang,
            dialect_code=request.dialect_code,
        )
        return GenerateResponse(answer=answer, llm_model=llm_model)
    except Exception as exc:
        logger.exception(f"generate failed: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/simplify", response_model=SimplifyResponse)
async def simplify_endpoint(request: SimplifyRequest):
    """
    Simplify text to Grade 5–7 reading level with optional Hijri date enrichment.
    """
    try:
        simplified, grade = await _simplify_text(
            text=request.text,
            language=request.language,
            conservative=request.conservative,
        )
        if request.enrich_hijri:
            simplified = enrich_text_with_hijri(simplified)
        return SimplifyResponse(simplified_text=simplified, readability_grade=grade)
    except Exception as exc:
        logger.exception(f"simplify failed: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/score", response_model=ScoreResponse)
async def score_endpoint(request: ScoreRequest):
    """
    Compute simplification fidelity score between LLM answer (before simplification)
    and simplified answer (after simplification). Both are in the same target language.
    """
    try:
        score = _compute_semantic_score(
            source_text=request.source_text,
            simplified_text=request.simplified_text,
        )
        return ScoreResponse(score=score)
    except Exception as exc:
        logger.exception(f"score failed: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))
