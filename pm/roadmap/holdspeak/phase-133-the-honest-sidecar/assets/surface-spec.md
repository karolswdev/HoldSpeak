# Phase 133 Surface Specification — The Honest Sidecar

**Status:** RULED — counsel review complete (2026-08-16); the four counsel
conditions are folded in below and recorded in "Counsel ruling record" at
the end. Implementation targets THIS revision.
**Scope:** MCP sidecar completeness + honesty sweep
**Base commit:** `d4acbbe7` (main, 2026-08-16)

---

## Part 1 — New Tool Families

### Naming convention

Every new tool follows the existing `domain.verb` law.
Every `inputSchema` carries `"additionalProperties": false`.

---

### 1A. AskService (`holdspeak/services/ask_service.py`)

The Ask surface is MODEL-INVOKING. It rides the existing admitted
inference path: `AskService.ask()` (:117) calls `self._invoke()` (:59)
which enters `InferenceRunner.invoke()` inside an `_as_principal` context
after `resolve_placement` + `capture_deployment_revision`. The MCP tool
dispatches through `AskService.ask()` exactly as the web route does
(`holdspeak/web/routes/primitives/ask.py`:44-52) and returns the same
result dict, which already carries `model`, `provider`,
`actual_placement`, `egress`, and `grounding_claims` -- the receipt
identity is already honest.

`ask.cancel` rides `AskService.cancel()` (:200) which enters
`InferenceRunner.cancel()` inside `_as_principal` -- no side door.

`ask.keep` is NOT model-invoking; it persists an artifact via
`AskService.keep()` (:205) -- a pure write.

`ask.list_models` is a read; it calls `AskService.list_models()` (:64).

`ask.resolve_grounding` is a read; it calls
`AskService.resolve_grounding()` (:107).

| Tool | R/W | Service method | Dispatch |
|---|---|---|---|
| `ask.models` | R | `AskService.list_models(principal)` | ask_service.py:64 |
| `ask.resolve_grounding` | R | `AskService.resolve_grounding(principal, refs)` | ask_service.py:107 |
| `ask.run` | W (model-invoking) | `AskService.ask(principal, question, grounding, ...)` | ask_service.py:117 |
| `ask.cancel` | W | `AskService.cancel(principal, invocation_id)` | ask_service.py:200 |
| `ask.keep` | W | `AskService.keep(principal, output, sources, ...)` | ask_service.py:205 |

#### Tool schemas

```json
{
  "name": "ask.models",
  "description": "List available inference destinations for Ask. Each row names the model the destination loads.",
  "inputSchema": {
    "type": "object",
    "properties": {},
    "additionalProperties": false
  }
}
```

```json
{
  "name": "ask.resolve_grounding",
  "description": "Resolve grounding references and return their hydrated titles and character counts without running inference.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "refs": {
        "type": "array",
        "items": {"type": "string"},
        "maxItems": 20,
        "description": "Qualified grounding references (e.g. 'note:abc', 'meeting:xyz')."
      }
    },
    "required": ["refs"],
    "additionalProperties": false
  }
}
```

```json
{
  "name": "ask.run",
  "description": "Ask the desk a question. MODEL-INVOKING: rides the admitted RunLifecycle path. The result carries the receipt (model, provider, egress, actual_placement) so the caller knows what ran and where.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "question": {"type": "string", "description": "The prompt to ask."},
      "lens": {"type": "string", "description": "Label for this Ask turn (default 'Ask')."},
      "inference_target_id": {"type": "string", "description": "Inference destination id. Omit for the hub default."},
      "context": {
        "type": "array",
        "items": {"type": "object"},
        "description": "Material context entries [{id, kind, title}]."
      },
      "grounding": {
        "type": "object",
        "description": "Grounding payload: meeting_ids, artifact_ids, refs, expand."
      },
      "max_tokens": {"type": "integer", "minimum": 1},
      "temperature": {"type": "number", "minimum": 0, "maximum": 2}
    },
    "required": ["question"],
    "additionalProperties": false
  }
}
```

```json
{
  "name": "ask.cancel",
  "description": "Cancel an in-flight Ask invocation by its invocation_id.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "invocation_id": {"type": "string", "description": "The invocation_id returned by ask.run."}
    },
    "required": ["invocation_id"],
    "additionalProperties": false
  }
}
```

```json
{
  "name": "ask.keep",
  "description": "Persist an Ask answer as a desk artifact. Not model-invoking.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "output": {"type": "string", "description": "The answer text to persist."},
      "sources": {
        "type": "array",
        "items": {"type": "object"},
        "description": "Source entries [{id, kind, title, ref}]."
      },
      "lens": {"type": "string"},
      "prompt": {"type": "string"},
      "grounding": {"type": "object"}
    },
    "required": ["output"],
    "additionalProperties": false
  }
}
```

**Dispatch notes:**
- `ask.run` is async (`AskService.ask` is a coroutine). Dispatch wraps it
  in `_run()` (the existing `asyncio.run` / active-loop pattern at
  tools.py:406-411).
- The `AskService` constructor requires `db`, `hub_model` (retired but
  accepted), `broadcast`, `rails_hydrator`, `observer`, and optionally
  `broker`. The MCP dispatch constructs it with `db=get_database()`,
  `observer=get_observer()`, no `broadcast` (MCP is request/response; the
  caller sees the result, not intermediate WS frames), no
  `rails_hydrator` (the web route supplies it from the Astro context;
  the MCP sidecar has no Astro context -- grounding through `refs` still
  works, grounding through `rails` returns an empty hydration). This is
  honest: the MCP surface is not a web surface.

