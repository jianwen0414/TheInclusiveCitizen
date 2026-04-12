"""
Vertex AI Search Retriever
PRD Section 6.3 — Online Query Phase (new):
  Query → Discovery Engine search → extractive answers → enrich with Supabase doc_type

Replaces the old gemini-embedding-001 + Supabase pgvector retrieval path.
Discovery Engine handles multilingual query understanding natively — no pre-translation.
"""

from __future__ import annotations

import logging
import os

from google.api_core.client_options import ClientOptions
from google.api_core.exceptions import InvalidArgument
from google.cloud.discoveryengine_v1 import SearchRequest, SearchServiceClient
from supabase import create_client, Client

logger = logging.getLogger(__name__)


# ── Client factories ──────────────────────────────────────────────────────────

def _get_client_options() -> ClientOptions | None:
    """
    Discovery Engine requires a regional API endpoint when the data store location
    is NOT 'global'. For global data stores use the default endpoint (return None).
    For regional data stores (e.g. 'us', 'eu') pass the regional endpoint.

    Valid Discovery Engine locations: global, us, eu.
    Note: 'us-central1' is NOT a valid Discovery Engine location — use 'global'.
    """
    location = os.getenv("VERTEX_SEARCH_LOCATION", "global")
    if location == "global":
        return None
    return ClientOptions(api_endpoint=f"{location}-discoveryengine.googleapis.com")


def _get_supabase() -> Client:
    return create_client(
        os.getenv("SUPABASE_URL", ""),
        os.getenv("SUPABASE_SERVICE_ROLE_KEY", ""),
    )


def _search_client() -> SearchServiceClient:
    opts = _get_client_options()
    return SearchServiceClient(client_options=opts) if opts else SearchServiceClient()


def _serving_config_path() -> str:
    """
    Returns the Discovery Engine serving config path for SearchServiceClient.search().

    IMPORTANT: The search path uses the ENGINE resource (engines/{engine_id}),
    NOT the data store resource. Using the data store path here causes a 404.
    The data store path is only used by DocumentServiceClient (vertex_search_ingestor.py).
    """
    project = os.getenv("GOOGLE_CLOUD_PROJECT", "")
    location = os.getenv("VERTEX_SEARCH_LOCATION", "us-central1")
    engine_id = os.getenv("VERTEX_SEARCH_ENGINE_ID", "")
    return (
        f"projects/{project}/locations/{location}"
        f"/collections/default_collection"
        f"/engines/{engine_id}"
        f"/servingConfigs/default_config"
    )


# ── Internal helpers ──────────────────────────────────────────────────────────

def _extract_doc_name(result) -> str:
    """
    Extract a human-readable document name from a Discovery Engine SearchResult.

    Discovery Engine sets document.name to the full resource path ending in
    /documents/<doc_id>. The actual filename is stored in derived_struct_data
    under 'title' or 'id' after indexing. Falls back to the last path segment.
    """
    doc = result.document
    if doc.derived_struct_data:
        for key in ("title", "id"):
            val = doc.derived_struct_data.get(key)
            if val:
                return str(val)
    if doc.struct_data:
        for key in ("title", "id"):
            val = doc.struct_data.get(key)
            if val:
                return str(val)
    # Last segment of the resource name (the Discovery Engine document ID)
    return doc.name.split("/")[-1] if doc.name else "unknown"


def _extract_chunk_text_and_page(result) -> tuple[str, int | None]:
    """
    Extract chunk_text and page_number from a Discovery Engine SearchResult.

    All extractive answers for the document are joined so the LLM receives the
    full breadth of relevant passages, not just one excerpt.

    Preference order:
    1. All extractive_answers joined — passage-length text for each matched section
    2. All snippets joined — shorter highlight text (fallback)
    3. Empty string — caller will substitute doc_name as a placeholder

    derived_struct_data is a MapComposite populated by Discovery Engine after indexing.
    """
    doc = result.document
    chunk_text = ""
    page_number: int | None = None

    if doc.derived_struct_data:
        answers = doc.derived_struct_data.get("extractive_answers", [])
        if answers:
            # Join all answer passages with a separator so the LLM sees the full document
            passages = [a.get("content", "") for a in answers if a.get("content")]
            chunk_text = "\n\n---\n\n".join(passages)
            # Use the page number from the first answer for citation purposes
            raw_page = answers[0].get("pageNumber") or answers[0].get("page_number")
            if raw_page is not None:
                try:
                    page_number = int(raw_page)
                except (ValueError, TypeError):
                    pass

        # Fall back to snippets if no extractive answers were returned
        if not chunk_text:
            snippets = doc.derived_struct_data.get("snippets", [])
            if snippets:
                snippet_texts = [s.get("snippet", "") for s in snippets if s.get("snippet")]
                chunk_text = " ... ".join(snippet_texts)

    return chunk_text, page_number


