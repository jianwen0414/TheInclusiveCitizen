#!/bin/sh
# infra/deploy_all.sh — Orchestrate a full deployment of all three services.
#
# Usage:
#   sh infra/deploy_all.sh
#
# Optional env vars (for frontend NEXT_PUBLIC_ bake-in):
#   NEXT_PUBLIC_API_BASE_URL      — FastAPI backend public URL (auto-detected if blank)
#   NEXT_PUBLIC_SUPABASE_URL      — Supabase project URL
#   NEXT_PUBLIC_SUPABASE_ANON_KEY — Supabase anon key
#
# Prerequisites:
#   • infra/setup.sh has been run and secrets populated
#   • gcloud authenticated with PROJECT_ID set
#   • Docker available and configured for Artifact Registry
#
# Run from the repository root.
set -e

REGION="${REGION:-us-central1}"
PROJECT_ID="$(gcloud config get-value project 2>/dev/null)"

if [ -z "$PROJECT_ID" ]; then
  echo "ERROR: No GCP project set. Run: gcloud config set project <project-id>" >&2
  exit 1
fi

echo "==================================================================="
echo " The Inclusive Citizen — Full Deployment"
echo " Project : ${PROJECT_ID} | Region: ${REGION}"
echo "==================================================================="

# ── Step 1: Deploy backend ────────────────────────────────────────────────────
echo ""
echo "─── [1/3] Deploying backend (FastAPI) ───────────────────────────────"
sh backend/deploy_backend.sh

BACKEND_URL="$(gcloud run services describe inclusive-citizen-backend \
  --region="${REGION}" \
  --format='value(status.url)')"
echo "    Backend URL: ${BACKEND_URL}"

# ── Step 2: Deploy Genkit server ──────────────────────────────────────────────
echo ""
echo "─── [2/3] Deploying Genkit server (TypeScript) ──────────────────────"
sh genkit-server/deploy_genkit.sh "${BACKEND_URL}"

GENKIT_URL="$(gcloud run services describe inclusive-citizen-genkit \
  --region="${REGION}" \
  --format='value(status.url)')"
echo "    Genkit URL: ${GENKIT_URL}"

# ── Step 3: Deploy frontend ───────────────────────────────────────────────────
echo ""
echo "─── [3/3] Deploying frontend (Next.js) ──────────────────────────────"
# If NEXT_PUBLIC_API_BASE_URL is not set, default to the backend URL.
NEXT_PUBLIC_API_BASE_URL="${NEXT_PUBLIC_API_BASE_URL:-${BACKEND_URL}}"
export NEXT_PUBLIC_API_BASE_URL
export NEXT_PUBLIC_SUPABASE_URL
export NEXT_PUBLIC_SUPABASE_ANON_KEY

sh frontend/deploy_frontend.sh "${GENKIT_URL}"

FRONTEND_URL="$(gcloud run services describe inclusive-citizen-frontend \
  --region="${REGION}" \
  --format='value(status.url)')"

# ── Summary ───────────────────────────────────────────────────────────────────
echo ""
echo "==================================================================="
echo " Deployment complete"
echo "==================================================================="
echo ""
printf "  %-28s %s\n" "Service" "URL"
printf "  %-28s %s\n" "───────────────────────────" "──────────────────────────────────────────"
printf "  %-28s %s\n" "Backend (FastAPI)"         "${BACKEND_URL}"
printf "  %-28s %s\n" "Genkit server (TS)"        "${GENKIT_URL}"
printf "  %-28s %s\n" "Frontend (Next.js)"        "${FRONTEND_URL}"
echo ""
echo "Open ${FRONTEND_URL}/chat to verify the full pipeline."
echo ""
echo "Post-deployment checklist:"
echo "  • Update CORS_ORIGINS on the backend to allow ${FRONTEND_URL}"
echo "    gcloud run services update inclusive-citizen-backend \\"
echo "      --region=${REGION} \\"
echo "      --set-env-vars=CORS_ORIGINS=${FRONTEND_URL}"
