# Lane B follow-up ledger

Last updated: 2026-09-24 night.

This phase-local backlog is the handover home for findings outside lane B.
The three counsel-on-built follow-ups below also have a durable home in
`pm/roadmap/holdspeak/BACKLOG.md`, “PHILO-6 follow-ups”. Only those BACKLOG
rows change in the older roadmap.

| Finding | Evidence | Disposition / owner |
| --- | --- | --- |
| Whole-desk refresh holds the decision result for about 1.8 s; the slower sibling is unidentified. | `body/diagnosis.md`; continuous red S4 traffic: decision GET resolves at 2297 ms, stale store commit about 4087 ms. | Pre-existing performance item, not a hole in the version fence. Home: BACKLOG PHILO-6 follow-ups, row 1; two brains to instrument sibling reads before choosing a repair. No performance claim in PHILO-6-05. |
| `deletePrimitive` and `renameZone` use optimistic writes without this version fence. | `web/src/desk/store/dataSlice.ts`; `checks/story-05-design-astra-invoked-claude.md` MISSED 2 in the phase roadmap. | Backlog for a separate real-producer reproduction; not implemented here. |
| `loadSetup` rejection can reject the existing `Promise.all` and rollback refresh. | `web/src/desk/store/dataSlice.ts`; Astra-invoked claude -p design check MISSED 3. | Unverified pre-existing path; separate focused reproduction before repair. |
| Preserving an item absent from an overlapping read can briefly retain an item deleted on another surface. | `body/design.md`, refresh fence. | Accepted limited write-window consequence of the checked design; no deletion semantics changed intentionally. |
| Observer wrapper baseline provenance should capture the imported module path from the running hub. | `rows/baseline.json`; `rows/README.md`; story-04 built check MISSED. | Backlog rig enhancement. Current evidence explicitly sets archive PYTHONPATH and excludes the contaminated trial. |
| Phase-wide morning rehearsal and owner review remain open. | Phase status exit 3 / 4. | Muad'Dib integration lane after both lanes and owner-ratified toast placement. Lane B does not claim phase completion. |
| Two overlapping writes both refuse: the second rollback can briefly restore the first optimistic text, then its read restores the durable value. | Story-05 built check MISSED; `updatePrimitive` captures the current item as prior. | Backlog for an independently reproduced multi-refusal path; not a claim of durable rollback before the read in this ordering. |
| Retained green probe metadata says `complete: false` because completion is set after the after-shot. | `body/green-s4-*/observation.json`; built check MISSED. | Cosmetic rig follow-up. The verified frame lists cover the terminal observation; no pass is derived from this flag. |
| Unreachable collection reads empty the entire kind. After a failed decision save plus failed collection read, the rolled-back decision stays but its siblings disappear. | `web/src/desk/api.ts:628,636` starts with empty buckets and marks the rejected kind unreachable; actual Muad’Dib counsel MISSED 3. | Pre-existing product bug, not fixed by 05. Home: BACKLOG PHILO-6 follow-ups, row 2; two brains to reproduce multi-item failed-read behavior before repair. No new reproduction in round two. |
| Red continuous S4 logs say `rig=1.2.0` while their continuous predicate text comes from 1.3.0; green runs name 1.3.0. | `body/red-s4-393-continuous.log`, `body/red-s4-1440-continuous.log`; actual counsel MISSED 5. | Cosmetic provenance debt; preserve the raw logs. Home: BACKLOG PHILO-6 follow-ups, row 3; rig owner to stamp the actual source revision consistently. |

Round-two classification: the slow refresh and unreachable-kind behavior are
inherited debt, not new regressions and not flakes; the rig stamp is cosmetic.
The a/b/c test-fallout scheme does not reclassify inherited product debt as a
flake (c). No new test fallout is claimed here.

## PHILO-6-03 placement build

| Class | Finding | Proof | Home / disposition |
| --- | --- | --- | --- |
| (a) inherited test fixture mismatch | `arrivalSummaryRun.test.tsx` seats only the meeting bucket (`seatMeeting`, line 57); the real refresh iterates every current kind bucket (`dataSlice.ts:191`). The untouched scoped run has 214 passing assertions but exits 1 with `currentBucket is not iterable`. | Untouched `git archive origin/main` at d8f608c8, own dependencies and isolated HOME: `toast/placement-proof/scoped-baseline.txt`; narrower branch/archive pair: `slot-chair-run.txt` and `slot-chair-baseline.txt`. | Final branch scope: 235 assertions pass, exit 1 on the same error (`toast/placement-proof/final-scoped-run.txt`). Separate fixture repair under this ledger. No product change or green-suite claim in 03. The production store starts with all buckets; this test bypasses that shape. |
| Out of scope, inherited placement limitation | Spatial WebGL Floor has no ratified flow slot; it retains the existing fixed card placement. | `pm/roadmap/holdspeak-philo/phase-6-the-honest-morning/assets/story-03-shots/20260925T050750Z-case.philo603.toast.floor_spatial_fallback-astra-393/after.png` and `observation.json`: computed fixed, 9/9 card points, zero scroll calls; WebGL items remain covered. | A later spatial-Floor placement canvas and story; this lane does not claim its no-overlap repair. |
| Browser proof limit | The actual 393/1440 walks use Chromium. The Arrival correction depends on native `overflow-anchor`; older engines without it can reproduce the late-summary shift. Safari 27 now supports it ([WebKit](https://webkit.org/blog/18325/webkit-features-for-safari-27-0/#scroll-anchoring)), but this lane makes no Safari device claim. | Built diagnostic `20260925T045018Z` and corrected `20260925T045707Z`; Astra-invoked check C1, scoped honestly. | If support for an engine without anchoring is required, coordinate the one scroll with completion of the asynchronous summary render and fence that engine. No compatibility shim in this pre-alpha lane. |
| Unverified multi-window extension | When a non-surface pullout is frontmost, the fallback can select an open surface window behind it; the first visible surface host follows DOM order. | `web/src/components/AmbientLayer.tsx` `findAftercareSlot`; Astra-invoked check finding 3. Single foreground Meetings, Arrival and Floor-list cases are verified; this overlap combination was not walked. | Separate multi-window placement decision and actual producer reproduction before extending this story's layout claim. |
| Latent rig composition limit | If a future atlas case declares both Dismiss and framing, the framing shot-list assignment replaces the dismissal entry. No PHILO-6-03 case declares framing, and the current observations retain all three shots. | `scripts/graph_walk.py:4857-4866`; closing Astra-invoked check finding 4. | Rig follow-up when a case needs both transitions: append the framing shot to the existing list and fence the combined case. No claim that the current placement cases lose a shot. |
| Inherited roadmap debt | Global `dw check` exits 1 on six existing errors: phase 101 story-04 evidence with a non-done story, and absent final summaries for phases 152, 153, 154, 156 and 200. | `toast/placement-proof/dw-global-baseline.txt`: the pinned untouched-main archive returns exactly the same errors; the branch capture at 05:37:14Z retains its output. PHILO-only check passes at 05:38:01Z. | Existing main-roadmap maintenance, outside this lane; no edits under `pm/roadmap/holdspeak/`. No global-clean claim. |

The initial worktree sync selected broken Homebrew Node 25 (`libllhttp.9.3.dylib` missing); pinning the existing Node 22.21.0 path made `uv sync --extra dev` and `npm ci` pass. No machine installation or global configuration changed.
