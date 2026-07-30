# Evidence - HS-109-07

- **Story:** HS-109-07 - Docs — memory at the entry points
- **Status:** done
- **Date:** 2026-07-29

## Proof

### Captured run — 2026-07-30T00:53:28Z

- **Command:** `uv run pytest -q tests/unit/test_doc_drift_guard.py tests/unit/test_web_vocabulary_guard.py tests/unit/test_product_copy.py tests/unit/test_mermaid_architecture_plugin.py tests/integration/test_mermaid_architecture_pipeline.py tests/e2e/test_mermaid_renders.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 1c705740832f689eed4823bc393004beaa638340

```text
.......................................................                  [100%]
55 passed in 29.91s
```

## What shipped

- **USER_GUIDE** — the memory loop in owner vocabulary (record →
  decisions with moments → accept/supersede → promote → search → ask
  with citations), reported/anchored/absence stated plainly,
  retention semantics where the user meets them (deletion severs
  provenance; the record survives marked; "years later" is a
  retrieval claim over what you kept), and the Process window's
  contract including what `Unknown` honestly means.
- **ARCHITECTURE** — the decision projection as DERIVED (plugins
  unchanged; the one record_artifact chokepoint), the memory indexes,
  cited grounding with matched/overflow, the process window as an
  Article XI clause-5 read consumer.
- **README** — one why-led paragraph in the pitch's voice.
- **SECURITY drift reconciled** — the stale "pending the owner's
  ruling" sentence on N10-N12 is gone; the remainder now reads five
  mixed + nine bypass + one dormant (= the ledger's 15 debt); the
  cooperating-code narrowing is byte-comparable in strength (only the
  pending-ruling sentence changed — diff in the session record).
- **BACKLOG candidate Y reconciled** (applied by the orchestrator —
  roadmap files): 23 of 38 closed, 15 debt rows, the three
  owner-ruled questions recorded as resolved.

Every user-facing claim was truth-audited to shipped file:line by the
implementation pass (26-row table in the session record); the guard
family above ran green (55 passed): doc drift, web vocabulary,
product copy, and the mermaid architecture chain (rendered).
