# HS-E50 · Make responsibility and proof easier to find

**Proposed structural workstream; implementation not assigned.** Parent: [ordered plan](../EXECUTION_INDEX.md#2-proposed-workstream-hierarchy). The goal is lower change amplification and bounded agent onboarding, not a new stack or a file-size quota.

## Outcome

A contributor should be able to find a feature's owner, its contract and the tests that prove a change without learning unrelated product mechanisms. Prefer a working façade with an explicit contract when moving code would add more concepts than it removes. A large cohesive file is acceptable.

Structural changes must preserve the product's existing journeys and authorities. Common data access does not make every read pure, and a method's name does not erase its transaction, observer or lifecycle effects. Measure the concrete dependency/reading burden before and after a selected change; do not promise an arbitrary token budget or number of files.

## Stories

| ID | Outcome | Local decision and constraint |
| --- | --- | --- |
| [HS-S51](#hs-s51-program-definition-ownership-gate) | Shared Program definitions have a coherent owner below orchestration, or an explicit retained façade | G51 remains pending: select the actual symbol/compatibility boundary, preserving exception identity, current composition/lock and partial-write behavior |
| **[HS-S52](../stories/HS-S52-project-review-boundary.md)** | Room's open-review query no longer requires private collaboration with the Delta command orchestrator, if a narrow move is justified | G52 compares retained query façade with an existing-repository query; preserve absent/empty/failure behavior and atomic acceptance |
| [HS-S53](#hs-s53-destination-ownership-gate) | Destination form/account navigation is reusable without Settings inversion | G53 remains pending: retain the current boundary or select a cohesive dependency repair; moving the form alone does not establish independence |
| HS-S54 | Small timestamp/ID and Room receipt contracts live at the right level | Preserve actual parsing/failure semantics; Room inclusion vocabulary is not global retention classification |
| HS-S55 | Already-shared project-update source policy has a focused common home | Do not create another policy engine; retain trusted HTTP run identity, durable CLI identity and private-source scope |
| HS-S56 | Optional retirement removes proven obsolete compatibility surface safely | Dynamic registration, supported external imports and tests must be checked; low references are not dead-code proof |

## Proposed delivery

Select one dependency that affects a real change or onboarding concern. Begin with [HS-T00](../tasks/HS-T00-baseline.md), record its current path/contract/proof, then compare retaining the façade against the smallest concrete ownership correction. No move is required if the evidence favors a clearer retained contract.

HS-S52 is the first detailed structural branch. It does not extract all Room reads, move saved Ask, invent a query framework or split every measured cluster into a service. Query selection belongs below orchestrators only if both callers can retain the same row/absence/failure semantics and capability availability. Delta's transaction-dependent item creation remains with the existing command owner.

## HS-S51 Program definition ownership gate

**Contract/discovery plan only; no implementation task, new module or moved symbol selected.** Use the [measured Program boundary](../STRUCTURAL-REVIEW.md#measured-appendix-program-dependency-direction), [backend alternatives](../NEXTGEN-TARGET-PROPOSAL.md#two-bounded-alternatives-against-the-measured-evidence), [Agent safety](../AGENT_START.md#authority-and-checkout-safety) and [HS-T00](../tasks/HS-T00-baseline.md). The source pin is `80b641fa41c7352280cfa52e933acf6dbe8d3857`. Removing imported definitions from the service does not make the runner an independent service or prove a runtime-cycle fix.

### Concrete boundary and G51 output

Return one contract record using the existing [completion report](../COMPLETION_REPORT_TEMPLATE.md), with these explicit choices and proof obligations:

1. **Retain or move:** compare an explicit retained façade with a minimal cohesive shared-definition move against the same bounded change, such as handling an existing named refusal through its consumers. A valid retained result must not claim import edges were removed. For a move, name only the selected vocabulary/refusal/representation symbols, current callers, runtime versus deferred/type uses, side effects, public export aliases and proposed destination. Exact new paths remain subject to review; `program_rules` or a generic errors/common file is not automatically the right home for all Program concepts.
2. **One refusal definition:** preserve `ProgramRefused` as one canonical class through supported old/new import aliases, with its existing `ServiceError` inheritance, `code`, `detail`, default status 409 and additional context. A second equivalent-looking sibling class is not a compatibility alias. HTTP `_call` catches the broader `ServiceError`; `_apply_text` and the inspected MCP shape/name flows catch `ProgramRefused` specifically (including subclasses). HTTP success alone therefore cannot prove the concrete catch contracts survived. Trace context/status through the actual HTTP projection and preserve the named MCP behavior, not just exception text.
3. **Runtime ownership stays put:** keep the service-owned `_LOCK`, thread-local `_held`, injection seams and default factories. `default_program_service` and `default_runner` each cache one **current** instance selected by identity; they are not maps retaining an instance for every past identity. Preserve same-object reuse and replacement when the selected DB/service changes, plus the existing fallback/injected-runner behavior. Do not introduce a new cache, service instance, lock, protocol-sized façade or transaction during a definition move. Annotation-only use of `ProgramService` is not proof that removing its runtime binding preserves supported annotation introspection.
4. **Preserve failure boundaries:** preflight refusal/dry-run can write nothing, while a later refusal inside `_apply_text` can leave earlier verbs written. The shared RLock and held-frame flag do not make the apply atomic. Preserve the refusal's context and partial-write explanation, `finally` cleanup/final `changed` call, and post-try tick ordering; on the propagated exception path the following `_tick_now` is not reached. Do not convert this into rollback-on-error or suppress already-written state/notes/history.
5. **Prove the claimed direction separately:** for selected moved definitions, trace their dependency closure and compatibility forwarding without reaching back into Program orchestration. Do not sweep in `your_turn`'s larger rule/requirement/word closure, `_budget`'s `program_text` dependency, or environment/UUID/clock helpers without separate analysis. A reduced lexical import count or annotation-only import is not proof of runtime independence, lower startup cost or less service collaboration.

### Exact source and proving boundaries

All paths below are **existing, read-only for this gate**. The measured report supplies broader import context; the local contract must select the exact implementation/test budget before code can be assigned.

| Existing source | What must survive / missing proof to specify |
| --- | --- |
| `holdspeak/services/program_service.py`: definitions/`__all__`, `_LOCK` 230, `ProgramRefused` 237–243; `holdspeak/services/errors.py`: `ServiceError` | Canonical class and public aliases; selected vocabulary values and identity where shared mutable objects matter; constructor/context compatibility |
| `holdspeak/web/routes/programs.py:_refused/_call` 105–121; `holdspeak/mcp/families/program.py:dispatch` shape catch 479–489 and name helper 537–548 | Broader HTTP base-class envelope versus concrete MCP catch, including by-name refusal returning existing spoken/no-start behavior rather than leaking a different exception |
| `holdspeak/services/program_service.py:runner` 891–896, `_held` 885–888, `default_program_service` 5625–5636; `holdspeak/services/program_runner.py:default_runner` 2386–2394 | Injected versus production default composition; same-object reuse and changed-object replacement; no split runtime ownership. Shared-rig injection alone is not default-factory proof |
| `holdspeak/services/program_service.py:text_apply/_apply_text` 4129–4440, `changed` 5022–5077; `holdspeak/db/programs.py`; `holdspeak/db/connection.py` | Existing preflight versus later-write boundaries, concrete refusal capture, context/suffix, held reset, final notification and tick ordering; preserve current commit semantics rather than infer atomicity from a lock |
| `holdspeak/services/program_runner.py` imports 52–55; `program_text.py:303–310` and `program_service.py:_budget` 5534–5544; same-directory `program_split.py:330–366` | Imported definitions versus shared object collaboration; reciprocal helper dependencies and existing lock-protected multi-operation coordination |

Initial test references are `tests/unit/test_program_service.py` (transition/refusal at 35–58, MCP authority at 117–163, name lookup at 311–327), `tests/unit/test_program_text.py` (dry run at 489–502, successful coalescing at 505–544, preflight refusal at 547–563), and `tests/integration/test_desk_programs.py` (actual HTTP refusal/context at 542–609 and text routes at 643–672). Existing helper `tests/integration/program_rig.py:314–334` injects a runner; it is not a runnable test or proof of production default identity. `tests/unit/test_program_family.py` tests Program ancestry, not the similarly named MCP family.

These inspected cases do not establish relocated alias identity, production factory/cache behavior or a late-refusal-after-write path. The future proof plan must name exact new assertions in suitable existing test homes: old/new class identity and catching, relevant vocabulary alias identity, real named-refusal transport, injected/default composition with globals restored per case, and a deterministic later refusal after an earlier successful write. Check stored state, error/context, held cleanup, notifications and ticks separately. Do not label a preflight refusal test as atomicity or partial-write proof. Inspection is not passing tests; collection/imports and the rig's real temporary Git/SQLite/processes require explicit assignment and [validation isolation](../VALIDATION.md#setup-and-isolation), with fake providers and no owner state.

### Readiness, rollback and stops

Discovery can finish with a bounded source-backed record and G51 still pending. An implementation brief needs accepted selected symbols/paths, caller/alias support, exact proof ownership and serialization with other Program service/runner/text lanes. Stop for unknown supported consumers or reflection compatibility, split class/lock/cache identity, hidden helper effects, a newly transactional promise or a move that only recreates reciprocal dependencies.

A future rollback reverses one coherent definition/import/alias change, preserving the one runtime owner and durable state; it does not undo external effects or erase partially written history. Keep old public contracts where required rather than duplicating definitions. No storage, authority, control-level, scheduling or concurrency redesign is proposed. Preserve [I16/I18/I19/I21/I22](../INVARIANTS.md) and the selected domain's behavior.

## HS-S53 destination ownership gate

**Contract/discovery plan only; no implementation task or exact new path selected.** The [source-checked consumer map](../STRUCTURAL-REVIEW.md#source-checked-appendix-send-and-destination-ownership) and [frontend target](../NEXTGEN-TARGET-PROPOSAL.md#feature-composition-above-shared-material) already identify the responsibility problem. This gate turns that diagnosis into a bounded output an implementation planner can use. Follow [Agent safety](../AGENT_START.md#authority-and-checkout-safety) and [HS-T00](../tasks/HS-T00-baseline.md); source-only characterization does not grant application/test or provider execution.

### Why a form move alone is insufficient

At pin `80b641fa41c7352280cfa52e933acf6dbe8d3857`, Settings' `Destinations.tsx:47` imports `accountChip` through the surface Send barrel, which re-exports the stateful `SendWell` module. That module restores pending commands at top level (`SendWell.tsx:84–107`), imports `ConnectionsPane.chipLabel` as a value (`43/245`), and lazily imports `Destinations.DestForm` (`66`). Moving only the form can leave those screen/store dependencies. These are inspected source edges, not a reproduced initialization failure or measured bundle cost.

`DestForm.setUpAccount` (`228–239`) also searches Settings DOM; changing its directory does not make that interaction host-independent. Settings and inline Send have different account-refresh/error/unmount behavior. Neither relocating code nor sharing a read hook may silently choose a new policy.

### G53 decisions and required contract output

Return one compact contract record in the existing [completion report](../COMPLETION_REPORT_TEMPLATE.md), not a new backlog. Record pending choices honestly:

1. **Select the actual structural claim:** retain the current collaboration with an explicit contract, make the narrow shared-form/warning repair, or also relocate generic Send composition. Retention may be the right result but must not be reported as removal of the dependency. The broader option affects more consumers/CSS/lazy boundaries and is not required by the narrow option. No arbitrary file-size target or new common framework.
2. **Name the dependency boundary before new filenames:** the one form and destination-warning policy may depend on lower account contracts/state presentation and public surface material, not on the Settings screen or stateful Send composition/barrel. Settings and Send consume that one implementation. A compatibility export must forward to the same owner, not duplicate form, held-command store or restoration. Type-only references, static value imports, dynamic imports and re-export paths must be labeled separately. Do not move account discovery/onboarding or document-specific adapters merely to satisfy a directory rule.
3. **Specify both host contracts:** retain existing draft/key knowledge; define the explicit account-setup action for Settings and an isolated inline Send host with no Settings DOM. Decide how focus/navigation preserves that draft and what happens when setup cannot open. The current inline-form test only proves Add opens without Settings or Send; it does not prove Set up account works in that state. Preserve host-specific freshness/error behavior initially unless G53 explicitly accepts a change; do not claim a shared hook is behavior-neutral.
4. **Inventory exact owned paths and compatibility consumers:** map source owner → required input/callback → consumers → proof for form, warning labels, account read, host navigation and send custody. Include public barrels, lazy entry, CSS and supported direct callers. Existing `features/channels/SendWell.tsx` is the update adapter, so a same-name move is not an ownership design. The selected new paths, aliases and supported-caller closure must be reviewed before implementation briefs are authored.
5. **Define proof of the claimed dependency improvement as well as parity:** for a repair, trace the selected form/warning closure after changes and show it no longer reaches `ConnectionsPane`, Settings' Destinations host or the stateful Send entry. Send may keep its present location under the narrow option, but its reused form/labels must no longer come from those screens. Preserve one shared send store and exact held request/target/body/preview custody across actual consumers. Do not claim general runtime isolation, whole-app compiler closure or performance gains from a lexical check.

### Bounded source and proof map

All paths below are **existing at the pin and read-only for this gate**. Line numbers aid rediscovery; current symbols control drift. No proposed production API name is treated as present.

| Concern | Exact source to inspect | Proof to specify, not a passing result |
| --- | --- | --- |
| Form, draft/key knowledge, host setup | `web/src/pages/cores/connections/Destinations.tsx`: `DestForm`, `setUpAccount`, `Destinations`; `web/src/pages/cores/connections/api.ts`; `ConnectionsPane.tsx` in that same directory: `chipLabel` | Settings add/replacement/park behavior; account-read failure versus absence; correct host setup and preserved mounted draft |
| Runtime warning/store dependency and inline host | `web/src/desk/surface/send/SendWell.tsx`: `accountChip`, `InlineDestinationForm`, `restorePendingCommands`; adjacent `index.ts` and `pendingCommand.ts` | Inline Add and isolated account setup; no implicit send; one store and unchanged unresolved-request/known-receipt behavior across compatibility entries |
| Destination save versus dispatch | `web/src/features/channels/channels.ts`: `wire.save`, `wire.send`; update adapter `web/src/features/channels/SendWell.tsx`; `holdspeak/channel_operations.py` | Save is not Send; fresh destination command versus retained send identity; update/document-specific history and owner/connected-agent/secret-write distinctions stay intact |
| Structural enforcement and current exception | `web/scripts/guard-architecture.mjs:75–113`; `web/src/desk/surface/contract.md`; `web/package.json` | A green guard is not this dependency proof. Its private-surface/roving loop skips outside `src/desk` and inside `src/desk/surface`; other global/CSS rules have different coverage. Define a targeted check for the chosen moved paths without weakening baselines or merely moving outside the fence |

Inspect these existing test homes as the initial proof references: `web/src/desk/__tests__/destinations.app.test.tsx` (failed-read/draft and Settings account setup at 188–223, provider-key/late-response cases); `web/src/desk/surface/send/__tests__/SendWell.test.tsx` (inline Add at 376–391 plus custody/reload cases); `web/src/features/channels/__tests__/slackDestination.test.tsx`, `resendProvider.test.tsx` and `SendWell.test.tsx` (channel identity/readiness and the separate update adapter). The final implementation/proof budget must select the exact cases and any missing host/closure case after G53 is resolved. These five inspected test homes are **not** an execution assignment, exhaustive compatibility proof or an invented new test harness. Existing typecheck/architecture scripts are source-defined in `web/package.json`; future invocations follow [Validation](../VALIDATION.md#setup-and-isolation), current instructions and the accepted file budget. Nothing was run for this gate.

### Exit and stop conditions

The gate may finish with a source-backed contract and pending owner choices; that does not unlock code. A ready implementation brief must include accepted G53 scope, named existing/proposed paths, exact caller/test ownership, the host behavior decisions and a feasible direction check. Stop dependent expansion for unknown supported consumers, hidden module side effects, a navigation policy invented during relocation, duplicated custody, new credential/dispatch authority or a guard that cannot measure the claimed change.

A future rollback must reverse the cohesive owner/import/host/compatibility change without leaving a split store or form; preserve pending command identity and all actual send history. It cannot undo an external effect, expose secret values, or turn unknown outcomes into safe retries. No backend/storage/credential/command protocol change is proposed. Preserve [I10/I16/I18/I21/I25](../INVARIANTS.md) and current domain authority throughout.

## Proof, rollback and stops

Require behavior parity plus the intended structural improvement: fewer inappropriate dependencies, one owner for the selected responsibility, unchanged public wire/admission/observation, and a short task-local context map. Static import counts alone do not prove runtime independence or feature benefit.

Preserve [I01/I08/I09/I13/I14/I16/I18/I23](../INVARIANTS.md) as applicable, and the task's actual transaction/observer constraints. No schema migration, new composition root, global dependency-injection platform or safe-deletion claim follows. Roll back the cohesive caller/wiring/query change without discarding durable rows. Stop on unresolved compatibility, doubled service instances/events, changed transactions, unproved behavior or a proposal that merely redistributes lines.
