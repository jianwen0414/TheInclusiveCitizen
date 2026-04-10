# NOTE: Genkit orchestration has migrated to genkit-server/ (TypeScript).
# This file is retained as logic reference and documentation only.
# The FastAPI endpoints called by the Genkit TS tools are in genkit-server/src/tools/.
"""
Genkit tool: synthesise_speech
Wraps Google Cloud TTS Neural2/Wavenet/Standard synthesis from services/tts_service.py.

Voice tier selection: Neural2 > Wavenet > Standard.
The standalone /api/synthesise endpoint calls the service function directly.
TTS failure in the query flow is non-fatal — the caller catches all exceptions.
"""
from __future__ import annotations

from pydantic import BaseModel

from genkit_config import ai
from services.tts_service import synthesise_speech as _synthesise_speech


class SynthesiseSpeechInput(BaseModel):
    text: str
    language: str = "en"   # ISO language code, e.g. "ms", "en", "id"
    speed: float = 1.0     # speaking rate: elderly=0.75, rural=0.9, migrant=1.0


class SynthesiseSpeechOutput(BaseModel):
    audio_base64: str
    content_type: str = "audio/mp3"


@ai.tool(
    name="synthesise_speech",
    description=(
        "Convert text to speech using Google Cloud TTS (Neural2 > Wavenet > Standard "
        "tier fallback). Returns base64-encoded MP3 audio and content type. "
        "Speaking rate is persona-aware: elderly=0.75×, rural=0.9×, migrant=1.0×."
    ),
)
async def synthesise_speech_tool(
    input: SynthesiseSpeechInput,
) -> SynthesiseSpeechOutput:
    audio_b64, content_type = await _synthesise_speech(
        text=input.text,
        language=input.language,
        speed=input.speed,
    )
    return SynthesiseSpeechOutput(audio_base64=audio_b64, content_type=content_type)