**Resources:** No new Ask resources. `ask.models` is a tool because it is
a point-in-time read (inference-target liveness changes within seconds).

---

### 1B. SettingsService (`holdspeak/services/settings_service.py`)

Read and write of the on-disk configuration. The service already validates
all sections (model, hotkey, UI, meeting, dictation, wake_word,
rails_observer, device, presence) and returns clean errors.

The MCP surface exposes:
- `settings.get` (R): `SettingsService.get_settings(principal)` (:185).
  Returns the redacted settings document (secrets masked, `_revision` and
  `_placement` enrichment included).
- `settings.update` (W): `SettingsService.update_settings(principal,
  patch)` (:191). Accepts a partial patch object. The service validates
  every field; the tool surfaces `ValidationError` and `ConflictError` as
  `isError:true` results.

Secrets are NOT exposed. The existing `strip_secret_mutations()` (:144)
ensures the MCP patch cannot write secrets. The redacted response masks
them. The MCP tool description says this explicitly.

| Tool | R/W | Service method | Dispatch |
|---|---|---|---|
| `settings.get` | R | `SettingsService.get_settings(principal)` | settings_service.py:185 |
| `settings.update` | W | `SettingsService.update_settings(principal, patch)` | settings_service.py:191 |

#### Tool schemas

```json
{
  "name": "settings.get",
  "description": "Read the current HoldSpeak settings. Secrets are redacted; _revision enables optimistic concurrency.",
  "inputSchema": {
    "type": "object",
    "properties": {},
    "additionalProperties": false
  }
}
```

```json
{
  "name": "settings.update",
  "description": "Update HoldSpeak settings with a partial patch. Secrets cannot be written through this tool. Echo _revision from settings.get for optimistic concurrency; omit it for last-writer-wins. EGRESS: changing intel_provider, intel_profile_id, or other profile assignments may change the product's egress boundary (local/cloud); the response's _placement block shows the effective placement after the write. Settings are persisted immediately; a running HoldSpeak web server picks up the new values on its next settings read (no live-reload signal is sent from the MCP sidecar).",
  "inputSchema": {
    "type": "object",
    "properties": {
      "patch": {
        "type": "object",
        "description": "Partial settings object. Only supplied keys are changed."
      }
    },
    "required": ["patch"],
    "additionalProperties": false
  }
}
```

**Exposed groups:** All non-secret sections (model, hotkey, UI, meeting,
dictation, wake_word, rails_observer, device, presence). The service
validates every section uniformly; the tool does not filter.

**Validation errors:** The service returns `{"success": false, "error":
"..."}` for field-level validation failures and raises `ConflictError` for
stale `_revision`. Both surface as `isError:true` in the MCP result.

**Constructor:** `SettingsService(db=get_database(),
on_settings_applied=None, observer=get_observer())`.
`on_settings_applied` is `None` because the MCP sidecar does not hold a
live runtime to reconfigure -- the web server picks up config changes on
its next reload. This is honest: the tool description names it.

**Resources:** `holdspeak://settings` as a static resource is NOT added.
Settings contain secret-state flags and deployment provenance that change
on every write; a static resource would be immediately stale. The tool is
the right shape.

---

### 1C. CoderService (`holdspeak/services/coder_service.py`)

Session listing and inspection. Steering verbs (`reply`, `select_session`,
`keep_note`, `process_input_commands`) are named out-of-scope for Phase
133 -- they require the live web runtime's `reply_sender` callback and the
agent-context filesystem, which the stdio sidecar does not own. This is an
honest boundary, not an omission.

| Tool | R/W | Service method | Dispatch |
|---|---|---|---|
| `coder.list` | R | `CoderService.list_sessions(principal, agent=..., include_ended=...)` | coder_service.py:30 |
| `coder.get` | R | `CoderService.get_session(principal, session_id)` | coder_service.py:54 |
| `coder.audit` | R | `CoderService.list_steering_audit(principal, session_key, limit)` | coder_service.py:88 |

#### Tool schemas

```json
{
  "name": "coder.list",
  "description": "List coder sessions. Steering verbs are out-of-scope for the MCP sidecar.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "agent": {"type": "string", "description": "Filter by agent name."},
      "include_ended": {"type": "boolean", "description": "Include ended sessions (default true)."}
    },
    "additionalProperties": false
  }
}
```

```json
{
  "name": "coder.get",
  "description": "Get one coder session by agent:session_id.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "session_id": {"type": "string", "description": "Session id in agent:session_id format."}
    },
    "required": ["session_id"],
    "additionalProperties": false
  }
}
```

```json
{
  "name": "coder.audit",
  "description": "Read the bounded steering audit trail for coder sessions.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "session_key": {"type": "string", "description": "Filter by session key."},
      "limit": {"type": "integer", "minimum": 1, "maximum": 500, "description": "Maximum entries (default 50)."}
    },
    "additionalProperties": false
  }
}
```

**Constructor:** `CoderService(db=get_database(),
observer=get_observer())`. `reply_sender=None` is correct: the sidecar
cannot deliver replies.

**Resources:** No new resources. Coder sessions are ephemeral filesystem
state; a static resource would be stale immediately.

---

### 1D. CadenceService (`holdspeak/services/cadence_service.py`)

