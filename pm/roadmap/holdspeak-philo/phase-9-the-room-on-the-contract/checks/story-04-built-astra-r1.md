VERDICT: DO-NOT-RATIFY

FINDINGS:

1. **Merge blocker: selected note text becomes unreadable. Tenets 3/6; UX-CANON C.** The new `web/src/styles/global.css:68` combines with CodeMirror’s unchanged `web/src/desk/components/deskEditorTheme.ts:33`. I reproduced **1.33:1 selected-text contrast at both widths**, versus **12.99:1 on main**. The logged CodeMirror exception misses this new regression. Evidence: [main shot](/tmp/astra-pr683-review/editor-selected-main-1440.png), [branch 1440](/tmp/astra-pr683-review/editor-selected-branch-1440.png), [branch 393](/tmp/astra-pr683-review/editor-selected-branch-393.png), [measurements](/tmp/astra-pr683-review/probe.json).

2. **The menu correction leaves desktop submenus outside the viewport. Tenets 3/5/6.** Open the Floor menu near the bottom-right, then Launch. At 1440×900, its submenu ends at **x=1474, y=1034**; Connections is below the screen. The new measurement handles `web/src/desk/components/DeskMenu.tsx:483`; the `web/src/desk/components/DeskMenu.tsx:626`. **This reproduces identically on main: inherited debt, not a new regression.** It nevertheless contradicts the evidence’s “every desk menu” claim. Evidence: [branch shot](/tmp/astra-pr683-review/floor-launch-1440.png), [main measurements](/tmp/astra-pr683-review/main-probe.json).

3. **The intended list repairs match the ratified canvas. Tenets 5/6 satisfied within that scope.** Compared the list, sort, one-item, menu and selection shots at both widths. The fold, SHOWN, library sort Buttons, 12 px floor and ATTN treatment agree. Fresh verification passed **38 story checks**, **35 focused web tests**, and the actual row-menu atlas case at **both widths**. I read the recorded main/branch atlas observations: expected failures and desktop preservation passes agree with the matrix. Attention comes through the `tests/e2e/test_philo9_04_desk_debts_glass.py:240`. I found no introduced raw button, lying double or weakened assertion in this diff.

4. **The sampled selection surfaces work outside CodeMirror.** List and palette fields pass; the Floor rename field also measures **4.26:1 selection/background and 4.56:1 selected text** at both widths. No new active-palette collision reproduced: dragging its option activated it without selecting text. Sampled top-level menus fit, including the scrolling Go menu at 393. Evidence: [Floor measurements](/tmp/astra-pr683-review/floor.json), [menu/palette measurements](/tmp/astra-pr683-review/probe.json).

CONDITIONS:

- Correct the editor’s selection background/ink pair and add a rendered editor-selection fence at both widths. Demonstrate failure on this revision and success after correction.
- Fix or explicitly ledger the inherited Launch-submenu overflow; narrow the “every desk menu” claim accordingly.
- Complete the pending CI checks and classify any failures before merge.

MISSED: Highest owner cost: selecting a note makes its words nearly disappear. Next: the species-wide menu claim exceeds the exercised and repaired paths.

TUESDAY: The list job is usable; editing selected note text is not ready.

UNKNOWN: Reviewed `f58cb5b0` in a fresh worktree and reproduced the baseline issues in a separate `1afcc576` worktree. No full-suite rerun or exhaustive dock/window-menu and resize sweep. Unit and macOS integration/E2E CI remained incomplete at the last check. Both review trees are clean; no repository files changed.