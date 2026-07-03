---
title: Retriever Test Effectiveness Audit
prepared_by: Claude Code (daedalus implementer)
updated: 2026-07-03T00:00:00-04:00
purpose: Audit every retriever test for whether it verifies real behavior, and record keep/rewrite/delete verdicts with rationale.
tags: []
aliases: []
---

# Retriever Test Effectiveness Audit

**Module:** `services/retriever`
**Date:** 2026-07-03
**Scope:** `services/retriever/tests/**` (26 unit test files + 5 integration test files, 383 tests total: 357 unit + 26 integration)

## Summary

| Metric | Count |
|---|---|
| Total tests audited | 383 |
| Keep | 353 |
| Rewrite | 23 |
| Delete | 7 |
| Files with edits applied | 11 |

This document audits every retriever test individually, one subsection per test file, each with a per-test ledger recording a keep/rewrite/delete verdict and rationale. Rewrite/delete verdicts for unit test files were applied directly to the corresponding file as that file's ledger was written (11 files touched — see `git status`). The 5 integration suites under `tests/integration/` were reviewed statically only: they require a live backend plus a live Supabase instance, the module-wide `_require_integration_env`/`_backend_reachable` fixtures auto-skip the whole suite when those aren't reachable, and the retriever's own `pyproject.toml` `addopts` already carries `--ignore=tests/integration`, so these tests never run in the default `pytest tests/` invocation or in the configured daedalus `test` gate. Their rewrite verdicts are recorded as follow-on work rather than applied edits. The mock-of-own-code inventory, a mutation-testing baseline attempt, and a behavior-coverage matrix follow the per-file ledgers.

## Per-file ledger

### tests/test_auth.py

| Test | Verdict | Rationale | Action |
|---|---|---|---|
| test_decode_valid_token | keep | Real RSA key pair, real `jwt.encode`/`JwksValidator.decode`; only the JWKS HTTP client (external boundary) is mocked. Asserts real payload fields. | none |
| test_decode_expired_token | keep | Exercises real expiry check via `jwt` library against a real token; asserts the real exception type. | none |
| test_decode_invalid_signature | keep | Signs with a different key pair and asserts `InvalidSignatureError` from real signature verification, not a mock. | none |
| test_require_auth_valid_token | keep | Full FastAPI `TestClient` round trip through `require_auth`; only the JWKS HTTP fetch is patched. Asserts status code and body. | none |
| test_require_auth_missing_token | keep | Verifies real 401 behavior when no `Authorization` header is sent. | none |
| test_require_auth_expired_token | keep | End-to-end 401 assertion for an expired real token through the dependency. | none |
| test_require_admin_non_admin | keep | Verifies `require_admin` rejects a real, validly-signed token whose claims lack `is_admin`. | none |
| test_require_admin_is_admin | keep | Verifies `require_admin` accepts admin claims and returns the real payload. | none |

**File totals:** 8 keep / 0 rewrite / 0 delete.

### tests/test_cache.py

| Test | Verdict | Rationale | Action |
|---|---|---|---|
| test_cache_miss_returns_none | keep | Real Postgres/pgvector round trip through `PgSemanticCache.get`; `@pytest.mark.integration` + `db_engine` fixture auto-skip when no DB, so the suite stays green without a live Postgres. No mocking of the unit under test. | none |
| test_set_and_get | keep | Exercises real `set`/`get` against a live DB, asserting real returned answer/sources, not a mock return value. | none |
| test_invalidate_clears_entries | keep | Verifies real invalidation removes a real cache row via a subsequent real `get`. | none |

**File totals:** 3 keep / 0 rewrite / 0 delete. (All three are DB integration tests living outside `tests/integration/`; they auto-skip without a reachable Postgres rather than failing — noted in the pytest run section below.)

### tests/test_config.py

| Test | Verdict | Rationale | Action |
|---|---|---|---|
| test_settings_defaults | keep | Instantiates real `Settings`, asserts real defaults. No mocking. | none |
| test_llm_gateway_base_url_raises_when_unconfigured | keep | Real property logic, real exception + message match. | none |
| test_llm_gateway_base_url_with_cloudflare | keep | Real URL construction verified via substring/suffix assertions on the real computed value. | none |
| test_llm_gateway_url_overrides_everything | keep | Verifies real precedence logic (explicit URL wins over CF IDs). | none |
| test_llm_gateway_auth_header_default | keep | Simple but real default-value assertion, no mocking. | none |
| test_llm_gateway_token_default | keep | Real `SecretStr` default behavior verified via `get_secret_value()`. | none |
| test_fallback_llm_model_default | keep | Real default constant check; cheap but legitimate regression guard against silent model-slug drift. | none |
| test_get_settings_returns_cached_instance | keep | Verifies real `lru_cache`/singleton behavior via identity (`is`), not a mock. | none |
| test_wildcard_origin_rejected | keep | Real validator raises on real input. | none |
| test_parse_origins_json_array | keep | Pure function, real input/output. | none |
| test_parse_origins_comma_separated | keep | Pure function, real input/output. | none |
| test_parse_origins_single_value | keep | Pure function, real input/output. | none |
| test_parse_origins_shell_escaped | keep | Covers a real production edge case (shell-mangled JSON) with a real parse. | none |
| test_parse_origins_empty | keep | Pure function edge case, real input/output. | none |

**File totals:** 14 keep / 0 rewrite / 0 delete.

### tests/test_docling_processor.py

| Test | Verdict | Rationale | Action |
|---|---|---|---|
| TestTitleFromFilename::test_strips_extension | keep | Pure function, real input/output. | none |
| TestTitleFromFilename::test_no_extension | keep | Pure function edge case. | none |
| TestTitleFromFilename::test_multiple_dots | keep | Pure function edge case (dotted filenames). | none |
| TestInferType::test_markdown | keep | Real classification logic. | none |
| TestInferType::test_text | keep | Real classification logic. | none |
| TestInferType::test_pdf | keep | Real classification logic. | none |
| TestInferType::test_word | keep | Real classification logic. | none |
| TestInferType::test_powerpoint | keep | Real classification logic. | none |
| TestInferType::test_excel | keep | Real classification logic. | none |
| TestInferType::test_html | keep | Covers both `.html`/`.htm` extensions for the real function. | none |
| TestInferType::test_image | keep | Covers multiple image extensions for the real function. | none |
| TestInferType::test_unknown | keep | Real fallback-branch coverage. | none |
| TestFormatAwareProcessorRouting::test_text_routes_to_text_path | **delete** | Docstring claims to test that text routes to the text path, but the body only sends a `.pdf` (binary) input and asserts `mock_docling.process.assert_called_once()` — it mislabels the binary-delegation path and never exercises text routing at all. `TestFormatAwareProcessorBinary::test_binary_delegates_to_docling_processor` already covers the same binary-delegation behavior with stronger assertions (`assert_called_once_with` exact args + return-value identity). The test is misnamed, redundant, and asserts nothing the other test doesn't already assert better. | Removed from `test_docling_processor.py`. |
| TestFormatAwareProcessorRouting::test_satisfies_document_processor_protocol | keep | Real `isinstance` check against the real `DocumentProcessor` protocol using a real (unmocked) `DoclingProcessor`. | none |
| TestFormatAwareProcessorText::test_process_markdown_extracts_title | keep | Mocks only the two factory methods (`_get_chunker`, `_get_text_converter`) that lazily construct heavy third-party Docling objects (avoids ML model downloads per file docstring); the title-extraction and type-inference business logic under test executes for real. | none |
| TestFormatAwareProcessorText::test_process_txt_uses_filename_title | keep | Same boundary-mocking pattern; verifies real fallback-to-filename title logic. | none |
| TestFormatAwareProcessorText::test_process_invalid_utf8_raises | keep | No mocking at all — real UTF-8 decode failure raises the real `DocumentConversionError` with a real message match. | none |
| TestFormatAwareProcessorText::test_process_text_fallback_chunk_for_short_content | keep | Mocks only the Docling boundary; verifies real fallback single-chunk logic when the chunker returns nothing. | none |
| TestFormatAwareProcessorBinary::test_binary_delegates_to_docling_processor | keep | `DoclingProcessor` is mocked at the class boundary (heavy ML dependency) but the assertion checks exact call args and return-value identity — a real contract check on `FormatAwareProcessor`'s delegation logic. | none |
| TestDoclingConfig::test_defaults | keep | Real pydantic model defaults, no mocking. | none |
| TestDoclingConfig::test_custom_values | keep | Real pydantic model override behavior. | none |
| TestExceptions::test_document_conversion_error | keep | Real exception hierarchy and attribute checks, no mocking. | none |

**File totals:** 21 keep / 0 rewrite / 1 delete (22 tests originally; one removed as a mislabeled duplicate).

### tests/test_document_routes.py

| Test | Verdict | Rationale | Action |
|---|---|---|---|
| test_upload_document_success | keep | Real FastAPI `TestClient` wiring, real routing/serialization; `DocumentService` (a genuine collaborator, not the unit under test) is mocked at the DI seam. Asserts real status code and response shape. | none |
| test_upload_document_requires_admin | keep | Verifies real auth-dependency enforcement (no override) yields 401/403. | none |
| test_upload_document_validation_error | keep | Verifies real exception-to-HTTP-status mapping (400) and real detail message passthrough. | none |
| test_upload_document_duplicate_error | keep | Verifies real exception-to-409 mapping. | none |
| test_upload_document_indexing_error | keep | Verifies real exception-to-500 mapping. | none |
| test_list_documents_success | keep | Real serialization round trip including field presence (`last_updated_at`) — guards against schema drift. | none |
| test_list_documents_requires_auth | keep | Real 401/403 enforcement without auth override. | none |
| test_get_document_success | keep | Real routing + serialization check. | none |
| test_get_document_not_found | keep | Real exception-to-404 mapping. | none |
| test_delete_document_success | keep | Real routing, real response shape. | none |
| test_delete_document_requires_admin | keep | Real admin-gate enforcement. | none |
| test_delete_document_not_found | keep | Real exception-to-404 mapping. | none |

**File totals:** 12 keep / 0 rewrite / 0 delete. `DocumentService` mocking here is a legitimate route/service seam, not a mock-of-own-code-under-test issue; cross-checked against `test_document_service.py` (real service logic) and `tests/integration/test_document_lifecycle.py` (full stack) for actual behavior coverage.

### tests/test_document_service.py

| Test | Verdict | Rationale | Action |
|---|---|---|---|
| test_upload_document_valid_file | keep | `DocumentService` (unit under test) is real; only its I/O collaborators (`DocumentRepository`, RAG service) are mocked. Asserts real returned fields and that `mark_indexed` receives the real parsed title, not just "was called". | none |
| test_upload_document_invalid_file_type | keep | Real validation branch, real exception + message match, no service-internal mocking. | none |
| test_upload_document_max_documents_exceeded | keep | Real limit-check branch against a mocked count boundary. | none |
| test_upload_document_duplicate_filename | keep | Real duplicate-check branch. | none |
| test_upload_document_indexing_failure_cleans_up | keep | Verifies real compensating-transaction logic (DB row deleted when indexing fails) with an exact-args assertion, not a bare `.called`. | none |
| test_upload_document_pdf_sets_correct_mime_type | keep | Verifies real MIME-type derivation is passed through to the repo create call. | none |
| test_upload_document_empty_file | keep | Real empty-file validation branch. | none |
| test_delete_document_success | keep | Verifies real orchestration order/args across vector store, cache invalidation, and repo delete — exact-args assertions, not bare `.called`. | none |
| test_delete_document_not_found | keep | Real not-found branch and exception message. | none |
| test_delete_document_no_cache | keep | Real optional-dependency branch (cache is `None`). | none |
| test_list_documents_returns_all | keep | Verifies real mapping/ordering from repo rows to response schema. | none |
| test_list_documents_empty | keep | Real empty-list branch. | none |
| test_get_document_found | keep | Real mapping from repo row to response schema. | none |
| test_get_document_not_found | keep | Real not-found branch. | none |
| test_get_document_count | keep | Thin pass-through to the repo, but it is real service code (not a mock echoing itself) and guards against the method silently dropping the tenant-scoping argument in future refactors. | none |

**File totals:** 15 keep / 0 rewrite / 0 delete. This file is the model for correct collaborator mocking in the suite: the unit under test (`DocumentService`) always runs its real code path; only true I/O boundaries (repo, RAG service, vector store, cache) are mocked, and assertions check real outputs/exact call args rather than bare `.called`.

### tests/test_embeddings.py

