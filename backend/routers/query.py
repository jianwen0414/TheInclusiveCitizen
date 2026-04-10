"""
/api/query — Main query endpoint
PRD Section 6.3 Online Query Phase

Proxies to the Genkit TypeScript orchestration server (genkit-server/).
All pipeline logic runs in genkit-server/src/flows/queryFlow.ts; all heavy
AI/NLP work runs in the FastAPI service layer via internal pipeline endpoints.

The request/response schema (QueryRequest / QueryResponse) is unchanged —
the frontend contract is fully preserved.
"""
from __future__ import annotations

import logging
import os

import httpx
from fastapi import APIRouter, HTTPException

from models.schemas import QueryRequest, QueryResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["query"])

GENKIT_SERVER_URL = os.getenv("GENKIT_SERVER_URL", "http://localhost:3001")


@router.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"{GENKIT_SERVER_URL}/flow/query",
                json={
                    "query": request.query,
                    "persona": request.persona,
                    "language": request.language,
                },
            )
            resp.raise_for_status()
            return QueryResponse(**resp.json())
    except Exception as exc:
        logger.exception(f"Query pipeline failed: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))
