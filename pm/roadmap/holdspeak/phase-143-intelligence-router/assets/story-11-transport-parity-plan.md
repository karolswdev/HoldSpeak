# HS-143-11 — HTTP, MCP, sync, and compatibility plan

**Planning baseline:** `feat/hs143-13-assignments` at the just-closed Story 13 tree. This is a source-read-only planning artifact; it does not open Story 11.

## Residual scope after the Story-12/13 fold-ins

Story 12 accepted and shipped the narrow owner-only Model Library HTTP seam, while explicitly retaining MCP twins, reciprocal parity, sync hostility, and compatibility inventory for Story 11 (`assets/story-12-model-library-plan.md:108-128`). Story 13 did the same for the five owner assignment HTTP endpoints (`assets/story-13-assignments-plan.md:56-68`, `:124-147`). Therefore HS-143-11 **does not reimplement, rename, or add UI to either HTTP glass**. Its residual is: give the twelve shipped owner HTTP operations closed MCP twins over the same application services; prove reciprocal transport truth; make the router's already hub-local state hostile to sync in production-object proofs; and delete/refuse the remaining direct-target and compatibility side doors.

The original charter's broad “library, profiles/bindings, registry, assignments, previews, and route receipts” wording (`story-11-http-mcp-sync-compatibility.md:15-28`) is now narrowed by those accepted fold-ins. Registry HTTP/resource parity already exists outside this work; no new unshipped route-receipt HTTP resource is invented merely to satisfy that older wording. The acceptance laws that remain binding are reciprocal fixtures, recursive closure/replay/changed-payload refusal, denial before discovery, hostile-sync inertness, and no private material in ordinary transport (`story-11-http-mcp-sync-compatibility.md:22-34`; `assets/architecture-contract.md:404-427`, `:547-585`).

## 1. Obligation register

| Residual obligation | Slice | Production proof |
| --- | --- | --- |
| One owner-facing service truth through HTTP and MCP, with matching logical result inside each transport envelope. | S1–S2 | Fresh, identically seeded production DBs drive the HTTP router and MCP JSON-RPC `tools/call`; normalized `{outcome, body}` goldens match for all twelve seam operations. HTTP routes already delegate to `ModelLibraryApplicationService` (`holdspeak/web/routes/model_library.py:72-169`) and `InferenceAssignmentService` (`holdspeak/web/routes/inference_assignments.py:51-104`), so twins must call those same methods, not their repositories. |
| Recursive schemas, owner-before-body, stable command replay, changed-payload conflict, and narrow assignment CAS remain identical. | S2 | Unknown nested key vectors refuse without echo; `None`, AGENT, and MODEL_TURN are denied before body decoding on both direct service/MCP protocol paths; set/clear replay equals the first result and reused command ID + changed payload refuses. The existing HTTP proof is the model to extend (`tests/unit/test_web_inference_assignment_routes.py:40-143`); MCP envelopes convert `ServiceError` to `isError` (`holdspeak/mcp/server.py:89-110`). |
| The Hub never imports or exports v2 profiles/bindings/assignments/routes/readiness/acquisition/probe/invocation, and a hostile payload cannot cause physical work. | S3 | Push poisoned router buckets into a real populated local DB, assert `sync_hub_local_bucket_forbidden`, byte/count identity of router tables and config, no observer/provider/probe/acquisition/resume/invoke call, and absent buckets on pull. The deny list is source truth (`holdspeak/services/sync_service.py:63-108`) and it refuses before merge work (`:1225-1251`). |
| Remove mutable target vocabulary and raw lower-layer MCP mutation paths after router cutover. | S4 | The MCP catalogue no longer advertises the retired families/fields; a direct stale call receives the selected terminal result; exercises of every retained neighbour show no profile/target write, resolver read, or routing change. This is named cross-cutting work, not a late sweep surprise. |
| Keep manifests, owner/capability/routing census, and MCP inventory honest only after the implementation and focused proof pass. | S5 and the final step of every source-changing slice | Regenerate `docs/api-surface.json`/`docs/API_SURFACE.md` from the live app (`scripts/gen_api_surface.py:2,32,203-218`), update the MCP sidecar inventory (`docs/MCP_SIDECAR.md:4,84-95,162-180`), then rerun the exact guard tests. The routing census is exact/fail-closed (`tests/unit/test_phase143_routing_authority_census.py:19-40,300-311`). |

