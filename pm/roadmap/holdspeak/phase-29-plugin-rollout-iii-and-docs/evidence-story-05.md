# HS-29-05 Evidence — RFC reality-check refresh + phase exit

**Date:** 2026-06-01.
**Story:** [story-05-phase-exit.md](./story-05-phase-exit.md).

## What shipped

**RFC reality-status table** (`docs/PLAN_ARCHITECT_PLUGIN_SYSTEM.md`): heading →
"phase 29 close — rollout complete"; **all fourteen plugins ✅, zero ⚠️**, each
annotated with its shipping story + artifact type. The note records that the
invariant is enforced by `test_no_deterministic_stub_remains`, that the e2e covers
ten plugins (incident/comms via direct live checks), and reframes the follow-on as
the **next frontier** (authoring guide / packs / actuators), not stubs.

**`final-summary.md`** per `roadmap-builder.md` §2.5: dates, 5/5 chunks, goal-met,
exit-criteria re-run, stories table, no cuts, per-plugin `.43` Q6 parse-quality for
the seven, surprises/lessons (theme-grouped chunks, the spoken-e2e ceiling, the
no-stubs guard), final asset/test posture, and the next-frontier handoff.

**`current-phase-status.md`** frozen with a closing line; phase marked done.

**`README.md`** (roadmap): phase-29 row → done; "Last updated" + "Current phase"
repointed.

## Regression sweep

```bash
uv run pytest -q --ignore=tests/e2e/test_metal.py
# 2062 passed, 14 skipped   (phase-28 close was 1978 passed, 14 skipped)
```

The spoken e2e remains opt-in (`spoken_e2e` marker) and excluded from the default
sweep; it exercises ten of the fourteen real plugins.

## Exit criteria

- [x] RFC reality-status table: fourteen ✅, zero ⚠️.
- [x] `final-summary.md` exists, conforms to §2.5.
- [x] `current-phase-status.md` frozen; README phase-29 row → done + Current phase repointed.
- [x] Every Phase-29 exit-criterion checked (see `final-summary.md`).
- [x] Full sweep green; the spoken e2e remains opt-in/excluded.

## Result

Phase 29 closed, 5/5 — and the plugin rollout is complete: **fourteen real
plugins, zero stubs**, every one producing a structured artifact rendered in
`/history`, the public README documenting the system, and the RFC reflecting
reality. Ready to push.