Status and read surface plus the safe write verbs. `snooze`,
`set_status`, `run_now`, and `apply_closeout` are included: all four
mutate only the local database (counsel-verified; `run_now` ticks the
engine via `TickService.tick()` at cadence_service.py:167-172,
`apply_closeout` applies decisions at :83-90, both return
`_LOCAL_EGRESS`). `reply` is excluded because it requires the live
agent-context pane delivery path (tmux) the sidecar does not own.

`get_loop` is async and potentially model-invoking (when
`config.use_llm=True`, it calls `_drafted_next_action` which enters the
kernel). It rides the same admitted `_as_principal` + `InvocationRequest`
path (cadence_service.py:254-276). The MCP tool surfaces this honestly.

| Tool | R/W | Service method | Dispatch |
|---|---|---|---|
| `cadence.status` | R | `CadenceService.status(principal)` | cadence_service.py:50 |
| `cadence.loops` | R | `CadenceService.list_loops(principal, include_terminal=...)` | cadence_service.py:62 |
| `cadence.get_loop` | R/W (conditional: may invoke model, minting kernel receipts) | `CadenceService.get_loop(principal, loop_id)` | cadence_service.py:177 |
| `cadence.brief` | R | `CadenceService.brief(principal)` | cadence_service.py:65 |
| `cadence.closeout` | R | `CadenceService.closeout(principal)` | cadence_service.py:75 |
| `cadence.history` | R | `CadenceService.history(principal, limit=...)` | cadence_service.py:91 |
| `cadence.audit` | R | `CadenceService.audit(principal)` | cadence_service.py:173 |
| `cadence.snooze` | W | `CadenceService.snooze(principal, loop_id, payload)` | cadence_service.py:100 |
| `cadence.set_status` | W | `CadenceService.set_status(principal, loop_id, status)` | cadence_service.py:108 |
| `cadence.run_now` | W | `CadenceService.run_now(principal)` | cadence_service.py:167 |
| `cadence.apply_closeout` | W | `CadenceService.apply_closeout(principal, payload)` | cadence_service.py:83 |

#### Tool schemas

```json
{
  "name": "cadence.status",
  "description": "Read Cadence engine status: enabled, pressure, loop counts, policy count.",
  "inputSchema": {
    "type": "object",
    "properties": {},
    "additionalProperties": false
  }
}
```

```json
{
  "name": "cadence.loops",
  "description": "List cadence loops. Omit include_terminal to exclude killed/closed loops.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "include_terminal": {"type": "boolean", "description": "Include killed/closed loops (default false)."}
    },
    "additionalProperties": false
  }
}
```

```json
{
  "name": "cadence.get_loop",
  "description": "Get one cadence loop with its next action. MAY INVOKE MODEL when cadence intelligence is enabled; rides the admitted inference path.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "loop_id": {"type": "string"}
    },
    "required": ["loop_id"],
    "additionalProperties": false
  }
}
```

```json
{
  "name": "cadence.brief",
  "description": "Read the deterministic Cadence morning brief.",
  "inputSchema": {
    "type": "object",
    "properties": {},
    "additionalProperties": false
  }
}
```

```json
{
  "name": "cadence.closeout",
  "description": "Read the current Cadence closeout recommendations.",
  "inputSchema": {
    "type": "object",
    "properties": {},
    "additionalProperties": false
  }
}
```

```json
{
  "name": "cadence.history",
  "description": "Read the Cadence nudge history.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "limit": {"type": "integer", "minimum": 1, "maximum": 500, "description": "Maximum nudges to return (default 50)."}
    },
    "additionalProperties": false
  }
}
```

```json
{
  "name": "cadence.audit",
  "description": "Export the full Cadence audit trail.",
  "inputSchema": {
    "type": "object",
    "properties": {},
    "additionalProperties": false
  }
}
```

```json
{
  "name": "cadence.snooze",
  "description": "Snooze a cadence loop until a given time or for a number of hours.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "loop_id": {"type": "string"},
      "until": {"type": "string", "description": "ISO-8601 snooze-until timestamp."},
      "hours": {"type": "number", "minimum": 0.1, "description": "Hours to snooze (default 24, used when until is omitted)."}
    },
    "required": ["loop_id"],
    "additionalProperties": false
  }
}
```

```json
{
  "name": "cadence.set_status",
  "description": "Set the status of a cadence loop. The reply verb is intentionally absent from the sidecar: it requires the live agent-context pane delivery path.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "loop_id": {"type": "string"},
      "status": {"type": "string", "enum": ["open", "closed", "killed"], "description": "New loop status."}
    },
    "required": ["loop_id", "status"],
    "additionalProperties": false
  }
}
```

```json
{
  "name": "cadence.run_now",
  "description": "Run a Cadence engine tick immediately. Local-only: projects loops, computes due nudges, returns them. May surface nudges ahead of schedule.",
  "inputSchema": {
    "type": "object",
    "properties": {},
    "additionalProperties": false
  }
}
```

```json
{
  "name": "cadence.apply_closeout",
  "description": "Apply closeout decisions to cadence loops. Each decision names a loop_id and an action; returns applied/skipped counts.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "decisions": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "loop_id": {"type": "string"},
            "action": {"type": "string"}
          },
          "required": ["loop_id", "action"],
          "additionalProperties": false
        },
        "maxItems": 100,
        "description": "Closeout decisions to apply."
      }
    },
    "required": ["decisions"],
    "additionalProperties": false
  }
}
```

**Constructor:** `CadenceService(db=get_database(),
config=Config.load().cadence, kernel=None, observer=get_observer())`.
`kernel=None` is correct: the service lazily loads the broker via
`_service()` when `use_llm` is true (cadence_service.py:220).

