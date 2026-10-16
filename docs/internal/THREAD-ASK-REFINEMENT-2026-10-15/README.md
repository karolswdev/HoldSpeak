# Thread, Ask and notifications

Owner request 2026-10-15. Base `9e45b3319232a2afb7c4884e449386bf8e2b0f60`;
branch `feat/thread-ask-refinement-20261015`, isolated worktree
`wt-thread-ask-refinement-20261015`. [Audit](AUDIT.md), [settled direction](DESIGN.md),
[Ask implementation](BUILD-ASK.md), [Thread implementation](BUILD-THREAD.md),
[notifications implementation](BUILD-NOTICES.md), [bounded source counsel](REVIEW.md).

## What changed

Thread and Ask now share the library paper traffic, readable turns and a bounded
question pad. The ordinary Thread window starts at 660×700, retaining saved owner
geometry. Mode selection uses the library menu. Thread has real load/reply recovery,
a working pointer Send while editing, and one scroll body. Failed replies put
technical details behind Details. Dead branch arrows are parked.

Ask has one answer action home: Keep and Bin in its footer, Copy beside the answer.
There is one engine repair action and direct Add notes. Retry uses the complete
submitted question and sources; newer typed work remains in the durable draft.
Keep writes the original question and references. Close/Cancel/Escape abandon the
local pending view and reject late updates; they do not promise server cancellation.
The host mic appends to the latest draft rather than its captured earlier value.

Existing notifications now share one bounded Workbench stack, paper payload wells,
library actions and nonzero queue facts. The stack clears the Dock and scrolls
when several notices arrive. Phone actions have 44 px targets. Existing running
pulses respect reduced motion. The preceding #1214 journal exclusion and successful
visible-row dismissal/cutoff remain intact; no notification service was added.

The actual walkthrough also exposed a backend Keep failure: canonical note sources
were rejected by the artifact source vocabulary. The existing legacy set now also
accepts the closed canonical `RESOURCE_KINDS` set. Unknown kinds remain rejected;
there is no new schema, route or service.

## Before and direction

Root rendered and read the library canvas at 1440 and 393 before build; outputs
`.tmp/thread-ask/canvas-final-1440/` and `canvas-final-393/`. The canvas is outside
the quick check and was rendered independently. It is a direction, not runtime proof.
Actual before captures use the preceding built bundle: `before-final-1440/` and
`before-final-393/`. The capture waits for finite entrance animations; earlier
partially transparent screenshots were capture timing, not a product failure.

## Focused proof and fixes

Root read collection and run output, not only worker summaries. Thread: 171 passes
in 8 files (`thread-list-final.log`, `thread-run-final.log`). Ask including the
late-speech callback: 16 passes in 2 files (`ask-voice-list.log`, `ask-voice-run.log`).
The route scope reproduced two stale assertions and then passed 33 in 3 files
(`ask-route-list.log`, `ask-route-before.log`, `ask-route-after.log`): route facts
remain asserted, answer prefix matches the shared turn, and completed RunLine time
was restored. Queue scope reproduced a real duplicate count; product markup was
fixed, unchanged tests plus material/dismissal tests pass 20 in 4 files
(`notices-queue-list.log`, `notices-queue-red.log`, `notices-queue-green.log`).

The first complete quick check returned RED: 3852 web passes and three failures,
651 affected Python passes, 107 sweeps with two existing xfails, and 15 canon passes
with two failures. Nothing was waived. The static Ask interior guard now asserts
one shared composer and exactly one Pad, retaining the raw Markdown ban. The mic
scanner recognizes four exact named fields only when an explicit MicButton exists
in the same component; general opt-outs still fail and the ratchet ceiling is
unchanged. Its 21 new boundary cases join existing scanner/ratchet tests: 66
collected and passed (`thread-mic-collect.log`, `thread-mic-run.log`). Root reran
interior/scanner/ratchet together: 74 pass (`guards-final.log`).

