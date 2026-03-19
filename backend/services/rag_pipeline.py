"""
RAG Pipeline Service
PRD Section 6.3 — Online Query Phase:
  1. Query embedded directly using gemini-embedding-001 (NO pre-translation)
  2. Top-k document chunks retrieved from Supabase pgvector by cosine similarity
  3. Retrieved context + prompt passed to LLM for answer generation
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
    top_k: int = 6,
    threshold: float = 0.25,
) -> list[RetrievedChunk]:
    """
    Embed the query and retrieve the top-k most relevant document chunks.

    Design decisions:
    - top_k=6: gives the LLM enough cross-page context (eligibility criteria
      often spans multiple pages; 3 was too few).
    - threshold=0.25: gemini-embedding-001 cross-lingual cosine scores for
      zh/en or ms/en pairs typically range 0.30–0.65 for relevant matches.
      0.25 catches near-misses without letting in junk.
    - fetch_count=50: fetch enough rows so the threshold filter still has a
      good pool to select from, especially with a 6-document knowledge base.
    - PRD constraint #3: query is NEVER pre-translated before embedding.

    Logs every retrieved candidate with its score so retrieval quality can
    be inspected at a glance without guessing.
    """
    # Embed the raw user query (any language — gemini-embedding-001 is multilingual)
    logger.info(f"[RAG] Embedding query: '{query[:100]}'")
    query_embedding = embed_query(query)

    # Fetch a large enough candidate pool from pgvector
    supabase = _get_supabase()
    fetch_count = 50  # fixed pool — large enough to cover all chunks in a ~6-doc KB

    result = supabase.rpc(
        "match_documents",
        {
            "query_embedding": query_embedding,
            "match_count": fetch_count,
            "filter": {},
        },
    ).execute()

    all_rows = result.data or []
    logger.info(f"[RAG] Supabase returned {len(all_rows)} candidate rows")

    # Log the full ranked list so we can see exactly what scores look like
    logger.info("[RAG] ── Candidate ranking (all rows) ──────────────────────")
    for i, row in enumerate(all_rows[:15], 1):  # log top-15 at most
        sim = float(row.get("similarity", 0))
        doc = row.get("doc_name", "?")
        pg = row.get("page_number", "?")
        preview = (row.get("chunk_text") or "")[:80].replace("\n", " ")
        logger.info(f"[RAG]  {i:>2}. sim={sim:.4f}  {doc} p{pg}  '{preview}…'")

    if len(all_rows) > 15:
        logger.info(f"[RAG]  … ({len(all_rows) - 15} more rows not shown)")
    logger.info("[RAG] ────────────────────────────────────────────────────────")

    # Apply threshold and take top_k
    chunks: list[RetrievedChunk] = []
    below_threshold: list[tuple[float, str, int]] = []

    for row in all_rows:
        similarity = float(row.get("similarity", 0))
        doc = row.get("doc_name", "?")
        pg = row.get("page_number", "?")

        if similarity >= threshold:
            chunks.append(
                RetrievedChunk(
                    doc_name=doc,
                    doc_type=row.get("doc_type"),
                    page_number=row.get("page_number"),
                    chunk_text=row["chunk_text"],
                    similarity=similarity,
                    metadata=row.get("metadata"),
                )
            )
        else:
            below_threshold.append((similarity, doc, pg))

    # Rows already arrive sorted by similarity DESC; slice to top_k
    chunks = chunks[:top_k]

    # Summary log
    if chunks:
        logger.info(
            f"[RAG] Selected {len(chunks)}/{len(all_rows)} chunks "
            f"(threshold={threshold}, top_k={top_k}) | "
            f"scores: {[f'{c.similarity:.3f}' for c in chunks]}"
        )
        for i, c in enumerate(chunks, 1):
            preview = c.chunk_text[:120].replace("\n", " ")
            logger.info(f"[RAG]  ✓ chunk {i}: {c.doc_name} p{c.page_number} "
                        f"sim={c.similarity:.4f} | '{preview}…'")
    else:
        logger.warning(
            f"[RAG] 0 chunks above threshold={threshold}. "
            f"Top row score was {float(all_rows[0].get('similarity', 0)):.4f} "
            f"({all_rows[0].get('doc_name', '?')} p{all_rows[0].get('page_number', '?')})"
            if all_rows else "[RAG] 0 chunks — Supabase returned empty result"
        )
        if below_threshold:
            logger.warning(
                f"[RAG] Rows below threshold: "
                + ", ".join(f"{s:.3f}/{d}p{p}" for s, d, p in below_threshold[:5])
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
