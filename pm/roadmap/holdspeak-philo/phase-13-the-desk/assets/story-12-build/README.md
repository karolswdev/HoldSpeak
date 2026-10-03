# PHILO-13-12 (C2) build shots, matched to the board

Source: `tests/e2e/test_philo13_12_gadgets_glass.py`. It runs on a real hub with a throwaway HOME, at 1440 x 900 (mouse) and 393 x 852 (touch), with `HOLDSPEAK_EVIDENCE_WRITE=1`. The measured facts and the empty failure list are in `gadget-facts-1440.json` and `gadget-facts-393.json`.

| Board (`../story-11-canvas/shots/`) | Build shot | What matches |
|---|---|---|
| C1-2b-window-menu-amiga-keys-1440 | build-C1-2b-window-menu-amiga-keys-1440.png | The right button in the window body opens Iconify ⌘M, Zoom ⌃M, To back ⌃B, Close window ⌘W, Desk ▸, Go ▸. Each key is in raised caps. Desk ▸ opens beside the menu and shows New Note ⌘N, New Decision ⌘⇧N, Search ⌘K and Keyboard shortcuts ⌘/. |
| C1-2b-window-menu-amiga-keys-393 | build-C1-2b-window-menu-amiga-keys-393.png | A long press opens the same menu. Zoom stays in it, ghosted with the reason "Fills the screen". Every row is at least 44 px tall. |
| C1-2c-depth-to-back-1440 | build-C1-2c-before-depth-1440.png → build-C1-2c-depth-to-back-1440.png | To back puts Meetings behind every window. The Room becomes the one blue window, and the screen title names it. |
| C1-2c-depth-to-back-393 | build-C1-2c-before-depth-393.png → build-C1-2c-depth-to-back-393.png | The head is one 44 px row: close · the title or the strip · depth, with depth flush right. A tap on depth makes Meetings the one blue window, and the screen title names it. |
| C1-2d-zoom-1440 | build-C1-2d-zoom-1440.png | Zoom fills the work band, and the gadget is pressed. The glass also checks the steps the shot cannot show: the zoomed window is resized, zoom back gives the exact prior rect, zoom again gives the resized rect, and both rects survive a reload. |
