# HS-26-05 — Extract Device / Companion / Project Routes

- **Project:** holdspeak
- **Phase:** 26
- **Status:** done
- **Depends on:** HS-26-01
- **Unblocks:** HS-26-07
- **Owner:** Claude (agent)

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

- [x] All remaining domain routes are served from modules; `_create_app()` no
      longer contains inline route handler bodies.
- [x] Existing device/companion/project/settings/WS tests pass unchanged.
- [x] Route-inventory diff shows identical paths/methods for the moved set.

## Test plan

- Unit: `uv run pytest -q tests/ -k "web and (device or companion or project or settings or ws)"`.
- Integration: companion status + project list + a `/ws` connect via the runtime.
- Manual: n/a.

## Notes / open questions

- The device-audio WebSocket (`device_audio_ws.py`) already lives outside the
  monolith; confirm it stays wired and unchanged.
- **Resolved:** device-audio WS stays registered in `_create_app`, unchanged.
- **Shipped as 3 modules**: `pages.py` (7 HTML routes), `system.py` (6: device-
  health, runtime/companion status, settings, `/ws`), `projects.py` (13). 6
  module-level helpers relocated. `web_server.py` **1817 → 532** (original 5658,
  −91%); `_create_app` is now a thin assembler (middleware + lifespan + mounts +
  `include_router` only). Relocation bug (page `__file__` path) caught by the full
  suite and fixed via `_HOLDSPEAK_DIR`. See `evidence-story-05.md`.
