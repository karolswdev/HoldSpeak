# PHILO-5-02 - The loop shares the contract

- **Project:** holdspeak-philo
- **Phase:** 5
- **Status:** backlog
- **Depends on:** PHILO-5-01
- **Unblocks:** PHILO-5-03
- **Owner:** Muad'Dib (Opus 5.5); Astra checks on built
- **Council tag:** Astra r2 findings 3, 4, 5; the owner's D1

## Problem

The rest of the loop has the same two hand-wired paths, and three of them diverge in behaviour. MCP builds a clockless brief service (`holdspeak/mcp/tools.py:685`; HTTP supplies the clock at `routes/monday_brief.py:97`) and an unwired summary service (`holdspeak/mcp/tools.py:879`, losing the `runtime_queue` notification at `holdspeak/services/meeting_intel_service.py:78`). HTTP summary `_svc()` prefers the factory over the composed instance (`holdspeak/web/routes/meetings/intel.py:16`, `holdspeak/web_server.py:932`). MCP resources construct their own brief, meeting and Thought services (`holdspeak/mcp/resources.py:504,523,566`). Import has no MCP tool and carries config, transcriber and tmp-file custody (`holdspeak/web/routes/meeting_import.py:52,90`). Shelf write/read has no MCP tool at all.

## Scope

- **In:** the corrected inventory (phase status, "The pilot inventory") minus the decision rows: `meeting.import` with the MCP import intake (its client contract settled between the brains BEFORE the worker brief; a raw `tmp_path`, configuration object or transcriber factory is not a client contract); `meeting.list` / `meeting.read` (the summary's planning, completion and terminal read — no separate summary-read implementation); `meeting.summary.run` with the `runtime_queue` callback; `brief.generate` / `brief.latest` with the producer clock (preserving `monday_brief.generate`'s `generate=true`); `brief.shelf.write` / `brief.shelf.read`; `thought.create` / `thought.save` / `thought.read` / `thought.workbench.read` / `thought.list`; the MCP resource bindings (`holdspeak://meetings/{id}`, `holdspeak://briefs/latest`, `holdspeak://thoughts/…`); the HTTP summary factory-vs-instance; gaps A–F closed.
- **Out:** everything the phase status lists as out; already-open brief refresh (a fresh/reopened Desk read is accepted); any face change.

## Acceptance criteria

- [ ] Every inventory row above reaches one declaration and the hub's one live instance by HTTP and by MCP (tool or resource), object identity asserted in-hub; the duplicate MCP definitions retired; the residual set shrinks by exactly these entries.
- [ ] Gap A: an MCP brief generate uses the hub's producer clock (same producer day as HTTP). Gap B + F: an MCP summary run fires the `runtime_queue` notification (the fence names `runtime_queue`, not `desk_changed`). Gap C: HTTP summary uses the composed instance, not a factory. Gap D: MCP resources read through the hub's instances. Gap E: import keeps its multipart/file custody in the transport.
- [ ] A4's KEPT is working-copy save: revision checks, workspace cursor and `working_note.last_modified` preserved (`holdspeak/web/routes/primitives/thoughts.py:191`).
- [ ] Phase 4 invariants preserved: Generate remains reachable in every ratified state; pending, failure and success receipts survive the rendered transition.
- [ ] Phase 4 invariants preserved: decision rows lead; recency comes from persisted `created_at`, survives reload, and respects the existing three-row cap.
- [ ] Phase 4 invariants preserved: one source failure appearing in two briefs produces distinct brief-scoped item IDs, while old rows and shelf state remain unchanged.
- [ ] Phase 4 invariants preserved: `ALL n HANDLED` counts the nonempty Arrival item set with valid Ack/Defer states, excludes THIS WEEK, and cannot appear while a hidden raw-ID row remains unhandled.
- [ ] Compatibility: names, arguments, defaults, envelopes, resource URIs, refusals and palette membership preserved; existing service-owned admissions and receipts preserved with no double admission; any missing admission named, not certified.
- [ ] Fence law: every behavioural fence is red pre-fix through the real producers (real services, the real hub, the real lock and config paths — no test double that lies about the field the check reads); new structural invariants are proved by deliberate mutations that turn the fence red. An import failure or an unavailable symbol is not the required red.

## Effort (council-style estimate, not a promise)

4–5 days (Astra r2)

## Test plan

- **Unit:** per-operation identity and behaviour fences (clock, `runtime_queue`, factory-vs-instance, resources, save revision) red pre-fix through the real services; the four Phase 4 invariant fences re-run; compatibility and residual guards.
- **Integration:** the loop by HTTP and by MCP against one isolated hub, durable state read back across a restart.
- **Manual / device:** none (proof mode: rehearsed; story 04).

## Notes

- 2026-09-24 — chartered from draft r3 + Astra r2 (`checks/charter-astra-r2.md`, findings 3, 4, 5 and the story-02 amendment).
