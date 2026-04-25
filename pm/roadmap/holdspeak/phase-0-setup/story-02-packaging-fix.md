# HS-0-02 — Fix vanilla `holdspeak` install (web deps + doctor check)

- **Project:** holdspeak
- **Phase:** 0
- **Status:** done
- **Depends on:** none
- **Unblocks:** HS-1-01 (DIR-01 needs a known-good baseline install)
- **Owner:** agent (this session)

## Problem

A vanilla `holdspeak` install (whether the README's curl one-liner or
`uv pip install -e .`) produced a default command that did not start.
The default `holdspeak` invokes the web runtime, which requires
`fastapi` + `uvicorn` + `websockets`. None of those were in core deps
— they were hidden in the `[meeting]` extra alongside heavy LLM
deps (`llama-cpp-python`, `resemblyzer`). The `[meeting]` extra
also listed plain `uvicorn` rather than `uvicorn[standard]`, so
even users who installed the extra got `Unsupported upgrade request`
warning spam on every page load. `holdspeak doctor` did not catch
any of this — it had no web-runtime preflight.

## Scope

- **In:**
  - Move `fastapi>=0.100.0` and `uvicorn[standard]>=0.20.0` into core `pyproject.toml` dependencies.
  - Drop the now-redundant `fastapi` and plain `uvicorn` from the `[meeting]` extra.
  - Add `_check_web_runtime()` to `holdspeak/commands/doctor.py` (importability check for `fastapi`, `uvicorn`, `websockets`).
  - Bump version `0.2.0 → 0.2.1`.
- **Out:**
  - `[meeting]` reshape beyond the two redundant entries.
  - `install.sh` changes (the curl install path picks up new core deps automatically).
  - README rewording (the curl one-liner is correct as-is once core deps are right).
  - MLX-LM vs llama-cpp question for meeting intel — separate, deferred.

## Acceptance criteria

- [x] `pyproject.toml` core `dependencies` lists `fastapi>=0.100.0` and `uvicorn[standard]>=0.20.0`.
- [x] `pyproject.toml` `[meeting]` extra no longer contains `fastapi` or plain `uvicorn`.
- [x] `pyproject.toml` `version = "0.2.1"`.
- [x] `holdspeak/commands/doctor.py` defines `_check_web_runtime()` and registers it in `collect_doctor_checks()`.
- [x] `holdspeak doctor` prints `Web runtime` row with `PASS` status on the reference machine.
- [x] `pytest -k doctor` passes (9 tests).
- [x] `holdspeak` (default web command) starts cleanly with no `Unsupported upgrade request` warnings.

## Test plan

- **Unit:** `uv run pytest tests/ -k doctor -q` — 9 tests, all pass. Output captured in evidence.
- **Integration:** Smoke-run `holdspeak` in background; capture stdout for ≥3s; verify no WebSocket warning spam. Captured in evidence.
- **Manual:** Eyeball `holdspeak doctor` output for the new `Web runtime` row.

## Notes / open questions

- Python 3.14 from homebrew has a `platform.mac_ver()` regression that
  trips up `uv pip install`. The reference venv was rebuilt on
  Python 3.13.11 (`uv sync --python 3.13`). This is an environment
  detail, not a project bug — does not affect the install fix.
- One real packaging quirk remains: `[meeting]` is now a "LLM intel +
  speaker" extra. Renaming or splitting it (`[intel]`, `[speaker]`)
  is deferred — see decision log in `current-phase-status.md`.
