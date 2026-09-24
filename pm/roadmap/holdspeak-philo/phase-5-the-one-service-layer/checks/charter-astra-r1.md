# Phase 5 charter check r1 — Astra (2026-09-23)

Astra (`gpt-6-astra`), `scripts/astra check`, run `.tmp/two-brains/20260923-190909-check/phase-4-charter-astra.md`, reviewed HEAD `46172fcf`. At the time the draft was numbered Phase 4; it became Phase 5 when The Morning took that number. Copied verbatim below.

---

VERDICT: BOUNCE

Revise before presenting this as the Phase 4 charter. A bounded shared-service pilot is justified. The draft misstates parts of the baseline, leaves the pilot's operation boundary unsettled, and asks the owner to choose implementation and proof rules that the two brains should resolve. Finish Phase 3 first, as instructed.

FINDINGS:

1. **The “verified” baseline needs correction before it becomes a ratchet.** Tenets 1 and 3: inaccurate counts will create work without proving consolidation. I read the draft itself and counted source at `46172fcf756397b2dc8c6e4dc83d0b0af27842f9`, without importing the product. These are source facts, not executed-behavior claims.

   | Draft row | Source check |
   |---|---|
   | Line 15: 113 service modules, all `Service(db, observer=)` | **113 Python files, including `__init__.py`; 112 excluding it. The universal constructor claim is false.** `AgentTurnService(foundation)` is at `holdspeak/services/agent_turn_service.py:53`; `PeopleService(store, setup_runner=)` at `holdspeak/services/people_service.py:72`; `SequenceWorkflowService(db, broker)` at `holdspeak/services/sequence_workflow_service.py:39`. No common transport-operation catalogue was found; that narrower claim is reasonable. |
   | Line 16: descriptor and one instance | **One production construction site confirmed**, `holdspeak/services/agent_turn_service.py:64`; declaration anchor `holdspeak/services/tool_capability_service.py:216` is correct. “One instance” should mean one declaration site, not a measured runtime object count. Its suitability needs qualification; see finding 3. |
   | Line 17: one composition root | **Confirmed as the intended shared application root**, `holdspeak/runtime/composition.py:205`, installed by `holdspeak/web_server.py:1133`. It does not currently guarantee one instance of every service; see finding 4. |
   | Line 18: 114 route modules | **111 Python files recursively; 105 excluding six `__init__.py` files.** Count files, not endpoints. |
   | Line 18: 46 bare-construction modules | **46 files contain 67 calls whose constructor name ends in `Service`.** This is a candidate census, not 46 demonstrated unlawful constructions. `holdspeak/web/routes/primitives/decisions.py:22` first returns the composed instance and constructs only for partial contexts; `holdspeak/web/routes/meetings/intel.py:22` supplies notification wiring. |
   | Line 18: 19 never use context | **Not reproduced as stated.** AST count: 15 files accept a `ctx` parameter and never load that name; 23 files never load `ctx` if files without such a parameter are included. Specify the population and matcher. Four files contain `del ctx`, including `holdspeak/web/routes/decisions.py:39`. |
   | Line 18: 61 `get_database()` calls | **60 direct AST calls.** The 61 literal text matches include the historical docstring at `holdspeak/web/routes/mcp_http.py:9`. There is additionally an indirect getter call at `holdspeak/web/routes/decisions.py:10`. A semantic census may count that, but must identify it rather than count a comment. |
   | Line 19: 225 tools / 61 branches / ~6.4k lines | **Confirmed:** 225 source-declared tool entries, 61 `if name ==` branches in `tools.py`, 6,430 lines across `tools.py` and all family Python files. The 225 includes the literal-loop expansions in `holdspeak/mcp/families/thought.py:136` and `:147`. “Four helpers” is not an exhaustive implementation count: there are ten tool-envelope helper definitions, across five names, including `_setup_proposal_tool` at `holdspeak/mcp/families/project.py:896`; Thought also has a separate argument-schema helper. Aggregation is at `holdspeak/mcp/tools.py:485`. |
   | Line 20: stdio is a proxy / one writer | **Correct for the default mode**, `holdspeak/mcp/server.py:176`, `:503`. Qualify the existing standalone diagnosis mode: it composes locally and claims the owner lock (`:459`, `:475`, `:487`). |
   | Line 21: about 20 kernel operations; routes/MCP do not go through it | **26 startup `OperationSpec` registrations**, `holdspeak/kernel/runtime.py:87`. The blanket bypass statement is false: HTTP directly calls `kernel.submit` at `holdspeak/web/routes/system/kernel_routes.py:35`; MCP sequence dispatch obtains the broker and calls the admitted execution service at `holdspeak/mcp/families/sequence.py:92`. Say there is no universal service-operation dispatcher; distinguish direct and service-mediated kernel paths. |
   | Line 22: shared middleware; stdio always OWNER | **Shared middleware confirmed**, `holdspeak/web_server.py:629`. Default stdio forwards the configured owner token and is authenticated by that middleware (`holdspeak/mcp/server.py:189`); missing credentials can be refused. `holdspeak/mcp/auth.py:27` describes local/standalone resolution, not the normal proxy's authentication path. |
   | Line 23: 419 UI / 52 API steps; no operation kind | **455 UI / 55 API steps across 74 atlas cases**, counting structured preconditions, setup and trigger. No `op` kind: confirmed at `scripts/graph_walk.py:2288` and `docs/internal/philo/graph/atlas.schema.json:197`. |
   | Line 24: council deferral | **Exact quote and line confirmed**, `docs/internal/philo/graph/COUNCIL.md:57`. It is a historical coverage statement, not proof those inputs have since been walked. |

   All relative code anchors in the draft's table also need their actual `holdspeak/` prefixes. Recount after Phase 3 lands and record that revision and the counting method.

