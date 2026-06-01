# HS-24-02 Evidence — Session Lifecycle Controls

**Date:** 2026-06-01.
**Story:** [story-02-session-lifecycle-controls.md](./story-02-session-lifecycle-controls.md).

## Implementation Evidence

**State model (`holdspeak/agent_context.py`):**

- Added a `pinned: bool` field to `AgentSession` (+ `from_mapping`/`to_dict`),
  preserved across `ingest_agent_hook_event` so a hook event never silently
  drops a user's pin.
- Pinned sessions are **exempt from the recency cutoff** in
  `_recent_awaiting_sessions_from_state` (a pin is the user's "keep this target"
  signal), and `select_next_awaiting_agent_session` **refuses to auto-cycle off**
  a pinned selection — so the physical device's `agent_next` honors a pin.
- New functions (all `state_path`-injectable, file-locked like their neighbors):
  - `select_awaiting_agent_session(agent, session_id)` — set the selected-response
    key to a *specific* waiting session (vs. the existing cycle-to-next).
  - `pin_agent_session(agent, session_id, pinned=True)` — set/clear the `pinned`
    flag and select the session; does **not** bump `updated_at` (keeps the age
    badge honest).
  - `clear_stale_agent_sessions(max_age_seconds=120)` — non-destructively clear
    (mirrors `clear_agent_session_response`) the captured response of every
    non-pinned awaiting session older than the threshold; returns the count.
  - `DEFAULT_STALE_AGENT_SESSION_SECONDS = 120`.

**Web routes (`holdspeak/web/routes/system.py`):** four new endpoints, each
calling `agent_context` **directly** (no `WebContext`/constructor change, exactly
as the dictation routes do):

- `POST /api/companion/select`      `{agent, session_id}` → 200 `{success, session}` / 404 `unknown_session`.
- `POST /api/companion/dismiss`     `{agent, session_id}` → 200 `{success, session}`.
- `POST /api/companion/pin`         `{agent, session_id, pinned?}` → 200 `{success, session}` / 404.
- `POST /api/companion/clear-stale` `{max_age_seconds?}` → 200 `{success, cleared, max_age_seconds}`.
- Missing `agent`/`session_id` → 400; non-integer `max_age_seconds` → 400.

`api_companion_status` now lists awaiting sessions over a wider overview window
(30 min) while the active reply target stays at 120 s (matching the device path
in `web_runtime.py`), and each item carries `age_seconds`, `stale`, and `pinned`.
The `agent` block reports `overview_max_age_seconds` + `stale_threshold_seconds`.

**Frontend (`web/src/pages/companion.astro` + `companion-app.js`):** per-card
Select / Pin·Unpin / Dismiss buttons, a "Clear stale (N)" action, and Stale /
Pinned badges; controls POST then refresh. The page subtitle was updated off the
"Controls land in HS-24-02" placeholder.

## Build

```bash
cd web && npm run build
```

```text
02:21:01 ▶ src/pages/companion.astro
02:21:01   └─ /companion/index.html (+1ms)
02:21:01 [build] 8 page(s) built in 747ms
02:21:01 [build] Complete!
```

## Tests

New unit tests (`tests/unit/test_agent_context.py`): `select_awaiting_agent_session`
sets a specific target, `pin_agent_session` keeps a target past the recency window,
`select_next` refuses to cycle off a pin, `clear_stale_agent_sessions` skips pinned.

New integration tests (`tests/integration/test_web_server.py::TestCompanionControlEndpoints`):
select/dismiss/pin/clear-stale over a tmp `AGENT_CONTEXT_FILE`, plus 404/400 paths.
The `/companion` page smoke test now asserts the four control endpoints appear in
the bundled JS.

```bash
uv run pytest -q tests/unit/test_agent_context.py
# 34 passed in 0.12s

uv run pytest -q tests/integration/test_web_server.py -k Companion
# 10 passed, 77 deselected in 1.52s
```

Full suite as the gate (per Phase 26's lesson):

```bash
uv run pytest -q --ignore=tests/e2e/test_metal.py
# 1889 passed, 13 skipped in 60.34s
```

`ruff check` on the changed Python files: **All checks passed!**

## Live runtime check (headless, no hardware)

Exercised the real `MeetingWebServer` app via `TestClient` against a tmp state
file: one fresh session (5 s) and one stale session (400 s).

```text
== status items + stale_threshold ==
stale_threshold_seconds: 120
{"sid": "fresh-a", "selected": true,  "pinned": false, "stale": false, "age_seconds": 5}
{"sid": "stale-b", "selected": false, "pinned": false, "stale": true,  "age_seconds": 400}
== pin stale-b -> exempts it; select returns it ==
pinned: True
stale-b now: {"pinned": true, "stale": false, "selected": true}
== clear-stale default 120s (pinned stale-b survives) ==
{"success": true, "cleared": 0, "max_age_seconds": 120}
remaining: ['fresh-a', 'stale-b']
```

This confirms end-to-end: stale badging by age, pin exempting a session from both
the stale badge and `clear-stale`, and pin/select mutating the same selected-target
state the physical device reads. A separate run (sessions aged > 30 min) confirmed
`clear-stale` reaps non-pinned sessions from state even once they age out of the
overview window (`cleared: 1`), and that `select`→unknown returns 404,
missing-field bodies return 400.

## Result

HS-24-02 turns `/companion` from read-only into an **operable** surface: the user
can select / dismiss / pin / clear-stale waiting agent sessions from the browser
without touching `agent_sessions.json`, and the change is reflected in the same
selected-target state the physical AI PI reads. Phase 24 is 2/5.

**Out of scope (by phase boundary):** physical-display affordances (HS-24-03),
push/repaint cadence (HS-24-04), and the live multi-session hardware dogfood
(HS-24-05) — all gated on the physical AI PI being on-site.
