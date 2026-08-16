# Phase 133 — The Honest Sidecar

**Status:** in-progress (6/11).

**Last updated:** 2026-08-16.

## Owner mandate

Recorded 2026-08-16, from the MCP/service-layer audit review: of the
proposed One Chokepoint slate, the owner selected items 4 and 5 — MCP
coverage for the user-facing services, and the honesty sweep — and asked
for "an absolutely amazing phase" run through the workers. Items 1-3 of
that slate (kernel admission for non-inference writes, the observer
holes, the runner dedup) stay parked for a later slice, as does issue
#450 Wave 1, which remains the owner-named next product slice after this
phase.

## Goal

The MCP sidecar becomes the desk's complete, honest programmable
surface. Every transport-neutral user-facing capability an MCP client
should reach — Ask, Settings, Coder sessions, Cadence, Sequences,
Workflows, Memory, plugin jobs — gets tools that ride the already-
admitted paths, and every honesty debt in the existing surface is paid:
the auth story tells the truth, the promised `holdspeak-mcp` entry point
exists, resources are bounded, the schema/CRUD kind gap is named where
clients read, and the one naming-law violation is retired. The sidecar
goes from 52 tools to 82 with zero new provider-reaching side doors.

## The evidence base

Three parallel Opus audits on main @ `d4acbbe7` (2026-08-16): a
structural census of the 41-service layer, a static + live MCP surface
audit (real JSON-RPC handshake on a fresh HOME, focused tests green),
and a canon/backlog alignment audit. Their joined verdict: the layer is
mechanically healthy and the One Admission Path law is intact with zero
side doors, but 30 services have no MCP exposure (including seven
user-facing families), auth is cosmetic with a misleading docstring and
dead `HOLDSPEAK_URL` code, Phase 122's `holdspeak-mcp` console-script
criterion was never literally delivered, resources are unpaginated, and
`pipeline_events_query` is the only tool violating the `domain.verb`
naming law.

The design beat ran before this charter: the full surface specification
— every tool name, schema, dispatch anchor, and invariant — was drafted
against real service signatures and RULED by an Opus counsel session
(verdict: implementation may begin; four conditions, all folded in).
The ruled spec is this phase's implementation contract:
[assets/surface-spec.md](./assets/surface-spec.md). Workers implement
against the spec verbatim; deviations are findings, not preferences.

## Scope

### In

- A family registry keystone: new tool families live in per-family
  modules under `holdspeak/mcp/families/`, aggregated by `tools.py`, so
  parallel family stories touch disjoint files (spec Part 5).
- Thirty new tools across eight families — ask (5), settings (2),
  coder (3), cadence (11), sequence (2), workflow (2), memory (1),
  plugin_job (4) — each dispatching to the service method the spec
  anchors, with the spec's exact schemas; four model-invoking tools ride
  the existing admitted `InferenceRunner.invoke()` paths (spec
  Invariant 1).
- One new resource: `holdspeak://cadence/status`, with a resource-read
  test.
- The honesty sweep: truthful `auth.py` (dead `HOLDSPEAK_URL`/`url`
  removed, docstring names process-boundary-as-trust-boundary),
  `holdspeak-mcp` console script + repo-root `.mcp.json`
  (holdspeak-only, per counsel Q1), resource pagination bounds,
  kind-gap sentences in the `desk.*` descriptions, and the
  `pipeline_events_query` → `pipeline.events` rename (pre-release, no
  compat shim).
- Tests per the spec's test law: dispatch-level + error-path tests for
  every new tool, catalogue (`REQUIRED_TOOLS`) extension, model-invoking
  tools tested against monkeypatched services.
- A docs story touching the real entry points, and a committed live walk
  of the sidecar (fresh-HOME boot, full handshake, every family
  exercised, a live `.43` proof for `ask.run`).

### Out

- Kernel admission for non-inference writes; the resource/tool observer
  asymmetry (flagged for the sitting, spec Q5); the
  SequenceWorkflow/WorkbenchRunner dedup — the unselected One Chokepoint
  items.
