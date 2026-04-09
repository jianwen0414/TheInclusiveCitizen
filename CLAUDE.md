# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

**The Inclusive Citizen** is a multilingual AI assistant for Malaysian public-service information. Users ask questions in voice or text (including Malay dialects like Kelantanese, and languages like Javanese/Bahasa Indonesia) and receive plain-language answers grounded in official government PDFs. The UI supports accessibility personas (Elderly, Migrant Worker, Rural Community) that tune contrast, TTS speed, and layout.

**Stack:** Next.js 16 / React 19 frontend + FastAPI backend + Supabase pgvector database.

---

## Development commands

### Frontend (repo root)
```bash
npm install          # install dependencies
npm run dev          # dev server → http://localhost:3000
npm run build        # production build
npm run lint         # ESLint check
```
Open the app at **http://localhost:3000/chat**.

### Backend (`backend/` directory)
```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # macOS/Linux
pip install -r requirements.txt
python -m spacy download en_core_web_sm   # for jargon features
python main.py                  # API → http://localhost:8000
```
Interactive API docs: **http://localhost:8000/docs**

### Ingest sample documents (Windows PowerShell, backend must be running)
```powershell
cd seed_docs
.\ingest_all.ps1
```

---

## Architecture

### Request lifecycle (`POST /api/query`)

1. **Dialect detection** — `lingua-py` + lexical markers (`services/dialect_detector.py`)
2. **Query embedding** — Gemini `gemini-embedding-001` with **no pre-translation** (intentional design constraint)
3. **Vector retrieval** — Supabase pgvector RPC `match_documents()`, top-6, threshold 0.25 (`services/rag_pipeline.py`)
4. **LLM generation** — SEA-LION v4 primary → Gemini fallback chain (`services/llm_service.py`)
5. **Translation** (only if LLM output language ≠ user language, `services/translation_service.py`)
6. **Simplification** — Flesch-Kincaid grading + spaCy NER + LLM jargon replacement (`services/simplifier.py`)
7. **Semantic scoring** — `sentence-transformers` cross-lingual cosine (source vs. answer, `services/semantic_scorer.py`)
8. **TTS** (optional) — persona-aware speed: elderly 0.75×, rural 0.9×, migrant 1.0× (`services/tts_service.py`)

### Backend structure (`backend/`)
- `main.py` — FastAPI app entry; registers 7 routers, CORS middleware
- `routers/` — one file per endpoint group (`query.py`, `transcribe.py`, `synthesise.py`, `translate.py`, `ingest.py`, `steps.py`, `health.py`)
- `services/` — all business logic (RAG, LLM, STT/TTS, dialect detection, simplification, scoring)
- `models/schemas.py` — Pydantic request/response schemas for all endpoints
- `utils/prompt_templates.py` — dialect-aware system/user prompts (modify here to change LLM behaviour)

### Frontend structure
- `app/` — Next.js App Router pages (`/` landing, `/chat` main UI)
- `components/ChatPanel.tsx` — voice recording (`MediaRecorder` + `WebAudio API`), query submission, response rendering
- `components/PersonaSelector.tsx` — persona state drives API parameters and UI styling
- `components/SourcePanel.tsx` — displays retrieved document excerpts
- `lib/api.ts` — typed `fetch`-based API client; all backend calls go through here
- `components/ui/` — 50+ Radix UI / shadcn primitives (do not edit these directly)

### Database (Supabase pgvector)
- Table: `document_chunks` (`id`, `doc_name`, `doc_type`, `page_number`, `chunk_text`, `embedding VECTOR(768)`, `metadata JSONB`)
- IVFFlat index on `embedding` (lists=100, cosine distance)
- Schema: `backend/supabase_schema.sql`

---

## Environment variables

**`backend/.env`** (required):

| Variable | Purpose |
|---|---|
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | Service role key |
| `GOOGLE_CLOUD_PROJECT` | GCP project ID |
| `SEALION_API_KEY` | SEA-LION v4 API key |
| `SEALION_API_BASE_URL` | Optional; defaults to `https://api.sea-lion.ai/v1` |
| `CORS_ORIGINS` | Comma-separated; defaults to `http://localhost:3000` |
| `BACKEND_PORT` | Defaults to `8000` |
| `NLLB_MODEL_PATH` | Optional NLLB-200 model id or local path |

Backend uses **Google Application Default Credentials** for Vertex AI, Speech, TTS, and Translation.

**Frontend `.env.local`** (optional):
- `NEXT_PUBLIC_API_BASE_URL` — backend base URL (defaults to `http://localhost:8000`)

---

## Key design decisions

- **No pre-translation of queries before embedding**: Gemini embedding model handles cross-lingual retrieval directly. Do not add translation steps before the embedding call.
- **Dialect-aware prompting**: Prompts in `utils/prompt_templates.py` vary by detected dialect. Changes here affect all LLM output style.
- **LLM fallback chain**: `llm_service.py` tries SEA-LION v4 → Gemini 3 Flash Preview → Gemini 2.0 Flash → Gemini 2.0 Flash Lite → Gemini 1.5 Flash. Translation fallback: Google Cloud Translation → NLLB-200.
- **TypeScript path alias**: `@/*` maps to the repo root (e.g. `import { X } from "@/components/ui/button"`).
- **TypeScript/ESLint errors are ignored at build time** (`next.config.mjs`: `ignoreBuildErrors: true`). Do not rely on build failure to catch type errors — run `npm run lint` explicitly.
- **State management**: plain React hooks only (no Redux/Zustand).
