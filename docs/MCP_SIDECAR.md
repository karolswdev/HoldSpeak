# MCP sidecar

The MCP sidecar is the desk's programmable surface over stdio. It exposes
248 tools across 43 families. Any MCP client (Claude Code, Cursor, a
custom script) can read and drive the desk without the web UI.

This page is the MCP transport reference. Each tool description in the
live catalogue is the per-tool reference. This page covers how the sidecar
connects, the tool families, the resources, and the trust rules.

## Connect a client

1. Start the hub: `holdspeak web`.
2. Point your MCP client at `uv run holdspeak-mcp`. For a PyPI install,
   use `uvx --from holdspeak holdspeak-mcp`. The server speaks stdio
   JSON-RPC.

The repository ships a `.mcp.json` at the root. Claude Code finds it when
it opens the repository:

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

The sidecar finds the hub for each message. A hub that starts after your
editor works with no restart.

### Reach a hub that runs under another HOME

The sidecar finds the hub through the database path under `$HOME`. It reads
the hub token from `$HOME/.config/holdspeak/config.json`. To use a hub that
runs under another HOME, set `HOME` in the client's server entry. For Codex:

```
codex exec \
  -c mcp_servers.holdspeak.command=/abs/path/.venv/bin/holdspeak-mcp \
  -c mcp_servers.holdspeak.cwd=/abs/path \
  -c mcp_servers.holdspeak.env.HOME=/abs/path/to/the/hub/home ...
```

### Limit People access

The People family defaults to `write` for the local owner process. To
restrict it, set `HOLDSPEAK_MCP_PEOPLE_ACCESS` in the server entry:

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

Use `read` for read-only access. Use `off` to disable the family. The
People family returns only `shared_intent` material in every mode.

## How the sidecar works

The sidecar is a client of the hub. It runs as a child process of the MCP
client and **does not open the database**. For each JSON-RPC message, it:

1. Finds the running hub through the owner lock beside the database file
   (`<database>.owner.lock`). It confirms that the process is alive and
   reads the host and port from the lock.
2. Sends the message unchanged to `POST http://127.0.0.1:<port>/api/mcp`,
   with the hub's owner token from the config file.
3. Returns the hub's response unchanged.

One process owns the database. The hub dispatches every tool through the
same service layer as its HTTP routes. The sidecar always dials loopback,
even when the hub binds to another address.

**With no hub running**, the sidecar answers the handshake (`initialize`,
`ping`) and notifications locally, so your client connects. Every other
call returns a JSON-RPC error (code `-32002`) that names the situation:

```
No running HoldSpeak hub owns /Users/you/.local/share/holdspeak/holdspeak.db;
start `holdspeak web`, then retry.
```

The sidecar opens nothing in that state. It creates no database and runs
no schema step.

The sidecar has one mode. It ignores `HOLDSPEAK_MCP_STANDALONE`.

### Decisions go through the operation contract

For `kind="decisions"`, `desk.list`, `desk.get`, `desk.create` and
`desk.update` call the operations `decision.list`, `decision.read`,
`decision.create` and `decision.update` (`holdspeak/operations.py`). The
HTTP routes `GET/POST /api/decisions` and `GET/PUT /api/decisions/{id}`
call the same operations. The contract refuses unknown fields on create. It
also refuses a field that names a principal. The transport supplies the
principal.

### A write reaches the open desk

A write through MCP emits one `desk_changed` frame on the hub's `/ws` bus:

```json
{"kind": "...", "id": "...", "op": "create", "origin": "..."}
```

The `op` value is `create`, `update` or `delete`. Any open desk then reads
the change. The hub emits the frame for every write through its
`PrimitiveService` and `WorkbenchService`, whichever caller made the write
(an HTTP route, MCP over stdio, MCP over `/api/mcp`, or the iPad). Writes
that reach a table by another path (a meeting, a Project, a Thought, a sync
pull) emit no frame. Those surfaces have their own signals.

## Tool families

Tool names follow the `domain.verb` pattern. The registered tools are
organized into the families below. The generated roster after this section
lists every tool name.

