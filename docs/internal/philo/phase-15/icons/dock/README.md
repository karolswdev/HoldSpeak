# PHILO Phase 15, lane 12: four Dock sprites (B19)

Four Dock items had a text glyph and no sprite: Intelligence, Desk memory, Delivery and Panes.
This folder holds the candidates and the picks. Open `sheet.html` to see them.

## Method

D1 Workbench+ mold (`docs/internal/philo/phase-14/icons/README.md`). One
`create_object_pro_flash` call per candidate: 32 x 32, `n_directions` 1, view `side`, style
reference `web/public/desk/sprites/system/dock-people.png` ("match this dock icon's palette,
outline weight, shading and scale exactly"). Description head: `Amiga Workbench 2.0 dock icon,
bevelled steel grey and slate blue metal, one ember orange accent, hard pixel shading, dark 1
pixel outline, transparent background: <object>`. No cleanup was needed: every result is 32 x 32
with a hard alpha edge and a 1 px dark outline.

## Picks

| Dock item | Launcher id | File | Candidate | PixelLab object |
|---|---|---|---|---|
| Intelligence | `intelligence:desk` | `system/dock-intelligence.png` | A, clipboard | `bce2c437-df1c-4ae8-953a-164061e9476b` |
| Desk memory | `attention` | `system/dock-desk-memory.png` | B, chip | `8e3fc324-6878-423a-8c01-ace5e7ae37ae` |
| Delivery | `delivery-board` | `system/dock-delivery.png` | A, outbox | `13224853-0a18-4aa6-8cd4-49dfcb6d7908` |
| Panes | `panes` | `system/dock-panes.png` | A, two windows | `dd939c8f-ec50-4473-83c7-b70c549448ee` |

Not picked: Intelligence B bulb `279555cf-8b93-4e30-83f8-4ed514b0dcff`; Desk memory A card index
`409564eb-6b74-4083-a178-84ace885e884`; Delivery B mailbox `b7987d77-ccd4-41b3-9126-36c47eac8e1d`;
Panes B monitor `2a2af44e-2ca5-4716-8c21-d19bba43571b`.

The reason for each pick is on the sheet. Muad'Dib ratifies from the sheet.

## Spend

8 calls, 40 generations. `get_balance` before: 290 used of 2000, credits $0.00.

## Code

`DOCK_SPRITES` in `web/src/desk/systemSprites.ts` maps every Dock item (the applications and the
launchers) to a file. `Dock.tsx` draws the sprite for a launcher as it does for an application.
Fence: `web/src/desk/systemSprites.test.ts` ("every Dock item has a sprite file").
