# PHILO-13-11 (C1) build, slice one: the frame

The product renders the ratified canvas (`../story-11-canvas/`, owner 2026-10-02: "Ratify, build it"; "Steel") on its own: no canvas CSS, no seat, no shim. Shots and facts come from `tests/e2e/test_philo13_11_frame_glass.py` (real hub, isolated HOME, the canvas seed trimmed to what the frame shows; 1440 mouse, 393 touch).

## Board beside shot

| Board (canvas) | Shot (build) | Match |
|---|---|---|
| `C1-1-the-desk-1440` | `build-C1-1-the-desk-1440.png` | Frame: match. Paper screen bar names the front window and the time; steel status plates; one blue window; steel frames; the sizing gadget. Not in this slice: the Chair as windows (the next slice), the steel Dock shelf and its live states (C3). |
| `C1-1-the-desk-393` | `build-C1-1-the-desk-393.png` | Screen bar: match (one 44 px row; mark, Go, the screen name, egress mark, bell, time). Search stays as a 44 px picture (it has no Go row today). The Chair body and the Dock look are later slices. |
| `C1-2a-window-gadgets-1440` | `build-C1-2a-window-gadgets-1440.png` | Match, one gadget withheld: close at the left; iconify and zoom at the right; the title on its plate; raised wings, the open one sunken paper; the sizing gadget. Depth (to back) is withheld until C2 builds it. |
| `C1-2a-window-gadgets-393` | `build-C1-2a-window-gadgets-393.png` | Match, depth withheld: one 44 px head row (close, the folded wings). |
| `C1-2b-window-menu-amiga-keys-1440` | `build-C1-2b-window-menu-1440.png` | Menu material: match (paper, ink, raised steel key caps, the drop). The board shows the window's right-button menu (C2); the shot shows the screen bar's Window menu on the same material. |
| `C1-2e-strip-menu-open-393` | `build-C1-2e-strip-menu-open-393.png` | Match: `OUTCOMES ▾`, the menu with every face, a check on the current one, the gear door after a separator. |
| `C1-6b-phone-window-sheet-393` | `build-C1-6b-phone-window-393.png` | Match: one window fills the work area (704 px of content), the head one 44 px row, the screen bar names the window. |

## Facts

- `frame-facts-1440.json`, `frame-facts-393.json`: this build. Fences F1 to F5 hold on every board.
- `red-before-main-02ce9e8c-1440.json`, `red-before-main-02ce9e8c-393.json`: the same test on main 02ce9e8c. F1 (no blue window, no screen name), F2 (the gadget layout), F3 (the wings do not fold at 393), F4 (content 547 and 459 px; screen-bar targets 22 to 26 px high) and F5 (`⌘K` at 10 px, the gear at 11 px) are red there. Two parts were already green on main: the ownership half of F2 and the clip and sideways half of F3.

# Slice two: the Chair as windows

The Chair is four `DeskWindowFrame` windows (Needs you, Brief, The week, Capture; owner 2026-10-02, Capture "Yes"). Shots and facts come from `tests/e2e/test_philo13_11_chair_glass.py` (real hub, isolated HOME, the canvas week: Avery, Sam, Jordan, Priya; three meetings; two decisions; a brief; the Team updates folder destination; 1440 mouse, 393 touch).

## Board beside shot

| Board (canvas) | Shot (build) | Match |
|---|---|---|
| `C1-4a-chair-windows-1440` | `build-C1-4a-chair-windows-1440.png` | Match: four windows tiled on the dithered screen; Needs you left above Capture (100 px); Brief 64 % of the right column with SEND on the first screen; The week below. One blue window, named by the screen bar. Each window: close left; iconify and zoom right (depth withheld until C2); the sizing gadget. Needs you leads with the number, the ranking strip on its own line, the availability and calendar line below it, the actions, then SETUP. Differs: the action caption still reads `NEEDS YOU 5 OF 6` (`ACTIONS` is A2-W, story 03); the bell and Dock counts are A2/C3; the folder path shows the rig's scratch HOME (the canvas mapped it to `~`). |
| `C1-4a-chair-windows-393` | `build-C1-4a-chair-windows-393.png` | Match: one window fills the work area (Brief, opened from Go ▸ Chair); the head one 44 px row; every target 44 px. Depth withheld. |
| `C1-4c-chair-window-closed-1440` | `build-C1-4c-chair-window-closed-1440.png` | Match: Close closed the Brief; one compact reopen Button (`Brief`, library Button, dense) stands in its place. |
| `C1-4c-chair-window-closed-393` | `build-C1-4c-chair-window-closed-393.png` | Match: Close closed the Brief and the next open Chair window (The week, as on the board) takes the work area. |
| `C1-4d-window-menu-chair-1440` | `build-C1-4d-window-menu-chair-1440.png` | Match: Window ▸ Chair lists Needs you, Brief, The week, Capture with a check on each open one (Brief unchecked). Differs: the build's Window rows are live (Close window closes the front Chair window; Minimize iconifies it to a Dock chip); the board drew them ghosted. |
| `C1-6a-phone-desk-393` | `build-C1-6a-phone-desk-393.png` | Match: Needs you alone fills the work area (704 px of content), `RANKED ▾` beside the availability chip, the actions with 44 px verbs. The Dock look is C3. |

