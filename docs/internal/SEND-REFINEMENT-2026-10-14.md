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
pytest-n8. No metal, owner port/DB/mic, inference or external dispatch.

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
