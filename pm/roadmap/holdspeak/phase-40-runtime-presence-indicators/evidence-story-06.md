# HS-40-06 Evidence — Desktop + Web Verification

Captured 2026-06-05 from `/tmp/holdspeak-gui-indicator`. The live checkout at
`/Users/karol/dev/tools/HoldSpeak` was not edited.

## Commands

```text
/Users/karol/dev/tools/HoldSpeak/.venv/bin/python -m pytest -q tests/unit/test_desktop_presence.py tests/unit/test_runtime_activity.py tests/unit/test_web_runtime.py tests/unit/test_web_presence_indicator.py
36 passed in 1.00s
```

```text
/Users/karol/dev/tools/HoldSpeak/.venv/bin/python -m pytest -q tests/unit/test_doc_drift_guard.py tests/unit/test_web_presence_indicator.py tests/unit/test_desktop_presence.py tests/unit/test_runtime_activity.py tests/unit/test_web_runtime.py
38 passed in 0.90s
```

```text
/Users/karol/dev/tools/HoldSpeak/.venv/bin/python -m pytest -q --ignore=tests/e2e/test_metal.py
2158 passed, 15 skipped in 61.27s
```

```text
/Users/karol/dev/tools/HoldSpeak/.venv/bin/python -m ruff check scripts/desktop_presence_smoke.py holdspeak/desktop_presence.py holdspeak/runtime_activity.py holdspeak/web_runtime.py tests/unit/test_desktop_presence.py tests/unit/test_runtime_activity.py tests/unit/test_web_runtime.py tests/unit/test_web_presence_indicator.py
All checks passed!
```

```text
/Users/karol/dev/tools/HoldSpeak/.venv/bin/python -m py_compile scripts/desktop_presence_smoke.py holdspeak/desktop_presence.py holdspeak/runtime_activity.py holdspeak/web_runtime.py tests/unit/test_desktop_presence.py tests/unit/test_runtime_activity.py tests/unit/test_web_runtime.py tests/unit/test_web_presence_indicator.py
passed
```

```text
npm run shots
8 page(s) built
Screenshots -> /private/tmp/holdspeak-gui-indicator/web/.shots/2026-06-05_07-56-40
```

```text
npm run build
8 page(s) built in 4.62s
```

```text
/Users/karol/dev/tools/HoldSpeak/.venv/bin/python scripts/desktop_presence_smoke.py --render view
Printed renderer-ready JSON for all activity states: idle, listening,
recording, transcribing, processing, typing, complete, meeting_live, saving,
and error.
```

```text
/Users/karol/dev/tools/HoldSpeak/.venv/bin/python scripts/desktop_presence_smoke.py --render tk --delay 0.2
tk smoke completed
```

```text
before=$(osascript -e 'tell application "System Events" to get name of first application process whose frontmost is true')
/Users/karol/dev/tools/HoldSpeak/.venv/bin/python scripts/desktop_presence_smoke.py --render tk --delay 0.15
after=$(osascript -e 'tell application "System Events" to get name of first application process whose frontmost is true')
frontmost_before=Terminal
frontmost_after=Terminal
```

```text
/Users/karol/dev/tools/HoldSpeak/.venv/bin/python scripts/desktop_presence_shots.py --settle 0.35 --capture-mode auto
Generated native presence screenshots with macOS screencapture.
Output -> /private/tmp/holdspeak-gui-indicator/pm/roadmap/holdspeak/phase-40-runtime-presence-indicators/evidence/native-presence-shots/2026-06-05_10-47-31
```

## Screenshot Artifacts

- Runtime desktop: `/private/tmp/holdspeak-gui-indicator/web/.shots/2026-06-05_07-56-40/runtime.png`
- Runtime mobile: `/private/tmp/holdspeak-gui-indicator/web/.shots/2026-06-05_07-56-40/runtime-mobile.png`
- Other generated pages: activity, companion, components, dictation, history,
  settings drawer.
- Native desktop presence contact sheet:
  `/private/tmp/holdspeak-gui-indicator/pm/roadmap/holdspeak/phase-40-runtime-presence-indicators/evidence/native-presence-shots/2026-06-05_10-47-31/contact-sheet.png`
- Native desktop presence manifest:
  `/private/tmp/holdspeak-gui-indicator/pm/roadmap/holdspeak/phase-40-runtime-presence-indicators/evidence/native-presence-shots/2026-06-05_10-47-31/manifest.json`
- Native individual state captures: `01-idle-hidden.png`,
  `02-listening-active.png`, `03-recording-active.png`,
  `04-transcribing-active.png`, `05-processing-active.png`,
  `06-typing-active.png`, `07-complete-linger.png`,
  `08-meeting_live-linger.png`, `09-saving-active.png`,
  `10-error-linger.png`.

## Observations

- The runtime dashboard presence card renders on desktop and mobile with stable
  dimensions, `Ready` state text, source metadata, and desktop window policy
  metadata (`Desktop hidden` for idle).
- The presence card itself shows no obvious overlap in the generated desktop
  or mobile screenshots.
- Source-level regression coverage confirms the web presence card has
  `role="status"`, `aria-live="polite"`, handles websocket
  `runtime_activity` messages, and disables live-ring animation under
  `prefers-reduced-motion: reduce`.
- User-facing docs were updated and covered by `test_doc_drift_guard.py`.
- The desktop view fixture confirms every runtime activity state maps to stable
  renderer dimensions and the expected hidden/active/linger visibility policy.
- `python-tk@3.13` was installed with Homebrew so the project venv can import
  `tkinter` (`TkVersion 9.0`).
- Interactive Tk smoke completed. The renderer now runs Tk in a subprocess so
  macOS keeps Tk on that process' main thread and the runtime only sends
  show/update/hide commands.
- Focus-preservation smoke kept the frontmost app as `Terminal` before and
  after the transient-window cycle.
- `scripts/desktop_presence_shots.py` drives the real desktop host and captures
  every state. This run used macOS `screencapture` for all 10 PNGs, including
  the hidden idle state.
- The mobile runtime screenshot shows reconnect/deferred-job toasts overlapping
  the lower transcript-empty state. That appears unrelated to the new presence
  card and should be handled separately if mobile toast placement becomes part
  of this phase's verification scope.

## Pending Evidence

- No pending automated evidence. The screenshot harness can be rerun during
  live merge on the final target Python/desktop session.
