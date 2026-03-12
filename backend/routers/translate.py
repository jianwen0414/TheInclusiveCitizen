"""
/api/translate — Translation endpoint
PRD Section 7.1 (Table 10): Translates text from BM to target language.
  Routes to Google Cloud TLLM (primary) or NLLB-200 (fallback).
"""

import logging

from fastapi import APIRouter, HTTPException

from models.schemas import TranslateRequest, TranslateResponse
from services.translation_service import translate_text

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["translate"])


@router.post("/translate", response_model=TranslateResponse)
async def translate(request: TranslateRequest):
    """
    Translate text using tiered translation layer.
    PRD F03b: dialect_code → check TLLM support → route to Tier 1 or Tier 2.
    """
    try:
        translated, model_used = await translate_text(
            text=request.text,
            source_lang=request.source_lang,
            target_lang=request.target_lang,
        )
        return TranslateResponse(
            translated_text=translated,
            model_used=model_used,
        )
    except Exception as exc:
        logger.exception(f"Translation failed: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))
