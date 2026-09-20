# Desk object and interaction model

This is the portable description of current Desk behavior. It names source
contracts and their exceptions so a consumer can reproduce the Desk without
guessing from React component structure. `Implemented` means source and a
focused assertion establish the behavior. `Spec-debt` means source exists but
the portable rule was previously undocumented. `Unimplemented` means the
current grammar records the gap.

## Object identity and projections

```ts
type WorldObject = {
  kind: PrimitiveKind;
  id: string;
  title: string;
  ref: Primitive;
};

type UnitPos = { x: number; y: number }; // normalized 0..1 world coordinates
type PanelRect = { x: number; y: number; w: number; h: number }; // viewport px
type DeskView = "spatial" | "list";
```

`world.ts` creates objects in the exhaustive order `meeting, note, decision,
thread, kb, project, recipe, artifact, chain, workflow, coder, roadmap, story,
repository, workbench, directory, game, layout, intelligence, people`
(`web/src/desk/world.ts:27-57`). Bare IDs and qualified `kind:id` IDs both
resolve. A missing ID or title falls back to the primitive kind
(`world.ts:63-79`).

The root spatial projection excludes directory, game, layout, intelligence and
people because they have dedicated paths. It also omits roadmaps from the
ordinary spatial Floor. If a Zone is open, the projection contains only
members. At root, filed items leave the open Floor; coder sessions always stay
visible (`world.ts:82-131`). The semantic list uses the same store items and
object refs, so it is the keyboard-accessible representation of the same
objects; it is not another data model.

The object descriptor (`web/src/lib/primitives.ts:66-82,419-644`) is the source
of labels, sync class, authorability, object-level capability set and opening
surface. It currently defines 21 kinds:

| Kind | Readable noun | Sync class | Can create | Object capabilities | Surface |
|---|---|---|---:|---|---|
| meeting | Meeting | content | no | ask | pullout |
| artifact | Artifact | content | no | ask | pullout |
| note | Note | content | yes | ask, edit, rename, duplicate, delete | pullout |
| decision | Decision | content | yes | duplicate, delete | pullout |
| directory | Zone | organization | yes | rename, delete | drawer window path |
| kb | Knowledge | organization | yes | ask, edit, rename, duplicate, delete | pullout |
| project | Project | organization | no | none | project memory surface |
| repository | Repository | organization | yes | none | repository window |
| recipe | Agent | capability | yes | ask, edit, rename, duplicate, delete | pullout |
| chain | Sequence | capability | yes | delete | pullout |
| workflow | Workflow | capability | yes | ask, edit, rename, duplicate, delete | pullout |
| coder | Coder session | presence | no | none | pullout |
| game | Game | local | no | none | none |
| layout | Layout | local | no | none | none |
| roadmap | Roadmap | organization | no | none | roadmap window |
| story | Story | local | no | none | none |
| workbench | Workbench | capability | yes | duplicate | workbench window |
| intelligence | Intelligence | local | no | none | pullout |
| people | People | local | no | none | People surface |
| thread | Thread | content | yes | delete | pullout |

The table is current implementation, not a proposal. A capability absent from
the descriptor is not silently inferred from a component.

## World placement and object motion

`objUnit` first returns a saved position. Otherwise it computes a deterministic
grid. On a wide Desk, columns are
`clamp(ceil(sqrt(max(1,n)*1.6)), 4, 8)`; on compact (`innerWidth <= 720`),
columns are clamped to 3..4. Wide x margin is `.06`, compact `.12`; wide y
minimum is `.20`, compact `.32`; y is capped at `.90`, and x is bounded by the
same margin (`web/src/desk/world.ts:159-193`). This default is deterministic;
dragging writes a user position and stops the grid from replacing it. Pixel
art is integer-true, axis-aligned and rest motion is `{phase:0, tilt:0,
scale:1}` (`world.ts:195-201`).

The icon law is 64×64 source art in a uniform cell. Selected and stale states
are generated files, not runtime CSS filters. A state badge is legal only when
a named live field supplies it (`docs/internal/DESK_GRAMMAR.md:11-18`).

## Window geometry contract

The following functions are pure except `workBand`/`clampRect` reading the
current CSS/viewport. `DESK_WINDOW` is generated from `web/design-tokens.json`
(`web/src/lib/tokens.gen.ts:15-21`):

