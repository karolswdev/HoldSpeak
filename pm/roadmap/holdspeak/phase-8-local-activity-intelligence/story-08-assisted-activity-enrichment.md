# HS-8-08 - Assisted activity enrichment sources

- **Project:** holdspeak
- **Phase:** 8
- **Status:** backlog
- **Depends on:** HS-8-05, HS-8-06, HS-8-07
- **Unblocks:** richer local intelligence from calendar, browser, and local CLIs
- **Owner:** unassigned

## Problem

Browser history metadata is a strong default source, but some useful work
signals are not reliably available from history alone. HoldSpeak should
have a principled enrichment framework for optional local helpers:
calendar metadata, a Firefox browser extension, and authenticated local
CLIs such as `gh` and `jira`.

The goal is not to scrape everything. The goal is to selectively enrich
the Local Attention Ledger when a user-visible source is enabled and when
the enrichment materially improves meeting scheduling, handoffs,
dictation context, or project activity mapping.

## Design

Add an "assisted enrichment" layer with connector contracts. Each
connector reads from one local/user-authorized source and emits normalized
activity records, activity annotations, or scheduling hints.

### Connector Contract

Each connector should expose:

- `id`
- `label`
- `enabled`
- `source_kind`
- `capabilities`
- `last_run_at`
- `last_error`
- `discover()`
- `preview()`
- `import_or_enrich()`

Connector output must be local, structured, and auditable:

- new activity records, or
- annotations linked to existing activity records, or
- scheduling hints linked to calendar events.

### Outlook / Calendar Connector

Purpose: detect upcoming/active meetings and schedule meeting recording
without relying only on manual start.

Candidate sources:

- local calendar database or exported calendar data where available
- Outlook web activity matches in the ledger
- macOS Calendar/EventKit bridge in a later implementation if needed
- Microsoft Graph only as a separate explicit opt-in story, not default

First implementation should prefer local metadata and browser activity:

- detect Outlook calendar URLs and meeting detail pages
- extract meeting title/time when present in URL/title metadata
- create local "meeting candidate" records
- expose candidates in the web runtime with manual "start/arm recording"
  action

Hard boundary: no email scraping, no hidden cloud calls, no automatic
meeting join, and no automatic recording without visible user control.

### Firefox Extension Connector

Purpose: improve parsing when browser history cannot safely provide
enough metadata.

Why Firefox first:

- Development and local installation workflow is more practical for this
  personal tool than Safari's extension distribution/signing path.
- WebExtension APIs can capture tab URL/title changes in a transparent
  opt-in extension.

Proposed extension behavior:

- local-only companion extension
- captures active tab URL/title/domain and timestamp
- optional page-specific extractors for Jira, GitHub, Miro, Outlook,
  Google Docs, Notion, and Confluence
- sends events only to a localhost HoldSpeak endpoint
- visibly paused/active in `/activity`
- never sends cookies, page body, credentials, form values, or private
  browsing data

This extension should be optional. Safari/Firefox SQLite history remains
the base ingestion path.

### Local CLI Enrichment

Purpose: use already-authenticated developer CLIs to enrich known work
objects without adding new auth handling to HoldSpeak.

Candidate helpers:

- `gh` for GitHub PR/issue title, state, labels, reviewers, and linked
  branch metadata
- `jira` for Jira issue title, status, assignee, sprint, labels, and
  project metadata

Rules:

- disabled by default until surfaced in `/activity`
- command path and availability shown before use
- dry-run/preview first
- timeouts and output-size caps
- no writes to external systems in this phase
- enrichment results stored as local annotations, not as hidden remote
  sync state

### Safety Model

- Base ledger remains local and default-enabled.
- Assisted connectors are visible and individually toggleable.
- Any connector that can trigger network via a local CLI must be clearly
  marked as such and run only after user enablement.
- All connector results are inspectable and deletable.
- No connector may read cookies, credentials, form contents, private
  browsing windows, or page bodies by default.

## Scope

- **In:**
  - Connector contract and registry design.
  - Activity annotation schema design.
  - Outlook/calendar candidate design.
  - Firefox extension companion design.
  - `gh`/`jira` CLI enrichment design.
  - Risk/permission matrix in PMO evidence.
- **Out:**
  - Shipping a browser extension.
  - Calling Microsoft Graph.
  - Automatically joining or recording meetings.
  - External writes to Jira/GitHub.
  - Reading cookies, credentials, email contents, or page bodies.

## Acceptance Criteria

- [ ] Assisted enrichment connector contract is documented.
- [ ] Calendar/Outlook meeting-candidate flow is scoped.
- [ ] Firefox extension companion architecture is scoped.
- [ ] `gh`/`jira` CLI enrichment boundaries are scoped.
- [ ] Permission and privacy matrix exists.
- [ ] Follow-up implementation stories are identified.

## Test Plan

- Design review against Phase 8 privacy boundaries.
- PMO evidence with connector contract examples.
- No production code required unless a narrow scaffold is chosen during
  implementation.
