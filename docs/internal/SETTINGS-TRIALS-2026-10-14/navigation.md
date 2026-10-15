# Settings navigation — diagnosis and repair

Status: BUILT — root review pending; hold for SHIP. Base: `a9f07971d`.

Tuesday job: open Accounts or Engines, move to another Settings face, and
keep an edit made immediately before opening Guide.

## Observed before repair

The real production bundle was built through the machine lock, then served
by `scripts.graph_walk.Hub` with a new isolated HOME and DB for each width.
No owner hub, real CLI, Keychain, calendars, microphone or agent state was
used. The complete observations carry the hub URL and resolved DB/HOME:
`.tmp/settings-trials/navigation-before2/observations.json`.

| Action at 1440 and 393 | Observed result |
| --- | --- |
| Press Accounts plate header | Hub stays open. The header is plain text. |
| Press Choose engines on hub | Engines opens; chrome still says Settings. |
| Press Connect an account on hub | Accounts opens; chrome still says Settings. |
| Then press Settings wing/menu item | Accounts stays open: a real dead navigation control. |
| Open Settings with `scope=models`, press Accounts | Chrome says Accounts; body stays Engines. |
| Then press Settings | Chrome says Settings; body stays Engines. |
| Toggle Auto export, immediately press Guide, read settings after 1 s | `meeting.auto_export` stays false although the control was changed to true. |

Both plated hub Buttons owned their center and four target corners. At
393 both were 44 px high. There was no hit ownership failure on those
doors. There were no page errors in the completed capture.

Shots, for each `W` of `1440` and `393`, are under
`.tmp/settings-trials/navigation-before2/`:

- `W-account-header-press.png`: the noninteractive header.
- `W-account-door.png` and `W-settings-wing-after-account-door.png`: stale
  chrome and the dead return.
- `W-scoped-engines-to-accounts.png` and `W-scoped-engines-to-settings.png`:
  wing/body disagreement after a scope entry.
- `W-pending-edit-to-guide.png`: Guide after the unsaved edit; the JSON
  records `before=false`, `expected=true`, `persisted=false`.

Capture setup attempt 1 stopped at the 393 folded menu because the scratch
locator used `menuitem`; the library uses `menuitemcheckbox`. Attempt 2
corrected that locator and completed both widths, exit 0. No additional
setup attempts were used.

## Causes

1. Two independent navigation owners. `SettingsCore.tsx:1245` owns wing
   state, while `SettingsCore.tsx:1303` owns module state. Hub doors change
   only the latter at `SettingsCore.tsx:1584`; pressing the already selected
   Settings wing changes neither. Fails Tenet 3 and UX-CANON A.11.
2. Initial scope remains a permanent override. The effect at
   `SettingsCore.tsx:1577` picks `scopedModule` before `moduleOverride`.
   A real wing press can select Accounts while leaving scoped Engines in
   the body. Fails Tenet 3 and the window's honest-state rule.
3. Guide drops the delayed edit. `SettingsCore.tsx:1250` replaces
   SettingsFace with RuntimeDocsCore. SettingsFace unmount cleanup at
   `SettingsCore.tsx:1349` cancels the 700 ms writer timer. The leave hook
   (`web/src/lib/flushOnLeave.ts:11`) sends only on pagehide/visibility,
   neither of which occurs on a wing change. Fails Tenet 3; reproduced
   against the real settings API at both widths.
4. The ENGINES and ACCOUNTS plate labels are plain `header`/`span` at
   `settingsPrefs.tsx:517` and `settingsPrefs.tsx:538`. Their real library
   Buttons are at `settingsPrefs.tsx:532` and `settingsPrefs.tsx:553`.
   These headings are not dead Buttons. No plate redesign is indicated.

The existing Settings writer holds pending edits, authoritative revision,
refusal and queue state in SettingsFace. Preserve that instance while
changing faces. The repair does not change its conflict/refusal policy.

## Root direction / native canvas

The repair uses the existing SurfaceWings, Buttons, plates and module
geometry. Correct-path production shots show the intended material and
selection before build:

- `.tmp/settings-trials/navigation-before2/1440-accounts-wing-from-engines.png`
- `.tmp/settings-trials/navigation-before2/393-accounts-wing-from-engines.png`
- `.tmp/settings-trials/navigation-before2/1440-scoped-engines.png`
- `.tmp/settings-trials/navigation-before2/393-scoped-engines.png`

