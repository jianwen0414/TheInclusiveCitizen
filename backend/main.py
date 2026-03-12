"""
The Inclusive Citizen — FastAPI Backend Entry Point
PRD Section 6.1: Three-tier architecture (presentation → intelligence → data)
PRD Section 7.1: All API endpoint registrations
"""

import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

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

from routers.health import router as health_router        # noqa: E402
from routers.ingest import router as ingest_router        # noqa: E402
from routers.query import router as query_router          # noqa: E402
from routers.translate import router as translate_router   # noqa: E402
from routers.transcribe import router as transcribe_router # noqa: E402
from routers.synthesise import router as synthesise_router # noqa: E402

app.include_router(health_router)
app.include_router(ingest_router)
app.include_router(query_router)
app.include_router(translate_router)
app.include_router(transcribe_router)
app.include_router(synthesise_router)


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("BACKEND_PORT", "8000"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