2. **The draft turns an interpretation into the owner's ruling.** Tenets 2, 3 and 7. The quotation at `pm/roadmap/holdspeak-philo/PHASE-4-CHARTER-DRAFT.md:7` is an edited paraphrase of the supplied ruling. Label it as such. Line 9's assertion that the owner meant every transport to be a generic adapter is the author's proposed architecture, not established by the quoted sentence. State the proposal separately: a client command and its Desk equivalent use the same application behavior and leave the same durable result. Retaining a protocol proxy is compatible with this, but the owner has not thereby selected decorators, a new invocation interface, or a new public endpoint.

3. **Reuse the existing boundaries without turning either existing descriptor into a universal broker.** Tenets 1 and 3. PHILO-4-01/02 and D2 (`draft:43`, `:44`, `:63`) omit the distinction between application operations, model-tool capabilities and kernel effects.

   `CanonicalApplicationOperationDescriptor` deliberately serves a narrower model projection (`holdspeak/services/tool_capability_service.py:3`, `:219`). Its schema rejects empty properties/required lists and keywords such as `minLength` (`:101`, `:113`, `:129`); its allowed classes and call/result limits are model-specific (`:20`, `:262`). Yet the pilot includes argument-free brief reads/generation and Thought's `minimum`/`minLength` constraints (`holdspeak/mcp/families/thought.py:26`). It also binds a **string**, not a service method (`tool_capability_service.py:230`). Conversely, `OperationSpec` binds a kernel codec, capability and execution lifecycle (`holdspeak/kernel/model.py:51`), not an HTTP or MCP presentation.

   Settle one small application declaration and derive transport schemas from it; retain the narrower model projection and existing kernel specs in their roles. Include description, result/refusal shape, async completion/read identity, and intentional transport exposure. Do not infer that every declared method becomes an MCP tool. Preserve existing tool names and palettes (`holdspeak/mcp/tools.py:1045`). No general plugin/decorator framework is needed to prove this slice.