| Test | Verdict | Rationale | Action |
|---|---|---|---|
| TestOpenAIEmbeddingProviderInit::test_init_with_injected_client | keep | Real constructor, mocks only the external `AsyncOpenAI` client (external API boundary). | none |
| TestOpenAIEmbeddingProviderInit::test_init_with_custom_model | keep | Real constructor override behavior. | none |
| TestOpenAIEmbeddingProviderInit::test_init_stores_injected_client | keep | Real DI-storage check via identity. | none |
| TestOpenAIEmbeddingProviderInit::test_dimensions_returns_correct_value_for_small | keep | Real model-to-dimension lookup logic, would catch a wrong constant. | none |
| TestOpenAIEmbeddingProviderInit::test_dimensions_returns_correct_value_for_large | keep | Same real lookup logic, second branch. | none |
| TestOpenAIEmbeddingProviderEmbed::test_embed_returns_vector | keep | Only the external OpenAI client call is mocked; real provider parsing logic converts the mock response into a real vector, asserted on value. | none |
| TestOpenAIEmbeddingProviderEmbed::test_embed_calls_api_with_correct_params | keep | Asserts exact call kwargs (model, input), not a bare `.called` — catches a param regression. | none |
| TestOpenAIEmbeddingProviderEmbed::test_embed_with_timeout_raises_timeout_error | keep | Real error-translation logic from a real OpenAI SDK exception type to the app's own exception, with message and attribute assertions. | none |
| TestOpenAIEmbeddingProviderEmbed::test_embed_with_rate_limit_raises_rate_limit_error | keep | Real error-translation branch for rate limiting. | none |
| TestOpenAIEmbeddingProviderEmbed::test_embed_with_connection_error_raises_provider_error | keep | Real error-translation branch for connection failure. | none |
| TestOpenAIEmbeddingProviderCircuitBreaker::test_circuit_breaker_opens_after_failures | keep | Exercises real circuit-breaker state machine across multiple real calls; asserts the breaker's own exception (not the underlying rate-limit exception) once open. | none |
| TestOpenAIEmbeddingProviderEmbedBatch::test_embed_batch_returns_multiple_vectors | keep | Real batch-parsing logic from a mocked API response. | none |
| TestOpenAIEmbeddingProviderEmbedBatch::test_embed_batch_with_empty_list_returns_empty | keep | Real empty-input short-circuit, no client call needed to verify. | none |
| TestOpenAIEmbeddingProviderEmbedBatch::test_embed_batch_timeout_raises_timeout_error | keep | Real error-translation branch for batch path. | none |
| TestOpenAIEmbeddingProviderEmbedBatch::test_embed_batch_connection_error_raises | keep | Real error-translation branch for batch path. | none |
| TestOpenAIEmbeddingProviderEmbedBatch::test_embed_batch_preserves_order | keep | Verifies real index-based reordering logic (API responses can arrive unordered) with `pytest.approx` for float comparison — a genuine correctness property, not a tautology. | none |

**File totals:** 16 keep / 0 rewrite / 0 delete. `AsyncOpenAI` is mocked at the true external-API boundary throughout; all app-side parsing, error translation, and circuit-breaker logic runs for real.

### tests/test_llm_provider.py

| Test | Verdict | Rationale | Action |
|---|---|---|---|
| TestOpenAICompatProviderInit::test_init_with_injected_client | keep | Real constructor; asserts real default `_default_model`/`_timeout` values, no mocking of the unit under test. | — |
| TestOpenAICompatProviderInit::test_init_with_custom_model | keep | Real constructor override behavior. | — |
| TestOpenAICompatProviderInit::test_init_stores_injected_client | keep | Real DI-storage check via identity (`is`). | — |
| TestOpenAICompatProviderInit::test_init_with_custom_circuit_breaker_settings | keep | Verifies `circuit_breaker_fail_max` is actually threaded into the real `aiobreaker.CircuitBreaker` instance (`provider._breaker._fail_max`); the breaker object is real, not a mock, so this checks real wiring rather than restating a mock's config. | — |
| TestOpenAICompatProviderComplete::test_complete_returns_content | keep | Only the external `AsyncOpenAI` client call is mocked (network boundary); real response-parsing logic in `_do_complete` runs and is asserted on value. | — |
| TestOpenAICompatProviderComplete::test_complete_uses_default_model | keep | Asserts the real call kwargs sent to the client carry the real default model, not a bare `.called`. | — |
| TestOpenAICompatProviderComplete::test_complete_with_custom_model | keep | Asserts real model-override precedence via exact call kwargs. | — |
| TestOpenAICompatProviderComplete::test_complete_timeout_raises_llm_timeout_error | keep | Real error-translation branch (`APITimeoutError` -> `LLMTimeoutError`); asserts real message content and `provider` attribute, not just the exception type. | — |
| TestOpenAICompatProviderComplete::test_complete_rate_limit_raises_llm_rate_limit_error | keep | Real error-translation branch (`RateLimitError` -> `LLMRateLimitError`) with a real message-substring assertion. | — |
| TestOpenAICompatProviderComplete::test_complete_connection_error_raises_llm_provider_error | keep | Real error-translation branch (`APIConnectionError` -> `LLMProviderError`) with a real message-substring assertion. | — |
| TestOpenAICompatProviderComplete::test_complete_handles_empty_response_content | keep | Verifies the real `content or ""` fallback when the mocked response has `content = None`; a genuine edge-case guard, not a mock echo. | — |
| TestOpenAICompatProviderCompleteWithHistory::test_complete_with_history_returns_content | keep | Same real-parsing pattern as `test_complete_returns_content`, exercising the separate `complete_with_history` code path (source implements this as a distinct method with its own try/except, so this is not redundant with the `complete()` tests). | — |
| TestOpenAICompatProviderCompleteWithHistory::test_complete_with_history_includes_system_prompt | keep | Asserts the real constructed `messages` list (system prompt prepended, exact length) sent to the client — a real contract check on history-assembly logic. | — |
| TestOpenAICompatProviderCompleteWithHistory::test_complete_with_history_timeout_raises | keep | Real error-translation branch for the history path. Weaker than its `complete()` sibling (only checks exception type, not message), but still a real, deterministic assertion of behavior on a distinct code path. | — |
| TestOpenAICompatProviderCompleteWithHistory::test_complete_with_history_rate_limit_raises | keep | Real error-translation branch for the history path (rate limit). | — |
| TestOpenAICompatProviderCompleteWithHistory::test_complete_with_history_connection_error_raises | keep | Real error-translation branch for the history path (connection error). | — |
| TestOpenAICompatProviderCompleteWithHistory::test_complete_with_history_unexpected_error_raises | keep | Verifies the real catch-all branch in `_do_complete_with_history` (`Exception` -> `LLMProviderError`) with a real message-substring assertion, distinct from the context-overflow branch. | — |
| TestOpenAICompatProviderResilience::test_retries_on_connection_error | keep | Exercises the real `tenacity` retry decorator end-to-end via `side_effect` sequencing (fail once, then succeed); asserts both the real returned content and the real `call_count == 2`, a genuine retry-count contract. Note: incurs a real `wait_exponential` sleep (unmocked), adding latency but not nondeterminism — outcome is deterministic regardless of wall time. | — |
| TestOpenAICompatProviderResilience::test_circuit_breaker_opens_after_failures | keep | Verified against `aiobreaker`'s real state machine (`CircuitClosedState.on_failure`, `aiobreaker/state.py`): with `fail_max=3`, the 3rd real failure trips `CircuitBreakerError` in place of the original exception, which `complete()` maps to `LLMProviderError`. The test's 2-loop-then-1-call shape exactly matches this real trip point; not a mock-driven assumption. | — |

**File totals:** 19 keep / 0 rewrite / 0 delete.

### tests/test_loader.py

| Test | Verdict | Rationale | Action |
|---|---|---|---|
| TestValidateFile::test_valid_markdown_file | keep | Calls the real `validate_file` with no mocking; "does not raise" is a real, deterministic assertion given the function's raise-on-failure contract. | — |
| TestValidateFile::test_valid_text_file | keep | Same pattern, `.txt` branch. | — |
| TestValidateFile::test_valid_pdf_file | keep | Same pattern, binary branch (`.pdf`) at a size well under the binary limit. | — |
| TestValidateFile::test_valid_docx_file | keep | Same pattern, `.docx` branch. | — |
| TestValidateFile::test_valid_pptx_file | keep | Same pattern, `.pptx` branch. | — |
| TestValidateFile::test_valid_xlsx_file | keep | Same pattern, `.xlsx` branch. | — |
| TestValidateFile::test_valid_html_file | keep | Same pattern, `.html` branch. | — |
| TestValidateFile::test_valid_htm_file | keep | Same pattern, `.htm` branch (distinct from `.html`, both hit the same `BINARY_EXTENSIONS` membership check but confirm both suffixes are actually wired in). | — |
| TestValidateFile::test_valid_image_files | keep | Loops 5 real image extensions through the real function; each iteration is a real assertion (no exception). Loop reduces per-extension failure attribution slightly but does not weaken behavior-sensitivity. | — |
| TestValidateFile::test_invalid_extension_raises | keep | Real `FileValidationError` with a real message-substring match for the unsupported-extension branch. | — |
| TestValidateFile::test_no_extension_raises | keep | Real message-substring match for the missing-extension branch, distinct code path from unsupported-extension. | — |
| TestValidateFile::test_text_file_too_large_raises | keep | Real boundary test at `MAX_FILE_SIZE_TEXT + 1`, real message match. | — |
| TestValidateFile::test_binary_file_too_large_raises | keep | Real boundary test at `MAX_FILE_SIZE_BINARY + 1`, real message match. | — |
| TestValidateFile::test_binary_file_within_limit_passes | keep | Real mid-range value distinct from the exact-boundary and small-file tests. | — |
| TestValidateFile::test_hidden_file_raises | keep | Real dotfile-rejection branch, real message match. | — |
| TestValidateFile::test_empty_file_raises | keep | Real zero-byte branch, real message match. | — |
| TestValidateFile::test_exactly_max_text_size_passes | keep | Off-by-one boundary test at exactly `MAX_FILE_SIZE_TEXT` (confirms `>` not `>=` in the size check) — a genuine correctness property, not a tautology. | — |
| TestValidateFile::test_exactly_max_binary_size_passes | keep | Same off-by-one boundary property for the binary limit. | — |
| TestExtensionConstants::test_text_extensions | keep | Restates `TEXT_EXTENSIONS` membership directly against the literal set, so it only fails if the constant itself is edited. Consistent with this audit's treatment of similar constant-membership checks in `test_config.py` (`test_fallback_llm_model_default`, kept as "cheap but legitimate regression guard"): this is a real, cheap guard against silently dropping/adding a supported file type, and the constant drives production routing/size-limit logic in `validate_file`. | — |
| TestExtensionConstants::test_binary_extensions | keep | Same pattern as `test_text_extensions`, binary side; same rationale. | — |
| TestExtensionConstants::test_supported_is_union | keep | Compares `SUPPORTED_EXTENSIONS` against a live re-evaluation of `TEXT_EXTENSIONS \| BINARY_EXTENSIONS` (not a hardcoded copy), so it actually guards the invariant that `SUPPORTED_EXTENSIONS` stays derived from the other two sets rather than becoming a second source of truth that could drift. | — |

**File totals:** 21 keep / 0 rewrite / 0 delete.