| Family | What it covers |
|---|---|
| `desk` | List, read, create, update and delete desk primitives. Also the snapshot, the verbs and the needs-you list. |
| `ask` | Ask the desk a question with named grounding. |
| `thought` | Develop a durable Thought, with context and review tools. |
| `thread` | Set a Thread's status line. |
| `interview` | Read and change the Interview state of a Thread. |
| `project`, `provider`, `connection`, `steward`, `nudge`, `channel` | Projects, Watches, the Steward, providers and the Send. |
| `meeting`, `proposal`, `decision`, `decision_record`, `follow_through`, `monday_brief` | Meetings, extracted proposals, decisions and follow-through. |
| `people` | The encrypted People ledger. |
| `cadence`, `heartbeat`, `scheduled_recording`, `door` | The Cadence engine, the Heartbeat sweep, scheduled recordings and the Door. |
| `model_library`, `inference`, `inference_assignment`, `concierge`, `settings` | Models, assignments and settings. |
| `sequence`, `workflow`, `workbench`, `recipe`, `practice_recipe`, `reaction`, `watch`, `zone`, `kb` | Runs, Workbenches, recipes and Automations. |
| `memory`, `dictation`, `event`, `pipeline`, `kernel`, `plugin_job`, `coder` | Search, journals, events, receipts, queued jobs and Coder sessions. |

### Desk

`desk.list`, `desk.get`, `desk.create`, `desk.update` and `desk.delete`
work on desk primitive kinds. Six kinds are stored as typed rows. The other
kinds are computed, composite, or managed by their own capability. Each
tool description names the kinds it handles.

### Ask

`ask.resolve_grounding` hydrates grounding references without a model call.
`ask.run` submits a question through the admitted inference path and
returns the answer with its receipt. `ask.cancel` cancels a run in flight.
`ask.keep` saves an answer as a desk Artifact. Model selection is never an
MCP control on Ask.

### Project

- **Read:** `project.list`, `project.get` and `project.get_room`.
- **Commands:** create, update (with `expected_revision`), archive, restore,
  link and unlink a Meeting, open and accept a review, decide a proposal,
  and list, draft, edit, publish and mark delivered a project update.
  Every effect tool accepts an optional `command_id` for idempotent replay.
  Where the web route checks `expected_revision`, the tool checks it too.
- **Steward:** `project.configure_steward` reads or writes the policy.
  `project.run_steward` returns a run id at once and runs on a daemon
  thread. `project.stop_steward` stops a run.
  `project.get_steward_run` returns the state, steps and receipts.
  `project.steward.trigger` evaluates and runs the due work for the desk.
- **Setup:** `project.setup.start`, `.resume`, `.answer`, `.suggest`,
  `.select_proposal`, `.deselect_proposal`, `.test_proposal`,
  `.clarify_repo_scope`, `.clarify_jira_scope` and `.finalize`. The setup
  session is durable across calls. The [Interview guide](INTERVIEW.md)
  explains the conversation that drives these tools.
- **Watches:** `project.watch.inspect`, `.test`, `.evaluate`, `.set_rules`,
  `.pause`, `.resume` and `.retire`. These tools work only on graduated
  Watches. A graduated tool that targets a legacy Watch refuses with
  `legacy_watch_boundary`. `.set_rules` accepts an optional
  `evaluation_cadence_minutes` value from 1 to 10080.
- **Suggested sources:** `project.suggested_sources` lists repositories and
  issue keys that Meetings mention. `project.add_suggested_source` creates
  a Watch source from one. `project.dismiss_suggested_source` hides one.
- **Items and resources:** `project.item.*` and `project.resource.*`.
- **Nudges:** `steward.nudges` lists reviewer nudge proposals for a Project.
  `nudge.send` approves and sends one through the gated connector.
  `nudge.dismiss` closes one with no write. Both refuse a nudge that is not
  in the `proposed` state.

`project.get_room` returns the Room projection. It includes the Meeting
Watch row when Meetings link to the Room. Calendar sources have no MCP
tools. Manage them through the HTTP routes under `/api/calendar/`.

### Provider and connection

