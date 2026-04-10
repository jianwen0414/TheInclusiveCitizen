#!/bin/sh
# deploy_frontend.sh — Build and deploy the Next.js frontend to Cloud Run.
#
# Usage:
#   ./frontend/deploy_frontend.sh <genkit-server-url> [options]
#
# Example:
#   ./frontend/deploy_frontend.sh https://inclusive-citizen-genkit-xxxx.run.app
#
# Optional environment variables (can also be set in shell before running):
#   NEXT_PUBLIC_API_BASE_URL      — FastAPI backend URL (for direct audio calls)
#   NEXT_PUBLIC_SUPABASE_URL      — Supabase project URL
#   NEXT_PUBLIC_SUPABASE_ANON_KEY — Supabase anon key
#
# IMPORTANT: NEXT_PUBLIC_ variables are baked into the JS bundle at build time.
# Changing them requires a rebuild (re-running this script).
#
# Run from the repository root.
set -e

NEXT_PUBLIC_GENKIT_URL="${1:?ERROR: Genkit server URL required. Usage: ./frontend/deploy_frontend.sh <genkit-url>}"
REGION="${REGION:-us-central1}"
PROJECT_ID="$(gcloud config get-value project 2>/dev/null)"

if [ -z "$PROJECT_ID" ]; then
  echo "ERROR: No GCP project set. Run: gcloud config set project <project-id>" >&2
  exit 1
fi

# Prompt for any missing NEXT_PUBLIC_ vars.
NEXT_PUBLIC_API_BASE_URL="${NEXT_PUBLIC_API_BASE_URL:-}"
NEXT_PUBLIC_SUPABASE_URL="${NEXT_PUBLIC_SUPABASE_URL:-}"
NEXT_PUBLIC_SUPABASE_ANON_KEY="${NEXT_PUBLIC_SUPABASE_ANON_KEY:-}"

IMAGE="gcr.io/${PROJECT_ID}/inclusive-citizen-frontend"
COMMIT_SHA="$(git rev-parse --short HEAD 2>/dev/null || echo manual)"

echo "==> Building frontend image: ${IMAGE}:${COMMIT_SHA}"
echo "    NEXT_PUBLIC_GENKIT_URL=${NEXT_PUBLIC_GENKIT_URL}"
docker build \
  --file frontend/Dockerfile \
  --tag "${IMAGE}:${COMMIT_SHA}" \
  --tag "${IMAGE}:latest" \
  --cache-from "${IMAGE}:latest" \
  --build-arg "NEXT_PUBLIC_GENKIT_URL=${NEXT_PUBLIC_GENKIT_URL}" \
  --build-arg "NEXT_PUBLIC_API_BASE_URL=${NEXT_PUBLIC_API_BASE_URL}" \
  --build-arg "NEXT_PUBLIC_SUPABASE_URL=${NEXT_PUBLIC_SUPABASE_URL}" \
  --build-arg "NEXT_PUBLIC_SUPABASE_ANON_KEY=${NEXT_PUBLIC_SUPABASE_ANON_KEY}" \
  .

echo "==> Pushing image to Artifact Registry"
docker push --all-tags "${IMAGE}"

echo "==> Deploying to Cloud Run (region: ${REGION})"
# Allow unauthenticated access for the public-facing UI.
sed \
  -e "s/PROJECT_ID/${PROJECT_ID}/g" \
  -e "s/COMMIT_SHA/${COMMIT_SHA}/g" \
  frontend/cloudrun.yaml \
| gcloud run services replace - --region="${REGION}"

gcloud run services add-iam-policy-binding inclusive-citizen-frontend \
  --region="${REGION}" \
  --member="allUsers" \
  --role="roles/run.invoker"

echo "==> Fetching deployed service URL"
SERVICE_URL="$(gcloud run services describe inclusive-citizen-frontend \
  --region="${REGION}" \
  --format='value(status.url)')"

echo ""
echo "Frontend deployed successfully."
echo "  URL: ${SERVICE_URL}"
echo ""
echo "Open ${SERVICE_URL}/chat to verify the deployment."
