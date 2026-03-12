"""
LLM Prompt Templates
PRD Section 6.3: LLM must only answer from retrieved context (grounded).
PRD Constraint #1: Never answer from parametric memory.
"""

# System prompt for BM answer generation (SEA-LION v4 / Gemini fallback)
GROUNDED_BM_SYSTEM_PROMPT = """Anda adalah pembantu kerajaan Malaysia yang membantu rakyat memahami perkhidmatan awam.

PERATURAN PENTING:
1. Anda HANYA boleh menjawab berdasarkan konteks dokumen rasmi yang diberikan di bawah.
2. JANGAN sekali-kali menjawab berdasarkan pengetahuan umum anda sendiri.
3. Jika konteks yang diberikan tidak mengandungi maklumat yang cukup, nyatakan: "Maklumat ini tiada dalam dokumen rasmi yang dirujuk. Sila hubungi agensi berkaitan."
4. Jawab dalam Bahasa Malaysia yang jelas dan mudah difahami.
5. Sertakan langkah-langkah jika soalan berkaitan prosedur.
6. Nyatakan nama dokumen sumber dalam jawapan anda.

You are a Malaysian government assistant helping citizens understand public services.

CRITICAL RULES:
1. You must ONLY answer from the official document context provided below.
2. NEVER answer from your own parametric knowledge.
3. If the context does not contain sufficient information, state: "This information is not found in the referenced official documents. Please contact the relevant agency."
4. Answer in clear, easy-to-understand Bahasa Malaysia.
5. Include step-by-step instructions if the question relates to a procedure.
6. Reference the source document name in your answer."""

GROUNDED_BM_USER_TEMPLATE = """KONTEKS DOKUMEN RASMI (BAHASA MALAYSIA):
{context}

SOALAN PENGGUNA: {query}

Berdasarkan konteks dokumen rasmi di atas SAHAJA, jawab soalan pengguna dalam Bahasa Malaysia."""


# Prompt for step extraction (procedural queries)
STEP_EXTRACTION_PROMPT = """Given the following answer about a government procedure, extract clear step-by-step instructions.
Return ONLY a JSON array of steps (strings). Each step should be a short, clear action.
Also return a JSON array of Lucide icon names (one per step) that best represents each action.

Answer:
{answer}

Return format:
{{"steps": ["Step 1 text", "Step 2 text", ...], "step_icons": ["IconName1", "IconName2", ...]}}

Use these Lucide icon names: FileText, Building2, Send, Clock, CreditCard, Users, Phone, MapPin, CheckCircle, Download, Upload, Calendar, Shield, Heart, Briefcase, Home"""


# Conservative simplification prompt (used when semantic score < 0.90)
CONSERVATIVE_SIMPLIFY_PROMPT = """Rewrite the following text in simpler language suitable for a Grade 5 reading level.
CRITICAL: You must preserve ALL legal meanings, numbers, dates, eligibility criteria, and proper nouns EXACTLY.
Only simplify sentence structure and replace difficult vocabulary. Do not remove any information.

Language: {language}

Text to simplify:
{text}

Simplified text:"""


# Standard simplification prompt
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


# Dialect-specific prompt adjustments
DIALECT_PROMPTS = {
    "ms": GROUNDED_BM_SYSTEM_PROMPT,
    "ms-kelantanese": GROUNDED_BM_SYSTEM_PROMPT + "\n\nNote: User speaks Kelantanese dialect. Answer in standard BM but use simple vocabulary.",
    "ms-kedah": GROUNDED_BM_SYSTEM_PROMPT + "\n\nNote: User speaks Kedah dialect. Answer in standard BM but use simple vocabulary.",
    "ms-sabah": GROUNDED_BM_SYSTEM_PROMPT + "\n\nNote: User speaks Sabah Malay. Answer in standard BM but use simple vocabulary.",
    "ms-sarawak": GROUNDED_BM_SYSTEM_PROMPT + "\n\nNote: User speaks Sarawak Malay. Answer in standard BM but use simple vocabulary.",
}


# Hijri calendar context template (Phase 16)
HIJRI_CONTEXT_TEMPLATE = """Tarikh akhir: {gregorian_date}
Tarikh Hijri bersamaan: {hijri_date}"""
