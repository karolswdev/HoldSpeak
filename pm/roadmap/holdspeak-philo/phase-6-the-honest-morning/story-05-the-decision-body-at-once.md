# PHILO-6-05 - The decision body at once

- **Project:** holdspeak-philo
- **Phase:** 6
- **Status:** backlog
- **Depends on:** -
- **Unblocks:** exit 3 (the decision body present at once after Done)
- **Owner:** Astra (Luna); Muad'Dib checks
- **Closure finding:** BACKLOG "PHILO-5-04 follow-ups", the S4 row; Astra's check of the drafts, finding 2 row 6
- **Canvas:** none (the existing transition, repaired)

## Problem

After Done in the decision pullout at 393, the DECISION body is empty for about one second: empty at 0.950 s, readable at 1.363 s; at 1440 readable at 0.955 s (`../phase-5-the-one-service-layer/assets/story-04-shots/carried/s4-393/20260924T233554Z-case.closure.chain.s4_saved_content-astra-393/`, `…/carried/verification/s4-1440-observation-summary.json`). The save/exit seam is `web/src/desk/pullouts/DecisionPullout.tsx:66` (`updatePrimitive("decision", …)`); `:69-71` is status cycling, not this seam (the BACKLOG row's `:69-71` is citation drift). `web/src/desk/store/dataSlice.ts:297` already patches the text optimistically, so "await the refresh" is NOT a diagnosis. The cause is unknown.

## Scope

- **In:** find and record the cause; repair the existing transition; the fences on the first transition and the failed save; the rig case at 393.
- **Out:** a new edit flow; any change to the pullout's verbs; everything the phase status lists as out.

## Acceptance criteria

- [ ] The cause is found and recorded with file:line and a probe that shows it (a render trace or a store timeline), before the fix.
- [ ] After Done, the first rendered frame of the read mode shows the saved text (no empty DECISION body). Fence on the INITIAL transition, not on eventual text; red pre-fix.
- [ ] A failed save does not show the new text as saved and does not show an empty body; the existing failure idiom is shown. Fenced.
- [ ] Rig: the S4 case (`case.closure.chain.s4_saved_content`) at 393 with a readability predicate (`readable_text`: visible, in the viewport, unobscured) at or before the first paint after Done; and at 1440.

## Effort (council-style estimate, not a promise)

0.5–1 day incl. the diagnosis

## Test plan

- **Unit:** vitest on the pullout's Done transition (first frame) and the failed save; red pre-fix.
- **Integration:** the S4 case at 393 and 1440 through `scripts/graph_walk.py`, `--out` under this phase's assets.
- **Manual / device:** rehearsed, owner-reviewed shots (exit 4).

## Notes

- 2026-09-24 — chartered from XXVIII r2 + Astra's check (finding 2 row 6: the seam is `DecisionPullout.tsx:66`; `dataSlice.ts:297` already patches optimistically; find the cause; fence the first transition and the failed save).
- 2026-09-24 — Astra's charter check: the proof plan REQUIRES the observation ARMED BEFORE Done — the rig waits 900 ms before its initial observation (`graph_walk.py:4393`) and the S4 atlas case allows 60 s (`atlas-phase3.json:6449`), so a passing rerun of the existing case cannot certify the first frame; keep the actual-atlas run AND add a transition probe (a browser-side observer registered before the click that records the DECISION body's text at first paint and every frame until readable); the fence fails if the first paint after Done is empty.
