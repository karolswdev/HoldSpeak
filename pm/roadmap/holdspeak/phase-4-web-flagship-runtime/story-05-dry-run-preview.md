# HS-4-05 — Dry-run preview API + UI (`WFS-CFG-005`)

- **Project:** holdspeak
- **Phase:** 4
- **Status:** done
- **Depends on:** HS-4-04 (the dictation panel exists; dry-run is the natural sibling control)
- **Unblocks:** "did my block actually match?" closing the loop in dogfood
- **Owner:** unassigned

## Problem

Even after authoring blocks via the UI (HS-4-02) and configuring
the runtime (HS-4-04), the user has no way to preview whether
their block will fire on a given utterance without holding the
hotkey and speaking it. The CLI has `holdspeak dictation dry-run
"<text>"` (HS-1-08); web has nothing.

This story wraps the same dry-run path in an API endpoint + UI
panel so authoring loops live entirely in the browser.

## Scope

- **In:**
  - `POST /api/dictation/dry-run` with body `{utterance: str}`. Calls `assembly.build_pipeline(cfg.dictation, project_root=...)` (current detected project), constructs a synthetic `Utterance` with `project=detected`, runs the pipeline, returns `{project: ProjectContext | None, runtime_status: str, runtime_detail: str, blocks_count: int, stages: [{stage_id, elapsed_ms, intent: {matched, block_id, confidence} | null, warnings: [], metadata: {}, text: str}], final_text: str, total_elapsed_ms: float, warnings: []}`.
  - Web UI panel: textarea for the utterance, "Run dry-run" button, results pane showing each stage, the matched intent (or no-match), the final enriched text (rendered as text + "copy to clipboard" affordance).
  - When the LLM stage is unavailable, surface that clearly (the runtime-status field already carries this).
  - Integration tests: happy path (block matches, kb-enricher fires); no-project path; LLM-unavailable path; bad utterance (empty / non-string).
- **Out:**
  - Dry-run against a *different* project than the cwd-detected one — keep symmetry with HS-3-02.
  - Diff-style visualization between `raw_text` and `final_text` — flagged as deferred per phase decisions.
  - Streaming output (the dry-run is single-shot; no incremental rendering).

## Acceptance criteria

- [x] `POST /api/dictation/dry-run` accepts `{utterance: str}`, returns the full pipeline-trace shape above.
- [x] Empty / missing utterance returns 4xx with field-level detail.
- [x] When the dictation pipeline is disabled in config, returns 200 with `runtime_status="disabled"` and an empty `stages: []` (matches CLI behaviour).
- [x] UI panel renders the trace clearly; "copy final text" works.
- [x] Integration tests cover the 4 paths above.
- [x] Full regression: `uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py` PASS (1072 passed, 13 skipped).

## Test plan

- **Integration:** `tests/integration/test_web_dry_run_api.py`.
- **Regression:** documented full-suite command (metal excluded).

## Notes / open questions

- The dry-run endpoint is the natural place to verify the full WFS-CFG-001..004 chain is wired correctly: edit a block, set up KB, run dry-run, see it fire. Document this in evidence.
- Avoid loading the LLM runtime *just* for dry-run unless the pipeline is enabled — the existing `build_pipeline` semantics (llm_enabled=False on missing runtime) cover this cleanly.
- Bundling note: committed together with HS-4-06 and HS-5-01..03 because the user asked to commit the accumulated significant work from this session. `.tmp/BUNDLE-OK.md` records the intentional bundle.
