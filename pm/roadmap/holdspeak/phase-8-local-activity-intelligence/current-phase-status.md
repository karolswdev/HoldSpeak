# Phase 8 - Local Activity Intelligence

**Last updated:** 2026-04-26 (HS-8-06 done - visible activity privacy controls and retention shipped).

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
| HS-8-02 | Activity ledger persistence | done | [story-02-activity-ledger-persistence.md](./story-02-activity-ledger-persistence.md) | [evidence-story-02.md](./evidence-story-02.md) |
| HS-8-03 | Safari and Firefox history readers | done | [story-03-browser-history-readers.md](./story-03-browser-history-readers.md) | [evidence-story-03.md](./evidence-story-03.md) |
| HS-8-04 | Work entity extractors | done | [story-04-work-entity-extractors.md](./story-04-work-entity-extractors.md) | [evidence-story-04.md](./evidence-story-04.md) |
| HS-8-05 | Shared activity context for plugins | done | [story-05-project-activity-surface.md](./story-05-project-activity-surface.md) | [evidence-story-05.md](./evidence-story-05.md) |
| HS-8-06 | Privacy controls and retention | done | [story-06-privacy-controls.md](./story-06-privacy-controls.md) | [evidence-story-06.md](./evidence-story-06.md) |
| HS-8-07 | DoD sweep + phase exit | backlog | [story-07-dod.md](./story-07-dod.md) | pending |

## Where We Are

Phase 8 has completed its source audit, local ledger foundation, and
first browser-history readers. HS-8-01 confirmed Safari history is
available locally as a WAL-mode SQLite database under
`~/Library/Safari/History.db`, with URL metadata in `history_items` and
visit/title metadata in `history_visits`. Firefox is not installed in
the standard local profile locations on this machine, so HS-8-03 used
fixture `places.sqlite` databases to validate the expected Mozilla
Places-style `moz_places` plus `moz_historyvisits` model.

HS-8-02 added normalized `activity_records` persistence, per-source
`activity_import_checkpoints`, deduplication by normalized URL or
extracted entity, raw source timestamp retention, and deletion primitives
for clear/retention controls. HS-8-03 added default-enabled local source
discovery, read-only temp-copy imports for Safari and Firefox, WAL/SHM
companion copying, browser timestamp normalization, checkpoint-based
incremental imports, and fixture coverage.

HS-8-04 added deterministic work-entity extraction and wired it into the
browser-history importer. Imported records can now identify Jira tickets,
Miro boards, GitHub PRs/issues, Linear issues, Confluence pages, Google
Docs/Sheets/Drive files, Notion pages, or a generic domain fallback
without any network calls.

HS-8-05 promoted the ledger into a shared plugin data source. Hosted MIR
plugins can receive `context["activity"]` through `PluginHost` context
providers, web runtime registers the activity provider by default, and
dictation transducers have an `Utterance.activity` field with the same
bundle shape.

HS-8-06 added the trust layer around that active data source: `/activity`
browser surface, status/records/settings/refresh/domain/clear APIs,
default-enabled privacy settings, pause/resume, retention days, domain
exclusions, source/checkpoint visibility, and importer enforcement.

The remaining Phase 8 work is the DoD sweep: verify the end-to-end
activity loop, document the final behavior, and decide whether project
mapping needs a follow-up phase or can remain a next enhancement.

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
