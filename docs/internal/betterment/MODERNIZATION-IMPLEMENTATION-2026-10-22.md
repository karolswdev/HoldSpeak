# Complete surface modernization

Owner instruction, 2026-10-22: “fully implement this, literally, across the
board.” This supersedes the preceding audit-only scope. Worktree:
`wt-modernize-all-20261022`; base product `62358b671`.

This implements the existing Workbench meets Pop!_OS direction and the living
in-desk reference, rather than introducing a second design framework.
Seven Tenets 3/5/6/7 govern it. Tuesday: every window must make its job and
next action clear, keep the owner's context, and remain useful when narrow.
The latest fast cycle in CLAUDE.md governs delivery; owner aesthetic judgment
is live and remains distinct from technical checks. No owner merge gate.

## Settled layout and canvas

The window frame owns title, window actions, feedback, placement and focus.
The interior owns its task. Use existing sections, forms, ledger, reader,
composer and state species; improve their common material instead of adding
feature skins. One primary content scroller; nested scrolling only for a
bounded editor, terminal, source preview or intentionally scrolling rail.

```
WINDOW: title / wings                  feedback / window actions
  leading fact                              leading task action
  quiet state / scope

  section label ---------------------------- section action
  grouped values, rows or readable content
  related metadata beside the thing it describes

  inline editor or working/error/retry state
  result / receipt at the action
FOOT: egress / current outcome                        local verbs
```

Use common spacing and fine, quiet outlines. Paper is for reading/editing;
avoid hard boxes around every row. Clear type hierarchy, readable line
length, generous but purposeful group spacing, intrinsic control widths.
Narrow content stacks by its surface container with labels beside their
values; actions wrap without overlapping. Code and metadata retain mono.

The existing Components window becomes the design reference. Its first
section is a compact pattern selector: Forms, Reading, Lists, Conversation,
and Progress. The selected example is interactive, with concise state
controls and a Local specimen marker. The existing control catalogue remains
available as Controls, rather than forcing every visitor through one long
page. No new app, pop-up or network writes for demonstration state.

```
COMPONENTS                                   Feedback / window actions
  Patterns: Form | Reading | List | Conversation | Progress | Controls
  state: ordinary / busy / failed / empty / long (as applicable)
  --------------------------------------------------------------
  [actual shared composition, its real controls and working states]
  --------------------------------------------------------------
  Uses: concise real consumer names             LOCAL SPECIMEN
```

Forms demonstrate dirty/invalid/saving/failed/retry/saved, keeping newer
edits. Reading demonstrates a long sourced result and reachable actions.
Lists demonstrate actual filtering, selection and details. Conversation uses
the shared composer and local results. Progress demonstrates completion,
failure and retry. All example buttons work; proposed/reference-only examples
are not labelled as production adoption. Existing feedback belongs to the
ordinary frame. The reference uses production imports and the same library
styles; no copied controls or independent design CSS.

## Implementation lanes

- Shared framework: common composition/material rules, layout modes and
  integration into active hosts; census every active application, scoped
  object/pullout and non-manifest host. Declare intentional canvas/editor
  exceptions. Fix the Room's fragmented narrow question controls and
  inconsistent agent/automation grouping through shared rules.
- Reference: implement the working patterns and retained controls catalogue
  in Components, using production APIs. Add behavioral state/keyboard proof.
- Compositor: one mounted live-front authority for frames, Dock and keyboard;
  one compact query; diagnose scroll ownership and registry seams without
  rewriting the store, remote protocol or window identity model.
- Documentation: reconcile current material/API/geometry guidance, provide
  one author map and an explicit adoption inventory. Keep old owner rulings
  as history. Update the executable specimen with future shared changes.

Workers hold for SHIP and never stage/commit. Root verifies and serializes
delivery. Run only scoped tests under the lock and an isolated HOME; root
runs the required quick check. Read desktop and narrow screenshots across
the active inventory. Existing owner edits in the main checkout remain
untouched. Do not revive parked applications to increase the adoption count.

## Adoption inventory

Source inventory: 25 manifest rows, 21 distinct active application windows.
Four parked compatibility entries redirect to current surfaces and are not
additional active apps. These are source/adoption facts; rendered evidence
and task/state limits are recorded separately below.

