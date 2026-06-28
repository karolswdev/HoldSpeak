# Cadence Phase 3 — Agent-blocker push

**Status:** done (built + tested; 141 cadence/web tests green, web bundle builds). **Start here:**
`../README.md`. Builds on Phases 1–2 (merged).

**Last updated:** 2026-06-28 (Phase 3 shipped: awaiting agent sessions → top loops + a reply
delivered into the agent's terminal from the cadence page, never autonomous).

## Objective

The highest-leverage cadence signal: when a coding agent (Claude/Codex) is **awaiting your
response**, surface it as a loop with the question + its context, and let you **reply from the
cadence surface** — the reply delivered into the agent's tmux pane via the existing transport. This
is the one place cadence performs a (user-initiated, never autonomous) delivery, and it does so
through the existing seam **outside** the cadence package (so the no-side-effects guard stays green).

## Design decisions

- **Read, don't capture.** The collector reads awaiting sessions via
  `agent_context.list_recent_awaiting_agent_sessions()` and mirrors them into `agent_question`
  loops (chart §3.2: mirror, don't migrate). `source_id = session_id`. Scoring already gives
  `agent_question` the top boost.
- **Delivery lives in the route, not the package.** `POST /api/cadence/loops/{id}/reply` resolves the
  session and calls `tmux_transport.send_text_to_pane(...)` — the existing mechanism. The
  `holdspeak/cadence/` package never imports tmux/subprocess (the Phase-1 guard forbids it). The
  reply is **user-typed and explicit** — never autonomous, never auto-drafted (the LLM draft is
  Phase 7).
- **Honest egress + safety.** A reply leaves the cadence surface for your *local* terminal (tmux on
  this machine) — egress stays `local`. Reply requires a non-empty body and a resolvable pane;
  missing tmux is a clear error, never a silent drop.

## Stories

| ID | Title | Status |
|----|-------|--------|
| CAD-3-01 | Collector: awaiting agent sessions → `agent_question` loops (with context evidence) | done |
| CAD-3-02 | Enrich the `reply_to_agent` next-action with the question + cwd/repo context | done |
| CAD-3-03 | `POST /api/cadence/loops/{id}/reply` — deliver a typed reply via `send_text_to_pane` | done |
| CAD-3-04 | The `/cadence` agent card: a reply composer (textarea + Send) | done |
| CAD-3-05 | Tests: collector over a fake session state; reply route (mocked transport); guard green | done |

## Where we are

**Phase 3 is complete.** The collector's `_collect_agent_questions` mirrors
`list_recent_awaiting_agent_sessions()` into **urgent** `agent_question` loops (the scorer already
ranks them top), each with the question as the title + an `agent_session` evidence ref. The
`reply_to_agent` next-action surfaces the question + where the agent is. `POST
/api/cadence/loops/{id}/reply` delivers a **user-typed** reply into the session's tmux pane via the
existing `send_text_to_pane` transport (the side effect lives in the route, not the package) and
closes the loop; it refuses an empty body / a non-agent loop / a missing pane — never autonomous.
The `/cadence` agent card shows a reply composer. **Proof:** 141 tests green
(`test_cadence_agent` + the full cadence/web-server suites); the Phase-1 no-side-effects guard still
passes; the web bundle builds.

**Next: Phase 4 (Telegram remote presence)** — pairing + a Telegram surface delivering nudges and
receiving decisions, with unpaired-chat rejection and a second-confirm for irreversible actions.

## Exit criteria

- An awaiting Claude/Codex session appears as a top-scored `agent_question` loop with the question
  text + a `agent_session` evidence ref.
- `POST /api/cadence/loops/{id}/reply {text}` delivers into the pane (mocked in tests) and is a no-op
  error for a non-agent loop / empty text / missing pane.
- The `/cadence` agent card shows the question + context + a reply box that drives the route.
- The Phase-1 no-external-side-effects guard still passes (the package stays clean); `uv run pytest
  -q` green; the web bundle builds.
