# PHILO-9-03 canvas 1: the ITEMS section in the Room

**Status: DRAFT, for the owner's ratification** (UX-CANON §A.2: the canvas before the build). Nothing here is built in product code. The Q3 ruling: "Show them; enter by MCP" — the Room shows its items; no Add control on the face.

- Review page (every board, both widths): `index.html` in this folder.
- Boards: `shots/<board>-<width>.png` (1440x900 and 393x852, device scale 2); rendered facts: `shots/facts.json`.
- The same harness serves canvas 2 (`../story-03-delivery-canvas/`).

## What the boards are, exactly

- **A real hub and the product app.** `harness/shoot.py` starts the rig hub (`scripts/graph_walk.py serve`) on an isolated HOME and database (a `tempfile.mkdtemp` HOME; the owner's database is not touched). It seeds through the real HTTP routes: the project "Payments ledger cutover" (`POST /api/projects`); the milestone "Cutover rehearsal", due today − 7 days; the risk "Old ledger freeze slips" (severity high, likelihood high, impact high); the milestone "Ledger go-live", due today + 14 days (`POST /api/projects/{id}/items`, all 200, `facts.json` `_seed`); and the project "Vendor review" with no items.
- **Two servings of the product.** vite serves `web/index.html` twice (`harness/vite.config.mjs`): TODAY is the product on this branch, unchanged; PROPOSAL swaps ONE module — `ProjectMemoryCore`'s import of `ProjectRoomCore` resolves to `harness/ProposedProjectRoomCore.tsx` — and loads `harness/shim.ts` and `harness/canvas.css` before the app.
- **The proposal** (`harness/ProposedProjectRoomCore.tsx`, blocks marked `PROPOSAL`): a copy of `web/src/features/project-room/ProjectRoomCore.tsx` with (1) the `ItemsSection`, composed of library species only (`SurfaceSection`, `SurfaceLedger`, `SurfaceLedgerRow`, `StateChip`, `surface-token`), seated directly after NEEDS YOU; (2) the headline "1 needs you" (today "1 need you"). The section reads the existing `GET /api/projects/{id}/items` (the real route, real rows).
- **The unbuilt backend (story 01) is a stated rule, not a posed state.** `harness/shim.ts` rewrites only the Room read: a milestone with lifecycle `planned` whose `due_at` date is before today is LATE by (today − due) days; then `health.assessment = at_risk`, `health.reason = "1 MILESTONE LATE"` (only when the hub gave no reason), and NEEDS YOU gains one row per late milestone (`MILESTONE · 7 DAYS LATE`). With nothing late the hub's answer passes through unchanged.
- **Board 2 is a real transition.** `POST /api/projects/{id}/items/{id}/transition {"verb": "reached"}` (200, `facts.json` `_seed.transition`), then the Room reopened: health goes back to ON TRACK by the same rule.

## Boards

| # | Board | What it shows |
|---|---|---|
| 0 | Today | the product: no items section; `ON TRACK`; "Nothing needs you" — the milestone 7 days late is not shown (F2) |
| 1a | Late, first view | `1 needs you`; `● AT RISK` + `1 MILESTONE LATE`; NEEDS YOU 1: `▣ Cutover rehearsal · MILESTONE · 7 DAYS LATE`; `ITEMS 3` under it |
| 1b | Late, the section in view | `● Cutover rehearsal · MILESTONE · DUE SEP 20 · 7 DAYS LATE` (danger tone); `⚠ Old ledger freeze slips · RISK · LIKELIHOOD HIGH · IMPACT HIGH`; `○ Ledger go-live · MILESTONE · DUE OCT 11` |
| 2a | Reached, first view | the rehearsal marked reached: `ON TRACK`, "Nothing needs you" |
| 2b | Reached, the section | the risk and go-live first; `✓ Cutover rehearsal · MILESTONE · DUE SEP 20 · REACHED` last |
| 3a | Empty (proposed) | "Vendor review", zero items: the section is **absent** — no head, no counter of zero |
| 3b | Empty (the other option) | the bare head `ITEMS` with nothing under it (`?items_empty=head`), for comparison |

## The strings (exact)

| Slot | String |
|---|---|
| Section head | `ITEMS 3` (`countLabel`); absent at zero |
| Row | lead glyph + title + tokens: type (`MILESTONE`, `RISK`, `DEPENDENCY`, …), `LIKELIHOOD <X>` `IMPACT <X>` (risk), `DUE MMM D`, then `N DAYS LATE` (late) or the closed lifecycle (`REACHED`, `MITIGATED`, …) |
| Lead | `●` failure = late; `⚠` warning = open risk; `○` idle = planned; `✓` success = closed |
| Order | late (most late first), open risks (by severity), planned (by date), closed |
| Health (story 01 rule) | `● AT RISK` + `1 MILESTONE LATE` / `N MILESTONES LATE` |
| NEEDS YOU row | `▣ <title>` · `MILESTONE · N DAYS LATE` (one row per late milestone; no verb) |
| Headline | `1 needs you` (today `1 need you`) |
| Verbs | none. No Add, no row verb: items enter by owner-authenticated MCP (`project.item.create`) |

## Three questions for the owner

1. **Health and NEEDS YOU count a late milestone as drawn** (`● AT RISK` + `1 MILESTONE LATE`; one NEEDS YOU row `MILESTONE · 7 DAYS LATE` with no verb)? Recommended: yes.
2. **Seat: ITEMS directly after NEEDS YOU**, before UNFINISHED and SOURCES (what needs him, then the plan)? Recommended: yes.
3. **Zero items: the section absent (3a) or a bare `ITEMS` head (3b)?** Items enter by MCP, so a head with nothing under it and no verb is noise. Recommended: absent (3a).

## Measurements (`shots/facts.json`, 14 renders)

- **Text under 12 px, proposal nodes:** 0 on every board, both widths.
- **Text under 12 px, inherited (the Room's own species, not changed here):** the head's `CHECKED`/time chip (`.surface-token.room-chip-faint`, 11 px) on every board; and on boards 1a/1b the reason chip `1 MILESTONE LATE` (11 px, the same class) and the NEEDS YOU why token `MILESTONE · 7 DAYS LATE` (`.room-why-token`, 11 px). These carry this canvas's words in existing 11 px species: **the story 03 build must lift them to 12 px** (the same `data-chip`/label-size repair PHILO-7-02 made).
- **Raw (non-library) buttons in the window:** 0 on every board.
- **Chip contrast (WCAG, text over the composited background):** every proposal chip and token ≥ 6.85:1 (lowest: the `●` late lead and the `7 DAYS LATE` token, 6.85:1); no chip in the window under 4.5:1.
- **Add controls inside ITEMS:** 0 (no button, no input) on every board.
- **Horizontal overflow:** none (page and window body) at both widths.
- **Modal / "send":** none.

## Limits

- Health and NEEDS YOU are the shim's rule (story 01 builds it in `ProjectService`), not the hub's answer. The rule is stated in `harness/shim.ts` and derives from the real item rows.
- The section reads the list route (`GET /api/projects/{id}/items`). Story 01 may carry the items in the Room read instead; the face is the same.
- At 393 the ledger rows stack (lead, title, tokens on three lines): the `SurfaceLedgerRow` species at a narrow container, unchanged.
- The Ask well at 393 (F10) and RECEIPTS (F7) are shown as they are today; they are story 03's other repairs, not this canvas.
- Dependencies, signals and workstreams are drawn by the same rule but were not seeded.

## Fence sketch (story 03, after ratification; not built)

Real hub, isolated HOME, seeded by the real item route, rendered at 1440 and 393:

| After | Assert | Red on main |
|---|---|---|
| a milestone due today − 7 | the ITEMS row reads `7 DAYS LATE`; the health chip reads `AT RISK`; NEEDS YOU has the row; each equals the hub's Room read in the same fence | no section; `ON TRACK` |
| `transition reached` | `ON TRACK`; the row reads `REACHED`, last | — (new) |
| a project with no items | no `[data-testid=items-section]`, no `ITEMS` head | preservation |
| every state | no button or input inside ITEMS; no text under 12 px in the Room window | the 11 px reason/why chips |

## Reproduce

```bash
PLAYWRIGHT_BROWSERS_PATH=$HOME/Library/Caches/ms-playwright \
  uv run --extra test python pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-03-items-canvas/harness/shoot.py
```

It boots the hub on an isolated HOME, serves both vites (proposal on `CANVAS_PORT`, default 4441), shoots both canvases and writes both `facts.json`.
