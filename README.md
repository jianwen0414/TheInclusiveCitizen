# The Inclusive Citizen

A prototype **multilingual AI assistant** for Malaysian public-service information. Citizens can ask questions in **voice or text**—including **Malay dialects** (e.g. Kelantanese) and **languages such as Javanese / Bahasa Indonesia**—and receive **plain-language answers** grounded in **official PDFs**, with **source excerpts**, **readability hints**, and a **meaning-accuracy** signal aligned to the retrieved document text.

The UI supports **personas** (Elderly, Migrant Worker, Rural Community) that tune accessibility—for example, higher-contrast layout and slower text-to-speech for the elderly mode.

---

## Architecture

| Layer | Stack |
|--------|--------|
| **Frontend** | [Next.js](https://nextjs.org/) 16, React 19, Tailwind CSS, Radix UI — chat at [`/chat`](http://localhost:3000/chat) |
| **Backend** | [FastAPI](https://fastapi.tiangolo.com/) (`backend/`) — REST API |
| **Retrieval** | [Supabase](https://supabase.com/) **pgvector** — chunked PDF embeddings, similarity search |
| **Embeddings** | Google **Gemini** embedding model (query embedded **without** pre-translation) |
| **Generation** | **Gemini 2.0 Flash** via Vertex AI (primary, all languages) + **SEA-LION v4** (optional BM specialist fallback) |
| **Speech** | Google Cloud **Speech-to-Text** and **Text-to-Speech** |
| **Optional** | Google Cloud **Translation** (advanced) and **NLLB-200** for some language paths; **sentence-transformers** for semantic scoring |

End-to-end query flow (simplified): **dialect / language detection** → **vector retrieval** → **grounded answer in the user’s language** → **simplification** → **semantic score vs. source chunk** → **TTS** (persona-aware speed).

Interactive API docs: `http://localhost:8000/docs` when the backend is running.

---

## Repository layout

```
app/                 Next.js app routes (main chat: app/chat/)
components/          UI (chat, persona selector, source panel, etc.)
lib/                 API client (NEXT_PUBLIC_API_BASE_URL)
backend/             FastAPI service (main.py, routers/, services/)
seed_docs/           Sample government PDFs + ingest script
docs/                Voice demo playbooks (Mak Cik Rohani, Budi)
public/demo/         Optional demo audio (see public/demo/README.md)
scripts/             Playwright E2E, Chrome CDP helpers, copy-audio scripts
```

---

## Prerequisites

- **Node.js** 20+ (LTS recommended; dev tooling targets current `@types/node`)
- **Python** 3.11+ recommended
- **Supabase** project with pgvector and tables used by ingest/RAG (configure via env)
- **Google Cloud** project with Vertex AI / Speech / TTS (and optionally Translation), plus application credentials
- **SEA-LION** API key ([SEA-LION](https://docs.sea-lion.ai/)) — optional; enables BM specialist fallback
- Optional: **ffmpeg** (Windows: `winget install ffmpeg`) for voice E2E demos

---

## Quick start

### 1. Backend

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

Create `backend/.env` (or set variables in your environment) — see [Environment variables](#environment-variables).

```bash
python main.py
```

Default URL: **http://localhost:8000** (override with `BACKEND_PORT`).

> **spaCy:** For jargon-related features, install the small English model if prompted:  
> `python -m spacy download en_core_web_sm`

### 2. Frontend

From the repo root:

```bash
npm install
```

Set `NEXT_PUBLIC_API_BASE_URL` if the API is not on `http://localhost:8000` (e.g. in `.env.local`).

```bash
npm run dev
```

Open **http://localhost:3000/chat**.

### 3. Ingest sample documents

PDFs in `seed_docs/` (e.g. BSH eligibility, work permit renewal, MySejahtera, EPF) can be uploaded to the vector store with the backend running:

```powershell
cd seed_docs
.\ingest_all.ps1
```

This calls `POST /api/ingest` for each PDF. Ensure Supabase and embedding credentials are configured first.

---

## Environment variables

Configure these in `backend/.env` (loaded via `python-dotenv`).

| Variable | Purpose |
|----------|---------|
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | Service role key (server-side only) |
| `GOOGLE_CLOUD_PROJECT` | GCP project for Vertex / Speech / TTS / GenAI |
| `GEMINI_MODEL_ID` | Primary LLM model ID (default `gemini-2.0-flash`) |
| `SEALION_API_KEY` | SEA-LION API key (optional — BM specialist fallback only) |
| `SEALION_API_BASE_URL` | Optional; default `https://api.sea-lion.ai/v1` |
| `CORS_ORIGINS` | Comma-separated allowed origins (default `http://localhost:3000`) |
| `BACKEND_PORT` | API port (default `8000`) |
| `NLLB_MODEL_PATH` | Optional NLLB model id or local path |

Frontend (e.g. `.env.local`):

| Variable | Purpose |
|----------|---------|
| `NEXT_PUBLIC_API_BASE_URL` | Backend base URL (default `http://localhost:8000`) |

Use **Google Application Default Credentials** (or the method your team uses) so the backend can call Vertex AI and other GCP APIs.

---

## NPM scripts

| Script | Description |
|--------|-------------|
| `npm run dev` | Next.js development server |
| `npm run build` / `npm start` | Production build and serve |
| `npm run lint` | ESLint |


Details: [`docs/DEMO_MAK_CIK_ROHANI.md`](docs/DEMO_MAK_CIK_ROHANI.md), [`docs/DEMO_BUDI.md`](docs/DEMO_BUDI.md), [`public/demo/README.md`](public/demo/README.md).

---

## API overview (backend)

Routers registered in `backend/main.py` include:

- `POST /api/query` — main RAG + simplify + semantic score + optional TTS payload
- `POST /api/transcribe` — speech to text
- `POST /api/synthesise` — text to speech
- `POST /api/ingest` — PDF → chunks → embeddings → Supabase
- `POST /api/extract-steps` — step list for UI cards
- `GET /api/health` — health / dependency checks

---

## Design & prototyping notes

- The frontend was initially scaffolded with **[v0](https://v0.app)**; the product logic lives in this repo’s **Next.js** and **FastAPI** layers.
- **[Continue working on v0 →](https://v0.app/chat/projects/prj_Xzg34VNqEXrOv5uRAlXSSdVORIMR)**

<a href="https://v0.app/chat/api/kiro/clone/jianwen0414/TheInclusiveCitizen"><img src="https://pdgvvgmkdvyeydso.public.blob.vercel-storage.com/open%20in%20kiro.svg?sanitize=true" alt="Open in Kiro" /></a>

---

## Learn more

- [Next.js Documentation](https://nextjs.org/docs)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Supabase Vector](https://supabase.com/docs/guides/ai)
