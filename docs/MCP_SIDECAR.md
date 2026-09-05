# MCP sidecar

The MCP sidecar is the desk's programmable surface over stdio. It exposes
201 tools across 36 families. The default non-owner discovery lists 34
resources; the owner discovery lists 37 because access filtering admits 16
static resources and 21 templates. Any MCP client (Claude Code, Cursor, a
custom script) can read and drive the desk without touching the web UI.

The sidecar runs as a child process of the MCP client. It opens the same
local database the web runtime uses, dispatches every tool through the same
service layer, and returns the same results. It has no web server, no
WebSocket, and no live-reload signal: it reads and writes the desk's state
directly.

## Wiring

The repo ships a `.mcp.json` at the root. Claude Code discovers it
automatically when it opens the repository:

```json
{
  "mcpServers": {
    "holdspeak": {
      "command": "uv",
      "args": ["run", "holdspeak-mcp"],
      "cwd": "."
    }
  }
}
```

To wire it into another MCP client, point it at `uv run holdspeak-mcp`
(or `uvx --from holdspeak holdspeak-mcp` for a PyPI install). The server
speaks stdio JSON-RPC.

People is an additional confidential-data boundary. The local owner process
has `write` access by default; the People family still returns only
`shared_intent` material. To reduce that process-start capability to read-only,
launch the sidecar with:

```json
{
  "mcpServers": {
    "holdspeak": {
      "command": "uv",
      "args": ["run", "holdspeak-mcp"],
      "cwd": ".",
      "env": {"HOLDSPEAK_MCP_PEOPLE_ACCESS": "read"}
    }
  }
}
```

Set `HOLDSPEAK_MCP_PEOPLE_ACCESS=off` to disable the family entirely. The
repository `.mcp.json` sets no override, so it uses the local-owner `write`
default.

## Tool families

The 201 tools are organized into domain families. Each tool follows the
`domain.verb` naming convention. Tool descriptions are the per-tool
reference; this page covers the families and the cross-cutting rules.

### desk (52 tools)

The original surface. CRUD for desk primitives (meetings, notes, artifacts,
projects, decision records, zones, workbenches, recipes, agents, sequences,
workflows), the pipeline observer, follow-through lanes, inference
invocations, and the Monday Brief. Five of the `desk.*` tools
(`desk.list`, `desk.get`, `desk.create`, `desk.update`, `desk.delete`)
operate on the primitive kind system: 6 surface kinds are stored as typed
rows; the remaining 12 (including the singleton People surface) are computed,
composite, or managed by a dedicated capability. Each description names
which kinds it handles.

### ask (4 tools)

Ask the desk a question. `ask.resolve_grounding` hydrates grounding references
without running inference. `ask.run` submits a question through the admitted
inference path and returns the answer with its receipt. `ask.cancel` cancels an
in-flight invocation. `ask.keep` persists an answer as a desk artifact (not
model-invoking). Model selection is never an Ask-side MCP control.

### door (2 tools)

`door.get` returns one closed, read-only Dashboard Door aggregate: the board,
active Thoughts, and a mixed upcoming timeline of calendar events (from all
enabled ICS sources, with per-source provenance when more than one source is
configured) and scheduled recordings, plus matching server-derived counts.
`door.add_item` creates an action item on the Door. It is an effect tool
(`effect_proposal`); in safe or neutral mode the call is held for the
decision box. An item created from a thread carries
`source_type='thread'` and `source_ref` pointing at the originating
message; the Door card shows a "from a thread" provenance chip.

Door has no MCP resource. Its
Follow-Through People overlay respects `HOLDSPEAK_MCP_PEOPLE_ACCESS` and is
safely empty when that encrypted disclosure capability is unavailable or off.

### project (35 tools)

Three read tools: `project.list` returns all projects (optionally
including archived). `project.get` returns one project by id with room
fields. `project.get_room` returns the coherent room projection.

Fourteen command tools mirror the web routes exactly (MCP-001 parity):
`project.create`, `project.update` (with expected_revision), `project.archive`,
`project.restore`, `project.link` / `project.unlink` (meeting association),
`project.open_review`, `project.get_delta`, `project.decide_proposal`,
`project.accept_review`, `project.list_updates`, `project.draft_update`,
`project.update_draft`, `project.publish_update`. Every effect tool
accepts an optional command_id for idempotent replay (MCP-002); where the
web route enforces expected_revision, the tool does too.

