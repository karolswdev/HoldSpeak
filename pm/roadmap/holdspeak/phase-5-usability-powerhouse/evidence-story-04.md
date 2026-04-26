# Evidence — HS-5-04: Template create + dry-run loop

- **Phase:** 5 (Usability Powerhouse)
- **Story:** HS-5-04
- **Captured at HEAD:** `ed43eb4` (pre-commit)
- **Date:** 2026-04-26

## What Shipped

- **Create + dry-run API** — `POST /api/dictation/blocks/from-template`
  now accepts `{"dry_run": true}`. It creates the selected starter
  block, then runs the template's `sample_utterance` through the same
  dry-run executor used by `POST /api/dictation/dry-run`.
- **Created block provenance** — combined responses include the actual
  duplicate-safe `created_block_id`, template metadata, sample input,
  pipeline stages, final output, runtime status, and project context.
- **Project-root override** — the combined flow honors
  `project_root` for project-scope creation and dry-run execution.
- **`/dictation` Blocks UI** — each starter template now has a
  **Create + dry-run** action. After creation, the page switches to
  Dry-run and shows the created block ID, starter sample, trace, and
  final text.

## Tests

Focused blocks + dry-run:

```
$ uv run pytest -q tests/integration/test_web_dictation_blocks_api.py tests/integration/test_web_dry_run_api.py
............................................                             [100%]
44 passed in 1.43s
```

Adjacent readiness:

```
$ uv run pytest -q tests/integration/test_web_dictation_readiness_api.py
.....                                                                    [100%]
5 passed in 0.35s
```

Full non-Metal regression:

```
$ uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py
1089 passed, 13 skipped in 23.78s
```

New coverage:

- template list guarantees sample utterances are present
- create + dry-run in global scope returns the actual created block ID,
  sample utterance, stage trace, and transformed final output
- create + dry-run in project scope honors `project_root`
- non-boolean `dry_run` input is rejected
- `/dictation` exposes the browser-facing "Create + dry-run" action

## Notes

The combined endpoint remains opt-in so existing create-only browser
flows and tests keep their simpler response shape.
