# Local Activity Assisted Enrichment Plan

## 1. Objective

Phase 8's base Local Attention Ledger is browser-history metadata:
default-on, local, visible, pausable, and deletable. Assisted enrichment
adds optional sources that can make the ledger more useful without
turning it into hidden surveillance.

The assisted layer is explicitly opt-in per connector. It may add:

- new activity records from local/user-authorized sources
- annotations attached to existing activity records
- meeting scheduling hints surfaced for manual action

It must not add hidden cloud calls, scrape page bodies, read cookies or
credentials, inspect private browsing, or automatically join or record a
meeting.

## 2. Connector Contract

Each connector is a small, auditable adapter with one source boundary.

```python
@dataclass(frozen=True)
class ActivityEnrichmentConnector:
    id: str
    label: str
    enabled: bool
    source_kind: str
    capabilities: tuple[str, ...]
    last_run_at: datetime | None
    last_error: str | None

    def discover(self) -> ConnectorDiscovery: ...
    def preview(self, limit: int = 50) -> ConnectorPreview: ...
    def import_or_enrich(self, limit: int = 100) -> ConnectorRunResult: ...
```

Required result shapes:

```python
@dataclass(frozen=True)
class ActivityAnnotationCandidate:
    activity_record_id: int | None
    entity_type: str | None
    entity_id: str | None
    annotation_type: str
    title: str
    value: dict[str, Any]
    confidence: float
    source_connector_id: str


@dataclass(frozen=True)
class MeetingCandidate:
    title: str
    starts_at: datetime | None
    ends_at: datetime | None
    meeting_url: str | None
    source_activity_record_id: int | None
    source_connector_id: str
    confidence: float
```

The registry should expose connector state in `/activity`:

- connector ID and label
- enabled/disabled state
- source availability
- capability list
- last run time and last error
- preview count before import/enrich
- clear/delete controls for connector output

## 3. Local Storage Design

HS-8-08 does not ship schema, but the first implementation story should
add local tables shaped like this.

```sql
CREATE TABLE activity_enrichment_connectors (
    id TEXT PRIMARY KEY,
    enabled INTEGER NOT NULL DEFAULT 0,
    settings_json TEXT NOT NULL DEFAULT '{}',
    last_run_at TEXT,
    last_error TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE activity_annotations (
    id TEXT PRIMARY KEY,
    activity_record_id INTEGER REFERENCES activity_records(id) ON DELETE CASCADE,
    source_connector_id TEXT NOT NULL,
    annotation_type TEXT NOT NULL,
    title TEXT NOT NULL DEFAULT '',
    value_json TEXT NOT NULL DEFAULT '{}',
    confidence REAL NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX idx_activity_annotations_record
ON activity_annotations(activity_record_id, annotation_type);
CREATE INDEX idx_activity_annotations_connector
ON activity_annotations(source_connector_id, created_at DESC);

CREATE TABLE activity_meeting_candidates (
    id TEXT PRIMARY KEY,
    source_connector_id TEXT NOT NULL,
    source_activity_record_id INTEGER REFERENCES activity_records(id) ON DELETE SET NULL,
    title TEXT NOT NULL,
    starts_at TEXT,
    ends_at TEXT,
    meeting_url TEXT,
    confidence REAL NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'candidate',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX idx_activity_meeting_candidates_time
ON activity_meeting_candidates(starts_at, status);
```

`status` values for meeting candidates should start with:

- `candidate`
- `armed`
- `dismissed`
- `started`

Only explicit user action may move a candidate to `armed` or `started`.

## 4. Calendar and Outlook Candidate Flow

First slice: derive meeting candidates from local browser activity and
visible calendar URL/title metadata.

Inputs:

- Outlook calendar URLs already in `activity_records`
- Google Calendar URLs already in `activity_records`
- browser titles that include meeting names or calendar event hints
- later: local calendar export files or macOS EventKit bridge

Flow:

1. Connector discovers whether relevant calendar domains exist in the
   ledger.
2. Preview extracts candidates from recent records without writing.
3. Import stores `activity_meeting_candidates`.
4. `/activity` or runtime dashboard shows candidate title, source, time
   when available, and confidence.
