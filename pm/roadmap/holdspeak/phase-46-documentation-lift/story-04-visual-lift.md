# HS-46-04 — Visual lift: real screenshots across the guides

- **Project:** holdspeak
- **Phase:** 46
- **Status:** done
- **Evidence:** [evidence-story-04.md](./evidence-story-04.md)
- **Depends on:** HS-46-01
- **Unblocks:** HS-46-06
- **Owner:** unassigned

## Problem
People love the graphics — but the pixellab art is *illustration*, not the app.
The README and guides contain **zero real screenshots of the actual product**,
despite a genuinely good-looking journal, `/history`, dictation cockpit, presence
HUD, and welcome wizard. Showing the real UI is the cheapest credibility +
delight win available, and the user explicitly asked for it.

## Scope
- **In:**
  - A **repeatable capture script** (`scripts/screenshot_docs.py`, mirroring the
    existing `scripts/screenshot_*.py` / Playwright pattern) that boots a real
    server with seeded state and writes a known set of PNGs to
    **`docs/assets/screenshots/`** — so visuals are reproducible, not hand-pasted.
  - **Real UI screenshots** of the marquee surfaces: the dictation **Journal**
    (reuse Phase-45's), the **moment-of-truth** + **replay** diff, the meeting
    **`/history`** artifacts, the **dictation cockpit**, the **welcome wizard**,
    and the **desktop presence** HUD (the latter may reuse the Phase-41 captures).
  - **Embed** them where they earn their place: the README highlights/feature
    showcase, Getting Started, the Intelligent Typing guide, the Meeting Mode
    guide. Each with descriptive alt text (accessibility) + a one-line caption.
  - A clean `(cd web && npm run build)` before capture so the screenshots reflect
    current UI; **0** `holdspeak/static/_built/` tracked.
- **Out:** new pixellab generation (reuse existing illustration); the README
  prose (HS-46-02); voice (HS-46-03). Visuals + the capture script.

## Acceptance criteria
- [ ] `scripts/screenshot_docs.py` captures the marquee surfaces into
      `docs/assets/screenshots/` from a real server, reproducibly (no mic / no
      LAN-LLM dependency beyond what dry-run/seeded state needs).
- [ ] Real UI screenshots appear in the README + at least Getting Started +
      Intelligent Typing + Meeting Mode, each with descriptive alt text + caption.
- [ ] The existing pixellab graphics are still present (additive, not replaced).
- [ ] Dangling-link/image-ref guard green (every image path resolves);
      `npm run build` ✓; **0** `_built/` tracked.

## Test plan
- Capture: `uv run python scripts/screenshot_docs.py` → PNGs written; eyeball
  each for quality (premium bar — no broken/empty/ugly states).
- Unit: `uv run pytest -q -k "doc_drift or link"` (image refs resolve).
- Manual: render each guide; confirm screenshots load and read well at GitHub
  width.

## Notes / open questions
- Reuse the Phase-45/41 screenshot scripts + seeded-state helpers; the journal
  screenshots already exist under the phase-45 evidence — promote/refresh rather
  than re-invent.
- Watch for the Astro **scoped-CSS-on-runtime-DOM** trap when seeding UI for
  shots (the journal fix) — capture against the built bundle, verify the surface
  actually rendered (a class in the bundle ≠ it applied).
