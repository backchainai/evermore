# Evermore local development orchestration.
#
# Quick start (first run pulls Docker images and may take a few minutes):
#   make env      # create .env files from examples (then add LLM keys to services/retriever/.env)
#   make dev      # bring up Supabase + pgvector + retriever, then run stacker in the foreground
#
# Topology (see docs/local-development.md):
#   Supabase auth (GoTrue)  http://localhost:54321
#   pgvector app database   localhost:5433
#   retriever API           http://localhost:8001
#   stacker portal          http://localhost:5173
#
# Stop everything with `make down`. `make dev` runs stacker in the foreground;
# Ctrl-C stops stacker, then run `make down` to stop the background services.

STACKER_DIR := apps/stacker
RETRIEVER_DIR := services/retriever
RUN_DIR := .dev
RETRIEVER_PID := $(RUN_DIR)/retriever.pid
RETRIEVER_LOG := $(RUN_DIR)/retriever.log

.PHONY: env supabase-up db-up db-migrate retriever-up retriever-bg stacker-up dev down

env:
	@[ -f $(STACKER_DIR)/.env ] || cp $(STACKER_DIR)/.env.example $(STACKER_DIR)/.env && echo "stacker .env ready"
	@[ -f $(RETRIEVER_DIR)/.env ] || cp $(RETRIEVER_DIR)/.env.example $(RETRIEVER_DIR)/.env && echo "retriever .env ready"
	@echo "Add your OPENROUTER_API_KEY and OPENAI_API_KEY to $(RETRIEVER_DIR)/.env for chat answers."

supabase-up:
	cd $(STACKER_DIR) && supabase start

db-up:
	cd $(STACKER_DIR) && docker compose up -d

db-migrate: db-up
	cd $(RETRIEVER_DIR) && uv sync && uv run alembic upgrade head

retriever-up: db-migrate
	cd $(RETRIEVER_DIR) && uv run uvicorn retriever.main:app --port 8001 --reload

# Background variant used by `dev` so stacker can own the foreground.
retriever-bg: db-migrate
	@mkdir -p $(RUN_DIR)
	cd $(RETRIEVER_DIR) && uv sync
	@echo "starting retriever in background (log: $(RETRIEVER_LOG))"
	@cd $(RETRIEVER_DIR) && nohup uv run uvicorn retriever.main:app --port 8001 --reload \
		> ../../$(RETRIEVER_LOG) 2>&1 & echo $$! > ../../$(RETRIEVER_PID)

stacker-up:
	cd $(STACKER_DIR) && npm install && npm run dev

dev: supabase-up retriever-bg stacker-up

down:
	-@[ -f $(RETRIEVER_PID) ] && kill `cat $(RETRIEVER_PID)` 2>/dev/null && rm -f $(RETRIEVER_PID) && echo "stopped retriever" || true
	-cd $(STACKER_DIR) && docker compose down
	-cd $(STACKER_DIR) && supabase stop
