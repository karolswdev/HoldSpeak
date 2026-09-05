# HS-169-03 - The Room rebuilt to the canvas (the head with the one headline; NEEDS YOU; SOURCES; SINCE YOU LOOKED; DECISIONS & COMMITMENTS; the ask well; two wings ROOM · HISTORY)

- **Project:** holdspeak
- **Phase:** 169
- **Status:** done
- **Depends on:** HS-169-01, HS-169-04
- **Unblocks:** HS-169-05, HS-169-06
- **Owner:** unassigned

## Problem

The Room showed counters of zero, raw field names, and four wings the owner did not understand. The ratified canvas (01) shows a Room that answers four questions.

## Scope

- **In:** ProjectRoomCore recomposed to the canvas from the library (SurfaceIdentity recomposed; SurfaceLedger/Row; SurfaceStream for HISTORY; SurfaceWell + MicButton for the ask; SurfaceFooter); the headline at display step ONCE (`N need you` / `Nothing needs you`); the health chip DERIVED from the source counts with its reason token (the derivation named in code and tests); SOURCES rows with live counts, `checked` time, host chip, hover verbs `Adjust` `Pause`; failing Watches in plain words with `Fix` / `Remove`; `SUGGESTED` rows offered never applied; SINCE YOU LOOKED grouped by source in phrases from the wire (04); DECISIONS & COMMITMENTS hidden when empty; the ask well on the desk-chat grammar with the model's egress chip; the Room's default width 800; wings ROOM · HISTORY only; the footer receipt `READ · NEXT CHECK`; every empty state one true line; the name said once. The 167 identity-band dedup and the 168 wings species fix carry.
- **Out:** the steward's run faces (167, reachable from `Adjust`); the update composer (162, reachable from `Draft update`).

## Acceptance criteria

- [ ] The Room's first paint after activation shows the source counts (never blank); the rig asserts it.
- [ ] Exactly one display-step element per face; three type steps present (the geometry walk).
- [ ] No counters of zero, no raw field names, no `REV`, no repeated name (a product-copy guard for the Room).
- [ ] Every verb is the library Button; hosts named where egress happens; the ask answers in an aerogel inset, never a modal.
- [ ] Vitest for the six sections' states; the glass rig at 1440 + 393 for both artboard states (needs you / quiet) and HISTORY.

## Test plan

`cd web && npx vitest run src/features/project-room`; tests/e2e/test_hs169_room_glass.py (both widths, three states); the web baseline; the Room copy guard under tests/unit/test_hs169_room_copy.py.

## Delivered (2026-09-05)

- ProjectRoomCore recomposed to the canvas over five rounds against
  the artboards: two wings ROOM · HISTORY; the head with ONE
  display-step headline (`N need you` / `Nothing needs you`), the
  health chip `● AT RISK` / `● ON TRACK` with its reason, the target
  token, `CHECKED <age>`, one primary verb `Draft update` (the 162
  composer's opener); the outcome line only when the title bar
  truncates; NEEDS YOU rows at the primary step with severity-toned
  WHY tokens and `Open` / `Decide` (+ a section-level `Review N` when
  proposals are pending); SOURCES rows in the two-line grammar (scope
  + count tokens · checked + host; `Pause`/`Resume`, `Remove` on
  cant_check with the plain reason; a section-level `Steward` verb as
  the honest interim entry to the 167 steward face); SINCE YOU LOOKED
  / SINCE CREATED in phrases; DECISIONS & COMMITMENTS hidden when
  empty; the ask well pinned to the body's foot (mic right; the model
  host chip, `MODEL · NOT SET` + `Choose` when unassigned; answers as
  an aerogel inset; `runAsk` with the project grounding); HISTORY as a
  SurfaceStream with flat filter tokens, a search typeahead and the
  footer receipt `N TODAY · M THIS WEEK`; the read marker posted after
  first paint and on Refresh; `READ · NEXT CHECK` from the wire (NEXT
  CHECK omitted when null); the window 800 wide; 393 stacks under a
  560px container query; motion moments 3 and 4.
- Selector edits (never skips) across the existing Room, controller,
  manifest, posture and core tests; web baseline zero branch-new
  (2423 passed); vitest project-room 19 files / 564.
- The glass rig tests/e2e/test_hs169_room_glass.py at 1440 + 393 with
  probes for the artboard, not just presence: one display element,
  primary-step titles in the sans face, tokens within 24px of their
  scope, no intersecting row children, the ask well inside the body,
  the read route called once after paint, HISTORY's count equal to
  the entries under TODAY, the window ≥ 800 wide. Shots in
  assets/story-03-shots/ read beside the artboards.
- tests/unit/test_hs169_room_copy.py: no `REV`, no PROJECT footer
  token, no zero counters, no raw kinds.
- Debts (07 ledger): the per-source `Adjust` well (the route
  `PUT /api/watches/{id}/rules` exists; the Door's AdjustWell must be
  extracted into a shared component first) — the verb is withheld, not
  dead; the steward's settings under the source rows (today the
  section-level `Steward` verb); the 167 TIMELINE/DECISIONS/SEARCH/ASK
  faces to park.
