# NOTE: Genkit orchestration has migrated to genkit-server/ (TypeScript).
# This file is retained as logic reference and documentation only.
# The FastAPI endpoints called by the Genkit TS tools are in genkit-server/src/tools/.
"""
Genkit tool: detect_dialect
Wraps dialect detection logic from services/dialect_detector.py.

Mirrors the exact branching in routers/query.py lines 76–98:
  - If language_hint is provided (e.g. from STT), skip the full lingua-py pipeline
    and run only the fast text-based sub-dialect check.
  - Otherwise, run the full detect_dialect() pipeline.
"""
from __future__ import annotations

from pydantic import BaseModel

from genkit_config import ai
from services.dialect_detector import (
    detect_dialect as _detect_dialect,
    detect_javanese_from_text,
    detect_malay_dialect,
)


class DetectDialectInput(BaseModel):
    query: str
    language_hint: str | None = None  # pre-detected language code (e.g. from STT)


class DetectDialectOutput(BaseModel):
    detected_language: str  # ISO code, possibly with dialect suffix e.g. "ms-kelantanese"
    target_lang: str        # base language code without dialect suffix e.g. "ms"


@ai.tool(
    name="detect_dialect",
    description=(
        "Detect the language and Malay sub-dialect of a query string. "
        "Returns an ISO language code (e.g. 'ms', 'ms-kelantanese', 'jv', 'en') as "
        "detected_language, and the base language code as target_lang. "
        "If language_hint is provided (e.g. from STT output), only sub-dialect "
        "refinement is performed to save latency."
    ),
)
async def detect_dialect_tool(input: DetectDialectInput) -> DetectDialectOutput:
    query = input.query

    if input.language_hint:
        detected_language = input.language_hint
        if detected_language == "ms":
            sub_dialect = detect_malay_dialect(query)
            if sub_dialect:
                detected_language = sub_dialect
        elif detected_language == "id":
            # STT often labels Javanese speech as Indonesian; refine from transcript
            if detect_javanese_from_text(query):
                detected_language = "jv"
            else:
                sub_dialect = detect_malay_dialect(query)
                if sub_dialect:
                    detected_language = sub_dialect
    else:
        detected_language = await _detect_dialect(query)

    target_lang = (
        detected_language.split("-")[0]
        if "-" in detected_language
        else detected_language
    )
    return DetectDialectOutput(
        detected_language=detected_language,
        target_lang=target_lang,
    )
