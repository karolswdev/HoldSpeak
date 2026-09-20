# HoldSpeak Desk design specification

**Status:** current implementation normalized into a portable design contract.
This document is an implementation specification, not a greenfield visual
proposal. The Desk keeps Workbench object behavior and Intuition interaction
discipline through the existing Signal/Desk material. Current facts cite source
and tests. Proposed work is marked `SPEC-DEBT`, `PARTIAL`, or `UNIMPLEMENTED`.

The product source snapshot is `675401a857b85336d4acaa8c65383dfc9636e4c8`.
[External research](EXTERNAL_RESEARCH.md), the [desktop host ADR](adr/desktop-host.md)
and [visual fixtures](visuals/README.md) distinguish authored specifications
and research probes from current product evidence.

## Design premise

The Desk is the operating surface. `/` owns the Desk, and product capabilities
open as Desk windows. The current architecture has one React/Vite shell, one
Zustand store, one Pixi/WebGL world, DOM-composited windows and one typed HTTP
and RuntimeBus boundary. See [`DESK_ARCHITECTURE.md`](../../DESK_ARCHITECTURE.md)
for the full census.

The design asks five questions of every object and surface:

1. What is the object or result?
2. What is selected and which command context is active?
3. What can the user do now, including why something cannot run?
4. What is happening and where did the result go?
5. How can the same job be done without a mouse?

The first user is a Senior Software Architect with reports. The Desk therefore
optimizes for fast return to work, visible state and durable records. It does
not add an interface merely to explain another interface.

## Material foundations

### Token graph

```text
primitive --p-* raw values in web/design-tokens.json
    ↓
semantic --bg, --surface-*, --text*, --accent*, status, focus, motion
    ↓
component --desk-*, --glow-*, --zone-tint-*
    ↓
theme aliases -- current Signal dark; future high-contrast/light aliases
    ↓
DOM + Pixi renderers + future bounded host chrome
```

`web/design-tokens.json` is the source. `generate-tokens.cjs` creates
`web/src/styles/tokens.css` and `web/src/lib/tokens.gen.ts`; `tokens:check` and
`tokens:gate` enforce drift and reject raw component CSS values
(`docs/internal/DESIGN_SYSTEM.md:8-30`). Components may consume semantic or
component tokens only.

| Family | Current contract |
|---|---|
| z ladder | stage -1; canvas 0; world overlay 25; chrome 30; Dock-under 40; windows 42+; Dock 80; transient 81; popover 82 (`web/src/lib/tokens.gen.ts:6-13`, `tokens.css:240-247`) |
| window geometry | margin 10px, grab 72px, cascade 26px, snap top 54px, snap bottom 52px (`tokens.gen.ts:15-21`) |
| material | opaque `--desk-window-fill` from `--surface-1`; head fill `--surface-2`; front head `--surface-3`; no blur or Gaussian shadow (`tokens.css:275-284`) |
| depth | raised bevel `--bevel-light`/`--bevel-dark`; sunken etch `--etch-dark`/`--etch-light`; front keyline `--border-strong` (`tokens.css:281-284`) |
| type | display 26px/650; primary 15px/600; body 13px; detail 12px; section label 11px mono (`tokens.css:291-323`) |
| surface density | row min 40px; row x pad 10px; row gap 2px; section gap 18px; body 13px; detail 12px (`tokens.css:291-297`) |
| control | default dense control height 36px; Signal primary target 44px; effective dense target at least 24px (`DESIGN_SYSTEM.md:24-46`) |
| motion | named duration/easing tokens; reduced motion sets durations to 0ms (`tokens.css:330-335`) |
| responsive | `.desk-surface-body` is `container-type:inline-size`, name `surface`; one 560px container breakpoint (`DESIGN_SYSTEM.md:143-158`) |

The current theme is dark Signal. High contrast and light themes are semantic
token work, not alternate interaction models. `THEME-002` records them as
roadmap requirements because this tree does not provide a complete light or
high-contrast token set.

### Object material

World objects use 64×64 pixel art at 1:1 in a uniform cell. Rest, selected and
stale are real generated assets. Selection must have the selected image/rim and
label treatment; color alone cannot carry state. A named field alone may create
a badge. The default grid is deterministic, while a dragged position is user
arrangement and survives until reset (`web/src/desk/world.ts:159-201`,
`docs/internal/DESK_GRAMMAR.md:11-18`).

### Surface material

Window bodies are one material. A surface uses `SurfaceVerbs` for primary
verbs, `SurfaceSection` for hairline groups, dense rows for records, a well for
machine material, and `SurfaceFooter` for egress/receipt/verbs. It does not
nest dashboard cards. The surface barrel at
`web/src/desk/surface/index.ts:3-149` is the supported import path. The
surface contract closes the state vocabulary at
`idle | active | working | success | warning | failure | unreachable`, requires
icon plus text, roving focus for composites, ARIA-expanded disclosures,
polite transition announcements and reduced motion
(`web/src/desk/surface/contract.md:3-27`).

