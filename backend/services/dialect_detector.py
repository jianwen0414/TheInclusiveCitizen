"""
Dialect Detection Pipeline
PRD Section 5.1, F02 — Dialect Detection & Routing:
  Primary: lingua-py with fastText
  Fallback: LangDetect for ambiguous inputs
  Detects language family + dialect classification within Malay.
"""

from __future__ import annotations

import logging
import re

logger = logging.getLogger(__name__)

_lingua_detector = None


# ── Malay Dialect Markers ────────────────────────────────

KELANTANESE_MARKERS = [
    "ambo", "demo", "gapo", "dok", "nok", "kito", "sapa", "guano",
    "maghi", "make", "ttido", "oghe", "nate", "tubik", "gak",
]

KEDAH_MARKERS = [
    "hang", "depa", "awat", "pasai", "loq", "kot", "mai", "hampa",
    "cemuih", "toksah", "naa",
]

SABAH_MARKERS = [
    "bah", "sudah", "bilang", "kasi", "mau", "sini", "sana",
    "tidak", "bagus", "ko", "sia",
]

SARAWAK_MARKERS = [
    "kitak", "kamek", "sik", "nang", "ya", "molah", "nemu",
    "polah", "iboh", "mena",
]

MANGLISH_MARKERS = [
    "lah", "lor", "mah", "wei", "weh", "leh", "dey", "hor",
    "aiyo", "can or not", "how come", "last time",
]


def _detect_malay_dialect(text: str) -> str | None:
    """Classify Malay dialect based on lexical markers."""
    text_lower = text.lower()
    words = set(re.findall(r"\b\w+\b", text_lower))

    scores = {
        "ms-kelantanese": sum(1 for m in KELANTANESE_MARKERS if m in words),
        "ms-kedah": sum(1 for m in KEDAH_MARKERS if m in words),
        "ms-sabah": sum(1 for m in SABAH_MARKERS if m in words),
        "ms-sarawak": sum(1 for m in SARAWAK_MARKERS if m in words),
        "ms-manglish": sum(1 for m in MANGLISH_MARKERS if m in text_lower),
    }

    best_dialect = max(scores, key=scores.get)  # type: ignore
    if scores[best_dialect] >= 2:
        return best_dialect
    return None


# ── lingua-py (Primary) ─────────────────────────────────

def _get_lingua_detector():
    global _lingua_detector
    if _lingua_detector is not None:
        return _lingua_detector

    try:
        from lingua import LanguageDetectorBuilder, Language

        _lingua_detector = (
            LanguageDetectorBuilder.from_languages(
                Language.MALAY,
                Language.INDONESIAN,
                Language.ENGLISH,
                Language.THAI,
                Language.VIETNAMESE,
                Language.CHINESE,
                Language.TAGALOG,
                Language.BENGALI,
                Language.TAMIL,
                Language.HINDI,
                Language.JAPANESE,
                Language.KOREAN,
            )
            .with_minimum_relative_distance(0.1)
            .build()
        )
    except Exception as exc:
        logger.warning(f"Failed to initialize lingua detector: {exc}")
        _lingua_detector = None

    return _lingua_detector


LINGUA_TO_ISO = {
    "MALAY": "ms",
    "INDONESIAN": "id",
    "ENGLISH": "en",
    "THAI": "th",
    "VIETNAMESE": "vi",
    "CHINESE": "zh",
    "TAGALOG": "tl",
    "BENGALI": "bn",
    "TAMIL": "ta",
    "HINDI": "hi",
    "JAPANESE": "ja",
    "KOREAN": "ko",
}


def _detect_with_lingua(text: str) -> str | None:
    detector = _get_lingua_detector()
    if detector is None:
        return None

    try:
        result = detector.detect_language_of(text)
        if result:
            return LINGUA_TO_ISO.get(result.name, None)
    except Exception as exc:
        logger.warning(f"lingua detection failed: {exc}")

    return None


# ── LangDetect (Fallback) ───────────────────────────────

def _detect_with_langdetect(text: str) -> str | None:
    try:
        from langdetect import detect

        lang = detect(text)
        lang_map = {
            "ms": "ms",
            "id": "id",
            "en": "en",
            "th": "th",
            "vi": "vi",
            "zh-cn": "zh",
            "zh-tw": "zh",
            "tl": "tl",
            "bn": "bn",
            "ta": "ta",
            "hi": "hi",
            "ja": "ja",
            "ko": "ko",
        }
        return lang_map.get(lang, lang)
    except Exception as exc:
        logger.warning(f"langdetect failed: {exc}")
        return None


# ── Script-Based Detection (fast pre-filter) ────────────

def _detect_by_script(text: str) -> str | None:
    """Quick script-based detection for non-Latin languages."""
    if re.search(r"[\u0E00-\u0E7F]", text):
        return "th"
    if re.search(r"[\u4E00-\u9FFF]", text):
        return "zh"
    if re.search(r"[\u0980-\u09FF]", text):
        return "bn"
    if re.search(r"[\u0B80-\u0BFF]", text):
        return "ta"
    if re.search(r"[\u0900-\u097F]", text):
        return "hi"
    if re.search(r"[\u3040-\u309F\u30A0-\u30FF]", text):
        return "ja"
    if re.search(r"[\uAC00-\uD7AF]", text):
        return "ko"
    return None


# ── Unified Detection Pipeline ───────────────────────────

async def detect_dialect(text: str) -> str:
    """
    Full dialect detection pipeline.
    PRD F02: lingua-py → fastText → LangDetect fallback chain.
    Returns ISO language code, possibly with dialect suffix.
    """
    if not text or not text.strip():
        return "en"

    # Quick script-based detection for non-Latin
    script_result = _detect_by_script(text)
    if script_result:
        return script_result

    # Primary: lingua-py
    lingua_result = _detect_with_lingua(text)

    if lingua_result in ("ms", "id"):
        # Malay and Indonesian are mutually intelligible — lingua-py
        # cannot reliably distinguish them.  Since this is a Malaysian
        # government assistant, any ms/id ambiguity resolves to "ms".
        dialect = _detect_malay_dialect(text)
        if dialect:
            return dialect
        return "ms"

    if lingua_result:
        return lingua_result

    # Fallback: LangDetect
    langdetect_result = _detect_with_langdetect(text)
    if langdetect_result:
        if langdetect_result in ("ms", "id"):
            dialect = _detect_malay_dialect(text)
            if dialect:
                return dialect
            return "ms"
        return langdetect_result

    return "en"
