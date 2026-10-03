# PHILO-13-11 title bar B: the build

The owner picked **B, Workbench refined** on 2026-10-03. His word, verbatim: **"B"**, on the page https://claude.ai/artifact/KF7PkJvexbmfuUkdPPHu3E. The boards are in `../titlebar-canvas/`. The product now renders B by itself, with no canvas CSS:
- The rule is in `web/src/desk/components/window-chrome.css` (the bar, the title, the gadget grid, the wings).
- The four new tokens are in `web/design-tokens.json`, generated into `web/src/styles/tokens.css`:
  - `--wb-stipple-fine`
  - `--wb-ink-dim`
  - `--wb-rule`
  - `--wb-raised-soft`

The shots and facts come from `tests/e2e/test_philo13_11_titlebar_glass.py`. It runs on a real hub with an isolated HOME and the canvas week. People on Priya Nair is in front, as on the boards. 1440 uses a mouse and 393 uses touch. The static fence is `web/src/desk/__tests__/titleBarB.test.ts`.

## Board beside shot

| Board (canvas B) | Shot (build) | Match |
|---|---|---|
| `TB-B-1-desk-1440.png` | `build-TB-1-desk-1440.png` | Match. One front bar: blue, with fine stripes. Four inactive bars: flat steel, title in dimmed ink. |
| `TB-B-2-closeup-1440.png` | `build-TB-2-closeup-1440.png` | Match. On the front bar the stripes stop around the title. The gadget cells sit on one grid with one hairline between cells. The board shows a hovered gadget; the shot has no hover. |
| `TB-B-3-phone-393.png` | `build-TB-3-phone-393.png` | Match. One 44 px row (close, title, depth). The title fills the row, so the stripes show only at its ends, as on the board. |
| `TB-B-4-window-menu-1440.png` | `build-TB-4-window-menu-1440.png` | Match. A right-click on the title opens the window menu, inside the viewport. |
| `TB-B-5-window-menu-393.png` | `build-TB-5-window-menu-393.png` | Match. A long press on the title opens the window menu, inside the viewport. |

## Measured (`titlebar-facts-1440.json`, `titlebar-facts-393.json`)

| | 1440 | 393 |
|---|---|---|
| Bar height | 26 px | 44 px |
| Front bar | striped (`--wb-stipple-fine` over `--wb-blue`) | striped |
| Inactive bars | 4 of 4 flat | 1 of 1 flat |
| Front title | #0b0c10 on #6688bb, **5.40:1**, 12 px | 5.40:1, 12 px |
| Inactive title | #2a2e36 on #9ea4b0, **5.44:1**, 12 px | 5.44:1, 12 px |
| Gadgets that do not own their centre / are not the library Button | 0 / 0 | 0 / 0 |
| Gadgets under 44 × 44 | n/a | 0 |
| Title bar texts under 12 px | 0 | 0 |
| Browser errors | 0 | 0 |

One change from the canvas CSS, for the canon: the left-edge hairline of the right gadget cells and of the wing tabs is drawn as an inset shadow (`inset 1px 0 0 var(--wb-rule)`), not as a `border-left`. The reason is HS-101 rule 6: the DS6 ratchet allows only `1px solid var(--wb-ink)`. The look is the same.
