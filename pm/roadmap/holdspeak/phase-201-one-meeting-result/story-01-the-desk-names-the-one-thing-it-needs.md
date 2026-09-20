# HS-201-01 - The desk names the one thing it needs

- **Project:** holdspeak
- **Phase:** 201
- **Status:** backlog
- **Depends on:** none
- **Unblocks:** (optional)
- **Owner:** unassigned

## Problem

The product knows the one thing that blocks the whole path and no face says it. `/api/setup/status` returns `overall: needs_attention` and a `primary_action` ("Set a valid local model path…"); its only reader, `web/src/pages/cores/SetupCore.tsx`, has zero importers. The Chair says `Nothing needs you` above a FAILED meeting that carries a NEEDS YOU section (audits/face-walk-opus.md defects 1, 8). Tenet 3: a clear next action. Article VI: honest by construction.

## Scope

- **In:** the Chair shows the MEETING-PATH blocker (no summary engine assigned, or no speech engine) as ONE row with ONE library Button that opens the matching repair (Models for an engine; the doctor row for a microphone check). Not `overall !== "pass"`: `overall` returns `ready`, never `pass` (`setup_status.py:50`), and `primary_action` (`setup_status.py:67`) may name a microphone or first-dictation action that Models cannot repair. The row clears after the repair. `SetupCore` is NOT mounted wholesale. Both headlines never read `Nothing needs you` while a needed action or a FAILED row exists: the Chair (`ChairHome.tsx:293`) AND the Meetings window, which has its own function (`HistoryCore.tsx:35`). The chrome chip and the Trust window agree (`desk/setup.ts:54-88`: no `EXTERNAL REACH ENABLED` with zero destinations).
- **Out:** the Go rail; any new window; the Models screen itself (story 05); wording beyond this row (story 06).

## Acceptance criteria

- [ ] Cold desk with no summary engine: the Chair shows the meeting-path blocker as one row and one Button; the Button opens Models; after an engine is assigned the row is gone. Shots at 1440 and 393.
- [ ] A microphone-type `primary_action` does not open Models.
- [ ] With a FAILED meeting, neither the Chair headline nor the Meetings window headline reads `Nothing needs you`.
- [ ] The chrome egress chip and the Trust window state the same thing on a virgin desk.
- [ ] Every verb is the library Button; no prose; no modal (UX-CANON A).

## Test plan

- **Unit:** vitest for the headline rule and the chip/trust agreement.
- **Integration:** `tests/e2e/` glass test: cold HOME, the row renders, the Button opens Models.
- **Manual / device:** shots at both widths in evidence.

## Notes / open questions

Lane B (Muad'Dib to Opus). Serves exit criteria 2 and 3.
