# Phase 5 charter check r2 — Astra (2026-09-24)

Astra (`gpt-6-astra`), `scripts/astra check`, run `.tmp/two-brains/20260924-090337-check/last.md`, reviewed HEAD `3881301f` (draft r3). Copied verbatim below.

---

VERDICT: RATIFY-WITH-CONDITIONS

The direction and four-story structure stand. **r3 needs the charter changes below before workers are briefed.** D3 has a concrete rig-discovery defect, beyond the configuration question.

FINDINGS:

1. **The current graph rig cannot be discovered by the retained proxy.** **Tenets 2 and 3.**

   HOME isolation works: `DEFAULT_DB_PATH`, its owner lock, and `CONFIG_FILE` all resolve beneath the subprocess HOME. I verified this in a fresh temporary HOME using the actual imported constants and discovery function. Evidence: `holdspeak/db/core.py:47`, `holdspeak/config/core.py:35`, `holdspeak/mcp/server.py:102`.

   However, the rig calls `claim_database(database.db_path)` **without a port**, while `discover_hub()` rejects missing or nonpositive ports. The real lock producer reproduced:

   ```text
   held=True, owner_alive=True, published_port=None, proxy_discovery=None
   ```

   Evidence: `scripts/graph_walk.py:1494`, `holdspeak/mcp/server.py:119`.

   There is a second seam: the rig passes its token directly to `MeetingWebServer`; the proxy reads `meeting.web_auth_token` from the config file. The rig does not persist that matching token. Publishing the port alone therefore does not complete the connection. Evidence: `scripts/graph_walk.py:1517`, `holdspeak/mcp/server.py:144`, `holdspeak/web_server.py:322`.

   **Pay both seams in story 01:** publish the rig’s actual loopback endpoint through the existing lock producer and persist its matching token through the isolated configuration path. Prove discovery, authentication, one real decision write, and restart rediscovery through the proxy.

