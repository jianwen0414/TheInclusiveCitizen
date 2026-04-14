"""
Semantic Preservation Score — Simplification Fidelity Validation
PRD Section 5.1, F05:
  Uses sentence-transformers (paraphrase-multilingual-MiniLM-L12-v2)
  to compute cosine similarity between:
    - LLM-generated answer (before simplification, in target language)
    - Final simplified output (same target language)
  Threshold: ≥ 0.70 triggers a conservative-simplification retry.

  Scoring anchor is always same-language (LLM answer vs. simplified answer),
  so calibration is independent of source document language. This handles BM,
  English, and any future document language without threshold changes.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

_st_model = None
# paraphrase-multilingual-MiniLM-L12-v2 same-language simplification scores:
#   faithful simplification: 0.75–0.92
#   over-simplified (grade-level gap > 4): 0.50–0.70
# Threshold of 0.70 catches aggressive simplifications that strip meaning
# while avoiding false-positive retries on well-simplified answers.
SCORE_THRESHOLD = 0.70
MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"


def _load_model():
    global _st_model
    if _st_model is not None:
        return _st_model

    try:
        from sentence_transformers import SentenceTransformer

        logger.info(f"Loading sentence-transformers model: {MODEL_NAME}")
        _st_model = SentenceTransformer(MODEL_NAME)
        logger.info("Sentence-transformers model loaded")
        return _st_model
    except Exception as exc:
        logger.error(f"Failed to load sentence-transformers model: {exc}")
        raise


def compute_semantic_score(
    source_text: str,
    simplified_text: str,
) -> float:
    """
    Compute simplification fidelity: cosine similarity between the LLM-generated
    answer (before simplification) and the simplified answer (after simplification).
    Both inputs are in the same target language, making the comparison
    language-agnostic and correctly calibrated for any source document language.
    PRD F05: cosine similarity using paraphrase-multilingual-MiniLM-L12-v2.
    """
    if not source_text or not simplified_text:
        return 0.0

    try:
        model = _load_model()
        from sentence_transformers import util

        emb_source = model.encode(source_text, convert_to_tensor=True)
        emb_simplified = model.encode(simplified_text, convert_to_tensor=True)

        similarity = util.cos_sim(emb_source, emb_simplified).item()
        return max(0.0, min(1.0, similarity))

    except Exception as exc:
        logger.error(f"Semantic scoring failed: {exc}")
        return 0.0


def passes_threshold(score: float) -> bool:
    """Check if simplification fidelity score meets the ≥ 0.70 threshold."""
    return score >= SCORE_THRESHOLD