4. **The pilot has concrete composition defects to pay; another exception is not the answer.** Tenets 1 and 3. HTTP brief construction supplies `ctx.brief_clock` (`holdspeak/web/routes/monday_brief.py:97`), whereas MCP constructs `MondayBriefService(db, observer=obs)` (`holdspeak/mcp/tools.py:685`). The latter therefore uses the wall clock (`holdspeak/services/monday_brief_service.py:139`). Moving the rig's producer clock cannot currently establish next-day parity through MCP.

   MCP also constructs an unwired `MeetingIntelService` at `holdspeak/mcp/tools.py:879`, losing its queue notification callback (`holdspeak/services/meeting_intel_service.py:78`). HTTP's factory takes precedence over its stored instance (`holdspeak/web/routes/meetings/intel.py:17`), and the hub supplies that factory (`holdspeak/web_server.py:933`). Merely fixing MCP lookup will not meet the draft's literal same-instance exit criterion.

   **Open question 1:** no fourth lawful-bare-construction case. `composition.service()` returns an installed instance or calls `build()` without caching it (`holdspeak/runtime/composition.py:337`). Case 2 at `:318` expressly permits fresh instances; it cannot prove object identity. Compose each declared pilot service once per hub, including its clock/callbacks, and bind the routes and invoker to it. Keep partial-test/standalone behavior explicit. Identity is per live hub, not across a process restart; the rig must invoke the owning hub rather than compose a second writer in its own process.

5. **The promised loop exceeds the declared slice, and “one line each” conceals real adapter work.** Tenets 2, 3 and 7. Scope at `draft:36` omits import, while PHILO-4-04 and 06 promise import → summary → restart → decision → next-day brief. Import currently stages multipart bytes and passes configuration and a transcriber factory (`holdspeak/web/routes/meeting_import.py:52`, `:90`); no meeting-import tool appears among the 225 declarations. Restart is a rig process action, not a service operation (`scripts/graph_walk.py:2630`), and advancing a test clock is not the owner waiting until tomorrow.

   Name the exact pilot operations and existing route/tool mappings. Include import intake and completion, planned summary route/hash, one enqueue and terminal read, the correct decision create/read pair, brief latest/generate, and Thought create/update/read needed for its save receipt. Distinguish Desk decisions (`holdspeak/web/routes/primitives/decisions.py:42`) from lifecycle transitions (`holdspeak/web/routes/decisions.py:57`) and decision records (`holdspeak/mcp/tools.py:914`). Preserve file staging and protocol response mapping in transport adapters; move shared application orchestration to services. The brief already has differing transport projections (`holdspeak/web/routes/monday_brief.py:109`; `holdspeak/mcp/tools.py:963`). Require equivalent domain results, not identical envelopes or a line-count target. Define the producer's injectable clock once; never expose a production clock-changing operation merely to complete this proof.

6. **PHILO-4-04's parity rule can certify the wrong thing, and an `op` branch alone will not remove Chromium.** Tenets 1 and 3; Article IX. `draft:46` demands browser/op verdict equality while `:66` correctly says browser-only defects can pass over MCP. Those statements need reconciliation. Compare the shared persisted outcome, identity and refusal across transports. Keep a separate face verdict; a failed UI with a successful service must remain a visible disagreement, not be forced into parity. Require a nonempty list of actual paired atlas cases, not “for cases that have both” with no required pair.

   `run_case()` unconditionally starts Playwright (`scripts/graph_walk.py:3603`, `:3675`); even protocol snapshots evaluate the page (`:488`). Restart retention capture is skipped when `page is None` (`:2640`, `:2651`). The story therefore needs headless setup, observation, waiting and restart evidence, plus the atlas schema update. Preserve isolated HOME, real producer setup, one-trigger correlation and terminal reads. “In seconds” is an unmeasured target, not an exit guarantee for real transcription/inference.

   **Open question 3:** keep `api` steps for HTTP contracts and protocol observations; add/select `op` steps for shared application semantics and useful setup. Do not mechanically convert the 55 API steps. The rig already records HTTP status/body and captures IDs (`scripts/graph_walk.py:2558`); losing those would lose transport proof. Run the actual atlas cases, per `agent/skills/holdspeak-capability-verifier/SKILL.md:49` and `:112`.

