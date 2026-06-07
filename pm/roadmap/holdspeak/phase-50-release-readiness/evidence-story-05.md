# Evidence — HS-50-05: Verified clean-machine install + pinned contract

Write-once record of actually running the documented install on a clean-ish
environment and confirming it reaches a working `holdspeak doctor`. The full
transcript is in [`install-transcript.txt`](./install-transcript.txt).

## What was run

The documented `GETTING_STARTED.md` step 1 ("From a checkout: `uv pip install
-e .`"), in full isolation so it never touched the developer's real config or
data:

- Fresh venv: `uv venv /tmp/hs-clean-install/venv --python 3.13` -> CPython
  3.13.11.
- `uv pip install -e <checkout> --python <venv>/bin/python` -> resolved and
  installed the entire dependency set (torch 2.12.0, fastapi/starlette, uvicorn
  0.49.0, websockets 16.0, the mlx stack, etc.) with no error.
- Clean temp `HOME` and `XDG_CONFIG_HOME` / `XDG_DATA_HOME` so config and DB
  landed under the temp tree.

## Result: a working doctor, exit 0

```
$ holdspeak doctor
[PASS] Runtime: HoldSpeak 0.2.1 on Darwin 25.2.0 (arm64), Python 3.13.11
[PASS] Config: Loaded .../config.json (config version 1)
[PASS] Database: No database yet at .../holdspeak.db; it is created on first use.
[PASS] Microphone: ...
[PASS] Transcription backend: `auto` resolves to `mlx`
[PASS] Web runtime: fastapi, uvicorn, and websockets are importable
...
[WARN] Meeting intelligence runtime: llama-cpp-python is not available
[WARN] System audio capture: System-audio capture source not configured
Summary: 21 passed, 2 warnings, 0 failed
doctor exit code: 0
```

Key points:
- The version resolves to `0.2.1` from the editable install's metadata (HS-50-01
  single source confirmed end to end on a real install).
- The new Database check (HS-50-04) reports a fresh install honestly: "No database
  yet ... created on first use" -> PASS. The Config check shows "config version 1".
- The two warnings are exactly the expected optional gaps on a minimal machine
  (no local llama.cpp model, no system-audio capture configured). doctor degrades
  honestly, it does not crash. Exit code is 0.

## The pinned install contract (HS-50-01 + this story)

- `scripts/install.sh` now drives the git source spec from `HOLDSPEAK_REF`
  (default `v0.2.1`), so the default install is a reproducible pinned tag, with
  `HOLDSPEAK_REF=main` as the documented development fallback.
- Static verification of that path:
  - `bash -n scripts/install.sh` parses cleanly.
  - default spec resolves to
    `holdspeak @ git+https://github.com/karolswdev/HoldSpeak.git@v0.2.1`.
  - dev fallback resolves to `...@main`.

## Honest scope note

The from-checkout path above is what verifies this branch's code, and it is THE
path documented in `GETTING_STARTED.md` step 1. A live `install.sh` network run
installs from a pushed git ref; the `v0.2.1` tag does not exist yet (tagging is a
maintainer release step, owned by the HS-50-06 release checklist), and an `@main`
install would predate these Phase 50 commits until the PR merges. So the script
path is verified statically here and is wired to pin a tag the moment the
maintainer pushes one; the editable path is verified live.

## No code changes needed

The documented install worked as-is on a clean environment with the Phase 50
changes in place. No breakage was found to fix. This story is verification plus
the captured transcript; the install contract (`HOLDSPEAK_REF`) landed in
HS-50-01.

## Tests

No new automated tests (this is a manual clean-environment verification with a
captured transcript, per the story's test plan). The full suite remains green
from HS-50-04 (2451 passed, 17 skipped); nothing in this story changed code.