`provider.list` returns the configured providers and their readiness.
`connection.list` and `connection.recheck` read and probe connections.
Provider tools only read. HoldSpeak makes no provider writes through MCP.
A tool refuses with a typed error when its adapter is absent
(`provider_not_configured`).

- **GitHub:** `provider.github_connection`, `provider.github_discover` and
  `provider.github_validate_repo`. These use the `gh` CLI.
- **Jira:** `provider.jira_connections`, `provider.jira_add_connection`,
  `provider.jira_connection`, `provider.jira_discover`,
  `provider.jira_search` and `provider.jira_validate_scope`. These use the
  Atlassian CLI (`acli`).
- **Confluence:** `provider.confluence_connections`,
  `provider.confluence_discover` and `provider.confluence_validate_space`.

A Jira connection is a (site, email) pair. One owner can hold many.
Each call runs `auth switch`, then the command, then an `auth status`
check, under a cross-process file lock. The lock timeout is 10 seconds. Set
`HOLDSPEAK_ACLI_LOCK_TIMEOUT` (seconds) to change it. A mismatch on the
check returns a typed error. Jira calls contact `<site>.atlassian.net` from
this device. `provider.jira_search` accepts only a fixed set of search
fields. It fills other fields through per-issue `workitem view` calls.

### Thread and Interview

`thread.set_status` writes the Thread's status line. `interview.get`,
`interview.change_section`, `interview.record_fact` and
`interview.suggest` expose the Interview state of a Thread. Commands keep
revision checks and source provenance. See [Agents and Threads](AGENTS_AND_THREADS.md).

### Thought

A Thought develops through one explicit model turn at a time.

- `thought.refine` asks one question from server-loaded material.
  `thought.reconcile` finalizes known durable proof.
  `thought.stop_refinement` suppresses a run before best-effort
  cancellation.
- `thought.answer_review`, `thought.accept_review` and
  `thought.reject_review` consume one receipt-gated review. They never
  start the next model turn.
- `thought.list_context`, `thought.attach_context`,
  `thought.detach_context` and `thought.refresh_context` manage context.
  They accept qualified references and cursors only. They never accept note
  bodies or prompt text. None calls a model.
- `thought.create` and `thought.adopt_note` create or adopt a Thought and
  return its default-context receipt. `thought.get_default_context` and
  `thought.replace_default_context` read and replace the default context
  set. The default is empty until you set it. It applies only to later
  create or adopt calls.
- `thought.update_working`, `thought.answer_and_continue`,
  `thought.complete` and `thought.resume` drive the Workbench.

The refine schema accepts no prompt, model or raw text. MCP supplies
identities and cursors. The Thought service loads the content, as the web
surface does. A command failure is a structured tool error. `error` holds
the readable detail and `code` holds the stable service code.

### Model library

- `model_library.*` are owner-only commands over the Model Library service:
  `get`, `download`, `add_to_library`, `use_model_file`,
  `connect_hosted_model`, `define_endpoint` and `connect_paired_device`.
  They add or connect models. They never select a model for a capability.
  File intake accepts a request id, a basename and base64 bytes, up to
  16 MiB decoded. Client paths are refused. Hosted-provider secrets go in a
  write-only `secret` field. They never appear in errors, logs or receipts.
- `inference.cancel_model_acquisition` cancels a download before
  verification starts.

### Assignments and settings

- `inference_assignment.summary`, `.editor`, `.set`,
  `.preview_use_default` and `.clear` read and change assignments.
- `concierge.detect`, `.propose`, `.probe`, `.apply` and `.download` detect
  engines and apply a proposed assignment. A paid cloud probe needs
  `generate: true`.
- `settings.get` returns the configuration with secrets removed and a
  `_revision` value. `settings.update` applies a partial patch.
  `settings.hub` reads the hub state. `settings.update` cannot write
  secrets or inference assignments. Use the Model Library and assignment
  tools for those.

### Sequence

`sequence.run` runs a sequence through the admitted inference path.
`sequence.cancel` cancels a run by its parent operation id.
`workflow.run` and `workflow.cancel` do the same for a Workflow.

### Meetings, decisions and follow-through

