# Evidence — HS-50-01: One true version (single source + surfaced)

Write-once record of what shipped for the version single-source-of-truth, the
cheapest honest win of Phase 50 and the unblock for doctor/install/docs. The
rule that matters: the version has exactly one source (`pyproject.toml`), the
code reads it from package metadata, and a drift test makes the old
`0.1.0` / `0.2.1` split impossible to bring back.

## The problem (before)

- `pyproject.toml:3` said `0.2.1`. `holdspeak/__init__.py:3` said `0.1.0`. Two
  different numbers, no source of truth.
- `__version__` was a hand-typed literal consumed nowhere; nothing surfaced the
  version to the user.
- `scripts/install.sh` pinned `git+...@main` (HEAD), so "install HoldSpeak" was
  not reproducible.

## What shipped

**One source of truth** (`holdspeak/__init__.py`)
- `__version__` now resolves at import time via `_resolve_version()`:
  `importlib.metadata.version("holdspeak")` is the primary path. The metadata is
  written from `pyproject.toml`, so an installed or editable
  (`uv pip install -e .`) tree resolves the true number with no hand-typed
  duplicate.
- Fallback for a raw checkout that was never installed: read the `version = "..."`
  line out of `pyproject.toml` with a regex (no `tomllib`, so it is safe on the
  declared `>=3.10` floor). Last-resort sentinel `0.0.0+unknown` if even that
  fails.
- Verified: `python -c "import holdspeak; print(holdspeak.__version__)"` prints
  `0.2.1` (matches `pyproject`).

**Surfaced in doctor** (`holdspeak/commands/doctor.py`)
- `_check_runtime()` now leads with the version:
  `Runtime: HoldSpeak 0.2.1 on Darwin 25.2.0 (arm64), Python 3.13.11`.
- Verified by running `holdspeak doctor`.

**Surfaced in the API** (`holdspeak/setup_status.py`)
- `build_setup_status()` adds a top-level `"version"` key (the resolved
  `__version__`) to the `/api/setup/status` payload, so the web runtime and any
  UI can show the running version honestly.

**Install pins a tag** (`scripts/install.sh`)
- New `HOLDSPEAK_REF` env var (default `v0.2.1`) drives the git source spec, so
  the default install is a reproducible pinned tag. `HOLDSPEAK_REF=main` is the
  documented development fallback. Usage text and the header comment updated.
- Behavior-preserving otherwise: `HOLDSPEAK_PIP_SPEC` still overrides everything,
  the web-build guard and extras logic are untouched.

## The drift guard

`tests/unit/test_version_ssot.py`:
- `test_code_version_matches_pyproject` — `holdspeak.__version__` equals the
  `pyproject.toml` `project.version`, read independently with `tomllib`. This is
  the guard that the split cannot return.
- `test_version_is_not_the_unknown_fallback` — the sentinel never resolves under
  the test suite.
- `test_doctor_runtime_check_reports_version` — the doctor runtime detail
  contains the version.
- `test_setup_status_reports_version` — the API payload's `version` equals
  `__version__`.

## Tests run

```
uv run pytest -q -k "version or doctor" --ignore=tests/e2e/test_metal.py
-> 53 passed, 2 skipped

uv run pytest -q -k "setup_status or setup or runtime" --ignore=tests/e2e/test_metal.py
-> 188 passed, 4 skipped
```

No UI bundle touched, so `_built/` stays clean (0 tracked).

## Not done here (by design)

- Choosing the actual release number to tag is a maintainer call at close; the
  default `HOLDSPEAK_REF=v0.2.1` tracks the current `pyproject` version and the
  release checklist (HS-50-06) owns keeping them in lockstep.
- The schema policy is HS-50-02.
