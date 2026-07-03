# Evidence — HSM-18-02 — Voice macros fire on the relay + the iPad CommandsBoard

**Status:** done (2026-07-03). Two halves, two increments:

## 1. The hub fix (landed 2026-06-27, the phase's opening commit)

`api_dictation_remote` never called `dispatch_voice_command` — a macro keyword spoken over
the iPad relay was silently dictated as prose. Fixed on open day: the remote relay fires
macros through the same bounded, guarded connector as the local path, the response carries
the `fired` object, off-by-default byte-identical. Proven then:
`tests/unit/test_web_routes_remote_dictation.py` incl. the remote-path macro test the audit
demanded. (The 18-01 `raw` lane deliberately skips macro dispatch — a previewed receipt's
words type as words; test-locked there.)

## 2. The iPad CommandsBoard (this increment)

- **Contracts** (`Contracts/VoiceCommands.swift`): `VoiceMacroSettings` / `VoiceMacroSpec` /
  `VoiceMacroActionSpec` (raw wire kinds — an unknown future kind never fails the decode)
  + `VoiceMacroTestResult`. The Swift `preview` strings are kept in lockstep with
  `VoiceMacroAction.preview()` in `config.py` (design §10: the card, the editor, and any
  audit read identically).
- **Client** (`HTTPDesktopClient+Commands.swift`, the parallel-extension pattern):
  `macroSettings()` decodes just the `dictation.macros` slice out of `GET /api/settings`
  (older hub without the block → default off/empty); `updateMacroSettings` PUTs ONLY the
  deep-merge macros slice (test-asserted: the body carries the `dictation` key and nothing
  else); `testMacro` posts to `/api/commands/test`. 5/5 in `CommandsClientTests`.
- **The board** (`CommandsBoard.swift`, entered from the Dictate screen): the enable
  toggle ("Off · keywords dictate as words"), macro cards with the four kind chips, a
  **speak-to-fill mic on every field** (`MicFillField` over `VoiceCaptureState` — spoken
  symbols apply), the canonical preview line, the **"runs code on your Mac"** warn chip on
  shell, per-card **Test** with the honest result line (`type_text` shows the preview-only
  note), and Save. The honesty mark heads the screen: **RUNS ON <your Mac>** — the iPad
  authors and triggers, never executes.

Screenshots: [`hsm-18-02-commands-board.png`](./screenshots/hsm-18-02-commands-board.png)
(seeded, all three kinds visible) ·
[`hsm-18-02-live-hub-board.png`](./screenshots/hsm-18-02-live-hub-board.png) (live).

## 3. The live-hub proof

Against a real `MeetingWebServer` with **the config redirected to scratch** (the owner's
real `~/.config/holdspeak/config.json` mtime-verified untouched):

- `GET` → macros default off/empty → `PUT` the standup macro → `GET` round-trips it →
  `POST /api/commands/test {type_text}` → `{"ok":true,"tested":false,"preview":"types: ##
  Standup","note":"types into the focused app"}` → an unknown kind is a clean 400.
- The connected simulator's board **loaded those live macros** and rendered them (the
  second screenshot is the macro the curl PUT created, not a seed).
- The regenerated `docs/api-surface.json` records the new iOS consumers — the HS-72-02
  route-surface lock caught the stale manifest in the suite run, exactly as designed
  (the 18-07 evidence promised this behavior; it fired for real here).

## Honest boundaries

- Test-firing an egress kind (open_url / launch_app / shell) against a live Mac was left
  to the owner's hands — the live test call used `type_text` (preview-only by design).
  The spoken keyword → macro-fires-as-an-object moment on real metal rides 18-06.

## Suites

`uv run pytest -q tests/unit` **2403 passed** (incl. the regenerated manifest) ·
`tests/integration` **685 passed** · `swift test` **422 passed** (5 new) · app build green.
