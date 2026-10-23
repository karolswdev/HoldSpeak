# Desktop applications are the unit of experience

Owner clarification, 2026-10-23: near-native apps, windows and file explorers;
not web pages fitted into small containers. This extends the research in
PR1429. The React/TypeScript/DOM stack stays fixed. Contracts below are
proposed implementation direction, not a claim that an explorer has shipped.

## The framework must own desktop behavior

A window frame and a collection of controls do not define an application.
The common framework must connect application/window/resource identity,
commands, navigation, focus, selection, editing, scrolling, drag-and-drop and
operation outcomes. Preference, conversation and collection patterns are
views within that application model. They are not the complete framework.

Use an explorer-style resource application as a demanding acceptance workload.
It reveals gaps a preference form does not: several windows on different
locations, independent selections, folder history, large collections,
range selection, contextual commands, rename, transfer, stale reads and
cross-window operations. This is an architectural yardstick, not authorization
to invent a full filesystem product or show unsupported file operations.

## Existing seams to evolve

The Desk already owns application registration, dynamic object windows,
workspace geometry, front-window authority and a command registry. Screen
has the Desk's object selection and context menus. ObjectList exposes stable
row ids, a controlled selected-id set, sorting, roving rows and separate
select/open actions. Repository APIs already expose registered-root tree,
file and status operations. Hand provides typed in-app object handoff.
These are useful foundations; they do not yet establish one complete
explorer interaction contract. Specific baseline anchors are in the research
source audit; new application capabilities still need actual consumer proof.

Evolve these seams in their current folders. Do not add a second window
manager, an app process per React root, a universal layout interpreter or a
parallel command bus.

## Verified application gaps at the baseline

The follow-up source audit inspected active consumers, not the parked Floor:

- Active Screen owns semantic HoldSpeak objects and the Desk selection (`web/src/desk/DeskApp.tsx:6-8`, `screen/Screen.tsx:104-117,207-255`). It supports marquee selection, but an icon press replaces selection. There is no shared Shift-range/primary-modifier contract there.
- ObjectList can display a selected-id set but exposes `onSelect(id)` without range/modifier intent (`surface/objects/ObjectList.tsx:80-99,127-185`). Active drawers and tables still use singular selection. A shared selection controller is a concrete missing behavior, not a reason to replace the view library.
- `keymap.ts:112-115` publishes one `selectedRef` only when exactly one object is selected. Extend the existing context to scope selected sets and documents; do not add another command bus.
- The active `components/RepoWindow.tsx:69-85,113-149,175-236` reads a registered repository's tree/status/branches. A file click selects its path; folder clicks change local path state and breadcrumbs exist. It has no Back/Forward stack or document-opening view, although `repository.ts:49-60` already exposes file read/write APIs. Start file open/read with those real services before proposing unsupported file operations.
- Internal Hand uses semantic refs (`hand/drag.ts:1-14,25-72`). The old global file-drop layer is parked and excluded from compilation; it is not proof of active desktop file drop. Feature-local import remains distinct from a desktop-wide drop contract.

These are source facts at main8a41884a4, whose product code matches PR1428;
anchors may drift. No new file operation, performance benchmark, or browser
workflow was run for this follow-up audit. Repository resources are not proof
of general OS-filesystem access or native file-manager integration.

## Application and view contracts

| Responsibility | Proposed shared contract |
| --- | --- |
| Application identity | A logical app owns its commands and supported resource kinds; window instances have stable separate ids. Several windows can belong to one app. A document/resource identity is separate from its current title and location. |
| Window lifecycle | Open, restore, raise, minimize, close and reopen use the existing compositor/registry. Distinguish a mounted view from a retained background operation or dirty document. Incoming events do not steal input focus. |
| Navigation | Each explorer window owns location, breadcrumbs, Back/Forward history and restoration. Folder navigation does not replace the entire Desk route or another window's history. Existing deep links remain entry points into this state. |
| Selection | Each collection view owns selected ids, focused item and range anchor. Switching windows preserves its previous selection. The active view publishes command context; the Desk keeps its own screen selection. A Screen refresh must not prune another window's selection. |
| Commands | Extend the existing verb registry/context. Menu items, toolbar actions, shortcuts, context menus and voice proposals resolve the same target set, availability and operation. Editors/IME keep their standard input commands. |
| View modes | List, icon and tree views can render the same collection model, selected identities, sort and operations. Changing view mode preserves work; it does not create a second selection model. |
| Data provider | A typed adapter exposes children, metadata, content and supported operations. Domain identity, path validation, permissions, revisions and side effects remain with existing backend/native services. |
| Persistence | Extend the existing workspace/view persistence where appropriate for location, split widths and view mode. Validate restored identities and stale locations. Do not introduce another global persistence authority. |

The currently global Screen selection remains valid for the Desk itself.
Application selection needs window/view scope; blindly copying that global
array into every explorer would make menus operate on the wrong objects.
Front-window activation, focused control and selected objects are related but
distinct. Preserve all three explicitly.

## Application families share the model, not one page template

| Application family | Common behavior beyond the frame |
| --- | --- |
| Explorer/resource browser | Navigation/history, selection, view modes, contextual commands, editing and transfer. |
| Document/editor | Document identity, dirty/save/recovery/undo, selection/caret, source and outline panes, per-window view state. Retain CodeMirror and existing document services. |
| Console/terminal/run monitor | Input ownership, selection/copy, bounded scrollback, follow/pause, running-operation identity and real stop/recovery. Terminal shortcuts remain terminal commands while it owns input. |
| Inspector/preferences | Context-bound fields, immediate editing, explicit save semantics and conflict handling, with shortcuts and toolbars from the same application command context. |
| Conversation/media/live work | Stable session identity, real transport/request states, selection, reader/composer or media controls, source/context inspection and interrupted-work recovery. |

