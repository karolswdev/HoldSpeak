# Continue the creation loop — Thought to saved file

The owner asked Astra to keep pushing the product after the recovery delivery.
The full main run at `fc02d9b8f` finished with **1 failed, 16,514 passed,
68 skipped and 1 expected failure**. Its one failure is existing queue R071,
`TestTheThoughtSends::test_write_a_thought_then_send_it_to_a_folder[393]`.
The preceding #1228 full run added one distinct long-context Thought case to
the union (R113), bringing the tracked historical total to 113. It no longer
failed in #1232; the current 17-case Thought-file run also passes.

The phone test saw a Thought frame, typed immediately and then could not find
its More actions door. This is evidence of a failed journey, not yet proof
that the product, fixture or assertion owns the cause.

Current base is `b9c348aea`, including the subsequent meeting-stop and Night
Train changes. Worktree: `/Users/karol/dev/tools/wt-thought-send-recovery-20261016`.
The serving Night Train worktree and the owner's state stay untouched during
verification. Sol HIGH implements; Astra integrates and judges the result.

## Job and settled behavior

Write a note, copy its current words, Send the exact saved revision to the
local HoldSpeak folder, then return to the same note and continue editing.
The note field must own typed input. A visible frame alone does not establish
an editable document. Send must wait for a successful save, reject a failed
save, retain newer words, name the saved file, and preserve return focus.
Keep the existing library composition and phone More actions grammar.
No new workflow, replacement component or broad timing retries.

## Bounded work

1. Trace the CI failure and reproduce the actual readiness/focus transition.
   Classify a product defect versus a test that acts before its required state.
   Fix the responsible seam and preserve exact clipboard, revision, file-byte,
   no-duplicate-send, focus, geometry and refusal assertions.
2. Review the connected save/send/return code for a concrete remaining user
   failure. Reproduce any finding before expanding the build scope.
3. Verify the changed path at desktop and phone widths, inspect the screenshots,
   run the ordinary quick check, merge and deliver the verified product if it
   changed. The next full main run stays a separate confirmation.

## Worker boundaries and proof

The Thought worker owns `web/src/desk/thought-workspace/` and
`tests/e2e/test_thought_glass.py`. Shared components, Send hosts/backend and
all other tests require a root scope decision before edits. Anchors drift:
verify current source. The CI trace is `.tmp/recovery/nightly-38985702250.log`
(lines 1933 onward); the failed journey starts near line 1441 of the test.

Focused budget: collect and run `tests/e2e/test_thought_glass.py::TestTheThoughtSends`
and, if changed, the relevant Thought workspace/controller component test.
Root expands only for a diagnosed seam. All test/build/browser jobs use
`scripts/test_lock.py`, isolated HOME and disabled native effects. Never
`tests/e2e/test_metal.py`; no owner DB, providers, microphone or keys. Helpers
`.tmp/recovery/locked.py` and `run_quick.py` carry the environment and logs.
Workers hold for SHIP and never stage, commit, merge or deploy. No destructive
git verbs. Report exact collection/run tails, actual shot paths, limits and
unresolved findings. A source hypothesis is not a reproduced defect.

## Observed continuation: Retry preview disagrees with its command

The real Note → local folder path reproduces at 1440 and 393. The first send
writes `Frozen send bytes one.`; only its returned response is dropped. Back
and a new saved revision change the note to `New saved words two.`. Reopening
Send shows those new words above Retry, but Retry correctly replays the old
command and original digest. The single existing file still contains the old
bytes. The newer note and return identity survive. This is a preview-truth
defect, not duplicate dispatch or note data loss (Tenets 3 and 7; Article VI).

Settled repair: the shared Send well keeps its original preview with the held
command through Back and later edits. Retry displays that exact content until
the held command resolves. The newer note stays saved; a distinct Send again
uses its fresh preview and a new command. Preserve existing components and
composition. The shared worker owns `web/src/desk/surface/send/SendWell.tsx`
and its relevant component tests; no backend changes are needed by this trace.

Before proof is under `.tmp/recovery/send-return/`: paired screenshots,
`facts-{1440,393}.json`, and exact saved files. The scratch probe performs the
actual click, producer, folder write and replay; it does not replace the send
with a successful fake response. Root inspected the phone mismatch and its
request/row/file records. The focused regression must fail before the repair;
the actual continuation must prove both replay and the later distinct send.

## New Project continuation

