# HS-167-01 - The audit + the settled design: the whole Room on the library

- **Project:** holdspeak
- **Phase:** 167
- **Status:** in-progress
- **Depends on:** -
- **Unblocks:** HS-167-03, HS-167-04, HS-167-05
- **Owner:** unassigned

## Problem

Seven of the eight Rooms faces were built brief-first and never
designed. The owner's law (2026-09-03): no face is built before he
has ratified its design on the library. This story is the design —
zero product code.

## Scope

- **In:** (a) the drift audit, committed under assets/: every face,
  its species count, every hand-rolled block with file:line (the
  recon's list is the seed: ProjectRoomCore.tsx:191/:197/:341-376/
  :431-477/:489-551; SetupInterview.tsx:167-206/:261-309;
  ActivationReview.tsx:152-170/:185-219; SetupBrief.tsx:27-35;
  ProviderWizardStep.tsx:46-114/:147-202/:349-440;
  ReviewPosture.tsx:47-55/:61-91/:110-138/:147-150;
  UpdatePosture.tsx:70-99/:129-158/:187-210;
  StewardPosture.tsx:62-100/:230-265/:293-331/:335-461;
  JiraWizard.tsx:74-77 raw px). (b) the settled design,
  assets/settled-design-room.md, in the 166 D1-D5 form but for the
  WHOLE Room: the spine every face shares (orientation band, ledger
  grammar, chip vocabulary, scroll-hint, footer with egress/receipt/
  verbs), then one section per face naming the species it composes
  and the species it needs that do not exist yet (the 03 list).
  Zero sentences in the UI; the egress chip names the real host at
  the point of egress; the Workbench 2.0 mold visible, dreamed
  forward. (c) the mockups: a `design` canvas with every face at
  1440 and 393, real token values, the .dc.html sources committed
  under assets/mockups/ (166's sources were session-local — never
  again). (d) the owner's verdict recorded verbatim in this story
  and the record; a bounce = redesign, not a build.
- **Out:** any change under web/src or holdspeak/.

## Acceptance criteria

- [ ] The audit names every hand-rolled block with an anchor and the species that replaces it; counsel reads the design first and its findings are paid in the design.
- [ ] Mockups for all eight faces at both widths published; sources committed; token values real (no raw px).
- [ ] The owner's word recorded verbatim; PASS before 03/04/05 start.

## Counsel round (2026-09-03)

Counsel (opus-worker, read-only) read the design against the barrel,
contract.md, the 166 precedent and the seven current faces: **RATIFY-
WITH-CONDITIONS** — 3 M (SurfaceLedgerRow's real props are `cells`,
not `tokens`/`trailing`; SurfaceIdentity had no typed contract; the
"On track" health chip fabricated a field the Room wire lacks), 9 S
(the design silently retired the TIMELINE/DECISIONS/SEARCH wings;
SurfaceSplit is master/detail, not a comparison; SurfaceVerbs has no
`active`; DeskEditor is not in the barrel; CitationChips is per
section; Review's keyboard grammar and two-step Defer unnamed; the
steward grant sentence dropped; the cadence stepper inert until 02;
no absent/degraded states), 6 N (mic in Review; `REV` casing; the Ask
well's runtime egress chip; LampGadget misused as a counter ×2;
SurfaceStreamDay/Entry unnamed). ALL EIGHTEEN PAID in the design
(D0 spine rows added: wings kept, absent/degraded, keyboard; D9 is
now a props table). The wings law: nothing retires.

## The mockups (2026-09-03)

Canvas: https://claude.ai/code/artifact/1dd81936-2c1a-484f-a78e-f56e5a5cf22b — sixteen
artboards (eight faces × 1440 window + 393 glass), two Fedaykin
authors composing from the atlas (assets/mockups/library-atlas.md:
every species' resolved values, extracted read-only from the barrel)
and the settled design. The orchestrator read all sixteen PNGs at
true size, three bounce rounds paid (primaries that ellipsized at 640
and 393; provenance chips abbreviated to "GH"/"ACLI" dropping the
host — an egress-honesty violation; a phone chrome missing a gem and
two wings; unequal CURRENT|PROPOSED columns; a chevron colliding with
the time cell; citation chips in a serif fallback; two footers
colliding at 393). Sources committed: assets/mockups/*.dc.html +
canvas.json; shots: assets/story-01-shots/. **Owner's word: PENDING.**

## Test plan

- **Design:** the token validator (`web/scripts/validate-tokens.cjs` or its current home) over the mockup sources; `.githooks/dw check holdspeak` green on phase-167.
