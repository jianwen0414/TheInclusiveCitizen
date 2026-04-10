"""
/api/ingest — Document ingestion endpoint
PRD Section 7.1 (Table 10): Admin — triggers ingestion pipeline
  for new government PDF document into Vertex AI Search.

New pipeline (replaces pymupdf + pgvector):
  PDF upload → GCS bucket → Discovery Engine import (async) → Supabase metadata
"""

import logging

from fastapi import APIRouter, File, UploadFile, Form, HTTPException

from models.schemas import IngestResponse
from services.vertex_search_ingestor import ingest_document

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["ingest"])


@router.post("/ingest", response_model=IngestResponse)
async def ingest_document_endpoint(
    file: UploadFile = File(...),
    doc_type: str = Form("government_guide"),
):
    """
    Upload a PDF and ingest it into Vertex AI Search.
    The document is uploaded to GCS and queued for async indexing.
    It becomes searchable once Discovery Engine completes indexing (typically 5–30 min).
    """
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    try:
        file_bytes = await file.read()
        result = await ingest_document(
            file_bytes=file_bytes,
            file_name=file.filename,
            doc_type=doc_type,
        )

        return IngestResponse(
            status=result["status"],
            doc_name=result["doc_name"],
            chunks_created=result["chunks_created"],
            indexing_note=result.get("indexing_note"),
        )
    except Exception as exc:
        logger.exception(f"Ingestion failed for {file.filename}")
        raise HTTPException(status_code=500, detail=str(exc))