`meeting.proposals` returns the pending proposals for a Meeting. It leaves
out proposals that are `confirmed` or `dismissed`. `proposal.confirm`
writes a decision record and a commitment for one `proposed` proposal. You
can override `text`, `owner` and `due`. `proposal.dismiss` marks one
`dismissed` and writes no record. Both refuse a proposal that is not
`proposed`.

### Cadence and Heartbeat

`cadence.status`, `.loops`, `.get_loop`, `.brief`, `.closeout`, `.history`
and `.audit` read the engine. `cadence.snooze`, `.set_status`, `.run_now`
and `.apply_closeout` change only the local database.

`heartbeat.status` reads the sweep settings. `heartbeat.run_now` runs one
sweep and returns the receipt. `heartbeat.set` updates
`sweep_every_minutes` (1 to 1440), `quiet_hours` (`{start, end}`), `notify`
(`off`, `edge` or `every_sweep`) and `muted_projects`.
`heartbeat.notify_test` fires one test notification.

### Memory

`memory.search` queries the long-horizon memory store with optional kind,
project, time and pagination filters. Valid kinds are `decision`,
`decision_record`, `desk_decision`, `artifact`, `meeting`, `note`,
`thread`, `action`, `project_item`, `workbench_item` and `cadence`. Each
hit states whether it matched by text or arrived over a relationship.
`memory.page` and `memory.observations` read memory pages and observations.

### People

`people.readiness` is content free and works while access is off. In
`read` mode, the family lists relationships and reads one relationship's
`shared_intent` 1:1s, agenda items, grounding notes, linked Project
references, requests and commitments. `people.grounding.get` returns those
accepted sources as an evidence bundle. It calls no model.

The default `write` mode also admits these tools:

- relationship, note, 1:1 and agenda creation;
- request creation and acceptance;
- commitment transitions;
- calendar and owner-alias link and unlink.

`people.resolve` matches an identity string against owner aliases and
display names inside the encrypted store. It returns an opaque
relationship id, or a typed `no_match`. It never writes.

MCP never starts or recovers the encrypted store. It never returns
leader-private sessions, prep, agenda, notes, requests or commitments. It
has no People archive, delete, capture, transcript, inference, scoring,
search, sync, export or connector tool. Tool results pass to your MCP
client over stdio. HoldSpeak does not write them to its plaintext
database, FTS index or Cadence.

### Other tools

- `plugin_job.list` and `.summary` read deferred plugin jobs.
  `plugin_job.retry` re-queues a job. `plugin_job.cancel` marks a job completed.
  Both refuse a running job.
- `coder.list`, `coder.get` and `coder.audit` read Coder sessions and the
  steering audit. See [Coder integration](CODER_INTEGRATION.md).
- `door.get` returns the Dashboard Door aggregate. `door.add_item` creates
  an action item. In a Thread, the Normal and Secure postures hold the
  call in the decision box.

<!-- BEGIN MCP TOOL ROSTER (machine-generated -- do not edit) -->

**Registry totals:** 248 tools across 43 families.

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

#### channel (9)

- `channel.check_destination`
- `channel.destinations`
- `channel.discard`
- `channel.prepare`
- `channel.preview`
- `channel.remove_destination`
- `channel.save_destination`
- `channel.send`
- `channel.sends`

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

#### interview (4)

- `interview.change_section`
- `interview.get`
- `interview.record_fact`
- `interview.suggest`

#### kb (3)

- `kb.add_member`
- `kb.list_members`
- `kb.remove_member`

#### kernel (1)

- `kernel.receipt`

#### meeting (9)

- `meeting.delete`
- `meeting.export`
- `meeting.get`
- `meeting.import`
- `meeting.list`
- `meeting.proposals`
- `meeting.run_intelligence`
- `meeting.start_capture`
- `meeting.stop_capture`

#### memory (3)

- `memory.observations`
- `memory.page`
- `memory.search`

#### model_library (7)

- `model_library.add_to_library`
- `model_library.connect_hosted_model`
- `model_library.connect_paired_device`
- `model_library.define_endpoint`
- `model_library.download`
- `model_library.get`
- `model_library.use_model_file`

#### monday_brief (4)

- `monday_brief.generate`
- `monday_brief.get`
- `monday_brief.shelf`
- `monday_brief.shelf_read`