| Active application | Common host / composition |
| --- | --- |
| Today | TodayView `desk-surface-body`; day/task layout retained |
| Capture | ChairDesk `chair-window-body`; capture task layout retained |
| Speak | SurfaceWindowHost; shared form/control species |
| Ask AI | AskPanel `desk-pullout-body`; conversation reading/context regions |
| Meetings | SurfaceWindowHost; meeting catalogue/reader |
| Agents | Conductor `surface-host-body`; shared group wells and drawer scroller |
| Settings | SurfaceWindowHost; preference groups and controls |
| Live meeting | SurfaceWindowHost; live task/reading layout |
| Setup | SurfaceWindowHost; first-arrival layout remains specialised |
| Context | SurfaceWindowHost; existing editor composition |
| Automations | SurfaceWindowHost home; object AutomationWindow with shared group wells |
| Components | SurfaceWindowHost; executable patterns and retained control catalogue |
| Activity | SurfaceWindowHost; event/result rows |
| Memory | SurfaceWindowHost; existing reading and object rows |
| New Project | SurfaceWindowHost; project door composition |
| Processes | SurfaceWindowHost; existing process rows |
| People | SurfaceWindowHost; roster/detail composition |
| Projects | SurfaceWindowHost; existing project rows |
| Decisions | SurfaceWindowHost; decision form/readers |
| Calendar snapshot | SurfaceWindowHost; snapshot reading layout |
| Engines | SurfaceWindowHost; assignment/engine composition |

Additional hosts: object Pullout supplies explicit common hosting; hosted
Meeting/People, Note opening, Trust, Builder/Workbench, Repository, Info,
project/info drawers, Conductor Info, Hand, Lane, Session, Delivery Dossier
and Delivery Terminal receive the common material through their existing
body classes. Roadmap now explicitly adopts the common host and readable
list composition; it is not a canvas exception. Its single body remains the
scroller. Send stays in its existing in-flow host and shared controls.

Intentional composition/scroll exceptions are functional: the Chair's task
layout, Ask's reading/context regions, Thought's editable document and answer
panes, canvas-like builder tools, and bounded terminal/raw/source/code/table
wells. These retain their existing layouts rather than becoming generic
form pages. They inherit common frame/control material; this inventory does
not imply every inner operation was newly exercised. Source mounting and
remote window identity remain explicit existing adapters, with no new window
manifest or framework.

## Verification and delivery

The shared framework, local reference, compositor and documentation are
implemented. Focused shared layout tests: nine files, 172 passed; shared
FilterTokens/Roadmap: four files, 27 passed; compositor: four files, 76
passed, including unmounted-row exclusion and depth-arrival preservation.
Additional focused People/material and Process empty-to-populated checks pass.
Root read the focused run tails and the final typecheck result.

Root reviewed 70 inventory screenshots (35 poses at each width), all six
reference patterns, and full-size captures of the changed surfaces. Evidence
is under `.tmp/evidence-shots/desk-sweep/`, `design-reference/` and
`modern-window-heads/` in the implementation worktree. These are layout and
specific state observations, not a claim that every inner action was walked.
The reference's ordinary patterns also pass axe checks; its behavioral tests
cover dirty saves, preserved newer drafts on retry, reset, source/excerpt
controls, real filtering/selection and progress retry.

Rendered review found two real gaps despite the earlier green checkpoint:
Speak could push its gadgets outside the frame, and Person could show a blank
body between readiness and detail. The shared head now folds by allocated
space at desktop widths too, then unfolds after widening. Fixed head controls
keep their targets, and the title leaves bare bar available for dragging.
Person shows loading until detail arrives; the screenshot fixture waits for
that detail. The sweep now fences visible head bounds and label clipping
without a new baseline exemption. Four browser cases prove 1440/393/280 head
geometry, both resize directions, actual empty-bar dragging and preservation
of owner-arranged positions across reload and a second view.

Final required check: build, 4,162 related web cases, 59 affected browser cases including strict Firefox feedback capture and resize/drag checks, 110 desk sweep cases, 27 canon and 1,126 repository guards passed; typecheck passed. The full pinned-main tape follows merge;
its result is separate from this required quick result.

The prior tape's two Dock outage failures came from a retired localStorage
builder flag in the fixture. The test now seeds the canonical hub setting,
retains the exact refresh command and all geometry assertions, and observes
the real refresh request. This does not revive a removed product command.

This work does not change the 115/117 betterment recipe count. Full-tape
failures, provider/native execution and owner aesthetic acceptance remain
separate from implementation and observed layout coverage.

Workspace correction after the harness restart: the isolated lane's host
marker had also been added as one line to the otherwise clean AutomationWindow
in the main checkout. Root removed only that exact addition with a patch and
verified the file matched its original HEAD. The owner's pre-existing tracked
and untracked paths remained unchanged; no git restore/stash/reset was used.
