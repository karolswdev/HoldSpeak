# Evidence — HS-32-02 (Invert meeting→web-server coupling)

**Shipped:** 2026-06-02. `MeetingSession` no longer reaches up into the web
layer. It owned, started, stopped, and broadcast to its own embedded
`MeetingWebServer` in ~8 places — an inversion-of-control violation meaning a
meeting couldn't run without a web server. It now **emits** live events through
an injected `on_broadcast` callback (default no-op); an observer (`WebRuntime`)
forwards them. Per the **user decision (2026-06-02)**, the embedded per-meeting
web server was **dropped** rather than relocated.

## What changed

### `holdspeak/meeting_session.py` (−84 net)
- Removed `from .web_server import MeetingWebServer, WebRuntimeCallbacks`, the
  `web_enabled` constructor param, `self.web_enabled`, the `self._web_server`
  attribute, the embedded-server **creation** block in `start()`, the **stop**
  block in `stop()`, and the `_web_server is web_server` teardown.
- Added `on_broadcast: Optional[Callable[[str, Any], None]] = None` and a single
  `_emit_broadcast(message_type, data)` helper (swallows observer exceptions,
  logs at debug). Every former `self._web_server.broadcast(t, d)` is now
  `self._emit_broadcast(t, d)` — covering `segment`, `intel_status`,
  `intel_token`, `intel_complete`, and the four `meeting_updated` (title/tag)
  sites.

### `holdspeak/web_runtime.py` (+28)
- `_start_meeting` drops `web_enabled=False` and passes
  `on_broadcast=self._on_meeting_broadcast`.
- New `_on_meeting_broadcast(message_type, data)`: forwards to
  `self.server.broadcast`, **filtering out** `segment` / `intel_complete` /
  `intel_status` — those already flow via the dedicated `on_segment` /
  `on_intel` handlers (which also drive the device LCDs), so re-forwarding would
  double-broadcast. Only `intel_token` + `meeting_updated` pass through.

### Callers
- `controller.py` (TUI) and `menubar.py` drop the now-invalid
  `web_enabled=config.meeting.web_enabled` argument. They pass **no**
  `on_broadcast`, so their meetings are silently web-free (the embedded
  dashboard is gone — the user's choice). Their `state.web_url` is now always
  `None`, which the existing `if state.web_url:` guards handle (no dashboard
  notify/menu, no crash).
- `tests/integration/test_intel_streaming.py`: removed 10 dead
  `web_enabled=False` kwargs.

## The overlap map (why no double- or zero-broadcast in the flagship)

| Event | Flagship-web path before | After |
|---|---|---|
| `segment` | `on_segment`→`_on_meeting_segment`→broadcast | unchanged (filtered from `on_broadcast`) |
| `intel_complete` | `on_intel`→`_on_meeting_intel`→broadcast | unchanged (filtered) |
| `intel_status` | `on_intel`→`_broadcast_intel_status` | unchanged (filtered) |
| `intel_token` | **dead** (embedded-only; `web_enabled=False` in runtime) | **now forwarded** → `dashboard-app.js` token streaming lights up |
| `meeting_updated` | **dead** (embedded-only) | **now forwarded** → title/tag updates reach the web client |

The flagship web path is unchanged for the three overlapping events; the two
events that were *only* ever delivered to the now-removed embedded server (and
were dead in the flagship runtime) are now observed by `WebRuntime` and
forwarded — the web client already has handlers for both, so this is additive,
not a regression.

## Tests ran

- New (`tests/unit/test_meeting_session.py`): `test_meeting_session_is_web_free_and_emits_via_on_broadcast`
  (constructs a session with **no** web server, asserts `not hasattr _web_server`
  / `web_enabled`, drives `set_title`/`add_tag`/`set_tags`, asserts the
  `meeting_updated` emits fire with the right payloads),
  `test_title_and_tag_edits_are_safe_without_an_observer` (default no-op emit),
  `test_on_broadcast_callback_exception_does_not_break_the_session`.
- `uv run pytest -q --ignore=tests/e2e/test_metal.py` → **2066 passed, 14
  skipped** (+3 new vs the 2063 baseline).
- Ruff: `web_runtime.py` clean; the changed `meeting_session.py` introduces no
  new findings (the lone `F841 current_time@1246` pre-dates this work — see
  Phase 31 evidence); `test_intel_streaming.py`'s 3 `E402` are pre-existing on
  HEAD; the 2 `menubar.py` `F541` are pre-existing and outside the diff.

## Decisions / deviations / follow-ups

- **User decision (2026-06-02): drop the embedded per-meeting web server**
  rather than relocate its lifecycle into `controller.py`/`menubar.py`.
  Greenfield/aggressive — the flagship `WebRuntime` is the one dashboard owner.
- **Payload aliasing left as-is.** `meeting_updated`/`segment` payloads
  reference live state; a real observer (`server.broadcast`) serializes
  synchronously on receipt, so it's correct. The new unit test snapshots at
  emit time to assert per-event values (documented in the test).
- **Vestigial config flag — flagged for HS-32-06.** `config.meeting.web_enabled`
  and its Settings checkbox now control nothing (the embedded server they gated
  is gone). Left in place to keep this commit atomic to the coupling inversion;
  the dead toggle + field are a clean target for the HS-32-06 drift sweep (or a
  small follow-up). `config.py`, `tui/screens/settings.py`, and `test_config.py`
  still reference the field, all green.
