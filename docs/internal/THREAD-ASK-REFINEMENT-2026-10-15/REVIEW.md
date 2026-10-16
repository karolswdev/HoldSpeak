# Finished-source counsel — Thread, Ask and notices

2026-10-15. Delegated source counsel against base `9e45b3319`;
not Muad'Dib's formal review. No product edits or test/browser/model runs.

VERDICT: RATIFY within the reviewed source scope after the one fix re-check.

FINDINGS:

1. **RESOLVED — preserve the latest Ask draft when speech finishes.** The
   first-round replacement Pad used its built-in mic.
   That path appends to the render-captured `value`, then supplies a string
   to `setPrompt` (`web/src/desk/surface/gadgets.tsx:452`). Mic transcription
   awaits `session.stop()` before calling that captured handler
   (`web/src/desk/components/MicButton.tsx:403`,
   `web/src/desk/components/MicButton.tsx:425`). If the owner edits the draft
   while transcription is pending, completion replaces those edits with
   the earlier draft plus speech, including its durable copy. The previous
   Ask callback used a functional setter and preserved the latest draft.
   This fails Tenet 3 and the settled requirement to preserve capture and
   newer work. Keep the existing functional append at this host, with one
   mic; no shared gadget redesign was required.

   Final re-check: `mic={false}` on the Pad and one external MicButton keep
   `draftScope="desk-ask"`; its handler uses functional `setPrompt(current =>
   ...)` (`web/src/desk/components/AskPanel.tsx:504`,
   `web/src/desk/components/AskPanel.tsx:517`,
   `web/src/desk/components/AskPanel.tsx:520`). The new test retains the old
   callback, edits the draft, invokes late speech, and checks both rendered
   and durable text plus one mic
   (`web/src/desk/__tests__/askPanelExperience.test.tsx:40`). Source and the
   focused regression test now address the finding.

CONDITIONS: None outstanding from source counsel. The one fix re-check is
complete. Root owns the actual 1440/393 UI/build/quick check.

MISSED: The editor migration preserved the ordinary speech append but
changed which draft it appends to. Thread's final external mic path already
uses the functional setter (`web/src/desk/components/ThreadComposer.tsx:900`,
`web/src/desk/components/ThreadComposer.tsx:1082`).

Source checks otherwise found no actionable regression: Ask Retry reuses
the copied request and Keep uses its sent prompt/context
(`web/src/desk/components/AskPanel.tsx:253`,
`web/src/desk/components/AskPanel.tsx:279`,
`web/src/desk/components/AskPanel.tsx:305`,
`web/src/desk/components/AskPanel.tsx:404`); local abandonment invalidates
and aborts the request before any late result update (`:144`, `:260`).
Thread's editor keeps focus transfers inside its group alive (`web/src/desk/components/ThreadComposer.tsx:1060`),
retains composition guards (`:1043`), and connects recovery to the existing
load/regenerate paths. The optional filter caption leaves other consumers'
fallback unchanged (`web/src/desk/surface/stripMenu.tsx:98`). Notification
material changes preserve the existing writers, cutoff, dictation exclusion
and doorless branch.

Read the workers' actual focused logs: `.tmp/thread-ask/thread-run-final.log`
reports 8 files/171 tests passed; `.tmp/thread-ask/ask-final-run.log` reports
1 file/15 tests passed; `.tmp/thread-ask/notices-run.log` reports 3 files/15
tests passed. Read their list outputs as well. On the fix re-check, read
`.tmp/thread-ask/ask-voice-list.log` (16 collected tests, including the new
delayed-callback regression) and `.tmp/thread-ask/ask-voice-run.log` (2 files,
16 tests passed). These are worker-run outcomes, not runs performed by this
counsel. The new test exercises the host callback and durable writer; it
does not prove real microphone/transcription execution.

TUESDAY: Retry/Keep now refer to the question that ran, and Thread recovery
has real actions. Ask's speech callback now preserves newer typed work.

UNKNOWN: Actual 1440/393 geometry, pointer focus/IME behavior, notification
stack scrolling and hit ownership, model execution and real speech were not
observed here. Local request abortion does not prove server cancellation.
