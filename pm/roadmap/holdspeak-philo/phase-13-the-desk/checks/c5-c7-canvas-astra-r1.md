VERDICT: RATIFY-WITH-CONDITIONS

FINDINGS:

1. **C7 loses Capture when the owner leaves it.** The ring includes Capture only while it is the current Chair window (`pm/roadmap/holdspeak-philo/phase-13-the-desk/assets/story-17-canvas/harness/c7.tsx:64`). Swiping away removes it from the switcher. With no other window hosting aftercare, its unmounted slot also sends the undismissed card back to the fixed overlay (`web/src/components/AmbientLayer.tsx:235`). C7-6 dismisses the card before testing further navigation. This contradicts “never floats over work.” **Tenet 3; story 17 acceptance 3–4.**

2. **The recommended phone Send path is not drawn as one working composition.** C5 exercises `Go ▸ Send to`; C7 exercises `Go ▸ Object`. Their proposed combination needs `Go ▸ Object ▸ Send to ▸ destination`, but the real menu stops handling submenu selection after the first level: `web/src/desk/components/DeskMenu.tsx:612` passes `setOpenSub={() => {}}`. The separate boards cannot establish this combined path. **Tenets 3 and 5; A.11.**

3. **The switcher hides its only visible affordance.** In `pm/roadmap/holdspeak-philo/phase-13-the-desk/assets/story-17-canvas/shots/C7-2a-swipe-to-brief-393.png`, even “Brief” becomes `Brief…`; the ▾ disappears. The same happens throughout the phone boards. Reading `innerText` as `Brief ▾` does not prove the owner sees it. **Tenet 3; UX-CANON D’s clickable-control rule.**

4. **Desktop destination submenus detach from their parent.** `pm/roadmap/holdspeak-philo/phase-13-the-desk/assets/story-15-canvas/shots/C5-2-object-menu-send-to-1440.png` puts Object at the left and its destinations at the far right, separated by most of the desktop. C5-10a/b do the same. Being inside the viewport is insufficient: the owner must visually reconnect the two panels. **Tenets 3 and 6.**

5. **The failed Room read has no arrival.** The shim’s project pick only acts when the update is known (`pm/roadmap/holdspeak-philo/phase-13-the-desk/assets/story-15-canvas/harness/c5.tsx:334`). Under `CAN'T CHECK`, selecting a destination therefore closes the menu without opening the promised error well. The runner escapes that menu and clears the failure before picking (`pm/roadmap/holdspeak-philo/phase-13-the-desk/assets/story-15-canvas/harness/shoot.py:200`). **Tenet 3; A.10–A.11; story 15 scope “The reads.”**

6. **The hit-ownership fence can accept chrome stealing a content target.** Its layer classifier treats the menubar and Dock as occluding layers; `TARGETS44` passes when `own + occ == 9` (`pm/roadmap/holdspeak-philo/phase-13-the-desk/assets/story-11-canvas/harness/shoot.py:140`, `pm/roadmap/holdspeak-philo/phase-13-the-desk/assets/story-11-canvas/harness/shoot.py:202`). Thus “all fences held” does not prove C7’s specific promise that chrome owns no content hit point. **Tenet 3; story 17 acceptance 4.**

CONDITIONS:

Apply the mechanical corrections together, then use the one confirmation for:

- Aftercare arrival → swipe away → return, with Capture still reachable and no floating card.
- The combined grouped phone Send path, tapped through to its preview.
- A persistent switcher chevron and adjacent desktop submenus.
- A failed Room read → destination pick → visible failure and recovery.
- A target-fence mutation on an actual board that rejects chrome covering a content control.

The recommended directions otherwise stand: Send first, retained offline destinations, fixed swipe order, grouped Go, title switcher, aftercare opening Capture, and 44×44 controls. No position counter is needed once the switcher is visibly discoverable. `--accent-text` is the correct contrast correction.

MISSED:

Ranked by owner cost: the combined Send path; returning to work after aftercare; the failed-read click; discoverability and submenu placement; the fence’s overly broad occlusion exemption.

TUESDAY: Happy-path Send is clear; the phone still needs a visible switcher, a working grouped Send path, and aftercare that stays out of resumed work.

UNKNOWN: I inspected all 53 boards and their harnesses. Fresh-HOME replay stopped during database creation with `sqlite3.OperationalError: disk I/O error`; the volume reported 100% capacity. The transition findings are source-traced, without new replay shots. Real phones and non-FILE delivery remain unverified. The tree is unchanged.