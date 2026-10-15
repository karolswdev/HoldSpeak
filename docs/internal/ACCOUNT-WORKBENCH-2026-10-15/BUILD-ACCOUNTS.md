# Accounts build — 2026-10-15

Status: DRAFT, HOLD FOR SHIP. Root owns source review, actual 1440/393
screens and geometry, quick check, and release. The worker staged and
committed nothing.

## Result

The Accounts ledger now uses identity/email on row 1, the full wrapping
state/check age on row 2, and account actions on row 3. The existing
StateChip wrap variant contains long words. The last Jira/Confluence
account row owns its Add action and the existing SurfaceWell; the detached
Add list row is removed. An empty provider retains its actual provider row.
Within provider actions, the host, Recheck and Add share one wrapping flex
group: the nested check wrapper uses `display:contents`. At narrow widths
the host can take a line while Recheck and Add can remain together when
their combined width fits. Root verifies the actual geometry.

Only site/email draft state moved to AtlassianCards. AddAccountFields has
optional controlled draft inputs and retains local defaults for its other
callers. The Add form stays mounted behind native `hidden` while closed or
on an existing account's sign-in detour, retaining its DOM identity,
pending state, refusal, and Retry. This applies to populated and empty
providers. Hidden inputs leave the accessible focus order; scoped layout
rules remove the closed expansion's empty space and open tint. A refused
Add stays open with its values and Retry. Successful Add clears
only fields still equal to the submitted values, preserving newer edits.
Provider Recheck routes, selected connection-ref busy state, Add route,
following refresh/check, existing focus selectors, sign-in commands and
host badges remain in their existing paths.

Anchors (verify after later edits):

- `web/src/pages/cores/connections/connections.css:6`: three row composition.
- `web/src/pages/cores/connections/ConnectionsPane.tsx:247`: provider row
  actions and shared expansion.
- `web/src/pages/cores/connections/ConnectionsPane.tsx:275`: optional draft
  inputs, local defaults, and accepted field clearing.
- `web/src/pages/cores/connections/ConnectionsPane.tsx:338`: draft ownership
  and last-account Add placement.
- `web/src/desk/__tests__/connections.app.test.tsx:165`: focused checks.

## Scoped checks

All vitest calls used the isolated HOME/machine lock runner from DESIGN.md:

```sh
.venv/bin/python .tmp/account-workbench/locked.py accounts_recovery_collect_final --web ./node_modules/.bin/vitest list src/desk/__tests__/connections.app.test.tsx src/pages/cores/__tests__/connections-pane.test.tsx --maxWorkers=2
.venv/bin/python .tmp/account-workbench/locked.py accounts_recovery_green_final --web ./node_modules/.bin/vitest run src/desk/__tests__/connections.app.test.tsx src/pages/cores/__tests__/connections-pane.test.tsx --maxWorkers=2
```

The initial collect listed 6 cases. With the first 6 additions and before
product changes, `accounts_red.log` reported `4 failed | 8 passed (12)`:
missing wrap, detached form in two checks, and unsupported controlled
draft inputs. `accounts_green_first.log` then reported `12 passed (12)`.
The final collect listed 13 cases, with one more default-input check.
After flattening the action wrapper, `accounts_green_flatten.log` reported
the same 13 cases green. That scope missed an existing contract: the
quick check found that existing account sign-in detours must retain the
Add form's DOM identity and refusal/Retry state for Jira and Confluence.
The first implementation remounted that form and lost those states.

The initial 7 new app cases cover wrapping chips/last-row Add, draft
Cancel/sign-in switching, provider Recheck route/selected-ref busy state,
refused Add/Retry/accepted refresh, Recheck failure/Retry, default local
fields, and accepted versus newer pending edits. The existing 6 cover
per-row ages, empty-provider states, GitHub Recheck, sign-in source, and
the cold face. Root then expanded this worker's exact test budget to
include `connections-pane.test.tsx`; that existing file was not edited.

The expanded pre-fix run reproduced `2 failed | 61 passed (63)` in
`accounts_recovery_red.log`, at the existing sign-in detour DOM identity
assertions. Keeping the form mounted fixed those 63 cases. Root also
requested empty-provider parity: two additional app cases assert Jira
and Confluence refusal/Retry and DOM identity across Cancel/reopen. They
first failed with `2 failed | 63 passed (65)` in
`accounts_empty_recovery_red.log`, then passed after the empty-provider
form used the same lifetime. App assertions also check that hidden Add
textboxes are excluded from accessible role queries.

The final collect lists 15 app cases and 50 existing pane cases, 65 total.
`accounts_recovery_collect_final.log` contains the exact collected names;
`accounts_recovery_green_final.log` contains the final run. Logs are in
`.tmp/account-workbench/`.

Final run tail:

```text
 Test Files  2 passed (2)
      Tests  65 passed (65)
   Start at  10:05:17
   Duration  4.46s
```

`git diff --check` passed. Only these two approved files ran in this lane.

## Limits

Vitest proves state/row composition and behavior, not CSS fit or actual
pointer geometry. The worker took no browser shots and made no claim
about live 1440/393 fit, real provider availability, or owner desk state.
Only fetch was replaced for app checks; reads/checks replay recorded hub
answers. Direct field tests exercise their callback without a hub.

Saving/failure state stays local to the mounted form; no new controller
or shared species was introduced. Site/email also remain in provider
draft custody when the last account row changes after an accepted Add.
