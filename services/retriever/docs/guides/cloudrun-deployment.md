# Google Cloud Run Deployment Guide

Deploy Retriever to Google Cloud Run with Secret Manager.

## Prerequisites

- Google Cloud account with billing enabled
- `gcloud` CLI configured and authenticated
- Docker installed
- API keys ready:
  - OpenRouter API key ([get here](https://openrouter.ai/keys))
  - OpenAI API key ([get here](https://platform.openai.com/api-keys))

## Data Persistence

Data is stored in Supabase managed Postgres (with pgvector). No local data persistence is needed on the Cloud Run container — all state lives in the external database.

---

## Step 1: Set Environment Variables

```bash
export PROJECT_ID=your-project-id
export REGION=us-central1
```

## Step 2: Enable APIs

```bash
gcloud services enable \
    run.googleapis.com \
    artifactregistry.googleapis.com \
    secretmanager.googleapis.com \
    --project="$PROJECT_ID"
```

## Step 3: Create Artifact Registry Repository

```bash
gcloud artifacts repositories create retriever \
    --repository-format=docker \
    --location="$REGION" \
    --description="Retriever container images" \
    --project="$PROJECT_ID"
```

## Step 4: Create Secrets

```bash
# Create secrets with placeholder values
echo -n "placeholder" | gcloud secrets create retriever-openrouter-api-key --data-file=- --project="$PROJECT_ID"
echo -n "placeholder" | gcloud secrets create retriever-openai-api-key --data-file=- --project="$PROJECT_ID"
echo -n "placeholder" | gcloud secrets create retriever-database-url --data-file=- --project="$PROJECT_ID"
echo -n "placeholder" | gcloud secrets create retriever-supabase-url --data-file=- --project="$PROJECT_ID"
echo -n "placeholder" | gcloud secrets create retriever-supabase-anon-key --data-file=- --project="$PROJECT_ID"
```

## Step 5: Update Secrets with Real Values

```bash
# OpenRouter API key
echo -n 'sk-or-v1-your-key-here' | gcloud secrets versions add retriever-openrouter-api-key --data-file=- --project="$PROJECT_ID"

# OpenAI API key
echo -n 'sk-your-key-here' | gcloud secrets versions add retriever-openai-api-key --data-file=- --project="$PROJECT_ID"

# Database URL (Supabase connection pooler)
echo -n 'postgresql+asyncpg://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres' | gcloud secrets versions add retriever-database-url --data-file=- --project="$PROJECT_ID"

# Supabase URL
echo -n 'https://[ref].supabase.co' | gcloud secrets versions add retriever-supabase-url --data-file=- --project="$PROJECT_ID"

# Supabase anon key
echo -n 'your-anon-key' | gcloud secrets versions add retriever-supabase-anon-key --data-file=- --project="$PROJECT_ID"
```

## Step 6: Grant Cloud Run Access to Secrets

```bash
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")

for SECRET in retriever-openrouter-api-key retriever-openai-api-key retriever-database-url retriever-supabase-url retriever-supabase-anon-key; do
  gcloud secrets add-iam-policy-binding $SECRET \
      --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
      --role="roles/secretmanager.secretAccessor" \
      --project="$PROJECT_ID"
done
```

## Step 7: Deploy to Cloud Run (Source-Based)

The simplest approach uses `--source` to build and deploy in one step:

```bash
gcloud run deploy retriever \
    --source ./backend \
    --region $REGION \
    --project $PROJECT_ID \
    --platform managed \
    --allow-unauthenticated \
    --memory 1Gi \
    --cpu 1 \
    --min-instances 0 \
    --max-instances 10 \
    --timeout 60 \
    --concurrency 80 \
    --set-env-vars "DEBUG=false" \
    --set-secrets "OPENROUTER_API_KEY=retriever-openrouter-api-key:latest,OPENAI_API_KEY=retriever-openai-api-key:latest,DATABASE_URL=retriever-database-url:latest,SUPABASE_URL=retriever-supabase-url:latest,SUPABASE_ANON_KEY=retriever-supabase-anon-key:latest"
```

Skip to Step 11 for verification.

### Alternative: Manual Image Build

If you prefer to build the image locally:

```bash
docker build --platform linux/amd64 -t $REGION-docker.pkg.dev/$PROJECT_ID/retriever/retriever:latest ./backend
```

## Step 8: Authenticate Docker with Artifact Registry

```bash
gcloud auth print-access-token | docker login -u oauth2accesstoken --password-stdin $REGION-docker.pkg.dev
```

## Step 9: Push Image

```bash
docker push $REGION-docker.pkg.dev/$PROJECT_ID/retriever/retriever:latest
```

## Step 10: Deploy to Cloud Run (Manual Image)

```bash
gcloud run deploy retriever \
    --image $REGION-docker.pkg.dev/$PROJECT_ID/retriever/retriever:latest \
    --region $REGION \
    --project $PROJECT_ID \
    --platform managed \
    --allow-unauthenticated \
    --memory 1Gi \
    --cpu 1 \
    --min-instances 0 \
    --max-instances 10 \
    --timeout 60 \
    --concurrency 80 \
    --set-env-vars "DEBUG=false" \
    --set-secrets "OPENROUTER_API_KEY=retriever-openrouter-api-key:latest,OPENAI_API_KEY=retriever-openai-api-key:latest,DATABASE_URL=retriever-database-url:latest,SUPABASE_URL=retriever-supabase-url:latest,SUPABASE_ANON_KEY=retriever-supabase-anon-key:latest"
```

## Step 11: Verify Deployment

```bash
# Get service URL
SERVICE_URL=$(gcloud run services describe retriever --region $REGION --project $PROJECT_ID --format="value(status.url)")
echo "Service URL: $SERVICE_URL"

# Test health endpoint
curl $SERVICE_URL/health
```

## Step 12: Create Admin User

Admin users are created in the Supabase dashboard (Authentication > Users). Set `is_admin: true` in the user's `app_metadata` to grant admin privileges:

```json
{
  "is_admin": true
}
```

---

## Redeployment

After code changes, redeploy from source:

```bash
gcloud run deploy retriever \
    --source ./backend \
    --region $REGION \
    --project $PROJECT_ID
```

Or if using manual image builds, repeat steps 7-10:

```bash
docker build --platform linux/amd64 -t $REGION-docker.pkg.dev/$PROJECT_ID/retriever/retriever:latest ./backend
gcloud auth print-access-token | docker login -u oauth2accesstoken --password-stdin $REGION-docker.pkg.dev
docker push $REGION-docker.pkg.dev/$PROJECT_ID/retriever/retriever:latest
gcloud run deploy retriever \
    --image $REGION-docker.pkg.dev/$PROJECT_ID/retriever/retriever:latest \
    --region $REGION \
    --project $PROJECT_ID
```

---

## Useful Commands

```bash
# View logs
gcloud run services logs read retriever --region $REGION --project $PROJECT_ID --limit 50

# Get service URL
gcloud run services describe retriever --region $REGION --project $PROJECT_ID --format="value(status.url)"

# Delete service
gcloud run services delete retriever --region $REGION --project $PROJECT_ID

# Update a secret
echo -n 'new-value' | gcloud secrets versions add retriever-openrouter-api-key --data-file=- --project=$PROJECT_ID
```

---

## Cost Estimate

Cloud Run free tier includes:
- 2M requests/month
- 360,000 GB-seconds/month

Estimated monthly cost for demo workload: **$5-15**

Scales to zero when idle (no cost).
