"""
LLM Service — SEA-LION v4 (primary) + Gemini 3 Flash Preview (fallback)
SEA-LION model name per https://docs.sea-lion.ai/guides/inferencing/api:
  "aisingapore/Gemma-SEA-LION-v4-27B-IT"
Gemini fallback model per https://cloud.google.com/vertex-ai/generative-ai/docs/models/gemini/3-flash:
  "gemini-3-flash-preview" — available in location "global" ONLY (not us-central1)
PRD Constraint #1: LLM must only answer from retrieved context.

Adapted: prompts are now bilingual-aware — the LLM generates answers directly
in the user's language from whatever language the context is in.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import httpx
from google import genai
from google.genai import types

from utils.prompt_templates import (
    build_system_prompt,
    build_user_prompt,
    DIALECT_PROMPTS,
    STEP_EXTRACTION_PROMPT,
)
from utils.fallback_handler import fallback_state
from utils.language_router import get_language_name

logger = logging.getLogger(__name__)


# ── SEA-LION v4 (Primary LLM) ───────────────────────────

async def generate_answer_sealion(
    context: str,
    query: str,
    answer_language: str = "Bahasa Malaysia",
    dialect_code: str = "ms",
) -> str:
    api_key = os.getenv("SEALION_API_KEY", "")
    api_base = os.getenv("SEALION_API_BASE_URL", "https://api.sea-lion.ai/v1")

    system_prompt = DIALECT_PROMPTS.get(dialect_code, build_system_prompt(answer_language))
    user_prompt = build_user_prompt(context, query, answer_language)

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{api_base}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "aisingapore/Gemma-SEA-LION-v4-27B-IT",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": 0.3,
                "max_tokens": 2048,
            },
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]


# ── Gemini fallback chain ────────────────────────────────
# Use alias names (no -001 suffix) so Vertex AI always resolves to the
# latest stable version. Only gemini-3-flash-preview needs explicit preview.
GEMINI_MODELS_PRIORITY = [
    "gemini-3-flash-preview",
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-1.5-flash",
]


def _get_gemini_client() -> genai.Client:
    project = os.getenv("GOOGLE_CLOUD_PROJECT", "")
    os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "True")
    return genai.Client(
        vertexai=True,
        project=project,
        location="global",
    )


async def _generate_with_fallback_model(
    client: genai.Client,
    contents: str,
    config: types.GenerateContentConfig,
) -> str:
    last_exc: Exception | None = None
    for model_name in GEMINI_MODELS_PRIORITY:
        # Retry this model once on 429 (rate limit) with a short backoff
        # before giving up and moving to the next model.
        for attempt in range(2):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=contents,
                    config=config,
                )
                return response.text
            except Exception as exc:
                err_str = str(exc)
                is_rate_limited = "429" in err_str or "RESOURCE_EXHAUSTED" in err_str
                if is_rate_limited and attempt == 0:
                    logger.warning(
                        f"Gemini model {model_name} rate-limited (429); "
                        "waiting 3 s before retry…"
                    )
                    await asyncio.sleep(3)
                    continue
                logger.warning(f"Gemini model {model_name} failed: {exc}")
                last_exc = exc
                break
    raise last_exc  # type: ignore


async def generate_answer_gemini(
    context: str,
    query: str,
    answer_language: str = "Bahasa Malaysia",
    dialect_code: str = "ms",
) -> str:
    client = _get_gemini_client()
    system_prompt = DIALECT_PROMPTS.get(dialect_code, build_system_prompt(answer_language))
    user_prompt = build_user_prompt(context, query, answer_language)

    return await _generate_with_fallback_model(
        client,
        contents=user_prompt,
            config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.3,
            max_output_tokens=2048,
        ),
    )


# ── Unified Generate with Fallback ───────────────────────

async def generate_answer(
    context: str,
    query: str,
    target_lang: str = "ms",
    dialect_code: str = "ms",
) -> tuple[str, bool]:
    """
    Generate answer in the user's target language directly.
    Returns (answer_text, is_fallback_used).
    """
    answer_language = get_language_name(target_lang)

    try:
        answer = await generate_answer_sealion(context, query, answer_language, dialect_code)
        fallback_state.llm_fallback_active = False
        return answer, False
    except Exception as exc:
        logger.warning(f"SEA-LION v4 failed ({exc}), falling back to Gemini 3 Flash")
        fallback_state.llm_fallback_active = True
        answer = await generate_answer_gemini(context, query, answer_language, dialect_code)
        return answer, True


# Legacy alias for backward compat
async def generate_bm_answer(
    context: str,
    query: str,
    dialect_code: str = "ms",
) -> tuple[str, bool]:
    return await generate_answer(context, query, target_lang="ms", dialect_code=dialect_code)


# ── Step Extraction ──────────────────────────────────────

def _parse_json_lenient(text: str) -> dict:
    """Parse JSON from LLM output, tolerating markdown fences and trailing content."""
    text = text.strip()
    if "```" in text:
        parts = text.split("```")
        for part in parts[1:]:
            candidate = part.strip()
            if candidate.startswith("json"):
                candidate = candidate[4:].strip()
            candidate = candidate.rstrip("`").strip()
            if candidate:
                text = candidate
                break

    # Find the outermost { ... }
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        text = text[start:end + 1]

    return json.loads(text)


# Icon keyword mapping: first matching keyword wins, case-insensitive
_ICON_KEYWORDS: list[tuple[str, list[str]]] = [
    ("Heart",      ["kesihatan", "kesehatan", "health", "medical", "fomema", "sakit", "doctor", "doktor", "periksa"]),
    ("CreditCard", ["bayar", "pay", "fee", "yuran", "wang", "money", "levy", "biaya", "duit", "cost"]),
    ("Upload",     ["upload", "unggah", "muat naik", "scan", "imbas", "online", "log in", "login", "myeg", "fwcms"]),
    ("Download",   ["epass", "e-pass", "cetak", "print", "download"]),
    ("Shield",     ["asuransi", "insurance", "perlindungan", "protect", "insuran", "socso", "spikpa", "fwcs"]),
    ("FileText",   ["dokumen", "document", "surat", "form", "formul", "passport", "paspor", "permit", "kad", "card", "sijil", "certificate", "ic ", "ic,"]),
    ("Building2",  ["pejabat", "office", "counter", "kaunter", "jabatan", "department", "agency", "agensi", "immigration", "imigresen", "jtksm"]),
    ("Send",       ["hantar", "submit", "permohonan", "application", "mohon", "apply", "daftar", "register"]),
    ("Briefcase",  ["kontrak", "contract", "kerja", "work", "employment", "majikan", "employer"]),
    ("Calendar",   ["tarikh", "date", "renewal", "perpanjang", "renew", "luput", "expire", "tempoh", "period", "valid"]),
    ("Clock",      ["masa", "time", "duration", "tunggu", "wait"]),
    ("Phone",      ["telefon", "phone", "call", "hubungi", "contact", "consult", "kedutaan", "konsulat"]),
    ("MapPin",     ["alamat", "address", "location", "lokasi"]),
    ("Users",      ["pekerja", "worker", "employee", "asing", "foreign"]),
]


def _assign_icons(steps: list[str]) -> list[str]:
    """Map each step to the best-matching Lucide icon name."""
    icons = []
    for step in steps:
        step_lower = step.lower()
        assigned = "CheckCircle"
        for icon, keywords in _ICON_KEYWORDS:
            if any(kw in step_lower for kw in keywords):
                assigned = icon
                break
        icons.append(assigned)
    return icons


def _clean_step_text(raw: str, max_chars: int = 120) -> str:
    """
    Clean a raw step string: strip markdown bold/italic, remove source
    citations, and truncate to the first sentence (or max_chars).
    Used for both numbered/bullet items and Title:Content paragraphs.
    """
    # Strip markdown bold/italic/code
    t = re.sub(r'\*\*(.+?)\*\*', r'\1', raw)
    t = re.sub(r'\*(.+?)\*', r'\1', t)
    t = re.sub(r'_(.+?)_', r'\1', t)
    t = re.sub(r'`(.+?)`', r'\1', t)
    # Remove source citations: "(Source 1)", "(Sumber 2)", "(Sumber: X)" etc.
    t = re.sub(r'\s*\((?:Source|Sumber)[^)]*\)', '', t, flags=re.IGNORECASE)
    t = t.strip()
    # Truncate at first sentence boundary (.  !  ?) followed by space or end
    sent_end = re.search(r'[.!?](?=\s|$)', t)
    if sent_end and sent_end.end() <= max_chars + 1:
        t = t[: sent_end.end()]
    else:
        t = t[:max_chars].rstrip()
    return t.strip()


def _extract_steps_deterministic(text: str) -> tuple[list[str], list[str]]:
    """
    Deterministic (zero-LLM) step extractor.  Handles three answer formats
    in order of specificity — returns on the first that produces >= 2 steps:

      Format 1 — Numbered list
        "1. Do this", "2) Do that", "Langkah 1: ...", "Step 2 ..."
      Format 2 — Bullet list
        "- Do this", "• Do that", "* Item"
      Format 3 — Title:Content paragraphs  (Javanese/BM LLM style)
        "FOMEMA: Pekerja kudu...", "Pemeriksaan Dhisik: Pasten paspor..."
        Also handles simplifier-generated markdown bold:
        "**Mlebu (Login):** Bapak/Ibu mlebu..."
    """
    STEP_WORDS = r"(?:Langkah|Tahap|Cara|Step)\s+"

    # Format 1: numbered
    numbered = re.findall(
        rf"(?:^|\n)\s*(?:{STEP_WORDS})?\d+[\.\):\s]\s*(.+?)(?=\n\s*(?:{STEP_WORDS})?\d+[\.\):\s]|\Z)",
        text,
        re.DOTALL | re.IGNORECASE,
    )
    if len(numbered) >= 2:
        steps = [_clean_step_text(m.strip().replace("\n", " ")) for m in numbered if m.strip()]
        steps = [s for s in steps if s]
        if len(steps) >= 2:
            return steps, _assign_icons(steps)

    # Format 2: bullet — use negative lookahead so "**bold**" lines are NOT
    # treated as bullets (a lone `*` used as bullet, not `**` markdown bold).
    bullets = re.findall(
        r"(?:^|\n)\s*(?:[-•]|\*(?!\*))\s*(.+?)(?=\n\s*(?:[-•]|\*(?!\*))|\Z)",
        text,
        re.DOTALL,
    )
    if len(bullets) >= 2:
        steps = [_clean_step_text(m.strip().replace("\n", " ")) for m in bullets if m.strip()]
        steps = [s for s in steps if s]
        if len(steps) >= 2:
            return steps, _assign_icons(steps)

    # Format 3: Title:Content per line.
    # Handles both plain "Title: content" and markdown "**Title:** content".
    title_content: list[str] = []
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        # Try markdown bold first: **Title:** content
        m = re.match(r'^\*\*([A-Za-z][A-Za-z0-9 /().-]{0,49}):\*\*\s+(.{10,})$', line)
        if not m:
            # Plain: Title: content
            m = re.match(r'^([A-Za-z][A-Za-z0-9 /().-]{0,49}):\s+(.{10,})$', line)
        if m:
            title_raw = m.group(1).strip()
            content_raw = m.group(2).strip()
            if len(title_raw.split()) <= 4:
                clean_content = _clean_step_text(content_raw, max_chars=100)
                step = f"{title_raw}: {clean_content}" if clean_content else title_raw
                title_content.append(step)
    if len(title_content) >= 2:
        return title_content, _assign_icons(title_content)

    return [], []


async def extract_steps(answer: str, language: str = "English") -> tuple[list[str], list[str]]:
    """
    Extract step-by-step instructions from an answer.
    PRD F09: Visual step-by-step instruction cards.

    Robustness layers (in order):
      1. Deterministic regex — zero-latency; handles numbered lists, bullet
         lists, and Title:Content paragraphs (the Javanese LLM output style).
         Most structured LLM answers are caught here without any API call.
      2. Gemini structured output (response_mime_type=application/json) — only
         called when deterministic extraction finds nothing, i.e. the answer is
         prose-only and may still contain implicit procedural steps.
      3. _parse_json_lenient — tolerates markdown fences / extra text from
         models that do not support response_mime_type.
      4. _extract_steps_deterministic on the Gemini output — catches cases
         where Gemini itself responds with a numbered/title list instead of JSON.
    """
    # Layer 1: deterministic extraction (fast, no API call)
    steps, icons = _extract_steps_deterministic(answer)
    if steps:
        logger.info(f"Step extraction: {len(steps)} steps via deterministic extractor")
        return steps, icons

    # Layer 2-4: LLM fallback for unstructured prose answers
    try:
        client = _get_gemini_client()
        prompt = STEP_EXTRACTION_PROMPT.format(answer=answer, language=language)

        try:
            text = await _generate_with_fallback_model(
                client,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.1,
                    max_output_tokens=1024,
                    response_mime_type="application/json",
                ),
            )
        except Exception as structured_exc:
            logger.debug(
                f"Structured JSON output unavailable ({structured_exc}); "
                "retrying without mime constraint"
            )
            text = await _generate_with_fallback_model(
                client,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.1,
                    max_output_tokens=1024,
                ),
            )

        # Layer 3: lenient JSON parser
        try:
            data = _parse_json_lenient(text)
            steps = data.get("steps", [])
            icons = data.get("step_icons", [])
            if steps:
                while len(icons) < len(steps):
                    icons.append("CheckCircle")
                logger.info(f"Step extraction: {len(steps)} steps via Gemini JSON")
                return steps, icons
        except Exception as json_exc:
            logger.debug(f"Lenient JSON parse failed ({json_exc}); trying deterministic on Gemini output")

        # Layer 4: deterministic on the raw Gemini text (Gemini may output a list instead of JSON)
        steps, icons = _extract_steps_deterministic(text)
        if steps:
            logger.info(f"Step extraction: {len(steps)} steps via deterministic on Gemini output")
            return steps, icons

        logger.debug("Step extraction: no steps found (answer may not be procedural)")
        return [], []

    except Exception as exc:
        logger.warning(f"Step extraction failed: {exc}")
        return [], []
