-- ─────────────────────────────────────────────────────
-- The Inclusive Citizen — Supabase pgvector Schema
-- PRD Appendix B (Table 19)
-- ─────────────────────────────────────────────────────

-- 1. Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Document chunks table
CREATE TABLE IF NOT EXISTS document_chunks (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  doc_name    TEXT NOT NULL,
  doc_type    TEXT,
  page_number INT,
  chunk_text  TEXT NOT NULL,
  embedding   VECTOR(768),
  metadata    JSONB,
  created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- 3. IVFFlat index for cosine similarity retrieval
CREATE INDEX IF NOT EXISTS document_chunks_embedding_idx
  ON document_chunks
  USING ivfflat (embedding vector_cosine_ops)
  WITH (lists = 100);

-- 4. RPC function for vector similarity search
-- Called from backend: supabase.rpc("match_documents", {...})
CREATE OR REPLACE FUNCTION match_documents(
  query_embedding VECTOR(768),
  match_threshold FLOAT DEFAULT 0.5,
  match_count     INT   DEFAULT 3
)
RETURNS TABLE (
  id          UUID,
  doc_name    TEXT,
  doc_type    TEXT,
  page_number INT,
  chunk_text  TEXT,
  metadata    JSONB,
  similarity  FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    dc.id,
    dc.doc_name,
    dc.doc_type,
    dc.page_number,
    dc.chunk_text,
    dc.metadata,
    (1 - (dc.embedding <=> query_embedding))::FLOAT AS similarity
  FROM document_chunks dc
  WHERE 1 - (dc.embedding <=> query_embedding) > match_threshold
  ORDER BY dc.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;
