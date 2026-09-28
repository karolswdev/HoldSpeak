# PHILO-9-03 canvas 2: copy and confirm delivery

**Status: RATIFIED 2026-09-27 by the owner ("Ratify as drawn"), after Codex Astra r1 DNR → r2 DNR → r3 RATIFY** (`../../checks/canvases-astra-r1.md`, `../../checks/canvases-astra-r2.md`, `../../checks/canvases-astra-r3.md`; AskUserQuestion; review page https://claude.ai/artifact/ADQeZoxRYmWfYKEfL8wePT). His pick, verbatim: "Ratify as drawn (Recommended)", all seven recommendations. This canvas: Q2 the list chip `DELIVERED ×N`; Q3 the To field and Mark delivered above the update body. Build exactly this. The seven answers across the four canvases: Q1 items after NEEDS YOU, omitted when empty; Q2 DELIVERED ×N; Q3 To + Mark delivered above the body; Q4 grant words set A; Q5 per-project list behind a visible ▸ Projects; Q6 the accent selection colours; Q7 at 393 the fold line.

Earlier status: (UX-CANON §A.2). Nothing here is built in product code. The rulings: Q0 "Copy to clipboard only" and "Several per update". Round two paid Codex Astra r1 findings 4 and 5 (`../../checks/canvases-astra-r1.md`); round three pays Codex Astra r2 findings 1–3 (`../../checks/canvases-astra-r2.md`): the held confirmation bound to its update, the draft's content repairs under the `surface` container, and a real nine-point pointer pass.

- Review page (every board, both widths): `index.html` in this folder.
- Boards: `shots/<board>-<width>.png` (1440x900 and 393x852, device scale 2); rendered facts: `shots/facts.json`.
- Harness: `../story-03-items-canvas/harness/` (one harness serves both story 03 canvases).

## What the boards are, exactly

- **A real hub and the product app.** The same run as canvas 1: the rig hub on an isolated HOME; "Payments ledger cutover" seeded through the real routes; one update drafted and published (200, 200; `facts.json` `_seed.update`). Board 8's draft is a real `Draft` press.
- **The proposal** (`harness/ProposedUpdatePosture.tsx`, `harness/proposedUpdateController.ts`, blocks marked `PROPOSAL`), copies of the product's Update posture and controller:
  1. **DELIVERY** first on a **published** update: the `To` field (library `StringGadget`, its mic built in) and **Mark delivered** (library `Button`, primary). Offered after Copy, after he leaves and returns, after earlier deliveries. A draft shows none of it.
  2. **The history**: one row per delivery, oldest first — `✓`, the To (or `—`), `SEP 27 21:30`. Head `DELIVERY` with no rows, `DELIVERED N` with N.
  3. **The failure faces** (Astra r1 F4): a named refusal (`✗ REFUSED` + the plain token, the hub code on `data-code`); and a result unknown (`⚠ NO ANSWER · RESULT UNKNOWN`, the verb becomes `Retry`). Never "not marked".
  4. **The update list:** the DELIVERED chip (`?chip=count` → `✓ DELIVERED ×3`; `?chip=latest` → `✓ DELIVERED SEP 27 21:30 · LENA`) and the F11 words (`UPDATES N`; `PUBLISHED` `REV 1`; the `▤` glyph).
  5. **Back** sits in the editor's head verbs (`SurfaceVerbs`, the sticky head species), not at the foot of the body (below).
- **The canvas carries the library repairs its geometry needs** (`harness/canvas.css`, "PROPOSED LIBRARY REPAIRS"; the story 03 build moves each into the named file): `.surface-token` and `.surface-provenance-source` at 12 px; the editor rail's chips at 12 px, the rail wrapping, and the editor column shrinkable (`.desk-editor` one `minmax(0, 1fr)` column; `.update-editor`/`.update-body-editor` children `min-width: 0`), so the draft editor no longer runs past the body; the body mic in its own line (it sat absolute over the rail's `List` and `1.`) — these content repairs sit under `@container surface (max-width: 559px)` (`canvas.css:71`), so a narrow window on a wide desktop gets them too (Astra r2 F2); the mixed/cloud egress chip text `--accent-hover` (4.29:1 → 5.47:1); and, as a DEVICE rule only (`@media (max-width: 420px)`, `canvas.css:93`, UX-CANON D's one exception), a 44 × 44 size for the non-`.btn` controls touched (the To field's in-well mic, the rail chips, the body mic). No content moves in that rule. The citation chips (SOURCES) and the claim-ref chips (`ITEM`) are the library `Button` (`ghost`, dense), not raw `<button>`s, so they carry the library's 44 px halo at 393.
- **The unbuilt backend is stated, not posed** (`harness/shim.ts`): the stored rows of `project_update_deliveries` stand in `sessionStorage`; `GET …/updates` carries `deliveries`; `POST /api/updates/{id}/delivered` refuses a draft `update_not_published`, replays a known `command_id`, refuses a changed payload under the same key `idempotency_conflict`, else appends one row. **Two fixture faults, stated on their boards:** `__philoRefuseNext` (the next mark answers 409 with a named hub code) and `__philoLoseNext` (the next mark COMMITS its row, then the answer is lost as a network error). Copy is the product's real Copy (`clipboard_head` in `facts.json`).

