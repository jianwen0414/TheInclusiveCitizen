"""
/api/synthesise — Text-to-speech endpoint
PRD Section 7.1 (Table 10): Converts text to speech audio
  using Google Cloud TTS Neural2 in specified language.
"""

import logging

from fastapi import APIRouter, HTTPException

from models.schemas import SynthesiseRequest, SynthesiseResponse
from services.tts_service import synthesise_speech

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["synthesise"])


@router.post("/synthesise", response_model=SynthesiseResponse)
async def synthesise(request: SynthesiseRequest):
    """
    Synthesise speech from text.
    PRD F07: Google Cloud TTS Neural2, language-matched voice.
    Speed 0.75x for elderly persona.
    """
    try:
        audio_b64, content_type = await synthesise_speech(
            text=request.text,
            language=request.language,
            speed=request.speed,
        )
        return SynthesiseResponse(
            audio_base64=audio_b64,
            content_type=content_type,
        )
    except Exception as exc:
        logger.exception(f"TTS synthesis failed: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))
