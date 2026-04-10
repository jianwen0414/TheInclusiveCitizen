# NOTE: Genkit orchestration has migrated to genkit-server/ (TypeScript).
# This file is retained as logic reference and documentation only.
# The FastAPI endpoints called by the Genkit TS tools are in genkit-server/src/tools/.
"""
Genkit tool: translate_answer
Wraps tiered translation from services/translation_service.py.

Tier 1: Google Cloud Translation Advanced v3 (high-resource languages).
Tier 2: NLLB-200 distilled-600M (low-resource / fallback).

This tool is only called when target_lang is NOT in LLM_DIRECT_LANGUAGES —
for high-resource languages the LLM generates directly in the target language.
The standalone /api/translate endpoint calls the service function directly.
"""
from __future__ import annotations

from pydantic import BaseModel

from genkit_config import ai
from services.translation_service import translate_text as _translate_text


class TranslateAnswerInput(BaseModel):
    text: str
    source_lang: str = "en"
    target_lang: str = "ms"


class TranslateAnswerOutput(BaseModel):
    translated_text: str
    translation_model: str  # "google_tllm" or "nllb200"


@ai.tool(
    name="translate_answer",
    description=(
        "Translate an answer to the target language using Google Cloud TLLM (Tier 1) "
        "or NLLB-200 (Tier 2 fallback for low-resource languages). "
        "Only invoked when the LLM cannot generate reliably in the target language directly."
    ),
)
async def translate_answer_tool(input: TranslateAnswerInput) -> TranslateAnswerOutput:
    translated, model_used = await _translate_text(
        text=input.text,
        source_lang=input.source_lang,
        target_lang=input.target_lang,
    )
    return TranslateAnswerOutput(
        translated_text=translated,
        translation_model=model_used,
    )
