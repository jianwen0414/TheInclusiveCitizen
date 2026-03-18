"""
Speech-to-Text Service — Google Cloud STT v2
PRD Section 5.1, F01 — Voice-First Multimodal Input:
  Transcribes spoken input using Google Cloud STT v2 with automatic
  language detection and code-switching support.
PRD Constraint #7: Audio files deleted from memory immediately after transcription.

API constraints (confirmed from official docs):
  - Multi-language detection (>1 code) is ONLY allowed in: eu, global, us
  - Maximum 3 language codes per request
  - ms-MY, en-US, cmn-Hans-CN are all confirmed in `us` + `chirp_3`
  Source: https://cloud.google.com/speech-to-text/v2/docs/speech-to-text-supported-languages
"""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)

# The `us` region is the only region that supports:
#   (a) multi-language detection, AND
#   (b) ms-MY + en-US + cmn-Hans-CN simultaneously with chirp_3.
STT_REGION = "us"
STT_MODEL = "chirp_3"
STT_API_ENDPOINT = "us-speech.googleapis.com"

# Maximum 3 language codes allowed for multi-language detection in `us`.
# Covers Malaysia's three primary spoken languages; chirp_3 also handles
# Malay-English code-switching natively within these 3 slots.
STT_LANGUAGE_CODES = [
    "ms-MY",        # Malay — primary language for Malaysian government services
    "en-US",        # English — second official language, widely used
    "cmn-Hans-CN",  # Mandarin Chinese — large Chinese Malaysian community
]

# Map STT-returned language codes to internal ISO codes used by the pipeline
_STT_LANG_MAP: dict[str, str] = {
    "ms":  "ms",
    "en":  "en",
    "cmn": "zh",
    "id":  "id",
    "ta":  "ta",
    "hi":  "hi",
    "th":  "th",
    "vi":  "vi",
    "fil": "tl",
    "bn":  "bn",
    "zh":  "zh",
}


async def transcribe_audio(audio_bytes: bytes, audio_format: str = "webm") -> tuple[str, str]:
    """
    Transcribe audio using Google Cloud STT v2.
    PRD F01: automatic language detection + code-switching support.

    Returns (transcribed_text, detected_language_code).
    Audio bytes are NOT persisted — PRD constraint #7.
    """
    from google.cloud import speech_v2 as speech
    from google.api_core.client_options import ClientOptions

    project = os.getenv("GOOGLE_CLOUD_PROJECT", "")

    # Regional client — must match STT_REGION exactly.
    client = speech.SpeechClient(
        client_options=ClientOptions(api_endpoint=STT_API_ENDPOINT)
    )

    config = speech.RecognitionConfig(
        auto_decoding_config=speech.AutoDetectDecodingConfig(),
        language_codes=STT_LANGUAGE_CODES,
        model=STT_MODEL,
        features=speech.RecognitionFeatures(
            enable_automatic_punctuation=True,
        ),
    )

    recognizer_path = f"projects/{project}/locations/{STT_REGION}/recognizers/_"

    request = speech.RecognizeRequest(
        recognizer=recognizer_path,
        config=config,
        content=audio_bytes,
    )

    response = client.recognize(request=request)

    transcript = ""
    detected_lang = "ms"  # default for Malaysian context

    for result in response.results:
        if result.alternatives:
            transcript += result.alternatives[0].transcript + " "
        if result.language_code:
            raw = result.language_code.split("-")[0].lower()
            detected_lang = _STT_LANG_MAP.get(raw, raw)

    transcript = transcript.strip()
    del audio_bytes  # PRD constraint #7 — no audio persistence

    if transcript:
        logger.info(f"STT: '{transcript[:80]}' → lang={detected_lang}")
    else:
        logger.warning("STT returned empty transcript")

    return transcript, detected_lang
