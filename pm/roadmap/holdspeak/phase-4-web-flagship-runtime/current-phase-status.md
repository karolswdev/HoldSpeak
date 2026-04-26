# Phase 4 — Web Flagship Runtime + Interactive Configurability (WFS-01 extended)

**Last updated:** 2026-04-26 (HS-4 scaffold — phase opened with 6 backlog stories; WFS-CFG-* requirement family amended into `docs/PLAN_PHASE_WEB_FLAGSHIP_RUNTIME.md` §5.5).

## Goal

Deliver WFS-01 (web flagship runtime + UX migration) per
`docs/PLAN_PHASE_WEB_FLAGSHIP_RUNTIME.md`, **extended** with a
`WFS-CFG-*` requirement family (§5.5, amended 2026-04-26) that
makes every dictation-side configurable surface editable from the
web UI. The driver: phase 3 made dictation grounded + observable
end-to-end, but using it still requires hand-rolling
`blocks.yaml` and `project.yaml` files. This phase closes that
gap so dogfood is approachable without a YAML reference open in
another window.

## Scope

- **In:**
  - HS-4-01 — audit + integration coverage for the existing web-flagship surfaces (`web_runtime.py`, CLI command contract, `/api/meeting/*`). Verify by test what's already shipped (lifecycle, decoupled-from-meeting startup, idle `/history` + `/settings`, deprecation of `--no-tui`); document any spec §5.1–§5.4 gaps as deferred.
  - HS-4-02 — `WFS-CFG-001` + `WFS-CFG-002`: block authoring API + UI. `GET/POST/PUT/DELETE /api/dictation/blocks` (global + per-project), validation mirroring `BlockConfigError`, web UI form with template editor.
  - HS-4-03 — `WFS-CFG-003`: project KB authoring API + UI. `GET/PUT /api/dictation/project-kb` (writes `<root>/.holdspeak/project.yaml`), UI shows auto-detected `name/root/anchor` + form-driven editor for arbitrary string-valued `kb.*` fields.
  - HS-4-04 — `WFS-CFG-004`: dictation runtime config UI. Extend `/api/settings` with `dictation.pipeline.*` + `dictation.runtime.*` fields; UI form with backend selection, model paths, `warm_on_start` toggle, `max_total_latency_ms` slider with the cap × 5 visualization, inline `runtime_counters` snapshot + session-disabled flag.
  - HS-4-05 — `WFS-CFG-005`: dry-run preview. `POST /api/dictation/dry-run` mirroring the CLI subcommand; UI panel that takes an utterance string and renders the pipeline trace (per-stage `elapsed_ms`, matched intent, final enriched text).
  - HS-4-06 — DoD sweep + phase-exit evidence bundle (mirrors HS-1-11 / HS-2-11 / HS-3-06).
- **Out:**
  - Hotkey / Whisper-model UI polish — existing `/settings` page covers these adequately for now.
  - MIR profile/override UI redesign — existing JSON `/api/intents/*` endpoints work; turning into form-driven UI is a candidate for phase 5 if dogfood demands.
  - TUI removal — explicitly out per WFS-01 §2.2 item 1.
  - Full visual redesign — out per WFS-01 §2.2 item 2.
  - Cloud / multi-user deployment — out per WFS-01 §2.2 item 3.

## Exit criteria (evidence required)

- [ ] All `WFS-CFG-*` requirements (§5.5 amendment) have passing verification.
- [ ] `WFS-P-001` through `WFS-O-004` (original WFS-01 requirements) audited in HS-4-01; existing surfaces verified by integration tests and any gaps documented as deferred.
- [ ] Web UI ships interactive editors for: blocks (global + per-project), project KB, dictation pipeline + runtime config, dry-run preview.
- [ ] Configurability writes are atomic (temp + rename) and validate before persisting.
- [ ] Full regression clean: `uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py` PASS.
- [ ] Phase summary at `docs/evidence/phase-wfs-01/<YYYYMMDD-HHMM>/99_phase_summary.md` enumerates what shipped + remaining deferreds.

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HS-4-01 | Audit + integration coverage for existing web-flagship surfaces | backlog | [story-01-audit](./story-01-audit.md) | — |
| HS-4-02 | Block authoring API + UI (`WFS-CFG-001` + `WFS-CFG-002`) | backlog | [story-02-blocks-api-ui](./story-02-blocks-api-ui.md) | — |
| HS-4-03 | Project KB authoring API + UI (`WFS-CFG-003`) | backlog | [story-03-project-kb-api-ui](./story-03-project-kb-api-ui.md) | — |
| HS-4-04 | Dictation runtime config UI (`WFS-CFG-004`) | backlog | [story-04-dictation-config-ui](./story-04-dictation-config-ui.md) | — |
| HS-4-05 | Dry-run preview API + UI (`WFS-CFG-005`) | backlog | [story-05-dry-run-preview](./story-05-dry-run-preview.md) | — |
| HS-4-06 | DoD sweep + phase exit | backlog | [story-06-dod](./story-06-dod.md) | — |

