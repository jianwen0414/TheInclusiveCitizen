# NOTE: Genkit orchestration has migrated to genkit-server/ (TypeScript).
# This file is retained as logic reference and documentation only.
# The FastAPI endpoints called by the Genkit TS tools are in genkit-server/src/tools/.
"""
Genkit tool: compute_semantic_score
Wraps simplification fidelity scoring from services/semantic_scorer.py.

Compares the LLM-generated answer (before simplification) against the simplified
answer (after simplification). Both inputs are in the same target language,
making scoring independent of source document language.

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
    source_text: str      # LLM-generated answer before simplification (target language)
    simplified_text: str  # simplified answer after simplification (same target language)


class ComputeSemanticScoreOutput(BaseModel):
    score: float  # cosine similarity 0.0–1.0


@ai.tool(
    name="compute_semantic_score",
    description=(
        "Compute simplification fidelity: cosine similarity between the LLM-generated "
        "answer (before simplification) and the simplified answer (after simplification) "
        "using paraphrase-multilingual-MiniLM-L12-v2. Both inputs are in the same target "
        "language. Returns a score between 0.0 and 1.0. Scores below 0.70 for ms/en/id "
        "trigger a conservative simplification retry."
    ),
)
async def compute_semantic_score_tool(
    input: ComputeSemanticScoreInput,
) -> ComputeSemanticScoreOutput:
    # Synchronous call — no await needed
    score = _compute_semantic_score(
        source_text=input.source_text,
        simplified_text=input.simplified_text,
    )
    return ComputeSemanticScoreOutput(score=score)
