# HS-160-06 - The review face: a posture in Now, judged from the keyboard

- **Project:** holdspeak
- **Phase:** 160
- **Status:** done
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

## What shipped

- Functional (e4272ce7): the posture in Now (no modal, in-place
  swap), grouped queue + count chips, the ledger comparison honest
  about record-only kinds, four verbs + session undo, typed edit,
  posture-scoped keyboard (letters dead in inputs), conflicts show
  both sources, the no-delta state. 48 tests, wire-mined fixtures.
- Beauty (c6aef96d), the orchestrator's seven-point list: plain-words
  card anchors (machine kind/ref → data-attrs), human queue rows,
  the value renderer that can never say [object Object], machine ids
  hidden from the ledger, one verb row with the defer two-step (L
  stays immediate — glass-compat verified selector by selector),
  materiality as High/Medium/Low temperatures, position stated once
  with a disposition tally. 31 more tests; 248 green.
- **THE OWNER'S VERDICT: PASS** (2026-09-01, "PASS — close it") —
  first round, no bounce: three phases of banked taste laws paid off.
  Evidence captures the scoped suites + a fresh build + the four
  glass legs green on the beautified face.

## Notes / open questions

- The keyboard letters stay posture-local by design (review verbs have no desk-wide meaning); the command deck integration note stands for P3's Draft-update verb.
