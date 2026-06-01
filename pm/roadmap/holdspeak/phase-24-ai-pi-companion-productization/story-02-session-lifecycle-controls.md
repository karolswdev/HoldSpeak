# HS-24-02 — Session Lifecycle Controls (web companion)

- **Project:** holdspeak
- **Phase:** 24
- **Status:** backlog (ready to pick up — this is the recommended resume point)
- **Depends on:** HS-24-01 (read-only `/companion` surface)
- **Unblocks:** HS-24-03, HS-24-05
- **Owner:** unassigned

> **Pickup note (written 2026-06-01 as a handover).** This story is **software-
> only** — it needs no physical AI PI hardware, so it is the right resume point
> while hardware dogfood (HS-24-03/04/05) is blocked on in-person access. It also
> rides the clean Phase 26 web seam: the companion routes now live in
> `holdspeak/web/routes/system.py` (`/api/companion/status`) +
> `holdspeak/web/routes/pages.py` (`/companion`).

## Problem

The `/companion` surface (HS-24-01) is **read-only**: the user can see waiting
Claude/Codex sessions but cannot act on them without editing
`~/.config/holdspeak/agent_sessions.json` or using the physical device. When
several sessions are waiting — or a stale/wrong one is selected — the device
feels risky. The user needs to **select**, **dismiss**, **pin**, and **clear
stale** sessions from the browser, mutating the *same* selected-target state the
physical AI PI reads.

## Scope

### In

- Web controls on `/companion` to, for a waiting session:
  - **Select** it as the device's active target (set the selected-response key).
  - **Dismiss** it (clear its captured response / drop it from the waiting set).
  - **Pin** / unpin it (keep it selected; exempt from auto-cycle + stale pruning).
  - **Clear stale** sessions in one action.
- Surface a **stale** marker in `/api/companion/status` (age vs a threshold) so
  the UI can badge stale sessions.
- New `agent_context` functions for the select-specific + pin operations (see
  "Implementation map").

### Out

- Physical-display affordances for confidence/unavailable targets (→ HS-24-03).
- Push/repaint cadence (→ HS-24-04).
- Live multi-session hardware dogfood (→ HS-24-05).
- Autonomous replies; cross-network; new hardware (phase boundaries).

## Implementation map (grounded — read before starting)

**State model** — `holdspeak/agent_context.py`, file-backed at
`AGENT_CONTEXT_FILE = ~/.config/holdspeak/agent_sessions.json`. The `AgentSession`
dataclass (frozen) keys on `(agent, session_id)`; relevant fields:
`awaiting_response`, `updated_at`, `last_assistant_text`, `tmux_pane`, `summary`,
`event_count`. Existing functions to build on:

- `list_recent_awaiting_agent_sessions(max_age_seconds=..., limit=...)` — the
  overview list (already feeds `/api/companion/status`).
- `get_selected_awaiting_agent_session(...)` / `select_next_awaiting_agent_session(...)`
  — read / cycle the *selected* target via a selected-response key in the state.
- `clear_agent_session_response(agent=, session_id=, project_root=, max_age_seconds=)`
  — already used by `/api/dictation/agent-context/clear`; the basis for **dismiss**.

**New `agent_context` functions to add (with unit tests):**
- `select_awaiting_agent_session(agent, session_id, *, state_path=None)` — set the
  selected-response key to a *specific* waiting session (today only "cycle to next"
  exists). Return the resulting selected `AgentSession | None`.
- `pin_agent_session(agent, session_id, pinned=True, *, state_path=None)` — store a
  `pinned` flag (in the session record or a top-level `pinned_key`); a pinned
  session stays selected and is exempt from stale pruning / auto-cycle. Reflect
  `pinned` in `AgentSession` (+ `to_dict`).
- (Optional) `clear_stale_agent_sessions(max_age_seconds, *, state_path=None)` —
  bulk-drop non-pinned sessions older than the threshold; return count cleared.

**Web routes** — add to `holdspeak/web/routes/system.py` right beside
`api_companion_status` (the companion surface lives there post-Phase-26). **Call the
`agent_context` functions directly** (module import inside the handler), exactly as
`routes/dictation.py` already does for `clear_agent_session_response` — *no
`WebContext` / `WebRuntimeCallbacks` change is needed* (this is file-backed module
state, not server-instance state):

- `POST /api/companion/select`   body `{agent, session_id}` → `select_awaiting_agent_session`.
- `POST /api/companion/dismiss`  body `{agent, session_id}` → `clear_agent_session_response`.
- `POST /api/companion/pin`      body `{agent, session_id, pinned: bool}` → `pin_agent_session`.
- `POST /api/companion/clear-stale` body `{max_age_seconds?}` → `clear_stale_agent_sessions`.
  (Pick REST shapes consistent with the existing `/api/...` handlers; return the
  refreshed companion payload or `{success: true, ...}`.)

Then extend `api_companion_status` to include a `stale: bool` (and/or
`age_seconds`) per session so the frontend can badge them.

**Frontend** — `/companion` is an **Astro-built page** (source in `web/`, built into
`holdspeak/static/_built/companion/`; the route in `routes/pages.py` just serves
the built HTML). Adding buttons means editing the Astro/TS source under `web/` and
running `(cd web && npm run build)`. Keep it consistent with the design system used
by the other rebuilt pages. **Note:** `static/_built/` is gitignored and built on
demand — page-content tests that assert on bundled strings need a fresh build.

## Acceptance criteria

- [ ] From `/companion`, the user can select / dismiss / pin / clear-stale a
      waiting session without touching state files; the change is reflected in the
      same selected-target state the physical device reads.
- [ ] `/api/companion/status` marks stale sessions; pinned sessions are exempt
      from stale-clear and auto-cycle.
- [ ] New `agent_context` functions covered by unit tests over a tmp state file.
- [ ] New endpoints covered by integration tests (TestClient) over a tmp state
      file — select/dismiss/pin/clear-stale mutate state and return expected JSON.
- [ ] Route-inventory diff: only the **new** companion routes added; nothing else
      changes. Full suite green.

## Test plan

- Unit: `uv run pytest -q tests/ -k "agent_context and (select or pin or stale)"`
  — the new state functions over `tmp_path` state files.
- Integration: a `MeetingWebServer(WebRuntimeCallbacks(...))` + `TestClient`
  exercising the new `/api/companion/*` endpoints (mirror
  `tests/integration/test_web_*` setup; **construct via `WebRuntimeCallbacks`** —
  the constructor was collapsed in HS-26-06).
- Full suite as the gate (per Phase 26's lesson — narrow `-k` filters missed real
  bugs three times).
- Manual/dogfood: **out of scope here** — left to HS-24-05 (needs the device).

## Notes / open questions

- Decide whether "dismiss" removes the session record or just clears its
  `awaiting_response`/response (prefer the latter — non-destructive, matches
  `clear_agent_session_response`).
- "Pin" semantics: confirm the physical-device selection logic
  (`get_selected_awaiting_agent_session` / `select_next_awaiting_agent_session`)
  honors a pinned session (it should refuse to auto-cycle away from a pin). Wire
  that when adding `pin_agent_session`.
- Replies stay user-driven (phase decision) — these controls manage *attention/
  selection*, never auto-answer.
