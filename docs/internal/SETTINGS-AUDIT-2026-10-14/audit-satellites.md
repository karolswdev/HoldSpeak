# Settings satellites — audit and repair

Status: DRAFT, implementation frozen for root integration and production review.
Base: `eef72f987` (#1203). Worktree: `wt-settings-audit-20261014`.
Source audit only before implementation; no owner HOME, DB, calendar,
Keychain, clipboard, microphone or other machine state was read or changed.

The Tuesday job is to connect an account, choose a calendar, keep a destination
draft, set identity/access and recover from failure without internal lore.
Repairs apply Tenets 2/3/4 (first use, clear action, simple words), use the
existing framework under Tenet 5, and avoid a new configuration system under
Tenet 1. Current Engines/Switchboard behavior was retained.

## Coverage

| Surface | States audited / repaired | Limits |
|---|---|---|
| Accounts | Initial read, failed read, GitHub sign-in/copy/check, Jira/Confluence empty/populated/Add/refusal, long site and wrapping actions | No new account edit or removal capability; actual clipboard was not exercised |
| Calendar connection | Existing onboarding chooser in Accounts; permission/refusal comes from existing CalendarCard; explicit native Refresh name, including disabled sources | Settings-only optional mode; existing first-use eligibility retained; backend source preservation is another lane's proof |
| Destinations | Folder, GitHub, Jira, Confluence, email, Slack; add/edit/check/park/remove; missing account, unread account, invalid required fields | Draft remains mounted while the real Accounts Add/Show opens; no channel expansion |
| Identity | Pending/failed initial read, Retry, name/aliases, refused write, leave flush and newest-wins | Both Settings and FirstRun expose read state; hook rejects writes until an initial read succeeds |
| Agent access | Off/read/read-and-write; environment lock; refused write/read Retry; one outcome receipt | Source variable is in Details; existing authority API remains unchanged |
| Wallpaper | Existing preview/selection and keyboard behavior | Inactive sound/motion switches and descriptions removed per `DESIGN-words.md:412`; duplicate Places registration was outside this lane |
| Speech | Browser support, absent server extra, read failure/Retry, model download/accepted result | Support reports browser API presence; no real speech/download was performed |
| Guide | Failing/warning/known/unknown/empty/failed read; repair actions and Retry | Known checks are required for the ready headline; readable wrapping is main lane's `settings.css` seam |
| Engines | Bounded source review of existing add/check/trial/result/egress and Settings hosting | No Switchboard redesign or additional engine tests in this lane |
| Voice, devices, remote access | Ownership mapped to main Settings modules | Main face lane owns these controls and their production verification |

## Causal repairs

- `connections/api.ts` propagates failed reads/checks. They no longer become
  empty configuration or a null successful result.
- `ConnectionsPane.tsx` awaits accepted Add before clearing Site/Email, names
  Add/check failure, keeps populated Add available, and reports clipboard
  outcomes only after the promise settles. Identity and action layout wraps.
- `Destinations.tsx` distinguishes loading/unread/missing accounts. Its Retry
  refreshes Accounts and destination account facts; the form stays mounted.
  Missing-account setup opens the existing Add or GitHub Show control.
  File/email/Slack remain independent of a failed account read. Required
  fields/key/webhook gate Save; existing server refusal validation remains.
- `ownerName.ts` blocks setters and saves until read success and exposes
  loading/read error/reload. Settings and FirstRun show existing SurfaceState
  and Retry. Write refusal retains the pending edit for retry.
- CalendarCard adds optional Settings-only native reselection and prewrite
  callback. `calendarStep.use()` returns acceptance; refused writes never
  notify the parent. An accepted write still notifies it when a later read
  fails. Main's prewrite callback flushes its save queue; its postwrite
  callback reconciles authoritative settings plus pending edits.
- Guide unknown/read failure never says everything is ready. TTS read failure
  never claims the optional server package is absent. Wallpaper hides controls
  with no live Desk effect.

## Native direction

`satellite-canvas/` composes the actual Button, gadgets, chips, wells, footer,
Desk/window/interior CSS and light window fill. Root inspected the corrected
1440/393 Accounts, People and Guide artboards and settled direction before
product edits. Canvas shots are under `.tmp/settings-audit/canvas-shots/`.
Canvas values are synthetic; these images are not production verification.
Root owns the production screenshots, combined quick check and deployment.

## Focused proof

Every command used `.tmp/settings-audit/locked.py`, isolated HOME, the shared
test lock, Vitest 4 and `--maxWorkers=2`.

- `satellites-collect.log`: initial named regression collection, 66 tests.
- `satellites-red.log`: 12 failed / 54 passed; reproduced original hidden
  failures, lost drafts, false readiness and unsupported Wallpaper controls.
- `satellites-green.log`: first repair run, 67 passed / 3 failed. The two old
  destination tests used cold accounts; they now use the existing recorded
  checked-account fixture. The third expectation omitted its mock's `Error:`.
- `satellites-corrected-green.log`: **8 files, 78 tests passed**, 4.03 seconds.
  Files: connections-pane, destinations.app, slackDestination, settingsPeople,
  settingsWallpaper, guide.refit, ownerNameFlush, settingsTts.
- `satellites-firstuse-collect.log`: two exact OneScreen cases collected.
- `satellites-firstuse-green.log`: **2 passed / 27 skipped**, 1.28 seconds:
  unread owner read/Retry and existing calendar selection/default eligibility.

Root then diagnosed the destination account-read/Setup ambiguity. The final
small repair tracks read error/loading, exposes Retry, withholds missing-account
setup until the read is known, and opens GitHub's actual Show control. Its
regression is in `destinations.app.test.tsx`; no further broad suite was run
under the lane budget. Root's final combined quick check covers this last edit.

No staging or commits. Hold for SHIP.

## Final author fix round — review findings 2, 3, 5 and 6

The bounded independent source review is `review.md`. Its four satellite
findings were reproduced with seven named cases from existing files, then
fixed in one batch:

- Settings-only CalendarCard shows native Allow / System Settings recovery
  when an existing feed is in use. Default FirstRun guards remain unchanged.
- Calendar URL Add uses the same prewrite gate and accepted-write callback
  as native selection. A refused gate sends neither Check nor Use.
- `calendarStep.addUrl()` returns the actual Use acceptance. A refused Use
  keeps the typed URL and does not notify the parent or clear the field.
- The active Project Room Door controller catches a rejected shared account
  check, names the provider's failure in its existing error surface, and
  retains the failure through the subsequent connection refresh.

Proof uses the same isolated HOME / lock / Vitest4 / two-worker helper:

- `satellites-review-collect.log`: seven exact cases collected in
  `connections-pane.test.tsx`, `OneScreen.test.tsx`, `DoorCore.test.tsx`.
- `satellites-review-red.log`: **5 failed / 2 passed / 99 skipped**, plus the
  reproduced Door unhandled rejection.
- `satellites-review-green.log`: **7 passed / 99 skipped**, three files,
  1.61 seconds. Permission recovery with an existing feed is covered for
  not-determined and denied access; actual OS actions are doubles.

This author fix round adds only CalendarCard/calendarStep/Door-controller
changes and the focused assertions. Product, tests and this record are frozen
again for root's combined quick check, production captures and independent
source re-check. No native prompt, CLI, network, owner state or clipboard was
used by these checks.
