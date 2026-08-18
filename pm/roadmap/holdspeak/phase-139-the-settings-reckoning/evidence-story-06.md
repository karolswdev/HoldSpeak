# Evidence - HS-139-06

- **Story:** HS-139-06 - The docs sweep
- **Status:** done
- **Date:** 2026-08-17

## Proof

### Captured run — 2026-08-18T03:05:02Z

- **Command:** `HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.BGZhZjxaWA uv run pytest -xvs tests/unit/test_doc_drift_guard.py tests/unit/test_product_copy.py tests/unit/test_api_surface.py`
- **Cwd:** .
- **Exit code:** 127
- **Index-tree:** 3b5fc785d9aecb9497fa036de98a4b70a5280f98

```text
(command could not be executed: [Errno 2] No such file or directory: 'HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.BGZhZjxaWA')
```

### Captured run — 2026-08-18T03:05:26Z

- **Command:** `bash /private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/8cb4eee1-518d-4508-859c-1c60b6eb0e3b/scratchpad/run_doc_guards.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 3b5fc785d9aecb9497fa036de98a4b70a5280f98

```text
============================= test session starts ==============================
platform darwin -- Python 3.13.11, pytest-9.0.2, pluggy-1.6.0 -- /Users/karol/dev/tools/HoldSpeak/.venv/bin/python3
cachedir: .pytest_cache
rootdir: /Users/karol/dev/tools/HoldSpeak
configfile: pyproject.toml
plugins: anyio-4.12.1, mock-3.15.1, xdist-3.8.0, timeout-2.4.0, asyncio-1.3.0, cov-7.0.0
timeout: 300.0s
timeout method: thread
timeout func_only: False
asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=function, asyncio_default_test_loop_scope=function
collecting ... collected 34 items

tests/unit/test_doc_drift_guard.py::test_no_live_doc_claims_a_deterministicplugin_stub PASSED
tests/unit/test_doc_drift_guard.py::test_drift_guard_actually_scans_docs PASSED
tests/unit/test_doc_drift_guard.py::test_no_live_doc_has_a_dangling_relative_link PASSED
tests/unit/test_doc_drift_guard.py::test_effect_census_doc_counts_match_ledger_expected_block PASSED
tests/unit/test_doc_drift_guard.py::test_readme_plugin_count_matches_registry PASSED
tests/unit/test_doc_drift_guard.py::test_all_embedded_image_refs_resolve PASSED
tests/unit/test_doc_drift_guard.py::test_no_user_facing_doc_leaks_roadmap_vocabulary PASSED
tests/unit/test_doc_drift_guard.py::test_roadmap_vocab_guard_scans_real_user_facing_docs PASSED
tests/unit/test_doc_drift_guard.py::test_roadmap_vocab_pattern_is_narrow_enough_to_keep_spec_names PASSED
tests/unit/test_doc_drift_guard.py::test_qlippy_doc_states_the_guarantees_verbatim PASSED
tests/unit/test_doc_drift_guard.py::test_no_user_facing_doc_uses_dashes_in_prose PASSED
tests/unit/test_doc_drift_guard.py::test_no_user_facing_doc_uses_ai_vocabulary PASSED
tests/unit/test_doc_drift_guard.py::test_no_user_facing_doc_uses_banned_feature_names PASSED
tests/unit/test_doc_drift_guard.py::test_no_web_src_copy_uses_banned_feature_names PASSED
tests/unit/test_doc_drift_guard.py::test_banned_name_guard_scans_web_src PASSED
tests/unit/test_doc_drift_guard.py::test_voice_guard_patterns_catch_seeded_violations PASSED
tests/unit/test_doc_drift_guard.py::test_no_swift_copy_uses_banned_feature_names PASSED
tests/unit/test_doc_drift_guard.py::test_no_swift_copy_narrates_privacy_reassurance PASSED
tests/unit/test_doc_drift_guard.py::test_swift_guard_scans_the_app_sources PASSED
tests/unit/test_product_copy.py::test_every_declared_primary_surface_expands_and_is_classified PASSED
tests/unit/test_product_copy.py::test_primary_copy_has_no_prohibited_operational_drift PASSED
tests/unit/test_product_copy.py::test_each_prohibited_product_copy_rule_is_exercised PASSED
tests/unit/test_product_copy.py::test_failure_statements_must_carry_the_four_failure_facts PASSED
tests/unit/test_product_copy.py::test_failure_facts_skip_chips_buttons_and_documentation_prose PASSED
tests/unit/test_product_copy.py::test_failure_facts_exception_is_exact_and_bounded PASSED
tests/unit/test_product_copy.py::test_generic_open_exception_is_exact_and_bounded PASSED
tests/unit/test_product_copy.py::test_markdown_code_is_not_copy_and_does_not_exempt_surrounding_prose PASSED
tests/unit/test_product_copy.py::test_copy_contract_covers_postures_failures_and_bounded_exceptions PASSED
tests/unit/test_product_copy.py::test_inventory_contains_shared_product_language_in_real_surfaces PASSED
tests/unit/test_api_surface.py::test_committed_manifest_matches_the_live_app PASSED
tests/unit/test_api_surface.py::test_committed_markdown_matches_the_manifest PASSED
tests/unit/test_api_surface.py::test_clients_only_call_served_routes PASSED
tests/unit/test_api_surface.py::test_manifest_is_not_vacuous PASSED
tests/unit/test_api_surface.py::test_extractors_see_the_real_call_sites PASSED

============================== 34 passed in 2.35s ==============================
```
