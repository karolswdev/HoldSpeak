# Evidence — HS-66-01: The system map + the diagram render guard

**Date:** 2026-06-13
**Verdict:** done. `docs/ARCHITECTURE.md` exists with an orienting overview
and a traced component diagram; a render guard keeps every Mermaid block
rendering, proven both ways; the docs index points at it.

## What shipped

- **`docs/ARCHITECTURE.md`**: the runtime view (not the module-structure
  view the two internal ARCHITECTURE_* docs cover, which it links to). An
  overview ("one process, two modes on shared building blocks"), the
  top-level component diagram, and product-tense section intros for the
  dictation pipeline, the meeting pipeline, and the trust boundary (HS-66-02
  and HS-66-03 fill those with diagrams).
- **The component diagram** traced against the SHIPPED code: the audio
  entry trio (`hotkey.py`, `wake_word.py`, `device_audio_ws.py`) into the
  voice session, the transcriber, the dictation/meeting split, the plugin
  host + router, the actuator executor → gated connectors, the web server,
  presence, and the SQLite repositories. Module names verified current
  post-decomposition (the `runtime/*` mixins, `meeting_session/` the
  package). Rendered to PNG and reviewed by eye: legible, the "approved
  egress" and "optional rewrite / intel" edges read correctly.
- **`tests/e2e/test_mermaid_renders.py`**: extracts every fenced ```mermaid
  block across README + docs/*.md + docs/internal/*.md and renders each via
  mmdc (`npx @mermaid-js/mermaid-cli`); fails with the file + block index +
  the renderer's error on any parse/render failure. Skips cleanly when no
  renderer/browser is present (CI has none), like the route pre-flight. A
  canary test fails if the docs ever lose all diagrams (no vacuous pass).
- **The docs index** gained an "Understand the system" entry pointing at
  the architecture map.

## Proof

- The render guard proven BOTH ways: green on the shipped doc (2 passed);
  a deliberately broken block made it fail with `docs/ARCHITECTURE.md
  block #1: <mermaid parse error>`, then restored and green again.
- mmdc availability + behavior confirmed directly: a good block renders
  to a 12 KB SVG (exit 0), a malformed block exits 1 with a parse error.
- Voice guard green (13 passed) after rewording HS-ID placeholders into
  product-tense section intros — the guard correctly caught `HS-66-02`
  leaking roadmap vocabulary into a user-facing doc.
- Full suite: **2779 passed, 17 skipped** (+2 = the guard's two tests).
