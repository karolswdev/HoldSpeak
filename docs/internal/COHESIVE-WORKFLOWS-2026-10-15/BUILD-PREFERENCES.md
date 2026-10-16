# Preferences and context — build report

Status: HOLD FOR SHIP. Lane B; base `7f3345745`, branch
`feat/cohesive-workflows-20261015`, worktree
`/Users/karol/dev/tools/wt-cohesive-workflows-20261015`.

Direction: [DESIGN.md](DESIGN.md), the Constitution's Seven Tenets and
UX-CANON. Tuesday: keep a newer draft, act once on the selected account,
release this window's mic, and see the accepted Thought result or a real
failure with a usable retry.

## Changes

- Connections forwards the selected account through the existing `{ ref }`
  Recheck body. One synchronous pending owner blocks competing actions.
  Failure Retry keeps that account. A read generation protects both rows and
  footer from older successful or failed reads.
- Runs on releases only a capture whose startup succeeded in this host. A
  startup that resolves after close releases its capture without transcribing.
  An idle or refused host cannot cancel the successful host's capture.
  At Stop, ownership ends before the transcription await: closing this host
  or receiving a late failure cannot cancel a later host's capture.
  The shared transcription helper releases the server floor in `finally`
  after success, failure or empty capture, unless a newer hold owns it.
- The calendar well binds Save completion to its editor/draft generation.
  Saving A cannot close or mark newer B as refused. Save uses library loading;
  an accepted write and failed calendar read retain separate outcomes.
- The older context picker uses StringGadget, SurfaceSection, a kit ledger
  with SRC leads, SurfaceWell, SurfaceState and library Buttons. Search keeps
  its existing mic replacement behavior; Note answer append behavior stays
  with PadGadget. The picker supplies a named surface container for its rows.
- Request IDs have guarded local memory fallbacks in the older picker/Note
  actions and the active ThoughtReadsWell/workspace actions. Failed writes
  reuse their ID. Accepted writes apply even if storage cleanup refuses;
  a local cleared marker prevents reusing a stale accepted ID.
- The older Note review path distinguishes named 409 conflicts from other
  failures. It installs an actual current aggregate or rereads ownership;
  failed reads never claim the latest Note is shown. Other failures retain
  the answer and usable action. Both top-level `current` from the existing
  route and the older nested form are read.
- The active Add a note well separates loading, read failure/Retry and true
  empty. Its existing checkbox/search material is retained.

Root granted ThoughtReadsWell, workspace stableId/cleanup call sites, and
their focused tests after the live host census showed owned Thoughts open
the workspace. NotePullout/ThoughtContextPicker are the older host; this
report makes no claim that they are the normal owned Thought face.

## Focused proof

Every invocation used `.venv/bin/python .tmp/cohesive/locked.py LABEL --web`
with `node node_modules/vitest/vitest.mjs`, isolated HOME and the machine
lock. No native capture, owner DB, provider or tmux was used.

Final union: 243 tests across nine files. Initial collection is
`.tmp/cohesive/preferences-memory-final-collect.log` (215); finished-source
counsel collection is `.tmp/cohesive/preferences-counsel-collect.log` (132),
which supersedes Runs on's count and adds the three granted test files.

| File under web/src | Collected | Passing proof |
| --- | ---: | --- |
| pages/cores/__tests__/connections-pane.test.tsx | 54 | preferences-counsel-final.log: part of 132 passed |
| pages/cores/__tests__/SettingsCalendar.test.tsx | 26 | preferences-calendar-final.log: 26 passed |
| features/runson/__tests__/runsOn.test.tsx | 52 | preferences-counsel-final.log: part of 132 passed |
| desk/pullouts/NotePullout.test.tsx | 36 | preferences-thoughts-memory-final.log: part of 85 passed |
| desk/thought-workspace/ThoughtReadsWell.test.tsx | 6 | preferences-thoughts-memory-final.log: part of 85 passed |
| desk/thought-workspace/ThoughtWorkspaceWindow.test.tsx | 43 | preferences-thoughts-memory-final.log: part of 85 passed |
| desk/__tests__/connections.app.test.tsx | 15 | preferences-counsel-final.log: part of 132 passed |
| lib/__tests__/micOwner.test.ts | 5 | preferences-counsel-final.log: part of 132 passed |
| lib/__tests__/speakToFill.test.ts | 6 | preferences-counsel-final.log: part of 132 passed |

Representative collected regressions:

