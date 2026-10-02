# Check — Astra (Codex `gpt-6-astra`, xhigh): PHILO-13-11 canvases, round 2

Session `01a0fa73-d58f-73c0-9c7e-93ab9a42a262`. Verbatim.

VERDICT: DO-NOT-RATIFY

FINDINGS:
1. **New phone defect:** in [C1-5a-meeting-selected-park-393.png](</Users/karol/dev/tools/wt-philo-13-muaddib/pm/roadmap/holdspeak-philo/phase-13-the-desk/assets/story-11-canvas/shots/C1-5a-meeting-selected-park-393.png>), the `NO SUMMARY ROUTE · NO ASSIGNMENT` warning is overlapped by the `MD` / `SRT` buttons. This contradicts [README.md:27](</Users/karol/dev/tools/wt-philo-13-muaddib/pm/roadmap/holdspeak-philo/phase-13-the-desk/assets/story-11-canvas/README.md:27>) and [workbench-look.md:129](</Users/karol/dev/tools/wt-philo-13-muaddib/pm/roadmap/holdspeak-philo/phase-13-the-desk/design/workbench-look.md:129>), which say the warning no longer overlaps the controls. The fence checks clipping and targets, but misses this rendered collision.

2. **Seven criteria on the boards:**
   - **1 — Mostly met:** the desktop boards show Chair windows, depth, and zoom; phone shows the reduced controls, as specified. See `C1-2a-d`, `C1-4b-e`, and `C1-6b`.
   - **2 — Met:** the top bar names the blue front window; `facts.json` records one blue front on all 50 boards.
   - **3 — Partial:** the material board makes the visual system checkable, but not all 19 hosts. The design itself records that limit at [workbench-look.md:169](</Users/karol/dev/tools/wt-philo-13-muaddib/pm/roadmap/holdspeak-philo/phase-13-the-desk/design/workbench-look.md:169>).
   - **4 — Visual lifecycle met; persistence unproven:** `C1-4c-e` show Close and reopen through Window ▸ Chair. The boards do not establish that `chair:*` IDs persist.
   - **5 — Partial:** contrast passes, but visible inherited raw buttons and the instructional text `Run · Bind an agent first` remain. They are named as C8/A1-F stand-ins in [README.md:80–89](</Users/karol/dev/tools/wt-philo-13-muaddib/pm/roadmap/holdspeak-philo/phase-13-the-desk/assets/story-11-canvas/README.md:80>), so the board does not yet satisfy the library-Button and no-prose canon.
   - **6 — Met on the boards:** both sizes are shown; `facts.json` reports 704 px phone content and no targets under 44 px. The footer collision in finding 1 is not covered by those checks.
   - **7 — Met:** `C1-8a-c` show the AppIcon states. The Dock exception is appropriate for the icon shelf.

3. **Round-one conditions:** R1’s close/reopen path is visible, but ID persistence is not; R2’s single phone window, content width, and target size pass, except for the collision above; R3’s work-first screen is visible in `C1-1`; R4’s one-front-window rule passes in the facts; R5’s in-place contrast checks pass; R6 shows Park/Restore outcomes, and `harness/shoot.py:549–602` checks the rendered receipt after the transition; R7’s comparison supports Steel as a coherent product choice; R8 has red-before and green-after evidence. For contrast, the README reports the old `8 need you` at 4.26:1 and the new accent at 5.43:1; both Steel and Honest 2.0 have no below-threshold cases in the comparison facts. Steel is a sound direction choice, not an accessibility win over Honest. The three README defaults also look sound: Park is reversible through Restore, and Capture as a fourth Chair window keeps that tool available without another permanent face ([README.md:111–115](</Users/karol/dev/tools/wt-philo-13-muaddib/pm/roadmap/holdspeak-philo/phase-13-the-desk/assets/story-11-canvas/README.md:111>)).

4. **Proof-text drift:** [README.md:28](</Users/karol/dev/tools/wt-philo-13-muaddib/pm/roadmap/holdspeak-philo/phase-13-the-desk/assets/story-11-canvas/README.md:28>) still says the ranking strip scrolls inside itself, while the current phone board uses a single menu Button (`C1-1-the-desk-393.png`, `C1-2e-strip-menu-open-393.png`). The old scroll comment also remains in the stylesheet at `harness/canvas.css:658`. Reconcile those claims and their fences together. There are also conflicting counts: README line 76 says 10 files/14 seats while reporting a guard of 12/16; `shots/run.log:1` reports 12/16. Design lines 167–168 report older observation totals than the current facts and README lines 41–43.

5. The canvas reads as more than a palette reskin: it combines a system bar, icon shelf, multiple Chair windows, and close/reopen behavior. The “on steroids” promise is still mostly visual, though: several depth, live-tag, persistence, and action outcomes are explicitly stand-ins for later stories. The cheap improvement is to fix the phone footer and fence rendered overlap; no new interface is needed.

CONDITIONS: Fix the 393 px Meetings footer collision, regenerate the affected board, and add an overlap fence for the rendered state. Reconcile the stale ranking-strip and count claims with current evidence, updating the associated fences in the same commit.

MISSED: Ranked by owner cost: (1) the phone collision makes the visible Park workflow harder to use; (2) stale proof text makes the evidence disagree with the current boards; (3) the 19-host variety and the “steroids” behavior are not demonstrated here, while live behavior is deferred to C2/C3/B2/A1-F; (4) the known raw controls and instructional prose remain canon debt.

TUESDAY: Not reliably on the phone yet: the warning collides with the adjacent controls on the selected-meeting screen where the owner must decide whether to Park.

UNKNOWN: I did not verify B2 persistence or live C2/C3/A1-F producers from these C1 boards, and the boards cannot prove behavior beyond their named stand-ins. No owner-device touch session was captured.