# HS-50-01 — One true version (single source + surfaced)

- **Project:** holdspeak
- **Phase:** 50
- **Status:** done
- **Depends on:** none
- **Unblocks:** HS-50-04, HS-50-05, HS-50-06, HS-50-07
- **Owner:** unassigned

## Problem
The version is two different numbers: `pyproject.toml:3` says `0.2.1`,
`holdspeak/__init__.py:3` says `0.1.0`. There is no single source of truth, nothing
surfaces the version to the user, and the install script pins git HEAD rather than
a tag. A release cannot have an ambiguous version.

## Scope
- **In:**
  - One source of truth for the version. Prefer reading the installed package
    metadata (`importlib.metadata.version("holdspeak")`) with a sane fallback for
    the editable/source run; or pin `__version__` to the `pyproject` value. The
    `0.1.0`/`0.2.1` mismatch is gone.
  - Surface the version in `doctor` (a line in the runtime check) and one
    API/UI spot (e.g. `/api/setup/status` or the settings page).
  - `scripts/install.sh` can install a pinned tag, with a documented `@main` dev
    fallback.
  - A test that pins code-version == package-version so it cannot drift again.
- **Out:** the schema policy (HS-50-02); choosing the actual release number to tag
  (a maintainer call at close).

## Acceptance criteria
- [x] A single source of truth for the version; `__init__.__version__` and
      `pyproject` agree (no mismatch); a drift test enforces it.
      (`holdspeak/__init__.py` `_resolve_version()`,
      `tests/unit/test_version_ssot.py`)
- [x] The version is surfaced in `doctor` and one API/UI spot.
      (doctor runtime check + `/api/setup/status` `version` key)
- [x] `scripts/install.sh` installs a pinned tag (documented `@main` fallback);
      behavior-preserving otherwise. (`HOLDSPEAK_REF`, default `v0.2.1`)
- [x] `npm run build` n/a (no UI bundle touched); 0 `_built/` tracked.

## Test plan
- Unit: `holdspeak.__version__` equals the `pyproject`/metadata version;
  `uv run pytest -q -k "version or doctor"`.
- Manual: `holdspeak doctor` prints the right version; the API/UI shows it.

## Notes / open questions
- `importlib.metadata` only resolves for an installed dist; keep a fallback for the
  source run and make the drift test robust to both (read `pyproject` directly in
  the test if needed).