## 2. Inventory

### A. Shipped HTTP seams requiring an MCP twin — 12 operations

The following is the entire HTTP-to-MCP parity set on this branch. Each proposed twin is an owner-only MCP tool with a recursively closed `inputSchema`; it calls the listed existing application method through composition, never the old profile or target services.

| HTTP seam and source | Shared application method | Proposed MCP twin | Disposition |
| --- | --- | --- | --- |
| `GET /api/inference/model-library`, `holdspeak/web/routes/model_library.py:72-80` | `ModelLibraryApplicationService.get_library`, `holdspeak/services/model_library_service.py:93-107` | `model_library.get` | TWIN |
| `POST …/download`, `model_library.py:82-89` | `ModelLibraryApplicationService.download`, `model_library_service.py:109-128` | `model_library.download` | TWIN |
| `POST …/add-to-library`, `model_library.py:91-98` | `ModelLibraryApplicationService.add_to_library`, `model_library_service.py:130-141` | `model_library.add_to_library` | TWIN |
| `POST …/connect-hosted-model`, `model_library.py:100-110` | `ModelLibraryApplicationService.connect_hosted_model`, `model_library_service.py:158-167` | `model_library.connect_hosted_model` | TWIN; retain the write-only secret envelope and sentinel tests. |
| `POST …/define-endpoint`, `model_library.py:112-122` | `ModelLibraryApplicationService.define_endpoint`, `model_library_service.py:169-173` | `model_library.define_endpoint` | TWIN; same write-only secret rule. |
| `POST …/connect-paired-device`, `model_library.py:124-134` | `ModelLibraryApplicationService.connect_paired_device`, `model_library_service.py:175-176` | `model_library.connect_paired_device` | TWIN |
| `POST …/use-model-file`, `model_library.py:136-169` | `ModelLibraryApplicationService.use_model_file`, `model_library_service.py:143-156` | `model_library.use_model_file` | TWIN with a bounded base64-byte command decoded only into server-owned staging; never accept a client path. See ORCH-CALL 2. |
| `GET /api/inference/assignments`, `holdspeak/web/routes/inference_assignments.py:51-59` | `InferenceAssignmentService.assignment_summary`, `holdspeak/services/inference_assignment_service.py:149-243` | `inference_assignment.summary` | TWIN |
| `POST …/editor`, `inference_assignments.py:61-68` | `InferenceAssignmentService.assignment_editor_projection`, `inference_assignment_service.py:272-380` | `inference_assignment.editor` | TWIN |
| `POST …/set`, `inference_assignments.py:70-77` | `InferenceAssignmentService.set_assignment`, `inference_assignment_service.py:382-520` | `inference_assignment.set` | TWIN |
| `POST …/preview-use-default`, `inference_assignments.py:79-95` | `InferenceAssignmentService.preview_use_default`, `inference_assignment_service.py:522-555` | `inference_assignment.preview_use_default` | TWIN |
| `POST …/clear`, `inference_assignments.py:97-104` | `InferenceAssignmentService.clear_assignment`, `inference_assignment_service.py:557-…` | `inference_assignment.clear` | TWIN |

The API manifest already contains all twelve endpoints (`docs/API_SURFACE.md:367-371,489-495`); its generated consumer labels are not an authority exemption.

### B. Stale or retired-shape MCP inventory