Five steward driver tools: `project.configure_steward` (policy read/write
including `unattended_enabled`), `project.run_steward` (returns run_id
PROMPTLY via MCP-003; phase execution on a daemon thread; typed refusals
for STW-002/disabled/cooldown), `project.stop_steward` (durable STW-003),
`project.get_steward_run` (pollable state with steps and receipts), and
`project.steward.trigger` (desk-wide, principal-scoped evaluate_due +
run_due NOW through the conductor's scheduler seam; unwired returns a typed
503 `scheduler_not_wired` refusal; never route-level dedup).

Six setup interview drivers: `project.setup.start`, `project.setup.resume`,
`project.setup.answer`, `project.setup.suggest`, `project.setup.finalize`,
and `project.setup.clarify_jira_scope` (refines a Jira proposal's project
keys and issue types within a setup session).
The durable session resumes across tool calls; finalize activates atomically
through the same ProjectService.create_from_setup seam as the web route.

Seven graduated watch tools: `project.watch.inspect`, `project.watch.test`,
`project.watch.evaluate`, `project.watch.set_rules`, `project.watch.pause`,
`project.watch.resume`, `project.watch.retire`. These operate ONLY on
graduated WatchSpec@1 rows (state in active/tested/paused/retired). Legacy
rows (state='') belong to the reactions family; the graduated tools
refuse legacy rows with typed `legacy_watch_boundary` errors. The
legacy side is not yet guarded in code (backlog). `project.watch.set_rules`
accepts an optional `evaluation_cadence_minutes` field (integer, 1..10080)
that sets the per-watch evaluation interval; the same field is accepted by
the HTTP `PUT /api/projects/{id}/steward/policy` route.

Five resource templates expose project data: `holdspeak://projects/{id}`,
`.../room`, `.../delta`, `.../updates/{update_id}`, and
`.../steward/runs/{run_id}`. Unknown ids refuse typed.

### provider (10 tools)

Provider discovery and connection status for GitHub and Jira.

**GitHub (4 tools).** `provider.list` returns all configured providers
(native + GitHub + Jira) with their capabilities and readiness.
`provider.github_connection` reads the GitHub adapter's connection status.
`provider.github_discover` runs bounded repository discovery through the
configured adapter (pagination surfaced). `provider.github_validate_repo`
validates a repository by owner/repo string. All GitHub tools refuse typed
with `provider_not_configured` when the adapter is absent.

**Jira (6 tools).** `provider.jira_connections` lists all Jira connections
(site+email pairs) and their status. `provider.jira_add_connection` adds a
connection by site and email (no credentials stored).
`provider.jira_connection` rechecks one connection's status (switch + auth
status probe). `provider.jira_discover` discovers Jira resources (projects,
issue types, statuses) for a connection. `provider.jira_search` runs a JQL
query and returns matching issues (optional per-issue enrichment for
duedate, resolution, updated via `workitem view`).
`provider.jira_validate_scope` validates a Jira project key. All Jira tools
refuse typed when the `acli` binary is absent.

No provider writes.

**Jira over acli.** The Atlassian CLI (`acli`) is the Jira transport, the
same relationship `gh` has with GitHub. Prerequisites: `acli` installed
(`brew tap atlassian/homebrew-acli && brew install acli`) and at least one
account authenticated (`acli jira auth login --site <site>.atlassian.net
--email <email> --token`). A connection is identified by (site, email);
one owner may hold many across multiple `*.atlassian.net` sites. Every call
follows the switch-and-verify law: `auth switch`, then the command, then
`auth status` read-back, under a cross-process file lock (`fcntl.flock` on
a lockfile in the data directory). The lock timeout defaults to 10 seconds
and is configurable via `HOLDSPEAK_ACLI_LOCK_TIMEOUT` (seconds, float).
A read-back mismatch is a typed error, never a silent wrong read. All
access is read-only.
The search field cap: `workitem search --fields` accepts only issuetype,
key, assignee, priority, status, summary, labels, reporter, creator,
description; fields such as duedate, resolution, and updated come from
per-issue `workitem view` enrichment (calls reported in the result).
Egress: Jira calls contact `<site>.atlassian.net` from this device.

Recorded shapes are from a live `acli 1.3.36-stable` session
(tests/unit/test_jira_provider.py carries the recorded fixtures).

### thread (1 tool)

`thread.set_status` writes the thread's persistent status line (shown in the
pullout head) and returns the written value. The text is persisted across turns.

### inference (1 tool)

`inference.cancel_model_acquisition` cancels a model download only before
verification begins. It cannot change model availability or any assignment.
Model acquisition enters through the seven Model Library commands below; model
and agent principals receive no authority through this tool.

### model library (7 tools)