#### nudge (2)

- `nudge.dismiss`
- `nudge.send`

#### people (17)

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
- `people.resolve`

#### pipeline (1)

- `pipeline.events`

#### plugin_job (4)

- `plugin_job.cancel`
- `plugin_job.list`
- `plugin_job.retry`
- `plugin_job.summary`

#### practice_recipe (3)

- `practice_recipe.compile`
- `practice_recipe.get`
- `practice_recipe.list`

#### project (50)

- `project.accept_review`
- `project.add_suggested_source`
- `project.archive`
- `project.configure_steward`
- `project.create`
- `project.decide_proposal`
- `project.dismiss_suggested_source`
- `project.draft_update`
- `project.get`
- `project.get_delta`
- `project.get_room`
- `project.get_steward_run`
- `project.item.create`
- `project.item.list`
- `project.item.transition`
- `project.item.update`
- `project.link`
- `project.list`
- `project.list_updates`
- `project.mark_update_delivered`
- `project.open_review`
- `project.publish_update`
- `project.resource.add`
- `project.resource.list`
- `project.resource.remove`
- `project.restore`
- `project.run_steward`
- `project.setup.answer`
- `project.setup.clarify_jira_scope`
- `project.setup.clarify_repo_scope`
- `project.setup.deselect_proposal`
- `project.setup.finalize`
- `project.setup.resume`
- `project.setup.select_proposal`
- `project.setup.start`
- `project.setup.suggest`
- `project.setup.test_proposal`
- `project.steward.trigger`
- `project.stop_steward`
- `project.suggested_sources`
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

#### proposal (2)

- `proposal.confirm`
- `proposal.dismiss`

#### provider (13)

- `provider.confluence_connections`
- `provider.confluence_discover`
- `provider.confluence_validate_space`
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

#### steward (1)

- `steward.nudges`

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

A tool that starts model work uses the same owner service authority as
HTTP. It cannot choose a provider, change an admitted run, or bypass the
capability and assignment checks. Results carry the receipt and placement
for that operation. The
[Intelligence Router architecture](internal/ARCHITECTURE_INTELLIGENCE_ROUTER.md)
describes routing, frozen plans, fallback and receipts. This page does not
repeat them.

## Trust model

The sidecar is a stdio process that your MCP client starts. It has the file
permissions of the user who launched it. The trust boundary is the process
boundary. It opens no network listener.

The sidecar sends the hub's owner token, which it reads from
`$HOME/.config/holdspeak/config.json`. The hub admits that token only from
a loopback request. If no token exists, run `holdspeak web` once on this
machine so the hub writes one.

People is a further boundary inside the owner process. A trusted MCP client
can keep or forward the relationship metadata and shared-intent text that
it receives.

## Deliberate absences

Four verbs do not exist. A tool that always fails wastes a turn, so the
catalogue leaves it out.

| Absent verb | Reason |
|---|---|
| `coder.reply` | Delivery into a tmux pane needs the live web runtime. |
| `coder.select_session` | Selection needs live agent context that the sidecar does not hold. |
| `cadence.reply` | Reply delivery needs the live runtime. |
| `plugin_job.process` | Queue processing runs in the web server. |

Use the Desk or the HTTP routes for these actions.

## Resources

Owner discovery exposes 16 static resources and 21 resource templates. The
default non-owner discovery filters that to 15 static resources and
19 templates, or 34 total. A list result holds at most 100 items.

### Static resources

| URI | Content |
|---|---|
| `holdspeak://desk/schema` | Primitive kinds, product nouns, synchronization classes |
| `holdspeak://desk/verbs` | Registered desk verbs, scopes, key bindings |
| `holdspeak://desk/constitution` | The project's constitutional context |
| `holdspeak://inference/capabilities` | Owner-only registered intelligence jobs, result contracts, requirements and boundaries; never profiles, paths, keys or assignments |
| `holdspeak://desk/snapshot` | Current desk state |
| `holdspeak://workbenches` | Workbench list and summaries |
| `holdspeak://recipes` | Agent recipe list |
| `holdspeak://dictation/journal` | Stored dictation entries |
| `holdspeak://follow-through/board` | Follow-through lanes |
| `holdspeak://briefs/latest` | Latest Monday Brief, or null |
| `pipeline://events/recent` | Recent pipeline events |
| `pipeline://events/stats` | Pipeline event statistics |
| `holdspeak://cadence/status` | Cadence engine status |
| `holdspeak://people/readiness` | Content-free People access and store readiness |
| `holdspeak://people/relationships` | Active relationship metadata, when People read access is on |
| `holdspeak://thoughts/unfinished` | Owner Resume projection for unfinished Thoughts |

