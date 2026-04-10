# NOTE: Genkit orchestration has migrated to genkit-server/ (TypeScript).
# This file is retained as logic reference and documentation only.
# The FastAPI endpoints called by the Genkit TS tools are in genkit-server/src/tools/.
"""
Genkit tool: compute_semantic_score
Wraps cross-lingual cosine similarity scoring from services/semantic_scorer.py.

Uses paraphrase-multilingual-MiniLM-L12-v2 (loaded eagerly at startup).
The underlying compute_semantic_score() is synchronous — called directly
without await inside this async tool wrapper.

Note: Future improvement — wrap in asyncio.to_thread() to avoid blocking the
event loop during the encode() call. Out of scope for current refactor.
"""
from __future__ import annotations

from pydantic import BaseModel

from genkit_config import ai
from services.semantic_scorer import compute_semantic_score as _compute_semantic_score


class ComputeSemanticScoreInput(BaseModel):
    original_bm_text: str           # raw retrieved chunk (BM source)
    translated_simplified_text: str  # final answer after translation + simplification


class ComputeSemanticScoreOutput(BaseModel):
    score: float  # cosine similarity 0.0–1.0


@ai.tool(
    name="compute_semantic_score",
    description=(
        "Compute cross-lingual semantic similarity between the original BM source chunk "
        "and the final translated + simplified answer using "
        "paraphrase-multilingual-MiniLM-L12-v2. Returns a cosine similarity score "
        "between 0.0 and 1.0. Scores below 0.45 for ms/en/id trigger a conservative "
        "simplification retry."
    ),
)
async def compute_semantic_score_tool(
    input: ComputeSemanticScoreInput,
) -> ComputeSemanticScoreOutput:
    # Synchronous call — no await needed
    score = _compute_semantic_score(
        original_bm_text=input.original_bm_text,
        translated_simplified_text=input.translated_simplified_text,
    )
    return ComputeSemanticScoreOutput(score=score)