Owner-only availability commands over the same Model Library application service
as the HTTP owner API: `model_library.get`, `model_library.download`,
`model_library.add_to_library`, `model_library.use_model_file`,
`model_library.connect_hosted_model`, `model_library.define_endpoint`, and
`model_library.connect_paired_device`. They can add or connect available models
but cannot select one for a capability; every command proves the assignment
heads are unchanged. File intake accepts only a request ID, a basename, and
base64 bytes capped at 16 MiB decoded. The sidecar owns temporary staging and
deletes it after the command; client paths are refused. Hosted-provider secrets
have a dedicated write-only `secret` field and never appear in errors, logs, or
receipts.

### inference assignment (5 tools)

Owner-only assignment projection and command twins over the same Assignment
application service as HTTP: `inference_assignment.summary`,
`inference_assignment.editor`, `inference_assignment.set`,
`inference_assignment.preview_use_default`, and
`inference_assignment.clear`. Their schemas are recursively closed. Set and
clear preserve the canonical narrow CAS and stable command replay; replay
returns the original committed-effect chain and hash, never a route, endpoint,
path, secret, or binding detail.

### thought (18 tools)

Develop a durable Thought through one explicit model turn. `thought.refine`
asks one useful question using server-loaded authoritative material;
`thought.reconcile` reads/finalizes only known durable proof, and
`thought.stop_refinement` durably suppresses an exact invocation before a
best-effort physical cancellation. `thought.answer_review`,
`thought.accept_review`, and `thought.reject_review` consume one receipt-gated
review through expected-revision CAS. They never start the next model turn.

Four context tools use that same application authority. `thought.list_context`
returns safe attachment metadata, pinned Everyday context, hub-local recent
choices, and bounded search/Browse results. `thought.attach_context` and
`thought.detach_context` replace the visible set under exact Thought cursors;
`thought.refresh_context` is the transport name for the UI's **Update context**
repair. They accept qualified refs and cursors only, never Note bodies, expanded
leaves, or copied prompt material. None invokes a model.

Four more Thought tools give MCP exact custody/default parity with HTTP.
`thought.create` and `thought.adopt_note` create or adopt through the shared
application service and return the final Thought plus its mandatory default-
application receipt. `thought.get_default_context` reads the complete hub-local
future set; `thought.replace_default_context` atomically replaces that set by
qualified refs under its own revision. The default is empty until the owner
sets it. It applies only to later local create/adopt, never changes an existing
Thought, never syncs, and never invokes a model. A source failure skips the
whole set and returns a named `not_applied` receipt rather than partial context.

Four Workbench tools complete the transport-neutral interview seam.
`thought.update_working` saves the live Note through the same cursor/CAS law as
the document editor; `thought.answer_and_continue` atomically adds one answer
and reserves exactly one next refinement turn; `thought.complete` finishes the
Thought locally; and `thought.resume` returns a completed Thought to working
state. The Workbench itself is available as a resource below. The model does
not receive this owner MCP catalogue: internal inference remains on the
separately admitted, least-authority execution path.

The two default operations correspond to `GET` and `PUT
/api/thoughts/default-context`. HTTP create/adopt use the same application
methods, closed nested schemas, authority checks, idempotency, and receipts.
Default reads/replacements accept no Note body, title, leaf metadata, prompt,
model, or attachment hash. Per-Thought detach and future-policy replacement are
different scopes.

The refine schema deliberately accepts no prompt, model, raw/working text,
grounding, or context payload. MCP supplies identities and cursors; the shared Thought
application service loads authoritative content exactly as the web surface
does, including the exact immutable attachment hash. The stdio sidecar keeps a coordinator loop alive for its whole process,
but does not perform global startup recovery because the web runtime may own
live work in the same database.

Thought command failures are structured tool errors: `error` is the readable
detail, `code` is the stable service code, and safe conflict context such as
the current Thought projection is retained. Thought resource failures carry
the same stable code in JSON-RPC `error.data`.

### settings (2 tools)

`settings.get` returns the current configuration with secrets redacted
and a `_revision` field for optimistic concurrency. `settings.update`
applies a partial patch. Secrets and inference assignments cannot be written
through this tool.

### coder (3 tools)

Read-only inspection of coder sessions. `coder.list` lists sessions
(optionally filtered by agent). `coder.get` returns one session by id.
`coder.audit` reads the bounded steering audit trail.

### concierge (5 tools)

Engine detection and model assignment. `concierge.detect` returns every
reachable engine (LAN, local, cloud, catalog presets) with hardware facts
and probe timestamps. `concierge.propose` returns a proposed assignment
per capability group using the same rules as the Settings, Models face.
`concierge.probe` runs a bounded latency check against one engine; a paid
cloud probe requires the explicit `generate:true` flag. `concierge.apply`
writes the complete assignment set in one step (refuses while any group is
WAITING and not OFF). `concierge.download` starts a catalog preset download
through the existing Model Library download path.

