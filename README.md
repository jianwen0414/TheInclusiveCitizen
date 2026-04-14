# The Inclusive Citizen

A prototype **multilingual AI assistant** for Malaysian public-service information. Citizens can ask questions in **voice or text**—including **Malay dialects** (e.g. Kelantanese) and **languages such as Javanese / Bahasa Indonesia**—and receive **plain-language answers** grounded in **official PDFs**, with **source excerpts**, **readability hints**, and a **meaning-accuracy** signal aligned to the retrieved document text.

The UI supports **personas** (Elderly, Migrant Worker, Rural Community) that tune accessibility—for example, higher-contrast layout and slower text-to-speech for the elderly mode.

---

## Architecture

| Layer | Stack |
|--------|--------|
| **Frontend** | [Next.js](https://nextjs.org/) 16, React 19, Tailwind CSS, Radix UI — chat at [`/chat`](http://localhost:3000/chat) |
| **Backend** | [FastAPI](https://fastapi.tiangolo.com/) (`backend/`) — REST API |
| **Retrieval** | Google **Vertex AI Search** (Discovery Engine) — PDF upload to GCS, async indexing, multilingual extractive-answer retrieval (no pre-translation needed) |
| **Document store** | [Supabase](https://supabase.com/) PostgreSQL — `document_metadata` table for `doc_type` lookup and ingestion tracking |
| **Generation** | **Gemini 3.0 Flash** via Vertex AI (primary, all languages) + **SEA-LION v4** (optional BM specialist fallback) |
| **Speech** | Google Cloud **Speech-to-Text** and **Text-to-Speech** |
| **Optional** | Google Cloud **Translation** (advanced) and **NLLB-200** for some language paths; **sentence-transformers** for semantic scoring |

End-to-end query flow (simplified): **dialect / language detection** → **Vertex AI Search retrieval** → **grounded answer in the user’s language** → **simplification** → **semantic score vs. source chunk** → **TTS** (persona-aware speed).

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
- **Supabase** project with the `document_metadata` table (run `supabase/migrations/create_document_metadata.sql` first)
- **Google Cloud** project with Vertex AI Search (Discovery Engine), Vertex AI, Speech, TTS (and optionally Translation), plus application credentials
- **GCS bucket** for PDF uploads during ingestion (name set via `GCS_BUCKET_NAME`)
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

PDFs in `seed_docs/` (e.g. BSH eligibility, work permit renewal, MySejahtera, EPF) can be ingested with the backend running:

```powershell
cd seed_docs
.\ingest_all.ps1
```

Or use the Python bulk ingest script directly:

```bash
python scripts/bulk_ingest.py --folder seed_docs --base-url http://localhost:8000
```

This calls `POST /api/ingest` for each PDF. Ensure Vertex AI Search, GCS, and Supabase credentials are configured first. Documents are uploaded to GCS and queued for async indexing — they become searchable **5–30 minutes** after ingestion completes.

---

## Environment variables

Configure these in `backend/.env` (loaded via `python-dotenv`).

| Variable | Purpose |
|----------|---------|
| `GOOGLE_CLOUD_PROJECT` | GCP project for Vertex AI Search, Vertex AI, Speech, TTS, GenAI |
| `VERTEX_SEARCH_LOCATION` | Discovery Engine region (default `us-central1`) |
| `VERTEX_SEARCH_DATA_STORE_ID` | Discovery Engine data store ID (holds government PDFs) |
| `VERTEX_SEARCH_ENGINE_ID` | Discovery Engine search engine (app) ID |
| `GCS_BUCKET_NAME` | GCS bucket name for PDF uploads during ingestion |
| `SUPABASE_URL` | Supabase project URL — used for `document_metadata` table |
| `SUPABASE_SERVICE_ROLE_KEY` | Service role key (server-side only) — used for `document_metadata` read/write |
| `GEMINI_MODEL_ID` | Primary LLM model ID (default `gemini-2.0-flash`) |
| `SEALION_API_KEY` | SEA-LION API key (optional — BM specialist fallback only) |
| `SEALION_API_BASE_URL` | Optional; default `https://api.sea-lion.ai/v1` |
| `CORS_ORIGINS` | Comma-separated allowed origins (default `http://localhost:3000`) |
| `BACKEND_PORT` | API port (default `8000`) |
| `NLLB_MODEL_PATH` | Optional NLLB model id or local path |
| `GENKIT_SERVER_URL` | Genkit orchestration server URL (default `http://localhost:3001`) |

**`genkit-server/.env`** (required):

| Variable | Purpose |
|----------|---------|
| `GOOGLE_CLOUD_PROJECT` | GCP project for Vertex AI plugin |
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to service account JSON (or use ADC) |
| `VERTEX_AI_LOCATION` | Vertex AI region (default `us-central1`) |
| `FASTAPI_BASE_URL` | FastAPI backend URL (default `http://localhost:8000`) |
| `PORT` | Genkit server port (default `3001`) |

Frontend (e.g. `.env.local`):

| Variable | Purpose |
|----------|---------|
| `NEXT_PUBLIC_API_BASE_URL` | Backend base URL (default `http://localhost:8000`) |
| `GOOGLE_MAPS_API_KEY` | Google Maps Static API key — used **server-side only** by the `/api/static-map` proxy route to render map images in Government Office Cards; the key never reaches the browser. Card degrades gracefully (shows coordinates) without it. |

Use **Google Application Default Credentials** (or the method your team uses) so the backend can call Vertex AI and other GCP APIs.

---

## NPM scripts

| Script | Description |
|--------|-------------|
| `npm run dev` | Next.js development server only |
| `npm run dev:all` | All three servers in parallel (Next.js + FastAPI + Genkit) |
| `npm run dev:backend` | FastAPI backend only |
| `npm run dev:genkit` | Genkit TypeScript server only |
| `npm run build` / `npm start` | Production build and serve (Next.js) |
| `npm run lint` | ESLint |


Details: [`docs/DEMO_MAK_CIK_ROHANI.md`](docs/DEMO_MAK_CIK_ROHANI.md), [`docs/DEMO_BUDI.md`](docs/DEMO_BUDI.md), [`public/demo/README.md`](public/demo/README.md).

---

## Genkit flow architecture

The `/api/query` pipeline is orchestrated by **Firebase Genkit for TypeScript** running in a dedicated Node.js server (`genkit-server/`).

> **Why TypeScript?** The Genkit Python SDK (`genkit==0.5.2`) depends on `dotpromptz-handlebars`, a Rust-compiled extension with no Windows wheels. The TypeScript SDK is Google's officially supported Genkit target and works on all platforms.

**Three-server architecture:**

```
Next.js (port 3000) → FastAPI /api/query (port 8000) → Genkit server (port 3001)
                                                            ↓ tool calls
                                                       FastAPI internal pipeline endpoints
                                                       (detect-dialect, retrieve, generate,
                                                        simplify, score, transcribe, synthesise)
```

### Key files

| File | Role |
|------|------|
| [`genkit-server/src/index.ts`](genkit-server/src/index.ts) | Express server, Genkit init, `/flow/query` endpoint |
| [`genkit-server/src/flows/queryFlow.ts`](genkit-server/src/flows/queryFlow.ts) | `inclusive_citizen_query_flow` — orchestrates all tools |
| [`genkit-server/src/tools/`](genkit-server/src/tools/) | One `defineTool()` per pipeline step, calls FastAPI |
| [`backend/routers/pipeline.py`](backend/routers/pipeline.py) | Internal FastAPI endpoints called by Genkit tools |
| [`GENKIT_NOTES.md`](GENKIT_NOTES.md) | SDK API reference and platform limitations |

### Pipeline steps (each is a named Genkit tool → FastAPI endpoint)

1. `detect_dialect` → `POST /api/detect-dialect` — lingua-py + lexical markers
2. `retrieve_documents` → `POST /api/retrieve` — Vertex AI Search (Discovery Engine) semantic retrieval
3. `generate_bm_answer` → `POST /api/generate` — Gemini 2.0 Flash (primary) / SEA-LION v4 (BM fallback)
4. `translate_answer` → `POST /api/translate` — Google Cloud TLLM → NLLB-200
5. `simplify_answer` → `POST /api/simplify` — spaCy NER + LLM Grade 5–7 rewrite + Hijri date enrichment
6. `compute_semantic_score` → `POST /api/score` — sentence-transformers cross-lingual cosine similarity
7. `synthesise_speech` → `POST /api/synthesise` — Google Cloud TTS Neural2/Wavenet/Standard

### Genkit Developer UI

```bash
# Install CLI (one-time)
curl -sL cli.genkit.dev | bash

# Start Genkit server with Dev UI
cd genkit-server
cp .env.example .env   # fill in values
GENKIT_ENV=dev npm run dev
# Open http://localhost:4000
```

Every `/api/query` call produces a full pipeline trace in the Dev UI with per-step
inputs, outputs, and latency. See [GENKIT_NOTES.md](GENKIT_NOTES.md) for streaming
and SDK details.

---

## API overview (backend)

Routers registered in `backend/main.py` include:

- `POST /api/query` — proxies to Genkit server; returns full pipeline response
- `POST /api/transcribe` — speech to text
- `POST /api/synthesise` — text to speech
- `POST /api/translate` — text translation
- `POST /api/ingest` — PDF → GCS upload → Vertex AI Search async import → Supabase metadata
- `POST /api/extract-steps` — step list for UI cards
- `GET /api/health` — health / dependency checks

Internal pipeline endpoints (called by Genkit TS tools, not by the frontend):
- `POST /api/detect-dialect`, `POST /api/retrieve`, `POST /api/generate`
- `POST /api/simplify`, `POST /api/score`

---

## Design & prototyping notes

- The frontend was initially scaffolded with **[v0](https://v0.app)**; the product logic lives in this repo’s **Next.js** and **FastAPI** layers.
- **[Continue working on v0 →](https://v0.app/chat/projects/prj_Xzg34VNqEXrOv5uRAlXSSdVORIMR)**

<a href="https://v0.app/chat/api/kiro/clone/jianwen0414/TheInclusiveCitizen"><img src="https://pdgvvgmkdvyeydso.public.blob.vercel-storage.com/open%20in%20kiro.svg?sanitize=true" alt="Open in Kiro" /></a>

---

## Learn more

- [Next.js Documentation](https://nextjs.org/docs)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Vertex AI Search (Discovery Engine)](https://cloud.google.com/generative-ai-app-builder/docs/introduction)
- [Supabase Documentation](https://supabase.com/docs)

---

## Deployment

All three services run on **Google Cloud Run** and are deployed independently.
Cloud Run provides HTTPS automatically on `*.run.app` — no SSL configuration needed.

### Architecture

```
  Browser
    │  HTTPS
    ▼
┌──────────────────────────────┐
│  inclusive-citizen-frontend  │  Cloud Run · Next.js · 512 Mi
│  (Next.js standalone)        │  public (--allow-unauthenticated)
└──────────────┬───────────────┘
               │ POST /flow/query (HTTPS)
               ▼
┌──────────────────────────────┐
│  inclusive-citizen-genkit    │  Cloud Run · Node.js · 1 Gi
│  (Genkit TS orchestration)   │
└──────────────┬───────────────┘
               │ POST /api/* tool calls (HTTPS)
               ▼
┌──────────────────────────────┐
│  inclusive-citizen-backend   │  Cloud Run · FastAPI · 4 Gi / 2 CPU
│  (Python + ML models)        │
└──────────────┬───────────────┘
               │
    ┌──────────┴──────────┐
    ▼                     ▼
 Supabase              GCP APIs
 (document_metadata)   (Vertex AI, Vertex AI Search,
                        GCS, STT, TTS,
                        Translation, Secret Manager)
```

**Communication direction**: frontend → Genkit server → backend.
The backend never calls the Genkit server.

### One-time setup

Run once per GCP project before any deployment:

```sh
gcloud config set project <your-project-id>
sh infra/setup.sh
```

This enables required APIs, creates an Artifact Registry repository (`inclusive-citizen`),
creates Secret Manager secrets (empty shells), creates the `inclusive-citizen-sa` service
account, and grants it the necessary IAM roles.

After the script finishes, **populate the secret values manually**:

```sh
echo -n 'your-value' | gcloud secrets versions add SEALION_API_KEY --data-file=-
echo -n 'your-value' | gcloud secrets versions add SUPABASE_URL --data-file=-
echo -n 'your-value' | gcloud secrets versions add SUPABASE_SERVICE_ROLE_KEY --data-file=-
echo -n 'your-value' | gcloud secrets versions add VERTEX_SEARCH_DATA_STORE_ID --data-file=-
echo -n 'your-value' | gcloud secrets versions add VERTEX_SEARCH_ENGINE_ID --data-file=-
echo -n 'your-value' | gcloud secrets versions add GCS_BUCKET_NAME --data-file=-
```

Configure Docker for Artifact Registry:
```sh
gcloud auth configure-docker us-central1-docker.pkg.dev
```

### Deployment order

The services must be deployed in this order because each depends on the URL of the previous:

1. **Backend** — no external dependencies on the other two services
2. **Genkit server** — needs `FASTAPI_BASE_URL` pointing to the deployed backend
3. **Frontend** — `NEXT_PUBLIC_GENKIT_URL` is baked into the JS bundle at build time and must point to the deployed Genkit server

#### Deploy all at once (recommended)

```sh
sh infra/deploy_all.sh
```

#### Deploy individually

```sh
# 1. Backend
sh backend/deploy_backend.sh
# Prints: Set FASTAPI_BASE_URL=https://inclusive-citizen-backend-xxxx.run.app

# 2. Genkit server (pass the backend URL from step 1)
sh genkit-server/deploy_genkit.sh https://inclusive-citizen-backend-xxxx.run.app
# Prints: Set NEXT_PUBLIC_GENKIT_URL=https://inclusive-citizen-genkit-xxxx.run.app

# 3. Frontend (pass the Genkit URL from step 2)
sh frontend/deploy_frontend.sh https://inclusive-citizen-genkit-xxxx.run.app
```

Use the **individual scripts** when you are updating a single service; use
`infra/deploy_all.sh` for first-time or full redeploys.

### Updating FASTAPI_BASE_URL without a full redeploy

If the backend URL changes (e.g. after a project move), update it on the Genkit
Cloud Run service without rebuilding the image:

```sh
gcloud run services update inclusive-citizen-genkit \
  --region=us-central1 \
  --set-env-vars="FASTAPI_BASE_URL=https://new-backend-xxxx.run.app"
```

### NEXT_PUBLIC_ variables: build-time vs runtime

| Environment | How vars are set |
|-------------|-----------------|
| **Local dev** | `.env.local` in the repo root — read at dev-server startup |
| **Production** | Docker `--build-arg` flags passed during `docker build` — baked into the JS bundle by `next build` |

Injecting `NEXT_PUBLIC_*` as Cloud Run **runtime** env vars has **no effect** — Next.js
only reads them at build time. To change a `NEXT_PUBLIC_` value in production you must
rebuild the Docker image and redeploy the frontend.
