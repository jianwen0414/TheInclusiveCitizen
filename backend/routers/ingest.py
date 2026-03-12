"""
/api/ingest — Document ingestion endpoint
PRD Section 7.1 (Table 10): Admin — triggers ingestion pipeline
  for new government PDF document into vector store.
"""

import logging

from fastapi import APIRouter, File, UploadFile, Form, HTTPException

from models.schemas import IngestResponse
from services.document_ingestor import ingest_pdf

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["ingest"])


@router.post("/ingest", response_model=IngestResponse)
async def ingest_document(
    file: UploadFile = File(...),
    doc_type: str = Form("government_guide"),
):
    """
    Upload a PDF and ingest it into the vector store.
    PRD Section 6.3 Offline Indexing Phase:
      PDF → pymupdf parse → 512-token chunks → gemini-embedding-001 → Supabase pgvector
    """
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    try:
        file_bytes = await file.read()
        result = await ingest_pdf(
            file_bytes=file_bytes,
            file_name=file.filename,
            doc_type=doc_type,
        )

        return IngestResponse(
            status=result["status"],
            doc_name=result["doc_name"],
            chunks_created=result["chunks_created"],
        )
    except Exception as exc:
        logger.exception(f"Ingestion failed for {file.filename}")
        raise HTTPException(status_code=500, detail=str(exc))
