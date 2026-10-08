# PHILO Phase 16: the pi agent sprite

pi is the third coding agent, after Claude Code and Codex. This folder records its world sprite.
`contact-sheet.png` shows the three agents side by side: at 64 px on the desk (#3c4454) and at
32 px on the steel (#9ea4b0). The sheet is drawn at 2x, nearest neighbour.

## Files

- `web/public/desk/sprites/agent-pi.png`: 64 x 64.
- `web/public/desk/sprites/32/agent-pi.png`: 32 x 32, drawn at 32. It is not a scaled 64.
- `agent-pi_sel.png` and `agent-pi_stale.png` at both sizes, from `web/scripts/gen-sprite-states.py`.

## Method

We used the D1 Workbench+ mold (`docs/internal/philo/phase-14/icons/README.md`) and the Dock
method of Phase 15 (`docs/internal/philo/phase-15/icons/dock/README.md`).

One `create_object_pro_flash` call per candidate. `n_directions` 1, view `side`.
The style reference is the Codex sprite at the same size, with the usage text "match this icon's
palette, outline weight, shading and scale exactly". At 64 the reference is
`web/public/desk/sprites/agent-codex.png`. At 32 it is `web/public/desk/sprites/32/agent-codex.png`.

Description head: `Amiga Workbench 2.0 desktop icon, bevelled steel grey and slate blue metal,
one ember orange accent, hard pixel shading, dark 1 pixel outline, transparent background:`.

- Candidate A (the object): `a small robot agent head shaped like a wide flat-topped hexagon,
  slate blue faceplate with one large bold ember orange Greek letter pi symbol in the centre, two
  small round steel bolt ears, no eyes`.
- Candidate B (the object): `a small robot agent head with a tall rounded capsule dome, one wide
  horizontal dark visor slit, and on top a chunky antenna bent in the shape of the Greek letter
  pi, the pi antenna painted ember orange`.
- The 32 px call used the description of candidate A.

No cleanup was necessary. Each result has the correct size, a hard alpha edge (alpha is 0 or 255
only) and a 1 px dark outline.

## Pick

| Size | Candidate | PixelLab object |
|---|---|---|
| 64 | A, hexagon head with the pi faceplate | `d40a3b1a-2a8e-46e9-a4ac-9bc080c717a3` |
| 32 | A, drawn at 32 | `28f7ba53-4dbf-452b-b7c3-d796d86d5502` |

Not picked: candidate B, capsule head with the pi antenna, `d6280dec-b9b5-4cd5-9bef-03f5e1fe3367`.

Why A:

- The pi is the face. It is large and ember orange, so it reads as pi at 32 px.
- The shape is a hexagon with no eyes. Claude Code is a round head with one eye. Codex is a
  square head with two eyes and a grille. The three heads are different at 32 px.
- B's pi antenna is small. At 32 px it is a few pixels and looks like a plain antenna. The B
  visor head is also near to the Codex head.

## Spend

3 calls, 15 generations. `get_balance` before: 330 used of 2000. After: 345 used of 2000.
Credits were $0.00 both times.

## States

`web/scripts/gen-sprite-states.py` made `_sel` and `_stale` at 64 and 32. The script makes all
the state files again. Only the six `agent-pi` files are new. No other sprite file changed
(`git status --short web/public/desk/sprites`).

Note: `uv run --project .. python scripts/gen-sprite-states.py` stops with
`ModuleNotFoundError: No module named 'PIL'`. Pillow is not in the project environment. We ran
it with `uv run --project .. --with pillow python scripts/gen-sprite-states.py`.

## Limits

- `web/src/desk/sprites.ts` does not use `agent-pi` yet. The lane owner adds it.
- We looked at the sprites only on the contact sheet. We did not look at them on a real Desk
  page.
