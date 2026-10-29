# Daily lane report

Audited all 15 guides assigned in `lanes.json` against active source paths. No
product files, generated files, tests, defaults, or sibling-lane documents were
changed. No live Desk, browser, provider, phone, microphone, or owner-data flow
was used.

## Corrections

- `docs/GETTING_STARTED.md`, `docs/USER_GUIDE.md`, `docs/WEB_DESK.md`, and
  `docs/programs.md`: corrected the active Engines path to **Settings > This
  Mac > Engines** and updated retired engine labels such as **Use these** and
  **Test** to the current **Use it**, **Use**, and **Try it** controls. Source:
  `web/src/pages/cores/settingsPrefs.tsx:75-85,124-130`,
  `web/src/features/runson/RunsOnCore.tsx:594-608,1030-1058`.
- `docs/USER_GUIDE.md` and `docs/WEB_DESK.md`: replaced generic/stale Window
  wording with the registered verbs, including **Close**, **Minimize**, **Next
  window**, **Tile left**, **Tile right**, **Zoom**, **To back**, **Stage**,
  **Arrange all**, and **Back**. Source:
  `web/src/desk/verbRegistry.ts:798-943`.
- `docs/DESK_MEMORY.md` and `docs/USER_GUIDE.md`: replaced parked **Ask your
  desk**/**RAW** wording with the active **Find or ask your desk** field and
  recall rows. Source: `web/src/pages/cores/MemoryCore.tsx:164-219,264-414`.
- `docs/PROJECT_ROOMS.md` and `docs/USER_GUIDE.md`: corrected Connections to
  **Settings > Accounts > Connections**. Source:
  `web/src/pages/cores/settingsPrefs.tsx:75-85,116-118`.
- `docs/ENVIRONMENTS.md` and `docs/GLOSSARY.md`: corrected Wallpaper to
  **Settings > Desk > Wallpaper**, Desk sounds to **Settings > Desk > Sounds &
  Presence > Desk sounds**, and removed the unsupported Settle keyboard
  shortcut. Source: `web/src/pages/cores/settingsPrefs.tsx:124-129`,
  `web/src/pages/cores/SettingsCore.tsx:2387-2417,2834-2840`,
  `web/src/desk/verbRegistry.ts:332-343,928-943`.
- `docs/calls.md`: corrected the visible Calls setup label to **Your numbers**
  while preserving the exact stored key `allowed_numbers`. Source:
  `web/src/desk/calls/CallsSettings.tsx:122-149,315-355`,
  `holdspeak/config/calls.py:10-29`.

The remaining six guides were source-checked without edits. Per-document
claims, source anchors, changes, and unknowns are in `daily-audit.json`.

## Cross-lane defect

`docs/DESK_OBJECT_MODEL.md` remains root-owned and contains a stale shortcut/menu
table. The active source is `web/src/desk/verbRegistry.ts:798-943` and
`web/src/desk/applications.ts:98-106,121-128,156-163,182-191,199-207,533-542`.
The daily lane did not edit that root-owned document.

## Verification limits

This lane will run only the permitted `scripts/check_docs.py` invocation over
the 15 owned guides and `git diff --check`. No live behavior or deployment
availability is certified by this report. Hold for SHIP.
