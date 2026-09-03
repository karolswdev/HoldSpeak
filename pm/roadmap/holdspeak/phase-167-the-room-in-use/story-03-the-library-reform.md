# HS-167-03 - The library reform: the species the design needs, promoted and expanded

- **Project:** holdspeak
- **Phase:** 167
- **Status:** backlog
- **Depends on:** HS-167-01
- **Unblocks:** HS-167-04, HS-167-05
- **Owner:** unassigned

## Problem

The design (01) names species that do not exist in the barrel or
exist as private copies: the scroll-hint is a Y-axis copy in
steward/model.ts:253-267 of DoorBoardLane.tsx:255-268; the
EgressBadge lives in desk/setup.ts:48-54 outside the barrel; the
Room's orientation band, the comparison side-by-side and the
policy sheet have no species at all. The owner's ruling
(2026-08-31): reform the library, expand its delights so every
room enjoys them — no one-room-only species.

## Scope

- **In:** every species the settled design names, in
  web/src/desk/surface/ behind the barrel, with contract.md
  sections, tokens only (validate-tokens green), roving/aria per the
  contract, both container widths: ScrollHint (one implementation,
  axis prop; DoorBoardLane and the steward model consume it);
  EgressChip as the one egress species (desk/setup.ts's badge
  delegates or dies); the orientation band; the comparison split;
  the policy sheet on GadgetGroup/GadgetRow; any ledger-row internal
  the faces hand-rolled (list-primary/rev/time; step rows with
  receipt refs). JiraWizard.tsx:74-77's raw px moved to tokens. The
  glass conftest: tests/e2e/conftest.py carrying ONE `_boot`, `_api`,
  `_assert_clean`, `_ensure_build`; the eight 158..166 rigs import
  it and every rig builds first (the 163 stale-pixels law).
  Vitest for each species; the storybook-style species sheet shot
  at both widths for the gallery.
- **Out:** recomposing the faces (04/05); species no face in the
  design composes.

## Acceptance criteria

- [ ] Every species in the design exists in the barrel with a contract.md entry, tokens, a11y, vitest; zero private copies remain (grep fence for computeScrollHint outside the barrel).
- [ ] The eight glass rigs run on the shared conftest, each building first, all green on the UNCHANGED faces (the reform breaks nothing).
- [ ] Web baseline zero branch-new; the token validator green.

## Test plan

- **Web:** web/src/desk/surface/__tests__; `uv run python scripts/check_web_baseline.py --run`.
- **Glass:** tests/e2e/test_hs158..166_*_glass.py in isolated HOME, `-n auto`.
