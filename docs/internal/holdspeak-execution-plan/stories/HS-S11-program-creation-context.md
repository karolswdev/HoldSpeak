# HS-S11 · Create a Program in the intended project

**Detailed conditional proposal, not implementation permission.** Epic: [HS-E10](../epics/HS-E10-context-and-navigation.md). Decision: D13 in [Decisions](../DECISIONS.md). Source baseline: `80b641fa41c7352280cfa52e933acf6dbe8d3857`. Source inspection is not runtime reproduction; no product tests ran during planning.

## Job and evidence

From the global Programs surface, the owner chooses the work's project, creates a Drafting Program and continues in that acknowledged Program. Existing project/action entry points retain their genuine context instead of forcing another choice.

At the pin, `ProgramsCore.make()` sends only `{title: 'New program', template}`. The API wrapper and HTTP route add no project or repository. `ProgramService.create()` calls `_repository()`, which requires a local repository path or a project that resolves to one. The existing frontend New test mocks success for the incomplete request. This is a concrete source contract mismatch; it is not a reproduced production outage.

The current Project filter is derived only from Programs already in the list. It cannot discover a project with no Programs and is not creation authority. All global creation entries use the same `make()` path: New, Templates, compact More/Templates and the empty-state action. There is no current global raw-path creation control to preserve. The API's existing raw repository-path mode is different and remains supported unchanged.

