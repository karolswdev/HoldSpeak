# Contributing to HoldSpeak

Thanks for your interest in HoldSpeak! This is a small, early-stage project —
contributions, bug reports, and ideas are all welcome.

## Setup

HoldSpeak uses [`uv`](https://docs.astral.sh/uv/) for environment and dependency
management.

```bash
git clone https://github.com/karolswdev/HoldSpeak.git && cd HoldSpeak
uv pip install -e '.[dev]'

# One-time: enable the project's git hooks (see "Commit workflow" below).
git config core.hooksPath .githooks
```

Optional runtime extras (install what you're working on):

- `.[meeting]` — meeting mode + local intel
- `.[dictation-mlx]` / `.[dictation-llama]` / `.[dictation-openai]` — dictation LLM backends
- `.[linux]` — `faster-whisper` for Linux transcription

The LLM is bring-your-own — see [`docs/MODELS.md`](docs/MODELS.md).

## Running the tests

```bash
# Full suite (the metal test hangs without a real mic — always exclude it):
uv run pytest -q --ignore=tests/e2e/test_metal.py

# Lint:
uv run ruff check holdspeak/
```

Run the **whole** suite before sending changes — `-k` filters miss real
regressions. If you touch anything under `web/`, rebuild the static bundle
(`cd web && npm run build`; Node ≥ 22.12) since some tests read the built JS.
Before changing web pages or their scripts, read
[`docs/internal/ARCHITECTURE_WEB_FRONTEND.md`](docs/internal/ARCHITECTURE_WEB_FRONTEND.md)
— it records the page decomposition pattern (section partials + behavior
modules), the Astro scoped-CSS-on-JS-rendered-DOM trap, and the density
budgets a guard test enforces. Before changing `web_runtime.py` or
`meeting_session/`, read
[`docs/internal/ARCHITECTURE_BACKEND_RUNTIME.md`](docs/internal/ARCHITECTURE_BACKEND_RUNTIME.md)
— the backend twin: the mixin pattern, where patch targets live, and the
backend density budgets.

## Commit workflow

This repo gates every commit on a small "commit contract" via a pre-commit hook
(installed by the `git config core.hooksPath .githooks` step above). Before each
commit, write `.tmp/CONTRACT.md` from the template in
[`pm/roadmap/PMO-CONTRACT.md`](pm/roadmap/PMO-CONTRACT.md) and check each box only
after honestly verifying it. The hook validates and deletes the file on success;
if it blocks you, its stderr says exactly which rule failed.

A few house rules the hook (and reviewers) expect:

- **Tests ran** — actually run the suite and read the output; a type-check is not
  validation.
- **Docs updated** — if you change behavior, update the relevant doc in the same
  commit.
- No `--no-verify`.

The project's planning of record lives under
[`pm/roadmap/holdspeak/`](pm/roadmap/holdspeak/); the documentation index is
[`docs/README.md`](docs/README.md).

## Reporting issues

Open an issue at
[github.com/karolswdev/HoldSpeak/issues](https://github.com/karolswdev/HoldSpeak/issues).
For anything security- or privacy-sensitive, see
[`docs/SECURITY.md`](docs/SECURITY.md) first.