5. User manually chooses "arm recording" or "start recording."

Boundaries:

- no email scraping
- no Microsoft Graph in this phase
- no hidden cloud calls
- no automatic meeting join
- no automatic recording
- no reading calendar databases unless the path and source are visible

## 5. Firefox Companion Extension

Firefox is the first browser extension target because WebExtension
development and local installation are straightforward compared with
Safari extension signing and distribution.

Extension behavior:

- disabled unless user installs and enables it
- captures active tab URL, title, domain, timestamp, and window focus
- optionally captures structured IDs already present in URL/title
- POSTs events only to a loopback HoldSpeak endpoint
- shows paused/active state in both the extension and `/activity`
- does not run in private windows
- does not capture cookies, credentials, page body, form values, or
  screenshots

Local endpoint shape:

```http
POST /api/activity/extension-events
Content-Type: application/json

{
  "source": "firefox_extension",
  "url": "https://github.com/openai/codex/pull/123",
  "title": "Fix activity mapping by contributor",
  "observed_at": "2026-04-27T10:15:00",
  "active": true
}
```

The server should normalize extension events into the same
`activity_records` path used by browser history import, including entity
extraction and project mapping rules.

## 6. Local CLI Enrichment

CLI connectors use tools the user has already authenticated locally.
They do not store new secrets in HoldSpeak.

Candidate connectors:

- `gh`: enrich GitHub PRs/issues with title, state, labels, reviewers,
  branch, and merged status.
- `jira`: enrich Jira tickets with title, status, assignee, sprint,
  labels, and project metadata.

Rules:

- disabled by default
- show command path and availability before use
- preview before writing annotations
- run with short timeouts
- cap stdout/stderr bytes
- parse structured JSON output where available
- never run write commands in Phase 8
- store results as local annotations

Example `gh` command policy:

```text
Allowed:
gh pr view OWNER/REPO#NUMBER --json title,state,labels,reviewRequests,headRefName,mergedAt
gh issue view OWNER/REPO#NUMBER --json title,state,labels,assignees

Forbidden:
gh pr edit
gh issue edit
gh api --method POST|PATCH|PUT|DELETE
```

Example `jira` command policy:

```text
Allowed:
jira issue view KEY --plain
jira issue view KEY --json

Forbidden:
jira issue create
jira issue edit
jira issue transition
```

## 7. Permission and Privacy Matrix

| Source | Default | May Network | Reads Secrets | Writes External | Stored Output | User Control |
|---|---|---:|---:|---:|---|---|
| Safari/Firefox history DB | enabled | no | no | no | activity records | pause, delete, retention, domain exclude |
| Project mapping rules | user-authored | no | no | no | `project_id` on records | create, preview, apply, disable, delete |
| Calendar/Outlook from ledger | disabled | no | no | no | meeting candidates | enable, preview, dismiss, delete |
| Local calendar export | disabled | no | no | no | meeting candidates | explicit file/source selection |
| Firefox extension | disabled | loopback only | no | no | activity records | install, enable, pause, delete |
| `gh` CLI | disabled | yes | CLI-managed only | no | annotations | enable, preview, timeout, delete |
| `jira` CLI | disabled | yes | CLI-managed only | no | annotations | enable, preview, timeout, delete |
| Microsoft Graph | out of scope | yes | OAuth token | no | TBD | separate story only |

## 8. Follow-Up Stories

Recommended implementation sequence:

1. `HS-9-01`: Activity enrichment connector registry and annotation
   persistence.
2. `HS-9-02`: Calendar/Outlook meeting candidates from existing local
   activity records.
3. `HS-9-03`: Firefox companion extension event endpoint and local
   installation guide.
4. `HS-9-04`: `gh` CLI enrichment preview and annotations for GitHub
   PRs/issues.
5. `HS-9-05`: `jira` CLI enrichment preview and annotations for Jira
   tickets.
6. `HS-9-06`: Assisted enrichment privacy controls, deletion, and phase
   exit.

Do not implement Microsoft Graph until a later explicit opt-in phase
defines OAuth storage, revocation, and threat model.
