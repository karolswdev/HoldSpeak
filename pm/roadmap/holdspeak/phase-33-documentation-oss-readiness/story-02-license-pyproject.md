# HS-33-02 — Apache-2.0 LICENSE + `pyproject` metadata

- **Status:** done (2026-06-03). Evidence: [evidence-story-02.md](./evidence-story-02.md).

## Goal

Make the package legally and metadata-complete for open source. Today there is
**no `LICENSE`** (a hard blocker for OSS) and `pyproject` carries only
`version`/`description`/`readme` — no `license`, `authors`, `classifiers`,
project URLs, or keywords.

## Scope

- **`LICENSE`** — the full **Apache-2.0** text (user decision, 2026-06-03) at the
  repo root.
- **`pyproject.toml` `[project]`:**
  - `license = "Apache-2.0"` (SPDX expression) — and drop any conflicting
    classifier form.
  - `authors = [{ name = "…", email = "…" }]` — confirm the name/email to use
    (the git author is `karolswdev` / `karolsane@gmail.com`).
  - `classifiers` — license, Python versions (3.12), OS (macOS/Linux),
    topic (Multimedia :: Sound, Utilities), development status.
  - `[project.urls]` — Homepage / Repository / Issues / Documentation
    (the GitHub repo + docs).
  - `keywords` — voice-typing, dictation, whisper, local-first, meeting,
    transcription, llm, privacy, etc.
- A short license header/notice is **not** required by Apache-2.0 for every file;
  add a top-level `NOTICE` only if we want attribution aggregation (optional).

## Test plan

- `uv build` (or `python -m build`) succeeds and the wheel/sdist metadata carries
  the license + classifiers.
- `uv run pytest -q --ignore=tests/e2e/test_metal.py` — green (metadata-only).

## Done when

- [x] `LICENSE` (Apache-2.0) at repo root.
- [x] `pyproject` carries license / authors / classifiers / urls / keywords;
      builds cleanly with the metadata.
- [x] Full suite green.
