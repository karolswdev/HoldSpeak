# Evidence — HS-33-05 (Visual assets via the pixellab MCP)

**Shipped:** 2026-06-03. HoldSpeak now has a brand mark + a GitHub social/OG card,
generated on the **Signal** palette (dark-first, orange `#FF6B35`) and harmonized
with the existing pixel-art spot-art set. Provenance recorded in
`docs/assets/pixellab/README.md`.

## Audit (existing set)

Reviewed the five existing assets (`hold-to-talk-microphone`,
`meeting-intelligence-notebook`, `project-aware-typing`, `aipi-lite-companion`,
`operator-working-loop.gif`). They're coherent clean pixel-art on transparent
backgrounds and read well on the dark Signal canvas — **no regeneration needed**.
The new mark was generated in the same clean-pixel-art / orange-accent register so
the set stays unified; the three workflow icons are reused in the social card.

## New assets

- **`docs/assets/pixellab/holdspeak-mark.png`** (128×128, transparent) — the brand
  mark: a glowing orange held/pressed keyboard key with three rising soundwave
  arcs (the "hold, speak, release" gesture). PixelLab object
  `52e0db41-4789-45b3-9136-1ee3e4e7838d` (side view, single-color outline).
- **`docs/assets/pixellab/social-card.png`** (1280×640) — the GitHub social/OG
  preview: Signal dark canvas, an orange accent baseline, the mark upscaled crisp
  (nearest-neighbour), the **HoldSpeak** wordmark + an orange tagline ("Local-first
  voice input & meeting intelligence") + a mono sub-line ("hold a key · speak ·
  release"), and the three pillar icons. *PixelLab makes ≤400px sprites, not wide
  banners* — so the card is **composed** from the mark + spot-art via a committed,
  reproducible script.
- **`docs/assets/pixellab/holdspeak-icon-256.png`** (256×256) — square padded app
  icon derived from the mark.
- **`web/public/apple-touch-icon.png`** (180×180) — refreshed to the mark on the
  Signal canvas (the site already linked an apple-touch-icon).
- **`docs/assets/pixellab/compose_og_card.py`** — the reproducible compositor for
  the three derived assets (reads the mark + workflow icons, applies the Signal
  palette + auto-fitting type; uses SF for the wordmark + Menlo for the mono lines,
  the closest installed faces to the Signal stack).

## Wire-in

- **README header** — the mark is now the centered logo under the `# HoldSpeak`
  title (`width=120`).
- **Workflow map** — unchanged (already wired; the three icons now also appear in
  the social card).
- **GitHub social preview** — `social-card.png` is committed. **Manual step
  (recorded here + in the provenance README):** set it under the repo's
  *Settings → Social preview* — that's a GitHub UI action, not a repo file.
- Web bundle rebuilt so the refreshed apple-touch-icon lands in `_built/`.

## Tests ran

- Visual (no automated test): inspected `holdspeak-mark.png`, `social-card.png`,
  and `holdspeak-icon-256.png` — on-brand, text fits the card, pixels crisp.
- `uv run pytest -q tests/unit/test_doc_drift_guard.py` → **3 passed** (the doc
  link-check now also covers the updated provenance README).
- `uv run pytest -q --ignore=tests/e2e/test_metal.py` → **1954 passed, 15 skipped**.
- All README + provenance relative links resolve.

## Done-when

- [x] A coherent prime-time asset set exists (logo/mark + social/OG card),
      harmonized with "Signal."
- [x] Wired into README/docs; favicon/social placed where the site/repo use them
      (apple-touch-icon refreshed; social card committed + manual repo-settings
      step noted).
- [x] Every new asset's pixellab object ID + prompt recorded in
      `docs/assets/pixellab/README.md` (derived assets note their compositor).

## Decisions / deviations

- **Social card is composed, not direct PixelLab output** — PixelLab's max canvas
  is 400px and it makes sprites, not 1280×640 banners. The card is built from the
  PixelLab mark + the existing spot-art on the Signal palette via the committed
  `compose_og_card.py`, keeping it fully reproducible.
- **No README hero banner / no workflow-trio regen** — both were "optional / only
  if the audit flags drift" (story §scope); the audit found no drift, so credits
  went to the highest-impact pieces (mark + social card).
- **Fonts:** Space Grotesk / Inter / JetBrains Mono aren't installed; used SF
  (wordmark) + Menlo (mono) as the closest available faces to the Signal stack.
