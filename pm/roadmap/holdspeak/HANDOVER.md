# HANDOVER — Phase 122-123 Complete

**Date:** 2026-08-07
**Author:** Opus 4.6 orchestrator session
**PR:** #441 (merged)

## What just shipped

Two phases in one session. DeskOS went from zero programmatic API to a
fully MCP-drivable platform.

**Phase 122 — The Backbone (12/12):** The service layer was born. Eight
services extracted from route handlers. An MCP server with 10 tools.
A walk harness. A desk doctor.

**Phase 123 — The Pipeline (13/13):** The service layer was completed.
33 services now own every operation in the system. The MCP server
expanded to 41 tools and 16 resources. Route handler bypass census:
157 → 2 (the two intentional chain/workflow run endpoints).

## The numbers

| Metric | Before | After |
|--------|--------|-------|
| Transport-neutral services | 0 | 33 |
| MCP tools | 0 | 41 |
| MCP resources | 0 | 16 |
| Route handlers calling DB directly | 157 | 2 |
| Service + MCP code | 0 | ~15,000 lines |

## What's on the desk for the next agent

### The NeXT moment: the service pipeline as a data lake

Here's the idea the owner planted, and it's a big one.

Every operation in DeskOS now flows through a named service method with
a typed `Principal`, typed arguments, and a typed result. Today those
calls execute and return. But imagine if every service call was also
*recorded* — not just its name, but its principal, its arguments, its
result, its timing, its causal chain.

```
┌─────────────────────────────────────────────────────────┐
│                   Service Pipeline                       │
│                                                         │
│  MCP client ───┐                                        │
│  FastAPI route ─┤──→ Service.method(principal, args)     │
│  Test fixture ──┤         │                              │
│  CLI ───────────┘         │                              │
│                           ▼                              │
│                    ┌─────────────┐                       │
│                    │  Pipeline   │──→ Repository layer    │
│                    │  Observer   │                        │
│                    └──────┬──────┘                       │
│                           │                              │
│                           ▼                              │
│                    ┌─────────────┐                       │
│                    │  Data Lake  │                        │
│                    │             │                        │
│                    │  Every call │                        │
│                    │  Every arg  │                        │
│                    │  Every result│                       │
│                    │  Every timing│                       │
│                    │  Every who   │                       │
│                    └─────────────┘                       │
│                           │                              │
│                           ▼                              │
│                                                         │
│  "What did the desk DO today?"                          │
│  "Which services are hot? Which are dead?"              │
│  "What did agent X actually touch?"                     │
│  "Replay this user's last hour"                         │
│  "What operations correlate with this outcome?"         │
│  "Build me a briefing from what actually happened"      │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

This is why the service extraction mattered. It wasn't refactoring for
purity. It was the **prerequisite for observability**. When operations
were scattered across 157 route handlers calling repositories directly,
there was no single chokepoint to observe. Now there is: 33 services,
each with a `Principal` and typed arguments. One decorator, one
middleware, one observer — and the entire system becomes a stream of
structured events.

The kernel already has a journal (the SHA-256 chain from Phase 106).
The service pipeline is the same idea at the application layer: every
`create`, `delete`, `run`, `chat`, `ask`, `file`, `resolve`, `seed`,
`approve`, `revoke` — recorded, correlated, replayable.

This is the NeXT moment. The desk isn't just an OS with a programmatic
API. It's an OS that *knows what it did*.

### Concrete next steps

1. **Phase 124 — The Observer.** A `PipelineObserver` protocol that
   services call (or a decorator wraps) on every public method. The
   observer records `{service, method, principal, args_summary,
   result_summary, duration_ms, timestamp, correlation_id}` to a
   durable append-only store. Day one: a SQLite `pipeline_events`
   table. Day two: the desk's own analytics surface. Day three: an
   MCP resource that answers "what happened?"

2. **The two remaining run endpoints.** `chains.py:108` and
   `workflows.py:132` are the last direct-DB handlers. They're
   complex orchestration (inference, graph linearization, artifact
   persistence). Extract them into `ChainRunService` and
   `WorkflowRunService` when the observer is ready — then even
   inference calls are observable.

3. **Phase 120 web changes.** The UI reckoning work (11 stories) is
   in the working tree but was not committed because its evidence
   files were missing. A fresh session should create evidence for
   each Phase 120 story and commit them.

4. **Phase 121 — The Fluency.** Chartered but not started. Kit-first
   UX architecture (SurfaceFooter, LedgerFilter, useCopyReceipt,
   useUndoReceipt — most primitives already exist and have tests).
   This is the web-side complement to the backend pipeline work.

### Repo conventions that bite

- **PMO commit gate:** `git config core.hooksPath .githooks` in every
  fresh clone. The gate requires `.tmp/CONTRACT.md` with all boxes
  flipped. Evidence files must ship with done-flipped stories.
- **Bundle rule:** Multiple stories in one commit need
  `.tmp/BUNDLE-OK.md` with a rationale.
- **Test exclusion:** `tests/e2e/test_metal.py` hangs without a mic.
  Use `-k "not metal"`.
- **Terra agents:** Run ONLY focused tests for their changes. The
  orchestrator runs the full suite. Standing rule in memory:
  `feedback_terra_scoped_tests_only.md`.
- **Web bundle is gitignored:** Edit `web/src/`, commit source only.
- **The .43 box:** LAN LLM at `192.168.1.43:8080`. Sandboxed Bash
  can't reach it.

### The service inventory

33 services under `holdspeak/services/`:

```
primitive_service.py          workbench_service.py
recipe_service.py             meeting_service.py
meeting_intel_service.py      meeting_aftercare_service.py
dictation_service.py          coder_service.py
profile_service.py            desk_service.py
authority_service.py          credential_service.py
settings_service.py           ask_service.py
decision_lifecycle_service.py project_service.py
projection_service.py         activity_ledger_service.py
activity_rules_service.py     activity_meeting_candidate_service.py
activity_enrichment_service.py plugin_job_service.py
activity_nudge_service.py     cadence_service.py
sync_service.py               actuator_service.py
gate_service.py               setup_service.py
mesh_service.py               memory_service.py
invocation_service.py         mission_control_service.py
delivery_service.py
```

Shared infrastructure:
- `errors.py` — `ServiceError`, `NotFound`, `ValidationError`, `ConflictError`
- `support.py` — capability descriptors, graph linearization, prompt
  rendering, artifact persistence, skill injection, grounding

MCP server at `holdspeak/mcp/`:
- `server.py` — stdio JSON-RPC loop
- `tools.py` — 41 tools
- `resources.py` — 16 resources (9 static + 7 templates)
- `auth.py` — principal from env token

Walk harness at `scripts/desk_walk/`:
- `fixtures.py` — isolated hub with temp DB
- `pages/` — DeskPage, Palette, WorkbenchWindow, Pullout
- `assertions.py` — footer/failure helpers
- `walk_mcp_122.py`, `walk_mcp_123.py`, `walk_keyboard_122.py`

Desk doctor at `holdspeak/doctor.py` — 8 health checks, runnable as
`holdspeak doctor` or `python -m holdspeak.doctor`.

---

*The desk is programmable. The pipeline is one observer away from
being observable. That's the seed.*