| Existing MCP surface — source | Why it is stale / consumer census | Disposition |
| --- | --- | --- |
| `inference.download_and_use` and `inference.use_existing_model`, schema/dispatch `holdspeak/mcp/families/inference.py:23-34,46-57,71-81` | They advertise “use” and `expected_route_revision`, while Story 12 replaced them with availability-only library commands. Repository consumer census finds only their declaration/dispatch, legacy setup HTTP aliases, and focused legacy tests; no web caller remains (`holdspeak/web/routes/setup.py:163-195`; `tests/unit/test_inference_model_acquisition.py:168-485`). | RETIRE after S1 substitutes `model_library.download` / `.add_to_library`; retain the acquisition *implementation* behind Library, not its retired public names. |
| `inference.cancel_model_acquisition`, `families/inference.py:36-44,73-78` | It is an acquisition lifecycle operation, not direct routing; no current Library HTTP peer exists. | KEEP, but rehome/narrow its description under `model_library.cancel_acquisition` only if the existing Library projection exposes the matching job command; otherwise leave it explicitly non-parity and test that it cannot mutate assignments. |
| `destination.list/get/create/update/delete`, schema `holdspeak/mcp/tools.py:322-349`, dispatch `:691-702` | Direct `ProfileService`/inference-target CRUD is retired mutable destination authority. It can bypass the HTTP router’s private-library guard: HTTP hides `library_provider_*` at `holdspeak/web/routes/primitives/profiles.py:44-50`, whereas the MCP dispatch calls the service directly. | RETIRE; model availability changes enter only through the seven library twins. |
| `model_profile.list/get/create/bind/probe/unbind/delete`, schema `tools.py:350-375`, dispatch `:703-725` | Raw revision/binding/probe bodies expose a lower application layer rather than the owner Models service. Existing tests prove their old parity and closed schemas (`tests/unit/test_model_profile_authority.py:690-750`), which become deletion/update work rather than an excuse to retain the side door. | RETIRE from the owner MCP catalogue; do not replace with raw profile/binding tools. |
| `ask.models`, `families/ask.py:10-19,116-120` | Its “available inference destinations” vocabulary is an old target selector. | UPDATE to an assignment-safe projection or RETIRE if no consumer requires it; it must not enumerate/select a mutable destination. |
| `ask.run.inference_target_id`, `families/ask.py:38-60,127-145` | `AskService` already refuses it after assignment migration with `inference_legacy_selector_retired` (`holdspeak/services/ask_service.py:209-215`), but the MCP schema still advertises and forwards it. | UPDATE: remove field and forwarding; exact stale field must now fail schema validation. |
| `sequence.run` / `sequence.workflow` target overrides, `holdspeak/mcp/families/sequence.py:20,50,99-100,133-134` | They still offer `inference_target_id`; their service treats target/placement as a retired selector (`holdspeak/services/sequence_workflow_service.py:275-…`). | UPDATE: remove field and forwarding; add the family’s focussed neighbour tests. |
| `recipe.run` / `recipe.chat` option forwarding, `holdspeak/mcp/tools.py:649-655` | Still forwards `inference_target_id` / `requested_placement`; `RecipeService` already refuses those selectors (`holdspeak/services/recipe_service.py:93-97,144-147`). | UPDATE: delete only retired option keys; retain content/egress options that are not routing authority. |
| `workbench.create/update` free-form `fields`, `holdspeak/mcp/tools.py:262-263,629-632` | Description explicitly offers `profile_id`; the service calls the post-cutover compatibility write-through at `holdspeak/services/workbench_service.py:55-78,89-149`. | UPDATE and then RETIRE the write-through: closed allowed fields must reject `profile_id`/`resolver_profile_id`; named transport tests cover create, update, template and schedule neighbours. |
| `settings.update` description, `holdspeak/mcp/families/settings.py:30-36` | It describes config `intel_profile_id` as an assignment, contrary to router ownership. | UPDATE copy/schema so Settings cannot promise a routing mutation. |
| Legacy MCP resources for destinations/model profiles, `holdspeak/mcp/resources.py:154-171,190-201,457-501` | Discovery of the old surfaces bypasses the new owner vocabulary even if mutation tools go away. Capability resource is separate and already canonical. | RETIRE target/profile resources and templates with their tool family; KEEP capability registry resource. |

