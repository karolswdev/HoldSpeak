# Evidence — Cadence Phase 5 (daily push brief)

**Date:** 2026-06-28. **Branch:** `holdspeak/cadence-phase5-brief`.

## What shipped

| Story | Files | Proof |
|-------|-------|-------|
| CAD-5-01/02 | `cadence/brief.py` (`build_brief`, renderers) | `test_cadence_brief.py` |
| CAD-5-03 | `polish_headline` (gated, fail-closed) | identity / mock-rewrite / fail-closed tests |
| CAD-5-04 | `should_send_daily_brief` + `runtime/cadence.py` `_maybe_push_daily_brief` | trigger tests |
| CAD-5-05 | `web/routes/cadence.py` (`GET /brief`), `commands/cadence.py` + `main.py`, `cadence_telegram.py` (`send_brief`) | route + CLI + Telegram tests |
| CAD-5-06 | `tests/unit/test_cadence_brief.py` + route/Telegram additions | 163 green |

## The brief

`build_brief` ranks the open loops (excluding `needs_review`), attaches each one's prepared
`next_action`, and leads with the #1 move as the headline:

```
Morning Push — 2026-06-28

File an issue: Create issue: watchdog.
  1. Create issue: watchdog  ->  Approve: Create issue: watchdog
  2. File the migration doc   ->  File an issue: File the migration doc

2 open loop(s).
```

- **Deterministic everywhere** (CLI `holdspeak cadence brief`, `GET /api/cadence/brief`, Telegram
  `/brief`) — no model required.
- **First-activity trigger** `should_send_daily_brief` is pure: fires once per day, only after quiet
  hours, never twice (the tick persists `last_sent_date` in a `daily_brief` policy row).
- **The morning push**: the `CadenceMixin` tick sends the brief to paired Telegram chats once per
  day (off unless Telegram is active).

## LLM polish — a tested seam, live wiring deferred (honest)

`polish_headline(brief, llm=…)` rewrites only the headline's *wording*: no-llm is identity, a mock
rewrite sets `generated_by="llm"`, and any llm error is **fail-closed** (the deterministic headline
stays) — all three tested. It is **not yet wired to the live intel provider**; doing so warrants a
real-metal control-vs-treatment proof on the `.43` endpoint
([[feedback_prefer_real_metal_proof]]), bundled with the Phase-7 LLM next-action work. The shipped
brief is the deterministic one and needs no model.

## Proof

- `uv run pytest -q tests/unit/test_cadence_*.py tests/integration/test_cadence_*.py
  tests/integration/test_web_server.py` → **163 passed.**
