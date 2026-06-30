# Evermore local development orchestration.
#
# Quick start (first run pulls Docker images and may take a few minutes):
#   make env        # create .env files from examples (then add LLM keys for `make dev`)
#   make dev        # Supabase + pgvector + retriever, then stacker (real LLM gateway)
#   make dev-full   # the whole stack locally with a stub LLM (no paid credentials)
#
# Topology (see docs/local-development.md):
#   Supabase auth (GoTrue)  http://localhost:54321
#   retriever app database   localhost:5433   (apps/stacker/docker-compose.yml)
#   pet data database        localhost:5434   (services/petdata/docker-compose.yml)
#   LLM stub gateway         http://localhost:8099   (make dev-full only)
#   retriever API            http://localhost:8001
#   pet data API             http://localhost:8002   (make dev-full)
#   stacker portal           http://localhost:5173
#
# Stop everything with `make down`. `make dev`/`make dev-full` run stacker in the
# foreground; Ctrl-C stops stacker, then run `make down` to stop the rest.

STACKER_DIR := apps/stacker
RETRIEVER_DIR := services/retriever
PETDATA_DIR := services/petdata
RUN_DIR := .dev
RETRIEVER_PID := $(RUN_DIR)/retriever.pid
RETRIEVER_LOG := $(RUN_DIR)/retriever.log
PETDATA_PID := $(RUN_DIR)/petdata.pid
PETDATA_LOG := $(RUN_DIR)/petdata.log
LLM_STUB_PID := $(RUN_DIR)/llm-stub.pid
LLM_STUB_LOG := $(RUN_DIR)/llm-stub.log

# Local LLM stub port; the retriever points LLM_GATEWAY_URL here under dev-full.
LLM_STUB_PORT ?= 8099

# Local Supabase asymmetric JWT signing key (gitignored). Enabled in
# supabase/config.toml so GoTrue issues ES256 tokens the retriever can validate.
SIGNING_KEYS := $(STACKER_DIR)/supabase/signing_keys.json

# Variable names retired from the .env templates; warn if a stale local .env
# still sets them (they are silently ignored, which boots a confusing stack).
STALE_VARS := OPENROUTER_API_KEY SUPABASE_ANON_KEY PUBLIC_SUPABASE_ANON_KEY

# Persistent dev-config store, outside any worktree so values survive across
# checkouts and worktree deletes. Override with EVERMORE_DEV_HOME.
DEV_HOME ?= $(or $(EVERMORE_DEV_HOME),$(HOME)/.config/evermore)

.PHONY: env link-env supabase-keys supabase-up db-up db-migrate retriever-up \
	retriever-bg petdata-db-up petdata-migrate petdata-bg llm-stub dev dev-full down

env:
	@[ -f $(STACKER_DIR)/.env ] || cp $(STACKER_DIR)/.env.example $(STACKER_DIR)/.env && echo "stacker   .env ready: $(STACKER_DIR)/.env"
	@[ -f $(RETRIEVER_DIR)/.env ] || cp $(RETRIEVER_DIR)/.env.example $(RETRIEVER_DIR)/.env && echo "retriever .env ready: $(RETRIEVER_DIR)/.env"
	@[ -f $(PETDATA_DIR)/.env ] || cp $(PETDATA_DIR)/.env.example $(PETDATA_DIR)/.env && echo "petdata   .env ready: $(PETDATA_DIR)/.env"
	@for envf in $(STACKER_DIR)/.env $(RETRIEVER_DIR)/.env $(PETDATA_DIR)/.env; do \
	  [ -f $$envf ] || continue; \
	  for v in $(STALE_VARS); do \
	    if grep -q "^$$v=" $$envf 2>/dev/null; then \
	      echo "WARN: $$envf sets retired variable $$v (ignored; refresh from the matching .env.example)"; \
	    fi; \
	  done; \
	done
	@echo ""
	@echo "Populate these before 'make dev':"
	@echo "  $(RETRIEVER_DIR)/.env  -> LLM_GATEWAY_TOKEN, CLOUDFLARE_ACCOUNT_ID, CLOUDFLARE_GATEWAY_ID  (required by 'make dev'; 'make dev-full' uses the stub instead)"
	@echo "  $(STACKER_DIR)/.env    -> PUBLIC_SUPABASE_PUBLISHABLE_KEY  (from: cd $(STACKER_DIR) && supabase status -o json, after 'make supabase-up')"
	@echo ""
	@echo "To retain config across worktrees instead, use 'make link-env' (see docs/local-development.md)."

