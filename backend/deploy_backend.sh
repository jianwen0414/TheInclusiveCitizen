#!/bin/sh
# deploy_backend.sh — Build and deploy the FastAPI backend to Cloud Run.
#
# Usage:
#   ./backend/deploy_backend.sh
#
# Prerequisites:
#   • gcloud CLI authenticated and PROJECT_ID set (gcloud config set project <id>)
#   • infra/setup.sh has been run at least once
#   • All Secret Manager secrets have been populated (see infra/setup.sh checklist)
#
# Run from the repository root.
set -e

REGION="${REGION:-us-central1}"
PROJECT_ID="$(gcloud config get-value project 2>/dev/null)"

if [ -z "$PROJECT_ID" ]; then
  echo "ERROR: No GCP project set. Run: gcloud config set project <project-id>" >&2
  exit 1
fi

IMAGE="gcr.io/${PROJECT_ID}/inclusive-citizen-backend"
COMMIT_SHA="$(git rev-parse --short HEAD 2>/dev/null || echo manual)"

echo "==> Building backend image: ${IMAGE}:${COMMIT_SHA}"
docker build \
  --tag "${IMAGE}:${COMMIT_SHA}" \
  --tag "${IMAGE}:latest" \
  --cache-from "${IMAGE}:latest" \
  ./backend

echo "==> Pushing image to Artifact Registry"
docker push --all-tags "${IMAGE}"

echo "==> Deploying to Cloud Run (region: ${REGION})"
# Substitute PROJECT_ID and COMMIT_SHA placeholders in the yaml before deploying.
sed \
  -e "s/PROJECT_ID/${PROJECT_ID}/g" \
  -e "s/COMMIT_SHA/${COMMIT_SHA}/g" \
  backend/cloudrun.yaml \
| gcloud run services replace - --region="${REGION}"

echo "==> Fetching deployed service URL"
SERVICE_URL="$(gcloud run services describe inclusive-citizen-backend \
  --region="${REGION}" \
  --format='value(status.url)')"

echo ""
echo "Backend deployed successfully."
echo "  URL: ${SERVICE_URL}"
echo ""
echo "Next step — set FASTAPI_BASE_URL in your Genkit server config:"
echo "  ./genkit-server/deploy_genkit.sh ${SERVICE_URL}"
