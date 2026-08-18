# Evidence - HS-139-07

- **Story:** HS-139-07 - The walk
- **Status:** done
- **Date:** 2026-08-17

## Proof

### Captured run — 2026-08-18T03:17:05Z

- **Command:** `bash -c HOME_REAL=$HOME HOME=$(mktemp -d) PLAYWRIGHT_BROWSERS_PATH=$HOME_REAL/Library/Caches/ms-playwright uv run python scripts/settings_walk_139.py`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** dcbb3d5ba391bf02778afec05efab6f64e865803

```text
Booting hub: port=50419 home=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/holdspeak-settings-walk-3_q8hllt
  hub pid=8792 home=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/holdspeak-settings-walk-3_q8hllt port=50419
Traceback (most recent call last):
  File "/Users/karol/dev/tools/HoldSpeak/scripts/settings_walk_139.py", line 520, in <module>
    sys.exit(walk())
             ~~~~^^
  File "/Users/karol/dev/tools/HoldSpeak/scripts/settings_walk_139.py", line 471, in walk
    browser = p.chromium.launch(headless=True)
  File "/Users/karol/dev/tools/HoldSpeak/.venv/lib/python3.13/site-packages/playwright/sync_api/_generated.py", line 14568, in launch
    self._sync(
    ~~~~~~~~~~^
        self._impl_obj.launch(
        ^^^^^^^^^^^^^^^^^^^^^^
    ...<17 lines>...
        )
        ^
    )
    ^
  File "/Users/karol/dev/tools/HoldSpeak/.venv/lib/python3.13/site-packages/playwright/_impl/_sync_base.py", line 115, in _sync
    return task.result()
           ~~~~~~~~~~~^^
  File "/Users/karol/dev/tools/HoldSpeak/.venv/lib/python3.13/site-packages/playwright/_impl/_browser_type.py", line 98, in launch
    await self._channel.send(
        "launch", TimeoutSettings.launch_timeout, params
    )
  File "/Users/karol/dev/tools/HoldSpeak/.venv/lib/python3.13/site-packages/playwright/_impl/_connection.py", line 69, in send
    return await self._connection.wrap_api_call(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    ...<3 lines>...
    )
    ^
  File "/Users/karol/dev/tools/HoldSpeak/.venv/lib/python3.13/site-packages/playwright/_impl/_connection.py", line 559, in wrap_api_call
    raise rewrite_error(error, f"{parsed_st['apiName']}: {error}") from None
playwright._impl._errors.Error: BrowserType.launch: Executable doesn't exist at /Library/Caches/ms-playwright/chromium_headless_shell-1200/chrome-headless-shell-mac-arm64/chrome-headless-shell
╔════════════════════════════════════════════════════════════╗
║ Looks like Playwright was just installed or updated.       ║
║ Please run the following command to download new browsers: ║
║                                                            ║
║     playwright install                                     ║
║                                                            ║
║ <3 Playwright Team                                         ║
╚════════════════════════════════════════════════════════════╝
```

### Captured run — 2026-08-18T03:17:31Z

- **Command:** `bash /private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/8cb4eee1-518d-4508-859c-1c60b6eb0e3b/scratchpad/run_walk.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** dcbb3d5ba391bf02778afec05efab6f64e865803

```text
Booting hub: port=50452 home=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/holdspeak-settings-walk-ieu_fy9v
  hub pid=9113 home=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/holdspeak-settings-walk-ieu_fy9v port=50452

== settings face @1440 ==
  PASS  face tiles ≤ 8  tiles=7
  PASS  face tiles == 7  tiles=7
  PASS  no hscroll on face @1440
  PASS  POSTURE label present
  PASS  precedence chain present
  SHOT  settings-face-overview-1440.png  seven tiles + POSTURE + precedence
  PASS  zero console errors  settings face @1440  []

== room voice @1440 ==
  PASS  room voice opened
  PASS  no hscroll in voice @1440
  SHOT  room-voice-open-1440.png  room voice
  controls  voice: 7 face + 10 RAW
  PASS  RAW well closed on open  voice #0
  SHOT  room-voice-raw-open-0-1440.png  RAW well #0 in voice
  PASS  zero console errors  room voice @1440  []