### C. Sync inventory and required hostile proofs

* The old v1 `profiles` bucket remains syncable and path-bearing (`holdspeak/services/sync_service.py:48,122-123`); the routing census deliberately calls this named Story-11 blocker (`tests/unit/test_phase143_routing_authority_census.py:384-392`). This story must not silently treat it as a v2 binding. Preserve historical v1 only where existing receipt-resolution law requires it, while proving it cannot mint v2 state.
* Router-owned v2 tables are excluded from `SYNC_REGISTRY` and explicitly forbidden: profile revisions/bindings/tombstones/readiness (`sync_service.py:63-74`), assignments and command/migration state (`:74-78`), route/operation/attempt/receipt state (`:79-103`), and acquisition/readiness/probe/invocation (`:104-108`). Push rejects before record validation/merge (`:1225-1251`) and pull enumerates only the registry (`:1206-1223`).
* Existing starting proofs are too narrow for the charter: profile/binding attack and pull omission (`tests/unit/test_model_profile_authority.py:753-773`) and assignment attack/pull omission (`tests/unit/test_phase143_inference_assignments.py:511-528`). S3 extends them with a single hostile compound payload and production spies/real table snapshots for **bind, assign, download, probe, resume, and invoke**.

### D. Compatibility cleanup ledger and consumer census

| Ledger item | Current site and consumers | Required cleanup / proof |
| --- | --- | --- |
| Dead browser `profile_id` map key | `web/src/desk/store/dataSlice.ts:297`; Story 13 audit explicitly named it (`evidence-story-13.md:139-155`). | Delete it and update the data-slice/wire guard tests. It is source cleanup only, not glass work. |
| Workbench compatibility write-through | `holdspeak/services/workbench_service.py:55-78`; invoked from create/update at `:100,111,133,149` and template application at `:367-373`. MCP `workbench.create/update` is still a reachable generic-fields consumer (`holdspeak/mcp/tools.py:262-263,629-632`). | Replace write-through with a typed retired-pointer refusal after migration; close MCP schemas/dispatcher first; test every named caller does not create/clear an assignment as a side effect. |
| Recipe compatibility write-through | `holdspeak/services/recipe_service.py:68-83,229-264`; route-level/MCP generic mutation callers must be searched before removal, while run/chat target overrides are already refused (`:93-97,144-147`). | Replace post-marker write-through with typed refusal; preserve only a one-time established migration reader if it remains required by the migration marker, never a new mutation side door. Test create/update plus recipe-run/chat neighbours. |
| Story-12 `download-and-use` / `use-existing` aliases | Service `holdspeak/services/inference_acquisition_service.py:162`; legacy HTTP `holdspeak/web/routes/setup.py:163-195`; MCP family `holdspeak/mcp/families/inference.py:23-81`. A repository-wide consumer scan finds no web call site, only declarations and focussed legacy tests. The aliases also alone append the obsolete `setup`/route-settings projection to their receipt (`inference_acquisition_service.py:619-626`), so their transport body differs from the canonical Library command. | Retire the HTTP aliases and MCP names in the same slice, replace tests with Library twin proofs, and assert their obsolete `setup` response cannot survive under another name; regenerate API/MCP inventories last. |
| Receipt-unforgeability note | Story-13 audit records “receipts could echo the committed chain” (`evidence-story-13.md:151-153`). Current `set_assignment` already records canonical `committed_effect` (`holdspeak/services/inference_assignment_service.py:501-515`), whose material includes the ordered entries (`:435-444`; helper `:2230-2231,2324-2329`). | Close this as an implemented-but-untested property: add golden assertions that first response and replay carry the same committed chain/hash, distinct from fresh current projection, without private binding/path/secret material. |

