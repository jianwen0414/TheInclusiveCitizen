# NOTE: Genkit orchestration has migrated to genkit-server/ (TypeScript).
# This file is retained as logic reference and documentation only.
# The FastAPI endpoints called by the Genkit TS tools are in genkit-server/src/tools/.
"""
Genkit tool: retrieve_documents
Wraps Vertex AI Search retrieval from services/rag_pipeline.py.

Sends the query directly to Vertex AI Search (no pre-translation — PRD constraint #3),
retrieves top-k chunks by relevance score, and returns the context string plus
chunk metadata for source attribution.
"""
from __future__ import annotations

import logging

from pydantic import BaseModel

from genkit_config import ai
from services.rag_pipeline import retrieve_relevant_chunks, build_context_from_chunks

logger = logging.getLogger(__name__)


class RetrieveDocumentsInput(BaseModel):
    query: str
    top_k: int = 6
    threshold: float = 0.25


class RetrievedChunkSchema(BaseModel):
    doc_name: str
    doc_type: str | None = None
    page_number: int | None = None
    chunk_text: str
    similarity: float
    metadata: dict | None = None


class RetrieveDocumentsOutput(BaseModel):
    chunks: list[RetrievedChunkSchema]
    context: str               # pre-built context string for the LLM prompt
    original_chunk_text: str   # first chunk's raw text — used for semantic scoring
    confidence: float          # relevance score of the top chunk (0.0 if no results)


@ai.tool(
    name="retrieve_documents",
    description=(
        "Send the query directly to Vertex AI Search and retrieve the top-k most "
        "relevant document chunks (relevance score ≥ threshold). Discovery Engine "
        "handles multilingual query understanding natively — no pre-translation needed. "
        "Returns the assembled context string, chunk metadata for source attribution, "
        "and the raw text of the top chunk for downstream semantic scoring. "
        "Raises on Vertex AI Search API errors so the Genkit flow can surface them "
        "clearly. Returns an empty result (not an error) when no chunks meet the threshold."
    ),
)
async def retrieve_documents_tool(
    input: RetrieveDocumentsInput,
) -> RetrieveDocumentsOutput:
    try:
        chunks = await retrieve_relevant_chunks(
            input.query, top_k=input.top_k, threshold=input.threshold
        )
    except Exception as exc:
        logger.error(f"[retrieve_documents] Vertex AI Search call failed: {exc}")
        raise  # surface to Genkit flow rather than returning empty context silently

    if not chunks:
        return RetrieveDocumentsOutput(
            chunks=[],
            context="",
            original_chunk_text="",
            confidence=0.0,
        )

    context = build_context_from_chunks(chunks)
    return RetrieveDocumentsOutput(
        chunks=[RetrievedChunkSchema(**c.__dict__) for c in chunks],
        context=context,
        original_chunk_text=chunks[0].chunk_text,
        confidence=chunks[0].similarity,
    )
