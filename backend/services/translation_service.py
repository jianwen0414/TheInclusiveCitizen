"""
Translation Service — Google Cloud TLLM (primary) + NLLB-200 (fallback)
PRD Section 5.1, F03b — Tiered Translation Layer:
  Tier 1: Google Cloud Translation Advanced v3 TLLM
  Tier 2: NLLB-200-distilled-600M for low-resource dialects
PRD Section 6.3 step 6: Route to translation tier based on target language.
"""

from __future__ import annotations

import logging
import os
from functools import lru_cache

from utils.language_router import get_translation_tier, get_nllb_code
from utils.fallback_handler import fallback_state

logger = logging.getLogger(__name__)

_nllb_model = None
_nllb_tokenizer = None


# ── Google Cloud Translation TLLM (Tier 1) ──────────────

async def translate_with_google_tllm(
    text: str,
    source_lang: str = "ms",
    target_lang: str = "en",
) -> str:
    """
    Translate using Google Cloud Translation Advanced v3 (TLLM).
    PRD: Primary translation engine for high-resource SEA language pairs.
    """
    from google.cloud import translate_v3 as translate

    project = os.getenv("GOOGLE_CLOUD_PROJECT", "")
    parent = f"projects/{project}/locations/global"

    client = translate.TranslationServiceClient()

    response = client.translate_text(
        request={
            "parent": parent,
            "contents": [text],
            "source_language_code": source_lang,
            "target_language_code": target_lang,
            "mime_type": "text/plain",
        }
    )

    return response.translations[0].translated_text


# ── NLLB-200 (Tier 2 — Fallback) ────────────────────────

def _load_nllb_model():
    """Lazy-load NLLB-200-distilled-600M model."""
    global _nllb_model, _nllb_tokenizer

    if _nllb_model is not None:
        return _nllb_model, _nllb_tokenizer

    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

    model_path = os.getenv("NLLB_MODEL_PATH", "facebook/nllb-200-distilled-600M")
    logger.info(f"Loading NLLB-200 model from {model_path}...")

    _nllb_tokenizer = AutoTokenizer.from_pretrained(model_path)
    _nllb_model = AutoModelForSeq2SeqLM.from_pretrained(model_path)

    logger.info("NLLB-200 model loaded successfully")
    return _nllb_model, _nllb_tokenizer


async def translate_with_nllb(
    text: str,
    source_lang: str = "ms",
    target_lang: str = "en",
) -> str:
    """
    Translate using NLLB-200-distilled-600M.
    PRD: Activated for ultra-low-resource dialects (Iban, Kadazan, Bajau).
    """
    model, tokenizer = _load_nllb_model()

    src_code = get_nllb_code(source_lang)
    tgt_code = get_nllb_code(target_lang)

    tokenizer.src_lang = src_code
    inputs = tokenizer(text, return_tensors="pt", max_length=512, truncation=True)

    tgt_lang_id = tokenizer.convert_tokens_to_ids(tgt_code)

    translated_tokens = model.generate(
        **inputs,
        forced_bos_token_id=tgt_lang_id,
        max_new_tokens=512,
    )

    return tokenizer.batch_decode(translated_tokens, skip_special_tokens=True)[0]


# ── Unified Translation with Tier Routing ────────────────

async def translate_text(
    text: str,
    source_lang: str = "ms",
    target_lang: str = "en",
) -> tuple[str, str]:
    """
    Translate text using the appropriate tier.
    PRD F03b routing logic: dialect_code → check TLLM support → route.
    Returns (translated_text, model_used).
    """
    if source_lang == target_lang:
        return text, "none"

    tier = get_translation_tier(target_lang)

    if tier == "google_tllm":
        try:
            translated = await translate_with_google_tllm(text, source_lang, target_lang)
            fallback_state.translation_fallback_active = False
            return translated, "google_tllm"
        except Exception as exc:
            logger.warning(f"Google TLLM failed ({exc}), falling back to NLLB-200")
            fallback_state.translation_fallback_active = True
            translated = await translate_with_nllb(text, source_lang, target_lang)
            return translated, "nllb200"
    else:
        fallback_state.translation_fallback_active = True
        translated = await translate_with_nllb(text, source_lang, target_lang)
        return translated, "nllb200"
