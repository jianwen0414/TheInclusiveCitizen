"""
LLM Prompt Templates
PRD Section 6.3: LLM must only answer from retrieved context (grounded).
PRD Constraint #1: Never answer from parametric memory.

Adapted for mixed-language knowledge base (documents may be in English or BM).
The LLM generates the answer directly in the user's target language so that
an extra translation round-trip is avoided when possible.
"""

from utils.language_router import LANGUAGE_NAMES

# ── Grounded System Prompt (bilingual-aware) ─────────────

GROUNDED_SYSTEM_PROMPT = """You are a Malaysian government assistant helping citizens understand public services.

CRITICAL RULES:
1. You must ONLY answer from the official document context provided below.
2. NEVER answer from your own parametric knowledge.
3. If the context does not contain sufficient information, state clearly that the information is not found in the referenced documents and advise the user to contact the relevant government agency.
4. Include step-by-step instructions if the question relates to a procedure.
5. Reference the source document name in your answer.
6. Answer in {answer_language}.
7. Use simple, everyday vocabulary — aim for a Grade 5 reading level."""


def build_system_prompt(answer_language: str = "Bahasa Malaysia") -> str:
    return GROUNDED_SYSTEM_PROMPT.format(answer_language=answer_language)


GROUNDED_USER_TEMPLATE = """OFFICIAL DOCUMENT CONTEXT:
{context}

USER QUESTION: {query}

Based ONLY on the official document context above, answer the user's question in {answer_language}. If the context is insufficient, say so."""


def build_user_prompt(context: str, query: str, answer_language: str = "Bahasa Malaysia") -> str:
    return GROUNDED_USER_TEMPLATE.format(
        context=context, query=query, answer_language=answer_language,
    )


# Legacy aliases kept for backward compat (used by dialect prompts)
GROUNDED_BM_SYSTEM_PROMPT = build_system_prompt("Bahasa Malaysia")
GROUNDED_BM_USER_TEMPLATE = """OFFICIAL DOCUMENT CONTEXT:
{context}

USER QUESTION: {query}

Based ONLY on the official document context above, answer the user's question in Bahasa Malaysia."""


STEP_EXTRACTION_PROMPT = """You are a step extraction assistant for a multilingual government services app.

The answer below is written in {language}. Your task:
1. Read the answer carefully, regardless of its language.
2. Identify ANY sequential actions, requirements, or stages described (even if not explicitly numbered).
3. Break them into short, clear step texts — keep each step in the SAME language as the answer ({language}). Do NOT translate.
4. If the answer describes a process or procedure, you MUST extract steps. Only return empty steps if the answer is purely definitional with zero procedural content.

Answer:
{answer}

Return ONLY this JSON (no other text before or after):
{{"steps": ["Step 1 text", "Step 2 text"], "step_icons": ["FileText", "Building2"]}}

Use icon names from: FileText, Building2, Send, Clock, CreditCard, Users, Phone, MapPin, CheckCircle, Download, Upload, Calendar, Shield, Heart, Briefcase, Home"""


CONSERVATIVE_SIMPLIFY_PROMPT = """Rewrite the following text in simpler language suitable for a Grade 5 reading level.
CRITICAL: You must preserve ALL legal meanings, numbers, dates, eligibility criteria, and proper nouns EXACTLY.
Only simplify sentence structure and replace difficult vocabulary. Do not remove any information.

Language: {language}

Text to simplify:
{text}

Simplified text:"""


STANDARD_SIMPLIFY_PROMPT = """Rewrite the following text in very simple, plain language suitable for a Grade 5 reading level.
Rules:
- Replace jargon and complex terms with everyday words
- Use short sentences (max 15 words each)
- Keep all numbers, dates, names, and eligibility criteria exactly the same
- Keep the meaning identical — do not add or remove information
- Write in {language}

Original text:
{text}

Plain language version:"""


DIALECT_PROMPTS = {
    "ms": build_system_prompt("Bahasa Malaysia"),
    "ms-kelantanese": build_system_prompt("Bahasa Malaysia") + "\n\nNote: User speaks Kelantanese dialect. Answer in standard BM but use simple vocabulary.",
    "ms-kedah": build_system_prompt("Bahasa Malaysia") + "\n\nNote: User speaks Kedah dialect. Answer in standard BM but use simple vocabulary.",
    "ms-sabah": build_system_prompt("Bahasa Malaysia") + "\n\nNote: User speaks Sabah Malay. Answer in standard BM but use simple vocabulary.",
    "ms-sarawak": build_system_prompt("Bahasa Malaysia") + "\n\nNote: User speaks Sarawak Malay. Answer in standard BM but use simple vocabulary.",
    "id": build_system_prompt("Bahasa Indonesia") + "\n\nNote: User is an Indonesian migrant worker in Malaysia. Use simple, clear Indonesian.",
    "jv": build_system_prompt("Javanese (Ngoko / everyday Javanese)") + "\n\nNote: User speaks Javanese. Answer in everyday Javanese (Ngoko) mixed with common Indonesian administrative terms where needed for clarity. Keep sentences short.",
}


HIJRI_CONTEXT_TEMPLATE = """Tarikh akhir: {gregorian_date}
Tarikh Hijri bersamaan: {hijri_date}"""
