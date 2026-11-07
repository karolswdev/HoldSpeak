# HS-S12 · Open the intended work through an explicit readiness boundary

**Conditional design and task plan, not implementation authority.** Epic: [HS-E10](../epics/HS-E10-context-and-navigation.md). D12/G-OPEN remains pending. Pin: `80b641fa41c7352280cfa52e933acf6dbe8d3857`. No application or tests ran while authoring.

## Outcome and existing behavior

Cold arrival, a warm Desk action and a return from recovery should reveal the intended application and exact work without losing scope, drafts or owner control. Simplify the mechanism that enables this job, not every asynchronous operation in the product.

There are different mechanisms with different purposes:

- The application manifest and literal lazy imports are static identity/code loading. Chunk recovery is independent of navigation registration.
- `shell.ts` owns mutable per-key opener callbacks, transient pending opens and a single staged route-arrival slot. Registration currently drains same-key pending requests backwards; staged storage retains only the latest arrival.
- `SurfaceWindows` owns recovery admission, clearing or temporarily withholding persisted windows, reveal when pressed, staged consumption and a readiness marker. Removing its registration effect without assigning those jobs elsewhere would change behavior.
- Project-proposal handoff carries project, proposal and repeated-request identity. It deliberately preserves an update draft and does not Save or Confirm. It is not equivalent to opening a project by name.

