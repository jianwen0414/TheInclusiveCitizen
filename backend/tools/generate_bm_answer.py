# NOTE: Genkit orchestration has migrated to genkit-server/ (TypeScript).
# This file is retained as logic reference and documentation only.
# The FastAPI endpoints called by the Genkit TS tools are in genkit-server/src/tools/.
"""
Genkit tool: generate_bm_answer
Wraps LLM answer generation from services/llm_service.py.

Primary: Gemini 2.0 Flash via Vertex AI (with model fallback chain).
Secondary: SEA-LION v4 BM specialist (only if SEALION_API_KEY is configured
           and target dialect is Bahasa Malaysia).

Despite the name (kept for historical consistency), this tool generates the
answer directly in the user's target language — not solely in BM.
"""
from __future__ import annotations

from pydantic import BaseModel

from genkit_config import ai
from services.llm_service import generate_answer as _generate_answer


class GenerateBmAnswerInput(BaseModel):
    context: str
    query: str
    target_lang: str = "ms"
    dialect_code: str = "ms"


class GenerateBmAnswerOutput(BaseModel):
    answer: str
    llm_model: str  # e.g. "gemini-2.0-flash", "sealion-v4"


@ai.tool(
    name="generate_bm_answer",
    description=(
        "Generate a grounded answer in the user's target language using Gemini 2.0 Flash "
        "(primary) or SEA-LION v4 BM specialist (fallback for Malay dialects). "
        "The answer is strictly grounded in the provided context — no parametric knowledge. "
        "Returns the answer text and the model ID that produced it."
    ),
)
async def generate_bm_answer_tool(
    input: GenerateBmAnswerInput,
) -> GenerateBmAnswerOutput:
    answer, llm_model = await _generate_answer(
        context=input.context,
        query=input.query,
        target_lang=input.target_lang,
        dialect_code=input.dialect_code,
    )
    return GenerateBmAnswerOutput(answer=answer, llm_model=llm_model)
