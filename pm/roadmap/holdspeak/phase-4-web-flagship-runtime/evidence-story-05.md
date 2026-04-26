# Evidence — HS-4-05: Dry-run preview API + UI (`WFS-CFG-005`)

- **Phase:** 4 (Web Flagship Runtime + Configurability)
- **Story:** HS-4-05
- **Captured at HEAD:** `0868153` (pre-commit)
- **Date:** 2026-04-26

## What shipped

- **`holdspeak/web_server.py` POST `/api/dictation/dry-run`** — accepts `{utterance: str}`, validates missing / empty / non-string payloads as 400 with `detail.utterance`, detects the current project root, builds the DIR-01 pipeline with the same assembly path as the CLI, and returns `project`, `runtime_status`, `runtime_detail`, `blocks_count`, per-stage trace, `final_text`, `total_elapsed_ms`, and warnings.
- **Disabled behavior** — when `dictation.pipeline.enabled` is false, returns 200 with `runtime_status="disabled"`, `stages=[]`, and passthrough `final_text`.
- **Runtime-unavailable behavior** — when the LLM runtime cannot load, returns 200 with `runtime_status="unavailable"` and still executes the non-LLM path, making the unavailable state visible in the UI instead of failing the preview.
- **`holdspeak/static/dictation.html`** — added a fourth top-level section, "Dry-run", with utterance textarea, run/clear actions, runtime/project/blocks/latency metadata, final text panel, copy-final-text button, warnings, and a per-stage trace showing stage id, elapsed ms, intent match, metadata, warnings, and text.
- **`holdspeak/plugins/dictation/project_root.py`** — project detection now reuses the canonical `project_kb.read_project_kb()` reader so `{project.kb.*}` placeholders resolve from the HS-4-03 schema (`project.yaml` shaped as `kb: {...}`).
- **`tests/integration/test_web_dry_run_api.py`** — 9 new tests covering matched block + project-KB enrichment, no-project execution, LLM-unavailable state, disabled pipeline state, bad payload validation, and page-surface anchors.
- **`tests/unit/test_project_detector_cwd.py`** — updated the project-KB detector fixture to the canonical nested `kb:` schema. There is no legacy flat-file compatibility path.

## Design calls made

| Call | Decision | Why |
|---|---|---|
| Runtime loading | Reuse `assembly.build_pipeline()` directly | Keeps API behavior aligned with CLI and controller assembly semantics. |
| Disabled pipeline | Return 200 with an empty trace | Matches the story acceptance criteria and lets the UI explain "disabled" without treating it as a server error. |
| Bad utterance | 400 with `detail.utterance` | Gives the UI a field-level error while keeping the API simple. |
| Project-KB schema | Canonical `kb: {...}` only | This is a new product with no users; avoid compatibility branches and keep the on-disk contract clean. |
| UI visualization | Plain text trace, no diff | Matches the story's explicit out-of-scope diff visualization. |

## Test output

### Targeted

```
$ uv run pytest -q tests/integration/test_web_dry_run_api.py
.........                                                                [100%]
9 passed in 0.40s
```

```
$ uv run pytest -q tests/unit/test_project_detector_cwd.py tests/integration/test_web_dry_run_api.py tests/integration/test_web_project_kb_api.py
.................................                                        [100%]
33 passed in 0.80s
```

### Full regression

```
$ uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py
... (output snipped)
1072 passed, 13 skipped in 18.65s
```

Pass delta vs. HS-4-04 baseline (1063 passed): **+9** (9 new tests). 13 skipped is unchanged.

## WFS-CFG-* coverage

| Requirement | How verified |
|---|---|
| WFS-CFG-005 | `test_dry_run_matches_block_and_enriches_with_project_kb`, `test_dry_run_no_project_still_runs_pipeline`, `test_dry_run_llm_unavailable_surfaces_runtime_status`, disabled-pipeline test, bad-payload parametrized test, and `/dictation` page-surface test. |
| WFS-CFG-001..004 chain | Happy-path test writes project blocks + project KB, enables runtime config, runs dry-run, and verifies both `intent-router` and `kb-enricher` trace output with final enriched text. |

## Out-of-scope

- Dry-run against an arbitrary project path — still uses current cwd detection.
- Diff visualization between input and final output.
- Streaming / incremental preview output.
