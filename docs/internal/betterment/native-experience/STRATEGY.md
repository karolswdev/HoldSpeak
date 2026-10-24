# A coherent desktop application framework

**DRAFT — UNCHECKED, awaiting Muad'Dib.** Astra, 2026-10-23.
This is a proposed strategy refinement, not an implementation instruction or
a claim of owner acceptance. It is governed by the Constitution's Seven
Tenets, UX-CANON and the current fast cycle.

## Definition before implementation

The owner's direction is to master the React-based product world: research
and workflows become a coherent design proposal, then a delivery plan.
The [proposal](DESIGN-PROPOSAL.md) now defines the application model,
interaction decisions and visual grammar. Its [47-family map](design-proposal/WORKFLOW-MAP.md),
[seven whole jobs](design-proposal/JOURNEYS.md) and [paired canvases](design-proposal/CANVASES.md)
make that definition reviewable. The [derived delivery plan](DELIVERY-PLAN.md)
connects each family to a bounded package and its real task proof.

This is design work. The bounded repairs are [recorded separately](checks/repair-closeout-2026-10-23.md).
The proposal does not promote the framework to delivered, close the audits,
or start another code lane.

## The changed experience

The target is a pleasant desktop for a senior architect's daily work: inspect
resources, prepare a review, write and speak, ask about sources, delegate,
read results and return to the original work without reconstructing context.
The application should make the next useful move apparent and preserve what
the user was doing when something else finishes or fails.

The React stack and Workbench × Pop!_OS direction are settled. The common
application behavior, composition and craft are not yet proved. PR1428's
material work, the component catalogue and subsequent bug repairs are useful
parts; they do not establish a coherent application framework or delight.
The [47 reviews](adversarial/README.md) supply counterexamples and boundaries,
not 47 rewrite instructions or 204 executed acceptance tests.

The strategic choice is to develop a small application/view contract through
real jobs, then share the compositions those jobs demonstrate. A cosmetic
pass alone leaves behavior inconsistent. A universal application controller
would force unrelated lifetimes and permissions into one abstraction.
Independent app rewrites would reproduce today's drift. The proposed middle
course costs more design effort before the first extraction, but makes its
usefulness falsifiable through a second, different production consumer.

## Strategic choices developed in the design proposal

These recommendations are expanded into D1–D10 of the [design proposal](DESIGN-PROPOSAL.md).
They have explicit counterexamples and remain proposed, not new canon.

| Decision | Proposed choice and reason | Counterexample or revisit condition |
| --- | --- | --- |
| Instance identity | A resource browser can open two locations of the same registered repository in separate, stable window instances. Keep application key, window id, qualified resource id and mutable location distinct. Existing singleton decisions, including the one Ask window, remain. | One window per repository with tabs is less initial persistence work, but does not demonstrate the independent-window job. Do not turn this pilot into permission to duplicate every app or document writer. |
| Lifetime and ownership | The compositor owns window activation and geometry; a window/view owns location, history, selection, focused row and scroll. Existing document services own saved content and draft/write authority. Existing domain services own background work and receipts. Closing a view is not an implicit cancellation policy. | Minimize, unmount, reload, dirty close and operation Stop have different meanings. State preservation must survive each relevant boundary without creating two writers for one document. |
| Command scope | Classify commands as view-local, Desk-global or explicitly targeted. A view command receives its originating window, resource/selection, focused control and availability. Equivalent menu, shortcut and context-menu invocations use that same scope. | A global navigation command and an explicitly configured voice macro must not silently inherit the front view's selection. Preserve macro execution policy versus contextual voice proposals and their confirmation rules. Native text-editing commands remain with the input/editor. |
| Read, edit and operation state | Keep provider read state, current draft, captured request, retained operation and domain outcome separate. Render their facts through existing read/receipt patterns. | Stale retained content is not an empty collection; a stopped capture is not proof of a saved Meeting; a cancelled wait is not proof of an absent delivery. No universal status enum or second operation ledger. |
| Common layout | Share deliberate regions and behavior: window head, contextual commands, optional navigation/inspector, work area, pane scrollers and outcome area. Compose distinct resource, document, conversation, preferences and live-work patterns. | A terminal, rich editor or media view must retain its input and rendering model. Common chrome must not force it into a card stack or a generic form. Narrow layout must preserve the same job. |
| Golden reference | Components exercises the same production pattern/controller boundary through isolated fixture adapters. Each example exposes its real states and links to its production consumer. | A separately copied specimen, or reuse of only Button and tokens, cannot demonstrate shared behavior. Keep an example labelled experimental until the production seam exists. |

