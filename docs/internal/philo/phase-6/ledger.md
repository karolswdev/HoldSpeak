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
