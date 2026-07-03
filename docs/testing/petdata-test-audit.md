# petdata test-effectiveness audit

- Status: complete
- Date: 2026-07-03
- Issue: #206 (child of epic #205)
- Module: services/petdata

## Summary

All 175 petdata test functions were audited under the epic #205 three-pass method (static smell, mutation counterfactual, portfolio matrix). The suite is high quality: tests are behavioral, assertion-rich, and readable as specifications. Verdicts: **173 keep, 1 rewrite, 1 delete**. The dominant weakness is not bad tests but incomplete field-level coverage: the mapper and parser tests assert a happy-path subset of fields, so many field and branch mutants survive. Those become follow-on coverage issues rather than rewrites of existing tests.

## Pass 2: mutation baseline

Measured with mutmut 3 on Python 3.14, unit tests only (`-m "not integration"`), whole-package `source_paths`. Codes: killed (tests failed on mutant), survived (tests passed on mutant), no-tests (mutant line uncovered).

| Module | Killed | Survived | No-tests | Kill rate |
|---|---|---|---|---|
| models/mappers.py | 144 | 161 | 58 | 47% |
| modules/api/parser.py | 105 | 198 | 0 | 35% |
| modules/api/auth.py | 30 | 11 | 0 | 73% |
| modules/auth/dependencies.py | 0 mutants generated | - | - | n/a |
| modules/db/repository.py | integration-gated (needs Postgres:5434), not run | - | - | n/a |

Surviving-mutant hotspots (functions with the most survivors):

- `parser.parse_animal_response` (94), `parser.parse_volunteer_note_response` (63), `parser.parse_walk_record_response` (41)
- `mappers.animal_from_row` (26), `mappers.volunteer_note_from_row` (20), `mappers.behavior_profile_from_row` (19), `mappers.volunteer_note_to_row` (19), `mappers.behavior_profile_to_row` (17), `mappers.animal_to_row` (16)

