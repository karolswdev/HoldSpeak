# Phase 11 - Local Connector Ecosystem

**Last updated:** 2026-04-27 (phase scaffolded).

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
| HS-11-01 | Connector manifest and SDK shape | backlog | [story-01-connector-manifest-sdk.md](./story-01-connector-manifest-sdk.md) | pending |
| HS-11-02 | Connector fixture and dry-run test harness | backlog | [story-02-fixture-dry-run-harness.md](./story-02-fixture-dry-run-harness.md) | pending |
| HS-11-03 | Firefox companion connector pack | backlog | [story-03-firefox-connector-pack.md](./story-03-firefox-connector-pack.md) | pending |
| HS-11-04 | GitHub CLI connector pack | backlog | [story-04-github-cli-connector-pack.md](./story-04-github-cli-connector-pack.md) | pending |
| HS-11-05 | Jira CLI connector pack | backlog | [story-05-jira-cli-connector-pack.md](./story-05-jira-cli-connector-pack.md) | pending |
| HS-11-06 | Connector developer documentation | backlog | [story-06-connector-developer-docs.md](./story-06-connector-developer-docs.md) | pending |
| HS-11-07 | Connector ecosystem phase exit | backlog | [story-07-dod.md](./story-07-dod.md) | pending |

## Where We Are

Phase 11 is planned but not active. Phase 9 should first polish the
first-party assisted enrichment flows enough to establish the shape of a
connector. Phase 11 begins once connector behavior is stable enough to
extract into reusable manifests, fixtures, and developer-facing docs.

## Source Design

- `docs/PLAN_ACTIVITY_ASSISTED_ENRICHMENT.md`
