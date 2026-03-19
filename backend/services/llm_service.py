"""
LLM Service — SEA-LION v4 (primary) + Gemini 3 Flash Preview (fallback)
SEA-LION model name per https://docs.sea-lion.ai/guides/inferencing/api:
  "aisingapore/Gemma-SEA-LION-v4-27B-IT"
Gemini fallback model per https://cloud.google.com/vertex-ai/generative-ai/docs/models/gemini/3-flash:
  "gemini-3-flash-preview" — available in location "global" ONLY (not us-central1)
PRD Constraint #1: LLM must only answer from retrieved context.

Adapted: prompts are now bilingual-aware — the LLM generates answers directly
in the user's language from whatever language the context is in.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import httpx
from google import genai
from google.genai import types

from utils.prompt_templates import (
    build_system_prompt,
    build_user_prompt,
    DIALECT_PROMPTS,
    STEP_EXTRACTION_PROMPT,
)
from utils.fallback_handler import fallback_state
from utils.language_router import get_language_name

logger = logging.getLogger(__name__)


# ── SEA-LION v4 (Primary LLM) ───────────────────────────

async def generate_answer_sealion(
    context: str,
    query: str,
    answer_language: str = "Bahasa Malaysia",
    dialect_code: str = "ms",
) -> str:
    api_key = os.getenv("SEALION_API_KEY", "")
    api_base = os.getenv("SEALION_API_BASE_URL", "https://api.sea-lion.ai/v1")

    system_prompt = DIALECT_PROMPTS.get(dialect_code, build_system_prompt(answer_language))
    user_prompt = build_user_prompt(context, query, answer_language)

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{api_base}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "aisingapore/Gemma-SEA-LION-v4-27B-IT",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": 0.3,
                "max_tokens": 2048,
            },
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]


# ── Gemini fallback chain ────────────────────────────────
# Use alias names (no -001 suffix) so Vertex AI always resolves to the
# latest stable version. Only gemini-3-flash-preview needs explicit preview.
GEMINI_MODELS_PRIORITY = [
    "gemini-3-flash-preview",
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-1.5-flash",
]


def _get_gemini_client() -> genai.Client:
    project = os.getenv("GOOGLE_CLOUD_PROJECT", "")
    os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "True")
    return genai.Client(
        vertexai=True,
        project=project,
        location="global",
    )


async def _generate_with_fallback_model(
    client: genai.Client,
    contents: str,
    config: types.GenerateContentConfig,
) -> str:
    last_exc: Exception | None = None
    for model_name in GEMINI_MODELS_PRIORITY:
        # Retry this model once on 429 (rate limit) with a short backoff
        # before giving up and moving to the next model.
        for attempt in range(2):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=contents,
                    config=config,
                )
                return response.text
            except Exception as exc:
                err_str = str(exc)
                is_rate_limited = "429" in err_str or "RESOURCE_EXHAUSTED" in err_str
                if is_rate_limited and attempt == 0:
                    logger.warning(
                        f"Gemini model {model_name} rate-limited (429); "
                        "waiting 3 s before retry…"
                    )
                    await asyncio.sleep(3)
                    continue
                logger.warning(f"Gemini model {model_name} failed: {exc}")
                last_exc = exc
                break
    raise last_exc  # type: ignore


async def generate_answer_gemini(
    context: str,
    query: str,
    answer_language: str = "Bahasa Malaysia",
    dialect_code: str = "ms",
) -> str:
    client = _get_gemini_client()
    system_prompt = DIALECT_PROMPTS.get(dialect_code, build_system_prompt(answer_language))
    user_prompt = build_user_prompt(context, query, answer_language)

    return await _generate_with_fallback_model(
        client,
        contents=user_prompt,
            config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.3,
            max_output_tokens=2048,
        ),
    )


# ── Unified Generate with Fallback ───────────────────────

async def generate_answer(
    context: str,
    query: str,
    target_lang: str = "ms",
    dialect_code: str = "ms",
) -> tuple[str, bool]:
    """
    Generate answer in the user's target language directly.
    Returns (answer_text, is_fallback_used).
    """
    answer_language = get_language_name(target_lang)

    try:
        answer = await generate_answer_sealion(context, query, answer_language, dialect_code)
        fallback_state.llm_fallback_active = False
        return answer, False
    except Exception as exc:
        logger.warning(f"SEA-LION v4 failed ({exc}), falling back to Gemini 3 Flash")
        fallback_state.llm_fallback_active = True
        answer = await generate_answer_gemini(context, query, answer_language, dialect_code)
        return answer, True


# Legacy alias for backward compat
async def generate_bm_answer(
    context: str,
    query: str,
    dialect_code: str = "ms",
) -> tuple[str, bool]:
    return await generate_answer(context, query, target_lang="ms", dialect_code=dialect_code)


# ── Step Extraction ──────────────────────────────────────

def _parse_json_lenient(text: str) -> dict:
    """Parse JSON from LLM output, tolerating markdown fences and trailing content."""
    text = text.strip()
    if "```" in text:
        parts = text.split("```")
        for part in parts[1:]:
            candidate = part.strip()
            if candidate.startswith("json"):
                candidate = candidate[4:].strip()
            candidate = candidate.rstrip("`").strip()
            if candidate:
                text = candidate
                break

    # Find the outermost { ... }
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        text = text[start:end + 1]

    return json.loads(text)


def _extract_steps_regex(text: str) -> tuple[list[str], list[str]]:
    """
    Last-resort regex extractor: pull numbered list items from plain text.
    Works on both Malay and English step lists produced by the LLM when
    JSON output is malformed.
    """
    # Match "1. ...", "2) ...", "Langkah 1: ..." etc.
    patterns = [
        r"(?:^|\n)\s*(?:Langkah\s+)?\d+[\.\):\s]\s*(.+?)(?=\n\s*(?:Langkah\s+)?\d+[\.\):\s]|\Z)",
        r"(?:^|\n)\s*[-•*]\s*(.+?)(?=\n\s*[-•*]|\Z)",
    ]
    for pattern in patterns:
        matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
        steps = [m.strip().replace("\n", " ") for m in matches if m.strip()]
        if len(steps) >= 2:
            icons = ["CheckCircle"] * len(steps)
            return steps, icons
    return [], []


async def extract_steps(answer: str) -> tuple[list[str], list[str]]:
    """
    Extract step-by-step instructions from an answer using Gemini.
    PRD F09: Visual step-by-step instruction cards.

    Robustness layers (in order):
      1. Gemini structured output (response_mime_type=application/json)
         guarantees syntactically valid JSON from the model.
      2. _parse_json_lenient — handles markdown fences / extra text if the
         first model in the fallback chain doesn't support structured output.
      3. _extract_steps_regex — pulls numbered steps from plain text as a
         last resort so the caller always gets *something* useful.
    """
    try:
        client = _get_gemini_client()
        prompt = STEP_EXTRACTION_PROMPT.format(answer=answer)

        # Layer 1: structured JSON output — Gemini is constrained by the
        # model to emit only valid JSON, eliminating parse errors at source.
        try:
            text = await _generate_with_fallback_model(
                client,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.1,
                    max_output_tokens=1024,
                    response_mime_type="application/json",
                ),
            )
        except Exception as structured_exc:
            # Some older models in the fallback chain may not support
            # response_mime_type; fall back to plain generation.
            logger.debug(
                f"Structured JSON output unavailable ({structured_exc}); "
                "retrying without mime constraint"
            )
            text = await _generate_with_fallback_model(
                client,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.1,
                    max_output_tokens=1024,
                ),
            )

        # Layer 2: lenient JSON parser
        try:
            data = _parse_json_lenient(text)
            steps = data.get("steps", [])
            icons = data.get("step_icons", [])
            if steps:
                while len(icons) < len(steps):
                    icons.append("CheckCircle")
                return steps, icons
        except Exception as json_exc:
            logger.debug(f"Lenient JSON parse failed ({json_exc}); trying regex fallback")

        # Layer 3: regex extraction from the raw LLM text
        steps, icons = _extract_steps_regex(text)
        if steps:
            logger.info(f"Step extraction recovered {len(steps)} steps via regex fallback")
            return steps, icons

        logger.debug("Step extraction: no steps found in answer (answer may not be procedural)")
        return [], []

    except Exception as exc:
        logger.warning(f"Step extraction failed: {exc}")
        return [], []
