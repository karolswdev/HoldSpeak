# HS-32-02 — Invert meeting→web-server coupling

- **Status:** done (2026-06-02). Evidence: [evidence-story-02.md](./evidence-story-02.md).

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

- [x] `MeetingSession` no longer imports or references a web server.
- [x] Broadcasts flow via an injected callback; web wiring lives in `WebRuntime`.
- [x] Headless-`MeetingSession` test added and green; full suite green; ruff clean.

## Evidence

[evidence-story-02.md](./evidence-story-02.md). Embedded per-meeting web server
**dropped** (user decision); `MeetingSession` emits via `on_broadcast` (default
no-op), `WebRuntime` forwards `intel_token`/`meeting_updated`. Suite green at
**2066 passed, 14 skipped** (+3 new tests). Note: `config.meeting.web_enabled`
is now vestigial — flagged for HS-32-06.
