# Design check — Astra, 2026-09-20: HS-201-12 Write a thought is one clean note

Session `01a0bf7d-9647-7de1-9f6b-6c81fc9c6759`. TWO-BRAINS §3; counsel ratifies the canvas on the owner's behalf (his 2026-09-17 ruling). Read-only on 397fd22f.

## Round 1 — Astra

VERDICT: RATIFY-WITH-CONDITIONS

FINDINGS:

All anchors refer to committed content at `397fd22f`.

1. **The job is right; retain it. Tenets 3, 7.** One editable, dictated note with an optional sharpening question serves this architect’s daily work. Band 3 supports that same job once synthesis and automatic continuation leave the interaction. Toolbar, tags, Info, tabs and marker chips need not return. Preserve editing, dictation, original content and access through existing surfaces. The proposed hierarchy, library species and single filled Finish are sound. `pm/roadmap/holdspeak/phase-201-one-meeting-result/story-12-write-a-thought-is-one-clean-note.md:16`

2. **Parking synthesis does not remove its live outcome. Tenets 3, 7.** The story excludes new AI behavior and leaves services unchanged, but the existing prompt explicitly permits synthesis. Ask can therefore produce something the new design has nowhere to show. Settle a visible, minimal outcome for that result; never silently fold it away or leave an empty question. After successful Add, fold the question and reveal the appended text. `pm/roadmap/holdspeak/phase-201-one-meeting-result/story-12-write-a-thought-is-one-clean-note.md:45`, `holdspeak/services/refinement_coordinator.py:581`

3. **“Kept and findable” lacks its closing contract. Tenets 3, 7.** Finish currently flushes the note, while the unadded answer lives separately in component state. Completion also locks editing. Define what Finish does with that answer and how a completed note becomes editable again. “Kept” must not imply unsaved edits persisted; preserve a working save-retry action. Extend the acceptance loop beyond Finish to close, find and reopen the same note. `web/src/desk/thought-workspace/ThoughtWorkspaceWindow.tsx:148`, `web/src/desk/thought-workspace/ThoughtWorkspaceWindow.tsx:301`, `web/src/desk/pullouts/editors/useThoughtNoteWriter.ts:227`, `pm/roadmap/holdspeak/phase-201-one-meeting-result/story-12-write-a-thought-is-one-clean-note.md:61`

4. **Band 4 still opens two jobs if Change inherits today’s picker. Tenets 3, 5.** That picker combines this note’s context with defaults for future thoughts. It also contains raw buttons, instructional prose and a body-portaled overlay. Settle Change as an in-window library well for this note; park default management elsewhere. Renaming Attach does not satisfy UX-CANON A1/A3/A4. `web/src/desk/pullouts/ThoughtContextPicker.tsx:163`, `web/src/desk/pullouts/ThoughtContextPicker.tsx:174`, `web/src/desk/pullouts/ThoughtContextPicker.tsx:206`

5. **Ask lacks its destination badge. Tenets 3, 5; UX-CANON A9.** “Reads” identifies input, not where it goes. Put the library egress badge beside Ask, using the intended destination before dispatch. The four-band drawing currently omits it. `pm/roadmap/holdspeak/phase-201-one-meeting-result/story-12-write-a-thought-is-one-clean-note.md:30`, `docs/internal/UX-CANON.md:45`

6. **Failure states need precise distinctions. Tenets 3, 4.** “No engine yet · Choose an engine” is minimal and honest for an absent assignment. Generic inference unavailability also covers an unavailable target or coordinator; do not label all of those “No engine yet.” A failed ask needs one plain reason and a legal recovery verb, with Finish still available. Stale/missing context must remain visible in Reads. `holdspeak/services/refinement_application_service.py:57`, `holdspeak/services/refinement_thought_service.py:1658`

7. **Clipping remains permitted outside the title. Tenets 3, 6.** The footer requires context on “one line,” although names and attachments vary. Allow wrapping at 393. Specify scroll ownership for long notes and questions, preserve reachable actions, and keep title wrapping during editing. A short-note screenshot cannot prove these cases. `pm/roadmap/holdspeak/phase-201-one-meeting-result/story-12-write-a-thought-is-one-clean-note.md:36`, `pm/roadmap/holdspeak/phase-201-one-meeting-result/story-12-write-a-thought-is-one-clean-note.md:50`

CONDITIONS:

Fold findings 2–7 into the settled design and fix round. Verify the ordinary note-only path, optional question loop, unadded-answer Finish, save/ask failures, context change and reopen path. Compare both-width shots against the revised design.

MISSED:

Ranked by owner cost: unfinished text at Finish; invisible synthesis; finding tomorrow’s note; Change reopening excessive controls; ambiguous failures; clipped context.

TUESDAY:

Yes, conditionally: dictate, edit, optionally answer, finish, and find it tomorrow—with no required AI setup.

UNKNOWN:

I reviewed committed design and code only. The owner’s shot is described but not linked in the Problem. I could not verify Workbench appearance, actual geometry, live dictation or persistence. No tests ran; no tree changes were made.
## Round 1 — Muad'Dib's rulings (folded into the build)

1. Job confirmed.
2. A synthesis draft shows in band 3 in the question's shape ("A draft from your note", the text, "Add to note"); after Add the band folds and the appended text is revealed in the note.
3. Finish = keep, not lock: an unadded answer is added first; a finished note reopens editable; a save failure is one line with Try again; the e2e closes, finds and reopens the note.
   **AMENDED 2026-09-20** (counsel on built, finding 2, accepted): "reopens
   editable" is withdrawn — the hub refuses working-note writes on a
   completed Thought (`refinement_thought_service.py:1147`). The settled
   rule: a finished note names `FINISHED` and `Resume` is one press. The
   save-failure verb is `Try again` only where a retry works; a conflict
   ("changed elsewhere") carries `Reload`, because `writer.retry` returns
   during a conflict (`useThoughtNoteWriter.ts:238`).
4. Change is an in-window well for this note's context, library species; default-context management is parked.
5. An egress chip beside Ask with the intended destination.
6. "No engine yet" only for an absent assignment; unreachable engine and failed ask have their own one-line truths and a recovery verb; stale context stays visible in Reads.
7. Nothing clips: the foot wraps, the note owns the scroll, the foot stays reachable, fences for long notes and questions at both widths.