def _fetch_metadata(supabase: Client, doc_names: list[str]) -> dict[str, dict]:
    """
    Batch-fetch doc_type and gcs_uri from document_metadata for the given doc_names.
    Returns {doc_name: {"doc_type": ..., "gcs_uri": ...}}.
    One Supabase call covers all results — avoids N+1 queries.
    """
    if not doc_names:
        return {}
    result = (
        supabase.table("document_metadata")
        .select("doc_name, doc_type, gcs_uri")
        .in_("doc_name", doc_names)
        .execute()
    )
    return {
        row["doc_name"]: {
            "doc_type": row.get("doc_type"),
            "gcs_uri": row.get("gcs_uri"),
        }
        for row in (result.data or [])
    }


# ── Public API ────────────────────────────────────────────────────────────────

async def retrieve_context(
    query: str,
    top_k: int = 6,
    threshold: float = 0.25,
    doc_type_filter: list[str] | None = None,
) -> list[dict]:
    """
    Search Vertex AI Search (Discovery Engine) for chunks relevant to query.

    Design decisions:
    - No pre-translation: Discovery Engine handles multilingual queries natively
      (PRD constraint #3).
    - top_k maps to SearchRequest.page_size.
    - threshold is applied post-fetch on relevance_score (0.0–1.0).
      Note: Discovery Engine relevance_score is NOT cosine similarity — it is a
      relevance rank. The 0.25 default is carried over from the pgvector threshold
      and may need tuning based on observed score distributions in production.
    - extractive_answers preferred over snippets (longer, more complete text).
    - doc_type and gcs_uri are joined from Supabase document_metadata in one call.
    - relevance_score maps to the 'similarity' field in RetrievedChunk for downstream
      compatibility with the existing semantic scorer and source citation logic.
    - doc_type_filter: when provided, builds a Vertex AI Search filter expression
      e.g. 'doc_type: ANY("flood_emergency", "flood_alert")'. Requires doc_type to
      be configured as a filterable field in the Discovery Engine data store schema.
      If doc_type is not indexed as filterable, the filter is silently ignored by
      Discovery Engine and all documents are returned (graceful degradation).

    Returns list[dict] with keys:
      chunk_text, doc_name, doc_type, page_number, source_url, relevance_score
    """
    logger.info(f"[Retriever] Querying Vertex AI Search: '{query[:100]}'")

    client = _search_client()
    serving_config = _serving_config_path()

    content_search_spec = SearchRequest.ContentSearchSpec(
        extractive_content_spec=(
            SearchRequest.ContentSearchSpec.ExtractiveContentSpec(
                # Fetch up to 5 answer passages per document so the LLM receives
                # a fuller picture of each document rather than a single excerpt.
                max_extractive_answer_count=5,
                max_extractive_segment_count=0,
            )
        ),
        snippet_spec=SearchRequest.ContentSearchSpec.SnippetSpec(
            return_snippet=True,
            max_snippet_count=3,
        ),
    )

    # Build filter expression for flood-specific retrieval when requested.
    # Syntax: 'doc_type: ANY("flood_emergency", "flood_alert")'
    # NOTE: Requires doc_type to be a filterable field in the Discovery Engine schema.
    # If not configured, the filter is silently ignored and all documents are searched.
    filter_expr: str | None = None
    if doc_type_filter:
        quoted = ", ".join(f'"{v}"' for v in doc_type_filter)
        filter_expr = f"doc_type: ANY({quoted})"
        logger.info(f"[Retriever] Applying doc_type filter: {filter_expr}")

    def _build_request(filter_str: str | None) -> SearchRequest:
        # Construct SearchRequest directly (not via **kwargs) to ensure compatibility
        # with the protobuf message constructor — filter is set as an attribute only
        # when non-empty to avoid sending a blank filter that could suppress results.
        req = SearchRequest(
            serving_config=serving_config,
            query=query,
            page_size=top_k,
            content_search_spec=content_search_spec,
        )
        if filter_str:
            req.filter = filter_str
        return req

    # When a filter expression is provided, attempt the filtered search first.
    # If Discovery Engine rejects it with InvalidArgument (field not configured
    # as filterable in the data store schema), fall back to an unfiltered search
    # rather than propagating a 500 error.
    try:
        response = client.search(request=_build_request(filter_expr))
    except InvalidArgument as exc:
        if filter_expr:
            logger.warning(
                f"[Retriever] Filter expression rejected by Discovery Engine "
                f"({exc.message.splitlines()[0]}); retrying without filter"
            )
            filter_expr = None
            response = client.search(request=_build_request(None))
        else:
            raise

    # Collect raw results before the Supabase metadata join
    raw_results: list[dict] = []
    for search_result in response.results:
        doc_name = _extract_doc_name(search_result)
        chunk_text, page_number = _extract_chunk_text_and_page(search_result)
        relevance_score = float(getattr(search_result, "relevance_score", 0.0))

        # Ensure chunk_text is never empty — semantic scorer requires a non-empty string
        if not chunk_text:
            chunk_text = doc_name
            logger.debug(
                f"[Retriever] No extractive text for {doc_name} — using doc_name as placeholder"
            )

        raw_results.append({
            "doc_name": doc_name,
            "relevance_score": relevance_score,
            "chunk_text": chunk_text,
            "page_number": page_number,
        })

    # If a doc_type filter was applied and returned 0 results, retry without the filter.
    # This handles the case where doc_type is not indexed as a filterable attribute in
    # Discovery Engine (graceful degradation) or the filter was too restrictive.
    if not raw_results and filter_expr:
        logger.info(
            f"[Retriever] Filtered search returned 0 results; retrying without doc_type filter"
        )
        response = client.search(request=_build_request(None))
        for search_result in response.results:
            doc_name = _extract_doc_name(search_result)
            chunk_text, page_number = _extract_chunk_text_and_page(search_result)
            relevance_score = float(getattr(search_result, "relevance_score", 0.0))
            if not chunk_text:
                chunk_text = doc_name
            raw_results.append({
                "doc_name": doc_name,
                "relevance_score": relevance_score,
                "chunk_text": chunk_text,
                "page_number": page_number,
            })

    if not raw_results:
        logger.warning(f"[Retriever] Vertex AI Search returned 0 results for: '{query[:80]}'")
        return []

    # Discovery Engine does not always populate relevance_score — it may return 0.0 for all
    # results even when they are highly relevant. When that happens, assign synthetic positional
    # scores (rank 1 = 1.0, rank 2 = 0.9, ...) so the threshold filter doesn't discard
    # everything. DE's result ordering is already by relevance, so position is meaningful.
    if all(r["relevance_score"] == 0.0 for r in raw_results):
        logger.debug(
            "[Retriever] relevance_score not populated by Discovery Engine; "
            "assigning positional scores (rank 1=1.0, rank 2=0.9, ...)"
        )
        for i, r in enumerate(raw_results):
            r["relevance_score"] = max(0.3, 1.0 - i * 0.1)

    raw_scores = [f"{r['relevance_score']:.3f}" for r in raw_results]
    logger.info(f"[Retriever] Raw results: {len(raw_results)} | scores: {raw_scores}")

    # Batch-fetch doc_type and gcs_uri from Supabase
    doc_names = list({r["doc_name"] for r in raw_results})
    supabase = _get_supabase()
    metadata_map = _fetch_metadata(supabase, doc_names)

    # Apply threshold and build final result list
    results: list[dict] = []
    for raw in raw_results:
        score = raw["relevance_score"]
        doc_name = raw["doc_name"]

        if score < threshold:
            logger.debug(
                f"[Retriever] Filtered {doc_name} (score={score:.4f} < threshold={threshold})"
            )
            continue

        meta = metadata_map.get(doc_name, {})
        results.append({
            "chunk_text": raw["chunk_text"],
            "doc_name": doc_name,
            "doc_type": meta.get("doc_type"),
            "page_number": raw["page_number"],
            "source_url": meta.get("gcs_uri"),
            "relevance_score": score,
        })

    final_scores = [f"{r['relevance_score']:.3f}" for r in results]
    logger.info(
        f"[Retriever] Selected {len(results)}/{len(raw_results)} results "
        f"(threshold={threshold}) | scores: {final_scores}"
    )
    return results
