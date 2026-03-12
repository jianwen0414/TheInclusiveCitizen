"""
Semantic Preservation Score — Cross-Lingual Validation
PRD Section 5.1, F05:
  Uses sentence-transformers (paraphrase-multilingual-MiniLM-L12-v2)
  to compute cross-lingual cosine similarity between:
    - Original BM retrieved chunk
    - Final translated + simplified output
  Threshold: ≥ 0.90 required before answer is displayed.
PRD Constraint #5: Comparison is cross-lingual (BM vs target language).
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

_st_model = None
SCORE_THRESHOLD = 0.90
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
    original_bm_text: str,
    translated_simplified_text: str,
) -> float:
    """
    Compute cross-lingual semantic similarity between original BM text
    and final translated+simplified output.
    PRD F05: cosine similarity using paraphrase-multilingual-MiniLM-L12-v2.
    """
    if not original_bm_text or not translated_simplified_text:
        return 0.0

    try:
        model = _load_model()
        from sentence_transformers import util

        emb_original = model.encode(original_bm_text, convert_to_tensor=True)
        emb_translated = model.encode(translated_simplified_text, convert_to_tensor=True)

        similarity = util.cos_sim(emb_original, emb_translated).item()
        return max(0.0, min(1.0, similarity))

    except Exception as exc:
        logger.error(f"Semantic scoring failed: {exc}")
        return 0.0


def passes_threshold(score: float) -> bool:
    """Check if semantic score meets the ≥ 0.90 threshold."""
    return score >= SCORE_THRESHOLD
