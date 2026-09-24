# Phase 5 — The One Service Layer (CHARTER DRAFT r2, not ratified; renumbered from 4 on 2026-09-23 when the owner opened Phase 4 The Morning)

**r1** drafted 2026-09-23 by Muad'Dib. **Astra check r1: BOUNCE** (`.tmp/two-brains/20260923-190909-check/phase-4-charter-astra.md`, reviewed HEAD 46172fcf) — the inventory was loose, the owner's ruling and Muad'Dib's proposal were blurred, the existing descriptor was over-read, two composition gaps were unnamed, the ratchet counted aggregates, and story 06 asked the owner to learn operation names. **r2** (this file) pays that check. Astra's counter-proposal for the story list is adopted with amendments noted. The owner has not ruled. Nothing is built. Phase 3 closes first.

## 1. The owner's ruling (verbatim, 2026-09-23)

"the sidecar design is an absolutely retarded design — things have to flow through services — it has always been my ask but somehow that ask got misinterpreted."

That is the whole of what he ruled. Everything below §1 is the two brains' proposal for how to honour it, and is labelled so.

## 2. What went wrong (the brains' reading)

"Flow through services" was built as "the MCP layer calls the service classes". The result is a second hand-wired catalogue: 225 tool declarations, a 61-branch `if name ==` dispatcher plus per-family dispatchers, 6,430 lines, each tool wiring its own service instance. It is not a surface of the services; it is a parallel adapter that drifts from the routes.

## 3. The tree today (Astra-verified counts, r1 corrected; counting rules in Astra's report)

| Fact | Where |
|---|---|
| 113 `.py` files under `holdspeak/services/` incl. `__init__.py`; constructors are NOT uniform (`agent_turn_service.py:53`, `people_service.py:72`, `sequence_workflow_service.py:39` differ) | `holdspeak/services/` |
| One production construction site of `CanonicalApplicationOperationDescriptor` (`agent_turn_service.py:64`). The descriptor is a narrow model-tool projection: rejects empty arg schemas and existing keywords (`tool_capability_service.py:101,113,129`), model-specific limits (`:262`), stores the operation as a STRING (`:230`). Precedent, not a contract. | `services/tool_capability_service.py:219` |
| One composition root (HS-200-45), which permits fresh instances (`composition.py:318,337`) and does not cache its fallback | `holdspeak/runtime/composition.py` |
| 111 route `.py` files (105 excl. package inits); 46 files hold 67 `*Service(...)` constructions — some lawful partial-context fallbacks, NOT 46 violations; 15 accept `ctx` and never load it; 60 direct `get_database()` calls | `holdspeak/web/routes/` |
| MCP: 225 declarations, 61 `if name ==` branches, 6,430 lines, ten envelope helpers over five names; stdio is a proxy by default but standalone mode still composes locally and claims the owner lock (`mcp/server.py:459`) | `holdspeak/mcp/` |
| **Composition gap A:** HTTP supplies the brief's producer clock (`routes/monday_brief.py:97`); MCP builds another `MondayBriefService` without it (`mcp/tools.py:685`) — MCP cannot prove next-day behaviour | |
| **Composition gap B:** MCP builds an unwired summary service (`mcp/tools.py:879`) losing the notification callback (`meeting_intel_service.py:78`) — an MCP-driven summary leaves the Desk stale | |
| Kernel: 26 startup operation registrations (`kernel/runtime.py:87`); `OperationSpec` is codecs + authority + lifecycle (`kernel/model.py:51`), a different job from an application operation; HTTP reaches `kernel.submit` at `routes/system/kernel_routes.py:35`; some services and MCP families reach admitted paths (`mcp/families/sequence.py:92`) | |
| The rig: 455 `ui` / 55 `api` steps over 74 cases; no `op` kind (`graph_walk.py:2288`); `run_case()` ALWAYS starts Playwright (`:3603,:3675`); protocol snapshots evaluate the page (`:488`); restart retention is skipped without a page (`:2640,:2651`) | `scripts/graph_walk.py` |
| Council deferral: "The 225 MCP tools, 29 CLI commands and the connector inputs are enumerated, not walked." | `COUNCIL.md:57` |

## 4. Goal (one line, the brains' proposal)

