# HS-158-05 - The web graduation: the Room face on the desk

- **Project:** holdspeak
- **Phase:** 158
- **Status:** in-progress
- **Depends on:** HS-158-04 (adoption half; extraction half may start with 01)
- **Unblocks:** HS-158-06
- **Owner:** unassigned

## Problem

AD-PRJ-003: `ProjectMemoryCore` graduates into the Project Room —
not replaced. WEB-ARC-001/002: a typed controller owns state; the
core composes. WEB-IA-001: the window head names the scoped Project,
not "Project memory". The five-request fan-out dies; `GET /room` is
the default read; and the face earns the desk: orientation band from
real data, honest absent-states for the domains P2+ will fill.

## Scope

- **In:** two halves.
  (1) EXTRACTION (no behavior change; may run parallel to 01/02):
  `web/src/features/project-room/` per the Web SRS §2 boundary —
  `api.ts`, `model.ts` (typed decode — WEB-ARC-004),
  `useProjectRoomController.ts` (discriminated state — WEB-ARC-003),
  `ProjectRoomCore.tsx` composing what ProjectMemoryCore renders
  today; `ProjectMemoryCore.tsx` becomes the thin compatibility
  re-export (interview SRS §13). All 157 pins + existing core tests
  stay green UNCHANGED in this half.
  (2) ADOPTION (after 04): controller consumes `GET /room` for first
  render (fan-out retired; detail loads stay progressive); the head
  names the scoped Project (WEB-IA-001), label Project Room;
  orientation band shows outcome/purpose/lifecycle/posture when
  present and NOTHING fabricated when absent (Art VI; separate facts,
  no health-score collapse — WEB-LC-001/002); items render in the
  working field grouped by kind; absent sections show their honest
  state. Surface library primitives only (barrel imports; the ratchet
  fence never grows); no modals; voice mic on every new text input
  (WEB-A11Y-009); keyboard reachable; both themes.
  Then the BEAUTY PASS, then shot sheets at 1440+393 on the real hub
  (rig boots its own hub — never the owner's live desk) into
  `assets/story-05-shots/`. THE OWNER SEES THE SHOTS BEFORE MERGE —
  his verdict closes this story.
- **Out:** setup interview, Delta review posture, Updates plane,
  Steward strip (P1a-P4); dynamic `project-room:<id>` windows
  (WEB-IA-012, later).

## Acceptance criteria

- [ ] Extraction half lands with zero behavior change: 157 pins + projectMemoryCore tests green unchanged; vitest suites for the new controller/model added.
- [ ] First render = one `/room` request (test asserts no fan-out); progressive detail intact; orientation renders before slow sections; one failed section never blanks the rest (WEB-STA-001/002).
- [ ] Window head names the scoped Project; lifecycle/posture/absent-states are separate honest facts; zero prose, zero modals; mic on every new input; ratchet fence baseline unchanged.
- [ ] `npm --prefix web run check` green; web baseline zero branch-new; glass legs at 1440+393 with zero overflow.
- [ ] Shot sheet in assets/story-05-shots/ (before/after); THE OWNER'S SHOT VERDICT: PASS recorded verbatim.

## Test plan

- **Web unit:** controller/model/decode suites + updated core tests (additive).
- **Glass:** e2e shots at 1440+393 via the rig-booted hub.
- **Manual:** the owner's shot review — the closing gate.

## Notes / open questions

- The extraction half must not move CSS or rename testids — the pins are the leash.
