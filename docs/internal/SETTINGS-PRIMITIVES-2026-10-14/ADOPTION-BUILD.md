# Settings primitive adoption build — 2026-10-14

**HOLD FOR SHIP — product source frozen; root review and live verification pending.**

Worktree: `/Users/karol/dev/tools/wt-settings-primitives-20261014`.
Base: `22de063e32edf21db5eb43bae7b63b6dc94c6b1f`.
Root selected the native canvas direction; this is not owner acceptance.

## Delivered

- Voice composes `SurfaceColumns variant="preferences"`, one inset **Voice
  typing** sheet (hold key, language, divider, preview, commands), **Wake
  word** below, and **Spoken symbols** in the side slot. Empty and populated
  dictionaries use the same bounded group action. `GadgetTable
  layout="fields"` retains existing array patches/defaults, native input
  names, and armed `Forget` / `Forget?` row verbs. LANGUAGE and WAKE option
  wires are unchanged; obsolete Wake helper prose is absent, as on canvas.
- `HotkeyCapture grouped={false}` exposes its existing row to the containing
  sheet. `grouped=true` remains the default with its former rendering; the
  native key map, event capture, refusal, and Escape behavior are unchanged.
- Meetings, Rhythm, Sounds, People, and System ordinary groups use inset
  sheets and the shared preference columns. Boolean choices use the native
  state variant. Text/range rows request full width, numeric rows short
  width, and pick rows standard width.
- Calendar keeps its source ledger, draft wells, source identity, error
  recovery, and egress. Its existing Add calendar/Add feed/Import image
  callbacks are in group actions. Remote credentials, Desk reset, and TTS
  download use group actions with their existing operation handlers. A ready
  TTS server with no receipt/error renders no empty action footer.
- The six modules get their existing pixel sprite beside the module name.
  The local frame owns module padding/header/max-width. Shared species own
  group, row, column, and action geometry. Legacy form overrides are scoped
  off `data-settings-material="inset"`; Accounts still has its existing
  `prefs-groups`/`prefs-column` layout and CSS. Engines, Guide, directory,
  footer recovery, and calendar ledger styling retain their compositions.

The initial adoption added no form state, backend behavior, validation
framework, or writer. The later producer-backed symbol correction below
adds one local incomplete-draft buffer, with the existing writer. Settings' exact-path queue, 700 ms debounce, newest-value Retry,
leave flush, secrets, and calendar coordinator were retained. People owner
aliases, independent endpoint, and environment holds were retained.

## Owned changes

Product paths, all under `web/src/pages/cores/`:
`SettingsCore.tsx`, `settings.css`, `settingsBespoke.tsx`,
`settingsPeople.tsx`, `settingsTts.tsx`, `settingsPrefs.tsx`.

Focused tests changed:
`web/src/desk/__tests__/settings.app.test.tsx` and
`web/src/pages/cores/__tests__/settingsTts.test.tsx`.

The Meetings column assertion now names the shared columns. The symbol test
checks one group action in both states, retained cell edits/defaults in the
settings wire, and two presses for Forget. A new Voice test proves key
capture survives another preference's rerender, Escape cancels, and F8
reaches the existing hotkey wire. A small TTS case proves ready means no
empty footer. Existing writer/retry/leave/calendar/People assertions remain.

## Initial adoption verification

Both commands used `.venv/bin/python .tmp/settings-primitives/locked.py`,
which allocates an isolated HOME, uses `scripts/test_lock.py`, and removes
the scratch HOME afterward. No test touched the owner's HOME or desk.

```text
.venv/bin/python .tmp/settings-primitives/locked.py adoption-collect-final --web ./node_modules/.bin/vitest list src/desk/__tests__/settings.app.test.tsx src/pages/cores/__tests__/SettingsCalendar.test.tsx src/pages/cores/__tests__/settingsPeople.test.tsx src/pages/cores/__tests__/settingsTts.test.tsx src/pages/cores/__tests__/settingsLeave.philo17.test.tsx src/pages/cores/__tests__/runtimeIdentity.test.tsx --maxWorkers=2
exit 0
```

Collection proof: `.tmp/settings-primitives/adoption-collect-final.log`.
88 tests: Settings app 41; Calendar 22; People 8; TTS 5; leave 2; runtime 10.

