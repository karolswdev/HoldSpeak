# Evidence — HS-71-07: Docs + the nav decision

**Date:** 2026-07-01
**Verdict:** done. The web Desk is documented, and the one product question the
build raised is resolved: **the Desk is celebrated on Home and kept in Studio**
(owner's call), so the four-door nav Phase 70 won stays intact.

## The nav decision (owner-chosen)

Options put to the owner: keep in Studio only / promote to a top-level door /
celebrate on Home + keep in Studio. The owner chose **celebrate on Home, keep in
Studio**. Implemented:

- **`web/src/pages/index.astro`** — Home gains a prominent, accent-edged **"The
  Desk · Your primitives as a spatial world →"** entry (with a diorama glyph),
  beside the existing quiet Studio link (which now correctly points at the
  `/studio` index). The two modes stay the front door; the Desk is one click
  away. `screenshots/07-home-desk-entry.png`.
- No nav change: `/desk` stays a Studio-tier surface.

## Docs (dash-free, canonical, under the voice guard)

- **`docs/WEB_DESK.md`** — a short guide: what the world is, the objects per
  kind, arrange-by-drag + Tidy, directories as shelves (file + dive), open an
  object, where it lives, and Qlippy (off by default). Linked from the docs
  index under "Extend: build on it".
- **`docs/internal/POSITIONING.md`** — the web-surface section gains a **Desk**
  paragraph: the spatial expression of the Primitive Framework, matching the
  iPad DeskOS and reusing the same `/api/*` data, in Studio and celebrated on
  Home.

## Proof

- **`screenshots/07-home-desk-entry.png`** — Home with the celebrated Desk entry
  (accent) + the quiet Studio link; the four-door nav unchanged.
- Home Desk entry `href = /desk` (verified).
- **Tests:** the voice/doc guard (`test_doc_drift_guard.py`) + route pre-flight
  **17 passed** (dash-zero + canonical-name checks over my new docs; zero page
  errors); full suite **3045 passed, 37 skipped**; build green.