A specialized editor, canvas, terminal or media renderer still participates in
application focus, command routing, window state, selection and feedback. A
bounded content-scroller exception does not exempt the application from the
common framework. Sidebars, split views, toolbars, status areas and inspectors
are composable application regions with explicit ownership, not extra web
pages or independent navigation systems.

## Explorer interaction contract

Selection must support ordinary desktop expectations: click selects, primary
modifier toggles an item, Shift extends from an anchor, and keyboard navigation
can move focus and extend selection. Double-click or Enter opens; expanding a
tree node is different from entering a folder. Typeahead, sorting, column
layout, context menus and in-place rename need consistent keyboard and pointer
behavior. Keep native editing, IME, selection and undo while renaming.

Choose tree, grid or treegrid semantics to match the actual interaction, not
because a component happens to look like a file manager. W3C's
[tree pattern](https://www.w3.org/WAI/ARIA/apg/patterns/treeview/) distinguishes
focus from selection, especially for multiple selection; its
[treegrid pattern](https://www.w3.org/WAI/ARIA/apg/patterns/treegrid/) adds a
specific row/cell keyboard contract. Neither ARIA roles nor browser popovers
supply those behaviors automatically. Avoid applying `role=application` to the
whole Desk to make it sound native.

React Aria's [selection](https://react-aria.adobe.com/selection) and
[drag-and-drop](https://react-aria.adobe.com/dnd) facilities are relevant
within-stack behavior sources for collection work. Evaluate a scoped adapter
when a diagnosed need warrants it; do not force a checkbox-group selection
model or another visual theme onto desktop collections. Keep the current
public Button and surface species.

Lazy folder reads distinguish unknown/loading children from a known empty
folder. Reject stale responses after fast navigation. Keep stable selection
through sort, rename and refresh where the provider can establish identity;
when an item disappears, resolve focus and command context deliberately.
A path-only provider needs authoritative rename/move mapping; a UI-generated
row id is not proof of durable filesystem identity.

## Transfer, editing and operations

Internal object transfer, browser file drop and OS file-manager transfer are
different capabilities. Extend the existing Hand model with explicit
copy/move/link intent and source/target identities when supported. A drop into
Ask may attach a reference; that must not pretend to move a file. Show allowed
and refused targets and offer an equivalent menu/keyboard operation.
Apple's [drag-and-drop guidance](https://developer.apple.com/design/human-interface-guidelines/drag-and-drop)
emphasizes the meaning of moving or duplicating selected content and clear
source/destination behavior; that principle applies without adopting AppKit.

An application clipboard may carry bounded resource references between Desk
windows. The OS clipboard and native file-manager integration have separate
browser/native capabilities. Preserve text copy/paste in editors; do not
silently claim a private reference is an OS file transfer. External drops use
user-provided `DataTransfer` files; they do not grant arbitrary disk access.

For local repository/filesystem resources, use the current authenticated
backend/native boundary rather than making browser-only directory APIs a
prerequisite for Firefox. UI capability flags describe available commands;
the backend still enforces roots, paths, symlinks, permissions and revisions.
Remote/semantic resources use their own adapters and egress facts.

Offer rename, create, copy, move, archive or undo only when the provider and
existing operation authority implement them. Preserve the owner's never-delete
rule; no permanent-delete capability is introduced here. Pending edits,
conflicts, partial transfer, refusal and indeterminate outcomes stay visible
at the operation. Do not invent undo from a visual state rollback when a file
operation is already committed. Reuse existing receipts and authority rather
than adding another approval system.

## Acceptance workload and delivery consequence

The first application-model proof should use an existing registered repository
or resource browser, plus the preferences consumer; a Settings form alone is
not sufficient. Use isolated fixture data and real available operations.
Capabilities the backend lacks remain explicit gaps, not decorative buttons.

1. Open two resource locations in separate window instances. Navigate one,
   switch focus, and verify independent history, selection and scroll state.
2. Select a range and a noncontiguous set; change view or sort; verify that
   commands still target the same valid resource identities.
3. Open the context menu on a selected item, invoke an available command by
   keyboard, and perform a supported in-place edit with IME/voice semantics.
4. Transfer or attach selected resources between windows through a supported
   operation, then exercise refusal, interruption and recovery. Do not test
   unsupported filesystem operations by faking a successful UI result.
5. Reopen and restore the window, refresh the provider, and exercise missing
   location/read-only/empty/large-folder cases without losing unrelated work.

Use the same app/view models and controls in Components with fixture adapters
so the reference can demonstrate the desktop behaviors. Include pointer,
keyboard, touch and assistive-technology paths, constrained window sizes and
local performance traces. Browser-native editing and DOM rendering remain the
foundation; the target is application coherence and craft throughout the Desk.

## Verification of this research follow-up

Root validated the exact manifest, public-job, capability and cluster-qualified
recipe source sets, family references and all 145 referenced source/test paths.
The inventory's source coverage is complete for that corpus; its family
associations are coarse audit groupings, not proof of per-command behavior.
The JSON and behavior matrix do not certify every use case as executed.
Required quick: build, 40 focused documentation/harness checks, 110 desk sweep
cases, 27 canon and 1,126 repository guards passed. After the audit records
were added, 40 focused checks and seven Markdown navigation checks passed.
Root reran the hardened capability probe in all three actual engines with the
canonical isolated invocation. Product web/backend source and dependency locks
are unchanged; live native-application quality remains implementation work.