Evidence: [navigation mechanisms](../NEXTGEN-JOURNEYS-AND-NAVIGATION.md#1-the-frontend-really-has-two-separate-mechanisms), [startup ordering](../NEXTGEN-TARGET-PROPOSAL.md#startup-navigation-ordering-before-retiring-registration-1900-review), and [exact proposal handoff](../NEXTGEN-JOURNEYS-AND-NAVIGATION.md#oversight-to-project-handoff-reveal-the-work-without-saving-or-accepting-it-1800-follow-up). These are source traces, not measurements of failure frequency or bundle cost.

## G-OPEN choices and proposed bounded branch

The following branch is fully planned only after its local policy and feasibility checks are accepted:

1. **One authority for opening built-in surfaces.** Resolve application identity and aliases from the existing manifest, then use the existing Desk state/window action. Replace per-key opener callbacks with explicit transient readiness/admission/reveal state. Do not add a second registry, callback bridge or another authoritative window model. Exact new field/helper names are proposals, not existing APIs.
2. **Keep two intent roles explicit.** Proposed: distinct transient `openSurfaceWhenReady` requests replay FIFO among requests admitted in the current mode (recovery doors can pass deferred normal requests), while route handoff remains one latest staged arrival and is consumed after the transient startup flush, as the existing staged phase is. This deliberately changes reverse transient replay; it is not a claim that all navigation becomes globally latest-wins or that FIFO command application guarantees final cross-family focus. Conductor currently schedules a later restore. Preserve/characterize that behavior in this branch; a deterministic final-focus requirement needs an explicit additional adapter contract before implementation. Different transient destinations must survive, and a staged arrival can intentionally be final. Alternatives are retaining the old behavior or adopting one globally latest arrival, which can discard separate requested opens. The owner must choose before implementation.
3. **Storage failure changes reliability, not the chosen in-session ordering.** A proposed single in-memory fallback represents that same staged arrival, not a new queue. Keep the latest staged intent during the current runtime if sessionStorage fails. A newer in-memory staged value must supersede an older successful stored value; a later successful stage must replace a stale fallback. Define read/remove failure and suppress repeated consumption on host remount. Do not promise exactly-once across reload when storage cannot be updated/removed; this is not durable domain work.
4. **Preserve lawful recovery.** Only the existing Setup/Settings/Engines recovery doors and their applicable aliases are admitted in recovery-only mode. Do not consume normal staged arrival there. Preserve clear-on-first-use versus retain-off-glass/reveal-on-press behavior. A direct store call is not permission to bypass admission.
5. **Retain purposeful distinct mechanisms.** Keep lazy loading/chunk recovery, mounted-read/layout readiness, the Dock-only compact Dictate first-answer behavior and the existing one-shot project-proposal handoff. This slice does not combine all intents into a generic queue or erase every lifecycle callback. Registration retirement refers specifically to the opener map/per-key registration sites.
6. **Compatibility before deletion.** Map Conductor and parked Drawer behavior to their actual current owners and check all supported callers/fallback contracts before removing an export. An unexplained key or external-support contract stops that removal. Parked does not prove unreachable; arbitrary test callbacks do not automatically establish a supported extension API either.

If the owner selects a different ordering or chooses to retain registration, revise this branch rather than implement a hidden default. Target-level proposal continuity and its proof remain valuable independently of opener removal. No unrelated Program/decision/People task is a prerequisite.

## Target ownership

Keep manifest identity/aliases in `applications.ts`; preserve `composeApplicationScope`, including default-wing and requested-target composition. Preserve the host's alias-after-canonical precedence, including old names redirected away from parked rows; use own-entry lookup for arbitrary keys rather than object prototype properties. The shell remains the public compatibility boundary for existing callers. The existing frontend compositor operation remains the single local writer of window identity, scope, placement and fronting; the existing hub window service remains cross-browser authority and local workspace remains first-paint cache. Do not replace that relationship. The host reports its explicit lifecycle/admission mode and renders that state rather than registering one callback per application.

The direct-state branch must locate off-glass reveal and readiness under one owner before cutover. A new callback registration named “navigation controller” would not meet the simplification. The existing shell pending array may retain transient requests; the host publishes its explicit mode and invokes one bounded flush, not per-key callbacks. Added readiness/reveal/pending state must be transient, not serialized as a domain task or stored as a second window list. No new generic navigation framework, event bus or retry engine is proposed.

Do not change every caller's Boolean/fallback behavior by assumption. `openSurface`, `openSurfaceWhenReady`, `openSurfaceOr` and staged route arrival have distinct contracts. Explicitly document what handled, deferred, disallowed and unknown mean at their existing interfaces; an accepted/deferred intent is not a mounted-window receipt. Preserve fallback behavior only where it is still supported and do not route-reload a recovery card as an accidental replacement.

The migration should be one logical cutover, with unused testable state/resolution pieces prepared first if useful. Never run old callbacks and a new dispatcher as two effect owners. No intermediate task is permission to deploy a mixed system.

## Acceptance matrix

All new cases below are proposed until implemented and run.

| ID | Required proof |
| --- | --- |
| C12-01 | Canonical keys and aliases resolve to the same existing window with exact composed scope; unknown/unsupported keys have an explicit bounded result |
| C12-02 | A then B for the same window before readiness has the accepted final scope; distinct transient keys are retained under the accepted policy |
| C12-03 | Staged route arrival precedence is explicit; success A → failure B and failure A → success B retain the latest current-runtime slot, not an older stored value or transient FIFO accidentally |
| C12-04 | Invalid stored JSON/key/scope and storage read/write/remove failure do not crash startup; normal host remount cannot replay an already-consumed intent in the same runtime |
| C12-05 | Recovery admits the exact doors/aliases, retains the normal staged arrival, and distinguishes clear-first-use from preserved-off-glass windows |
| C12-06 | Pressing an admitted alias reveals a retained hidden window and applies scope once; leaving recovery restores the intended existing windows |
| C12-07 | Host mount/unmount/remount and readiness transitions do not duplicate open, consume too early or let stale lifecycle cleanup clear a newer host's state |
| C12-08 | One scoped Meetings window retains identity/geometry; People object and live-meeting redirects in the existing store still apply |
| C12-09 | Conductor behavior and any retained Drawer compatibility still use their actual owner; dispatch order is not mislabeled final focus order; no silent unsupported-key drop or second registry |
| C12-10 | Only Dock-origin compact Dictate may take the existing first-answer path; menu/shortcut/route behavior stays distinct. No real recording is required for fixture proof |
| C12-11 | Lazy imports and failed-chunk recovery remain; mount-read/layout readiness is not removed with opener registration |
| C12-12 | Needs You opens the exact project proposal, including repeated same-target request; unprojected proposals retain their Meeting Review path |
| C12-13 | Pending/failed update Save and newer draft survive proposal navigation; navigation initiates no extra Save, Confirm, publish or Send. Existing in-flight Save is not cancelled |
| C12-14 | Cold/warm/recovery and repeat-target outcomes are observed in a safe browser, including focus/reveal and compact layout; a readiness marker alone is not successful target rendering |

Unavailable or already-settled proposal behavior must be characterized rather than invented. Preserve the current transient target lifetime (no reload persistence) unless separately accepted. Navigation can update Desk/read-tracking state; “no autosave” does not mean zero writes of any kind.

## Exact source, owned paths and task handoff

Existing paths below refer to the pin and must be rechecked. New fields/helpers/cases are proposals, not existing APIs. The focused text-only value-import closures found no static return path to shell from Desk, Conductor or Drawer stores; this supports synchronous dispatch without an added async drain. It excludes dynamic/type-only edges, assets/package internals and runtime initialization. Full supported-caller closure and current build/test proof remain task01/04 gates.

| Existing path | Exact responsibility | Ownership |
| --- | --- | --- |
| `web/src/desk/shell.ts` | Public signatures 11–105; pending/staged semantics; first-answer hook; Boolean/fallback wrappers; partial `__resetSurfaces` | Task02/03, serialized. Preserve origin union `dock/menu/route`; no invented shortcut enum |
| `web/src/desk/applications.ts` | Manifest 73; surface projection 703; aliases 805; scope composition 818; `applicationForAction` 829 | Read-only identity authority; not all rows are active surfaces |
| `web/src/desk/store/types.ts`; `web/src/desk/store/compositorSlice.ts` | Surface actions 385–396; slice type/initialization 273–302; `openSurfaceWindow` 537–577; dynamic shell back-edge 415–421 | Task02/03. Reuse existing open/redirect/fronting; no second canonical window model |
| `web/src/desk/store.ts`; `web/src/desk/store/index.ts`; `web/src/desk/store/workspaceStorage.ts`; `web/src/desk/compositor/hubWindows.ts` | Store composition 12–18; explicit serialization 292–315/374–432; hub transport's specific window fields | Read-only dependency/persistence checks. Keep new state outside persisted/cache/hub payloads |
| `web/src/desk/components/SurfaceWindows.tsx` | Nonparked rows/lazy hosts 61–76; recovery keys 94; waiting/paint/registry mode 110–179; host slots | Task03. Move admission/reveal ownership explicitly; keep lazy and read/layout behavior |
| `web/src/desk/DeskApp.tsx`; `web/src/App.tsx` | Combined setup/read and keyed host choice 155–178/226–244/317–338; committed staged-route effect 20–45 with search preserved | Read-only. Do not conflate data-settled, navigation-ready, loaded chunk or rendered target |
| `web/src/desk/conductor/ConductorWindows.tsx`; `web/src/desk/conductor/store.ts` | Registration 14; `CONDUCTOR_KEY`, `openConductor`; delayed restore 116–123 | Host editable task03; store read-only named owner. Delayed final focus is an explicit limit |
| `web/src/desk/drawer/DrawerWindows.tsx`; `web/src/desk/drawer/store.ts` | Parked `open-project-drawer`, project-scope check; `openDrawer` | Host editable task03 if compatibility retained; store read-only. Ordinary project opens still target Room |
| `web/src/desk/chair/ChairDesk.tsx`; `web/src/desk/chair/chairWindows.ts`; `web/src/desk/components/window/Dock.tsx` | First-answer hook 143–145; compact branch 235–238; fresh launch after restore/focus 559–571/621–628 | Read-only preservation. Do not statically import Chair into shell: a source return path through NeedsDrawer/openObject exists |
| `web/src/desk/openObject.ts`; `web/src/desk/needs/NeedsDrawer.tsx`; `web/src/features/project-room/ProjectRoomCore.tsx`; `web/src/features/project-room/update/useUpdateController.ts` | Exact proposal request/event 98–109/145–150; producer 85–92; consume/reveal 2104–2275; stepAside 191–200 | Read-only target/draft/consent boundary; no new proposal queue |
| `web/src/runtime/freshBuild.ts`; `web/src/features/project-room/roomReads.ts` | Failed lazy-chunk recovery; mounted read/late-slot placement | Read-only; neither mechanism is the opener registry |

V12 names every initially owned test target, impacted compatibility seam, existing browser node and proposed browser file. No new fixtures are planned. Extra callers/files discovered by the current closure require a bounded ownership amendment before deletion. Historical parked tests are not silently counted as passing or promoted to active requirements.

[HS-T00](../tasks/HS-T00-baseline.md) → [HS-T12-01](../tasks/HS-T12-01-contract.md) → accepted G-OPEN → [HS-T12-02](../tasks/HS-T12-02-dispatch-state.md) → [HS-T12-03](../tasks/HS-T12-03-host-cutover.md) → [HS-T12-04](../tasks/HS-T12-04-verification.md). Use [V12](../VALIDATION.md#v12-focused-navigation-verification).

## Rollback and stops

No wire/schema/data migration is intended. Reverse a reviewed cohesive dispatcher/host/test patch, not only one side of the cutover. Retain the same persisted window model and staged-key compatibility. Reverting restores previous ordering/registration limits; disclose that. Never clear a user's windows, drafts or storage merely to make tests pass.

Stop for unresolved ordering, undiscovered callers, unsupported legacy/extension assumptions, an unassigned visibility owner, a new import cycle, dual dispatch, broadened recovery admission, changed Save/Confirm authority or a need to replace the proposal handoff. Keep the useful preservation proof even if removal is deferred. Preserve [I16/I17/I18/I21/I25](../INVARIANTS.md).