### cadence (11 tools)

The cadence engine: reviews meetings, proposed actions, and waiting coder
sessions, then prepares next actions. `cadence.status` returns the engine
state. `cadence.loops` and `cadence.get_loop` read individual loops.
`cadence.brief` returns the current brief. `cadence.closeout` reads the
closeout. `cadence.history` and `cadence.audit` read the event history.
`cadence.snooze`, `cadence.set_status`, `cadence.run_now`, and
`cadence.apply_closeout` are safe write verbs that mutate only the local
database.

### sequence (2 tools)

`sequence.run` runs a sequence (chain) through the admitted inference
path. `sequence.cancel` cancels a running sequence by its parent operation
id.

### workflow (2 tools)

`workflow.run` runs a workflow through the admitted inference path.
`workflow.cancel` cancels a running workflow by its parent operation id.

### memory (1 tool)

`memory.search` queries the long-horizon memory store with optional kind,
project, time, and pagination filters. Valid kinds are `decision`, `artifact`,
`note`, and `thread`.

### people (16 tools)

The encrypted People ledger defaults to `write` for the local owner process.
`people.readiness` is content-free and also works while access is explicitly
disabled. Set `HOLDSPEAK_MCP_PEOPLE_ACCESS=read` to restrict the sidecar to
listing relationships and reading one relationship's `shared_intent` 1:1s,
agenda items, grounding notes, linked Project refs, requests, and commitments.
`people.grounding.get` returns those accepted manual sources as a structured
evidence bundle; it does not invoke a model or infer an assessment. The default
`write` capability additionally admits relationship and grounding-note creation,
notes-only 1:1 and agenda creation, request creation/explicit acceptance, and
done/dismiss/reopen for shared commitments. `people.calendar.link` and
`people.calendar.unlink` manage ICS calendar source association for a
relationship. `people.owner_alias.link` and `people.owner_alias.unlink`
bind and unbind the owner's own alias within the People boundary.

MCP never initializes or recovers the encrypted store and never returns
leader-private sessions, private prep, agenda, grounding notes, requests, or commitments. It
also offers no People archive/delete, capture/transcript, inference, scoring,
search, sync, export, connector, or employment-decision tool. Tool results are
transient stdio disclosure to the explicitly trusted parent client; they are
not written to HoldSpeak's plaintext database, observer, FTS, or Cadence.

### heartbeat (4 tools)

The Heartbeat sweep: the unattended cadence that evaluates due Watches and
caches the needs-you aggregate. `heartbeat.status` reads the current
settings (interval, quiet hours, notification mode, last/next sweep
timestamps, and whether the sweep is currently held by quiet hours).
`heartbeat.run_now` triggers one immediate sweep and returns the receipt
(watch count, room count, duration, outcome summary). `heartbeat.set`
updates the sweep settings: `sweep_every_minutes` (1 to 1440, default
15), `quiet_hours` (`{start, end}` as hour integers), `notify` (`off`,
`edge`, or `every_sweep`), and `muted_projects` (project IDs excluded
from the notification aggregate). `heartbeat.notify_test` fires one test
desktop notification and returns `{fired: boolean}`.

### plugin_job (4 tools)

`plugin_job.list` and `plugin_job.summary` read deferred plugin job state.
`plugin_job.retry` re-queues a failed or completed job. `plugin_job.cancel`
marks a job done. Both refuse running jobs.

<!-- BEGIN MCP TOOL ROSTER (machine-generated -- do not edit) -->

**Registry totals:** 201 tools across 36 families.

#### ask (4)

- `ask.cancel`
- `ask.keep`
- `ask.resolve_grounding`
- `ask.run`

#### cadence (11)

- `cadence.apply_closeout`
- `cadence.audit`
- `cadence.brief`
- `cadence.closeout`
- `cadence.get_loop`
- `cadence.history`
- `cadence.loops`
- `cadence.run_now`
- `cadence.set_status`
- `cadence.snooze`
- `cadence.status`

#### coder (3)

- `coder.audit`
- `coder.get`
- `coder.list`

#### concierge (5)

- `concierge.apply`
- `concierge.detect`
- `concierge.download`
- `concierge.probe`
- `concierge.propose`

#### connection (2)

- `connection.list`
- `connection.recheck`

#### decision (1)

- `decision.supersede`

#### decision_record (5)

- `decision_record.create_from_desk`
- `decision_record.create_from_meeting`
- `decision_record.get`
- `decision_record.list`
- `decision_record.search`

#### desk (8)

