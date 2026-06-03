# HS-33-04 — README + getting-started OSS pass + CHANGELOG

**Status:** not-started.

## Goal

Make the front door OSS-grade and **honest**. The README is decent but lacks the
signals an open-source visitor expects, and it positions the project as released
when it isn't (the "v0.2.0 released" line is forward-looking).

## Scope

- **README:**
  - Badges: license (Apache-2.0), CI status, Python version, platform. (Use
    shields.io against the real repo/workflow.)
  - **Honest status** — replace any "released / v0.2.0 released" claim with an
    accurate "early / pre-release, install from source" framing (the repo is not
    actually published; see memory `feedback_holdspeak_not_really_released`).
  - A crisp **quickstart** that works from a clean clone (install → `doctor` →
    run), pointing at `docs/MODELS.md` for the model choice.
  - Links: `LICENSE`, `docs/README.md` (index), `CONTRIBUTING.md`,
    `docs/SECURITY.md`.
  - Keep the Phase-30 "Signal" identity + the (refreshed in HS-33-05) spot art.
- **`CHANGELOG.md`** — a `Keep a Changelog`-style file; seed it from the phase
  history (an honest "Unreleased" + the notable milestones) without overclaiming
  a release.
- **`CONTRIBUTING.md`** (minimal) — how to set up (`uv`, the test command), the
  PMO/commit-contract note (point at `pm/roadmap/PMO-CONTRACT.md`), the
  `git config core.hooksPath .githooks` one-time step, and how to run the suite.

## Test plan

- Manual: a clean-clone reader can follow the quickstart; every README link
  resolves (incl. the moved docs from HS-33-03).
- `uv run pytest -q --ignore=tests/e2e/test_metal.py` — green.

## Done when

- [ ] README is OSS-grade: badges, honest pre-release status, working quickstart,
      license/docs/contributing links.
- [ ] `CHANGELOG.md` + a minimal `CONTRIBUTING.md` exist and are accurate.
- [ ] No broken README links; full suite green.
