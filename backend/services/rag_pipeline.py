"""
RAG Pipeline Service
PRD Section 6.3 — Online Query Phase:
  1. Query embedded directly using gemini-embedding-001 (NO pre-translation)
  2. Top-3 BM document chunks retrieved from Supabase pgvector by cosine similarity
  3. Retrieved BM context + prompt passed to LLM for answer generation
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass

from supabase import create_client, Client

from services.document_ingestor import embed_query

logger = logging.getLogger(__name__)


@dataclass
class RetrievedChunk:
    doc_name: str
    doc_type: str | None
    page_number: int | None
    chunk_text: str
    similarity: float
    metadata: dict | None


def _get_supabase() -> Client:
    return create_client(
        os.getenv("SUPABASE_URL", ""),
        os.getenv("SUPABASE_SERVICE_ROLE_KEY", ""),
    )


async def retrieve_relevant_chunks(
    query: str,
    top_k: int = 3,
    threshold: float = 0.3,
) -> list[RetrievedChunk]:
    """
    PRD Section 6.3 Online Query Phase steps 3-4:
    Embed query with gemini-embedding-001, then retrieve top-k BM chunks
    from Supabase pgvector by cosine similarity.

    CRITICAL (PRD constraint #3): Never pre-translate the user query.
    gemini-embedding-001 handles cross-lingual matching natively.

    Matches the existing Supabase function signature:
      match_documents(query_embedding, match_count, filter)
    Threshold filtering is applied in Python after retrieval.
    """
    # Step 1: Embed the raw user query (any language)
    query_embedding = embed_query(query)

    # Step 2: Vector similarity search via Supabase RPC.
    # Fetch more rows than needed (top_k * 4) so Python threshold filter
    # still yields top_k results even if some fall below threshold.
    supabase = _get_supabase()
    fetch_count = max(top_k * 4, 20)

    result = supabase.rpc(
        "match_documents",
        {
            "query_embedding": query_embedding,
            "match_count": fetch_count,
            "filter": {},
        },
    ).execute()

    # Step 3: Parse rows and apply similarity threshold in Python
    chunks: list[RetrievedChunk] = []
    for row in result.data or []:
        similarity = float(row["similarity"])
        if similarity >= threshold:
            chunks.append(
                RetrievedChunk(
                    doc_name=row["doc_name"],
                    doc_type=row.get("doc_type"),
                    page_number=row.get("page_number"),
                    chunk_text=row["chunk_text"],
                    similarity=similarity,
                    metadata=row.get("metadata"),
                )
            )

    # Rows already arrive sorted by similarity DESC; slice to top_k
    chunks = chunks[:top_k]

    if chunks:
        logger.info(
            f"Retrieved {len(chunks)} chunks "
            f"(top similarity: {chunks[0].similarity:.3f})"
        )
    else:
        logger.info("Retrieved 0 chunks above threshold for query")

    return chunks


def build_context_from_chunks(chunks: list[RetrievedChunk]) -> str:
    """Combine retrieved BM chunks into a single context string for LLM."""
    if not chunks:
        return ""

    sections = []
    for i, chunk in enumerate(chunks, 1):
        header = f"[Source {i}: {chunk.doc_name}"
        if chunk.page_number:
            header += f", Page {chunk.page_number}"
        header += "]"
        sections.append(f"{header}\n{chunk.chunk_text}")

    return "\n\n---\n\n".join(sections)