Evidence: [existing workflow trace](../NEXTGEN-JOURNEYS-AND-NAVIGATION.md#workflow-follow-up-context-carried-through-real-work). Exact pinned sources: [ProgramsWindow.tsx](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/web/src/desk/programs/ProgramsWindow.tsx), [programs API](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/web/src/desk/programs/api.ts), [route](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/holdspeak/web/routes/programs.py), [service](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/holdspeak/services/program_service.py).

**Readiness boundary:** this slice supplies genuine creation context; it does not prepare or clone a repository. Its success proof uses a resolvable task-owned local source. A remote registration alone may still yield `no_repository`, while a filed/local source can resolve without that registration. Resolution exceptions can also collapse to `no_repository`; do not diagnose every such refusal as missing registration or promise Register will fix it. Do not gate Create on the registration's `cloned` flag or add clone/start work to this UI change. The broader [project lifecycle proof](../EXECUTION_INDEX.md#repository-readiness-in-the-project-journey) remains separately scoped; it is not a new S11 dependency or test-budget expansion.

## D13 and G11 decision boundary

D13 has two valid, still-pending product branches:

- **A, fit the current lifecycle:** gather project/repository context before creation. This story fully specifies a narrow global **explicit-project** UI under that branch; the service resolves the repository. It is the recommendation because the existing backend contract can remain unchanged.
- **B, unbound Draft:** create without a repository and bind it before Start. This requires separate design of persisted unbound state, validation, templates/checkpoints, planning and start prerequisites, API/SDK compatibility and existing-Draft migration. Selecting B stops this implementation plan. Do not simulate B by sending an empty or guessed project, or weakening `_repository()`.

**G11** accepts or redirects branch A's local interaction before implementation:

1. Global New/template selection opens an in-flow creation well in the existing Programs surface. It does not create immediately. The chosen template is retained; the existing default title `New program` remains, avoiding an unrelated naming/editor redesign.
2. Read the actual active-project list, with an explicit Refresh projects/read-retry action. Require an explicit selection, even when there is one project. No first/recent project, display filter, last-used file, person or window scope silently becomes the creation target. Dismissing before submit creates nothing.
3. Show the chosen project and template at the final Create action. After submit, freeze/capture that request tuple and allow only one in-flight create in this surface. A click selecting a template is not a repository-operation approval or Start action.
4. Keep all existing contextual `/from-action` behavior and provenance unchanged. Do not put this global well in front of Run as a program.
5. Separate known refusal, uncertain outcome and acknowledged creation. Preserve an acknowledged Program ID even if opening its window or refreshing the list fails. Unknown creation must not be automatically retried. Closing/unmounting a pending flow is not cancellation of the server operation; a late answer must not overwrite a newer selection or force an abandoned flow's window open.

Other decisions, including D14 completion, D15 overview and D12 navigation, do not block this slice. Acceptance of G11 does not approve an opener rewrite, new universal context object or backend lifecycle change.

## Proposed interaction and truthful outcomes

Use the current Desk composition: title/frame, Toolbar, one in-flow well/content and StatusBar. Compose public `GadgetRow`/`CycleGadget`, `Button` and existing named feedback species. Do not create a modal, new application, route, shell or generic picker infrastructure. Keep any small cohesive form code in `ProgramsWindow.tsx`; no file-size rule requires extraction.

The proposed feature-local typed project-list read belongs in the existing `programs/api.ts` and uses `apiFetch`. Its helper/type names are new proposals, not existing API. Consume the existing `/api/projects` endpoint; do not reuse list filters or send a repository record ID in `repository`. `/api/repositories` IDs are not local paths. `/api/projects/{id}/repository` is not the complete Program resolver and cannot certify creation readiness.

| State / event | Required behavior under proposed G11 |
| --- | --- |
| Project choices loading | Named loading state; Create unavailable; no create POST |
| Choice lookup failed | Named failure and explicit read retry; no success-shaped empty state |
| Latest choices remove/archive the selected project | Mark that selection unavailable and disable Create until a fresh explicit valid selection; CycleGadget retaining an off-roster option does not make it valid |
| No active projects | Explain that a project is needed; no guessed target or create POST. Do not add a new project-creation workflow in this slice |
| Project has no existing Programs | It remains selectable from the project source, not excluded by the Programs filter |
| Choice made / template changed before submit | Show the current explicit choice and template; no write until final Create. Refresh projects is read-only and cannot silently choose a replacement |
| Cancel before submit | Discard the local well/restore focus; no Program exists as a result of this flow |
| Submit pending / repeated press | One captured `{title, template, project_id}`; block concurrent duplicate submission; no Start, plan or provider call |
| Current project cannot resolve a repository | Show the service refusal and retain input for a deliberate correction. A project-list entry is not proof of a usable repository |
| Known pre-write refusal | For the proved `ApiError` status/code pairs `400/repository_required` and `409/no_repository`, explain the specific refusal. Do not classify every 4xx/service error as pre-write; resolver registration may still have occurred, so no blanket `Nothing changed` claim |
| Transport failure, generic server failure or malformed success | State that creation could not be confirmed; preserve input and offer to inspect/refresh existing Programs before an explicit new attempt. Do not say `Nothing changed`, infer an ID from a title match or automatically retry |
| Valid acknowledgement with a nonempty string Program ID | Keep that ID, reveal that Program and refresh through existing mechanisms. The created Program is authoritative even if later reveal/refresh fails |
| Reveal/refresh fails after acknowledged creation | Show that creation succeeded and retain a same-ID Open/refresh action. Never turn that action into a second create |
| Flow unmounts while pending | Do not claim cancellation or open an abandoned flow on late completion. A later list refresh may reveal the persisted result; do not erase it |

The create path saves before later checkpoints, requirements, announcements and final readback. A failed response is therefore not proof that the Program does not exist. No idempotency key exists in this contract. This story improves honest client behavior; it does not create a backend reconciliation engine or promise exactly-once creation across browsers. Its global-list reload does not refresh an already mounted Project Room. If S13 is also accepted, the [creation-to-Room integration gate](../VALIDATION.md#creation-to-room-integration-gate) proves that separate read/identity handoff. Missing notification or a failed Room read cannot justify a second create or identify an uncertain attempt by title.

## Acceptance matrix

The following cases are proposed coverage, not passing or preexisting tests.

| ID | Proving boundary |
| --- | --- |
| C11-01 | Each global entry opens the same well with its correct template and sends no immediate POST |
| C11-02 | Real project-list response includes a project with no Programs; choices are not derived from current Program rows |
| C11-03 | No auto-selection from first/only/recent project or current Project filter; final Create requires an explicit durable ID |
| C11-04 | Read loading, unavailable, empty and retry are distinct; request failure is not empty success; late reads cannot revive a removed/archived selection |
| C11-05 | Final press emits exactly the selected project/template/default-title tuple, including with a conflicting display filter |
| C11-06 | Real HTTP route/service accepts that tuple with a temporary local project/repository; returned/stored project and repository match; state is Drafting and no work starts |
| C11-07 | Missing context and project-without-repository refuse through real route/service; no test stub fabricates successful creation for the old incomplete body |
| C11-08 | Repeated click/Enter while pending yields one POST; a later input change cannot redirect the captured request |
| C11-09 | Proved status/code refusal retains input; generic error and malformed acknowledgement stay unknown. Real post-save fault returns 500 with the exact persisted Program still present and no launch; UI never calls that no-write or automatically retries |
| C11-10 | Acknowledged creation followed by reveal/list failure retains the same ID; recovery does not create again |
| C11-11 | Cancel before submit and unmount while pending have different semantics; late completion does not overwrite or reveal a newer/abandoned flow |
| C11-12 | Existing Run as a program carries action/project, retains its origin and does not acquire the global chooser; API raw-path creation stays supported |
| C11-13 | 393-wide/narrow-in-wide window, keyboard focus/selection/Escape and real hit targets work using current public primitives; no clipped actions or new shell |

Frontend interaction proof and real backend contract proof must agree on the same request shape. A recorded response is useful, but cannot replace the request assertion or real producer test. Do not broaden this into all Program lifecycle correctness, live repository operation or organizational permissions.

## Exact source map and ownership

Read these symbols/sections at the pin, then revalidate current source. The source-only archive check for this slice did not independently re-fetch current main; the package's 19:34 UTC main check is the last recorded remote comparison. Fresh drift checking remains HS-T00's job.

| Existing path | Exact context | Ownership |
| --- | --- | --- |
| `web/src/desk/programs/ProgramsWindow.tsx` | `ProgramsCore`/`make` 143–166; empty action 224–226; template/compact entries 258–293; toolbar 307–313; filter rows 168–190 | Editable only for this global creation flow |
| `web/src/desk/programs/api.ts` | `CreateBody`/`createProgram` 39–55; `usePrograms`/reload 267–283 | Add small typed project read; keep creation/body and existing list-read contract. Reload catches its error; awaiting it does not establish refresh success |
| `web/src/desk/programs/programs.css` | Current `pg-window`/body/toolbar/container layout | Optional narrowly scoped layout only; no token/theme redesign |
| `web/src/desk/surface/gadgets.tsx`; `web/src/desk/surface/index.ts` | `CycleGadget` 159–205 and public export; off-roster option behavior | Read-only species; form validates selected membership |
| `web/src/desk/conductor/StartAgent.tsx`; `web/src/pages/cores/SettingsCore.tsx` | In-flow/read-state examples 152–182/314–335; correct `is_archived` and read-generation example 866–879 | Read-only examples. Do not copy StartAgent's auto-selection or incorrect archived field |
| `holdspeak/web/routes/projects.py`; `holdspeak/services/project_service.py` | `build_projects_router`, GET projects 232–237; list 516–525; `_project_payload` 5888–5893 | Read-only actual `{projects: [...]}` DTO with row `id`, `name`, `is_archived` |
| `holdspeak/web/routes/programs.py`; `holdspeak/services/program_service.py` | `_CREATE_FIELDS` 78–82; `_call` 106–120; create route 145–150; `_repository` 1846–1864, `_project_source` 1866–1876, `create` 1912–2015, `_wire` 1617–1647, `_plant_requirements` 3124–3143, `changed` 5022–5076 | Read-only binding/persistence/refusal contract; no new lifecycle/API |
| `holdspeak/services/agent_hand_service.py` | `resolve_project_repository` 263–341; precedence/fallback and project-map registration branch | Read-only resolver. Do not equate a registration endpoint with this whole contract |
| `web/src/desk/programs/RunAsProgram.tsx`, `fromNote.ts`; `web/src/features/project-room/ProjectRoomCore.tsx` | Action call/verb 13–44; note call 14–27; Room CTA 891–896 | Read-only genuine context and provenance; not global picker consumers |
| `web/src/lib/api.ts`; `web/src/desk/programs/open.ts` | `ApiError` status/payload 13–23; JSON fallback 62–78; `openProgram` 4–5 | Read-only. Malformed 2xx may yield `{}`; void open is not mounted-window acknowledgement |
| `web/src/desk/programs/__tests__/programs.app.test.tsx` | API/open mocks 93–124, reset 189–201, current New 265–274, template 579, note origin 800–809 | Editable existing app suite. Deferred Promise requires direct mock; `hub()` structured-clones values |
| `tests/integration/test_desk_programs.py`; `tests/integration/program_rig.py` | `_fixture`/`_client` 46–61; current create 530–539; Rig 300–334 | First test file editable; Rig read-only. New focused test setup uses temporary actual repo/DB |
| `tests/integration/test_desk_program_from_action.py`; `web/src/desk/programs/__tests__/runAsProgram.app.test.tsx` | Context/provenance 33–57; UI body/open/refusal 22–42 | Read-only focused regression tests. Backend test mocks `_project_source`, so not the new resolver proof |
| `tests/unit/test_agent_hand.py`; `tests/unit/test_project_room_read.py`; `tests/conftest.py`; `holdspeak/runtime/composition.py` | Temporary registry precedent 447–455; partial `WebContext`/projects router 366–378; isolated composition 904–927; supplied instance resolution 347–377 | Read-only test construction/reference; never copy owner configuration |

**Read-only frame proof:** `web/src/desk/components/DeskWindow.tsx` exposes the pointer-driven `resizeBind` 679–696, `.desk-window-grip` 786–790, root `id` 1250 and noncompact grip 1451. `web/src/desk/applications.ts` 218–234 gives `surface-programs` and minimum width 420. V11 uses that actual control at 1440, not CSS sizing; 393 is separate compact proof. These sources identify a test path, not an observed browser result.

**Proposed new browser test:** `tests/e2e/test_program_creation_glass.py`, using read-only `tests/e2e/glass_infra.py` helpers and the isolated/intercepted [V11 lane](../VALIDATION.md#bounded-browser-lane). No new harness or real Program creation is allowed in that UI proof. The existing keys-glass test actually creates/starts Programs and is not a substitute.

**Proposed new fixtures, all explicitly owned:** `web/src/desk/programs/__fixtures__/program.create_projects.json`, `program.create_project.json`, `program.create_no_repository.json`, `program.create_repository_required.json`. Their producer cases are new work, not present or passing at the pin. One sole capture owner produces all four from the same seeded scenario, with linked roster/request/success/refusal IDs; a second case only asserts refusal and post-save-fault outcomes. V11 specifies test-only request/status/body capture records, preserving real bodies unchanged and giving the refusal an explicit recorded request ID. Existing drafting and other fixtures remain unchanged.

For the new real-resolver test, register the Rig's temporary local repository in a temporary `DeliveryRegistry`, file `repository:<source_id>` to the chosen project and supply only the composed hand/registry dependency. Include `build_projects_router(WebContext(get_state=lambda: {}, project_service=ProjectService(rig.db)))` in that bounded test app and supply the owner principal. Patch environmental project-map loading to an empty test map if needed; do not patch the resolver's answer. The actual test code must follow the current signatures when implemented.

**Scope limits:** the current resolver can register a local source through its project-map fallback, so even a pre-Program refusal is not a universal no-side-effect guarantee. `no_repository` also collapses underlying source-read failures. Current create does not supply a general archive or path/project consistency check. The UI uses active choices from its latest successful read but cannot promise server-time archive eligibility. Leave those backend semantics unchanged and describe the actual refusal rather than invent a stronger contract.

## Tasks and proof

[HS-T00](../tasks/HS-T00-baseline.md) → [HS-T11-01](../tasks/HS-T11-01-contract.md) → [HS-T11-02](../tasks/HS-T11-02-implementation.md) → [HS-T11-03](../tasks/HS-T11-03-verification.md).

Use the exact focused budget in [V11](../VALIDATION.md#v11-program-creation-verification). Existing command definitions and tests are source-verified; new cases and helper names are proposals. Run only in an assigned safe execution environment after the local contract is accepted. Integrated checks follow the current integration owner's rules, not a full-suite worker run.

## Rollback and stops

This branch requires no API/schema change or migration. A reviewed reverse patch can remove the well/read/helper and matching tests, restoring the former incomplete global request behavior; disclose that limitation. Never delete Programs created during verification outside isolated fixture data, and do not treat reverting UI code as undoing a server write.

Stop for D13 branch B, unsettled G11, new raw-path/registration/cloning UX, necessary backend changes, unknown fixture effects, source drift, uncontrolled project choice semantics, unsupported chooser primitives or an inability to distinguish acknowledged creation from reveal failure. Request a bounded amendment rather than inventing infrastructure. Preserve [I16/I18/I21/I24/I25](../INVARIANTS.md).
