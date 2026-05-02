# HS-13-06 evidence — Pipeline manifest + dependency-graph runner

## What shipped

- `holdspeak/connector_sdk.py`
  - `KNOWN_KINDS` gained `"pipeline"`.
  - `KNOWN_PERMISSIONS` gained `read:activity_annotations`
    and `read:activity_meeting_candidates`.
  - New `PIPELINE_OUTPUT_KINDS = {"records", "annotations",
    "candidates"}` and the `_OUTPUT_KIND_TO_READ_PERMISSION`
    map enforced by the validator.
  - New `ConsumesEntry(pack_id, output_kind)` frozen
    dataclass; `ConnectorManifest.consumes:
    tuple[ConsumesEntry, ...]` and `pipeline_freshness_seconds:
    int = 300` fields.
  - `validate_manifest` enforces: `kind=pipeline` → non-empty
    consumes + matching `read:*` permissions; `kind != pipeline`
    → consumes must be empty; per-entry: `pack_id` regex,
    `output_kind` whitelist, no duplicates.
- `holdspeak/connector_pack_loader.py`
  - `build_registry` runs `_validate_pipeline_graph` after
    discovery: rejects pipeline packs whose `consumes`
    references an unknown id (`unknown_consumed_pack`), and
    rejects every pack participating in a dependency cycle
    (`pipeline_cycle`). Self-loops trip the same code path.
  - Rejected packs are removed from the registry; their errors
    show up in `discovery_errors()` (and therefore in
    `holdspeak doctor --connectors`).
- `holdspeak/connector_runtime.py`
  - `PipelineRunner(db, *, registry=None, now=None)` — `plan(target_id)`
    returns the topological order with the target last;
    `run(target_id) -> PipelineRunResult` walks the order and
    invokes each step.
  - `PipelineStepResult.status` is one of `"ran" | "skipped_fresh"
    | "failed" | "missing_runner"`. Step failure aborts the
    pipeline and is recorded in `connector_runs` with
    `succeeded=false` so HS-13-05's run-history surface
    reflects it.
  - Freshness rule: an upstream pack is skipped when its most
    recent `connector_runs` row succeeded within
    `pipeline_freshness_seconds`. The `now` injection point
    keeps the test deterministic.
  - The pipeline target itself never short-circuits on
    freshness — invoking the pipeline is the whole point of
    the call.
- `holdspeak/connector_packs/{github_cli,jira_cli,calendar_activity}.py`
  - Each first-party producer pack now exposes a uniform
    `run(db, *, limit=None)` callable. gh + jira wrap their
    existing CLI run functions; calendar persists the previews
    that were previously preview-only and records its own
    `connector_runs` row at completion. Firefox's pack
    intentionally does not expose `run` — it's purely event-
    driven, with its run row recorded by the ingestion endpoint
    (HS-13-05).

## Acceptance criteria

- [x] `kind: pipeline` validates with a non-empty `consumes`.
  Verified: `test_pipeline_manifest_round_trips`,
  `test_pipeline_requires_non_empty_consumes`.
- [x] `consumes` referencing an unknown pack id rejects with
  `unknown_consumed_pack`. Verified:
  `test_pipeline_with_unknown_consumes_id_is_rejected`.
- [x] Cycle detection rejects `pipeline_a → pipeline_b →
  pipeline_a` with `pipeline_cycle`. Verified:
  `test_pipeline_cycle_is_rejected` (two-node cycle),
  `test_self_referential_pipeline_is_rejected_as_cycle`
  (single-node), and `test_acyclic_pipeline_chain_survives`
  proves the validator does not over-reject.
- [x] `PipelineRunner.plan(target)` returns the topological
  order including the target last. Verified:
  `test_plan_returns_topological_order_with_target_last`.
  Edge cases: `test_plan_unknown_id_raises`,
  `test_plan_non_pipeline_raises`.
- [x] `PipelineRunner.run(target, db)` executes each step in
  order, records `connector_runs` rows, returns a
  `PipelineRunResult` with per-step status. Verified:
  `test_run_executes_each_step_and_records_runs`. The
  "step records its own row" contract is documented in
  `evidence-story-05.md` and called out in the test docstring.
- [x] Freshness skip: a recently-successful upstream is not
  re-run. Verified: `test_run_skips_fresh_upstream` seeds a
  successful row at `now-5s`, runs with a 300-second window,
  asserts the upstream's `run` is *not* invoked, and counts
  `connector_runs` rows before/after.
  `test_run_does_not_skip_target_on_freshness` proves the
  target itself is exempt.
- [x] Permission gate denies a pipeline pack consuming
  `annotations` if its manifest lacks
  `read:activity_annotations`. Verified at the manifest layer
  via `test_pipeline_must_declare_matching_read_permissions`
  (`pipeline_missing_read_permission`). The cross-field check
  fires before the manifest is ever instantiated, so a
  consumer that forgot the read permission cannot be loaded
  to begin with.

Bonus assertion not in the AC but worth covering:
`test_first_party_packs_expose_run_callables` proves the
gh / jira / calendar packs all carry a `run(db)` entry point
and firefox's pack does not.

## Tests ran

```
$ uv run pytest -q tests/unit/test_pipeline_runner.py
20 passed in 0.25s
```

Full sweep:

```
$ uv run pytest -q --ignore=tests/e2e/test_metal.py
1386 passed, 13 skipped in 32.28s
```

The 13 pre-existing skips (mock meeting WAV, llama-cpp / Qwen
GGUF) are unrelated. +20 over HS-13-05 reflects the new
pipeline-runner test module.

## Why "missing_runner" is its own status

The runner has three terminal states for an upstream step:

  - `skipped_fresh` — recent success, no work to do.
  - `ran` — the pack's `run(db)` succeeded.
  - `failed` — the pack's `run(db)` raised.

But there's a fourth case that isn't really any of those: an
upstream pack with no recent successful run AND no `run`
callable at all. That happens for firefox_ext (event-driven
ingester — no `run`) and for arbitrary user packs that only
ship a manifest. Conflating it with `failed` would mislead
operators reading run history. `missing_runner` makes the
distinction explicit so the user sees the actionable signal
("this pack has no automatic run path; trigger it some other
way or remove it from the consumes list").

## Why pipelines record on failure but not on success

The runner trusts the pack's own `run(db)` to record the
success row — that's the contract HS-13-05 already enforced
for gh / jira / calendar / firefox-ingest. Recording an extra
row per step from the pipeline runner would double-count
every successful run and skew the freshness window for the
*next* invocation.

For *failure*, the pack's exception path may never reach its
own record_connector_run call (the runner catches the
exception). The runner records the failure row itself so the
operator's run-history surface still reflects the bad step.

## Greenfield

Manifest extensions are additive (default empty / 300). The
permission set grew by two read permissions; existing first-
party manifests don't need either, so no manifest changes
beyond the new `run` callables on the producer packs. No
schema changes (run rows already exist as of HS-13-05).
