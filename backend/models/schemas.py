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
    answer_bm: str = Field(description="Intermediate BM answer from SEA-LION v4")
    original_text: str = Field(description="Raw retrieved BM text from government document")
    translation_model: str = Field(description="'google_tllm' or 'nllb200'")
    semantic_score: float = Field(description="Cross-lingual cosine similarity 0.0–1.0")
    readability_grade: float = Field(description="Flesch-Kincaid grade level in target language")
    sources: list[Source]
    detected_language: str = Field(description="ISO language code of detected input")
    confidence: float = Field(description="RAG retrieval confidence 0.0–1.0")
    audio_url: str | None = None
    steps: list[str] | None = None
    step_icons: list[str] | None = None
    disclaimer: str | None = None


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
