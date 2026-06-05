# HS-40-03 — Native-Style Status Window Renderer

- **Project:** holdspeak
- **Phase:** 40
- **Status:** implemented in `/tmp`
- **Depends on:** HS-40-02
- **Unblocks:** HS-40-05, HS-40-06
- **Owner:** unassigned

## Problem

The desktop host needs a polished, non-disruptive window that makes voice
activity obvious without stealing focus from the app the user is dictating
into. It should feel native enough on macOS and Linux to be trusted, while
remaining small and predictable.

## Scope

- **In:**
  - Render transient status windows for meaningful non-idle states:
    `listening`, `recording`, `transcribing`, `processing`, `typing`,
    `complete`, `meeting_live`, `saving`, and `error`. `idle` is a
    hide/destroy command, not a visible desktop state.
  - Show a state ring/dot, short label, one-line detail, optional safe last
    utterance/result snippet, and error detail.
  - Define show/update/hide timing: immediate on press/recording, update during
    processing/typing, linger briefly on `complete`/`error`, then hide/destroy.
    No window may sit on screen while HoldSpeak is idle.
  - Keep window dimensions stable across labels; truncate long text.
  - Avoid focus theft and preserve the active app while dictating.
  - Respect reduced-motion / low-animation config where detectable or
    configured.
- **Out:**
  - Audio waveform meters.
  - Rich meeting transcript/intel UI inside the native window.
  - Native controls beyond maybe dismiss/open-dashboard in a later story.

## Acceptance Criteria

- [ ] Each activity state maps to a visually distinct but restrained native
      window state.
- [ ] The window can update in place without flicker or layout jump.
- [ ] `idle` hides/destroys the native window; it does not render a persistent
      idle widget.
- [ ] Resolved states (`complete` for typed/saved/empty/no-op, and `error`)
      linger for a bounded duration and then disappear.
- [ ] Showing the window does not steal text focus from the target app in the
      supported smoke path.
- [ ] Long labels/details are truncated safely; no raw secrets are displayed.
- [ ] Errors remain visible long enough to read and then settle predictably.
- [ ] Renderer can be exercised with a fake event sequence in tests.

## Test Plan

- Unit: renderer state-to-view model tests.
- Smoke: manual macOS/Linux focus test: type into an editor, hold hotkey, and
  verify the status window appears without taking focus.
- Screenshot/evidence: representative state captures in HS-40-06.

## Notes / Open Questions

- 2026-06-05 — Implemented in `/tmp`: `desktop_presence.py` now has
  a renderer-safe `PresenceWindowView` (`build_presence_window_view`) with state
  tones, accent colors, fixed dimensions, truncation, and secret redaction; the
  optional Tk renderer uses that view model and draws a compact status window
  with a state dot. Unit coverage exercises show/update/linger/hide, hidden
  idle, cancellation of stale linger timers, view metadata, truncation, and
  redaction. Remaining verification: real GUI smoke on macOS/Linux and focus
  preservation evidence under HS-40-06.
- If the chosen toolkit cannot guarantee non-focus-stealing behavior on one
  platform, record the platform as degraded and prefer a no-focus fallback over
  a pretty but disruptive window.
- Explicit user decision: native windows pop in/out when things happen. They
  must not remain visible as an always-on overlay.
