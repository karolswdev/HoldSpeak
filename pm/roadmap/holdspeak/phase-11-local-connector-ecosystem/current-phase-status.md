# Phase 11 - Local Connector Ecosystem

**Last updated:** 2026-04-30 (HS-11-02 fixture-driven dry-run harness shipped).

## Goal

Turn Phase 9's first-party assisted enrichment work into a small local
connector ecosystem: reusable connector contracts, manifest metadata,
dry-run fixtures, developer docs, and first-party connector packs that
can be tested and installed locally without hidden network behavior.

## Scope

- **In:**
  - Connector manifest format.
  - Local connector SDK and test harness.
  - First-party connector packs for Firefox events, GitHub CLI, Jira CLI,
    and calendar candidates.
  - Connector fixture library.
  - Local installation and development docs.
  - Privacy and permission review for each connector.
- **Out:**
  - Public marketplace or remote registry.
  - OAuth-backed cloud connectors.
  - External writes by default.
  - Browser extension store submission.

## Story Status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HS-11-01 | Connector manifest and SDK shape | done | [story-01-connector-manifest-sdk.md](./story-01-connector-manifest-sdk.md) | [evidence-story-01.md](./evidence-story-01.md) |
| HS-11-02 | Connector fixture and dry-run test harness | done | [story-02-fixture-dry-run-harness.md](./story-02-fixture-dry-run-harness.md) | [evidence-story-02.md](./evidence-story-02.md) |
| HS-11-03 | Firefox companion connector pack | backlog | [story-03-firefox-connector-pack.md](./story-03-firefox-connector-pack.md) | pending |
| HS-11-04 | GitHub CLI connector pack | backlog | [story-04-github-cli-connector-pack.md](./story-04-github-cli-connector-pack.md) | pending |
| HS-11-05 | Jira CLI connector pack | backlog | [story-05-jira-cli-connector-pack.md](./story-05-jira-cli-connector-pack.md) | pending |
| HS-11-06 | Connector developer documentation | backlog | [story-06-connector-developer-docs.md](./story-06-connector-developer-docs.md) | pending |
| HS-11-07 | Connector ecosystem phase exit | backlog | [story-07-dod.md](./story-07-dod.md) | pending |

## Where We Are

Phase 11 is now **active**. Phases 9 and 10 are both done; the
phase-9 first-party connectors (`gh`, `jira`, `calendar_activity`,
`firefox_ext`) and the shared dry-run harness from HS-9-13 are
the substrate.

HS-11-01 ships the contract: `holdspeak/connector_sdk.py` exposes
a `ConnectorManifest` frozen dataclass + `validate_manifest()`
that collects every problem at once + four runtime-checkable
Protocols (`Discover`, `Preview`, `Enrich`, `Clear`). Frozen
vocabulary sets enumerate the kinds, capabilities, and
permissions the existing first-party connectors actually use, so
HS-11-03..05 can rebuild them on top of this shape without
surface drift. Permission model requires at least one network
permission for any manifest declaring `requires_network=true`.

HS-11-02 ships the fixture harness:
`holdspeak/connector_fixtures.py` exposes
`load_fixture` / `discover_fixtures` / `run_fixture` plus a
`ConnectorFixtureExpectation` whose every field is optional —
fixtures express only the invariants they care about. Six
golden JSON fixtures under `tests/fixtures/connectors/` cover
the three first-party connectors at happy-path and empty-
ledger states; a parametrized pytest auto-grows whenever a new
JSON file lands. The mutation-free guarantee is part of every
fixture run by construction. `FixtureRunResult.diff_report()`
renders failures with each drifted field and a payload summary
the operator can paste back as the new expectation.

Up next: HS-11-03..05 (rebuild Firefox / gh / jira packs
against the manifest + Protocols, dropping fixtures alongside),
HS-11-06 (developer docs), HS-11-07 (phase exit).

## Source Design

- `docs/PLAN_ACTIVITY_ASSISTED_ENRICHMENT.md`
