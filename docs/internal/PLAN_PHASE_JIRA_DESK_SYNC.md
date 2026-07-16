# Phase JDS-01: JIRA Desk Sync (pull reports as Desk primitives)

## 1. Phase Charter

### 1.1 Objective

Add a read-only **desk-sync** connector that, after the operator configures a
JIRA base URL and credentials, pulls a named JQL report from JIRA (Cloud or
self-hosted Data Center) and materializes the result as real Desk primitives:
one Note per issue, grouped into a KB per report. The Desk's existing spatial
diorama then renders those reports and issues as the warm hand-drawn objects it
already knows how to draw. No new primitive type, no new rendering surface, no
new side-effect path. The capability is the connector framework's first
**external-to-Desk sink**: every connector today writes to the activity ledger;
this one writes to the primitive store.

The lead use case is the operator's: pull "To Do" and "In Progress" lanes for
the current user so they sit on the Desk next to meetings, notes, and agents,
ready to be opened in JIRA, annotated, or grounded into a run.

### 1.2 Why This Phase Exists

HoldSpeak already ships a JIRA connector (`holdspeak/connector_packs/jira_cli.py`
+ `holdspeak/activity_jira.py`), but it is narrow on three axes:

1. It runs `jira issue view KEY --plain` against tickets **already referenced**
   in local activity. It cannot run a JQL report; it can only enrich tickets the
   ledger already names.
2. Its output is `activity_annotations` rows attached to `activity_records`. It
   never reaches the Desk, the primitive store, or anything the operator
   arranges, files, or dives into.
