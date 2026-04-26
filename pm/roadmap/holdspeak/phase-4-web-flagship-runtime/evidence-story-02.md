# Evidence — HS-4-02: Block authoring API + UI (`WFS-CFG-001` + `WFS-CFG-002`)

- **Phase:** 4 (Web Flagship Runtime + Configurability)
- **Story:** HS-4-02
- **Captured at HEAD:** `7328d2e` (pre-commit)
- **Date:** 2026-04-26

## What shipped

- **`holdspeak/plugins/dictation/blocks.py`** — new `save_blocks_yaml(path, data)` helper. Validates via the same `_build_loaded_blocks` rules used on read, then writes via temp-and-`os.replace` (`WFS-CFG-006`). On validation failure the existing target file is untouched.
- **`holdspeak/web_server.py`** — five new endpoints under `/api/dictation/blocks`:
  - `GET /api/dictation/blocks?scope=<global|project>`
  - `POST /api/dictation/blocks?scope=<global|project>` (body: `{"block": {...}}`)
  - `PUT /api/dictation/blocks/{block_id}?scope=<scope>`
  - `DELETE /api/dictation/blocks/{block_id}?scope=<scope>`
  - `GET /dictation` — serves the new editor page.
  - Module-level `_GLOBAL_BLOCKS_PATH` constant is monkeypatchable (matches the `CONFIG_FILE` pattern in `test_web_server.py::TestSettingsApiEndpoints`).
