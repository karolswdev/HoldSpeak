# Decision save and folded Send — worker handover

**HOLD FOR SHIP.** Built in `wt-decision-delight-20261015` from
`c910cd580`, to this folder's settled DESIGN.md and root's read canvas.
No staging, commit, build, browser, install, real dispatch or owner-state access.

Tuesday: the architect reads one decision, opens Send deliberately, and keeps
all three draft fields through a refused or delayed save. Tenets 2/3/5/6/7.

## Changes

- `DecisionPullout.tsx`: Done awaits the existing `updatePrimitive` boolean.
  A synchronous ref blocks double presses and conflicting status writes.
  Done/Cancel/status are disabled while the body write is pending; fields stay
  editable. Only an accepted unchanged draft closes. A later edit remains in
  the editor after an older accepted write.
- The in-window `Save failed` fact reads the existing global subject failure
  through `currentWriteFailure`/`subscribeWriteFailure`. The existing desk
  receipt remains the only body-save Retry and retains its exact original
  patch. Its successful Retry clears the local failure fact without replacing
  later local input. No store or receipt-hook edits.
- One `SendWellsFold` in the existing Send species shares one sends read with
  the actual existing `SendWell` and `SendHistory` composition. Both decision
  adapters use it. Destinations and ordinary previews mount on Send. Nonzero
  prepared/running work, ended sends, refused outcomes and read Retry remain
  discoverable folded. Held/busy presses keep the well open and disable Hide.
- DeskDecision passes a stable JSON signature of title, accepted visible
  status, deciders, three body fields and alternatives through existing
  `doc.version`. Ordinary previews refresh on that signature; prepared bytes
  stay frozen. Brief/Artifact/Note adapters and all dispatch authority stay
  unchanged. The new host is documented in the existing species contract.

Nine existing files changed: the pullout, document adapters, Send species,
sub-barrel/CSS/contract, decision app tests, species tests and the old decision
face tests' boolean mocks. No sibling compositor files were edited here.

## Focused proof

All runs used root's `.tmp/decision-delight/locked.py`, isolated HOME and the
machine test lock. Exact five files: decision.app, philo301DecisionFace,
philo301DecisionNoLoss, philo605DecisionBodyDiagnosis and species SendWell.

Initial RED, before product edits: `.tmp/decision-delight/decision-red.log`:

```text
Test Files  2 failed | 3 passed (5)
Tests       8 failed | 57 passed (65)
Duration    3.15s
```

Double Done submitted two writes; refusal and pending success dismissed the
editor; both hosts eagerly mounted Send; no folded prepared chip/Send toggle.

Final GREEN: `.tmp/decision-delight/decision-green-2.log`:

```text
Test Files  5 passed (5)
Tests       65 passed (65)
Duration    3.77s
```

An intermediate run had three test assumptions corrected: wait for the
refused boolean/refresh to settle before expecting enabled Done; answer sends
with its real `{sends: []}` envelope; scope ordinary versus prepared preview
body queries. No new product behavior was weakened to make those pass.
The app fixture previously answered an unhandled sends GET with `{}`. The
real wire correctly rejects that malformed answer, and the new folded host
correctly exposes its read Retry. Returning the actual empty-sends envelope
removed that fixture failure; a separate regression case deliberately
refuses the sends read and proves its visible Retry while folded.

Collection: `.tmp/decision-delight/decision-collect.log`, exit 0. Eight new
collected cases:

1. Done waits for one write and disables conflicting status and cancel presses.
2. A refusal keeps all fields; the existing exact Retry cannot replace a newer draft.
3. A successful older save keeps fields typed while it was pending.
4. Desk decision reads sends folded and reads destinations/preview only after Send.
5. Decision record has the same folded behavior.
6. A folded sends-read failure has exact read Retry without opening destinations.
7. Prepared work is visible folded; its frozen payload survives ordinary version change.
8. Hide cannot conceal a held send; Retry retains command and destination.

Existing no-loss immediate reopen, optimistic body/refresh races, exact
document dispatch, prepared Send/Discard/result and preview-refusal cases pass.

## Boundaries for root verification

Root owns actual hub glass, 1440/393 shots, typecheck/build and quick check.
This worker's proof is T2 over the existing real store/wire adapters and test
transport doubles. No live dispatch, external provider, clipboard or hardware
action was performed.

The pullout's existing contract still unmounts Send while editing a stored
decision. Hide is blocked for a held press. Explicit Edit/Back preserves the
existing per-document held state; reader remount automatically opens the
existing exact Retry. Root accepted this existing boundary; no additional
Edit/send controller interlock was added.

**Product and tests frozen after the 65/65 run; awaiting root SHIP.**

Final kit adjustment requested by root: both `Saving decision` and `Saving
status` use the existing `StateChip state="working"` pending state. No new
animation or controller. Re-ran the same exact five files under the same
isolated HOME/lock: `.tmp/decision-delight/decision-green-final.log`, exit 0,
5 files / 65 tests passed, 4.06s. Product and tests frozen again.

Root's TypeScript run then identified eight test queries with unsupported
`ByRoleOptions.exact`. All eight now use anchored `/^Send$/` or `/^Hide$/`
names, preserving full-name matching. Product source was unchanged. Same-five
collection exited 0 (`decision-collect-final.log`); same-five run passed
65/65, 5 files, 3.90s (`decision-green-typed.log`). Both logs are under
`.tmp/decision-delight/`. Frozen for root's TypeScript re-check and SHIP.

Root's finished-source review found that status failure Retry was still
enabled while a body save was pending, although the writer guard refused
its press. The existing pending-save regression now first creates a status
refusal, then asserts that status choice, its Retry and Cancel are disabled
through the body write; Retry cannot submit another status request. This
reproduced RED in the same five files: 1 failed / 64 passed, specifically the
enabled status Retry (`decision-status-retry-red.log`). One product line now
uses `disabled={savingStatus || savingDecision}` for that Retry, matching the
status choice. Same-five GREEN: 65/65, 5 files, 4.03s
(`decision-status-retry-green.log`). Logs live under `.tmp/decision-delight/`.
No broader changes; frozen for root runtime re-check and SHIP.
