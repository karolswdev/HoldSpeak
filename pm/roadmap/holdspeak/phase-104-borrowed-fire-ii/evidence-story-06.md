# Evidence - HS-104-06

- **Story:** HS-104-06 - Docs — the gate and the watch at the entry points
- **Status:** done
- **Date:** 2026-07-26

## What shipped (entry points, truth-audited)

- **USER_GUIDE.md** — "The Gate: A Steered Agent Asks First" beside the
  steering material, its FIRST paragraph the honest fail-closed trade
  (armed + hub down = denied call, off is the default); the two-step
  opt-in exactly as the CLI behaves (`install` prints, never edits
  `~/.claude`; arm + allow; status/doctor read it back — spot-run in
  this session); the shade card, deny-reason ride-back, expiry, and
  restart honesty. "Pull Request Receipts" inside the Mission
  Control/delivery material: registering, the Refresh verb + opt-in
  cadence, the observed-at rule, and the attribution labels with the
  council's caution in plain words. "Session Receipts": the three
  tiers and why a missing cost line is a feature.
- **SECURITY.md** — trust boundary 7 (chokepoint, record-never-
  authority, fail-closed, restart invalidation, redaction, the
  install rule, the Stop-leg's numbers-only report) and the PR
  receipts egress row (what leaves, when, under which gate; fetch as
  a separate explicit act).
- **ARCHITECTURE.md** — "The tool-call gate" section with the
  hook → hub → shade → decision → hook mermaid (render guard green,
  2 passed) plus the collector's PR pass paragraph.
- **README.md** — one POSITIONING-voiced Desk paragraph leading with
  off-by-default, plus a "Where to go next" row anchored to the new
  guide section.
- The first capture below (exit 4) is the honest record of a wrong
  test path in the capture command; the final capture is the green
  guard run. The doc-drift guard also caught "the Phase-87 pattern"
  leaking roadmap vocabulary into SECURITY.md — reworded in
  product-tense before the flip.

## Proof

### Captured run — 2026-07-26T19:19:24Z

- **Command:** `uv run pytest -q tests/unit/test_doc_drift_guard.py tests/e2e/test_mermaid_renders.py tests/unit/test_product_language_guard.py`
- **Cwd:** .
- **Exit code:** 4
- **Index-tree:** f09a3c05a152a07f43263f979f6465c2b4550949

```text
ERROR: file or directory not found: tests/unit/test_product_language_guard.py


no tests ran in 0.00s
```

### Captured run — 2026-07-26T19:19:33Z

- **Command:** `uv run pytest -q tests/unit/test_doc_drift_guard.py tests/e2e/test_mermaid_renders.py tests/unit/test_vocabulary_guard.py`
- **Cwd:** .
- **Exit code:** 4
- **Index-tree:** f09a3c05a152a07f43263f979f6465c2b4550949

```text
ERROR: file or directory not found: tests/unit/test_vocabulary_guard.py


no tests ran in 0.00s
```

### Captured run — 2026-07-26T19:19:41Z

- **Command:** `uv run pytest -q tests/unit/test_doc_drift_guard.py tests/e2e/test_mermaid_renders.py tests/unit/test_product_language.py tests/unit/test_web_vocabulary_guard.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** f09a3c05a152a07f43263f979f6465c2b4550949

```text
................................                                         [100%]
32 passed in 32.47s
```
