# Title bar canvas: three directions and the control

**Status:** RATIFIED by the owner on 2026-10-03: he picked **B, Workbench refined**. His word, verbatim: **"B"**, on the page https://claude.ai/artifact/KF7PkJvexbmfuUkdPPHu3E. B replaces C1's solid title plate. The build and its shots are in `../titlebar-build/`, and the design is amended in `../../design/workbench-look.md` §3. The boards below were drawn before his pick, with no product change. The control is the bar from C1 (PHILO-13-11, ratified 2026-10-02): `web/src/desk/components/window-chrome.css:340-381` (stipple, plate) and `:392-441` (gadgets) on main `d7a9553f5`.

**Method:** the C1 canvas method, run on the real product. A real hub runs on a scratch HOME (it is removed after the run), with the C1 seed (`harness/seed_db.py` and `harness/rig.py`, copied from `../story-11-canvas/harness/`). The app is main as it stands, served by vite with no seats (`harness/vite.config.mjs`). Each direction is one CSS file in `harness/proposals/`, injected after the app's CSS. The desk on every board: the Chair as windows (Needs you, Brief, The week, Capture) with **People on Priya Nair** in front, dragged by its title bar so that it sits among the inactive bars. 1440 × 900 uses a mouse; 393 × 852 uses touch. All boards are at 2x.

**Fences** (`harness/shoot.py`). These are C1's fence functions, imported from `../story-11-canvas/harness/shoot.py`: CONTRAST_ALL, TARGETS44, CLIP and OVERLAP. The OVERLAP More waiver now names the built `.desk-dock-more`, and its relationship is unchanged. OWN is C1's ownership fence, run over the built `.desk-gadget` classes. The 12 px floor and TITLES (each title's contrast on its own ground, plus the bar height) are also measured. Run log: `shots/run.log`, ending `ALL FENCES HELD; EXIT 0`. All facts: `shots/facts.json`.

## Measurements (from `shots/facts.json`)

| | Control (today) | A Quiet | B Workbench refined | C Modern Workbench |
|---|---|---|---|---|
| Bar height 1440 / 393 | 26 / 44 px | 26 / 44 px | 26 / 44 px | **32** / 44 px |
| Front title: ink on ground, contrast | #0b0c10 on #6688bb plate, **5.40:1** | #0b0c10 on #6688bb bar, **5.40:1** | #0b0c10 on #6688bb, **5.40:1** | #0b0c10 on #d5d9df, **13.79:1** |
| Inactive title: ink on ground, contrast | #0b0c10 on #9ea4b0 plate, **7.81:1** | #2a2e36 on #9ea4b0, **5.44:1** | #2a2e36 on #9ea4b0, **5.44:1** | #23262d on #9ea4b0, **6.05:1** |
| Title type | 12 px 700 JetBrains Mono, on a plate | 12 px 700 mono, no plate | 12 px 700 mono, knockout on the front bar only | 13 px 600 Inter (`--font-sans`), no plate |
| Front bar vs inactive bar (luminance) | 1.45 (blue vs steel, both striped) | 1.45 (blue vs steel, flat) | 1.45 (striped blue vs flat steel) | 1.77 (light vs steel) and a 2 px blue underline |
| Gadget box 1440 / 393 | 26 × 26 / 44 × 44 | 20 × 20 / 44 × 44 | 26 × 26 / 44 × 44 | 26 × 26 rounded / 44 × 44 |
| Gadgets are the library Button (`btn--chrome`) | yes | yes | yes | yes |
| Ownership: frame-control observations / lost points | 155 / 0 | 155 / 0 | 155 / 0 | 155 / 0 |
| Texts under 12 px / under 4.5:1 (whole board) | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |
| 393: targets under 44 × 44 / front content | 0 / 704 px | 0 / 704 px | 0 / 704 px | 0 / 704 px |
| Clipped text, sideways strips, rendered overlaps | 0 | 0 | 0 | 0 |
| Window menu inside the viewport (1440 right-click, 393 long press) | yes | yes | yes | yes |

The front window's 4 px blue frame (`window-chrome.css:26`) is the same in every direction. Only the bar changes.

## Boards (`shots/`)

| Board | Control | A Quiet | B Workbench refined | C Modern Workbench |
|---|---|---|---|---|
| 1440, five windows, People in front | `TB-control-1-desk-1440.png` | `TB-A-1-desk-1440.png` | `TB-B-1-desk-1440.png` | `TB-C-1-desk-1440.png` |
| 1440 close-up at 2x: Needs you and Brief (inactive) above People (front). The pointer is on Needs you's Iconify gadget (hover). | `TB-control-2-closeup-1440.png` | `TB-A-2-closeup-1440.png` | `TB-B-2-closeup-1440.png` | `TB-C-2-closeup-1440.png` |
| 393, one window (People on Priya) | `TB-control-3-phone-393.png` | `TB-A-3-phone-393.png` | `TB-B-3-phone-393.png` | `TB-C-3-phone-393.png` |
| 1440, the window menu (right-click on the title) | `TB-control-4-window-menu-1440.png` | `TB-A-4-window-menu-1440.png` | `TB-B-4-window-menu-1440.png` | `TB-C-4-window-menu-1440.png` |
| 393, the window menu (long press on the title) | `TB-control-5-window-menu-393.png` | `TB-A-5-window-menu-393.png` | `TB-B-5-window-menu-393.png` | `TB-C-5-window-menu-393.png` |

## The directions

- **A Quiet** (`harness/proposals/A-quiet.css`): no stripes. The bar is flat, with a 1 px shine on top and the ink rule below. The title is plain bold mono, to the left beside Close, with no plate. The front bar is blue and inactive bars are flat steel with dimmed ink. The glyphs are ink lines only. Gadgets are 20 px with a 4 px gap, and a box shows only on hover.
- **B Workbench refined** (`harness/proposals/B-refined.css`): fine stripes (1 px every 3 px, 7 % ink) on the front bar only, and inactive bars are flat. The title has no plate. On the front bar the stripes stop around the title (a knockout in the bar's own colour). Gadgets sit in square cells as tall as the bar, with one hairline between cells and a half-strength bevel.
- **C Modern Workbench** (`harness/proposals/C-modern.css`): the bar is 32 px and the title is 13 px semibold sans, to the left. The front bar is light steel with a 2 px blue underline, and inactive bars are steel. Gadgets are monochrome 26 px icon buttons with 6 px corners, a 6 % tint at rest and 14 % on hover.

## Re-run

```
PLAYWRIGHT_BROWSERS_PATH=$HOME/Library/Caches/ms-playwright \
  .venv/bin/python pm/roadmap/holdspeak-philo/phase-13-the-desk/assets/titlebar-canvas/harness/shoot.py
```

## Unknowns

- The Brief's SEND well shows the rig's scratch folder (`/private/tmp/p13c1-tb-…`). C1 hid it with a seat, and this canvas runs with no seats. This is not part of the title bar.
- The family `Inter` is what CSS asked for (`getComputedStyle`). This run did not check that the face loaded (`document.fonts`). The shots look like a sans.
- In B, a user can see the front bar's knockout, but the contrast measure reads the solid bar colour. The stripes under the rest of the bar are 7 % ink and are not under the text.
- The frame, the sizing gadget and the screen title bar stay as C1 drew them. A or C may also want a thinner frame. That was not drawn.