Interpretation: parser and mapper tests exercise the code but assert a subset of fields, so per-field and per-branch mutants survive. `modules/api/auth.py` at 73% is the strongest measured path. `repository.py` is exercised only by Postgres-backed integration tests, so its mutation score is deferred to CI (epic child #209). `auth/dependencies.py` produced no mutants (thin FastAPI dependency wiring).

Reproduce: from `services/petdata`, add a temporary `[tool.mutmut]` block (`source_paths = ["src/petdata/"]`, `pytest_add_cli_args_test_selection = ["tests/unit/"]`), then `uv run --with mutmut mutmut run "petdata.models.mappers.*" "petdata.modules.api.parser.*" "petdata.modules.api.auth.*"`. Automating this is epic child #210; no mutmut dependency is committed here.

## Pass 3: critical-behavior matrix

| Behavior | Covered | Test(s) / level | Gap resolution |
|---|---|---|---|
| Auth required on data routes | yes | test_auth.py::test_animals_route_requires_auth (401), unit | - |
| Subscription guard on data routes | yes | test_auth.py::test_animals_route_requires_subscription (403), unit | - |
| Admin authz | yes | test_auth.py::test_require_admin_non_admin/is_admin, unit | - |
| JWT signature/expiry validation | yes | test_auth.py::test_decode_invalid_signature/expired, unit | - |
| Health endpoint stays open | yes | test_auth.py::test_health_stays_open, unit | - |
| Header/cookie injection defense (CRLF, null byte) | yes | test_auth.py (api)::test_cookies_with_newline/carriage_return/null_byte, unit | - |
| Ingestion input validation (bad shape, range) | partial | test_parser.py error cases, unit | G1: assert all mapped fields per record |
| Mapper round-trip integrity (all fields, 7 entities) | partial | test_mappers.py round-trips, unit | G2: full-field round-trips for all 7 entities |
| Multi-tenant data isolation (tenant_id on every table) | yes | test_tables.py::test_every_table_is_tenant_owned/has_tenant_id, unit | - |
| Cascade delete of animal children | yes | test_tables.py FK + test_repository.py::test_delete_animal_cascades_to_children, integration | - |
| Alembic migration safety | yes (static) | test_alembic.py, integration (CI-only) | verified in CI (#209) |
| Repository CRUD correctness | yes (static) | test_repository.py, integration (CI-only) | mutation score deferred to #209 |
| SMS client retry/backoff/rate-limit | yes | test_client.py, mocked-HTTP | - |
| OpenAPI spec freshness | yes | test_openapi_spec.py, unit | - |

Named gaps become follow-on coverage issues against epic #205: G1 parser field-level assertions (raise the 35% kill rate); G2 mapper full-field round-trips for all seven entities (raise the 47% kill rate); G3 repository mutation score under CI Postgres (folds into #209); G4 rewrite the config-restatement pool-defaults test.

## Pass 1: verdict ledger

All 175 test functions. Integration tests receive static verdicts (they require live Postgres and run in CI, not locally).

| Test | Verdict | Rationale | Action |
|---|---|---|---|
| `tests/integration/api/test_client.py::test_retry_on_429_with_backoff` | keep | Retry/backoff/rate-limit behavior with mocked HTTP transport (justified boundary mock). | keep (static: HTTP mocked) |
| `tests/integration/api/test_client.py::test_retry_exhausted_raises_rate_limit_error` | keep | Retry/backoff/rate-limit behavior with mocked HTTP transport (justified boundary mock). | keep (static: HTTP mocked) |
| `tests/integration/api/test_client.py::test_retry_on_500_with_backoff` | keep | Retry/backoff/rate-limit behavior with mocked HTTP transport (justified boundary mock). | keep (static: HTTP mocked) |
| `tests/integration/api/test_client.py::test_retry_exhausted_raises_server_error` | keep | Retry/backoff/rate-limit behavior with mocked HTTP transport (justified boundary mock). | keep (static: HTTP mocked) |
| `tests/integration/api/test_client.py::test_server_error_includes_status_and_body` | keep | Retry/backoff/rate-limit behavior with mocked HTTP transport (justified boundary mock). | keep (static: HTTP mocked) |
| `tests/integration/api/test_client.py::test_rate_limiting_enforces_delay` | keep | Retry/backoff/rate-limit behavior with mocked HTTP transport (justified boundary mock). | keep (static: HTTP mocked) |
| `tests/integration/api/test_client.py::test_rate_limiting_handles_elapsed_greater_than_delay` | keep | Retry/backoff/rate-limit behavior with mocked HTTP transport (justified boundary mock). | keep (static: HTTP mocked) |
| `tests/integration/api/test_client.py::test_context_manager_closes_client` | keep | Retry/backoff/rate-limit behavior with mocked HTTP transport (justified boundary mock). | keep (static: HTTP mocked) |
| `tests/integration/api/test_client.py::test_explicit_close_works` | keep | Retry/backoff/rate-limit behavior with mocked HTTP transport (justified boundary mock). | keep (static: HTTP mocked) |
| `tests/integration/api/test_client.py::test_fetch_animals_includes_query_params` | keep | Retry/backoff/rate-limit behavior with mocked HTTP transport (justified boundary mock). | keep (static: HTTP mocked) |
| `tests/integration/api/test_client.py::test_fetch_volunteer_notes_uses_correct_table` | keep | Retry/backoff/rate-limit behavior with mocked HTTP transport (justified boundary mock). | keep (static: HTTP mocked) |
| `tests/integration/api/test_client.py::test_fetch_walk_records_uses_correct_table` | keep | Retry/backoff/rate-limit behavior with mocked HTTP transport (justified boundary mock). | keep (static: HTTP mocked) |
| `tests/integration/api/test_client.py::test_authentication_headers_injected` | keep | Retry/backoff/rate-limit behavior with mocked HTTP transport (justified boundary mock). | keep (static: HTTP mocked) |
| `tests/integration/api/test_client.py::test_invalid_json_response_raises_error` | keep | Retry/backoff/rate-limit behavior with mocked HTTP transport (justified boundary mock). | keep (static: HTTP mocked) |
| `tests/integration/api/test_client.py::test_retry_after_header_respected` | keep | Retry/backoff/rate-limit behavior with mocked HTTP transport (justified boundary mock). | keep (static: HTTP mocked) |
| `tests/integration/db/test_alembic.py::test_alembic_upgrade_then_downgrade` | keep | Alembic migration upgrade/downgrade safety. | keep (static: needs Postgres; runs in CI) |
| `tests/integration/db/test_repository.py::test_insert_and_get_animal_round_trips_fields` | keep | Real-Postgres CRUD, ordering, pagination, cascade-delete round-trips. | keep (static: needs Postgres; runs in CI) |
| `tests/integration/db/test_repository.py::test_get_animal_missing_returns_none` | keep | Real-Postgres CRUD, ordering, pagination, cascade-delete round-trips. | keep (static: needs Postgres; runs in CI) |
| `tests/integration/db/test_repository.py::test_update_animal_applies_partial_change` | keep | Real-Postgres CRUD, ordering, pagination, cascade-delete round-trips. | keep (static: needs Postgres; runs in CI) |
| `tests/integration/db/test_repository.py::test_list_animals_orders_by_name_with_pagination` | keep | Real-Postgres CRUD, ordering, pagination, cascade-delete round-trips. | keep (static: needs Postgres; runs in CI) |
| `tests/integration/db/test_repository.py::test_delete_animal_cascades_to_children` | keep | Real-Postgres CRUD, ordering, pagination, cascade-delete round-trips. | keep (static: needs Postgres; runs in CI) |
| `tests/integration/db/test_repository.py::test_insert_volunteer_note_returns_id_and_fetches` | keep | Real-Postgres CRUD, ordering, pagination, cascade-delete round-trips. | keep (static: needs Postgres; runs in CI) |
| `tests/integration/db/test_repository.py::test_get_notes_for_animal_orders_recent_first` | keep | Real-Postgres CRUD, ordering, pagination, cascade-delete round-trips. | keep (static: needs Postgres; runs in CI) |
| `tests/integration/db/test_repository.py::test_update_volunteer_note_without_id_raises` | keep | Real-Postgres CRUD, ordering, pagination, cascade-delete round-trips. | keep (static: needs Postgres; runs in CI) |
| `tests/integration/db/test_repository.py::test_update_and_delete_volunteer_notes` | keep | Real-Postgres CRUD, ordering, pagination, cascade-delete round-trips. | keep (static: needs Postgres; runs in CI) |
| `tests/integration/db/test_repository.py::test_upsert_behavior_profile_inserts_then_updates_same_row` | keep | Real-Postgres CRUD, ordering, pagination, cascade-delete round-trips. | keep (static: needs Postgres; runs in CI) |
| `tests/integration/db/test_repository.py::test_get_behavior_profile_by_id_and_delete` | keep | Real-Postgres CRUD, ordering, pagination, cascade-delete round-trips. | keep (static: needs Postgres; runs in CI) |
| `tests/integration/db/test_repository.py::test_staff_assessment_crud_and_tags` | keep | Real-Postgres CRUD, ordering, pagination, cascade-delete round-trips. | keep (static: needs Postgres; runs in CI) |
| `tests/integration/db/test_repository.py::test_walk_record_crud_and_ordering` | keep | Real-Postgres CRUD, ordering, pagination, cascade-delete round-trips. | keep (static: needs Postgres; runs in CI) |
| `tests/integration/db/test_repository.py::test_animal_image_crud_and_ordering` | keep | Real-Postgres CRUD, ordering, pagination, cascade-delete round-trips. | keep (static: needs Postgres; runs in CI) |
| `tests/integration/db/test_repository.py::test_sync_log_lifecycle_and_latest` | keep | Real-Postgres CRUD, ordering, pagination, cascade-delete round-trips. | keep (static: needs Postgres; runs in CI) |
| `tests/integration/web/test_llms_txt.py::test_llms_txt_returns_200` | keep | /llms.txt endpoint contract. | keep (static) |
| `tests/integration/web/test_llms_txt.py::test_llms_txt_reflects_openapi_surface` | keep | /llms.txt endpoint contract. | keep (static) |
| `tests/integration/web/test_llms_txt.py::test_llms_txt_ignores_auth_header` | keep | /llms.txt endpoint contract. | keep (static) |
| `tests/test_openapi_spec.py::test_committed_openapi_spec_is_fresh` | keep | Regression guard: committed openapi.json stays in sync with the live app. | keep |
| `tests/unit/api/test_auth.py::test_missing_cookies_raises_error` | keep | Cookie-format validation, behavioral, well-named. | keep |
| `tests/unit/api/test_auth.py::test_empty_cookies_raises_error` | delete | Exact duplicate of test_missing_cookies_raises_error (same input cookies="", same match); adds no counterfactual. | deleted here |
| `tests/unit/api/test_auth.py::test_whitespace_only_cookies_raises_error` | keep | Cookie-format validation, behavioral, well-named. | keep |
| `tests/unit/api/test_auth.py::test_cookies_with_newline_raises_error` | keep | Cookie-format validation, behavioral, well-named. | keep |
| `tests/unit/api/test_auth.py::test_cookies_with_carriage_return_raises_error` | keep | Cookie-format validation, behavioral, well-named. | keep |
| `tests/unit/api/test_auth.py::test_cookies_with_null_byte_raises_error` | keep | Cookie-format validation, behavioral, well-named. | keep |
| `tests/unit/api/test_auth.py::test_invalid_format_no_equals_raises_error` | keep | Cookie-format validation, behavioral, well-named. | keep |
| `tests/unit/api/test_auth.py::test_invalid_format_missing_key_raises_error` | keep | Cookie-format validation, behavioral, well-named. | keep |
| `tests/unit/api/test_auth.py::test_invalid_format_missing_value_raises_error` | keep | Cookie-format validation, behavioral, well-named. | keep |
| `tests/unit/api/test_auth.py::test_valid_single_cookie_passes` | keep | Cookie-format validation, behavioral, well-named. | keep |
| `tests/unit/api/test_auth.py::test_valid_multiple_cookies_passes` | keep | Cookie-format validation, behavioral, well-named. | keep |
| `tests/unit/api/test_auth.py::test_valid_cookies_with_hyphens_passes` | keep | Cookie-format validation, behavioral, well-named. | keep |
| `tests/unit/api/test_auth.py::test_valid_cookies_with_underscores_passes` | keep | Cookie-format validation, behavioral, well-named. | keep |
| `tests/unit/api/test_auth.py::test_get_headers_includes_cookie` | keep | Cookie-format validation, behavioral, well-named. | keep |
| `tests/unit/api/test_auth.py::test_get_headers_includes_accept` | keep | Cookie-format validation, behavioral, well-named. | keep |
| `tests/unit/api/test_auth.py::test_get_headers_preserves_cookie_value` | keep | Cookie-format validation, behavioral, well-named. | keep |
| `tests/unit/api/test_auth.py::test_is_valid_true_for_non_empty_cookies` | keep | Cookie-format validation, behavioral, well-named. | keep |
| `tests/unit/api/test_auth.py::test_is_valid_only_checks_format` | keep | Cookie-format validation, behavioral, well-named. | keep |
| `tests/unit/api/test_exceptions.py::test_all_exceptions_inherit_from_api_error` | keep | Near-tautological structure test, but the inheritance contract is what except-clauses rely on; low value, retained. | keep (low) |
| `tests/unit/api/test_exceptions.py::test_api_error_inherits_from_exception` | keep | Near-tautological, but guards catchability of APIError; low value, retained. | keep (low) |
| `tests/unit/api/test_exceptions.py::test_exception_chains_cause` | keep | Exception attribute/chaining behavior used by error handling. | keep |
| `tests/unit/api/test_exceptions.py::test_server_error_with_status_code` | keep | Exception attribute/chaining behavior used by error handling. | keep |
| `tests/unit/api/test_exceptions.py::test_server_error_with_response_body` | keep | Exception attribute/chaining behavior used by error handling. | keep |
| `tests/unit/api/test_exceptions.py::test_server_error_with_all_attributes` | keep | Exception attribute/chaining behavior used by error handling. | keep |
| `tests/unit/api/test_exceptions.py::test_server_error_without_optional_attributes` | keep | Exception attribute/chaining behavior used by error handling. | keep |
| `tests/unit/api/test_parser.py::test_valid_animal_response_returns_models` | keep | Behavioral parser test: asserts parsed values and error cases with match=. | keep; field-coverage gap -> follow-on G1 |
| `tests/unit/api/test_parser.py::test_empty_records_list_returns_empty_list` | keep | Behavioral parser test: asserts parsed values and error cases with match=. | keep; field-coverage gap -> follow-on G1 |
| `tests/unit/api/test_parser.py::test_missing_records_key_returns_empty_list` | keep | Behavioral parser test: asserts parsed values and error cases with match=. | keep; field-coverage gap -> follow-on G1 |
| `tests/unit/api/test_parser.py::test_records_not_list_raises_validation_error` | keep | Behavioral parser test: asserts parsed values and error cases with match=. | keep; field-coverage gap -> follow-on G1 |
| `tests/unit/api/test_parser.py::test_pydantic_validation_error_wrapped` | keep | Behavioral parser test: asserts parsed values and error cases with match=. | keep; field-coverage gap -> follow-on G1 |
| `tests/unit/api/test_parser.py::test_partial_data_with_optional_fields` | keep | Behavioral parser test: asserts parsed values and error cases with match=. | keep; field-coverage gap -> follow-on G1 |
| `tests/unit/api/test_parser.py::test_species_field_mapped` | keep | Behavioral parser test: asserts parsed values and error cases with match=. | keep; field-coverage gap -> follow-on G1 |
| `tests/unit/api/test_parser.py::test_species_absent_defaults_to_none` | keep | Behavioral parser test: asserts parsed values and error cases with match=. | keep; field-coverage gap -> follow-on G1 |
| `tests/unit/api/test_parser.py::test_multiple_animals_parsed` | keep | Behavioral parser test: asserts parsed values and error cases with match=. | keep; field-coverage gap -> follow-on G1 |
| `tests/unit/api/test_parser.py::test_valid_note_response_returns_models` | keep | Behavioral parser test: asserts parsed values and error cases with match=. | keep; field-coverage gap -> follow-on G1 |
| `tests/unit/api/test_parser.py::test_empty_records_list_returns_empty_list` | keep | Behavioral parser test: asserts parsed values and error cases with match=. | keep; field-coverage gap -> follow-on G1 |
| `tests/unit/api/test_parser.py::test_records_not_list_raises_validation_error` | keep | Behavioral parser test: asserts parsed values and error cases with match=. | keep; field-coverage gap -> follow-on G1 |
| `tests/unit/api/test_parser.py::test_rating_out_of_range_raises_validation_error` | keep | Behavioral parser test: asserts parsed values and error cases with match=. | keep; field-coverage gap -> follow-on G1 |
| `tests/unit/api/test_parser.py::test_optional_ratings_can_be_none` | keep | Behavioral parser test: asserts parsed values and error cases with match=. | keep; field-coverage gap -> follow-on G1 |
| `tests/unit/api/test_parser.py::test_multiple_notes_parsed` | keep | Behavioral parser test: asserts parsed values and error cases with match=. | keep; field-coverage gap -> follow-on G1 |
| `tests/unit/api/test_parser.py::test_valid_walk_record_response_returns_models` | keep | Behavioral parser test: asserts parsed values and error cases with match=. | keep; field-coverage gap -> follow-on G1 |
| `tests/unit/api/test_parser.py::test_empty_records_list_returns_empty_list` | keep | Behavioral parser test: asserts parsed values and error cases with match=. | keep; field-coverage gap -> follow-on G1 |
| `tests/unit/api/test_parser.py::test_records_not_list_raises_validation_error` | keep | Behavioral parser test: asserts parsed values and error cases with match=. | keep; field-coverage gap -> follow-on G1 |
| `tests/unit/api/test_parser.py::test_optional_fields_can_be_none` | keep | Behavioral parser test: asserts parsed values and error cases with match=. | keep; field-coverage gap -> follow-on G1 |
| `tests/unit/api/test_parser.py::test_multiple_walks_parsed` | keep | Behavioral parser test: asserts parsed values and error cases with match=. | keep; field-coverage gap -> follow-on G1 |
| `tests/unit/db/test_models.py::test_create_animal_minimal` | keep | Pydantic model behavior: computed props (age, days-in-custody, is_adoptable), tag coercion, model_dump include/exclude. | keep |
| `tests/unit/db/test_models.py::test_create_animal_with_species` | keep | Pydantic model behavior: computed props (age, days-in-custody, is_adoptable), tag coercion, model_dump include/exclude. | keep |
| `tests/unit/db/test_models.py::test_species_defaults_to_none` | keep | Pydantic model behavior: computed props (age, days-in-custody, is_adoptable), tag coercion, model_dump include/exclude. | keep |
| `tests/unit/db/test_models.py::test_create_animal_full` | keep | Pydantic model behavior: computed props (age, days-in-custody, is_adoptable), tag coercion, model_dump include/exclude. | keep |
| `tests/unit/db/test_models.py::test_model_dump_excludes_none` | keep | Pydantic model behavior: computed props (age, days-in-custody, is_adoptable), tag coercion, model_dump include/exclude. | keep |
| `tests/unit/db/test_models.py::test_model_dump_includes_none` | keep | Pydantic model behavior: computed props (age, days-in-custody, is_adoptable), tag coercion, model_dump include/exclude. | keep |
| `tests/unit/db/test_models.py::test_custody_location_kennel` | keep | Pydantic model behavior: computed props (age, days-in-custody, is_adoptable), tag coercion, model_dump include/exclude. | keep |
| `tests/unit/db/test_models.py::test_custody_location_foster` | keep | Pydantic model behavior: computed props (age, days-in-custody, is_adoptable), tag coercion, model_dump include/exclude. | keep |
| `tests/unit/db/test_models.py::test_custody_location_defaults_to_none` | keep | Pydantic model behavior: computed props (age, days-in-custody, is_adoptable), tag coercion, model_dump include/exclude. | keep |
| `tests/unit/db/test_models.py::test_custody_location_invalid_raises` | keep | Pydantic model behavior: computed props (age, days-in-custody, is_adoptable), tag coercion, model_dump include/exclude. | keep |
| `tests/unit/db/test_models.py::test_age_years_with_birth_date` | keep | Pydantic model behavior: computed props (age, days-in-custody, is_adoptable), tag coercion, model_dump include/exclude. | keep |
| `tests/unit/db/test_models.py::test_age_years_without_birth_date` | keep | Pydantic model behavior: computed props (age, days-in-custody, is_adoptable), tag coercion, model_dump include/exclude. | keep |
| `tests/unit/db/test_models.py::test_age_years_with_invalid_date` | keep | Pydantic model behavior: computed props (age, days-in-custody, is_adoptable), tag coercion, model_dump include/exclude. | keep |
| `tests/unit/db/test_models.py::test_age_years_with_future_date` | keep | Pydantic model behavior: computed props (age, days-in-custody, is_adoptable), tag coercion, model_dump include/exclude. | keep |
| `tests/unit/db/test_models.py::test_days_in_custody_with_intake_date` | keep | Pydantic model behavior: computed props (age, days-in-custody, is_adoptable), tag coercion, model_dump include/exclude. | keep |
| `tests/unit/db/test_models.py::test_days_in_custody_without_intake_date` | keep | Pydantic model behavior: computed props (age, days-in-custody, is_adoptable), tag coercion, model_dump include/exclude. | keep |
| `tests/unit/db/test_models.py::test_days_in_custody_with_invalid_date` | keep | Pydantic model behavior: computed props (age, days-in-custody, is_adoptable), tag coercion, model_dump include/exclude. | keep |
| `tests/unit/db/test_models.py::test_days_in_custody_with_future_date` | keep | Pydantic model behavior: computed props (age, days-in-custody, is_adoptable), tag coercion, model_dump include/exclude. | keep |
| `tests/unit/db/test_models.py::test_is_adoptable_green_category` | keep | Pydantic model behavior: computed props (age, days-in-custody, is_adoptable), tag coercion, model_dump include/exclude. | keep |
| `tests/unit/db/test_models.py::test_is_adoptable_yellow_category` | keep | Pydantic model behavior: computed props (age, days-in-custody, is_adoptable), tag coercion, model_dump include/exclude. | keep |
| `tests/unit/db/test_models.py::test_is_adoptable_orange_category` | keep | Pydantic model behavior: computed props (age, days-in-custody, is_adoptable), tag coercion, model_dump include/exclude. | keep |
| `tests/unit/db/test_models.py::test_is_adoptable_senior_category` | keep | Pydantic model behavior: computed props (age, days-in-custody, is_adoptable), tag coercion, model_dump include/exclude. | keep |
| `tests/unit/db/test_models.py::test_is_adoptable_designated_category` | keep | Pydantic model behavior: computed props (age, days-in-custody, is_adoptable), tag coercion, model_dump include/exclude. | keep |
| `tests/unit/db/test_models.py::test_is_adoptable_without_category` | keep | Pydantic model behavior: computed props (age, days-in-custody, is_adoptable), tag coercion, model_dump include/exclude. | keep |
| `tests/unit/db/test_models.py::test_is_adoptable_case_insensitive` | keep | Pydantic model behavior: computed props (age, days-in-custody, is_adoptable), tag coercion, model_dump include/exclude. | keep |
| `tests/unit/db/test_models.py::test_is_adoptable_unknown_category` | keep | Pydantic model behavior: computed props (age, days-in-custody, is_adoptable), tag coercion, model_dump include/exclude. | keep |
| `tests/unit/db/test_models.py::test_create_note_with_ratings` | keep | Pydantic model behavior: computed props (age, days-in-custody, is_adoptable), tag coercion, model_dump include/exclude. | keep |
| `tests/unit/db/test_models.py::test_model_dump_excludes_id` | keep | Pydantic model behavior: computed props (age, days-in-custody, is_adoptable), tag coercion, model_dump include/exclude. | keep |
| `tests/unit/db/test_models.py::test_model_dump_includes_id_when_present` | keep | Pydantic model behavior: computed props (age, days-in-custody, is_adoptable), tag coercion, model_dump include/exclude. | keep |
| `tests/unit/db/test_models.py::test_create_behavior_profile` | keep | Pydantic model behavior: computed props (age, days-in-custody, is_adoptable), tag coercion, model_dump include/exclude. | keep |
| `tests/unit/db/test_models.py::test_create_behavior_profile_commands_and_housebreaking` | keep | Pydantic model behavior: computed props (age, days-in-custody, is_adoptable), tag coercion, model_dump include/exclude. | keep |
| `tests/unit/db/test_models.py::test_behavior_mod_tags_from_json_string` | keep | Pydantic model behavior: computed props (age, days-in-custody, is_adoptable), tag coercion, model_dump include/exclude. | keep |
| `tests/unit/db/test_models.py::test_behavior_mod_tags_from_list` | keep | Pydantic model behavior: computed props (age, days-in-custody, is_adoptable), tag coercion, model_dump include/exclude. | keep |
| `tests/unit/db/test_models.py::test_behavior_mod_tags_none` | keep | Pydantic model behavior: computed props (age, days-in-custody, is_adoptable), tag coercion, model_dump include/exclude. | keep |
| `tests/unit/db/test_models.py::test_behavior_mod_tags_empty_string` | keep | Pydantic model behavior: computed props (age, days-in-custody, is_adoptable), tag coercion, model_dump include/exclude. | keep |
| `tests/unit/db/test_models.py::test_behavior_mod_tags_empty_array` | keep | Pydantic model behavior: computed props (age, days-in-custody, is_adoptable), tag coercion, model_dump include/exclude. | keep |
| `tests/unit/db/test_models.py::test_behavior_mod_tags_invalid_json` | keep | Pydantic model behavior: computed props (age, days-in-custody, is_adoptable), tag coercion, model_dump include/exclude. | keep |
| `tests/unit/db/test_models.py::test_behavior_mod_tags_non_array_json` | keep | Pydantic model behavior: computed props (age, days-in-custody, is_adoptable), tag coercion, model_dump include/exclude. | keep |
| `tests/unit/db/test_models.py::test_behavior_mod_tags_model_dump_serializes` | keep | Pydantic model behavior: computed props (age, days-in-custody, is_adoptable), tag coercion, model_dump include/exclude. | keep |
| `tests/unit/db/test_models.py::test_behavior_mod_tags_coerces_to_strings` | keep | Pydantic model behavior: computed props (age, days-in-custody, is_adoptable), tag coercion, model_dump include/exclude. | keep |
| `tests/unit/db/test_models.py::test_behavior_mod_tags_size_limit` | keep | Pydantic model behavior: computed props (age, days-in-custody, is_adoptable), tag coercion, model_dump include/exclude. | keep |
| `tests/unit/db/test_models.py::test_create_assessment` | keep | Pydantic model behavior: computed props (age, days-in-custody, is_adoptable), tag coercion, model_dump include/exclude. | keep |
| `tests/unit/db/test_models.py::test_assessment_tags_from_json_string` | keep | Pydantic model behavior: computed props (age, days-in-custody, is_adoptable), tag coercion, model_dump include/exclude. | keep |
| `tests/unit/db/test_models.py::test_assessment_tags_from_list` | keep | Pydantic model behavior: computed props (age, days-in-custody, is_adoptable), tag coercion, model_dump include/exclude. | keep |
| `tests/unit/db/test_models.py::test_assessment_tags_none` | keep | Pydantic model behavior: computed props (age, days-in-custody, is_adoptable), tag coercion, model_dump include/exclude. | keep |
| `tests/unit/db/test_models.py::test_assessment_tags_empty_string` | keep | Pydantic model behavior: computed props (age, days-in-custody, is_adoptable), tag coercion, model_dump include/exclude. | keep |
| `tests/unit/db/test_models.py::test_assessment_tags_empty_array` | keep | Pydantic model behavior: computed props (age, days-in-custody, is_adoptable), tag coercion, model_dump include/exclude. | keep |
| `tests/unit/db/test_models.py::test_assessment_tags_invalid_json` | keep | Pydantic model behavior: computed props (age, days-in-custody, is_adoptable), tag coercion, model_dump include/exclude. | keep |
| `tests/unit/db/test_models.py::test_assessment_tags_non_array_json` | keep | Pydantic model behavior: computed props (age, days-in-custody, is_adoptable), tag coercion, model_dump include/exclude. | keep |
| `tests/unit/db/test_models.py::test_assessment_model_dump_serializes_tags` | keep | Pydantic model behavior: computed props (age, days-in-custody, is_adoptable), tag coercion, model_dump include/exclude. | keep |
| `tests/unit/db/test_models.py::test_assessment_tags_coerces_to_strings` | keep | Pydantic model behavior: computed props (age, days-in-custody, is_adoptable), tag coercion, model_dump include/exclude. | keep |
| `tests/unit/db/test_models.py::test_assessment_tags_size_limit` | keep | Pydantic model behavior: computed props (age, days-in-custody, is_adoptable), tag coercion, model_dump include/exclude. | keep |
| `tests/unit/db/test_models.py::test_create_walk_record` | keep | Pydantic model behavior: computed props (age, days-in-custody, is_adoptable), tag coercion, model_dump include/exclude. | keep |
| `tests/unit/db/test_models.py::test_create_image` | keep | Pydantic model behavior: computed props (age, days-in-custody, is_adoptable), tag coercion, model_dump include/exclude. | keep |
| `tests/unit/db/test_models.py::test_create_sync_log` | keep | Pydantic model behavior: computed props (age, days-in-custody, is_adoptable), tag coercion, model_dump include/exclude. | keep |
| `tests/unit/db/test_models.py::test_sync_log_defaults` | keep | Pydantic model behavior: computed props (age, days-in-custody, is_adoptable), tag coercion, model_dump include/exclude. | keep |
| `tests/unit/db/test_models.py::test_sync_log_none_to_zero_conversion` | keep | Pydantic model behavior: computed props (age, days-in-custody, is_adoptable), tag coercion, model_dump include/exclude. | keep |
| `tests/unit/db/test_models.py::test_sync_log_zero_preserved` | keep | Pydantic model behavior: computed props (age, days-in-custody, is_adoptable), tag coercion, model_dump include/exclude. | keep |
| `tests/unit/models/test_base.py::test_async_url_coerces_driver` | keep | Async engine URL coercion behavior (driver swap, sslmode stripping). | keep |
| `tests/unit/models/test_base.py::test_async_url_strips_trailing_sslmode` | keep | Async engine URL coercion behavior (driver swap, sslmode stripping). | keep |
| `tests/unit/models/test_base.py::test_async_url_strips_leading_sslmode_keeps_other_params` | keep | Async engine URL coercion behavior (driver swap, sslmode stripping). | keep |
| `tests/unit/models/test_mappers.py::test_animal_round_trip_preserves_fields` | keep | Round-trip mapper test asserting fields both directions; sound AAA. | keep; field-coverage gap -> follow-on G2 |
| `tests/unit/models/test_mappers.py::test_animal_to_row_leaves_server_default_timestamps_unset` | keep | Round-trip mapper test asserting fields both directions; sound AAA. | keep; field-coverage gap -> follow-on G2 |
| `tests/unit/models/test_mappers.py::test_birth_date_accepts_datetime_string` | keep | Round-trip mapper test asserting fields both directions; sound AAA. | keep; field-coverage gap -> follow-on G2 |
| `tests/unit/models/test_mappers.py::test_behavior_profile_round_trip_preserves_fields` | keep | Round-trip mapper test asserting fields both directions; sound AAA. | keep; field-coverage gap -> follow-on G2 |
| `tests/unit/models/test_mappers.py::test_volunteer_note_round_trip` | keep | Round-trip mapper test asserting fields both directions; sound AAA. | keep; field-coverage gap -> follow-on G2 |
| `tests/unit/models/test_mappers.py::test_staff_assessment_round_trip_tags` | keep | Round-trip mapper test asserting fields both directions; sound AAA. | keep; field-coverage gap -> follow-on G2 |
| `tests/unit/models/test_mappers.py::test_sync_log_round_trip` | keep | Round-trip mapper test asserting fields both directions; sound AAA. | keep; field-coverage gap -> follow-on G2 |
| `tests/unit/models/test_pool.py::test_create_engine_accepts_pool_params` | keep | Env-driven pool sizing behavior. | keep |
| `tests/unit/models/test_pool.py::test_settings_db_pool_defaults` | rewrite | Config-restatement: asserts default literals equal the same literals; mutation-blind. | follow-on G4: assert pool defaults via behavior, not literal echo |
| `tests/unit/models/test_tables.py::test_all_seven_tables_present_and_prefixed` | keep | Encodes multi-tenant data-isolation invariants (tenant_id on every table, cascade FKs, index presence); structure-coupled but guards a security-critical contract. | keep |
| `tests/unit/models/test_tables.py::test_every_table_is_tenant_owned` | keep | Encodes multi-tenant data-isolation invariants (tenant_id on every table, cascade FKs, index presence); structure-coupled but guards a security-critical contract. | keep |
| `tests/unit/models/test_tables.py::test_every_table_has_tenant_id` | keep | Encodes multi-tenant data-isolation invariants (tenant_id on every table, cascade FKs, index presence); structure-coupled but guards a security-critical contract. | keep |
| `tests/unit/models/test_tables.py::test_expected_indexes_present` | keep | Encodes multi-tenant data-isolation invariants (tenant_id on every table, cascade FKs, index presence); structure-coupled but guards a security-critical contract. | keep |
| `tests/unit/models/test_tables.py::test_decay_critical_indexes_on_volunteer_notes` | keep | Encodes multi-tenant data-isolation invariants (tenant_id on every table, cascade FKs, index presence); structure-coupled but guards a security-critical contract. | keep |
| `tests/unit/models/test_tables.py::test_timestamp_columns_are_timezone_aware` | keep | Encodes multi-tenant data-isolation invariants (tenant_id on every table, cascade FKs, index presence); structure-coupled but guards a security-critical contract. | keep |
| `tests/unit/models/test_tables.py::test_animals_has_species_column` | keep | Encodes multi-tenant data-isolation invariants (tenant_id on every table, cascade FKs, index presence); structure-coupled but guards a security-critical contract. | keep |
| `tests/unit/models/test_tables.py::test_animals_has_custody_location_column` | keep | Encodes multi-tenant data-isolation invariants (tenant_id on every table, cascade FKs, index presence); structure-coupled but guards a security-critical contract. | keep |
| `tests/unit/models/test_tables.py::test_tag_columns_are_jsonb` | keep | Encodes multi-tenant data-isolation invariants (tenant_id on every table, cascade FKs, index presence); structure-coupled but guards a security-critical contract. | keep |
| `tests/unit/models/test_tables.py::test_animal_child_foreign_keys_cascade` | keep | Encodes multi-tenant data-isolation invariants (tenant_id on every table, cascade FKs, index presence); structure-coupled but guards a security-critical contract. | keep |
| `tests/unit/models/test_tables.py::test_behavior_profile_column_shapes` | keep | Encodes multi-tenant data-isolation invariants (tenant_id on every table, cascade FKs, index presence); structure-coupled but guards a security-critical contract. | keep |
| `tests/unit/test_auth.py::test_decode_valid_token` | keep | JWKS/JWT + FastAPI dependency auth: asserts real 401/403/200; JWKS mock is a justified network-boundary mock. | keep |
| `tests/unit/test_auth.py::test_decode_expired_token` | keep | JWKS/JWT + FastAPI dependency auth: asserts real 401/403/200; JWKS mock is a justified network-boundary mock. | keep |
| `tests/unit/test_auth.py::test_decode_invalid_signature` | keep | JWKS/JWT + FastAPI dependency auth: asserts real 401/403/200; JWKS mock is a justified network-boundary mock. | keep |
| `tests/unit/test_auth.py::test_require_auth_valid_token` | keep | JWKS/JWT + FastAPI dependency auth: asserts real 401/403/200; JWKS mock is a justified network-boundary mock. | keep |
| `tests/unit/test_auth.py::test_require_auth_missing_token` | keep | JWKS/JWT + FastAPI dependency auth: asserts real 401/403/200; JWKS mock is a justified network-boundary mock. | keep |
| `tests/unit/test_auth.py::test_require_auth_invalid_signature` | keep | JWKS/JWT + FastAPI dependency auth: asserts real 401/403/200; JWKS mock is a justified network-boundary mock. | keep |
| `tests/unit/test_auth.py::test_require_auth_expired_token` | keep | JWKS/JWT + FastAPI dependency auth: asserts real 401/403/200; JWKS mock is a justified network-boundary mock. | keep |
| `tests/unit/test_auth.py::test_require_admin_non_admin` | keep | JWKS/JWT + FastAPI dependency auth: asserts real 401/403/200; JWKS mock is a justified network-boundary mock. | keep |
| `tests/unit/test_auth.py::test_require_admin_is_admin` | keep | JWKS/JWT + FastAPI dependency auth: asserts real 401/403/200; JWKS mock is a justified network-boundary mock. | keep |
| `tests/unit/test_auth.py::test_animals_route_requires_auth` | keep | JWKS/JWT + FastAPI dependency auth: asserts real 401/403/200; JWKS mock is a justified network-boundary mock. | keep |
| `tests/unit/test_auth.py::test_animals_route_requires_subscription` | keep | JWKS/JWT + FastAPI dependency auth: asserts real 401/403/200; JWKS mock is a justified network-boundary mock. | keep |
| `tests/unit/test_auth.py::test_animals_route_subscribed_passes_guard` | keep | JWKS/JWT + FastAPI dependency auth: asserts real 401/403/200; JWKS mock is a justified network-boundary mock. | keep |
| `tests/unit/test_auth.py::test_health_stays_open` | keep | JWKS/JWT + FastAPI dependency auth: asserts real 401/403/200; JWKS mock is a justified network-boundary mock. | keep |
| `tests/unit/web/test_routes.py::test_animal_to_response_exposes_species_location_custody_and_synced_at` | keep | Route helper mapping to response schema. | keep |
