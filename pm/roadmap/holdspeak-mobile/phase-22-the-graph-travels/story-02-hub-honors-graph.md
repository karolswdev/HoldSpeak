# HSM-22-02 — The hub honors the graph

- **Project:** holdspeak-mobile
- **Phase:** 22
- **Status:** done (pre-paid, Equilibrium Wave 1, 2026-06-27) — see
  [`evidence-story-02.md`](./evidence-story-02.md). The linearizer runs the faithful
  subset, applies `failure_policy`, carries `runs_on`, and refuses control flow with
  an honest `warning`.
- **Depends on:** the Swift Blueprint wire shape (the tagged-union Codable form).
- **Unblocks:** 22-01's conformance target; 22-04's cross-surface run.
- **Owner:** unassigned

## Problem

The audit filed the hub side as footnotes: `linearize` parsed one straight pipeline
and dropped per-node `failure_policy`/`runs_on` entirely (`GraphNode` held only
id/kind/payload), and nothing documented what the hub refused.

## The design (as shipped)

`holdspeak/web/routes/workflow_graph.py`: `GraphNode` carries `failure_policy` +
`runs_on`; `linearize()` accepts the Swift tagged-union shape (incl. the
`{"extract":{"_0":…}}` Codable form) and refuses branch/for-each/while/sequence,
fan-out, joins, cycles, and disconnected chains with a stated reason. The runner
applies the faithful subset (skip / fallback-on-device continue; retry-then-queue and
unset fail fast) and surfaces per-step `failure_policy`/`runs_on`/`status` in the run
route's `steps`, with a `warning` when a graph was refused. The route docstring
documents what is NOT enforced (runs_on is carried, not pinned; no real retry queue).

## Scope

- **In (shipped):** the linearizer + policy carry/apply + honest refusals + run-route
  steps/warning + docstring omissions.
- **Out:** executing control flow on the hub (deliberately refused, not emulated);
  Swift-encoder conformance bytes (22-01's golden pin).

## Test plan

- `uv run pytest -q tests/unit/test_workflow_graph.py tests/unit/test_web_routes_primitives.py`
  — green (re-run on phase open, 50 passed).
