# HS-13-06 - Pipeline manifest + dependency-graph runner

- **Project:** holdspeak
- **Phase:** 13
- **Status:** backlog
- **Depends on:** HS-13-01
- **Unblocks:** packs that consume other packs' output (HS-13-07)
- **Owner:** unassigned

## Problem

Today every pack stands alone — it reads activity records and
writes annotations or candidates. There's no way to say "this
pack consumes the gh + jira annotation streams and produces a
synthesized briefing annotation." Without that, the substrate
can't grow into anything bigger than parallel CLI shims.

## Scope

- **In:**
  - New `kind: pipeline` value in `KNOWN_KINDS`.
  - `ConnectorManifest` gains a `consumes:
    tuple[ConsumesEntry, ...]` field. `ConsumesEntry` declares
    `(pack_id, output_kind)` where `output_kind ∈
    {"annotations", "candidates", "records"}`.
  - `validate_manifest` enforces: `kind=pipeline` must declare
    `consumes` (non-empty); other kinds must NOT declare
    `consumes` (it stays empty); every consumed `pack_id` must
    exist in the registry; cycles are rejected.
  - New `PipelineRunner` in `holdspeak/connector_runtime.py`:
    given a target pipeline pack, computes the topological
    order of its dependency graph, runs each upstream pack
    first (or skips if it ran recently — see "freshness"
    below), then runs the pipeline pack with the upstream
    output collected as input.
  - "Freshness" rule: a pack's output is fresh if it ran
    successfully within the last `pipeline_freshness_seconds`
    (manifest-declared, default 300) — saves needless re-runs.
  - Runner records every step in `connector_runs` (HS-13-05)
    with the pipeline id as `triggered_by`.
  - Permission gate enforces: a pipeline pack inherits
    `read:activity_annotations` / `read:activity_meeting_candidates`
    permissions for the kinds it `consumes`.
- **Out:**
  - Streaming pipelines (output as it's produced). Pipelines
    run to completion, then hand off.
  - Conditional / branching pipelines. The graph is a DAG of
    runs, not a programmable language.

## Acceptance Criteria

- [ ] `kind: pipeline` validates with a non-empty `consumes`.
- [ ] `consumes` referencing an unknown pack id rejects with
  `unknown_consumed_pack`.
- [ ] Cycle detection rejects `pipeline_a → pipeline_b →
  pipeline_a` with `pipeline_cycle`.
- [ ] `PipelineRunner.plan(target)` returns the topological
  order including the target last.
- [ ] `PipelineRunner.run(target, db)` executes each step in
  order, records `connector_runs` rows, and returns a
  `PipelineRunResult` with per-step status.
- [ ] Freshness skip: a recently-successful upstream is not
  re-run (verified by counting `connector_runs` rows before
  and after).
- [ ] Permission gate denies a pipeline pack consuming
  `annotations` if its manifest lacks
  `read:activity_annotations`.

## Test Plan

- Unit: validate_manifest cycle / unknown / kind-misuse
  cases.
- Unit: PipelineRunner plan + run with a fake upstream
  + downstream pair.
- Unit: freshness skip behaviour (mock now() to test the
  300-second window).
- Integration: end-to-end pipeline against the real
  fixture-driven gh + jira packs (no live network).

## Notes

The runner is deliberately simple: topological sort + sequential
execution + freshness. No retries, no parallelism, no
back-pressure. If a step fails the pipeline aborts and reports
the failed step. Phase 14+ can complicate this if real
workflows demand it.
