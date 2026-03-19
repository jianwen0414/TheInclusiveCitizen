"""
Speech-to-Text Service — Google Cloud STT v2 (chirp_3, us region)
PRD Section 5.1, F01 — Voice-First Multimodal Input:
  Transcribes spoken input using Google Cloud STT v2 with automatic
  language detection for Malay, English, and Chinese.
PRD Constraint #7: Audio files deleted from memory immediately after transcription.

Confirmed working configuration (from official chirp_3 auto-detect docs):
  https://cloud.google.com/speech-to-text/v2/docs/chirp_3-model

  region   = "us"                        # chirp_3 does NOT exist in "global"
  endpoint = "us-speech.googleapis.com"  # required for us location
  model    = "chirp_3"                   # confirmed in us for ms-MY, en-US, cmn-Hans-CN
  langs    = ["auto"]                    # chirp_3 auto-detects; specific codes caused
                                         #   INVALID_ARGUMENT in the us region
  features = (none)                      # chirp_3 rejects explicit RecognitionFeatures

Errors history:
  - RecognitionFeatures(enable_automatic_punctuation=True) → INVALID_ARGUMENT
  - specific language_codes ["ms-MY","en-US","cmn-Hans-CN"] → INVALID_ARGUMENT
  - location="global" → 'chirp_3 does not exist in global'
  Solution: us + ["auto"] — exact pattern from chirp_3 auto-detect docs.
"""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)

STT_MODEL = "chirp_3"
STT_REGION = "us"
STT_API_ENDPOINT = "us-speech.googleapis.com"

# Map BCP-47 tags returned by chirp_3 to internal ISO codes used by the pipeline.
# chirp_3 returns full tags like "ms-MY", "en-US", "cmn-Hans-CN" etc.
_STT_LANG_MAP: dict[str, str] = {
    "ms":  "ms",
    "en":  "en",
    "cmn": "zh",
    "zh":  "zh",
    "id":  "id",
    "ta":  "ta",
    "hi":  "hi",
    "th":  "th",
    "vi":  "vi",
    "fil": "tl",
    "tl":  "tl",
    "bn":  "bn",
}


async def transcribe_audio(audio_bytes: bytes, audio_format: str = "webm") -> tuple[str, str]:
    """
    Transcribe audio using Google Cloud STT v2 chirp_3 (global, auto language).
    PRD F01: automatic language detection + code-switching support.

    Returns (transcribed_text, detected_language_code).
    Audio bytes are NOT persisted — PRD constraint #7.

    Uses the exact config from the official sync-recognize docs:
      SpeechClient()  →  global endpoint
      language_codes=["auto"]  →  chirp_3 detects dominant language
      model="chirp_3"
      NO RecognitionFeatures (chirp_3 rejects them → INVALID_ARGUMENT)
    """
    from google.cloud.speech_v2 import SpeechClient
    from google.cloud.speech_v2.types import cloud_speech

    project = os.getenv("GOOGLE_CLOUD_PROJECT", "")

    logger.info(
        f"[STT] audio={len(audio_bytes)} bytes, fmt={audio_format}, "
        f"model={STT_MODEL}, region={STT_REGION}"
    )

    if not audio_bytes:
        logger.warning("[STT] Received empty audio bytes — returning empty transcript")
        return "", "ms"

    from google.api_core.client_options import ClientOptions

    # us-speech.googleapis.com is required; chirp_3 is NOT available in "global".
    client = SpeechClient(
        client_options=ClientOptions(api_endpoint=STT_API_ENDPOINT)
    )

    # ["auto"] → chirp_3 auto-detects the dominant language.
    # Specific language codes (["ms-MY","en-US","cmn-Hans-CN"]) raised INVALID_ARGUMENT
    # in the us region; "auto" is the documented approach for chirp_3.
    # No RecognitionFeatures — chirp_3 rejects them (INVALID_ARGUMENT).
    config = cloud_speech.RecognitionConfig(
        auto_decoding_config=cloud_speech.AutoDetectDecodingConfig(),
        language_codes=["auto"],
        model=STT_MODEL,
    )

    recognizer_path = f"projects/{project}/locations/{STT_REGION}/recognizers/_"
    logger.info(f"[STT] recognizer={recognizer_path}")

    request = cloud_speech.RecognizeRequest(
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
