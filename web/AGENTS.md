# Web Desk — interface development

Follow the [root guide](../AGENTS.md). Read the [UX canon](../docs/internal/UX-CANON.md),
current sections of the [Design System](../docs/internal/DESIGN_SYSTEM.md),
[surface contract](src/desk/surface/contract.md) and
[design author map](README.md#design-author-map) before changing a face.
Older canvases and nearby legacy code do not override current material or APIs.

## Compose the Desk

- The OS owns windows. Use `DeskWindowFrame`; do not build a feature shell,
  modal, full-screen wizard or route that ejects the user from the Desk.
  The frame owns title, wings, focus, drag/resize, geometry and compact form.
  Reuse the compositor's mounted-front authority (`computePlanes().front`)
  and its helpers; an announced hub row is not a mounted front window.
- Register application identity in `src/desk/applications.ts`. Register a
  supported hub window in `holdspeak/services/desk_window_service.py` when
  needed. Deep links in `src/routes.tsx` open the correct Desk state.
  Do not create a second menu, shortcut or application registry.
- A core accepts `CoreProps` and scope from its host. Keep router hooks,
  `window.location`, page chrome and window-placement logic out of cores.
  Use title, Back, wings and interior slots exposed by the surface library.
- The normal window reads: **title bar → one Toolbar → edge-to-edge content
  → one StatusBar**. Reuse the appropriate reading, editing, list or settings
  pattern. Do not repeat the title as a page H1, nest cards in cards, float
  verbs in empty bands or add a second footer.

## Use the framework

Import surface species from `src/desk/surface/index.ts`, the public barrel.
Use the library `Button` from `src/components/signal/Signal` for every verb and
`WorkMenu` from `src/desk/components/DeskMenu` for menus. Do not add raw buttons,
clickable divs or hand-built menu/focus behavior. Follow documented direct
import exceptions, such as `DeskEditor`; old private imports are not a model.

| Need | Existing species or pattern |
| --- | --- |
| Actions and feedback | `Toolbar`, `ToolbarFold`, `StatusBar`, `DotWord`, `StateChip` |
| Text and preferences | `StringGadget`, `PadGadget`, `CycleGadget`, `CheckGadget`, `GadgetGroup`, `GadgetRow` |
| Lists and inspection | `ListView`, `SurfaceRows`/`SurfaceRow`, `SurfaceSplit`, `ScrollHint` |
| Long reading and sources | `ReadingDocument`, `Material`, citation/source doors |
| Conversation and editing | `ComposerWell`, `DeskEditor`, captured voice-target and draft patterns |
| Loading, empty, refusal, retry | `SurfaceState`, `ActionNotice`, existing plain-failure mapping |
| Disclosure and inline confirmation | `FoldGadget`, `Disclosure`, `ConfirmVerb`; in-flow wells |
| Real running work and receipts | `ProgressPlan`, `Receipt`, `SurfaceFooter` where that host uses it |

Open **Components** (`/design/components`) for executable patterns. Its local
fixture IO demonstrates a composition; it does not prove a real provider or
a live feature uses the complete pattern. Check an active consumer too.
If a recurring species is missing, extend the shared library, its public
barrel, contract and matching reference example in the same change.

## Material, layout and input

- Follow the current **Workbench meets Pop!_OS** shell: fine frames, cool
  paper, restrained rounding, soft depth and quiet sans controls. Historical
  Steel bevels and hatched titles are not the current shell treatment.
  Use the **Icons D** flat front-on family and shared sprites/glyphs; do not
  invent emoji icons, tilted illustrations or a new icon system per feature.
- `design-tokens.json` owns values. Change tokens there, then run
  `npm run tokens` from `web/`; do not hand-edit generated CSS/TS mirrors.
  Reuse shared material and spacing rules instead of copying their skin.
  Do not add raw colors, z-index or duration literals to feature CSS.
- Interior reflow uses **`@container surface`**. A narrow window on a wide
  desk still needs a narrow layout. Use the shared compact-viewport rule for
  frame policy; do not clone it into a feature. Keep one primary content
  scroller; bounded editor, terminal, code/table and preview wells are valid
  exceptions. Titles can shrink (`min-width: 0`); actions keep their targets.
- At 393 px, controls own real 44×44 px targets and strips fold by measured
  fit into the library menu. Do not clip actions or make a toolbar scroll
  sideways. Check hit ownership, not only a large bounding rectangle.
  Narrow settings use one Back path, supplied to the frame when appropriate.
- Keep visible focus, accessible names, native input/radio semantics, menu
  return focus and library roving behavior. Test keyboard operation and the
  destination of Escape; do not steal editor, selection or IME keys.
  Respect reduced motion. New motion uses shared duration/easing tokens and
  compositor-friendly properties.
- Every text-entry flow keeps the shared microphone affordance and one mic
  authority. Capture the editor/resource target before async work. Preserve
  selection, composition, undo and retained voice text if insertion fails.
  Do not let a late answer insert into a different document.

## Words and honest state

Use short labels, verbs and facts in simple sentence case. No helper essays,
marketing copy, visible snake_case wire keys or decorative uppercase. Preserve
proper names and acronyms through the shared word formatters; do not force
capitalization with CSS. Mono is for code and IDs, ordinary metadata is quiet
sans, and readable text has a 12 px floor.

Use the library states (`idle`, `active`, `working`, `success`, `warning`,
`failure`, `unreachable`) with an icon and word, never color alone. Map domain
states deliberately. Omit zero-count chrome; an empty face has one true line
and a useful next action. A progress plan is for work that actually runs.

Disclose egress at the **choice or act**: Send preview/confirm, Engines,
Accounts, Destinations, Setup or the Door. Do not add host, IP, LAN/cloud or
scope chips to ordinary working rows, toolbars or status bars. An engine is
named by its name. Use the existing disclosure/hover contract for the verb.

## Data and recovery

Use typed app API functions through `src/lib/api.ts` and the shared
`RuntimeBus`. Do not add direct feature `fetch` calls or another general
`/ws` connection. Filter live frames to the relevant entity; a window-only
change must not cause every app to reread its data. Clean up subscriptions.

Keep view selection and transient busy/error state local. Hub-owned domain
state and shared window state remain authoritative across browsers. Protect
reads from stale completion and writes from revision conflict. Use the
acknowledged entity or an explicit refresh after a successful write.

Show success only for the acknowledged value. Preserve newer edits through
an older save, retain input on failure and offer a useful retry. Keep the
receipt visible in the branch the press leaves on screen. Loading must
resolve to data or a named failure; do not hide refusals as empty success.
A 404 means empty only where the endpoint contract explicitly defines it.

## Examples and verification

Use these as examples of the named responsibility, not whole-file approval:

- `src/desk/programs/ProgramsWindow.tsx`: Toolbar/list/StatusBar composition;
  `programs/api.ts` and `model.ts`: typed app boundary and wire-to-face mapping.
- `src/pages/cores/settingsWindow.tsx`: shared preference rail/pane and compact
  Back; `surface/contract.md`: acknowledged save and captured editor patterns.
- `src/desk/calls/CallsWindow.tsx`: readiness words, shared Calls/Phone hosting
  and app-local interaction state.

Follow the root guide's test tiers, isolation and lock. App tests use recorded
real hub answers and assert the rendered outcome after a press, including the
relevant refusal/recovery state. Use real-browser checks for pointer, focus,
keyboard, touch or geometry claims. The required quick check already runs the
Desk sweep at 1440 and 393; opt into PNG capture with `DESK_SWEEP_SHOTS=1`
and inspect the changed faces' shots against the canvas. Include a narrow window on a wide desk when reflow changes.

For tokens or shared components, also run the relevant `tokens:check`,
`tokens:gate`, `guard:architecture` or type check from `web/package.json`.
These checks supplement behavior tests. Do not expand allowlists to make new
violations pass. A local passing check does not establish owner acceptance;
the owner judges appearance live on the deployed Desk.