== room sounds @1440 ==
  PASS  room sounds opened
  PASS  no hscroll in sounds @1440
  SHOT  room-sounds-open-1440.png  room sounds
  controls  sounds: 3 face + 0 RAW
  PASS  zero console errors  room sounds @1440  []

== room meetings @1440 ==
  PASS  room meetings opened
  PASS  no hscroll in meetings @1440
  SHOT  room-meetings-open-1440.png  room meetings
  controls  meetings: 1 face + 19 RAW
  PASS  RAW well closed on open  meetings #0
  SHOT  room-meetings-raw-open-0-1440.png  RAW well #0 in meetings
  PASS  zero console errors  room meetings @1440  []

== room rhythm @1440 ==
  PASS  room rhythm opened
  PASS  no hscroll in rhythm @1440
  SHOT  room-rhythm-open-1440.png  room rhythm
  controls  rhythm: 6 face + 3 RAW
  PASS  RAW well closed on open  rhythm #0
  SHOT  room-rhythm-raw-open-0-1440.png  RAW well #0 in rhythm
  PASS  zero console errors  room rhythm @1440  []

== room models @1440 ==
  PASS  room models opened
  PASS  no hscroll in models @1440
  SHOT  room-models-open-1440.png  room models
  controls  models: 11 face + 4 RAW
  PASS  RAW well closed on open  models #0
  SHOT  room-models-raw-open-0-1440.png  RAW well #0 in models
  PASS  zero console errors  room models @1440  []

== room integrations @1440 ==
  PASS  room integrations opened
  PASS  no hscroll in integrations @1440
  SHOT  room-integrations-open-1440.png  room integrations
  controls  integrations: 0 face + 0 RAW
  PASS  RAW well closed on open  integrations #0
  SHOT  room-integrations-raw-open-0-1440.png  RAW well #0 in integrations
  PASS  zero console errors  room integrations @1440  []

== room system @1440 ==
  PASS  room system opened
  PASS  no hscroll in system @1440
  SHOT  room-system-open-1440.png  room system
  controls  system: 1 face + 0 RAW
  PASS  zero console errors  room system @1440  []

== control count bar @1440 ==
  PASS  on-glass controls (excl RAW) ≤ 40  total=29
  CONTROLS BY TILE: {'voice': 7, 'sounds': 3, 'meetings': 1, 'rhythm': 6, 'models': 11, 'integrations': 0, 'system': 1}

== task (a): change hotkey @1440 ==
  hotkey before: '⌥R'
  PASS  hotkey listening mode
  hotkey after: 'F9'
  PASS  hotkey changed on glass  old='⌥R' new='F9'
  SHOT  task-hotkey-changed-1440.png  push-to-talk hotkey changed to F9
  PASS  hotkey round-trips via API  api key='f9'
  PASS  zero console errors  task hotkey @1440  []

== task (c): change RAW knob @1440 ==
  SHOT  task-raw-knob-changed-1440.png  transcribe_timeout changed to 125
  PASS  RAW knob round-trips via API  old=120 new_input=125 api=125
  PASS  zero console errors  task RAW knob @1440  []

== settings face @393 ==
  PASS  face tiles ≤ 8  tiles=7
  PASS  face tiles == 7  tiles=7
  PASS  no hscroll on face @393
  PASS  POSTURE label present
  PASS  precedence chain present
  SHOT  settings-face-overview-393.png  seven tiles + POSTURE + precedence
  PASS  zero console errors  settings face @393  []

== room voice @393 ==
  PASS  room voice opened
  PASS  no hscroll in voice @393
  SHOT  room-voice-open-393.png  room voice
  controls  voice: 7 face + 10 RAW
  PASS  RAW well closed on open  voice #0
  SHOT  room-voice-raw-open-0-393.png  RAW well #0 in voice
  PASS  zero console errors  room voice @393  []

== room sounds @393 ==
  PASS  room sounds opened
  PASS  no hscroll in sounds @393
  SHOT  room-sounds-open-393.png  room sounds
  controls  sounds: 3 face + 0 RAW
  PASS  zero console errors  room sounds @393  []

== room meetings @393 ==
  PASS  room meetings opened
  PASS  no hscroll in meetings @393
  SHOT  room-meetings-open-393.png  room meetings
  controls  meetings: 1 face + 19 RAW
  PASS  RAW well closed on open  meetings #0
  SHOT  room-meetings-raw-open-0-393.png  RAW well #0 in meetings
  PASS  zero console errors  room meetings @393  []

