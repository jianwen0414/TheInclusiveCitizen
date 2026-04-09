"""
/api/health — Service health check
PRD Section 7.1 (Table 10): verifies upstream API connections
"""

import os

from fastapi import APIRouter

from models.schemas import HealthResponse

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    statuses: dict[str, str] = {}

    # Supabase
    try:
        from supabase import create_client

        url = os.getenv("SUPABASE_URL", "")
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
        if url and key:
            sb = create_client(url, key)
            sb.table("document_chunks").select("id", count="exact").limit(1).execute()
            statuses["supabase"] = "ok"
        else:
            statuses["supabase"] = "not_configured"
    except Exception as exc:
        statuses["supabase"] = f"error: {exc}"

    # Gemini 2.0 Flash — PRIMARY LLM (via Vertex AI)
    project = os.getenv("GOOGLE_CLOUD_PROJECT", "")
    gemini_model = os.getenv("GEMINI_MODEL_ID", "gemini-2.0-flash")
    statuses["gemini_primary"] = f"configured ({gemini_model})" if project else "not_configured"

    # SEA-LION v4 — OPTIONAL BM specialist fallback
    sealion_key = os.getenv("SEALION_API_KEY", "")
    statuses["sealion_v4_bm_specialist"] = "configured" if sealion_key else "not_configured (optional)"

    # Google Cloud Translation
    statuses["cloud_translation"] = (
        "configured" if project else "not_configured"
    )

    # Healthy when Gemini is configured and Supabase is reachable.
    # SEA-LION being absent is not a degraded condition.
    overall = "healthy" if (
        statuses["supabase"] == "ok"
        and "configured" in statuses["gemini_primary"]
    ) else "degraded"

    return HealthResponse(status=overall, services=statuses)
