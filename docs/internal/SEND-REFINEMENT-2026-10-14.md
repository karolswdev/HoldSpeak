# Send refinement — 2026-10-14

Owner: continue refinement; opened a Note and found Send ugly. Base: main
821578c2b (#1200). Worktree: wt-send-refinement-20261014.

## Tuesday job and observed problem

Send the saved note to a chosen destination, review the exact payload, see the
result, return to the same note. Root reproduced the actual Note producer →
Search → Note → Send at 1440/393 in an isolated hub. The desktop Send region
was nearly hidden below the editor and engine band; the phone retained Finish
as its footer primary. Shared preview nesting and indents waste available room.
Source audit: audit_send_face and audit_note_doors, gpt-6.1-sol xhigh.
Tenets 3, 5 and 6: simplify the job using the existing component framework.

## Settled composition

- Note Send owns the existing window body. Unmount note editor, engine, Ask,
  context and Task/Project wells while sending. Keep the writer/controller
  mounted; flush before opening, retain draft/save/conflict/revision fences.
- One local sending state controls posture and the frame's existing onBack.
  Phone Back and a desktop library Back return to the note, not close it.
  Close continues its existing writer-safe close. Restore Send focus on return.
- Replace the Note action footer in Send posture. No Finish/Resume, Copy or
  task actions while sending. Shared Send owns actual dispatch and receipts;
  the host owns return. Opening Send replaces unrelated open local wells.
- Shared Send uses existing SurfaceSection/ledger/well/Button tokens. Compact
  destination identity, visible Add destination using the current Settings
  action, clear Preview caption and exact frozen fields/body. No decorative
  duplicate metadata. Keep required egress at dispatch and named receipts.
- Expanded preview uses the content width, not stacked host/row/well indents.
  One outer scroll region; inner preview payload has no independent cap.
  Fields and dispatch/results remain reachable and own 44px phone targets.
- Use SurfaceState for chunk/read/preview loading; failed reads retain Retry.
  Preserve prepared sends/history, digest approval, held command IDs, lost
  answer retry and unknown-result behavior. No backend, routing or store rewrite.
- Existing note geometry/frame is reused; Send must fit a usable body at the
  current sticky size. The observed desktop Send cap requires minH520 while sending (Note360).
  This minimum-size adjustment stays in existing
  frame props and is measured, never a new window manager or global CSS reset.

## Lanes and boundaries

1. Shared Send: surface/send/SendWell.tsx and send-well.css; documentSendsLazy
   loading, send component tests and canvas/surface-send. No Note host edits.
2. Note host: ThoughtWorkspaceWindow.tsx, thought-workspace.css and its tests.
   No Send internals, shared footer/frame implementation or backend edits.
Root owns this record, graph cases, integration, final verification and ship.
Workers hold for SHIP, never stage/commit. One coherent PR and local hub update.
Every test/build/browser command uses test_lock, isolated HOME; Vitest2workers,
pytest-n8. No metal, owner port/DB/mic, real model inference or external dispatch.

## Integration findings

The actual Note browser flow passed at both widths, including a real folder
save, exact frozen payload/file bytes, current saved revision, no extra rows
on held/failed saves, and phone Back/focus. Root then inspected the shared
consumer checks. Their Meeting window ids and eager Week assumptions predated
#1200; the cases are being adapted to real current doors while retaining their
geometry, pointer, durable row and kernel receipt assertions.

One real menu seam was diagnosed: windowSend only knew the scoped Meetings
record after its folded Send well mounted. It now needs the actual existing
meeting scope and existing read fact before that mount; its destination pick
must emit the existing scoped SEND_OPEN event to unfold the existing well.
This connects an existing entry point without a new navigator, event or store.
WorkMenu selectors are scoped so the persistent Go Home menu is not confused
with the opened window menu.

## Verified implementation

- Native canvas: 14 adjusted ready/email/loading/saved poses at 1440/393;
  root read the ordinary ready compositions before build.
- Shared Send: four focused web files, 70 passed; menu seam: two files, 29
  passed. Note host: 40 passed, including keyboard entry, portaled return
  focus, editor unmount/return, save refusal, current revision and Close veto.
- Note browser: two final cases passed in 15.52s after final product freeze.
  Checks compare actual saved revisions, frozen DB payload, file bytes and
  receipt; blocked/failed saves leave the send count unchanged. Phone targets,
  keyboard entry and actual frame Back/visible More return focus are observed.
- Meeting browser: both widths passed with the real Week Open → Meetings →
  requested Send route. Retained-summary failure, form picker nine-point
  ownership, file bytes, DB/API row and kernel receipt remain asserted.
  The now-identical phone picker scroll board uses existing same_as metadata.
- Root graph: actual Note producer → Search → Note Send passed at 1440/393.
  Root read both observations and shots. They use temporary HOME/DB, no engine,
  and record main821578c2b with dirty=true (implementation not yet committed).
  The named real preview text is readable; editor/ordinary Note footer absent.
  Phone observation records focused region Send note. Paths:
  `.tmp/graph-walk/send-refinement/after-{1440,393}/`.

Room's new Add destination action can lie behind the existing sticky Back bar
after arrival scrolls the chosen row to the top. Its pointer check now uses the
existing shared rig's ordinary wheel recovery, then the same nine-point target
proof; misses without proven recovery remain failures. This is a visibility
classification in the test, not a hidden-control waiver or a product change.

Limits: no owner acceptance, actual email/Slack delivery, microphone, inference
or real device beyond Chromium mouse/touch viewports is claimed. Prepared,
failed, unknown and lost-answer branches retain focused component coverage;
all of those exact states have not received new live captures in this pass.

The Room recovery was executed and read: one wheel step, Add destination owns
126 × 44 and all nine points, with missed=[]. Proof:
`.tmp/evidence-shots/pm/roadmap/holdspeak-philo/phase-13-the-desk/assets/story-15-shots/C5-17b-scroll-targets-393.json`.
Final TypeScript passed after removing unsupported test-only exact options.
The graph source anchor follows the new non-toggle openSend declaration.

## Combined check and retained Note coverage

The first combined quick check was RED: 3,536 web passed with one obsolete
Folder target-chip assertion; 534 Python passed with 12 old Note checks
failing. Sweep passed 107 with two existing xfails; canon passed 15.
No failure was waived. Folder preview coverage now asserts the exact field,
absence of the duplicate open-row chip and the full destination hover path
(40 focused checks passed). Current phone New → Note coverage passed four.

Retained Note checks now use the actual Add a note / Add notes / More doors
and Saved receipt. Their deterministic interview fixture uses the canonical
capability assignment migration. Idle Ask opens Ask AI, so the distinct retained
in-note continuation is seeded through its real refine producer. One captured
pre-turn cursor is replayed in the browser request to obtain the real hub's
409, followed by the writer's actual retry and 200; no response is fabricated.
These checks retain custody, exact model-call count, stale-result suppression,
answer append, Finish, Resume and failed-write assertions. This is fixture
inference, not observation of the owner's model or LAN engine.

The retained checks exposed two real host defects: desktop long-question/context
content can extend below the 360px Note frame, and phone Reads Escape returns
focus to BODY because its action is inside More. The measured frame carried
a restored inline height of 360px, with 491px of child material. The bounded design gives ordinary Note an expanded minimum
up to its existing 640px/work-band cap while a Reads well or question is open.
Collapsed Note remains 360; Send remains 520; phone keeps its existing shell.
This minimum constrains manual shrinking while expanded material is present;
it does not override the user’s height with an intrinsic !important rule.
Focus uses one local visible-door fallback shared with Send. The host unit
recheck passed all 40 tests in 4.62s, including portaled phone Reads return
focus; final TypeScript passed. The final retained browser checks passed:
eight receipt/clean-note/long-note/
long-question/long-context cases in 14.05s, and two workbench custody/focus/
restart cases in 15.77s. Root read both log tails and the expanded desktop
context shot. No geometry, custody, receipt, pointer or focus assertion was
waived. Logs: `.tmp/send-refinement/legacy-note-final.log` and
`.tmp/send-refinement/workbench-browser-final.log`.

A fresh Sol source/shot review of the Send implementation returned RATIFY,
with no confirmed blocker. This was an independent implementation review,
not Muad'Dib's check or the postmerge Astra review. It covered saved-revision
fences, mounted writer, Back/Close authority, digest, scoped meeting routing,
actual file/DB comparisons and Room's nine-point wheel recovery.

## Final release check

Combined quick check GREEN against main821578c2b: production build; 3,537
web tests in 392 files; 546 affected Python/browser checks in four files;
107 desk sweep checks with two existing xfails; 15 canon guards. No new skip,
waiver or ratchet allowance. Logs: `.tmp/send-refinement/quick-final-2/`.
Final TypeScript passed in `.tmp/send-refinement/final-types-last.log`.
The canvas files outside web/src were built and captured separately before
product build. The owner’s real HOME/DB was not used by any test or walk.

Open: owner judgment on the running desk, actual email/Slack delivery, real
model/LAN inference, microphone and physical devices; the full main tape and
postmerge review. These are not inferred from deterministic browser fixtures.

Release: [PR #1201](https://github.com/karolswdev/HoldSpeak/pull/1201),
branch `feat/send-refinement-20261014`. Main checkout and its owner artifacts
remain untouched; local redeploy uses this verified worktree.