## 3. Ordered slices

**Universal command rule:** every command below uses an isolated `HOME`, including generators and the MCP walk. Capture stdout/stderr, read it before advancing, and remove the throwaway home after evidence capture. No UI implementation or screenshot leg belongs to this story.

### S1 — Compose closed MCP twins over owner services

Add the twelve tools in the existing MCP family idiom (`holdspeak/mcp/families/inference.py:11-81`; family-first dispatch at `holdspeak/mcp/tools.py:581-592`) and compose real `ModelLibraryApplicationService` / `InferenceAssignmentService` with the same process foundation used by web composition (`holdspeak/web_server.py:711-724,839-840`). Define versioned, recursively closed request DTO schemas. Provider secrets remain write-only and must never occur in tool results, errors, logs, or receipts; the browser file multipart seam’s equivalent MCP body is bounded base64 bytes decoded into hub-owned staging only.

**Focused command:**
```bash
HOME_REAL="$HOME" HOME="$(mktemp -d)" uv run --python 3.13.11 pytest -q \
  tests/unit/test_web_model_library_routes.py \
  tests/unit/test_web_inference_assignment_routes.py \
  tests/unit/test_model_profile_authority.py \
  tests/unit/test_inference_model_acquisition.py --tb=short
```

**Last step:** regenerate/review only affected MCP catalogue/docs anchors after the focused test output is read; do not alter an inventory first to make a test pass.

### S2 — Reciprocal HTTP↔MCP golden harness and transport safety

Add `tests/unit/test_phase143_transport_parity.py` using the existing real protocol idioms: FastAPI `TestClient`, `mcp_server.handle_message`, and `mcp_tools.dispatch` (`tests/unit/test_mcp_tools.py:34-45,79-101`; `tests/unit/test_model_profile_authority.py:690-750`). Seed each side through real profile/binding/assignment setup, not mocks. Compare a normalizer that retains HTTP status/MCP `isError` as envelope facts and canonicalizes only volatile IDs/timestamps in otherwise identical domain bodies. Cover each of the twelve rows, nested unknowns, owner/None/AGENT/MODEL_TURN denial before body discovery, secret sentinels, set/clear replay, changed request-ID conflict, narrow stale CAS, and the committed-effect replay assertion.

**Focused command:**
```bash
HOME_REAL="$HOME" HOME="$(mktemp -d)" uv run --python 3.13.11 pytest -q \
  tests/unit/test_phase143_transport_parity.py \
  tests/unit/test_web_model_library_routes.py \
  tests/unit/test_web_inference_assignment_routes.py \
  tests/unit/test_model_profile_authority.py \
  tests/unit/test_mcp_tools.py --tb=short
```

**Last step:** regenerate/review the MCP tool documentation/count and only the API manifest if a legacy HTTP surface changed in this slice; rerun their exact test/command after generation.

### S3 — Hub-local sync hostility, with physical-work inertness

Keep the existing explicit router deny set as the single source rather than adding active-route sync. Build a production-object hostile compound payload with every forbidden category and a local DB already holding a ready binding and assignment. Spy at the actual probe/acquisition/runner/resume entrances while using real `SyncService.push`; assert refusal occurs before every spy, config/router table snapshots remain byte/count-identical, and `pull` omits every v2 router bucket. Add a v1 profile payload control that proves it cannot create a v2 binding/assignment or physical action.

**Focused command:**
```bash
HOME_REAL="$HOME" HOME="$(mktemp -d)" uv run --python 3.13.11 pytest -q \
  tests/unit/test_model_profile_authority.py \
  tests/unit/test_phase143_inference_assignments.py \
  tests/unit/test_phase143_inference_route_plans.py \
  tests/unit/test_phase143_inference_fallback_controller.py --tb=short
```

**Last step:** regenerate/review the routing-authority census only after all hostility vectors are passing, then rerun `tests/unit/test_phase143_routing_authority_census.py` under isolated HOME.

