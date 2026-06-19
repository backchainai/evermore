# Implementation Roadmap

Agile vertical slices - each increment delivers a working, visible feature.

## Increment Dependencies

```
1. Walking Skeleton
        ↓
2. LLM Integration
        ↓
3. Single Document RAG ←─── Core MVP (functional Q&A)
        ↓
4. Multi-Document
        ↓
5. RAG Quality Hardening ←─── Quality MVP (caching, evaluation, hybrid search)
        ↓
    ┌───┴───┐
    ↓       ↓
6. Safety  7. Auth
    ↓       ↓
    └───┬───┘
        ↓
8. Conversation History
        ↓
9. Audit Logging
        ↓
    ┌────┴────┐
    ↓         ↓
10. Observability  11. Feedback
    ↓         ↓
    └────┬────┘
         ↓
12. Mobile Polish
         ↓
13. Production
```

**Core MVP = Increments 1-4** (functional Q&A from documents)
**Quality MVP = Increments 1-5** (production-grade RAG with caching and evaluation)

---

## Increment 1: Walking Skeleton

**Goal:** Prove the stack works end-to-end. Hardcoded everything.

**Deliverable:** A web page where you type a question and get a response.

```
[Browser] → [FastAPI] → [Hardcoded response] → [Browser]
```

**What you'll see:**
- Visit `http://localhost:8000`
- See a simple chat interface
- Type "Hello" → Get "Hello! I'm Retriever, the volunteer assistant."

**Build:**
- [x] Project setup (pyproject.toml, dev container)
- [x] FastAPI app with single route
- [x] Jinja2 template with Tailwind (chat UI)
- [x] HTMX for form submission
- [x] Hardcoded response (no LLM yet)
- [x] Health endpoint `/health`
- [x] Input validation (1-2000 chars) *(added during code review)*
- [x] XSS prevention tests *(added during code review)*
- [ ] Pre-commit hooks for automated quality checks (ruff, mypy)
- [ ] GitHub Actions CI pipeline (lint, type-check, test on PR)

**Validates:** Dev environment, FastAPI, HTMX, Tailwind, deployment pipeline

