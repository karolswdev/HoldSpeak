# Cadence Phase 6 — Stale-loop escalation + end-of-day closure

**Status:** done (built + tested; 171 cadence/web tests green, web bundle builds). **Start here:**
`../README.md`. Builds on Phases 1–5 (merged).

**Last updated:** 2026-06-28 (Phase 6 shipped: escalation severity + the EOD closeout ritual across
CLI/web/Telegram + a batch-apply + a history view).

## Objective

Add *pressure* (without spam) and a *closure ritual*. A loop that survives several nudges/days
escalates so it stops being ignorable; at end of day, every open loop comes with a recommended cheap
decision (close / file / snooze / kill / delegate) so clearing the board is a batch of one-taps.

## What shipped

- **Escalation** (`cadence/closeout.py` `escalation_severity`): `quiet | normal | persistent |
  escalated`, by `nudge_count` (≥3 / ≥6) or age (≥2d / ≥4d); `needs_review` is always `quiet`.
- **Closeout** (`build_closeout`): groups the open loops with a deterministic recommendation each —
  `agent_question`→reply, `proposal`→approve, `needs_review`→review, escalated+unowned→**kill**,
  unowned→delegate, owned+stale→file, persistent→file, else→snooze. `render_closeout_text`.
- **Delegate semantics** + `apply_decision(db, loop_id, action)` — the lifecycle-only batch primitive
  (snooze/kill/close/done/delegate); refuses unknown actions / missing loops. No external side effect.
- **Surfaces:** `GET /api/cadence/closeout`, `POST /api/cadence/closeout/apply` (batch),
  `GET /api/cadence/history` (recent nudges via the new `CadenceRepository.list_nudges`); `holdspeak
  cadence closeout [--json]`; Telegram `/closeout`; and the `/cadence` page gained a **Closeout**
  section (recommendations with the recommended-action badge + severity ring + one-tap apply) and a
  **History** list.

## Stories

| ID | Title | Status |
|----|-------|--------|
| CAD-6-01 | Escalation severity (`escalation_severity`) | done |
| CAD-6-02 | The closeout builder + recommendations (`build_closeout`) | done |
| CAD-6-03 | Delegate semantics + `apply_decision` + the batch-apply route | done |
| CAD-6-04 | History: `list_nudges` + `GET /api/cadence/history` | done |
| CAD-6-05 | Surfaces: CLI `closeout`, Telegram `/closeout`, the page Closeout + History sections | done |
| CAD-6-06 | Tests: escalation, recommendations, apply, history, the route + CLI | done |

## Exit criteria

- A loop escalates by nudges/age; closeout recommends a cheap decision per loop; batch-apply mutates
  them; history lists recent nudges. All deterministic, local, off by default.
- `uv run pytest -q` green (171 cadence/web tests); the web bundle builds. **Next: Phase 7 (LLM
  next-best-action, with the real-metal proof that also lights up the Phase-5 brief polish).**