### S4 — Retire target-shaped MCP and compatibility side doors

Perform the inventory dispositions as one named cross-cutting slice: remove old acquisition aliases, direct destination/profile tools/resources, and advertised per-request target fields; close Workbench/Recipe compatibility write-throughs and the dead data-slice key; update Settings wording. Put retirement assertions beside each affected family and run every neighbour suite named in the inventory, including direct protocol calls and generic Workbench/Recipe mutations. A stale MCP call follows the chosen ORCH-CALL policy and must never reach a service, DB write, resolver, probe, acquisition, or invocation.

**Focused command:**
```bash
HOME_REAL="$HOME" HOME="$(mktemp -d)" uv run --python 3.13.11 pytest -q \
  tests/unit/test_mcp_tools.py \
  tests/unit/test_mcp_phase133.py \
  tests/unit/test_model_profile_authority.py \
  tests/unit/test_inference_model_acquisition.py \
  tests/unit/test_recipe_precedence.py \
  tests/unit/test_recipe_runner_migration.py \
  tests/unit/test_workbench_runner_migration.py \
  tests/unit/test_phase143_subject_pointer_migration.py \
  tests/unit/test_phase143_surface_fallback_census.py \
  tests/unit/test_phase143_routing_authority_census.py --tb=short
```

**Last step:** run the repository consumer census for every retired name, update/remove its tests/docs only after it returns no production consumer, then regenerate API/MCP/census artifacts and rerun each corresponding guard.

### S5 — Final transport/census closeout

Run the full parity + hostility + retirement focused set as one isolated-HOME command, then the isolated-HOME fast full suite from `CLAUDE.md` with `-n auto` and `--ignore=tests/e2e/test_metal.py`. Read captured output before evidence. Regenerate in this final order: API manifest, MCP sidecar inventory/walk expectation, routing-authority census, capability census only if a capability-facing resource changed. Review diffs to ensure an absent tool/route is removed rather than reclassified as an exception.

**Focused closeout command:**
```bash
HOME_REAL="$HOME" HOME="$(mktemp -d)" uv run --python 3.13.11 pytest -q \
  tests/unit/test_phase143_transport_parity.py \
  tests/unit/test_mcp_tools.py \
  tests/unit/test_api_surface.py \
  tests/unit/test_phase143_routing_authority_census.py \
  tests/unit/test_phase143_inference_capability_census.py --tb=short
```

**Last step:**
```bash
HOME_REAL="$HOME" HOME="$(mktemp -d)" \
PLAYWRIGHT_BROWSERS_PATH="$HOME_REAL/Library/Caches/ms-playwright" \
npm_config_cache="$HOME_REAL/.npm" \
uv run pytest -q -n auto --ignore=tests/e2e/test_metal.py
```

## 4a. Orchestrator dispositions (2026-08-26)

