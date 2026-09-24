# Phase 5 - The One Service Layer

**Last updated:** 2026-09-24 (02 BUILT on `feat/philo-5-02-the-loop`; Astra checks on built).

## Goal

The Phase 3 meeting loop (import → summary → restart → decision → dated brief → the Thought's save), with the Phase 4 morning seams, reachable by HTTP, by MCP and by the rig through ONE declared application-operation contract bound to ONE live service instance per hub, with the duplicate MCP definitions for that slice retired and a residual set that only shrinks.

## Authority

The owner, 2026-09-23 (verbatim): "the sidecar design is an absolutely retarded design — things have to flow through services — it has always been my ask but somehow that ask got misinterpreted."

The owner, 2026-09-24, by AskUserQuestion (verbatim options chosen; the parked draft §9):

- **D1 Pilot scope: the whole Phase 3+4 loop.** Import, summary run/read, decision create/read, brief generate/latest with the producer clock, Thought save/read (plus the Phase 4 seams: Generate in every state, the visible-row order, brief-scoped breakage ids, the handled line). Not decisions-only; not the desk-primitive family.
- **D2 The stdio proxy: KEEP the thin proxy.** `holdspeak-mcp` keeps forwarding to the running hub; the leftover standalone mode that composes services locally and claims the owner lock (`mcp/server.py:459`) is RETIRED in this phase.
- **D3 Access path for the closing use: CODEX (Astra's side).** The loop is driven from the other brain's client, proving the catalogue is client-neutral. Consequence: story 04's rehearsal runs on Astra's lane (Codex's MCP config pointed at an isolated hub), Muad'Dib counsels on built; the owner's own client is not required.
- **Proof mode: REHEARSED, the owner skims shots.** A lane drives the loop from Codex in an isolated hub, retains the transcript and the desk shots at 1440 and 393; the owner looks at the shots; no live sitting. Recorded as "rehearsed, owner-reviewed shots", never as an observed sitting.

Everything below the owner's words is the two brains' proposal for how to honour them.

## The roots

Tenet 1 and Tenet 3 cut both ways. The over-engineering already happened (a second catalogue). This phase removes an interface; it adds none the owner sees. The desk stays 90% of the work. Article IX (evidence): service/state proof, kernel proof where observed, and browser proof are three different claims and are never substituted for one another.

What went wrong (the brains' reading): "flow through services" was built as "the MCP layer calls the service classes". The result is a second hand-wired catalogue: 225 tool declarations, a 61-branch `if name ==` dispatcher plus per-family dispatchers, 6,430 lines, each tool wiring its own service instance. It is a parallel adapter that drifts from the routes, not a surface of the services.

## Status of this charter

RATIFIED by the owner 2026-09-24 (AskUserQuestion): "Ratify, build it" — the four sequential stories and the provisional 11–14 engineering days; and "Accept reopening" — for Phase 5 a fresh/reopened Desk read is accepted to see a brief changed through Codex; already-open refresh is NOT claimed and is not in scope. Build starts: story 01 (Muad'Dib lane), Astra checks on built.

## Scope

- **In:** the pilot per D1 — the corrected inventory below (Astra r2 finding 3); a small application-operation contract (a descriptor module: name, version, args schema, description, result and refusal shapes, asynchronous completion/read identity, intended transport exposure); per-hub eager binding of the pilot services (callbacks, clock) with both transports bound to it; the MCP resources that read the pilot's objects; the retirement of the standalone MCP entry (D2); the Codex seams (D3); the rig's headless `op` execution against the owning isolated hub; compatibility guards, the residual fence and the complete-roster doc check shipped with each conversion; the rehearsal (proof mode).
- **Out:** migrating the other tools/routes (the residual set pays story by story, later phases); CLI and connectors; any face change; new kernel admissions (existing service-owned admissions and receipts are preserved, never double-admitted, never exempted by a label — `CONSTITUTION.md:169`); native recording; the generic `desk.*` tools for kinds other than decisions; the brief's freshness on an already-open Desk: **a fresh/reopened Desk read is accepted for the brief; already-open brief refresh is NOT claimed** (Arrival reads the brief on mount; its `desk_changed` subscription refreshes assignments, not the brief — `web/src/desk/chair/ChairHome.tsx:523,634,917`). A stronger freshness promise needs a named scope amendment.

### The pilot inventory (Astra r2 finding 3, verbatim)

The minimum transport inventory is below. Canonical names are the application-operation names proposed for the charter; existing public names remain compatible.

| Application operation | Current HTTP | Current MCP |
|---|---|---|
| `meeting.import` | `POST /api/meetings/import` | **No tool.** A real MCP intake must be added. |
| `meeting.list` / `meeting.read` | `GET /api/meetings`; `GET /api/meetings/{meeting_id}` | `meeting.list`; `meeting.get` |
| `meeting.summary.run` | `POST /api/meetings/{meeting_id}/intelligence/run` | `meeting.run_intelligence` |
| Summary planning, completion and terminal read | The same meeting-detail GET carries the planned route/hash, summary, job state and run receipt | `meeting.get`; also `holdspeak://meetings/{id}` |
| `decision.create` / `decision.update` | `POST /api/decisions`; `PUT /api/decisions/{decision_id}` | `desk.create` / `desk.update`, with `kind="decisions"` |
| `decision.list` / `decision.read` | `GET /api/decisions`; `GET /api/decisions/{decision_id}` | `desk.list` / `desk.get`, with `kind="decisions"` |
| `brief.generate` / `brief.latest` | `POST /api/brief/generate`; `GET /api/brief/latest` | `monday_brief.generate`; `monday_brief.get`. Preserve its `generate=true` behavior. Latest also has `holdspeak://briefs/latest`. |
| `brief.shelf.write` / `brief.shelf.read` | `POST /api/brief/items/{item_id}/shelf`; `GET /api/brief/shelf` | **No tools.** Needed for Ack/Defer and handled-state parity. |
| `thought.create` / `thought.save` | `POST /api/thoughts`; `PATCH /api/thoughts/{thought_id}/working` | `thought.create`; `thought.update_working` |
| `thought.read` / `thought.workbench.read` | `GET /api/thoughts/{thought_id}`; `GET /api/thoughts/{thought_id}/workbench` | No corresponding tools; existing resources `holdspeak://thoughts/{thought_id}` and `…/workbench` |
| `thought.list` | `GET /api/thoughts?state=unfinished` | Resource `holdspeak://thoughts/unfinished`; no corresponding tool |

Sources: `holdspeak/web/routes/meeting_import.py:52`, `holdspeak/web/routes/meetings/crud.py:39`, `holdspeak/web/routes/meetings/intel.py:86`, `holdspeak/web/routes/primitives/decisions.py:35`, `holdspeak/web/routes/monday_brief.py:104`, `holdspeak/web/routes/primitives/thoughts.py:51`, `holdspeak/mcp/tools.py:689`, `holdspeak/mcp/tools.py:764`, `holdspeak/mcp/families/thought.py:182`, `holdspeak/mcp/resources.py:523`.

Specific corrections:

- `decision_record.create_from_desk` consumes an existing decision ID; it is not A1’s create operation.
- The closure’s **Done** writes through PUT. Create/read alone cannot preserve the browser chain: `docs/internal/philo/graph/atlas-phase3.json:1453`.
- A4’s **KEPT** means working-copy save, not `thought.complete`. Preserve revision checks, workspace cursor, and `working_note.last_modified`: `holdspeak/web/routes/primitives/thoughts.py:191`.
- Do not invent a separate summary-read implementation when `meeting.read` already supplies it.
- Restart and producer-clock advancement remain rig actions. Neither becomes an owner operation.

## The revision and counting basis

Pinned to main `4b4f8d94` (Astra r2 reviewed `3881301f`; its only change from `4b4f8d94` is the draft). Astra r2 finding 7, verbatim — **census facts, not violation counts:**

> Recount confirms 113 service Python files; 111 route Python files, 105 excluding package initializers; 67 syntactic `*Service(...)` constructions across 46 files; 15 files accepting but never loading `ctx`; 60 direct `get_database()` calls; 225 assembled unique tools; 61 `if name ==` branches in `tools.py`; and 6,430 lines across `tools.py` plus family Python files. These are census facts, not violation counts.
>
> The atlas count is incomplete for D1: `atlas.json` contains 74 cases, 455 UI and 55 API steps; `atlas-phase3.json` adds **16 cases, 251 UI and 34 API steps**. Count both named files, excluding archived variants.

Other baseline facts (draft r3 §3, Astra r1-corrected): constructors are not uniform (`agent_turn_service.py:53`, `people_service.py:72`, `sequence_workflow_service.py:39`); one production construction of `CanonicalApplicationOperationDescriptor` (`agent_turn_service.py:64`), a narrow model-tool projection (`tool_capability_service.py:101,113,129,230,262`) — precedent, not a contract; one composition root that permits fresh instances and does not cache its fallback (`runtime/composition.py:318,337`); kernel `OperationSpec` is codecs + authority + lifecycle (`kernel/model.py:51`), a different job; the rig has no `op` kind (`graph_walk.py:2288`) and `run_case()` always starts Playwright (`:3603,:3675`).

## Composition gaps

- **A — the brief's clock.** HTTP supplies the brief's producer clock (`routes/monday_brief.py:97`); MCP builds another `MondayBriefService` without it (`mcp/tools.py:685`). MCP cannot prove next-day behaviour.
- **B — the summary's callback.** MCP builds an unwired summary service (`mcp/tools.py:879`), losing the notification callback (`meeting_intel_service.py:78`).
- **C — the HTTP summary factory.** HTTP summary `_svc()` prefers the factory over the already-composed instance; the hub supplies both, so fixing MCP alone does not establish shared object identity (`holdspeak/web/routes/meetings/intel.py:16`, `holdspeak/web_server.py:932`).
- **D — the MCP resources.** MCP resource reads independently construct brief, meeting and Thought services; Thought workbench reads obtain their coordinator through the standalone-family runtime, not the hub's application service (`holdspeak/mcp/resources.py:504,523,566`).
- **E — import's custody.** Import carries configuration, transcriber construction and temporary-file custody — real dependencies, not a generic JSON call (`holdspeak/web/routes/meeting_import.py:90`).
- **F — the right event.** The notification fence names the actual event: summary notification is `runtime_queue`, not `desk_changed` (`holdspeak/services/meeting_intel_service.py:78`). Requiring `desk_changed` for every successful operation would be a false fence.

## The Codex seams (D3)

Astra r2 findings 1 and 2, in substance. Owner: story 01.

- **HOME isolation works.** `DEFAULT_DB_PATH`, its owner lock and `CONFIG_FILE` resolve beneath the subprocess HOME; Astra verified this in a fresh temporary HOME with the real constants and discovery function (`holdspeak/db/core.py:47`, `holdspeak/config/core.py:35`, `holdspeak/mcp/server.py:102`).
- **The rig publishes no port.** The rig calls `claim_database(database.db_path)` without a port (`scripts/graph_walk.py:1494`); `discover_hub()` rejects a missing or nonpositive port (`holdspeak/mcp/server.py:119`). The real lock producer reproduced `held=True, owner_alive=True, published_port=None, proxy_discovery=None`.
- **The rig's token is not persisted.** The rig passes its token directly to `MeetingWebServer`; the proxy reads `meeting.web_auth_token` from the config file, and the rig does not persist the matching token (`scripts/graph_walk.py:1517`, `holdspeak/mcp/server.py:144`, `holdspeak/web_server.py:322`). Publishing the port alone does not complete the connection.
- **The wrapper passes `-C`, no `-c`.** `scripts/astra` forwards `-C` but accepts neither arbitrary Codex configuration overrides nor a profile option (`scripts/astra:20,50`). `--cd` alone does not establish isolation. Local `codex-cli 0.155.1` accepted explicit `-c mcp_servers.…` overrides incl. the server HOME; project-config activation is unverified. The wrapper gains a narrow repeated `-c` passthrough.
- **The concrete Codex configuration binds:** the lane's executable and working directory (absolute paths); the proxy's `HOME` = the hub's isolated HOME, set before Python imports its path constants; proxy mode only, no standalone composition; the default DB path under that HOME (a hub on an arbitrary custom DB path does not redirect `serve()` discovery). Codex's own authentication/session environment stays separate from HoldSpeak's data HOME.
- **Story 01 pays and proves both seams:** publish the rig hub's loopback endpoint through the existing lock producer; persist the matching token through the isolated configuration path; then discovery, authentication, one real decision write and restart rediscovery through the proxy, from a fresh Codex session. Never the desk.

## Named atlas pairs

Astra r2's list, verbatim. The existing cases are retained; **`.op` siblings to be minted in story 03** (they do not exist yet).

- `case.closure.chain.s1_import_complete`, `s2_summary_with_host`, `s3_same_summary_after_restart`, `s4_decision_recorded`.
- `case.a1.decision_face_create.opens_and_reopens`, including its named invalid-status refusal.
- `case.a3.brief_next_day.decision_on_the_face` paired with existing API case `case.a3.brief_next_day.new_id_with_the_decision`.
- `case.closure.chain.s5_next_day_brief_has_it` and its separate `s5_next_day_brief_with_breakage` variant.
- `case.philo404.arrival_triaged_headline.all_handled`, paired with the shelf operations.
- `case.j11.thought_keep.receipt_time`, paired with durable saved-body/revision/time assertions.
- From `atlas.json`: summary no-transcript/no-assignment refusals; same-day brief identity; shelf acknowledged/deferred/refused cases.

Evidence anchors: `docs/internal/philo/graph/atlas-phase3.json:454,926,1772,3129`.

## Compatibility and the residual set

Astra r2 finding 6:

- Residual identities are `(transport, entry point, discriminator)` where necessary — tool names are too coarse. `desk.create/get/update/list` serve several primitive kinds (`holdspeak/mcp/tools.py:554,689`).
- Retire the duplicated **decision path**, not the generic `desk.*` tools; the generic compatibility entry stays for its remaining kinds. Generated aliases reach the same declaration; paid application branches disappear in the same commit.
- Preserve names, arguments, defaults, envelopes, refusal behaviour and palette membership. Test palette refusal through dispatch (`holdspeak/mcp/tools.py:1045`) as well as catalogue filtering.
- Newly exposed import/shelf operations may raise the public tool count while the residual implementation set shrinks. These are different measurements, reported separately.

## Phase 4 invariants preserved

Astra r2 finding 5, verbatim, as acceptance (story 02; proved again by the named pairs in story 03):

- Generate remains reachable in every ratified state; pending, failure and success receipts survive the rendered transition.
- Decision rows lead; recency comes from persisted `created_at`, survives reload, and respects the existing three-row cap.
- One source failure appearing in two briefs produces distinct brief-scoped item IDs, while old rows and shelf state remain unchanged.
- `ALL n HANDLED` counts the nonempty Arrival item set with valid Ack/Defer states, excludes THIS WEEK, and cannot appear while a hidden raw-ID row remains unhandled.

Evidence: `web/src/desk/chair/ChairHome.tsx:716,883`, `holdspeak/services/monday_brief_service.py:394,556`.

## Settled between the brains

Astra r2's seven positions, verbatim; Muad'Dib's answer after each.

- **Declaration:** a small explicit descriptor module, bound to actual callables at hub composition. No general decorator/plugin framework. Permit empty argument objects; describe result, refusal and asynchronous completion/read identity. Keep the existing model-tool descriptor and kernel `OperationSpec` in their narrower roles.
  Muad'Dib: ACCEPTED.
- **Composition:** eagerly bind the pilot’s existing services once per hub, including the clock-bearing brief service. Reuse the existing composition root; do not change global fallback caching to solve this slice. Compare object identity within a hub; compare durable state across restart.
  Muad'Dib: ACCEPTED.
- **Effects:** transports derive the principal; arguments cannot supply authority. Preserve existing service-owned admissions and terminal receipts, without double admission or descriptor-label exemptions. Any discovered missing admission is named for resolution, not silently certified.
  Muad'Dib: ACCEPTED.
- **Transport:** preserve multipart/file custody, HTTP response mapping, MCP envelopes and resource URIs. Settle the MCP import intake before its worker brief; a raw service `tmp_path`, configuration object or transcriber factory is not a client contract.
  Muad'Dib: ACCEPTED.
- **Proof:** `op` reaches the registry inside the owning isolated hub. Setup, waiting, observation and restart must work without a page; currently snapshots call `page.evaluate`, and restart retention is skipped without a page: `scripts/graph_walk.py:523`, `scripts/graph_walk.py:2715`. Preserve API checks and independent rendered 1440/393 checks. Compare domain outcomes and identity relationships across transports, not identical protocol envelopes or independently generated model text.
  Muad'Dib: ACCEPTED, and the headless path is charted in story 03 before any `op` verdict is trusted.
- **Closing proof:** record **“rehearsed, owner-reviewed shots.”** Preserve existing summary delivery without manual refresh. For the brief, explicitly accept a fresh/reopened Desk read within this phase’s no-face-change scope; do not claim already-open brief refresh. A stronger freshness promise requires a named scope amendment.
  Muad'Dib: ACCEPTED.
- **Fences:** real producers for behavioral red/green evidence; deliberate mutations for new structural invariants. Import failure or an unavailable new symbol is not the required pre-fix red.
  Muad'Dib: ACCEPTED.

## Exit criteria (evidence required)

- [ ] 1. Every pilot operation is reachable by route, by MCP and by the rig's `op` step, resolving to the same declared contract and the same live instance within one hub (object identity proved in-hub; durable state compared across restart).
- [ ] 2. The duplicate MCP definitions for the pilot are retired (the decision PATH, not the generic `desk.*` tools); the residual set is explicit, reasoned by `(transport, entry point, discriminator)`, and shrank by the pilot's entries; the fence fails on a new residual identity (red proved on a copy of main).
- [ ] 3. The complete tool roster (generated + legacy) is regenerated and drift-guarded.
- [ ] 4. The named atlas pairs agree on durable outcome and refusals between the `api`/`op` path and the browser path; the 1440/393 face walks are retained separately; real-engine and replayed runs are retained separately.
- [ ] 5. Rehearsed, owner-reviewed shots: Astra drives the job in ordinary words through Codex against an isolated hub; the MCP transcript and the Desk shots at 1440 and 393 are retained; Muad'Dib checks; the owner reviews the shots. Never recorded as a sitting.

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| PHILO-5-01 | One decision through one contract (and the Codex path proved) | done | [story-01-one-decision-through-one-contract](./story-01-one-decision-through-one-contract.md) | [evidence-story-01](./evidence-story-01.md) |
| PHILO-5-02 | The loop shares the contract | done | [story-02-the-loop-shares-the-contract](./story-02-the-loop-shares-the-contract.md) | [evidence-story-02](./evidence-story-02.md) |
| PHILO-5-03 | The atlas proves the three paths | backlog | [story-03-the-atlas-proves-the-three-paths](./story-03-the-atlas-proves-the-three-paths.md) | - |
| PHILO-5-04 | The owner asks in his own words (rehearsed, owner-reviewed shots) | backlog | [story-04-the-owner-asks-in-his-own-words](./story-04-the-owner-asks-in-his-own-words.md) | - |

## Lanes

| Lane | Stories | Owner | Checker | Worktree | Branch |
|---|---|---|---|---|---|
| The contract and the Codex path | 01 | Muad'Dib (Opus 5.5) | Astra | ../wt-philo-5-01 | feat/philo-5-01-one-decision |
| The loop | 02 | Muad'Dib (Opus 5.5) | Astra | ../wt-philo-5-02 | feat/philo-5-02-the-loop |
| The atlas | 03 | Astra (Luna) | Muad'Dib | ../wt-philo-5-03 | feat/philo-5-03-the-atlas |
| The rehearsal | 04 | Astra (Luna) | Muad'Dib | ../wt-philo-5-04 | feat/philo-5-04-his-words |

## Where we are

2026-09-24: PHILO-5-02 ROUND TWO after Astra's check on built (`checks/story-02-built-astra.md`, BOUNCE, four conditions). Paid: (1) the owner boundary — `meeting.import` is `owner_only` in the contract; a remote DESK credential, issued through the real settings route and calling `/api/mcp` from a non-loopback client, now gets `owner_required` and the hub never opens, checks or copies the file (on round one the same call imported the file); the local owner still imports; (2) `thought.list` declares `{items, next_cursor}`, and every braced result declaration is run against its real producer; (3) the shelf write and read are recorded through the registry on HTTP and MCP, and mutations M12/M13 (bypass `invoke`) turn that fence red; (4) the decision admission is INHERITED Article XI DEBT, unruled, assigned to the owner's ruling (BACKLOG + "Decisions deferred"); the zero-count test is characterization only. Audit: no other registry operation reads the filesystem or spawns from a caller-named path. Proof under `docs/internal/philo/phase-5/the-loop/round-2/`. Next: Astra's re-check on built.

2026-09-24: PHILO-5-02 BUILT (`feat/philo-5-02-the-loop`). The rest of the loop is on the contract: 13 more descriptors (`meeting.list/read/import`, `meeting.summary.run`, `brief.generate/latest`, `brief.shelf.write/read`, `thought.create/save/read/workbench.read/list`), bound once at hub composition to the hub's own instances; HTTP routes, MCP tools and the pilot MCP resources call `invoke`, and the hand-written MCP branches are gone. Gaps A-F closed and fenced in the real hub: MCP brief generate runs on the hub's producer clock (the brief service is now composed once, with the clock); an MCP summary run puts `runtime_queue` on the bus; the hub has one summary instance and no factory; the resources read through the registry; import keeps its custody per transport. New MCP tools: `meeting.import` (the hub reads an absolute path and imports its own copy), `monday_brief.shelf`, `monday_brief.shelf_read`. Two measurements: residual 327 -> 320 (7 MCP identities paid; one HTTP identity moved, not paid), public tools 225 -> 228. The decision admission: recorded "no lawful kernel place yet" (below). Found and paid on the way: three Phase 143 census tests were already red on main after PHILO-5-01 (a registry `.invoke` read as a runner entrance; stale line pins) — the census now tells a contract call apart by its declared operation name, mutation-proved. Next: Astra's check on built, then story 03.

2026-09-24: PHILO-5-01 ROUND TWO after Astra's check on built (`checks/story-01-built-astra.md`, BOUNCE on two compatibility regressions). Paid: `GET /api/decisions?limit=501` answers 501 rows again (the caller's `limit` passes through `decision.list` to the repository; round one sliced a 500-row result); the create/update fields are type-permissive again, so every input main accepted is accepted (`title=123`, `decided_at=20260924`, `tags="one"` ...), and a `decision_id` in update data stays refused. Fence: `tests/unit/test_philo5_compat.py` — green on main, red on round one (9 of 11), green now. One narrowing stays on purpose (the settled Effects position): an authority field in `decision.update` data, accepted and ignored on main, is refused. Homes given: the Info-window rename bug (below, deferred + BACKLOG) and the admission gap (below, "Discovered missing admissions"). Next: Astra's re-check on built.

2026-09-24: PHILO-5-01 BUILT (`feat/philo-5-01-one-decision`). The descriptor module `holdspeak/operations.py` holds `decision.create/update/read/list`, bound once at hub composition to the hub's `PrimitiveService`; the decision routes and the MCP `kind="decisions"` branch call `invoke`; the standalone MCP mode is retired; `docs/generated/operations.json` and the residual set (334 -> 327 identities; public tools 225 -> 225) are drift-guarded. The Codex path is PROVED: a fresh `codex exec` session through `scripts/astra -c ...` discovered the rig's isolated hub, wrote `decision_32e0c6ba0eea`, read it back, and read it again after a rig restart (evidence `evidence-story-01.md`). Found: in the hub the project-decisions router answers the decision GETs first; its desk branches now use the contract. Next: Astra's check on built, then story 02.

2026-09-24: RATIFIED by the owner; freshness ruled (reopening accepted). Story 01 starts on `../wt-philo-5-01` / `feat/philo-5-01-one-decision` (Muad'Dib, Opus 5.5 worker); its first proof is the Codex → proxy → isolated-hub loop.

2026-09-24: CHARTERED by the two brains from draft r3 (the owner's D1–D3 and proof mode ruled) and Astra's r2 check (RATIFY-WITH-CONDITIONS); every condition is paid in this file and the four story files. Nothing is built. The owner's ratification is owed; then story 01 starts on `../wt-philo-5-01`.

**Estimate:** 11–14 engineering days, SEQUENTIAL (01 → 02 → 03 → 04), provisional until story 01 proves the integration. The sum is not parallel elapsed time. Owner availability is no longer a live-sitting dependency.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| A third catalogue beside routes and tools | high | duplicates RETIRED in the same story; residual set explicit | a pilot op still has a hand-written route body or tool |
| An MCP reply leaves the Desk stale or on the wrong producer day | high today | gaps A–F are named acceptance in 01/02; the fence names `runtime_queue` for the summary | a successful MCP call with no expected event, or the wrong brief date |
| Op-tier confidence substitutes for face truth | medium | Article IX; face walks browser-only and retained | an atlas face case loses its selector or is "proved" by op |
| Migration appetite swallows the phase | high | the pilot inventory is the whole scope | a story touches an op outside the inventory |
| The owner is asked to operate the catalogue | medium | story 04 is an ordinary-words job request; he reviews shots | a rehearsal step names an operation to him |
| MISSED 1 (highest owner cost): an "isolated" Codex rehearsal cannot find or authenticate to its rig, or reaches the real desk because only `--cd` changed | high until 01 | story 01 pays the port and token seams and proves a fresh Codex session against an isolated HOME | a Codex session resolves a HOME, lock or DB path outside the lane's isolated HOME |
| MISSED 2: a false completed loop (decision update, Thought save vs read, durable shelf operations missing) | medium | the corrected inventory incl. `decision.update`, `thought.save`, `brief.shelf.*` | the closure chain's Done (PUT) or Ack/Defer has no `op` path |
| MISSED 3: duplicate read compositions survive (MCP resources, the HTTP summary factory) | medium | gaps C and D are story 02 acceptance | a resource or `_svc()` constructs its own pilot service |
| MISSED 4: a migration breaks other jobs (generic `desk.*` removed; palette behaviour changed) | medium | retire the decision path only; palette refusal tested through dispatch | a non-decision `desk.*` call or a palette refusal changes |
| MISSED 5: inflated proof (old atlas counts, a replay presented as real-engine, reviewed shots presented as a sitting) | medium | counts pinned to `4b4f8d94`; real/replayed retained separately; the "rehearsed, owner-reviewed shots" wording | any evidence line calls a replay real or a review a sitting |

## Decisions made (this phase)

- 2026-09-24 — PHILO-5-02 round two (Astra's check on built, finding 4, which replaced the round-one text): INHERITED DEBT (Article XI): decision.create/update leave no kernel operation and no receipt through either transport; whether a desk decision write 'acts under Article V' (filing) is UNRULED; retained as debt with an assigned follow-up: `pm/roadmap/holdspeak/BACKLOG.md` "PHILO-5-02 follow-ups" and the line in "Decisions deferred" below, assigning it to the owner's ruling / a later phase; the test at `tests/unit/test_philo5_the_loop.py:618` is CHARACTERIZATION ONLY (both transports leave the same zero) and is labelled so in its docstring. The round-one text claimed that a desk decision write meets none of XI.1's triggers; it omitted "acts under Article V", so that claim is withdrawn. This phase adds no kernel admission (Scope; Tenet 1) — Muad'Dib lane (Opus 5.5), on Astra's ruling on 9.
- 2026-09-24 — PHILO-5-02 round two: `meeting.import` is `owner_only` in the contract (`holdspeak/operations.py:355`); `OperationRegistry.authorize` (`:609`) refuses every non-owner principal with `owner_required` (a `ServiceError`, status 403, the owner-only service idiom) and `invoke` calls it first; the MCP intake calls it before it looks at the caller's path (`holdspeak/mcp/tools.py:706`) and the HTTP upload before it stores the body (`holdspeak/web/routes/meeting_import.py:66`). An absolute caller path copied into hub custody stays the local-owner contract (Astra's ruling on 3: no root restriction) — Muad'Dib lane (Opus 5.5).
- 2026-09-24 — PHILO-5-02 round two: `thought.list` declares `{items, next_cursor}`, the producer's real shape (`holdspeak/services/refinement_thought_service.py:295`) — Muad'Dib lane (Opus 5.5).
- 2026-09-24 — PHILO-5-02: the MCP import intake as built: `meeting.import {path, title?, occurred_at?}`; the hub opens the absolute path, copies it into its own temporary file (the worker consumes the copy, never the caller's file), and makes the same post-custody call as the HTTP upload; refusals by name `path_not_absolute`, `path_not_readable`, `unsupported_type`, `file_empty`; result `{meeting_id, transcription_status}`; completion through `meeting.get` — Muad'Dib (contract), built by the Muad'Dib lane.
- 2026-09-24 — PHILO-5-02: `monday_brief.shelf` takes `state: null` beside the two lawful states, because the face's Ack/Defer toggle clears with null (`web/src/desk/chair/ChairHome.tsx:914`); the three new tools are classified (`thread_tools.py`) and kept out of CHAT_PALETTE, as `monday_brief.generate` is — Muad'Dib lane (Opus 5.5).
- 2026-09-24 — PHILO-5-02: the contract gains `held` (transport-held inputs: a custody file, a config, a factory — never arguments, never validated as data), used only by `meeting.import` (gap E) — Muad'Dib lane (Opus 5.5).

- 2026-09-24 — Astra r2 on story 01: RATIFY-WITH-CONDITIONS, paid; the authority-field narrowing in `decision.update` RATIFIED as an explicit compatibility exception (eight fields accepted-and-ignored on main → refused; `principal` already failed on main). Merged on the fast CI jobs + both brains' verdicts per the owner's ruling — Muad'Dib.

- 2026-09-24 — PHILO-5-01: the published MCP tool schemas stay byte-identical (no per-kind conditional schemas); the decisions branch's effective schema is the descriptor's, enforced by `invoke` and fenced through dispatch — Muad'Dib lane (Opus 5.5).
- 2026-09-24 — PHILO-5-01 round two: the descriptor's decision fields are type-permissive (they were typed in round one and refused inputs main accepted); `decision.list` takes an optional `limit`; a `decision_id` in update data stays refused; the one kept narrowing is the authority refusal on update (settled Effects position) — Muad'Dib lane (Opus 5.5), after Astra's BOUNCE on built.
- 2026-09-24 — PHILO-5-01: `decision.update` keeps `additionalProperties: true` because both transports passed unknown fields through before (the desk rename sends `name`); `decision.create` is closed — Muad'Dib lane (Opus 5.5).

- 2026-09-24 — the owner RATIFIED the charter ("Ratify, build it") and ruled brief freshness ("Accept reopening"). Story 01 in progress — Muad'Dib.

- 2026-09-24 — Astra r3 (final) on the charter: RATIFY-WITH-CONDITIONS; the one condition (story 02: `generate=true` belongs to `monday_brief.get`, not `monday_brief.generate`) paid; the two owner questions Astra named (ratify the charter + 11–14 sequential days; accept reopening the Desk for a Codex-changed brief vs amend scope) put to the owner by AskUserQuestion — Muad'Dib.

- 2026-09-24 — CHARTERED by the two brains; the draft parked at `assets/charter-draft-r3.md`; Astra r2's conditions paid in this file and the story files — Muad'Dib.
- 2026-09-24 — Muad'Dib ACCEPTS all seven of Astra's r2 between-brain positions (Declaration, Composition, Effects, Transport, Proof, Closing proof, Fences); on Proof, the headless path is charted in story 03 before any `op` verdict is trusted — Muad'Dib.
- 2026-09-24 — Astra check r2 on draft r3: RATIFY-WITH-CONDITIONS (`checks/charter-astra-r2.md`); the four-story list amended with estimates 3–4 / 4–5 / 3–4 / 1 days.
- 2026-09-24 — the owner ruled D1 (the whole Phase 3+4 loop), D2 (keep the thin proxy; retire standalone), D3 (Codex drives the closing use) and the proof mode (rehearsed, owner-reviewed shots).
- 2026-09-23 — Astra check r1 on the draft then numbered Phase 4: BOUNCE (`checks/charter-astra-r1.md`); paid across r2 and r3.
- 2026-09-23 — the owner: "things have to flow through services".

## Decisions deferred

- The Info-window rename of a decision (the face sends `name`; `decision.update` ignores it; `web/src/desk/components/InfoWindow.tsx:31`) — a real bug, fenced as observed in 01, not fixed there; parked in `pm/roadmap/holdspeak/BACKLOG.md` (PHILO-5-01 follow-ups).
- The owner's ratification of this charter.
- ~~The MCP import intake's client contract~~ — settled by Muad'Dib for story 02 and built (Decisions made, 2026-09-24); Astra checks on built.
- The decision admission (INHERITED DEBT, Article XI): whether a desk decision write "acts under Article V" (filing) is UNRULED. Assigned to the owner's ruling; if he rules it consequential, a later phase admits the desk writes through the kernel. Parked in `pm/roadmap/holdspeak/BACKLOG.md` (PHILO-5-02 follow-ups). `tests/unit/test_philo5_the_loop.py:618` is characterization only.
- Any stronger brief-freshness promise than a fresh/reopened Desk read (needs a named scope amendment).

## Discovered missing admissions

- 2026-09-24 (Astra's check on built, PHILO-5-01 finding 8): `decision.create` and `decision.update`, over HTTP and over MCP, run no kernel operation and write no receipt. A real Codex decision write made the row and ZERO kernel operations and ZERO receipts (Astra's `admission-proof.json`). Inherited Article XI debt, older than the contract. Named here for resolution in PHILO-5-02's effects acceptance; not fixed in 01, not certified.
  - 2026-09-24 (PHILO-5-02 round one) said "RESOLVED AS RECORDED, NOT ADMITTED"; Astra's check on built (finding 4) rejected the exemption claim. Round two: INHERITED DEBT (Article XI), NOT resolved — decision.create/update leave no kernel operation and no receipt through either transport; whether a desk decision write 'acts under Article V' (filing) is UNRULED; assigned to the owner's ruling / a later phase ("Decisions deferred"; BACKLOG "PHILO-5-02 follow-ups"). The test at `tests/unit/test_philo5_the_loop.py:618` is characterization only.