## Atomic documentation taxonomy

The levels below classify existing exports. They do not require moving source
directories.

| Level | HoldSpeak meaning | Examples |
|---|---|---|
| Foundation | tokens, type, z, geometry, state and icon rules | token graph, `PanelRect`, `ChipState` |
| Atom | one semantic control or fact | `StateChip`, `EgressChip`, `MicButton`, `CheckGadget` |
| Molecule | one coherent task or row grammar | `EditInPlace`, `ConfirmVerb`, `StringGadget`, `FilterTokens`, `SurfaceLedgerRow` |
| Organism | substantial window or region | `DeskWindowFrame`, `SurfaceLedger`, `SurfaceFooter`, Dock, Exposé, Switcher |
| Template | posture/layout independent of record values | working, reviewing, configuring, drawer, Info, thread and meeting review |
| Page | mounted Desk or hosted core instance | spatial Desk, list Desk, arrival, Presence, Speak, Meetings, Agents, Settings |

The exact component catalogue, props, states, token families, source symbols,
consumers and inspected tests is machine-readable in
[`components-catalogue.json`](data/components-catalogue.json). The catalogue
has one record for every component exported from `desk/surface` and does not
invent props that are absent from source.

## Interaction specification

### Selection and opening

The spatial world uses single click to select and double click to open. Touch
and pen tap opens directly. `Enter` opens the current object through the same
registered `object.open` command. A directory opens a Zone window; all other
supported object kinds open their declared pullout/window. `selectedIds` is
store state; a single selected ID becomes `selectedRef`, while a multi-selection
has no single-object command target (`web/src/desk/keymap.ts:66-74`).

The current tree does not implement a persisted anchor, range selection,
marquee, or Select All. Those remain `SPEC-DEBT`; they must not be documented as
current behavior. Selection remains visible in the semantic list representation
and is not discarded merely because a window gains focus.

### Focus and command target

These are different facts:

| Fact | Meaning | Owner |
|---|---|---|
| active window | front non-minimized window in `panelOrder` | window registry/store |
| DOM focus | element receiving keyboard events | browser/React |
| selected object | current world/list selection | Desk store |
| command target | object/window a registered verb will act on | registry context |

Opening a window focuses its frame and records the opener. Closing returns to
the opener when still mounted. An ordinary window is a region and does not
trap focus. Menus/popovers may bound focus and return it on dismissal. The
front window is the last open non-minimized registered ID
(`web/src/desk/components/window/windowRegistry.ts:60-70`).

### Keyboard

The registry key fields are the only document-level bindings. `keymap.ts`
translates `⌘` into Meta on macOS or Ctrl elsewhere, rejects Meta+Ctrl and Alt
together, ignores repeats and composition, and refuses typing-guarded chords in
an input (`web/src/desk/keymap.ts:19-89`). Pointer and keyboard commands call
the same `Verb.run`.

| Command family | Current keys | State |
|---|---|---|
| create Note/Decision | `⌘N`, `⌘⇧N` | IMPLEMENTED |
| open Ask / search / shortcut sheet | `⌘I`, `⌘K`, `⌘/` | IMPLEMENTED |
| app launch/focus | `⌘1` Speak, `⌘2` Meetings, `⌘3` Agents, `⌘4` Settings | IMPLEMENTED |
| object edit/delete | `F2`, `Delete`/Backspace | IMPLEMENTED; delete is confirmation-owned |
| front window | `⌘W`, `⌘M` | IMPLEMENTED |
| cycle | `⌃\``, `⌃⇧\`` | IMPLEMENTED |
| overview | `⌃↑` | IMPLEMENTED |
| menu traversal | Arrow keys, Enter/Space, Escape through menu implementation | IMPLEMENTED; source guard in `web/src/desk/__tests__/workMenu.test.tsx` |
| range/marquee/Select All | none | SPEC-DEBT |
| platform-specific browser conflict table | none | SPEC-DEBT |

### Menus

The verb registry supplies the menu bar, context menus, window-head menu, Dock
chip menu, command deck and shortcut sheet. Every verb has stable ID, label,
scope, applicability/ghost reason and runner. Ghosted menu rows teach the
vocabulary; in-content dead verbs are withheld. `windowMenuAdapter.tsx` derives
head/Dock labels and keycaps from `verbById`; `windowMenuRegistry.test.tsx`
inspects this relationship. `thread.*` verbs are registered slash IDs with
empty registry runners because `ThreadComposer` owns their execution. This is
an intentional adapter boundary, not a second command model.

Destructive work stays in-world. Reset opens Settings to show and arm the
reset scope; object delete dispatches `OBJECT_DELETE_REQUEST`; `ConfirmVerb`
arms on first press and fires on second, self-disarming after 3000ms
(`web/src/desk/surface/Surface.tsx:1216-1270`). Product modal dialogs remain
prohibited. Native browser/OS permission dialogs are the only external
exception.

