"""
Translation Tier Routing Logic
PRD Section 5.1, F03b — Tiered Translation Layer:
  Tier 1: Google Cloud TLLM (Advanced v3) — high-resource SEA languages
  Tier 2: NLLB-200-distilled-600M — ultra-low-resource dialects
"""

# Languages supported by Google Cloud Translation TLLM (Advanced v3)
# BM → target pairs with high quality
TLLM_SUPPORTED_TARGETS = {
    "en",       # English
    "id",       # Indonesian
    "th",       # Thai
    "tl",       # Tagalog / Filipino
    "vi",       # Vietnamese
    "zh",       # Chinese (Simplified)
    "zh-TW",    # Chinese (Traditional)
    "bn",       # Bengali
    "ms",       # Malay (Standard BM)
    "ta",       # Tamil
    "hi",       # Hindi
    "ja",       # Japanese
    "ko",       # Korean
}

# Low-resource dialects requiring NLLB-200 fallback
NLLB_ONLY_LANGUAGES = {
    "iba",      # Iban
    "dtp",      # Kadazan-Dusun
    "bdr",      # Bajau
    "bjn",      # Banjar
    "min",      # Minangkabau
    "jv",       # Javanese
    "su",       # Sundanese
}

# NLLB-200 language code mapping (flores-200 codes)
NLLB_LANG_CODES = {
    "en": "eng_Latn",
    "ms": "zsm_Latn",
    "id": "ind_Latn",
    "th": "tha_Thai",
    "tl": "tgl_Latn",
    "vi": "vie_Latn",
    "zh": "zho_Hans",
    "bn": "ben_Beng",
    "ta": "tam_Taml",
    "hi": "hin_Deva",
    "jv": "jav_Latn",
    "su": "sun_Latn",
    "iba": "iba_Latn",
    "min": "min_Latn",
    "bjn": "bjn_Latn",
}

# Human-readable language names
LANGUAGE_NAMES = {
    "en": "English",
    "ms": "Bahasa Melayu",
    "id": "Bahasa Indonesia",
    "th": "Thai",
    "tl": "Filipino",
    "vi": "Vietnamese",
    "zh": "Chinese",
    "bn": "Bengali",
    "ta": "Tamil",
    "hi": "Hindi",
    "jv": "Javanese",
    "su": "Sundanese",
    "iba": "Iban",
    "dtp": "Kadazan-Dusun",
    "bdr": "Bajau",
    "ms-kelantanese": "Kelantanese Malay",
    "ms-kedah": "Kedah Malay",
    "ms-sabah": "Sabah Malay",
    "ms-sarawak": "Sarawak Malay",
}

# Google Cloud TTS voice mapping (PRD F07)
TTS_VOICE_MAP = {
    "ms": "ms-MY",
    "en": "en-US",   # Google TTS has no en-MY locale; en-US is the correct code
    "id": "id-ID",
    # No dedicated Javanese locale in Google Cloud TTS — Indonesian voice is the
    # closest practical fallback for Latin-script Javanese / mixed BI text.
    "jv": "id-ID",
    "th": "th-TH",
    "tl": "fil-PH",
    "vi": "vi-VN",
    "zh": "cmn-CN",
    "bn": "bn-IN",
    "ta": "ta-IN",
    "hi": "hi-IN",
}


def get_translation_tier(target_lang: str) -> str:
    """
    Determine which translation tier to use for a target language.
    PRD F03b: check TLLM support list → route to Tier 1 or Tier 2.
    Returns "google_tllm" or "nllb200".
    """
    base_lang = target_lang.split("-")[0] if "-" in target_lang else target_lang

    if base_lang in NLLB_ONLY_LANGUAGES:
        return "nllb200"

    if base_lang in TLLM_SUPPORTED_TARGETS or target_lang in TLLM_SUPPORTED_TARGETS:
        return "google_tllm"

    # Default to NLLB-200 for unknown languages
    return "nllb200"


def get_nllb_code(lang_code: str) -> str:
    """Map ISO language code to NLLB-200 flores-200 code."""
    base = lang_code.split("-")[0] if "-" in lang_code else lang_code
    return NLLB_LANG_CODES.get(base, "eng_Latn")


def get_tts_locale(lang_code: str) -> str:
    """Map language code to Google Cloud TTS locale."""
    base = lang_code.split("-")[0] if "-" in lang_code else lang_code
    return TTS_VOICE_MAP.get(base, "en-US")


def get_language_name(lang_code: str) -> str:
    """Get human-readable name for a language code."""
    return LANGUAGE_NAMES.get(lang_code, lang_code)
