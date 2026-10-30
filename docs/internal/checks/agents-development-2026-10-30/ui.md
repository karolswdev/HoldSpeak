# Committee input: UI craft guidance for `AGENTS.md`

**DRAFT — UI craft member; audited 2026-10-30 at `44b7104f7`**

This note guides root `AGENTS.md` and proposed nested `web/AGENTS.md`; it is
not a product change, canvas approval, or owner aesthetic acceptance. The
audit made no runtime, desk, device, database, or test mutation.

## Short rules for the root file

1. Ask the Tuesday question first: does this face help a Senior Software
   Architect finish one job? Prefer one clear next action over a new screen.
   The Seven Tenets and the Constitution outrank implementation preference
   (`docs/internal/CONSTITUTION.md:17-37`).
2. A face is a Desk window, not a feature-owned page. Use the one
   `DeskWindowFrame`; it owns chrome, lifecycle, focus, geometry, persistence,
   and compact bottom-sheet form (`web/src/desk/components/DeskWindow.tsx:1-9`). Never add a feature window shell or modal.
3. Keep cores host-agnostic. Accept `CoreProps`; the host supplies scope,
   label, and optional chrome (`web/src/pages/cores/core-types.ts:7-16`). Put
   application identity in `DESK_APPLICATIONS`; Dock, Go, aliases, shortcuts,
   and loaders project that one manifest (`web/src/desk/applications.ts:4-25`).
4. Compose from the surface library. Import surface species from the public
   `desk/surface` barrel; import `Button` from `web/src/components/signal/Signal`
   and `WorkMenu` from `web/src/desk/components/DeskMenu`. Use gadgets, rows, states,
   `Toolbar`, `StatusBar`, `SurfaceFooter`, and patterns before inventing a species
   (`docs/internal/UX-CANON.md:218-240`, `web/src/desk/surface/index.ts:1-39`). Add any recurring missing species to the library, barrel, contract, and reference in one change.
5. Use the window grammar: title bar → one `Toolbar` → edge-to-edge content →
   one `StatusBar`. The title is the name; do not repeat it as a page heading,
   add card-in-card chrome, or leave a dead footer (`docs/internal/UX-CANON.md:45-53`,
   `web/src/desk/surface/kit.tsx:155-167`, `web/src/desk/surface/kit.tsx:403-455`).
6. Layout answers to the window, not the viewport. The public `surface`
   container is declared on the window body (`web/src/desk/components/window-chrome.css:702-720`);
   use `@container surface` and do not add viewport media queries
   (`docs/internal/DESIGN_SYSTEM.md:373-379`).
7. Keep the material current: Workbench meets Pop!_OS means fine borders,
   restrained rounding, soft depth, and quiet sans controls; heavy Steel is
   historical (`docs/internal/UX-CANON.md:17-25`). Icons D are flat, front-on
   silhouettes with two or three tones, navy outline, and no gradient, tilt, or
   perspective (`docs/internal/UX-CANON.md:27-38`). Use sprites, `ToolGlyph`,
   and `GadgetGlyph`; no emoji or ad-hoc icons. CSS uses tokens, not raw
   color/z/duration literals (`docs/internal/DESIGN_SYSTEM.md:175-183`,
   `web/src/desk/surface/contract.md:17-26`, `docs/internal/UX-CANON.md:324-336`).
8. Every verb is the library `Button`, including row, footer, menu, and phone
   actions. A raw button, a fake toggle, or a dead verb is a species defect
   (`docs/internal/UX-CANON.md:151-168`, `docs/internal/UX-CANON.md:207-210`).
   Every text input keeps its `MicButton` unless the host owns the one capture
   path (`docs/internal/UX-CANON.md:227-240`).
9. Use the closed state vocabulary: `idle`, `active`, `working`, `success`,
   `warning`, `failure`, `unreachable`. Render icon plus readable word, never
   colour alone (`web/src/desk/surface/contract.md:6-16`). Prefer `StateChip`
   or `DotWord`; pass wire state through sentence-casing `stateWords`
   (`web/src/desk/surface/words.ts:1-15`, `web/src/desk/surface/words.ts:52-97`).
