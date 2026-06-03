# Phase 33 — Documentation & Open-Source Readiness — Final Summary

**Status:** CLOSED ✅ — 6/6 stories shipped. **Closed:** 2026-06-03.

Phase 33 took HoldSpeak from "mature code with a rough outward surface" to
**adoptable**: the model story is de-prescribed and current, the package is
legally + metadata-complete, `docs/` is navigable, the README is OSS-grade and
honest about being pre-release, and the project has a coherent brand mark + social
card. It builds directly on HS-32-06 (which made docs *true*); this phase makes the
project *presentable*.

## What shipped

| Story | Outcome |
|---|---|
| **HS-33-01** | De-prescribed model framing — runtime errors, doctor/guidance, and the web dictation-runtime docs page now say "any GGUF/MLX chat model / OpenAI-compatible endpoint"; example/default models bumped to the **Qwen3.5** family (dictation `llama_cpp`/`mlx`/`openai_compatible`; intel realtime + `DEFAULT_INTEL_MODEL_PATH` → Qwen3.5-9B); new **`docs/MODELS.md`** bring-your-own contract; intel `cloud` clarified as "any OpenAI-compatible endpoint." |
| **HS-33-02** | **Apache-2.0 `LICENSE`** + complete `pyproject` `[project]` metadata (SPDX license + license-files, authors, 11 keywords, 13 classifiers, `[project.urls]`). `uv build` verified clean (`Metadata-Version: 2.4`, `License-Expression`). |
| **HS-33-03** | `docs/` reorg — 13 internal/historical docs `git mv`'d to **`docs/internal/`**, 11 user-facing guides kept in `docs/`, a new **`docs/README.md`** index; every *live* inbound link repointed; a doc link-check added. Frozen history (`docs/evidence/`, `pm/` phase folders) kept verbatim. |
| **HS-33-04** | OSS-grade README pass — badges, an honest **pre-release** banner, a clean-clone quickstart, docs/license/contributing links, `MIT`→Apache-2.0 fix; new **`CHANGELOG.md`** + minimal **`CONTRIBUTING.md`**. |
| **HS-33-05** | Brand identity via the **pixellab MCP** — a **brand mark** (held-key + rising soundwaves, orange `#FF6B35`) and a composed **1280×640 social/OG card** + app/touch icons (PixelLab makes ≤400px sprites, so the card is built from the mark + spot-art on the Signal palette via a committed `compose_og_card.py`). Mark wired into the README header; provenance recorded. |
| **HS-33-06** | Closeout — link-check sweep, drift-guard + doc-truth re-verify, OSS checklist, this summary. |

## Decisions of record

- **License = Apache-2.0** (user, 2026-06-03) — permissive + explicit patent grant.
- **GGUF stays** the default local format — only model *names* + *prescription*
  were refreshed (names are framed as suggestions + a `MODELS.md` contract so they
  can rot gracefully).
- **`docs/internal/` layout** — a single folder for plans + a `docs/README.md`
  index (the deferred-decision default).
- **Frozen history kept verbatim** — only *live* references were repointed in the
  reorg; `docs/evidence/` snapshots and `pm/` phase folders were untouched (the
  principle the drift guard already encodes).
- **Social card is composed, not raw PixelLab output** — PixelLab tops out at
  400px sprites; the card is reproducibly composed via `compose_og_card.py`.
- **Pre-release positioning** made consistent — README banner, `CHANGELOG`
  ("everything Unreleased; the `0.2.x` marker is not a published tag"), and the
  roadmap's own project-metadata line all now say the same thing.

## State at close

- **Suite:** green — `uv run pytest -q --ignore=tests/e2e/test_metal.py` →
  **1954 passed, 15 skipped**. The doc drift-guard + new link-check are in that run.
- **New OSS surface:** `LICENSE`, `CHANGELOG.md`, `CONTRIBUTING.md`,
  `docs/README.md`, `docs/MODELS.md`, `docs/internal/`, the brand mark + social
  card; `pyproject` metadata complete.
- **Branch:** the phase is the local branch `phase-33/hs-33-01-model-framing`
  (6 story commits) — **unpushed; open a PR to `main`.**

## Manual follow-ups (not repo files)

- **Set the GitHub social preview** — upload `docs/assets/pixellab/social-card.png`
  under the repo's *Settings → Social preview* (a GitHub UI action).
- **Cutting an actual release** (tag + PyPI) remains a deliberate follow-up — this
  phase made the positioning *honest*, not *published*.
- **CODE_OF_CONDUCT / issue + PR templates** — deferred beyond the minimal
  `CONTRIBUTING.md` per the phase scope.

## Hardware-gated, still open (unchanged)

Phase 24 (companion, 3/6), Phase 25 (HS-25-07 dogfood), Phase 15 (out-and-about)
— all need the physical AI-PI / a real mic and a non-remote author.
