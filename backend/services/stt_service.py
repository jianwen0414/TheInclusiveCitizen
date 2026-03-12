"""
Speech-to-Text Service — Google Cloud STT v2
PRD Section 5.1, F01 — Voice-First Multimodal Input:
  Transcribes spoken input using Google Cloud STT v2 with automatic
  language detection and code-switching support.
PRD Constraint #7: Audio files deleted from memory immediately after transcription.
"""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)

# Supported language codes for STT v2 recognition
STT_LANGUAGE_CODES = [
    "ms-MY",   # Malay
    "id-ID",   # Indonesian
    "en-MY",   # English (Malaysia)
    "en-US",   # English (US)
    "th-TH",   # Thai
    "vi-VN",   # Vietnamese
    "tl-PH",   # Tagalog
    "zh",      # Chinese
    "bn-IN",   # Bengali
    "ta-IN",   # Tamil
    "hi-IN",   # Hindi
]


async def transcribe_audio(audio_bytes: bytes, audio_format: str = "webm") -> tuple[str, str]:
    """
    Transcribe audio using Google Cloud STT v2.
    PRD F01: automatic language detection + code-switching support.

    Returns (transcribed_text, detected_language_code).
    Audio bytes are NOT persisted — PRD constraint #7.
    """
    from google.cloud import speech_v2 as speech

    project = os.getenv("GOOGLE_CLOUD_PROJECT", "")

    client = speech.SpeechClient()

    # Map audio formats to encoding
    encoding_map = {
        "webm": speech.ExplicitDecodingConfig.AudioEncoding.AUTO,
        "wav": speech.ExplicitDecodingConfig.AudioEncoding.LINEAR16,
        "mp3": speech.ExplicitDecodingConfig.AudioEncoding.AUTO,
        "ogg": speech.ExplicitDecodingConfig.AudioEncoding.AUTO,
        "flac": speech.ExplicitDecodingConfig.AudioEncoding.AUTO,
    }

    config = speech.RecognitionConfig(
        auto_decoding_config=speech.AutoDetectDecodingConfig(),
        language_codes=STT_LANGUAGE_CODES,
        model="long",
        features=speech.RecognitionFeatures(
            enable_automatic_punctuation=True,
        ),
    )

    request = speech.RecognizeRequest(
        recognizer=f"projects/{project}/locations/global/recognizers/_",
        config=config,
        content=audio_bytes,
    )

    response = client.recognize(request=request)

    # Extract transcription and language
    transcript = ""
    detected_lang = "en"

    for result in response.results:
        if result.alternatives:
            best = result.alternatives[0]
            transcript += best.transcript + " "

            if result.language_code:
                lang = result.language_code
                # Normalize to ISO 639-1
                detected_lang = lang.split("-")[0] if "-" in lang else lang

    transcript = transcript.strip()

    # Audio bytes are NOT persisted (PRD constraint #7)
    del audio_bytes

    logger.info(f"STT transcription: '{transcript[:50]}...' (detected: {detected_lang})")

    return transcript, detected_lang
