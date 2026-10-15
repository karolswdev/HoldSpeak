# Settings visual revision — satellites

2026-10-14 · **HOLD FOR SHIP** · Root owns production capture and final review.

## Direction and implementation

The owner kept Workbench and rejected the previous composition. This build
follows `VISUAL-REVISION.md` and the corrected native Accounts canvas viewed
by root. It uses existing window, ledger, well, field, fold and Button species.

| Surface | Composition | Preserved behavior |
| --- | --- | --- |
| Accounts | Provider name and account lead one ledger grammar. Commands open by Sign in/Details. Never checked has direct Recheck; degraded has Retry. Full host appears once beside the check action. Add fields, refusal and Retry stay together. | Existing read, check and Add handlers; accepted writes and retained refused drafts; awaited clipboard; provider focus. |
| Calendar chooser | Settings `reselectNative` uses the chooser without the first-use card, repeated title or explanatory line. | Native access/denial actions, URL draft, save gate, accepted-use callback, disabled-source name refresh. Default FirstRun still uses its original Card. |
| Destinations | Named destination with quiet target, channel/state and Details. Egress remains at the actual Check/Save boundary. Long editors fill the value column. | Save gates, account read Retry, missing-account setup, mounted destination draft, park/check/edit flows and built-in protections. |
| People | Wide name/alias editors, plain body facts for started-agent access. | Owner read guard/save queue, refusal Retry, environment access lock, one outcome. |
| Speech | Paired browser/server facts. Missing installation command and installed dependency detail fold under Details. | Unknown/read failure Retry, browser feature probe, model download/receipt/egress. |
| Guide | Shared body/type hooks, readable named facts and row separation. | Known/unknown/error headline, actual fix actions, command/raw folds, Retry. |
| Wallpaper | Existing picker with shared two-column phone gallery and sans identity; quiet selection label. | Live persistence, selection and keyboard traversal; no inactive sound/motion controls. |

Main lane owns shared typography, Accounts/People column wrappers and the
Wallpaper/Guide material rules. Satellites did not edit shared settings CSS,
the settings writer/API, FirstRun eligibility, or the shared project-room
SignInWell default command behavior.

## Focused proof

All runs used `.tmp/settings-audit/locked.py`, isolated HOME, the shared test
lock, Vitest 4.1.9 and `--maxWorkers=2`.

- Collection: 139 named tests across the eight authorized files;
  `.tmp/settings-audit/visual-satellites-collect.log`.
- Red: three new composition regressions failed as expected (provider
  identity, explicit sign-in well, folded server install detail);
  `visual-satellites-red.log`.
- First focused run: 100 passed, eight failed across two files. Failures were
  stale DOM scope/visibility assertions: a ledger line's open well is its
  sibling; a closed native details fold keeps its children mounted.
  `visual-satellites-green.log`.
- One corrective run: Connections pane and Speech, **44 passed**;
  `visual-satellites-corrective.log`. The other five authorized files had
  already passed (64 tests). Final focused coverage: **108 passed**.
- FirstRun preservation: URL-use refusal retains draft; existing-feed native
  permission guard unchanged; found calendar Use/receipt contract —
  **3 passed, 28 skipped**; `visual-satellites-firstrun.log`.
- `git diff --check` passed for this lane's product and test paths.

Test paths: `connections-pane.test.tsx`, `destinations.app.test.tsx`,
`DoorCore.test.tsx`, `settingsPeople.test.tsx`, `settingsTts.test.tsx`,
`guide.refit.test.tsx`, `settingsWallpaper.test.tsx`; the three named cases
in `OneScreen.test.tsx`.

## Visual evidence and limits

Corrected canvas evidence:
`.tmp/settings-audit/canvas-v2-shots/satellite-canvas-v2-{populated,refused}-{393,1440}.png`.
Both phone states were inspected. The canvas measured two email lines in
295px identity width, 44px actions, 113px populated provider rows and no
horizontal overflow. Calendar ended at y=693 in populated393. Root then
captured and viewed the native canvas independently before authorizing build.

