# Phase 46 — Documentation Excellence & the 10-Second Hook — FINAL SUMMARY

**Status: CLOSED ✅ (6/6).** Opened + closed 2026-06-06/07.
Branch `phase-46-documentation-lift`. Author: Claude (Opus 4.8 session).

## Goal — and was it met?

> Make the documentation worthy of the product: a README that hooks in ten
> seconds and sells what's genuinely cool (honestly), and a docs set that is
> accurate, consistent, visually rich, and easy to navigate — every shipped
> capability discoverable, the graphics kept, the bloat gone.

**Met.** The README went spec-sheet → product pitch (205 → 157 lines) with a
10-second hook + a cool-facts strip and a real app screenshot, every pixellab
graphic kept; the 13 guides now clear a shared voice + page skeleton with a
uniform `## See also` footer; the index is a journey map; a truth audit fixed the
factual drift and pins the headline plugin count + image refs with guards; and a
coverage matrix proves no shipped capability is undiscoverable. Docs-only — the
suite stayed green throughout (2364 → 2365 with the new guards).

## Before → after (the headline)

| | Before | After |
|---|---|---|
| **README** | 205 lines, spec-sheet: one-liner then a feature list; no hook; the best stories buried; pre-release stated twice; a 52-line plugin table; 22 lines of AIPI prose; **zero real app screenshots** | **157 lines**: a hook ("Hold a key. Speak. It types — anywhere. 100% local. And it learns you.") + a "Why it's different" cool-facts strip; journal/replay above the fold; the plugin table + AIPI prose → teasers; pre-release once; **a real journal screenshot**; every graphic kept |
| **Docs index** | a 64-line **flat list** | a **journey map** — Start here · Dictate · Meet · Extend · Operate & Trust, each entry a one-line value prop |
| **Guides (×13)** | written across 13 phases; different tone/structure; inconsistent or missing footers ("Related Docs" / "Where to go next" / none) | a shared lede + skeleton + a **uniform `## See also` footer (13/13)**, governed by `DOCS_STYLE.md` |
| **Visuals** | pixellab illustration only | illustration **kept** + **real UI screenshots** (welcome wizard, dictation journal, `/history` artifact cards) from a repeatable capture script |
| **Accuracy** | drifted (presence env-var-only; a phantom config key; a missing connector kind; a self-contradicting protocol example) | a truth audit + 4 fixes; guards pin the plugin count + image refs |

Evidence: `evidence-story-{01..06}.md`; the README before/after is the 205→157
line delta + the section-structure diff in `evidence-story-02.md`; the screenshots
live under `docs/assets/screenshots/`.

## Per-story recap

- **HS-46-01 — Doc truth audit & drift fix.** `docs/internal/DOC_AUDIT_2026-06.md`:
  a canonical-facts yardstick + a per-doc verdict for all 18 live docs. 4 drift
  findings fixed across 6 docs (presence is config-backed not env-var-only; a
  phantom `intel_cloud_timeout_seconds` removed; the missing `pipeline` connector
  kind; the stale device-protocol pushbacks). New plugin-count guard. The
  "verified-correct" anchors note prevents a future regression.
- **HS-46-02 — The README, reimagined.** 205 → 152 lines; hook + cool-facts strip;
  every graphic kept; repetition cut; pre-release once; honest per the audit.
- **HS-46-03 — Voice & structure + elevated index.** `DOCS_STYLE.md`; a uniform
  `## See also` footer across all 13 docs; `docs/README.md` rebuilt as a journey
  map.
- **HS-46-04 — Visual lift.** `scripts/screenshot_docs.py` (real server + seeded
  state, no mic/LLM) → welcome / journal / history PNGs, embedded in the README +
  Getting Started + Meeting Mode; a new image-ref guard. (Took the README to 157.)
- **HS-46-05 — Coverage & discoverability.** A feature → doc matrix (16
  capabilities, no orphans); the index now names actuators; the user-reported
  **"project KB" confusion** fixed in the docs — and a follow-up commit corrected
  *that* fix (the KB is `.holdspeak/project.yaml`, not `.hs/`). The product/UX
  legibility spun out as **Phase 47**.
- **HS-46-06 — Closeout.** This summary; invariants re-asserted; PR to `main`.

## Invariants — re-asserted

- **Graphics kept.** All 6 pixellab assets remain in the README; screenshots are
  additive. ✓
- **Honest, not hype.** Pre-release stated once; "100% local by default" framed as
  the local-first invariant; the "14 plugins" headline pinned to the registry;
  every cool fact cross-checked against the audit. ✓
- **Docs only.** No source/behavior change. The only code is *test* guards
  (plugin-count, image-ref) + a *script* (`screenshot_docs.py`); the app is
  untouched. ✓
- **Reproducible visuals.** Screenshots come from a committed capture script. ✓
- **Grounded.** Every claim checked against live code — and when a fix itself
  drifted (project KB), it was corrected against the code, not left. ✓

## Verification

- Full suite: `uv run pytest -q --ignore=tests/e2e/test_metal.py` → **2365 passed,
  17 skipped** (exit 0).
- Guards: `uv run pytest -q -k "doc_drift or link"` → **8 passed** (doc-drift +
  dangling-link + plugin-count + image-ref).
- `(cd web && npm run build)` ✓; **0** `holdspeak/static/_built/` tracked.

## Handoff

- **Phase 47 — Project Knowledge: Legible & Inviting** is scaffolded (6 stories) —
  the product/UX side of the project-KB legibility the docs pass could only
  partly fix. Lead exhibit: the `/dictation` two-tab overload ("Project KB" =
  `project.yaml` kb map; "Project Context" = `.hs/`). HS-47-01 (concept & naming)
  is the entry point.
- The audit doc + `DOCS_STYLE.md` are the durable map + style floor for the next
  doc pass; refresh the screenshots with `uv run python scripts/screenshot_docs.py`
  after UI changes.
- **Lesson recorded:** "project KB" ≠ `.hs/`. KB = `.holdspeak/project.yaml` `kb:`
  map (deterministic `kb-enricher`); context = `.hs/` (optional `project-rewriter`
  LLM). Don't re-conflate.
