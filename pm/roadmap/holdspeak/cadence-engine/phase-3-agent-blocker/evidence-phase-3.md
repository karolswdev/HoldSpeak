# Evidence — Cadence Phase 3 (agent-blocker push)

**Date:** 2026-06-28. **Branch:** `holdspeak/cadence-phase3-agent`.

## What shipped

| Story | Files | Proof |
|-------|-------|-------|
| CAD-3-01 | `cadence/collector.py` (`_collect_agent_questions`) | `test_cadence_agent.py` (2) |
| CAD-3-02 | `cadence/next_action.py` (enriched `reply_to_agent`) | covered by routes/page |
| CAD-3-03 | `web/routes/cadence.py` (`POST /loops/{id}/reply`) | `test_cadence_agent.py` (2) |
| CAD-3-04 | `web/src/scripts/cadence-app.js` + `cadence.astro` (reply composer) | bundle builds |
| CAD-3-05 | the tests above + the guard | 8 green incl. guard |

## The capability

- **Collector** mirrors `agent_context.list_recent_awaiting_agent_sessions()` into **urgent**
  `agent_question` loops keyed by `session_id`, with the question as the title and an `agent_session`
  evidence ref. The scorer's top `agent_question` weight makes a blocked agent the #1 loop
  (`test_collector_projects_awaiting_agent_as_top_loop`). When the agent stops awaiting, its loop
  closes on the next collect (`test_answered_agent_closes_its_loop_on_recollect`).
- **Reply route** `POST /api/cadence/loops/{id}/reply {text}` resolves the session, delivers the
  **user-typed** reply into its tmux pane via the existing `send_text_to_pane`, then closes the loop.
  It refuses an empty body (400), a non-agent loop (400), and a missing pane/session (409) — and
  delivers nothing in those cases (`test_reply_rejects_empty_and_non_agent_and_missing_pane`). Never
  autonomous: the reply is only ever the explicit text the user submitted.
- **Page** — agent cards render a reply textarea + Send that drives the route.

## Trust boundary held

The delivery side effect lives in the **route** (`send_text_to_pane`); the `holdspeak/cadence/`
package only *reads* sessions. The Phase-1 `test_cadence_package_has_no_external_side_effects` guard
still passes (no tmux/subprocess/network in the package). Egress stays `local` (the reply goes to a
terminal on this machine).

## Proof

- `uv run pytest -q tests/unit/test_cadence_*.py tests/integration/test_cadence_*.py
  tests/integration/test_web_server.py` → **141 passed.**
- `cd web && npm run build` → 15 pages (the `/cadence` page + the reply composer compile).
