# Check — Astra (Codex `gpt-6-astra`, xhigh): PHILO-13-11 canvases, round 1

Session `01a0fa73-d58f-73c0-9c7e-93ab9a42a262`. Verbatim.

VERDICT: DO-NOT-RATIFY

FINDINGS:

Checked commit `1467d9173`. Steel is a defensible direction; this canvas set is not yet a reliable build contract. Paths below use `P = pm/roadmap/holdspeak-philo/phase-13-the-desk` and `C = P/assets/story-11-canvas`, in the named worktree.

1. **The seven criteria are not all met.**

   | Criterion | Assessment | Evidence |
   |---|---|---|
   | 1. One gadget set | Partial. Desktop close/depth/zoom are drawn. Phone sheets omit zoom; Chair windows retain it. This exception needs to be explicit. | `C/harness/p13.tsx:151`, `:249`; C1-2a, C1-4a |
   | 2. Front-window title and time | Drawn and legible. The competing blue title bars weaken the front-window signal—finding 5. | C1-2a and C1-2c |
   | 3. Shared material | Tokens exist; universal application is not demonstrated. People exposes a contrast problem. Repeated observations are not coverage of all 19 hosts. | C1-3-1440, C1-6b-393 |
   | 4. Chair as windows | Visually met. Window behaviour is inconsistent—finding 4. | C1-1, C1-4a, C1-4b |
   | 5. Floor and library Buttons throughout | Not met. The evidence contains readable **10 and 11 px** text and inherited raw buttons. | `C/shots/facts.json`, `C1-1-the-desk-1440.small_text`; `C/README.md:57` |
   | 6. Both widths | Both supplied; some phone evidence is invalid—finding 3. | C1-3-393, C1-6a-393 |
   | 7. State on AppIcons | Met as a drawing of the named stand-ins. C3’s remaining states need designs—finding 8. | C1-1, C1-3-1440 |

2. **The phone layout contradicts C7’s working-space requirement.**  
   The claimed 96 px counts only the screen bar and shelf. The recorded open Chair window is **579 px including its chrome**, against C7’s **700 px of content**. Three collapsed window bars consume space; the first `Done` is clipped in `pm/roadmap/holdspeak-philo/phase-13-the-desk/assets/story-11-canvas/shots/C1-1-the-desk-393.png`. The Meetings warning still overlaps `MD`/`SRT` in `pm/roadmap/holdspeak-philo/phase-13-the-desk/assets/story-11-canvas/shots/C1-5a-meeting-selected-park-393.png`. Evidence: `C/shots/facts.json:9500`; `P/story-17-c7-the-phone-desk.md:32`. **Fails Tenets 2, 3 and 7.** C7 cannot both reproduce this layout and satisfy its charter.

3. **“All fences held” overstates what the fences establish.**  
   `pm/roadmap/holdspeak-philo/phase-13-the-desk/assets/story-11-canvas/shots/C1-3-material-tokens-393.png` has no visible material sheet content. `pm/roadmap/holdspeak-philo/phase-13-the-desk/assets/story-11-canvas/shots/C1-6a-phone-desk-393.png` still shows the Workbench window; its recorded front title is `Ledger cutover bench`, not the intended Chair (`facts.json:9181`). The comparison’s “Chair” also retains that window.

   More seriously, the ownership fence accepts `own >= 1` (`harness/shoot.py:258`). **35 gadget observations have uncovered points owned elsewhere within the same window**. `Close People` owns six of nine, with no other-window occlusion (`facts.json:9813`). Screen-bar controls are forced to 22 px high and phone wings to 36 px (`canvas.css:203`, `:571`); the gadget-only probe does not cover them. **Fails Tenets 3 and 5; UX-CANON C.** Correct the boards and fence the actual visible state and complete target ownership.

4. **Chair windows introduce a second meaning of Close.**  
   The settled design says Close sends a Chair window backward (`P/design/workbench-look.md:90`); the harness wires Close and depth to the same function (`C/harness/p13.tsx:249`). On tiled desktop panes, that may leave the entire window visible. On phone, it does not close the open pane. This is a design decision, not merely unfinished C2 behaviour. **Fails Tenets 3 and 5.** Use the shared window lifecycle, with an obvious reopening route. Also explicitly add the four Chair IDs to B2’s persistence contract; its current family table does not name them.

