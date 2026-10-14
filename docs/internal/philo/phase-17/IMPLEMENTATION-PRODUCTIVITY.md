# The productive desk implementation

Owner direction, 2026-10-13: "work very diligently, as a master orchestrator"
and "stop making those tiny-ass PRs, I want a huge PR that modifies it for
A LOT BETTER." This explicitly replaces the one-small-PR-per-slice cadence
for this task. One integration branch, one substantial PR, shared verification.

Base: fetched origin/main `1e3bce495`. Worktree:
`/Users/karol/dev/tools/wt-desk-productivity-overhaul`.
Branch: `feat/desk-productivity-overhaul`.

The settled designs are DESIGN-verbs.md, DESIGN-attention.md,
DESIGN-windows.md and DESIGN-words.md; DESIGNS.md resolves their shared
decisions. Workers read those documents and CLAUDE.md's current agreements.
The Seven Tenets govern the result: usable work for an architect with reports,
simple words, the existing component framework and Workbench behavior.

## Outcomes in this PR

- The chosen engine actually powers Ask and notes, with a useful failure
  reason; Room Draft update produces a draft in one press with visible work.
- Settings hosts Engines and stays closed when closed. Desktop windows land
  usefully; phone navigation opens on one tap and returns with Back.
- A meeting has one review, and its confirmed actions reach the correct
  person's prep. Completion survives rereads across these surfaces.
- A note can become a task, join a project, or ground an ask. Search opens
  the object before offering verbs.
- One attention list/count, a reduced dock, meaningful words and user-owned
  desk material replace duplicate surfaces and demo clutter.

Use the designs' recommended defaults. The owner explicitly settled Q1 in
this session: "Inside Meetings, with Back (design recommendation)". This
supersedes the October 10 interpretation that a meeting owns a separate
window. All meeting openers reuse Meetings; Back returns to the selected
list row; a reload retains the current detail. Automatic extraction on Finish and retiring the
legacy branch after a week of actual use are later work; manual note-to-task
and note-to-project must work in this PR. No new workflow engine or schema
rewrite is warranted for those jobs.

## Three implementation corrections from the design review

1. An explicitly chosen incompatible assignment remains under assignment
   authority and gives its repair. It must not select the legacy local model.
   Preserve invocation/subject overrides when deciding that authority.
2. An Engines handoff carries both Settings section and target job. The
   current alias `scope ?? alias.scope` cannot preserve both by itself.
3. The meeting review projection includes the linked action's completion
   status. Confirmed and completed are different facts; Done must survive
   reload and remove the item from open prep.

## Ownership

| Worker | Owns |
|---|---|
| engine_workflows | inference routing/adoption gates and reasons; Ask API and UI; shared EngineLine/RunLine/hook; Room draft backend/controller/UI |
| window_workflows | Settings/Engines hosting; application registry, aliases, window lifecycle/placement; dock/Go/chrome/phone; shared compact footer |
| attention_workflows | People/prep and follow-through/proposals; meeting review UI; note task/project/ask UI and route; Needs you/compose; palette default and snippets |

Workers implement only owned paths and their focused tests. Shared paths are
serialized by the orchestrator. Notify the orchestrator of a needed overlap;
do not edit another worker's file. All anchors in designs are hints: check
them against the current source; sibling edits may land while work proceeds.

Workers never stage or commit: HOLD FOR SHIP. No stash, reset, restore, clean,
switch or checkout; never git add -A. Park retired code instead of deleting it.
No owner HOME, DB, Keychain, mic, real CLI or external delivery in verification.

## Verification

Every test command runs through scripts/test_lock.py, with isolated HOME;
use -n 8 for pytest. Workers run only file-named focused budgets in their
brief, collect first, and report exact names and run tails. No worker runs
the full suite or quick_check. Never run tests/e2e/test_metal.py.

The orchestrator runs the integrated build, related tests, quick check and
the desktop/393 sweep; reads the shots; and walks the relevant jobs through
scripts/graph_walk.py where current cases cover them. A fixture engine is
reported as a fixture, never a real LAN-engine observation. Main and the
owner's machine state stay untouched during the build. Real owner judgment
of the resulting desk remains the final usability evidence.
