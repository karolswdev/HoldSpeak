# Evidence — HS-5-02: Dictation readiness panel

- **Phase:** 5 (Usability Powerhouse)
- **Story:** HS-5-02
- **Captured at HEAD:** `0868153` (pre-commit)
- **Date:** 2026-04-26

## What Shipped

- **`holdspeak/web_server.py`** — added
  `GET /api/dictation/readiness?project_root=...`, a single snapshot
  of dictation setup health. It inspects config, selected project,
  global/project block files, resolved block source, project KB,
  backend resolution, model path existence, runtime counters, and
  session-disabled state.
- **No model load for readiness** — runtime checks use backend
  resolution + model path existence. Readiness does not call
  `build_runtime()` or load LLM weights.
- **Actionable warnings** — returns warning objects with `code`,
  `message`, `action`, and `section` for disabled pipeline, missing
  project, missing/invalid blocks, missing/invalid project KB,
  unavailable runtime, and missing model path.
- **`holdspeak/static/dictation.html`** — added a Readiness section
  with four status cards (Pipeline, Blocks, Project KB, Runtime) and
  next-action rows that navigate directly to the relevant panel.
- **`tests/integration/test_web_dictation_readiness_api.py`** — 5 new
  integration tests covering ready, disabled/no-project, missing
  model, invalid project root, and UI anchors.

## Tests

Focused:

```
$ uv run pytest -q tests/integration/test_web_dictation_readiness_api.py tests/integration/test_web_dictation_blocks_api.py tests/integration/test_web_project_kb_api.py tests/integration/test_web_dry_run_api.py
..........................................................               [100%]
58 passed in 1.61s
```

Full regression:

```
$ uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py
1081 passed, 13 skipped in 21.03s
```

## Notes

This is intentionally a cockpit/checklist surface rather than another
settings editor. It points the user to the right existing panel when
something is missing.
