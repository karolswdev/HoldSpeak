# Evidence — HSM-22-02 — The hub honors the graph

**Status:** done. Built in **Equilibrium Wave 1 (2026-06-27)** ("Graph node
policy/target", the wave log in `EQUILIBRIUM.md`), before this phase opened; recorded
here on phase open (2026-07-04) with a fresh green run.

## The shipped mechanism (`holdspeak/web/routes/workflow_graph.py`)

- `GraphNode` (`:99-112`) carries per-node `failure_policy` + `runs_on`, parsed from
  the wire (`:168-174`) — the exact fields the audit said the linearizer dropped.
- `linearize()` (`:205-283`) accepts the Swift tagged-union Codable shape — including
  the `{"extract":{"_0":"action_items"}}` single-unlabeled-associated-value form
  (`_extract_artifact_type`, `:289-303`, the god-review fix) — and REFUSES
  branch/for-each/while/sequence (`_CONTROL_FLOW_KINDS`), fan-out, joins, cycles, and
  disconnected chains with a stated reason (`LinearPlan.linearizable=False`).
- The runner applies the faithful subset: `skip` / `fallbackOnDevice` carry the input
  through and continue; `retryThenQueue` and unset fail fast (`on_node_error`,
  `:381-402`).
- The run route (`holdspeak/web/routes/primitives/workflows.py:97`,
  `POST /api/workflows/{id}/run`) returns `output`, `provider`, per-step
  `node_id`/`kind`/`failure_policy`/`runs_on`/`status`, `sources`, `artifact_id`, and
  a `warning` when a graph was refused; its docstring (`:128-136`) documents what the
  hub does NOT enforce (`runs_on` carried, not pinned to a provider; no real retry
  queue) — the honest-omission clause this story demanded.

## The lock

- `tests/unit/test_workflow_graph.py` — tagged-union decode, every refusal class, the
  `failure_policy`/`runs_on` carry (`:170-180`), the `extract` Codable shape
  (`:150-157`).
- `tests/unit/test_web_routes_primitives.py` — `_linear_graph()` (`:455`) is the
  Swift-shape conformance dict; `test_run_workflow_linear_graph_runs_in_order`
  (`:497`), the branch-refusal warning (`:536`), the 400 (`:555`).

## Fresh run on phase open (2026-07-04)

```
uv run pytest -q tests/unit/test_workflow_graph.py tests/unit/test_web_routes_primitives.py
50 passed
```

## Honest boundaries

- The conformance dict is hand-written in the Swift shape; real Swift-ENCODER bytes
  reach `linearize()` only with 22-01's golden fixture (deliberately that story's
  lock, not claimed here).
- Control flow is refused, not emulated; the omissions are documented, not fixed —
  that is the design call, unchanged.
