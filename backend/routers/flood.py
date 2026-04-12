"""
POST /api/detect-flood-intent — Classify a query for flood intent.

Uses keyword matching across Bahasa Malaysia, English, and major SEA
languages. Returns deterministic results in < 1 ms with no I/O.

Replaces the previous Gemini-based classifier which suffered from
partial SSE responses on the Vertex AI global endpoint (google-genai
v1.67.0 sync SDK only reads the first SSE frame from the transport
layer regardless of whether generate_content or generate_content_stream
is called).
"""
from __future__ import annotations

import ast
import json
import logging
import re

from fastapi import APIRouter

from models.schemas import FloodIntentRequest, FloodIntentResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["flood"])

_SAFE_DEFAULT = FloodIntentResponse(
    is_flood_related=False, situation_type=None, confidence=0.0
)

# ── Keyword sets ──────────────────────────────────────────────────────────────
# All entries are lowercase. Matching is case-insensitive substring search
# against query.lower().

_FLOOD_KEYWORDS: frozenset[str] = frozenset({
    # Bahasa Malaysia — standard
    "banjir", "kebanjiran", "banjir kilat", "banjir lumpur",
    "banjir bandang", "banjir besar", "banjir bah",
    "air bah", "air naik", "air pasang", "air meluap",
    "limpah", "melimpah", "meluap", "limpahan",
    "mangsa banjir", "kawasan banjir", "bencana banjir",
    # Evacuation / shelter
    "pusat pemindahan", "pusat evakuasi", "tempat perlindungan banjir",
    "pusat relief", "kem bantuan",
    "evakuasi", "dipindahkan", "pemindahan",
    # Aid / response agencies
    "bantuan banjir", "bantuan mangsa", "mangsa bencana",
    "nadma", "jps", "jkm", "apam",
    "jabatan pengairan", "angkatan pertahanan awam",
    # Warning / water level
    "amaran banjir", "paras air bahaya", "paras air kritikal", "paras banjir",
    # English
    "flood", "flooding", "flooded", "floods", "flash flood",
    "inundation", "inundated", "submerged", "waterlogged",
    "evacuate", "evacuation", "evacuated", "evacuation centre", "evacuation center",
    "flood relief", "flood aid", "flood emergency",
    "flood warning", "flood alert", "flood victim", "flood damage",
    "flood claim", "flood assistance", "flood recovery",
    "flood preparedness", "flood risk", "flood prone",
    "water level rising", "river overflow", "riverbank burst",
    "dam overflow", "dam burst",
    "flood relief centre", "flood relief center",
})

_FLOOD_EXCLUSIONS: frozenset[str] = frozenset({
    # BM financial / metaphorical uses of "banjir" — not real floods
    "banjir wang", "banjir duit", "banjir rezeki",
    "banjir idea", "banjir hadiah", "banjir maklumat",
})

_ACTIVE_EMERGENCY_KEYWORDS: frozenset[str] = frozenset({
    # BM urgency
    "sekarang", "sedang berlaku", "masa kini", "ketika ini", "saat ini",
    "terjebak", "terperangkap", "tersekat", "terputus",
    "tolong", "tolonglah", "minta tolong", "bantulah",
    "darurat", "kecemasan", "bahaya", "nyawa", "sos",
    "air dah naik", "air makin naik", "air naik laju",
    "air masuk rumah", "air dalam rumah", "rumah tenggelam",
    "tidak boleh keluar", "tak boleh keluar",
    "jalan ditutup", "jalan banjir", "terputus hubungan",
    "mangsa terperangkap",
    # English urgency
    "right now", "happening now", "help me", "help us",
    "urgent", "urgently", "emergency", "trapped", "stuck", "stranded",
    "rescue", "need rescue", "need help", "save me", "save us",
    "cannot escape", "cannot leave", "cut off",
    "rising fast", "rising quickly", "water rising", "mayday",
})