- `desk.create`
- `desk.delete`
- `desk.get`
- `desk.list`
- `desk.needs_you`
- `desk.snapshot`
- `desk.update`
- `desk.verb`

#### dictation (2)

- `dictation.get`
- `dictation.list`

#### door (2)

- `door.add_item`
- `door.get`

#### event (1)

- `event.list`

#### follow_through (3)

- `follow_through.board`
- `follow_through.commit_decision`
- `follow_through.complete`

#### heartbeat (4)

- `heartbeat.notify_test`
- `heartbeat.run_now`
- `heartbeat.set`
- `heartbeat.status`

#### inference (1)

- `inference.cancel_model_acquisition`

#### inference_assignment (5)

- `inference_assignment.clear`
- `inference_assignment.editor`
- `inference_assignment.preview_use_default`
- `inference_assignment.set`
- `inference_assignment.summary`

#### kb (3)

- `kb.add_member`
- `kb.list_members`
- `kb.remove_member`

#### meeting (7)

- `meeting.delete`
- `meeting.export`
- `meeting.get`
- `meeting.list`
- `meeting.run_intelligence`
- `meeting.start_capture`
- `meeting.stop_capture`

#### memory (1)

- `memory.search`

#### model_library (7)

- `model_library.add_to_library`
- `model_library.connect_hosted_model`
- `model_library.connect_paired_device`
- `model_library.define_endpoint`
- `model_library.download`
- `model_library.get`
- `model_library.use_model_file`

#### monday_brief (2)

- `monday_brief.generate`
- `monday_brief.get`

#### people (16)

- `people.agenda.add`
- `people.calendar.link`
- `people.calendar.unlink`
- `people.commitment.transition`
- `people.grounding.get`
- `people.note.create`
- `people.one_on_one.brief`
- `people.one_on_one.create`
- `people.owner_alias.link`
- `people.owner_alias.unlink`
- `people.readiness`
- `people.relationship.create`
- `people.relationship.get`
- `people.relationship.list`
- `people.request.accept`
- `people.request.create`

#### pipeline (1)

- `pipeline.events`

#### plugin_job (4)

- `plugin_job.cancel`
- `plugin_job.list`
- `plugin_job.retry`
- `plugin_job.summary`

#### project (35)

- `project.accept_review`
- `project.archive`
- `project.configure_steward`
- `project.create`
- `project.decide_proposal`
- `project.draft_update`
- `project.get`
- `project.get_delta`
- `project.get_room`
- `project.get_steward_run`
- `project.link`
- `project.list`
- `project.list_updates`
- `project.open_review`
- `project.publish_update`
- `project.restore`
- `project.run_steward`
- `project.setup.answer`
- `project.setup.clarify_jira_scope`
- `project.setup.finalize`
- `project.setup.resume`
- `project.setup.start`
- `project.setup.suggest`
- `project.steward.trigger`
- `project.stop_steward`
- `project.unlink`
- `project.update`
- `project.update_draft`
- `project.watch.evaluate`
- `project.watch.inspect`
- `project.watch.pause`
- `project.watch.resume`
- `project.watch.retire`
- `project.watch.set_rules`
- `project.watch.test`

#### provider (10)

- `provider.github_connection`
- `provider.github_discover`
- `provider.github_validate_repo`
- `provider.jira_add_connection`
- `provider.jira_connection`
- `provider.jira_connections`
- `provider.jira_discover`
- `provider.jira_search`
- `provider.jira_validate_scope`
- `provider.list`

#### reaction (5)

- `reaction.create`
- `reaction.list`
- `reaction.presets`
- `reaction.process`
- `reaction.set_enabled`

#### recipe (4)

- `recipe.chat`
- `recipe.get`
- `recipe.list`
- `recipe.run`

#### scheduled_recording (5)

- `scheduled_recording.cancel_armed`
- `scheduled_recording.create`
- `scheduled_recording.delete`
- `scheduled_recording.list`
- `scheduled_recording.update`

#### sequence (2)

- `sequence.cancel`
- `sequence.run`

#### settings (3)

- `settings.get`
- `settings.hub`
- `settings.update`

#### thought (18)

- `thought.accept_review`
- `thought.adopt_note`
- `thought.answer_and_continue`
- `thought.answer_review`
- `thought.attach_context`
- `thought.complete`
- `thought.create`
- `thought.detach_context`
- `thought.get_default_context`
- `thought.list_context`
- `thought.reconcile`
- `thought.refine`
- `thought.refresh_context`
- `thought.reject_review`
- `thought.replace_default_context`
- `thought.resume`
- `thought.stop_refinement`
- `thought.update_working`

#### thread (1)

- `thread.set_status`