2. **Codex can express the required configuration; `scripts/astra --cd` alone does not establish isolation.** **Tenets 1 and 3.**

   The wrapper forwards `-C`, but accepts neither arbitrary Codex configuration overrides nor a profile option: `scripts/astra:20`, `scripts/astra:50`.

   Codex supports project MCP configuration, server-specific `env`, and `cwd`; project configuration depends on trust. [Official MCP configuration](https://learn.chatgpt.com/docs/extend/mcp?surface=cli), [configuration precedence](https://learn.chatgpt.com/docs/config-file/config-basic).

   The concrete configuration must bind:

   - The **lane’s executable and working directory**, using absolute paths.
   - The proxy’s `HOME` to the **same isolated HOME as the hub**, before Python imports its path constants.
   - Proxy mode, with no standalone composition.
   - The default database location beneath that HOME. Merely starting a hub with an arbitrary custom database path does not redirect `serve()` discovery.

   Keep Codex’s authentication/session environment separate from HoldSpeak’s data HOME.

   Local `codex-cli 0.155.1` accepted explicit `-c mcp_servers.…` overrides, including the server HOME. A configuration-only `codex mcp get` probe did **not** discover a temporary project-config server; that is not proof that `codex exec` ignores project configuration. It means activation remains unverified. My position: give the wrapper a narrow repeated `-c` passthrough and prove the effective lane configuration in a **fresh Codex session during story 01**, rather than discovering this at closure.

3. **§6 still misidentifies the decision operation and omits operations required by the actual loop.** **Tenets 2, 3 and 7.**

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

4. **The composition gaps extend beyond A and B.** **Tenets 1 and 3.**

   A and B remain valid: MCP constructs a clockless brief service and an unwired summary service at `holdspeak/mcp/tools.py:685` and `holdspeak/mcp/tools.py:879`.

   Add these:

   - HTTP summary `_svc()` prefers the factory over the already-composed instance. The hub supplies both, so fixing MCP alone does not establish shared object identity: `holdspeak/web/routes/meetings/intel.py:16`, `holdspeak/web_server.py:932`.
   - MCP resource reads independently construct brief, meeting and Thought services. Thought workbench reads also obtain their coordinator through the standalone-family runtime rather than the hub’s application service: `holdspeak/mcp/resources.py:504`, `holdspeak/mcp/resources.py:523`, `holdspeak/mcp/resources.py:566`.
   - Import additionally carries configuration, transcriber construction and temporary-file custody. Those are real dependencies, not a generic JSON call: `holdspeak/web/routes/meeting_import.py:90`.
   - The notification fence must name the actual event. Summary service notification is `runtime_queue`; requiring `desk_changed` for every successful operation would be a false fence: `holdspeak/services/meeting_intel_service.py:78`.

   Brief freshness needs an explicit limit. Arrival reads the brief on mount; its own Generate and shelf handlers update local state. Its `desk_changed` subscription refreshes assignments, not the brief: `web/src/desk/chair/ChairHome.tsx:523`, `web/src/desk/chair/ChairHome.tsx:634`, `web/src/desk/chair/ChairHome.tsx:917`. Shared services alone therefore do not prove an already-open brief updates after an MCP write.

5. **D1 requires preserving the Phase 4 semantics, not merely its operation names.** **Tenets 3–7.**

   Charter these as explicit acceptance criteria:

   - Generate remains reachable in every ratified state; pending, failure and success receipts survive the rendered transition.
   - Decision rows lead; recency comes from persisted `created_at`, survives reload, and respects the existing three-row cap.
   - One source failure appearing in two briefs produces distinct brief-scoped item IDs, while old rows and shelf state remain unchanged.
   - `ALL n HANDLED` counts the nonempty Arrival item set with valid Ack/Defer states, excludes THIS WEEK, and cannot appear while a hidden raw-ID row remains unhandled.

   Evidence: `web/src/desk/chair/ChairHome.tsx:716`, `holdspeak/services/monday_brief_service.py:394`, `holdspeak/services/monday_brief_service.py:556`, `web/src/desk/chair/ChairHome.tsx:883`.

   I inspected the retained `pm/roadmap/holdspeak-philo/phase-4-the-morning/assets/story-02-shots/20260924T072614Z-case.closure.chain.s5_next_day_brief_has_it-astra-1440/after.png` and `pm/roadmap/holdspeak-philo/phase-4-the-morning/assets/story-02-shots/20260924T072514Z-case.closure.chain.s5_next_day_brief_has_it-astra-393/after.png`: the new decision is visible. These are retained Phase 4 evidence, not Phase 5 proof.

6. **The residual fence needs finer identities than tool names.** **Tenets 1 and 3.**

   `desk.create/get/update/list` serve several primitive kinds. Migrating decisions cannot retire those entire public tools without breaking unrelated capabilities. Retire the duplicated **decision path**, keeping the generic compatibility entry for its remaining kinds.

   Use identities such as `(transport, entry point, discriminator)` where necessary. Generated aliases must reach the same declaration; paid application branches disappear in that commit. Newly exposed import/shelf operations may increase the public tool count while the residual implementation set shrinks. Those are different measurements. Evidence: `holdspeak/mcp/tools.py:554`, `holdspeak/mcp/tools.py:689`.

   Preserve names, arguments, defaults, envelopes, refusal behavior and palette membership. Test palette refusal through dispatch as well as catalogue filtering: `holdspeak/mcp/tools.py:1045`.

7. **The baseline and closing language still need reconciliation.** **Tenets 1–3; Article IX.**

   Reviewed HEAD is `3881301f`; its only change from requested `4b4f8d94` is the draft.

   Recount confirms 113 service Python files; 111 route Python files, 105 excluding package initializers; 67 syntactic `*Service(...)` constructions across 46 files; 15 files accepting but never loading `ctx`; 60 direct `get_database()` calls; 225 assembled unique tools; 61 `if name ==` branches in `tools.py`; and 6,430 lines across `tools.py` plus family Python files. These are census facts, not violation counts.

   The atlas count is incomplete for D1: `atlas.json` contains 74 cases, 455 UI and 55 API steps; `atlas-phase3.json` adds **16 cases, 251 UI and 34 API steps**. Count both named files, excluding archived variants.

   Finally, §3 still says the owner has not ruled and Phase 3 must close first; §4 names only Phase 3; story 04 and exit criterion 5 still require a live sitting. These contradict §9’s explicit ruling. Evidence: `pm/roadmap/holdspeak-philo/PHASE-5-CHARTER-DRAFT.md:3`, `pm/roadmap/holdspeak-philo/PHASE-5-CHARTER-DRAFT.md:61`, `pm/roadmap/holdspeak-philo/PHASE-5-CHARTER-DRAFT.md:71`.

CONDITIONS:

**Pay §12’s decisions in the charter; pay their implementation and proof in the stories.**

| Carried condition | Required before briefing | Implementation payment |
|---|---|---|
| Revision/counting basis | Pin `4b4f8d94`; state populations and counting rules, including both atlases | Story 01 creates the identity-based baseline/fence |
| Exact transport mapping | Replace §6 with the corrected inventory, including resources, decision update and shelf operations | 01 proves decisions; 02 completes the remainder |
| Named atlas pairs | Name the cases and expected equivalence now | 03 creates and executes their operation siblings |
| Compatibility/palettes | State preservation rules and treatment of generic-tool branches | Guards ship with every conversion, beginning in 01 |
| Real/replayed evidence | Separate acceptance and provenance now | 03/04 retain separate runs and outcomes |
| Codex isolation | Name HOME, endpoint-lock, token, executable and wrapper seams; assign ownership | **01 proves an actual Codex/proxy/hub call and restart** |

**Named atlas coverage to record now:** retain the existing cases below and mint explicitly named `.op` siblings. Those siblings do not exist yet.

- `case.closure.chain.s1_import_complete`, `s2_summary_with_host`, `s3_same_summary_after_restart`, `s4_decision_recorded`.
- `case.a1.decision_face_create.opens_and_reopens`, including its named invalid-status refusal.
- `case.a3.brief_next_day.decision_on_the_face` paired with existing API case `case.a3.brief_next_day.new_id_with_the_decision`.
- `case.closure.chain.s5_next_day_brief_has_it` and its separate `s5_next_day_brief_with_breakage` variant.
- `case.philo404.arrival_triaged_headline.all_handled`, paired with the shelf operations.
- `case.j11.thought_keep.receipt_time`, paired with durable saved-body/revision/time assertions.
- From `atlas.json`: summary no-transcript/no-assignment refusals; same-day brief identity; shelf acknowledged/deferred/refused cases.

Evidence anchors: `docs/internal/philo/graph/atlas-phase3.json:454`, `docs/internal/philo/graph/atlas-phase3.json:926`, `docs/internal/philo/graph/atlas-phase3.json:1772`, `docs/internal/philo/graph/atlas-phase3.json:3129`.

**Between-brain settlement — my position for the charter record:**

- **Declaration:** a small explicit descriptor module, bound to actual callables at hub composition. No general decorator/plugin framework. Permit empty argument objects; describe result, refusal and asynchronous completion/read identity. Keep the existing model-tool descriptor and kernel `OperationSpec` in their narrower roles.
- **Composition:** eagerly bind the pilot’s existing services once per hub, including the clock-bearing brief service. Reuse the existing composition root; do not change global fallback caching to solve this slice. Compare object identity within a hub; compare durable state across restart.
- **Effects:** transports derive the principal; arguments cannot supply authority. Preserve existing service-owned admissions and terminal receipts, without double admission or descriptor-label exemptions. Any discovered missing admission is named for resolution, not silently certified.
- **Transport:** preserve multipart/file custody, HTTP response mapping, MCP envelopes and resource URIs. Settle the MCP import intake before its worker brief; a raw service `tmp_path`, configuration object or transcriber factory is not a client contract.
- **Proof:** `op` reaches the registry inside the owning isolated hub. Setup, waiting, observation and restart must work without a page; currently snapshots call `page.evaluate`, and restart retention is skipped without a page: `scripts/graph_walk.py:523`, `scripts/graph_walk.py:2715`. Preserve API checks and independent rendered 1440/393 checks. Compare domain outcomes and identity relationships across transports, not identical protocol envelopes or independently generated model text.
- **Closing proof:** record **“rehearsed, owner-reviewed shots.”** Preserve existing summary delivery without manual refresh. For the brief, explicitly accept a fresh/reopened Desk read within this phase’s no-face-change scope; do not claim already-open brief refresh. A stronger freshness promise requires a named scope amendment.
- **Fences:** real producers for behavioral red/green evidence; deliberate mutations for new structural invariants. Import failure or an unavailable new symbol is not the required pre-fix red.

These are my positions; Muad’Dib should record acceptance or dissent, not label unresolved items jointly settled.

**Keep four stories, with these amendments and planning estimates:**

| Story | Amendment | Engineering effort |
|---|---|---:|
| 01 | Decision create/update/read/list; contract/export/compatibility/residual guards; retire production standalone entry and update its docs/tests; prove Codex isolation and proxy discovery/authentication | 3–4 days |
| 02 | Complete the corrected inventory, including resource bindings, import intake, shelf operations and all Phase 4 invariants | 4–5 days |
| 03 | Headless setup/observation/restart and named actual-atlas equivalence; separate real/replayed and browser evidence | 3–4 days |
| 04 | Astra drives the normal-language job through Codex; retains MCP transcript and Desk shots; Muad’Dib checks; owner reviews shots | 1 day |

That is **11–14 engineering days**, provisional until story 01 proves the integration. The stated dependency chain is sequential; do not describe the sum as parallel elapsed time. Owner availability is no longer a live-sitting dependency.

MISSED:

1. **Highest owner cost:** a supposedly isolated Codex rehearsal that cannot find or authenticate to its rig—or reaches the real desk because only `--cd` was changed.
2. **A false completed loop:** missing decision update, Thought save/read distinctions, and durable shelf operations.
3. **A consolidation that leaves duplicate read compositions:** MCP resources and the HTTP summary factory.
4. **A migration that breaks other jobs:** removing generic `desk.*` tools or changing palette behavior to retire one discriminator branch.
5. **Inflated proof:** old atlas counts, a replay presented as real-engine evidence, or reviewed screenshots presented as an observed owner sitting.

TUESDAY: The retained Phase 4 shots show the decision where he can see it; Phase 5 should let him request the job in ordinary words and find those same objects, but Codex-driven completion is not proved yet.

UNKNOWN:

- No complete Codex → stdio proxy → isolated hub loop was run in this read-only check.
- No suites or new atlas walks were run. The path, catalogue, configuration-parser and real-lock probes described above were executed in temporary locations.
- Retained Phase 4 shots carry their original revision and dirty-state provenance; they are not fresh verification of `4b4f8d94`.
- Current real-engine availability and the owner’s future usefulness judgment remain unverified.
- The repository tree was unchanged; the three pre-existing untracked files remain untouched.