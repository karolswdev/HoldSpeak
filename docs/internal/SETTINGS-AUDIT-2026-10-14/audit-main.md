# Main Settings audit and repair

Story: [BRIEF.md](BRIEF.md). Base `eef72f987`. Main face lane; HOLD FOR SHIP.
Root settled the native direction before product edits on 2026-10-14.
Tuesday: find an ordinary preference, change it, retain the edit on failure,
and recover without knowing device identifiers or internal wiring.

## Coverage

| Surface | Finding and repair | Evidence / limit |
|---|---|---|
| Home | Ordinary preferences were hidden by More. Rows now follow Engines/Accounts immediately; parked toggle. Default engine uses the settled name. | `settingsPrefs.tsx`, `PrefsFace`; app regression and prior hub journeys. |
| Navigation | Deliberate module/wing changes reset the existing surface body's scrollTop. Saves do not reset it. Engines keeps full available width; ordinary forms cap at 680 px. | `SettingsCore.tsx`, `contentRef` module effect; `settings.css` excludes `models`; root production walk owns geometry proof. |
| Voice | Existing hotkey, language, preview, commands, symbols, and wake controls retained. Operator tuning uses Advanced without a stale count. | `SettingsCore.tsx`, voice case. Hardware discovery not added. |
| Sounds & Presence | Existing toggles retained in compact form. Hosted TTS is repaired by satellite lane. | `SettingsCore.tsx`, sounds case; observed browser support assertion updated in app test. |
| Wallpaper | Hosted existing picker; no main redesign. | `SettingsCore.tsx`, wallpaper case; satellite owns picker changes. |
| Meetings summary | Removed duplicate display banner. One timing control: Manual / After room meetings / After every meeting. Engine facts and existing Engines destination; local blank egress omitted, LAN host retained. Last-run history folds under Advanced. | `SettingsCore.tsx`, meetings case; cold/LAN/off app tests. |
| Recording | Readable default/current microphone and system-audio facts. Custom name overrides in Audio devices fold. Auto-record reads the edited setting, not stale statistics. | Immediate Auto-record app regression. Actual audio capture not run. |
| Calendar | Stored human name and canonical source type; blank native name becomes Mac calendar. No URL/UUID-derived primary name. Name editor preserves native/snapshot URL; read-only source location under Details. All source IDs/disabled states remain in atomic array patch. | Native rename regression asserts only `_revision` and `calendar.sources`, both sources retained and native URI unchanged. Snapshot fallback uses its registered `calendar-snapshots/*.ics` location when disabled sources have no statistics row. |
| Calendar entry | Add calendar opens Accounts with calendar focus; Add feed and Import image retain existing methods. Remove remains behind explicit existing confirmation. | Accepted native setup callbacks coordinated with satellite: flush queued/debounced edits before Use; reconcile authoritative base after accepted Use. Root production walk owns full native chooser proof. |
| Export | Separate group; format shown when Auto export is selected. | Existing app edit/leave journeys and partial-write regressions. |
| Advanced meeting knobs | Retained capture, queue, routing and actuator controls folded. Retry attempts minimum 1. Parked webhook header input because this writer does not persist it. | Source review; backend lane covers persisted fields. No model/actuator effects run. |
| Rhythm | Existing cadence, brief and Telegram controls retained, operator knobs under Advanced. | Backend lane proves persistence; root production walk owns live face behavior. |
| Engines | Retained hosted RunsOnCore, one window/footer, target focus, full board width. | Existing Engines navigation/footer app tests. No new board or route system. |
| Accounts | Secret save/refusal visible through shared main receipt. Secret progress contributes Saving; accepted secret writes reconcile the queued base instead of replacing dirty form state. Credentials and alert secrets remain folded. | Source review; satellite owns account operations and drafts. Root quick check covers the final secret reconciliation followup. |
| System | Removed large duplicate device banner while retaining hooks. Existing remote credentials/grants and reset preserved. Remote/runtime failed reads offer Retry; reads do not paint a false OFF identity. Operator diagnostics fold under Advanced. | Existing remote/grant/runtime app journeys plus failed-runtime Retry regression. No remote authority or reset effect invoked on an owner hub. |
| People / Guide | Existing hosted modules. Guide reason text wraps; a failed main save stays in-body without unmounting Guide or creating a second footer. | Existing Guide navigation/save/retry app tests; satellite owns identity/readiness semantics. |
| Writer / status | PUT includes only changed paths and current revision. Arrays stay atomic. Failed paths overlay the reconciled base until accepted/replaced. Unrelated success retains older failure; newer same-field value wins. Existing queue, conflict fence and leave flush retained. Accepted writes refresh hub/calendar facts without delay timers. Footer receipt contains short state; Back occupies verbs. | New failure/partial-patch regressions; atomic writer unit and leave tests. Root owns combined quick check and live persisted-state verification. |

