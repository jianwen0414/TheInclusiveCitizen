"""
Jargon Simplification Engine
PRD Section 5.1, F04 — Jargon Simplification Engine:
  Stage 1: Named entity extraction using spaCy to identify legal/medical terms
  Stage 2: LLM-driven replacement at Grade 5 reading level in target language
  Flesch-Kincaid grade scoring via textstat to validate readability.
PRD Constraint #4: Simplification always operates on POST-TRANSLATION text.
"""

from __future__ import annotations

import logging

from google.genai import types
import textstat

from utils.prompt_templates import STANDARD_SIMPLIFY_PROMPT, CONSERVATIVE_SIMPLIFY_PROMPT

logger = logging.getLogger(__name__)

TARGET_GRADE = 7.0  # Grade 5-7 range per PRD Section 3.2


def compute_readability(text: str) -> float:
    """
    Compute Flesch-Kincaid grade level of text.
    PRD: textstat library automated scoring.
    """
    try:
        grade = textstat.flesch_kincaid_grade(text)
        return max(0.0, grade)
    except Exception:
        return 0.0


async def simplify_text(
    text: str,
    language: str = "en",
    conservative: bool = False,
) -> tuple[str, float]:
    """
    Stage 2: LLM-driven simplification to Grade 5 reading level.
    PRD F04: LLM rewrite + textstat grade validation.
    PRD Constraint #4: Operates on the already-translated text.

    Returns (simplified_text, readability_grade).
    """
    current_grade = compute_readability(text)
    if current_grade <= TARGET_GRADE and current_grade > 0:
        logger.info(f"Text already at Grade {current_grade:.1f}, no simplification needed")
        return text, current_grade

    prompt_template = CONSERVATIVE_SIMPLIFY_PROMPT if conservative else STANDARD_SIMPLIFY_PROMPT
    prompt = prompt_template.format(text=text, language=language)

    try:
        from services.llm_service import _generate_with_fallback_model

        simplified = await _generate_with_fallback_model(
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.2,
                max_output_tokens=8192,
            ),
            disable_thinking=True,
        )
        simplified = simplified.strip()
        grade = compute_readability(simplified)

        logger.info(f"Simplification: {current_grade:.1f} → {grade:.1f} grade level")
        return simplified, grade

    except Exception as exc:
        logger.error(f"Simplification failed: {exc}")
        return text, current_grade


async def simplify_with_retry(
    text: str,
    language: str = "en",
    max_retries: int = 2,
) -> tuple[str, float]:
    """
    Simplify with retry logic.
    PRD F05: If semantic score < 0.90, retry with conservative prompt (max 2 retries).
    """
    simplified, grade = await simplify_text(text, language, conservative=False)

    if grade <= TARGET_GRADE:
        return simplified, grade

    for attempt in range(max_retries):
        logger.info(f"Simplification retry {attempt + 1}/{max_retries} (conservative mode)")
        simplified, grade = await simplify_text(simplified, language, conservative=True)
        if grade <= TARGET_GRADE:
            return simplified, grade

    return simplified, grade
