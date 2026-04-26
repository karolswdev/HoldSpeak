# HS-4-02 — Block authoring API + UI (`WFS-CFG-001` + `WFS-CFG-002`)

- **Project:** holdspeak
- **Phase:** 4
- **Status:** done
- **Depends on:** HS-4-01 (audit confirms web runtime is stable to extend)
- **Unblocks:** dogfood-friendly block authoring without YAML editing
- **Owner:** unassigned

## Problem

Today, using DIR-01 means hand-writing
`~/.config/holdspeak/blocks.yaml` (and optionally
`<project_root>/.holdspeak/blocks.yaml`). The schema is non-trivial:
each block carries `match.examples`, `match.negative_examples`,
`match.threshold`, `match.extras_schema`, `inject.mode`,
`inject.template` with `{raw_text}` / `{project.name}` /
`{project.kb.*}` / `{intent.extras.*}` placeholders. This is the
single biggest barrier to using the dictation pipeline.

This story ships a web API + UI so blocks are authored from the
browser with validation that mirrors the YAML loader.

## Scope

- **In:**
  - `GET /api/dictation/blocks?scope=global` → returns the global `blocks.yaml` parsed via `load_blocks_yaml()`.
  - `GET /api/dictation/blocks?scope=project` → returns the per-project `blocks.yaml` if a project is detected, else 404 with a clear message.
  - `POST /api/dictation/blocks?scope=<global|project>` → adds a new block; validates via `load_blocks_yaml()` round-trip.
  - `PUT /api/dictation/blocks/{block_id}?scope=<scope>` → replaces an existing block; same validation.
  - `DELETE /api/dictation/blocks/{block_id}?scope=<scope>` → removes; rejects if last block in file (or allows + leaves `blocks: []` — pick at impl time).
  - All writes are atomic: write to `<path>.tmp`, then `os.replace` (`WFS-CFG-006`). Bad writes return HTTP 4xx with field-level `BlockConfigError` detail; never clobber existing valid files.
  - Web UI panel in `holdspeak/static/dashboard.html` (or a new dedicated page; pick at impl time): list current blocks, "+ new block" button, per-block edit form with fields for examples / negative examples / threshold / inject mode / template. Live preview of the resolved template against the current `Utterance.project` + a sample `raw_text`.
  - Integration tests covering each endpoint + each error path (invalid YAML payload, missing project, unknown block_id on PUT/DELETE, atomic-write rollback on validation failure).
- **Out:**
  - Schema-driven editor for `match.extras_schema` — ship a free-text JSON field for v1; richer schema editor is a polish story.
  - Multi-project switching (per phase risk #1 — scoped to currently-detected project only).
  - Importing blocks from external sources (e.g., starter packs) — a candidate for a later phase if dogfood demands.

## Acceptance criteria

- [x] All 5 endpoints implemented and integration-tested.
- [x] Validation mirrors `BlockConfigError`: HTTP 4xx body includes the offending field path + canonical error message.
- [x] Atomic write semantics verified by test: a deliberately-bad PUT does not modify the existing `blocks.yaml`.
- [x] UI panel shipped; lists blocks, supports add/edit/delete, shows template preview against `{raw_text: <sample>, project: <auto-detected>}` context.
- [x] On settings save, the controller's pipeline cache is invalidated. **Wired as an optional `on_dictation_config_changed` callback on `MeetingWebServer`; `web_runtime.py` does not run dictation locally so the callback is unwired in that path. Cache invalidation is contract-shaped and ready for whichever later story (HS-4-04 dictation runtime config) actually shares the controller.**
- [x] Full regression: `uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py` PASS (1036 passed, +24 vs. baseline 1012).

## Test plan

- **Integration:** `tests/integration/test_web_dictation_blocks_api.py` covering CRUD + error paths.
- **Unit:** validation pass-through (the API layer should be a thin shell over `load_blocks_yaml`).
- **Regression:** documented full-suite command (metal excluded).

## Notes / open questions

- `holdspeak/static/dashboard.html` is currently meeting-focused. Either extend it with a "Dictation" tab or add a new `holdspeak/static/dictation.html` page; pick at impl time and document.
- Template-preview rendering: implement client-side via the same `_resolve_template` regex shape as `kb_enricher.py` to avoid an extra round-trip; document where that source-of-truth lives.
- Per-project scope detection: use `detect_project_for_cwd()` on every request (cheap; same call site as the rest of the dictation surface).