The Phase 3 meeting loop (import → summary → restart → decision → dated brief → the Thought's save) reachable by HTTP, by MCP and by the rig through ONE declared application-operation contract bound to ONE live service instance per hub, with the duplicate MCP definitions for that slice retired and a residual set that only shrinks.

## 5. The roots

Tenet 1 and Tenet 3 cut both ways. The over-engineering already happened (a second catalogue). This phase removes an interface; it adds none the owner sees. The desk stays 90% of the work. Article IX (evidence): service/state proof, kernel proof where observed, and browser proof are three different claims and are never substituted for one another.

## 6. Scope

- **In:** the enumerated pilot below; a small application-operation contract (name, version, args schema, description, result and refusal shapes, completion identity, intended transport exposure); per-hub wiring for the pilot services (callbacks, clock) with both transports bound to it; the rig's headless `op` execution against the owning isolated hub; migration fences and the complete-roster doc check shipped with each conversion; the owner's rehearsal.
- **Out:** migrating the other tools/routes (the residual set pays story by story, later phases); CLI and connectors; any face change; new kernel admissions (existing service-owned admissions and receipts are preserved, never double-admitted, never exempted by a label — `CONSTITUTION.md:169`); native recording.

### The pilot operations (to be settled exactly in story 01 — this is the enumeration Astra asked for)

| Job step | Operation(s) to declare | Today's HTTP | Today's MCP | Note |
|---|---|---|---|---|
| Import + completion | `meeting.import` (multipart custody stays transport work, `meeting_import.py:52,90`), `meeting.read` (transcription state) | route | none | no MCP import tool exists today |
| Summary | `meeting.summary.run` (planned host/hash), `meeting.summary.read` (terminal reads, plain cause) | route + factory (`routes/meetings/intel.py:17`) | `tools.py:879` unwired | gap B |
| Restart | not an operation — a rig process action (`graph_walk.py:2630`); equality is proved by `meeting.read` before/after | | | |
| Decision | `decision.create` / `decision.read` (the A1 route pair; Desk decisions vs lifecycle transitions vs decision records distinguished) | route | `records` in tools.py | |
| Brief | `brief.generate` / `brief.latest` with the producer clock | route (`monday_brief.py:97`) | `tools.py:685` no clock | gap A; projections differ (`monday_brief.py:109` vs `tools.py:963`) — equivalent domain behaviour, transport contracts preserved |
| Thought | `thought.save` / `thought.read` (A4's KEPT receipt) | route | ? | to enumerate |

## 7. Stories (Astra's counter-proposal, amended; effort = council-style estimate)

| ID | Story | What is true when it is done | Effort |
|---|---|---|---|
| PHILO-5-01 | One decision through one service contract | The minimal contract settled between the brains (decorator vs descriptor module is theirs, not the owner's). `decision.create`/`decision.read` reachable by route and by MCP through one adapter bound to the hub's one instance; dispatch, persistence, refusal and notification proven; the duplicate MCP definition retired. The export (`docs/generated/operations.json`), the migration fence (explicit residual set with reasons; a new residual identity FAILS; paid entries removed in the same commit) and the complete-roster doc check (generated + legacy, `gen_mcp_sidecar_doc.py:34`, `test_mcp_sidecar_doc_drift.py:41`) ship together. | 2–3 days |
| PHILO-5-02 | Meeting, brief and Thought share that contract | The rest of the pilot table: import/completion, summary run/read with the callback (gap B), brief with the producer clock (gap A), Thought save/read; existing service-owned admissions preserved; residual set shrinks by exactly these. | 3–4 days |
| PHILO-5-03 | The actual atlas proves the three paths | Headless `op` execution and observation in `graph_walk.py` against the owning isolated hub (never a second writer): setup, observation, waiting, restart evidence all charted for the no-page path. NAMED atlas pairs (listed in the story, not "cases that have both") where the durable outcome and refusals must agree between the `api`/`op` path and the browser path; face verdicts stay independent and browser-only; `api` steps stay for HTTP contracts. Duration measured and recorded, not promised. | 2–3 days |
| PHILO-5-04 | The owner uses the loop | Rehearsed in isolation first. Then the owner asks for the meeting job in his normal way (his MCP client, his words) and finds the summary, the decision, the dated brief and the saved Thought on his Desk — he never operates operation names, arguments or test clocks. Both brains' technical verdicts; his usefulness judgment; his words close the phase. | his sitting |

Dependency: 01 → 02 → 03 → 04.

## 8. Exit criteria (evidence required)

- [ ] Every pilot operation is reachable by route, by MCP and by the rig's `op` step, resolving to the same declared contract and the same live instance within one hub (proved in-hub, not across restart).
- [ ] The duplicate MCP definitions for the pilot are gone; the residual set is explicit, reasoned, and shrank by the pilot's entries; the fence fails on a new residual identity (red proved on a copy of main).
- [ ] The complete tool roster (generated + legacy) is regenerated and drift-guarded.
- [ ] The named atlas pairs agree on durable outcome and refusals; the 1440/393 face walks are retained separately.
- [ ] The owner's sitting: the loop from his client, results on his Desk, his words.

## 9. Decisions for the owner (r2 — only what is his)

- **D1 Pilot scope.** The complete bounded Phase 3 jobs incl. the Thought (recommended, both brains), or the decision slice only.
- **D2 The stdio proxy.** Keep the thin proxy for his chosen client (recommended); standalone-mode local composition (`server.py:459`) retired.
- **D3 Access path for his sitting.** Which MCP client he wants to drive the loop from (Claude Code in this repo, or another).

Settled between the brains, not put to him: declaration style; effect handling (preserve existing admissions, no double-admit, no label exemption); proof discipline (Article IX).

## 10. Risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| A third catalogue beside routes and tools | high | duplicates RETIRED in the same story; residual set explicit | a pilot op still has a hand-written route body or tool |
| An MCP reply leaves the Desk stale or on the wrong producer day | high today | gaps A and B are named story-02 acceptance | a successful MCP call with no `desk_changed` / wrong brief date |
| Op-tier confidence substitutes for face truth | medium | Article IX; face walks browser-only and retained | an atlas face case loses its selector or is "proved" by op |
| Migration appetite swallows the phase | high | the pilot table is the whole scope | a story touches an op outside the table |
| The owner is asked to operate the catalogue | medium | story 04 is his normal job request | a sitting step names an operation |

## 11. Open, for Astra r2

- Exact pilot table (§6): confirm the Thought pair and the decision create/read pair against A1/A4's routes.
- Whether `composition.service()` gains caching for pilot services or the hub composes them eagerly at startup.
