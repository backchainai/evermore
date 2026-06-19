# Deployment Guide

How to deploy Retriever to production.

## Architecture

| Component | Platform | Method |
|-----------|----------|--------|
| Backend | Google Cloud Run | `gcloud run deploy --source ./backend` |
| Frontend | Cloudflare Pages | Git-connected or `wrangler pages deploy` |
| Database | Supabase | Managed Postgres + pgvector |
| Auth | Supabase Auth | Managed, JWKS endpoint for JWT verification |
| LLM Gateway | Cloudflare AI Gateway | Routes OpenRouter + OpenAI traffic |

## Prerequisites

- Google Cloud account with billing enabled
- `gcloud` CLI configured and authenticated
- Cloudflare account (for Pages + AI Gateway)
- Supabase project created
- API keys ready:
  - OpenRouter API key ([get here](https://openrouter.ai/keys))
  - OpenAI API key ([get here](https://platform.openai.com/api-keys))

---

## Backend: Cloud Run

### One-Command Deploy

```bash
gcloud run deploy retriever \
    --source ./backend \
    --region us-central1 \
    --project $PROJECT_ID \
    --allow-unauthenticated \
    --memory 1Gi \
    --cpu 1 \
    --min-instances 0 \
    --max-instances 10 \
    --timeout 60 \
    --set-env-vars "DEBUG=false" \
    --set-secrets "OPENROUTER_API_KEY=retriever-openrouter-api-key:latest,OPENAI_API_KEY=retriever-openai-api-key:latest,DATABASE_URL=retriever-database-url:latest"
```

This builds the container from source using Cloud Build and deploys it in one step. No local Docker build required.

### Secret Manager Setup

Create secrets before first deploy:

```bash
export PROJECT_ID=your-project-id

# Create secrets
echo -n "placeholder" | gcloud secrets create retriever-openrouter-api-key --data-file=- --project="$PROJECT_ID"
echo -n "placeholder" | gcloud secrets create retriever-openai-api-key --data-file=- --project="$PROJECT_ID"
echo -n "placeholder" | gcloud secrets create retriever-database-url --data-file=- --project="$PROJECT_ID"

# Update with real values
echo -n 'sk-or-v1-your-key' | gcloud secrets versions add retriever-openrouter-api-key --data-file=- --project="$PROJECT_ID"
echo -n 'sk-your-key' | gcloud secrets versions add retriever-openai-api-key --data-file=- --project="$PROJECT_ID"
echo -n 'postgresql+asyncpg://...' | gcloud secrets versions add retriever-database-url --data-file=- --project="$PROJECT_ID"

# Grant Cloud Run access
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
for SECRET in retriever-openrouter-api-key retriever-openai-api-key retriever-database-url; do
  gcloud secrets add-iam-policy-binding $SECRET \
      --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
      --role="roles/secretmanager.secretAccessor" \
      --project="$PROJECT_ID"
done
```

### Verify Deployment

```bash
SERVICE_URL=$(gcloud run services describe retriever --region us-central1 --project $PROJECT_ID --format="value(status.url)")
curl $SERVICE_URL/health
```

See [Cloud Run Deployment Guide](./cloudrun-deployment.md) for detailed step-by-step instructions.

---

## Frontend: Cloudflare Pages

### Git-Connected Deploy (Recommended)

1. Go to Cloudflare Dashboard > Pages
2. Connect your GitHub repository
3. Configure build settings:
   - **Build command:** `npm run build`
   - **Build output directory:** `.svelte-kit/cloudflare`
   - **Root directory:** `frontend`
4. Add environment variables:
   - `PUBLIC_SUPABASE_URL`
   - `PUBLIC_SUPABASE_ANON_KEY`
   - `PUBLIC_API_BASE_URL` (Cloud Run backend URL)

### Manual Deploy

```bash
cd frontend
npm run build
npx wrangler pages deploy .svelte-kit/cloudflare --project-name=retriever
```

---

## Database: Supabase

### Setup

1. Create a Supabase project at [supabase.com](https://supabase.com)
2. Enable pgvector extension: SQL Editor > `CREATE EXTENSION IF NOT EXISTS vector;`
3. Run Alembic migrations against the Supabase database:
   ```bash
   cd backend
   DATABASE_URL="postgresql+asyncpg://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres" \
       uv run alembic upgrade head
   ```
4. Configure RLS policies for the `messages`, `documents`, and `users` tables

### Connection String

Use the Supabase connection pooler URL (port 6543) for the `DATABASE_URL` environment variable. Format:

```
postgresql+asyncpg://postgres.[project-ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres
```

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | Supabase Postgres connection string (asyncpg) |
| `OPENROUTER_API_KEY` | Yes | OpenRouter API key for LLM |
| `OPENAI_API_KEY` | Yes | OpenAI API key for embeddings |
| `SUPABASE_URL` | Yes | Supabase project URL |
| `SUPABASE_ANON_KEY` | Yes | Supabase anonymous key |
| `CLOUDFLARE_ACCOUNT_ID` | No | Cloudflare account ID (enables AI Gateway) |
| `CLOUDFLARE_GATEWAY_ID` | No | Cloudflare gateway ID (enables AI Gateway) |
| `LANGFUSE_SECRET_KEY` | No | Langfuse secret key (LLM observability) |
| `LANGFUSE_PUBLIC_KEY` | No | Langfuse public key |
| `LANGFUSE_HOST` | No | Langfuse host URL |
| `GCP_PROJECT_ID` | No | GCP project (enables Cloud Trace exporter) |
| `ENVIRONMENT` | No | `development` or `production` |
| `LOG_LEVEL` | No | `DEBUG`, `INFO`, `WARNING`, `ERROR` |

---

## Production Checklist

- [ ] Supabase project created with pgvector extension enabled
- [ ] Alembic migrations applied to Supabase database
- [ ] RLS policies configured for all tables
- [ ] GCP Secret Manager secrets created and populated
- [ ] Backend deployed to Cloud Run: `gcloud run deploy --source ./backend`
- [ ] Frontend deployed to Cloudflare Pages
- [ ] Health check responds: `GET /health`
- [ ] Admin user created in Supabase Auth dashboard
- [ ] Can log in and ask a question
- [ ] SSL certificates active (automatic on both platforms)
- [ ] Cloudflare AI Gateway configured (optional but recommended)
- [ ] Langfuse configured for LLM observability (optional)
- [ ] GCP Cloud Trace enabled for distributed tracing (optional)

---

## Monitoring

### Health Checks

```
GET /health    → Liveness + DB + pgvector checks
```

### Logs

```bash
# Cloud Run logs
gcloud run services logs read retriever --region us-central1 --project $PROJECT_ID --limit 50
```

### Observability

- **Structured logs:** JSON via structlog (visible in Cloud Run logs)
- **Distributed tracing:** GCP Cloud Trace (if `GCP_PROJECT_ID` set) or Jaeger (if `OTEL_EXPORTER_OTLP_ENDPOINT` set)
- **LLM observability:** Langfuse (if credentials configured)

---

## Scaling

Cloud Run auto-scales from 0 to `max-instances`. For MVP scale (50-100 volunteers), default settings are sufficient.

If needed:
1. Increase `--memory` and `--cpu` before adding instances
2. Enable Supabase connection pooling (PgBouncer) if connection limits hit
3. See [Future: Production Hardening](../implementation-plan.md#future-production-hardening-post-validation)

---

## Rollback

**Backend (Cloud Run):**
```bash
# List revisions
gcloud run revisions list --service retriever --region us-central1 --project $PROJECT_ID

# Route traffic to previous revision
gcloud run services update-traffic retriever --to-revisions=REVISION_NAME=100 --region us-central1 --project $PROJECT_ID
```

**Frontend (Cloudflare Pages):**
Roll back via the Cloudflare Pages dashboard > Deployments > select previous deployment > "Rollback to this deploy".
