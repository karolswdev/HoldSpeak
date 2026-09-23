# PHILO-3-02 D2 — documented installation and meeting model client

Date: 2026-09-23
Worktree: `/Users/karol/dev/tools/wt-philo-3-02`
Branch: `feat/philo-3-02-summary`
Scope: baseline installation diagnosis, followed by the checked installation correction. No hub, microphone, owner desk, keychain, or model was started or touched.

## Corrected result — Astra verification, 2026-09-23

The ordinary source install now includes `openai>=1.0.0`; local model and speaker runtimes remain optional. Muad'Dib ratified this seam for the first commit, without closing the story. The reproduction below this section is the historical pre-fix result, not the current package contract.

Astra independently repeated `uv venv`, venv activation, and `uv pip install -e .` from a fresh copy of the tracked build inputs with the corrected `pyproject.toml`. The copy had no venv, `node_modules`, or prebuilt web assets. HOME and the package environment were separate temporary directories. Node was the nvm 22.21.0 binary; the normal build hook ran, with no `HOLDSPEAK_SKIP_WEB_BUILD` flag. The production `OpenAI` assertion passed. `openai==3.19.0` was present; `llama_cpp`, `resemblyzer`, `zeroconf`, and `pytest` were absent. [Complete installation output](astra-isolated-source-install-raw.txt).

The same installed-metadata fence fails against the separately built pre-fix package (1 failure, exit 1) and passes after the correction. Astra collected and ran the packaging, intel-package and cloud-client suites: 17 collected, 17 passed. [Pre-fix raw failure](astra-before-metadata-raw.txt), [collection](astra-focused-collect-raw.txt), [run](astra-focused-run-raw.txt). These tests use isolated HOME and a provider double; no real summary is claimed.

One independent attempt in the worktree failed at `npm ci` with `ENOTEMPTY` in `web/node_modules/caniuse-lite/data/regions`; it is retained in [the failed attempt](astra-base-install-after-raw.txt). The fresh source-copy repeat above passed. This is a local dependency-directory problem, not evidence that the corrected public dependency is absent.

Worker provenance: its initial after-fix attempt omitted venv activation and updated the worktree's development environment. That attempt is not the decisive D2 proof. Its later separate-venv proof and Astra's source-copy proof are isolated. Some worker logs are edited transcripts, despite their original “raw” label; the `astra-*-raw.txt` files retain complete command output.

## Historical baseline (before correction)

## Read commands and source result

The required source reads were:

```sh
sed -n '1,240p' docs/internal/TWO-BRAINS.md
sed -n '1,240p' AGENTS.md
sed -n '1,260p' CLAUDE.md
sed -n '1,260p' pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/story-02-see-and-find-the-summary.md
sed -n '1,320p' pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/current-phase-status.md
nl -ba README.md | sed -n '1,260p'
nl -ba pyproject.toml | sed -n '1,220p'
```

The relevant contract is:

- `README.md:18-28` documents `uv venv`, activation, and `uv pip install -e .`; it also names meeting review at `README.md:40-46`.
- `docs/GETTING_STARTED.md:53-64` repeats the base source install (`-e .` on Apple Silicon, `.[linux]` on Linux).
- `docs/GETTING_STARTED.md:221-233` separately documents `uv pip install -e '.[meeting]'` as an optional meeting-analysis capability.
- `docs/MODELS.md:123-135` lists `.[meeting]` as optional meeting-analysis dependencies.
- `pyproject.toml:64-96` declares the `[meeting]` extra with `llama-cpp-python>=0.3.34` and `openai>=1.0.0`.
- `holdspeak/intel/__init__.py:17-35` imports both model clients optionally and sets each to `None` when absent.
- `holdspeak/intel/engine.py:231-261` raises a named error when either client is needed but absent; `:298-318` loads the selected client before inference.
- `holdspeak/intel/engine.py:880-910` parses the model response, including the meeting `summary` field.

## Environment identity

Host: Darwin 25.2.0, arm64 (`uname -a` reported `RELEASE_ARM64_T6020`).
`uv`: 0.9.28 (Homebrew 2026-01-29).
The `uv venv` command selected CPython 3.13.11 from `/Users/karol/.local/bin/python3.13`.
Node was v22.21.0. The repository `.venv` did not exist before the run and was not created.

Each installation used a new `mktemp -d` HOME and a venv in a different `mktemp -d` path. The temporary paths are retained in the logs. No command started `holdspeak`, a hub, a web server, audio capture, or model inference.

## Result

The README/base installation is insufficient for meeting summaries: it installs `holdspeak==0.4.0` and the core dependencies, but neither meeting model client. The fresh import probe found:

```text
holdspeak distribution: 0.4.0
holdspeak: /Users/karol/dev/tools/wt-philo-3-02/holdspeak/__init__.py
openai: MISSING
llama_cpp: MISSING
holdspeak.intel.OpenAI: None
holdspeak.intel.Llama: None
```

The documented `[meeting]` extra does provide the model clients. Its fresh package identity was `openai==3.19.0` and `llama-cpp-python==0.3.35`, and the import probe found `openai.OpenAI` and `llama_cpp.llama.Llama`. It also installed `resemblyzer==0.1.4` and `zeroconf==0.151.3` as declared.

The exact command/output is retained in [baseline-install.log](./baseline-install.log) and [meeting-extra-install.log](./meeting-extra-install.log).

## Minimal fix classification

My initial worker proposal was documentation/install-surface alignment: include the `meeting` extra in the source install command (`uv pip install -e '.[meeting]'` on Apple Silicon, and `uv pip install -e '.[linux,meeting]'` on Linux), or state directly beside the base command that meeting summaries require the separately documented extra. That wording approach is retained as a proposal only; it is not settled or implemented.

The current draft under review is a different boundary: promote the lightweight OpenAI-compatible endpoint client into core dependencies, while leaving the heavyweight local meeting runtime (`llama-cpp-python`, and other local meeting extras) optional. That would make the default installation's endpoint model-client seam importable without forcing a local GGUF runtime. This draft is also neither settled nor implemented.

The package extra itself is correct and was proven importable in isolation. The stronger executable production import fence is retained in [production-import-fence.log](./production-import-fence.log): the base venv fails `from holdspeak.intel import OpenAI; assert OpenAI is not None` with exit `1`, while the `[meeting]` venv passes with exit `0`. This is an executable package/production import probe, not a pytest collection or suite claim.

## Unknowns

The run did not download a GGUF model, configure an endpoint key, call an endpoint, or execute a summary. Therefore it proves dependency/package availability only. It does not prove model readiness, endpoint credentials, summary quality, or the Phase 3 rig chain.