| Constant | Value | Meaning |
|---|---:|---|
| `MARGIN` | 10px | viewport clamp margin |
| `GRAB` token | 72px | minimum title-head grab strip; frame CSS owns its hit area |
| `CASCADE` | 26px | saturated default-seat cascade step |
| `snapTop` / work top | 54px | below system bar |
| `snapBottom` / work bottom | 52px | above Dock |
| `HEAD` | 44px | title strip used for occlusion scoring |
| placement scan step | 32px | candidate grid increment |
| default minimum width | 320px | `DeskWindowFrame` fallback |
| default minimum height | 220px | `DeskWindowFrame` fallback |
| snap edge | 26px | left/right flank trigger |
| snap corner | 150px | four corner trigger region |
| Exposé gap | 18px | pick-grid gap |
| resize debounce | 150ms | viewport resize re-clamp debounce |

### Working band and placement

`workBand()` reads `--desk-work-top` and `--desk-work-bottom`; it falls back to
54/52px (`web/src/desk/components/window/windowGeometry.ts:14-29`).
`placeWindow(seed, existing, vw, vh, minW=320, minH=220)` performs this
algorithm (`windowGeometry.ts:32-93`):

1. Clamp width to `[minW, vw - 2*MARGIN]` and height to
   `[minH, max(minH, vh - top - bottom)]`.
2. Clamp the seed origin into the working band.
3. Score a candidate by `heads * 1e9 + overlapArea * 10 + distanceFromSeed`.
   A title overlap uses a 44px high strip. Thus a title overlap always beats
   any body overlap, and lower body overlap beats a longer move.
4. Scan x and y in 32px increments. Accept a candidate only when it improves
   the score by more than `.5`.
5. If every candidate overlaps a title, move the seed down/right by
   `26 * min(existing.length, 8)` and clamp again. This saturation path is
   intentionally allowed to shade bodies but preserves a usable title bar.

`clampIntoBand` applies the same size and boundary equations to saved geometry
on open, preserving the user's arrangement otherwise
(`windowGeometry.ts:95-110`). `clampRect` applies them during drag/resize using
the live viewport (`windowGeometry.ts:175-183`).

### Snap, resize and Exposé

`snapForPointer` returns null in the middle. A pointer within 26px of the left
or right edge gets a half-width tile. A pointer in a 150px corner region (with
the 54px top and 52px bottom bands applied) gets a quarter tile. Half widths
are `floor((vw - 3*MARGIN)/2)`; half heights are
`floor((vh-top-bottom-MARGIN)/2)` (`windowGeometry.ts:113-147`).

Resizing supports `r`, `b`, `br`, `l`, `bl`. Right/bottom edges add movement to
width/height. The left edge moves x and subtracts movement from width; when the
minimum bites, x becomes `base.x + base.w - minW` so the right edge stays fixed.
The result is clamped to the working band (`windowGeometry.ts:150-183`).

Exposé chooses `ceil(sqrt(count))` columns, enough rows for count, an 18px gap,
and centers an incomplete last row. Cells remain inside the band with an
additional 8px inset (`windowGeometry.ts:186-216`). MRU sorting preserves the
store order, with the front window last (`windowGeometry.ts:219-223`).

## Window lifecycle, focus and persistence

The frame lifecycle has one ID, one identity, one normal rect, one order entry,
and a minimized/maximized state. Opening calls `presentPanel`: a remembered ID
keeps its place and a new ID goes on top. Focus removes the ID and appends it;
closing calls `retirePanel`. The front window is the last open, non-minimized
registered ID (`web/src/desk/components/window/windowRegistry.ts:60-70`).

The frame opens as a `role="region"` and focuses its shell. Close returns focus
to the opener when it remains in the document. Ordinary windows coexist and do
not trap focus; only a menu/popover may use bounded focus behavior. Escape
inside a frame closes its open head menu first; a second Escape reaches the
window close path. These behaviors are asserted in
`web/src/desk/__tests__/windows.test.tsx:87-108` and `windows.test.tsx:250-285`.

Window actions are common semantic verbs:

| Verb | Pointer | Keyboard/registry | Store effect |
|---|---|---|---|
| focus/raise | shell pointer down or Dock chip | `focusOrRestoreApp` | append `panelOrder` |
| move | title head drag | no direct equivalent; snap commands remain available | update rect, persist on release |
| resize | left/right/bottom/bottom-corner grip | no direct equivalent | update clamped rect, persist on release |
| minimize | head/Dock menu | `⌘M` | add `panelMin`, do not persist |
| restore | Dock chip | app shortcut or Dock | remove `panelMin`, focus |
| maximize/restore | head menu or head double click | menu command | add/remove `panelMax`, preserve normal rect |
| close | head/Dock menu | `⌘W` | feature callback, retire ID |
| snap | edge release or Window menu | Window menu | save exact half tile |
| overview | Dock or `⌃↑` | `⌃↑` | Exposé pick grid; Escape cancels |
| cycle | Dock/keyboard binder | `⌃\`` / `⌃⇧\`` | MRU focus or restore |

