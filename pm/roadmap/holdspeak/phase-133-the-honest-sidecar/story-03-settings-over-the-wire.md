# HS-133-03 — Settings over the wire

- **Project:** holdspeak
- **Phase:** 133
- **Status:** done
- **Depends on:** HS-133-01
- **Unblocks:** HS-133-11
- **Owner:** unassigned

## Problem

Settings are readable and writable from the web only.
`SettingsService` validates every section and strips secret mutations
(`strip_secret_mutations`, settings_service.py:144), but no MCP surface
exists, and a naive one would move the egress boundary silently —
`meeting.intel_provider` local→cloud is one patch away
(settings_service.py:363-371).

## Scope

### In

Per assets/surface-spec.md §1B, verbatim:
`holdspeak/mcp/families/settings.py` implementing `settings.get`
(get_settings :185) and `settings.update` (update_settings :191) with
the spec's schemas INCLUDING the counsel-mandated egress sentence in the
`settings.update` description (Article III.2). Secrets stay unwritable
(the service strips them) and redacted on read. Validation failures and
stale `_revision` conflicts surface as `isError: true`.
`on_settings_applied=None` per counsel Q3; the description names the
no-live-reload behavior.

### Out

- Adding `companion_github_repo` to SECRET_PATHS (held owner question 2
  in the phase status). A `holdspeak://settings` resource (declined in
  the spec — staleness). Any SettingsService change.

## Acceptance criteria

- [ ] `settings.get` returns the redacted document with `_revision` and
  `_placement`; a test asserts no secret value appears in the response.
- [ ] `settings.update` applies a valid patch, refuses a secret-path
  write, surfaces a validation error and a stale-revision conflict as
  `isError: true` (four tests).
- [ ] The shipped `settings.update` description contains the egress
  warning and `_placement` pointer verbatim from the spec.
- [ ] REQUIRED_TOOLS extended with both names.

## Test plan

- `HOME=$(mktemp -d) uv run pytest -q tests/unit/test_mcp_phase133.py tests/unit/test_mcp_tools.py --tb=short`
