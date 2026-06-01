# HS-27-05 — RFC reality-check refresh + phase exit

- **Project:** holdspeak
- **Phase:** 27
- **Status:** done
- **Depends on:** HS-27-01..04 (whichever shipped)
- **Unblocks:** none (phase exit)
- **Owner:** unassigned

## Problem

Closes Phase 27. The parent RFC's reality-status table (added in HS-16-05) must
be refreshed so the plugins shipped this phase flip ⚠️ → ✅, and the phase needs
its `final-summary.md`. Mirrors HS-16-05.

## Scope

### In

- Update `docs/PLAN_ARCHITECT_PLUGIN_SYSTEM.md`: flip every plugin shipped this
  phase to ✅ in the "Reality status" table; keep the rest ⚠️. Note
  `decision_capture` if added (new row).
- Write `final-summary.md` per `roadmap-builder.md` §2.5: dates, chunks shipped,
  goal-met assessment, exit-criteria re-run, stories table, cut/deferred stories
  (e.g. `requirements_extractor` if deferred), surprises/lessons (esp. anything
  the spoken e2e revealed), handoff to the next plugin-rollout phase (the
  remaining stub long-tail), asset/test posture.
- Reference the HS-27-02 e2e screenshots as phase evidence.
- Freeze `current-phase-status.md` (closing line + immutable).
- Update `pm/roadmap/holdspeak/README.md`: "Last updated", phase-27 row → done,
  "Current phase" → next non-done phase.

### Out

- Any remaining stub long-tail (incident/runbook/stakeholder/customer-signal/
  milestone/dependency/scope/risk) — explicitly handed to the next phase.

## Acceptance criteria

- [x] RFC reality-status table reflects what actually shipped this phase.
- [x] `final-summary.md` exists, conforms to §2.5, references the e2e evidence.
- [x] `current-phase-status.md` frozen; README phase-27 row → done + Current
      phase repointed.
- [x] Every Phase-27 exit-criterion checked or marked deferred-with-reason.
- [x] Full sweep green; the spoken e2e remains opt-in/excluded.

## Test plan

- No new test code. Regression sweep `uv run pytest -q --ignore=tests/e2e/test_metal.py`;
  record the count delta in `final-summary.md`.

## Notes / open questions

- The next plugin-rollout phase picks up the remaining stubs; this summary should
  hand it a per-plugin parse-quality note from whatever shipped here (the Phase-16
  pattern: record real `.43` parse-success per plugin).
