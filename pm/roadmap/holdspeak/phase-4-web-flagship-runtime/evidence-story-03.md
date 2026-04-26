# Evidence — HS-4-03: Project KB authoring API + UI (`WFS-CFG-003`)

- **Phase:** 4 (Web Flagship Runtime + Configurability)
- **Story:** HS-4-03
- **Captured at HEAD:** `3e76510` (pre-commit)
- **Date:** 2026-04-26

## What shipped

- **`holdspeak/plugins/dictation/project_kb.py`** — new module, parallel to `project_root.py`. Exports:
  - `kb_path_for(root) -> Path`
  - `read_project_kb(root) -> dict | None` (returns `None` when the file is absent; `{}` when it exists but has no `kb` section).
  - `write_project_kb(root, kb)` — validates then atomic-write (`temp + os.replace`, `WFS-CFG-006`).
  - `delete_project_kb(root) -> bool` — removes `<root>/.holdspeak/project.yaml`; preserves the `.holdspeak/` directory itself (it's also the strongest project-anchor signal in `detect_project_for_cwd`).
  - `KB_KEY_RE = ^[A-Za-z_][A-Za-z0-9_]*$` — enforced on every key so `{project.kb.<key>}` resolves cleanly via `kb_enricher._lookup`'s dotted-name traversal.
  - Values must be `str` or `None`; anything else raises `ProjectKBError`.
- **`holdspeak/web_server.py`** — three new endpoints:
  - `GET /api/dictation/project-kb` — returns `{detected, kb, kb_path}`. When no project is detected, all three are null and `message` carries the cwd. Never errors on absence.
  - `PUT /api/dictation/project-kb` — body `{kb: {...}}`; writes (and creates if needed) `<root>/.holdspeak/project.yaml`. Re-detects after the write so the response surfaces the upgraded `holdspeak` anchor when the PUT just created `.holdspeak/`.
  - `DELETE /api/dictation/project-kb` — removes the file; 404 when there's no project root or no file.
  - All writes call `on_dictation_config_changed` if wired (same callback introduced in HS-4-02).
- **`holdspeak/static/dictation.html`** — added a top-level section toggle ("Blocks" / "Project KB"). The KB section shows the detected context, a row-based key/value editor (add/remove rows; empty value = `null`), and Save / Reset / Delete-file actions. Disambiguated `loadScope`'s active-class toggle to avoid colliding with the section buttons.
- **`tests/integration/test_web_project_kb_api.py`** — 16 tests covering GET (no project / no file / present / malformed), PUT (create / overwrite / bad key / bad value / null value / missing payload key / no project), DELETE (success / no file / no project), round-trip, and a page smoke test that the new section is reachable.

## Design calls made (and why)

| Call | Decision | Why |
|---|---|---|
| Helpers location | New `plugins/dictation/project_kb.py` (parallel to `project_root.py`) | `project_root.py` is detection-only; mixing in write semantics would muddle its scope. The new module is the symmetric write side. |
| GET when no project | 200 with all-null fields + `message` | The page always loads — the UI needs to render the "no project" state without a banner-error path. Distinct from PUT/DELETE which 404 because they require a project. |
| PUT response re-detects | Re-runs `detect_project_for_cwd` after the write | Creating `.holdspeak/project.yaml` also creates `.holdspeak/`, which upgrades the anchor signal from `git`/manifest to `holdspeak`. The response should reflect the new state so the UI doesn't need a separate refresh. |
| Value type | `str` or `None` | The kb-enricher renders templates as strings; complex / nested values would have to be flattened anyway. `None` lets a user keep a placeholder slot. |
| Section UI integration | Top-level toggle inside `dictation.html` (not a separate page) | Both editors share the same "dictation surface" mental model; one page is less navigation surface. Re-used the existing `.scope-row` style. |
| Cache invalidation | Reuses `on_dictation_config_changed` from HS-4-02 | Same contract; same unwired-in-web_runtime caveat. HS-4-04 is the natural integration point. |

## Test output

### Targeted

```
$ uv run pytest tests/integration/test_web_project_kb_api.py -v --timeout=30
... (output snipped)
collected 16 items

tests/integration/test_web_project_kb_api.py::TestGetProjectKB::test_no_project_returns_nulls PASSED
tests/integration/test_web_project_kb_api.py::TestGetProjectKB::test_project_no_kb_file_returns_kb_null PASSED
tests/integration/test_web_project_kb_api.py::TestGetProjectKB::test_project_with_kb_returns_dict PASSED
tests/integration/test_web_project_kb_api.py::TestGetProjectKB::test_malformed_existing_file_422 PASSED
tests/integration/test_web_project_kb_api.py::TestPutProjectKB::test_put_creates_file PASSED
tests/integration/test_web_project_kb_api.py::TestPutProjectKB::test_put_overwrites_existing_atomically PASSED
tests/integration/test_web_project_kb_api.py::TestPutProjectKB::test_put_bad_key_422_and_atomic_rollback PASSED
tests/integration/test_web_project_kb_api.py::TestPutProjectKB::test_put_bad_value_type_422 PASSED
tests/integration/test_web_project_kb_api.py::TestPutProjectKB::test_put_null_value_allowed PASSED
tests/integration/test_web_project_kb_api.py::TestPutProjectKB::test_put_missing_kb_key_400 PASSED
tests/integration/test_web_project_kb_api.py::TestPutProjectKB::test_put_no_project_404 PASSED
tests/integration/test_web_project_kb_api.py::TestDeleteProjectKB::test_delete_removes_file_preserves_dir PASSED
tests/integration/test_web_project_kb_api.py::TestDeleteProjectKB::test_delete_no_file_404 PASSED
tests/integration/test_web_project_kb_api.py::TestDeleteProjectKB::test_delete_no_project_404 PASSED
tests/integration/test_web_project_kb_api.py::test_dictation_page_includes_project_kb_section PASSED
tests/integration/test_web_project_kb_api.py::test_round_trip_put_then_get PASSED

============================== 16 passed in 0.57s ==============================
```

### Full regression

```
$ uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py
... (output snipped)
1052 passed, 13 skipped in 19.33s
```

Pass delta vs. HS-4-02 baseline (1036 passed): **+16** (16 new tests). 13 skipped is unchanged.

## WFS-CFG-* coverage

| Requirement | How verified |
|---|---|
| WFS-CFG-003 | Full CRUD via the 3 new endpoints + UI section. Tests cover GET (4 cases), PUT (7 cases), DELETE (3 cases), round-trip (1), page smoke (1). |
| WFS-CFG-006 | Atomic write — `TestPutProjectKB::test_put_bad_key_422_and_atomic_rollback` asserts on-disk byte equality after a rejected PUT. Reused temp-and-`os.replace` pattern from HS-4-02. |

## Side effect documented

A first PUT against a project whose anchor was `git` or a language manifest will create `<root>/.holdspeak/`, which upgrades the anchor priority on subsequent `detect_project_for_cwd()` calls (per `_ANCHOR_PRIORITY` in `project_root.py`). The PUT response re-runs detection so the UI sees this immediately. Documented here so it isn't surprising.

## Out-of-scope (deferred per story / phase shape)

- Locking down the kb schema (specific required keys like `stack`, `recent_adrs_short`) — open per phase decisions.
- Markdown rendering for kb values — strings only.
- Multi-project KB editor — scoped to the cwd-detected project per phase risk #1.
- Wiring `on_dictation_config_changed` from a controller — HS-4-04.