# Persistent alternative to `env`: keep one copy of your dev config in $(DEV_HOME)
# and symlink each service's .env to it. Run once per worktree; values persist.
link-env:
	@mkdir -p $(DEV_HOME)
	@for svc in $(RETRIEVER_DIR) $(STACKER_DIR) $(PETDATA_DIR); do \
	  name=$$(basename $$svc); store=$(DEV_HOME)/$$name.env; envf=$$svc/.env; \
	  if [ ! -f $$store ]; then \
	    if [ -f $$envf ] && [ ! -L $$envf ]; then mv $$envf $$store && echo "adopted existing $$envf -> $$store"; \
	    else cp $$svc/.env.example $$store && echo "bootstrapped $$store from $$svc/.env.example"; fi; \
	  fi; \
	  ln -sfn $$store $$envf && echo "linked $$envf -> $$store"; \
	done
	@echo "Edit values once in $(DEV_HOME)/*.env; they persist across worktrees and development cycles."

# Generate the local ES256 signing key if absent. `supabase gen signing-key`
# pollutes stdout with a PostHog shutdown line and exits non-zero, so isolate
# the JWK by its "kty" field and wrap it in the keys array config.toml expects.
# Validate the JWK parses as JSON before writing, so a future CLI output change
# fails loudly here instead of writing a malformed key that GoTrue silently
# rejects (surfacing far downstream as "tokens rejected on chat").
supabase-keys:
	@if [ ! -f $(SIGNING_KEYS) ]; then \
	  echo "generating local ES256 JWT signing key -> $(SIGNING_KEYS)"; \
	  jwk=$$(supabase gen signing-key --algorithm ES256 2>/dev/null | grep '"kty"' | head -1); \
	  if [ -z "$$jwk" ]; then echo "ERROR: could not generate signing key (is the supabase CLI installed?)" >&2; exit 1; fi; \
	  echo "$$jwk" | python3 -c 'import json,sys; json.loads(sys.stdin.read())' 2>/dev/null \
	    || { echo "ERROR: generated signing key is not valid JSON (supabase CLI output changed?)" >&2; exit 1; }; \
	  printf '[%s]\n' "$$jwk" > $(SIGNING_KEYS); \
	else echo "signing key present: $(SIGNING_KEYS)"; fi

supabase-up: supabase-keys
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

petdata-db-up:
	cd $(PETDATA_DIR) && docker compose up -d

petdata-migrate: petdata-db-up
	cd $(PETDATA_DIR) && uv sync && uv run alembic upgrade head

# Background pet data service for `dev-full`.
petdata-bg: petdata-migrate
	@mkdir -p $(RUN_DIR)
	cd $(PETDATA_DIR) && uv sync
	@echo "starting petdata in background (log: $(PETDATA_LOG))"
	@( cd $(PETDATA_DIR) && exec nohup uv run uvicorn petdata.main:app --port 8002 --reload ) \
		> $(PETDATA_LOG) 2>&1 & echo $$! > $(PETDATA_PID)

# Offline OpenAI-compatible LLM stub (stdlib only; no venv). dev-full points the
# retriever's LLM_GATEWAY_URL at it so chat/embeddings/moderation work with no
# paid credentials. Answers are fake; embeddings are deterministic 1536-dim.
llm-stub:
	@mkdir -p $(RUN_DIR)
	@echo "starting LLM stub on http://localhost:$(LLM_STUB_PORT) (log: $(LLM_STUB_LOG))"
	@( exec nohup python3 tools/llm-stub/llm_stub.py --port $(LLM_STUB_PORT) ) \
		> $(LLM_STUB_LOG) 2>&1 & echo $$! > $(LLM_STUB_PID)

dev: supabase-up retriever-bg stacker-up

# Whole stack locally with the stub LLM: Supabase + both databases + stub +
# retriever + pet data, then stacker in the foreground. No paid credentials.
dev-full: export LLM_GATEWAY_URL := http://localhost:$(LLM_STUB_PORT)/v1
dev-full: export PUBLIC_ENABLED_MODULES := retriever,petdata
dev-full: supabase-up llm-stub retriever-bg petdata-bg stacker-up

stacker-up:
	cd $(STACKER_DIR) && npm install && npm run dev

down:
	-@for pid in $(RETRIEVER_PID) $(PETDATA_PID) $(LLM_STUB_PID); do \
	  [ -f $$pid ] && kill `cat $$pid` 2>/dev/null && rm -f $$pid && echo "stopped $$(basename $$pid .pid)"; \
	done; true
	-cd $(STACKER_DIR) && docker compose down
	-cd $(PETDATA_DIR) && docker compose down
	-cd $(STACKER_DIR) && supabase stop