## Where we are

Phase opened. The audit finding that drove the phase shape: the
runtime/CLI/meeting-control halves of WFS-01 are *already built*
(`holdspeak/web_runtime.py` exists at 1101 LOC; `holdspeak/main.py`
ships `web` + `tui` subcommands with `--no-tui` deprecation; the
README documents `holdspeak` as web-first; `/api/meeting/start|stop`,
`/api/meeting` PATCH, `/api/settings` GET/PUT, `/api/projects`
CRUD all live). The configurability half is *entirely unbuilt*:
zero `/api/dictation/*` endpoints, no block editor, no project-KB
editor, no dry-run UI. This phase fills that gap — five new
stories (HS-4-02..05 + DoD) of net-new code, with one audit
story (HS-4-01) covering the pre-existing surfaces by integration
test so the phase exits with full WFS-01 coverage rather than
just the configurability half.

## Active risks

1. **Block-config validation drift between API and CLI.** The CLI has `holdspeak dictation blocks validate`; the new API needs to surface the same `BlockConfigError` shape. Mitigation: have both call `load_blocks_yaml` directly; do not duplicate validation logic.
2. **Atomic write races on `~/.config/holdspeak/blocks.yaml`.** A long-running web runtime + a CLI invocation could write simultaneously. Mitigation: `WFS-CFG-006` requires temp-and-rename atomicity; document that the controller's pipeline-cache invalidation already happens via `apply_runtime_config()` on settings save.
3. **Project KB schema is user-defined.** `<root>/.holdspeak/project.yaml` has no schema today (kb.* keys are arbitrary). Mitigation: HS-4-03 keeps the editor schema-less (any string-valued top-level key under `kb`) — locking it down to a schema is a separate phase.
4. **UI complexity outgrowing `static/dashboard.html` + `static/history.html`.** Today the web UI is two static HTML files with vanilla JS. Adding 4 new editor panels + a dry-run preview will push that. Mitigation: keep the new panels as additive sections; do not introduce a JS framework. If complexity demands, defer to a phase 5.

## Decisions made (this phase)

- 2026-04-26 — Phase canon is `docs/PLAN_PHASE_WEB_FLAGSHIP_RUNTIME.md` with §5.5 amendment (WFS-CFG-001..007). Original WFS-* requirements remain unchanged; this phase covers them via HS-4-01's audit story.
- 2026-04-26 — Phase shape pivoted from initial 8-story proposal to 6-story shape after audit revealed half of the original cut was already built. HS-4-01 absorbs the original WFS-R-001/R-002/R-003 + WFS-C-001..003 work as "verify by test" rather than re-building.
- 2026-04-26 — Configurability writes are temp-and-rename atomic per WFS-CFG-006. No filesystem locks beyond what `os.replace` guarantees.
- 2026-04-26 — Project-KB schema stays user-defined / open. HS-4-03 ships a free-form key/value editor under the `kb.*` namespace; locking it down is a candidate for a later phase if the user finds friction.

## Decisions deferred

- Whether the per-project blocks editor (`WFS-CFG-002`) should support multiple project roots in a single session. HS-4-02 will scope to "the currently-detected project root" — switching projects mid-session means relaunching `holdspeak` from a different cwd. If dogfood reveals this is annoying, a follow-up story can add a project-switcher.
- Whether the dry-run UI should render a syntax-highlighted diff between `raw_text` and `final_text` when the kb-enricher fires. HS-4-05 ships a plain-text trace first; visual diff is a polish story.
- MIR profile/override UI overhaul — explicitly out of this phase; revisit in a phase 5 if needed.
