# HS-28-05 — RFC reality-check refresh + phase exit

- **Project:** holdspeak
- **Phase:** 28
- **Status:** backlog
- **Depends on:** HS-28-01..04 (whichever shipped)
- **Unblocks:** none (phase exit)
- **Owner:** unassigned

## Problem

Closes Phase 28. The parent RFC's reality-status table must flip the plugins
shipped this phase ⚠️ → ✅, and the phase needs its `final-summary.md`. Mirrors
HS-16-05 / HS-27-05.

## Scope

### In

- Update `docs/PLAN_ARCHITECT_PLUGIN_SYSTEM.md`: flip every plugin shipped this
  phase to ✅ in the "Reality status" table (counts: N real / M stub); keep the
  rest ⚠️.
- Write `final-summary.md` per `roadmap-builder.md` §2.5: dates, chunks shipped,
  goal-met assessment, exit-criteria re-run, stories table, cut/deferred stories,
  per-plugin `.43` Q6 parse-quality, surprises/lessons (esp. anything the registry
  refactor or the new structured shapes revealed), handoff to the next
  plugin-rollout phase (the remaining stub long-tail), asset/test posture.
- Reference the spoken-e2e screenshots as phase evidence.
- Freeze `current-phase-status.md` (closing line + immutable).
- Update `pm/roadmap/holdspeak/README.md`: "Last updated", phase-28 row → done,
  "Current phase" → next non-done phase.

### Out

- The remaining stub long-tail (`dependency_mapper`, `scope_guard`,
  `customer_signal_extractor`, `incident_timeline`, `runbook_delta`,
  `stakeholder_update_drafter`, `decision_announcement_drafter`) — explicitly
  handed to the next phase.

## Acceptance criteria

- [ ] RFC reality-status table reflects what actually shipped this phase.
- [ ] `final-summary.md` exists, conforms to §2.5, references the e2e evidence.
- [ ] `current-phase-status.md` frozen; README phase-28 row → done + Current
      phase repointed.
- [ ] Every Phase-28 exit-criterion checked or marked deferred-with-reason.
- [ ] Full sweep green; the spoken e2e remains opt-in/excluded.

## Test plan

- No new test code. Regression sweep `uv run pytest -q --ignore=tests/e2e/test_metal.py`;
  record the count delta in `final-summary.md`.

## Notes / open questions

- Hand the next phase a per-plugin parse-quality note (Phase-16/27 convention).
- If the registry refactor (HS-28-01) made adding bodies trivial, say so — it
  changes the cost estimate for the remaining seven stubs.
