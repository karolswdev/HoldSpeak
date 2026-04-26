# Evidence — HS-5-03: Starter block templates

- **Phase:** 5 (Usability Powerhouse)
- **Story:** HS-5-03
- **Captured at HEAD:** `0868153` (pre-commit)
- **Date:** 2026-04-26

## What Shipped

- **`GET /api/dictation/block-templates`** — returns four starter
  block templates: AI prompt context, action item, concise note, and
  code review focus.
- **`POST /api/dictation/blocks/from-template`** — creates a block
  from a starter template in global or project scope. Repeated creates
  suffix duplicate IDs (`action_item_2`, etc.) rather than failing.
- **Project-root override** — template creation honors the HS-5-01
  `project_root` override for project-scope blocks.
- **`/dictation` Blocks UI** — added a Starter templates section that
  creates blocks directly from server-defined templates and selects
  the newly-created block for editing.

## Tests

Focused:

```
$ uv run pytest -q tests/integration/test_web_dictation_blocks_api.py tests/integration/test_web_dictation_readiness_api.py tests/integration/test_web_dry_run_api.py
..............................................                           [100%]
46 passed in 1.39s
```

Full regression:

```
$ uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py
1086 passed, 13 skipped in 18.92s
```

New coverage:

- template listing
- global create from template
- duplicate-safe unique IDs
- project-root override create from template
- unknown template 404

## Notes

This does not introduce user-authored template management. The point is
to give users an immediate first useful block while keeping the schema
canonical and server-validated.
