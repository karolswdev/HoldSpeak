# Evidence — HS-65-02: The release cut

**Date:** 2026-06-13
**Verdict:** done. v0.3.0 is set, the changelog summarizes P51–P64, and
fresh-venv wheel installs reach a clean doctor on both macOS and real .43
Linux metal.

## What shipped

- `pyproject.toml` → **0.3.0** (`holdspeak.__version__` reads it from
  metadata; the dev tree and a fresh install both report 0.3.0).
- The CHANGELOG **[0.3.0]** entry: Keep-a-Changelog, canon names, grouped
  Added / Changed / Fixed / Internal — covering the wake word, the spoken
  language setting + the spoken-symbol dictionary, Send to Slack, voice
  command macros, activity pre-briefing, meeting + transcript import +
  facets, Qlippy, quiet trust (the egress badge), the front door, and the
  production-bug fixes from the two decomposition phases.
- A version-claims sweep over README + docs/*.md: no stale `0.2.x`
  strings in prose (the PyPI-README pass had already removed them).

## The build (exactly as release.yml does it)

`cd web && npm run build`, then `HOLDSPEAK_SKIP_WEB_BUILD=1 uv build
--sdist` and `--wheel` separately (the workflow's note: a combined build
round-trips through an isolated env and drops the bundle). Results:

- `uvx twine check dist/*` → both PASSED.
- The wheel carries the web bundle: **194** `static/_built/` entries
  (the workflow's gate is ">0").

## The install proofs

- **macOS** (fresh venv, uv-managed CPython 3.13): the wheel installs;
  `holdspeak doctor` → **20 passed, 3 warnings, 0 failed**, version
  0.3.0. The 3 warnings are the documented-expected optional ones (the
  `openai` package absent; the dev config's cloud provider choice).
- **.43 Linux real metal** (fresh venv, Python 3.12.3, isolated
  HOME/XDG, the `[linux]` extra, real `DISPLAY=:0`): version 0.3.0;
  `holdspeak doctor` → **22 passed, 1 warning, 0 failed** — fresh DB
  created, `auto` resolves to faster-whisper, local-only egress, real
  X11 hotkey + text injection PASS. The one warning is the optional
  llama-cpp-python intel backend.
  - Honest note: a first .43 run against the polluted dev HOME showed 4
    fails (a dev DB newer than 0.3.0 triggering the refuse-newer safety,
    the missing `[linux]` extra, a dev config's model path, and headless
    SSH with no DISPLAY). The isolated-HOME rerun above is the true
    fresh-machine proof; the safety refusal firing on a newer DB is the
    Phase-50 behavior working, not a regression.

## Proof

- Full suite: **2777 passed, 17 skipped**.
- `dist/` is not committed (build artifact); the wheel is rebuilt by the
  release workflow at tag time.