- Coder write verbs (`reply`, `select_session`) and `cadence.reply` —
  they require live-runtime delivery paths the stdio sidecar does not
  own (counsel Q2/Q4); backlogged, absence named in tool descriptions.
- Issue #450 Waves 1-3; any web UI work; any Swift/iPad work.
- Wiring dw-mcp into `.mcp.json` (counsel Q1).
- The broader test-debt burn-down (untested Activity/credential/
  invocation services) — stays on the ledger.

## Constitutional grounding

- **Article II.2 (a primitive exposes a contract):** seven user-facing
  capabilities have no programmable contract; this phase gives them one.
- **Article III.2 (egress disclosed at the point of decision):**
  `settings.update` can move the egress boundary; its description now
  carries the counsel-mandated egress warning and points to the
  response's `_placement` block.
- **Article VI.1 (states its own limits):** verbs the sidecar cannot
  honestly deliver are excluded and their absence is named in the
  descriptions — an always-failing tool is worse than a missing one.
- **Article XI (one admission path):** all four model-invoking tools
  ride existing admitted paths; the phase opens zero side doors, held by
  the spec's Invariant 1 anchors.
- **Article IX (real-runtime proof):** the phase closes on a live
  sidecar walk — real handshake, real tools, fresh HOME, live `.43`
  proof for the model-invoking path.

## Stories

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HS-133-01 | One registry, many families | done | [story-01](./story-01-family-registry.md) | [evidence-story-01](./evidence-story-01.md) |
| HS-133-02 | Ask over the wire | backlog | [story-02](./story-02-ask-over-the-wire.md) | [evidence-story-02](./evidence-story-02.md) |
| HS-133-03 | Settings over the wire | done | [story-03](./story-03-settings-over-the-wire.md) | [evidence-story-03](./evidence-story-03.md) |
| HS-133-04 | Coder and Memory read out | done | [story-04](./story-04-coder-memory-read.md) | [evidence-story-04](./evidence-story-04.md) |
| HS-133-05 | Cadence over the wire | done | [story-05](./story-05-cadence-over-the-wire.md) | [evidence-story-05](./evidence-story-05.md) |
| HS-133-06 | Sequences and Workflows run admitted | done | [story-06](./story-06-sequence-workflow-run.md) | [evidence-story-06](./evidence-story-06.md) |
| HS-133-07 | Plugin jobs over the wire | done | [story-07](./story-07-plugin-jobs.md) | [evidence-story-07](./evidence-story-07.md) |
| HS-133-08 | The honest handshake | backlog | [story-08](./story-08-honest-handshake.md) | [evidence-story-08](./evidence-story-08.md) |
| HS-133-09 | Surface honesty | backlog | [story-09](./story-09-surface-honesty.md) | [evidence-story-09](./evidence-story-09.md) |
| HS-133-10 | The sidecar has a manual | backlog | [story-10](./story-10-sidecar-docs.md) | [evidence-story-10](./evidence-story-10.md) |
| HS-133-11 | The walk | backlog | [story-11](./story-11-the-walk.md) | [evidence-story-11](./evidence-story-11.md) |

The ask each story answers, in one line: 01 — thirty tools can land in
parallel without six workers fighting over one file; 02 — an MCP client
can ask the desk a question and read an honest receipt; 03 — it can read
and change settings with the egress consequence named; 04 — it can see
coder sessions and search memory; 05 — it can read and safely drive the
cadence engine; 06 — it can run a Sequence or Workflow through the
admitted path; 07 — it can see and retry plugin jobs; 08 — the promised
entry point exists and the auth story is true; 09 — resources are
bounded, the kind gap is named, the last naming violation dies; 10 —
someone who has never seen the sidecar can wire it and use it; 11 — the
whole surface proven live, model path on real metal.

## Suggested order

01 first (keystone, serialized). Then 02-07 in parallel waves with
serialized SHIP (disjoint family modules). 08 and 09 any time after 01
(08 is independent; 09 touches `tools.py`/`resources.py`, serialized
against the keystone). 10 after the families land. 11 last, cannot be
waived.

