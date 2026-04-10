"""
Vertex AI Search Ingestor
PRD Section 6.3 — Offline Indexing Phase (new):
  PDF → GCS upload → Discovery Engine import (async) → Supabase document_metadata

Replaces the old pymupdf + gemini-embedding-001 + Supabase pgvector pipeline.
Discovery Engine handles PDF parsing, chunking, and embedding internally.
"""

from __future__ import annotations

import logging
import os

from google.api_core.client_options import ClientOptions
from google.cloud import storage
from google.cloud.discoveryengine_v1 import (
    DocumentServiceClient,
    GcsSource,
    ImportDocumentsRequest,
)
from supabase import create_client, Client

logger = logging.getLogger(__name__)


# ── Client factories ──────────────────────────────────────────────────────────

def _get_supabase() -> Client:
    return create_client(
        os.getenv("SUPABASE_URL", ""),
        os.getenv("SUPABASE_SERVICE_ROLE_KEY", ""),
    )


def _gcs_client() -> storage.Client:
    return storage.Client(project=os.getenv("GOOGLE_CLOUD_PROJECT"))


def _get_client_options() -> ClientOptions | None:
    """
    Discovery Engine requires a regional API endpoint when location is not 'global'.
    Valid locations: global, us, eu. Note: 'us-central1' is NOT valid — use 'global'.
    """
    location = os.getenv("VERTEX_SEARCH_LOCATION", "global")
    if location == "global":
        return None
    return ClientOptions(api_endpoint=f"{location}-discoveryengine.googleapis.com")


def _doc_service_client() -> DocumentServiceClient:
    opts = _get_client_options()
    return DocumentServiceClient(client_options=opts) if opts else DocumentServiceClient()


def _data_store_branch_path() -> str:
    """
    Returns the Discovery Engine branch resource path used by DocumentServiceClient.
    Note: uses the data store path (dataStores/{data_store_id}), not the engine path.
    The engine path is used only by SearchServiceClient (see vertex_search_retriever.py).
    """
    project = os.getenv("GOOGLE_CLOUD_PROJECT", "")
    location = os.getenv("VERTEX_SEARCH_LOCATION", "us-central1")
    data_store_id = os.getenv("VERTEX_SEARCH_DATA_STORE_ID", "")
    return (
        f"projects/{project}/locations/{location}"
        f"/collections/default_collection"
        f"/dataStores/{data_store_id}"
        f"/branches/default_branch"
    )


# ── Internal helpers ──────────────────────────────────────────────────────────

def _upload_to_gcs(file_bytes: bytes, file_name: str) -> str:
    """
    Upload PDF bytes to GCS and return the gs:// URI.
    Objects are stored at documents/<file_name> to keep ingested PDFs organised.
    """
    bucket_name = os.getenv("GCS_BUCKET_NAME", "")
    client = _gcs_client()
    bucket = client.bucket(bucket_name)
    blob_name = f"documents/{file_name}"
    blob = bucket.blob(blob_name)
    blob.upload_from_string(file_bytes, content_type="application/pdf")
    gcs_uri = f"gs://{bucket_name}/{blob_name}"
    logger.info(f"[Ingestor] Uploaded {file_name} → {gcs_uri}")
    return gcs_uri


def _trigger_vertex_import(gcs_uri: str) -> str:
    """
    Tell Discovery Engine to import the document at gcs_uri into the data store.

    Uses INCREMENTAL reconciliation so existing documents are never deleted.
    data_schema="content" tells Discovery Engine to parse the raw PDF itself
    (as opposed to "document" schema which expects pre-structured JSONL).

    Returns the long-running operation name for reference.
    We do NOT await operation.result() — Discovery Engine indexes asynchronously
    (typically 5–30 min for PDFs). Waiting would exceed Cloud Run's 120 s timeout.
    """
    client = _doc_service_client()
    parent = _data_store_branch_path()

    request = ImportDocumentsRequest(
        parent=parent,
        gcs_source=GcsSource(
            input_uris=[gcs_uri],
            data_schema="content",
        ),
        reconciliation_mode=ImportDocumentsRequest.ReconciliationMode.INCREMENTAL,
    )
    operation = client.import_documents(request=request)
    operation_name = operation.operation.name
    logger.info(
        f"[Ingestor] Discovery Engine import queued for {gcs_uri}. "
        f"Operation: {operation_name}"
    )
    return operation_name


def _store_metadata(
    supabase: Client,
    doc_name: str,
    doc_type: str,
    gcs_uri: str,
) -> None:
    """
    Upsert a row into document_metadata.
    ON CONFLICT (doc_name) updates doc_type and gcs_uri so re-ingestion is idempotent.
    Sets vertex_import_status to 'pending' — update manually or via a webhook once
    the Discovery Engine operation completes.
    """
    supabase.table("document_metadata").upsert(
        {
            "doc_name": doc_name,
            "doc_type": doc_type,
            "gcs_uri": gcs_uri,
            "vertex_import_status": "pending",
        },
        on_conflict="doc_name",
    ).execute()
    logger.info(f"[Ingestor] Metadata stored for {doc_name} (type={doc_type})")


# ── Public API ────────────────────────────────────────────────────────────────

async def ingest_document(
    file_bytes: bytes,
    file_name: str,
    doc_type: str = "government_guide",
) -> dict:
    """
    Ingest a PDF into Vertex AI Search:
      1. Upload to GCS bucket at documents/<file_name>
      2. Trigger Discovery Engine async import (fire-and-forget)
      3. Upsert metadata into Supabase document_metadata table

    Returns a dict compatible with IngestResponse fields.
    status is 'processing' because Discovery Engine indexes asynchronously —
    the document is not yet searchable when this function returns.
    """
    logger.info(f"[Ingestor] Starting Vertex AI Search ingestion for {file_name}")

    gcs_uri = _upload_to_gcs(file_bytes, file_name)
    operation_name = _trigger_vertex_import(gcs_uri)

    supabase = _get_supabase()
    _store_metadata(supabase, file_name, doc_type, gcs_uri)

    return {
        "status": "processing",
        "doc_name": file_name,
        "chunks_created": 0,  # Vertex AI Search chunks internally; we do not chunk manually
        "indexing_note": (
            "Document uploaded to GCS and queued for Vertex AI Search indexing. "
            f"Operation: {operation_name}. "
            "Search results will be available once indexing completes (typically 5–30 min)."
        ),
    }


def list_ingested_documents() -> list[dict]:
    """Return all rows from the document_metadata table."""
    supabase = _get_supabase()
    result = (
        supabase.table("document_metadata")
        .select("*")
        .order("ingestion_timestamp", desc=True)
        .execute()
    )
    return result.data or []


def delete_document(doc_id: str) -> None:
    """
    Remove a document record from the Supabase metadata table.

    NOTE: This does NOT delete the document from Vertex AI Search.
    To remove a document from the search index, either:
      - GCP Console → Discovery Engine → Data Stores → [store] → Documents → Delete
      - Or call: DocumentServiceClient().delete_document(name=<document_resource_name>)
        where document_resource_name has the form:
        projects/{project}/locations/{location}/collections/default_collection/
        dataStores/{data_store_id}/branches/default_branch/documents/{document_id}
    """
    supabase = _get_supabase()
    supabase.table("document_metadata").delete().eq("id", doc_id).execute()
    logger.info(f"[Ingestor] Deleted metadata row id={doc_id}")
