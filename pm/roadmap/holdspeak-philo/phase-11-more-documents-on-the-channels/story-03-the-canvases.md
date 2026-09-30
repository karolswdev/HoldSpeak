# PHILO-11-03 - The canvases A–E

- **Project:** holdspeak-philo
- **Phase:** 11
- **Status:** in-progress
- **Depends on:** the owner's ratification; design section 4 (the wire the harness shim serves)
- **Unblocks:** PHILO-11-04, PHILO-11-05
- **Owner:** Muad'Dib's lane (Fedaykin, Opus 5.5); Astra checks
- **Closure finding:** `docs/internal/philo/phase-11/grounding/faces.md` §6, F3, F5, F6, F7, F8; rulings R4, R5, R7, R8, R9
- **Design:** `design/document-sources.md` (the wire)
- **Canvas:** five, before any build (UX-CANON §A.2): A the brief, B a decision, C a meeting summary, D Destinations with Slack, E the shared well

## Problem

The SEND well lives only under a published update (`web/src/features/project-room/update/UpdatePosture.tsx:438`). R4 puts it on every face where the brief, a decision and a meeting summary live. Those windows are narrow at desktop width (the decision window about 400 px, the Meetings window about 640 px; faces.md F7). Nothing is drawn yet.

## Scope

- **In:** the boards of faces.md §6, each at 1440 × 900 and 393 × 852, on the real product with a harness shim for the new wire (the Phase 10 pattern, `../phase-10-the-channels/assets/story-04-send-canvas/README.md`): A1–A6 (the brief on the Chair BRIEF section and the Intelligence BRIEF view, the person sections in the preview; A5 set up as a change to the **same** brief after a send — same-day Generate returns the same id (`holdspeak/services/monday_brief_service.py:398-406`), so A5 shows the new preview of that brief, or a next-day brief with a new id, and Send again (R9)); B1–B5 (the desk decision window; the decision record in Intelligence → DECISIONS **and** in the Room's DECISIONS & COMMITMENTS rows, including rows marked `source="meeting"`, which are `decision_record` (`holdspeak/services/project_service.py:2034`, `:2103`); Edit after a send). Before canvas B, confirm on glass that no face renders a lifecycle `decisions` row (design §6a); if none, `meeting_decision` gets no board; if one is found, it gets the well and a board. Record what the Room row's `Open` shows (design §6a, unknown); C1–C6 (the Meetings record, the meeting window, the Chair MEETINGS row, the digest and follow-up as forms in the same well, the old `DIGEST → SLACK` rows gone, a meeting with no summary); D1–D4 (the Slack form, the webhook saved and refused, the Slack row with Check, Credentials without the webhook row); E1 (the four wells side by side); and the failure transitions (design §6b; Astra r1 finding 8): T1 the over-limit Slack preview with its refusal word (never `NO ANSWER`), T2 `preview_changed` → a fresh preview → another press, T3 the Chair after its last brief item is acknowledged or deferred, with the well still on the section. The history head word (F8) proposed on the boards. Astra's check; then the owner's word, recorded verbatim.
- **Out:** the build (04, 05).

## Acceptance criteria

- [ ] Every board drawn at both widths; the decision and Meetings boards at their real window widths at 1440; the full well's fit at 393 shown, not assumed.
- [ ] Boards T1–T3 drawn at both widths.
- [ ] No board shows a stale-version word or an old-version row (R9); no board shows Mark delivered on a new kind (R8); no board shows a message link for a Slack post.
- [ ] Every verb the library Button; the egress chip on each row that leaves the machine; no modal; no prose; no counter of zero.
- [ ] Astra's check recorded; the owner's ratification recorded verbatim before story 04 or 05 commits a face change.

## Effort (not a promise)

PROVISIONAL: 1–1.5 engineering days.

## Test plan

- **Glass:** the harness boards through the real hub on an isolated HOME at both widths; shots under `assets/story-03-canvas/`.

## Notes

- 2026-09-29 — round one DRAWN (Fedaykin lane, Opus 5.5): 42 boards × 1440 and 393 on the real product with a harness shim (`assets/story-03-canvas/`, README + `index.html`); fences 132/132 named on screen, 0 stale words, 0 Slack links, 0 Mark delivered on a new kind. `meeting_decision` confirmed seatless on glass; the Room row's Open opens nothing (G1). Seven open questions with recommendations. Owed: Astra's check, then the owner's word.
- 2026-09-29 — round two: amended on Astra r1 RATIFY-WITH-CONDITIONS (`checks/charter-astra-r1.md`).
- 2026-09-29 — drafted by the Fedaykin docs lane for Muad'Dib; unratified.
