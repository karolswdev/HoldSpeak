# PHILO-9-03 canvas 2: copy and confirm delivery

**Status: DRAFT, for the owner's ratification** (UX-CANON §A.2). Nothing here is built in product code. The rulings: Q0 "Copy to clipboard only" (the Room gives the finished text; it is marked delivered when he confirms) and "Several per update" (one record per confirmation).

- Review page (every board, both widths): `index.html` in this folder.
- Boards: `shots/<board>-<width>.png` (1440x900 and 393x852, device scale 2); rendered facts: `shots/facts.json`.
- Harness: `../story-03-items-canvas/harness/` (one harness serves both story 03 canvases).

## What the boards are, exactly

- **A real hub and the product app.** The same run as canvas 1: the rig hub on an isolated HOME; "Payments ledger cutover" seeded through the real routes; one update drafted (`POST /api/projects/{id}/updates/draft`) and published (`POST /api/updates/{id}/publish`), both 200 (`facts.json` `_seed.update`). Board 8's draft is a real `Draft` press.
- **The proposal** (`harness/ProposedUpdatePosture.tsx` and `harness/proposedUpdateController.ts`, blocks marked `PROPOSAL`), copies of the product's Update posture and controller, reached through the proposed Room (canvas 1's one swapped module):
  1. **DELIVERY** on a **published** update, first under the lifecycle band: the `To` field (the library `StringGadget`, its speak-to-fill mic built in) and **Mark delivered** (the library `Button`, primary). Always offered on a published update: after Copy, after he leaves and returns, after earlier deliveries. A draft shows none of it.
  2. **The history** under the line: one row per delivery, oldest first — `✓`, the To (or `—`), the time `SEP 27 20:08`. The head reads `DELIVERY` with no rows and `DELIVERED 2` with two.
  3. **The update list:** the DELIVERED chip in two forms for the owner to pick (`?chip=count` → `✓ DELIVERED ×2`; `?chip=latest` → `✓ DELIVERED SEP 27 20:08 · TOMAS`); and the F11 words: head `UPDATES 1` (today `DRAFTS 1`), row `PUBLISHED` `REV 1` as spaced tokens (today "PUBLISHEDRev 11m agoDeterministic draft"), the update glyph `▤` for the fixed `E`.
- **One press, one key.** Mark delivered mints one `command_id` per press and keeps it across that press's retries (a ref cleared only on success; Codex Astra r5).
- **The unbuilt backend is stated, not posed** (`harness/shim.ts`): the stored rows of `project_update_deliveries` stand in `sessionStorage` (they survive a reload and nothing else); `GET …/updates` carries each update's `deliveries`; `POST /api/updates/{id}/delivered` refuses a draft `update_not_published`, replays a known `command_id` (the original row), refuses a changed payload under the same key `idempotency_conflict`, else appends one row (`delivered_at` = now, `project_id` from the stored update, an `operation_id`). The Copy is the product's real Copy (`GET /api/updates/{id}/markdown`, the real clipboard; `facts.json` `clipboard_head`).

## Boards

| # | Board | What it shows |
|---|---|---|
| 0a | Today, the list | `DRAFTS 1`; `E`; "PUBLISHEDRev …Deterministic draft" (F11) |
| 0b | Today, published | Regenerate and Copy only; nothing records a delivery |
| 1 | After Copy | Copy reads `Copied` (2 s, unchanged); DELIVERY: the To field and Mark delivered |
| 2 | He left and returned | a full reload, the Room reopened: Copy reads `Copy`, Mark delivered still offered (no clipboard state; R4-3) |
| 3 | To typed | `Priya` in the field |
| 4 | Pending | the press held: Mark delivered in its loading face, the field disabled |
| 5 | Delivered once | `DELIVERED 1`; `✓ Priya · SEP 27 20:08`; the field empty for the next. The press was a **double-click**: one call, one row (`facts.json` `calls_after_double_click`) |
| 6 | The mistake kept | Priya was the wrong person; he marks `Tomas`: `DELIVERED 2`, both rows, Priya not retracted or marked |
| 7a | List, chip ×N | `UPDATES 1`; `▤ PUBLISHED REV 1 ✓ DELIVERED ×2` — the count includes the mistaken row |
| 7b | List, chip latest | `✓ DELIVERED SEP 27 20:08 · TOMAS` |
| 8 | A draft | the draft editor: no DELIVERY, no Mark delivered |

## The strings (exact)

