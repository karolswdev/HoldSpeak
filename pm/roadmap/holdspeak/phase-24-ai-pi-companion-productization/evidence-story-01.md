# HS-24-01 Evidence — AI PI Companion Surface Overview

**Date:** 2026-05-26.
**Story:** [story-01-ai-pi-companion-surface-overview.md](./story-01-ai-pi-companion-surface-overview.md).

## Implementation Evidence

- Added `Companion` to the existing HoldSpeak portal top navigation.
- Added `/companion` as an Astro-built portal page, served by
  `MeetingWebServer`.
- Added `web/src/scripts/companion-app.js` to poll `/api/companion/status`
  every 3 seconds.
- Kept the surface read-only. It exposes selected target, waiting sessions,
  confidence/transport, AI PI connection, runtime state, and readiness blockers.
- Added a smoke test for `/companion` and its bundled JavaScript markers.

## Build

Command:

```bash
npm run build
```

Observed output:

```text
23:02:32   ├─ /companion/index.html (+2ms)
23:02:32 ✓ Completed in 29ms.
23:02:32 [build] 8 page(s) built in 888ms
23:02:32 [build] Complete!
```

## Tests

Command:

```bash
.venv/bin/python -m pytest tests/integration/test_web_server.py::TestCompanionUiSmoke tests/integration/test_web_server.py::TestCompanionStatusEndpoint -q
```

Observed output:

```text
....                                                                     [100%]
4 passed in 0.62s
```

## Live Runtime Check

The web runtime was restarted from the local checkout on port `34999`, then the
new page and companion status were queried.

Command:

```bash
curl -s -D - http://127.0.0.1:34999/companion -o /tmp/holdspeak-companion.html
curl -s http://127.0.0.1:34999/api/companion/status | jq '{status, runtime: .runtime.status, voice_state: .runtime.voice_state, agent_waiting: .agent.awaiting_response, sessions: .agent.sessions.count, blockers}'
```

Observed output:

```text
HTTP/1.1 200 OK
content-type: text/html; charset=utf-8

{
  "status": "ok",
  "runtime": "ok",
  "voice_state": "idle",
  "agent_waiting": false,
  "sessions": 0,
  "blockers": [
    "no_agent_waiting",
    "text_injection_unavailable"
  ]
}
```

Browser-level smoke check:

```bash
google-chrome --headless --disable-gpu --no-sandbox --virtual-time-budget=5000 --dump-dom http://127.0.0.1:34999/companion
```

Observed DOM markers after JavaScript execution:

```text
No reply target
1 connected
0 sessions
No selected waiting session
No waiting sessions
No agent waiting
Text injection unavailable
```

## Result

HS-24-01 closes the first productization gap: the existing HoldSpeak web portal
now has a first-class, read-only AI PI Companion surface. HS-24-02 can add
selection, dismissal, pinning, and stale-session controls on top of this view.
