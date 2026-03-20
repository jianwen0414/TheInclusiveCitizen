"""
POST /api/extract-steps — Asynchronous step extraction endpoint.

Decoupled from /api/query so the main response (text + audio) is returned
immediately.  The frontend calls this endpoint after displaying the answer,
then updates the message with step cards when ready.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from models.schemas import ExtractStepsRequest, ExtractStepsResponse
from services.llm_service import extract_steps

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["steps"])


@router.post("/extract-steps", response_model=ExtractStepsResponse)
async def extract_steps_endpoint(request: ExtractStepsRequest):
    try:
        steps, step_icons = await extract_steps(
            answer=request.answer,
            language=request.language,
        )
        return ExtractStepsResponse(steps=steps, step_icons=step_icons)
    except Exception as exc:
        logger.exception(f"extract-steps failed: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))
