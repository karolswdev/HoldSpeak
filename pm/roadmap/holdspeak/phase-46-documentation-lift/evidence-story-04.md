# Evidence — HS-46-04: Visual lift — real screenshots across the guides

**Date:** 2026-06-07. **Author:** Claude (Opus 4.8 session).
**Branch:** `phase-46-documentation-lift`.

## What shipped

A **repeatable capture script** and **three real UI screenshots** of the actual
app, embedded where they earn their place — the README, Getting Started, and
Meeting Mode. The pixellab illustration stays; screenshots are additive.

### The capture script

`scripts/screenshot_docs.py` — boots one real `MeetingWebServer` over a temp DB
seeded with realistic state (a dictation journal + a meeting with three
synthesized artifacts), drives the marquee surfaces with Playwright, and writes a
known set of PNGs to `docs/assets/screenshots/`:

- `welcome.png` — the first-run `/welcome` wizard.
- `journal.png` — the dictation Journal (said → typed → routed → latency).
- `history.png` — a saved meeting's elevated artifact cards at `/history`.

**Reproducible + no hardware:** every surface is driven from seeded state — **no
microphone, no LLM endpoint**. The seed makes the DB the global singleton so
`/history` (which calls `get_database()`) sees it; the journal repo is injected
into the server. The artifact `structured_json` matches the `/history` renderers
(requirements `{requirements:[{text,type}]}`, decisions
`{decisions:[{decision,rationale}],open_questions:[...]}`, risk_register
`{risks:[{risk,impact,likelihood,mitigation,owner}]}`) so the cards render rich,
not empty. Run:

```bash
(cd web && npm run build)
uv run python scripts/screenshot_docs.py            # all three
uv run python scripts/screenshot_docs.py welcome    # one surface
```

### Where they're embedded (each with descriptive alt text + a caption)

- **README** → `journal.png` in the **See it learn** section (the real product
  doing the "it learns you" thing — said → typed → routed → latency, one row
  corrected). Below the fold; the hook + cool-facts strip are untouched.
- **Getting Started** → `welcome.png` in the first-run wizard section ("Hold a
  key. Speak. Watch it type." — fresh clone → verified first dictation).
- **Meeting Mode** → `history.png` under **Meeting Intelligence** (the elevated
  artifact cards: a risk-register table, decisions, typed requirements).
- **Intelligent Typing** already carries **9** real screenshots (cockpit ×2,
  presence ×4, journal ×3) from Phases 40/41/45 under `docs/assets/{cockpit,
  journal,presence}/` — left in place; `screenshot_docs.py` is the consolidated
  repeatable entry going forward.

### A new image-ref guard

`test_doc_drift_guard.py::test_all_embedded_image_refs_resolve` — scans the README
*and* the live docs for **both** markdown `![](…)` and HTML `<img src="…">` local
image refs and asserts every path resolves. The pre-existing dangling-link guard
only saw markdown `[](…)` links in `docs/` — it missed the `<img>` tags (used for
width/centering) and the root README entirely. This closes that gap, so a
renamed/missing asset can't ship a broken image.

## Quality (the premium bar)

Each PNG was captured against the freshly built bundle and eyeballed — no broken,
empty, or ugly states. The `/history` cards render the full risk table (impact /
likelihood level-pills, mitigation, owner), the decisions + open-questions list,
and the typed requirement pills; the journal shows real routing + latency strips +
a corrected row; the welcome wizard shows the step rail + the local-trust footer.
Watched for the Astro scoped-CSS-on-runtime-DOM trap — verified the surfaces
actually rendered, not just that classes exist in the bundle.

## Tests run

- Capture: `uv run python scripts/screenshot_docs.py` → 3 PNGs written, all
  eyeballed.
- Story test plan: `uv run pytest -q -k "doc_drift or link"` → **8 passed, 1
  skipped** (the new image-ref guard included; every embedded image resolves).
- Full suite: `uv run pytest -q --ignore=tests/e2e/test_metal.py` → **2365 passed,
  17 skipped** (exit 0; +1 vs. prior — the new image-ref guard).
- `(cd web && npm run build)` ✓; **0** `holdspeak/static/_built/` files tracked.

## Acceptance criteria

- [x] `scripts/screenshot_docs.py` captures the marquee surfaces into
      `docs/assets/screenshots/` from a real server, reproducibly (no mic / no
      LAN-LLM — seeded state + dry-run/journal data).
- [x] Real UI screenshots appear in the README + Getting Started + Intelligent
      Typing + Meeting Mode, each with descriptive alt text + a caption.
- [x] The existing pixellab graphics are still present (additive, not replaced — 6
      assets in the README).
- [x] Image-ref guard green (every image path resolves); `npm run build` ✓; **0**
      `_built/` tracked.
