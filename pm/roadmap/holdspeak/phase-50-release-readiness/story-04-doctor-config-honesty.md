# HS-50-04 — doctor + config honesty

- **Project:** holdspeak
- **Phase:** 50
- **Status:** backlog
- **Depends on:** HS-50-01, HS-50-02
- **Unblocks:** HS-50-07
- **Owner:** unassigned

## Problem
`doctor` runs 16 checks and never looks at the database it depends on
(`commands/doctor.py`), so a user on an unexpected/newer schema has no signal until
something breaks. `Config` has no `config_version` (`config.py:405-448`) and
silently drops unknown keys, so an evolving config format fails invisibly.

## Scope
- **In:**
  - A database/schema check in `doctor` and in `/api/setup/status`
    (`setup_status.py:build_setup_status`): report the DB's current schema version
    vs this build, and flag "unexpected" / "newer than this build" plainly (ties to
    HS-50-02's refusal state).
  - A `config_version` field on `Config` with load-time coercion: a known-older
    config is coerced forward without dropping data; an unknown/newer one is flagged
    honestly rather than silently defaulted.
  - The version (HS-50-01) shown in the same surface.
- **Out:** the schema policy itself (HS-50-02); the backup (HS-50-03). This story is
  the honest reporting + config versioning.

## Acceptance criteria
- [ ] `doctor` and `/api/setup/status` report the real schema state (version vs
      build; unexpected/newer flagged); honest, no silent fix that hides a problem.
- [ ] `Config` carries `config_version` with load-time coercion; an evolving config
      does not silently drop renamed/removed fields.
- [ ] doctor check messages follow the humanizer voice; behavior-preserving
      otherwise; `npm run build` ✓ if UI touched, 0 `_built/` tracked.

## Test plan
- Unit/integration: doctor reports OK on a current DB, flags a stamped newer DB;
  config round-trips with a version, coerces a known-older shape, flags an unknown
  one. `uv run pytest -q -k "doctor or config or setup_status"`.

## Notes / open questions
- Reuse the HS-50-02 refusal exception so doctor renders the same truth the open
  path enforces.
- Keep the new doctor check non-fatal where reasonable (report, do not crash the
  whole doctor run on a missing DB).