7. **The ratchet and documentation transition are incomplete.** Tenets 1 and 3. PHILO-4-05 (`draft:47`) counts files, tool entries and one dispatch syntax. Removing one old violation can fund one new violation without increasing any total; another constructor in an already-counted file costs nothing; aliasing the constructor or moving dispatch to a dictionary evades the syntax metric. Also, the quoted 46 includes lawful fallbacks, while aliases such as `_MIS` demonstrate why name-only scans are insufficient (`holdspeak/mcp/tools.py:879`).

   Keep an explicit residual set with reasons; reject new residual identities and remove paid entries in the migration commit. For the pilot, prove actual route/MCP dispatch reaches the declared operation and composed dependency, preserves result/error behavior, and emits the expected notification. Ship the behavior fence and descriptor/docs updates with each migrated operation, not only in story 05 after all adapters land. Show each behavior fence fails on the old producer path; use deliberate mutations for newly introduced structural invariants that cannot exist on old main. An import error is not proof of a useful pre-fix failure (`draft:55`).

   **Open question 2:** retain `TOOLS` + `dispatch` as a compatibility/generated family interface for the slice; retain legacy families for unmigrated tools. The contract already routes by tool ownership and propagates owned failures (`holdspeak/mcp/families/__init__.py:3`; `holdspeak/mcp/tools.py:663`). Retire duplicate active definitions for migrated entries, not whole mixed families. Reject duplicate names. The complete roster must continue to cover generated **and** legacy tools: today's generator/guard reads the assembled catalogue (`scripts/gen_mcp_sidecar_doc.py:34`; `tests/unit/test_mcp_sidecar_doc_drift.py:41`). Replacing that with a pilot-only `operations.json` would silently drop most of the public roster. Keep a full exposed-roster check while proving each generated entry comes from the application declaration.

8. **Reduce the five owner decisions to choices that affect his work.** Tenets 1, 2, 3 and 7. My disposition of every decision at `draft:62`–`:66`:

   | Decision | Disposition |
   |---|---|
   | D1, pilot scope | Keep as the owner-facing scope choice, with the complete bounded loop and its cost. Recommend the Phase 3 jobs, including the owner-selected Thought work (`docs/internal/philo/graph/COUNCIL.md:50`). Do not call Phase 3 fully proven before it closes. |
   | D2, decorator versus module | Settle between the brains after the small contract review. It is not a useful prerequisite question for the owner's Tuesday. Either storage form can meet the same contract. |
   | D3, stdio proxy | Recommend retaining the existing thin proxy for his chosen client. Separate subprocess transport from duplicate service composition. Ask the owner only if retiring stdio removes an access path he wants; that retirement is unnecessary to this pilot. |
   | D4, kernel admission | Replace the false binary with: preserve existing service-owned admissions and receipts; map the pilot's consequential effects and fix an actual uncovered path if found. Do not wrap already-admitted effects again, and do not treat effect labels as permission to bypass admission. Article XI requires admission once (`docs/internal/CONSTITUTION.md:169`); Tenet 1 favors preserving the existing mechanism, not building another. A real canon exception must be named under Article X (`:158`). |
   | D5, operation-tier claims | Settle as proof discipline: service/state evidence only; kernel evidence only where actually observed; a face needs its browser evidence. This is already constrained by Article IX (`docs/internal/CONSTITUTION.md:148`), not an elective replacement for it. |

   PHILO-4-06 is a useful close if the owner gives a normal job request and sees the result arrive. It should not require him to learn operation names, assemble arguments, repair installation, or change test clocks. Keep technical completion separate from his usefulness verdict. Generated user-facing descriptions/refusals still owe Tenet 4's simple English; “no face change” does not waive the existing component/Workbench experience or 1440/393 regression evidence (Tenets 5 and 6).

CONDITIONS:

- Correct the baseline and attribution; pin the post-Phase-3 revision and explicit counting rules.
- Settle the bounded operation/mapping table, per-hub composition, transport projections, and existing kernel-admission relationships before implementation briefs. Include the import and terminal-read dependencies the promised loop needs.
- Integrate identity-based migration fences and complete generated-plus-legacy documentation with each conversion. Preserve compatibility and palette behavior.
- Define actual atlas pairs, headless observation/restart support, separate domain/transport/face verdicts, and real-engine versus replayed evidence. Retain both viewport walks for the existing faces.
- Present the owner with the next useful result, scope/cost and access-path recommendation. Keep implementation mechanics and non-negotiable evidence rules with the two brains.

MISSED:

Ranked by cost to the owner:

1. **Another phase can finish while his loop still needs hidden setup.** Import, terminal summary reads, restart ownership, next-day timing and Thought reopening must be explicit parts of the proof, with durable IDs linking the steps (findings 5–6).
2. **A successful tool reply can leave his open Desk stale or use the wrong day.** The notification and producer-clock wiring are concrete acceptance criteria, not future cleanup (finding 4).
3. **“One catalogue” can become a third definition and lose old clients during migration.** Preserve public names, intended exposure, result/refusal semantics, model projection boundaries and the complete roster (findings 3 and 7).
4. **A green aggregate can hide a new bypass or a broken face.** Residual identities and separate evidence axes are needed; more global count gates will not fix that (findings 6–7).

Counter-proposal for the story list:

| Story | Done means |
|---|---|
| 01 — One decision through one service contract | Settle the minimal operation/mapping design; compose and bind a decision create/read vertical slice through the existing route and generated MCP adapter. Prove real dispatch, persisted identity, refusal and Desk notification. Introduce its declaration export, compatibility guard and residual ledger in the same story. |
| 02 — The meeting, brief and Thought use that contract | Complete the enumerated pilot operations, including import custody/completion and summary route/result reads. Preserve the wired summary service, brief clock, Thought revision/save facts, existing admission paths and transport projections. Generate migrated tools; update fences and full roster with each conversion. |
| 03 — The real atlas proves the three paths | Add headless operation execution/observation in the existing rig, reaching the owning isolated hub. Prove terminal results, real restart retention and producer-day behavior on named actual atlas cases; retain API contract checks and independent 1440/393 face walks. Record real-engine and replayed proof separately. |
| 04 — The owner uses the loop | Rehearse the complete path in isolation, then let the owner request his job through his chosen MCP client and see the same objects on the Desk. Retain both brains' technical verdicts and his own usefulness verdict. |

This changes sequencing, not a promise to compress the work into four days. No separate generic framework or terminal ratchet project is needed before the first working vertical slice.

TUESDAY: Not established by this draft: the owner should request the meeting job and find its summary, decision, dated brief and saved Thought on the Desk; he should not have to operate the catalogue or the verification rig.

UNKNOWN:

- No product tests, hub, MCP client, browser walk, model call, or owner DB access was run. Counts come from read-only Python AST/JSON inspection, including literal-loop expansion for the 225 tool declarations; runtime import failures/degraded families were not evaluated. The constructor census is intentionally not claimed as a count of unlawful constructions.
- `python3 -B scripts/philo_graph_reference.py --check` exited 0: the generated join matches its inputs, with 14 reported subtype-conflict notes. This does not certify current runtime coverage or Phase 3 completion.
- I have not established actual timing, universal HTTP/MCP behavioral equivalence, or the owner's preferred replacement for the access path he called “sidecar.” Those remain explicit pilot/owner questions, not inferred facts.
- Check session: `01a0d0f5-93c7-7c93-b36b-7dedbaec83a0`. Reviewed HEAD: `46172fcf756397b2dc8c6e4dc83d0b0af27842f9`. Draft SHA-256: `393619e2d80d64e4383eb2e3313e90fab125426c7df3ff3ef36c311ad0a2e644`. Atlas SHA-256: `ff719b7af9787cc98b3953bc05eeff5e989d6917e9d7d347efe485834be7b1ec`.
- The report is the only authored file, under `.tmp/two-brains/`. The draft and all product, roadmap, and evidence files were left unchanged.
