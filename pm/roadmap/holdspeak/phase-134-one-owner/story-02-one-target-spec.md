# HS-134-02 — One target spec, one API

- **Project:** holdspeak
- **Phase:** 134
- **Status:** backlog
- **Depends on:** —
- **Unblocks:** HS-134-03
- **Owner:** unassigned

## Problem

The dual API survives in reads: `GET /api/profiles` and
`GET /api/profiles/{id}` still serve raw `ProfileRecord` dicts
(`holdspeak/web/routes/primitives/profiles.py:58-95`) beside the
canonical `/api/inference-targets` family; the `_target_fields()`
aliasing is duplicated (`profiles.py:100-124` vs
`profile_service.py:139-167`); and the `profile_alias` compatibility
block rides every target (`inference_targets.py:175-179`,
`profile_service.py:81-86`). Pre-release product — no compat ceremony.

## Scope

### In

- Retire the `/api/profiles` read routes (delete or 301 to
  `/api/inference-targets`; pick the simpler that keeps web tests
  honest — pre-release, deletion preferred).
- One `_target_fields()`: keep `profile_service.py:139-167`, delete the
  route-file duplicate.
- Delete `PROFILE_ALIAS_VERSION` and the `profile_alias` blocks; fix
  the web client if anything reads them (grep web/src first).

### Out

- MCP renames (HS-134-03). The internal `db.profiles` storage name —
  internal storage may keep its name this wave.

## Acceptance criteria

- [ ] No route serves a raw `ProfileRecord` shape; the target contract
  is the only wire shape.
- [ ] Exactly one `_target_fields` definition remains.
- [ ] `grep -rn profile_alias holdspeak/ web/src/` returns zero hits.
- [ ] Focused web-route + inference-target tests green.

## Test plan

- `HOME=$(mktemp -d) uv run pytest -q tests/unit/test_web_routes_primitives.py tests/unit/test_inference_targets.py --tb=short`
  plus affected web tests (`cd web && npx vitest run` scoped to touched
  suites).
