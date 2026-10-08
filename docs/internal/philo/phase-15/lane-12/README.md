# PHILO Phase 15, lane 12: the UGLY bounces

Bounces from rehearsal 1A (`../rehearsal-1a/BOUNCES.md`). Before = the rehearsal shot (main 859e71dd6).
After = `shots/after-*`, taken by `tests/e2e/test_philo15_12_ugly_glass.py` on an isolated HOME.

| Bounce | Rule (species) | Before | After |
|---|---|---|---|
| B19 | Every Dock item wears a sprite (`DOCK_SPRITES`, `systemSprites.ts`); four new D1 sprites, `../icons/dock/` | `2.1-chair-arrival-1440.png`, `2.1-chair-393.png` | `after-B19-dock-1440.png`, `after-B19-dock-393.png` |
| B22 | A railed split puts the list in a strip above the open record; the record has the window's width (`surface.css`) | `3.3-meeting-open-1440.png`, `3.5-decide-pressed-1440.png` | `after-B22-record-1440.png`, `after-B22-record-zoomed-1440.png`, `after-B22-record-393.png` |
| B23 | A folder reads by its name (`HoldSpeak/Sent`, the `~` token on hover); a filename is never italics (`channels.ts targetName`, `Material.tsx`). The well still opens itself when the built-in folder is the only destination (owner ruling 2026-10-05) | `3.5-needs-after-summary-1440.png`, `2.3-brief-generated-1440.png` | `after-B23-week-well-*.png`, `after-B23-brief-well-*.png` |
| B24 | A card kind can name its first-open size; Intelligence opens AT 640 x 620 (no longer content-fitted), its first items in view; a saved size wins (`pullouts/size.ts`, `Pullout.tsx`) | `3.5-review-1-1440.png` | `after-B24-intelligence-1440.png`, `after-B24-intelligence-saved-size-1440.png` |
| B25 | An empty Project reads NEW; the Door's receipt reads CREATE (`project-room/model.ts roomHealthWord`, `egress.ts`) | `4.2-project-created-1440.png` | `after-B25-project-1440.png`, `after-B25-project-393.png` |
| B27 | A footer receipt clips to its cell (ellipsis, title) and wraps in a narrow window; it never runs under a verb (`surface-footer.css`) | `1.5-add-checked-393.png` | `after-B27-concierge-footer-1440.png`, `after-B27-concierge-footer-393.png` |
| B28 | A wrap chip keeps its wrap inside a room row (`surface.css`, `MeetingSummarySlab.tsx`) | `2.4-the-week-393.png` | `after-B28-the-week-393.png`, `after-B28-the-week-1440.png` |
| B30 | A desk label (two lines, monospaced) is set by `fitName`: spaces break first, a too-long word breaks at its joins `_ - . /`, never inside letters; a name that needs more lines is cut in the middle so its end stays (`Payments ledger… v2`); a single overlong word is cut with `…`. A drawer's icons and its List never clip: they wrap, words first (`nameBreaks`: one inline block per word), the row grows (`DeskIcon.tsx`, `fitName.ts`, `ObjectList.tsx`, `objects.css`) | `2.1-chair-393.png` | `after-B30-labels-1440.png`, `after-B30-labels-393.png`, `after-B19-B30-desk-393.png` |

No before-shot exists at the second width for B22, B24 and B25 (the rehearsal shot one width).