_POST_FLOOD_RELIEF_KEYWORDS: frozenset[str] = frozenset({
    # BM aid / claim
    "bantuan", "tuntutan", "pampasan", "kerosakan", "ganti rugi",
    "permohonan", "mohon bantuan", "borang bantuan",
    "wang bantuan", "ex gratia", "senarai semak",
    "kerugian", "kemusnahan", "rosak", "musnah",
    "selepas banjir", "pasca banjir", "tempat tinggal sementara",
    "baik pulih", "pembaikan",
    # English relief / claim
    "claim", "damage claim", "compensation", "relief", "aid",
    "apply", "application", "how to apply", "register for aid",
    "recovery", "rebuild", "repair", "restore",
    "flood insurance", "insurance claim",
    "after flood", "post flood", "following flood",
    "apply for", "eligible for", "financial assistance", "government aid",
})


# ── Classifier ────────────────────────────────────────────────────────────────

def _classify_flood_intent(query: str) -> FloodIntentResponse:
    """
    Pure keyword-based flood intent classifier.

    Performs case-insensitive substring matching. Returns a deterministic
    result with confidence=1.0 when flood keywords are found, or the safe
    default (is_flood_related=False, confidence=0.0) otherwise.

    Priority: active_emergency > post_flood_relief > general_info.
    """
    text = query.lower()

    is_flood = (
        any(kw in text for kw in _FLOOD_KEYWORDS)
        and not any(excl in text for excl in _FLOOD_EXCLUSIONS)
    )

    if not is_flood:
        return FloodIntentResponse(
            is_flood_related=False,
            situation_type=None,
            confidence=0.0,
        )

    if any(kw in text for kw in _ACTIVE_EMERGENCY_KEYWORDS):
        situation_type = "active_emergency"
    elif any(kw in text for kw in _POST_FLOOD_RELIEF_KEYWORDS):
        situation_type = "post_flood_relief"
    else:
        situation_type = "general_info"

    return FloodIntentResponse(
        is_flood_related=True,
        situation_type=situation_type,
        confidence=1.0,
    )


# ── Endpoint ──────────────────────────────────────────────────────────────────

@router.post("/detect-flood-intent", response_model=FloodIntentResponse)
def detect_flood_intent(request: FloodIntentRequest) -> FloodIntentResponse:
    """
    Classify whether the query is flood-related and determine situation type.

    Keyword-based — completes in < 5 ms with no I/O, no external API calls.
    Returns is_flood_related=False on any failure so the main pipeline
    continues unblocked.
    """
    try:
        result = _classify_flood_intent(request.query)
        logger.info(
            f"[FloodIntent] '{request.query[:80]}' → "
            f"flood={result.is_flood_related}, type={result.situation_type}"
        )
        return result
    except Exception as exc:
        logger.warning(f"[FloodIntent] Classification failed: {exc}; returning safe default")
        return _SAFE_DEFAULT


# ── Retained for reference (not called by the keyword classifier) ─────────────

def _parse_json(text: str) -> dict:
    """
    Lenient JSON extraction from LLM output.

    Not called by the current keyword classifier but retained in case the
    LLM-based path is re-enabled in the future.
    """
    text = text.strip()
    if "```" in text:
        for part in text.split("```")[1:]:
            candidate = part.strip()
            if candidate.startswith("json"):
                candidate = candidate[4:].strip()
            candidate = candidate.rstrip("`").strip()
            if candidate:
                text = candidate
                break
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end > start:
        text = text[start : end + 1]
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    normalised = text.replace("True", "true").replace("False", "false").replace("None", "null")
    try:
        return json.loads(normalised)
    except json.JSONDecodeError:
        pass
    try:
        result = ast.literal_eval(text)
        if isinstance(result, dict):
            return result
    except (ValueError, SyntaxError):
        pass
    is_flood_val = None
    situation = None
    confidence = 0.0
    m = re.search(r'"?is_flood_related"?\s*:\s*(true|false|True|False)', text, re.I)
    if m:
        is_flood_val = m.group(1).lower() == "true"
    m = re.search(r'"?situation_type"?\s*:\s*"?([a-z_]+|null)"?', text, re.I)
    if m:
        val = m.group(1)
        situation = None if val.lower() == "null" else val
    m = re.search(r'"?confidence"?\s*:\s*([0-9.]+)', text)
    if m:
        try:
            confidence = float(m.group(1))
        except ValueError:
            pass
    if is_flood_val is not None:
        return {"is_flood_related": is_flood_val, "situation_type": situation, "confidence": confidence}
    raise ValueError(f"Cannot parse LLM response as JSON: {text[:200]!r}")
