# Phase 40 Final Summary — Desktop Presence & Runtime Activity Indicators

Status: closed in the temp worktree. This captures the implementation in
`/tmp/holdspeak-gui-indicator`; the live checkout was not edited.

## What Landed In Temp

- A normalized runtime activity contract in `holdspeak/runtime_activity.py`.
- WebRuntime snapshots and `runtime_activity` websocket broadcasts.
- Optional desktop presence host in `holdspeak/desktop_presence.py`, gated by
  `HOLDSPEAK_DESKTOP_PRESENCE=1`.
- Transient desktop-window policy: idle is hidden; active work shows/updates;
  complete, meeting-live notifications, and errors linger briefly then hide.
- Renderer-safe desktop view data with stable dimensions, tone/accent mapping,
  truncation, and secret redaction.
- A compact optional Tk renderer for interactive desktop sessions.
- Web dashboard presence card driven by the same activity contract.
- Dictation and meeting mapping for model loading, hotkey/device activity,
  transcribing, processing, typing, meeting segments, intel/proposals, saving,
  complete, and error states.
- CI-safe desktop view fixture script:
  `scripts/desktop_presence_smoke.py --render view`.

## Evidence Captured

- Full non-metal suite: `2158 passed, 15 skipped in 61.27s`.
- Focused unit/doc tests: `38 passed in 0.90s`.
- Presence-focused unit tests: `36 passed in 1.00s`.
- Ruff: all checked Python files passed.
- Python compile: all touched Python files passed.
- Web screenshots: `npm run shots`, artifacts under
  `/private/tmp/holdspeak-gui-indicator/web/.shots/2026-06-05_07-56-40`.
- Native desktop screenshots: `scripts/desktop_presence_shots.py --settle 0.35
  --capture-mode auto`, artifacts under
  `/private/tmp/holdspeak-gui-indicator/pm/roadmap/holdspeak/phase-40-runtime-presence-indicators/evidence/native-presence-shots/2026-06-05_10-47-31`.
- Web build: `npm run build`, 8 pages built.
- PMO evidence: [evidence-story-06.md](./evidence-story-06.md).

## Native Smoke

- `python-tk@3.13` was installed with Homebrew so the project venv can import
  `tkinter` (`TkVersion 9.0`).
- `scripts/desktop_presence_smoke.py --render tk --delay 0.2` completed.
- A macOS frontmost-app smoke kept `Terminal` frontmost before and after the
  transient-window cycle.
- `scripts/desktop_presence_shots.py` captured 10 macOS `screencapture` PNGs
  plus a contact sheet covering idle hidden, listening, recording,
  transcribing, processing, typing, complete, meeting live, saving, and error.
- The Tk renderer now runs in a subprocess, avoiding macOS Tk-on-background-
  thread hangs while preserving the runtime's non-blocking show/update/hide
  interface.

## Remaining Before Live Merge

- Decide whether to address the unrelated mobile toast overlap seen in runtime
  screenshots.
- Rebase/apply this temp work onto the live checkout after Phase 39 dirty work
  is resolved or intentionally integrated.

## Follow-Ups

- Tray/menu affordance to reopen the dashboard.
- Richer desktop preferences.
- Audio level meters.
- Persistent recent-activity history.
- Platform-specific desktop adapters if Tk is not reliable enough on one of the
  supported desktop environments.
