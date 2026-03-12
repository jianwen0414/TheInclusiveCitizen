"""
Document Ingestion Service
PRD Section 6.3 — Offline Indexing Phase:
  1. Government PDFs uploaded
  2. pymupdf extracts text; chunked into 512-token segments with 50-token overlap
  3. Each chunk embedded using gemini-embedding-001 via Vertex AI
  4. Embeddings + metadata stored in Supabase pgvector table
"""

from __future__ import annotations

import io
import logging
import os
import uuid
from typing import BinaryIO

import fitz  # pymupdf
import google.generativeai as genai
from supabase import create_client, Client

logger = logging.getLogger(__name__)

CHUNK_SIZE_TOKENS = 512
CHUNK_OVERLAP_TOKENS = 50
CHARS_PER_TOKEN = 4  # conservative estimate for BM/EN mixed text
EMBEDDING_MODEL = "models/gemini-embedding-001"
EMBEDDING_DIM = 768


def _get_supabase() -> Client:
    url = os.getenv("SUPABASE_URL", "")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    return create_client(url, key)


def _init_genai() -> None:
    """Configure google.generativeai to use Vertex AI via ADC."""
    project = os.getenv("GOOGLE_CLOUD_PROJECT")
    if project:
        genai.configure(
            client_options={"api_endpoint": f"us-central1-aiplatform.googleapis.com"},
            default_metadata=[("x-goog-user-project", project)],
        )


# ── PDF Parsing ──────────────────────────────────────────

def extract_pages_from_pdf(pdf_bytes: bytes) -> list[dict]:
    """
    Parse PDF with pymupdf and return per-page text.
    Returns list of {"page_number": int, "text": str}.
    """
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    pages = []
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text = page.get_text("text")
        if text.strip():
            pages.append({"page_number": page_num + 1, "text": text.strip()})
    doc.close()
    return pages


# ── Chunking ─────────────────────────────────────────────

def chunk_text(
    text: str,
    chunk_size: int = CHUNK_SIZE_TOKENS,
    overlap: int = CHUNK_OVERLAP_TOKENS,
) -> list[str]:
    """
    Split text into overlapping chunks of approximately `chunk_size` tokens.
    PRD: 512-token segments with 50-token overlap.
    """
    char_chunk = chunk_size * CHARS_PER_TOKEN
    char_overlap = overlap * CHARS_PER_TOKEN

    if len(text) <= char_chunk:
        return [text]

    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = start + char_chunk

        # Try to break at sentence boundary
        if end < len(text):
            last_period = text.rfind(".", start, end)
            last_newline = text.rfind("\n", start, end)
            break_at = max(last_period, last_newline)
            if break_at > start + char_chunk // 2:
                end = break_at + 1

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        start = end - char_overlap
        if start >= len(text):
            break

    return chunks


# ── Embedding ────────────────────────────────────────────

def embed_texts(texts: list[str]) -> list[list[float]]:
    """
    Embed a batch of texts using gemini-embedding-001 via Vertex AI.
    PRD: gemini-embedding-001 handles cross-lingual matching natively.
    Returns list of 768-dim vectors.
    """
    _init_genai()

    embeddings: list[list[float]] = []
    batch_size = 20  # API batch limit

    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        result = genai.embed_content(
            model=EMBEDDING_MODEL,
            content=batch,
            task_type="retrieval_document",
        )
        if isinstance(result["embedding"][0], list):
            embeddings.extend(result["embedding"])
        else:
            embeddings.append(result["embedding"])

    return embeddings


def embed_query(text: str) -> list[float]:
    """Embed a single query for retrieval."""
    _init_genai()
    result = genai.embed_content(
        model=EMBEDDING_MODEL,
        content=text,
        task_type="retrieval_query",
    )
    return result["embedding"]


# ── Supabase Upsert ─────────────────────────────────────

def upsert_chunks(
    supabase: Client,
    chunks: list[dict],
) -> int:
    """
    Insert chunk records into Supabase document_chunks table.
    Each record: {doc_name, doc_type, page_number, chunk_text, embedding, metadata}
    """
    rows = []
    for chunk in chunks:
        rows.append({
            "id": str(uuid.uuid4()),
            "doc_name": chunk["doc_name"],
            "doc_type": chunk.get("doc_type"),
            "page_number": chunk.get("page_number"),
            "chunk_text": chunk["chunk_text"],
            "embedding": chunk["embedding"],
            "metadata": chunk.get("metadata", {}),
        })

    if not rows:
        return 0

    # Batch insert (Supabase supports bulk inserts)
    batch_size = 50
    total = 0
    for i in range(0, len(rows), batch_size):
        batch = rows[i : i + batch_size]
        supabase.table("document_chunks").insert(batch).execute()
        total += len(batch)

    return total


# ── Main Ingestion Pipeline ─────────────────────────────

async def ingest_pdf(
    file_bytes: bytes,
    file_name: str,
    doc_type: str = "government_guide",
) -> dict:
    """
    Full ingestion pipeline:
    1. Parse PDF → per-page text
    2. Chunk each page into 512-token overlapping segments
    3. Embed all chunks with gemini-embedding-001
    4. Upsert to Supabase pgvector
    """
    logger.info(f"Ingesting document: {file_name}")

    # Step 1: Parse PDF
    pages = extract_pages_from_pdf(file_bytes)
    logger.info(f"Extracted {len(pages)} pages from {file_name}")

    # Step 2: Chunk all pages
    all_chunks: list[dict] = []
    for page in pages:
        page_chunks = chunk_text(page["text"])
        for chunk_text_str in page_chunks:
            all_chunks.append({
                "doc_name": file_name,
                "doc_type": doc_type,
                "page_number": page["page_number"],
                "chunk_text": chunk_text_str,
                "metadata": {
                    "source": file_name,
                    "page": page["page_number"],
                    "doc_type": doc_type,
                },
            })

    logger.info(f"Created {len(all_chunks)} chunks from {file_name}")

    if not all_chunks:
        return {"status": "empty", "doc_name": file_name, "chunks_created": 0}

    # Step 3: Embed all chunks
    texts_to_embed = [c["chunk_text"] for c in all_chunks]
    embeddings = embed_texts(texts_to_embed)

    for chunk, emb in zip(all_chunks, embeddings):
        chunk["embedding"] = emb

    logger.info(f"Generated {len(embeddings)} embeddings for {file_name}")

    # Step 4: Upsert to Supabase
    supabase = _get_supabase()
    count = upsert_chunks(supabase, all_chunks)

    logger.info(f"Inserted {count} chunks into Supabase for {file_name}")

    return {"status": "success", "doc_name": file_name, "chunks_created": count}
