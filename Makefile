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

# Persistent dev-config store, outside any worktree so values survive across
# checkouts and worktree deletes. Override with EVERMORE_DEV_HOME.
DEV_HOME ?= $(or $(EVERMORE_DEV_HOME),$(HOME)/.config/evermore)

.PHONY: env link-env supabase-up db-up db-migrate retriever-up retriever-bg stacker-up dev down

env:
	@[ -f $(STACKER_DIR)/.env ] || cp $(STACKER_DIR)/.env.example $(STACKER_DIR)/.env && echo "stacker   .env ready: $(STACKER_DIR)/.env"
	@[ -f $(RETRIEVER_DIR)/.env ] || cp $(RETRIEVER_DIR)/.env.example $(RETRIEVER_DIR)/.env && echo "retriever .env ready: $(RETRIEVER_DIR)/.env"
	@echo ""
	@echo "Populate these before 'make dev':"
	@echo "  $(RETRIEVER_DIR)/.env  -> LLM_GATEWAY_TOKEN, CLOUDFLARE_ACCOUNT_ID, CLOUDFLARE_GATEWAY_ID  (required; chat fails fast without them)"
	@echo "  $(STACKER_DIR)/.env    -> PUBLIC_SUPABASE_ANON_KEY  (from: cd $(STACKER_DIR) && supabase status -o json, after 'make supabase-up')"
	@echo ""
	@echo "To retain config across worktrees instead, use 'make link-env' (see docs/local-development.md)."

# Persistent alternative to `env`: keep one copy of your dev config in $(DEV_HOME)
# and symlink each service's .env to it. Run once per worktree; values persist.
link-env:
	@mkdir -p $(DEV_HOME)
	@for svc in $(RETRIEVER_DIR) $(STACKER_DIR); do \
	  name=$$(basename $$svc); store=$(DEV_HOME)/$$name.env; envf=$$svc/.env; \
	  if [ ! -f $$store ]; then \
	    if [ -f $$envf ] && [ ! -L $$envf ]; then mv $$envf $$store && echo "adopted existing $$envf -> $$store"; \
	    else cp $$svc/.env.example $$store && echo "bootstrapped $$store from $$svc/.env.example"; fi; \
	  fi; \
	  ln -sfn $$store $$envf && echo "linked $$envf -> $$store"; \
	done
	@echo "Edit values once in $(DEV_HOME)/*.env; they persist across worktrees and development cycles."

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
	@( cd $(RETRIEVER_DIR) && exec nohup uv run uvicorn retriever.main:app --port 8001 --reload ) \
		> $(RETRIEVER_LOG) 2>&1 & echo $$! > $(RETRIEVER_PID)

stacker-up:
	cd $(STACKER_DIR) && npm install && npm run dev

dev: supabase-up retriever-bg stacker-up

down:
	-@[ -f $(RETRIEVER_PID) ] && kill `cat $(RETRIEVER_PID)` 2>/dev/null && rm -f $(RETRIEVER_PID) && echo "stopped retriever" || true
	-cd $(STACKER_DIR) && docker compose down
	-cd $(STACKER_DIR) && supabase stop