### Drag and drop

The current internal matrix is exactly:

```text
recipe  <- note | kb | meeting | artifact : Hold as source / ground-into
chain   <- note | kb | meeting | artifact : Hold as source / ground-into
workflow<- note | kb | meeting | artifact : Hold as source / ground-into
kb      <- note | meeting | artifact | recipe : Add to Knowledge / file-knowledge
```

Unlisted pairs are inert. Grounding holds input beside an explicit run verb;
filing is an add-only membership write with a separate removal path. Valid
targets light, the cursor carries the release verb and internal drop returns
the source home (`dropMatrix.ts:19-47`; `DESK_GRAMMAR.md:76-91`).

External file drops are a separate glass surface: `dragenter` arms the veil,
unknown files refuse with a named reason, transcript/audio posts to
`/api/meetings/import`, and calendar screenshots post to
`/api/calendar/snapshot` (`web/src/desk/components/GlassDropLayer.tsx:21-107`).
Cross-window refiling, multi-object drops, keyboard destination picking,
auto-scroll, orb drops and extraction from windows are UNIMPLEMENTED.

## Responsive and compact behavior

The Desk chooses list mode above 16 objects only when compact and no explicit
view preference exists (`web/src/desk/store/types.ts:49-72`). User selection
wins over density defaults. Surface internals use `@container surface`, not
viewport queries. Wide layouts may show split master/detail and columns; at a
560px-or-less surface container they stack or let the detail replace the master.
Window frame compact mode activates at `max-width:720px`: windows become
bottom-sheet compositions, maximize is omitted from head menus and the Dock
uses its compact layer (`DeskWindow.tsx:520-600`,
`web/src/desk/__tests__/windowMenuRegistry.test.tsx`).

The current implementation has no complete pseudo-locale, RTL, light-theme or
high-contrast visual fixture. These are requirements in the SRS with status
UNIMPLEMENTED or SPEC-DEBT. The portable rule is: retain the same object,
window, command and state identities; change composition only.

## Motion

Every moving part carries meaning:

| Moment | Current implementation | Reduced motion |
|---|---|---|
| window origin open/close | WAAPI transform/opacity from object point; 240/200ms | appear/disappear |
| ordinary close | scale 1 → .96, opacity 1 → 0; 140ms | immediate close |
| Dock minimize/restore | transform/opacity to/from Dock chip; 220ms | state transition |
| fit-content growth | height transition; 200ms | CSS content size |
| snap ghost | static tile follows pointer | static tile |
| selected/new/drop | state image/ring/glow | state image/ring immediately |
| async outcome | state chip/receipt changes | same text/state, no animation |

Motion uses transform/opacity or bounded height; frame drag/resize has no
transition. Reduced-motion is read through `useReducedMotion` and media rules.
World bob is presentation only and stops while dragging/editing.

## Accessibility and language

The current baseline provides native checkboxes/radios/selects/inputs,
ARIA-labelled regions, `aria-expanded` disclosures, roving rows, menu keyboard
patterns, status/alert surfaces, focus-visible tokens and `MicButton` on text
inputs. The catalogue records the exact oracle for each component.

The SRS target is WCAG 2.2 AA. Product acceptance also requires:

- semantic list parity for spatial objects;
- keyboard path for every pointer verb;
- non-drag pointer operation for every drag action;
- focus never fully hidden by authored UI;
- state expressed by text/icon as well as color;
- meaningful transition announcements only;
- 200% zoom/reflow and long labels without clipping;
- product language from a future localization catalogue, with stable internal IDs;
- simple English, no explanatory walls in the UI, and one true empty-state line.

The exact current gaps are requirements `NFR-A11Y-006`, `NFR-I18N-001` through
`NFR-I18N-004` and `NFR-THEME-001` through `NFR-THEME-003` in
[`SRS.md`](SRS.md). No external research claim is repeated here; the later
research artifact owns primary-source citations.

## Acceptance and evidence

At implementation time the design is accepted only when the source-backed
contracts and proposed gaps are clear in tests. Current focused evidence names:

| Contract | Assertion source |
|---|---|
| placement, clamp, snap, resize, Exposé | `web/src/desk/__tests__/shell.test.tsx:125-285` |
| window coexistence, persistence, focus, menus | `web/src/desk/__tests__/windows.test.tsx:27-285` |
| registry uniqueness/ghosting/keys | `web/src/desk/__tests__/verbRegistry.test.ts:14-104` |
| key parser and dispatch | `web/src/desk/__tests__/keymap.test.ts:16-86` |
| drop matrix | `web/src/desk/__tests__/dropMatrix.test.ts:6-43` |
| surface state/ARIA/roving/scroll | `web/src/desk/surface/__tests__/` focused files |
| route demotion | `web/src/routes.test.ts:1-220` |
| RuntimeBus lifecycle | `web/src/runtime/RuntimeBus.test.tsx` |

No owner glass walk or 1440/393 shot is claimed by this documentation lane.