The only persisted document is `hs.desk.workspace.v1`. Its exact shape is:

```ts
type DeskWorkspaceDocumentV1 = {
  version: 1;
  windowsById: Record<string, {
    id: string; kind: "surface"; applicationKey: string;
    scope: string | null; persistence: "workspace";
  }>;
  panel: { rects: Record<string, PanelRect>; order: string[]; max: string[] };
  zoneWindows: string[];
  zoneViewPrefs: Record<string, { view: "icons"|"list";
    sort: "name"|"kind"|"modified"; dir: "asc"|"desc" }>;
};
```

Only `panelSaved` rects are serialized. The ID grammar is
`^[A-Za-z0-9:_-]+$`; invalid rects, invalid window instances and invalid zone
preferences are dropped. Ordered IDs are unique and capped at 100. `panelMin`
is session-only and never appears in storage. Unknown versions and malformed
storage produce an empty workspace (`web/src/desk/store/workspaceStorage.ts:8-117`).

## Selection and command context

`selectedIds` is the Desk's current selection set; `toggleSelected`,
`setSelected`, and `clearSelection` are its store commands
(`web/src/desk/store/types.ts:244-251`). The world uses one current context:

```text
none -> current object -> selected group
       ^                     |
       +-- clear / Escape ---+
```

The current command target is `selectedRef` only when exactly one selected ID
exists (`web/src/desk/keymap.ts:71-74`). A multi-selection remains visible and
usable by context-aware surfaces, but single-object verbs ghost until one
object is current. The implementation currently exposes `selectedIds` and
`selectedRef`; there is no separate persisted anchor or window-internal
selection model. A future range/marquee anchor is therefore SPEC-DEBT, not a
current contract.

Current pointer grammar:

| Gesture | Result | Exceptions |
|---|---|---|
| spatial single click | select object | row/card controls keep their own click |
| spatial double click | open selected object | directory opens a Zone window |
| touch/pen tap | open | avoids unreliable double tap |
| object context menu | menu with selected object context | absent selection ghosts each object verb |
| drag object | set `draggingId`; valid target may light | drop is an entrance, not a move |
| Escape | close front transient/card according to mounted surface | settle mode consumes Escape in capture phase |

The current semantic list is the non-spatial keyboard surface. The repository
does not prove Shift/Ctrl range selection, marquee selection, or Select All in
the Desk store; those are proposed requirements with explicit gap status.

## Verb registry and actual matrix

`VERBS` is the sole registry. Each row has ID, label, menu/scope, optional key,
glyph/palette metadata, `ghost(context)` and `run(context)`
(`web/src/desk/verbRegistry.ts:28-62`). Menus, command palette, floor/object
menus, head menus and Dock menus derive from it. Ghosting keeps unavailable
verbs visible with a reason. The focused assertion confirms unique IDs, closed
scopes, object ghost reasons, derived Go entries, and exact bound key set
(`web/src/desk/__tests__/verbRegistry.test.ts:14-104`).

| Scope | IDs / behavior |
|---|---|
| Floor create | `desk.new-note`, `desk.new-decision`, `desk.new-knowledge`, `desk.new-agent`, `desk.new-workflow`, `desk.new-workbench`, `desk.new-zone`, `desk.new-thread`, `desk.new-project`; each creates in-world or opens the registered setup surface |
| Floor view | `desk.settle`, `desk.toggle-view`, `desk.arrange` (ghosts `Nothing moved`), `desk.refresh`, `desk.open-intelligence`, `desk.open-people`, `desk.intelligence-brief`, `desk.intelligence-overdue`, `desk.intelligence-find-receipt…`, `desk.intelligence-review-decisions` |
| Floor/window layout | `desk.overview`, `desk.reset-layout` ghost with `No window open`; `desk.reset-to-seed…` opens Settings where the in-world armed confirmation runs the destructive reset |
| Object | `object.open`, `object.info`, `object.ask-project`, `object.ask`, `object.continue-in-thread`, `object.edit`, `object.rename`, `object.duplicate`, `object.file`, `object.delete`, `zone.focus`; each checks kind/capability and names the refusal |
| Go | Generated from `DESK_TOOLS` and `DESK_APPLICATIONS`: Ask, Speak, Meetings, Agents, Settings, and every registered tool/app action. Existing open windows focus/restore instead of duplicating |
| Window | `window.close`, `window.minimize`, `window.cycle`, `window.cycle-reverse`, `window.snap-left`, `window.snap-right`, `window.maximize`; all ghost when no window exists |
| System | `system.search`, `system.sheet` |
| Thread | `thread.keep`, `thread.fork`, `thread.stop`, `thread.new`, `thread.mode`, `thread.prompt`, `thread.tools`, `thread.todo`, `thread.compact`, `thread.guardrail`; these are slash-command IDs whose composer owns execution, so registry `run` is intentionally empty |