Root reviewed the native 393 Engines pose and directed the repair to keep
this material and geometry. SettingsCore's retained SettingsFace now owns
one navigation state for body and active wing. Hub doors, wing presses,
back controls and changed scope entry intents change that state. Scope is
entry intent, not a later-click override. A navigation press clears its
entry focus, so a previous job/provider focus does not return by accident.

SettingsFace remains mounted when Guide opens, so its existing delayed
writer completes. A write failure replaces Guide content with the existing
SurfaceState error and Try again Button; PrefStatusBar owns the one footer
in that state. Try again sends the exact failed changes through the existing
save queue. Normal Guide uses its current footer. No shared hook, router,
plate or CSS changes were needed.

## Verification budget

Existing files only: `SettingsCore.test.ts`, `settingsFaceRoster.test.tsx`,
`settingsLeave.philo17.test.tsx`, `settingsWords.philo17.test.tsx`,
`settingsSummaryName202.test.tsx`, and `settings.app.test.tsx`. Mounted
regressions will drive real wings through a WingSlotContext host and check
the rendered body, pending Guide write, and refusal. Run collection first,
then the exact files through `.tmp/settings-trials/locked.py` with Vitest 4,
maxWorkers 2. After repair, repeat the real pointer transitions at 1440 and
393 and compare the settings API value.

## Delivered proof

Changes: `web/src/pages/cores/SettingsCore.tsx` and
`web/src/desk/__tests__/settings.app.test.tsx`, plus this record. No other
lane's files were edited.

Collection: `.tmp/settings-trials/navigation-vitest-final-collect.log`, exit 0.
The new collected mounted tests are:

- `Settings navigation uses one selection > a scoped Engines entry can open Accounts, Settings, both hub doors, Guide and Back with matching wings`
- `Settings navigation uses one selection > Guide keeps an edit made before the save delay and has one footer`
- `Settings navigation uses one selection > opening the same external scope again leaves Guide and keeps the pending writer`
- `Settings navigation uses one selection > a pending write failure is visible in Guide; Try again resends the edit and restores its single footer`

The exact six named files ran through the lock at maxWorkers 2:
`.tmp/settings-trials/navigation-vitest-final.log`, exit 0:

```text
Test Files  6 passed (6)
     Tests  62 passed (62)
  Duration  6.07s
```

The same working capture rig ran after repair with strict body/wing,
target ownership, and persisted settings assertions at 1440 and 393:
`.tmp/settings-trials/navigation-after.log`, exit 0. Complete observations:
`.tmp/settings-trials/navigation-after/observations.json`.

Every previously failing navigation now shows the requested body and wing.
Auto export false → true → Guide persists true at both widths. A deliberate
browser transport abort on the subsequent real PUT shows Failed to fetch
and Try again immediately in Guide. Removing that abort and pressing Try
again persists the retry's true → false edit through the real hub. Both
failure and recovery have exactly one footer. All measured hub target
points remain owned; no page errors occurred.

For each `W` of `1440` and `393`, final shots under
`.tmp/settings-trials/navigation-after/` include the same before action
names plus `W-guide-write-failure.png` and `W-guide-write-retry.png`.

Root authorized one additional diagnosed entry seam: the window host passes
only a scope string, so repeating that exact scope after internal navigation
does not change the prop. The existing compositor replaces its Settings
window instance on every external open. SettingsFace now observes that
instance identity alongside scope, so a repeated open is a new entry intent
without unmounting the writer. No shared host/store file was edited. The
mounted repeated-scope test uses the real store openSurfaceWindow method,
keeps an edit through the repeated entry, and proves Settings was read once.

The targeted real pointer check reused the same capture setup and completed
at both widths, exit 0: `.tmp/settings-trials/navigation-entry.log`. Enter
with `scope=models`, press Guide, then press its Choose engines Button: the
same scope now returns to Engines with matching chrome. Shots:
`.tmp/settings-trials/navigation-entry/1440-same-scope-guide-choose-engines.png`
and `.tmp/settings-trials/navigation-entry/393-same-scope-guide-choose-engines.png`.
The observation JSON records isolated DB/HOME paths and zero page errors.

Unknown: the live failure is a transport abort, not a backend policy
refusal. No production before refusal is claimed.
