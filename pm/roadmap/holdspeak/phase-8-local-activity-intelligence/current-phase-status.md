# Phase 8 - Local Activity Intelligence

**Last updated:** 2026-04-26 (HS-8-01 done - Safari/Firefox source audit completed with safe copy strategy and privacy contract).

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
remaining local, enabled by default, inspectable, pausable, and
deletable.

## Scope

- **In:**
  - Default-enabled browser-history source plugin for Safari and Firefox
    when source databases are available and readable.
  - Read-only ingestion using safe database-copy strategies.
  - Local persistence for normalized activity records.
  - Entity extraction for Jira, Miro, GitHub, Linear, Confluence/Atlassian
    pages, Google Docs/Drive, Notion, and generic domains.
  - Project-linking rules and recent activity surfaces.
  - Privacy controls: visible enabled/paused state, pause, clear imported
    activity, allowlist/denylist, retention, and exact-data visibility.
- **Out:**
  - Scraping page contents or browser cookies.
  - Reading credentials, form contents, or private browsing windows.
  - Network calls to Jira/Miro/GitHub/etc.
  - Automatic external task creation.
  - Hidden collection. The feature may be enabled by default for this
    personal local tool, but it must be visible, local-only, pausable,
    and deletable.

## Story Status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HS-8-01 | Browser history source audit | done | [story-01-browser-history-source-audit.md](./story-01-browser-history-source-audit.md) | [evidence-story-01.md](./evidence-story-01.md) |
| HS-8-02 | Activity ledger persistence | backlog | [story-02-activity-ledger-persistence.md](./story-02-activity-ledger-persistence.md) | pending |
| HS-8-03 | Safari and Firefox history readers | backlog | [story-03-browser-history-readers.md](./story-03-browser-history-readers.md) | pending |
| HS-8-04 | Work entity extractors | backlog | [story-04-work-entity-extractors.md](./story-04-work-entity-extractors.md) | pending |
| HS-8-05 | Project activity linking and surface | backlog | [story-05-project-activity-surface.md](./story-05-project-activity-surface.md) | pending |
| HS-8-06 | Privacy controls and retention | backlog | [story-06-privacy-controls.md](./story-06-privacy-controls.md) | pending |
| HS-8-07 | DoD sweep + phase exit | backlog | [story-07-dod.md](./story-07-dod.md) | pending |

## Where We Are

Phase 8 has completed its source audit. HS-8-01 confirmed Safari history
is available locally as a WAL-mode SQLite database under
`~/Library/Safari/History.db`, with URL metadata in `history_items` and
visit/title metadata in `history_visits`. Firefox is not installed in the
standard local profile locations on this machine, so HS-8-03 must use
fixture `places.sqlite` databases to confirm exact columns while
targeting Mozilla Places' `moz_places` plus `moz_historyvisits` model.

The next story should add the local activity ledger persistence and
checkpoint primitives before any browser reader imports real data.

## Initial Hypothesis

The strongest value loop is:

1. HoldSpeak starts local activity intelligence by default when browser
   history sources are available.
2. HoldSpeak imports browser history metadata from Safari/Firefox,
   read-only, via a safe temporary copy.
3. HoldSpeak normalizes recently viewed work objects into a local ledger.
4. `/history`, `/dictation`, and handoff exports can reference recent
   Jira tickets, Miro boards, PRs, docs, and project URLs without network
   calls or external publishing.