The registry's actual key bindings are:

| Key | ID |
|---|---|
| `⌘N` / `⌘⇧N` | new Note / new Decision |
| `⌘⇧F` | settle |
| `⌃↑` | overview |
| `F2` / `Delete` | rename / delete selected object |
| `⌘I` | Ask AI |
| `⌘1`..`⌘4` | Speak, Meetings, Agents, Settings |
| `⌘W` / `⌘M` | close / minimize front window |
| `⌃\`` / `⌃⇧\`` | cycle / reverse cycle windows |
| `⌘K` / `⌘/` | search / shortcut sheet |

The keymap accepts Meta or Ctrl as the primary modifier but rejects both
together, suppresses repeats/IME, and refuses plain/typing-guarded chords in
inputs. Mac Delete and Backspace both match `Delete`
(`web/src/desk/keymap.ts:19-64,76-89`). There is no current platform-specific
shortcut table; the primary modifier abstraction is the implemented boundary.

## Menus and exceptions

The menu faces are the system menubar (`Desk`, `Object`, `Go`, `Window`), Floor,
object and Zone context menus, window-head menu, Dock chip menu, command palette
and shortcut sheet. All labels and keycaps derive from the registry; the
head/Dock adapter is pinned by `web/src/desk/__tests__/windowMenuRegistry.test.tsx`.
Unavailable menu capabilities remain visible and ghosted; ordinary in-content
dead verbs are withheld. Menu outside pointer-down and Escape dismiss it. A
head Escape closes the menu before it closes the window
(`web/src/desk/__tests__/windows.test.tsx:250-285`).

The destructive `desk.reset-to-seed` exception is intentional: the menu verb
opens Settings, where the user sees the reset scope and arms the confirmation;
the menu never destroys directly (`verbRegistry.ts:302-311`,
`web/src/desk/__tests__/verbRegistry.test.ts:58-72`). Object Delete dispatches
an `OBJECT_DELETE_REQUEST`; the rendered Desk owns the confirmation/receipt
path (`verbRegistry.ts:545-563`).

## Drag and drop contract

Internal object drops use `DROP_MATRIX`, which is data rather than component
logic (`web/src/desk/dropMatrix.ts:9-47`):

| Target | Accepted source kinds | Release label | Action |
|---|---|---|---|
| `recipe` | note, kb, meeting, artifact | Hold as source | ground-into |
| `chain` | note, kb, meeting, artifact | Hold as source | ground-into |
| `workflow` | note, kb, meeting, artifact | Hold as source | ground-into |
| `kb` | note, meeting, artifact, recipe | Add to Knowledge | file-knowledge |

Any unlisted pair returns `null` and is inert. Grounding holds material beside
the run verb; it never silently runs a model. Filing is a reversible membership
write. The current world rule says the source returns home after a drop and
valid targets use selected sprite state and a cursor verb
(`docs/internal/DESK_GRAMMAR.md:76-91`).

The glass accepts external files anywhere. It enters `armed`, refuses unknown
extensions with a named reason, imports transcript/audio through
`POST /api/meetings/import`, or sends calendar screenshots to
`POST /api/calendar/snapshot`; importing and extraction expose status and
refusal faces (`web/src/desk/components/GlassDropLayer.tsx:9-107`). This is an
exception to the internal object matrix because the browser file payload, not a
Desk primitive, is the source.

Current gaps are cross-window refiling, multi-object drops, the Record orb as a
drop target, pulling results out of windows, auto-scroll and keyboard destination
pickers (`docs/internal/DESK_GRAMMAR.md:229`). Until implemented, a consumer
must expose command/menu alternatives and must not claim these as shipped.

## Motion and state

The current visual state vocabulary is `idle`, `active`, `working`, `success`,
`warning`, `failure`, `unreachable`; every state uses icon plus text
(`web/src/desk/surface/contract.md:5-17`). Surface transitions use tokenized
duration/easing and reduced motion removes animation. Window open, close,
minimize, restore and origin motion use WAAPI transform/opacity; origin-open is
240ms, origin-close 200ms, ordinary close 140ms, Dock flight 220ms, fit-content
growth 200ms. These values are in `DeskWindow.tsx:250-310,445-490` and are
compositor properties. No animation is authoritative state.

The current component exception is `SurfaceLedgerRow`: the row is a `div
role="button"` because a trailing action cannot be nested in a button. The
trailing slot stops click and key propagation. This is source-derived and
asserted by surface ledger tests; it is not permission to add raw buttons to
new faces.
