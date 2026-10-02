# H-A1 — Park and restore backend

**DRAFT — UNCHECKED — awaiting Muad'Dib.** PHILO-13-02 remains in-progress until H-A1 and A1-F are merged. A1-F also requires the owner's ratification of C1's “Parked and Restore” artboard.

The normal meeting and Workbench item removal paths set `parked = 1`. They keep the row and its related records. Normal reads omit parked rows. Restore clears the bit. Schema reconciliation adds the two columns to an existing DB.

## Client contract for A1-F

All functions are exported from `web/src/desk/api.ts`.

| Function | HTTP contract | Result |
|---|---|---|
| `parkMeeting(id)` | `DELETE /api/meetings/{id}` | `{parked: id}`; client resolves void |
| `fetchParkedMeetings()` | `GET /api/meetings?parked=true` | mapped Meeting rows |
| `restoreMeeting(id)` | `POST /api/meetings/{id}/restore` | mapped Meeting or null |
| `parkWorkbenchItem(workbenchId, itemId)` | existing item DELETE | `{success: true, parked: id, item}`; client resolves void |
| `fetchParkedWorkbenchItems(workbenchId)` | `GET /api/workbenches/{id}?parked=true` | Workbench item rows |
| `restoreWorkbenchItem(workbenchId, itemId)` | `POST /api/workbenches/{id}/items/{itemId}/restore` | item or null |
| `parkWorkbenchItems(workbenchId, itemIds)` | `POST /api/workbenches/{id}/items/park`, body `{item_ids: [...]}` | parked IDs |
| `restoreWorkbenchItems(workbenchId, itemIds)` | `POST /api/workbenches/{id}/items/restore`, same body | restored IDs |

`GET /api/meetings/{id}?include_parked=true` reads the retained detail. Parked meeting search composes with `search` and the existing facets. The normal detail read returns 404 while parked. The Workbench parked-only read leaves its normal item list untouched. The legacy `deleteWorkbenchItem` client delegates to park.

Single and bulk Workbench transitions validate the Workbench and item IDs. A claimed item refuses parking with 409. Bulk validation and the update share one transaction; a refused request changes no items. Repeating park or restore succeeds. Unknown IDs return 404. Empty or malformed bulk lists return 400.

An item parked before the runner claims it is skipped; a parked pending item does not enter a later run. Parking a meeting keeps independent action items and artifacts actionable. Confirming a proposal whose meeting is parked gives `meeting_parked` (409) and directs the owner to restore it. A genuinely missing historical parent still gives `meeting_deleted`.

## A1-F work still required

Build the Parked filter, Restore Buttons and PARKED receipt on the ratified artboard. Use these clients in both single and bulk paths. Show the receipt in every branch reached by park and restore, including refusal. Verify the 8-second removal window and reload through the face at 1440 and 393 with native touch. This backend handoff does not certify those face transitions.

The lane report and captured observations will carry the backend verification. No story closing evidence or done call is claimed here.