React preserves component state according to render-tree identity. That is a
mechanism to use deliberately, not a substitute for retained document or
operation ownership. Derived state should also avoid unnecessary effect-driven
copies. These recommendations follow the official [state identity guidance](https://react.dev/learn/preserving-and-resetting-state)
and [effect guidance](https://react.dev/learn/you-might-not-need-an-effect);
their use here is an architecture inference, not evidence that HoldSpeak has
already implemented the contract.

## Convergence that respects the whole job

Use the existing W/F/S/N/C/E/V/T/X/A/O/K/P axes and inventory crosswalk in
[the audit](USE-CASE-AUDIT.md). Do not introduce another capability catalogue.
For each work package, name the active consumer, the behavior being shared,
the domain authority it retains, and a counterexample from another family.

| Contract or composition | First stress case | Different consumer that can challenge it |
| --- | --- | --- |
| Window/view identity, selection and command context | Two repository locations with independent history and selected resources | Active Thought workspace: document identity, caret and editor commands must remain independent of Desk selection. |
| Editing and retained request/draft | Settings edit, external revision, refusal, newer edit and Retry | Thought document with IME, voice at the caret and undo. Share the input/ownership principles; do not force the Settings writer onto CodeMirror. |
| Collection/detail and honest reads | Repository tree and file inspection | Meetings or People: stable object identity, filtering, read failure, narrow Back and return. They need not inherit filesystem path navigation. |
| Conversation and source handoff | Ask from a selected resource, inspect a source, retain the conversation or save a Note, return | A real specialized conversation after its active route and scope are verified; a second rendering of Ask in Components is a fixture consumer, not a second production app. |
| Background work and outcomes | Meeting Stop/save and project-update run/delivery | Agent result or Automation occurrence: retain actual run/result/receipt identity and specialized cancellation/egress rules. |

Not every proposed extraction will survive. If a second consumer requires
many unrelated flags or obscures its domain rules, keep the controller local
and share the smaller behavior or composition. Existing Thought, Room,
Today/Needs, Send custody and agent-result contracts are starting points,
not things to replace because the audit found an adjacent defect.

## A falsification sequence, not a march through 47 windows

1. **Review the actual proposed world.** The [proposal](DESIGN-PROPOSAL.md)
   chooses identities, ownership, scoped commands, state transitions,
   selection/navigation, editing, source return and reference behavior. The
   [canvases](design-proposal/CANVASES.md) show the resource and preferences
   compositions, active Thought/Ask counterexample, retained Meeting work and
   Components, followed by delegation/result, follow-through/Send, readiness
   and terminal/feedback return scenes. The [map](design-proposal/WORKFLOW-MAP.md) traces all 47 families
   to journeys and packages. This definition is now present, not a future
   deliverable; provider and owner evidence remain distinct open conditions.
2. **Prove one resource job after the design is settled.** In RepoWindow,
   open a supported file through the existing provider, navigate and return,
   change the active window, and survive a stale/refused read without losing
   selection or location. Declare file-read/write and Git branch/stage/commit
   support separately from filesystem copy/move/drop. Initial navigation/read
   proof does not certify the Git mutation job or a general OS file manager.
   Components runs that same proven seam with fixtures.
3. **Challenge the boundary with Settings and Thought.** Settings stresses
   dirty/revision/retry semantics; Thought challenges editing, selection,
   voice, IME and undo. This precedes a broad collection migration. Ask/source
   handoff follows as the complete asynchronous reading and return job.
   A faster Ask-first alternative is valid, but leaves rich input ownership
   unchallenged; choosing People first mostly confirms another collection.
4. **Adopt by compatible behavior and complete journeys.** Move appropriate
   collection/detail, preferences, conversation and operation consumers in
   small changes. Keep specialized exceptions explicit in the existing
   surface contract. A second useful production consumer earns an extraction;
   a passing catalogue does not earn whole-product adoption.

One proposed cross-application proving journey is preparation for a project
review or 1:1: open the project, inspect its source Meeting/Note, ask a scoped
question, retain useful material, delegate an explicit task, read its actual
result, and return to the original source. This tests the transitions between
apps that isolated window screenshots cannot. The exact owner scenario and
fixture must be named before calling it an executed job.

## Craft and proof travel together

Set task-appropriate initial window sizes, minimum bounds and reading widths
on the canvases. Respect user-resized geometry; arriving data must not resize
or refocus the work. A small preference task should not inherit an oversized
page composition, and a resource workspace should have room for navigation
and inspection. Decide these proportions from meaningful states, not empty
screens or one shared default rectangle.

The resource canvas needs readable, scannable rows, visible selection,
contextual commands and quiet status. Preferences group fields without
turning every setting into a card. Documents use a deliberate reading measure;
conversations privilege that material and a stable composer. Use shared
density and spacing tokens for the input environment, rather than local
shrinking or padding patches. Keep material hierarchy clear between frame,
work surface, selection and inspector; nested borders are not hierarchy.

Typography, rich illustrated icon construction, active/inactive selection,
focus, pressed/busy states, pointer targets, scroll ownership and narrow
reflow are reviewed together. Loading should preserve useful structure;
empty and failed states need a clear local next move. Compare the same job
and states side by side, including transitions, rather than approving an
isolated icon or idle screenshot. Workbench character must survive the
quieter modern material, and the owner's repeated visual rejection remains
open evidence until the relevant experience is accepted.

At 1440 and 393, and at a representative constrained floating-window width,
use the same meaningful fixture through populated, empty, busy, failed and
resumed states. Include pointer and keyboard paths, and voice/IME where the
job edits text. Resizing is an application behavior, not a separate phone
page; GNOME's [adaptive guidance](https://developer.gnome.org/hig/guidelines/adaptive.html)
supports evaluating windows across desktop and narrow sizes. The proposed
HoldSpeak compositions still need their own task and accessibility evidence.

Record three different answers: does it render and behave correctly in the
tested case; can the owner complete the intended job without losing work or
context; does the owner find it clear and delightful? Layout floors and local
timing traces contribute to the first answer. Only the owner's actual task
and feedback can establish the latter judgments. A shot alone cannot.

Use the existing per-window feedback route to connect the reported moment
to its window state, screenshot and audio/transcript. Preserve the owner's
requirement that transcription use the installed speech engine. Link each
report to the job, expected behavior, shared pattern and affected consumers.
A visual rejection remains a visual rejection; do not relabel it as resolved
because a functional check passed. Revisit the same meaningful state after
the correction instead of judging an unrelated empty window.

Before setting performance budgets, collect production-build traces for
typing, window activation/drag, collection navigation and a returning async
result, both idle and while background work runs. Record input-to-paint and
long frames on the named machine/browser, then choose a justified budget.
Do not make a React upgrade, Compiler, virtualization or a new browser API a
prerequisite without that evidence. Browser/native and assistive-technology
proof remain separate from DOM component tests. Presence stays disabled.

## Keep the plan and reality aligned

The owner sets product direction and judges the live experience. Muad'Dib's
workers implement settled designs; Astra reviews merged changes under the
existing fast cycle. This refinement adds no 47-stage approval queue. Future
implementation still uses small changes, required quick checks, exact-main
deployment and post-merge review/full tape. Current repairs are a bounded
closeout. The larger project-update Stop candidate is parked outside main on
`fix/update-stop-repair-20261023`, commit `54a7436b7`, with explicit unverified
identity, transaction and editor conditions. It is not a shipped repair.
The remaining implementation backlog is organized by the proposed design;
this document does not start it.

When a pattern is delivered, update its actual public contract, Components
example, production-consumer record and evidence pointer together. Keep the
baseline audit and dissent as history; append what changed and what remains
unknown. [The synthesis](adversarial/SYNTHESIS.md) records repair delivery;
[the delivery plan](DELIVERY-PLAN.md) derives package order and task proof from
the proposal. Update the workflow trace and journey when a design changes;
update the shared contract, real consumer and Components specimen in the same
implementation change when behavior changes. Do not rewrite historical audit
verdicts to imply that a proposed or merged fix was observed by the owner.
Keep source inspection, executed tests, live task observation and owner
aesthetic acceptance distinct in every status update.

Method: provisional Vision Control Develop/Review, using the existing
repository as the durable strategy record. No Vision Control portfolio was
initialized or updated. Stack direction is authorized; the application
framework has not been shown enabled or proven. This draft awaits Muad'Dib's
check, and its recommendations have not been acted on.
