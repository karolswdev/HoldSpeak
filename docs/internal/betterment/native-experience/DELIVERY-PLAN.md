# Delivery plan: a stronger desktop framework in React

Proposed implementation sequence from the 2026-10-23 research. The owner has
settled the stack. These work packages are not implemented by publishing this
plan. They preserve the current fast cycle, public control API, runtime
protocols and Workbench meets Pop!_OS direction.

## Planning checkpoint — owner correction, 2026-10-23

**DRAFT — UNCHECKED, awaiting Muad'Dib.** Finish the bounded repairs already
underway; refine the strategy before starting further implementation. The
owner clarified that this work should have continued the plan and strategy,
not immediately turned the audit findings into code changes.

[The refined strategy](STRATEGY.md) makes the missing choices explicit. Its
[adversarial review](checks/strategy-adversarial-2026-10-23.md) found three
material gaps: same-resource instance/lifetime identity, command scope and
selection authority, and separate read/edit/operation state with real task
and craft proof. These must be designed in the first packet; another list
of component extractions would leave those decisions unresolved.

| Sequence | Work to settle | Concrete output and limit |
| --- | --- | --- |
| Now: design refinement | Recommend the identity/lifetime, command-scope and state-ownership choices in STRATEGY; declare actual provider/Git operations; choose complete owner jobs. | One coherent decision table, resource/preferences/Thought state canvases, keyboard/focus/return stories and named evidence gaps. This is design work, not a new implementation lane. |
| First proposed pilot | Two supported resource-browser locations, file inspection, navigation/return, selected command targets and refused/stale reads. | Existing RepoWindow/provider plus the same proven seam in Components. Read/navigation proof does not certify general filesystem operations or the Git mutation job. |
| Counterexample before broad adoption | Settings dirty/revision/retry and active Thought caret/IME/voice/undo. | Challenge ownership with unlike consumers before generalizing. Share smaller behaviors if a common controller requires unrelated flags. |
| Complete transition job | Project or 1:1 preparation through source inspection, scoped Ask, retained material, delegation/result and return. | Actual resource/session/operation identities survive the app boundaries. The owner scenario and fixture must be named before execution claims. |
| Compatible adoption | Collections, preferences, conversations and retained-work surfaces. | Per-consumer adoption and specialized exceptions in existing records; appearance and real task acceptance stay distinct from technical checks. |

The implementation homes below remain useful source maps. Their original
package numbers are not a build order or permission to start them. Keep the
existing fast delivery cycle when a later design is settled; this refinement
adds no 47-stage gate.

## Application-model correction

The owner's clarification makes desktop applications the architecture unit.
The [application model](APPLICATION-MODEL.md) is now part of this sequence:
per-window navigation/history/selection, contextual commands, resource identity,
view modes, editing and cross-window transfer. An explorer-style workflow is
an acceptance workload alongside Settings; preferences alone do not prove a
desktop framework. This changes the first checkpoint below without authorizing
a new filesystem product or unsupported operations.

## Investment priority

Prioritize coherent desktop application behavior and complete, polished views.
The first wave includes an explorer-style resource workflow alongside daily
preference, sourced-Ask and person-preparation work. The resource workflow
proves application contracts that a form alone cannot. Work on the
framework and a real consumer together. The Components reference renders
that same pattern using fixture-backed services; it does not copy the face.

Keep useful existing pieces: Signal Button, gadgets, DeskMenu,
WorkbenchSelect, ComposerWell, ReadingDocument, SurfaceSplit, reading-end
anchoring, durable drafts, the command registry, live compositor and the
microphone/audio-floor machinery. A new package is justified by an observed
missing capability, not by a claim that the old stack cannot look good.

## Audit-driven scope

The [use-case audit](USE-CASE-AUDIT.md) and [inventory snapshot](USE-CASE-INVENTORY.json)
reconcile the declared product corpus. Use their behavior gaps and affected
families to order implementation. A merged recipe is not evidence of native
interaction quality. Each delivery brief selects a real job, its relevant
shared behavior contracts, interruption/recovery cases and existing evidence;
it does not create a speculative requirement for every button combination.

## Corrections from the 47 adversarial reviews

