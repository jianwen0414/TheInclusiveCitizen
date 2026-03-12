"""
/api/transcribe — Speech-to-text endpoint
PRD Section 7.1 (Table 10): Accepts audio blob, returns transcribed text
  and detected language via Google Cloud STT v2.
PRD Constraint #7: Audio deleted from memory immediately after transcription.
"""

import logging

from fastapi import APIRouter, File, UploadFile, HTTPException

from models.schemas import TranscribeResponse
from services.stt_service import transcribe_audio

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["transcribe"])


@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe(file: UploadFile = File(...)):
    """
    Transcribe audio to text with language detection.
    PRD F01: Google Cloud STT v2 with automatic language detection.
    Audio is NOT persisted — PRD constraint #7.
    """
    try:
        audio_bytes = await file.read()
        audio_format = "webm"
        if file.filename:
            ext = file.filename.rsplit(".", 1)[-1].lower()
            if ext in ("wav", "mp3", "ogg", "flac", "webm"):
                audio_format = ext

        text, detected_language = await transcribe_audio(audio_bytes, audio_format)

        # Explicit cleanup — PRD constraint #7, #8
        del audio_bytes

        return TranscribeResponse(
            text=text,
            detected_language=detected_language,
        )
    except Exception as exc:
        logger.exception(f"Transcription failed: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))