| Slot | String |
|---|---|
| Section head | `DELIVERY` (no rows) / `DELIVERED N` |
| Field | `To` (accessible name and placeholder); optional, free text; mic `Speak To` |
| Verb | `Mark delivered` (library Button, primary) |
| History row | `✓` · the To or `—` · `MMM D HH:MM` (the owner's confirmation time) |
| List chip (form A) | `✓ DELIVERED ×N` |
| List chip (form B) | `✓ DELIVERED MMM D HH:MM · <TO>` |
| Refused (drawn in code, not shot) | `✗ NOT MARKED` under the line |
| List head / row (F11) | `UPDATES N`; `PUBLISHED` `REV N` |
| Never | "send", "sent", an egress badge, a modal |

## Three questions for the owner

1. **The list chip: `DELIVERED ×2` (7a) or the latest time and To `DELIVERED SEP 27 20:08 · TOMAS` (7b)?** Both fit one line at 393 (7b wraps under the row's first line). ×N counts a mistaken mark too; the latest form names the last person, which after a correction is the right one. Recommended: ×N (short, and the history on the update carries the names).
2. **The seat: DELIVERY first on the published update**, above the body, with the verb beside its To field — not in the footer beside Copy? The footer at 393 holds Regenerate and Copy only, with no room for a field. Recommended: yes, as drawn.
3. **A mistaken mark stays as drawn** (board 6: the wrong row kept, the count includes it, no undo) until "Undo a delivery" leaves the BACKLOG? Recommended: yes — the record says what he confirmed.

## Measurements (`shots/facts.json`, 22 renders)

- **Text under 12 px, proposal nodes:** 0 on every board, both widths.
- **Text under 12 px, inherited:** the provenance chip source word (`deterministic`, `.surface-provenance-source`, 10 px) on the list boards; on the published boards 4 nodes in the Update body; on the draft board 14 (the editor toolbar `B I U H1 …`, 11 px). Not changed here.
- **Raw (non-library) buttons in the window, inherited:** 6 on each published board (the citation chips in SOURCES, `button.desk-chip`, `UpdatePosture.tsx` `SectionSourceRow`); 6 on the draft board (the inline claim ref chips `ITEM`). 0 on the list boards. None in the proposal.
- **Pointer ownership of Mark delivered:** centre + four corners owned by `elementFromPoint` on every board where it shows (the 44 × 44 target at 393; face 118.8 × 24 px, 142.8 × 26 pending).
- **Chip contrast:** every proposal chip and token ≥ 7.39:1 (the history time token and the list tokens). One inherited chip under 4.5:1: `LOCAL + CLOUD` (the `Draft with model` egress chip on the list), **4.29:1**, both widths.
- **Horizontal overflow:** none, except board 8 at 393: the draft editor's body scrolls sideways (inherited; the editor toolbar).
- **"send"/"sent" in the window:** none. **Egress badge in the delivery states:** none. **Modal:** none.
- **Double-click:** one call and one row at both widths.

## Limits

- The delivery table, the read-back and the route are unbuilt (stories 01 and 02). The shim states their contract; the rows live in `sessionStorage`, so the "return" board is a reload of the same tab, not a hub restart or another device.
- `delivered_at` in the history is the shim's clock at the press, standing in for the owner's confirmation time; operation ids are the shim's, not kernel receipts. RECEIPTS showing each delivery write (story 01) is not drawn.
- The refused face (`✗ NOT MARKED`) is in the code but was not shot: the shim refuses only a draft, and a draft offers no verb.
- At 393 the history rows stack (the `SurfaceLedgerRow` species at a narrow container).
- **Inherited, unknown:** at 393, after the two deliveries, the editor's `Back` press did not return to the list within 10 s; Escape did (`facts.json` `_browser_errors`). At 1440 Back worked. The cause is not read.

## Fence sketch (story 03, after ratification; not built)

| After | Assert | Red on main |
|---|---|---|
| reopen a published update (after Copy, after a reload) | `[data-testid=deliver-verb]` reads `Mark delivered`; no stored clipboard state | no verb |
| To `Priya`, press; then To `Tomas`, press | two rows read back from the hub in the same fence; the face shows both, oldest first; the chip reads the ratified form | new |
| a double-click on one press | one row; one `command_id` | new |
| the pending state | the verb in its loading face, the field disabled, then the row | new |
| a draft | no DELIVERY, no verb | preservation |
| every state | no "send"; no egress badge; no modal; no proposal text under 12 px | — |

## Reproduce

```bash
PLAYWRIGHT_BROWSERS_PATH=$HOME/Library/Caches/ms-playwright \
  uv run --extra test python pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-03-items-canvas/harness/shoot.py
```
