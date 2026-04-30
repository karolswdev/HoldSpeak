# HS-13-03 - Pack-declared settings + defaults

- **Project:** holdspeak
- **Phase:** 13
- **Status:** backlog
- **Depends on:** HS-13-01
- **Unblocks:** per-connector configuration UI
- **Owner:** unassigned

## Problem

Settings live in three places today:

  1. Hard-coded module constants
     (`activity_github.DEFAULT_*`, `activity_jira.DEFAULT_*`).
  2. The pack module's own `DEFAULT_TIMEOUT_SECONDS` etc
     (HS-11-04/05 added these as references but they aren't
     read at runtime).
  3. The connector state's `settings` JSON column (whatever
     the user PUT to `/api/activity/enrichment/connectors/{id}`).

`run_github_cli_enrichment` reads option (3) but falls back to
option (1). The pack-declared option (2) is dead. Phase 13
makes the pack the source of truth.

## Scope

- **In:**
  - Extend `ConnectorManifest` with a `settings_schema` field —
    a list of `SettingDescriptor(key, type, default, label, help)`.
  - Each pack manifest declares its settings (gh: timeout,
    max_bytes, limit; jira: same; firefox_ext: nothing —
    declares an empty schema; calendar: limit only).
  - `activity_github` / `activity_jira` read defaults from the
    pack's settings_schema, not their own `DEFAULT_*` constants.
  - User-set values in `connector.settings` JSON override the
    schema defaults; values for keys not in the schema are
    rejected with a 400 from the PUT endpoint.
  - Migration story: existing settings JSON rows survive (any
    `connector.settings` keys that match a schema key are
    honoured).
- **Out:**
  - A settings-editor UI in `/activity`. The schema enables one
    but the UI itself is a phase-14 story.
  - Schema versioning / migration. We're additive-only for now.

## Acceptance Criteria

- [ ] `ConnectorManifest.settings_schema: tuple[SettingDescriptor, ...]`
  with `validate_manifest` enforcing well-formed entries.
- [ ] gh + jira packs declare timeout / max_bytes / limit;
  calendar declares limit; firefox_ext declares an empty
  schema.
- [ ] `run_github_cli_enrichment` and
  `run_jira_cli_enrichment` resolve defaults via the pack
  schema, not module constants.
- [ ] PUT `/api/activity/enrichment/connectors/{id}` rejects
  unknown setting keys with a 400 + readable error.
- [ ] Existing tests pass without changes to settings payloads.
- [ ] New unit tests cover schema validation, default
  resolution, unknown-key rejection.

## Test Plan

- Unit: pack manifest with an unknown `type` in
  settings_schema fails `validate_manifest`.
- Unit: `resolve_setting(connector, "timeout_seconds")` returns
  the user value if set, the pack default otherwise.
- Integration: PUT settings with `{"timeout_seconds": 10}`
  succeeds; `{"unknown_key": 1}` returns 400.
- Integration: gh enrichment with no user settings uses pack
  defaults; with user settings uses overrides.

## Notes

The settings schema is also the right shape for a future
config-driven UI — labels and help strings travel with the
schema so the UI doesn't need its own copy of those strings.
HS-13-08 might surface a small "configure" panel using this.