## Held owner questions

1. **Resource observer asymmetry** (spec Q5): tool reads are observed,
   resource reads are not — fix in a future slice, or ratify the
   asymmetry under Article XI.5? Orchestrator default: future story.
2. **`companion_github_repo` writable via `settings.update`** (counsel
   C.iii): not a secret path, so an MCP client can redirect the
   companion's target repo (no new egress channel; local `gh` auth).
   Acceptable, or should it join SECRET_PATHS? Orchestrator default:
   acceptable, documented.

## Exit criteria (evidence required)

- [ ] `holdspeak/mcp/families/` exists; every new family exports TOOLS +
  dispatch; `tools.py` aggregates; the catalogue test covers all 82.
- [ ] All 30 new tools dispatch to the spec's anchored service methods
  with the spec's schemas; `uv run pytest -q tests/unit/test_mcp_phase133.py
  tests/unit/test_mcp_tools.py` green.
- [ ] The four model-invoking tools reach `InferenceRunner.invoke()`
  through the spec's Invariant-1 chains; no new provider-reaching path
  exists outside them.
- [ ] `holdspeak://cadence/status` reads through `resources/read` with a
  test.
- [ ] `auth.py` carries the truthful docstring; `HOLDSPEAK_URL`/`url` are
  gone; nothing imports them.
- [ ] `uvx --from . holdspeak-mcp` (or `uv run holdspeak-mcp`) starts the
  stdio server; `.mcp.json` exists at repo root, holdspeak-only.
- [ ] Unbounded resources truncate at the ruled limits; `desk.*`
  descriptions name the 6-vs-17 kind boundary; `pipeline.events` replaces
  `pipeline_events_query` everywhere including test function names.
- [ ] Docs entry points teach the sidecar: what it is, how to wire it,
  the tool families, what the sidecar honestly cannot do.
- [ ] The walk: committed harness in `scripts/`, fresh-HOME boot, full
  handshake, every family exercised with real JSON-RPC captured, live
  `.43` proof of `ask.run` receipt honesty, all through
  `dw evidence capture`.

## Where we are

HS-133-01 done: the family registry keystone is in place -- seven skeleton family modules under `holdspeak/mcp/families/`, aggregated by `tools.py`, with synthetic-family registry and dispatch tests green alongside all existing MCP tests.

HS-133-07 done: plugin_job.list, plugin_job.summary, plugin_job.retry, plugin_job.cancel dispatching to PluginJobService with closed schemas; retry/cancel refuse running jobs as isError:true; REQUIRED_TOOLS extended.

HS-133-04 done: coder.list, coder.get, coder.audit, memory.search dispatching to CoderService (reply_sender=None) and MemoryService with spec-verbatim filter schemas; coder.get unknown-session and memory.search missing-query return isError:true; REQUIRED_TOOLS extended; 13 tests green.

HS-133-03 done: settings.get and settings.update dispatching to SettingsService(on_settings_applied=None) with spec-verbatim schemas including the counsel-mandated egress warning; secrets redacted on read and stripped on write; validation errors and stale-revision conflicts surface as isError:true; REQUIRED_TOOLS extended; 8 tests green.

HS-133-05 done: all eleven cadence tools (status, loops, get_loop, brief, closeout, history, audit, snooze, set_status, run_now, apply_closeout) dispatching to CadenceService with spec-verbatim schemas; get_loop async via _run(); set_status rejects outside enum; snooze on unknown loop returns isError:true; holdspeak://cadence/status resource registered and tested through resources/read; REQUIRED_TOOLS extended; 26 tests green.

HS-133-06 done: sequence.run, sequence.cancel, workflow.run, workflow.cancel dispatching to SequenceWorkflowService(db, broker) with broker from _configure(db); runs async via _run(); cancels route through broker.parent_run_controller.cancel_by_operation_id; unknown chain_id/workflow_id/parent_operation_id return isError:true; REQUIRED_TOOLS extended; 12 tests green.
