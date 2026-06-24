# Cloudflare AI Gateway setup

How to stand up a new Cloudflare AI Gateway for Evermore development. Every
outbound model call in Retriever (chat, embeddings, moderation) routes through
one OpenAI-compatible gateway, so all LLM usage is visible, cost-tracked, and
shareable across services (ADR `docs/adr/0007-llm-gateway-consolidation.md`).
Provider keys live in the gateway (BYOK); the app sends only a single gateway
token.

This guide is the one-time gateway setup. To keep the resulting IDs and token
across development cycles, see the persistent-config section of
`docs/local-development.md`.

## What you end up with

Three values the app needs, plus provider keys held inside the gateway:

| App variable | Source |
|---|---|
| `CLOUDFLARE_ACCOUNT_ID` | Cloudflare account |
| `CLOUDFLARE_GATEWAY_ID` | the gateway name you create |
| `LLM_GATEWAY_TOKEN` | the gateway authentication token you mint |

The app derives the endpoint `https://gateway.ai.cloudflare.com/v1/{account_id}/{gateway_id}/compat`
and addresses models as `{provider}/{model}`: `anthropic/claude-sonnet-4.6` for
chat, `openai/text-embedding-3-small` for embeddings, `openai/omni-moderation-latest`
for moderation.

## 1. Create the gateway

In the Cloudflare dashboard: **AI > AI Gateway > Create Gateway**. Name it (64
character limit), for example `evermore-dev`, and select **Create**. Record your
**Account ID** (`CLOUDFLARE_ACCOUNT_ID`) and the gateway name
(`CLOUDFLARE_GATEWAY_ID`).

Reference: [Get started](https://developers.cloudflare.com/ai-gateway/get-started/).

## 2. Turn on Authenticated Gateway and mint the token

In the gateway's **Settings**: **Create authentication token** with `Run`
permission, and save it now (it is shown only once). Then toggle
**Authenticated Gateway** on. This token is `LLM_GATEWAY_TOKEN`; the app sends it
on the `cf-aig-authorization` header as `Bearer <token>`. With authentication on
and no token present, requests fail.

These tokens are account-scoped: any token with `AI Gateway Run` reaches every
gateway in the account, so a separate Cloudflare account is the only hard
isolation boundary between dev and prod.

Reference: [Authentication](https://developers.cloudflare.com/ai-gateway/configuration/authentication/).

## 3. Store the provider keys (BYOK)

BYOK keeps provider keys in Cloudflare's encrypted store instead of app
configuration, so the app sends no provider keys at all. It requires an
authenticated gateway (step 2) plus Secrets Store permissions on your account.

In the gateway's **Provider Keys** section: **Add API Key**, select the provider,
paste the key, **Save**. Add two:

- **OpenAI** key, for embeddings (`text-embedding-3-small`) and moderation
  (`omni-moderation-latest`).
- **Anthropic** key, for chat (`claude-sonnet-4.6`).

After this the app authenticates only with the gateway token; the gateway
attaches the right provider key per request. If you store more than one key for
a provider, the app can select one with the optional `cf-aig-byok-alias` header;
otherwise the `default` alias is used.

Reference: [Bring Your Own Keys](https://developers.cloudflare.com/ai-gateway/configuration/bring-your-own-keys/).

## 4. Point Retriever at the gateway

Put the three values in `services/retriever/.env` (or your persistent store):

```
CLOUDFLARE_ACCOUNT_ID=...
CLOUDFLARE_GATEWAY_ID=evermore-dev
LLM_GATEWAY_TOKEN=...
```

To use a non-Cloudflare OpenAI-compatible gateway instead, set `LLM_GATEWAY_URL`
to its `.../compat` base (this replaces the two Cloudflare IDs) and, if it
expects a different auth header, set `LLM_GATEWAY_AUTH_HEADER`. The gateway is
required: with none configured, Retriever fails fast on startup.

To pin or change models without code changes, set `DEFAULT_LLM_MODEL`,
`DEFAULT_EMBEDDING_MODEL`, or `FALLBACK_LLM_MODEL` in the same env; keeping them
in the persistent store carries the pin across cycles.

## 5. Verify

Start Retriever (`make dev`) and ask a question in the portal. A successful
answer that also appears under **AI Gateway > Logs** with token count and cost
confirms the path end to end. A 401 or 403 means a bad gateway token or BYOK
key; a model 404 means a bad `{provider}/{model}` slug.

## 6. Observability and cost controls

The gateway dashboard shows **Analytics** (Requests, Token Usage, Costs, Errors,
Caching) and a GraphQL API for custom queries, plus **Logging** with Logpush
export. Set **Spend Limits** and **Custom Costs** to cap development spend.

The gateway surfaces cost and analytics through this dashboard, GraphQL, and
Logpush, not through OpenTelemetry. Application-level OTel tracing is separate:
Retriever emits its own spans via `OTEL_EXPORTER_OTLP_ENDPOINT`, independent of
the gateway.

References: [Analytics](https://developers.cloudflare.com/ai-gateway/observability/analytics/),
[Logging](https://developers.cloudflare.com/ai-gateway/observability/logging/).
