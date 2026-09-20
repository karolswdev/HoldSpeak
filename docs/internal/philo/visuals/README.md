# HoldSpeak Desk artboard gallery

This is the Philo visual specification fixture for Story 05, Desk. It is an
authored gallery of annotated compositions. It is not owner-use evidence and
it does not claim that the proposed variants are shipped.

The fixture renders against the requested source anchor
`675401a857b85336d4acaa8c65383dfc9636e4c8` as described in the Philo package.
It imports the production `DeskWindowFrame`, Signal `Button`, Desk surface
barrel and generated tokens. It uses synthetic state and browser storage only;
there is no API call, RuntimeBus connection, owner database access or real
filesystem operation.

## Open the gallery

The clone-local Node 22 environment is in `.tmp/philo/env.sh`.

```sh
source .tmp/philo/env.sh
node web/node_modules/vite/bin/vite.js --config docs/internal/philo/visuals/vite.config.mjs
```

Open `http://127.0.0.1:4399/`. The top strip selects every artboard. A direct
fixture URL is useful when reviewing a single face:

```
/?artboard=meeting-review&bare=1
```

The capture command renders the 19 states at 1440px wide and the primary
faces at 393px compact width. It writes the PNGs in `assets/`.

```sh
source .tmp/philo/env.sh
node docs/internal/philo/visuals/capture.mjs
```

## What is current and what is proposed

`AUTHORED · SOURCE-BACKED` means that the composition is a visual reference
for an existing Desk contract. It does not replace a production walk or say
that the screenshot itself is product evidence. The source-backed groups are
the spatial/list Desk, selection/context, windows, Speak, Meeting review,
Thread, Agents, Settings, Info, drop matrix, command deck and system shade.

`AUTHORED · PROPOSED` means that the artboard makes a requirement visible for
future work. `high-contrast` is the `NFR-THEME-002` variant. `pseudo` is the
`NFR-I18N-001` variant. The gallery keeps these faces labelled as future
variants and does not imply light theme, high contrast, pseudo-locale, RTL or
host support is implemented.

The fixture deliberately names synthetic boundaries in the face. For example,
Speak says `FIXTURE STATE · no microphone or backend call is made`; the drop
refusal says `FIXTURE · source-backed matrix`, and the future faces carry their
SRS IDs. These labels prevent a composed state from becoming a fake backend
outcome.

## Artboards and interaction annotations

| Artboard | State and annotation | Acceptance link | Wide shot | Compact shot |
| --- | --- | --- | --- | --- |
| Desk · spatial | Populated 6-object Workbench. Single object identity is visible in the spatial representation; pixel art carries rest state. | `FR-DESK-002`, `FR-OBJ-001` | [desk-spatial-wide.png](assets/desk-spatial-wide.png) | [desk-spatial-compact.png](assets/desk-spatial-compact.png) |
| Desk · list | The same object records in a semantic list. `LIST` and `SPATIAL` are library Buttons; row verbs stay at the row. | `FR-DESK-002`, `NFR-A11Y-001` | [desk-list-wide.png](assets/desk-list-wide.png) | [desk-list-compact.png](assets/desk-list-compact.png) |
| Desk · selected + menu | Selected `RuntimeBus boundary` has a visible sprite/rim treatment. Context commands use the shared vocabulary and stay beside the target. | `FR-OBJ-002`, `FR-MENU-001` | [desk-context-wide.png](assets/desk-context-wide.png) | [desk-context-compact.png](assets/desk-context-compact.png) |
| Desk · drawer | Project drawer owns its body and retains the source/egress facts in the window. | `FR-WIN-001` | [desk-drawer-wide.png](assets/desk-drawer-wide.png) | — |
| Windows · coexist | Meeting and Thread windows share the Desk and retain independent focusable heads. | `FR-WIN-001`, `FR-WIN-004` | [windows-two-wide.png](assets/windows-two-wide.png) | — |
| Windows · Exposé | Exposé is a review posture over the same two windows. `RETURN TO FRONT` is the one next verb. | `FR-WIN-003` | [windows-expose-wide.png](assets/windows-expose-wide.png) | — |
| Speak · ready | One admitted speech run: focused input, local egress and explicit delivery. | `FR-STATE-001` | [speak-ready-wide.png](assets/speak-ready-wide.png) | [speak-ready-compact.png](assets/speak-ready-compact.png) |
| Speak · progress | Capture, transcribe and deliver are honest stages. The fixture does not start a run. | `FR-STATE-001` | [speak-progress-wide.png](assets/speak-progress-wide.png) | [speak-progress-compact.png](assets/speak-progress-compact.png) |
| Meeting · review | Retained architecture meeting with four concrete segments, three review records and local egress at the footer. | `FR-INFO-002` | [meeting-review-wide.png](assets/meeting-review-wide.png) | [meeting-review-compact.png](assets/meeting-review-compact.png) |
| Thread · retained | One thread with three turns and two frozen sources. `REPLY`, `PIN`, `ATTACH SOURCE` and `SEND` stay in the library grammar. | `FR-INFO-001` | [thread-wide.png](assets/thread-wide.png) | [thread-compact.png](assets/thread-compact.png) |
| Agents · workbench | Two retained workbench records. The face states that process status is not inferred from a record fixture. | `FR-OBJ-001` | [agents-wide.png](assets/agents-wide.png) | [agents-compact.png](assets/agents-compact.png) |
| Settings | In-world settings with token controls and a boundary section. No modal is introduced. | `NFR-THEME-001` | [settings-wide.png](assets/settings-wide.png) | — |
| Info | Object properties and content stay in the Info window. `OPEN` and `RENAME` are window-scoped verbs. | `FR-INFO-001`, `FR-INFO-002` | [info-wide.png](assets/info-wide.png) | — |
| Drop · valid | The valid matrix pairs `Note → Knowledge` with `FILE INTO KNOWLEDGE` and `Note → Recipe` with `GROUND INTO RECIPE`. | `FR-DND-001` | [drop-valid-wide.png](assets/drop-valid-wide.png) | — |
| Drop · refusal | `Recipe → Knowledge` is inert and has a named reason. No write or fake receipt is shown. | `NFR-ERR-002`, `FR-DND-001` | [drop-refusal-wide.png](assets/drop-refusal-wide.png) | — |
| Command palette | Registry vocabulary and keycaps are visible together. | `FR-MENU-001` | [command-wide.png](assets/command-wide.png) | — |
| System shade | Shade is a bounded chrome state with one return path. It is retained as a fixture because the requirement is a state of the Desk shell. | `FR-WIN-001` | [shade-wide.png](assets/shade-wide.png) | — |
| High contrast | Proposed token-only contrast variant. Geometry, commands and state names stay fixed. | `NFR-THEME-002` | [high-contrast-wide.png](assets/high-contrast-wide.png) | — |
| Pseudo-locale | Proposed expanded-label fixture. Stable command/object IDs remain unchanged. | `NFR-I18N-001`, `NFR-I18N-002` | [pseudo-wide.png](assets/pseudo-wide.png) | — |