```text
.venv/bin/python .tmp/settings-primitives/locked.py adoption-focused --web ./node_modules/.bin/vitest run src/desk/__tests__/settings.app.test.tsx src/pages/cores/__tests__/SettingsCalendar.test.tsx src/pages/cores/__tests__/settingsPeople.test.tsx src/pages/cores/__tests__/settingsTts.test.tsx src/pages/cores/__tests__/settingsLeave.philo17.test.tsx src/pages/cores/__tests__/runtimeIdentity.test.tsx --maxWorkers=2
exit 0
Test Files  6 passed (6)
     Tests  88 passed (88)
  Start at  22:59:07
  Duration  16.43s (transform 1.41s, setup 291ms, import 2.60s, tests 18.21s, environment 1.12s)
```

Run proof: `.tmp/settings-primitives/adoption-focused.log`. No corrective
focused run was needed. `git diff --check` returned no findings before the
run. No build, install, broad tests, staging, or commit was performed by this
lane. Shared surface implementation/tests/contract/barrel/canvas were owned
by the kit worker and not changed by this lane.

## Producer correction batch

The root's `voice-first-1440` producer observation found Add symbol sent
`{spoken:"", symbol:"", attach:"none"}` and received HTTP 400. The required
fields are checked by `holdspeak/config/meeting.py:335` and `:339`. The
initial test mock accepted these invalid rows, so its first green did not
prove that Add worked against the producer.

The Settings app mock now refuses blank required fields before mutation.
The revised symbol regression advances 800 ms after Add and after a partial
phrase and requires **no PUT**. Complete fields must queue the exact array,
and armed Forget must persist the empty array. A second regression keeps a
newer incomplete row through an unrelated accepted write, symbol write
failure, Back, and Retry of the older valid payload.

Collection: 42 Settings app tests, exit 0, in
`.tmp/settings-primitives/symbols-draft-collect.log`.

```text
.venv/bin/python .tmp/settings-primitives/locked.py symbols-draft-red --web ./node_modules/.bin/vitest run src/desk/__tests__/settings.app.test.tsx --maxWorkers=2
exit 1
Test Files  1 failed (1)
     Tests  2 failed | 40 passed (42)
  Duration  15.88s
```

The two failures reproduced the cause: Add had already sent one PUT at
800 ms, and an unrelated language change stayed at `auto` because its batch
contained the invalid symbol row. Full RED proof:
`.tmp/settings-primitives/symbols-draft-red.log`.

The bounded correction keeps `spokenSymbolsDraft` on `SettingsFace`, outside
the settings document. Add only extends that buffer. A complete patch or
Forget result uses the existing `update`; incomplete entries never enter
the queue. A quiet **Draft** fact stays beside Add until an authoritative
matching array has no exact-path pending, debounced, or failed write. The
existing writer, revisions, Retry, and leave flush are unchanged.

The same batch flattens the TTS chip, Download, receipt, and error nodes
directly into shared group actions, removing the retained nonwrapping
wrapper. It changes only the inset child padding to `6px 10px 10px`:
`window-chrome.css:662` already gives the host 12 px top and 14 px side/bottom
(`styles/tokens.css:299`). This restores 24 px total side padding without
changing global window geometry.

```text
.venv/bin/python .tmp/settings-primitives/locked.py symbols-draft-green --web ./node_modules/.bin/vitest run src/desk/__tests__/settings.app.test.tsx --maxWorkers=2
exit 0
Test Files  1 passed (1)
     Tests  42 passed (42)
  Start at  23:09:04
  Duration  18.09s (transform 797ms, setup 63ms, import 1.01s, tests 16.75s, environment 189ms)
```

GREEN proof: `.tmp/settings-primitives/symbols-draft-green.log`.
This correction reran only the owned Settings app file, as briefed; it does
not claim the earlier six-file batch was repeated after the correction.
Product source is frozen for root's new production build.

After the 42-test GREEN, root requested the final producer normalization
correction. Matching trims the draft spoken phrase and trims/lowercases its
attachment before comparison with the authoritative row. Validation requires
a nonempty trimmed spoken phrase and a symbol of nonzero length, preserving
the producer's valid literal-space output. Inputs remain raw until server
acceptance. These final literal expression changes were **not rerun by this
lane**, as root directed; root's actual outer-space-phrase/literal-space-
symbol case and quick check cover that final source. Product source is now
frozen again.

## Remaining root verification

Root owns production build, 1440/393 producer shots, pointer ownership, and
live acceptance. This lane makes no visual or owner-desk green claim.

The TTS wrapping risk is fixed in the correction batch and awaits root's
controlled installed/missing-model capture without an actual download.
The final normalized-match and literal-space-symbol expressions await
root's actual producer case and quick check; the lane's 42-test GREEN
predates those exact expression corrections.