**Resources:** `holdspeak://cadence/status` as a static resource -- yes,
it earns its place: a client can poll the cadence engine state without
calling a tool, and the shape is small and stable.

---

### 1E. SequenceWorkflowService (`holdspeak/services/sequence_workflow_service.py`)

Both `run_sequence` (:110) and `run_workflow` (:146) are MODEL-INVOKING.
They ride the admitted path: `_invoke()` (:38) enters
`InferenceRunner.invoke()` inside `_as_principal`, after
`resolve_placement` + `capture_deployment_revision`. Both use
`parent_run_controller.start()` to open a kernel parent run and close it
with a durable receipt.

The MCP surface does NOT expose CRUD for sequences/workflows -- that
already exists via `desk.create`/`desk.update`/`desk.delete` with
`kind="chains"` or `kind="workflows"`. The new tools expose only the
admitted run path and cancel.

| Tool | R/W | Service method | Dispatch |
|---|---|---|---|
| `sequence.run` | W (model-invoking) | `SequenceWorkflowService.run_sequence(principal, chain_id, body)` | sequence_workflow_service.py:110 |
| `workflow.run` | W (model-invoking) | `SequenceWorkflowService.run_workflow(principal, workflow_id, body)` | sequence_workflow_service.py:146 |
| `sequence.cancel` | W | `broker.parent_run_controller.cancel_by_operation_id(principal, op_id)` | (same pattern as chains.py:72) |
| `workflow.cancel` | W | `broker.parent_run_controller.cancel_by_operation_id(principal, op_id)` | (same pattern as workflows.py:70) |

#### Tool schemas

```json
{
  "name": "sequence.run",
  "description": "Run a Sequence (chain) through the admitted inference path. MODEL-INVOKING. The result carries the receipt, steps, and artifact reference.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "chain_id": {"type": "string", "description": "Sequence identifier."},
      "input": {"type": "string", "description": "Input text for the first step."},
      "variables": {"type": "object", "description": "Template variables for prompt rendering."},
      "inference_target_id": {"type": "string", "description": "Override inference destination."},
      "temperature": {"type": "number", "minimum": 0, "maximum": 2},
      "max_tokens": {"type": "integer", "minimum": 1},
      "request_id": {"type": "string", "description": "Idempotency key for replay."}
    },
    "required": ["chain_id"],
    "additionalProperties": false
  }
}
```

```json
{
  "name": "sequence.cancel",
  "description": "Cancel an in-flight Sequence run by its parent operation id.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "parent_operation_id": {"type": "string"}
    },
    "required": ["parent_operation_id"],
    "additionalProperties": false
  }
}
```

```json
{
  "name": "workflow.run",
  "description": "Run a Workflow through the admitted inference path. MODEL-INVOKING. Returns the receipt, node steps, and artifact reference.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "workflow_id": {"type": "string", "description": "Workflow identifier."},
      "input": {"type": "string", "description": "Input text for the workflow."},
      "variables": {"type": "object", "description": "Template variables for prompt rendering."},
      "inference_target_id": {"type": "string", "description": "Override inference destination."},
      "temperature": {"type": "number", "minimum": 0, "maximum": 2},
      "max_tokens": {"type": "integer", "minimum": 1},
      "request_id": {"type": "string", "description": "Idempotency key for replay."}
    },
    "required": ["workflow_id"],
    "additionalProperties": false
  }
}
```

```json
{
  "name": "workflow.cancel",
  "description": "Cancel an in-flight Workflow run by its parent operation id.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "parent_operation_id": {"type": "string"}
    },
    "required": ["parent_operation_id"],
    "additionalProperties": false
  }
}
```

**Dispatch notes:**
- `run_sequence` and `run_workflow` are async coroutines. Dispatch wraps
  them in `_run()`.
- The `SequenceWorkflowService` constructor requires `(db, broker)`. The
  broker must be a live kernel instance. The dispatch creates it with
  `from holdspeak.kernel.runtime import _configure; broker =
  _configure(db)` -- same pattern as the web routes
  (chains.py:56, workflows.py:56).
- Cancel dispatches through the broker, same pattern as the web routes.

**Resources:** No new resources. Run results are kernel-level durable
receipts; the existing `pipeline://events/*` resources already expose the
audit trail.

---

### 1F. MemoryService (`holdspeak/services/memory_service.py`)

A single search tool. The service has exactly one public method:
`search()` (:18). It enforces `PrincipalRight.READ` internally (:30-36).

| Tool | R/W | Service method | Dispatch |
|---|---|---|---|
| `memory.search` | R | `MemoryService.search(principal, query, ...)` | memory_service.py:18 |

#### Tool schema

```json
{
  "name": "memory.search",
  "description": "Search the long-horizon memory store. Results are filtered by the principal's read permission.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "query": {"type": "string", "description": "Search query."},
      "kind": {"type": "string", "description": "Optional kind filter."},
      "project_id": {"type": "string", "description": "Optional project filter."},
      "time_from": {"type": "string", "description": "Optional ISO-8601 start bound."},
      "time_to": {"type": "string", "description": "Optional ISO-8601 end bound."},
      "limit": {"type": "integer", "minimum": 1, "maximum": 500, "description": "Maximum results (default 50)."},
      "offset": {"type": "integer", "minimum": 0, "description": "Pagination offset (default 0)."}
    },
    "required": ["query"],
    "additionalProperties": false
  }
}
```

**Constructor:** `MemoryService(db=get_database(),
observer=get_observer())`.

