-- Migration: create document_metadata table
-- Replaces document_chunks pgvector table for ingestion tracking.
-- Used by vertex_search_ingestor to store doc_type per document,
-- and by vertex_search_retriever to enrich Vertex AI Search results
-- (Discovery Engine does not expose custom per-chunk metadata fields).
--
-- Run this in the Supabase SQL editor before deploying backend code.

CREATE TABLE IF NOT EXISTS document_metadata (
  id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  doc_name             TEXT NOT NULL UNIQUE,
  doc_type             TEXT NOT NULL DEFAULT 'government_guide',
  gcs_uri              TEXT,
  ingestion_timestamp  TIMESTAMPTZ DEFAULT NOW(),
  vertex_import_status TEXT DEFAULT 'pending'
);

-- Index for the batch join in vertex_search_retriever:
-- WHERE doc_name = ANY(array_of_doc_names)
CREATE INDEX IF NOT EXISTS document_metadata_doc_name_idx
    ON document_metadata (doc_name);