- `sends the selected account through the existing ref wire key`
- `ignores a stale account read response after the latest rows and footer arrive`
- `releases a capture that finishes starting after this host closes`
- `closing idle or refused hosts leaves another host's capture alone`
- `keeps a newer another source draft when the earlier Save succeeds`
- `keeps an accepted Save distinct from a failed calendar reread`
- `keeps the answer and retry identity when storage getItem and the review write fail`
- `does not claim a latest note when a superseded review cannot be reread`
- `reuses its attach request after storage getItem and transport refuse`
- `applies the accepted detach receipt even when cleanup refuses`
- `installs the accepted active answer when request cleanup refuses`
- `keeps the new action ID across set denial after accepted cleanup left an older stored ID`
- `closing a transcribing host leaves a newer capture alone after late failure`
- `a rejected transcription releases its floor when no later hold owns it`
- `late transcription success neither releases nor aborts a newer hold`

Initial six-file run: 207 passed, two Connections failures. The new test
queried only the row line, while its opened well is a sibling; that left a
deferred mock unused and affected the next test. The test now queries the
enclosing row. The 54-test Connections rerun passed. Final Thought and
calendar additions were collected and run separately as shown above. Root's
local review found that a readable stale storage value could replace a newer
memory ID after cleanup and set both refused. All four local helpers now
consult storage only when the memory Map has no entry. The exact sequence is
the final Reads regression; all 85 Thought tests passed after that change.

`git diff --check` on owned paths passed. No staging, commits or pushes.

## Limits

The root owns TypeScript/build, full quick check, 1440/393 shots and the live
task walk. This worker ran only the nine named vitest files and makes no visual,
real microphone, provider, owner-data, full-suite or deployment claim. The
storage fallback lasts for the current browser runtime; it is not durable
across page reloads when the browser denies storage. Capture ownership uses
successful startup in this host; the shared capture API was not redesigned.

## Finished-source counsel — round 1

The reviewer found that Stop synchronously ends the mic hold inside
`stopAndTranscribe`, before awaiting the transcription response. Keeping
`ownsCapture` true across that await let closing the old Runs on window cancel
a newer host's hold. Ownership now ends at Stop handoff, and the late failure
path does not issue a global cancellation. Two focused regressions cover a
second host starting capture, then the first host closing and receiving late
success or failure. Live-listening close and deferred-start cleanup remain
covered.

Root granted the small shared-helper correction in `speakToFill.ts`, plus
`micOwner.test.ts` and the explicit `speakToFill.test.ts` mock's existing
`holdOwnsFloor` export. Floor release now runs in `finally` after success,
failure or an empty hold. `holdOwnsFloor()` prevents this old transcription
from releasing a newer hold's claim; it never aborts capture. No token/API
refactor. Real micSession state with fake WebAudio proves idle rejection
releases, and late success/failure leaves a newer hold and stream active.
Release remains best effort if the release HTTP request itself fails.

The wider quick check exposed one old Connections app assertion expecting a
peer action to remain enabled during Recheck. Its exact failure is reproduced
in `.tmp/cohesive/preferences-connections-app-reproduce.log` (1 failed,
14 skipped). Root granted the assertion update to the settled single action
owner: only the selected row shows loading, peers are disabled, another peer
press sends no request, and the actual POST body is `{ ref: selected }`.
Existing successful results and refusal/retry tests remain. All five final
counsel files passed: `.tmp/cohesive/preferences-counsel-final.log`, 132/132.

## Actual screenshot amendment — narrow desktop Thought footer

Root's final live screenshot
`.tmp/cohesive/after-final-1440/thought-storage-denied-attach-kept.png` showed
READS: RELEASE CHECKLIST squeezed to approximately 45 px beside the full
desktop action group, breaking words into five fragments. The paired 393
shot retained readable context with the existing Finish/More overflow.

Root approved a CSS-only amendment in `thought-workspace.css`: inside its
existing `@container surface (max-width: 560px)`, a Thought footer that still
contains the full `.surface-footer-verbs-group` uses one column with READS,
the existing wrapping actions, and the receipt on separate rows. Compact
phone footers have no group wrapper and retain their existing allocation.
No controls, action semantics or shared footer component changed.

Focused collection/run: `.tmp/cohesive/preferences-thought-footer-collect.log`
and `.tmp/cohesive/preferences-thought-footer-final.log`: 43 collected and
43 passed existing ThoughtWorkspaceWindow tests. These are behavior
regressions; root owns the
rebuilt screenshots and actual geometry assertions at both widths. This
worker inspected the before shots and makes no after-fit claim from jsdom.
