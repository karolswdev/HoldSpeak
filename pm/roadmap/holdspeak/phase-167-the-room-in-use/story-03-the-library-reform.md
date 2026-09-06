# HS-167-03 - The library reform: the species the design needs, promoted and expanded

- **Project:** holdspeak
- **Phase:** 167
- **Status:** done
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

- [x] Every species in the design exists in the barrel with a contract.md entry, tokens, a11y, vitest; zero private copies remain (grep fence for computeScrollHint outside the barrel).
- [x] The eight glass rigs run on the shared conftest, each building first, all green on the UNCHANGED faces (the reform breaks nothing).
- [x] Web baseline zero branch-new; the token validator green.

## Landed (2026-09-03)

SurfaceIdentity, SurfaceLedgerRow `trailing` + `wrap`, SurfaceVerbs
`active`, ScrollHint (axis prop; DoorBoardLane + the steward posture
consume it; the private copies are thin re-exports — ledgered) in the
barrel with contract.md sections + the DeskEditor note; JiraWizard's
raw px tokenized (its glass rig unchanged); EgressBadge already
delegated (six raw `.egress-badge` sites remain outside the barrel —
04/05 debt). tests/e2e/glass_infra.py is the ONE `_boot`/`_api`/
`_assert_clean`/`_ensure_build` (conftest.py is not importable as a
module — pytest's own rule); two copies reconciled honestly
(`_assert_clean` filters ResizeObserver noise; 166's raw-status `_api`
became `_api_allow_error`). ORCHESTRATOR CATCH: the worker's
`_ensure_build` trusted any existing marker — the 163 stale-pixels
theater reborn; rewritten to build whenever a web source is newer
than the marker, under a cross-process file lock (xdist-safe); the
first honest run rebuilt in 4.1s — the marker HAD been stale. Gates
read: surface vitest 252/252; token gate clean; the eight glass rigs
46 passed + 1 honest skip (`gh` auth absent in the isolated HOME) in
parallel; DoorBoardLane 55/55; web baseline zero branch-new (a first
run's single Door hit was a mid-edit artifact, clean on the settled
tree).

## Test plan

- **Web:** web/src/desk/surface/__tests__; `uv run python scripts/check_web_baseline.py --run`.
- **Glass:** tests/e2e/test_hs158..166_*_glass.py in isolated HOME, `-n auto`.
