# HS-32-02 — Invert meeting→web-server coupling

**Status:** not-started.

## Goal

Stop `MeetingSession` reaching up into the web layer. Today
`meeting_session.py:1552` calls `self._web_server.broadcast(...)` directly — an
inversion-of-control violation that means a meeting can't run without a web
server. Replace it with an emit/callback the `WebRuntime` observes, mirroring how
`controller.py` wires `MeetingSession` via `on_segment`/`on_intel`/… callbacks.

## Scope

- Add a broadcast/emit callback to `MeetingSession` (e.g. `on_broadcast`), default
  no-op; remove the `self._web_server` reference and any web import.
- `WebRuntime` supplies the callback that forwards to `broadcast`.
- The TUI path (which already uses callbacks) is unaffected.

## Test plan

- New test: construct a `MeetingSession` with **no** web server, drive a
  broadcast-triggering path, assert the emit callback fires with the right payload.
- `uv run pytest -q --ignore=tests/e2e/test_metal.py` — full suite green; existing
  meeting/web broadcast tests still pass.

## Done when

- [ ] `MeetingSession` no longer imports or references a web server.
- [ ] Broadcasts flow via an injected callback; web wiring lives in `WebRuntime`.
- [ ] Headless-`MeetingSession` test added and green; full suite green; ruff clean.