A real isolated browser sitting now closes the earlier entry-only coverage gap
at 1440 and 393: Search → New Project → name → Create Project → exact Room →
Close/Back → Go Projects → reopen → reload. Each sitting produces exactly one
`POST /api/projects/door` with its named outcome and no sources. Its returned
ID, project DB row, Room read and persisted window scope agree through each
step. No extra project, source or watch is created. The selected phone controls
own their measured nine points and 44 px targets.

Phone Back follows the current scoped grammar: project → Memory → closed,
requiring two presses to close the host. This is recorded rather than called
one-step return. Both screenshots and persisted facts were inspected. Evidence:
`.tmp/recovery/project-walk/run-20261016T232029/{1440,393}/facts.json` and the
four named shots beside each. Build: `3ebdb08ab76ecc2b`; this scope has no product
change. The bare hub reports an unrelated 503 from People relationships on
initial read; no page exception, external browser request or nonhub TCP attempt
occurred. External-source creation and native/provider effects are not claimed.

## Bounded verification

- The unchanged Thought folder pair passed locally (2 cases), then a held
  authoritative read reproduced the old immediate footer assertion (1 failure).
  Its corrected boundary uses the actual GET and held-route observation, then
  requires the exact buffered words in the editable, focused Note. Final paired
  run: 2 passed in 15.19 seconds. All original save/revision/file/Back/geometry
  and refusal checks remain; clipboard content is now exact equality.
- The new Send regression failed against the previous product at the frozen
  preview assertion. The repaired real desktop/phone continuation passes
  (2 cases in 15.16 seconds): Retry has the identical original command/digest,
  one original send/file remains, and a distinct later Send again uses a new
  key/digest and writes the newer words. The first file is unchanged; the note
  revision and return focus survive. Root inspected both the mismatched and
  fixed phone preview and the desktop new-send result.
- Independent integrated source review found no concrete blocker. It checked
  per-document/target ownership, pending/failed fresh reads, prepared sends,
  stale effect cleanup and the unchanged unsaved-note fence. This is counsel;
  formal postmerge review remains a separate step.
- The shared component file passes 35 cases, including replay of recorded real
  responses with the later preview both ready and pending. Ordinary quick is
  GREEN: 4,119 related web checks, 17 Thought browser checks, 109 Desk sweep
  checks and 17 canon guards. TypeScript and 28 documentation guards pass.
  Source/build agree at `2759d0c6c13d4b6b`.
  This proves in-memory held-command return and local folder delivery; reload
  persistence and external delivery are not claimed. Full main follows merge.

## Merged and delivered — #1236

Merged main `20f6113b5`; formal Astra review RATIFY is recorded on
[the PR](https://github.com/karolswdev/HoldSpeak/pull/1236#issuecomment-6230245839).
The verified idle hub was delivered normally: PID20767, port8765, worktree
`wt-thought-send-recovery-20261016`, build `2759d0c6c13d4b6b`. Served build and
merged source agree. Health, Desk, Conductor and Models return200. Runtime is
idle with no meeting active. Night Train fidelity and preceding layout repairs
remain included. Remote full run39006834509 is pending; no full-green claim.

VERDICT: RATIFY
FINDINGS:
1. No blocker found in merged #1236. The held command retains its original preview and body at `web/src/desk/surface/send/SendWell.tsx:406`; Retry renders that preview at line 600. Settlement or refusal clears both together at lines 414/418. This restores truthful Send content (Tenets 3 and 7).
2. The real local-folder continuation at 1440/393 verifies the identical retry command/digest, one original file with unchanged bytes, and a distinct later send of the newer note. Proof: `.tmp/recovery/send-return/fixed/facts-{1440,393}.json`, corresponding four shots and saved files in the delivery worktree. Root inspected the mismatch and repaired phone preview and desktop later-send result.
3. The Thought regression now explicitly holds the real initial read before typing and proves exact buffered text/focus before actions (`tests/e2e/test_thought_glass.py:1464`). Original save, clipboard, revision, file, refusal and return assertions remain. Ordinary quick: 4,119 web, 17 Thought, 109 sweep, 17 canon; TypeScript and 28 doc guards pass.
CONDITIONS: None for this bounded change. Full main verification continues separately.
MISSED: The broader recovery originally omitted one historical long-context failure identity; R113 is now tracked and passes the current Thought-file run. No unresolved product finding in this diff.
TUESDAY: The owner can return from an uncertain send, edit the note, retry the original words truthfully, then send the newer revision separately.
UNKNOWN: External delivery, native effects and persistence of an uncertain command across browser reload were not exercised. A passing local release check is not yet a full-main result.
