"""
LLM Service — SEA-LION v4 (primary) + Gemini 3 Flash (fallback)
PRD Section 6.3 step 5: Pass retrieved BM context + prompt to SEA-LION v4
  to generate answer in BM. If SEA-LION unavailable, auto-fallback to
  Gemini 3 Flash (gemini-3-flash-preview).
PRD Constraint #1: LLM must only answer from retrieved context.
"""

from __future__ import annotations

import json
import logging
import os

import httpx
import google.generativeai as genai

from utils.prompt_templates import (
    GROUNDED_BM_SYSTEM_PROMPT,
    GROUNDED_BM_USER_TEMPLATE,
    STEP_EXTRACTION_PROMPT,
    DIALECT_PROMPTS,
)
from utils.fallback_handler import fallback_state

logger = logging.getLogger(__name__)


# ── SEA-LION v4 (Primary LLM) ───────────────────────────

async def generate_answer_sealion(
    context: str,
    query: str,
    dialect_code: str = "ms",
) -> str:
    """
    Generate BM answer using SEA-LION v4 API (AI Singapore).
    PRD: SEA-LION v4 generates answer in BM from retrieved context.
    """
    api_key = os.getenv("SEALION_API_KEY", "")
    api_base = os.getenv("SEALION_API_BASE_URL", "https://api.sea-lion.ai/v1")

    system_prompt = DIALECT_PROMPTS.get(dialect_code, GROUNDED_BM_SYSTEM_PROMPT)
    user_prompt = GROUNDED_BM_USER_TEMPLATE.format(context=context, query=query)

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{api_base}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "sea-lion-v4",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": 0.3,
                "max_tokens": 1024,
            },
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]


# ── Gemini 3 Flash (Fallback LLM) ───────────────────────

async def generate_answer_gemini(
    context: str,
    query: str,
    dialect_code: str = "ms",
) -> str:
    """
    Fallback: Generate BM answer using Gemini 3 Flash via Vertex AI.
    PRD: Activates when SEA-LION API is unavailable.
    """
    project = os.getenv("GOOGLE_CLOUD_PROJECT")
    genai.configure(
        client_options={"api_endpoint": "us-central1-aiplatform.googleapis.com"},
        default_metadata=[("x-goog-user-project", project)] if project else [],
    )

    system_prompt = DIALECT_PROMPTS.get(dialect_code, GROUNDED_BM_SYSTEM_PROMPT)
    user_prompt = GROUNDED_BM_USER_TEMPLATE.format(context=context, query=query)

    model = genai.GenerativeModel(
        "gemini-3-flash-preview",
        system_instruction=system_prompt,
    )
    response = model.generate_content(
        user_prompt,
        generation_config=genai.GenerationConfig(
            temperature=0.3,
            max_output_tokens=1024,
        ),
    )
    return response.text


# ── Unified Generate with Fallback ───────────────────────

async def generate_bm_answer(
    context: str,
    query: str,
    dialect_code: str = "ms",
) -> tuple[str, bool]:
    """
    Generate BM answer using SEA-LION v4 with Gemini 3 Flash fallback.
    Returns (answer_text, is_fallback_used).
    PRD Section 13: SEA-LION v4 API downtime → Gemini 3 Flash auto-activates.
    """
    try:
        answer = await generate_answer_sealion(context, query, dialect_code)
        fallback_state.llm_fallback_active = False
        return answer, False
    except Exception as exc:
        logger.warning(f"SEA-LION v4 failed ({exc}), falling back to Gemini 3 Flash")
        fallback_state.llm_fallback_active = True
        answer = await generate_answer_gemini(context, query, dialect_code)
        return answer, True


# ── Step Extraction ──────────────────────────────────────

async def extract_steps(answer: str) -> tuple[list[str], list[str]]:
    """
    Extract step-by-step instructions from an answer using Gemini.
    PRD F09: Visual step-by-step instruction cards.
    Returns (steps, step_icons).
    """
    try:
        project = os.getenv("GOOGLE_CLOUD_PROJECT")
        genai.configure(
            client_options={"api_endpoint": "us-central1-aiplatform.googleapis.com"},
            default_metadata=[("x-goog-user-project", project)] if project else [],
        )

        model = genai.GenerativeModel("gemini-3-flash-preview")
        prompt = STEP_EXTRACTION_PROMPT.format(answer=answer)
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                temperature=0.1,
                max_output_tokens=512,
            ),
        )

        text = response.text.strip()
        # Parse JSON from response (handle markdown code blocks)
        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
            text = text.strip()

        data = json.loads(text)
        return data.get("steps", []), data.get("step_icons", [])
    except Exception as exc:
        logger.warning(f"Step extraction failed: {exc}")
        return [], []
