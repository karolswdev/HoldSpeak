# Phase 27 — Ubiquitous plugins + spoken-meeting e2e: Final Summary

**Opened:** 2026-06-01 (scaffolded) · first ship 2026-06-01 (HS-27-01).
**Closed:** 2026-06-01.
**Chunks shipped:** 5 / 5 (HS-27-01 … HS-27-05).

## Goal — was it met?

> Flip the highest-value `DeterministicPlugin` stubs to real LLM-backed plugins —
> the ones useful on almost every meeting, not niche ones — and prove the whole
> stack with a real spoken-meeting end-to-end harness: a mock meeting synthesized
> with `say`, transcribed by Whisper, routed through MIR, processed by the real
> plugins against the live `.43` LLM, persisted, and rendered in the web UI,
> captured as screenshots.

**Met.** Three ubiquitous plugins went real this phase (`action_owner_enforcer`,
`decision_capture`, `requirements_extractor`), joining phase 16's
`mermaid_architecture` — **four real plugins, ten stubs**. The spoken-meeting e2e
exists, runs against real endpoints, and exercises all four real plugins, ending
in a refreshed `/history` screenshot. Breadth (more real plugins) + confidence (a
watchable e2e) both delivered.

## Exit criteria (re-run against evidence)

- [x] At least the ubiquity champion (`action_owner_enforcer`) ships a real,
      non-stub `run()` meeting all four Appendix-A bars — HS-27-01
      (`evidence-story-01.md`). (In the end three did.)
- [x] A spoken-meeting e2e harness exists and runs against real endpoints
      (`say` → Whisper → real plugin chain → persisted artifacts → ≥1 web
      screenshot), opt-in and skips cleanly when prerequisites are absent —
      HS-27-02 (`evidence-story-02.md`; screenshot in `evidence/`).
- [x] Every plugin flipped to real this phase is ✅ in the RFC reality-status
      table; the rest stay ⚠️ — HS-27-05 (this commit; `docs/PLAN_ARCHITECT_PLUGIN_SYSTEM.md`).
- [x] No regressions: full sweep `uv run pytest -q --ignore=tests/e2e/test_metal.py`
      green (**1939 passed, 14 skipped**, up from 1902/13 at phase-16 close); the
      new e2e is excluded from the default sweep (own `spoken_e2e` marker).
- [x] `final-summary.md` records which plugins shipped, the e2e posture, and the
      handoff for the next plugin-rollout phase — this file.

## Stories shipped

| ID | Story | Evidence |
|---|---|---|
| HS-27-01 | `action_owner_enforcer` — real run (ubiquity champion) | evidence-story-01.md |
| HS-27-02 | Spoken-meeting e2e harness (`say` → pipeline → screenshots) | evidence-story-02.md |
| HS-27-03 | `decision_capture` — decisions + open questions (net-new) | evidence-story-03.md |
| HS-27-04 | `requirements_extractor` — real run (typed requirements) | evidence-story-04.md |
| HS-27-05 | RFC reality-check refresh + phase exit | this summary |

## Cut / deferred

None. The phase-04 doc flagged `requirements_extractor` as cuttable if budget ran
out; it shipped. No stories were dropped or descoped.

## Plugin parse-quality on live `.43` Q6 (handoff data)

Each real plugin was exercised against the live endpoint (direct call + the spoken
e2e). On clean, on-topic transcripts all four parsed first-try; none demoted to
their failure shape in observed runs. The structured-JSON-in-a-fence prompt shape
is reliable on Q6 — the next rollout phase can assume it rather than re-proving it
per plugin. Notably, on a **natural, implicit** conversation (the HS-27-04 e2e
script — nobody reads out a list) the plugins still inferred a sensible
architecture diagram, typed requirements, decisions/open-questions, and
owned/unowned action items.

## Surprises / lessons

- **Test the real wiring, not just an injected override.** The spoken e2e caught
  that `register_builtin_plugins` built a bare `MeetingIntel()` (module defaults),
  so in the real runtime plugins never used the `.43` config and silently returned
  their failure shape. Fixed by `build_configured_meeting_intel()` (`fe9c0e8`).
  Unit tests with an `intel_call` override would never have surfaced this.
- **Every text-output plugin ships a structured web render — never the raw
  `body_markdown` path.** `/history` originally dumped `action_items` as a
  collapsed plain-text blob; the fix was a structured render. `decision_capture`
  and `requirements_extractor` shipped their structured renders up front because
  of this lesson.
- **No routing ripple when the ID is already in a base chain.** `decision_capture`
  was net-new → added to the balanced base chain → rippled `test_intent_dispatch`
  + two full-pipeline stub unions. `requirements_extractor` was *already* routed
  (balanced + architect), so flipping the stub to real changed nothing about the
  dispatched chain — zero routing-test churn. Worth knowing for the next batch:
  net-new IDs ripple; flipping an already-routed stub does not.
- `MeetingState.started_at` must be a **naive** datetime — the codebase's duration
  math uses `datetime.now()`.

## Asset / test posture

- **Real plugins:** `holdspeak/plugins/builtin/{mermaid_architecture,
  action_owner_enforcer,decision_capture,requirements_extractor}.py`.
- **Synthesis bodies:** `diagram`, `action_items`, `decisions`, `requirements` —
  per-type branches in `synthesis.py` (other bodies byte-for-byte unchanged). The
  in-file TODO stands: once a *fifth* custom body lands, extract a per-type
  renderer registry instead of branching.
- **Web render:** `web/src/pages/history.astro` + `web/src/scripts/history-app.js`
  render diagram (SVG), action-items (checklist), decisions (two lists), and
  requirements (typed list) from `structured_json`. `holdspeak/static/_built/` is
  gitignored — rebuild with `(cd web && npm run build)`.
- **Spoken e2e:** `tests/e2e/test_spoken_meeting_e2e.py`, opt-in via
  `HOLDSPEAK_SPOKEN_E2E=1 uv run pytest -q -m spoken_e2e -s`; module-skips
  otherwise and skips cleanly if `say` / scipy / Playwright+Chromium / `.43` /
  Whisper are absent. Playwright is still a **transient install** (not in
  `pyproject.toml`) — an open question carried forward. Latest evidence:
  `evidence/spoken_meeting_artifacts.png`.

## Handoff to the next plugin-rollout phase

The remaining **ten** stubs — `adr_drafter`, `milestone_planner`,
`dependency_mapper`, `scope_guard`, `customer_signal_extractor`,
`incident_timeline`, `risk_heatmap`, `stakeholder_update_drafter`,
`runbook_delta`, `decision_announcement_drafter` — are the long tail for a later
phase. The pattern is fully trodden (see HS-27-04's evidence for the step list):
real plugin → `_REAL_PLUGINS` → `_ARTIFACT_TYPE_BY_PLUGIN` → structured synthesis
body + `structured_json` → structured web render → unit + synthesis tests → extend
the spoken e2e. Net-new IDs ripple the routing tests; already-routed stubs do not.
Consider the per-type renderer-registry refactor when the fifth body lands, and
deciding Playwright's home in `pyproject.toml` (a dev/e2e extra).
