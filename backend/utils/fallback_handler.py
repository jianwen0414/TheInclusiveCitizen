"""
Fallback Handler
PRD Section 13 (Table 16): Risk mitigations for API failures.
Manages LLM and translation fallback chains.
"""

from __future__ import annotations

import logging
from typing import Callable, TypeVar, Any

logger = logging.getLogger(__name__)

T = TypeVar("T")


async def with_fallback(
    primary: Callable[..., Any],
    fallback: Callable[..., Any],
    *args: Any,
    primary_name: str = "primary",
    fallback_name: str = "fallback",
    **kwargs: Any,
) -> tuple[Any, str]:
    """
    Try the primary callable; on failure, fall back to the secondary.
    Returns (result, model_name_used).
    """
    try:
        result = await primary(*args, **kwargs)
        return result, primary_name
    except Exception as exc:
        logger.warning(
            f"{primary_name} failed ({exc}), falling back to {fallback_name}"
        )
        try:
            result = await fallback(*args, **kwargs)
            return result, fallback_name
        except Exception as fallback_exc:
            logger.error(f"Both {primary_name} and {fallback_name} failed")
            raise fallback_exc


class FallbackChain:
    """
    Manages a chain of fallback services with automatic failover.
    PRD: Gemini 2.0 Flash → SEA-LION v4 (optional BM specialist) for LLM
    PRD: Google Cloud TLLM → NLLB-200 for translation
    """

    def __init__(self):
        self._llm_fallback_active = False
        self._translation_fallback_active = False

    @property
    def llm_fallback_active(self) -> bool:
        return self._llm_fallback_active

    @llm_fallback_active.setter
    def llm_fallback_active(self, value: bool):
        self._llm_fallback_active = value

    @property
    def translation_fallback_active(self) -> bool:
        return self._translation_fallback_active

    @translation_fallback_active.setter
    def translation_fallback_active(self, value: bool):
        self._translation_fallback_active = value


fallback_state = FallbackChain()
