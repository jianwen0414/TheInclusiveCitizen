"""
Pydantic request/response models for all API endpoints.
PRD Section 7.1 (Table 10) — endpoint definitions
PRD Section 7.2 — /api/query response schema
"""

from __future__ import annotations

from pydantic import BaseModel, Field


# ── /api/query ────────────────────────────────────────────

class QueryRequest(BaseModel):
    query: str
    persona: str = "elderly"
    language: str | None = None  # auto-detected if omitted


class Source(BaseModel):
    doc_name: str
    section: str | None = None
    page_number: int | None = None
    url: str | None = None
    excerpt: str | None = None


class QueryResponse(BaseModel):
    answer: str = Field(description="Translated + simplified answer in user's language")
    answer_bm: str = Field(description="Intermediate BM answer (before simplification)")
    original_text: str = Field(description="Raw retrieved BM text from government document")
    translation_model: str = Field(description="'google_tllm' or 'nllb200'")
    llm_model: str = Field(description="Model that generated the answer, e.g. 'gemini-2.0-flash' or 'sealion-v4'")
    semantic_score: float = Field(description="Cross-lingual cosine similarity 0.0–1.0")
    readability_grade: float = Field(description="Flesch-Kincaid grade level in target language")
    sources: list[Source]
    detected_language: str = Field(description="ISO language code of detected input")
    confidence: float = Field(description="RAG retrieval confidence 0.0–1.0")
    audio_url: str | None = None
    steps: list[str] | None = None
    step_icons: list[str] | None = None
    disclaimer: str | None = None
    flood_mode: bool | None = None
    situation_type: str | None = None
    triage_message: str | None = None


# ── /api/translate ────────────────────────────────────────

class TranslateRequest(BaseModel):
    text: str
    source_lang: str = "ms"
    target_lang: str = "en"


class TranslateResponse(BaseModel):
    translated_text: str
    model_used: str  # "google_tllm" or "nllb200"


# ── /api/transcribe ──────────────────────────────────────

class TranscribeResponse(BaseModel):
    text: str
    detected_language: str


# ── /api/synthesise ──────────────────────────────────────

class SynthesiseRequest(BaseModel):
    text: str
    language: str = "en"
    speed: float = 1.0


class SynthesiseResponse(BaseModel):
    audio_base64: str
    content_type: str = "audio/mp3"


# ── /api/ingest ──────────────────────────────────────────

class IngestRequest(BaseModel):
    doc_type: str = "government_guide"


class IngestResponse(BaseModel):
    status: str
    doc_name: str
    chunks_created: int
    indexing_note: str | None = None  # explains async Vertex AI Search indexing delay


# ── /api/extract-steps ───────────────────────────────────

class ExtractStepsRequest(BaseModel):
    answer: str
    language: str = "English"


class ExtractStepsResponse(BaseModel):
    steps: list[str]
    step_icons: list[str]


# ── /api/health ──────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    services: dict[str, str]


# ── /api/detect-dialect (internal pipeline endpoint) ────

class DetectDialectRequest(BaseModel):
    query: str
    language_hint: str | None = None


class DetectDialectResponse(BaseModel):
    detected_language: str
    target_lang: str


# ── /api/retrieve (internal pipeline endpoint) ──────────

class RetrieveRequest(BaseModel):
    query: str
    top_k: int = 6
    threshold: float = 0.25
    doc_type_filter: list[str] | None = None


class RetrievedChunkSchema(BaseModel):
    doc_name: str
    doc_type: str | None = None
    page_number: int | None = None
    chunk_text: str
    similarity: float
    metadata: dict | None = None


class RetrieveResponse(BaseModel):
    chunks: list[RetrievedChunkSchema]
    context: str
    original_chunk_text: str
    confidence: float


# ── /api/generate (internal pipeline endpoint) ──────────

class GenerateRequest(BaseModel):
    context: str
    query: str
    target_lang: str = "ms"
    dialect_code: str = "ms"


class GenerateResponse(BaseModel):
    answer: str
    llm_model: str


# ── /api/simplify (internal pipeline endpoint) ──────────

class SimplifyRequest(BaseModel):
    text: str
    language: str = "English"
    conservative: bool = False
    enrich_hijri: bool = False


class SimplifyResponse(BaseModel):
    simplified_text: str
    readability_grade: float


# ── /api/score (internal pipeline endpoint) ─────────────

class ScoreRequest(BaseModel):
    original_bm_text: str
    translated_simplified_text: str


class ScoreResponse(BaseModel):
    score: float


# ── /api/detect-flood-intent ─────────────────────────────

class FloodIntentRequest(BaseModel):
    query: str
    detected_language: str


class FloodIntentResponse(BaseModel):
    is_flood_related: bool
    situation_type: str | None
    confidence: float
