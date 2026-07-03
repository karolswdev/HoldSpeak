# Evidence — HS-79-05 — the docs story

**Status:** done (2026-07-03).

- `docs/internal/ARCHITECTURE_BACKEND_RUNTIME.md` retitled for both phases and
  extended: the three Phase-79 packages with their module tables, the guard
  additions (init ≤ 90; modules ≤ 600; settings.py named 800), and the watch-item
  ledger updated (`db/core.py` in; the meetings-route item recorded as resolved by
  Phase 72).
- `docs/ARCHITECTURE.md`: the two Mermaid nodes naming `web/routes/primitives.py`
  now name the package path; the render guard proves both diagrams still draw.
- `docs/API_SURFACE.md` + the manifest were regenerated in 02/03 (per-submodule
  route attribution — richer than the old single-module rows).

Proven: voice/drift/api-surface/density guards 32 passed; the Mermaid render
guard 2 passed.
