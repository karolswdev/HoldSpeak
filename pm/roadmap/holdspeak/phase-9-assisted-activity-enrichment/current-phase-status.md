# Phase 9 - Assisted Activity Enrichment

**Last updated:** 2026-04-27 (HS-9-08 meeting candidate browser controls shipped).

## Goal

Build the optional assisted-enrichment layer designed in Phase 8. The
base Local Attention Ledger remains local and default-enabled. Phase 9
adds explicit, visible, user-controlled connectors that can add local
annotations, meeting candidates, extension events, and CLI-derived
metadata without hidden collection or external writes.

## Scope

- **In:**
  - Connector registry and local connector state.
  - Local activity annotations linked to records or entities.
  - Calendar/Outlook meeting candidates from existing local activity.
  - Firefox companion extension event ingestion through loopback.
  - `gh` and `jira` CLI preview/enrichment with timeouts and output caps.
  - Connector privacy controls and deletion.
- **Out:**
  - Microsoft Graph or OAuth.
  - Browser extension store distribution.
  - Automatic meeting join or recording without visible user action.
  - External writes to Jira/GitHub.
  - Cookies, credentials, page bodies, form contents, screenshots, or
    private browsing data.

## Story Status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HS-9-01 | Connector registry and annotation persistence | done | [story-01-connector-registry-annotations.md](./story-01-connector-registry-annotations.md) | [evidence-story-01.md](./evidence-story-01.md) |
| HS-9-02 | Calendar and Outlook meeting candidates | done | [story-02-calendar-outlook-candidates.md](./story-02-calendar-outlook-candidates.md) | [evidence-story-02.md](./evidence-story-02.md) |
| HS-9-03 | Firefox companion extension events | backlog | [story-03-firefox-extension-events.md](./story-03-firefox-extension-events.md) | pending |
| HS-9-04 | GitHub CLI enrichment annotations | backlog | [story-04-gh-cli-enrichment.md](./story-04-gh-cli-enrichment.md) | pending |
| HS-9-05 | Jira CLI enrichment annotations | backlog | [story-05-jira-cli-enrichment.md](./story-05-jira-cli-enrichment.md) | pending |
| HS-9-06 | Assisted enrichment controls + phase exit | backlog | [story-06-controls-dod.md](./story-06-controls-dod.md) | pending |
| HS-9-07 | Meeting candidate API surface | done | [story-07-meeting-candidate-api.md](./story-07-meeting-candidate-api.md) | [evidence-story-07.md](./evidence-story-07.md) |
| HS-9-08 | Meeting candidate browser controls | done | [story-08-meeting-candidate-browser-controls.md](./story-08-meeting-candidate-browser-controls.md) | [evidence-story-08.md](./evidence-story-08.md) |

## Where We Are

Phase 9 has started with HS-9-01. The local database now stores optional
connector state and local activity annotations. This gives future
connectors a durable place to record enablement, settings, last run
status, and structured enrichment output without adding network behavior
or new credential handling.

HS-9-02 added local meeting-candidate persistence and deterministic
candidate previews from existing calendar-related activity records. The
preview path recognizes Outlook, Microsoft Teams, Google Calendar, and
Google Meet domains from already-imported local activity metadata and
does not introduce network calls.

HS-9-07 made those candidates directly testable through the local web API:
preview, persist, list, update status, and delete. The API stays local to
existing ledger data and does not introduce cloud calls or automatic
recording.

HS-9-08 added browser controls to `/activity` for the same candidate
workflow: preview candidates from local activity, save a candidate,
refresh saved candidates, arm/dismiss/reset status, and clear dismissed
candidates.

## Source Design

- `docs/PLAN_ACTIVITY_ASSISTED_ENRICHMENT.md`