No edits were applied to either `test_llm_provider.py` or `test_loader.py`: every test verifies real, deterministic behavior of production code (either unmocked pure functions in `test_loader.py`, or `test_llm_provider.py`'s `OpenAICompatProvider` with only the external `AsyncOpenAI` client mocked at the network boundary). No assertion-free, mock-echo, tautological, structure-mirror, assertion-swallowing, or time/order/network-flaky tests were found.

### tests/test_error_handling.py

| Test | Verdict | Rationale | Action |
|---|---|---|---|
| test_unhandled_exception_returns_500_with_cors_header | keep | Behavior-sensitive: asserts status 500, exact CORS header value, and exact generic body against a real app + real TestClient; mutation-killable on the CORS-safe error handler. | — |
| test_unhandled_exception_body_is_generic | keep | Asserts the response body does not leak exception class/message; specific and deterministic negative assertions catch a real information-disclosure regression. | — |
| test_streaming_exception_after_body_started_reraises | keep | Exercises the mid-stream failure branch (after `http.response.start`), asserting the exception re-raises rather than being rewritten; deterministic via `pytest.raises` with message match, well-documented rationale for why this path can't return a clean 500. | — |
| test_cors_preflight_still_carries_header | keep | Regression guard that the fix didn't break the working CORS preflight path; asserts the actual header value on a real OPTIONS request. | — |

**File totals:** 4 keep / 0 rewrite / 0 delete.

### tests/test_gateway_client.py

| Test | Verdict | Rationale | Action |
|---|---|---|---|
| test_build_gateway_client_sets_base_url | keep | Asserts the real `AsyncOpenAI` client's `base_url` derives from settings; mutation-killable on the base_url wiring. | — |
| test_build_gateway_client_adds_auth_header_when_token_present | keep | Asserts the real client's `default_headers` carries the bearer token under the configured header name when a token is present. | — |
| test_build_gateway_client_uses_configured_header_name | keep | Distinct case from the above: proves the header *name* is read from settings, not hardcoded, using a different header name. | — |
| test_build_gateway_client_omits_auth_header_when_token_absent | keep | Covers the empty-token branch: header key must be absent, not just falsy. Kills the mutant that always adds the header. | — |
| test_build_gateway_client_uses_placeholder_api_key_when_token_empty | keep | Covers the SDK's non-empty-api_key requirement fallback; specific value assertion (`"unused"`). | — |
| test_build_gateway_client_uses_token_as_api_key_when_present | keep | Covers the token-present branch of the same fallback; complements the empty-token case above for full branch coverage. | — |

**File totals:** 6 keep / 0 rewrite / 0 delete.

### tests/test_health.py

| Test | Verdict | Rationale | Action |
|---|---|---|---|
| test_health_returns_degraded_when_factory_raises | **rewrite** | Originally `test_health_returns_response`, whose only assertion was `response.status_code == 200` — tautological, since the health endpoint is documented to always return 200 even when degraded, so the assertion could never catch a regression in the degraded-state fields. Renamed to name the actual fault-injection point (the `_get_factory()` call itself raises, before any session context manager exists) and strengthened with real `status`/`database`/`pgvector` value assertions on the degraded response body. | applied in this PR |
| test_health_response_has_expected_fields | keep | Asserts the full response key set plus every field value (status, version, database, pgvector, moderation) on the healthy path; mutation-killable on any field's hardcoded/derived value. | none |
| test_health_reports_configured_moderation_mode | keep | Injects a different `moderation_status` via a settings mock and asserts it propagates into the response; kills mutants that hardcode the moderation field. | none |
| test_health_with_db_unavailable_returns_degraded | keep | Simulates the DB context manager raising on `__aenter__`; asserts degraded status with database/pgvector both unavailable. Distinct fault point from the factory-raises test above. | none |
| test_health_db_connected_but_no_pgvector | keep | Covers the partial-degradation branch: DB reachable but pgvector extension missing; asserts database="connected" while pgvector="unavailable", killing mutants that conflate the two checks. | none |

**File totals:** 4 keep / 1 rewrite / 0 delete.

### tests/test_hybrid_retriever.py

| Test | Verdict | Rationale | Action |
|---|---|---|---|
| test_rrf_merges_overlapping_results | keep | Exercises the real `_reciprocal_rank_fusion` algorithm across two overlapping ranked lists; asserts exact ordering (B first, A second) and full set membership derived from actual RRF math. | — |
| test_rrf_scores_are_correctly_computed | keep | Asserts the exact RRF score formula (`weight / (k + rank + 1)` summed across sources) to float tolerance; directly mutation-killable on the formula in `_reciprocal_rank_fusion`. | — |
| test_semantic_only_results | keep | Edge case: empty keyword side; asserts order and count are preserved from semantic-only input. | — |
| test_keyword_only_results | keep | Edge case: empty semantic side; symmetric coverage to the semantic-only case. | — |
| test_empty_results_from_both | keep | Edge case: both sources empty; asserts `retrieve()` returns `[]` rather than raising or returning junk. | — |
| test_deduplication_by_chunk_id | keep | Asserts a chunk present in both lists is emitted once, with the semantic version's content preferred; kills mutants in the `doc_map` preference logic. | — |
| test_top_k_limits_output | keep | Asserts the merged list is sliced to `top_k`; kills mutants that drop or skip the final slice. | — |
| test_semantic_weight_bias | keep | Distinct weight configuration (0.9/0.1) proves the weight parameters actually drive ranking, not just accepted and ignored. | — |
| test_keyword_weight_bias | keep | Symmetric case (0.1/0.9) to the above; together the pair kills mutants that hardcode or swap the weight application. | — |
| test_vector_store_called_with_correct_params | keep | The over-retrieve limit (`top_k * 2`) and `min_score` threshold have no other observable effect once `vector_store.search` is mocked, so asserting the exact call args is the only way to pin this business rule; kills mutants changing the multiplier or threshold. | — |

**File totals:** 10 keep / 0 rewrite / 0 delete. `_build_retriever` mocks `vector_store` (VectorStore protocol backed by pgvector) and `session_factory`/`AsyncSession` (SQLAlchemy session backed by Postgres) — both cross a real external-system boundary (the database), not internal retriever logic, so treated as justified boundaries rather than flagged (see the Mock-of-own-code inventory).

### tests/test_llm_fallback.py

| Test | Verdict | Rationale | Action |
|---|---|---|---|
| test_primary_success_no_fallback | keep | Asserts the primary path returns a response and only one call is made (no fallback attempted); mutation-killable on the try/except structure. | — |
| test_fallback_on_primary_failure | keep | Asserts the exact two-call sequence (primary model then fallback model) with precise model args per call; mutation-killable on the fallback-model substitution logic. | — |
| test_raises_when_both_fail | keep | Asserts `LLMProviderError` propagates when both primary and fallback fail, and that fallback was attempted (2 calls). Both errors are message-identical in this fixture so the test doesn't distinguish which of `primary_error`/`fallback_error` is re-raised (`raise primary_error from None`) — a real but minor gap, not an anti-pattern. | — |
| test_model_override_passed_to_primary | keep | Asserts a caller-supplied model override reaches the primary call unchanged; specific and mutation-killable on argument pass-through. | — |
| test_complete_with_history_fallback | keep | Mirrors the `complete()` fallback test for the `complete_with_history` code path, confirming the fallback branch isn't unique to the single-turn method. | — |

**File totals:** 5 keep / 0 rewrite / 0 delete. `MockLLMProvider` is a hand-written fake implementing the `LLMProvider` protocol (not a `MagicMock`), standing in for a real LLM API call, an external network/paid-API boundary. Treated as a justified boundary (see the Mock-of-own-code inventory).

### tests/test_message_repos.py

| Test | Verdict | Rationale | Action |
|---|---|---|---|
| test_save_message_persists_and_returns_message | keep | Asserts against a real `Message` instance built by the repository (isinstance + field values), then confirms the add/commit/refresh persistence sequence on the mocked session; combines real-object and interaction assertions rather than relying on mock-echo alone. | — |
| test_save_message_rejects_invalid_role | keep | Specific `ValueError` message match on the invalid-role guard clause; mutation-killable on the role-validation conditional. | — |
| test_save_message_accepts_assistant_role | keep | Covers the second accepted branch of the role conditional (`"assistant"`), complementing the `"user"` case in the persistence test and the rejection case above for full branch coverage. | — |
| test_get_recent_messages_returns_chronological_order | keep | Asserts the real `rows.reverse()` behavior: DB rows arrive newest-first and must come back oldest-first; checks exact element order, not just count. Mutation-killable on the reverse call. | — |
| test_get_recent_messages_empty | keep | Edge case: empty result set returns `[]` rather than raising. | — |
| test_clear_messages_returns_count | keep | Asserts the returned count equals the mocked `cursor.rowcount` and that `commit` was awaited; verifies the rowcount pass-through and the commit-on-delete contract. | — |
| test_clear_messages_zero_deleted | keep | Edge case: zero rows deleted still returns `0` cleanly (exercises the `if deleted > 0` branch without asserting on the logging side-effect). | — |

**File totals:** 7 keep / 0 rewrite / 0 delete. `_fake_session_factory` mocks SQLAlchemy's `async_sessionmaker`/`AsyncSession` (third-party ORM standing in for Postgres, an external boundary). `_make_message` builds a `MagicMock(spec=Message)` standing in for a DB row mapped to the repository's own `Message` model — flagged as an own-code mock in the inventory below, but judged justified because it stands in for data the real database would return (no live Postgres in this unit tier), not for any of `Message`'s own logic (it has none — a plain SQLAlchemy declarative model).

### tests/test_models.py

| Test | Verdict | Rationale | Action |
|---|---|---|---|
| test_async_url_converts_postgres_scheme | keep | Pure function, real input/output; verifies real scheme rewrite in `_async_url`. | none |
| test_async_url_converts_postgresql_scheme | keep | Pure function, real input/output, second scheme variant. | none |
| test_async_url_strips_sslmode_query_param | keep | Real regex-stripping behavior, asserts absence of `sslmode` and correct URL tail. | none |
| test_async_url_strips_sslmode_with_other_params | keep | Real edge case: `sslmode` alongside another query param, asserts the other param survives. | none |
| test_async_url_strips_sslmode_when_first_param | keep | Real edge case: `sslmode` as the first param, asserts correct `?`-prefixed remainder — guards a genuine regex-ordering bug class. | none |
| test_async_url_preserves_asyncpg_scheme | keep | Real idempotency check: an already-`+asyncpg` URL is not double-suffixed. | none |
| test_create_engine_returns_engine | **rewrite** | Only asserted `engine is not None`, which `create_engine` can never fail to satisfy (it either returns an `AsyncEngine` or raises) — the assertion checked nothing `_async_url` or the engine construction actually did. Rewritten to assert `isinstance(engine, AsyncEngine)` and `engine.url.drivername == "postgresql+asyncpg"`, which verifies `create_engine` actually wires the translated URL into the real engine, not just that construction didn't throw. | applied in this PR |
| test_create_session_factory_returns_factory | **rewrite** | Same `is not None` tautology. The function's whole documented purpose (per its docstring) is to force `expire_on_commit=False`; the original test never checked that. Rewritten to assert `isinstance(factory, async_sessionmaker)` and `factory.kw["expire_on_commit"] is False`. | applied in this PR |
| test_create_engine_accepts_pool_params | **rewrite** | Config-restatement: passed `pool_size=3, max_overflow=7, pool_timeout=15.0, pool_recycle=900, pool_pre_ping=False` and asserted only `engine is not None` — none of the five params were checked to have actually taken effect, so a regression that silently dropped every kwarg would still pass. Rewritten to assert `engine.pool.size() == 3`, a real, publicly-documented `QueuePool`/`AsyncAdaptedQueuePool` accessor that verifies `pool_size` was actually threaded through `create_async_engine`. | applied in this PR |
| test_settings_db_pool_defaults | keep | Real `Settings()` instantiation, real default-value assertions across five fields — matches the established `test_config.py` pattern for legitimate default-drift guards. | none |
| test_all_tables_registered | keep | Real `Base.metadata` introspection, no mocking. | none |
| test_user_table_has_tenant_id_column | keep | Real SQLAlchemy `__table__.columns` introspection. | none |
| test_message_table_has_tenant_id_column | keep | Real SQLAlchemy `__table__.columns` introspection. | none |
| test_document_table_has_tenant_id_column | keep | Real SQLAlchemy `__table__.columns` introspection. | none |
| test_default_tenant_id_is_uuid | keep | Real type check on a real module constant, no mocking. | none |
| test_user_insert_and_fetch | keep | `@pytest.mark.integration`; real DB round trip via the `session` fixture, real `select`/`scalar` query, asserts real returned field values (`tenant_id`, `is_admin`), not a mock echo. | none |
| test_message_insert | keep | Real DB insert + flush, asserts a real server-assigned `id`. | none |
| test_document_insert | keep | Real DB insert + flush, asserts real default value (`is_indexed is False`). | none |

**File totals:** 15 keep / 3 rewrite / 0 delete.

### tests/test_observability.py

| Test | Verdict | Rationale | Action |
|---|---|---|---|
| test_configure_logging_production_mode_emits_json | **rewrite** | Originally `test_configure_logging_production_mode`, whose only assertion was `logger is not None` — `structlog.get_logger()` never returns `None`, so this was a pure tautology that verified nothing about production-mode JSON output. Renamed and rewritten to capture real stdout via `capsys`, parse the emitted line as JSON, and assert real field values (`event`, `foo`, `level`). No mocking. | applied in this PR |
| test_configure_logging_debug_mode_emits_console_output | **rewrite** | Same tautology (`logger is not None`) in the original `test_configure_logging_debug_mode`. Rewritten to assert the human-readable event string appears in captured output and that the output is *not* valid JSON (`pytest.raises(JSONDecodeError)`) — a genuine behavioral contrast with the production-mode test. | applied in this PR |
| test_trace_context_in_logs_when_span_active | keep | Real OTel `TracerProvider`/span, real `_add_trace_context` processor call; asserts the real hex-formatted `trace_id` matches the span's own context and that GCP-specific log keys are populated. No mocking anywhere. | none |
| test_trace_context_absent_without_span | keep | Real no-op-span branch of `_add_trace_context`; asserts the keys are genuinely absent, not just falsy (strengthened in this pass from a weaker guarded conditional). | none |
| test_configure_tracing_disabled_leaves_provider_unset | keep | Real global-state check: captures the tracer provider before and after `enabled=False`, asserts identity (`is`) is unchanged — a real no-op guarantee, not a mock assertion. | none |
| test_configure_tracing_no_exporter_installs_provider_without_processor | keep | Real OTel provider installed; introspects the real (private but stable, already-used-elsewhere-in-file) `_active_span_processor._span_processors` tuple to assert zero processors when unconfigured. | none |
| test_configure_tracing_debug_console_exporter_adds_batch_processor | keep | Real provider wiring; asserts the real processor and exporter types (`BatchSpanProcessor` wrapping `ConsoleSpanExporter`) via `isinstance`, not a mock. | none |
| test_build_exporter_returns_none_without_config | keep | Pure function, real input/output. | none |
| test_build_exporter_returns_console_in_debug | keep | Pure function, real input/output, `isinstance` check on the real return type. | none |
| test_configure_tracing_with_sample_rate_threads_rate_to_sampler | keep | Real sampler installed on the real global provider; asserts both type (`TraceIdRatioBased`) and the actual configured rate value — would catch the rate silently not being threaded through. | none |
| test_configure_tracing_instruments_fastapi | keep | `FastAPIInstrumentor.instrument_app` is mocked at the third-party instrumentation boundary (avoids real bytecode patching of Starlette internals in a unit test); assertion is `assert_called_once_with(app)`, an exact-args check on real `configure_tracing` orchestration logic, not a mock echoing itself. | none |
| test_request_id_generated_when_missing | keep | Real FastAPI `TestClient` request through the real `RequestIdMiddleware`; asserts a real UUID4-shaped header was generated. No mocking. | none |
| test_request_id_preserved_when_present | keep | Real end-to-end header passthrough assertion. | none |
| test_configure_langfuse_disabled_without_credentials_skips_client | keep | `langfuse` module is mocked only because it's an optional third-party dependency (import boundary); assertion (`assert_not_called`) verifies real `configure_langfuse` guard logic short-circuits before construction. | none |
| test_configure_langfuse_disabled_partial_credentials_skips_client | keep | Same real guard-logic branch, partial-credentials case. | none |
| test_configure_langfuse_initialises_with_credentials | keep | Same import-boundary mocking; asserts real `configure_langfuse` passes through exact `secret_key`/`public_key`/`host` values via `assert_called_once_with`, not a bare `.called`. | none |
| test_flush_langfuse_safe_when_not_configured | keep | No mocking; calls the real function in the not-configured state and asserts it doesn't raise — a real, meaningful guarantee for a function whose job is "never break the app". | none |
| test_flush_langfuse_swallows_client_errors | keep | New test added in this pass. Constructs a real mock client whose `.flush()` raises, verifying `flush_langfuse`'s real exception-swallowing behavior (the actual contract under test) while `assert_called_once()` confirms the real code path was reached rather than short-circuited. | added in this PR |
| test_observe_decorator_does_not_break_async_functions | keep | Real `@observe()` decorator applied to a real async function; asserts the real computed result (`10`), not a mock return value — verifies the decorator doesn't swallow the coroutine. | none |

**File totals:** 17 keep / 2 rewrite / 0 delete (19 tests; includes one new test added in this pass to close a coverage gap). Beyond the two rewrite verdicts above (both fixing genuine `is not None` tautologies), this pass also added an autouse `_reset_otel_tracer_provider` fixture that resets OpenTelemetry's process-global `TracerProvider` before and after every test — without it, `configure_tracing()`'s set-once global meant a test running after an earlier one silently inherited whatever provider that earlier test installed. Several of the tracing/Langfuse tests above (`test_configure_tracing_disabled_leaves_provider_unset`, `test_configure_tracing_no_exporter_installs_provider_without_processor`, `test_configure_tracing_debug_console_exporter_adds_batch_processor`, `test_configure_tracing_with_sample_rate_threads_rate_to_sampler`, and the two `test_configure_langfuse_disabled_*` tests) had their assertions strengthened in the same pass — they were already real, non-tautological "doesn't raise"/"doesn't construct a client" checks before this pass (matching this audit's established treatment of thin-but-real smoke tests, e.g. `NoOpModerator::test_close_is_noop`), so they remain "keep" rather than "rewrite", but the isolation fix was necessary for their strengthened assertions to be deterministic under any test execution order.

### tests/test_openapi_spec.py

| Test | Verdict | Rationale | Action |
|---|---|---|---|
| test_committed_openapi_spec_is_fresh | keep | Real drift guard: reads the actual committed `openapi.json` from disk and compares it byte-for-byte against a freshly serialized spec generated from the real, live FastAPI app (`get_openapi_spec()`/`serialize_spec()`, both real, unmocked). This is exactly the kind of test the rubric wants — behavior-sensitive (fails the moment a route or schema changes without regenerating the committed file) and deterministic. | none |

**File totals:** 1 keep / 0 rewrite / 0 delete.

### tests/test_prompts.py

| Test | Verdict | Rationale | Action |
|---|---|---|---|
| TestBuildRagPrompt::test_formats_chunks_correctly | keep | Calls `build_rag_prompt` with real chunk data, asserts on numbering, content, and separator behavior. Behavior-sensitive and specific. | — |
| TestBuildRagPrompt::test_empty_chunks_returns_no_documents_message | keep | Exercises the empty-input branch of `build_rag_prompt`; deterministic and specific. | — |
| TestBuildRagPrompt::test_single_chunk | **rewrite** | Docstring claims "formatted without separator" but original test never asserted `"---"` absence, so the single-chunk-vs-separator behavior wasn't actually covered. | applied in this PR |
| TestBuildRagPrompt::test_score_not_included_in_output | keep | Asserts the unused `score` value never leaks into the rendered prompt text; real behavior guard. | — |
| TestRagSystemPrompt::test_contains_strict_rules | keep | Static-string check, but guards hallucination-prevention safety copy (STRICT RULES / ONLY / NEVER) that is not exercised by any other test; regression here is a real product-safety risk. | — |
| TestRagSystemPrompt::test_contains_context_placeholder | **delete** | Structure-mirror: only checks the literal `{context}` token exists in the template. Fully redundant — if the placeholder were removed, `test_formats_chunks_correctly`/`test_score_not_included_in_output` would already fail because substituted content would never appear. | applied in this PR |
| TestRagSystemPrompt::test_mentions_retriever | **delete** | Config-restatement: asserts a branding word appears in a string literal, no code executed. Low-value cosmetic check. | applied in this PR |
| TestFallbackSystemPrompt::test_exists_and_non_empty | **delete** | Near-tautological: a hardcoded non-empty string literal is checked for non-emptiness/length. No behavior exercised, effectively always true. | applied in this PR |
| TestFallbackSystemPrompt::test_mentions_no_documents | keep | Static-string check, but protects the one differentiating behavior of the fallback prompt (telling the volunteer no documents are indexed); no other test covers this content. | — |
| TestFallbackSystemPrompt::test_mentions_retriever | **delete** | Config-restatement duplicate of the RAG-prompt branding check; no behavior exercised. | applied in this PR |

**File totals:** 5 keep / 1 rewrite / 4 delete (10 tests originally). No mocking is used anywhere in this file.

### tests/test_rag_dependencies.py

| Test | Verdict | Rationale | Action |
|---|---|---|---|
| test_get_session_factory_delegates_to_shared_factory | **delete** | Mock-echo: patches `_get_factory`, calls the one-line wrapper `get_session_factory`, asserts the mock's own return value comes back. Tests only that a pass-through delegates, no real logic. | applied in this PR |
| test_get_rag_service_creates_singleton | keep | Exercises real module-level singleton caching logic across two calls with real (non-mocked) constructors for every RAG component; only `_get_factory`/`get_settings` are mocked to avoid a live DB/env dependency. | — |
| test_reset_dependencies_clears_singleton | keep | Exercises the real reset-then-rebuild singleton behavior; deterministic, specific. | — |
| test_get_semantic_cache_returns_none_when_disabled | keep | Real conditional branch (`cache_enabled=False -> None`). | — |
| test_get_semantic_cache_returns_cache_when_enabled | **rewrite** | Original only asserted `is not None`; strengthened to `isinstance(result, PgSemanticCache)` so the test verifies the real branch returns the correct concrete type, not just a truthy value. | applied in this PR |
| test_get_hybrid_retriever_returns_none_when_disabled | keep | Real conditional branch (`hybrid_retrieval_enabled=False -> None`). | — |
| test_get_hybrid_retriever_returns_retriever_when_enabled | **rewrite** | Strengthened `is not None` to `isinstance(result, HybridRetriever)` for the same reason as the semantic-cache case. | applied in this PR |
| test_get_embedding_provider_uses_gateway_base_url | keep | Constructs the real provider and inspects the real client's `base_url`; specific, behavior-sensitive. | — |
| test_get_embedding_provider_keeps_provider_prefix | keep | Verifies the real model string threaded from settings into the provider. | — |
| test_get_embedding_provider_sends_gateway_token_header | keep | Verifies the real gateway client carries the BYOK auth header built from settings. | — |
| test_get_llm_provider_uses_settings_fallback_model | keep | Verifies fallback model is sourced from settings, not hardcoded, on the real provider object. | — |
| test_get_llm_provider_sends_gateway_token_header | keep | Verifies the real nested provider's client carries the gateway auth header. | — |
| test_get_safety_service_routes_moderator_through_gateway | keep | Verifies real `openai_api` backend wiring (base URL) on the constructed moderator. | — |
| test_get_safety_service_uses_guardrails_by_default | keep | Real isinstance check on the default moderation backend selection. | — |
| test_get_safety_service_uses_openai_api_backend | keep | Real isinstance check on the `openai_api` backend selection. | — |
| test_get_safety_service_returns_none_when_disabled | keep | Real conditional branch (`moderation_enabled=False -> None`). | — |
| test_get_vector_store_creates_store | **rewrite** | Strengthened `is not None` to `isinstance(store, PgVectorStore)`. | applied in this PR |
| test_get_confidence_scorer_creates_scorer | **rewrite** | Strengthened `is not None` to `isinstance(scorer, ConfidenceScorer)`. | applied in this PR |
| test_get_message_repository_creates_repo | **rewrite** | Strengthened `is not None` to `isinstance(repo, MessageRepository)`. | applied in this PR |
| test_get_document_processor_returns_format_aware | keep | Already asserts `isinstance(processor, FormatAwareProcessor)`; real construction from settings. | — |

**File totals:** 14 keep / 5 rewrite / 1 delete (20 tests originally).

### tests/test_rag_routes.py

| Test | Verdict | Rationale | Action |
|---|---|---|---|
| test_ask_success_returns_answer | keep | Real end-to-end `TestClient` POST through the actual `ask` route; only the expensive/external boundaries (`RAGService`, `MessageRepository`) are mocked via DI overrides. Asserts specific, distinct field values (`answer`, `confidence_level`, `confidence_score`, `blocked`, `blocked_reason`, `chunks_used[0].source`) that only pass if `_to_ask_response`'s real field mapping and FastAPI's real response-model serialization both run correctly — a swapped or dropped field would fail this test, not just a mock-echo. | — |
| test_ask_saves_user_and_assistant_messages | keep | Asserts real route orchestration: `save_message` called exactly twice, with correct `role`/`content` kwargs and correct call order (user then assistant). This exercises the route's own persistence logic, not the mock's behavior. | — |
| test_ask_loads_conversation_history | keep | Verifies the route's real `Message` → `{"role", "content"}` dict transformation and that it's threaded into `rag_service.ask(conversation_history=...)`; specific value assertions on both list length and per-item shape. | — |
| test_ask_requires_auth | keep | `require_auth` is *not* overridden here, so the real FastAPI auth dependency executes; asserts the real 401/403 outcome. Genuine auth-boundary guard, not a mock. | — |
| test_ask_empty_question_returns_422 | keep | Exercises the real Pydantic `min_length=1` constraint on `AskRequest.question`; no mocking involved in the validation path. | — |
| test_ask_question_too_long_returns_422 | keep | Exercises the real Pydantic `max_length=2000` constraint with a boundary-crossing input (2001 chars); guards a genuine off-by-one regression class. | — |
| test_ask_blocked_by_safety_returns_blocked_response | keep | Same real-mapping justification as `test_ask_success_returns_answer`, covering the `blocked=True`/`blocked_reason` branch specifically (a distinct code path from the happy-path test). | — |
| test_ask_missing_question_returns_422 | keep | Exercises the real Pydantic required-field validator (`question` has no default) — a different validator than the `min_length`/`max_length` tests, so not redundant with them. | — |
| test_ask_no_history_passes_none_to_rag | keep | Verifies the real `conversation_history if conversation_history else None` branch in the route: empty history list from the repo must surface as `None` to the RAG service, not `[]`. Specific, behavior-sensitive. | — |

**File totals:** 9 keep / 0 rewrite / 0 delete. No edits applied — every test exercises a distinct, real route-level behavior (request validation, auth wiring, history-to-dict transformation, persistence call shape, or response-field mapping) through an actual `TestClient` HTTP round trip; mocking is confined to the RAG/DB service-layer DI seams.

### tests/test_message_routes.py

| Test | Verdict | Rationale | Action |
|---|---|---|---|
| test_get_history_returns_messages | keep | Real `TestClient` GET through the actual `get_history` route; asserts real `Message` → `MessageResponse` mapping (count, list length, per-item `role`, and preserved order) via the real response model. | — |
| test_get_history_empty | keep | Real empty-list branch; asserts `count == 0` and `messages == []`, not just truthiness. | — |
| test_get_history_requires_auth | keep | `require_auth` not overridden; asserts the real 401/403 outcome from the real dependency. | — |
| test_clear_history_deletes_messages | **rewrite** | Original asserted `"3" in data["message"]`, a loose substring check that would also pass for accidental strings like `"has 3 items"` or `"33"`. Rewritten to `data["message"] == "Cleared 3 message(s)."`, an exact match on the real f-string the route builds from `deleted`, tightening the test to guard the actual message format. | applied in this PR |
| test_clear_history_no_messages | keep | Real zero-deletion branch; asserts `deleted_count == 0`, a distinct value from the non-zero case above. | — |
| test_clear_history_requires_auth | keep | `require_auth` not overridden; real 401/403 auth-boundary guard on this specific route. | — |
| test_get_history_passes_correct_user_id | keep | Asserts the real `uuid.UUID(user.sub)` conversion the route performs is actually threaded into `get_recent_messages(user_id=...)` — a specific call-arg check on real route logic, not `assert_called()` alone. | — |
| test_clear_history_passes_correct_user_id | keep | Same real-conversion justification for the `clear_messages(user_id=...)` call on the delete route. | — |

**File totals:** 7 keep / 1 rewrite / 0 delete.

### tests/test_subscription_guard.py

| Test | Verdict | Rationale | Action |
|---|---|---|---|
| test_subscribed_user_passes_documents_route | keep | Builds the real `create_app()` FastAPI app with real router-level `require_subscription` dependency wiring; only `require_auth` (JWT/JWKS network boundary) is overridden. Exercises real claim-based guard logic. | none |
| test_subscribed_user_passes_messages_route | keep | Same real-wiring pattern against the messages/history router. | none |
| test_subscribed_user_passes_rag_route | keep | Same pattern against the `/api/v1/ask` router; assertion is deliberately narrow (`!= 403`) to isolate the guard from downstream RAG pipeline behavior, which is out of scope for this file. | none |
| test_unsubscribed_user_blocked_documents_route | keep | Real guard rejects a real user object lacking the `retriever` claim; asserts exact 403 body, not just status code. | none |
| test_unsubscribed_user_blocked_messages_route | keep | Same real-rejection pattern for the messages router. | none |
| test_unsubscribed_user_blocked_rag_route | keep | Same real-rejection pattern for the ask router. | none |
| test_expired_subscription_blocked_with_403 | keep | Distinct edge case (claims present but the specific `retriever` tool claim absent) exercised for real, not a duplicate of the empty-claims case. | none |
| test_health_remains_unguarded | keep | Verifies real router composition excludes `/health` from the subscription dependency; asserts real status code. | none |

**File totals:** 8 keep / 0 rewrite / 0 delete.

### tests/test_storage.py

| Test | Verdict | Rationale | Action |
|---|---|---|---|
| test_in_memory_round_trip | keep | Real `InMemoryStorage` put/get round trip, real bytes equality assertion. | none |
| test_in_memory_get_missing_raises | keep | Real `ObjectNotFoundError` raised by real code path. | none |
| test_in_memory_delete_missing_is_noop | **rewrite** | Original body had zero assertions — it only relied on the absence of a raised exception, so it couldn't catch a delete-of-missing that silently corrupted other stored state. | Added a `put`/`delete`/`get` sequence asserting an unrelated key survives the no-op delete. |
| test_in_memory_delete_then_get_raises | keep | Real put→delete→get sequence, real exception assertion. | none |
| test_in_memory_url_is_deterministic_string | keep | Real deterministic `memory://key` format assertion, not a mock return value. | none |
| test_r2_put_delegates | keep | `R2Storage` (real, unmocked) wraps a hand-written `_FakeS3Client` test double standing in for boto3/AWS's S3-compatible client — a legitimate external network boundary, not retriever-owned code. Asserts exact forwarded kwargs. | none |
| test_r2_get_round_trip | keep | Real `R2Storage.put`/`get` round trip through the fake client; real bytes equality. | none |
| test_r2_get_missing_maps_to_object_not_found | keep | Verifies real `_is_not_found` mapping logic translates a `NoSuchKey` client error into `ObjectNotFoundError`. | none |
| test_r2_get_missing_bucket_propagates_client_error | keep | Verifies real logic does *not* swallow a `NoSuchBucket` misconfiguration error — asserts the original exception type propagates. | none |
| test_r2_delete_delegates | keep | Real delegation logic; asserts exact forwarded kwargs and real post-condition (key removed from fake store). | none |
| test_r2_delete_missing_is_noop | keep | Asserts the real call still reaches `delete_object` (idempotent S3 semantics) even when the key is absent. | none |
| test_r2_delete_propagates_client_error | keep | Verifies a non-not-found error (`AccessDenied`) is not swallowed by the real `_is_not_found` check. | none |
| test_r2_url_delegates | keep | Real presigned-URL delegation; asserts exact forwarded operation, params, and expiry. | none |
| test_r2_endpoint_from_explicit_url | keep | Real `Settings.r2_endpoint` property precedence logic, real pydantic model. | none |
| test_r2_endpoint_from_account_id | keep | Real fallback URL construction from account id. | none |
| test_r2_endpoint_raises_when_unconfigured | keep | Real `ValueError` from real property logic, message-matched. | none |
| test_build_r2_storage_raises_when_config_empty | keep | Real `build_r2_storage` validation path raises real `StorageConfigError` before ever touching boto3. | none |

**File totals:** 16 keep / 1 rewrite / 0 delete.

### tests/test_vectordb.py

| Test | Verdict | Rationale | Action |
|---|---|---|---|
| test_upsert_and_search | keep | `@pytest.mark.integration` against a real, freshly-created-per-test Postgres/pgvector schema (`db_engine` fixture auto-skips when unreachable, matching the `test_cache.py` precedent). Real cosine-similarity search, real content and score assertions — no mocking of `PgVectorStore`. | none |
| test_search_returns_empty_below_threshold | **rewrite** | Assertion only checked `isinstance(results, list)`, which trivially passes for a non-empty list too — it doesn't actually verify the "empty" the test name and docstring claim. Additionally, the query embedding and any embedding built from the same `_embedding()` helper are collinear constant vectors with cosine similarity 1.0 against each other, so the test never truly exercises the `min_score` filter — it passes only because no chunk exists for the fresh random tenant. | Strengthened the assertion to `results == []` (correct given the fixture's per-test schema) and added a docstring note naming the collinear-vector gap. |
| test_delete_by_document | keep | Real upsert → real delete_by_document → real search sequence against a live DB; asserts the deleted content is genuinely absent from results, not a mock call count. | none |

**File totals:** 2 keep / 1 rewrite / 0 delete.

**Follow-on filed:** the `min_score` WHERE-clause filter itself (excluding a chunk whose cosine similarity is genuinely below threshold while another chunk for the same tenant is above it) has no real test coverage in this file — `_embedding()`'s constant-vector shape makes every non-trivial embedding collinear. A follow-on should add a non-constant embedding fixture (e.g. two chunks with orthogonal-ish vectors) to exercise the actual filter branch.

### tests/test_rag_service.py

All infrastructure collaborators (`LLMProvider`, `EmbeddingProvider`, `VectorStore`, `DocumentProcessor`, `SemanticCache`, `HybridRetriever`, `SafetyService`, `ConfidenceScorer`) are mocked via `AsyncMock`/`MagicMock` fixtures; `RAGService` itself runs unmocked. See the Mock-of-own-code inventory below for the boundary assessment.

| Test | Verdict | Rationale | Action |
|---|---|---|---|
| TestAskBasicFlow::test_ask_returns_answer | keep | Real `RAGService.ask` orchestration executes; asserts real field mapping (answer, question echo, chunks_used count, blocked flag) plus exact call args on the embed/search/complete boundary mocks. | none |
| TestAskWithCache::test_ask_with_cache_hit | keep | Exercises the real cache-hit short-circuit branch; asserts the cached answer and deserialized chunk count are used, and that `complete`/`complete_with_history`/`search` are never awaited — a real negative-call assertion, not just a happy-path check. | none |
| TestAskWithCache::test_ask_with_cache_miss | keep | Exercises the real cache-miss branch: LLM is called and the result is written back to cache. `cache.set` is checked only for call count, not exact kwargs, so it would not catch a bug in which value is cached — acceptable for a wiring test, but weaker than it could be. | none |
| TestAskSafety::test_ask_safety_blocks_input | keep | Real early-return branch on unsafe input; the `embeddings.embed` not-awaited assertion is a strong, specific check that the pipeline short-circuits *before* embedding, not just before generation. | none |
| TestAskSafety::test_ask_hallucination_detected | keep | Real post-generation block branch; asserts the non-obvious real behavior that `chunks_used` is retained (length 2) even though the response is blocked, unlike the input-blocked case where it's empty. | none |
| TestAskNoDocuments::test_ask_no_documents | keep | Real fallback-prompt branch when retrieval returns no chunks; asserts real answer/chunks_used/blocked fields. | none |
| TestAskHybridRetrieval::test_ask_with_hybrid_retrieval | keep | Real conditional branch selection (hybrid retriever over direct vector-store search) with a real negative assertion (`search.assert_not_awaited`) plus real content mapping check. | none |
| TestAskConversationHistory::test_ask_with_conversation_history | keep | Verifies real list-extension logic (history + new user turn) via exact message content and length assertions, not a mock echo. | none |
| TestAskConfidenceScoring::test_ask_with_confidence_scoring | keep | Asserts `ConfidenceScorer.score` is called with real business-computed `chunk_scores`/`grounding_ratio` values threaded through from the search results and the hallucination-detail mock (a real wiring check); the trailing `response.confidence_level`/`confidence_score` assertions do mirror the mock's configured return, but they ride along with the stronger call-args check rather than standing alone. | none |
| TestIndexDocument::test_index_document | keep | Real data-flow verification: raw bytes → processor → chunk contents → `embed_batch` → `upsert`, with exact-argument assertions at each boundary hop. | none |
| TestIndexDocument::test_index_document_error | keep | Real try/except path in `index_document`; asserts the real exception message is folded into `error_message`, not swallowed. | none |
| TestIndexDocument::test_index_document_empty_chunks | keep | Real early-return branch for zero chunks; the `embed_batch.assert_not_awaited()` check confirms the short-circuit actually skips embedding rather than just returning the right counts by coincidence. | none |
| TestClearCache::test_clear_cache | keep | Real default-tenant fallback; asserts `invalidate` called with the service's configured tenant. | none |
| TestClearCache::test_clear_cache_with_explicit_tenant | keep | Distinct real branch from the previous test (explicit tenant overrides the default) — not redundant. | none |
| TestClearCache::test_clear_cache_no_cache_configured | **rewrite** | Original body called `service.clear_cache()` with no assertions at all — a pure "does not raise" test. | Captured the return value and added `assert result is None`, matching the real (always-`None`) return of `clear_cache`. |

**File totals:** 14 keep / 1 rewrite / 0 delete.

**Follow-on filed:** no test in this file drives `ConfidenceScore.needs_review = True` through `ask()` to verify the real `not confidence.needs_review` gate on line ~340 of `service.py` skips `cache.set` for low/medium-confidence answers — every fixture's `mock_confidence_scorer` is hardcoded to `needs_review=False`. A follow-on should add a case where the confidence scorer mock returns `needs_review=True` and assert `cache.set` is *not* awaited.

### tests/test_safety.py

| Test | Verdict | Rationale | Action |
|---|---|---|---|
| TestPromptInjectionDetector::test_normal_question_not_flagged | keep | Real `PromptInjectionDetector`, no mocking. Runs five realistic volunteer questions through the real regex pattern set and asserts none are flagged — guards against overly-broad patterns causing false positives. | none |
| TestPromptInjectionDetector::test_ignore_instructions_detected | keep | Real detector, real regex match against four phrasing variants of instruction-override attacks. | none |
| TestPromptInjectionDetector::test_role_change_detected | keep | Real detector, real regex match against four role-manipulation phrasings. | none |
| TestPromptInjectionDetector::test_system_prompt_extraction_detected | keep | Real detector, real regex match against four prompt-extraction phrasings. | none |
| TestPromptInjectionDetector::test_jailbreak_attempts_detected | keep | Real detector, real regex match against three jailbreak phrasings. | none |
| TestPromptInjectionDetector::test_debug_mode_detected | keep | Real detector, real regex match against three debug/admin-mode phrasings. | none |
| TestPromptInjectionDetector::test_get_matched_pattern_returns_name | keep | Asserts the specific matched pattern *name* (`ignore_instructions`, `role_change`), not just a boolean — catches pattern-to-name mis-mapping that `is_injection` alone would miss. | none |
| TestPromptInjectionDetector::test_case_insensitive | keep | Real case-folding behavior via `re.IGNORECASE`, asserted on three case variants. | none |
| TestPromptInjectionDetector::test_custom_patterns | keep | Real constructor extension point (`additional_patterns`); verifies both detection and correct name lookup for the injected patterns. | none |
| TestPromptInjectionDetector::test_partial_matches | keep | Verifies patterns match when embedded in longer surrounding text, not just at string boundaries — a real, distinct behavior from the other detection tests. | none |
| TestModerationResult::test_safe_result | keep | Real `ModerationResult.safe()` classmethod; this factory is the fail-open default used throughout the safety stack, so its exact shape (empty dicts, `flagged=False`) is worth pinning. | none |
| TestModerationResult::test_flagged_result | keep | Direct pydantic construction with real field access; thin (no custom validation logic to exercise) but cheap and not harmful. | none |
| TestSafetyCheckResult::test_passed_result | keep | Real `passed()` classmethod; asserts violation type and message content, not just truthiness. | none |
| TestSafetyCheckResult::test_failed_moderation | keep | Real `failed_moderation()` classmethod; asserts `details["flagged_categories"]` actually contains the passed category, not just that `details` is non-None. | none |
| TestSafetyCheckResult::test_failed_injection | keep | Real `failed_injection()` classmethod; asserts the specific matched-pattern value round-trips into `details`. | none |
| TestSafetyCheckResult::test_failed_hallucination | keep | Real `failed_hallucination()` classmethod; asserts the specific `support_ratio` value round-trips into `details`. | none |
| TestSafetyCheckResult::test_user_messages_are_helpful | keep | Encodes a real security contract: moderation and injection failures share one message (so a user can't distinguish which check fired and probe the detector), while hallucination failures use a different, distinct message. Specific, behavior-sensitive, and would catch a regression that leaked which safety layer blocked the request. | none |
| TestNoOpModerator::test_always_returns_safe | keep | Real `NoOpModerator.check()`, real return-value assertion. | none |
| TestNoOpModerator::test_close_is_noop | keep | Thin (no explicit assertion beyond "doesn't raise") but real: `close()` on the disabled-moderation default path must never throw, since `SafetyService.close()` calls it unconditionally. A mutation that made this raise would be caught. | none |
| TestGuardrailsModerator::test_always_returns_safe | keep | Real `GuardrailsModerator.check()`, real return-value assertion. | none |
| TestGuardrailsModerator::test_takes_no_client | **delete** | Sole assertion (`not hasattr(moderator, "_client")`) is a pure structure check on an internal implementation detail, not an observable behavior — a legitimate future refactor (e.g. holding a placeholder attribute) would break this test with no behavior change. Fully redundant with `test_check_makes_no_http_call`, which covers the same "no client is ever called" intent via a real functional assertion (`result == ModerationResult.safe()`). | Removed from `test_safety.py`. |
| TestGuardrailsModerator::test_check_makes_no_http_call | **rewrite** | Had the same structure-sensitive `hasattr` assertion bolted onto an otherwise-good functional assertion. The `hasattr` line added no behavior-sensitivity beyond what the real `check()` call + return-value assertion already provides, while making the test brittle to internal refactors. | Removed the `assert not hasattr(moderator, "_client")` line; kept the real `check()` call and `result == ModerationResult.safe()` assertion. |
| TestGuardrailsModerator::test_close_is_noop | keep | Same thin-but-real smoke-test rationale as `NoOpModerator::test_close_is_noop`. | none |
| TestOpenAIModerator::test_safe_content_returns_safe | keep | Mocks only the external `AsyncOpenAI` client (`moderations.create`) — a genuine external-API boundary. Real parsing logic in `OpenAIModerator.check()` runs and is asserted on. | none |
| TestOpenAIModerator::test_flagged_content_returns_flagged | keep | Same boundary-mocking pattern; asserts real category-dict parsing (`result.categories["hate"] is True`), not just `.flagged`. | none |
| TestOpenAIModerator::test_timeout_fails_open | keep | Real fail-open exception-handling branch (`TimeoutError`) exercised via a mocked SDK `side_effect`; asserts the real safe fallback. | none |
| TestOpenAIModerator::test_api_error_fails_open | keep | Real fail-open branch for a generic exception, distinct code path from the timeout branch. | none |
| TestOpenAIModerator::test_bad_request_logs_endpoint_unsupported | keep | Real `BadRequestError` branch; patches the module logger to assert the *specific* structured-log event name (`moderation_endpoint_unsupported`) fired and the generic one did not — this event name is an intentional operator-facing contract per the source comments, so pinning it is real, specific, behavior-sensitive coverage of an otherwise-invisible side effect. | none |
| TestOpenAIModerator::test_bad_request_distinct_from_generic_error | keep | Complements the above: verifies the generic-error branch logs the *other* event name and not the endpoint-unsupported one — together the pair is mutation-killable against the branches being merged or swapped. | none |
| TestOpenAIModerator::test_close_calls_client_close | keep | Real `close()` delegates to the injected client's `close()`; `assert_awaited_once()` on the mocked external client, not on the unit under test. | none |
| TestOpenAIModerator::test_calls_with_correct_model | keep | Asserts exact call kwargs (`input`, `model=openai/omni-moderation-latest`) via `assert_awaited_once_with` — would catch silent model-slug drift. | none |
| TestOpenAIModerator::test_routes_through_injected_gateway_client | keep | Builds a real `AsyncOpenAI` client via the real `build_gateway_client()` (only `Settings` is a `MagicMock` supplying input values); asserts real base URL and auth header on the real constructed client, then real DI-identity through `OpenAIModerator`. No mocking of the moderator or gateway-client logic under test. | none |
| TestHallucinationDetector::test_grounded_answer | keep | Real `HallucinationDetector.check()`, real keyword-overlap computation; asserts both `is_grounded` and a `support_ratio` floor. | none |
| TestHallucinationDetector::test_hallucinated_answer | keep | Real detection of an unsupported claim against real chunks. | none |
| TestHallucinationDetector::test_empty_answer | keep | Real edge case: no answer text -> no claims -> vacuously grounded; asserts `total_claims == 0` specifically, not just `is_grounded`. | none |
| TestHallucinationDetector::test_no_claims_in_answer | keep | Real claim-extraction filter (short/non-substantive sentences produce no claims). | none |
| TestHallucinationDetector::test_empty_chunks | keep | Real edge case: claims exist but no chunks to verify against -> not grounded. Distinct branch from the no-claims case above. | none |
| TestHallucinationDetector::test_partial_support | keep | Real mixed-support scenario (one of two claims supported); the loose bound (`0.3 < ratio < 0.8`) still requires the real keyword-overlap math to land in a specific band, not a tautology. | none |
| TestHallucinationDetector::test_claim_extraction_filters_questions | keep | Real question-filtering branch in `_extract_claims`; asserts the specific resulting claim count. | none |
| TestHallucinationDetector::test_custom_threshold | **rewrite** | Original scenario (`"One true claim here. Another true claim too."` against `["One true claim here."]`) produced keyword overlap high enough that *both* claims were supported (support_ratio 1.0) regardless of threshold, so the assertion `is_grounded or support_ratio >= 0.5` passed even if the constructor's `support_threshold` argument were silently ignored — the test's stated purpose ("custom threshold should be respected") was never actually exercised. | Replaced with a scenario where exactly one of two claims is supported (`support_ratio == 0.5`): grounded at the custom 0.5 threshold, would fail the module's default 0.8 threshold. Now mutation-killable against the threshold argument being dropped. |
| TestHallucinationDetector::test_sources_tracked | **rewrite** | The body's only assertion was gated behind `if result.claims and result.claims[0].supported:` — with the original answer/chunk pair the claim was *not* supported (keyword overlap ~0.33, no substring match), so the guarded assertion silently never ran and the test passed vacuously regardless of whether source-tracking worked at all. Classic assertion-swallowing conditional. | Replaced the answer/chunk pair with an exact-substring match that deterministically yields `supported=True`, and made all three assertions (`total_claims`, `supported`, `supporting_source`) unconditional. |
| TestSafetyService::test_safe_input_passes | keep | Real `SafetyService` with default (real) collaborators end-to-end; asserts both `is_safe` and the specific `violation_type`. | none |
| TestSafetyService::test_injection_blocked | keep | Real end-to-end injection blocking through the default `PromptInjectionDetector`, no mocking. | none |
| TestSafetyService::test_output_moderation | keep | Real service, default `NoOpModerator`; exercises the real output-check pass-through path. | none |
| TestSafetyService::test_hallucination_check_grounded | keep | Real hallucination path through the service facade, real assertion. | none |
| TestSafetyService::test_hallucination_check_detected | keep | Real hallucination-detected path; asserts specific `violation_type`, not just `is_safe`. | none |
| TestSafetyService::test_get_hallucination_details | **rewrite** | Two of three assertions were `hasattr(details, "support_ratio")` / `hasattr(details, "claims")` — since `HallucinationCheckResult` is a pydantic model, those fields always exist on the schema regardless of computed values, so the assertions were structurally tautological and could never fail from a logic bug. | Replaced the `hasattr` checks with real value assertions: exact `total_claims == 2`, `len(claims) == total_claims`, a bounded `support_ratio`, and the exact text of the first extracted claim. |
| TestSafetyService::test_close | keep | Thin smoke test but real: `close()` on the default `NoOpModerator`-backed service must not raise, since callers call it unconditionally on shutdown. | none |
| TestSafetyService::test_input_moderation_flagged | keep | `SafetyService` (unit under test) is real; only its `ModerationProvider` collaborator is a test double standing in for a flagged-moderation scenario that's otherwise hard to drive through the real `NoOpModerator` default. Legitimate DI-seam substitution, not mocking the unit under test — asserts real `is_safe`/`violation_type` outcome. | none |
| TestConfidenceScorer::test_high_confidence_with_good_scores | keep | Real `ConfidenceScorer.score()`, real weighted computation; asserts level, score floor, and `needs_review`. | none |
| TestConfidenceScorer::test_low_confidence_with_poor_scores | keep | Real computation, LOW branch with a score ceiling and `needs_review is True`. | none |
| TestConfidenceScorer::test_medium_confidence | keep | Real computation, MEDIUM branch with both bounds checked. | none |
| TestConfidenceScorer::test_no_chunks_is_low_confidence | keep | Real edge case: empty `chunk_scores` list -> forced LOW + `needs_review`. | none |
| TestConfidenceScorer::test_without_grounding_ratio | keep | Real branch coverage: `grounding_ratio=None` omits the `"grounding"` key from `factors` — verifies a real conditional, not a mock echo. | none |
| TestConfidenceScorer::test_factors_recorded | keep | Complementary real branch: all three factor keys present when `grounding_ratio` is supplied. | none |
| TestConfidenceScorer::test_single_chunk_limits_high_confidence | **rewrite** | The disguising second operand of the assertion (`len([0.95]) >= 2`) was a literal list, not the actual `chunk_scores` argument passed to `score()` — always `1 >= 2` (False), so the assertion silently reduced to `result.level != ConfidenceLevel.HIGH` while reading as if it depended on chunk count. It happened to still be mutation-killable against the `min_chunks_for_high` gate, but the dead literal obscured that and failed the readable-as-spec bar. | Removed the dead literal; asserted the exact expected outcome directly (`result.score >= 0.8` and `result.level == ConfidenceLevel.MEDIUM`), naming the `min_chunks_for_high` gate in a comment. |
| TestConfigModerationEnabled::test_moderation_enabled_default | keep | Real `Settings()` read against a real (patched) environment; asserts the real default. | none |
| TestConfigModerationEnabled::test_moderation_enabled_can_be_disabled | keep | Real env-override branch, real computed setting value. | none |
| TestConfigModerationStatus::test_backend_defaults_to_guardrails | keep | Real default-backend computed property. | none |
| TestConfigModerationStatus::test_status_disabled_when_moderation_off | keep | Real computed `moderation_status` branch: disabled overrides backend regardless of what backend is configured. | none |
| TestConfigModerationStatus::test_status_gateway_guardrails | keep | Real computed property, guardrails branch. | none |
| TestConfigModerationStatus::test_status_openai_api | keep | Real computed property, openai_api branch. | none |

**File totals:** 56 keep / 5 rewrite / 1 delete (62 tests originally; one removed as a redundant structure-only check, five rewritten for assertion-swallowing conditionals, dead-code literals, or tautological `hasattr` checks).

### tests/integration/test_auth_flow.py

Static review only — no test execution (`uv`/`pytest`/`mutmut` withheld per assignment), no test-code edits. This file requires a live backend (`:8000`) plus a live Supabase instance (`:54321`); the module-wide `_require_integration_env`/`_backend_reachable` session fixtures in `tests/integration/conftest.py` auto-skip the whole suite when those aren't reachable, and `--ignore=tests/integration` in `pyproject.toml` `addopts` already excludes this file from the default `pytest tests/` invocation and the daedalus `test` gate. Verdicts below are static judgement per the rubric; Action notes point to live-run follow-up rather than an applied edit.

| Test | Verdict | Rationale | Action |
|---|---|---|---|
| test_ask_unauthenticated | keep | Real live-server round trip through `POST /api/v1/ask` with no `Authorization` header; asserts the real 401 auth-boundary status code, no mocking. | static — see CI-integrity #209 |
| test_history_unauthenticated | keep | Same real-auth-boundary pattern against `GET /api/v1/history`. | static — see CI-integrity #209 |
| test_documents_list_unauthenticated | keep | Same real-auth-boundary pattern against `GET /api/v1/documents`. | static — see CI-integrity #209 |
| test_documents_upload_unauthenticated | keep | Confirms auth middleware runs before body/file validation on `POST /api/v1/documents/upload`; real 401 against a live backend. | static — see CI-integrity #209 |
| test_documents_delete_unauthenticated | keep | Same real-auth-boundary pattern against `DELETE /api/v1/documents/{id}`. | static — see CI-integrity #209 |
| test_history_authenticated_empty | keep | Explicitly clears history first (`DELETE /api/v1/history`) to remove cross-test order dependence, then asserts real `count == 0` and `messages == []` from a live backend response. | static — see CI-integrity #209 |
| test_documents_authenticated_empty | **rewrite** | Name promises an "empty" check but, unlike the sibling `test_history_authenticated_empty`, the body never clears documents first; it asserts only `count >= 0` and `isinstance(documents, list)`, both true for any non-negative list length — near-tautological and does not verify emptiness at all. | → follow-on: tighten `test_documents_authenticated_empty` to assert a known document-count delta instead of `count >= 0` |

**File totals:** 6 keep / 1 rewrite / 0 delete.

### tests/integration/test_document_lifecycle.py

| Test | Verdict | Rationale | Action |
|---|---|---|---|
| test_upload_document | keep | Real multipart upload against a live backend; asserts real `id`/`filename`/`title` presence and `chunks_created > 0` (a genuine pipeline-ran check, not tautological), and seeds `_uploaded_doc_id` for the rest of the chain. | static — see CI-integrity #209 |
| test_list_documents_after_upload | keep | Depends on `test_upload_document` running first via a module-scoped mutable list (guarded by an explicit `assert ..., "Upload test must run first"` rather than failing silently); real assertions that the uploaded doc appears in the live list and `is_indexed is True` (verifies the async indexing pipeline actually completed, not just that upload returned 201). No test-order-randomization plugin (`pytest-randomly`/`xdist`) is configured in `pyproject.toml`, so the intra-file ordering this relies on is stable under the current toolchain, but the coupling is worth noting. | static — see CI-integrity #209 |
| test_ask_with_indexed_document | **rewrite** | Docstring claims "answer references it" and the question ("What time is feeding?") targets content seeded by the fixture doc, but the assertions only check `isinstance(answer, str)` and `len(answer) > 0` — this passes for any non-empty LLM answer, grounded or not, and does not verify RAG retrieval actually used the uploaded document. `AskResponse` (`src/retriever/modules/rag/routes.py`) also returns `chunks_used: list[ChunkWithScore]`, which this test ignores entirely. | → follow-on: assert `chunks_used` references the uploaded `document_id` (or the answer contains an expected substantive token) instead of only non-empty-string |
| test_delete_document | keep | Real delete against a live backend; asserts real 200 + message. Completes the lifecycle chain, cleaning up the doc created by `test_upload_document`. | static — see CI-integrity #209 |
| test_non_admin_cannot_upload | keep | Independent of the upload chain; real 403 enforcement against a live backend when a non-admin token attempts upload. | static — see CI-integrity #209 |
| test_non_admin_cannot_delete | keep | Independent test; real 403 enforcement for delete with a non-admin token against `NIL_UUID` (permission check runs before existence check). | static — see CI-integrity #209 |

**File totals:** 5 keep / 1 rewrite / 0 delete. The middle three tests (`test_list_documents_after_upload`, `test_ask_with_indexed_document`, `test_delete_document`) share state via a module-scoped mutable list and rely on file-definition execution order; this is an intentional, documented lifecycle chain (module docstring: "upload → list → ask → delete") rather than an accidental ordering bug, and failures are surfaced via explicit assert messages rather than silently passing — flagged for awareness, not a rewrite on its own.

### tests/integration/test_health.py

| Test | Verdict | Rationale | Action |
|---|---|---|---|
| test_health_returns_200 | keep | Real `GET /health` against a live backend; asserts the real 200 status. | static — see CI-integrity #209 |
| test_health_response_fields | keep | Real response-body check for `status`, `database`, `pgvector` against a live backend/DB connection (verifies actual infra connectivity, not mocked). The pinned `version == "2.0.0"` assertion is a deliberate drift guard (same pattern as `test_config.py::test_fallback_llm_model_default`) — it will need a one-line update on the next version bump, which is the intended behavior, not a defect. | static — see CI-integrity #209 |
| test_cors_allowed_origin | keep | Real CORS check: a known-allowed origin gets the real `access-control-allow-origin` echoed back by the live backend's CORS middleware. | static — see CI-integrity #209 |
| test_cors_disallowed_origin | keep | Real negative-boundary CORS check: an untrusted origin gets no CORS header — verifies the middleware actually rejects unlisted origins rather than allowing all. | static — see CI-integrity #209 |
| test_openapi_docs_accessible | keep | Real `GET /docs` against a live backend; asserts 200 and a real content substring (`swagger`) confirming the Swagger UI actually rendered, not just that routing resolved. | static — see CI-integrity #209 |

**File totals:** 5 keep / 0 rewrite / 0 delete.

### tests/integration/test_input_validation.py

| Test | Verdict | Rationale | Action |
|---|---|---|---|
| test_ask_empty_question | keep | Real Pydantic validation on a live endpoint; empty string violates `AskRequest.question` (`min_length=1`, `src/retriever/modules/rag/routes.py:33`), correct 422 for the real min-length boundary. | static — see CI-integrity #209 |
| test_ask_missing_question_field | keep | Real required-field validation via a live request with no `question` key; correct 422 for a genuinely required field. | static — see CI-integrity #209 |
| test_ask_question_too_long | keep | Precise boundary test: `"x" * 2001` is exactly one character over the real `max_length=2000` constraint, not an arbitrarily large number — a correctly targeted off-by-one boundary check against a live endpoint. | static — see CI-integrity #209 |

**File totals:** 3 keep / 0 rewrite / 0 delete. Despite the module docstring's section-mapping framing ("empty/missing/oversized questions"), this file covers only length/presence validation — no injection-style payload (SQL, prompt-injection, script/HTML) is exercised anywhere in this file; see the behavior matrix and follow-on issues below.

### tests/integration/test_rag_and_history.py

| Test | Verdict | Rationale | Action |
|---|---|---|---|
| test_ask_returns_valid_response | keep | Clears history first to make the downstream count assertion reliable; real live RAG call, asserts a full real response contract (`answer` str, `chunks_used` list, `confidence_level` in the real enum set, `confidence_score` float, `blocked` bool, `blocked_reason` key present) — a genuine schema/contract check against a live LLM-backed endpoint, not tautological. | static — see CI-integrity #209 |
| test_history_after_ask | keep | Depends on `test_ask_returns_valid_response` running first; module docstring explicitly documents "Tests run in declaration order within this module," so the coupling is intentional and self-disclosed. Asserts real persistence: `count == 2` (exact, not `>=`) and both `user`/`assistant` roles present. | static — see CI-integrity #209 |
| test_clear_history | keep | Real deletion against a live backend; asserts `deleted_count == 2`, an exact match against the prior test's real state rather than a bare success check. | static — see CI-integrity #209 |
| test_history_after_clear | keep | Real post-delete state check: `count == 0` and `messages == []` against a live backend. | static — see CI-integrity #209 |
| test_ask_no_crash_empty_vectorstore | keep | Genuine regression guard for a specific historical failure class (RAG ask 500ing when no chunks are retrievable): asserts real 200, then cleans up its own history rows. Minor naming caveat: the test doesn't itself verify or force the vectorstore to be empty (that state depends on whatever ran earlier in the same live environment) — the "empty_vectorstore" name asserts a precondition it doesn't control, though the 200-not-500 check it does make is valid regardless of actual doc count. | static — see CI-integrity #209 |

**File totals:** 5 keep / 0 rewrite / 0 delete.

#### Integration coverage notes

**What the five integration suites cover:**
- **Auth flow** (`test_auth_flow.py`): every mutating/reading endpoint (`ask`, `history`, `documents` list/upload/delete) rejects unauthenticated requests with a real 401 from the live auth middleware; authenticated-empty-state checks for history.
- **Document lifecycle** (`test_document_lifecycle.py`): full upload → list → ask → delete chain against a live backend + live RAG pipeline, including admin-only enforcement (403 for non-admin upload/delete) and real indexing-completion verification (`is_indexed is True`).
- **Health** (`test_health.py`): live DB/pgvector connectivity, CORS allow/deny boundary, and OpenAPI docs availability.
- **Input validation** (`test_input_validation.py`): precise min/max-length and required-field boundaries on `AskRequest.question` (422s), verified against the real Pydantic constraint (`min_length=1, max_length=2000` in `src/retriever/modules/rag/routes.py`).
- **RAG + history** (`test_rag_and_history.py`): full ask-response contract shape, conversation-history persistence and clearing, and a no-crash guard when RAG has nothing to retrieve.

**Gaps:**
- **No injection coverage.** Despite `test_input_validation.py`'s docstring gesturing at "input validation" broadly, none of the five files send an actual injection-shaped payload (SQL metacharacters, prompt-injection strings like "ignore previous instructions," script/HTML tags) through `/api/v1/ask` or the document upload path. All three `test_input_validation.py` tests are length/presence checks only.
- **No malicious/oversized file upload coverage.** `test_document_lifecycle.py` uploads only a well-formed `test-doc.md`; there's no live test for a wrong-content-type file, a corrupt file, or an over-limit upload size.
- **No rate-limiting / concurrency coverage** across any of the five files.
- **`test_ask_with_indexed_document`** (flagged above) is the one place a grounding/relevance check on RAG output would matter most and currently doesn't happen.
- All five files are excluded from the default `pytest tests/` run (`pyproject.toml` `addopts` carries `--ignore=tests/integration`) and from the daedalus `test` gate in `.daedalus/config.json`; they only execute when a developer runs them explicitly against a live backend + local Supabase, so none of the behaviors above are checked in CI today except whatever `ci_delegated` covers separately.

## Mock-of-own-code inventory

Every mocking target flagged across the per-file ledgers, consolidated into one table. "Justified boundary" / "acceptable" mean the mock stands in for a real external system (network, paid API, database, heavy ML dependency) rather than hiding untested logic in retriever's own code; "not flagged" means the mocked symbol is third-party, not retriever-owned; "not applicable" means the mock target is inert (never actually exercised by the code path under test).

| Mocked symbol | Test file | Verdict | Rationale |
|---|---|---|---|
| `AsyncOpenAI` client (`_make_client()` helper, `MagicMock(spec=AsyncOpenAI)`) | tests/test_llm_provider.py | justified boundary | External third-party SDK client for the LLM gateway network call. Not retriever-owned code. `OpenAICompatProvider` itself (retry/circuit-breaker/error-translation logic) always executes for real. |
| *(none — no mocking used)* | tests/test_loader.py | n/a | File contains no mocking at all; `validate_file` and its constants are exercised directly. |
| `retriever.config.Settings` (via `_make_settings` MagicMock) | tests/test_gateway_client.py | justified boundary | Isolates a pure settings→client mapping function from full `Settings` construction (which needs env vars/secrets); assertions land on the real `AsyncOpenAI` output object's attributes, not on mock call spies. |
| `retriever.config.get_settings` (patched to return a MagicMock) | tests/test_health.py (`test_health_reports_configured_moderation_mode`) | justified boundary | Injects one field (`moderation_status`) without needing a full real `Settings` environment; the assertion checks the real HTTP response body, not the mock. |
| `retriever.main._get_factory` (patched) | tests/test_health.py (4 of 5 tests) | justified boundary | `_get_factory` is the accessor onto the DB session factory; patching it simulates DB up/degraded/unreachable states that would otherwise require a live Postgres instance in a unit test — the unowned boundary is the database, not `_get_factory`'s own logic (it has none beyond returning the factory). |
| `retriever.infrastructure.vectordb.protocol.VectorStore` (AsyncMock) | tests/test_hybrid_retriever.py | justified boundary | `VectorStore` is an interface over pgvector; no implementation logic lives on the protocol itself, so mocking it stands in for the real external vector database. |
| `retriever.infrastructure.llm.protocol.LLMProvider` (hand-written `MockLLMProvider` fake) | tests/test_llm_fallback.py | justified boundary | Interface over a real LLM API call (network + paid API); the fake implements realistic conditional failure behavior rather than being a bare call-recorder. |
| `retriever.models.message.Message` (via `MagicMock(spec=Message)` in `_make_message`) | tests/test_message_repos.py | justified boundary | Stands in for rows a live Postgres query would return; `Message` itself carries no logic to bypass (plain SQLAlchemy declarative model), so the mock isn't hiding untested own-code behavior. |
| `FastAPIInstrumentor.instrument_app` (patched) | tests/test_observability.py (`test_configure_tracing_instruments_fastapi`) | not flagged | Third-party OTel instrumentation entry point (unowned boundary), not retriever-owned code. |
| `sys.modules["langfuse"]` / `Langfuse` class (patched) | tests/test_observability.py (4 tests: disabled/no-creds, disabled/partial-creds, initialises-with-credentials, flush-swallows-errors) | not flagged | `langfuse` is an optional third-party SDK imported lazily; patching the import boundary is the standard pattern for an optional-dependency guard, not a mock of retriever's own `configure_langfuse`/`flush_langfuse` logic (those functions run for real in every case). |
| *(none — no mocking used)* | tests/test_models.py | n/a | Neither the unit assertions nor the `@pytest.mark.integration` DB tests mock anything. |
| *(none — no mocking used)* | tests/test_openapi_spec.py | n/a | No mocking of any kind. |
| *(none — no mocking used)* | tests/test_prompts.py | n/a | No mocking used. |
| `retriever.modules.rag.dependencies._get_factory` (owned) | tests/test_rag_dependencies.py | justified boundary | Stands in for a real DB session-factory/engine construction; avoids opening a live Postgres connection in unit tests, so it guards a network/DB boundary even though the function itself is owned code. |
| `retriever.modules.rag.dependencies.get_settings` (owned) | tests/test_rag_dependencies.py | justified boundary | DI seam for injecting deterministic settings values; the module reads global config via a function call rather than an injected parameter, so mocking it is the only way to vary settings per test without touching real env/files. |
| `AsyncMock(spec=RAGService)` (`get_rag_service` DI override) | tests/test_rag_routes.py (all 9 tests) | justified boundary | `RAGService.ask` drives live LLM calls and vector-DB retrieval; mocking it at the route's DI seam isolates request-validation/auth/persistence-orchestration logic from that expensive, non-deterministic dependency. Every test that uses it asserts on the route's own mapping or call-arg behavior, not on the mock echoing its own configured return value. |
| `AsyncMock(spec=MessageRepository)` (`get_message_repository` DI override) | tests/test_rag_routes.py (all 9 tests), tests/test_message_routes.py (all 8 tests) | justified boundary | `MessageRepository` wraps a live async SQLAlchemy/Postgres session; mocking it at the route layer avoids requiring a live DB for route-level unit tests. Assertions check specific call kwargs (`user_id`, `role`, `content`) or response-body values derived from the mock's data, not merely that a method was called. |
| `MagicMock(spec=Message)` (`_make_mock_message`/`_make_message` helpers) | tests/test_rag_routes.py, tests/test_message_routes.py | justified boundary | Used purely as a lightweight data holder (sets `id`/`user_id`/`tenant_id`/`role`/`content`/`created_at` attributes) to avoid a real DB insert when constructing fixture rows; no `Message` *behavior* is mocked or asserted against. |
| `require_auth` overridden with `lambda: TEST_USER` | tests/test_rag_routes.py, tests/test_message_routes.py (all "authenticated" tests) | justified boundary | Bypasses the real auth dependency only in tests whose subject is business logic, not auth. Auth itself is separately and directly covered by `test_ask_requires_auth`, `test_get_history_requires_auth`, and `test_clear_history_requires_auth`, which leave `require_auth` un-overridden and assert the real 401/403 outcome. |
| `LLMProvider` (`mock_llm`) | tests/test_rag_service.py | acceptable | Protocol boundary in front of a real network/paid LLM-gateway call; mocking it in an orchestrator unit test is the standard isolation seam, not a self-mock. |
| `EmbeddingProvider` (`mock_embeddings`) | tests/test_rag_service.py | acceptable | Same pattern; real implementation calls a network/paid embedding API. |
| `VectorStore` (`mock_vector_store`) | tests/test_rag_service.py | acceptable | Real implementation (`PgVectorStore`, audited in `test_vectordb.py`) is a live Postgres/pgvector boundary. |
| `SemanticCache` (`mock_cache`) | tests/test_rag_service.py | acceptable | Real implementation is a live Postgres boundary (audited separately in `test_cache.py`). |
| `DocumentProcessor` (`mock_processor`) | tests/test_rag_service.py | acceptable | Real implementation wraps Docling, a heavy local ML dependency; avoiding model load per test is the same accepted pattern used in `test_docling_processor.py`. |
| `HybridRetriever` (`mock_hybrid`) | tests/test_rag_service.py | acceptable | Retriever-owned orchestration code, but its own RRF-fusion logic is independently unit-tested in `test_hybrid_retriever.py`; mocking it here isolates `RAGService`'s branch-selection logic from a collaborator that already has direct coverage. |
| `SafetyService` (`mock_safety`) | tests/test_rag_service.py | acceptable | Retriever-owned, but its constituent algorithms (injection detection, hallucination detection) are independently unit-tested in `test_safety.py`; `check_input` also fronts a real moderation API call for the non-NoOp provider. |
| `ConfidenceScorer` (`mock_confidence_scorer`) | tests/test_rag_service.py | acceptable, no external boundary | Pure local algorithm with no network/clock/paid-API boundary — the one collaborator in this file mocked purely for orchestration isolation rather than boundary-guarding. Flagged acceptable only because its real scoring logic has full independent coverage in `test_safety.py::TestConfidenceScorer` (7 tests); if that coverage were ever removed, this mock would leave `RAGService`'s confidence-driven branches (caching, `needs_review`) untested against real scoring math. |
| `AsyncSession`/`session_factory` (`mock_session_factory`) | tests/test_rag_service.py | not applicable | `RAGService` stores `session_factory` but never calls it in `ask`/`index_document`/`clear_cache` (verified by reading `service.py`) — the fixture is inert, not a meaningful mock of behavior. |
| `AsyncOpenAI` client (`_make_moderator()` helper, `MagicMock(spec=AsyncOpenAI)`) | tests/test_safety.py | justified boundary | External third-party SDK client for the LLM-gateway moderation call. Not retriever-owned code. `OpenAIModerator.check()` itself (parsing, category conversion, fail-open error translation) always executes for real. |
| `retriever.infrastructure.safety.moderation.logger` (patched) | tests/test_safety.py | justified boundary | Patches the module's structlog logger binding to observe which structured-log *event name* fires on two distinct error branches. The real `check()` code path executes fully; only the otherwise-invisible logging side effect is captured. |
| `ModerationProvider` collaborator (`mock_moderator = MagicMock(); mock_moderator.check = AsyncMock(...)`) | tests/test_safety.py | justified boundary | `SafetyService` (unit under test) is real and executes its own `check_input` logic for real; only its injected `ModerationProvider` dependency is swapped for a test double that returns a flagged result, driving a branch the real default `NoOpModerator` can't reach. |
| `Settings` (`MagicMock()`) in `test_routes_through_injected_gateway_client` | tests/test_safety.py | justified boundary | Stands in for input configuration data (base URL, token, header name) fed into the real `build_gateway_client()` and real `OpenAIModerator` constructor — not a mock of any safety logic under test. |

No mock in `test_safety.py` stands in for `PromptInjectionDetector`, `HallucinationDetector`, `ConfidenceScorer`, `SafetyCheckResult`/`ModerationResult` construction logic, or `SafetyService`'s own orchestration code — all of that executes for real across every test in the file. The five integration suites use no mocking at all (they run against a live backend), so they contribute no rows to this table.

## Pass 2 — Mutation baseline

A scoped mutation-testing pass was planned against the four highest-risk target modules, each run against its own scoped test file to keep per-mutant runtime small:

| Module | Source | Killed | Survived | Total | Score | Notes |
|---|---|---|---|---|---|---|
| Auth dependencies | `src/retriever/modules/auth/dependencies.py` | — | — | — | — | Blocked (see below) |
| Safety service | `src/retriever/infrastructure/safety/service.py` | — | — | — | — | Blocked (see below) |
| RAG service | `src/retriever/modules/rag/service.py` | — | — | — | — | Blocked (see below) |
| Document service | `src/retriever/modules/documents/services.py` | — | — | — | — | Blocked (see below) |

**BLOCKER:** mutmut 3.x could not produce numeric scores in this environment: its stats-collection baseline run fails with `BadTestExecutionCommandsException` because the tool executes the copied `mutants/` source tree while `uv` installs `retriever` as an editable `src/`-layout package pointing at the real `src/`, so the mutated copies are never imported. Stripping the project's pytest coverage `addopts` did not resolve it. Reproducible config and the exact failure are recorded here. Producing the numeric baseline is handed to child issue #210 (institutionalize mutation-score tracking), which owns standing up a working mutation harness for the monorepo.

**Reproduction:**

`setup.cfg` (one section per target module; run separately per module to keep per-mutant runtime small):

```ini
[mutmut]
paths_to_mutate=src/retriever/modules/auth/dependencies.py
```

```ini
[mutmut]
paths_to_mutate=src/retriever/infrastructure/safety/service.py
```

```ini
[mutmut]
paths_to_mutate=src/retriever/modules/rag/service.py
```

```ini
[mutmut]
paths_to_mutate=src/retriever/modules/documents/services.py
```

Run command (from `services/retriever/`):

```bash
uv run --with mutmut mutmut run
```

This reproducibly hits `BadTestExecutionCommandsException` during mutmut's stats-collection baseline run, before any mutant is generated: mutmut executes tests against the copied `mutants/` tree it creates, but the `uv`-managed venv has `retriever` installed editable (`src/`-layout, `pip install -e .` equivalent) pointing at the real `src/retriever/`, so Python imports the unmutated real package instead of the mutated copy regardless of which directory mutmut invokes pytest from.

## Pass 3 — Behavior matrix

| Critical behavior | Unit | Integration | Verdict/Gap |
|---|---|---|---|
| Route auth coverage | `test_auth.py` (8 tests: JWT decode/expiry/signature, `require_auth`, `require_admin`); `test_document_routes.py` (admin/auth gates on upload/list/delete); `test_rag_routes.py::test_ask_requires_auth`; `test_message_routes.py::test_get_history_requires_auth`/`test_clear_history_requires_auth`; `test_subscription_guard.py` (8 tests, claim-based subscription gate across documents/messages/rag routers) | `test_auth_flow.py` (7 tests: real 401 against a live backend for every mutating/reading endpoint) | Covered — real auth-boundary assertions (401/403) at both unit and live-integration tiers. |
| Input validation & prompt-injection surfaces | `test_safety.py::TestPromptInjectionDetector` (10 tests: instruction-override, role-change, extraction, jailbreak, debug-mode, case-insensitivity, custom patterns, partial matches — all real regex matching); `test_rag_routes.py` (422s for empty/too-long/missing `question`); `test_loader.py` (file-type/size validation) | `test_input_validation.py` (3 tests: length/presence 422s only) | GAP — the injection *detector* itself is thoroughly unit-tested, but no integration test sends an actual injection-shaped payload (SQL metacharacters, "ignore previous instructions" strings, script/HTML tags) through the live `/api/v1/ask` or document-upload endpoints. Rate-limiting and concurrency are also untested anywhere in the suite. → follow-on: add integration tests posting injection-shaped payloads to `/ask` and `/documents/upload`; add rate-limit/concurrency coverage. |
| Document lifecycle integrity | `test_document_service.py` (15 tests, including compensating-transaction cleanup on indexing failure); `test_document_routes.py` (12 tests); `test_docling_processor.py` (22 tests, format-aware processing) | `test_document_lifecycle.py` (6 tests: full upload → list → ask → delete chain, admin-only enforcement, real `is_indexed` verification) | GAP (partial) — CRUD lifecycle and admin enforcement are solidly covered; but no live test exercises a malicious/oversized/malformed upload, and `test_ask_with_indexed_document` doesn't verify the RAG answer actually grounds in the uploaded document. → follow-on: add oversized/malformed-upload integration coverage; strengthen `test_ask_with_indexed_document` to assert on `chunks_used`. |
| Embedding/vector correctness guards | `test_embeddings.py` (16 tests: OpenAI embedding provider parsing, circuit breaker, batch-order preservation); `test_hybrid_retriever.py` (10 tests: real RRF fusion math, weight bias, dedup, top-k slicing); `test_vectordb.py` (3 tests: real upsert/search/delete against pgvector, DB-skip-safe) | none directly (RAG contract checked in `test_rag_and_history.py` but not vector-search internals) | GAP (partial) — RRF fusion and embedding-provider logic are strongly covered; but `test_vectordb.py`'s `min_score` WHERE-clause filter has no real coverage because the fixture's embeddings are collinear (constant-vector shape), so the actual threshold branch is never exercised. → follow-on: add a non-constant/orthogonal embedding fixture to `test_vectordb.py` to exercise the `min_score` filter. |
| LLM fallback behavior | `test_llm_fallback.py` (5 tests: primary success, fallback-on-failure with exact call sequence, both-fail raises, model-override pass-through, `complete_with_history` fallback); `test_llm_provider.py` (circuit breaker, `tenacity` retry, real error-translation branches — 19 tests) | none (no live-gateway fallback drill) | Covered (unit) — fallback branching, retry, and circuit-breaker state machine are exercised against real logic with only the network client mocked; no integration gap flagged in the source material. |
| Gateway error handling | `test_error_handling.py` (4 tests: 500 CORS-safe handler, generic non-leaking body, mid-stream re-raise, CORS preflight); `test_gateway_client.py` (6 tests: base-URL/auth-header wiring); `test_llm_provider.py`/`test_safety.py` (real timeout/rate-limit/connection-error → app-exception translation branches); `test_health.py` (unit, degraded-state branches) | `test_health.py` (integration: live CORS allow/deny, live DB/pgvector connectivity) | Covered — real error-translation and CORS-safety behavior verified at both tiers. |

## Follow-on issues

- Mutation-score baseline: hand off to #210 (institutionalize mutation-score tracking) — the mutmut harness itself is blocked in this environment (see Pass 2); #210 owns standing up a working mutation harness for the monorepo.
- Injection-payload coverage: add integration tests posting SQL/prompt-injection/HTML-shaped payloads through `/api/v1/ask` and `/documents/upload` and assert the live safety layer blocks them.
- Oversized/malformed upload coverage: add a live integration test for a wrong-content-type, corrupt, or over-size-limit file upload against `/documents/upload`.
- Rate-limit/concurrency coverage: add integration coverage exercising rate-limiting and concurrent-request handling; none of the five integration suites test either today.
- Tighten `test_documents_authenticated_empty` (`tests/integration/test_auth_flow.py`): assert a known document-count delta instead of `count >= 0`.
- Strengthen `test_ask_with_indexed_document` (`tests/integration/test_document_lifecycle.py`): assert `chunks_used` references the uploaded `document_id` (or the answer contains an expected substantive token) instead of only checking a non-empty string.
- Exercise the `min_score` filter branch in `PgVectorStore` (`tests/test_vectordb.py`): add a non-constant/orthogonal embedding fixture so the WHERE-clause threshold is actually tested; the current constant-vector `_embedding()` helper makes every non-trivial embedding collinear.
- Cover the `needs_review=True` cache-skip branch in `RAGService.ask` (`tests/test_rag_service.py`): every fixture's `mock_confidence_scorer` is hardcoded to `needs_review=False`; add a case that returns `needs_review=True` and assert `cache.set` is not awaited.