**Resources:** `holdspeak://memory` is NOT added. Memory is a search
index, not a list. A static resource with no query is meaningless.

---

### 1G. PluginJobService (`holdspeak/services/plugin_job_service.py`)

List, summary, retry, and cancel. The `process` verb (the web route at
`plugin_jobs.py`:28-37) is out-of-scope: it requires
`ctx.on_process_plugin_jobs`, which is a live-runtime callback the MCP
sidecar does not hold. The tool description names this omission.

The service supports `retry` (:31) -- VERIFIED: it calls
`self._db.plugins.retry_plugin_run_job()` to re-queue a failed/completed
job. It refuses running jobs (:34).

The service supports `cancel` (:39) -- VERIFIED: it calls
`self._db.plugins.complete_plugin_run_job()` to mark a job done. It
refuses running jobs (:42).

| Tool | R/W | Service method | Dispatch |
|---|---|---|---|
| `plugin_job.list` | R | `PluginJobService.list(principal, status, meeting_id, limit)` | plugin_job_service.py:24 |
| `plugin_job.summary` | R | `PluginJobService.summary(principal)` | plugin_job_service.py:27 |
| `plugin_job.retry` | W | `PluginJobService.retry(principal, job_id)` | plugin_job_service.py:31 |
| `plugin_job.cancel` | W | `PluginJobService.cancel(principal, job_id)` | plugin_job_service.py:39 |

#### Tool schemas

```json
{
  "name": "plugin_job.list",
  "description": "List deferred plugin jobs by status. Queue processing is unavailable from the MCP sidecar.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "status": {
        "type": "string",
        "enum": ["all", "queued", "running", "failed", "completed"],
        "description": "Job status filter (default 'all')."
      },
      "meeting_id": {"type": "string", "description": "Optional meeting filter."},
      "limit": {"type": "integer", "minimum": 1, "maximum": 500, "description": "Maximum jobs (default 200)."}
    },
    "additionalProperties": false
  }
}
```

```json
{
  "name": "plugin_job.summary",
  "description": "Read aggregate plugin job statistics: total, queued, running, failed counts and next retry time.",
  "inputSchema": {
    "type": "object",
    "properties": {},
    "additionalProperties": false
  }
}
```

```json
{
  "name": "plugin_job.retry",
  "description": "Re-queue a failed or completed plugin job for immediate retry. Refuses running jobs.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "job_id": {"type": "integer", "description": "Numeric job identifier."}
    },
    "required": ["job_id"],
    "additionalProperties": false
  }
}
```

```json
{
  "name": "plugin_job.cancel",
  "description": "Mark a non-running plugin job as completed (cancels it). Refuses running jobs.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "job_id": {"type": "integer", "description": "Numeric job identifier."}
    },
    "required": ["job_id"],
    "additionalProperties": false
  }
}
```

**Constructor:** `PluginJobService(db=get_database(),
observer=get_observer())`.

**Resources:** No new resources. Job state is transient.

---

### New tool count summary

| Family | Tools | Model-invoking |
|---|---|---|
| ask | 5 | `ask.run` |
| settings | 2 | none |
| coder | 3 | none |
| cadence | 11 | `cadence.get_loop` (conditional) |
| sequence | 2 | `sequence.run` |
| workflow | 2 | `workflow.run` |
| memory | 1 | none |
| plugin_job | 4 | none |
| **Total new** | **30** | **4** |

Combined with the existing 52, Phase 133 brings the sidecar to **82
tools**.

### New resource summary

| URI | Description |
|---|---|
| `holdspeak://cadence/status` | Cadence engine status (small, stable shape) |

All other services were evaluated and declined -- see family sections for
reasoning.

---

## Part 2 — The Honesty Sweep

### 2.1. auth.py truth

**Current state (holdspeak/mcp/auth.py):**
- `MCPAuth.url` field is set from `HOLDSPEAK_URL` env var (:29) but
  NEVER READ by any consumer. Grep confirms: no file in `holdspeak/mcp/`
  reads `.url` on an `MCPAuth` instance. `server.py` calls
  `resolve_auth().principal` (:67, :80) -- never `.url`.
- The `MCPAuth` docstring (:14-19) claims "the sidecar operates on the
  local HoldSpeak store, so its bearer is never emitted" -- this is
  correct but incomplete.
- Both code paths (token present, token absent) yield
  `PrincipalKind.OWNER` (:32) -- the token changes nothing.

**Corrected auth.py:**

Remove `DEFAULT_HOLDSPEAK_URL`, `url` field, and `HOLDSPEAK_URL` env
read. Retain `HOLDSPEAK_TOKEN` read because it at least distinguishes the
identity label (`"mcp-token"` vs `"local-mcp"`), which is useful for
observer audit trails, even though both yield OWNER.

Corrected docstring:

```python
@dataclass(frozen=True)
class MCPAuth:
    """Process-boundary principal for the MCP stdio sidecar.

    The sidecar runs as a child of the same user process that owns the
    HoldSpeak database.  No network authentication is performed: the
    process boundary IS the trust boundary, and the principal is always
    PrincipalKind.OWNER.

    When HOLDSPEAK_TOKEN is set, the identity label is 'mcp-token' (so
    observer events can distinguish token-bearing clients); otherwise it
    is 'local-mcp'.  Both are OWNER -- the token does not gate access.
    """

    principal: Principal
```

Corrected `resolve_auth`:

```python
def resolve_auth(environ: dict[str, str] | None = None) -> MCPAuth:
    """Resolve the sidecar principal from the process environment."""
    env = os.environ if environ is None else environ
    token = str(env.get("HOLDSPEAK_TOKEN") or "").strip()
    identity = "mcp-token" if token else "local-mcp"
    return MCPAuth(principal=Principal(PrincipalKind.OWNER, identity))
```

**What to verify before removal:** Grep for `MCPAuth` imports and `.url`
attribute access outside `auth.py`. Current grep result:

- `holdspeak/mcp/auth.py:13` -- definition
- `holdspeak/mcp/auth.py:26` -- factory
- `holdspeak/mcp/auth.py:32` -- construction
- `holdspeak/mcp/server.py:8` -- imports `resolve_auth`
- `holdspeak/mcp/server.py:67,80` -- calls `resolve_auth().principal`

No other file imports `MCPAuth` or accesses `.url`. Removal is safe.

---

### 2.2. `holdspeak-mcp` console script and `.mcp.json`

**pyproject.toml addition:**

```toml
[project.scripts]
holdspeak = "holdspeak.main:main"
holdspeak-mcp = "holdspeak.mcp.server:main"
```

The entry function `main()` already exists at `holdspeak/mcp/server.py:109`.

**`.mcp.json` creation at repo root:**

The brief stated `.mcp.json` "currently exists and wires dw-mcp". This
is INCORRECT: no `.mcp.json` file exists in the repo (verified by `find`
across the full tree). The CLAUDE.md reference "wired via `.mcp.json`"
describes the Delivery Workbench framework's own documentation, not a
file in THIS repo. So we CREATE `.mcp.json`, not ADD to it.

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

RULED (counsel, 2026-08-16): `.mcp.json` ships HOLDSPEAK-ONLY. The
Delivery Workbench framework generates its own MCP discovery through the
managed CLAUDE.md block; wiring dw-mcp here would couple this repo to the
framework's binary path. If the owner later wants dw-mcp wired, it is a
one-line addition.

---

### 2.3. Resource pagination

**Affected static resources (resources.py:316-338):**

| URI | Current call | Limit behavior |
|---|---|---|
| `holdspeak://workbenches` | `list_workbenches(principal)` | unbounded |
| `holdspeak://recipes` | `list_recipes(principal)` | unbounded |
| `holdspeak://profiles` | `list_profiles(principal)` | unbounded |
| `holdspeak://dictation/journal` | `list_journal(principal)` | default 200 |
| `holdspeak://follow-through/board` | `board(principal)` | bounded by design (4 lanes) |
| `holdspeak://desk/snapshot` | `snapshot(principal)` | bounded by desk size |
| `pipeline://events/recent` | `recent(principal)` | default 50 |
| `pipeline://events/stats` | `stats(principal)` | single summary |

**Ruling:** Resources carry the first page at a house default limit.
Tools carry cursors for full traversal. Rationale in one paragraph:

> MCP resources are context providers -- a client reads them to seed its
> understanding, not to enumerate every row. A 200-workbench desk
> producing a 500KB resource payload degrades the client's context window
> for no gain: the client that needs row 201 should call the tool with a
> cursor. The house default is `limit=100` for list resources. The
> `dictation/journal` resource already passes `limit=200` via its service
> default; normalize it to 100 for consistency. `pipeline://events/recent`
> already has a service default of 50; keep it. `follow-through/board`
> and `desk/snapshot` are bounded by design and unchanged.

**Implementation:** For the three unbounded calls (`list_workbenches`,
`list_recipes`, `list_profiles`), the resource handler truncates the
returned list to `[:100]` before serialization. The services do not have
a `limit` parameter today, so the truncation happens at the resource
layer, not the service layer. This is correct: the resource is a
convenience view, not a paginated API.

For `holdspeak://dictation/journal`, call `list_journal(principal,
limit=100)` explicitly.

---

### 2.4. Kind-gap documentation

The `desk.*` CRUD tools (tools.py:32-95) accept 6 kinds via the
`PRIMITIVE_KINDS` enum: `notes`, `decisions`, `kbs`, `directories`,
`workflows`, `chains`. The `holdspeak://desk/schema` resource advertises
17 kinds (resources.py:31-49) because the Desk carries content,
organization, capability, presence, and local kinds beyond the CRUD
subset.

**Added sentence in each desk CRUD tool description:**

For `desk.list`, `desk.get`:
> The desk schema advertises 17 primitive kinds; this tool operates on the
> 6 authorable kinds: notes, decisions, kbs, directories, workflows, and
> chains. The remaining 11 kinds (meeting, artifact, project, repository,
> recipe, coder, game, roadmap, story, workbench, layout) are managed
> through their own dedicated tools or are read-only.

For `desk.create`, `desk.update`, `desk.delete`:
> Authorable kinds: notes, decisions, kbs, directories, workflows, chains.

This is appended to the existing `description` string in the tool schema.

---

### 2.5. `pipeline_events_query` rename to `pipeline.events`

**Rationale:** Pre-release product (owner standing rule: skip
backwards-compat ceremony). The flat name violates the `domain.verb`
naming law that every other tool follows.

**All references to rename:**

