# CAD-1-03 — Stale-scoring v1 (deterministic, explainable)

- **Program:** cadence-engine · **Phase:** 1 · **Status:** todo
- **Depends on:** CAD-1-01, CAD-1-02. **Unblocks:** 1-04 (the tick orders by score), 1-05.

## Problem

Loops need a deterministic priority so the engine pushes the right one and the user can see *why*.
No LLM (chart: baseline is deterministic).

## The design

`holdspeak/cadence/scoring.py` → `score_loop(loop, *, now, signals) -> ScoreBreakdown`. Pure
function, no I/O — takes the loop + a small `signals` struct the collector assembles (recent
activity for the project, source weight, recurrence count). Implements the design §7.1 additive
heuristic:

```
stale_score = age_weight + priority_weight + source_weight + recurrence_weight
            + accepted_action_weight  − recent_activity_weight − snooze_weight − dismissal_weight
```

Suggested initial weights (design §7.1, tunable constants in one place):

| Signal | Effect |
|--------|--------|
| accepted action not executed | high boost |
| unowned action | medium boost |
| appears across related meetings | high boost |
| related activity touched today | boost (the loop is "alive") |
| recently dismissed same loop | suppress |
| snoozed | suppress until due |
| `needs_review` (low confidence) | suppress (never a push) |

Returns a **`ScoreBreakdown`** (the total **and** the per-signal contributions) so every nudge is
explainable — the breakdown is what the future debug payload + the "why" line render. Persist the
total onto `cadence_loops.stale_score` via the repo; keep the breakdown ephemeral (recomputed).

## Scope

- **In:** the pure scorer + `ScoreBreakdown`; the weight constants; persisting the total.
- **Out:** policy/quiet-hours scheduling (1-04), agent-blocker weight (Phase 3 adds the huge boost),
  any LLM classification (Phase 7).

## Proof / acceptance

- Deterministic: same inputs → same score (no clock/random leakage; `now` is injected).
- An accepted-but-unexecuted action outranks an unowned action outranks a fresh low-priority loop.
- A snoozed or `needs_review` loop scores below any active loop.
- The breakdown sums to the total.

## Test plan

`tests/unit/test_cadence_scoring.py` — table-driven cases for each weight + ordering invariants +
breakdown-sums-to-total + determinism (inject `now`). `uv run pytest -q tests/unit/test_cadence_scoring.py`.
