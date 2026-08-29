# MCP sidecar

The MCP sidecar is the desk's programmable surface over stdio. It exposes
140 tools across 30 families. The default non-owner discovery lists 29
resources; the owner discovery lists 32 because access filtering admits 16
static resources and 16 templates. Any MCP client (Claude Code, Cursor, a
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

The 140 tools are organized into domain families. Each tool follows the
`domain.verb` naming convention. Tool descriptions are the per-tool
reference; this page covers the families and the cross-cutting rules.

### desk (47 tools)

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

### door (1 tool)

`door.get` returns one closed, read-only Dashboard Door aggregate: the board,
active Thoughts, and a mixed upcoming timeline of calendar events (from all
enabled ICS sources, with per-source provenance when more than one source is
configured) and scheduled recordings, plus matching server-derived counts.
Door has no MCP resource. Its
Follow-Through People overlay respects `HOLDSPEAK_MCP_PEOPLE_ACCESS` and is
safely empty when that encrypted disclosure capability is unavailable or off.

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
project, time, and pagination filters.

### people (11 tools)

The encrypted People ledger defaults to `write` for the local owner process.
`people.readiness` is content-free and also works while access is explicitly
disabled. Set `HOLDSPEAK_MCP_PEOPLE_ACCESS=read` to restrict the sidecar to
listing relationships and reading one relationship's `shared_intent` 1:1s,
agenda items, grounding notes, linked Project refs, requests, and commitments.
`people.grounding.get` returns those accepted manual sources as a structured
evidence bundle; it does not invoke a model or infer an assessment. The default
`write` capability additionally admits relationship and grounding-note creation,
notes-only 1:1 and agenda creation, request creation/explicit acceptance, and
done/dismiss/reopen for shared commitments.

MCP never initializes or recovers the encrypted store and never returns
leader-private sessions, private prep, agenda, grounding notes, requests, or commitments. It
also offers no People archive/delete, capture/transcript, inference, scoring,
search, sync, export, connector, or employment-decision tool. Tool results are
transient stdio disclosure to the explicitly trusted parent client; they are
not written to HoldSpeak's plaintext database, observer, FTS, or Cadence.

### plugin_job (4 tools)

`plugin_job.list` and `plugin_job.summary` read deferred plugin job state.
`plugin_job.retry` re-queues a failed or completed job. `plugin_job.cancel`
marks a job done. Both refuse running jobs.

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
