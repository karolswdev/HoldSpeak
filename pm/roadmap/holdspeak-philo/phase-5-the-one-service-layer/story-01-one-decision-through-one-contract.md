# PHILO-5-01 - One decision through one contract

- **Project:** holdspeak-philo
- **Phase:** 5
- **Status:** in-progress
- **Depends on:** -
- **Unblocks:** PHILO-5-02, PHILO-5-04 (the Codex path)
- **Owner:** Muad'Dib (Opus 5.5); Astra checks on built
- **Council tag:** Astra r2 findings 1, 2, 6, 7; the owner's D2 and D3

## Problem

Decisions reach HTTP through `POST/PUT/GET /api/decisions` (`holdspeak/web/routes/primitives/decisions.py:35`) and MCP through the generic `desk.create/update/list/get` with `kind="decisions"` (`holdspeak/mcp/tools.py:554,689`): two hand-wired paths to one job. No application-operation contract exists; the one descriptor in production is a narrow model-tool projection (`services/tool_capability_service.py:219`). The stdio MCP entry still has a standalone mode that composes services locally and claims the owner lock (`holdspeak/mcp/server.py:459`), which D2 retires. The Codex path of D3 is broken on two seams: the rig claims the lock without a port (`scripts/graph_walk.py:1494`), which `discover_hub()` rejects (`holdspeak/mcp/server.py:119`); the rig's token is not persisted to `meeting.web_auth_token` (`scripts/graph_walk.py:1517`, `holdspeak/mcp/server.py:144`, `holdspeak/web_server.py:322`). `scripts/astra` forwards `-C` but no `-c` overrides (`scripts/astra:20,50`).

## Scope

- **In:** `decision.create` / `decision.update` / `decision.read` / `decision.list` through one descriptor-module contract bound at hub composition, reached by the HTTP routes and by the MCP decision path; the export `docs/generated/operations.json`; the compatibility guards and the identity-based residual baseline/fence (`(transport, entry point, discriminator)`, pinned to `4b4f8d94`); the complete-roster doc check (generated + legacy); RETIRING the production standalone MCP entry (`mcp/server.py:459`) with its docs and tests; the Codex path: the rig publishes its loopback endpoint through the existing lock producer and persists the matching token through the isolated config path; the wrapper's narrow repeated `-c` passthrough; the concrete Codex configuration (lane executable + cwd absolute, proxy HOME = hub HOME, proxy mode only, default DB path under that HOME, Codex auth kept apart).
- **Out:** everything the phase status lists as out; the other pilot operations (story 02); the generic `desk.*` tools for other kinds; the rig's `op` step (story 03).

## Acceptance criteria

- [ ] The contract is a small explicit descriptor module (name, version, args schema incl. empty objects, description, result and refusal shapes, completion/read identity, transport exposure) bound to the hub's one live decision service at composition; no decorator/plugin framework; the model-tool descriptor and kernel `OperationSpec` keep their roles.
- [ ] HTTP and MCP reach the same declaration and the same live instance within one hub (object identity asserted in-hub); durable state compared across restart.
- [ ] The duplicated MCP decision path is retired; `desk.*` stays for its other kinds with unchanged names, arguments, defaults, envelopes, refusals and palette membership; palette refusal tested through dispatch (`holdspeak/mcp/tools.py:1045`) and catalogue filtering.
- [ ] `docs/generated/operations.json` is generated and drift-guarded; the complete tool roster (generated + legacy, `gen_mcp_sidecar_doc.py:34`, `test_mcp_sidecar_doc_drift.py:41`) regenerated and drift-guarded.
- [ ] The residual fence lists identities with reasons; a new residual identity FAILS (red proved on a copy of main); paid entries leave in the same commit; the public tool count and the residual implementation set are reported as separate measurements.
- [ ] The standalone MCP entry is gone from production (`mcp/server.py:459`), with its docs and tests updated; `holdspeak-mcp` is proxy-only.
- [ ] The Codex path, against an isolated HOME and never the desk: the rig hub's port is published through the existing lock producer and its token persisted through the isolated config path; from a FRESH Codex session with the wrapper's `-c` passthrough, the proxy discovers the hub, authenticates, performs one real decision write, and rediscovers the hub after a restart. The effective Codex configuration (HOME, lock, DB path) is retained as evidence.
- [ ] Fence law: every behavioural fence is red pre-fix through the real producers (real services, the real hub, the real lock and config paths — no test double that lies about the field the check reads); new structural invariants are proved by deliberate mutations that turn the fence red. An import failure or an unavailable symbol is not the required red.

## Effort (council-style estimate, not a promise)

3–4 days (Astra r2)

## Test plan

- **Unit:** the contract binding and identity fence; the residual fence (red on a copy of main); compatibility and palette-through-dispatch guards; the lock-publishes-port and token-persisted fences against the real lock producer and config path.
- **Integration:** the Codex → stdio proxy → isolated rig hub run (discovery, auth, one decision write, restart rediscovery), transcript and effective configuration retained under this phase's assets.
- **Manual / device:** none (proof mode: rehearsed; story 04).

## Notes

- 2026-09-24 — chartered from draft r3 + Astra r2 (`checks/charter-astra-r2.md`, findings 1, 2, 6, 7 and the story-01 amendment).
- 2026-09-24 — the owner ratified the charter; build starts (Muad'Dib lane).
