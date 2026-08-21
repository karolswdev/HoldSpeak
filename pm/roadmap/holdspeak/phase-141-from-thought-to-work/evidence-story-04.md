# Evidence — HS-141-04 One useful question

**Result:** done; owner accepted the live loop, and final technical and
owner-glass counsel **RATIFY**.

## Shipped contract

- One explicit owner action freezes the current working/context cursors and
  produces at most one receipt-gated question or synthesis. It never starts an
  autonomous chat or a second model turn.
- Stop durably suppresses first and then reaches the exact owning runtime when
  physical cancellation is available. Late output cannot become a review or
  mutate the Note.
- Answer, Accept, and Reject are caller-idempotent owner commands. Answer and
  Accept write immediately under aggregate/working CAS; Reject changes no Note.
- Durable host leases, epochs, heartbeats, and cancellation signals keep web and
  MCP execution ownership truthful across concurrent processes and crashes.
  Recovery is reconcile-only and never redispatches abandoned work.
- `RefinementApplicationService` is the shared command boundary. HTTP and six
  closed-schema `thought.*` MCP tools expose the same cursors, receipts, named
  conflicts, and public continuity without leaking Ask/kernel identifiers or
  source material.

## Owner glass

The [story-04 record](./assets/story-04/README.md) documents fresh isolated
HOME/database walks at 1440×900 and 393×900. The browser created and developed
the Note through ordinary controls, then traversed the real HTTP, coordinator,
kernel, receipt, projection, reconciliation, and Note-write path. Only the
in-process provider engine and temporary exact `this_machine` model artifact
were deterministic. There was no fetch interception, result seeding, or direct
review call.

Both widths proved the ready, live Stop, question, Answer-applied, and late
suppression states with zero console/page errors and zero horizontal overflow.
The owner said the result was starting to please them and explicitly approved
continuing. The overlapping **Good enough / Keep refining / Continue refining**
language is recorded for HS-141-09's subtraction pass rather than churned here.

## Local verification

Run by the orchestrator on the assembled tree:

```text
.venv/bin/pytest -q \
  tests/unit/test_refinement_thought_service.py \
  tests/unit/test_refinement_coordinator.py \
  tests/integration/test_refinement_coordinator_kernel.py \
  tests/unit/test_web_routes_thoughts.py \
  tests/unit/test_web_routes_ask.py \
  tests/unit/test_mcp_thoughts.py \
  tests/unit/test_api_surface.py \
  tests/unit/test_db.py

151 passed in 28.62s

uv run pytest -q tests/e2e/test_hs14104_refinement_glass.py --timeout=120
2 passed in 21.06s

npm run test:web -- --run src/desk/pullouts/NotePullout.test.tsx
18 passed
```

The production Vite build and `git diff --check` passed. The build emitted only
the existing dynamic-import and chunk-size warnings. GitHub Actions was not
watched or used as a gate.

## Choose-your-AI recovery evidence

The model-unavailable recovery door was simplified after the owner rejected
the topology-first **Runs on** setup. Settings now opens with the owner task
**Choose your AI**, leads with **This device**, adds three strong OpenRouter
Qwen presets, then offers **Choose AI for each job**. Reusable endpoints and
placement detail stay available under **AI connections**; background assistance
and tuning remain under **Advanced**.

The screen uses the existing target and secret APIs. It discovers local model
choices through `GET /api/setup/runtime-options`, offers only executable GGUF
choices for local Thought interviews, and uses the safe `GET /api/models`
readiness projection for **Check local AI**. That check sends no prompt and
invokes no model. MLX remains available for writing/dictation and is never
misrepresented as a working Thought target.

The new `thoughts.inference_target_id` pointer closes the previous execution
gap: Workbench projection, admission, transaction-bound readiness recheck, and
physical execution all resolve the same selected target. A blank pointer still
means the built-in on-device GGUF target. The three OpenRouter cards create
ordinary OpenAI-compatible targets for `qwen/qwen3-8b`,
`qwen/qwen3.5-35b-a3b`, and `qwen/qwen3.8-27b`; custom providers remain fully
editable under **AI connections**.

Fresh isolated-HOME browser evidence at 1440×900 and 393×900 proved the guided
hierarchy, preset creation/selection through public HTTP, owner-only key
custody, the per-job Thought pointer, initially closed custom connections, 44px
narrow-screen targets, zero horizontal overflow, and zero page or console
errors:

```text
npx vitest run src/pages/cores/__tests__/settingsModels.test.tsx --maxWorkers=2
25 passed

npm run build
passed (existing dynamic-import and chunk-size warnings only)

uv run pytest -q tests/e2e/test_hs141_models_setup_glass.py
2 passed in 7.67s
```

See the final [desktop](./assets/story-04/hs-141-models-setup-1440.png) and
[narrow](./assets/story-04/hs-141-models-setup-393.png) setup captures, plus the
selected-preset [desktop](./assets/story-04/hs-141-models-openrouter-presets-1440.png)
and [narrow](./assets/story-04/hs-141-models-openrouter-presets-393.png) proof.

## Honest boundary

The walkthrough provider was a labelled deterministic in-process simulation,
not a claimed production model. HS-141-04 attaches no context and creates no
local outcome or external effect. HS-141-05 adds explicit visible context;
HS-141-07 and HS-141-08 own typed local and real-tool outcomes.

### Captured run — 2026-08-21T02:05:20Z

- **Command:** `uv run pytest -q tests/e2e/test_hs141_models_setup_glass.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 5d90f27ee1cd38aacb7f8dd752ac7b830998638a

```text
..                                                                       [100%]
2 passed in 5.68s
```

### Captured run — 2026-08-21T02:34:44Z

- **Command:** `uv run pytest -q tests/e2e/test_hs141_models_setup_glass.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** fd28cbe9b2199a8cee6dcaa1a8b53aa70b176d7f

```text
uv run pytest -q tests/unit/test_one_dial.py tests/unit/test_inference_targets.py \
  tests/unit/test_config.py tests/unit/test_thought_workbench_backend.py \
  tests/unit/test_refinement_coordinator.py tests/unit/test_refinement_thought_service.py \
  tests/unit/test_web_routes_thoughts.py tests/unit/test_mcp_thoughts.py \
  tests/unit/test_connector_settings.py tests/unit/test_mcp_phase133_settings.py
216 passed in 18.25s

npm exec vitest -- run src/pages/cores/__tests__/settingsModels.test.tsx
25 passed

uv run pytest -q tests/e2e/test_hs141_models_setup_glass.py
2 passed in 7.67s

npm run build
passed (existing dynamic-import and chunk-size warnings only)
```
