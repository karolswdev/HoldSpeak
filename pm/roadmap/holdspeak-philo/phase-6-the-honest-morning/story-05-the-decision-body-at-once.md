# PHILO-6-05 - The decision body at once

- **Project:** holdspeak-philo
- **Phase:** 6
- **Status:** done
- **Depends on:** -
- **Unblocks:** exit 3 (the decision body present at once after Done)
- **Owner:** Astra (Luna); Muad'Dib checks
- **Closure finding:** BACKLOG "PHILO-5-04 follow-ups", the S4 row; Astra's check of the drafts, finding 2 row 6
- **Canvas:** none (the existing transition, repaired)

## Problem

After Done in the decision pullout at 393, the DECISION body is empty for about one second: empty at 0.950 s, readable at 1.363 s; at 1440 readable at 0.955 s (`../phase-5-the-one-service-layer/assets/story-04-shots/carried/s4-393/20260924T233554Z-case.closure.chain.s4_saved_content-astra-393/`, `…/carried/verification/s4-1440-observation-summary.json`). The save/exit seam is `web/src/desk/pullouts/DecisionPullout.tsx:66` (`updatePrimitive("decision", …)`); `:69-71` is status cycling, not this seam (the BACKLOG row's `:69-71` is citation drift). `web/src/desk/store/dataSlice.ts:297` already patches the text optimistically, so "await the refresh" is NOT a diagnosis. The cause was unknown at charter; the pre-fix trace in `docs/internal/philo/phase-6/body/diagnosis.md` now identifies the delayed CREATE refresh commit.

## Scope

- **In:** find and record the cause; repair the existing transition; the fences on the first transition and the failed save; the rig case at 393.
- **Out:** a new edit flow; any change to the pullout's verbs; everything the phase status lists as out.

## Acceptance criteria

- [x] The cause is found before the fix: `docs/internal/philo/phase-6/body/diagnosis.md`, source anchors at the archive revision and both `red-s4-*-continuous/` traces show the CREATE refresh's decision GET resolving before Done, with the whole refresh committed later after a slower sibling.
- [x] With the observer armed before Done, the first read frame and every frame through terminal observation remain readable. `body/verify_transition.py` checks the actual S4 red/green pair at both widths; `evidence-story-05.md` captures the run. Continuous pre-fix blank: +159.1 ms at 393, +77.3 ms at 1440. First-frame-only was already green on main. Built: 129 readable frames at each width.
- [x] Failed saves restore the prior body with the existing SAVE FAILED / Retry receipt; stale refusals do not post an obsolete Retry. Real store/producer/receipt tests: `web/src/desk/__tests__/philo605DecisionBodyDiagnosis.test.tsx`; `body/origin-main-red.log` (5 failed, 2 controls passed), `evidence-story-05.md` final frontend capture (29 passed).
- [x] Actual S4 atlas case at 393 and 1440, with pre-click observer and readable_text geometry/hit tests: `body/green-s4-393/` and `body/green-s4-1440/`. Parent inspected both after.png shots. Full commands and PASS terminal=settled are in `evidence-story-05.md`; no claim of phase-wide rehearsal or owner review.

## Effort (council-style estimate, not a promise)

0.5–1 day incl. the diagnosis

## Test plan

- **Unit:** real store and rendered pullout/receipt tests for Done, overlapping refreshes and failed saves; five semantic reds on archive. Browser probe tests require the first read frame and all later frames to stay readable.
- **Integration:** the S4 case at 393 and 1440 through `scripts/graph_walk.py`, `--out` under this phase's assets.
- **Manual / device:** rehearsed, owner-reviewed shots (exit 4).

## Notes

- 2026-09-24 night — checked amendment (`checks/story-05-design-muaddib.md`, condition 5): actual archived-main S4 traces show a readable first frame, then an older refresh erases the body at +159.1 ms (393) / +77.3 ms (1440). Criterion 2 now fences the continuous transition, retaining the initial-frame requirement. The original first-frame-only probe is a passing negative control, not claimed as red. See `docs/internal/philo/phase-6/body/diagnosis.md` and both `red-s4-*-continuous/` records. The owner can overrule this recorded amendment.
- 2026-09-24 — chartered from XXVIII r2 + Astra's check (finding 2 row 6: the seam is `DecisionPullout.tsx:66`; `dataSlice.ts:297` already patches optimistically; find the cause; fence the first transition and the failed save).
- 2026-09-24 — Astra's charter check: the proof plan REQUIRES the observation ARMED BEFORE Done — the rig waits 900 ms before its initial observation (`graph_walk.py:4393`) and the S4 atlas case allows 60 s (`atlas-phase3.json:6449`), so a passing rerun of the existing case cannot certify the first frame; keep the actual-atlas run AND add a transition probe (a browser-side observer registered before the click that records the DECISION body's text at first paint and every frame until readable); the fence fails if the first paint after Done is empty.
