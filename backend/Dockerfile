# ── The Inclusive Citizen — Backend (FastAPI) ─────────────────────────────────
# Base image: Python 3.11 slim (Debian Bookworm)
FROM python:3.11-slim

# System dependencies:
#   build-essential — compiles C extensions (e.g. sentencepiece, tokenizers)
#   libgomp1        — OpenMP runtime required by PyTorch (NLLB-200, torch)
#   libglib2.0-0    — glib2 shared library required by PyMuPDF
#   libgl1-mesa-glx — OpenGL runtime required by PyMuPDF (fitz)
#   curl            — health-check and download utilities
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgomp1 \
    libglib2.0-0 \
    libgl1 \
    curl \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies before copying source so Docker layer cache is
# reused on source-only changes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download the spaCy multilingual NER model at build time so the first request
# is not penalised by a cold download.
RUN python -m spacy download xx_ent_wiki_sm

# Pre-download the sentence-transformers model used by semantic_scorer.py.
# Without this the container downloads ~470 MB from HuggingFace on every cold
# start, which triggers rate-limiting (HTTP 429) and causes Cloud Run's startup
# probe to time out (DEADLINE_EXCEEDED).  Baking the weights into the image
# trades image size for reliable, fast startup.
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')"

# ── NLLB-200 model weights ────────────────────────────────────────────────────
# The NLLB-200 distilled model (~2.4 GB) is NOT bundled in this image.
# Bundling it would make the image prohibitively large and slow to pull.
#
# At runtime, set NLLB_MODEL_PATH to one of:
#   • A HuggingFace model ID:  facebook/nllb-200-distilled-600M
#     (transformers downloads on first use; weights are cached in /root/.cache)
#   • A GCS path mounted via Cloud Storage FUSE or gcsfuse sidecar:
#     /mnt/models/nllb-200-distilled-600M
#
# The translation_service.py already reads this env var via:
#   model_path = os.getenv("NLLB_MODEL_PATH", "facebook/nllb-200-distilled-600M")
# ─────────────────────────────────────────────────────────────────────────────

# Copy application source.
COPY . .

# Cloud Run injects PORT=8080 by default; expose it here for documentation.
EXPOSE 8080

# Use PORT env var so Cloud Run can override if needed; default to 8080.
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}"]