The primary faces for the compact acceptance pass are Desk (spatial/list and
selected), Speak, Meeting review, Thread and Agents. The generated compact
shots are intentionally viewport shots at 393×844; the compact window uses
the production sheet rule and its body scrolls when the transcript is longer
than the viewport.

## Composition contract

Every window in the fixture enters through the production
`DeskWindowFrame` at [`web/src/desk/components/DeskWindow.tsx`](../../../../web/src/desk/components/DeskWindow.tsx) (line 510).
The frame supplies the title bar, icon, window verbs, focus return, placement,
compact sheet and resize affordance. Fixture content supplies only the
synthetic record values and uses the frame's `.desk-surface-body` container.

Every authored verb uses the production Signal `Button` at
[`web/src/components/signal/Signal.tsx`](../../../../web/src/components/signal/Signal.tsx) (line 21).
The fixture does not add an inline button kit. Rows, sections, wells, state
chips, egress chips, progress plans, receipts and footer are imported from
the supported surface barrel at
[`web/src/desk/surface/index.ts`](../../../../web/src/desk/surface/index.ts) (line 3).

The CSS imports the generated material and typography from
[`web/src/styles/tokens.css`](../../../../web/src/styles/tokens.css), plus
the existing window, dock and surface CSS. The gallery's CSS only lays out
the stage, annotations and fixture world. Existing pixel art is loaded from
[`web/public/desk/sprites`](../../../../web/public/desk/sprites) and the
rainy-city atmosphere is loaded from
[`web/public/desk/atmospheres/rainy-city.webp`](../../../../web/public/desk/atmospheres/rainy-city.webp).

The focus annotation on each artboard is:

```
window shell → head verbs → surface verbs → records → footer egress
```

`Tab` follows the production Button and surface control semantics. `Escape`
closes the authored window through the production frame handler. The fixture
does not claim that its static artboard selector proves the full application
keyboard path.

## Evidence and limits

The local checks for this lane are intentionally narrow:

- `vite build --config docs/internal/philo/visuals/vite.config.mjs` passed.
- `capture.mjs` rendered 19 wide states and 8 compact primary states.
- Browser assertions recorded `bodyWidth === innerWidth` and no element
  crossing the viewport edge for each rendered shot.
- Representative wide and compact shots were inspected: Desk spatial,
  Speak ready/progress, Meeting review, Thread, selected context, drop
  refusal, high contrast and pseudo-locale.

These are fixture checks. They do not prove production behavior, backend
outcomes, accessibility conformance of the whole product, real drag/drop,
RuntimeBus delivery, host permissions, localized message formatting or an
owner desk walk. The gallery remains on hold for SHIP until the parent lane
records its own review and source-backed product evidence.
