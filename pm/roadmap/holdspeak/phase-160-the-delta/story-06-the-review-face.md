# HS-160-06 - The review face: a posture in Now, judged from the keyboard

- **Project:** holdspeak
- **Phase:** 160
- **Status:** backlog
- **Depends on:** HS-160-05
- **Unblocks:** HS-160-07, HS-160-08
- **Owner:** unassigned

## Problem

WEB-IA-003: Review Changes is a POSTURE within Now — never a modal,
never a separate app. WEB-DLT-001..009: wide = queue + selected
proposal + comparison + verbs; narrow = one card with persistent
footer verbs; the verbs are Accept / Edit & accept / Defer /
Dismiss; every claim opens its source. WEB-CMD-002: J/K or arrows,
Space preview, A/E/L/X, layered Escape — through the house command
grammar (plain letters dead while inputs own focus — WEB-CMD-003).
WEB-NOW-002: "Review changes" becomes the primary verb when a delta
exists. The proposal view model is §7's ProjectProposal shape.

## Scope

- **In:** inside features/project-room/: the review posture in
  ProjectRoomCore's Now (the orientation verb flips to Review
  changes when pending_count > 0 — WEB-NOW-002's order); the queue
  (grouped by MEANING per WEB-NOW-004/PV-020 — kind groups with the
  count-chip grammar), the selected proposal with its typed
  comparison (current truth vs proposed — WEB-DLT-001) and source
  chips opening canonically (WEB-DLT-009); the four verbs (dismiss
  needs no confirmation + offers session Undo — WEB-DLT-006);
  edit-and-accept edits the TYPED record fields (WEB-DLT-004);
  completion summary + Finish review (WEB-DLT-008; Draft update is
  P3 — the slot exists, honestly disabled-absent); the keyboard law
  via the house command system; roving focus (WEB-CMD-004);
  announcements (WEB-A11Y-003: position/total/kind/disposition);
  mic law on any new input; degraded/empty states per WEB-STA-004/
  005/006 (conflicts show BOTH sources). Wire fixtures mined from
  05's integration tests (the standing law). Then the BEAUTY PASS
  and shots — THE OWNER'S VERDICT closes this story. Budget the
  bounce rounds; the 159 lesson: consequence first, objects always,
  the library owns material (ChoiceCardShell/SurfaceLedger exist
  now — use them from the barrel).
- **Out:** Draft update (P3), bulk accept beyond same-kind batching
  (WEB-DLT-007), Timeline extension (P3's story).

## Acceptance criteria

- [ ] The posture lives in Now; zero modals; the primary verb flips per WEB-NOW-002; groups by meaning with count chips.
- [ ] All four verbs + Undo-on-dismiss + typed edit; every material claim opens its source; conflicts show both.
- [ ] J/K/arrows/Space/A/E/L/X/Escape per WEB-CMD-002, dead while inputs focus (WEB-CMD-003); roving focus; announcements per WEB-A11Y-003/004.
- [ ] Wide 3-pane and narrow one-card compositions per WEB-DLT-001/002 at the 560px container law; no horizontal scroll.
- [ ] check green; baseline zero branch-new; glass overflow-free; SHOTS + THE OWNER'S VERDICT: PASS recorded verbatim.

## Test plan

- **Web unit:** queue/comparison/verbs/keyboard/announcement suites on wire-true fixtures.
- **Glass:** rides 07's walk + dedicated face shots.
- **Manual:** the owner's verdict — the closing gate.

## Notes / open questions

- The keyboard letters route through the command deck (WEB-CMD-001 ranking comes with it) — find the house command registration before writing any listener.
