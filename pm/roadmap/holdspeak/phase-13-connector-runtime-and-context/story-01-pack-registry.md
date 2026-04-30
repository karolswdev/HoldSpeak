# HS-13-01 - Pack-driven runtime registry

- **Project:** holdspeak
- **Phase:** 13
- **Status:** backlog
- **Depends on:** HS-11-07
- **Unblocks:** every other phase-13 story
- **Owner:** unassigned

## Problem

Phase 11 built `connector_packs/{firefox_ext,github_cli,jira_cli}.py`
with validated manifests, but the runtime still reaches for
`holdspeak/activity_connectors.py:KNOWN_CONNECTORS` — a static
list of `ConnectorDescriptor` instances assembled by hand. The
manifests are documentation; the descriptors are truth. Every
new pack means editing the registry in two places.

## Scope

- **In:**
  - Add a calendar-candidates pack module under
    `connector_packs/` so all four first-party connectors are
    pack-shaped.
  - Replace `KNOWN_CONNECTORS` with a function that derives the
    registry from `ALL_PACKS` (manifest fields → descriptor
    fields). Existing call sites
    (`web_server.api_list_activity_enrichment_connectors`,
    `activity_connector_preview.dry_run`) stay on the same
    descriptor shape.
  - Drop the `activity_connectors.ConnectorDescriptor` dataclass
    or alias it to a thin wrapper around `ConnectorManifest`.
  - Update fixture harness to read the descriptor from the
    pack-derived registry.
- **Out:**
  - User-pack discovery (HS-13-04).
  - Permission enforcement (HS-13-02).
  - Pack-declared settings (HS-13-03).

## Acceptance Criteria

- [ ] `connector_packs/` ships four pack modules
  (`firefox_ext`, `github_cli`, `jira_cli`, `calendar_activity`).
- [ ] `activity_connectors.KNOWN_CONNECTORS` is removed (or
  becomes a function delegating to the pack registry).
- [ ] `GET /api/activity/enrichment/connectors` returns the same
  payload shape as today, sourced from pack manifests.
- [ ] Existing phase-9 + phase-11 tests stay green without
  modification.
- [ ] No code path references both `ConnectorDescriptor` *and*
  `ConnectorManifest` for the same connector.

## Test Plan

- Existing `tests/integration/test_web_activity_api.py` connector
  list assertions should pass unchanged.
- Existing `tests/unit/test_activity_connector_preview.py` cases
  should pass unchanged.
- Existing `tests/unit/test_connector_fixture_harness.py` cases
  should pass unchanged.
- Existing `tests/unit/test_connector_packs.py` manifest tests
  should pass unchanged.
- New unit test asserting the pack-derived registry contains
  exactly the four expected pack ids.

## Notes

This is the riskiest substrate story because every other
phase-13 story builds on it. Land it carefully; keep the
descriptor shape stable so the API + UI don't ripple.