10. Say only material facts. Use tokens, verbs, counts, and names; an empty
    state may have one true line and its next action, but no helper essay
    (`docs/internal/UX-CANON.md:161-172`). Omit zero counts with `countToken`,
    `countLabel`, or the section species (`web/src/desk/surface/contract.md:231-234`,
    `web/src/desk/surface/Surface.tsx:106-140`). Keep product text in simple
    sentence case and ASD-STE100; do not display raw snake_case wire keys.
11. Treat egress as a fact at the choice or act. Do not put host, IP, LAN,
    cloud, or scope chips on ordinary list rows, toolbars, or status bars.
    Disclose in Settings, a Send preview/confirm, Setup, or the Door, using
    the canonical mapper where a chip is allowed (`docs/internal/UX-CANON.md:179-201`,
    `web/src/desk/surface/egress.ts:143-162`). Calls is a current exemplar:
    its status names readiness, while egress stays in Settings
    (`web/src/desk/calls/CallsWindow.tsx:1-17`, `web/src/desk/calls/CallsWindow.tsx:214-231`).
12. Make state honest and recoverable. Use `SurfaceState` for loading, error,
    and empty; add Retry beside a refusal, preserve user data, and never show
    a stack, raw code, or smoothed-over green (`web/src/desk/surface/Surface.tsx:215-339`,
    `web/src/desk/surface/plainFailure.ts:1-7`). A long read becomes a named
    no-answer state, not an endless spinner (`web/src/desk/surface/kit.tsx:618-691`).
13. Keep authority at the right layer. The core owns view-local selection,
    busy/refusal state, and rendering; the host owns window lifecycle; a store
    or runtime bus is for state that crosses windows. Subscribe to the named
    entity and clean up; do not reread every window event
    (`web/src/desk/calls/CallsWindow.tsx:249-303`,
    `web/src/desk/applications.ts:5-10`).
14. Keep backend boundaries typed and narrow. Read and write through `apiFetch`
    in an app API module, map wire data to face words in a pure model, and
   return the server's authoritative object after a write. Treat a missing optional slice as empty only when its endpoint contract says 404 means absent (`web/src/desk/programs/api.ts:1-35`, `web/src/desk/programs/api.ts:161-200`).
15. Keyboard and phone are first-class. Use real native inputs/radios, the
    library menu and `useRovingRows`; preserve Escape/Tab/Home/End and return
    focus. Composite accessibility, polite live updates, and real radio
    grouping are library contract (`web/src/desk/surface/contract.md:10-16`,
    `web/src/desk/surface/roving.ts:1-9`). At 393, plated controls own 44×44
    px and strip rows are at least 44 px; prove reach with a real pointer and
    `elementFromPoint`, not only rectangle dimensions
    (`docs/internal/UX-CANON.md:267-280`).
16. At phone width, fold strips by measured fit into one library Button and a
    `WorkMenu`; never clip or introduce sideways scrolling. A narrow settings
    pane uses the frame's Back once, with rail navigation on Arrow/Home/End
    (`web/src/desk/surface/contract.md:276-297`,
    `web/src/pages/cores/settingsWindow.tsx:50-79`).

## Data, loading, and state rules for `web/AGENTS.md`

- Keep a small app boundary: typed API functions, a read-lifecycle
  hook/controller, a pure wire-to-face model, and a library-composing core.
  Programs shows the pattern: `apiFetch`, typed reads, 404-to-empty, alive
  guards, and named runtime frames (`web/src/desk/programs/api.ts:18-31`,
  `web/src/desk/programs/api.ts:130-199`).
- A successful press updates from the returned authoritative entity (or an
  explicit reload); a refusal leaves material visible and names what stayed
  unchanged. Busy state belongs to the pressed verb (`web/src/desk/programs/ProgramsWindow.tsx:47-66`,
  `web/src/desk/programs/ProgramWindow.tsx:91-139`).
