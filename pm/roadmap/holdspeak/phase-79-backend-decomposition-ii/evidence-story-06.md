# Evidence — HS-79-06 — closeout

**Status:** done (2026-07-03). The full ledger lives in
[`final-summary.md`](./final-summary.md); this file records the closeout bars as run:

- **Full suite** (`uv run pytest -q --ignore=tests/e2e/test_metal.py`):
  **3,113 passed / 37 skipped**. One earlier run showed a single failure in
  `tests/integration/test_dictation_journal_replay.py::test_replay_after_target_correction_changes_routing`
  that passed in isolation (5/5) and on the full re-run — recorded as a flake
  candidate, not hidden.
- **Web build:** `cd web && npm run build` — 17 pages, green (the moved route
  modules feed the pages).
- **Swift package:** `swift test` — **425 passed** (the iPad consumes the moved
  routes; paths byte-identical, proven by the manifest).
- **Manifest stability:** `uv run python scripts/gen_api_surface.py` from the repo
  root produced a byte-identical `docs/api-surface.json` + `API_SURFACE.md`
  (empty `git diff --stat`).
