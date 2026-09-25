# Lane B follow-up ledger

Last updated: 2026-09-24 night.

This phase-local backlog is the handover home for findings outside lane B.
The existing `pm/roadmap/holdspeak/` roadmap remains untouched by this lane.

| Finding | Evidence | Disposition / owner |
| --- | --- | --- |
| Whole-desk refresh holds the decision result for about 1.8 s; the slower sibling is unidentified. | `body/diagnosis.md`; continuous red S4 traffic: decision GET resolves at 2297 ms, stale store commit about 4087 ms. | Backlog for the two brains: instrument sibling reads before choosing a performance repair. No performance claim in PHILO-6-05. |
| `deletePrimitive` and `renameZone` use optimistic writes without this version fence. | `web/src/desk/store/dataSlice.ts`; `checks/story-05-design-muaddib.md` MISSED 2 in the phase roadmap. | Backlog for a separate real-producer reproduction; not implemented here. |
| `loadSetup` rejection can reject the existing `Promise.all` and rollback refresh. | `web/src/desk/store/dataSlice.ts`; Muad'Dib design check MISSED 3. | Unverified pre-existing path; separate focused reproduction before repair. |
| Preserving an item absent from an overlapping read can briefly retain an item deleted on another surface. | `body/design.md`, refresh fence. | Accepted limited write-window consequence of the checked design; no deletion semantics changed intentionally. |
| Observer wrapper baseline provenance should capture the imported module path from the running hub. | `rows/baseline.json`; `rows/README.md`; story-04 built check MISSED. | Backlog rig enhancement. Current evidence explicitly sets archive PYTHONPATH and excludes the contaminated trial. |
| Phase-wide morning rehearsal and owner review remain open. | Phase status exit 3 / 4. | Muad'Dib integration lane after both lanes and owner-ratified toast placement. Lane B does not claim phase completion. |
| Two overlapping writes both refuse: the second rollback can briefly restore the first optimistic text, then its read restores the durable value. | Story-05 built check MISSED; `updatePrimitive` captures the current item as prior. | Backlog for an independently reproduced multi-refusal path; not a claim of durable rollback before the read in this ordering. |
| Retained green probe metadata says `complete: false` because completion is set after the after-shot. | `body/green-s4-*/observation.json`; built check MISSED. | Cosmetic rig follow-up. The verified frame lists cover the terminal observation; no pass is derived from this flag. |