== room rhythm @393 ==
  PASS  room rhythm opened
  PASS  no hscroll in rhythm @393
  SHOT  room-rhythm-open-393.png  room rhythm
  controls  rhythm: 6 face + 3 RAW
  PASS  RAW well closed on open  rhythm #0
  SHOT  room-rhythm-raw-open-0-393.png  RAW well #0 in rhythm
  PASS  zero console errors  room rhythm @393  []

== room models @393 ==
  PASS  room models opened
  PASS  no hscroll in models @393
  SHOT  room-models-open-393.png  room models
  controls  models: 11 face + 4 RAW
  PASS  RAW well closed on open  models #0
  SHOT  room-models-raw-open-0-393.png  RAW well #0 in models
  PASS  zero console errors  room models @393  []

== room integrations @393 ==
  PASS  room integrations opened
  PASS  no hscroll in integrations @393
  SHOT  room-integrations-open-393.png  room integrations
  controls  integrations: 0 face + 0 RAW
  PASS  RAW well closed on open  integrations #0
  SHOT  room-integrations-raw-open-0-393.png  RAW well #0 in integrations
  PASS  zero console errors  room integrations @393  []

== room system @393 ==
  PASS  room system opened
  PASS  no hscroll in system @393
  SHOT  room-system-open-393.png  room system
  controls  system: 1 face + 0 RAW
  PASS  zero console errors  room system @393  []

== control count bar @393 ==
  PASS  on-glass controls (excl RAW) ≤ 40  total=29
  CONTROLS BY TILE: {'voice': 7, 'sounds': 3, 'meetings': 1, 'rhythm': 6, 'models': 11, 'integrations': 0, 'system': 1}

== task (b): add destination @393 ==
  PASS  destination card appeared  cards=6
  SHOT  task-destination-card-added-393.png  destination card added at 393px
  PASS  destination exists via API  targets=7
  PASS  no hscroll in destinations @393
  PASS  zero console errors  task destination @393  []

============================================================
WALK COMPLETE: 76 passed, 0 failed, 0 findings, 29 shots

CONTROL COUNTS (excl RAW): {'voice': 7, 'sounds': 3, 'meetings': 1, 'rhythm': 6, 'models': 11, 'integrations': 0, 'system': 1}
TOTAL ON-GLASS: 29 (bar: ≤40)

SHOTS:
  settings-face-overview-1440.png  (seven tiles + POSTURE + precedence)
  room-voice-open-1440.png  (room voice)
  room-voice-raw-open-0-1440.png  (RAW well #0 in voice)
  room-sounds-open-1440.png  (room sounds)
  room-meetings-open-1440.png  (room meetings)
  room-meetings-raw-open-0-1440.png  (RAW well #0 in meetings)
  room-rhythm-open-1440.png  (room rhythm)
  room-rhythm-raw-open-0-1440.png  (RAW well #0 in rhythm)
  room-models-open-1440.png  (room models)
  room-models-raw-open-0-1440.png  (RAW well #0 in models)
  room-integrations-open-1440.png  (room integrations)
  room-integrations-raw-open-0-1440.png  (RAW well #0 in integrations)
  room-system-open-1440.png  (room system)
  task-hotkey-changed-1440.png  (push-to-talk hotkey changed to F9)
  task-raw-knob-changed-1440.png  (transcribe_timeout changed to 125)
  settings-face-overview-393.png  (seven tiles + POSTURE + precedence)
  room-voice-open-393.png  (room voice)
  room-voice-raw-open-0-393.png  (RAW well #0 in voice)
  room-sounds-open-393.png  (room sounds)
  room-meetings-open-393.png  (room meetings)
  room-meetings-raw-open-0-393.png  (RAW well #0 in meetings)
  room-rhythm-open-393.png  (room rhythm)
  room-rhythm-raw-open-0-393.png  (RAW well #0 in rhythm)
  room-models-open-393.png  (room models)
  room-models-raw-open-0-393.png  (RAW well #0 in models)
  room-integrations-open-393.png  (room integrations)
  room-integrations-raw-open-0-393.png  (RAW well #0 in integrations)
  room-system-open-393.png  (room system)
  task-destination-card-added-393.png  (destination card added at 393px)
```
