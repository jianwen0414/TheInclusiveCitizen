"""
Text-to-Speech Service — Google Cloud TTS
PRD Section 5.1, F07 — Voice Output:
  Answers read aloud using Google Cloud TTS voices.
  Uses best available voice tier: Neural2 > Wavenet > Standard.
  Speed: 0.75x for elderly persona by default.

Available voices per https://cloud.google.com/text-to-speech/docs/voices:
  ms-MY: Wavenet only (no Neural2)
  id-ID: Wavenet only (no Neural2)
  en-US: Neural2 available
  th-TH: Neural2 available
  vi-VN: Neural2 available
  fil-PH: Neural2 available
  hi-IN: Neural2 available
  cmn-CN: No Neural2 (Wavenet)
  bn-IN: No Neural2 (Wavenet)
  ta-IN: No Neural2 (Wavenet)
"""

from __future__ import annotations

import base64
import logging
import re

from utils.language_router import get_tts_locale

logger = logging.getLogger(__name__)

# Best available voice per locale (verified against Google Cloud docs)
TTS_VOICES = {
    "ms-MY": "ms-MY-Wavenet-A",
    "en-US": "en-US-Neural2-J",
    "id-ID": "id-ID-Wavenet-A",
    "th-TH": "th-TH-Neural2-C",
    "fil-PH": "fil-ph-Neural2-A",
    "vi-VN": "vi-VN-Neural2-A",
    "cmn-CN": "cmn-CN-Wavenet-A",
    "bn-IN": "bn-IN-Wavenet-A",
    "ta-IN": "ta-IN-Wavenet-A",
    "hi-IN": "hi-IN-Neural2-A",
}

# Fallback to Standard if even Wavenet fails
TTS_STANDARD_FALLBACK = {
    "ms-MY": "ms-MY-Standard-A",
    "en-US": "en-US-Standard-J",
    "id-ID": "id-ID-Standard-A",
    "th-TH": "th-TH-Standard-A",
    "fil-PH": "fil-PH-Standard-A",
    "vi-VN": "vi-VN-Standard-A",
    "cmn-CN": "cmn-CN-Standard-A",
    "bn-IN": "bn-IN-Standard-A",
    "ta-IN": "ta-IN-Standard-A",
    "hi-IN": "hi-IN-Standard-A",
}


_MD_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
_MD_IMAGE_RE = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")
_MD_CODE_BLOCK_RE = re.compile(r"```[\s\S]*?```", re.MULTILINE)
_MD_INLINE_CODE_RE = re.compile(r"`([^`]+)`")
_MD_BOLD_ITALIC_RE = re.compile(r"(\*\*\*|___)(.+?)\1")
_MD_BOLD_RE = re.compile(r"(\*\*|__)(.+?)\1")
_MD_ITALIC_RE = re.compile(r"(\*|_)([^*_]+?)\1")
_MD_HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s+", re.MULTILINE)
_MD_BLOCKQUOTE_RE = re.compile(r"^\s{0,3}>\s?", re.MULTILINE)
_MD_LIST_BULLET_RE = re.compile(r"^\s*[-*+]\s+", re.MULTILINE)
_MD_LIST_NUMBER_RE = re.compile(r"^\s*\d+\.\s+", re.MULTILINE)


def sanitize_tts_text(text: str) -> str:
    """
    Convert Markdown-ish formatted text into plain speakable text.
    Keeps the visible words (e.g. **bold** -> bold) and strips markup so
    TTS doesn't read punctuation like asterisks.
    """
    if not text:
        return ""

    s = str(text)
    s = _MD_CODE_BLOCK_RE.sub(" ", s)
    s = _MD_IMAGE_RE.sub(r"\1", s)  # keep alt text
    s = _MD_LINK_RE.sub(r"\1", s)  # keep link text only
    s = _MD_INLINE_CODE_RE.sub(r"\1", s)

    # Emphasis markers
    s = _MD_BOLD_ITALIC_RE.sub(r"\2", s)
    s = _MD_BOLD_RE.sub(r"\2", s)
    s = _MD_ITALIC_RE.sub(r"\2", s)

    # Common line prefixes
    s = _MD_HEADING_RE.sub("", s)
    s = _MD_BLOCKQUOTE_RE.sub("", s)
    s = _MD_LIST_BULLET_RE.sub("", s)
    s = _MD_LIST_NUMBER_RE.sub("", s)

    # Remove any remaining stray emphasis characters that would be read aloud
    s = s.replace("*", "").replace("_", "")

    # Normalize whitespace
    s = re.sub(r"[ \t]+\n", "\n", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    s = re.sub(r"[ \t]{2,}", " ", s)
    return s.strip()


async def synthesise_speech(
    text: str,
    language: str = "en",
    speed: float = 1.0,
) -> tuple[str, str]:
    """
    Convert text to speech using Google Cloud TTS.
    Tries best voice (Neural2/Wavenet), falls back to Standard on error.
    Returns (audio_base64, content_type).
    """
    from google.cloud import texttospeech

    client = texttospeech.TextToSpeechClient()
    locale = get_tts_locale(language)

    cleaned = sanitize_tts_text(text)
    # API limit ~5000 bytes; keep a conservative margin.
    synthesis_input = texttospeech.SynthesisInput(text=(cleaned or text)[:4500])
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,
        speaking_rate=speed,
    )

    voice_name = TTS_VOICES.get(locale, "en-US-Neural2-J")
    fallback_name = TTS_STANDARD_FALLBACK.get(locale, "en-US-Standard-J")

    for name in [voice_name, fallback_name]:
        try:
            voice = texttospeech.VoiceSelectionParams(
                language_code=locale,
                name=name,
            )
            response = client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config,
            )
            audio_b64 = base64.b64encode(response.audio_content).decode("utf-8")
            logger.info(f"TTS: {len(response.audio_content)} bytes, voice={name}")
            return audio_b64, "audio/mp3"
        except Exception as exc:
            logger.warning(f"TTS voice {name} failed: {exc}")

    raise RuntimeError(f"All TTS voices failed for locale {locale}")
