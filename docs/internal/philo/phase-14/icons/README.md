# PHILO Phase 14, lane A0: the icon mold

> **RULED 2026-10-07 by Muad'Dib (owner: "you make ALL the calls, including the icon selection"): D1 Workbench+, all 17 kinds.** In situ it is the only direction that belongs to the steel desk: bevelled grey-blue objects with the ember as the one warm note; the drawer family matches; the reel-to-reel reads as a recording without repeating the Dock's mic; the two agents stay distinct at 32 px. D2 reads as Mac System 7 in our colors; D3 is wood and brass against steel. Notes for the install (lane A0b): memory stays the chip for now and is redrawn later on the same stem; the four paper kinds (ticket, pinned note, plain, sealed) keep their silhouettes through the state variants; the 32 px set is to be redrawn at 32, not scaled, when the list view lands.


**Status: a canvas. The owner picks.** The owner, on the icons: "the existing icons are pretty cringe and deserve a freaking overhaul ... we still have PixelLab MCP which is insane". This folder holds three directions for the 17 kinds of Movement A. Nothing in `web/public/desk/sprites` or `web/src/desk/sprites.ts` changed.

The page: `sheet.html` (open it from this folder). One row per kind: the current sprite, D1, D2, D3, each at 64 px on the desk (`--wb-backdrop` #3c4454 with the `--wb-dither` checker) and at 32 px on the steel screen (`--wb-steel` #9ea4b0). Under them: board A-1 with each direction pasted in. At the top: "Your call".

## Files

- `candidates/<D>/<kind>-64.png`: the pick, as PixelLab made it (64x64 native, no rescale).
- `candidates/<D>/<kind>-32.png`: the list-row size. A 2x2 box average, then the alpha cut at 50%, so the edge stays hard.
- `current/<kind>.png`: the sprite that stands for the kind today (copies, for the page).
- `insitu/<D>-left.png`, `<D>-right.png`: board A-1 (`canvas/shots/A-1-1440.png`) with the sprites replaced. Counts and lamps are the board's pixels. `control-*` is the board as drawn.
- `batches/<D>-b1.png`, `-b2.png`: every candidate PixelLab returned (16 per batch), picks and rejects.
- `tools/`: the scripts (contact sheet, 64/32 cut, in-situ paste, page build) and `picks.json` / `ids.json`. They read the raw candidates from the session scratchpad; the raw files are not in the tree. `batches/` shows them.

## Method

One `create_1_direction_object` call per batch, size 64 (16 candidates, one per `item_descriptions` entry, 20 generations per call). Each direction has one style stem. The stem is the call's `description` and the head of every item. The items name the object only. Batch 1 per direction: 16 kinds. Batch 2: memory (four ideas) plus the rerolls of the weak kinds. Picks were made by looking at each candidate on both grounds at 64 and 32.

### The three stems

- **D1 Workbench+** (view `sidescroller`). Description: `Amiga Workbench 2.0 desktop icon, bevelled steel grey and slate blue metal, one ember orange accent, hard pixel shading, 3/4 view, dark outline`. Item head: `Workbench steel icon: <object>`.
- **D2 Signal objects** (view `sidescroller`). Description: `flat bold desktop icon, Mac System 7 style, chunky simple silhouette, two-tone cool grey and white with one ember orange accent, front view, thick black outline, no texture`. Item head: `flat System 7 icon, front view: <object>`.
- **D3 Tactile desk** (view `top-down`). Description: `rich tactile pixel art desk object, paper grain, brushed metal, worn tape, warm palette cream brown amber with ember orange, top-down three-quarter diorama view, dark outline`. Item head: `tactile diorama desk object: <object>`.

## Picks (PixelLab object ids, tags `p14-icons-D1|D2|D3`)

Each pick was promoted with `select_object_frames`; the id is the promoted object. `bN:i` is the batch and the frame in `batches/`.

| Kind | D1 | D2 | D3 |
|---|---|---|---|
| project drawer | `5e6870c4-7856-4501-ab10-9ddff39e4ac2` b1:0 | `32249d26-2d0b-4cb0-b8be-24190bf25e6c` b1:0 | `718ce286-2085-4cac-8a78-a95f2215b206` b1:0 |
| smart drawer | `65c80b4a-ab6d-4453-be27-4b4c17a5ad40` b2:4 (lens) | `cb03ed4d-c3c3-4449-b3c5-028f50a68d6f` b2:5 (lamp) | `7626352f-f950-44ed-ae53-c76c6c2ddcb4` b2:6 (lantern) |
| Conductor drawer | `14618dfc-55c5-413d-9ff0-bd6902c7b445` b2:7 | `47ddf9a5-027d-4062-b448-cfc2bf5ca9a5` b2:6 | `923bb65f-930b-44d6-9c17-02af27fae217` b2:7 |
| Parked drawer | `2bd5e79a-cd55-4068-bbb3-04c64e8bd3de` b1:3 | `83080520-bd16-4e42-9a00-6d7924c3ed41` b1:3 | `19c031cd-7140-46d3-a61a-0f55a3d8ff1e` b1:3 |
| meeting | `d45849f2-6e03-4450-9d13-ea90e70d66af` b1:4 (reel-to-reel) | `0827e06e-d90b-4047-862e-0076cba33184` b2:11 (tape recorder) | `295dabb3-3058-4341-95a6-4c3f45b8e619` b1:4 (reel-to-reel) |
| note | `4646b125-41ca-486e-bcf2-a992ffff9f56` b1:5 | `d9a84c61-9d90-46e1-ab21-ebef3b29f30a` b1:5 | `ae2dc9d9-b64d-47b5-8b93-5824bb12e8d1` b1:5 |
| decision | `12178bdb-f589-4ff4-8b70-701d0be74051` b1:6 | `6965ffd0-2c68-4486-8e4a-06f8047aeac5` b1:6 | `f0f4ca74-144a-46e1-a03c-c9b027999d99` b1:6 (sealed scroll) |
| action item | `ba74bc96-aa44-4d57-a95e-17614cbe9492` b1:7 | `fd6efdba-21bd-49e4-80a4-5fa4f2943840` b1:7 | `c88569c4-9b75-46a8-98e6-4d241b157b1f` b1:7 |
| artifact | `ffd45ade-41cf-430c-ba95-edbd43bc9bc8` b1:8 | `4f516974-e52d-47d3-8a8d-b5c821216773` b1:8 | `d447ebc3-7be3-4e43-8142-7ee441b7439a` b1:8 |
| pull request | `30f3e4bd-59e2-4b53-bb3b-946ee6b02426` b1:9 | `d6a79e09-5444-412b-ac4d-a1b4df397c19` b1:9 | `391215b3-6632-4b51-bdb6-8dfe4321d5c6` b2:9 |
| repository | `7325ff12-0b50-4abe-b96c-8da56e00ddbd` b1:10 | `ccc6d4f7-78c5-4876-8238-195ca3044a0b` b1:10 | `58ba02b5-64e8-4a71-a6e6-105f28fc102e` b1:10 |
| person | `567cfef4-b7cf-40a4-8a53-aa07d8e8ae16` b1:11 | `c9a35ab9-7188-4ff1-8dee-f719bcd39b2f` b1:11 | `2a981674-abd3-4fab-a18a-c17da6facfab` b2:14 |
| people ledger | `77242e8a-cf1d-4607-b013-3090e61ec924` b1:12 | `68158e2f-1597-4fc2-9ca1-14848436236c` b1:12 | `8e381016-188e-46ea-ad04-7658c9f23294` b1:12 |
| agent: Claude Code | `1c936981-886d-4dfd-9ce5-0415e2e61ff2` b1:13 | `fb2cbd93-6514-4713-a9f2-12b80c426c70` b1:13 | `127de57a-bc63-4eb5-835a-b6f6ddcf6aac` b1:13 |
| agent: Codex | `ebbeb58c-bd93-471c-8229-dd1ce79766d9` b2:13 | `f275aa5f-eb5f-49c0-bed4-f5fcc8b457db` b1:14 | `d66931ba-5678-460c-9583-9046313c9a2b` b2:13 |
| thread | `ecdcb2b8-b182-4d07-ae44-df9cb515b2ea` b1:15 | `b657b064-f424-4191-86c8-62951a7d6444` b1:15 | `858168f6-aaaa-49dd-805a-8a30e96d9b9f` b1:15 (spool) |
| memory | `3b094ff5-4dd9-4f63-b01e-996aac125e17` b2:0 (chip) | `ae14c505-bec0-4062-b481-a23eab83f35a` b2:0 (chip) | `54c62b25-d9cc-431b-b29f-714f73505490` b2:2 (jar of sparks) |

Review batches (the frames above come from these): D1 `e4450453-dc1d-4f19-9fec-e888d73e8283`, `9dfc3d5c-7a74-400a-9f66-14ea32698bda`; D2 `abded5c2-cccc-4089-b5d4-f9fbee16f4e4`, `f3732b65-6420-49c9-ba23-f409a367031e`; D3 `0776900d-d374-4b41-8456-37d5cc619d3f`, `04cc0466-6030-4030-8cb9-9941b243c59b`.

## Generations used

**120 of the 300 budget** (6 calls x 20; `get_balance` before 0 used, after 120 used). 96 candidates for 51 picks.

## Rejects (the silhouette did not read at 64 without its label): 14

- D1 (5): smart drawer b1:1 (a lamp box, not a drawer); Conductor drawer b1:2 (the badge is lost at 64); b2:5 (the lamp cabinet reads as a locker); b2:9 (the antenna cabinet reads as a radio); memory b2:2 (the jar is empty at 32).
- D2 (5): meeting b1:4 and b2:9 (a reel alone reads as a wheel or a valve); Conductor drawer b1:2 and b2:7 (the badge is too small); memory b2:2 (the jar is empty at 32).
- D3 (4): smart drawer b1:1 (a box with a lens, no drawer); pull request b1:9 (thin lines vanish at 32); pull request b2:10 (an org chart, not a merge); Codex b1:14 (reads as a camera).

Not rejects, not picked: the other memory ideas (tome, card index) and alternates such as D1 b2:10 / D2 b2:10 (a studio mic). The mic reads well, but the Dock's Speak already wears a mic.

## Honest limits

- All 17 kinds have a pick in all three directions. None is unreadable at 64. The weak ones, by eye:
  - **D2 people ledger**: a plain grey book with tabs. It reads as a binder; the tabs carry it.
  - **D2 memory** and **D1 memory**: a chip. It says "memory" to an engineer; to anyone else it needs its label. **D3 memory** (a jar of sparks) is the most charming and the least literal.
  - **D3 note**: the scribble is noise at 32. **D3 action item**: the ticket lines blur at 32; the ticket shape still reads.
  - **D2 pull request**: a dark page, off D2's white-page rule. It reads.
- Family drift inside a direction: **D3 project drawer** is a wide cabinet; its smart and Conductor drawers are narrow single drawers (they came from batch 2). D1's drawers match (one steel cabinet language); D2's drawers match.
- **D1 is not isometric.** PixelLab drew it front-on with a bevel; "3/4 view" in the stem did not take. D3 has the most depth.
- The 32 px row is a downscale of the 64, not a drawn 32. D2 holds up best at 32 (by design); D3 holds up least.
- Not made: state variants (`_sel`, `_stale`, the agents' states). They come from `web/scripts/gen-sprite-states.py` after the pick.
- Not checked: the owner's screen; a real phone. The page was shot at 1440 and 393 in Chromium (no page-level sideways scroll; the table scrolls inside itself at 393).

## A0b: the install (2026-10-07)

- World sprites: the 17 D1 icons are in `web/public/desk/sprites/<kind>.png`; `VARIANTS` in `web/src/desk/sprites.ts` maps every kind to one file. The old mold is parked in `web/public/desk/sprites/_parked-2026-10-07/`.
- States: `web/scripts/gen-sprite-states.py` now traces the `_sel` rim one pixel OUTSIDE the alpha edge and lifts brightness by 1.14 (was inside, 1.24). The inside rim erased the dark outline of the four paper kinds. `a0b-shots/states-paper-agents.png` shows rest, sel and stale on both grounds.
- Dock and chrome: 16 glyphs drawn by PixelLab at 32 px in the D1 stem, one call (review object `cf4c9f3f-a901-44e0-9dc8-50e9d263c4af`, 20 generations). At size 32 the tool returns one 256 px sheet on a 10 x 10 grid, cut into 64 frames on a 32 px pitch; the frames do not hold whole objects. The objects were cut from the reassembled sheet on the 25.6 px pitch and centred in 32 x 32. Picks (sheet cell): dock-speak 8, dock-meetings 18, dock-agents 21, dock-settings 25, dock-people 40, floor-grid 45, menu-mark 50, menu-bell 65, menu-search 60, mic 73, mic-listening 74, mic-recording 76, record-orb 81, cadence-metronome 78, empty-loops 89, empty-nudges 90. The old set is parked in `web/public/desk/sprites/system/_parked-2026-10-07/`. `a0b-shots/dock-glyphs-old-vs-d1.png`: old (top two rows), D1 (bottom two rows).

## A0c: the 32 px set, drawn at 32 (2026-10-07)

**RULED by Muad'Dib (the owner's autonomy ruling): the picks in `32px/sheet.html`.** The list rows showed the 64 px D1 icons scaled to 32, so the art lost pixels. All 18 base sprites (the 17 kinds plus `cartridge`) are now drawn at 32.

- Files: `web/public/desk/sprites/32/<name>.png` with `_sel`/`_stale` from `web/scripts/gen-sprite-states.py` (the script now walks the 64 set and `32/`; same rim 1 px outside, same lift 1.14; no change was needed for 32).
- Code: `spriteUrl(kind, id, state, agent, size)` takes `size` 64 (default; every old call unchanged) or 32. `listSprite(url)` maps a 64 px world-sprite URL to its 32 px sibling and leaves any other URL alone. ObjectList, NeedsRow, ConfirmLine, PRCard and the DeskIcon badge read through it; the lane title icon asks for size 32. The icon view, Get Info and the drag ghost keep the 64.
- `objectSprite(kind, id, state, size)`: every kind reads its own D1 file. Before, action items wore `note`, PRs wore `artifact` and a person wore the people ledger (the pre-A0b borrowing, left in `kinds.ts` after A0b drew those kinds). The screen's People drawer asks for `people` (the ledger) in `screen/compose.ts`; one loose person wears the badge.
- The Needs you sprite is the 32 at 1:1 in the 40 px cell (4 px padding); the PR card's sprite goes from 20 px (scaled) to 32 px.

### Method

Seed: the 64 px icon, a 2x2 premultiplied box average, the alpha cut at 50% (`32px/tools/seed.py`). Then `edit_image_pro_flash` at 32x32 on the seed with a text description per kind ("redraw ... as clean crisp 32x32 pixel art: same object, same silhouette and placement, same palette, hard pixel clusters, no anti-aliasing, a clean 1 pixel dark outline, simplified detail, transparent background"). e1 = seed 1 for all 18; e2 = seed 2 with a firmer description, for the 11 kinds where e1 had a flaw or a close call. Every result: 32x32, no partial alpha. Job ids per candidate: `32px/tools/picks.json`; the page: `32px/tools/page.py` + `page.tpl`.

### Picks (e1 / e2 as on the sheet)

action-item e1, agent-claude-code e2, agent-codex e1, artifact e2, cartridge e2, conductor-drawer e1, decision e2, meeting e1, memory e1, note e1, parked-drawer e1, people-ledger e1, person e1, project-drawer e1, pull-request e2, repository e1, smart-drawer e2, thread e1. The reason for each pick is on the sheet. Rejects that matter: pull-request e1 (dropped the paper: a second silhouette), cartridge e1 (false letters on the label), agent-claude-code e1 (the antenna knob floats).

### Generations used

**150** (30 edit calls x 5; `get_balance` 140 used before, 290 after; credits $0.00 both times). Three calls failed on a malformed base64 seed (my paste) and were not charged; the seeds after them were sent as 32-colour PNGs (shorter).

### Also from #934

- The idle mic (`system/mic.png`) and the Speak glyph (`system/dock-speak.png`) are lifted: grey pixels move toward the steel highlight (l -> l + (0.84 - l) x 0.4), the dark outline and the ember accent unchanged (`32px/tools/lighten-dock.py`). The D1 originals are parked in `system/_parked-2026-10-07/a0c-dark/`.
- Not changed: kb/roadmap wear `artifact`, story wears `note`, the capability kinds keep `cartridge` (no 32 px kind fell out for them).

### Honest limits

- The 32 px art keeps the 64's composition because it starts from the 64's seed. It is a redraw of the seed, not a new drawing from a blank canvas.
- The cartridge's 32 has no DATA label text (letters do not survive 32 px).
- `conductor-drawer` touches the bottom edge (as its 64 does), so `_sel` has no rim on that edge.
- The window title icons (drawer, Conductor, Info, 20 px) still scale the 64; 32 to 20 is not an integer step either. Left for a chrome pass.
- In the Components gallery the Codex Needs row shows the Claude Code robot: the gallery row passes `kind="agent"` with no agent name. A face passes the sprite (the Conductor does); lane A5 must do the same.
- `tests/e2e/test_philo14_a0b_codex_sprite_glass.py` fails on main too (the page asks for `agent-claude-code.png`, likely the Conductor drawer's badge `spriteUrl("coder", "conductor-badge")`); inherited, not changed here.
- Shots: `32px/shots/` (before/after at 1440 and 393: a drawer's list, the Conductor's list, Needs you rows, the lane; the sheet). Checked in Chromium only.
