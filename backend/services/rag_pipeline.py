"""
RAG Pipeline Service
PRD Section 6.3 — Online Query Phase:
  1. Query sent directly to Vertex AI Search (no embedding step — Discovery Engine handles it)
  2. Top-k document chunks retrieved from Discovery Engine by relevance score
  3. Retrieved context + prompt passed to LLM for answer generation

Replaces the old gemini-embedding-001 + Supabase pgvector retrieval path.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from services.vertex_search_retriever import retrieve_context

logger = logging.getLogger(__name__)


@dataclass
class RetrievedChunk:
    doc_name: str
    doc_type: str | None
    page_number: int | None
    chunk_text: str
    similarity: float
    metadata: dict | None


async def retrieve_relevant_chunks(
    query: str,
    top_k: int = 6,
    threshold: float = 0.25,
    doc_type_filter: list[str] | None = None,
) -> list[RetrievedChunk]:
    """
    Retrieve top-k most relevant document chunks from Vertex AI Search.

    Design decisions:
    - No embedding step: Discovery Engine handles query embedding internally.
    - top_k=6: unchanged from pgvector implementation (enough cross-page context).
    - threshold=0.25: applied to Discovery Engine relevance_score (0.0–1.0).
      Note: Discovery Engine relevance_score is not cosine similarity — monitor
      real score distributions after deployment and tune this value if needed.
    - relevance_score maps to the similarity field for downstream compatibility
      (semantic scorer, source citation, confidence field in QueryResponse).
    - metadata carries source_url (GCS URI) and doc_type for citation building.
    - PRD constraint #3: query is NEVER pre-translated (Discovery Engine is multilingual).
    - doc_type_filter: optional list of doc_type values to restrict retrieval to
      flood-specific documents (e.g. ['flood_emergency', 'flood_alert']).
    """
    logger.info(f"[RAG] Querying Vertex AI Search: '{query[:100]}'")

    raw_results = await retrieve_context(
        query, top_k=top_k, threshold=threshold, doc_type_filter=doc_type_filter
    )

    chunks: list[RetrievedChunk] = []
    for r in raw_results:
        chunks.append(
            RetrievedChunk(
                doc_name=r["doc_name"],
                doc_type=r.get("doc_type"),
                page_number=r.get("page_number"),
                chunk_text=r["chunk_text"],
                similarity=r["relevance_score"],  # Discovery Engine score → similarity
                metadata={
                    "source_url": r.get("source_url"),
                    "doc_type": r.get("doc_type"),
                },
            )
        )

    if chunks:
        scores = [f"{c.similarity:.3f}" for c in chunks]
        logger.info(f"[RAG] {len(chunks)} chunks retrieved | scores: {scores}")
        for i, c in enumerate(chunks, 1):
            preview = c.chunk_text[:120].replace("\n", " ")
            logger.info(
                f"[RAG]  ✓ chunk {i}: {c.doc_name} p{c.page_number} "
                f"sim={c.similarity:.4f} | '{preview}…'"
            )
    else:
        logger.warning(
            f"[RAG] 0 chunks returned from Vertex AI Search for: '{query[:80]}'"
        )

    return chunks


def build_context_from_chunks(chunks: list[RetrievedChunk]) -> str:
    """Combine retrieved chunks into a single context string for LLM."""
    if not chunks:
        return ""

    sections = []
    for i, chunk in enumerate(chunks, 1):
        header = f"[Source {i}: {chunk.doc_name}"
        if chunk.page_number:
            header += f", Page {chunk.page_number}"
        header += f" (similarity={chunk.similarity:.3f})]"
        sections.append(f"{header}\n{chunk.chunk_text}")

    return "\n\n---\n\n".join(sections)