- **New optional `on_dictation_config_changed` callback** on `MeetingWebServer` — called after any successful block write. Unwired in `web_runtime.py` today (web runtime doesn't run dictation locally; the controller path that holds `_dictation_pipeline` is non-web). Contract-shaped for HS-4-04 to wire via `apply_runtime_config()`.
- **`holdspeak/static/dictation.html`** — block editor page. Scope toggle (global / project), block list, edit form (id, description, examples, negative examples, threshold, inject mode, template, free-text JSON `extras_schema`), client-side template preview that mirrors `kb_enricher._resolve_template`'s `{name}` / `{a.b.c}` placeholder shape against an editable sample utterance + the auto-detected project context.
- **`tests/integration/test_web_dictation_blocks_api.py`** — 24 tests covering CRUD × global/project, validation parity (malformed YAML, invalid template, invalid inject mode, empty examples), atomic-write rollback (read-back assertion that bad writes don't modify the existing file), 404 for unknown blocks / no-project-detected / missing files, 409 for duplicate-id / rename collision, last-block-delete leaves a valid empty document, page-route smoke test.

## Design calls made (and why)

| Call | Decision | Why |
|---|---|---|
| Editor location | New `static/dictation.html` (not extending `dashboard.html`) | `dashboard.html` is 2819 LOC, meeting-focused, Alpine-based. HS-4-02..05 will add 4 editor surfaces; jamming them into one page is a maintenance liability. New page navigates back to `/`, `/history`, `/settings`. |
| Template preview | Client-side regex mirroring `kb_enricher._resolve_template` shape | No round-trip; the template grammar is small (`{name}` / `{a.b.c}`) and re-implementing it in JS is ~10 LOC. A server-side `/api/dictation/preview-template` will become natural in HS-4-05 (dry-run preview); not warranted here. |
| `extras_schema` editor | Free-text JSON textarea | Story stub explicitly authorizes this for v1; richer schema editor is a polish follow-up. |
| Last-block DELETE | Allowed; leaves `{blocks: []}` on disk | `resolve_blocks` already handles a `blocks: []` file by falling back to the empty default `LoadedBlocks`. Simpler than a special-case rejection. Asserted in `test_delete_last_block_leaves_empty_list`. |
| Cache invalidation | Optional `on_dictation_config_changed` callback (unwired today) | Controller's `_dictation_pipeline` cache lives in the non-web TUI flow. Web runtime doesn't share that controller. The callback is contract-shaped; HS-4-04 will wire it when settings UI lands. |
| Cross-link from `dashboard.html` | Deferred | Adding nav into the Alpine-based hero card is a non-trivial UI surgery for marginal value (the new page already has a back-nav). Polish follow-up. |

## Test output

### Targeted

```
$ uv run pytest tests/integration/test_web_dictation_blocks_api.py -v --timeout=30
... (output snipped)
collected 24 items

tests/integration/test_web_dictation_blocks_api.py::test_dictation_page_route_serves_html PASSED
tests/integration/test_web_dictation_blocks_api.py::TestGetBlocks::test_global_missing_returns_empty_default PASSED
tests/integration/test_web_dictation_blocks_api.py::TestGetBlocks::test_global_present_returns_document PASSED
tests/integration/test_web_dictation_blocks_api.py::TestGetBlocks::test_project_returns_project_context PASSED
tests/integration/test_web_dictation_blocks_api.py::TestGetBlocks::test_project_404_when_no_project_detected PASSED
tests/integration/test_web_dictation_blocks_api.py::TestGetBlocks::test_invalid_scope_400 PASSED
tests/integration/test_web_dictation_blocks_api.py::TestGetBlocks::test_malformed_existing_file_422 PASSED
tests/integration/test_web_dictation_blocks_api.py::TestCreateBlock::test_create_in_empty_global PASSED
tests/integration/test_web_dictation_blocks_api.py::TestCreateBlock::test_create_appends PASSED
tests/integration/test_web_dictation_blocks_api.py::TestCreateBlock::test_create_duplicate_id_409 PASSED
tests/integration/test_web_dictation_blocks_api.py::TestCreateBlock::test_create_invalid_block_422_and_atomic_rollback PASSED
tests/integration/test_web_dictation_blocks_api.py::TestCreateBlock::test_create_invalid_template_422 PASSED
tests/integration/test_web_dictation_blocks_api.py::TestCreateBlock::test_create_in_project_scope PASSED
tests/integration/test_web_dictation_blocks_api.py::TestCreateBlock::test_create_missing_block_key_400 PASSED
tests/integration/test_web_dictation_blocks_api.py::TestCreateBlock::test_project_scope_no_project_404 PASSED
tests/integration/test_web_dictation_blocks_api.py::TestUpdateBlock::test_update_replaces_in_place PASSED
tests/integration/test_web_dictation_blocks_api.py::TestUpdateBlock::test_update_unknown_id_404 PASSED
tests/integration/test_web_dictation_blocks_api.py::TestUpdateBlock::test_update_missing_file_404 PASSED
tests/integration/test_web_dictation_blocks_api.py::TestUpdateBlock::test_update_invalid_block_422_and_atomic_rollback PASSED
tests/integration/test_web_dictation_blocks_api.py::TestUpdateBlock::test_update_rename_collision_409 PASSED
tests/integration/test_web_dictation_blocks_api.py::TestDeleteBlock::test_delete_removes_block PASSED
tests/integration/test_web_dictation_blocks_api.py::TestDeleteBlock::test_delete_unknown_id_404 PASSED
tests/integration/test_web_dictation_blocks_api.py::TestDeleteBlock::test_delete_missing_file_404 PASSED
tests/integration/test_web_dictation_blocks_api.py::TestDeleteBlock::test_delete_last_block_leaves_empty_list PASSED

============================== 24 passed in 0.82s ==============================
```

### Full regression

```
$ uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py
... (output snipped)
1036 passed, 13 skipped in 18.01s
```

Pass delta vs. HS-4-01 baseline (1012 passed): **+24** (24 new tests in `test_web_dictation_blocks_api.py`). 13 skipped is unchanged.

## WFS-CFG-* coverage

| Requirement | How verified |
|---|---|
| WFS-CFG-001 | Block CRUD on `scope=global` (`TestGetBlocks::test_global_*`, `TestCreateBlock`, `TestUpdateBlock`, `TestDeleteBlock`). |
| WFS-CFG-002 | Per-project scope: `TestGetBlocks::test_project_returns_project_context`, `TestGetBlocks::test_project_404_when_no_project_detected`, `TestCreateBlock::test_create_in_project_scope`, `TestCreateBlock::test_project_scope_no_project_404`. |
| WFS-CFG-006 | Atomic write (temp + `os.replace`) — `TestCreateBlock::test_create_invalid_block_422_and_atomic_rollback`, `TestUpdateBlock::test_update_invalid_block_422_and_atomic_rollback` (both assert on-disk byte equality vs. `before` snapshot after a rejected write). |

## Out-of-scope (deferred per story / phase shape)

- Cross-link from `dashboard.html` to `/dictation` — polish; the new page already navigates to `/`, `/history`, `/settings`.
- Schema-driven editor for `match.extras_schema` — story stub authorizes free-text JSON for v1.
- Multi-project switching mid-session — phase risk #1; current session uses `detect_project_for_cwd()`.
- Wiring `on_dictation_config_changed` into a controller — deferred to HS-4-04 (dictation runtime config) which is the natural integration point.
- Server-side `/api/dictation/preview-template` — deferred to HS-4-05 (dry-run preview).
- Manual UI dogfood verification — covered by HTML smoke test (`test_dictation_page_route_serves_html`); a real browser pass on the operator's reference Mac is recommended at phase exit but not gated here.
