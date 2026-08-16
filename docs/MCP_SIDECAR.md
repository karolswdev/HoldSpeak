# MCP sidecar

The MCP sidecar is the desk's programmable surface over stdio. It exposes
82 tools and 24 resources through the Model Context Protocol, so any MCP
client (Claude Code, Cursor, a custom script) can read and drive the desk
without touching the web UI.

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

## Tool families

The 82 tools are organized into families. Each tool follows the
`domain.verb` naming convention. Tool descriptions are the per-tool
reference; this page covers the families and the cross-cutting rules.

### desk (47 tools)

The original surface. CRUD for desk primitives (meetings, notes, artifacts,
projects, decision records, zones, workbenches, recipes, agents, sequences,
workflows), the pipeline observer, follow-through lanes, inference
invocations, and the Monday Brief. Five of the `desk.*` tools
(`desk.list`, `desk.get`, `desk.create`, `desk.update`, `desk.delete`)
operate on the primitive kind system: 6 surface kinds are stored as typed
rows; the remaining 11 are computed or composite. Each description names
which kinds it handles.

### ask (5 tools)

Ask the desk a question. `ask.models` lists available inference
destinations. `ask.resolve_grounding` hydrates grounding references
without running inference. `ask.run` submits a question through the
admitted inference path and returns the answer with its receipt.
`ask.cancel` cancels an in-flight invocation. `ask.keep` persists an
answer as a desk artifact (not model-invoking).

### settings (2 tools)

`settings.get` returns the current configuration with secrets redacted
and a `_revision` field for optimistic concurrency. `settings.update`
applies a partial patch. Secrets cannot be written through this tool.
Changing `intel_provider`, `intel_profile_id`, or destination assignments
may change the product's egress boundary; the response's `_placement`
block shows the effective placement after the write.

### destination (5 tools)

CRUD for inference destinations. `destination.list` returns all
destinations with current mesh-node liveness. `destination.get`,
`destination.create`, `destination.update`, and `destination.delete`
manage individual destinations. Secrets cannot be read or written
through these tools.

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

### plugin_job (4 tools)

`plugin_job.list` and `plugin_job.summary` read deferred plugin job state.
`plugin_job.retry` re-queues a failed or completed job. `plugin_job.cancel`
marks a job done. Both refuse running jobs.

## Model-invoking tools

Four tools reach an inference provider. Each rides the admitted
`InferenceRunner.invoke()` path; no tool opens a side door.

| Tool | Admitted path |
|---|---|
| `ask.run` | `AskService.ask()` enters `InferenceRunner.invoke()` via `_as_principal` |
| `cadence.get_loop` | Conditional: when the loop's `use_llm` is true, enters the kernel through `_drafted_next_action` |
| `sequence.run` | `SequenceWorkflowService.run_sequence()` enters `InferenceRunner.invoke()` via `_as_principal` |
| `workflow.run` | `SequenceWorkflowService.run_workflow()` enters `InferenceRunner.invoke()` via `_as_principal` |

Every model-invoking result carries a receipt: `model`, `provider`,
`egress`, and `actual_placement` (`_placement`). The receipt names what
ran and where, so the caller can verify the egress boundary after the
fact.

**Placement provenance.** Each model-invoking result also carries
`placement.effective_target_id` and `placement.source`. The source names
which precedence tier decided the run's destination: `invocation`,
`workbench`, `agent`, or `global`.

## The egress note on settings.update

`settings.update` can change the product's egress boundary by reassigning
which inference destination a feature uses. The tool description carries this
warning, and the response includes a `_placement` block showing the
effective placement after the write. This is a constitutional requirement
(Article III.2: egress disclosed at the point of decision).

## Trust model

The sidecar is a stdio process started by the MCP client as a child
process. It inherits the filesystem permissions of the user who launched
it. The trust boundary is the process boundary: the sidecar can read and
write exactly what the user can.

The sidecar always runs as `OWNER`. The `token` field in `.mcp.json` is an
identity label, not an authorization credential. No network listener is
opened; the sidecar communicates only over stdin/stdout with its parent
process.

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

The sidecar exposes 14 static resources and 10 resource templates. List
results are bounded to the first 100 items per read.

### Static resources

| URI | Content |
|---|---|
| `holdspeak://desk/schema` | Primitive kinds, product nouns, synchronization classes |
| `holdspeak://desk/verbs` | Registered desk verbs, scopes, key bindings |
| `holdspeak://desk/constitution` | The project's constitutional context |
| `holdspeak://desk/inference-targets` | Available inference destinations |
| `holdspeak://desk/snapshot` | Current desk state (objects, layout) |
| `holdspeak://workbenches` | Workbench list and summaries |
| `holdspeak://recipes` | Agent recipe list |
| `holdspeak://destinations` | Redacted inference destination list |
| `holdspeak://dictation/journal` | Stored dictation entries |
| `holdspeak://follow-through/board` | Follow-through execution lanes |
| `holdspeak://briefs/latest` | Latest Monday Brief (or null) |
| `pipeline://events/recent` | Recent pipeline events |
| `pipeline://events/stats` | Pipeline event statistics |
| `holdspeak://cadence/status` | Cadence engine status (enabled, pressure, loop counts) |

### Resource templates

| URI template | Content |
|---|---|
| `holdspeak://primitives/{kind}/{id}` | One desk primitive by kind and id |
| `holdspeak://workbenches/{id}` | One workbench with its items and run summary |
| `holdspeak://workbenches/{id}/runs` | Run history for one workbench |
| `holdspeak://recipes/{id}` | One agent recipe |
| `holdspeak://destinations/{id}` | One inference destination (redacted) |
| `holdspeak://zones/{id}/members` | Members of one desk zone |
| `holdspeak://meetings/{id}` | One archived meeting |
| `holdspeak://decision-records/{id}` | One decision record with evidence and revision trail |
| `pipeline://events/recent/{service}` | Recent pipeline events for one service |
| `pipeline://events/correlation/{id}` | Pipeline events in one correlation chain |
