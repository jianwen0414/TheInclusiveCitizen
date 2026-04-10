# NOTE: Genkit orchestration has migrated to genkit-server/ (TypeScript).
# This file is retained as logic reference and documentation only.
# The FastAPI endpoints called by the Genkit TS tools are in genkit-server/src/tools/.
"""
Genkit tool: transcribe_audio
Wraps Google Cloud STT v2 (chirp_3) call in services/stt_service.py.
Used by the query flow when audio_base64 is provided directly to the flow.
The standalone /api/transcribe endpoint calls the service function directly.
"""
from __future__ import annotations

import base64

from pydantic import BaseModel

from genkit_config import ai
from services.stt_service import transcribe_audio as _transcribe_audio


class TranscribeAudioInput(BaseModel):
    audio_base64: str
    audio_format: str = "webm"


class TranscribeAudioOutput(BaseModel):
    text: str
    detected_language: str


@ai.tool(
    name="transcribe_audio",
    description=(
        "Transcribe base64-encoded audio to text using Google Cloud STT v2 chirp_3. "
        "Returns the transcript and the detected ISO language code. "
        "Audio bytes are deleted from memory immediately after transcription."
    ),
)
async def transcribe_audio_tool(input: TranscribeAudioInput) -> TranscribeAudioOutput:
    audio_bytes = base64.b64decode(input.audio_base64)
    text, detected_language = await _transcribe_audio(audio_bytes, input.audio_format)
    return TranscribeAudioOutput(text=text, detected_language=detected_language)
