# HoldSpeak structural diagnosis and layout options

**Publication note, 4 November 2026:** `${ANALYSIS_ARTIFACTS}` is a placeholder for the original external analysis directory. Its scripts and data are not bundled. The historical commands below are not runnable from this documentation checkout alone. Only path notation changed; the findings and execution claims remain historical.

Read-only first pass at `80b641fa41c7352280cfa52e933acf6dbe8d3857`, 2 November 2026. The original findings below came from source/tree inspection, not product tests or a runtime reachability census. A subsequent [measured Python AST pass](PYTHON-STATIC-ANALYSIS.md) analyzed all 916 hub Python files without importing application code; it is separate evidence with its own graph limitations. These are findings and options for user supervision, not implementation tickets or a frozen target layout. The [version 2 refinement](PYTHON-STATIC-ANALYSIS-V2.md) adds context/root-aware measurements and source-checked responsibility directions, distinguishing small misplaced helpers/contracts from intentional lifecycle composition.

## Main finding

The outer runtime/package boundaries are defensible. The stronger concern is ownership *inside* the hub and Desk: central services mix independent responsibilities, sibling modules import contracts from their orchestrator, and a shared UI layer reaches upward into application composition. Selective boundary repair appears more justified than a repository-wide rewrite. This is a preliminary recommendation, not accepted scope.

## Inventory and its limits

The reviewer used nontruncated Git tree metadata. Counts indicate review scope, not bloat or unused code.

| Area | Observed inventory | Important denominator |
| --- | --- | --- |
| Python hub | 916 Python files: 198 services, 145 package-root, 133 web, 70 kernel, 60 DB | Includes declarations/support files; these subgroups do not exhaust the total |
| Browser | 1,539 TS/TSX files; 785 non-test/non-parked paths; 569 of that path-filtered subset in desk, 105 pages, 50 features | Path count only, not runtime-active files; excluded parked production modules can still be imported |
| Python tests | 1,697 Python files, 368 under parked paths | Parked content is not automatically dead or safe to delete |
| Apple | 265 Swift files, 93 under Tests | Explicit runtime targets, not part of the browser stack |

[pyproject.toml](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/pyproject.toml) and [hatch_build.py](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/hatch_build.py) deliberately package the Python hub with bundled Vite output. [apple/Package.swift](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/apple/Package.swift) declares Contracts, Providers, RuntimeCore, Hosts and separate inference dependencies. The separate AIPI/device runtime and Firefox extension have distinct purposes. There is no evidence here for merging these runtimes or multiplying deployable packages.

## Finding 1 Project responsibilities are mixed and mutually composed

**Evidence:** [ProjectService](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/holdspeak/services/project_service.py) has Room read aggregation (`room` around line 766 and section readers through 3225), resumable Ask-task/cursor handling (about 3245–3608), and project/resource/item mutation machinery (about 3608–5960). The approximately 5,982-line size helps locate the work, but the independent reasons to change are the concern.

