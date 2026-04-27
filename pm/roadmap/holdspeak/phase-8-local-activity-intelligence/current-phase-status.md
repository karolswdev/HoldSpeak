# Phase 8 - Local Activity Intelligence

**Last updated:** 2026-04-27 (HS-8-08 assisted enrichment sources scoped).

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

The ledger should also become the stable substrate for optional assisted
enrichment. Browser history remains the default source, while explicit
user-enabled helpers such as project mapping rules, calendar/Outlook
parsing, a Firefox companion extension, or local developer CLIs may add
more structure without hiding collection or bypassing local controls.

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
  - User-authored activity-to-project mapping rules.
  - Assisted enrichment design for calendar/Outlook candidates, optional
    Firefox extension capture, and local `gh`/`jira` CLI lookups.
- **Out:**
  - Scraping page contents or browser cookies.
  - Reading credentials, form contents, or private browsing windows.
  - Hidden network calls to Jira/Miro/GitHub/etc.
  - Automatic external task creation.
  - Automatic meeting join or recording without visible user control.
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
| HS-8-07 | Project activity mapping rules | done | [story-07-project-activity-mapping-rules.md](./story-07-project-activity-mapping-rules.md) | [evidence-story-07.md](./evidence-story-07.md) |
| HS-8-08 | Assisted activity enrichment sources | done | [story-08-assisted-activity-enrichment.md](./story-08-assisted-activity-enrichment.md) | [evidence-story-08.md](./evidence-story-08.md) |
| HS-8-09 | DoD sweep + phase exit | backlog | [story-09-dod.md](./story-09-dod.md) | pending |

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

HS-8-07 added deterministic project activity mapping rules. Users can
create, edit, disable, delete, preview, and apply rules from `/activity`.
The DB stores priority-ordered rules, existing records can be backfilled
to `activity_records.project_id`, and future imports assign projects
after entity extraction without network calls or hidden enrichment.

HS-8-08 scoped richer optional sources in
`docs/PLAN_ACTIVITY_ASSISTED_ENRICHMENT.md`: a connector contract,
activity annotation and meeting-candidate storage design,
Calendar/Outlook candidate flow, Firefox companion extension architecture,
local `gh`/`jira` CLI enrichment boundaries, and a permission/privacy
matrix. The next Phase 8 step is HS-8-09: evidence, regression, and phase
exit.

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
