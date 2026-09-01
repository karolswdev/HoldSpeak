# HS-159-05 - The interview face: two questions and a living brief

- **Project:** holdspeak
- **Phase:** 159
- **Status:** done
- **Depends on:** HS-159-04 (scaffolding may start against 04's frozen contract)
- **Unblocks:** HS-159-07
- **Owner:** unassigned

## Problem

WEB-CR-001..015 (the P1a-applicable subset): Project becomes
authorable through the shared creation grammar; the first questions
are "What are you trying to accomplish?" and "What should HoldSpeak
notice without being asked?" (WEB-CR-002); within two questions,
typed Watch candidates + a live brief of the durable configuration
(WEB-CR-003/INT-003); autosave + Continue-setup after reload
(WEB-CR-009); activation review shows everything (WEB-CR-011/ACT-001);
success opens populated Now (WEB-CR-012). §13: setup composes a
guided question plane + live brief at wide widths; keyboard
WEB-CMD-005; a11y WEB-A11Y-008/009. No modals; no prose; voice
fills but never submits (WEB-CMD-006).

## Scope

- **In:** `web/src/features/project-room/setup/` (inside the
  existing feature boundary): the interview plane + live brief
  (SurfaceColumns at width; brief follows in DOM order below 560px —
  WEB-RSP-005), suggestion cards as OBJECTS (the 156-08/158 taste:
  source chip, subject, conditions in plain words, cadence, readiness
  state, rationale — INT-008), the brief distinguishing
  mentioned/proposed/tested/disabled/active (INT-011), the bounded
  clarify step for a selected native candidate (INT-009), the
  activation review (ACT-001) and finalize → the Room opens scoped
  (WEB-CR-012 — via the existing open-project-memory action),
  Continue-setup on reload (WEB-CR-009), the Blank path visible and
  unshamed (INT-002). Creation entry: the shared creation/command
  grammar (find where Desk objects get created today — match it;
  WEB-CR-001). Enter/Shift+Enter/Cmd+Enter/Escape/arrows/Space per
  WEB-CMD-005; announcements per WEB-A11Y-008; mic per WEB-A11Y-009.
  Then the BEAUTY PASS, bundle rebuild, shots at 1440+393 into
  assets/story-05-shots/. THE OWNER'S VERDICT closes this story.
- **Out:** provider wizard/discovery UI (P2a), model assistance,
  Info→Watches edit mode (INT-012 — P2a hardening), template pickers
  (V1).

## Acceptance criteria

- [ ] Two questions max before candidate cards (INT-003 — tested); candidates render source/scope/conditions/action/cadence/readiness/rationale as object slots (INT-008).
- [ ] The live brief mirrors the durable session state at every step and distinguishes the five watch states (INT-011).
- [ ] Reload mid-interview → Continue setup restores the exact stage (WEB-CR-009, against real route persistence).
- [ ] Activation review shows outcome, each Watch spec, cadence, action, test result, first-run behavior (ACT-001/WEB-CR-011); finalize opens the populated Room (WEB-CR-012).
- [ ] Keyboard + announcements per WEB-CMD-005/WEB-A11Y-008; voice fills, never submits; zero modals; zero prose; ratchet fence unchanged; both themes.
- [ ] `npm --prefix web run check` green; baseline zero branch-new; glass overflow-free at both widths.
- [ ] Shot sheet (before/after if bounced); THE OWNER'S SHOT VERDICT: PASS recorded verbatim.

## Test plan

- **Web unit:** setup plane/brief/cards/controller suites; keyboard + announcement tests.
- **Glass:** rides story 06's walk legs + dedicated face shots.
- **Manual:** the owner's verdict — the closing gate.

## Verdict record

- **ROUND 1 (the orchestrator's own review):** wall-of-text cards —
  six defects fixed in 103496ad (card objects, plain-words
  conditions, YOLO token, dl ledger, count chips, one step system).
- **ROUND 2 — THE OWNER'S BOUNCE (2026-08-31, verbatim):** looking
  at walk-review-1440: "I legit don/t know what I am looking at...?"
  Diagnosis: the review fails WEB-CR-011's job — (1) no consequence
  headline (what activation MEANS), (2) the review and the brief say
  every fact twice, (3) the primary verb below the fold, (4)
  "SIGNALS" jargon, (5) floating unframed test evidence. Round 2 in
  flight on exactly this list.

- **ROUND 3 (2026-08-31):** the consequence round landed (headline in
  frame after the orchestrator's scroll fix, one column, pinned
  verbs, framed evidence) — the review shot passes. THE OWNER
  BOUNCED THE CARDS (the orchestrator's own stated reservation):
  token-level wash/hairline fixes did not register on the dark
  plane. Round 4 ruling: STOP hand-rolling card CSS — adopt the
  library ChoiceCard (the 156-08 object) so the cards inherit real
  material, slots, and selection presence from the one place that
  owns them.
- **ROUND 4 (12f9be03):** the cards wear ChoiceCard (classes, not the
  radiogroup component — multi-select listbox semantics, reasoned);
  name anchor, plain-words summary bar, labeled fact chips, action
  fold, library selection presence; 80 lines of bespoke CSS deleted.
- **ROUND 4 VERDICT: PASS** (owner, 2026-08-31: "PASS — close it").
  Four rounds total: orchestrator walls-of-text → owner's
  "I legit don/t know what I am looking at" consequence round →
  orchestrator clip/material touches → the library cards. The story
  closes; the verdict holds the merge word.

## Notes / open questions

- Fixtures speak the backend's dialect — decode against 04's REAL wire, never imagined shapes (the 158 law).
