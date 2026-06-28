# Cadence Phase 5 — Daily push brief

**Status:** done (built + tested; 163 cadence/web tests green). **Start here:** `../README.md`. Builds
on Phases 1–4 (merged).

**Last updated:** 2026-06-28 (Phase 5 shipped: the deterministic morning brief across CLI/web/Telegram
+ the first-activity push trigger; the LLM-polish seam is tested, live wiring deferred to a
real-metal follow-up).

## Objective

A daily prioritized brief — your highest-leverage move first, then the top prepared next-actions —
delivered on first activity in the morning. Deterministic and useful **without** an LLM; an LLM may
polish only the headline's *wording*, behind a gate, fail-closed.

## What shipped

- **`cadence/brief.py`** — `build_brief(db, now, limit)` ranks open loops (excludes `needs_review`),
  attaches each one's prepared `next_action`, and leads with the #1 move as the headline.
  `render_brief_markdown` / `render_brief_text`. `should_send_daily_brief(now, last_sent_date,
  earliest_hour)` is the **pure first-activity trigger** (once per day, only after quiet hours).
- **`polish_headline(brief, llm=…)`** — optionally rewrites the headline's wording via an injected
  LLM; **fail-closed** (no llm / any error ⇒ the deterministic headline stays); never changes which
  loops are chosen.
- **Surfaces:** `GET /api/cadence/brief`; `holdspeak cadence brief [--json]`; Telegram `/brief` now
  renders the full brief (with action buttons on the #1 loop) via `send_brief`.
- **The morning push:** the `CadenceMixin` tick calls `_maybe_push_daily_brief` — once per day after
  quiet hours it sends the brief to paired Telegram chats and records `last_sent_date` in a
  `daily_brief` policy row (durable across restarts). Off unless Telegram is active.

## Honest scope

The brief is **deterministic in every surface today** (the shipped product). The `polish_headline`
LLM seam is built and tested in both modes (no-llm identity + a mock rewrite + fail-closed), but it
is **not yet wired to the live intel provider** — doing that calls for a real-metal proof on the
`.43` endpoint (control-vs-treatment, [[feedback_prefer_real_metal_proof]]), bundled naturally with
the Phase-7 LLM next-action work. The deterministic brief needs no model and is fully proven.

## Stories

| ID | Title | Status |
|----|-------|--------|
| CAD-5-01 | `build_brief` (deterministic; top-N + next-actions + headline) | done |
| CAD-5-02 | Renderers (`markdown` / `text`) | done |
| CAD-5-03 | The LLM-polish seam (`polish_headline`, gated, fail-closed, tested) | done |
| CAD-5-04 | The first-activity morning trigger (`should_send_daily_brief` + the tick push) | done |
| CAD-5-05 | Surfaces: web `GET /brief`, CLI `cadence brief`, Telegram `/brief` | done |
| CAD-5-06 | Tests: deterministic, LLM/no-LLM, the trigger, the surfaces | done |

## Exit criteria

- `holdspeak cadence brief` + `GET /api/cadence/brief` + Telegram `/brief` all render the brief with
  the headline + the top moves; deterministic, no model required.
- The trigger fires once per day after quiet hours; never twice (persisted).
- `uv run pytest -q` green (163 cadence/web tests). **Next: Phase 6 (stale-loop + EOD closure).**
