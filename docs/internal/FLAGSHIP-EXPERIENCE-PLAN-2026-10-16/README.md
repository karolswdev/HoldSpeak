# HoldSpeak: flagship experience and product cohesion plan

**Execution resumed by the owner's invocation of [KICKOFF.md](KICKOFF.md),
2026-10-16.** The plan was written during the earlier planning pause. Baseline:
main `ebfce9feb` / released build `1db394185ca801fe` (#1219). The merged first batch is recorded in [Implementation](IMPLEMENTATION.md) and
[Delivery B](DELIVERY-B.md). The connected follow-up is
[Daily work and recovery](IMPLEMENTATION-CDE.md), with [actual verification](DELIVERY-CDE.md); [coverage](COVERAGE.md)
reconciles every surface family with current and carried evidence. Historical source-audit and candidate descriptions
below retain their original evidence limits; they do not pause the authorized
execution. Formal postmerge review and owner visual judgment remain separate.
The owner selected an Astra master orchestrator and Sol HIGH workers for this
programme; see [Delegation and delivery](EXECUTION.md).

## 1. The experience we are building

HoldSpeak should feel like a crafted personal workbench: calm to read, obvious
to act on, and satisfying when work lands. Its value is helping a senior
architect understand the day, prepare for people, capture decisions, develop
work and follow through. Amiga Workbench material gives it a distinct identity;
the information hierarchy and handoffs make that identity useful.

Every flagship must answer four questions on first contact:

1. What am I looking at, and how current is it?
2. What matters now?
3. What can I do next?
4. Where did this come from, and where did my action land?

The design bar includes visual quality, legibility, navigation, accurate
meaning, and recovery. A passing geometry check establishes geometry. A
successful API response establishes that response. Neither establishes that a
screen feels pleasant or that the whole job works. The owner judges the
released experience live. The previous technical pass does not establish
whole-product aesthetic acceptance; the broken Brief links expose a concrete
coverage gap in its populated-source journeys.

## 2. What the evidence says now

| Finding | Evidence | Consequence |
| --- | --- | --- |
| Brief's weekly action reference cannot expose a snoozed action | Owner report plus read-only inspection of the exact source/loop; normal board suppression in `holdspeak/services/follow_through_service.py` and missing-focus handling in `FollowThroughView.tsx` | Reading a source must work while that source is snoozed, without waking it. |
| Brief's PR reference cannot load an output awaiting review | Owner report plus exact artifact read-only inspection; public listing deliberately excludes pending-review/rejected outputs in `holdspeak/db/plugins.py:list_run_artifacts`; opener refreshes that listing in `web/src/desk/shell.ts:openPrimitive` | Explicit source inspection needs an exact read, independent of public list visibility. |
| Brief's date, generated stamp, repeated event labels and repeated source emblems compete with the work | Prior actual `brief-{1440,393}.png`, read for this plan; current `BriefView.tsx` and `intelligence.css` preserve the composition | Give Brief an intentional reading order, useful section hierarchy and compact source relationships. |
| Day's next meeting sits below unfinished summary work and substantial chrome on phone | Actual released-build `today-393.png`, read for this plan; `TodayView.tsx` composition | Put the next useful action where the owner first looks; let older work remain reachable. |
| Memory's phone rows spend substantial height on repeated type/source/owner controls | Actual released-build `surface-project-memory-393.png`, read for this plan | Keep title and meaning first; move detail and secondary work into a deliberate expansion. |
| Shared kit adoption has improved, but a manifest screenshot misses cited inner objects and lifecycle states | Existing completion audit and the two current source failures | Audit by owner journey and state, alongside the application inventory. |

Prior screenshots are evidence of their named builds and states, never new
owner-session observation. The Day/Memory samples are from the Entry worktree
quick captures; the Brief pair is from the preceding Cohesive Workflows tree.
No tests or new runtime walks are run for this plan. Exact current owner source
IDs and private bodies stay out of this document.

The PR-related citation names a saved agent output, not an independently
verified pending task. Its body says it lacked PR context. The design must make
source kind and current state clear; opening an output does not prove a review
ran. The weekly action's hold date also needs to remain visible when opened.

## 3. The shared visual direction

Use the existing token and component system. Preserve steel frames, paper
reading surfaces, square bevels, ink rules, blue active selection and restrained
amber/green/red state signals. Keep the Desk's personality and environments.

- **Reading hierarchy:** one leading fact/title, clear section titles, a
  readable body, quiet time/source metadata. Follow the canonical type roles:
  display26/650 once, primary15/600, body13, metadata/captions12. Names and
  sentences use sans; mono distinguishes metadata and controls.
- **Composition:** steel frames the work; paper holds readable material;
  inset wells hold editable material. Space separates meaningful groups. Avoid
  repetitive nested framing and wide empty plates around small facts.
- **Density:** desktop uses purposeful side-by-side support where it helps.
  Narrow windows and phone use a composed reading sequence. Responsive layout
  follows the actual window container, not only the browser width.
- **Actions:** the main action is easy to find. Secondary actions sit beside
  their relevant object or in the existing overflow/disclosure. Status facts
  remain distinct from actions. Selection, expansion and navigation are clear.
- **Sources:** prefer a readable source name/type with a quiet date. Preserve
  canonical identity and a clear open affordance; opaque IDs are fallback or
  detail. Show source status when it changes the meaning of the claim.
- **Feedback:** immediate press feedback, an honest working state, a named
  outcome, and a clear recovery action. Use shared motion; maintain stability
  while results arrive. Preserve reduced motion and do not fake progress.

Canvas directions must use actual components, real window widths, long names,
and representative populated material. Empty-window mockups are insufficient
for a source-heavy flagship. The earlier two-status specimen in the link-fix
folder is exploratory; it is not approval of the complete flagship direction.

## 4. What each flagship should become

| Surface | Primary job and proposed composition | Journey that must work |
| --- | --- | --- |
| **Brief** | A readable weekly/daily briefing: period and freshness, What needs me, What changed, then supporting history. Give standing answers and source-backed facts a consistent paper composition. Keep engine/run details in relevant supporting detail. Render complete Markdown documents, including tables, without flattening their structure. | Read a claim → open the exact source → inspect its current status → return with reading position intact → act on the intended record. |
| **Day** | A useful next-meeting/prep lead; time and next action first, then a clean timeline and unfinished work. Existing decision/owed support stays subordinate. | Open the day → prepare for the right person/event → record → recover from a refused start → reach the resulting meeting. |
| **Follow-through** | Task title, owner, due/hold state and one clear next action; expanded controls keep their draft and visible source. A direct citation may inspect its exact held task. | Open cited task → understand why/when it is held → change owner/date or complete → see the durable outcome → return without losing other edits. |
| **Meetings and People** | Meeting outcomes and person prep remain connected. Maintain the established list/detail/Back grammar and clear summary/decision/action reading hierarchy. | Person prep → linked meeting → outcome → confirm exact work → find it in Follow-through/Project. |
| **Ask and Thread** | A calm reading surface, clear question/composer, grounded context and readable sources. Shared result, pending, refusal and retry treatment. | Start from a note/passage → ask with visible context → inspect source → refine → Keep/Send → reopen the exact saved result. |
| **Workbench and Conductor** | Separate instruction/input, current work, result and next owner decision through hierarchy. Readable deliverables lead; execution detail is available when useful. | Add work → run → understand waiting/refusal → inspect real result → revise/retry exact input → keep or hand off. |
| **Memory and Project** | Find a decision, obligation or source in context; title and current meaning lead. Preserve source identity, useful filters and readable history. | Find work → inspect source/current status → open the right Project/person/task → perform next work → return to the same context. |
| **Desk, Settings and notices** | Predictable doors, coherent settings rows, unobtrusive actionable notices. Setup and repair are direct, consistent journeys. | Find application → open exact object → configure missing capability once → return to the job; dismiss or open a notice without trapping the owner. |

Section names above are proposed reading labels. Final words must obey the
product vocabulary and existing source semantics. Show available facts; do not
invent summaries, tasks, deadlines or successful agent work to fill a layout.

## 5. Shared component work

The new owner screenshot of Codex asks exposes literal pipe-table syntax and
flattened block structure. Exact source trace: `AskWell` renders `AgentWords`;
Codex Stop capture and transcript capture collapse whitespace before storing
the question (`holdspeak/agent_context/sessions.py:261`, `:1017`). AgentWords
has no table blocks. Material is a separate renderer and also lacks tables;
swapping the caller alone would leave upstream loss. Preserve original block
structure, then select a bounded shared parser/renderer repair. Add
proper headings/lists/tables/code/link treatment in the existing material
species, with useful narrow-window behavior. A readable result must retain the
original source; unsupported syntax must not silently lose structure.

Audit the existing composition layer before adding primitives. Standardize
these usages across the flagship batch:

| Duty | Existing component homes | Required improvement |
| --- | --- | --- |
| Identity, sections and supporting facts | `SurfaceIdentity`, `SurfaceSection`, `SurfaceFacts` in `desk/surface/Surface.tsx` | One hierarchy and spacing rhythm; subordinate freshness/engine/source facts. |
| Reading and editable material | `Material`, `Paper`, `PadGadget`, `StringGadget` | Consistent text measure, paragraphs, long-name wrapping, padding and focus. |
| Task/result lists and inline details | `SurfaceLedger`, `SurfaceLedgerRow`, `Disclosure`, `GadgetGroup` | Name-first rows; clear selection/expansion; useful narrow layout; durable edits. |
| Source references | `CitationChips`, `RefTokens`, `openRef`, `holdObject` | Same source-open contract, exact identities, readable labels and visible failure. Reuse the two renderings' required contexts rather than force one oversized abstraction. |
| State, receipt and recovery | `StateChip`, `SurfaceState`, `ActionNotice`, `SurfaceFooter` | Shared working/refused/partial/completed vocabulary; exact Retry; results remain readable. |
| Commands and choices | Library `Button`, `SurfaceWings`, `WorkbenchSelect`/`CycleGadget` | Consistent visual priority, native keyboard behavior and touch ownership. |
| Window, navigation and return | Existing compositor, scoped windows, app manifest | Preserve placement, restore, Back and reading context; fix specific handoff gaps. |

A new shared component needs two concrete consumers and a clearly missing
responsibility. Prefer a small addition to an existing species. Component
examples should demonstrate ordinary, long, narrow, pending and refused poses
in the existing Components app; avoid a second design-system application.

## 6. Delivery sequence

The implementation unit is a coherent owner journey with all its relevant
surfaces. Use substantial PRs that are independently usable and reviewable.
Do not split a face into a sequence of disconnected cosmetic PRs.

### A. Settle the flagship direction

Create one surface/journey inventory from `applications.ts`, pullout/editor
registries and non-manifest hosts. Reconcile previous audits against current
source so healed findings stay healed. For each family record primary job,
entry, detail, edit, result/recovery, phone behavior and evidence status.

Inspect populated Brief, Day, Follow-through and Memory first. Produce paired
actual-library canvas directions for these four as one visual family, with a
shared source/receipt/action example. Capture specific before-state weaknesses;
settle hierarchy and density before implementation. This is a bounded design
pass, not another framework or exhaustive permutation campaign.

**Exit:** one coherent direction, ranked findings with sources, and concrete
build briefs. The owner can judge the direction in the actual Workbench material.

### B. Deliver Brief → source → Follow-through/Memory

Build the flagship reading composition and close its actual source journeys in
one meaningful PR. Include the two diagnosed link defects; exact pending output
read; focused snoozed/deferred task inspection; visible missing-source outcomes;
accurate state labels; return/context retention; phone composition; shared
Markdown rendering and the affected Codex asks surface. Inspect the
semantics of Brief claims against their source kind and state.

**Exit:** both owner-reported references open their exact records, status remains
unchanged on inspection, Brief feels intentionally composed, and the surrounding
reading/action/return loop passes. Publish before/after pairs on the same build.

### C. Deliver the daily work loop

Apply the settled family to Day, meeting/person prep and outcome handoffs;
finish Follow-through details and Project/Memory transitions. Preserve working
strengths such as People’s next-1:1 lead and the Project's supporting folds.

**Exit:** next work is apparent on phone and desktop; prep→meeting→outcome→task
is complete, accurate and recoverable; readers return to their context.

### D. Deliver the creation and execution loop

Use the same reading/composer/state/source conventions in Ask, Thread,
Workbench and Conductor. Carry forward already proved fixes and assess actual
inner results, empty/refused states and handoffs. Each agent/workbench view
makes its current work and useful outcome understandable.

**Exit:** note→Ask/Thread→Workbench/agent→saved result uses one visual language
and completes without ambiguous result status or lost drafts.

### E. Complete the supporting surfaces and final judgment

Roll the accepted conventions through Settings/Engines/Accounts, Speak,
notifications, Search/Context, object/edit/send/info windows and entry surfaces.
Group repairs by journey and shared component, rather than one PR per control.
Use the authoritative inventory to ensure satellites and inner poses are seen.

**Exit:** explicit coverage status for every active surface family; remaining
exceptions named with owner cost; final side-by-side and real-use review. The
owner's live feedback informs refinement. Keep formal postmerge review and main
tape results distinct from aesthetic acceptance.

## 7. Definition of done for each batch

- **Visually composed:** a clear first focal point, readable hierarchy and
  purposeful spacing; paper/steel/ink roles are consistent. Review actual
  populated before/after shots at1440 and393 and a narrow desktop window.
  Reject awkward repetition, weak grouping and cramped layouts even when fit
  checks pass. Keyboard focus, hover and pending states are included.
- **One useful job completes:** verify entry, selection, action, exact resulting
  record and return. Every source kind touched includes ordinary and one
  meaningful lifecycle edge, such as snoozed, awaiting review or missing.
- **State stays truthful:** no inspection mutates lifecycle; accepted operations
  and failed rereads are distinct; no invented deadline or successful work.
- **Work is retained:** drafts, selection, scroll and scoped identity survive
  relevant refresh/close/return behavior. Retry acts on its recorded input.
- **Narrow layout is deliberate:** source names and text fit; primary action and
  return remain reachable; visible controls own their required touch area;
  menus/focus follow the established grammar; reduced motion stays useful.
- **Checks remain proportionate:** cheapest scoped behavior checks; focused
  actual walks for navigation/keys/touch/geometry; quick check before merge.
  The full suite remains the main watcher's job. No scanner waivers or broad
  reruns of unchanged jobs just to inflate proof.
- **Delivered means live:** merged source/build match what the owner's hub serves.
  Technical verification and visual acceptance are reported separately.

Use representative short and long material, realistic populated lists and the
source lifecycle most relevant to that journey. Enumerate remaining unobserved
states. Test totals and screenshot totals are not usability scores.

## 8. Orchestration and scope control

Root owns the product direction, inventory, shared decisions, integration and
final claims. Bounded workers own disjoint files and implement the settled
composition. An independent reviewer checks the complete journey and visual
result. Keep a small team, one test run per machine, and one SHIP coordinator.
Workers report evidence and stop at their lane boundary. A blocked source or
new abstraction gets a short root decision; it does not start an open-ended
research loop. Root reads the actual results before repeating claims.

Dependencies are explicit: source reachability and current-state reads precede
source affordances; accepted composition precedes broad shared-component edits;
shared improvements precede satellite migration. Split a PR only when a genuine
independent dependency makes it reviewable sooner. No fixed dates are promised
before the initial direction/inventory establishes scope.

Park: new OS/window architecture, agent/kernel rewrite, token-system replacement,
new notification bus, novel model campaigns and additional background spectacle.
Keep these separate from the owner-requested usability and craft work.

## 9. Preserved link-fix candidate

Worktree `wt-brief-reference-open-20261016`, branch
`fix/brief-reference-open-20261016`, based on main `ebfce9feb`.
Ten product/test files contain uncommitted candidate edits. They are not shipped.
The action backend candidate collected and passed48 focused tests; its UI is
unfinished. The artifact candidate has no executed checks and no face change.
No commit, PR, merge or deployment occurred. Preserve this work for phaseB,
review it against the settled direction, and validate before integrating it.

Planning source audits: [Flagship journeys](../BRIEF-REFERENCE-OPEN-2026-10-16/PLAN-AUDIT-FLAGSHIPS.md) and [Shared system and workflow continuity](../BRIEF-REFERENCE-OPEN-2026-10-16/PLAN-AUDIT-SYSTEM.md). Root read both reports and checked the principal source mechanisms. Their findings are counsel,
with evidence classification, not formal Muad'Dib ratification or live user
acceptance. The plan is ready for discussion; implementation remains paused.


## 10. Coverage inventory for execution

This groups the current registry and mounted hosts for planning. The execution
inventory must follow their live declarations; this table does not become a
second application manifest. Previously repaired behavior is preserved.

| Family | Surfaces and inner poses to account for | Delivery home |
| --- | --- | --- |
| Daily orientation | Today/Day, Brief, Follow-through, Decisions; standing answers, selected task, held task, proposal and missing source | B/C |
| People and meetings | People roster/person/prep/agenda/obligations, Meetings list/import/record/detail/outcomes/transcript/artifacts, Live meeting, calendar snapshot | C |
| Knowledge and work | Memory recall/scoped Project/Review/Update/History, New Project, Notes/Thought workspace, selection/context/attachments, Knowledge and member edit | B/C/E |
| Conversation | Ask, Thread, composer/context/source picker, result/edit/Keep/Send, command/refusal/late reply | D |
| Execution | Workbenches home/open item/config/schedule/runs/memory/results, Conductor/session/lane/held decision, agent launch/hand/pane picker | D |
| Preferences and repair | Settings home/Voice/Meetings/Engines/Accounts/Guide/Remote access and inner editors; Setup/Get ready; Context and Commands | E |
| Attention and records | Menu-bar notice, ambient Qlippy, Needs you, Activity, Processes, send preview/history/receipts | D/E |
| Desk and objects | Desk home/drawers/Contents/Search/window menus, Info, repository/roadmap/story/Delivery dossier/terminal, object readers/editors for Recipe/Sequence/Workflow | E |
| Supporting experience | Rhythm, Change places, Presence, Components examples, archived/parked/compatibility entry behavior | E |

For each family record the entry, meaningful inner state, action/result and
return. The current inventory must distinguish an actually active host from a
parked compatibility declaration, and a known defect from an unobserved pose.
Markdown is an explicit cross-cutting pose: tables, headings, paragraphs,
nested lists, code fences, inline code and links must be represented in the
reading examples and real affected host. A wide table scrolls within its own
well; it must not widen the Desk/window or hide adjacent actions.

Source/display identity and privacy boundaries stay attached to the same object
through the journey. Duplicate text is not evidence of duplicate records.

## 11. Initial priority ledger

The first two entries are owner-reported and diagnosed. The remainder are
source candidates to reproduce before implementation; hierarchy opportunities
need populated visual judgment, not a claim that they block use.

| Priority | Candidate and owner cost | Planned treatment |
| --- | --- | --- |
| First | Brief cannot open the two cited sources; the reader cannot inspect its claims | PhaseB exact source journey, truthful hold/review states, return |
| First | Thread `/todo` clears words before writer acceptance (`components/ThreadComposer.tsx:652`) | PhaseD preserve submitted/newer drafts and exact command recovery |
| Next | Ask Projects failure becomes empty choices (`components/AskPanel.tsx:187`); related Thread helper reads do the same | PhaseD distinct loading/empty/unavailable states and local read recovery |
| Next | Qlippy proposal decision has finally-only cleanup (`components/AmbientLayer.tsx:408`) | PhaseD exact proposal/decision pending/refused/outcome and recovery |
| Next | Remote access write errors share Retry that only reloads (`pages/cores/SettingsCore.tsx:1228`) | PhaseE accurate Reload/Retry labels and operation ownership |
| Flagship craft | Brief source marks and repeated event labels consume reading space; Day hides imminent next work below older work | B/C settled reading order and meaningful density |
| Flagship craft | People obligation detail differs by direction; Project Review can receive less emphasis than Draft update | C inspect destination/authority, settle priority from current work |

All paths in this ledger are relative to `web/src/desk/`, except
`pages/cores/SettingsCore.tsx`, which is relative to `web/src/`. Anchors can
drift. The source audit records contain the detailed evidence and limits.
Their proposed small-concern release suggestions are input; the owner's
requested comprehensive, coherent batches above govern delivery.

## 12. The first acceptance walkthrough

Use one representative architect's desk with an upcoming1:1, a recorded
meeting needing review, open and snoozed tasks, and an output awaiting review.
Keep the short/long names and canonical references explicit.

1. Open Brief and identify what needs attention, the period and freshness.
2. Open the weekly task citation. The exact task opens expanded, with its hold
   date; the stored hold remains unchanged. Return to the same Brief position.
3. Open the PR output citation. Read its actual words and Awaiting review state;
   no successful PR review or new task is implied. Return without losing place.
4. Open Day and find the next person/event and preparation action in the first
   phone content viewport. Inspect a decision's evidence before confirming it.
5. Prepare, record, review one outcome and find the exact resulting work.
6. Ask about a selected passage, inspect a source, and keep a result. Exercise
   one refused submission and preserve a newer draft during Retry.

Run the individual cases through the repository's existing isolated rig when
implementation resumes. Keep actual source/task writers distinct from declared
provider replies and standing-answer fixtures. Inspect both the result and its
record. A screenshot of an open window or a mocked opener call cannot close
this walkthrough. Provider/hardware acceptance is named separately if needed.