## The retry rule (settled; Astra r1 F4, r2 F1)

One confirmation is one `{update_id, command_id, delivered_to}`, held **per update** (`proposedUpdateController.ts:95-125`). A press mints a key only when that update holds no confirmation. While a confirmation is **pending** or its result is **unknown**, that update's To field is **locked** to the held payload, and the request always goes to the **held** `update_id` — never to whichever update is open (`:290`). Opening another update neither takes over nor clears the lock, the unknown result or the Retry: each update keeps its own. A new key is minted only after the result is **known** — a row came back (the field clears) or the hub named a refusal (the field unlocks with his words). A lost answer keeps the update, the key and the payload; `Retry` sends all three again, and the hub's replay returns the original row if it was recorded.

Proved at both widths with real clicks (boards 6c → 6f; `facts.json`): lose the answer on A → Back → open B (B: field free, no Retry, no unknown — `b_state`) → Back → open A (A: `RESULT UNKNOWN`, `Lena` locked, Retry — `a_state`) → Retry: the call goes to A's URL with the same key and To (`retry_same_update`, `retry_same_key`, `retry_same_to` all true) → one Lena row on A (`lena_rows_on_a` 1), none on B (`b_rows_after` 0, `b_calls` 0). On board 6e A's history already lists the Lena row: the read shows what the hub recorded, while the face keeps the press's result unknown until Retry resolves it.

## Settled (not asked)

- **A mistaken mark stays** (the charter, "A mistaken delivery"): board 6 — the wrong row kept, the count includes it, no undo ("Undo a delivery" is on the BACKLOG).
- The named refusal and the result-unknown faces above.

## Boards

| # | Board | What it shows |
|---|---|---|
| 0a / 0b | Today | `DRAFTS 1`, the fixed `E`, the words run together (F11); published: Regenerate and Copy only |
| 1 | After Copy | `Copied` (2 s, unchanged); DELIVERY: the To field and Mark delivered |
| 2 | He left and returned | a full reload, the Room reopened: `Copy`, Mark delivered still offered (no clipboard state; R4-3) |
| 3 | To typed | `Priya` |
| 4 | Pending | Mark delivered loading, the field disabled |
| 5 | Delivered once | a **double-click**: one call, one row (`calls_after_double_click`) |
| 6 | The mistake kept | Priya was the wrong person; `Tomas` added; both rows; `DELIVERED 2` |
| 6b | Refused (fixture code) | `✗ REFUSED` `NOT PUBLISHED`, `data-code="update_not_published"`; nothing recorded; the field unlocked with `Priya` |
| 6c | Result unknown (fixture fault) | `⚠ NO ANSWER · RESULT UNKNOWN`; the field locked to `Lena`; the verb `Retry` |
| 6d | Another update, clean | Back, open update B: its field free, no Retry, no unknown result, no rows |
| 6e | Back on A | A still `⚠ NO ANSWER · RESULT UNKNOWN`, `Lena` locked, `Retry`; the read lists the committed Lena row |
| 6f | Retried on A | Retry to A's URL, same key and To: one `Lena` row on A (`DELIVERED 3`); B has none |
| 7a | List, chip ×N — after Back | Back returned to the list at both widths (`_back`); `✓ DELIVERED ×3` |
| 7b | List, chip latest | `✓ DELIVERED SEP 27 21:30 · LENA` |
| 8 | A draft | no DELIVERY; the rail wraps inside the body at 393; the body mic on its own line |

## The strings (exact)

| Slot | String |
|---|---|
| Section head | `DELIVERY` / `DELIVERED N` |
| Field | `To` (name and placeholder); mic `Speak To` |
| Verb | `Mark delivered`; `Retry` while the result is unknown |
| History row | `✓` · the To or `—` · `MMM D HH:MM` |
| Refused | `✗ REFUSED` + `NOT PUBLISHED` (`update_not_published`) / `OWNER ONLY` (`project_delegation_required`) / `ALREADY USED` (`idempotency_conflict`: the hub saw this key with other arguments. The held-per-update lock keeps this face from causing it, but the hub still returns it to another client or a stale tab, so the face names it) |
| Result unknown | `⚠ NO ANSWER · RESULT UNKNOWN` |
| List chip | `✓ DELIVERED ×N` or `✓ DELIVERED MMM D HH:MM · <TO>` |
| Never | "send", "sent", "not marked", an egress badge, a modal |

