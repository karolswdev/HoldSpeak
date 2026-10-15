# Voice canvas — inset preference sheets

DRAFT design — root reviewed the direction; owner judgment remains pending.
The library variants below are implemented and hold for SHIP.

This canvas uses the production `DeskWindowFrame`, wings, footer, hotkey
capture, native gadgets, table, and library Buttons. Local wrappers preserve
the reviewed composition as an artboard for comparison with the product.
Values are synthetic. The shared surface kit now implements the opt-in
composition changes below; this worker changed no Settings bindings.

Render `canvas/index.html` from the repository-root Vite canvas server at
1440 × 900 and 393 × 852. The default state has two symbols. Add
`?symbols=empty` for the empty state. Add symbol, boolean changes, language,
hotkey capture, and armed Forget act on local canvas state.

The inset sheet uses an engraved legend, an etched outline, and the existing
paper well material (`--wb-well`). It has no nested window bar, toolbar,
card shadow, or rounded card. Composition stops at 960 px. Labels use a
bounded 118–160 px column beside the value column. The left column places
the key, language, and typing switches together. Wake word follows. The
right column holds the symbol dictionary. At 920 px or less, the same
source order becomes one column bounded at 620 px.

## Implemented primitive API

| Library species | Opt-in addition | Responsibility |
| --- | --- | --- |
| `GadgetGroup` | `material?: "default" \| "inset"`; `actions?: ReactNode` | Inset sheet with quiet engraved legend. An actions slot after the sheet content uses flex with bounded library Buttons. Defaults retain current rendering. |
| `GadgetRow` | `controlWidth?: "standard" \| "short" \| "full"` | `standard` reserves a consistent value column, 190 px on the desk and 172 px in a narrow sheet. `short` keeps compact key/boolean values aligned within that column. `full` spans long fields. The opt-in inset group supplies the common row rhythm. |
| `CheckGadget` | extend `variant` with `"state"` | Keep the real checkbox input and square well; add a visible On/Off word inside its label. The complete check and word own one target. Retain focus, disabled, keyboard, and native change behavior. No second button or switch implementation. |
| `GadgetTable` | `layout?: "table" \| "fields"` | Default stays unchanged. `fields` repeats each supplied head beside its cell below the narrow breakpoint. Keep row identity, native input labels, roving focus, and armed row verbs. The canvas `NamedCell` adapter demonstrates the labels which the library generates from `head`. |
| `SurfaceColumns` | `variant?: "default" \| "preferences"` | Retain the existing `main` and `side` slots. The opt-in preference layout uses equal bounded columns with a shared gap and one column below the preference breakpoint. The default 3:2 layout remains unchanged. |
| `GadgetDivider` | exported semantic `hr` | Native etched rule between the capture and typing rows in the first sheet. |

The implementation adds no preference-specific input family, schema renderer,
second form framework, or new column component. The additions are documented
in `surface/contract.md`. Existing native inputs and Buttons carry behavior.
The canvas local column wrappers preserve the reviewed `SurfaceColumns`
direction. The implemented table derives labels directly from `head`.

For Voice, keep the current data producers and update paths in
`SettingsCore.tsx:1766–1935`. `HotkeyCapture` keeps its key capture behavior.
Its sheet receives the same material through composition. The group actions
slot owns Add symbol in both the empty and populated states; `GadgetTable`
does not receive `onAdd` in this composition. Existing `verbs` permits the
armed Forget Button shown here. Labels at phone width come from table heads,
not a Settings selector that assumes cell order.

## Tuesday

The owner can see and set the hold key, language, preview, and commands in
the first sheet. Their labels remain beside their controls at 393. Symbols
keep readable labels and native 44 px fields and row actions when narrow.
Production rendering and pointer ownership are pending root verification.

The design beat ran no tests, install, staging, or commits. The subsequent kit
build runs only `gadgets.test.tsx`, through the isolated lock helper. Proof and
remaining verification are recorded in `../audit-kit.md`.
