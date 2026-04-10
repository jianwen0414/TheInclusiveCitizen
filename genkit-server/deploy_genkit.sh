#!/bin/sh
# deploy_genkit.sh — Build and deploy the Genkit TypeScript server to Cloud Run.
#
# Usage:
#   ./genkit-server/deploy_genkit.sh <fastapi-backend-url>
#
# Example:
#   ./genkit-server/deploy_genkit.sh https://inclusive-citizen-backend-xxxx.run.app
#
# Prerequisites:
#   • gcloud CLI authenticated and PROJECT_ID set
#   • Backend already deployed (run deploy_backend.sh first)
#   • infra/setup.sh has been run at least once
#
# Run from the repository root.
set -e

FASTAPI_BASE_URL="${1:?ERROR: FASTAPI_BASE_URL is required. Usage: ./genkit-server/deploy_genkit.sh <fastapi-url>}"
REGION="${REGION:-us-central1}"
PROJECT_ID="$(gcloud config get-value project 2>/dev/null)"

if [ -z "$PROJECT_ID" ]; then
  echo "ERROR: No GCP project set. Run: gcloud config set project <project-id>" >&2
  exit 1
fi

IMAGE="gcr.io/${PROJECT_ID}/inclusive-citizen-genkit"
COMMIT_SHA="$(git rev-parse --short HEAD 2>/dev/null || echo manual)"

echo "==> Building Genkit server image: ${IMAGE}:${COMMIT_SHA}"
docker build \
  --tag "${IMAGE}:${COMMIT_SHA}" \
  --tag "${IMAGE}:latest" \
  --cache-from "${IMAGE}:latest" \
  ./genkit-server

echo "==> Pushing image to Artifact Registry"
docker push --all-tags "${IMAGE}"

echo "==> Deploying to Cloud Run (region: ${REGION})"
sed \
  -e "s/PROJECT_ID/${PROJECT_ID}/g" \
  -e "s/COMMIT_SHA/${COMMIT_SHA}/g" \
  -e "s|FASTAPI_BASE_URL_PLACEHOLDER|${FASTAPI_BASE_URL}|g" \
  genkit-server/cloudrun.yaml \
| gcloud run services replace - --region="${REGION}"

echo "==> Fetching deployed service URL"
SERVICE_URL="$(gcloud run services describe inclusive-citizen-genkit \
  --region="${REGION}" \
  --format='value(status.url)')"

echo ""
echo "Genkit server deployed successfully."
echo "  URL:              ${SERVICE_URL}"
echo "  FASTAPI_BASE_URL: ${FASTAPI_BASE_URL}"
echo ""
echo "Next step — pass this URL to the frontend deploy script:"
echo "  ./frontend/deploy_frontend.sh ${SERVICE_URL}"
echo ""
echo "To update FASTAPI_BASE_URL without a full redeploy:"
echo "  gcloud run services update inclusive-citizen-genkit \\"
echo "    --region=${REGION} \\"
echo "    --set-env-vars=FASTAPI_BASE_URL=<new-backend-url>"
