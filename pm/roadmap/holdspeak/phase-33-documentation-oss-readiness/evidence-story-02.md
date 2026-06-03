# Evidence — HS-33-02 (Apache-2.0 LICENSE + `pyproject` metadata)

**Shipped:** 2026-06-03. The package is now legally and metadata-complete for
open source: a full **Apache-2.0** `LICENSE` at the repo root, and a real
`[project]` metadata block (license / authors / classifiers / urls / keywords)
that builds cleanly and lands in the wheel/sdist metadata.

## What changed

- **`LICENSE`** (new) — the verbatim Apache-2.0 text (user decision 2026-06-03),
  appendix copyright line "Copyright 2026 HoldSpeak contributors".
- **`pyproject.toml` `[project]`:**
  - `license = "Apache-2.0"` — SPDX expression (metadata 2.4 / `License-Expression`);
    `license-files = ["LICENSE"]` so the text bundles into dists.
  - `authors = [{ name = "karolswdev", email = "karolsane@gmail.com" }]` — the git
    author identity.
  - `keywords` — voice-typing, dictation, speech-to-text, whisper, transcription,
    meeting, local-first, privacy, llm, macos, linux.
  - `classifiers` — Development Status :: 4 - Beta, Console env, audiences,
    macOS + Linux OS, Python 3 / 3.10–3.13 (matching `requires-python = ">=3.10"`),
    Topic :: Multimedia :: Sound/Audio :: Speech, Topic :: Utilities.
  - `[project.urls]` — Homepage / Repository / Issues / Documentation, all under
    `github.com/karolswdev/HoldSpeak` (confirmed via `git remote -v`).
  - sdist `include` gained `/LICENSE`.
- No `NOTICE` file added — Apache-2.0 does not require per-file headers or a
  NOTICE for a single-origin project (the story marked it optional).

## Decisions / deviations

- **Python classifiers list 3.10–3.13**, not just 3.12 as the story sketched —
  the package's actual floor is `requires-python = ">=3.10"`, so the classifiers
  match the real support matrix.
- **Author = `karolswdev` / `karolsane@gmail.com`** — taken from the git author
  identity the story pointed at; no separate decision needed.

## Tests ran

- `uv build` → **`Successfully built dist/holdspeak-0.2.1.tar.gz`** and
  **`…-py3-none-any.whl`**. Inspected `holdspeak-0.2.1.dist-info/METADATA`:
  `Metadata-Version: 2.4`, `License-Expression: Apache-2.0`,
  `License-File: LICENSE`, all four `Project-URL` lines, the `Keywords` line, and
  all 13 `Classifier` lines present.
- `uv run pytest -q --ignore=tests/e2e/test_metal.py` → **1953 passed, 15 skipped**
  (metadata-only change; suite unchanged from HS-33-01).

## Done-when

- [x] `LICENSE` (Apache-2.0) at repo root.
- [x] `pyproject` carries license / authors / classifiers / urls / keywords;
      builds cleanly with the metadata (verified in the wheel METADATA).
- [x] Full suite green.
