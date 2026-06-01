# Phase 28 — Plugin rollout II: Final Summary

**Opened:** 2026-06-01 (scaffolded) · first ship 2026-06-01 (HS-28-01).
**Closed:** 2026-06-01.
**Chunks shipped:** 5 / 5 (HS-28-01 … HS-28-05).

## Goal — was it met?

> Flip the next batch of `DeterministicPlugin` stubs to real LLM-backed plugins,
> completing the architecture / delivery / risk meeting types: ADRs, milestone
> plans, and risk registers. Lead with a behavior-preserving synthesis refactor so
> adding three new artifact bodies doesn't grow an unmaintainable chain. Each new
> plugin ships a structured `/history` render and is demonstrated in the
> spoken-meeting e2e.

**Met.** `adr_drafter`, `milestone_planner`, and `risk_heatmap` went real, on top
of a renderer-registry refactor that paid down the Phase-27-flagged synthesis
debt. **Seven real plugins, seven stubs.** The spoken e2e exercises all seven on
real endpoints and screenshots them.

## Exit criteria (re-run against evidence)

- [x] Synthesis renderer registry lands behavior-preserving — HS-28-01
      (`evidence-story-01.md`); `test_artifact_synthesis_diagram.py` passed
      unchanged.
- [x] `adr_drafter`, `milestone_planner`, `risk_heatmap` each ship a real,
      non-stub `run()` meeting all four Appendix-A bars — HS-28-02/03/04
      (`evidence-story-02/03/04.md`); each verified live on `.43` Q6.
- [x] Each new artifact type renders structured in `/history` (`adr` records,
      `milestone_plan` list, `risk_register` table with colour-coded level pills).
- [x] The three flipped plugins are ✅ in the RFC reality-status table; the rest ⚠️
      — HS-28-05 (this commit; `docs/PLAN_ARCHITECT_PLUGIN_SYSTEM.md`).
- [x] No regressions: full sweep green (**1978 passed, 14 skipped**, up from
      1939/14 at Phase-27 close); the spoken e2e stays opt-in/excluded and was
      extended to exercise the three new plugins.
- [x] `final-summary.md` records which plugins shipped, per-plugin `.43` Q6
      parse-quality, and the handoff — this file.

## Stories shipped

| ID | Story | Evidence |
|---|---|---|
| HS-28-01 | Synthesis per-type renderer registry (behavior-preserving) | evidence-story-01.md |
| HS-28-02 | `adr_drafter` — real run (ADRs) | evidence-story-02.md |
| HS-28-03 | `milestone_planner` — real run (delivery) | evidence-story-03.md |
| HS-28-04 | `risk_heatmap` — real run (risk register) | evidence-story-04.md |
| HS-28-05 | RFC reality-check refresh + phase exit | this summary |

## Stories cut or deferred

None. All five shipped as scoped. (The status-doc deferred decision — a literal 2D
risk heatmap visual vs a table — resolved to a table for v1, as planned.)

## Plugin parse-quality on live `.43` Q6 (handoff data)

All three new plugins parsed first-try on clean, on-topic transcripts; none
demoted to the failure shape in observed runs (direct calls + the spoken e2e).
Confirmed in live checks: `adr_drafter` drafted accepted + proposed ADRs;
`milestone_planner` extracted a Private-Beta→GA plan with deliverables +
dependencies; `risk_heatmap` surfaced vendor-slip / data-loss / compliance risks
with impact/likelihood/owner. The fenced-JSON prompt shape continues to be
reliable on Q6 (consistent with Phase 27) — the next rollout phase can assume it.
Enum coercion (ADR status, risk levels) absorbed the LLM's occasional synonym
drift (`approved`→accepted, `critical`→high) without failures.

## Surprises and lessons

- **The registry refactor (HS-28-01) paid for itself within the same phase.** After
  it landed, each new artifact body was a `_*_body` helper + a `_render_*` function
  + one registry entry — no dispatch edits, no risk to the other bodies. The three
  plugin stories were near-mechanical because of it. Do the refactor *before* the
  bulk add, not after.
- **Already-routed stubs flip with zero routing-test churn.** All three plugins
  were already in their profile/intent chains (`adr_drafter`→architect,
  `milestone_planner`→delivery, `risk_heatmap`→incident), so flipping stub→real
  changed no dispatched chain. Confirmed: `test_intent_dispatch.py` needed no
  edits across the whole phase. (Contrast Phase 27's `decision_capture`, a net-new
  ID added to the balanced chain, which did ripple.)
- **The spoken e2e is non-deterministic** (real LLM) — one run failed transiently
  mid-phase and passed on retry. It's opt-in and excluded from the default sweep,
  with structural assertions, exactly to contain this. Treat a single red as a
  retry, not a regression.
- **A fixed-overlay modal defeats `full_page` screenshots.** The meeting-detail
  modal scrolls internally, so `page.screenshot(full_page=True)` capped at the
  fold (the decisions/ADR cards fell off-screen). Fixed by measuring
  `.modal-body` `scrollHeight` and growing the viewport to fit before capturing —
  the demo now shows the transcript + all seven artifacts in one frame.

## Final asset / test posture

- **Real plugins (7):** `holdspeak/plugins/builtin/{mermaid_architecture,
  action_owner_enforcer,decision_capture,requirements_extractor,adr_drafter,
  milestone_planner,risk_heatmap}.py`.
- **Synthesis:** `synthesis._ARTIFACT_RENDERERS` registry — body types `diagram`,
  `action_items`, `decisions`, `requirements`, `adr`, `milestone_plan`,
  `risk_register` (+ default). Adding a body = a renderer + a registry entry.
- **Web render:** `web/src/pages/history.astro` + `web/src/scripts/history-app.js`
  render every artifact shape from `structured_json` (never raw `body_markdown`).
  `holdspeak/static/_built/` is gitignored — rebuild with `(cd web && npm run build)`.
- **Spoken e2e:** `tests/e2e/test_spoken_meeting_e2e.py`, opt-in via
  `HOLDSPEAK_SPOKEN_E2E=1 uv run pytest -q -m spoken_e2e -s`; exercises all seven
  real plugins; `EVIDENCE_DIR` points here. Latest evidence:
  `evidence/spoken_meeting_artifacts.png`. Playwright remains a transient install
  (still not in `pyproject.toml` — carried-forward open question).

## Handoff to the next plugin-rollout phase

The remaining **seven** stubs — `dependency_mapper`, `scope_guard`,
`customer_signal_extractor`, `incident_timeline`, `stakeholder_update_drafter`,
`runbook_delta`, `decision_announcement_drafter` — are the long tail for a later
phase. The pattern is fully mechanized: real plugin (copy any of the seven) →
`_REAL_PLUGINS` → `_ARTIFACT_TYPE_BY_PLUGIN` (most already mapped) → a renderer in
`_ARTIFACT_RENDERERS` → structured web render → unit + synthesis tests → extend
the spoken e2e. Net-new IDs ripple the routing tests; already-routed stubs do not.
With the registry in place, each is ~an hour of well-trodden work. Note: the comms
drafters (`stakeholder_update_drafter`, `decision_announcement_drafter`) ride the
`comms` intent chain, and `incident_timeline` / `runbook_delta` the `incident`
chain — all already routed.
