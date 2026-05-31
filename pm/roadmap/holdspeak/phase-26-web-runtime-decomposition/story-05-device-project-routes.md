# HS-26-05 — Extract Device / Companion / Project Routes

- **Project:** holdspeak
- **Phase:** 26
- **Status:** backlog
- **Depends on:** HS-26-01
- **Unblocks:** HS-26-07
- **Owner:** unassigned

## Problem

The remaining clusters — device health/registry, the companion surface,
project CRUD/briefings, settings, and the WebSocket endpoints — are the last
routes inline in `_create_app()`. Moving them leaves `web_server.py` a thin
assembler.

## Scope

### In

- Move `/api/devices/*` (health/registry; the device-audio WS keeps its PSK
  handshake), `/api/companion/*`, `/api/projects*`, `/api/settings`, and the
  `/ws` broadcast endpoint into their route module(s)
  (`routes/devices.py`, `routes/projects.py`, or grouped).
- After this story, `web_server.py` retains only app assembly + shared
  infrastructure (WebSocketManager, lifespan), no inline route bodies.

### Out

- Callback-bag removal (HS-26-06) and closeout (HS-26-07).
- Any change to the device-audio WS auth.

## Acceptance criteria

- [ ] All remaining domain routes are served from modules; `_create_app()` no
      longer contains inline route handler bodies.
- [ ] Existing device/companion/project/settings/WS tests pass unchanged.
- [ ] Route-inventory diff shows identical paths/methods for the moved set.

## Test plan

- Unit: `uv run pytest -q tests/ -k "web and (device or companion or project or settings or ws)"`.
- Integration: companion status + project list + a `/ws` connect via the runtime.
- Manual: n/a.

## Notes / open questions

- The device-audio WebSocket (`device_audio_ws.py`) already lives outside the
  monolith; confirm it stays wired and unchanged.
