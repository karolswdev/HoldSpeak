# Evidence — HSM-22-04 — The cross-surface proof + docs

**Status:** done (2026-07-04), on `holdspeak-mobile/hsm-22-04-cross-surface-run`.
The on-glass rider ([`HSM-22-WALK-RIDER.md`](./HSM-22-WALK-RIDER.md), G1+G2, ~3 min)
is staged and rides the couch session as the phase gate — the build deliverables
below are complete and live-proven.

## 1. `runWorkflow` joins the iPad hub path

- **`HTTPDesktopClient+Workflows.swift`** (own extension file, the conflict rule):
  `runWorkflow(id:input:)` → `POST api/workflows/{id}/run`, decoding the graph run's
  envelope — `HubWorkflowRunResult` with OBJECT steps
  (`node_id`/`kind`/`failure_policy`/`runs_on`/`status`), the honest `warning`, and
  the run-born `artifact_id`. A dedicated type because `HubRunResult`'s string steps
  cannot carry a graph trail — and renamed `Hub…` after the flattened App target
  exposed a collision with the ENGINE's `WorkflowRunResult` that SPM module
  boundaries had hidden (`swift test` green, app build red — the gen-copy build is
  the arbiter for App-visible names).
- `WorkflowRunClientTests` (3): the real route shape decodes (object steps +
  provenance fields), the warning-refusal envelope, the non-2xx throw.
- **The desk:** `PendingHubRun.Kind` gains `.workflow`; dropping a card on a
  workflow WITH a graph aboard now offers the runs-on sheet (a prompt-only saved
  Ask keeps the old no-sheet local path, byte-identical); the hub arm prints the
  card with the run's REAL `artifact_id` (the 18-07 duplicate-on-sync lesson),
  `Workflow · your desktop` lens, cloud egress, and the `warning` (when present)
  riding the card body, never dropped. `docs/api-surface.json` regenerated in the
  same commit (the standing HS-72-02 rule).

## 2. The sync fixture upgrade + the crown test

- The 23-04 placeholder graph in
  `test_web_routes_sync_primitives.py` (bare-string kinds, flat `edges` — it only
  byte-survived) upgraded to a REAL canonical graph: sync survival and runnability
  are the same wire now.
- **`test_ipad_synced_graph_workflow_runs_on_the_hub`** (integration, the real ASGI
  app): the SWIFT-ENCODED golden fixture rides `/api/sync/push` as a workflow's
  `graph_json`, then `/api/workflows/{id}/run` executes it — node order
  `llm → extract → keep_if`, the iPad-authored `failure_policy`/`runs_on` surfaced
  per step, `keep_if` filtering the model output, the run-born artifact minted with
  workflow lineage, no warning. Authored, synced, run: one test, the whole thesis.

## 3. The live proof — REAL METAL (.43 intel)

Scratch hub configured with `intel_provider: cloud` on the **real .43 endpoint**
(Qwythos-9B, the grammar-free vision server; probed live). The connected sim's desk,
paired and synced, ran the **iPad-authored 22-01 workflow** (`Canvas · Decisions`,
the graph saved from the shipping canvas two stories ago) on the hub via the
`HS_DESK_WF_HUB_RUN` affordance — the exact `runOnHub` path the sheet's
"your desktop" row fires:

- [`hsm-22-04-ipad-hub-run.png`](./screenshots/hsm-22-04-ipad-hub-run.png) — the
  printed card: **Canvas · Decisions**, "fresh from your desktop",
  **Cloud · your desktop** badge, provenance chips `Standup → Canvas · Decisions`,
  body **"Decision: keep linear runs on the hub."** — the real model ran the real
  graph over the seeded standup text and extracted the actual decision.
- The hub's `/api/sync/pull` then carried ONE run-born artifact:
  `origin: "run"`, `sources: [{source_type: "workflow", source_ref: "be54d003-…"}]`
  — the lineage naming the iPad-authored workflow. The loop is audited, not
  narrated.
- A first run against a default-config hub surfaced the honest 502 sheet
  ("no model loaded") — the error path proven live too, incidentally.

## 4. Docs + the rider

- `docs/ARCHITECTURE.md` meeting-pipeline diagram gains the graph-bridge node
  (authored on the iPad canvas or the web desk, synced as graph_json; linear subset
  runs, control flow refused with a warning) — mermaid render guard green.
- [`HSM-22-WALK-RIDER.md`](./HSM-22-WALK-RIDER.md) staged: G1 (author on the iPad →
  Save → hub run on glass) + G2 (web author + run), ~3 minutes riding the couch
  session. PASS×2 closes the phase on glass.

## Suites

- Full `swift test` — **445 tests, 8 skipped, 0 failures** (+3 run-client).
- `uv run pytest -q tests/unit/test_web_routes_sync_primitives.py
  tests/integration/test_primitive_framework_sync.py` — **24 passed** (+1 crown).
- Drift guard + mermaid render guard — **20 passed**.
- Meeting-capture sim build — **BUILD SUCCEEDED**; `test_api_surface` 5/5 after the
  regen.

## Honest boundaries

- The iPad still runs a workflow's PROMPT on-device (its engine does not execute
  synced graphs yet); the runs-on sheet says where the graph itself runs — the hub.
  On-device graph execution is the v2 canvas's future, not claimed.
- The desk card carries output + warning; the per-node steps trail is read on the
  web/history surfaces (deliberate: a printed card is a result, not a debugger).
