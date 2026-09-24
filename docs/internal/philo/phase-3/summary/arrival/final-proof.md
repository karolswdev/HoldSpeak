# PHILO-3-02 Arrival frontend proof

Date: 2026-09-23. This proof covers the repaired Arrival seams in the
assigned frontend lane. The producer wire is the retained
`tests/fixtures/philo3_summary_wire.json`; the test-only identity helper only
gives lifecycle snapshots distinct IDs when a fence needs several rows. It
does not change producer status, cause, receipt, transcript, or summary data.

The final origin/main pre-fix run is
[`pre-fix-origin-main-final-11.raw.log`](pre-fix-origin-main-final-11.raw.log). It uses a fresh
`git archive origin/main` copy, the real producer fixture, and the existing
mapper with only a test-only export. It reached rendered assertions and failed
all 11 completion tests, including both Run-once transitions. The exact export adaptation is retained in
[`pre-fix-mapper-export.patch`](pre-fix-mapper-export.patch).

The final focused collection is
[`focused-final.collect.raw.log`](focused-final.collect.raw.log), with 23
named tests. The final focused run is
[`focused-final.after-ready-fix.raw.log`](focused-final.after-ready-fix.raw.log): 4 files passed and 23 tests
passed. It includes Run-once → running → ready through the debounced
`desk_changed` refresh, durable actual receipt rendering, retry → terminal
failure receipt retention, producer cause, the three-detail-read cap, stale
generation drop, and named wrong-identity read errors.

The isolated typecheck is [`typecheck.after-ready-fix.raw.log`](typecheck.after-ready-fix.raw.log) and passed.
Astra independently repeated the final four files: **23 passed**, retained
in [`astra-focused-final.raw.log`](astra-focused-final.raw.log), and read the
final pre-fix failure tail. The successful state has no retry/failure facts
well, as the ratified canvas requires.

The earlier `pre-fix-real-fixture.txt` and `report.md` are superseded worker
claims. Their claimed rendered pre-fix results were not supported by the raw
output. They are retained as history and are not evidence for closure. The
fresh archive logs above reach actual rendered assertions without mapper
export errors.
No full suite, live rig, or 1440/393 browser shot was run in this frontend
worker lane; those remain with the orchestrator and the rig lanes. This lane
holds for SHIP.