### Resource templates

| URI template | Content |
|---|---|
| `holdspeak://primitives/{kind}/{id}` | One desk primitive |
| `holdspeak://workbenches/{id}` | One Workbench with its items and run summary |
| `holdspeak://workbenches/{id}/runs` | Run history for one Workbench |
| `holdspeak://recipes/{id}` | One agent recipe |
| `holdspeak://zones/{id}/members` | Members of one desk zone |
| `holdspeak://meetings/{id}` | One archived Meeting |
| `holdspeak://decision-records/{id}` | One decision record with evidence and revision trail |
| `pipeline://events/recent/{service}` | Recent pipeline events for one service |
| `pipeline://events/correlation/{id}` | Pipeline events in one correlation chain |
| `holdspeak://people/relationships/{id}` | One relationship, shared-intent records only |
| `holdspeak://thoughts/{thought_id}` | One Thought with its working Note, attachments and continuity |
| `holdspeak://thoughts/{thought_id}/reviews/{review_result_id}` | One receipt-gated review card |
| `holdspeak://thoughts/{thought_id}/workbench` | The owner Workbench projection |
| `holdspeak://thoughts/{thought_id}/original` | The raw capture of a Thought, read on request |
| `holdspeak://inference/acquisitions/{id}` | Owner-only download, verification and install state |
| `holdspeak://inference/capabilities/{capability_id}` | Owner-only contract for one intelligence capability |
| `holdspeak://projects/{project_id}` | One Project |
| `holdspeak://projects/{project_id}/room` | The Project Room projection |
| `holdspeak://projects/{project_id}/delta` | The Project delta |
| `holdspeak://projects/{project_id}/updates/{update_id}` | One Project update |
| `holdspeak://projects/{project_id}/steward/runs/{run_id}` | One Steward run |

An unknown id refuses with a typed error.

## The project palette

The project family ships a `PROJECT_PALETTE`: a frozen set of the 65
project.*, provider.* and connection.* tool names. Two functions in the MCP layer
use it.

`tools_for_palette(palette)` returns only the tools in the palette. A
client that lists tools through this filter sees 65 tools
instead of 248.

`dispatch_for_palette(name, arguments, principal, palette)` runs a tool
only if `name` is in the palette. A name outside the palette gets a typed
refusal, never a silent ignore.

The named palettes are `PROJECT`, `SWEEP`, `DESK` and `ALL`
(`holdspeak/mcp/palettes.py`). `PROJECT` adds `kernel.receipt` and the
`channel.*` tools to the project palette. `SWEEP` adds the `heartbeat.*`
tools to `PROJECT`.

## Transports

`handle_message` runs behind three transports. All three announce the same
protocol version.

| Transport | Entry point | Principal | Palette |
|---|---|---|---|
| **stdio** (the sidecar) | `holdspeak-mcp`, which proxies to the hub | `OWNER` | none |
| **in-process** (the web runtime) | direct call to `handle_message` | inherited from the web session | inherited |
| **Streamable HTTP** | `POST /api/mcp` on the hub | `AGENT` from a scoped credential | from the credential |

### `POST /api/mcp` and the Reach flag

The setting `remote.streamable_http_enabled` controls the remote listener.
It is off by default. The route derives the principal as follows:

| Request | Result |
|---|---|
| Loopback with the owner token | `OWNER`. Admitted with the flag off. This is the path the sidecar uses. |
| Loopback with an agent credential | `AGENT`, with the credential's palette. Needs the flag on. |
| Non-loopback with an agent credential | `AGENT`, with the credential's palette. Needs the flag on. |
| Non-loopback with the owner token | Refused with 403. |
| No match | Refused with 401. |

