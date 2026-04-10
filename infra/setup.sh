#!/bin/sh
# infra/setup.sh — One-time GCP infrastructure setup for The Inclusive Citizen.
#
# Run this ONCE before any service is deployed.  It is safe to re-run; most
# gcloud commands are idempotent (they return an error only if the resource
# already exists with incompatible config, which we handle with || true).
#
# Usage:
#   gcloud config set project <your-project-id>
#   sh infra/setup.sh
#
# Run from the repository root.
set -e

PROJECT_ID="$(gcloud config get-value project 2>/dev/null)"
if [ -z "$PROJECT_ID" ]; then
  echo "ERROR: No GCP project set. Run: gcloud config set project <project-id>" >&2
  exit 1
fi
PROJECT_NUMBER="$(gcloud projects describe "${PROJECT_ID}" --format='value(projectNumber)')"
REGION="${REGION:-us-central1}"
SA_NAME="inclusive-citizen-sa"
SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
REGISTRY_REPO="inclusive-citizen"

echo "==================================================================="
echo " The Inclusive Citizen — Infrastructure Setup"
echo " Project : ${PROJECT_ID}"
echo " Region  : ${REGION}"
echo "==================================================================="

# ── 1. Enable required GCP APIs ───────────────────────────────────────────────
echo ""
echo "==> Enabling GCP APIs (this may take a minute)..."
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  secretmanager.googleapis.com \
  aiplatform.googleapis.com \
  speech.googleapis.com \
  texttospeech.googleapis.com \
  translate.googleapis.com \
  discoveryengine.googleapis.com \
  storage.googleapis.com \
  --project="${PROJECT_ID}"

# ── 2. Create Artifact Registry repository ────────────────────────────────────
echo ""
echo "==> Creating Artifact Registry repository: ${REGISTRY_REPO}"
gcloud artifacts repositories create "${REGISTRY_REPO}" \
  --repository-format=docker \
  --location="${REGION}" \
  --description="Docker images for The Inclusive Citizen" \
  --project="${PROJECT_ID}" 2>/dev/null || echo "    (already exists — skipping)"

# ── 3. Create Secret Manager secrets (empty — populate values manually) ───────
echo ""
echo "==> Creating Secret Manager secrets (empty shells)..."
for SECRET in \
  SEALION_API_KEY \
  SUPABASE_URL \
  SUPABASE_SERVICE_ROLE_KEY \
  VERTEX_SEARCH_DATA_STORE_ID \
  VERTEX_SEARCH_ENGINE_ID \
  GCS_BUCKET_NAME
do
  gcloud secrets create "${SECRET}" \
    --replication-policy=automatic \
    --project="${PROJECT_ID}" 2>/dev/null \
    || echo "    ${SECRET} already exists — skipping"
done

# ── 4. Create service account ─────────────────────────────────────────────────
echo ""
echo "==> Creating service account: ${SA_EMAIL}"
gcloud iam service-accounts create "${SA_NAME}" \
  --display-name="Inclusive Citizen Cloud Run SA" \
  --project="${PROJECT_ID}" 2>/dev/null || echo "    (already exists — skipping)"

# ── 5. Grant IAM roles to the service account ─────────────────────────────────
echo ""
echo "==> Granting IAM roles to ${SA_EMAIL}..."
for ROLE in \
  roles/aiplatform.user \
  roles/discoveryengine.viewer \
  roles/storage.objectViewer \
  roles/secretmanager.secretAccessor \
  roles/speech.client \
  roles/cloudtranslate.user \
  roles/texttospeech.client
do
  gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="${ROLE}" \
    --condition=None \
    --quiet
  echo "    Granted ${ROLE}"
done

# Allow Cloud Build to deploy Cloud Run services.
gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
  --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
  --role="roles/run.admin" \
  --condition=None \
  --quiet
gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
  --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser" \
  --condition=None \
  --quiet

# ── Done ──────────────────────────────────────────────────────────────────────
echo ""
echo "==================================================================="
echo " Setup complete.  Manual steps required before deploying:"
echo "==================================================================="
echo ""
echo " 1. Populate Secret Manager secrets with real values:"
echo "      gcloud secrets versions add SEALION_API_KEY --data-file=-"
echo "      gcloud secrets versions add SUPABASE_URL --data-file=-"
echo "      gcloud secrets versions add SUPABASE_SERVICE_ROLE_KEY --data-file=-"
echo "      gcloud secrets versions add VERTEX_SEARCH_DATA_STORE_ID --data-file=-"
echo "      gcloud secrets versions add VERTEX_SEARCH_ENGINE_ID --data-file=-"
echo "      gcloud secrets versions add GCS_BUCKET_NAME --data-file=-"
echo "    (pipe the secret value into stdin, e.g.: echo -n 'value' | ...)"
echo ""
echo " 2. Configure Docker to push to Artifact Registry:"
echo "      gcloud auth configure-docker ${REGION}-docker.pkg.dev"
echo ""
echo " 3. Deploy services in order (each depends on the previous URL):"
echo "      sh backend/deploy_backend.sh"
echo "      sh genkit-server/deploy_genkit.sh <backend-url>"
echo "      sh frontend/deploy_frontend.sh <genkit-url>"
echo ""
echo "    Or run all at once:"
echo "      sh infra/deploy_all.sh"
echo ""
echo " 4. Update CORS_ORIGINS on the backend once the frontend URL is known:"
echo "      gcloud run services update inclusive-citizen-backend \\"
echo "        --region=${REGION} \\"
echo "        --set-env-vars=CORS_ORIGINS=https://inclusive-citizen-frontend-xxxx.run.app"
echo ""
