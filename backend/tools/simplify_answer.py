# NOTE: Genkit orchestration has migrated to genkit-server/ (TypeScript).
# This file is retained as logic reference and documentation only.
# The FastAPI endpoints called by the Genkit TS tools are in genkit-server/src/tools/.
"""
Genkit tool: simplify_answer
Wraps Flesch-Kincaid grading + spaCy NER + LLM jargon replacement
from services/simplifier.py, with optional Hijri date enrichment
from services/hijri_service.py.

enrich_hijri=True only on the first simplification pass in the flow.
The conservative retry pass sets enrich_hijri=False to match the
behaviour of the original query.py pipeline.
"""
from __future__ import annotations

from pydantic import BaseModel

from genkit_config import ai
from services.simplifier import simplify_text as _simplify_text
from services.hijri_service import enrich_text_with_hijri


class SimplifyAnswerInput(BaseModel):
    text: str
    language: str = "English"    # human-readable language name for the LLM prompt
    conservative: bool = False   # True = preserve meaning strictly, minimal rewrite
    enrich_hijri: bool = False   # True = annotate Gregorian dates with Hijri equivalents


class SimplifyAnswerOutput(BaseModel):
    simplified_text: str
    readability_grade: float  # Flesch-Kincaid grade level of the output


@ai.tool(
    name="simplify_answer",
    description=(
        "Simplify an answer to a Grade 5–7 reading level using spaCy NER for jargon "
        "extraction and an LLM rewrite pass. If the text is already ≤ Grade 7 it is "
        "returned unchanged. The conservative mode only restructures sentences without "
        "altering meaning, used for the semantic-score retry pass. "
        "Optionally annotates Gregorian dates with their Hijri equivalents inline."
    ),
)
async def simplify_answer_tool(input: SimplifyAnswerInput) -> SimplifyAnswerOutput:
    simplified, grade = await _simplify_text(
        text=input.text,
        language=input.language,
        conservative=input.conservative,
    )
    if input.enrich_hijri:
        simplified = enrich_text_with_hijri(simplified)
    return SimplifyAnswerOutput(simplified_text=simplified, readability_grade=grade)
