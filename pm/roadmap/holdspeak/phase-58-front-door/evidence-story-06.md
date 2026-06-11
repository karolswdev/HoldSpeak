# Evidence — HS-58-06: Closeout: fresh-eyes pass + final-summary + PR

**Date:** 2026-06-11
**Branch:** `phase-58-front-door`

The full narrative lives in [`final-summary.md`](./final-summary.md) (this
same commit); this file records the story-level proof.

## 1. The fresh-eyes render pass

- **GitHub's own renderer**, fetched via
  `gh api "repos/karolswdev/HoldSpeak/readme?ref=phase-58-front-door"`
  with the HTML accept header: 35,744 rendered bytes, **11 images**, and
  every key marker present ("One local copilot, two modes", "The two
  modes", "How it compares (as of mid-2026)", "superwhisper", "Talon",
  "14 built-in plugins").
- **Absolute asset URLs**: all 7 raw.githubusercontent images + the
  install script return HTTP 200 (curl-checked one by one).
- Relative links and embedded images are covered by the standing locks
  (`test_no_live_doc_has_a_dangling_relative_link`,
  `test_all_embedded_image_refs_resolve`), green.

## 2. Before / after metrics

- Em/en dashes in user-facing **prose**: ~170+ → **1** (the allowlisted
  verbatim UI quote; measured by the same fenced-block-aware walker the
  guard uses). Remaining non-prose dashes live only inside example-code
  blocks (PLUGIN_AUTHORING 43, DEVICE_PROTOCOL 2), exempt by the canon.
- Comparison content: none → a named, dated, both-ways section.
- README feature story: stopped ~Phase 48 → covers the live tree.
- AI-vocab and banned-name hits on the corpus: **0** (guard-verified).

## 3. Gates

```
$ uv run pytest -q tests/unit/test_doc_drift_guard.py
13 passed
$ uv run pytest -q --ignore=tests/e2e/test_metal.py
2645 passed, 17 skipped
```

BACKLOG: **Q → shipped (CLOSED 6/6)**. Project README: phase CLOSED +
index row. PR to `main` merged on green CI (recorded in the project
README's operating cadence).
