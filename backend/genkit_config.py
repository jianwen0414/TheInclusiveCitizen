# NOTE: Genkit orchestration has migrated to genkit-server/ (TypeScript).
# This file is retained as logic reference and documentation only.
# The FastAPI endpoints called by the Genkit TS tools are in genkit-server/src/tools/.
"""
backend/genkit_config.py

Shared Firebase Genkit instance for The Inclusive Citizen backend.
Import `ai` from this module in all tool and flow files.
Never instantiate a second Genkit() — the registry is process-global.

Vertex AI plugin (genkit-plugin-google-genai) uses Google Application Default
Credentials, matching the existing google-cloud-aiplatform setup in this project.
"""
from __future__ import annotations

import os

from genkit import Genkit
from genkit.plugins.google_genai import VertexAI

ai = Genkit(
    plugins=[
        VertexAI(
            project=os.environ.get("GOOGLE_CLOUD_PROJECT", ""),
            location=os.environ.get("VERTEX_AI_LOCATION", "us-central1"),
        )
    ],
)