## Proof

All test commands used `.tmp/settings-audit/locked.py`, isolated HOME, and the
shared machine test lock. Vitest4 ran with `--maxWorkers=2`.

Collected six named files, 74 tests: `.tmp/settings-audit/main-collect.log`.

- `web/src/desk/__tests__/settings.app.test.tsx`
- `web/src/pages/cores/__tests__/SettingsCore.test.ts`
- `web/src/pages/cores/__tests__/settingsLeave.philo17.test.tsx`
- `web/src/pages/cores/__tests__/settingsWords.philo17.test.tsx`
- `web/src/pages/cores/__tests__/settingsSummaryName202.test.tsx`
- `web/src/desk/__tests__/restOfDay.philo1518.test.tsx`

Before repair, the three added initial regressions each failed:
`.tmp/settings-audit/main-red.log`, 3 failed / 29 skipped.

First focused run: `.tmp/settings-audit/main-green.log`, 70 passed / 4 failed.
One implementation error was corrected: LAN egress has `scope=local` but a
nonempty external label; only an empty label suppresses the host chip. Three
test expectations were corrected for expanded source controls and observed
browser voice wording. Corrective run:

```text
Test Files  6 passed (6)
     Tests  74 passed (74)
  Duration  10.39s
```

Log: `.tmp/settings-audit/main-corrective.log`. No wider worker run.
TypeScript completed with exit 0 after satellite callback/types landed.
`git diff --check` had no findings.

Final source followups after this focused green: secret success uses queued
reconciliation and contributes busy status; disabled Snapshot identity retains
the registered source path. Root's combined quick check covers these changes.

## Visual evidence and limits

Native direction sources: [main-canvas](main-canvas/main.tsx), production
GadgetGroup/Row/Cycle/Fold/Section/Ledger/Button/Footer and native materials.
Synthetic content, no claim of real device or model readiness.

- `.tmp/settings-audit/main-canvas-1440.png`
- `.tmp/settings-audit/main-canvas-393.png`

Root viewed both and settled direction before implementation. The direction
canvas is not production geometry evidence; root owns the real 1440/393 walk,
body scrolling, heading visibility, footer reach, and persisted-state checks.
No worker product browser, owner-state, network, microphone, Keychain, external
account, reset, or remote-authority run. No stage or commit.

## Final review fix round

Repaired review findings 1 and 4, plus root's production observations:

- Retry filters older failed tuples whose paths have newer queued or debounced
  values. The ordinary `commitMany` command ordering is unchanged. The exact
  failed A → new B → Retry within 700 ms sequence now retains and sends B.
- Successful secret reconciliation and control-mode changes preserve the
  earlier unresolved preference refusal and its Retry.
- Main-owned footers offer primary Retry while failed preference changes
  remain pending; Settings remains secondary and uses the existing compact
  More behavior. In-body reason and Retry remain, without automatic scrolling
  or focus movement. Guide/Engines retain their own operation footer; their
  failed preference recovery remains in the body, exposed on navigation entry.
- Snapshot import uses the existing canonical host classifier to omit known
  loopback destinations while keeping external LAN/cloud hosts.

Read root's actual `candidate-393/save-refused-draft-kept.png` and
`candidate-393/meetings.png`: footer recovery was absent while the in-body
reason was above the visible scroll region; the import displayed 127.0.0.1.
Root owns the fresh production capture proving these face repairs.

Before the fixes, focused regressions produced 7 failures, 2 passes and 43
skips: `.tmp/settings-audit/main-review-red.log`. The failures reproduced the
newer-value overwrite, hidden earlier failure, missing footer Retry, and four
loopback destination spellings. Collection lists 52 tests in
`.tmp/settings-audit/main-review-collect.log`. The one green run covered the
owned Settings app and SettingsCore unit files:

```text
Test Files  2 passed (2)
     Tests  52 passed (52)
  Duration  12.58s
```

Log: `.tmp/settings-audit/main-review-green.log`. Two test-only compatibility
corrections immediately afterward use `.filter().at(-1)` for the configured
TypeScript target and JSON response headers in the secret/control-mode fixture.
No product source changed after this green. Root's final quick check covers
the final tree. Main lane frozen again; no stage or commit.
