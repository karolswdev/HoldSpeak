# Evidence — HS-18-04 OpenAI-Compatible Runtime Support

**Date:** 2026-05-10
**Status:** done

## What shipped

- Runtime config supports `openai_compatible` with endpoint base URL, model name, optional API-key environment variable, and timeout.
- The OpenAI-compatible runtime uses the common `/v1/chat/completions` shape, requests JSON for classification, validates structured output, and retries without `response_format` for compatible servers that reject that field.
- The project-aware rewriter now fails open: timeout or runtime exceptions preserve the original transcript and emit a warning instead of breaking typing.
- Tests cover successful OpenAI-compatible classification/rewrite, timeout handling, malformed/invalid output, disabled-provider resolution, settings round-trip, and dry-run fallback.
- Docs now describe known-good endpoint families, timeout configuration, API-key env behavior, and the preserve-original fallback rule.

## Files touched

- `holdspeak/plugins/dictation/builtin/project_rewriter.py`
- `tests/unit/test_dictation_project_rewriter.py`
- `tests/unit/test_dictation_runtime.py`
- `README.md`
- `docs/USER_GUIDE.md`
- `web/src/pages/docs/dictation-runtime.astro`
- `holdspeak/static/_built/`

## Verification

```bash
.venv/bin/pytest -q tests/unit/test_dictation_runtime.py tests/unit/test_dictation_project_rewriter.py tests/integration/test_web_dictation_settings_api.py tests/integration/test_web_dry_run_api.py tests/unit/test_doctor_command.py
```

Result: `94 passed in 1.69s`.

```bash
cd web && npm run build
```

Result: Astro built 7 static pages successfully into `holdspeak/static/_built/`.

## Notes

- The fake-server test validates URL path, model name, bearer auth header, and response shape without requiring the optional `openai` package in CI.
- A first parallel verification attempt raced the Astro build and failed one static-page marker check because the built dictation file was momentarily absent. The serial rerun after the build passed.
- Manual smoke against the user's LAN endpoint was not run in this turn; the fake OpenAI-compatible server covers the contract-level behavior.