- Use `useRovingRows` inside a library composite, not a consumer-specific
  keyboard clone. It owns one Tab stop, arrows, Home/End, type-ahead, and
  re-anchoring after rows arrive (`web/src/desk/surface/roving.ts:34-100`).
- Keep stale-response and retained-copy behaviour at the pattern boundary; do
  not invent a second reader/editor state machine
  (`web/src/desk/surface/contract.md:63-70`, `web/src/desk/surface/contract.md:98-114`).
- A Components specimen is useful executable documentation, not proof of a
  live consumer. Keep fixture IO labelled and do not claim provider effects
  from it (`web/src/pages/cores/design-reference/DesignReference.tsx:37-43`,
  `web/src/desk/surface/contract.md:40-55`).
- New code should use the public barrel. The current tree still has direct
  submodule imports; treat those as migration debt, not as examples to copy.
  The contract names `desk/surface` as the supported path and documents only
  the `DeskEditor` direct import as sanctioned (`web/src/desk/surface/contract.md:1-4`,
  `web/src/desk/surface/contract.md:219-220`).

## Ranked anti-patterns

1. **New page, modal, or custom window chrome** — highest cost: breaks the
   Desk OS and multiplies the owner's navigation. Evidence:
   `DeskWindow.tsx:1-9`; `UX-CANON.md:166-172`.
2. **Hand-rolled controls, cards, or duplicated surface skin** — breaks the
   component framework and causes phone/a11y drift. Evidence:
   `DESIGN_SYSTEM.md:357-379`; `contract.md:124-137`.
3. **Egress labels in working rows or vague status copy** — either hides a
   real boundary or adds noise to every task. Evidence: `UX-CANON.md:179-201`.
4. **Infinite loading, optimistic success, or raw backend errors** — lies
   about the owner's work and loses recovery. Evidence: `Surface.tsx:265-293`;
   `plainFailure.ts:38-64`; `kit.tsx:620-651`.
5. **Viewport-only layout, clipped strips, or sub-44 px phone targets** —
   works in one screenshot and fails in a narrow window or keyboard walk.
   Evidence: `window-chrome.css:716-720`; `contract.md:276-297`;
   `UX-CANON.md:267-280`.
6. **New direct private surface imports or a second app registry** — creates
   API drift and inconsistent launch/keyboard identity. Evidence:
   `contract.md:1-4`; `applications.ts:5-10`.

## Exemplar files

- `web/src/desk/programs/ProgramsWindow.tsx:47-137` — host-agnostic list core:
  typed hook, explicit loading/error/empty, one primary Toolbar verb, rows,
  WorkMenu, and zero-count-safe StatusBar.
- `web/src/desk/calls/CallsWindow.tsx:249-353` — shared Calls/Phone core:
  cross-window focus handoff, local busy/refusal state, phone wing selection,
  and egress kept out of working rows.
- `web/src/pages/cores/settingsWindow.tsx:28-121` — native settings rail/pane,
  real library Buttons, roving Arrow/Home/End, and one compact Back contract.

Components remains the pattern index, not a fourth production exemplar (`web/src/pages/cores/design-reference/DesignReference.tsx:37-43`).

## Verification guidance

- Before merge, use the current fast cycle's `scripts/quick_check.sh`; it is
  the check that covers web build, related tests, affected pytest, desk sweep,
  and canon guards. Do not restore historical full-suite or pre-merge review
  gates (`CLAUDE.md:6-33`, `CLAUDE.md:173-180`).
- For a web change, name the focused Vitest app file and run it from `web/`
  with the isolated-HOME policy inherited from the root instructions. Run
  token/architecture gates when CSS, exports, or shared species change
  (`web/package.json:13-20`).
- A face is not closed by a green unit test alone: capture 1440 and 393 shots,
  inspect them against the ratified canvas, then let the owner judge the live
  desk. Check type steps, clipping/intersection, state words, truthful egress,
  keyboard focus, and 44 px touch ownership (`docs/internal/UX-CANON.md:324-338`).

**Unknown:** source audit only; no live desk shots or owner Tuesday walk were available, so visual acceptance remains open.
