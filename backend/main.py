"""
The Inclusive Citizen — FastAPI Backend Entry Point
PRD Section 6.1: Three-tier architecture (presentation → intelligence → data)
PRD Section 7.1: All API endpoint registrations
"""

import logging
import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

# Ensure our application loggers emit INFO regardless of uvicorn's root
# logger configuration. basicConfig is a no-op if uvicorn added handlers
# first, so we forcibly set levels on each module logger.
_APP_LOGGERS = [
    "routers.query",
    "routers.steps",
    "routers.flood",
    "services.rag_pipeline",
    "services.llm_service",
    "services.simplifier",
    "services.semantic_scorer",
    "services.translation_service",
    "services.stt_service",
    "services.tts_service",
]
for _name in _APP_LOGGERS:
    logging.getLogger(_name).setLevel(logging.INFO)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)

app = FastAPI(
    title="The Inclusive Citizen API",
    description="Multilingual AI assistant for Malaysian government public services",
    version="1.0.0",
)

# CORS — PRD constraint #6: accept requests from http://localhost:3000
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Router registration (PRD Section 7.1, Table 10) ──────

from routers.flood import router as flood_router             # noqa: E402
from routers.health import router as health_router           # noqa: E402
from routers.ingest import router as ingest_router           # noqa: E402
from routers.pipeline import router as pipeline_router       # noqa: E402
from routers.query import router as query_router             # noqa: E402
from routers.steps import router as steps_router             # noqa: E402
from routers.translate import router as translate_router     # noqa: E402
from routers.transcribe import router as transcribe_router   # noqa: E402
from routers.synthesise import router as synthesise_router   # noqa: E402

app.include_router(flood_router)
app.include_router(health_router)
app.include_router(ingest_router)
app.include_router(pipeline_router)
app.include_router(query_router)
app.include_router(steps_router)
app.include_router(translate_router)
app.include_router(transcribe_router)
app.include_router(synthesise_router)

_startup_logger = logging.getLogger("startup")


@app.on_event("startup")
async def _warm_up_models():
    """
    Eagerly load slow models so the first real query isn't penalised.
    Runs in the background so the server accepts requests immediately.
    """
    import asyncio

    async def _load():
        try:
            _startup_logger.info("Warming up sentence-transformers model…")
            from services.semantic_scorer import _load_model
            _load_model()
            _startup_logger.info("sentence-transformers model ready.")
        except Exception as exc:
            _startup_logger.warning(f"Model warm-up failed (non-fatal): {exc}")

    asyncio.create_task(_load())


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("BACKEND_PORT", "8000"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
