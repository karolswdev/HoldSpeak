# Evidence — HS-46-05: Coverage & discoverability (feature → doc matrix)

**Date:** 2026-06-07. **Author:** Claude (Opus 4.8 session).
**Branch:** `phase-46-documentation-lift`.

## What shipped

A **feature → doc coverage matrix** that proves no shipped capability is
undiscoverable and nothing is overstated, plus the small gaps it surfaced —
closed.

### The matrix

Added to `docs/internal/DOC_AUDIT_2026-06.md` (§"Feature → doc coverage matrix"):
**16 user-facing capabilities** mapped to their **guide home → README/highlights
hook → index journey**. Verdict: **no orphan features** (every capability has a
guide home + an index link) and **no orphan docs** (every `docs/*.md` is linked
from the journey-map index — verified by a filename sweep against `docs/README.md`,
which printed nothing). The honest line drawn: the README strip carries the seven
top differentiators; depth features (cockpit/memory, wizard, settings) live in
their guide and are reached from the index rather than padded into the strip —
discoverable without overstating.

### Gaps closed

1. **Actuators were discoverable only by opening the guide.** The index's Plugin
   Authoring entry now names the **actuator** propose → approve → execute flow.
2. **The "project KB" was under-explained (user-reported).** The term +
   `kb-enricher` appeared in the Intelligent Typing guide ~150 lines before the
   `.hs/` folder that *is* the KB was shown; the README never grounded it. Fixed
   (docs side): a **plain definition on first use** in the guide (a `.hs/` folder of
   Markdown files: `instructions`/`context`/`workflows`/`targets` + `ignore`), a
   **gloss on `kb-enricher`** ("the project-KB stage"), a link to §5, and a
   **glossary entry** in `docs/internal/DOCS_STYLE.md`. The deeper **product/UX
   legibility** is explicitly out of scope for a docs-only phase and is teed up as
   **Phase 47 — "Project KB: legible & inviting"** (scaffolded this session).

### Stale content

Swept the user-facing docs for "coming soon / not yet implemented / TODO / TBD /
placeholder / under construction / stub" — **no stale residue** (the two
`PLUGIN_AUTHORING` hits are legitimate: a checklist item and "test against a stub
or injected connector", both current).

## Honesty (cross-checked vs HS-46-01)

Every hook in the matrix was checked against the canonical-facts table: counts,
defaults, and enablement match live code; coverage did not reintroduce any
overstatement. The project-KB definition matches the `.hs/` contract in the guide
and the `kb-enricher` stage in the pipeline.

## Tests run

- Story test plan: `uv run pytest -q -k "doc_drift or link"` → **8 passed, 1
  skipped** (no new dangling links; the new `#5-create-project-context` anchor
  matches its heading; the actuator/index + glossary edits resolve).
- Full suite: `uv run pytest -q --ignore=tests/e2e/test_metal.py` → **2365 passed,
  17 skipped** (exit 0).

## Acceptance criteria

- [x] A feature → doc matrix exists and shows **no** shipped user-facing capability
      without documentation + a link.
- [x] Journal/replay, actuators, presence, the wizard, persistent memory, and the
      cockpit each have a hook + a guide home + an index link (mapped in the matrix).
- [x] No orphan docs (every `docs/*.md` linked from the index) and no orphan
      features; stale content swept (none found).
- [x] Every "cool fact" surfaced is true (cross-checked vs HS-46-01) — coverage
      didn't reintroduce overstatement.