| File | Line | Change |
|---|---|---|
| `holdspeak/mcp/tools.py` | 301 | `"pipeline_events_query"` -> `"pipeline.events"` |
| `holdspeak/mcp/tools.py` | 554 | `if name == "pipeline_events_query":` -> `if name == "pipeline.events":` |
| `tests/unit/test_124_verify_round3.py` | 41 | function name: `test_pipeline_events_query_...` -> `test_pipeline_events_...` |
| `tests/unit/test_124_verify_round3.py` | 47 | `dispatch("pipeline_events_query", ...)` -> `dispatch("pipeline.events", ...)` |
| `tests/unit/test_124_verify_round3.py` | 52 | function name: `test_pipeline_events_query_...` -> `test_pipeline_events_...` |
| `tests/unit/test_124_verify_round3.py` | 60 | `"pipeline_events_query"` -> `"pipeline.events"` |

No other files reference `pipeline_events_query` (grep verified).

---

## Part 3 — Laws the Implementation Must Hold

### Invariant 1: One Admission Path

No new tool opens a provider-reaching side door. Model-invoking tools and
their admitted paths:

| Tool | Admitted path |
|---|---|
| `ask.run` | `AskService.ask()` -> `InferenceRunner.invoke()` via `_as_principal` (ask_service.py:59,117) |
| `cadence.get_loop` | `CadenceService.get_loop()` (:177) -> `_next_action()` (:187) -> `_drafted_next_action()` (:206) -> `_draft_child()` (:254) -> `InferenceRunner.invoke()` via `_as_principal` (:272-276) |
| `sequence.run` | `SequenceWorkflowService.run_sequence()` -> `_invoke()` -> `InferenceRunner.invoke()` via `_as_principal` (sequence_workflow_service.py:38-45,110) |
| `workflow.run` | `SequenceWorkflowService.run_workflow()` -> `_invoke()` -> `InferenceRunner.invoke()` via `_as_principal` (sequence_workflow_service.py:38-45,146) |

Every path enters the kernel through `InferenceRunner.invoke()` with a
`ServiceContract`, `InvocationRequest`, and `CanonicalPromptAdapter`,
after `resolve_placement` + `capture_deployment_revision`. No new path is
manufactured.

### Invariant 2: Naming Law

Every new tool uses `domain.verb` naming. The `pipeline_events_query`
rename to `pipeline.events` fixes the only existing violation.

### Invariant 3: Schema Law

Every new `inputSchema` carries:
- `"type": "object"`
- `"additionalProperties": false`
- Enums for constrained string fields
- `minimum`/`maximum` bounds on pagination integers (house range:
  `minimum: 1, maximum: 500` unless the service enforces tighter)
- `maxItems` on array inputs

### Invariant 4: Observer Law

New TOOL dispatch creates services with `observer=get_observer()`,
exactly as the existing dispatch does at tools.py:419-431.

New RESOURCES follow the existing unobserved pattern: resources.py
constructs services with `get_database()` only (no observer). Example:
`ProfileService(get_database())` at resources.py:313.

**Known asymmetry (flagged for owner sitting, out-of-scope):** Resource
reads are unobserved. This means a client that reads
`holdspeak://cadence/status` via `resources/read` produces no pipeline
event, while the same read through `cadence.status` via `tools/call`
does. This is the existing pattern for all 13 static resources and 10
resource templates. Fixing this asymmetry is a schema-level change
(adding observer to every resource-layer service construction) and should
be its own story.

### Invariant 5: Error Law

Every new tool dispatch wraps service calls in the existing try/except
chain at server.py:79-84:
- `ToolError`, `ValueError`, `KeyError`, `TypeError` -> `isError: true`
  with the error message
- All other `Exception` -> `isError: true`, never a sidecar crash

Service-level errors (`ServiceError`, `ValidationError`, `ConflictError`,
`NotFound`) are subclasses of `Exception` and are caught by the outer
`except Exception` at server.py:83. The tool dispatch MAY also catch
`ServiceError` explicitly to extract `code` and `context` into the error
payload for richer MCP error results. House convention: catch
`(ToolError, ValueError, KeyError, TypeError)` first, then
`ServiceError` with context, then bare `Exception`.

### Invariant 6: Test Law

Every new tool gets:
1. A dispatch-level unit test: monkeypatch the service, call
   `mcp_tools.dispatch(name, args, OWNER)`, assert the service method was
   called with the right arguments and the return value is
   JSON-serializable. Pattern: `tests/unit/test_mcp_tools.py:32-88`.
2. At least one error-path test: call with invalid/missing arguments,
   assert `isError: true` in the MCP response. Pattern:
   `tests/unit/test_mcp_tools.py:20-29` (schema validation) +
   `test_124_verify_round3.py:41-74` (dispatch through handle_message).
3. For model-invoking tools: the test monkeypatches the service's
   async method to return a canned result (no real provider call). The
   test verifies the MCP dispatch wraps `_run()` correctly.

New tests go in a new file: `tests/unit/test_mcp_phase133.py`, following
the existing fixture pattern (tmp_path db, monkeypatch service classes).

AMENDED at wave open (orchestrator, 2026-08-16, recorded in the phase
status): registry tests live in `test_mcp_phase133.py` (landed with
HS-133-01); each family story's tests live in
`tests/unit/test_mcp_phase133_<family>.py` so parallel workers never
share a test file. The REQUIRED_TOOLS extension happens serially at each
story's SHIP, never during parallel implementation.

Counsel conditions folded into the test law:

4. The `REQUIRED_TOOLS` catalogue set in `tests/unit/test_mcp_tools.py:11-17`
   is extended with ALL 30 new tool names, so the closed-schema catalogue
   test (`test_tools_list_exposes_pipeline_mcp_tools_with_closed_schemas`)
   fails on any tool defined in code but missing from the catalogue.
5. The new resource `holdspeak://cadence/status` gets a resource-read test
   through `handle_message` with `method: "resources/read"`, following the
   existing resource test pattern.
