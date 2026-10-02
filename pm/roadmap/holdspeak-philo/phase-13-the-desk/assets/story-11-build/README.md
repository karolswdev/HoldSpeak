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
