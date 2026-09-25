# PHILO-6-05 — decision text stays after Done

Last updated: 2026-09-24 night.

The cause was the CREATE-triggered whole-desk refresh. Its decision read
finished before Done, then waited for a slower sibling. Its delayed store
commit erased the optimistic saved body. The first paint was already correct.
`diagnosis.md` records the trace and source anchors at the archived revision;
`design.md` records the checked repair. No DecisionPullout code changed.

The store snapshots per-item write versions before reads, keeps the current
item across an overlapping refresh, restores the prior body immediately on a
current refusal, and retains that item if the rollback read fails. An obsolete
refusal cannot roll back a newer success or post an old Retry. The map belongs
to each store instance. Other unreachable buckets keep their old behavior.

## Proof per acceptance box

1. **Cause before repair:** actual archived-main `red-s4-393-continuous/`
   and `red-s4-1440-continuous/` traces plus `diagnosis.md`. GET resolves at
   2297 ms, PUT starts at 3928 ms, blank appears at click +159.1 ms at 393.
2. **Continuous readable transition:** `verify_transition.py` checks the actual
   S4 cases, with the browser observer registered before Done. First frame
   remains required; every read-mode frame through terminal observation must
   be readable. Both widths change FAIL to PASS. This checked amendment is in
   story 05 and the phase status. The first-frame-only assertion was green on
   main and is never called a pre-fix red.
3. **Failed save:** the real Zustand producer, subscribed projection, pullout
   and receipt tests cover slow rollback read, failed rollback read and a
   stale refusal after newer success. `origin-main-red.log`: five semantic
   failures and two controls. `scoped-green-after-bucket-fix.log`: 29 passed.
   Astra repeated all 29 through DW. Existing receipt and no-loss tests pass.
4. **Actual atlas and glass:** `green-s4-393/` and `green-s4-1440/`, each one
   invocation of `scripts/graph_walk.py` against an isolated real hub and real
   LAN engine. Astra opened both after.png shots. Both decision bodies are
   visible, in the viewport and unobscured. Each saved trace contains 129
   readable frames from about +10 ms to +1.07 s (terminal observation).

```text
Origin-main: Tests  5 failed | 2 passed (7)
Parent DW: Tests  29 passed (29)
143 tests collected in 0.19s
143 passed in 99.83s (0:01:39)
393: FAIL (first blank +159.1 ms) -> PASS (no unreadable frame)
1440: FAIL (first blank +77.3 ms) -> PASS (no unreadable frame)
```

The paired roadmap `evidence-story-05.md` retains canonical DW command output.
The final frontend capture at `2026-09-25T03:19:34Z` also passes typecheck and
build. The earlier combined capture exited 2 on a bucket-assignment type error;
it is retained, and the typed helper fixed it. Its verbose build exceeded DW's
output cap; the final concise build capture is complete. An invocation missing
`--atlas` is retained as an excluded CLI error, not a product red.

## Provenance and limits

- Archive base: `66205729332ef66a6d16a186c04ae4801311734a`, created by
  `git archive origin/main`. Only test/rig/atlas overlays, no repaired product
  code. `baseline.json` records source hashes; `../rows/baseline.json` records
  the archive/import correction. Explicit PYTHONPATH keeps the hub on the
  archive, despite the reused Python environment's editable installation.
- Continuous baseline traces used the new probe before its rig version was
  bumped (raw provenance 1.2.0). Green traces use 1.3.0. Raw records remain
  unchanged. `red-s4-393/` is the earlier first-frame-only prototype that
  passed despite a later blank; it is a negative control, not the red fence.
- The original held-prop unit hypothesis was rejected: the real DeskApp
  subscribes to items and derives the object on each render. The retained
  synthetic test is explicitly labelled a negative control.
- Slower sibling identity, delete/rename race class and setup-read rejection
  remain in `../ledger.md`. No phase-wide rehearsal, owner sitting, or toast
  placement proof is claimed here. Scoped tests only, per the lane brief.

Tuesday: Done keeps the sentence readable. A current refusal shows the prior
sentence with the existing SAVE FAILED / Retry receipt.

Muad'Dib's built check is recorded in the phase roadmap
`checks/story-05-built-muaddib.md`; all pre-flip conditions are paid. The final
test-only amendment asserts the prior body and receipt after the failed
rollback read commits: archive still 5 failed / 2 passed, built 7 passed.
`build-identity.json` ties the green runtime index/assets to the source digest
and dataSlice hash before that additional assertion. Generated references and
the architecture/API checks passed (15 tests); no source runtime changed
after the green S4 runs.