5. **The material still paints conflicting focus and unreadable text.**  
   In `pm/roadmap/holdspeak-philo/phase-13-the-desk/assets/story-11-canvas/shots/C1-2a-window-gadgets-1440.png`, Meetings retains blue title-bar areas while Payments is front. The inherited `.is-front` selector still sets the blue background (`web/src/desk/components/window-chrome.css:337`); the canvas’s neutral rule does not override its specificity.

   In `pm/roadmap/holdspeak-philo/phase-13-the-desk/assets/story-11-canvas/shots/C1-6b-phone-window-sheet-393.png`, `Encrypted · Local storage · Notes only` is nearly invisible on steel. Its muted token against steel is approximately **1.03:1** (`web/src/pages/cores/people.css:1`). **Fails Tenets 3, 5 and 6.** Token contrast in isolation does not establish contrast where hosts actually use it.

6. **Park’s default is right; Restore’s completion is underdesigned.**  
   One deliberate press plus durable Restore fits Tenet 1 and Constitution XI.4. The PARKED footer survives the selected-detail-to-list transition: that part is good.

   Restore then clears the receipt (`C/harness/p13.tsx:349`). In C1-5d-393 the restored meeting is outside the visible area, so neither the object nor a completion receipt confirms success. A1 explicitly requires receipts for restore success/failure and claimed-item refusal (`P/story-02-a1-park-never-delete.md:62`). Those states, Workbench restoration, and bulk parking are not drawn. **Fails Tenets 3 and 7.** Add compact outcomes using the existing receipt species; retain the no-confirm default.

7. **Steel is sound as a practical preference; the comparison’s explanation needs correction.**  
   I independently reproduced the five stated pen ratios, rounded: **7.81, 5.40, 17.12, 5.73 and 5.24**. The recorded eight-versus-two low-contrast observations also match the JSON (`facts.json:5105`).

   However, Honest’s **1.56:1** headline is the proposal’s **blue-on-grey**, not inherited ember: `canvas.css:491` changes `--accent`. This demonstrates an incomplete alternate palette, not an unavoidable disadvantage of grey bodies. Steel’s 4.26 headline is large text; its 3.79 `Add` remains a small-text problem. The comparison excludes the People problem above. **Tenets 3 and 6:** recommend Steel for coherent integration and preference, with these limits stated accurately.

8. **The later-story handoffs need a few explicit states.**  
   Named stand-ins are appropriate for this canvas stage. C2’s two remembered rectangles and proposed keys are honestly deferred. But C3 also requires meeting-ready, send-settled, failed/unknown send and disconnected states; the boards show REC, appointments and counts only (`P/story-13-c3-a-live-dock.md:37`, `:55`). Further, the harness filters project icons by a truthy count (`C/harness/p13.tsx:306`): an active project with no needs-you items disappears. Omit its zero badge, not its AppIcon. **Fails Tenets 3 and 7.**

CONDITIONS:

- Correct the phone composition and target sizes before freezing it for C7.
- Repair the blank/wrong boards, partial-ownership fence, competing blue bars and People contrast.
- Settle one window lifecycle and explicitly assign Chair persistence.
- Draw the missing A1-F/C3 outcomes. Show the final 12 px typography on the affected boards; explicitly assign the admitted raw-button repairs.
- Correct the comparison description and regenerate evidence with fences that fail on these observed defects.

MISSED:

1. **Highest owner cost: more chrome without faster access.** This is recognisably Workbench and more than a recolour: independent panes and AppIcon state are meaningful changes. “On steroids” remains underdeveloped where setup/ranking consumes the phone’s first screen and SEND falls below the desktop Brief. Cheap improvement: compact those controls and keep the next job’s verb visible.
2. **Window semantics matter more than additional decoration.** Real close, depth, zoom and remembered placement would add more Workbench character than further bevels.
3. **The three defaults:** **Steel—yes, with corrected evidence. Park without confirmation—yes. Capture as a fourth window—yes on desktop; on demand on phone, rather than another permanent collapsed strip.** No new modal or status window is needed.

TUESDAY: At 1440 the owner can find work and capture; at 393 he still faces clipped actions, excessive chrome and an unconfirmed Restore.

UNKNOWN: This was a read-only artifact check; I inspected every C1 PNG and read the harness, design, facts and log. I did not rerun the mutating capture script, exercise real touch/keyboard behaviour, verify durable Park/Restore or bus events, or establish all-19-host coverage. No new prose or zero-counter violation was apparent; meeting summaries are content. The supplied modal scan reports none. The tree is unchanged.