#### watch (5)

- `watch.create`
- `watch.list`
- `watch.preview`
- `watch.refresh`
- `watch.set_enabled`

#### workbench (10)

- `workbench.add_item`
- `workbench.create`
- `workbench.delete`
- `workbench.delete_item`
- `workbench.get`
- `workbench.list`
- `workbench.list_runs`
- `workbench.run`
- `workbench.update`
- `workbench.update_item`

#### workflow (2)

- `workflow.cancel`
- `workflow.run`

#### zone (3)

- `zone.file`
- `zone.list_members`
- `zone.unfile`

<!-- END MCP TOOL ROSTER -->

## Model-invoking tools

A sidecar tool that starts model work uses the same owner service authority as
HTTP. It cannot choose a provider, alter an already admitted run, or bypass the
registered capability and assignment checks. Results carry the receipt and
placement projection appropriate to that product operation, so a caller can
inspect the boundary after the fact.

Route resolution, frozen plans, controller fallback, physical execution, and
receipt election are documented once in
[Intelligence Router architecture](internal/ARCHITECTURE_INTELLIGENCE_ROUTER.md).
This guide is the MCP transport reference, not a second routing specification.

## The egress note on settings.update

`settings.update` cannot write inference assignments or connection secrets.
Use the Model Library and inference-assignment tools for those owner actions.
The corresponding tool descriptions state their closed input and receipt
contracts.

## Trust model

The sidecar is a stdio process started by the MCP client as a child
process. It inherits the filesystem permissions of the user who launched
it. The trust boundary is the process boundary: the sidecar can read and
write exactly what the user can.

The sidecar always runs as `OWNER`. The `token` field in `.mcp.json` is an
identity label, not an authorization credential. No network listener is
opened; the sidecar communicates only over stdin/stdout with its parent
process.

People is a further disclosure boundary within that owner process. It defaults
to `write`; set `HOLDSPEAK_MCP_PEOPLE_ACCESS=read` or `=off` before start to
reduce or disable it. A trusted parent MCP client can retain or forward the
returned relationship metadata and shared-intent text.

## Deliberate absences

Four verbs are intentionally excluded. An always-failing tool is worse
than a missing one: it wastes a turn and breaks tool-calling agents.

| Absent verb | Reason |
|---|---|
| `coder.reply` | Requires the live web runtime's `reply_sender` callback to deliver into an agent session's tmux pane. The stdio sidecar does not own that delivery path. |
| `coder.select_session` | Requires the live filesystem-based agent context the sidecar does not hold. |
| `cadence.reply` | Requires the live agent-context pane delivery infrastructure (`submit_process_input_from_owner_gesture`). The sidecar cannot deliver replies to tmux panes. |
| `plugin_job.process` | Requires `ctx.on_process_plugin_jobs`, a live-runtime callback the sidecar does not hold. Queue processing runs in the web server. |

Each tool description in the affected family names the absence so an MCP
client discovers it at tool-listing time, not at call time.

## Resources

Owner discovery exposes 16 static resources and 16 resource templates. The
default non-owner discovery filters that to 15 static resources and 14
templates, or 29 total. List results are bounded to the first 100 items per
read.

### Static resources

| URI | Content |
|---|---|
| `holdspeak://desk/schema` | Primitive kinds, product nouns, synchronization classes |
| `holdspeak://desk/verbs` | Registered desk verbs, scopes, key bindings |
| `holdspeak://desk/constitution` | The project's constitutional context |
| `holdspeak://inference/capabilities` | Owner-only registered intelligence jobs, result contracts, requirements, boundaries, and retry-policy facts; never profiles, paths, keys, or assignments |
| `holdspeak://desk/snapshot` | Current desk state (objects, layout) |
| `holdspeak://workbenches` | Workbench list and summaries |
| `holdspeak://recipes` | Agent recipe list |
| `holdspeak://dictation/journal` | Stored dictation entries |
| `holdspeak://follow-through/board` | Follow-through execution lanes |
| `holdspeak://briefs/latest` | Latest Monday Brief (or null) |
| `pipeline://events/recent` | Recent pipeline events |
| `pipeline://events/stats` | Pipeline event statistics |
| `holdspeak://cadence/status` | Cadence engine status (enabled, pressure, loop counts) |
| `holdspeak://people/readiness` | Content-free People MCP access/store readiness |
| `holdspeak://people/relationships` | Active relationship metadata when People MCP read access is enabled |
| `holdspeak://thoughts/unfinished` | Bounded owner Resume projection for unfinished Thoughts |

### Resource templates