[ProjectDeltaService.attach_project_service](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/holdspeak/services/project_delta_service.py#L609-L617) explicitly documents mutual composition: Delta needs ProjectService to create items, and ProjectService needs Delta for the Room review section. This is evidence of bidirectional responsibility, not a demonstrated runtime failure.

**Option:** Separate Room read aggregation from project commands while keeping the existing façade initially. Decide Ask-task ownership separately; do not automatically create another service for every cluster of methods.

**Benefit and risk:** A concrete dependency can become one-way and onboarding becomes more local. Preserve transaction/revision boundaries, authorization, section-level degradation and callers. No generic CQRS infrastructure is needed. Confidence is high on the mixed responsibilities; the precise split remains a design choice.

## Finding 2 Program contracts still live inside the orchestrator

**Evidence:** [ProgramService](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/holdspeak/services/program_service.py) is already accompanied by many `program_*` modules, yet [program_runner imports](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/holdspeak/services/program_runner.py#L52-L55) takes its service class, errors, constants and formatters from the service. The service imports its runner around lines 891–896. [program_audit](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/holdspeak/services/program_audit.py) imports `ProgramRefused` and `_is_owner`. Deferred imports accommodate these reciprocal dependencies; no import-time crash is established.

**Options:** Extract genuinely stable domain contracts and pure helpers below orchestration while keeping filenames, or gradually group the domain into a package after that ownership is clear. Moving files alone would preserve the coupling. A roughly 5,646-line service is not, by itself, a reason to split it.

**Benefit and risk:** An agent could find contract, implementation and tests without loading a central service as a contracts barrel. Avoid a generic types dumping ground, dozens of tiny services or duplicate lifecycle authorities. Confidence is high on coupling and medium on final layout.

## Finding 3 The shared surface owns application composition

**Evidence:** [SendWell](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/web/src/desk/surface/send/SendWell.tsx#L42-L66) imports connection API/presentation from `pages/cores/connections`, behavior/CSS from `features/channels`, and lazily loads Settings' destination form. Its comment explicitly says this avoids a static Settings import cycle. Reusing one admitted form is good; the direction of ownership is less clear.

**Options:** Make Send an application/domain composition built from lower-level surface primitives; or move reusable connection presentation/form ownership to a feature module consumed by Settings and Send, keeping Send's location initially. Neither option duplicates the form.

[The architecture guard](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/web/scripts/guard-architecture.mjs) checks its private surface-import and roving rules only for `src/desk` consumers. Other checks, including library CSS, have broader scope. Apps live across `desk`, `pages/cores` and `features`; folder placement therefore affects some enforcement. Agree on ownership/import rules before cosmetic migration.

**Benefit and risk:** A clearer shared-versus-application boundary limits change amplification. Preserve pending-command custody, preview identity, durable-send/replay and unknown-outcome semantics. Confidence is high on the inversion; the right home needs a domain-consumer map.

## Finding 4 Bootstrap construction is harder to find than its name suggests

**Evidence:** [web_server._create_app](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/holdspeak/web_server.py) contains substantial service construction around lines 1271–1694 as well as host lifecycle, sockets and loops. [holdspeak/runtime/composition.py](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/holdspeak/runtime/composition.py) maps, installs and exposes services. This is **not** proof of two independent composition roots.

**Option:** First make the ownership split explicit. If lifecycle evidence supports it, make runtime bootstrap construction a clear runtime responsibility, with the web host supplying callbacks/routes. Preserve one installed object graph and documented bare-service contexts.

**Benefit and risk:** A fresh agent can locate actual construction without chasing a misleading module name. Extraction without lifecycle proof could create the duplicate composition root it is meant to prevent. Confidence is high on current placement, medium on extraction value.

## Layout options to discuss

| Option | What it changes | Tradeoff |
| --- | --- | --- |
| A Selective boundary repair | Keep outer layout; clarify contracts/read aggregation/shared form ownership/bootstrap responsibilities | Smallest disruption, but mixed naming/layout may remain temporarily |
| B Gradual domain packages | Group domains after responsibilities are settled, keep compatibility façades during migration | Better navigation; more imports, fixtures, selectors and documentation must move coherently |
| C Whole-repository architecture rewrite | Replace the current layering broadly | Not justified by current evidence; large risk and onboarding cost during transition |

A is the preliminary lean, not a decision. A and B can be staged, but no path move is prescribed or authorized. First map the affected static/dynamic imports, barrels and registries. The manual first pass did not calculate cycles or fan-in/fan-out. The later Python AST report now supplies qualified all-context import measurements for the hub, not runtime cycles, frontend coverage or feature change sets.

## What to preserve and what is not proved dead

Keep the coherent web stack and existing runtime boundaries, kernel/effect contracts, canonical schema/reconciliation, memory freshness checks and decision reader distinctions unless new evidence says otherwise. Large cohesive modules are acceptable. Existing co-located app tests and tiered Python tests are useful.

ProjectMemoryCore currently retains test/type compatibility references, but the Memory application registry loads MemoryCore directly. Its header's lazy-loader rationale is stale and must not be repeated as current runtime evidence. A parked path is not automatically unreachable: a nonparked SystemShade wrapper re-exports a parked module, without establishing that wrapper's production reachability.

The [dead-code evidence review](DEAD-CODE-REVIEW.md) records these corrections and three investigated candidates. Its follow-up traces the Desk registry path and an inspected 18-local-module Briefing closure without finding either frontend candidate; the full Desk graph remains unresolved. Three nonparked tests value-import the ProjectMemory wrapper, while the barrel is type-only. Retained older Vite chunks do not prove current-source reachability. MemoryIndexRepository is required through dynamic registration in source; neither frontend candidate has been established as safely dead. Dead-code decisions require entrypoint, dynamic registration, plugin, compatibility and test evidence. No removal is authorized.

## User decision needed

Is this structural framing closer to the intended goal? Prefer selective in-place repair, progressive domain ownership, or a different emphasis? Which feature-change or agent-onboarding pain should the next bounded investigation use as its concrete test? [Record direction](DECISIONS.md) before expanding implementation plans.

## Measured appendix: ProjectService responsibility cohesion

**3 November 2026. Finding:** the scoped AST evidence supports distinguishable Room, saved-Ask and command responsibilities, but not three independent, pure services. A shared database handle exaggerates cohesion if counted coarsely; helper-mediated state and transaction obligations make an easy mechanical split unsafe. This refines Finding 1, without approving a target layout.

### Scope and reproducibility

Snapshot remains `80b641fa41c7352280cfa52e933acf6dbe8d3857`. A new standard-library analyzer parsed **one complete application file**, `holdspeak/services/project_service.py`: **98 direct class methods**, including the constructor, 16 static methods and one async method. It verified the file's Git blob against the retained manifest: zero parse or integrity errors. The earlier 916-file v2 census was reused, not rerun. Supplemental source checks accessed 12 Python files in total, including this file; all 12 blobs match the same manifest. Those checks are not another AST census.

Run `python ${ANALYSIS_ARTIFACTS}/project_responsibility_cohesion.py`. The analyzer and `project_responsibility_cohesion.json`, its compact `_summary.json`, and `project_responsibility_source_checks.json` are retained outside the source tree in that directory. Synthetic checks of our analyzer passed, and an independent lexical recount agreed. No application import, execution, test, installation or source edit occurred; no file-length threshold or truncation was used.

### What the machine actually measured

A field edge is a lexical access to `self.<field>`, with class constants separated and `_db.<repository-or-access-handle>` retained. A call edge is `self.<declared-method>(...)`; repeated call sites and distinct caller/callee pairs are counted separately. All branches are retained. There are **215 call sites / 182 pairs**, including **18 sites inside nested functions or lambdas**, plus **three method-value references** counted separately. These are potential dependencies, not demonstrated execution.

The following named entrypoint sets were chosen from the observed responsibilities, not generated by clustering. Closures include the entrypoints themselves and follow internal calls through helpers.

| Responsibility probe | Entry methods | Potential method closure | Distinctive direct collaborators within closure |
| --- | ---: | ---: | --- |
| Room projection (`room`) | 1 | 41; 42 including method-value references | `_delta_service`; broad project, meeting, source, update and steward reads |
| Saved-Ask lifecycle | 6 | 13 | `_db.project_ask_tasks`; cursor helpers; DTO delegates to custody outside this graph |
| Revisioned project/item commands | 15 | 32 | `_ledger` in all 15 entry methods; shared command helpers |

All three closures intersect only at `_require_project`; Room and commands additionally share `_project_payload`. None of the Room or saved-Ask closures reaches a revisioned command in this graph. Conversely, **65 of the 97 nonconstructor methods load `_db`**, so treating any common field as the same responsibility would obscure the separation. Finer handles still overlap: Room and commands both access projects, meetings, project relationships, automations and steward policies, as well as connections and the unqualified DB object.

The inventory also retains 14 other public read entrypoints and `mark_room_read` separately. All 37 public methods are covered by the declared probes; their reference-augmented union covers all 97 nonconstructor methods. This is coverage of the class inventory, not production reachability. Callback handling matters: excluding nested function/lambda bodies reduces the `room` closure from 41 methods to five. `needs_you` passes `self.room` and `self.list_projects` to a builder, while source sorting passes `_token_sort_key`; none is a direct call at that site.

### Strongest counterevidence and limits

- **Few field assignments do not imply little shared state.** The only four direct `self` field stores are constructor assignments. Yet [saved-Ask cursor handling](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/holdspeak/services/project_service.py#L3565-L3592) can initialize a database secret, and [Needs-you's helper](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/holdspeak/services/needs_you_aggregate.py#L228-L273) writes/prunes its durable cache. Public reads are [decorator-observed](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/holdspeak/services/observer.py#L267-L279), potentially writing pipeline events with SQLiteObserver; NullObserver is the constructor default. Thus “read” is not a proven purity boundary.
- **Commands have a stronger shared reason to change than a common DB field.** Fourteen command entries directly call `_check_idempotency`, `_command_txn` and `_record_command`. The fifteenth, [create_item_in_transaction](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/holdspeak/services/project_service.py#L5261-L5276), uses its caller's connection and idempotency responsibility. [Delta invokes it inside proposal acceptance](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/holdspeak/services/project_delta_service.py#L980-L1012). Revision, item/change rows, events and [kernel answer completion](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/holdspeak/services/project_kernel.py#L456-L474) must remain atomically coordinated. `mark_room_read` and saved Ask use different mutation paths; not every Room write follows this command contract.
- **Saved Ask has existing ownership intent.** Its [source rationale](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/holdspeak/services/project_service.py#L3233-L3243) assigns durable saved questions to Room state and injects dispatch. Do not automatically relocate them into AskService. The same comment's claim that AskService persists nothing is not a current global invariant: [AskService.keep records artifacts](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/holdspeak/services/ask_service.py#L1625-L1651).

Aliases, imported helpers, decorators, passed connections, dynamically attached `_people_service`, runtime wiring and external callers are not expanded into the graph. Absence of a direct field/call edge does not establish purity, independence or dead code. The useful design direction remains making Room composition easier to find while preserving one authority for each lifecycle and transaction, rather than creating a small service per measured group. Whether that reduces real change and onboarding burden remains a supervised design question.

## Measured appendix: Program dependency direction

**3 November 2026. Finding:** the service is a contracts barrel, but this is not simply eleven siblings needing its concrete class. Most imported names are vocabulary, an error or helpers. The important residual coupling is the shared service instance, mutation coordination and default wiring. This refines Finding 2; it does not approve an extraction or a target package layout.

### Scope, counts and reproduction

At the same pinned snapshot, `80b641fa41c7352280cfa52e933acf6dbe8d3857`, a new standard-library AST pass parsed **24 complete files**: all **21 `services/program*.py` files**, plus their three directly imported Program-family collaborators, `db/programs.py`, `kernel/program_ops.py` and `program_templates.py`. There were **zero parse or Git-blob integrity errors**. Four additional DB files were source-checked for persistence context, making 28 source files accessed in this bounded pass. All 28 match the retained manifest. This is not a rerun of the 916-file census.

The 21-file family contains **440 import statements / 627 imported bindings**: **145 top-level**, **295 deferred inside function bodies**, and **zero type-only guarded statements**. The 24-file scope totals 455 statements / 651 bindings. Every imported name, alias, resolved module, source line and enclosing definition is retained. A statement importing several names counts once as a statement and once per name as bindings; neither count measures runtime executions.

Reproduce with `python ${ANALYSIS_ARTIFACTS}/program-boundary/analyze_program_boundary.py`. That directory contains the analyzer, full `program_boundary.json`, compact `program_boundary_summary.json`, and `program_boundary_source_checks.json`. The analyzer's synthetic checks cover aliases, relative imports, class/function contexts, type guards, postponed/quoted annotations and parameter shadowing. A separate full-file AST recount agrees with the key counts; its checker and `program_boundary_independent_validation.json` are retained alongside them. No application imports, application tests, installation or source edits occurred; no file-length cutoff was used.

### Exact service-symbol boundary

**Eleven siblings** import from `program_service`: audit, delivery, handoff, lessons, night, planner, rounds, runner, shaper, split and text. Their **40 import statements / 59 bindings** name **27 distinct symbols**. Only the runner's [line 52 import](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/holdspeak/services/program_runner.py#L52-L55) is top-level; the other 39 statements are deferred, not type-only.

| Kind | Distinct symbols | Import bindings | Exact names |
| --- | ---: | ---: | --- |
| Vocabulary | 9 | 14 | `ACTIVE_STATES`, `CLOSED_STATES`, `DEFAULT_REVIEWER`, `FINISHED_STATES`, `FROZEN_SET`, `NIGHT_ENDED`, `PARKED_BY_ENGINE`, `PARKED_BY_RACE`, `RACE_PROFILES` |
| Refusal contract | 1 | 14 | `ProgramRefused` |
| Helpers | 14 | 20 | `_budget`, `_is_owner`, `_new_id`, `_seconds_between`, `agent_label`, `duration_words`, `history_of`, `program_own`, `programs_on`, `race_all_red`, `race_group`, `steps_finished`, `triage_effort`, `your_turn` |
| Shared synchronization | 1 | 9 | `_LOCK` |
| Concrete class name | 1 | 1 | `ProgramService` |
| Default composition | 1 | 1 | `default_program_service` |

Only the runner imports `ProgramService` itself. Its **two name uses** are annotations at [line 153](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/holdspeak/services/program_runner.py#L151-L157) and [line 2386](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/holdspeak/services/program_runner.py#L2386-L2394), under `from __future__ import annotations`: no construction, subclassing, `isinstance` or other value use of that imported class name appears in the importing siblings. Its import statement still executes at module load. Annotation-only use is not proof that removing the runtime binding preserves external annotation introspection.

The service imports **18 siblings through 81 statements**, 80 deferred; its sole top-level family target is `program_rules`. The family graph has **68 distinct directed pairs** across all contexts and **13 top-level runtime-possible pairs**. A 15-module strongly connected component appears in the all-context graph; none appears in its top-level-only subgraph. These are bounded import graphs, not proof of runtime cycles or import-time safety outside this scope.

### What a contracts move would not fix

- **Object collaboration remains substantial.** A deliberately narrow lexical probe finds **460 accesses to 50 distinct attributes across 14 siblings**, using only the exact receivers `service`, `self.service` and `runner.service`. The runner alone has **181 `self.service` accesses to 24 names**, including `transition`, `save_step`, `store`, `_checkpoint` and `_clock`. These counts do not infer object identity or follow aliases. They show why changing imports to type-only imports or protocols would not, by itself, make these independent services.
- **The runner and service deliberately share lifecycle wiring.** [Service.runner](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/holdspeak/services/program_service.py#L891-L896) accepts an injected runner or calls `default_runner(self)`. The [runner factory](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/holdspeak/services/program_runner.py#L2386-L2394) obtains `default_program_service()` when necessary and caches by service identity. This is composition behavior, not a misplaced formatter.
- **One shared lock spans mutations.** Night, rounds, shaper and split import the service's [single `threading.RLock`](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/holdspeak/services/program_service.py#L230) at nine sites and use it in **12 `with` statements**; the service has another 36. [Split application](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/holdspeak/services/program_split.py#L330-L366) coordinates planning, dependency order, requirement reassignment and original-step removal under that same object. Duplicating the lock while moving helpers would change coordination.
- **A lock is not an atomic database transaction here.** `_apply_text` coalesces frames/ticks through the service's thread-local `_held`; `changed()` still performs state/note work before checking that flag. Text application [explicitly reports that earlier changes remain written on refusal](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/holdspeak/services/program_service.py#L4432-L4439). [ProgramStore writes](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/holdspeak/db/programs.py#L190-L200) use individual connection contexts, which [commit on clean exit](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/holdspeak/db/connection.py#L218-L242). Preserve this observed partial-write/error behavior unless a separately approved change replaces it. No concurrency or atomicity test ran.

### Smallest directional alternative, still a proposal

A cohesive domain-definition boundary below orchestration is better supported than splitting the service by size: place genuinely shared vocabulary, refusal and related state/representation rules together, retain the service façade and one lifecycle/mutation authority, and treat default wiring and synchronization explicitly. Existing focused Program modules may already be suitable homes; no new service or package is selected here.

Do not move every helper indiscriminately. `your_turn` has a lexical closure of **25 top-level definitions, including itself**, with dependencies on Program rules, requirements and brief wording. `_budget` [calls `program_text.parse_tokens`](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/holdspeak/services/program_service.py#L5534-L5544), while `program_text` [imports `triage_effort` back from the service](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/holdspeak/services/program_text.py#L303-L310). Moving both into an indiscriminate “common” module could preserve a reciprocal dependency. `programs_on` reads the environment, `_new_id` generates UUIDs and `_seconds_between` can read the clock; these are not all pure formatters.

The prospective onboarding benefit is a clear place for domain definitions without disguising the service's actual responsibilities. It has not been measured against a real feature change or new-agent exercise. Dynamic imports, callback wiring, external consumers, assigned aliases and runtime annotation introspection remain outside this graph. Lexical helper closures are not execution or purity proofs. This evidence supports selective ownership repair, not dozens of tiny files, a new transaction model, or approved implementation tasks.

## Source-checked appendix: Send and destination ownership

**3 November 2026. Finding:** the existing `features/channels` family is a credible home for the **one shared destination form and its destination/account presentation**, without creating a generic common bucket. The consumer map does **not** support moving every connection, onboarding or document workflow into it. This answers Finding 3's placement question more narrowly; neither the home nor a migration is approved.

### Actual consumers and dependency direction

At the same pinned archive, `80b641fa41c7352280cfa52e933acf6dbe8d3857`, a full-content literal-specifier/symbol search under `web/` and manual source checks found two current form host components:

| Consumer | What it actually needs | What remains distinct |
| --- | --- | --- |
| Settings' [`Destinations`](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/web/src/pages/cores/connections/Destinations.tsx#L525-L564) | `DestForm` for add and replacement edit; account warnings | Active/parked list, check/removal results, focus arrival and history-preserving replacement |
| Send's [`InlineDestinationForm`](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/web/src/desk/surface/send/SendWell.tsx#L604-L644) | The same form for add only | On save, choose the destination for this document and reload; saving does not send |
| Document adapters | One Send composition, not their own destination forms | Brief/note/artifact/decision references in `desk/documentSends.tsx`; meeting form/history in `meetings/MeetingSendWell.tsx`; update manual delivery in `features/channels/SendWell.tsx`; producer target restriction in `features/project-room/NudgeCard.tsx:217-232` |
| Narrow read/action consumers | `PutEditor` needs destination reads; `windowSend` reads/picks and navigates; `NeedsDrawer` shares prepared-send/retry/discard custody | Selecting an automation destination or a menu row does not dispatch; `ProjectRoomCore` imports only `Unreadable` |

The exact mixed static/dynamic loop is `Destinations.tsx:47` → `desk/surface/send/index.ts:5-34` → `SendWell.tsx:66` → dynamically loaded `Destinations.DestForm`. Separately, `SendWell.tsx:43,245` imports/calls `ConnectionsPane.chipLabel`. Both are value dependencies; the response/state imports marked `type` are not. The `accountChip` import reaches the Send module's top-level store restoration (`SendWell.tsx:84-107`). This establishes source coupling, not a measured bundle cost, static initialization failure or runtime cycle.

### Counterexamples and obligations a move would not solve

- **Account consumers are broader than destinations.** `features/project-room/door/useDoorController.ts:8-13,245,573,591-592` imports `fetchConnections`, `addAtlassianAccount`, `recheckProvider` and type-only `ConnectionTool` for source setup. `DoorCore.tsx:23-24` uses `SignInWell`/`notSignedIn` plus type-only `ConnectionState`. First-run's `connectionsStep.ts:13-14,53-114` instead discovers/adopts candidates through `/api/onboarding/connections`. Calls settings, Line settings, RuntimeDocs, TTS settings and `ConnectionsCard` import only the pane's command-display helper, with first-run also using `stateWords`. These are not evidence for a universal connections/send feature.
- **The shared form still knows Settings' DOM.** [`setUpAccount`](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/web/src/pages/cores/connections/Destinations.tsx#L228-L239) searches `.prefs-module` or the whole document for `connections-*` controls, clicks/focuses them, and keeps its draft mounted. Inline Add provides no alternate account-setup callback. Moving the file leaves this dependency intact; whether another open window supplies the controls is unverified.
- **The hosts' read contracts differ.** Settings listens to focus and `ACCOUNTS_CHANGED`, clears failed account data and guards unmounts (`Destinations.tsx:441-457`). Inline Add listens only to focus/manual retry, retains old `conns` on error, and lacks that live guard (`SendWell.tsx:604-620`). Shared-read extraction must decide freshness/error behavior rather than silently choosing one. Repeated empty-draft/default and key-save scaffolding is small duplication; the validation/form implementation is already shared.
- **Credential knowledge and account readiness are not one boolean.** Jira/Confluence require account reads; GitHub obtains identity at destination save. Email tracks provider/ref identity, legacy refs and stale responses; Slack distinguishes unknown from absent and Check does not post (`Destinations.tsx:154-225,351-433`). `accountChip` is a destination warning policy, not authorization.
- **Destination setup and send custody remain different.** The [declared operations](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/holdspeak/channel_operations.py#L7-L15) distinguish owner allow-list changes, preparation by owner/connected agent, owner send/discard and HTTP-only secret writes. Form drafts/key knowledge are component-local. Send's held key/body/preview uses tab `sessionStorage` and one shared store (`pendingCommand.ts:3-35`; `SendWell.tsx:450-547`). Do not replace this with the destination-save retry semantics or merge the update's manual delivery into generic send history.

### Placement options, not implementation tasks

A narrow repair could place the form, cohesive draft/default helpers and destination warning adapter beside `features/channels/channels.ts`, while keeping account contracts/state presentation below the `ConnectionsPane` screen and making account-setup navigation host-owned. Send could retain its exceptional current path initially; that would remove Settings-screen coupling, not make it a primitive.

A broader, consistent option would give the same existing feature family ownership of generic Send composition too, preserving one store and any chosen public compatibility exports. Document adapters keep their identities/history. This requires wider lazy-loading, CSS and consumer review; `features/channels/SendWell.tsx` is already an update adapter, so a same-named file move is not the design. No new stack, general recovery engine or common-types bucket is justified.

**Evidence limits:** reproduction and the detailed path/symbol map are retained in `${ANALYSIS_ARTIFACTS}/send-boundary/` (`inspect_source_references.py`, `literal_references.json`, `CONSUMER-MAP.md`). The scan covered all 1,550 web TS/TSX/MJS files without file-size/count cutoffs; it is lexical, not a TypeScript compiler graph or production reachability proof. Test/parked/unresolved literals remain labeled. Historical canvas copies are not additional current form hosts. The supplemental operation declaration matches the retained Python blob manifest. No application execution, tests, builds, installations or repository source changes occurred. Exact placement, navigation behavior and migration scope await user feedback.

## Measured appendix: imports into the HTTP layer (2026-11-03 17:00)

**Question:** which apparent reverse dependencies into the web layer are actual misplaced helper ownership, and which are composition or compatibility? This fresh scan refines symbol ownership rather than repeating the whole-graph SCC analysis. Snapshot remains `80b641fa41c7352280cfa52e933acf6dbe8d3857`; no application modules, repository scripts or tests were executed.

### Actual method and scope

Ran our standard-library AST analyzer over **916 hub Python files**, with **0 parse errors** and **0 Git blob-hash/byte-size mismatches** against the retained manifest. It resolves explicit `Import`/`ImportFrom` targets, including relative imports and known package-imported submodules. The selected boundary is imports into `holdspeak.web` (including descendants) or `holdspeak.web_server`, from modules outside those two targets. This is a namespace boundary chosen for this question, not a claim that every outside module is a domain service.

Result: **12 imported-symbol/target records, at 9 import statements, in 7 importer modules, pointing to 4 target modules**. These units are different; none is a runtime dependency, execution or performance count. The fresh scan also compares the two selected ID helper definitions structurally and records module-wide `Name` loads for imported bindings.

Reproduce with our analyzer, not a repository script:

```sh
python ${ANALYSIS_ARTIFACTS}/web_boundary_scan.py
```

Artifacts: `web_boundary_scan.py`, `web_boundary_scan.json`, `web_boundary_scan.stdout.txt` in `${ANALYSIS_ARTIFACTS}/`. JSON contains every selected import, scope, source hash, manifest validation, helper AST comparison and limitations. Earlier v1/v2 outputs remain unchanged.

### What the nine sites actually mean

- **Three helper-ownership sites.** The previously identified activity-meeting service imports `_parse_iso_datetime` from HTTP runtime support (`services/activity_meeting_candidate_service.py:32`). Two additional callers import a router-private ID generator: built-in skill seeding (`skills_library/__init__.py:60`) and artifact minting (`workbench_conductor.py:303`) depend on `web/routes/primitives/_shared.py::_new_id:14–15`. That target also imports FastAPI Request and WebContext. UUID-prefixed ID generation does not require those HTTP responsibilities.
- **Three sites need reachability/compatibility triage, not automatic deletion.** `runtime/device_glue.py:57–58` imports `_UnknownDeviceError`, `MeetingWebServer` and `WebRuntimeCallbacks`; `web_runtime.py:54` imports `_UnknownDeviceError`. The scanner finds **four imported bindings with zero module-local AST Name loads across these three statements**. That is a concrete unused-binding lead, not proof of dead imports: module reexports, dynamic attribute access and import side effects are outside this scan.
- **Three sites have identifiable wiring/use.** `runtime/composition.py:485` calls the HTTP adapter's `build_ask_service` to retain the configured hub transport; `runtime/meeting_glue.py:20` imports the exception it raises at `:211,214`; `web_runtime.py:55` imports web bootstrap types/constants. Composition's builder placement remains reviewable, but moving it must preserve its configured dependencies. These are not interchangeable with the small helper leaks.

### Small, defensible simplification versus another generic utility module

The ID functions in `services/support.py:62–63` and `web/routes/primitives/_shared.py:14–15` have **identical FunctionDef ASTs**, including signature and body. Both return the supplied prefix followed by twelve UUID hex characters. The conductor already imports the service copy at module scope (`workbench_conductor.py:20`), then shadows it with the HTTP copy inside `_auto_mint_artifact`. Reusing the existing binding is a concrete repair-in-place option that would remove this particular direct HTTP import without inventing a new module.

That option is not a blanket endorsement of `services.support` as the home for all shared helpers: it imports grounding and provider egress (`:47–54`) and owns Blueprint execution. Redirecting the skill seeder there would substitute another broad dependency. For the seeder, retaining a tiny local generator is also a reviewable alternative to introducing a broader dependency. If normalizing IDs across more callers, select a narrow, transport-independent owner after checking existing ID conventions; do not create a catch-all “common” package or merge unrelated generators merely because their names match.

AST equality is declaration evidence, not runtime equivalence under monkeypatching. Removing the conductor's local import changes its lookup seam from the router attribute at call time to an existing module-global binding. A targeted test-source search found no reference to that helper seam; one migration test patches the entire mint function instead (`tests/unit/test_workbench_runner_migration.py:482`). External consumers and dynamic patches were not inspected. Preserve ID format, call-time generation and caller behavior in any future change; no implementation or deletion is approved here.

### Interpretation and limits

This measured boundary is smaller and more varied than “the backend imports the web layer everywhere.” There is one direct import from the `services` package in this selected set; root-level skill/conductor modules contain the two new helper cases. It supports targeted ownership cleanup and a bounded unused-binding investigation, not a wholesale layer rewrite.

The scan omits dynamic imports, transitive reachability, wildcard reexport expansion, calls and arbitrary alias rebinding. Module-wide Name loads are spelling references, not a binding-resolved usage graph. Import presence does not establish execution; absence of loads does not authorize deletion. An independent reviewer reproduced the counts with separately implemented AST resolution, confirmed the duplicate helper structure and challenged the initial grouping of bootstrap imports, leading to the explicit compatibility-triage category above. No runtime import-cost or cycle claim follows.

### ID-helper follow-up: what a small simplification must preserve (17:30)

Same pinned snapshot; source-only follow-up to the measured HTTP-import boundary. The identical helper ASTs establish the declared algorithm (`prefix + '_' + uuid.uuid4().hex[:12]`), not equivalence of all import/patch behavior. Neither caller needs a new ID policy, prefix validation, deterministic IDs or a changed format as part of an ownership cleanup.

**The conductor case is narrower than its name suggests.** The source-visible caller of `_auto_mint_artifact` is `WorkbenchService.retry_mint` (`services/workbench_service.py:747–805`), which recovers a completed item's historical route evidence before minting. This is not evidence that every current automatic publication goes through that helper. The helper returns an existing artifact before its local HTTP import (`workbench_conductor.py:296–303`), generates a request ID for kernel admission (`:315–323`) and an artifact ID for persistence (`:362–374`). Its stable idempotency key is separately derived from run/item identity; artifact collision recovery also uses those source identities (`:376–390,466–488`), backed by the unique run/item index (`db/schema.py:385–387`). Changing random-ID ownership should not change admission/refusal, receipt handling, historical routing or artifact/link transaction boundaries (`:408–462`).

Removing the conductor's local HTTP import would select its already-imported service helper, with no new module dependency. It would also remove that import's possible exception before admission and change function patching from a call-time router attribute to a captured conductor binding. That is a small candidate change, **not a behavior-verified patch**. `tests/unit/test_workbench_runner_migration.py:446–487` tests Retry Mint's historical-route selection but substitutes the entire mint function at `:482`; it does not validate the real helper's ID generation or failure boundaries.

**The seeder has a different dependency context.** Its known source caller is web startup (`web_server.py:1994–1995`), after primitive routers have already been mounted (`:1818`). Thus a reduced import graph does not demonstrate a startup speedup: the relevant modules can already be cached in that path. `skills_library/__init__.py:59–78` currently imports the HTTP helper before checking whether seeding is needed and catches exceptions by returning zero. Because it performs upserts one by one, that return alone does not establish that no rows were written. A helper-ownership cleanup should not silently redesign this seeding/failure contract or mistake zero for a verified clean rollback.

Importing `_shared` can initialize its parent packages, whose top-level imports include route families (`web/routes/__init__.py`; `web/routes/primitives/__init__.py:10–31`). That is source-level import coupling, **not** proof that importing starts a server or mounts routes. Conversely, redirecting seeding to `services.support` introduces its grounding/provider dependencies; `intel/__init__.py:17–36,78` also attempts optional provider/native imports and imports the engine. Their runtime availability or cost was not measured. The defensible options remain: reuse the conductor's existing helper locally; for seeding, retain a tiny local generator or choose a deliberately narrow shared owner if broader evidence warrants it. A new catch-all utility package is not needed to remove two HTTP edges.

**Before any future implementation:** check exact ID shape and fresh generation for the three used prefixes (`request`, `artifact`, `skill`), existing-artifact early return, admission refusal before persistence, artifact/link rollback and duplicate recovery, empty/nonempty seeding, and failures within the seeding loop. Preserve the intentional patch boundary or explicitly adjust tests for the selected owner. These are review criteria, not tests executed or implementation tasks. The bounded reference search found no test of the ID helper import seam or the seeder; absence of textual references is not proof of no dynamic/external consumers.

The follow-up interpretation was independently challenged against callers, package initializers, repository transaction code and the test substitution. Both cleanup options remain design alternatives, with no implemented or runtime-verified change.

## Receipt vocabulary ownership, not a universal write registry (2026-11-03 18:30)

**Question advanced:** the earlier graph found persistence retention importing a ProjectService constant. Does this justify another package or a shared policy engine? The source supports a much smaller ownership option, while the actual classification makes a blanket consolidation misleading.

At pinned snapshot `80b641fa41c7352280cfa52e933acf6dbe8d3857`, a fresh standard-library AST scan parsed all **916 hub Python files**, with **zero parse errors and zero manifest blob-hash/size mismatches**. It located the selected declaration/import/Name references and extracted literal data from three declarations, without importing target modules or invoking target functions. Reproduce using `python ${ANALYSIS_ARTIFACTS}/receipt_contract_scan.py`; detailed results are in the adjacent `receipt_contract_scan.json`. Earlier graph outputs were not overwritten.

- `services/project_service.py:270–283` declares **24 `ROOM_WRITE_METHODS`**. This is the vocabulary of Project/Watch writes shown in a Room, not every write in HoldSpeak. Its receipt projection uses the set at `:3143–3164`; its adjacent `_RECEIPT_SCOPE` maps each producer to the structured field containing project identity (`:295–320`). These responsibilities belong together semantically even if their storage location changes.
- `db/pipeline_events_retention.py:32–41,53–59` defines **12 exact read names and four read prefixes**. It keeps a named Room write first, then classifies other methods; unknown names are retained. The fresh literal-data comparison found **zero current Room-write names matching those read names/prefixes**. The override is therefore not resolving a present naming collision in this snapshot. That does **not** make it safe to delete: it explicitly protects the Room vocabulary if either declaration evolves.
- The two source-visible production consumers of that spelling are the Room projection and retention. `test_pipeline_events_table.py:105–115` asserts the classification and that every Room write survives; `test_philo9_03_receipt_scope.py:17–18,32–39` checks exact correspondence with the identity declarations, including a mutation case. These are inspected test contracts, not tests run. Because the current overlap is empty, the retention assertion alone would not detect removal of the explicit override; a future change should check a deliberately colliding read-like Room-write name to preserve precedence. The identity census checks declared producers, not exhaustive discovery of every new write. A file move that loses either fence would weaken the useful relationship rather than improve it.

**Dependency interpretation:** retention imports the service inside `is_read_method`; ProjectService imports database modules, so the package directions are bidirectional. A traversal of the retained v2 non-type explicit-import graph found no reverse ProjectService-to-retention path. This is an ownership inversion at the namespace boundary, **not a demonstrated module cycle, startup failure or runtime deadlock**. Deferred imports and parent-package initialization require separate interpretation; no import-performance claim is made.

**Small alternatives for review:** leave the working relationship intact until a related change, or place the Room receipt vocabulary with a narrow existing domain contract owner such as `project_contracts.py`, which already describes pure Room contracts and imports standard-library modules plus `refs` (`:1–27`). Preserve the service's import/export compatibility if tests or consumers use it. Whether the identity map should move alongside the vocabulary depends on the desired Room-contract boundary; do not move the whole receipt query or parsing implementation merely to obtain a cleaner arrow. No new generic registry, callback injection framework or universal read/write taxonomy is warranted by two consumers.

In particular, retention's global keep-unknown policy and Room presentation's explicit inclusion list are **different contracts**, not duplicate implementations of one list. Replacing either with the other would change which events are pruned or displayed. Keep batching, cutoff, disable-with-zero and transaction behavior separate from vocabulary ownership. This recommendation is based on responsibility and change coupling, not the number of lines in ProjectService.

**Limits:** explicit symbol-spelling references do not resolve aliases, dynamic attributes, external consumers or all reexports. Literal overlap is a snapshot property, not future equivalence. Graph traversal reused the audited syntactic graph and does not establish runtime reachability. No application imports, repository scripts, tests or source modifications were performed. Exact placement and any implementation remain pending review.

An independent source reviewer reproduced the literal counts/empty overlap and inspected the classification, pruning and receipt-scope tests. The review identified the missing collision-precedence coverage above; it did not establish runtime behavior or authorize a move.