**Status:** ✅ Complete (PR #1)

---

## Increment 2: Real LLM Integration

**Goal:** Replace hardcoded response with actual Claude via OpenRouter.

**Deliverable:** Ask any question, get a real AI response (no RAG yet).

```
[Browser] → [FastAPI] → [OpenRouter/Claude] → [Browser]
```

**What you'll see:**
- Ask "What's the capital of France?" → Get actual Claude response
- See loading state while waiting
- See error message if API fails

**Build:**
- [x] OpenRouter provider (Protocol-based)
- [x] Environment config for API keys
- [x] Loading spinner in UI *(HTMX built-in from Increment 1)*
- [x] Error handling + display
- [x] Request timeouts (30s for LLM calls)
- [x] Circuit breaker for LLM calls (fail fast after 5 failures)
- [x] Rate limiting (10 requests/minute per session)
- [x] Input validation (max 2000 chars, basic sanitization) *(done in Increment 1)*

**Validates:** LLM integration, provider abstraction, error handling, resilience

**Status:** ✅ Complete

---

## Increment 3: Single Document RAG

**Goal:** Load ONE document, answer questions from it.

**Deliverable:** Upload/index a document, ask questions about it.

```
[Document] → [Chunks] → [Embeddings] → [Chroma]
                                            ↓
[Question] → [Retrieve] → [Claude + Context] → [Answer]
```

**What you'll see:**
- Admin page: "Index document" button
- Index one shelter document
- Ask "Where do volunteers sign in?" → Answer from document
- See which chunks were used (debug view)

**Build:**
- [x] Document loader (markdown/text first)
- [x] Text chunker (structure-aware)
- [x] OpenAI embeddings
- [x] Chroma vector store
- [x] RAG pipeline (retrieve + generate)
- [x] Admin page to trigger indexing
- [x] Show retrieved chunks in response

**Validates:** Full RAG pipeline, chunking strategy, retrieval quality

**Status:** ✅ Complete (PR #3)

---

## Increment 4: Multi-Document Support

**Goal:** Index multiple documents, show sources in answers.

**Deliverable:** Index all shelter docs, answers cite their sources.

**What you'll see:**
- Index multiple documents
- Ask question → Answer with expandable source citations
- Admin view of all indexed documents with metadata

**Build:**
- [x] ~~Word document loader (.docx)~~ - Not needed (using .md/.txt only)
- [x] Document metadata (title, section, filename)
- [x] Source citation in answers (expandable citation cards)
- [x] Document list in admin (with title, type badges)
- [x] Re-index capability (already existed from Increment 3)

**Enhancements (discovered during implementation):**
- [ ] Markdown rendering in chat answers (currently shows raw markup)
- [ ] Indexing progress indicator in admin panel (no feedback during indexing)

**Validates:** Multi-document handling, citation accuracy

**Status:** ✅ Core complete (PR pending)

---

## Increment 5: RAG Quality Hardening

**Goal:** Production-grade RAG quality: caching, evaluation, hybrid retrieval.

**Deliverable:** Faster responses, measurable quality, better retrieval.

**What you'll see:**
- Repeated questions return instantly (~50ms vs ~3s)
- RAG quality tests run in CI with pass/fail
- Answers cite sources more accurately

**Build:**
- [x] Semantic caching (cache by question similarity)
- [x] Golden Q&A dataset (30+ examples from real docs)
- [x] RAG quality tests (retrieval accuracy, answer accuracy)
- [x] Hybrid retrieval (semantic + BM25 keyword search)
- [x] Reranking integration (Cohere or RRF)
- [x] Cache invalidation on document reindex
- [x] Quality metrics logging

**Validates:** Cache effectiveness, retrieval quality improvement, regression detection

**Status:** ✅ Complete

---

## Increment 6: Content Safety

**Goal:** Filter inappropriate content, detect attacks, prevent hallucinations.

**Deliverable:** Safe, accurate answers with attack prevention.

**What you'll see:**
- Ask inappropriate question → "I can only help with volunteer questions"
- Prompt injection attempt → Blocked and logged
- Answers verified against source documents
- Low-confidence answers flagged for review

**Build:**
- [x] OpenAI Moderation API integration
- [x] Input/output filtering
- [x] Prompt injection detection (pattern-based)
- [x] Hallucination detection (claim verification)
- [x] Confidence scoring for answers
- [x] Fallback responses for low-confidence
- [x] Safety logging (without storing harmful content)
- [x] Model fallback chain (Sonnet → Haiku)

**Validates:** Content moderation, attack prevention, answer accuracy

**Status:** ✅ Complete

---

## Increment 7: User Authentication

**Goal:** Volunteers must log in to use the app.

**Deliverable:** Login page, protected chat, user sessions.

**What you'll see:**
- Visit app → Redirected to login
- Log in with email/password
- Access chat interface
- Log out

**Build:**
- [x] User model + SQLite
- [x] Registration endpoint (admin creates users)
- [x] Login page
- [x] JWT session handling
- [x] Protected routes
- [x] Logout

**Validates:** Auth flow, session management

**Status:** ✅ Complete

---

## Increment 8: Conversation History

**Goal:** Remember conversation within a session.

**Deliverable:** Follow-up questions work, can see past Q&A.

**What you'll see:**
- Ask "Where do I sign in?"
- Follow up "What time does it open?" → Understands context
- Scroll up to see conversation history

**Build:**
- [ ] Conversation storage (session-based)
- [ ] Context window management
- [ ] Chat history UI
- [ ] Clear conversation button

**Validates:** Multi-turn conversations, context handling

---

## Increment 9: Q&A Audit Logging

**Goal:** Track all questions and answers for improvement.

**Deliverable:** Admin can see what volunteers are asking.

**What you'll see:**
- Admin dashboard with recent Q&A
- Filter by date, user
- See unanswered/low-confidence questions
- Export for analysis

**Build:**
- [ ] Audit log table
- [ ] Log every Q&A with metadata
- [ ] Admin dashboard page
- [ ] Basic analytics (common questions)

**Validates:** Audit trail, data for improvement

---

## Increment 10: Observability & Monitoring

**Goal:** Production-ready monitoring.

**Deliverable:** Error tracking, structured logs, cost visibility.

**What you'll see:**
- Sentry dashboard with errors and performance
- Structured logs queryable by request ID
- Cost tracking in admin dashboard
- Health check endpoints

**Build:**
- [ ] Sentry integration (errors + performance)
- [ ] structlog setup (JSON, request IDs)
- [ ] OpenTelemetry tracing for production debugging
- [ ] Prompt versioning for tracking prompt changes
- [ ] Cost tracking per request
- [ ] Health check endpoints (/health, /health/ready)
- [ ] External uptime monitoring (UptimeRobot)

**Validates:** Production readiness, debugging capability

---

## Increment 11: Feedback & Improvement

**Goal:** Volunteers can rate answers and quickly find key info.

**Deliverable:** Thumbs up/down on answers, feedback loop, prominent contact/source display.

**What you'll see:**
- Each answer has 👍/👎 buttons
- Feedback stored for review
- Admin sees low-rated answers
- **Most likely contact person shown at top of answer** (e.g., "Contact: Jane Smith, Adoption Coordinator")
- **Primary source document highlighted** (e.g., "Source: Adoption Procedures Guide")

**Build:**
- [ ] Feedback UI
- [ ] Feedback storage
- [ ] Admin feedback review
- [ ] Flag for document updates
- [ ] Extract and display primary contact from source documents
- [ ] Surface most relevant source document prominently at answer top

**Validates:** Continuous improvement loop, quick access to contacts/sources

---

## Increment 12: Mobile Polish

**Goal:** Excellent mobile experience.

**Deliverable:** Fully responsive, touch-friendly on all devices.

**What you'll see:**
- Works great on phone, tablet, desktop
- Touch-friendly buttons
- Keyboard doesn't hide input
- Fast on slow connections

**Build:**
- [ ] Mobile testing & fixes
- [ ] Touch target optimization
- [ ] Offline-friendly error states
- [ ] Performance optimization

**Validates:** Real-world usability

---

## Increment 13: Production Deployment

**Goal:** Live on the internet, ready for volunteers.

**Deliverable:** Deployed app with documentation.

**What you'll see:**
- App running at `retriever.example.org`
- SSL certificate
- Volunteers can actually use it

**Build:**
- [ ] Railway/Render deployment
- [ ] Environment configuration
- [ ] Domain + SSL
- [ ] Volunteer onboarding guide
- [ ] Admin documentation

**Validates:** Production deployment, real users

---

## Increment 14: Docker Container Build

**Goal:** Build and test production Docker image locally.

**Deliverable:** Production-ready Docker image that can be tested locally before Cloud Run deployment.

**What you'll see:**
- Build production image: `docker build -t retriever .`
- Run containerized app: `docker-compose up`
- Test production build locally before cloud deployment
- Data persists in volumes across container restarts

**Development workflow:**
- Active development: Git worktree on host with `uv run uvicorn --reload`
- Docker testing: Test production build locally before pushing to cloud

**Build:**
- [ ] Production-ready multi-stage Dockerfile
- [ ] .dockerignore for build optimization
- [ ] docker-compose.yml for container management
- [ ] README.md Docker deployment section
- [ ] Environment variables documented
- [ ] Volume management documentation

**Validates:** Production container build, local testing workflow, Cloud Run readiness

**Status:** 🚧 In Planning

---

## Increment 15: Cloud Run Deployment

**Goal:** Deploy to Google Cloud Run with managed infrastructure.

**Deliverable:** Production deployment on Cloud Run with auto-scaling.

**What you'll see:**
- App running on Cloud Run with custom domain
- Automatic scaling based on traffic
- Managed SSL certificates
- Centralized logging and monitoring

**Build:**
- [ ] Cloud Run deployment configuration
- [ ] GCS-backed volume mounting for data persistence
- [ ] Secret Manager integration for API keys
- [ ] GitHub Actions CI/CD pipeline
- [ ] Cloud Monitoring dashboards
- [ ] Deployment documentation

**Validates:** Cloud-native deployment, auto-scaling, production resilience

**Status:** ⏸️ Future (after Increment 14)

---

## Future: Production Hardening

See [implementation-plan.md](implementation-plan.md#future-production-hardening-post-validation) for operational excellence items deferred until product validation.
