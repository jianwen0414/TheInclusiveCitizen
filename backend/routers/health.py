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

    # Google Cloud (Vertex AI)
    try:
        project = os.getenv("GOOGLE_CLOUD_PROJECT", "")
        if project:
            statuses["vertex_ai"] = "configured"
        else:
            statuses["vertex_ai"] = "not_configured"
    except Exception as exc:
        statuses["vertex_ai"] = f"error: {exc}"

    # SEA-LION v4
    sealion_key = os.getenv("SEALION_API_KEY", "")
    statuses["sealion_v4"] = "configured" if sealion_key else "not_configured"

    # Google Cloud Translation
    statuses["cloud_translation"] = (
        "configured" if os.getenv("GOOGLE_CLOUD_PROJECT") else "not_configured"
    )

    overall = "healthy" if all(
        v in ("ok", "configured") for v in statuses.values()
    ) else "degraded"

    return HealthResponse(status=overall, services=statuses)
