# Evidence — HS-33-04 (README + getting-started OSS pass + CHANGELOG)

**Shipped:** 2026-06-03. The front door is now OSS-grade and honest: badges, a
pre-release status banner, a clean-clone quickstart, license/docs/contributing
links, plus a `CHANGELOG.md` and a minimal `CONTRIBUTING.md`.

## README changes

- **Badges** (top of README): Apache-2.0 license → `LICENSE`; the **Tests** CI
  workflow (`actions/workflows/test.yml/badge.svg`); Python 3.10+; platform
  macOS | Linux. All against the real repo (`github.com/karolswdev/HoldSpeak`).
- **Honest status banner** — a blockquote right under the tagline: "early /
  pre-release… not yet published to PyPI — install from source… APIs/config/
  defaults may still change." (per memory `feedback_holdspeak_not_really_released`).
- **Quickstart** (renamed from "Install") — the install-script one-liner *and* a
  from-clone `uv pip install -e .` path, both ending in `holdspeak doctor &&
  holdspeak`; the `--with-meeting` extra fixed from a placeholder `curl ...` to a
  real command; a closing pointer to `docs/MODELS.md` for the bring-your-own model
  choice.
- **Links** — the "Where to go next" table gained a **Documentation index**
  (`docs/README.md`) row and a **Models** row; a new **Contributing** section
  links `CONTRIBUTING.md` + `CHANGELOG.md`.
- **License section** — `MIT` → "Licensed under the **Apache License 2.0** — see
  `LICENSE`." (the project is Apache-2.0 as of HS-33-02; the stray MIT line was
  wrong).

## New files

- **`CHANGELOG.md`** — Keep a Changelog format with an explicit pre-release note
  ("not formally released… everything is Unreleased; `0.2.1` is an in-dev marker,
  not a published tag") and an `[Unreleased]` section grouped Added / Changed /
  Removed, seeded honestly from the phase history (plugins, dictation pipeline,
  meeting mode, AIPI-Lite, web runtime, trust/hardening, the model + LICENSE +
  docs work; the db decomposition + `WebRuntime` + TUI/menubar removal).
- **`CONTRIBUTING.md`** (minimal) — `uv` setup, the `git config core.hooksPath
  .githooks` one-time step, optional extras, the full-suite test command (with the
  metal-exclusion + `web` rebuild caveats), and the commit-contract workflow
  pointing at `pm/roadmap/PMO-CONTRACT.md`.

## Tests ran

- **README link check** — extracted every relative markdown link + the HTML
  `<img src>` assets and confirmed all resolve on disk (15 markdown links incl.
  the HS-33-03-moved `docs/internal/PLAN_ARCHITECT_PLUGIN_SYSTEM.md`, plus 5 spot-art
  assets). Zero misses.
- `uv run pytest -q --ignore=tests/e2e/test_metal.py` → **1954 passed, 15 skipped**
  (the HS-33-03 doc link-check now also covers `docs/README.md`).

## Done-when

- [x] README is OSS-grade: badges, honest pre-release status, working quickstart,
      license/docs/contributing links.
- [x] `CHANGELOG.md` + a minimal `CONTRIBUTING.md` exist and are accurate.
- [x] No broken README links; full suite green.

## Decisions / deviations

- The current README had **no literal "v0.2.0 released" string** (the memory's
  concern lived in the roadmap's project-metadata, not the public README); the
  honest-status work is therefore an added pre-release banner + the corrected
  license line, not a deletion.
- Community-health beyond a minimal `CONTRIBUTING.md` (CODE_OF_CONDUCT, issue/PR
  templates) stays deferred per the phase scope.
