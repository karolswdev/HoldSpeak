# Phase 29 — Complete the plugin rollout + public docs: Final Summary

**Opened:** 2026-06-01 (scaffolded) · first ship 2026-06-01 (HS-29-01).
**Closed:** 2026-06-01.
**Chunks shipped:** 5 / 5 (HS-29-01 … HS-29-05).

## Goal — was it met?

> Flip the remaining seven stubs to real, grouped by meeting theme, and document
> the whole plugin surface publicly. After this phase: fourteen real plugins, zero
> stubs — every registered MIR plugin has a real `run()`, a structured artifact,
> and a `/history` render. The public `README.md` gains a "Meeting intelligence
> plugins" section.

**Met.** All seven remaining stubs went real (delivery/product, incident, comms),
taking the registrar to **fourteen real plugins, zero `DeterministicPlugin`
stubs** — locked by `test_no_deterministic_stub_remains`. The public README now
documents the plugin system. The plugin rollout (Phases 16 → 27 → 28 → 29) is
**complete**.

## Exit criteria (re-run against evidence)

- [x] All seven remaining stubs ship a real, non-stub `run()` (four Appendix-A
      bars); `_REAL_PLUGINS` covers all fourteen IDs; no `DeterministicPlugin`
      left — HS-29-01/02/03, `test_no_deterministic_stub_remains`.
- [x] Each new artifact type renders structured in `/history` — `dependency_map`,
      `scope_review`, `customer_signals`, `incident_timeline`, `runbook_delta`,
      `stakeholder_update`, `decision_announcement`.
- [x] Each new plugin verified live on `.43` Q6 (direct checks in
      `evidence-story-01/02/03.md`).
- [x] `README.md` documents the plugin system (14-row table + how-it-works) —
      HS-29-04.
- [x] RFC reality-status table: fourteen ✅, zero ⚠️ — HS-29-05 (this commit).
- [x] No regressions: full sweep green (**2062 passed, 14 skipped**, up from
      1978/14 at Phase-28 close); the spoken e2e stays opt-in/excluded.
- [x] `final-summary.md` records completion + the next-frontier handoff — this file.

## Stories shipped

| ID | Story | Evidence |
|---|---|---|
| HS-29-01 | Delivery & product plugins (dependency_mapper, scope_guard, customer_signal_extractor) | evidence-story-01.md |
| HS-29-02 | Incident plugins (incident_timeline, runbook_delta) | evidence-story-02.md |
| HS-29-03 | Comms plugins (stakeholder_update_drafter, decision_announcement_drafter) → zero stubs | evidence-story-03.md |
| HS-29-04 | Public README + plugin docs | evidence-story-04.md |
| HS-29-05 | RFC reality-check refresh + phase exit | this summary |

## Stories cut or deferred

None. All five shipped as scoped.

## Plugin parse-quality on live `.43` Q6 (the seven flipped here)

All seven parsed first-try on theme-appropriate transcripts; none demoted to the
failure shape in observed runs. Highlights from the live checks:
`dependency_mapper` mapped 2 edges with notes; `scope_guard` correctly flagged
scope creep among in/out findings; `customer_signal_extractor` classified
request/pain/churn-risk; `incident_timeline` produced a 4-event ordered timeline;
`runbook_delta` produced added/modified/removed; `stakeholder_update_drafter`
produced a full headline + highlights/risks/next-steps; `decision_announcement_drafter`
drafted two audience-targeted announcements. The fenced-JSON + enum-coerce shape
remains reliable on Q6 across all fourteen plugins.

## Surprises and lessons

- **Theme-grouped atomic chunks scaled well.** Grouping the seven into three
  themed commits (delivery/product, incident, comms) kept the PMO cadence honest
  (one done-flip per commit, documented bundling) without seven near-identical
  ceremonies. The renderer registry (HS-28-01) made each plugin a drop-in.
- **The shared spoken e2e has a natural ceiling.** Its one conversation (a product
  kickoff) can exercise ~ten plugins; the incident and comms plugins don't
  naturally fire there. Forcing them in would make the e2e brittle. Resolution:
  the e2e covers the plugins that fit its conversation (now ten); incident/comms
  are verified by **direct live checks** against tailored transcripts + unit
  tests. Honest coverage beats a fragile all-in-one assertion.
- **"No stubs left" needs its own guard.** As each stub flipped, two old tests
  that used "a stub" as a stand-in had to be repointed, then finally reworked once
  none remained. `test_no_deterministic_stub_remains` now encodes the end-state so
  the invariant can't silently regress.
- **The fixed-modal screenshot fix (Phase 28) held** — the demo still captures the
  full meeting-detail modal as plugins were added.

## Final asset / test posture

- **Real plugins (14):** every file in `holdspeak/plugins/builtin/` except the
  `DeterministicPlugin` fallback class (which now has no registered users — kept as
  the registrar's safety net for any future unmapped ID).
- **Synthesis:** `synthesis._ARTIFACT_RENDERERS` — 14 body renderers keyed by
  artifact type (+ default). Adding a body = a renderer + a registry entry.
- **Web render:** `web/src/pages/history.astro` + `web/src/scripts/history-app.js`
  render every artifact shape from `structured_json` (never raw `body_markdown`),
  with the fallback gated behind `hasStructuredRender(artifact)`.
- **Public docs:** `README.md` §"Meeting intelligence plugins" (14-row table).
- **Spoken e2e:** ten plugins, opt-in, `EVIDENCE_DIR` →
  `phase-28-…/evidence/spoken_meeting_artifacts.png`. Playwright still a transient
  install (carried-forward open question).
- **Tests:** full sweep **2062 passed, 14 skipped**.

## Handoff — the next frontier (not stubs)

The built-in rollout is done; there are no stubs left to flip. The next plugin
work is a step up the abstraction ladder:

1. **A public plugin-authoring guide** — the pattern is fully trodden internally
   (RFC + the 14 reference impls); externalize it so others can add plugins.
2. **Plugin packs** — group/distribute plugins; per-project enable/disable.
3. **Actuators** (RFC-disabled today) — external side effects (Jira/Slack/GitHub)
   behind explicit human approval; the RFC's open question #5.
4. **e2e breadth** — a second spoken scenario (an incident retro) so the incident/
   comms plugins get e2e coverage too, not just direct live checks.

Unrelated open tracks remain hardware-gated: Phase 25 (HS-25-07 dogfood), Phase 24
(companion HS-24-03/04/05), Phase 15 (out-and-about, gated on Phase 25).
