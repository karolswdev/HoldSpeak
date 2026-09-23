# The live pass — lane brief (PHILO-2-04 Muad'Dib · PHILO-2-05 Astra)

Both brains receive this text verbatim. The contract is `docs/internal/philo/briefs/graph-audit-brief.md` §§0–5, 7, 8, 9. Story 01 delivered the rig (`scripts/graph_walk.py` v1.1.0), the atlas (`docs/internal/philo/graph/atlas.json`: 73 cases, 71 applicable), the schema and the calibration. This page fixes the deliverables, the order, the runtime laws and the sealing law.

## Deliverables (this lane's files only)

1. `docs/internal/philo/graph/observations/<brain>/<run_id>/` — one directory per run, written by the rig (`observation.json` + shots), never overwritten, never edited by hand.
2. `docs/internal/philo/graph/live-<brain>.json` — validates with `uv run --extra dev python scripts/philo_graph_validate.py`: `cases` = the atlas cases run (verbatim), `observations` = every run's observation (one row per run/case/brain/viewport, provenance intact), `findings` = ranked by owner cost with bin, `claim_reviews` for the Phase 1 records the observed jobs touch.
3. `docs/internal/philo/graph/live-<brain>.md` — the §9 report: PASS: live; SOURCE; CONTRACT (brief, schema, atlas sha256, rig version); RUNTIME (frontend build, hub, db path, clock, engine mode per run); JOBS: for each of J1–J11 the expected result, the observed result, pass/fail/blocked/unexercised with the run ids; COVERAGE (discovered 73; applicable 71; exercised; unexercised with reasons); FINDINGS; ORPHANS; UNKNOWN.

## Order and bounds

- One case per rig invocation: `HOME=$(mktemp -d) PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright uv run --extra dev python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas.json --case <id> --brain <brain> --viewport <1440|393> --engine <real|replayed|none> --out docs/internal/philo/graph/observations/<brain>`. Serial; never two hubs from one lane at once; slow polls; the machine kills long jobs, so one run at a time and read each result before the next.
- The eleven jobs' cases FIRST (J1 → J11 in the story-01 table order), every face case at 1440 AND 393, protocol cases once. Then `beyond.*`.
- **J6 with the real LAN engine:** `--engine real`; the SET_ENGINE chain fills the address `http://192.168.1.43:8080/v1` (the atlas step's `value` is the placeholder for the LAN address — substitute that exact address); record the engine identity the hub reports and the summary text verbatim in the observation; report TECHNICAL completion and OWNER usefulness separately — a generated text's existence is not a verdict that it is useful. Use synthetic meeting material that makes summary errors inspectable (the fixture WAV's transcript is what it is; say so).
- Every other engine-dependent case: `--engine replayed` with the boundary step's recorded reply, labelled; if no recorded reply exists for a case, record it BLOCKED with the missing artefact named. Never `--engine none` for a case whose predicate needs a summary.
- A block is a result: record it with its exact reason (selector not present, precondition not met, unresolved placeholder, mechanism missing). A block caused by the ATLAS (a wrong selector, a wrong recipe) is a `tooling-debt` finding naming the case and field; do not edit the atlas or the rig in this lane.
- The rig refuses a HOME under /Users/karol/.local and never opens the microphone; do not work around either.
- Time-dependent cases (`next_day`, `week_boundary`, `continuity_horizon`) are unreachable by the atlas's own word; do not manufacture them.

## Sealing

Work in your own worktree (`../wt-philo-2-04` Muad'Dib, `../wt-philo-2-05` Astra), branch `audit/philo-2-0N-live-<brain>`. Commit through the gate (`dw evidence capture` of the validator + your report's JOBS block; `dw contract new --story PHILO-2-0N`) or hold for SHIP if you are a worker. **Do not read the other brain's `live-*`, `static-*` or observations, its branch or its worktree until all four pass outputs are sealed.** The static graphs on main are sealed outputs: do not read `static-astra.*` (Muad'Dib) or `static-muaddib.*` (Astra).

## Laws

Isolated HOME per run; never the owner's data dir, keychain or microphone; never a git verb that moves or cleans a tree; stage by explicit path; `set -o pipefail`; restore nothing with blanket loops (the rig writes only to its `--out`). Report with the validator's output for your JSON, the JOBS block, the run count, and UNKNOWN. Never inflate; "blocked" and "unexercised" are good answers.
