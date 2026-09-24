# PHILO-4-04 - The triaged headline

- **Project:** holdspeak-philo
- **Phase:** 4
- **Status:** done
- **Depends on:** PHILO-4-01 (the quiet branch it draws, boards 7b, 8a, 8b)
- **Unblocks:** the morning in one move
- **Owner:** Astra (Muad'Dib counsels on built; PR #627 remains open)
- **Council tag:** Astra r3 finding 6 (the PHILO-4-01 canvas check, round three)

## Problem

After every row is handled, the stored headline still says "N things waiting" with nothing to reach. The producer composes the headline once, at generation, from the brief's items (`holdspeak/services/monday_brief_service.py:327-387`; the items in their sections, e.g. `Commitment due` into `decisions` at `:812`). Triage writes the shelf and never rewrites the headline (`shelve`, `:1110-1139`). The Arrival's quiet branch renders that stored headline, bare, when nothing is untriaged (`web/src/desk/chair/ChairHome.tsx:1283`, the headline at `:1310`). So the generated snapshot and the current triage state are conflated. On the canvas (round five fixture, `assets/story-01-canvas/harness/compose_headline.py`, the real `_compose`), the day-one brief has six rows (m1 changed; o1, u1, l1 waiting; d2, c1 decisions). Board 7b: the owner has handled every row (Ack or Defer), and the section still shows `1 thing changed, 3 things waiting, 2 decisions waiting.`

## Scope

- **In:** the result below, its fence(s) red pre-fix, the face at 1440 and 393.
- **Out:** everything the phase status lists as out; the brief window (`BriefView.tsx`).

## Acceptance criteria

- [x] The headline distinguishes the generated snapshot from the current triage state, without rewriting historical counts (the stored headline and the items stay as generated).
- [x] Canvas first: the face is designed on the library and the owner ratifies it before build (UX-CANON A.2).
- [x] Fence red pre-fix, asserting the INTENDED state: render the quiet branch with the round-five fixture (six rows, every row Ack'd or Defer'd). The fence asserts that the section distinguishes the generated snapshot from the current triage state: the headline is marked as the generated snapshot, or the triaged state is named (the exact words come from the ratified canvas). It fails today, because `arrival-brief-headline` holds the bare stored sentence and nothing on the section names the state (`ChairHome.tsx:1310`). The same fence asserts that no `BRIEF · 0 …` head shows (no counter of zero), and that the stored headline and the six items read back unchanged (no rewriting of historical counts).

## Acceptance proof — 2026-09-24

1. **Snapshot and current triage:** `ChairHome.tsx:886-899` derives the
   positive Arrival-only state from acknowledged/deferred shelf entries;
   `:1395-1405` renders it after the original headline and date. The static
   12 px receipt adds no control or live region. The shared seven-row
   `_compose` variant proves that `ALL 6 HANDLED` can be smaller than the
   headline total. Partial, hidden unshelved and empty states show no line.
   [Rendered fences](../../../../web/src/desk/chair/__tests__/triagedHeadline.philo404.test.tsx).
2. **Canvas first:** owner ratification of board 7c and all three asks is
   recorded in `89208bae`, the Notes below, and the
   [canvas README](assets/story-04-canvas/README.md). The sitting was waived.
   Historical transition PNGs use the earlier alternative date placement;
   the explicit board 7c ruling controls the build in every state.
3. **Intended-state red, then green; historical values retained:** final
   rendered fence on an archive of `origin/main` at `6cfc64e0` gives
   `Tests  5 failed | 3 passed (8)`, then `Tests  8 passed (8)` after the fix.
   Empty and all-handled tests exclude `BRIEF · 0`; generating, failure
   and same-day-success tests retain the handled line in order. The real
   `generate`/`shelve`/fresh `get_latest` test preserves the six-item fields,
   headline and dates, using explicitly named collector adapters for the
   original `_compose` fixture. Full collection is exercised separately
   through two production-created decisions on the actual atlas.
   [Red provenance](../../../../docs/internal/philo/phase-4/headline/rendered-red-origin-main-20260924T0818Z.md),
   [readback fence](../../../../tests/unit/test_philo4_04_headline_storage.py),
   [observation proof](../../../../docs/internal/philo/phase-4/headline/observation-proof.json).

The actual atlas case `case.philo404.arrival_triaged_headline.all_handled`
passes at 1440 (`20260924T142054Z`) and 393 (`20260924T142158Z`). Both use
real Generate/Ack/Defer face gestures, retain an unchanged stored headline
and item rows, show `ALL 2 HANDLED`, and pass `readable_text` with all nine
hit points owned. Before/after shots were inspected by Astra. Final scoped
verification: **90 Python tests and 36 rendered tests passed**; graph/API/
boundary reference checks passed. No full suite was run, by lane instruction.
[Captured evidence](evidence-story-04.md),
[lane report](../../../../docs/internal/philo/phase-4/headline/lane-report.md).

## Effort (council-style estimate, not a promise)

0.5–1 day

## Test plan

- **Unit:** fences that fail pre-fix for every repaired seam.
- **Integration:** the quiet branch on the rig at 1440 and 393, observations retained under this phase's assets.
- **Manual / device:** the owner's sitting on the morning.

## Notes

- 2026-09-23 — chartered (unratified) from Astra's round-three check of the PHILO-4-01 canvas (finding 6); the canvas README ask 6 points here.
- 2026-09-23 — canvas round six (Astra round-five condition): the Problem cites the round-five fixture; the fence criterion asserts the intended state, so it fails today.
- 2026-09-24 — RATIFIED by the owner on the canvas (https://claude.ai/artifact/WJocx1XUtYfvHzZM6s1qed, PR #627 @ 34475b1e): board 7c; the count = Arrival rows with Ack/Defer (THIS WEEK excluded); `No changes` bare. Build what was ratified.

- 2026-09-24 — built and verified by Astra; all three acceptance boxes paid. PR #627 remains open for Muad'Dib's counsel on built. No merge or owner observation claimed.
- 2026-09-24 — Muad'Dib's counsel on built: RATIFY-WITH-CONDITIONS (`checks/story-04-built-muaddib.md`); C1 (the headline sentence ledgered as Tenet 4 debt) paid in the same commit.
