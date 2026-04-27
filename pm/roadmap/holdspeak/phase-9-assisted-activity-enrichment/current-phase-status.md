# Phase 9 - Assisted Activity Enrichment

**Last updated:** 2026-04-27 (HS-9-11 activity dashboard polish shipped).

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
| HS-9-09 | Meeting candidate dedupe and time hints | done | [story-09-candidate-dedupe-time-hints.md](./story-09-candidate-dedupe-time-hints.md) | [evidence-story-09.md](./evidence-story-09.md) |
| HS-9-10 | Meeting candidate recording workflow | done | [story-10-candidate-recording-workflow.md](./story-10-candidate-recording-workflow.md) | [evidence-story-10.md](./evidence-story-10.md) |
| HS-9-11 | Activity dashboard polish | done | [story-11-activity-dashboard-polish.md](./story-11-activity-dashboard-polish.md) | [evidence-story-11.md](./evidence-story-11.md) |
| HS-9-12 | Connector controls and output deletion | backlog | [story-12-connector-controls-output-deletion.md](./story-12-connector-controls-output-deletion.md) | pending |
| HS-9-13 | Connector dry-run harness | backlog | [story-13-connector-dry-run-harness.md](./story-13-connector-dry-run-harness.md) | pending |

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

The next polishing work is now explicitly scoped. HS-9-09 makes candidate
results less noisy through dedupe and simple time hints. HS-9-10 connects
armed candidates to a visible recording workflow. HS-9-11 improves the
`/activity` user experience around empty states, saved/previewed
candidates, and repeated actions. HS-9-12 adds connector-level controls
and output deletion. HS-9-13 adds a dry-run harness so connector behavior
can be tested without mutating the ledger.

HS-9-09 shipped candidate dedupe and simple visible time hints. Repeated
saves from the same connector/source record now merge into one candidate,
preserving armed/dismissed status where appropriate, and local titles/URLs
with `YYYY-MM-DD HH:MM[-HH:MM]` text can populate start/end hints.

HS-9-10 shipped the first visible candidate-to-recording workflow. Saved
meeting candidates can now be manually started from `/activity`, use the
normal runtime start hook, carry the candidate title into the meeting where
the runtime supports meeting updates, and persist the started meeting ID
back onto the candidate row.

HS-9-11 made `/activity` more dogfoodable: empty states now describe the
next local action, candidate previews and saved candidates are visually
distinct, saved candidates can be filtered by status, repeated async
submits are guarded, and panel-specific messages keep errors close to the
controls that triggered them.

## Source Design

- `docs/PLAN_ACTIVITY_ASSISTED_ENRICHMENT.md`