## Facts (slice two)

- `chair-facts-1440.json`, `chair-facts-393.json`: this build; fences C1 to C6 hold on every board.
- `red-chair-before-bbf7e9a4-1440.json`, `red-chair-before-bbf7e9a4-393.json`: the same test on bbf7e9a4 (slice one): no Chair window, no blue window, the screen says `Chair`, the Chair page scrolls; at 393 no content measure.
- `red-screen-title-dock-list-1440.json`, `red-screen-title-dock-list-393.json`: the same test with the screen title reading the Dock-only window list (Astra, #730): the screen says `Chair` over every front Chair window.
- `red-go-speak-opens-capture-393.json`: before Muad'Dib's ruling, Go ▸ Speak at 393 opened Capture, not the Speak window (`speak_window: 0`, screen `Capture`). Now only the Dock's Speak AppIcon opens Capture; Go ▸ Speak opens the Speak window (fence C4b).

## Atlas walks (Astra counsel r3 on #730)

The atlas cases whose steps reach a Chair window now open it at 393 through the real doors: Go ▸ Chair ▸ <window>, and the Dock's Speak AppIcon for Capture. These are `at_width: 393` ui steps, skipped at 1440. A reload trigger reopens the window in its `then` steps. The first-value gate check reads `[data-testid=chair-desk]`, which renders only past the gate. 76 cases changed in 7 atlas files; `case.p13.close.intelligence_gone` has the stale `.desk-light-close` replaced with `.desk-gadget-close`. Real hub, isolated HOME, one case per `scripts/graph_walk.py run` invocation, brain muaddib (observations are under `.tmp/graph-walk/philo13-11-chair/`, untracked):

| Case (atlas) | 1440 | 393 | Observation (393) |
|---|---|---|---|
| `case.j10.arrival_generate_brief.populated` (atlas.json) | pass | pass | `.tmp/graph-walk/philo13-11-chair/j10.arrival_generate_brief.populated-393/20261002T230908Z-case.j10.arrival_generate_brief.populated-muaddib-393/observation.json` |
| `case.j11.write_a_thought.window_open` (atlas.json) | pass | pass | `.tmp/graph-walk/philo13-11-chair/j11.write_a_thought.window_open-393/20261002T231344Z-case.j11.write_a_thought.window_open-muaddib-393/observation.json` |
| `case.p13.record.refused_not_recording` (atlas-phase13-muaddib.json) | pass | pass | `.tmp/graph-walk/philo13-11-chair/p13.record.refused_not_recording-393/20261002T232137Z-case.p13.record.refused_not_recording-muaddib-393/observation.json` |
| `case.p13.close.intelligence_gone` (atlas-phase13-muaddib.json) | pass | pass | `.tmp/graph-walk/philo13-11-chair/p13.close.intelligence_gone-393/20261002T232134Z-case.p13.close.intelligence_gone-muaddib-393/observation.json` |

Every other changed case was walked at both widths (results: `.tmp/philo13-11-tools/results*.txt`; the engine-replay cases with `--engine replayed`). Final, 76 cases:
- Pass at both widths: 59.
- Blocked at both widths, same reason, not the Chair (no `engine_reply` boundary, no microphone boundary, `route_failure` or `remote_origin_call` not implemented, the Concierge add-engine step): 14.
- Pass at 1440, fail at 393: 3, held for a rig step or a ruling.
  - `case.closure.chain.s3_same_summary_after_restart` and its `.replayed` twin: the trigger is `cli restart_hub`, and the page comes back on Needs you. A cli trigger takes no `then` steps (atlas.schema.json), so The week cannot be reopened before the observation. B2 (story 07) persisting the open Chair window would also clear it.
  - `case.philo603.toast.arrival` at 393: its predicate needs the card clear of `meeting-summary-text` (The week) AND `arrival-capture-bar` (Capture), with hit tests, at one moment. At 393 those are two windows, one at a time. This needs a per-width `clear_of` (rig/schema) or a ruling on where the aftercare card stands at 393.