6. The `pipeline.events` rename updates the test FUNCTION NAMES in
   `tests/unit/test_124_verify_round3.py` (lines 41, 52) as well as the
   4 string references, so test names track the tool they exercise.

---

## Part 4 — Open Questions for Counsel

### Q1. `.mcp.json` — holdspeak only, or holdspeak + dw-mcp?

**Recommendation:** Ship with both servers wired. The `dw-mcp` wiring is
already documented in CLAUDE.md as the canonical MCP entry point for
Delivery Workbench, and a `.mcp.json` that wires only holdspeak forces
any Claude Code user to manually add dw-mcp. The DW riderdocs already
forbid PI-authored `.mcp.json` content, but THIS file is authored by the
project, not a PI fragment.

**Rationale:** The `.mcp.json` is the repo's canonical MCP server
manifest. Omitting dw-mcp from it when CLAUDE.md already references it
creates a discovery gap.

### Q2. `cadence.reply` -- include or exclude?

**Recommendation:** Exclude. The verb requires the live agent-context pane
delivery infrastructure (`submit_process_input_from_owner_gesture`), which
the stdio sidecar does not own. Including it would either (a) always fail
at runtime with "delivery refused" or (b) require the sidecar to
import tmux process code that it cannot safely run. The tool description
for `cadence.set_status` documents that `reply` is intentionally absent.

**Rationale:** An always-failing tool is worse than a missing one: it
breaks tool-calling agents that try to use it and wastes a turn.

### Q3. `settings.update` -- should `on_settings_applied` be wired?

**Recommendation:** No. The callback is a web-runtime concern
(reconfiguring the live whisper model, restarting the wake-word listener).
The MCP sidecar writes to the same config file the web server reads; the
web server picks up changes on its next settings load. The tool
description should state: "Settings are persisted immediately. A running
HoldSpeak web server picks up the new values on its next settings read;
no live-reload signal is sent from the MCP sidecar."

**Rationale:** Honest over convenient. The alternative (HTTP POST to the
running web server) would re-introduce the `HOLDSPEAK_URL` field we are
removing as dead code.

### Q4. `coder.reply` / `coder.select_session` -- Phase 133 or backlog?

**Recommendation:** Backlog. Both require `reply_sender` (a live WS
callback) and the filesystem-based agent context. The sidecar cannot
deliver replies to tmux panes or select awaiting sessions. Including
read-only `coder.list` + `coder.get` + `coder.audit` is genuinely useful
for MCP clients inspecting the desk state.

**Rationale:** Ship the read surface now, backlog the write surface for
when the sidecar can communicate with the live runtime (e.g., via IPC
or the `HOLDSPEAK_URL` that Phase 133 is removing from auth.py -- Q5
implicitly).

### Q5. Resource observer asymmetry -- flag or fix?

**Recommendation:** Flag (as specified in Invariant 4). The asymmetry is
the existing pattern for all 23 resources. Fixing it is a cross-cutting
change (adding observer to every resource construction, deciding which
pipeline events resource reads emit, handling the doubled event volume).
It deserves its own story in a future phase.

**Rationale:** Phase 133 is "complete and honest", not "complete, honest,
and refactored". The flag in this spec is the honest acknowledgment.

---

## Part 5 — Counsel ruling record (2026-08-16)

Counsel session ruled: **implementation may begin** under four conditions,
all folded into this revision:

1. `cadence.run_now` + `cadence.apply_closeout` prose/table inconsistency
   — RESOLVED by orchestrator ruling: both ADDED (counsel verified both
   mutate only the local DB). Counts updated to 30 new / 82 total.
2. `settings.update` Article III.2 egress warning — ADDED to the tool
   description (1B).
3. `cadence.get_loop` reclassified R/W (conditional); Invariant 1 call
   chain corrected to name `_next_action` → `_drafted_next_action` →
   `_draft_child` (:272-276).
4. Test law extended: REQUIRED_TOOLS catalogue update, cadence/status
   resource-read test, renamed test functions in the pipeline.events
   rename (Invariant 6 items 4-6).

Open questions resolved: Q1 `.mcp.json` holdspeak-only (counsel overruled
the draft's both-servers recommendation); Q2 `cadence.reply` excluded;
Q3 `on_settings_applied` stays unwired, description names it; Q4 coder
write verbs backlogged; Q5 resource observer asymmetry flagged for the
owner sitting, not fixed here.

Known gap documented per counsel C.iii: `companion_github_repo` is
writable via `settings.update` (not in SECRET_PATHS,
settings_service.py:22-34). No new egress channel — the companion uses
the host's local `gh` CLI — but the destination repo is redirectable.
Recorded as a ledger item for the owner sitting, not blocked on.

### Orchestrator structural ruling: the family registry keystone

Thirty new tools would nearly double the 610-line `tools.py`, and the
family stories are implemented by parallel workers in one shared tree.
Implementation therefore begins with a keystone: new tool families live
in per-family modules under `holdspeak/mcp/families/` (ask.py,
settings.py, coder.py, cadence.py, sequence.py, memory.py,
plugin_job.py), each exporting its `TOOLS` list and a `dispatch(name,
arguments, principal)` callable; `tools.py` aggregates family TOOLS into
the catalogue and routes unmatched names to family dispatchers before
its own dispatch chain. The existing 52 tools stay in `tools.py`
untouched. After the keystone, every family story touches exactly one
new file plus its tests — no shared-file contention in the waves.
