# Evidence — HSM-22-03 — Web authors a linear graph

**Status:** done (2026-07-04), on `holdspeak-mobile/hsm-22-03-web-linear-builder`.

## 1. The pieces

- **The type fix:** `web/src/lib/primitives.ts` `graphJson?: string` → the
  `WorkflowGraphJson` OBJECT wire type (the drift the survey confirmed; no other
  consumer existed, so the fix is clean).
- **The builder (`web/src/desk/graph.ts`):** `buildLinearGraph()` lowers an ordered
  step list to the EXACT canonical wire (Swift tagged-union kinds incl.
  `{"extract":{"_0":…}}` and the snake_cased `keep_if`; `exec_edges` chaining named
  exec-outs; empty `data_edges`) — the same shape the HSM-22-01 golden fixtures pin.
  `parseLinearGraph()` is the honest inverse: control flow, fan-out, cycles, unknown
  kinds, and **iPad provenance** (`failure_policy`/`runs_on` — which this editor
  cannot re-emit and must never silently strip) all return null → read-only
  ("Graphed on iPad"), never rewritten to less than they were.
- **Authoring on the desk:** `+ Workflow` in the chrome creates a workflow born with
  a real one-step graph (never the empty `{}` the run route must refuse); the
  in-world editor (no modal, the desk grammar) gains the linear-step builder — the
  palette (Summarize / Decisions / Action items / Rewrite / Keep if / LLM prompt),
  per-step params, reorder, remove — every change debounce-PUT through the real
  `/api/workflows/{id}`.
- **The dropped `warning` reaches the reader:** `runCapability` now carries the
  hub's honest refusal (`warning`) and the pull-out renders it amber above the
  output; the pull-out's workflow Steps section renders the real graph's steps
  (`parseLinearGraph` labels) instead of falling back to the prompt.

## 2. The locks

- **vitest (`graph.test.ts`, 9 tests):** the emitted wire deep-equals the canonical
  shape (kinds, edges, `_0`, `keep_if`), the builder↔parser round-trip, every
  refusal class (control flow / fan-out / cycle / junk / provenance), the
  explicit-null-tolerance (the Swift-absent = hub-None rule), and every palette
  entry. Desk suite **18 passed**.
- **pytest (`test_run_workflow_web_authored_graph_runs`):** the web builder's exact
  emission POSTed and RUN through the real route — steps `summarize → keep_if` in
  order, `keep_if` kept the risk line, no warning. Suite **34 passed**.

## 3. The live proof (real Chromium, real scratch hub)

Playwright drove the REAL desk at a scratch `MeetingWebServer`: clicked
`+ Workflow`, added Decisions + Keep if in the in-world editor
([`hsm-22-03-web-workflow-editor.png`](./screenshots/hsm-22-03-web-workflow-editor.png)
— the editor beside the NEW-badged object, palette + step rows visible). Then:

- `GET /api/workflows` returned the persisted graph:
  `entry → source → summarize → extract → keep_if → out`, the exec chain intact.
- The hub's own `linearize()` accepted it: `linearizable: True`, the six-node plan.

Web-authored, persisted, hub-runnable — the second producer speaks the one wire.

## Suites

- `npm run test:desk` — **18 passed** (+9 graph tests).
- `uv run pytest -q tests/unit/test_web_routes_primitives.py` — **34 passed** (+1).
- `cd web && npm run build` — 17 pages, green.
- `uv run pytest tests/e2e/test_route_preflight.py` — **2 passed** (real Chromium;
  the new desk code loads clean).

## Honest boundaries

- Linear only, by design: control flow stays graphed on the iPad's Blueprint canvas;
  the web presents such graphs read-only.
- A fresh scratch hub redirects to the first-run welcome wizard — proof runs mark
  the `FIRST_DICTATION_SUCCESS` milestone first (recorded for the next proof).
- The run `warning` render is unit-locked (hub emission + store passthrough); the
  live warning render on glass rides 22-04's cross-surface run.
