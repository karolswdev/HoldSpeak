# PHILO-9-03 canvas 1: the ITEMS section in the Room

**Status: DRAFT, round two, for the owner's ratification** (UX-CANON §A.2). Nothing here is built in product code. The Q3 ruling: "Show them; enter by MCP" — the Room shows its items; no Add control on the face. Round two pays Codex Astra r1 findings 5 and 7 (`../../checks/canvases-astra-r1.md`).

- Review page (every board, both widths): `index.html` in this folder.
- Boards: `shots/<board>-<width>.png` (1440x900 and 393x852, device scale 2); rendered facts: `shots/facts.json`.
- The same harness serves canvas 2 (`../story-03-delivery-canvas/`).

## What the boards are, exactly

- **A real hub and the product app.** `harness/shoot.py` starts the rig hub (`scripts/graph_walk.py serve`) on an isolated HOME and database (a `tempfile.mkdtemp` HOME; the owner's database is not touched). It seeds through the real HTTP routes (`facts.json` `_seed`, every status 200): the project "Payments ledger cutover"; the milestone "Cutover rehearsal", due today − 7 days; the risk "Old ledger freeze slips" (severity, likelihood and impact high); the milestone "Ledger go-live", due today + 14 days; the milestone "Parallel run", due today − 10 days, moved to `missed`; the milestone "Vendor shadow run", due today + 5 days, moved to `dropped` (both by `POST …/items/{id}/transition`); and the project "Vendor review" with no items.
- **Two servings of the product.** vite serves `web/index.html` twice (`harness/vite.config.mjs`): TODAY is the product on this branch, unchanged; PROPOSAL swaps ONE module — `ProjectMemoryCore`'s import of `ProjectRoomCore` resolves to `harness/ProposedProjectRoomCore.tsx` — and loads `harness/shim.ts` and `harness/canvas.css` before the app.
- **The proposal** (`harness/ProposedProjectRoomCore.tsx`, blocks marked `PROPOSAL`): the `ItemsSection`, composed of library species only (`SurfaceSection`, `SurfaceLedger`, `SurfaceLedgerRow`, `StateChip`, `surface-token`, `Button`), seated after NEEDS YOU; its read is the existing `GET /api/projects/{id}/items`; and the headline "1 needs you" (today "1 need you").
- **The canvas carries the library repairs its geometry needs** (`harness/canvas.css`, "PROPOSED LIBRARY REPAIRS"): every `.surface-token` at the 12 px label size (surface.css:570 is 11 px — the head's reason chip and the NEEDS YOU why token), and the F10 repair: at a narrow window (`@container surface (max-width: 559px)`) the Ask well is in the flow, the last section, not sticky over the body (project-room.css:307). The story 03 build moves each into the named product file.
- **The unbuilt backend (story 01) is a stated rule, not a posed state.** `harness/shim.ts` rewrites only the Room read: a milestone with lifecycle `planned` whose `due_at` date is before today is LATE by (today − due) days; then `health.assessment = at_risk`, `health.reason = "1 MILESTONE LATE"` (only when the hub gave no reason), and one NEEDS YOU row per late milestone. Nothing late → the hub's answer passes through.
- **Board 2 is a real transition** (`Cutover rehearsal` → `reached`, 200): health goes back to ON TRACK by the same rule. **Board 4 is a fixture fault**: `?items_fail=1` makes the face's items read answer 503 (the shim's own health read is not affected).

## Settled (not asked)

- **A late milestone counts in health and NEEDS YOU** (the charter, "Items in the Room"): `● AT RISK` + `1 MILESTONE LATE`; the NEEDS YOU row `▣ Cutover rehearsal · MILESTONE · 7 DAYS LATE`, no verb.
- **Honest item states (Astra r1 F7):** late = `failure ●` + `N DAYS LATE`; open risk = `warning ⚠`; planned = `idle ○`; **missed = `failure ✗` + `MISSED` (danger tone)**; **dropped = `idle —` + `DROPPED`**; only reached/mitigated/closed/resolved earn `success ✓`.
- **A failed read is not empty (Astra r1 F7):** the section shows its head, `— ITEMS UNAVAILABLE`, and the library Button `Retry`. Empty (zero items, read succeeded) = the section omitted.

## Boards

| # | Board | What it shows |
|---|---|---|
| 0 | Today | the product: no items section; `ON TRACK`; the late milestone is not shown (F2) |
| 1a | Late, first view | `1 needs you`; `● AT RISK` + `1 MILESTONE LATE`; NEEDS YOU 1; `ITEMS 5` under it |
| 1b | Late, the section | late, risk, planned, `✗ Parallel run · MISSED`, `— Vendor shadow run · DROPPED` |
| 1c | SOURCES in view | 393: the Ask well is in the flow; the Steward verb and every head are clear |
| 2a / 2b | Reached | the rehearsal reached: `ON TRACK`; the row `✓ … REACHED` after the missed one |
| 3 | Empty | "Vendor review", zero items: no section, no counter of zero |
| 4 | Items read failed | `ITEMS` · `— ITEMS UNAVAILABLE` · `Retry` |

## The strings (exact)

| Slot | String |
|---|---|
| Section head | `ITEMS 5` (`countLabel`); omitted at zero; `ITEMS` + `ITEMS UNAVAILABLE` + `Retry` on a failed read |
| Row | lead + title + tokens: type (`MILESTONE`, `RISK`, …), `LIKELIHOOD <X>` `IMPACT <X>`, `DUE MMM D`, then `N DAYS LATE` or the closed lifecycle (`MISSED`, `DROPPED`, `REACHED`, …) |
| Order | late (most late first), open risks (by severity), planned (by date), missed, then the other closed |
| Health (story 01 rule) | `● AT RISK` + `1 MILESTONE LATE` / `N MILESTONES LATE` |
| Headline | `1 needs you` |
| Verbs | none on a row; `Retry` only on the failed read |

## One question for the owner

1. **ITEMS directly after NEEDS YOU, and omitted when a project has no items?** Recommended: yes.

## Measurements (`shots/facts.json`, 16 renders; boards 0 are the product today)

On every proposal board (1a–4), at 1440 and 393, the whole Room window **including its footer** (`footer_in_scan: true`):

- **Text under 12 px:** 0 (proposal and inherited).
- **Raw (non-library) buttons:** 0.
- **Chip contrast (WCAG, text over the composited background):** every chip ≥ 5.8:1 (lowest: `1 MILESTONE LATE`, 5.8:1).
- **Pointer ownership:** every control this canvas touched (the items `Retry`) is owned at its centre and four corners, the 44 × 44 target at 393.
- **The Ask well (F10) at 393:** `under_ask_well` is empty on every board (the well is `position: static`); on board 0 (today, sticky) it covers `SOURCES`, `Steward` and `RECEIPTS 10`.
- **Horizontal overflow:** none. **Add controls inside ITEMS:** 0. **Modal / "send":** none.

**Named, not paid here (controls this canvas did not touch):** at 1440 the sticky Ask well lies over the `RECEIPTS 10` head on the first view (1a, 2a) — the body scrolls it clear; the round-two repair is the narrow-window one Astra asked for. The window chrome (`Close`, `Minimize`, the `ROOM` wing tab) and the Ask well's `Speak` and `Submit` fail the corner probe (neighbouring chrome; at 393 the 44 × 44 target) — `facts.json` `pointer`, `touched: false`.

## Limits

- Health and NEEDS YOU are the shim's rule (story 01 builds it in `ProjectService`). The failed read is a fixture fault.
- At 393 the ledger rows stack (lead, title, tokens on three lines): the `SurfaceLedgerRow` species at a narrow container, unchanged.
- RECEIPTS (F7) and the steward counts (F3) are shown as they are today; they are story 03's other repairs.

## Fence sketch (story 03, after ratification; not built)

| After | Assert | Red on main |
|---|---|---|
| a milestone due today − 7 | the row reads `7 DAYS LATE`; health `AT RISK`; the NEEDS YOU row — each equal to the hub's Room read in the same fence | no section; `ON TRACK` |
| `transition missed` / `dropped` | `✗ … MISSED` (failure) / `— … DROPPED` (idle), never `✓` | new |
| the items read fails | `ITEMS UNAVAILABLE` + `Retry`, never an omitted section | new |
| a project with no items | no ITEMS section | preservation |
| 393, first view | `elementFromPoint` at the Steward verb hits the verb | `room-ask-well` |
| every state | no button or input on an item row; no text under 12 px in the window | the 11 px chips |

## Reproduce

```bash
PLAYWRIGHT_BROWSERS_PATH=$HOME/Library/Caches/ms-playwright \
  uv run --extra test python pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-03-items-canvas/harness/shoot.py
uv run --extra test python pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-03-items-canvas/harness/build_review.py
```
