# Phase 8 - Local Activity Intelligence

**Last updated:** 2026-04-26 (phase opened after Phase 7 closure - focus shifts to opt-in local browser-history activity context).

## Goal

Build a private, local-first activity intelligence layer from browser
history metadata. Phase 7 made reviewed meeting work portable. Phase 8
adds the next ambient context source: read-only Safari and Firefox
history ingestion that identifies work objects the user recently touched
such as Jira tickets, Miro boards, GitHub PRs/issues, docs, and related
project URLs.

The core product idea is a **Local Attention Ledger**: a normalized,
auditable local timeline of work objects, not raw surveillance. HoldSpeak
should use it to help answer "what have I been working on?", enrich
meeting/dictation context, and assemble better handoff material while
remaining local, opt-in, inspectable, and deletable.

## Scope

- **In:**
  - Opt-in browser-history source plugin for Safari and Firefox.
  - Read-only ingestion using safe database-copy strategies.
  - Local persistence for normalized activity records.
  - Entity extraction for Jira, Miro, GitHub, Linear, Confluence/Atlassian
    pages, Google Docs/Drive, Notion, and generic domains.
  - Project-linking rules and recent activity surfaces.
  - Privacy controls: pause, clear imported activity, allowlist/denylist,
    retention, and exact-data visibility.
- **Out:**
  - Scraping page contents or browser cookies.
  - Reading credentials, form contents, or private browsing windows.
  - Network calls to Jira/Miro/GitHub/etc.
  - Automatic external task creation.
  - Always-on hidden collection. The feature must be opt-in and visible.

## Story Status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HS-8-01 | Browser history source audit | ready | [story-01-browser-history-source-audit.md](./story-01-browser-history-source-audit.md) | pending |
| HS-8-02 | Activity ledger persistence | backlog | [story-02-activity-ledger-persistence.md](./story-02-activity-ledger-persistence.md) | pending |
| HS-8-03 | Safari and Firefox history readers | backlog | [story-03-browser-history-readers.md](./story-03-browser-history-readers.md) | pending |
| HS-8-04 | Work entity extractors | backlog | [story-04-work-entity-extractors.md](./story-04-work-entity-extractors.md) | pending |
| HS-8-05 | Project activity linking and surface | backlog | [story-05-project-activity-surface.md](./story-05-project-activity-surface.md) | pending |
| HS-8-06 | Privacy controls and retention | backlog | [story-06-privacy-controls.md](./story-06-privacy-controls.md) | pending |
| HS-8-07 | DoD sweep + phase exit | backlog | [story-07-dod.md](./story-07-dod.md) | pending |

## Where We Are

Phase 8 is open. The first story is intentionally an audit because
browser history storage is platform- and permission-sensitive. Before
writing ingestion code, HS-8-01 should map Safari and Firefox paths,
schema expectations, lock/copy behavior, and the privacy contract the
runtime must enforce.

## Initial Hypothesis

The strongest value loop is:

1. User opts into local activity intelligence.
2. HoldSpeak imports browser history metadata from Safari/Firefox,
   read-only, via a safe temporary copy.
3. HoldSpeak normalizes recently viewed work objects into a local ledger.
4. `/history`, `/dictation`, and handoff exports can reference recent
   Jira tickets, Miro boards, PRs, docs, and project URLs without network
   calls or external publishing.