All six recommendations ACCEPTED as written, decided by the
orchestrator as tie-breaker. Emphases: call 3 (disappear, not
hard-refuse) implements the standing owner ruling that HoldSpeak is not
really released — no backwards-compat ceremony; call 6 (retire raw
`model_profile.*` / `destination.*` MCP families) closes the
MCP-vs-HTTP private-provider bypass the inventory proved — the Library
and Assignments twins ARE the owner API, underlying services stay
internal composition. Call 4 closes the Story-13 ledger note as a
golden proof, no new behavior. Build order: S1 (twelve twins) + S2
(declarative-vector parity harness) in one round; S3 (sync hostility);
S4 (named cross-cutting retirement — the shared-file law applies: every
family/tool retired drags its neighbors' test files into the round);
S5 (manifest/census closeout + sweep). No UI work; no shots needed this
story (transport only) — the shots-before-merge law is satisfied
vacuously, noted here so the close does not stall on it.

## 4. [ORCH-CALL] items

1. **Golden-parity mechanism — recommend shared declarative vectors, not recorded transcripts.** A single table declares seed, command, valid/invalid/replay/CAS vectors, and expected normalized body. The harness executes that table independently against fresh production HTTP and MCP compositions, then compares their logical envelopes. Recorded transcripts would freeze volatile IDs/times and conceal a changed service call; shared mocks would fail the “production objects” requirement. This extends the repo’s actual HTTP/MCP reciprocal pattern (`tests/unit/test_model_profile_authority.py:716-737`) rather than inventing a third test transport.
2. **MCP model-file intake — recommend a bounded base64 command, never a path or pseudo-local locator.** `model_library.use_model_file` takes `{request_id, filename, bytes_base64}` under a documented payload cap, creates a server-owned temporary file, calls the existing library service, and deletes staging in `finally`, matching the custody property of HTTP multipart (`holdspeak/web/routes/model_library.py:136-169`). Its parity golden compares the receipt/projection, not byte-for-byte HTTP multipart framing.
3. **Retired-shape MCP policy — recommend disappear, not a compatibility hard-refusal tool.** The consumer census for acquisition aliases has no production client and the repo is not carrying a release-compatibility contract. Remove retired names from `tools/list`, family dispatch, resources, docs, and tests; direct JSON-RPC calls get the standard unknown-tool response. New schemas reject formerly advertised fields before dispatch. This produces zero discovery and zero side door rather than preserving old target vocabulary in the catalogue.
4. **Receipt-unforgeability ledger — recommend close it here as a proof, not a new source feature or a deferred note.** `set_assignment` already persists and returns canonical `committed_effect` with its ordered chain (`holdspeak/services/inference_assignment_service.py:435-444,501-515,2230-2231,2324-2329`). Add parity/replay assertions for it and confirm it excludes path/endpoint/secret/binding material; then remove the ledger note as verified.
5. **Alias-retirement verdict — recommend retire both `download-and-use` / `use-existing` HTTP aliases and their MCP names in S4.** Their only source consumers are their own adapter/legacy tests and routes, while the Model Library commands are live and assignment-invariant. Retire together with named acquisition, API-manifest, MCP, and neighbour tests; do not leave one transport as an escape hatch.
6. **Raw model-profile family verdict — recommend retire the owner-facing raw `model_profile.*` and `destination.*` MCP surfaces rather than “updating” their wire shape.** The Model Library twin is the owner API; direct profile/binding/target mutation retains the bypass the charter exists to close. Underlying services remain internal composition dependencies, not MCP authority.

## 5. Risk register

| Risk | Containment |
| --- | --- |
| A parity test compares mocks or strips a meaningful semantic difference. | Seed two real databases; preserve result/error envelope and all nonvolatile domain fields; limit normalization to IDs/timestamps whose generation differs by transport. |
| An MCP file tool reintroduces local-path custody or unbounded memory use. | Accept bounded encoded bytes only, decode to server staging, reject extra/path fields, clean in `finally`, and test oversized/path-shaped inputs. |
| Removing a generic target field breaks an indirect Workbench/Recipe/Sequence test late. | S4 names every neighbour suite and runs a full source consumer census before retirement; no catch-all sweep surprise. |
| Retiring raw MCP tools leaves an HTTP or resource side door. | Assert absence from `tools/list`, `resources/list`, API manifest (where applicable), docs, and dispatch; run the existing owner/AGENT matrix through protocol and direct service. |
| Sync denial merely rejects a payload after it has already observed/configured/invoked something. | Instrument real probe/acquisition/runner/resume edges and assert zero calls plus DB/config snapshots around `SyncService.push`. |
| Receipt proof accidentally exposes private binding or provider material. | Compare the committed chain to a safe allowlist and run secret/path/endpoint sentinels through both transports. |
| Generated inventory drifts or the MCP walk has stale count expectations. | Regenerate artifacts last, repair `scripts/mcp_walk.py` expectations as named S5 work, and run it with isolated HOME after review. |