| URI template | Content |
|---|---|
| `holdspeak://primitives/{kind}/{id}` | One desk primitive by kind and id |
| `holdspeak://workbenches/{id}` | One workbench with its items and run summary |
| `holdspeak://workbenches/{id}/runs` | Run history for one workbench |
| `holdspeak://recipes/{id}` | One agent recipe |
| `holdspeak://zones/{id}/members` | Members of one desk zone |
| `holdspeak://meetings/{id}` | One archived meeting |
| `holdspeak://decision-records/{id}` | One decision record with evidence and revision trail |
| `pipeline://events/recent/{service}` | Recent pipeline events for one service |
| `pipeline://events/correlation/{id}` | Pipeline events in one correlation chain |
| `holdspeak://people/relationships/{id}` | One relationship with shared-intent records only |
| `holdspeak://thoughts/{thought_id}` | One canonical Thought with its working Note, visible attachment metadata/state, and public continuity |
| `holdspeak://thoughts/{thought_id}/reviews/{review_result_id}` | One validated receipt-gated review card with frozen cursors, Used-context metadata when present, and placement/egress receipt |
| `holdspeak://thoughts/{thought_id}/workbench` | One coherent owner Workbench projection: Note authority, interview state, actions, context health, and placement truth |
| `holdspeak://thoughts/{thought_id}/original` | The owner-only raw capture for a Thought; read lazily and never included in the Workbench projection |
| `holdspeak://inference/acquisitions/{id}` | Owner-only durable download, verification, installation, and activation truth |
| `holdspeak://inference/capabilities/{capability_id}` | Owner-only exact registered contract for one intelligence capability |

## The project palette (MCP-007)

The project family ships a `PROJECT_PALETTE`: a frozen set of the 47
project.*, provider.* and connection.* tool names. Two functions in the MCP layer
consume it.

`tools_for_palette(palette)` returns only the tools whose names are in
the palette. A client that lists tools through this filter sees 47 tools
instead of 197.

`dispatch_for_palette(name, arguments, principal, palette)` dispatches
a tool call only if `name` is in the palette. A name outside the palette
gets a typed refusal ("Tool ... is not in the configured palette"), never
a silent ignore.

The palette contains exactly the tools in this family. The SS15
acceptance scenario resolves entirely within project.* and provider.*;
no companion families from other domains are needed.

### Project thread mode

A Project thread mode is seeded alongside the palette. It identifies
project-agent threads and sets a scoped system prompt. The mode carries
no thread-side tools today (its tool set is empty) because all project
tools are MCP-only. If project tools register in the thread-side
TOOL_NAMES in the future, the mode's palette will surface them
automatically through the existing `palette_for` species.

## Worked example: the project lifecycle (SS15)

The transcript excerpts below are from a real MCP walk that drove the
full lifecycle over stdio. The walk ran twice with deterministic results.
Each excerpt is real structured output, trimmed where noted.

### 1. Boot the sidecar

Wire the sidecar into your MCP client (see Wiring above). The server
speaks stdio JSON-RPC; it opens the local database on startup.

### 2. Start the setup interview and create a project

Start a session, answer questions, then finalize to create the project
atomically:

```json
{"tool": "project.setup.start", "arguments": {}}
// result: {"id": "psetup_22e34a18403a", "stage": "outcome", "state": "active"}

{"tool": "project.setup.answer", "arguments": {
  "session_id": "psetup_22e34a18403a",
  "question_id": "outcome",
  "payload": {"text": "Track CI health on my repos"}
}}

{"tool": "project.setup.finalize", "arguments": {
  "session_id": "psetup_22e34a18403a",
  "command_id": "walk-finalize-001"
}}
// result (trimmed): {"project_id": "proj-adcf170869d3",
//   "name": "Track CI health on my repos",
//   "result_kind": "created", "project_revision": 1}
```

The session is durable: `project.setup.resume` returns the full state
at any point, including after finalize.

### 3. Configure the steward and set up a watch

Enable the steward with a policy, then test a watch to verify the
connector returns data:

```json
{"tool": "project.configure_steward", "arguments": {
  "project_id": "proj-adcf170869d3",
  "enabled": true,
  "unattended_enabled": true,
  "eligible_effect_kinds": [
    "refresh_sources", "create_proposals",
    "apply_proposal_effects", "draft_update", "create_door_item"
  ],
  "cooldown_seconds": 0
}}

{"tool": "project.watch.test", "arguments": {"watch_id": "cw_walk_001"}}
// result (trimmed): {"test_state": "passed",
//   "result": {"entity_count": 2, "message": "Test passed - 2 current matches"}}
```

### 4. Evaluate changes and open a review

Evaluate the watch to detect transitions, then open a review window
that materializes proposals from the observations:

```json
{"tool": "project.watch.evaluate", "arguments": {"watch_id": "cw_walk_001"}}
// result (trimmed): {"state": "completed", "transitions": 2,
//   "evaluation_id": "weval_011bee19ce0a"}

{"tool": "project.open_review", "arguments": {
  "project_id": "proj-adcf170869d3"
}}
// result: review with proposals (observation_attention, conflict)
// and source_manifest showing coverage across native + watch sources
```

### 5. Run the steward (MCP-003: prompt return, async execution)

`project.run_steward` returns the run_id immediately. Phase execution
happens on a daemon thread. Poll with `project.get_steward_run`:

```json
{"tool": "project.run_steward", "arguments": {
  "project_id": "proj-adcf170869d3",
  "watermark": "weval_011bee19ce0a",
  "command_id": "walk-steward-001"
}}
// result: {"run_id": "pstrun_104deaf8dd3b4612bec19d9bf3d34eeb", "success": true}

{"tool": "project.get_steward_run", "arguments": {
  "run_id": "pstrun_104deaf8dd3b4612bec19d9bf3d34eeb"
}}
// first poll: {"run": {"state": "queued", "phase": "observe"}, "steps": []}
// later poll: {"run": {"state": "completed", "phase": "record",
//   "summary": {"outcome": "completed"}}, "steps": [/* 11 steps elided */]}
```

### 6. Idempotent replay (MCP-002)

Replaying `run_steward` with the same `command_id` returns the original
run_id. No new run is created:

```json
{"tool": "project.run_steward", "arguments": {
  "project_id": "proj-adcf170869d3",
  "watermark": "weval_011bee19ce0a",
  "command_id": "walk-steward-001"
}}
// result: {"run_id": "pstrun_104deaf8dd3b4612bec19d9bf3d34eeb", "success": true}
// same run_id as step 5 -- the command_id dedup prevented a duplicate run
```

This holds for every effect tool: same command_id + same payload returns
the stored result. Mismatched payload with the same command_id refuses
with a typed conflict.

### 7. Draft, publish, and verify the room

Draft an update, publish it, then read the room projection to confirm
revisions:

```json
{"tool": "project.draft_update", "arguments": {
  "project_id": "proj-adcf170869d3",
  "generator": "deterministic",
  "command_id": "walk-draft-001"
}}
// result (trimmed): {"update": {"id": "pupd_aa69557dec894e1fbb568b587bcabf93",
//   "lifecycle": "draft", "generator": "deterministic"}}

{"tool": "project.publish_update", "arguments": {
  "update_id": "pupd_aa69557dec894e1fbb568b587bcabf93",
  "command_id": "walk-publish-001"
}}
// result: lifecycle -> published, project_revision bumped

{"tool": "project.get_room", "arguments": {
  "project_id": "proj-adcf170869d3"
}}
// result: coherent room projection with identity, recent changes,
// review state, published updates, and steward run history
```

The room projection is the same shape the web UI reads.

## Boundary notes

### Legacy reactions family vs. graduated watch tools

Two watch surfaces exist. The legacy reactions family
(`watch.list`, `watch.create`, `watch.set_enabled`, `watch.refresh`,
`watch.preview`, `reaction.*`) owns state='' rows. The graduated
project.watch.* tools (inspect, test, evaluate, set_rules, pause,
resume, retire) operate only on WatchSpec@1 rows (state in
active/tested/paused/retired).

The boundary is enforced in one direction today: a graduated tool
called on a legacy row refuses with `legacy_watch_boundary`. The
legacy reactions tools are not yet guarded against graduated rows
(a legacy refresh of a graduated watch is wasteful, not destructive;
the code-side guard is backlog). Nothing was replaced; both surfaces
coexist.

### What V0 refuses

Provider writes are not available through MCP. The provider.* tools
are read-only (list, connection status, bounded discovery, validation).

Remote MCP transport (MCP-008) is deferred. The sidecar speaks stdio
only; no network listener is opened.

### The fetcher seam

The sidecar's `_watch_service()` factory builds `WatchService(db)` with
no `snapshot_fetcher`. The web server injects its fetcher via
`_gh_watch_service_kwargs`. This means `project.watch.evaluate` and
`project.watch.test` need a snapshot fetcher that can reach the
GitHub API. In the walk, this was solved with a file-based fixture.
In production, watch evaluation requires live `gh` auth (the adapter
reads stored snapshots, but evaluation fetches new ones).

This is pre-existing composition debt: the web app injects the fetcher
at server startup; the sidecar does not. The watch tools will return
`connector_unavailable` when evaluation requires a live fetch and no
fetcher is composed.
