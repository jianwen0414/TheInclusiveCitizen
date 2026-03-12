"""
Text-to-Speech Service — Google Cloud TTS Neural2
PRD Section 5.1, F07 — Voice Output:
  Answers read aloud using Google Cloud TTS Neural2 voices.
  Language-matched voice: ms-MY for BM, id-ID for Indonesian, etc.
  Speed: 0.75x for elderly persona by default.
"""

from __future__ import annotations

import base64
import logging
import os

from utils.language_router import get_tts_locale

logger = logging.getLogger(__name__)

# Neural2 voice names per locale
TTS_VOICES = {
    "ms-MY": "ms-MY-Neural2-A",
    "en-MY": "en-US-Neural2-J",
    "en-US": "en-US-Neural2-J",
    "id-ID": "id-ID-Neural2-A",
    "th-TH": "th-TH-Neural2-C",
    "fil-PH": "fil-PH-Neural2-A",
    "vi-VN": "vi-VN-Neural2-A",
    "cmn-CN": "cmn-CN-Neural2-A",
    "bn-IN": "bn-IN-Neural2-A",
    "ta-IN": "ta-IN-Neural2-A",
    "hi-IN": "hi-IN-Neural2-A",
}


async def synthesise_speech(
    text: str,
    language: str = "en",
    speed: float = 1.0,
) -> tuple[str, str]:
    """
    Convert text to speech using Google Cloud TTS Neural2.
    PRD F07: Natural-sounding Malay, Indonesian, Thai, Filipino output.

    Returns (audio_base64, content_type).
    """
    from google.cloud import texttospeech

    client = texttospeech.TextToSpeechClient()

    locale = get_tts_locale(language)
    voice_name = TTS_VOICES.get(locale, "en-US-Neural2-J")

    synthesis_input = texttospeech.SynthesisInput(text=text)

    voice = texttospeech.VoiceSelectionParams(
        language_code=locale,
        name=voice_name,
    )

    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,
        speaking_rate=speed,
    )

    response = client.synthesize_speech(
        input=synthesis_input,
        voice=voice,
        audio_config=audio_config,
    )

    audio_b64 = base64.b64encode(response.audio_content).decode("utf-8")
    logger.info(f"TTS synthesis complete: {len(response.audio_content)} bytes, locale={locale}")

    return audio_b64, "audio/mp3"