The hub never reads `X-Forwarded-For` to derive a principal.

A scoped credential carries a palette and a time to live (TTL). The
default TTL is 12 hours. The maximum is 30 days. The hub shows the token
once at issue and stores only a hash. Issue and revoke credentials with
`POST /api/settings/remote/credentials` and
`DELETE /api/settings/remote/credentials/{id}`. A call outside the palette
returns a typed refusal.

## Watch tools and the fetcher

`project.watch.evaluate` and `project.watch.test` need a snapshot fetcher
that can reach the source. For GitHub, this needs live `gh` authentication.
The hub injects the fetcher at startup. When a call needs a live fetch and
no fetcher exists, the tool returns `connector_unavailable`.

`project.watch.evaluate` records `watch_effects`, as a scheduled
evaluation does. It uses the same evaluation-derived idempotency key. A
manual run followed by a scheduled one makes one effect. The first
evaluation of a Watch with no baseline is silent. It sets the baseline and
returns `state: "baselined"` with zero transitions, observations and
effects.

## Legacy Watches

Two Watch surfaces exist. The `watch.*` and `reaction.*` families own
legacy Watches. The `project.watch.*` tools own graduated Watches. A
graduated tool refuses a legacy Watch. A legacy tool does not refuse a
graduated Watch. A legacy refresh of a graduated Watch wastes work and
destroys nothing.

## Example: the project lifecycle

The calls below create a Project and run the Steward over stdio. Start
`holdspeak web` first. Each result is trimmed.

1. Start the setup, answer a question and finalize:

   ```json
   {"tool": "project.setup.start", "arguments": {}}
   // {"id": "psetup_...", "stage": "outcome", "state": "active"}

   {"tool": "project.setup.answer", "arguments": {
     "session_id": "psetup_...", "question_id": "outcome",
     "payload": {"text": "Track CI health on my repos"}}}

   {"tool": "project.setup.finalize", "arguments": {
     "session_id": "psetup_...", "command_id": "finalize-001"}}
   // {"project_id": "proj-...", "result_kind": "created", "project_revision": 1}
   ```

   `project.setup.resume` returns the full session state at any point.

2. Enable the Steward and test a Watch:

   ```json
   {"tool": "project.configure_steward", "arguments": {
     "project_id": "proj-...", "enabled": true, "unattended_enabled": true,
     "eligible_effect_kinds": ["refresh_sources", "create_proposals",
       "apply_proposal_effects", "draft_update", "create_door_item"],
     "cooldown_seconds": 0}}

   {"tool": "project.watch.test", "arguments": {"watch_id": "cw_..."}}
   // {"test_state": "passed"}
   ```

3. Evaluate the Watch and open a review:

   ```json
   {"tool": "project.watch.evaluate", "arguments": {"watch_id": "cw_..."}}
   // {"state": "completed", "transitions": 2, "evaluation_id": "weval_..."}

   {"tool": "project.open_review", "arguments": {"project_id": "proj-..."}}
   ```

4. Run the Steward. The call returns a run id at once. Poll for the state:

   ```json
   {"tool": "project.run_steward", "arguments": {
     "project_id": "proj-...", "watermark": "weval_...",
     "command_id": "steward-001"}}
   // {"run_id": "pstrun_...", "success": true}

   {"tool": "project.get_steward_run", "arguments": {"run_id": "pstrun_..."}}
   // {"run": {"state": "completed", "phase": "record"}, "steps": [...]}
   ```

5. Replay a command. The same `command_id` with the same payload returns
   the stored result and makes no new run. The same `command_id` with a
   different payload refuses with a typed conflict.

6. Draft and publish an update, then read the Room:

   ```json
   {"tool": "project.draft_update", "arguments": {
     "project_id": "proj-...", "generator": "deterministic",
     "command_id": "draft-001"}}

   {"tool": "project.publish_update", "arguments": {
     "update_id": "pupd_...", "command_id": "publish-001"}}

   {"tool": "project.get_room", "arguments": {"project_id": "proj-..."}}
   ```

   The Room projection has the same shape as the web UI reads.