The actual intermediate Keep route returned HTTP 500 for a note source. Focused
real database tests first reproduced two failures with 19 passes, then passed all
21 after the additive source-kind correction (`ask-keep-list.log`,
`ask-keep-before.log`, `ask-keep-after.log`). A retained answer keeps its original
question, canonical note/knowledge references and relationship snapshot after DB
reopen; a zone is accepted; invented kinds are rejected at service and repository.

Source counsel found one delayed-speech overwrite, then ratified after one fix
re-check. Later queue, completed-time, scanner and source-kind fixes were reviewed
by root and are not attributed to that earlier verdict. Formal postmerge review
remains separate. No model or microphone execution is inferred.

## Verification boundaries

All checks and walks use the machine lock and isolated HOME/DB with engines and
native capture disabled. They do not write the owner's DB, microphone, Keychain,
clipboard, provider or tmux. Normal owner hub deployment is a separate final step
after merge. Conversation walkthroughs replay only Ask inference HTTP responses;
Keep uses the actual writer and database. Thread fixtures are persisted messages;
Edit/Send dispatches the canonical branch request. Notifications replay declared
runtime frames at the browser WebSocket boundary while forwarding the real hub.
They do not prove real wake capture, inference or job execution. Queue Open landing
is not claimed by the notification walkthrough. No full nightly suite, remote CI,
formal postmerge review, hardware performance or owner acceptance is inferred.

## Final release verification

Final complete quick is GREEN, actual exit 0: 3855 web tests in 409 files,
761 affected Python tests, 107 Desk sweeps with two existing xfails, and 17 canon
guards. Release TypeScript exits 0. Logs: `quick-release.log`, its four suite logs
under `quick-release/`, and `typecheck-release.log`. Root read the actual tails.
Generated architecture check passes 10 outputs; graph join passes with 14 existing
subtype notes. No ceiling or failed result was waived.

Final build `228dd99cb87915de` was observed in `after-release-1440/` and
`after-release-393/`: 12 states each, no page errors. Real pointer/touch Edit/Send
reaches the Thread branch writer with the edited text. Actual no-engine failure
has one repair. Replayed Ask pending/failure/success verifies exact retry after
the draft and note selection change. Real Keep returns the route's HTTP 201 and
writes an artifact carrying Question A and its qualified note reference; reopened
Ask retains Question B. Closing the pending view under normal and reduced motion
rejects late updates and keeps the draft. Root read observations and paper answer,
composer and recovered-draft screenshots at both widths. The first release walk
stopped on the rig expecting 200 from the existing 201 creation route; correcting
that assertion changed no product source.

`notices-final-1440/` and `notices-final-393/` each capture seven states on that same
build, no page errors. Nineteen real isolated journal warnings remain recorded
without a popup. Declared runtime frame replay produces full preview, learning,
running and expanded queue hosts in one stack. Stack bounds are 390×585 at desktop
and 369×554 at phone, above the Dock; its overflow scrolls. Actual Discard/Dismiss
hit points belong to their Buttons, phone heights are 44px. Running pulse computes
`surface-state-pulse`, reduced motion `none`. Root read both observations and stacks.

Official `case.desk.ask.composer.ready` passed in separate 1440 and 393 invocations,
fresh isolated HOME/DB, engine none and no substitutions. Actual Search/palette
pointer or native touch opens the labeled shared Pad. Root read provenance,
initial/terminal predicate and before/after shots: settled in 1.085s/1.099s within
30s, no console errors. This proves entry/composer readiness, not inference.
Raw local logs and images remain under `.tmp/thread-ask/`, not a committed archive.

Normal local hub deployment follows merge. Exact serving source/merge/tree, PID,
HTTP/build agreement and warm runtime belong in this retained tree's untracked
`LOCAL-HUB.md`; no authenticated token is recorded there. The Jupiter preview
on port 4488 remains available. Broader whole-app audit findings are the next
scope; this release does not claim every interface is finished.
