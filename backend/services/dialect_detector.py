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
    # Classic Kelantanese vocabulary (appear in raw dialect text)
    "ambo", "demo", "gapo", "dok", "nok", "kito", "sapa", "guano",
    "maghi", "make", "ttido", "oghe", "nate", "tubik", "gak",
    # Words that frequently survive chirp_3 STT normalization because
    # chirp_3 may transcribe them phonetically rather than normalising:
    "loni",      # Kelantanese: "sekarang" (now)
    "pom",       # Kelantanese: "pun" (also/too) — transcribed phonetically
    "bukey",     # Kelantanese: "bukan" — sometimes preserved
    "buleh",     # Kelantanese: "boleh" — phonetic variant
    "takdok",    # Kelantanese: "tiada/tak ada"
    "doh",       # Kelantanese: "dah/sudah" — sometimes preserved
    "ado",       # Kelantanese: "ada" — sometimes preserved
    "kijo",      # Kelantanese: "kerja"
    "nyo",       # Kelantanese: "nya/dia"
    "tahu dok",  # Kelantanese: "tahu tak"
    "sokmo",     # Kelantanese: "selalu" (always)
    "peghak",    # Kelantanese: "perak" (silver/state)
    "royak",     # Kelantanese: "cakap/bagitahu" (tell)
    "pehe",      # Kelantanese: "faham" (understand)
    "terer",     # Kelantanese: "pandai" (clever)
    # Typed Kelantanese orthography (often not normalised by STT)
    "layok",     # layak
    "dapak",     # dapat
    "puloh",     # puluh
    "tahon",     # tahun
    "umor",      # umur
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


def detect_malay_dialect(text: str) -> str | None:
    """
    Classify Malay dialect based on lexical markers.
    Public API — called both from within this module and from query.py
    when the STT has already identified the language as 'ms' but the
    text may still contain surviving dialect cues.
    """
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
    # Threshold: ≥2 hits for marker-dense raw dialect text; ≥1 hit is
    # sufficient for the post-STT survival markers which are individually
    # diagnostic (e.g. "loni", "pom", "takdok").
    POST_STT_SURVIVAL_MARKERS = {
        "loni", "pom", "bukey", "buleh", "takdok", "doh", "ado",
        "kijo", "nyo", "sokmo", "royak", "pehe",
        "layok", "dapak", "puloh", "tahon", "umor",
    }
    has_survival_marker = any(m in words for m in POST_STT_SURVIVAL_MARKERS)
    threshold = 1 if has_survival_marker else 2
    if scores[best_dialect] >= threshold:
        return best_dialect
    return None


# Keep private alias for backward compatibility within module
_detect_malay_dialect = detect_malay_dialect


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

def _has_malay_content_cues(text: str) -> bool:
    """
    Pan-Malay lexical cues that rarely co-occur in genuine Tagalog/Filipino.
    Used when lingua-py mislabels short colloquial Malay as TAGALOG (tl).

    Lingua's docs note strong accuracy on short text overall, but Austronesian
    languages share vocabulary; very short Kelantanese-style sentences can
    still be misclassified — see lingua-py README / accuracy tables on GitHub.
    """
    t = text.lower()
    # Multi-word phrases (high precision for Malaysian context)
    phrase_hits = sum(
        1
        for p in (
            "mak cik", "pak cik", "datuk", "datuk seri", "encik", "puan",
            "ringgit", "mykad", "kwsp", "lhdn", "jtk", "bsh", "str",
            "kerajaan malaysia", "kementerian",
        )
        if p in t
    )
    if phrase_hits >= 1:
        return True
    words = set(re.findall(r"\b\w+\b", t))
    # Single tokens common in Malaysian colloquial BM, uncommon in Tagalog
    token_hits = words & {
        "nak", "cik", "duit", "kerja", "kijo", "tetap", "puloh", "tahon",
        "umor", "layok", "dapak", "dok", "nok", "ambo",
    }
    return len(token_hits) >= 3


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

    # Colloquial Malaysian Malay (especially dialect spellings) is sometimes
    # misclassified as TAGALOG because both are Austronesian. If the text
    # clearly carries Malay dialect markers OR strong Malaysian BM cues,
    # override lingua and route through the Malay dialect path.
    if lingua_result and lingua_result not in ("ms", "id"):
        dialect = _detect_malay_dialect(text)
        if dialect:
            logger.debug(
                "Overriding lingua=%s → %s (dialect markers in text)",
                lingua_result,
                dialect,
            )
            return dialect
        if lingua_result == "tl" and _has_malay_content_cues(text):
            logger.debug(
                "Overriding lingua=tl → ms (Malay content cues; likely false Tagalog)"
            )
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