The [review reconciliation](adversarial/SYNTHESIS.md#delivery-order) now precedes
shared extraction: repair the reproduced Settings leave/return conflict and
high-cost capture/operation branches, then prove the resource workload with
Components and a real consumer. Preserve existing caret insertion, Today/Needs
projection, agent results, Send custody and domain-specific outcomes. Review
identities and active routes before extracting from a retained component.

Use the [individual records](adversarial/README.md) for each affected job. This
is proposed work, with concrete acceptance challenges; the 47 reviews and 204
challenges do not close betterment recipes or create another approval queue.

## Candidate implementation homes and proof

Each row can require several small PRs; one PR handles one concern, a few
files, and its real consumer. Targets name existing integration homes, not
exclusive ownership or an instruction to rewrite the entire file. Line
anchors belong to [the baseline audit](CURRENT-STATE.md) and may drift.

| Order | Concrete change | Existing homes | Completion evidence |
| --- | --- | --- | --- |
| 0 | Define and prove the application/view contract in an existing registered repository or resource browser, with a second window instance. | Existing application manifest, object-window host, `RepoWindow.tsx`, `repository.ts`, ObjectList, command context and Hand | Independent location/history/selection per window; actual file open/read through existing APIs; consistent keyboard/context-menu targets; supported in-place edit and cross-window handoff; stale/read-only/refused outcomes. Use actual provider capabilities, not fake file operations. |
| 1a | Establish a reproducible local interaction baseline and close the folded-Room test gap. Keep inline tabs and folded menus equally reachable in the helper. | `tests/e2e/test_room_glass.py`, `glass_infra.py`, existing frame/reference browser cases; local profiling recipe | A 393px Room actually opens History through the menu, while desktop tab behavior remains; no assertion removal. Record production-build input/drag traces for the named scenes. Attribute unrelated tape reds separately. |
| 1b | Define head allocation and focus as one frame contract. Preserve fixed right controls, yielding title, wings, task verbs and a deliberate drag region. | `DeskWindow.tsx`, `window-chrome.css`, `surface/wings.tsx`, `stripMenu.tsx`, existing keymap/compositor | Pointer and keyboard operations, fold/unfold in both directions, focus return, long titles, canceled gestures and multiwindow activation. Retain the existing mounted-front authority and 1440/393/280 head checks. |
| 2 | Build the first complete production preference pattern with typed edit-state ownership and a fixture adapter. Start with the You category; keep the current field semantics, revisions and save policy. | `SettingsCore.tsx` merge/install/project-pending helpers, `settingsPrefs.tsx`, public surface species, `design-reference` | Same pattern runs in Settings and Components. Dirty/invalid/pending/rejected/retried/saved, external-revision conflict and newer edits during save all preserve work. The real window and reference receive paired visual, keyboard and spoken-input proof. |
| 3 | Share the sourced-conversation composition and its explicit controller boundary. Keep requests, drafts, operation receipts and source identity distinct. | `AskPanel.tsx`, `ComposerWell.tsx`, `ReadingDocument.tsx`, `useReadingEndAnchor.ts`, existing Ask services and reference | Streaming follows only when already at the end; text selection and older reading stay put; retries use the captured request and preserve a newer draft; source inspection returns correctly; mic and IME do not accidentally submit. |
| 4 | Extract a reusable collection/detail pattern from real People behavior; then adopt it in one other suitable collection. | `PeopleCore.tsx`, `SurfaceRows`, `SurfaceSplit`, roving rows and object adapters | Stable selection through filter/refresh/reorder, narrow Back, correct load/error/empty states, focus restoration and accessible row identity. A second production consumer proves useful reuse. |
| 5 | Converge other active surface families through those patterns and explicit exceptions. | Existing application manifest and adoption inventory; Meetings, Automations, Agents, Activity/Memory/Projects, object pullouts | Record actual patterns used by each real consumer. Keep terminals/editors/canvas/media layouts specialized where needed; retain common frame/control/input floors. Do not count parked compatibility routes as new adoption. |
| 6 | Apply measured rendering improvements and optional browser enhancements. | Current compositor/store selectors, React build configuration, existing menu placement and capabilities | Demonstrated before/after traces with unchanged focus, selection, voice and recovery. Compiler, virtualization, containment, Activity and ViewTransition each need their own reason and fallback; none is a prerequisite for a useful first wave. |

A native-presence repair is a separate bounded item. Inspect route/auth,
WebView readiness, sizing/transparency and activity transitions; provide a
visible dismiss/disable path and a real native-window screenshot. Keep the
owner's saved disabled state. Do not auto-enable the panel as part of a
React upgrade or this research. Its current renderer is not certified fixed.

## Pattern contracts

A preference pattern owns arrangement, grouping, validation presentation and
visible edit/request state. A typed adapter supplies fields, domain validation,
read revision, save operation and authoritative result. Reuse the current
Settings merge helpers; do not introduce a generic serialized form language
or replace backend concurrency rules. In-flight requests carry their captured
snapshot, while current edits remain separately owned.

A conversation pattern owns its reader/composer relationship, source actions,
selection presentation and scroll-follow policy. Its adapter supplies turns,
draft, request state, engine/egress facts and actions. The existing Ask
controller retains its abort identity and operation authority. A collection
pattern owns collection/detail reflow and focus/selection restoration; its
adapter supplies stable object ids and feature actions.

The frame owns the window head and scroller contract. Prefer explicit slots
and allocation rules over reaching into sibling feature classes to negotiate
space. Keep one animator per element/property so press feedback, arrangement
and content transitions do not compete for the same transform.

Evolve existing component CSS toward clear ownership. Cascade layers are an
option for an isolated species, not a blanket wrapper around old CSS:
unlayered normal rules outrank layered rules, and important rules reverse
layer priority. Migrate a whole component's material/states with its consumers
before parking obsolete overrides. See the
[CSS cascade rules](https://developer.mozilla.org/en-US/docs/Web/CSS/Guides/Cascade/Introduction).
No mass class renaming, import cleanup or all-at-once stylesheet rewrite is
needed to start improving the product.

## Local measurement protocol

No performance measurements were collected by this research. Collect a named
scene baseline before proposing new timing or resource budgets. Earlier
provisional numbers were not adopted acceptance thresholds. Existing canon
guards remain; this protocol adds no merge gate or owner budget.

| Property | Observation and method |
| --- | --- |
| Direct feedback | Measure input-to-paint for an ordinary command in the foreground production build, idle and with background work. Record the local acknowledgment separately from completion of the operation. |
| Discrete interaction responsiveness | Record representative-session latency and its instrument/browser support; retain browser traces. A discrete interaction metric does not establish continuous-drag smoothness. |
| Drag/resize | Compare frame work with the measured display refresh period. Inspect frame intervals, forced layout and main-thread/paint work; rAF timing alone is not proof of displayed smoothness. |
| Work preservation | No lost or overwritten draft, selected range, captured request or retained voice on the tested interruption/retry/refresh path. Assert exact values and authoritative outcomes. |
| Layout and access | Useful at 1440 and 393, plus constrained floating-window widths and head stress poses. No hidden action, clipped label, overlapping hit ownership or dead-end keyboard path. Check text zoom and reduced motion. |
| Cost | Record load/parse, React renders/commits, layout/paint, DOM count and resource use for 1, 5, 10 and 20 windows. There is no established memory or bundle-size budget yet; derive one from measured scenes. |

Record browser and engine version, OS, viewport, window sizes, DPR/display
refresh, production/profiling build identity, data volume, warm/cold cache and
backend/provider conditions. Include an animated Desk environment where the
owner uses one; an empty static page can hide real contention. Use local
artifacts, not a telemetry service or network beacon. Profile only the scenes
that justify a change; do not add an instrumentation subsystem to every face.

Firefox is the owner's primary browser and an explicit validation target.
Chromium supplies existing automation and richer diagnostic tools. Add WebKit
coverage for the same core tasks, while naming that Playwright WebKit is not
a proof of installed Safari or the native WKWebView host. Manual IME,
VoiceOver/NVDA and actual native-host observations remain distinct evidence.
Do not relabel automated axe success as a screen-reader usability pass.

## Enablement, adoption and exceptions

The paved road is a production pattern, a public API, a matching reference,
and a short author recipe. Update the existing surface contract and author
map as the implementation lands. Add guards only after that road exists;
recurring exceptions are input to framework design. Frame, command and
microphone authority remain centralized, while domain validation and write
results stay with each feature/backend.

Track distribution (pattern exists), adoption (named live consumers), and
outcome (the owner completes the job and likes it) separately. Useful
measures are the number of task-specific escape hatches, repeated focus or
lost-draft defects, failed/retried interactions, time to implement a second
consumer, and the owner's feedback tied to exact build/window/state. None is
a substitute for the actual task or a new merge gate.

The existing feedback engine should capture the screenshot and semantic
pattern state together: selected object, active input, sanitized field values,
request/draft status and scroll context. Reuse its redaction and configured
transcription path. Do not copy secrets, whole runtime stores or hidden
transcripts into a new diagnostic collector. Pattern adapters can expose
bounded state to the current collector when DOM inference is insufficient.

## Delivery discipline

Use the current CLAUDE fast cycle: scoped worker briefs, quick check and
relevant screenshots, immediate PR merge on green, deploy exact main, full
tape and Astra review afterward, fix findings forward. Face work gets its
canvas in the existing library material. The owner judges appearance on the
running Desk; that does not add a routine owner approval gate.

All automated checks use the shared lock and isolated HOME. Native/voice
walks use the existing capability-verifier skill and `graph_walk.py`, one
case per invocation; no walk writes into the owner's desk and agents never
run `tests/e2e/test_metal.py`. Preserve the explicit off state of native
Presence. On a real desk regression, follow the existing last-working-head
recovery rule; do not add another delivery framework.

First checkpoint: application/view behavior in an explorer-style resource
workflow, plus the production preference consumer and their shared reference
models. Prove independent window state, command targets and supported transfer
as well as preserved edits, coherent layout and keyboard/voice behavior. Add
a local timing baseline and the owner's live visual feedback, then proceed to
Ask, People and other application families.
