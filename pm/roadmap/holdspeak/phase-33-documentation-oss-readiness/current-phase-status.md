# Phase 33 — Documentation & Open-Source Readiness

**Status:** in-progress (opened 2026-06-03). 5/6 stories shipped.

**Last updated:** 2026-06-03 (HS-33-05 shipped — brand mark + social/OG card via
the pixellab MCP, on the Signal palette; wired into README + apple-touch-icon).

## Goal

Get HoldSpeak ready for **open-source prime time**. The code is mature
(Phases 0–32) but the *outward-facing* surface isn't: there's no `LICENSE`, the
`pyproject` metadata is a stub, the model/runtime story is framed around aging
hard-coded models (Qwen2.5 / Mistral-7B-v0.3 while the project already runs
Qwen3.5-9B), `docs/` mixes user guides with internal phase plans, and the README
needs an honest OSS-grade pass. Plus: refresh the visual assets (pixel-art spot
art) to a coherent, prime-time set.

This phase touches **outward-facing docs, metadata, and assets** — not product
behavior. It builds on HS-32-06 (the doc-truth sweep): that made docs *true*;
this makes the project *presentable and adoptable*.

## Scope

### In

- **Model framing (HS-33-01).** Stop prescribing specific aging models in
  user-facing strings; bump example/default models to the current **Qwen3.5**
  family; add `docs/MODELS.md` (the "bring your own — GGUF in-process / MLX on
  Apple / any OpenAI-compatible endpoint" contract); clarify the intel `cloud`
  provider as "OpenAI-compatible endpoint" (it already takes a `base_url`).
- **Apache-2.0 LICENSE + `pyproject` metadata (HS-33-02).** Add the `LICENSE`
  file (Apache-2.0, **user decision 2026-06-03**); fill `pyproject` `license`,
  `authors`, `classifiers`, `[project.urls]`, `keywords`.
- **`docs/` reorganization (HS-33-03).** Separate user-facing guides from
  internal/historical plans (e.g. `docs/internal/` for `PLAN_*`,
  `CROSS_PLATFORM_*`, `LINUX_PORT_*`, `RELEASE_HARDENING_CHECKLIST`); add a
  `docs/README.md` index that surfaces the user journey; fix any links the move
  breaks. The PMO roadmap corpus (`pm/`) is untouched.
- **README + getting-started OSS pass (HS-33-04).** Badges (license/CI/python),
  honest version/status positioning (the repo is **not actually released** —
  README's "v0.2.0 released" is forward-looking), a crisp quickstart, links to
  LICENSE / docs / contributing; a `CHANGELOG.md`; a minimal `CONTRIBUTING.md`.
- **Visual assets via pixellab MCP (HS-33-05).** Audit the existing
  `docs/assets/pixellab/` spot art; spec + generate the prime-time set (a
  logo/hero mark, a GitHub social-preview / OG image, refreshed workflow
  illustrations in one coherent style); wire them into the README/docs. *(Runs
  with the pixellab MCP connected — the asset generation, not a code gate.)*
- **Phase closeout (HS-33-06).** Re-verify doc truth + the drift guard, write the
  `final-summary.md`.

### Out

- **Product behavior.** No runtime/feature changes — defaults can change values
  (model names) but no new behavior. (HS-33-01 changes *defaults/strings*, not
  the runtime that consumes them.)
- **The PMO roadmap corpus** (`pm/roadmap/**`) — kept verbatim; this phase
  reorganizes `docs/`, not `pm/`.
- **A formal release** (tagging, PyPI publish) — positioning is made *honest*
  here, but cutting a release is its own follow-up.
- **CODE_OF_CONDUCT / full community-health set** — not selected for this phase
  (a minimal `CONTRIBUTING.md` lands in HS-33-04; the rest is a noted follow-up).

## Exit criteria (evidence required)

- [x] User-facing model strings **suggest**, don't prescribe; example/default
      models are current (Qwen3.5 family); `docs/MODELS.md` documents the
      bring-your-own contract; the intel `cloud` provider is clearly "OpenAI-
      compatible endpoint." (HS-33-01) ✅
- [x] An **Apache-2.0 `LICENSE`** exists; `pyproject` carries `license`,
      `authors`, `classifiers`, `urls`, `keywords`. (HS-33-02) ✅
- [x] `docs/` cleanly separates user-facing from internal/historical, with a
      `docs/README.md` index; no broken links. (HS-33-03) ✅
- [x] README is OSS-grade (badges, honest status, quickstart, license/docs
      links); `CHANGELOG.md` + a minimal `CONTRIBUTING.md` exist. (HS-33-04) ✅
- [x] The visual-asset set is coherent and prime-time; wired into README/docs;
      generation provenance (prompts/IDs) recorded like the existing
      `docs/assets/pixellab/README.md`. (HS-33-05) ✅
- [ ] `uv run pytest -q --ignore=tests/e2e/test_metal.py` green throughout (this
      is mostly docs, but the model-default + any link-check tests must pass).

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HS-33-01 | Model framing + `MODELS.md` | done | [story-01-model-framing.md](./story-01-model-framing.md) | [evidence-story-01.md](./evidence-story-01.md) |
| HS-33-02 | Apache-2.0 LICENSE + `pyproject` metadata | done | [story-02-license-pyproject.md](./story-02-license-pyproject.md) | [evidence-story-02.md](./evidence-story-02.md) |
| HS-33-03 | `docs/` reorganization + index | done | [story-03-docs-reorg.md](./story-03-docs-reorg.md) | [evidence-story-03.md](./evidence-story-03.md) |
| HS-33-04 | README + getting-started OSS pass + CHANGELOG | done | [story-04-readme-oss-pass.md](./story-04-readme-oss-pass.md) | [evidence-story-04.md](./evidence-story-04.md) |
| HS-33-05 | Visual assets (pixellab MCP) | done | [story-05-visual-assets.md](./story-05-visual-assets.md) | [evidence-story-05.md](./evidence-story-05.md) |
| HS-33-06 | Phase closeout + final-summary | not-started | [story-06-closeout.md](./story-06-closeout.md) | — |

## Where we are

Opened 2026-06-03 right after Phase 32 closed (and merged via PR #8). Phase 32
made the docs *true*; Phase 33 makes the project *adoptable*. The trigger was a
review of the model framing — we kept pointing at Qwen2.5-3B / Mistral-7B-v0.3 in
defaults and "Download exactly this" strings, while the project already runs
Qwen3.5-9B. Research (2026-06-03) confirmed Qwen is at **3.5** (Feb 2026) / **3.6**
(Apr 2026), so the references are 2–3 generations stale; GGUF itself is current
and fine. From there the broader OSS gap was obvious: no LICENSE, stub metadata,
a `docs/` folder a newcomer can't navigate, and assets worth refreshing.

**HS-33-01 shipped** (2026-06-03): de-prescribed the user-facing model strings
(missing-model errors, doctor/guidance fixes, the web dictation-runtime docs page);
bumped the example/default models to the **Qwen3.5** family (dictation
`llama_cpp`/`mlx`/`openai_compatible`, intel realtime + `DEFAULT_INTEL_MODEL_PATH`);
added **`docs/MODELS.md`** (the bring-your-own contract — GGUF in-process · MLX on
Apple · any OpenAI-compatible endpoint) and clarified the intel `cloud` provider as
"any OpenAI-compatible endpoint" (it already honors `intel_cloud_base_url`, key
optional). Rebuilt the web bundle so the served docs page matches. Suite green at
1953/15; touched files ruff-clean.

**HS-33-02 shipped** (2026-06-03): added the Apache-2.0 `LICENSE` (user decision)
and a complete `[project]` metadata block — `license = "Apache-2.0"` (SPDX) +
`license-files`, `authors`, 11 `keywords`, 13 `classifiers` (Python 3.10–3.13,
macOS/Linux, speech/utilities topics, Beta), and `[project.urls]`
(Homepage/Repository/Issues/Documentation → `github.com/karolswdev/HoldSpeak`).
`uv build` succeeds; verified `Metadata-Version: 2.4` + `License-Expression` +
`License-File` in the built wheel.

**HS-33-03 shipped** (2026-06-03): `git mv`'d 13 internal/historical docs into
`docs/internal/` (the `PLAN_*` specs + `CROSS_PLATFORM_*` / `LINUX_PORT_*` /
`RELEASE_HARDENING_CHECKLIST`), leaving 11 user-facing guides in `docs/`; added a
`docs/README.md` index (Start-here user journey + reference + an `internal/`
pointer); repointed every **live** inbound link (CLAUDE.md + the live roadmap
README source-canon, root README, ~12 source docstrings, `release_gate.py`, the
flagship-audit test, internal cross-refs); and added a link-check
(`test_no_live_doc_has_a_dangling_relative_link`). Frozen history (`docs/evidence/`
+ `pm/` phase folders) left verbatim. Suite green 1953/15.

**HS-33-04 shipped** (2026-06-03): OSS-grade README pass — license/CI/Python/
platform badges, a pre-release status banner, a clean-clone quickstart (one-liner
+ from-clone, both → `doctor && holdspeak`) with a `docs/MODELS.md` pointer, a
docs-index + Models + Contributing links, and the stray `MIT` license line
corrected to Apache-2.0. New `CHANGELOG.md` (Keep a Changelog, honest "everything
Unreleased") + minimal `CONTRIBUTING.md` (uv setup, hooks, test command, commit
contract). All README links verified; suite green 1954/15.

**HS-33-05 shipped** (2026-06-03): generated the HoldSpeak **brand mark** (held-key
+ rising soundwaves, orange `#FF6B35`, PixelLab obj
`52e0db41-4789-45b3-9136-1ee3e4e7838d`) and composed a **1280×640 social/OG card**
+ a 256px app icon + a refreshed 180px `apple-touch-icon` (PixelLab makes ≤400px
sprites, so the card is composed from the mark + workflow icons on the Signal
palette via committed `compose_og_card.py`). Audited the existing spot-art set —
coherent, no regen. Wired the mark into the README header; provenance recorded.
Manual follow-up: set `social-card.png` in the repo's *Settings → Social preview*.

**Next: HS-33-06** (phase closeout + final-summary) — the last story.

## Pickup order

1. HS-33-01 — model framing + `MODELS.md`. **✅ done (2026-06-03).**
2. HS-33-02 — Apache-2.0 LICENSE + `pyproject` metadata. **✅ done (2026-06-03).**
3. HS-33-03 — `docs/` reorg + index (do before the README pass so links settle). **✅ done (2026-06-03).**
4. HS-33-04 — README + getting-started OSS pass + CHANGELOG. **✅ done (2026-06-03).**
5. HS-33-05 — visual assets via the pixellab MCP. **✅ done (2026-06-03).**
6. HS-33-06 — closeout + final-summary. **◀ next (last story).**

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| Model names rot again (we enshrine Qwen3.5, it ages) | High (certain, over time) | Frame as *suggestions* + a `MODELS.md` that says "current picks, refreshed periodically"; lean on the bring-your-own contract, not a single hardcoded model | A future reader finds a "Download exactly X" string |
| `docs/` reorg breaks inbound links (README, code comments, other docs) | Medium | Grep every moved file's basename before+after; a link-check pass in the closeout | A 404 / dead relative link |
| Asset restyle drifts from the "Signal" web identity (Phase 30) | Medium | Reuse the existing pixellab style + the Signal palette; keep the existing spot-art set as the style anchor | New assets clash with the web UI |
| Changing a default model value breaks a test that pins the old string | Low | `grep` tests for the model paths before editing; update assertions in the same commit | `test_config` / dictation tests fail on a pinned model name |

## Decisions made (this phase)

- 2026-06-03 — **License = Apache-2.0** (permissive + explicit patent grant) — user.
- 2026-06-03 — **Phase scope:** model framing + LICENSE/metadata + `docs/` reorg +
  README OSS pass + **visual assets (pixellab)**; community-health set
  (CODE_OF_CONDUCT etc.) deferred beyond a minimal CONTRIBUTING — user.
- 2026-06-03 — **GGUF stays** as the default local format (it's current, not
  stone-age); only the specific *model names* are refreshed and de-prescribed.

## Decisions deferred

- ~~Exact `docs/internal/` layout~~ — **resolved in HS-33-03**: a single
  `docs/internal/` for plans + a `docs/README.md` index (the default).
- Whether to cut an actual release (tag + PyPI) — trigger: post-phase — default:
  positioning made honest now; release is a separate follow-up.
