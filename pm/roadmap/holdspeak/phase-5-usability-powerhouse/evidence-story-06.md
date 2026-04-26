# Evidence — HS-5-06: Readiness starter actions

- **Phase:** 5 (Usability Powerhouse)
- **Story:** HS-5-06
- **Captured at HEAD:** `24dee07` (pre-commit)
- **Date:** 2026-04-26

## What Shipped

- **Actionable `no_blocks` warning** — readiness now includes
  `template_id`, `template_action`, and `template_scope` when no
  blocks are loaded.
- **Scope-aware recommendation** — the no-blocks recommendation targets
  `global` when no project is selected and `project` when the user has
  an active project root.
- **Readiness UI action** — the warning list now renders a
  **Create + dry-run** button for template-backed recommendations. It
  calls the HS-5-04 create-plus-dry-run path and displays the resulting
  dry-run trace/final output.

## Tests

Focused dictation cockpit sweep:

```
$ uv run pytest -q tests/integration/test_web_dictation_readiness_api.py tests/integration/test_web_dictation_blocks_api.py tests/integration/test_web_dry_run_api.py
.....................................................                    [100%]
53 passed in 1.60s
```

Full non-Metal regression:

```
$ uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py
1093 passed, 13 skipped in 21.17s
```

New coverage:

- no-project/no-blocks readiness recommends `action_item` in global scope
- project-selected/no-blocks readiness recommends `action_item` in project scope
- `/dictation` contains the readiness template-action wiring

## Notes

The endpoint still does not mutate config. It only tells the browser
which safe next action to offer.
