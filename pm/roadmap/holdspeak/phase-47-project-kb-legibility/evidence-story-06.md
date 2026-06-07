# Evidence — HS-47-06: Closeout (before/after + dogfood + PR)

**Date:** 2026-06-07. **Author:** Claude (Opus 4.8 session).
**Branch:** `phase-47-project-kb-legibility`.

## What shipped

The verified exit: before/after captures, a repeatable screenshot script, a green
dogfood, a green suite, and the final summary. The phase is CLOSED and the PR to
`main` is opened (merged on green CI).

### Before / after

Real screenshots under `docs/assets/screenshots/`:

- `project-knowledge-before-facts.png` / `project-knowledge-before-context.png` —
  the old surfaces: a bare lede over a key/value grid and a `.hs/` textarea, with
  no explainer, no inviting empty state, no guided flow, and no discovery hint.
- `project-knowledge-facts.png` / `project-knowledge-context.png` — the new
  surfaces: a what/why/worked-example explainer plus a teaching empty state with a
  one-click starter.
- `project-knowledge-setup.png` — the guided "Set up project knowledge" panel: the
  template starter and the copiable, repo-aware coding-agent prompt.
- `project-knowledge-nudge.png` — the ambient discovery nudge above the tabs.

The before set was captured by temporarily checking out `main`'s
`dictation.astro` + `dictation-app.js`, building, and screenshotting, then
restoring the branch versions and rebuilding. The after-state is regenerable via
`scripts/screenshot_project_knowledge.py` (boots a real server, no mic/LLM).

### Dogfood (green)

`scripts/dogfood_project_knowledge.py` re-run at closeout:

```
6. dry-run utterance: 'help me refactor the payments module'
   stages: ['intent-router', 'kb-enricher']
   final text: 'help me refactor the payments module\n\nProject stack: Rails 7 + Postgres 16'
PASS: the fact 'Rails 7 + Postgres 16' reached dictation output with zero file editing.
```

## Tests run

- Dogfood: `scripts/dogfood_project_knowledge.py` → PASS.
- Full-suite gate: `uv run pytest -q --ignore=tests/e2e/test_metal.py`
  → **2372 passed, 17 skipped** (exit 0).
- `(cd web && npm run build)` clean; **0** `_built/` tracked; the branch bundle
  carries the Phase-47 markup after restoring from the before-capture.

## Acceptance criteria

- [x] Before/after captured + a green dogfood transcript.
- [x] Full suite green; `npm run build` ✓; 0 `_built/` tracked.
- [x] `final-summary.md` written; phase CLOSED; status docs + roadmap updated; PR
      to `main` opened (merged when CI green).
