# Evidence — HS-56-06: Docs: Qlippy

**Date:** 2026-06-11
**Branch:** `phase-56-qlippy`

## 1. What shipped

**`docs/INTELLIGENT_TYPING_GUIDE.md`** — the Desktop Presence section (the
Phase-41/43 home, extended rather than fragmented) gains **"Qlippy, the
mascot (optional)"** right after the focus-invariant subsection:

- the double opt-in (`presence.enabled` AND `presence.mascot`, both off by
  default; the Settings sub-toggle named; presence-off removes everything in
  one click),
- the two levels (the ambient no-buttons-no-sound dock vs. the
  one-at-a-time, always-dismissible card),
- **exactly which moments produce a card** (decision needed / result of an
  approved action / learned-from-you with the honest-count rule stated /
  meeting left open items),
- **the never-acts guarantee**, verbatim-checkable ("never acts on his
  own"; Approve sends the identical audited request the dashboard sends;
  nothing runs and nothing leaves the machine before approval; dismissing
  is always safe),
- **the three privacy answers** with their verbatim markers ("Data used:",
  "If you approve, this goes to", "Your controls:"), plus the local-only
  statement for non-decision cards,
- the native HUD behavior (pointer clicks only while a card shows,
  click-through otherwise, keyboard focus never moves),
- motion/accessibility (screen-reader announce, hover pauses auto-dismiss,
  reduced-motion fades).

Two screenshots shipped to `docs/assets/presence/`:
`qlippy-decision-card.png` (the web decision card, from the live HS-56-03
dogfood) and `qlippy-native-overlay.png` (the real Linux overlay over a real
desktop, from the live HS-56-05 run). **`docs/README.md`** (the docs index)
links the new section from the Desktop Presence entry.

## 2. The guards

- **Zero em/en dashes in the new text** (grep over the new section and the
  index entry: no `—`/`–` hits).
- **Roadmap-vocab guard**: green over the extended guide (product-tense
  throughout; no phase/story vocabulary).
- **Humanizer pass**: the section was written against the checklist (no
  filler openers, no rule-of-three padding, bold lead-ins match the guide's
  existing house style, plain copulas).
- **New lock**: `test_qlippy_doc_states_the_guarantees_verbatim` (appended
  to `tests/unit/test_doc_drift_guard.py`) pins the never-acts phrase and
  the three privacy markers in the guide AND asserts the same three markers
  still exist in `qlippy-events.js` — the doc and the cards cannot drift
  apart silently.

## 3. Tests + suite

```
$ uv run pytest -q tests/ -k "doc"
75 passed, 2 skipped
$ uv run pytest -q tests/unit/test_doc_drift_guard.py
9 passed
$ uv run pytest -q --ignore=tests/e2e/test_metal.py
2602 passed, 17 skipped
```

(2601 → 2602: the new doc lock.)