These are canvas measurements, not production acceptance. Root still owns
fresh production captures, combined quick verification and the finished
source check. No native OS, owner account, clipboard, real network, DB or
keychain operation was performed by this lane. No broad suite was run.

## Frozen files

- `web/src/pages/cores/connections/ConnectionsPane.tsx`
- `web/src/pages/cores/connections/connections.css`
- `web/src/pages/cores/connections/Destinations.tsx`
- `web/src/desk/firstrun/CalendarCard.tsx`
- `web/src/pages/cores/settingsPeople.tsx`
- `web/src/pages/cores/settingsTts.tsx`
- `web/src/pages/cores/settingsWallpaper.tsx`
- `web/src/pages/cores/RuntimeDocsCore.tsx`
- `web/src/pages/cores/__tests__/connections-pane.test.tsx`
- `web/src/pages/cores/__tests__/settingsTts.test.tsx`
- This record and the `satellite-canvas-v2/` design files.

No staging or commit. Hold for root.

## Finished review — one bounded fix round

`review-visual.md` found three source transitions/layout mismatches. The fix
touches only ConnectionsPane, Destinations and their two authorized test files.

1. Populated Atlassian Add forms now stay mounted in a local hidden well while
   an existing account's sign-in/details is visible. Site, Email and the failed
   outcome survive the detour; no draft manager or shared form API changed.
   The empty-account branch still changes after a confirmed Add, which may
   clear a completed draft.
2. A collapsed Atlassian row shows the full site as identity when the check
   host is inside a closed sign-in/details well. Opening that well removes
   the extra identity line. It is plain identity, not an egress claim.
3. Parked destination facts now use `.surface-ledger-cells`, as required by
   the named destination grid. Name, long target and parked date remain;
   no park/remove behavior changed.

Focused proof, same isolated locked Vitest4/maxWorkers2 helper:

- Collection: 60 tests in `connections-pane.test.tsx` and
  `destinations.app.test.tsx`; `visual-satellites-review-collect.log`.
- Red: seven new cases failed as expected: Jira/Confluence draft + refusal
  detours, both providers' same-email/different-site recovery identities,
  and parked long-target cells. `visual-satellites-review-red.log`.
- First run: 58 passed, two test assertions failed (mounted but hidden
  command contents; incorrect parked channel literal).
  `visual-satellites-review-green.log`.
- One corrective run: 59 passed; all account regressions passed. The remaining
  parked test still expected `FOLDER`; the actual rendered channel literal is
  `FILE`. That test-only literal was corrected from the failure DOM afterward.
  `visual-satellites-review-corrective.log`.
- No further worker run, respecting the one-corrective limit. Root's combined
  quick must cover the final literal correction. This round is **not claimed
  fully green** from worker evidence.
- `git diff --check` passed for the four changed paths.

Product and tests are re-frozen. Root still owes the actual parked long-target
walk at393 and the final review re-check. No staging or commit.

### Production parked-path follow-up

Root's actual393 parked walk passed grid/overflow checks, but the inspected
`accounts-visual-complete-393/destination-parked-long-target.png` showed the
target still clamped with an ellipsis. The inherited channels `.send-target`
rule clamps two lines; parked rows have no expanded detail door. One local
`connections.css` rule now scopes to parked destination rows, removes that
clamp and hidden overflow, and lets the full target wrap. No other composition
or behavior changed. No test/build was run for this source follow-up, as
directed; root's final build/quick/capture owns verification. Re-frozen.

### Slack test compatibility follow-up

Root's combined quick exposed D3's old collapsed-row host expectation in
`web/src/features/channels/__tests__/slackDestination.test.tsx`. Test-only
repair now checks the collapsed Slack/name identity, opens the actual Details
action and verifies visible `HOOKS.SLACK.COM` beside Check. The destination
check-only POST/no-send assertion and webhook/key/unknown/refusal coverage are
retained; the body is also checked for absence of the synthetic secret.

The same isolated locked helper collected eight tests
(`visual-slack-compat-collect.log`); one focused run was **8 passed**
(`visual-slack-compat-green.log`, Vitest4.1.9/maxWorkers2). No corrective run,
product edit or build. Test and record re-frozen; hold for root.