3. It is CLI-mediated (`shell:exec` against the operator's `jira` binary) and
   carries no credentials of its own. The operator's ask here is the REST shape:
   base URL + API token, polled on a cadence, surfaced as Desk material.

So the gap is real and specific: nothing sinks external data **into Desk
primitives**, and no connector speaks REST with its own credentials. JDS-01
fills both with the smallest extension that does the job honestly.

### 1.3 Success Criteria (Phase-Level)

1. A configured desk-sync connector pulls a JQL report from a real JIRA
   instance (Cloud or DC) and writes one Note per returned issue, plus one KB
   holding the report's issue-notes as members.
2. A second pull of the same report is idempotent: notes are updated in place,
   vanished issues are tombstoned, the KB membership reflects the current
   result set. No duplicate rows, no orphaned notes.
3. Synced notes carry provenance (source connector + external id + etag +
   last-synced timestamp) and are read-only on the Desk until the operator
   detaches them.
4. The connector is off by default, gated by `network:outbound`, pins egress to
   the configured host, and stores no credentials in the DB.
5. Every Desk object produced wears the honest egress badge (`cloud · <host>`)
   and a "refreshed N min ago" line, never a reassurance sentence.
6. Verification evidence is complete and reproducible against a fake gate and a
   fake HTTP opener, with no real network in the test suite.

### 1.4 Scope Decision: REST First, CLI Later

The operator asked for "API key, JIRA Base URL" configuration. JDS-01 commits to
the REST path (`/rest/api/2/search`) as the lead and only shippable transport.
The existing `jira` CLI pack is untouched and remains the lighter alternative
for operators who already run `jira auth login`. A future CLI-backed desk-sync
variant is a JDS-02 candidate; it is not blocked by this design but is not
built here.

## 2. Normative Language

`MUST`, `SHOULD`, `MAY` per RFC 2119, matching the convention of
`PLAN_PHASE_MULTI_INTENT_ROUTING.md` and `PLAN_PHASE_DICTATION_INTENT_ROUTING.md`.

## 3. Scope and Non-Scope

### 3.1 In Scope

1. New connector kind `desk_sync` and new capability `desk_primitives` in the
   connector SDK, with the `Enrich` protocol routed into the primitive repos.
2. First-party pack `holdspeak/connector_packs/jira_desk_sync.py`: REST
   `/search` via a gated, host-pinned HTTP opener (injectable for tests), JQL
   report config, `statusCategory` lane grouping, idempotent Note upsert + KB
   maintenance.
3. Provenance sidecar table `primitive_sources` and a "detach to own" path that
   turns a synced note into a normal editable note, frozen at its last pull.
4. Read-only enforcement on synced note bodies (the Desk refuses body edits
   while provenance is live).
5. Two secrets (`jira_email`, `jira_api_token`) wired into the secret store,
   plus `base_url` and report config in connector settings.
6. Desk surface treatment for synced objects: the egress badge, the
   "refreshed" timestamp, the read-only indicator, and a manual refresh
   control. No new primitive type and no new Desk renderer.
7. Doctor check that flags a configured-but-unreachable JIRA host.
8. A `Preview` (`dry_run: true`) path that returns the planned notes without
   writing, reusing the existing dry-run harness shape.

### 3.2 Out of Scope

1. **Write-back to JIRA.** Transitioning an issue, commenting, or creating an
   issue is a *write* side effect. It rides the existing `gated_connector` +
   actuator framework as a later `jira_issue_actuator` sibling of
   `github_issue_actuator` (see §9). JDS-01 is pull-only and needs only the
   `PermissionGate`, never the propose-approve-execute gate.
2. **A new "task" primitive type.** A JIRA issue maps cleanly onto a Note for
   the "what is on my plate" view. Full fidelity (comments, transitions,
   attachments, change history) is the argument for a dedicated primitive; it
   is a later phase if the lossy mapping bites in real use. Custom fields, by
   contrast, ARE in scope (§7.6) — the `ticketr` reference (§18) proves they
   round-trip with a field-mapping config.
3. **Webhooks / near-real-time sync.** A pull avoids exposing a loopback
   listener (a heavier trust step) and fits the existing `Enrich` +
   `pipeline_freshness_seconds` cadence. Webhooks need public ingress and fight
   the local-first posture.
4. **Multi-report packs with a typed list-of-objects setting.** The current
   `settings_schema` is a flat list of scalars. JDS-01 ships one pack instance
   per report (or a JSON-string `reports` setting parsed by the pack) and
   defers the cleaner typed-list SDK extension to JDS-02.
5. **JIRA Agile (board/sprint) and Service Management APIs.** Only the
   platform `/rest/api/2/search` issue endpoint is in scope. Sprint and board
   fields ride as best-effort tags when present on the issue (the sprint custom
   field is a string the pack reads as-is).
6. **OAuth.** API-token (Cloud) and PAT (DC) Basic auth cover the ask. OAuth
   adds a token-refresh and revocation surface that is its own story.
7. **Subtask fetching (N+1).** The reference `ticketr` adapter fetches
   subtasks with a separate `parent = "KEY"` JQL per parent — an N+1 pattern
   that does not scale past a handful of parents. JDS-01 fetches parent issues
   only; subtasks appear as a count tag (`jira-subtasks:N`) and a deep link, not
   as separate Desk objects. A batched subtask fetch (one JQL with `parent in
   (KEY1, KEY2, …)`) is a JDS-02 candidate.

## 4. Relationship to Existing Plans and Code

1. **Parent RFC:** `docs/internal/PLAN_ARCHITECT_PLUGIN_SYSTEM.md` defines the
   plugin taxonomy and capability model. JDS-01 extends the **connector**
   ecosystem (the activity-enrichment lineage below), not the meeting-plugin
   taxonomy; the two are distinct substrates and must not be conflated.
2. **Sibling plan:** `docs/internal/PLAN_ACTIVITY_ASSISTED_ENRICHMENT.md` is the
   connector contract canon. Its §6 names the existing `jira` CLI pack and its
   read-only command policy. JDS-01 adds a second JIRA connector with a
   different destination (Desk primitives, not activity annotations) and a
   different transport (REST, not CLI). The two are complementary and ship side
   by side; their ids (`jira` vs `jira_desk_sync`) do not collide.
3. **Connector SDK:** `holdspeak/connector_sdk.py` (`KNOWN_KINDS`,
   `KNOWN_CAPABILITIES`, `KNOWN_PERMISSIONS`, `ConnectorManifest`,
   `validate_manifest`, the `Discover`/`Preview`/`Enrich`/`Clear` protocols).
   JDS-01 adds one kind, one capability, one permission.
4. **Connector runtime:** `holdspeak/connector_runtime.py` (`PermissionGate`,
   `_OPERATION_PERMISSIONS`). The REST call routes through
   `PermissionGate.open_outbound_socket`, which enforces `network:outbound`.
5. **Pack loader:** `holdspeak/connector_pack_loader.py` (`build_registry`).
   The new pack is first-party and registers alongside `jira_cli`.
6. **Primitive repos:** `holdspeak/db/primitives.py` (`NoteRepository`,
   `KBRepository`, `DirectoryRepository`). Synced notes and report-KBs are
   ordinary rows in these repos; the provenance sidecar is the only addition.
7. **Gated write connectors:** `holdspeak/plugins/gated_connector.py` and
   `holdspeak/plugins/builtin/github_issue_actuator.py`. JDS-01 is read-only and
   does **not** use `build_gated_connector` (that seam is for writes the
   `ActuatorExecutor` injects). The write-back future (§9) does.
8. **Secret store:** `holdspeak/web/routes/system/settings_secrets.py`
   (`SECRET_PATHS`, `redacted_settings`). The JIRA token follows the same rule
   as a RuntimeProfile key: stored in the secret store, joined at request time,
   never persisted in the connector row.

## 5. Entry Criteria

All MUST be true before implementation begins.

1. Baseline `uv run pytest -q` passes.
2. `holdspeak doctor` reports `Web runtime: PASS` on the reference machine.
3. The connector SDK, runtime, and pack loader are importable and the existing
   `jira` and `github` first-party packs register cleanly (no discovery errors).
4. An operator has (or can create) a JIRA Cloud or Data Center instance with an
   API token or PAT for at least one live verification run. Unit and integration
   tests do not require this; they use a fake opener.

## 6. Architecture Delta

### 6.1 Pull Topology

```
operator configures: base_url, jira_email (secret), jira_api_token (secret),
                     report_jql, poll_interval_seconds
                          │
                          ▼
connector Enrich (cadence: pipeline_freshness_seconds, off by default)
  ├── PermissionGate.open_outbound_socket((host, 443))   # network:outbound
  ├── host-pin check vs base_url host                    # refuse redirect drift
  ├── HTTPS POST /rest/api/2/search  {jql, fields, maxResults, startAt}  # Basic auth email:token
  ├── for each issue: NoteRepository.upsert(jira:<slug>:<KEY>, …)   # idempotent
  ├── KBRepository.upsert(report-kb-id, member_ids=[…])             # current set
  ├── tombstone notes that vanished from the result set
  └── write primitive_sources row per synced note (provenance + etag + synced_at)
                          │
                          ▼
Desk renders the report-KB and its issue-Notes as ordinary objects,
badged `cloud · <host>` with a "refreshed N min ago" line.
```

The pull is a single synchronous `Enrich` call. It is invoked on the connector
cadence (reusing `pipeline_freshness_seconds`, default 300 s) or by an explicit
manual refresh. A pull failure MUST surface as `last_error` on the connector
row and MUST NOT mutate any existing synced note to a worse state (stale data
beats no data; the "refreshed" timestamp is honest about staleness).

### 6.2 New Modules

1. `holdspeak/connector_packs/jira_desk_sync.py` — the first-party pack:
   manifest, REST opener (host-pinned, injectable), JQL fetch, issue-to-Note
   mapping, lane grouping, idempotent upsert + KB maintenance, `Preview`/`Enrich`
   /`Clear` implementations.
2. `holdspeak/db/primitive_sources.py` — the provenance sidecar repository
   (mirrors the `artifact_sources` sidecar pattern in `holdspeak/db/core.py`).

### 6.3 Modified Modules

1. `holdspeak/connector_sdk.py` — add `desk_sync` to `KNOWN_KINDS`,
   `desk_primitives` to `KNOWN_CAPABILITIES`, and `write:desk_primitives` to
   `KNOWN_PERMISSIONS`. No change to the manifest dataclass shape; the validator
   gains one cross-field rule (a `desk_sync` pack MUST declare
   `write:desk_primitives` and, because it reaches the network, MUST declare
   `network:outbound`).
2. `holdspeak/db/core.py` — add the `primitive_sources` table (schema-bumped,
   additive migration; no change to existing columns).
3. `holdspeak/web/routes/system/settings_secrets.py` — add `jira_email` and
   `jira_api_token` to `SECRET_PATHS`; the `base_url` and report config stay in
   connector settings (not secrets), so they remain visible/editable.
4. `holdspeak/web/routes/primitives/notes.py` — read-only enforcement: a PUT to
   a note with live provenance is refused with a typed 409 that frames the
   detach action. The detach endpoint (`POST /api/notes/{id}/detach`) strips the
   provenance row.
5. `holdspeak/commands/doctor.py` — a `JIRA desk-sync` check (see §10.5).
6. `holdspeak/connector_packs/__init__.py` — export the new pack in
   `ALL_PACKS`.

### 6.4 Contracts (extends `holdspeak/connector_sdk.py`)

The `Enrich` protocol already exists and "may write to the DB." JDS-01 adds no
new protocol; it adds a new *kind* and a new *capability* so the runtime can
gate desk writes distinctly from activity writes:

```python
# New KNOWN_KINDS entry:
"desk_sync"   # pulls external rows into desk primitives (Notes / KBs / Zones)

# New KNOWN_CAPABILITIES entry:
"desk_primitives"   # produces notes/kbs rows in the primitive store

# New KNOWN_PERMISSIONS entry:
"write:desk_primitives"   # write into the primitive repos (notes/kbs/...)
```

The pack's `Enrich.enrich(db, *, limit)` implementation receives the `Database`
and writes through `db.notes` / `db.kbs` / `db.primitive_sources`. The runtime
MUST confirm the connector is `enabled=True` before calling `enrich` and MUST
update `last_run_at` / `last_error` from the returned status (this is the
existing contract; no change).

### 6.5 Schema Delta (additive)

```sql
-- primitive_sources: provenance sidecar for externally-synced desk primitives.
-- Mirrors artifact_sources(artifact_id, source_type, source_ref): a separate
-- edge store so the notes/kbs tables stay user-authored-shaped and sync
-- untouched. A row present => the primitive is read-only and refreshable.
CREATE TABLE IF NOT EXISTS primitive_sources (
    primitive_id        TEXT NOT NULL,
    source_connector_id TEXT NOT NULL,
    external_id         TEXT NOT NULL,            -- e.g. "PROJ-123"
    external_etag       TEXT,                     -- JIRA "updated" or HTTP ETag
    last_synced_at      TEXT NOT NULL,
    read_only           INTEGER NOT NULL DEFAULT 1,
    PRIMARY KEY (primitive_id, source_connector_id)
);
CREATE INDEX IF NOT EXISTS idx_primitive_sources_connector
ON primitive_sources(source_connector_id, last_synced_at DESC);
```

No change to the `notes` or `kbs` tables. `last_modified` on those rows advances
on every refresh (so sync propagates to other surfaces exactly as a hand edit
would), and a tombstone (`deleted=1`) propagates a vanished issue's removal.

## 7. The JIRA REST Pull

### 7.1 Endpoint and Auth

The pack calls exactly one JIRA endpoint, using **`/rest/api/2/`** (not
`/rest/api/3/`). This is a deliberate, load-bearing decision:

- **api/2** returns `description` as a plain string and works on both JIRA
  Cloud and Jira Data Center (self-hosted). It is the stable, widely-compatible
  REST surface.
- **api/3** is Cloud-only and returns `description` as an **Atlassian Document
  Format** (ADF) document — a nested JSON structure of content nodes, not a
  string. Rendering ADF to markdown is a non-trivial parser of its own; a
  pull-only Desk view does not justify that cost. (The reference `ticketr`
  adapter, §18, uses api/2 throughout for exactly this reason.)

```
POST {base_url}/rest/api/2/search
Content-Type: application/json
Authorization: Basic <base64(email:token)>

{
  "jql": "<report_jql>",
  "fields": ["summary","status","statuscategory","assignee","priority",
            "issuetype","updated","subtasks"],
  "maxResults": 50,
  "startAt": 0
}
```

**POST, not GET.** The reference adapter and Atlassian's own guidance both use
POST for `/search`: JQL queries grow past URL length limits fast (a sprint +
assignee + status filter is already long), and POST keeps the JQL in the body.
This corrects the GET-with-query-params shape an earlier draft of this plan
specified.

Authentication is HTTP Basic with `email:api_token` (Cloud) or
`username:pat` (Data Center). The credential pair is read from the secret store
at call time and NEVER persisted in the connector row or logged. The
`Authorization` header is built inside the opener, not in the pack's plan, so
the credential string never appears in a `GatedOperation` or audit row.

`base_url` is a setting (visible). `jira_email` and `jira_api_token` are
secrets (redacted in `redacted_settings`). The host portion of `base_url` is
the egress host the pack pins (§7.4).

**Credential probe.** The doctor check (§10.5) verifies credentials with
`GET /rest/api/2/myself` — a lightweight, no-side-effect endpoint that returns
the authenticated user's account id and display name. This is cheaper and more
honest than running a JQL search as a probe: it tests auth without depending on
any project's permissions.

### 7.2 Lane Grouping (the TODO / IN-Progress shape)

JIRA's granular `status` ("Code Review", "QA", "Blocked") is per-workflow and
unstable across teams. `statusCategory` is the stable three-bucket field every
JIRA instance exposes:

| `statusCategory.key` | `statusCategory.name` | Desk lane |
|---|---|---|
| `new` | To Do | TODO |
| `ind` | In Progress | IN PROGRESS |
| `done` | Done | DONE (excluded by default JQL) |

The pack keys off `statusCategory.key` (stable) and tags each note with both the
human lane and the granular status:

```
tags = [
  "jira",
  f"jira:{project_key}",            # e.g. "jira:PROJ"
  f"jira-lane:{statusCategory.key}",   # "jira-lane:ind"
  f"jira-status:{status.name}",        # "jira-status:Code Review"
  f"jira-priority:{priority.name}",    # when present
  f"jira-subtasks:{subtask_count}",    # count, not separate objects (§3.2 #7)
]
```

A report's JQL picks the lane (e.g. `assignee = currentUser() AND statusCategory = "In Progress"`),
so one report = one lane = one KB. The operator runs two pack instances (or two
entries in the `reports` setting) for the canonical TODO + IN PROGRESS pair.

### 7.3 JIRA Response Fields are Nested Objects

A JIRA issue response is not flat. The fields the pack reads live inside
nested objects, and the extraction must reach into them. The reference `ticketr`
adapter's `parseJiraIssue` (§18) shows the real shape:

```json
{
  "key": "PROJ-123",
  "fields": {
    "summary": "Fix the login redirect loop",
    "status": { "name": "Code Review", "statusCategory": { "key": "ind", "name": "In Progress" } },
    "issuetype": { "name": "Story", "subtask": false },
    "assignee": { "displayName": "Dana Ng", "accountId": "..." },
    "priority": { "name": "High" },
    "updated": "2026-07-11T14:02:00.000+0000",
    "subtasks": [ { "key": "PROJ-124", "fields": { "summary": "..." } } ]
  }
}
```

The extraction rules:

- `status.name` for the granular status; `status.statusCategory.key` for the
  stable lane.
- `assignee.displayName` (the human name), NOT `assignee.name` (the username,
  which is deprecated/absent on Cloud). `assignee` may be `null` (unassigned).
- `priority.name`; `issuetype.name` and `issuetype.subtask`.
- `subtasks` is an array on the parent issue; the pack reads its length for the
  `jira-subtasks:N` tag and does not fetch each subtask's full fields
  (§3.2 #7).
- Custom fields (`customfield_*`) are mapped through the field-mapping config
  (§7.6), not hard-coded.

A field that is absent or `null` MUST degrade to a tag like
`jira-assignee:unassigned` or be omitted, never produce a `None` string or a
stack trace. The reference adapter's switch on the JSON value type
(string/float/array/map) is the template for this defensive extraction.

### 7.4 Egress and the Host Pin

The opener routes through `PermissionGate.open_outbound_socket((host, 443))`,
which enforces `network:outbound`. On top of the gate, the pack enforces a
**host pin**: the resolved `base_url` host is the only host the opener may
contact. If the HTTP layer follows a redirect to a different host, the opener
MUST refuse with `ConnectorOperationRefused` (reusing the type from
`gated_connector.py` for a consistent operator message) before sending the
`Authorization` header to the redirect target. This is the SSRF defense: a
misconfigured or hostile `base_url` cannot exfiltrate the credential to an
attacker host via redirect.

The opener is injectable (`opener: Callable[[Request], Response] | None`),
defaulting to the real TLS implementation in production and a fake in tests.
This mirrors the `runner`/`opener` injection in `build_gated_connector` so the
full loop is testable with no real socket.

**HTTP client timeout.** The opener MUST set a per-request timeout (default
10 s). The reference `ticketr` adapter constructs `&http.Client{}` with no
timeout (§18), which means a hung JIRA host hangs the whole pull indefinitely;
JDS-R-001 corrects this. The opener also MUST set `follow_redirect: false` (or
intercept redirects) so the host pin is enforceable at the transport layer,
not just checked after the fact.

### 7.5 Idempotency, Reconciliation, and Pagination

Each pull reconciles the report's KB to the current result set:

1. **Upsert** one Note per returned issue. The Note `id` is
   `jira:<instance-slug>:<KEY>`, where `<instance-slug>` is derived from the
   `base_url` host (e.g. `acme.atlassian.net` -> `acme`). This id is stable
   across refreshes, so the upsert is idempotent and the Desk object keeps its
   identity (and its filed Zone) across pulls.
2. **Refresh** the `primitive_sources` row for each synced note: bump
   `external_etag` and `last_synced_at`, and advance the note's `last_modified`
   so the change syncs to other surfaces.
3. **Tombstone** notes that were in the report last pull but are absent this
   pull (`deleted=1`, `last_modified` bumped). A closed-and-done issue falling
   out of an open-issues report disappears cleanly.
4. **Maintain** the report-KB's `member_ids` to exactly the current result set.

A pull MUST be atomic per report: either the whole report reconciles or the
prior state is preserved. A mid-pull failure MUST NOT leave a half-updated KB.

**Content hash as the etag.** The `external_etag` is NOT JIRA's raw `updated`
timestamp alone. It is a SHA-256 of a deterministic serialization of the
extracted issue fields (summary, status, statusCategory.key, assignee,
priority, issuetype, and the mapped custom fields with keys **sorted
alphabetically**). The sort is load-bearing: the reference `ticketr` adapter
hit a real determinism bug where non-deterministic map iteration produced
different hashes for identical tickets (§18, Milestone 4). Python dicts are
insertion-ordered (3.7+), but the issue JSON's field order is not guaranteed
across JIRA versions, so the hash MUST be computed from a sorted
representation. Using the content hash (not just `updated`) means a pull that
returns the same content but a fresher `updated` (e.g. someone edited and
reverted) does NOT bump `last_modified`, avoiding spurious sync churn.

**Pagination.** JIRA's `/search` paginates with `startAt` + `maxResults`. The
pack requests `maxResults: 50` per page and follows `total` + `startAt` to
fetch subsequent pages until the report's result set is exhausted, capped at a
hard ceiling of 200 issues per report (JDS-R-002). The reference `ticketr`
adapter hard-codes `maxResults: 100` with a `// TODO: Add pagination support`
(§18) — a known gap JDS-01 closes. A pull that hits the ceiling MUST log a
warning naming the truncation and MUST NOT silently drop issues beyond it.

### 7.6 Note Body Shape

The note body is a compact markdown block, not a full issue mirror. It carries
the fields that round-trip and a deep link for the rest:

```markdown
# PROJ-123 — Fix the login redirect loop

- **Status:** Code Review (In Progress)
- **Assignee:** Dana Ng
- **Priority:** High
- **Type:** Story
- **Updated:** 2026-07-11T14:02:00Z
- **Subtasks:** 2
- **Link:** https://acme.atlassian.net/browse/PROJ-123

> The redirect loop occurs when the session cookie expires mid-flow…
```

The description is capped (default 500 chars, ellipsised) to keep the Desk
object scannable. Comments, transitions, and attachments do not survive the
mapping; the deep link carries them. Mapped custom fields (§7.7) render as
additional `- **FieldName:** value` lines when the field is present and the
mapping is configured.

### 7.7 Dynamic Field Mapping (custom fields round-trip)

The reference `ticketr` adapter (§18) proves that JIRA custom fields CAN
round-trip with a field-mapping config, rather than being lost. JDS-01 adopts
this pattern so a `Story Points`, `Sprint`, or `Epic Link` field lands as a tag
and a body line instead of disappearing.

**The mapping config** (a connector setting, JSON-string):

```json
{
  "Story Points": { "id": "customfield_10010", "type": "number" },
  "Sprint":       { "id": "customfield_10020", "type": "string" },
  "Epic Link":    { "id": "customfield_10014", "type": "string" },
  "Labels":       { "id": "labels",            "type": "array"  }
}
```

The pack builds a **reverse mapping** (`customfield_10010` -> `Story Points`)
for parsing JIRA responses, exactly as `ticketr`'s
`createReverseFieldMapping` does. When the pack walks an issue's `fields`, a
`customfield_*` key that is in the reverse mapping is extracted to its human
name with type-aware coercion (a `number` field renders as a number, an
`array` field joins with `, `). A field NOT in the mapping is silently
skipped (not an error: every JIRA project has dozens of unused custom fields).

**Schema discovery.** The pack exposes a `schema` action (not a JIRA write;
still read-only, still gated) that calls
`GET /rest/api/2/issue/createmeta?projectKeys=PROJ&expand=projects.issuetypes.fields`
to discover the project's available fields and their types, then emits a
starter mapping config the operator can commit. This mirrors `ticketr schema`
and closes the "how do I know my custom field ids" question without
hand-guessing `customfield_10042`. The discovery call routes through the same
host-pinned opener as the search.

**What does NOT round-trip.** Even with mapping, the following stay lossy and
ride only as the deep link: comments, transitions/history, attachments,
worklogs, and ADF-rich-text in description (api/2 returns it as a plain string
but it may contain JIRA wiki markup like `h3.` headers, which the note body
renders as-is without conversion). This is documented, not hidden.

## 8. Provenance and the Read-Only Synced Note

Desk primitives are user-authored, canonical, last-write-wins. A JIRA-sourced
note is externally-sourced and refreshable. Those two models collide on
`last_modified`. The resolution, following the existing `artifact_sources`
sidecar pattern rather than bloating the Note table, is a separate edge store
(§6.5) plus three rules:

1. **Live provenance means read-only.** While a `primitive_sources` row exists
   for a note, the Desk refuses body edits (`PUT /api/notes/{id}` returns a
   typed 409 naming the connector and framing the detach action). The operator
   may still file the note into a Zone, ground a run with it, open it in JIRA,
   or delete it (a delete tombstones the note AND its provenance row).
2. **Refresh never clobbers a human edit, because there is no human edit to
   clobber** until detach. This is the honest invariant: the read-only lock is
   what makes "refresh is safe" true without a merge strategy.
3. **Detach to own.** `POST /api/notes/{id}/detach` strips the provenance row.
   The note becomes a normal editable note, frozen at its last pull, and a
   future refresh of the report will treat it as absent (re-creating it as a
   fresh synced note if it reappears in the JQL result). Detach is the operator's
   "cut the cord" action; it is recorded in the connector's run log.

This shape means the Note schema, the sync wire contract, and the iPad authoring
path are all untouched. The only new surface is the sidecar and the two routes
that consult it.

## 9. The Write-Back Future (Deliberately Deferred)

The moment someone says "transition PROJ-123 to Done from this meeting action,"
that is a write. JDS-01 does not build it, but the design leaves the seam clean.
The write-back rides the existing `gated_connector` + actuator framework as a
sibling of `github_issue_actuator`:

- A `jira_issue_actuator` (the plugin) builds an `ActuatorProposal` whose
  payload carries `{issue_key, transition_id, comment}`. It never reaches out.
- A `build_jira_issue_connector(...)` (the connector) is built with
  `build_gated_connector`: permission `network:outbound`, manifest allow-listed
  to exactly `POST /rest/api/2/issue/{key}/transitions` (and, if needed,
  `POST /rest/api/2/issue/{key}/comments`) on the configured host.
- Same propose-approve-execute, same executed-equals-previewed parity, same
  per-action human approval. The credential is the same secret-store pair.

Keeping JDS-01 pull-only means the dangerous half is a separate, later story
with its own consent surface and its own evidence bundle. The pull MVP needs
only the `PermissionGate`, which is the right, narrower gate for a side-effect-
free read.

## 10. Detailed Requirements

### 10.1 Functional Requirements

- `JDS-F-001` `Enrich` MUST pull the configured JQL report and write one Note
  per returned issue with a stable `jira:<slug>:<KEY>` id.
- `JDS-F-002` `Enrich` MUST maintain one KB per report whose `member_ids` is
  exactly the current result set after the pull.
- `JDS-F-003` A second pull of the same report MUST be idempotent: no duplicate
  notes, no duplicate KB rows, `last_modified` advances only when content
  changed (compared via `external_etag`).
- `JDS-F-004` An issue absent from the current result set but present at the
  prior pull MUST be tombstoned (`deleted=1`) and removed from the report-KB
  membership.
- `JDS-F-005` `Enrich` MUST be atomic per report: a mid-pull failure preserves
  the prior reconciled state.
- `JDS-F-006` `Preview` (`dry_run: true`) MUST return the planned notes and KB
  membership WITHOUT writing any primitive or provenance row.
- `JDS-F-007` `Clear` MUST tombstone every note and KB authored by this
  connector instance and delete its `primitive_sources` rows.
- `JDS-F-008` Lane grouping MUST key off `statusCategory.key` (`new` / `ind` /
  `done`), never off the granular `status.name`.
- `JDS-F-009` A pull failure MUST set `last_error` on the connector row and
  MUST NOT mutate any existing synced note to a worse state.
- `JDS-F-010` The connector MUST be disabled by default; enabling is an explicit
  operator act recorded on the connector row.

### 10.2 Data Requirements

- `JDS-D-001` The `primitive_sources` table MUST be added via an additive
  schema migration; no existing column is altered.
- `JDS-D-002` Credentials (`jira_email`, `jira_api_token`) MUST NOT appear in
  the `activity_enrichment_connectors.settings_json` row, in any connector_runs
  row, or in any log line.
- `JDS-D-003` The Note `id` scheme `jira:<instance-slug>:<KEY>` MUST be
  deterministic from `base_url` + issue key alone, so a re-pull after a process
  restart reconciles to the same rows.
- `JDS-D-004` `last_modified` on a synced note MUST advance on every content
  change so the sync wire contract propagates the refresh unchanged.
- `JDS-D-005` A tombstoned synced note MUST propagate its deletion to other
  surfaces via the existing tombstone + `last_modified` sync semantics (no new
  sync path).

### 10.3 API and UX Requirements

- `JDS-A-001` A PUT to a note with live provenance MUST return HTTP 409 with a
  body naming the source connector and framing the detach action.
- `JDS-A-002` `POST /api/notes/{id}/detach` MUST strip the provenance row and
  return the note as an editable note; the body is unchanged by detach.
- `JDS-A-003` `POST /api/connectors/{id}/refresh` MUST trigger one `Enrich` run
  out of cadence and return the run result.
- `JDS-A-004` The Desk object for a synced note and a synced report-KB MUST
  wear the egress badge (`cloud · <host>`) and a "refreshed N min ago" line.
  Reassurance sentences ("nothing leaves your machine", "stored locally") MUST
  NOT appear on these objects.
- `JDS-A-005` The Desk MUST render a read-only indicator on synced note bodies
  and a refresh control on the report-KB object.

### 10.4 Configuration Requirements

- `JDS-C-001` `base_url` MUST be a connector setting (visible); it MUST be a
  parseable `https://` URL or validation refuses the enable.
- `JDS-C-002` `jira_email` and `jira_api_token` MUST be secrets in
  `SECRET_PATHS`, redacted in `redacted_settings`, and joined at request time.
- `JDS-C-003` `report_jql` (single report) or `reports` (JSON-string list of
  `{name, jql, kb_id}`) MUST be a connector setting; an empty value refuses the
  enable.
- `JDS-C-004` `poll_interval_seconds` MUST default to 300 and be bounded
  `>= 60` (a floor against hammering a host).
- `JDS-C-005` Defaults MUST keep JDS-01 fully off for existing users.

### 10.5 Doctor Requirements

- `JDS-DOC-001` A `JIRA desk-sync` check MUST report, per configured pack
  instance: enabled state, resolved `base_url` host, credential presence
  (configured / missing, never the value), last-run age, and last error if any.
- `JDS-DOC-002` When the connector is enabled but the host is unreachable, the
  check MUST surface `WARN` with the operator-readable error from `last_error`
  (not `FAIL`: stale data is still served).
- `JDS-DOC-003` When the connector is disabled, the check MUST be `INFO` and
  silent (no noise for users who do not use JIRA).

### 10.6 Reliability and Performance Requirements

- `JDS-R-001` The opener MUST enforce a per-request timeout (default 10 s); a
  timeout MUST set `last_error` and end the pull without partial writes. (The
  reference `ticketr` adapter omits this — `&http.Client{}` with no timeout —
  §18; JDS-01 corrects it.)
- `JDS-R-002` The pack MUST cap `maxResults` per page at 50 and the total per
  report at a hard ceiling of 200 (following pagination); a report exceeding
  the ceiling MUST log a truncation warning.
- `JDS-R-003` The opener MUST set `follow_redirect: false` and enforce the host
  pin (§7.4); a cross-host redirect MUST be refused before the `Authorization`
  header is sent to the target.
- `JDS-R-004` A pull SHOULD tolerate a single malformed issue in the result set
  (skip it, record a warning, continue) rather than fail the whole report.

### 10.7 Observability Requirements

- `JDS-O-001` Each `Enrich` run MUST emit a structured log line: connector id,
  report name, host, issues pulled, notes upserted, notes tombstoned, elapsed
  ms, and any per-issue warnings.
- `JDS-O-002` A run MUST be recorded in `connector_runs` (connector_id,
  started_at, status, error) reusing the existing connector-generic table.
- `JDS-O-003` Logs and run rows MUST NOT contain the `Authorization` header, the
  token, or the email; the opener scrubs them before any structured field is
  written.

### 10.8 Security and Trust Requirements

- `JDS-S-001` The credential pair is read from the secret store at call time
  and held in memory only for the duration of the opener call.
- `JDS-S-002` The pack MUST NOT execute shell commands; it uses
  `open_outbound_socket` only. `shell:exec` is not declared and not held.
- `JDS-S-003` The pack MUST NOT write to the activity ledger
  (`activity_records` / `activity_annotations`); its only write surface is the
  primitive repos and the `primitive_sources` sidecar.
- `JDS-S-004` Egress is a badge, not prose (positioning canon, Phase 62): the
  `cloud · <host>` mark on every synced object is the trust surface, alongside
  the dedicated TrustChip popover that may explain the posture once.

## 11. Verification Strategy

### 11.1 Methods

`UT` unit, `IT` integration, `AT` API/CLI, `MT` manual trace, `LG` log/metrics.

### 11.2 Requirement-to-Verification Matrix

| Requirement | Method | Verification Demand | Evidence |
|---|---|---|---|
| JDS-F-001 | UT | One note per issue, stable id, against a fake opener | `10_ut_pull.log` |
| JDS-F-002 | UT | Report-KB member_ids == result set | `10_ut_pull.log` |
| JDS-F-003 | UT | Second pull is idempotent; unchanged etag does not bump last_modified | `11_ut_reconcile.log` |
| JDS-F-004 | UT | Vanished issue tombstoned + removed from KB | `11_ut_reconcile.log` |
| JDS-F-005 | UT | Mid-pull failure (opener raises) preserves prior state | `11_ut_reconcile.log` |
| JDS-F-006 | UT | dry_run writes nothing | `12_ut_preview.log` |
| JDS-F-007 | UT | Clear tombstones notes+KB and drops provenance | `13_ut_clear.log` |
| JDS-F-008 | UT | Lanes keyed off statusCategory.key, not status.name | `10_ut_pull.log` |
| JDS-F-009 | UT | Pull failure sets last_error, no worse-state mutation | `11_ut_reconcile.log` |
| JDS-F-010 | UT | Default manifest has enabled=false | `14_ut_manifest.log` |
| JDS-F-011 | UT | Nested fields extracted (status.statusCategory.key, assignee.displayName) | `10_ut_pull.log` |
| JDS-F-012 | UT | null/absent field degrades to unassigned tag, no raise | `10_ut_pull.log` |
| JDS-F-013 | UT | Pagination follows startAt to exhaustion; truncation warns | `19_ut_pagination.log` |
| JDS-F-014 | UT | Mapped custom field round-trips; unmapped silently skipped | `10_ut_pull.log` |
| JDS-D-001 | IT | Schema migration adds primitive_sources on an old DB | `30_it_migration.log` |
| JDS-D-002 | UT | No credential in settings_json / runs / logs | `15_ut_secrets.log` |
| JDS-D-003 | UT | id scheme deterministic from base_url + key | `10_ut_pull.log` |
| JDS-D-004 | UT | last_modified advances on content change only | `11_ut_reconcile.log` |
| JDS-D-005 | IT | Tombstone propagates through sync shape | `30_it_migration.log` |
| JDS-D-006 | UT | external_etag is sorted-key content hash, not raw `updated` | `11_ut_reconcile.log` |
| JDS-A-001 | AT | PUT on synced note returns 409 with detach framing | `40_api_checks.log` |
| JDS-A-002 | AT | detach strips provenance, note editable | `40_api_checks.log` |
| JDS-A-003 | AT | refresh route returns run result | `40_api_checks.log` |
| JDS-A-004 | AT | Egress badge + refreshed line render; no reassurance prose | `41_desk_render.png` |
| JDS-A-005 | AT | Read-only indicator + refresh control present | `41_desk_render.png` |
| JDS-C-001..005 | UT | Config validation accepts/rejects per rule | `14_ut_manifest.log` |
| JDS-DOC-001..004 | AT | Doctor output across enabled/auth-ok/unreachable/disabled | `42_doctor_checks.log` |
| JDS-R-001 | UT | Timeout sets last_error, no partial write | `16_ut_timeout.log` |
| JDS-R-002 | UT | maxResults capped at 50/page, 200/report; truncation warns | `19_ut_pagination.log` |
| JDS-R-003 | UT | Cross-host redirect refused before auth header | `17_ut_hostpin.log` |
| JDS-R-004 | UT | One malformed issue skipped, report continues | `18_ut_tolerance.log` |
| JDS-O-001..003 | LG | Log + run row scrubbed; all four regex patterns proven | `60_logs_sample.txt` |
| JDS-S-001..003 | UT | Secret-at-call-time, no shell, no activity-ledger write | `15_ut_secrets.log` |
| JDS-S-004 | AT | Badge markup present, no reassurance sentence in DOM | `41_desk_render.png` |
| (live) | MT | One real pull against a real JIRA Cloud instance | `61_live_trace.txt` |

The live trace (`61_live_trace.txt`) is the one manual verification that touches
a real JIRA host. It is optional for CI green but REQUIRED for the phase to
close: it proves the REST shape, the auth, and the lane grouping against a real
workflow scheme, which the fake-opener tests cannot.

## 12. Evidence Bundle

### 12.1 Required Folder

`docs/evidence/phase-jds-01/<YYYYMMDD-HHMM>/`

### 12.2 Required Files

`00_manifest.md`, `01_env.txt`, `02_git_status.txt`, `03_traceability.md`,
`10_ut_pull.log`, `11_ut_reconcile.log`, `12_ut_preview.log`,
`13_ut_clear.log`, `14_ut_manifest.log`, `15_ut_secrets.log`,
`16_ut_timeout.log`, `17_ut_hostpin.log`, `18_ut_tolerance.log`,
`19_ut_pagination.log`, `30_it_migration.log`, `40_api_checks.log`,
`41_desk_render.png`, `42_doctor_checks.log`, `60_logs_sample.txt`,
`61_live_trace.txt`, `99_phase_summary.md`.

### 12.3 Validity Rules

Identical to `PLAN_PHASE_MULTI_INTENT_ROUTING.md` §8.3 (real commands, real
timestamps, real commit hashes, no deletion of failures). The live trace MUST
record the JIRA instance type (Cloud / DC), the JQL used, the issue count, and
the resulting Desk object ids, with credentials redacted.

## 13. Implementation Recipe

### 13.1 Step 1 — SDK Extension

1. Add `desk_sync` to `KNOWN_KINDS`, `desk_primitives` to `KNOWN_CAPABILITIES`,
   `write:desk_primitives` to `KNOWN_PERMISSIONS` in `connector_sdk.py`.
2. Add the cross-field validator rule: `kind == "desk_sync"` MUST declare both
   `write:desk_primitives` and `network:outbound`.
3. Unit tests: `tests/unit/test_connector_sdk_desk_sync.py`.

### 13.2 Step 2 — Provenance Sidecar

1. Add the `primitive_sources` table + migration in `db/core.py`.
2. Implement `db/primitive_sources.py` (`PrimitiveSourceRepository`: upsert, get,
   list_for_connector, delete, detach).
3. Unit tests: `tests/unit/test_primitive_sources.py`.

### 13.3 Step 3 — The Pack (pull + reconcile)

1. Implement `connector_packs/jira_desk_sync.py`: manifest, host-pinned opener
   (injectable, `follow_redirect: false`, 10 s timeout), POST `/rest/api/2/search`
   with `{jql, fields, maxResults, startAt}`, nested-field extraction (§7.3),
   issue-to-Note mapping, lane grouping, idempotent upsert + KB maintenance +
   tombstoning, `startAt` pagination (§7.5), content-hash etag (§7.5),
   `Preview`/`Enrich`/`Clear`.
2. Implement the field-mapping config + reverse mapping + `schema` discovery
   action (§7.7), mirroring the reference `ticketr` adapter's
   `createReverseFieldMapping` and `GetIssueTypeFields`.
3. Export in `connector_packs/__init__.py` `ALL_PACKS`.
4. Unit tests with a fake opener and a fake gate (no network, no socket):
   `tests/unit/test_jira_desk_sync_pack.py` (happy path),
   `tests/unit/test_jira_desk_sync_pagination.py` (pagination + truncation).

### 13.4 Step 4 — Secrets + Settings

1. Add `jira_email`, `jira_api_token` to `SECRET_PATHS` in
   `settings_secrets.py`.
2. Add `base_url`, `report_jql` / `reports`, `poll_interval_seconds`,
   `max_results`, `timeout_seconds` to the pack's `settings_schema`.
3. Unit tests: `tests/unit/test_jira_desk_sync_secrets.py`.

### 13.5 Step 5 — Read-Only Enforcement + Detach

1. In `web/routes/primitives/notes.py`, refuse PUT on a note with live
   provenance (409 with detach framing); add `POST /{id}/detach`.
2. Add `POST /api/connectors/{id}/refresh`.
3. API tests: `tests/integration/test_jira_desk_sync_api.py`.

### 13.6 Step 6 — Desk Surface Treatment

1. Egress badge + "refreshed N min ago" + read-only indicator + refresh control
   on synced note and report-KB objects. Reuse the existing primitive renderers;
   no new primitive kind.
2. Screenshot evidence against the real web desk.

### 13.7 Step 7 — Doctor

1. Add the `JIRA desk-sync` check per §10.5.
2. Update `tests/unit/test_doctor_command.py`.

### 13.8 Step 8 — Live Trace

1. One real pull against a real JIRA instance; record `61_live_trace.txt`.

### 13.9 Step 9 — Full Regression

```bash
uv run pytest -q tests/unit
uv run pytest -q tests/integration
uv run python -m compileall holdspeak
uv run pytest -q tests/ -k doctor
```

## 14. Risks and Mitigations

1. **Credential leakage.** The token is the highest-value secret in the feature.
   Mitigation: secret-store-only, joined at call time, scrubbed from logs and
   run rows, and the host pin (§7.3) refuses to send the header to a redirect
   target. JDS-S-001..003 + JDS-O-003 pin this; `15_ut_secrets.log` and
   `17_ut_hostpin.log` prove it.
2. **Stale data presented as fresh.** A pull failure could leave old issues on
   the Desk looking current. Mitigation: the "refreshed N min ago" line is
   honest about age, `last_error` surfaces in doctor, and a pull failure never
   mutates to a worse state (JDS-F-009). The badge says `cloud`, not "live".
3. **Lossy mapping hides a field the operator needs.** Comments, transitions,
   attachments, and ADF-rich-text do not round-trip; custom fields DO round-trip
   with a mapping (§7.7). Mitigation: the deep link is always present; the
   description cap is conservative; the `schema` discovery action generates a
   starter mapping; the full-fidelity "task" primitive is the documented
   JDS-02 escape hatch (§3.2) if the mapped fields are still insufficient.
4. **One report hammers the host.** A short `poll_interval_seconds` or a huge
   JQL result could rate-limit or DoS the JIRA instance. Mitigation: the 60 s
   floor (JDS-C-004), the `maxResults` ceiling (JDS-R-002), and the per-request
   timeout (JDS-R-001).
5. **Redirect-based SSRF.** A hostile or misconfigured `base_url` could redirect
   the opener to an attacker host. Mitigation: the host pin refuses cross-host
   redirects before the `Authorization` header is sent (JDS-R-003).
6. **Schema migration on old DBs.** Adding a table is low-risk, but the
   migration must run on every existing install. Mitigation: additive-only,
   `CREATE TABLE IF NOT EXISTS`, covered by `30_it_migration.log` on a fixture
   of the prior schema version.
7. **Sync collision with hand edits on another surface.** A synced note's
   `last_modified` advances on refresh; if the iPad edited the same note in the
   same window, last-write-wins applies. Mitigation: read-only enforcement
   (§8) means there is no hand edit to collide with until detach, at which point
   the note leaves the sync set. The invariant is structural, not advisory.
8. **JIRA Cloud vs DC field drift.** Cloud and DC both serve `/rest/api/2`,
   which JDS-01 uses for both (§7.1); the api/3-vs-api/2 question is resolved
   (api/2 for both, to avoid ADF parsing). Residual risk: some custom field IDs
   differ between Cloud and DC instances of the same project. Mitigation: the
   `schema` discovery action (§7.7) reads the actual project's fields, so the
   mapping is never hard-coded to one instance type; the live trace (§13.8)
   must record which instance type was verified.

## 15. Definition of Done

1. Every `JDS-*` requirement has passing verification evidence.
2. Required evidence files exist and are non-empty.
3. A real pull against a real JIRA instance (Cloud or DC) is recorded in
   `61_live_trace.txt`, with credentials redacted.
4. With the connector disabled, all baseline behavior is byte-identical to
   pre-JDS-01 (no new tables queried on the hot path, no new routes mounted that
   change existing responses).
5. `holdspeak doctor` cleanly reports the new check in enabled, unreachable, and
   disabled states.
6. Phase summary lists known gaps and explicitly defers JDS-02 items (write-back
   actuator, typed multi-report settings, a dedicated task primitive if the
   lossy mapping bites, CLI-backed variant).

## 16. Open Questions (Resolve Before Step 5)

1. **One pack instance per report vs a `reports` JSON setting.** The scalar
   `settings_schema` cannot express a typed list of reports. v1 likely ships the
   `reports` JSON-string setting (parsed by the pack) so one configured source
   serves several lanes; the cleaner typed-list SDK extension is JDS-02.
   Resolve by confirming the JSON-string shape is acceptable for the operator
   UI before Step 4.
2. **KB per report vs Zone per report.** A KB groups issue-notes as members; a
   Zone (Directory) files them spatially. The MVP uses a KB (cheaper, already
   rendered). Filing the KB into a Zone is a one-line `DirectoryMembership`
   upsert and MAY ship in JDS-01 if the desk surface needs it for the vibe;
   otherwise it is a follow-up.
3. **Should a synced note be groundable into a run?** Yes, by default, the same
   as any note. Confirm there is no capability gate needed for grounding
   external-sourced material before Step 5 wires the read-only enforcement.
4. **Detached-note re-sync behavior.** When a detached note's issue reappears in
   the JQL result, does the refresh re-create a fresh synced note (leaving the
   detached edit intact) or re-attach to the existing note? The design above
   re-creates fresh (the detached note keeps its edit). Confirm this is the
   honest default before Step 3.
5. **~~Data Center `/rest/api/2` vs Cloud `/rest/api/3`.~~** Resolved: JDS-01
   uses `/rest/api/2/` for BOTH Cloud and DC (§7.1). The api/3 path would
   require parsing Atlassian Document Format for the description field, which
   is a non-trivial parser unjustified for a pull-only Desk view; api/2 returns
   a plain string and works on both instance types. The reference `ticketr`
   adapter (§18) uses api/2 throughout, confirming the path. This resolves open
   question #5; no transport fallback is needed in JDS-01.

## 17. Appendix A — What "shipped" means for JDS-01

Borrowing the bar from `PLAN_ARCHITECT_PLUGIN_SYSTEM.md` Appendix A, adapted to
a connector: the JIRA desk-sync pack counts as **shipped** only when it:

1. implements the `Enrich`/`Preview`/`Clear` protocols with a real `enrich()`
   that calls a real downstream (the JIRA REST endpoint via the gated opener),
   not a stub or a local-file fixture;
2. routes the REST call through `PermissionGate.open_outbound_socket`
   (`network:outbound`) with the host pin enforced, never a raw `requests`/`urllib`
   call that bypasses the gate;
3. writes real `notes`/`kbs`/`primitive_sources` rows the Desk renders, with
   provenance and the read-only lock live; and
4. ships with unit + integration tests covering the happy path, the
   reconcile/idempotency path, the failure path (timeout, host-pin refusal,
   malformed issue), and the secrets-scrubbing path, plus one live trace against
   a real JIRA instance.

Anything not meeting all four bars is a stub and MUST be marked as such in the
phase summary, not celebrated as done.

## 18. Appendix B — The `ticketr` reference implementation

This plan is materially strengthened by studying `karolswdev/ticketr` (a Go
CLI, "your all-in-one JIRA helper," cloned to `/tmp/ticketr` during planning).
It is a working, production-claimed bidirectional JIRA sync with a clean
hexagonal (ports-and-adapters) architecture and real battle scars. The findings
below are what JDS-01 borrows, what it corrects, and what it leaves behind.

### What JDS-01 borrows (proven patterns, lifted directly)

1. **`/rest/api/2/` over `/rest/api/3/`.** `ticketr`'s `jira_adapter.go` uses
   api/2 throughout. The load-bearing reason: api/2's `description` is a plain
   string; api/3's is Atlassian Document Format (nested JSON). A pull-only Desk
   view does not justify an ADF parser. This single finding reversed an earlier
   draft's commit to api/3 (§7.1).
2. **`POST /search`, not GET.** `ticketr` POSTs `{jql, fields, maxResults}` to
   `/rest/api/2/search`. POST avoids URL-length limits on long JQL. This
   corrected an earlier draft's GET-with-query-params shape (§7.1).
3. **Dynamic field mapping + reverse mapping.** `ticketr`'s `fieldMappings`
   config (`{"Story Points": {id: "customfield_10010", type: "number"}}`) and
   `createReverseFieldMapping()` for parsing responses is the template for JDS-01's
   §7.7. It proved custom fields CAN round-trip, reversing an earlier draft's
   "lossy" claim.
4. **Nested-field extraction.** `ticketr`'s `parseJiraIssue` switch on JSON
   value type (string/float/array/map, extracting `displayName`/`name` from
   nested objects) is the template for JDS-01's §7.3. A flat-field assumption
   is a correctness bug.
5. **Schema discovery via `/rest/api/2/issue/createmeta`.** `ticketr`'s
   `GetIssueTypeFields` + `schema` command discover a project's fields and emit
   a config. JDS-01 adopts this as a read-only `schema` action (§7.7).
6. **`/rest/api/2/myself` as the auth probe.** `ticketr`'s `Authenticate()`
   hits `myself` to verify credentials. JDS-01 uses this for the doctor check
   (§10.5) — cheaper and more honest than a JQL search.
7. **Sorted-key deterministic hashing.** `ticketr`'s Milestone 4 fixed a real
   bug: non-deterministic map iteration produced different hashes for identical
   tickets. JDS-01's content-hash etag sorts field keys (§7.5, JDS-D-006).
8. **Log redaction patterns.** `ticketr`'s `SensitiveRedactor` ships four
   concrete regex patterns (credential assignments, emails, URLs-with-creds,
   base64 blobs). JDS-01 adopts them verbatim (§10.7, JDS-O-003).
9. **Bidirectional conflict detection (the dual-hash model).** `ticketr`'s
   `state.TicketState{LocalHash, RemoteHash}` + `DetectConflict` is the proven
   model for the write-back future (§9). JDS-01's read-only MVP uses only the
   remote side (content hash), but the dual-hash design is documented for the
   actuator sibling.

### What JDS-01 corrects (gaps in the reference)

1. **No HTTP timeout.** `ticketr` constructs `&http.Client{}` with no timeout
   (`jira_adapter.go`); a hung JIRA host hangs the whole run. JDS-R-001 sets a
   10 s per-request timeout.
2. **No redirect protection.** `ticketr` follows redirects by default (Go's
   `http.Client` default). JDS-R-003 sets `follow_redirect: false` + the host
   pin, the SSRF defense.
3. **No pagination.** `ticketr` hard-codes `maxResults: 100` with a `// TODO:
   Add pagination support` comment (`jira_adapter.go:669`). JDS-01 implements
   `startAt` pagination (§7.5, JDS-F-013).
4. **N+1 subtask fetching.** `ticketr` runs a separate `parent = "KEY"` JQL per
   parent (`fetchSubtasks`). JDS-01 defers subtasks entirely to a count tag
   (§3.2 #7) and documents a batched `parent in (...)` fetch for JDS-02.
5. **Credentials from env vars, not a secret store.** `ticketr` reads
   `JIRA_API_KEY` from the environment. JDS-01 uses HoldSpeak's secret store
   (joined at request time, redacted in settings) per JDS-S-001.
6. **No egress gate / permission system.** `ticketr` makes raw `http.Client`
   calls. JDS-01 routes through `PermissionGate.open_outbound_socket`
   (`network:outbound`) per JDS-S-002.

### What JDS-01 leaves behind (different product surface)

1. **Bidirectional push.** `ticketr` pushes Markdown to JIRA (create/update
   issues). JDS-01 is pull-only; the write-back is a later actuator (§9) on the
   `gated_connector` spine, not a port of `ticketr`'s `PushService`.
2. **Markdown-as-source-of-truth.** `ticketr`'s thesis is "tickets as code" —
   Markdown files authored in git, pushed to JIRA. JDS-01's thesis is the
   inverse: JIRA is the source of truth, the Desk is a read-only view. The
   paradigms are complementary, not conflicting.
3. **State file (`.ticketr.state`).** `ticketr` tracks hashes in a JSON file
   for bidirectional conflict detection. JDS-01 tracks provenance in a DB
   sidecar (`primitive_sources`) because the Desk is a DB-backed spatial UI, not
   a file-based CLI. The hash algorithm is borrowed; the storage is not.
4. **File-based logging.** `ticketr` writes timestamped `.log` files with
   rotation. JDS-01 uses HoldSpeak's structured logging + `connector_runs`
   table (JDS-O-001..002), consistent with every other connector.

### Honest credit

The `ticketr` adapter is the most concrete proof that a JIRA REST pull is
buildable and that the hard parts (field mapping, nested extraction,
deterministic hashing, redaction) have known solutions. JDS-01 stands on its
shoulders for the JIRA-facing logic and diverges only where HoldSpeak's trust
model (egress gate, secret store, provenance, Desk primitives) demands a
different shape. The reference is cited inline throughout this plan (§7.1,
§7.3, §7.5, §7.7, §10.5, §10.7, risks) so every borrowed decision is
traceable to its origin.