## Two questions for the owner

1. **The list chip: `DELIVERED ×3` (7a) or the latest time and To (7b)?** Both fit at 393. Recommended: ×N — short; the names are in the history on the update.
2. **DELIVERY first on the published update, above the body** (the To field beside its verb), not in the footer beside Copy? Recommended: yes.

## Measurements (`shots/facts.json`, 32 renders; boards 0a/0b are the product today)

On every proposal board (1–8), at 1440 and 393, the whole Room window **including its footer**:

- **Text under 12 px:** 0 (proposal and inherited).
- **Raw (non-library) buttons:** 0 (today's boards: 10 on 0b, the citation chips).
- **Chip contrast:** every chip ≥ 5.47:1 (lowest: `LOCAL + CLOUD`, now `--accent-hover`; today 4.29:1).
- **Pointer pass (Astra r2 F3; `harness/shoot.py:166-236`):** every Button in the window — body, head verbs and footer (menus when open; none open on these boards) — at NINE points (centre, four edge midpoints, four corners, inset 1 px; the painted face at 1440, the 44 × 44 target at 393), each with `elementFromPoint` AND a real `page.mouse.move` whose `pointermove` target is recorded. Proposal boards (1–8), both widths: **332 touched-control renders, 0 failures** (Mark delivered / Retry, the To mic, Back, the citation and claim-ref Buttons, the draft rail's chips and the body mic); the untouched footer verbs (Regenerate, Copy, Save, Publish) are owned too. 4,698 points in all.
- **Horizontal overflow:** none (page and window body), including the draft at 393.
- **Back:** returned to the list at 1440 and 393 (`facts.json` `_back`: one click each).
- **"send"/"sent", egress badge in the delivery states, modal:** none. **Double-click:** one call, one row, both widths.

**Named, not paid here (controls this canvas did not touch):** the window chrome (`Close`, `Minimize`, the `ROOM` wing tab) fails the corner probe — neighbouring chrome at 1440, the 44 × 44 target at 393 (`pointer`, `touched: false`).

**The 393 Back defect, found and fixed.** Round one: at 393 Back at the foot of the editor got no click. Measured (round two, event log): on `pointerdown` Back took focus, the body scrolled and the button moved 36 px (top 534 → 570) before `pointerup`, which landed on a `DIV`; the `click` went to `.update-editor`, not the button. Back was in a `SurfaceVerbs` — a **top**-sticky species (surface.css:12) — placed at the end of the body. The canvas seats Back in the editor's head verbs (`ProposedUpdatePosture.tsx:518`); both widths then return to the list on one click.

## Limits

- The delivery table, read-back and route are unbuilt (stories 01 and 02); the rows live in `sessionStorage`, so "return" is a reload of the same tab. The refusal on board 6b and the lost answer on board 6c are fixture faults; the codes are the route's own set.
- `delivered_at` is the shim's clock at the press; operation ids are the shim's. RECEIPTS showing each delivery write (story 01) is not drawn.
- At 393 the history rows stack (the `SurfaceLedgerRow` species at a narrow container).

## Fence sketch (story 03, after ratification; not built)

| After | Assert | Red on main |
|---|---|---|
| reopen a published update (after Copy, after a reload) | `Mark delivered` offered; no stored clipboard state | no verb |
| To `Priya`, press; To `Tomas`, press | two rows read back from the hub in the same fence; the face shows both; the chip reads the ratified form | new |
| a double-click on one press | one row, one `command_id` | new |
| the hub refuses | `REFUSED` + the token; `data-code` equals the hub's code; the field unlocked | new |
| the answer is lost after commit | `RESULT UNKNOWN`; the field locked; `Retry` sends the same update, key and To; one row | new |
| lost on A → Back → open B → Back → open A → Retry | B clean (free field, no Retry); A still unknown with Retry; the retry's URL is A's, same key and To; one row on A, zero rows and zero calls on B | new (round one's face sent A's key to B's URL → `idempotency_conflict`) |
| the hub answers `idempotency_conflict` | `REFUSED` + `ALREADY USED`, `data-code` the hub's code | new |
| Back at 393 | one click returns to the list | no click (round one) |
| a narrow window on a wide desktop | the draft editor's content repairs apply (container rule), no overflow | mutation: the rule under viewport media |
| every state | no "send"; no egress badge; no modal; no text under 12 px; every touched control owned at nine points by `elementFromPoint` and a real pointer move (44 × 44 at 393) | — |

## Reproduce

```bash
PLAYWRIGHT_BROWSERS_PATH=$HOME/Library/Caches/ms-playwright \
  uv run --extra test python pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-03-items-canvas/harness/shoot.py
```
