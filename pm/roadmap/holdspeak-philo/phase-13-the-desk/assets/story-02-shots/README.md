# PHILO-13-02 A1-F: the shots against the boards

The shots come from `tests/e2e/test_philo13_02_park_glass.py`. Each run uses the real hub, a throwaway HOME, and meetings and items made by the real producers. Width 1440 uses the mouse. Width 393 uses touch (`has_touch`, `tap`). The boards are in `../story-11-canvas/shots/` (the C1 artboard "Parked and Restore", ratified 2026-10-02).

| Shot (1440 and 393) | Board | What the shot shows | Difference from the board |
|---|---|---|---|
| `01-meeting-selected-park` | C1-5a | The selected record's footer verbs are `MD`, `SRT` and `Park`. There is no `Delete`. | None. |
| `02-meeting-parked-receipt` | C1-5b | The receipt `PARKED hh:mm` and `Restore` in the footer. The row is gone from the list. The `PARKED 1` token is under the facets. | None. |
| `03-meetings-parked-filter` | C1-5c | `PARKED 1` is on. The list gives way to the parked row: time, title, `PARKED` chip and `Restore`. | A meeting parked before this session shows its meeting date, not the park time. The hub keeps no park time for a meeting (H-A1). |
| `04-meeting-restored` | C1-5d | `RESTORED hh:mm`. The meeting is back in the list, in view, with a blue mark. The token is gone. | None. |
| `05-meeting-restore-refused` | C1-5e | `NOT RESTORED · THE HUB DID NOT ACCEPT THE CHANGE` in the danger tone, with `Retry`. | The glass makes the refusal with a 500 on the restore route. |
| `06-workbench-item-parked` | C1-5f | `Park` on the item parks it at once. The receipt is `PARKED hh:mm` with `Restore`. The token is `PARKED 1`. | The item verb reads `Park`. The board shows `Remove`, and the brief says Park replaces Remove. |
| `07-workbench-parked-filter` | C1-5g | After a reload, `PARKED 1` is on, with the parked row and `Restore`. | The park time comes from the item's `last_modified`, which park sets. |
| `08-workbench-item-restored` | C1-5h | `RESTORED hh:mm`. The item is back, in view, with a blue mark. | None. |
| `09-workbench-clear-done-parked` | C1-5j | `Clear done` parked both done items. The receipt is `PARKED 2 · hh:mm` with `Restore`. The token is `PARKED 2`. | None. |
| `10-workbench-claimed-refused` | C1-5i | A run claims the item between the read and the press. The receipt is `NOT PARKED · CLAIMED BY A RUN` in the danger tone. There is no Restore, and the item stays. | The glass makes the claim with the runner's own claim statement (`holdspeak/services/workbench_runner.py:257`), not with a full run. |

Each case reads the row back from the hub's DB after park (kept, parked, with all its segments, intel, action items and artifacts, or its artifact link) and again after Restore (kept, active, the same rows). Each case also reloads the page.

## Round 2 (Astra's single pass on #734)

- The 393 footer now has two rows, as on board C1-5a-393: the egress warning on its own row, the receipt and `MD` / `SRT` / `Park` below it. This is the canvas round 3c rule, moved into `web/src/desk/surface/surface-footer.css`.
- A park outcome wraps instead of clipping. `NOT RESTORED · THE HUB DID NOT ACCEPT THE CHANGE` shows in full, and `Retry` stays whole at both widths (`05-meeting-restore-refused-*`).
- Each shot state is now read as rendered (`_assert_readable` in `tests/e2e/glass_infra.py`): no text clipped by its container, no overlap between text and controls in any footer.
