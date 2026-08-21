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

## Honest boundary

The walkthrough provider was a labelled deterministic in-process simulation,
not a claimed production model. HS-141-04 attaches no context and creates no
local outcome or external effect. HS-141-05 adds explicit visible context;
HS-141-07 and HS-141-08 own typed local and real-tool outcomes.
