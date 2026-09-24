# PHILO-4-01 canvas: Generate is always reachable (with the PHILO-4-02 row order)

**Status: UNRATIFIED, round two.** Astra checked round one and bounced it (six findings). This round pays them. The owner has not seen these boards. Build nothing until he ratifies them (UX-CANON A.2).

**Canvas:** https://claude.ai/artifact/LHjuHKL1pVZuh4aK5J9qRU

`morning-brief.html` is one self-contained page, with the shots inlined and no fetch. `morning-brief.png` shows the page at 1440 and `morning-brief-393.png` shows it at 393. Each board has its own PNG in `shots/` at `<board>-1440.png` and `<board>-393.png`, taken at device scale 2 from the `[data-testid=arrival-brief]` element. `shots/labels.json` lists the exact strings for each board. `shots/facts.json` holds the facts measured in the rendered DOM for each shot.

## Round two: what changed

1. **The 12 px floor, paid in the library** (Astra finding 1). Two readable texts in the BRIEF head were 10 px. Both are species bugs, so the fix is in the species, not on this face:
   - `web/src/desk/surface/surface.css:70` `.surface-section-head h3`: `font-size: 10px` → `12px` (weight 600, mono, `0.06em`, uppercase: kept).
   - `web/src/desk/surface/gadgets.css:840` `.gadget-chip`: `font: 600 10px / 1` → `600 12px / 1` (`0.08em`, uppercase: kept), and `:843` `white-space: nowrap` (new). At 12 px the chip broke `THIS DEVICE` onto two lines inside its etched frame at 393; a chip is one token, so it does not wrap.
   - `web/src/desk/surface/surface.css:59-65` (new rule): `.surface-section-head > .btn` and `.surface-section-head > .gadget-chip` get `flex-shrink: 0`. At 12 px the head is tight at 393: without this, flex squeezed `Generate` from 76 px to 71 px and its word ran over its own padding (text 58 px in a 53 px content box). With it, the label wraps and the verb and chip keep their width.
   - **Blast radius.** Every `SurfaceSection` head label on the desk is now 12 px (133 `<SurfaceSection` call sites in `web/src`). Every `.gadget-chip` is now 12 px and one line: the egress badge (`BriefEgress` and the other egress chips) and the secret-state chips (7 non-test `.tsx` files use the class). The head-shrink rule touches only a Button or a chip that is a direct child of a section head. `tests/e2e/test_hs202_05_first_use_type_floor.py:68,70` (and the other `h3@10px` / `.gadget-chip.gadget-chip-egress@10px` lines in `FLOOR_LEDGER`) record these two as sub-floor residue; that fence prints healed entries and does not fail on them (`:780-785`), so the ledger lines can go when that rig runs next. I did not run that e2e rig.
   - **The geometry change at 393.** At 12 px the head label `BRIEF · 4 THINGS WAITING` wraps to two lines at 393 on the populated boards (1, 2a, 3a, 4, 5; `head.label_lines: 2` in `facts.json`). `THIS DEVICE` and `Generate` stay on one line, at full width (`Generate` 76 px, its text inside its box on all 22 shots: `text_fits: true`). The round-one claim "Generate fits at 393" was measured on 10 px text; this round measures it on 12 px text. The case against `Generate again` holds: a longer label takes more width from the label, which then wraps further.
2. **Board 3a: one verb** (finding 2). Retry is gone from 3a. The enabled head `Generate` repeats the same POST, so a second verb did the same thing. Board 3b keeps Retry: it repeats the GET, a different action.
3. **The missing states** (finding 4): board 6 (no brief yet), board 7 (a brief, every row triaged: the branch that says `Generate again` today) and board 3c (Generate pressed from the 3b state).
4. **Accurate measurement claims** (findings 5 and 6), below.

## Method

`harness/main.tsx` renders the **real** library species with the real CSS: `SurfaceSection`, `SurfaceLedger`, `SurfaceLedgerRow`, `countToken`, the library `Button` (`components/signal/Signal`), `BriefEgress` and `Chair`, plus `styles/global.css`, `styles/react-app.css` and `desk/desk.css`. They sit in the BRIEF section's own markup (`web/src/desk/chair/ChairHome.tsx:1196-1330` and `BriefSection` at `:1978-2040`). A Vite dev server served that markup, and Playwright shot it at 1440×900 and 393×852 (`harness/shoot.py`). `harness/vite.config.mjs` holds absolute paths from the author's machine; change them to run it again.

## What the measurements prove, and what they do not

- **The 12 px floor.** `shoot.py` walks EVERY painted text node inside `[data-testid=arrival-brief]` and reads its computed `font-size` (`facts.json` `texts`, `min_text_px`, `floor_ok`). It fails the run if any shot is under 12 px. Result: `min_text_px: 12` on all 22 shots. It reads text nodes only; it does not read `::before`/`::after` content.
- **The hit probe.** For each Button, `elementFromPoint` at the center and at four points 1 px inside the left and right edges, 21 px above and below the center (`owns_44_band`). It does not probe edge midpoints, and it is not a real pointer. Result: `true` for every Button at 393; `false` at 1440, where the halo is not applied (the same as round one).
- **The head.** `head.label_lines`, `head.chip_h`, and for each Button `w`, `content_w`, `text_w` and `text_fits` (the text range inside the Button box).
- **Scope of the render.** The harness renders only the BRIEF section inside `Chair`, not the full Arrival. So the viewport numbers (`rows[].in_viewport`) do not prove clearance from the real Arrival footer or the sections above. That clearance is for the build to prove on the real face.
- **Order.** The `created_at` values of boards 4 and 5 live only in code comments in `harness/main.tsx` and in `labels.json`. The harness shows the proposed order; it does not prove that the producer or a reload keeps that order. Story 02 proves it.
- Also on every shot: `raw_buttons: 0`, no horizontal scroll (`scrollW` = `vw`), no console errors.

## The one placement

Generate goes in the BRIEF section's **head verb slot**, after the egress badge (`THIS DEVICE` before `Generate`). This is where `Generate` (no brief) and `Generate again` (nothing untriaged) sit today (`ChairHome.tsx:1231-1245,1293-1306`). It is the smallest lawful placement: the slot exists, and `SurfaceSection` already accepts `actions`. `BriefSection` passes them. The rows, Ack/Defer and `N more` do not change.

The rule for every branch: the head has the badge and Generate. Generate is **disabled while a read or a generation is open**, and enabled in all other states. The status slot under the section holds one line: the open request (`READING…`, `GENERATING…`) or the last failure.

## The boards (11 boards × 2 widths = 22 shots)

| # | Board | 1440 | 393 | What it shows |
|---|---|---|---|---|
| 0 | Today (reference) | `shots/0-today-1440.png` | `shots/0-today-393.png` | The face on main (with the 12 px library): no Generate while a row is untriaged; decisions come LAST, so the decision is behind `1 more` |
| 1 | Generate is reachable | `shots/1-generate-reachable-1440.png` | `shots/1-generate-reachable-393.png` | Day-one brief, 4 untriaged rows, Ack/Defer as today; badge + `Generate` in the head; the decision row leads |
| 2a | Generating | `shots/2a-generating-1440.png` | `shots/2a-generating-393.png` | `Generate` disabled (its label does not change); `GENERATING…` in the status slot; rows and caption stay |
| 2b | Reading | `shots/2b-reading-1440.png` | `shots/2b-reading-393.png` | The read is open: `READING…` (PHILO-3-03 state 2) with `Generate` disabled |
| 3a | Did not generate | `shots/3a-did-not-generate-1440.png` | `shots/3a-did-not-generate-393.png` | `BRIEF DID NOT GENERATE · HTTP 500`; **no Retry**: the enabled `Generate` is the recovery; the day-one rows, triage and caption do not change |
| 3b | Did not load | `shots/3b-did-not-load-1440.png` | `shots/3b-did-not-load-393.png` | PHILO-3-03 state 3 (`BRIEF DID NOT LOAD · HTTP 500` + Retry reads again), plus the head verbs, `Generate` enabled |
| 3c | Generate after a load failure | `shots/3c-generate-after-load-failure-1440.png` | `shots/3c-generate-after-load-failure-393.png` | `Generate` pressed from 3b: `GENERATING…` takes the status slot (the read-failure line and its Retry go), `Generate` disabled. Success: the populated branch with the receipt (board 4). Failure: `BRIEF DID NOT GENERATE · <cause>`, `Generate` enabled (board 3a) |
| 4 | Next day, one Generate | `shots/4-next-day-one-decision-1440.png` | `shots/4-next-day-one-decision-393.png` | The new decision is row 1 at both widths; caption `SEP 21 – 24 · GENERATED SEP 24 08:02`; the badge does not change; `3 more` = 6 − 3 |
| 5 | Next day, several decisions | `shots/5-next-day-several-decisions-1440.png` | `shots/5-next-day-several-decisions-393.png` | Decisions newest first (illustrated `created_at`: SEP 24 07:58, SEP 23 16:10, SEP 22 11:30 visible; SEP 21 09:05 in the fold); `4 more` = 7 − 3 |
| 6 | No brief yet | `shots/6-null-brief-1440.png` | `shots/6-null-brief-393.png` | No brief on the hub: `No brief yet` (A3) and `Generate` in the head. Busy: `GENERATING…` takes the place of `No brief yet`, `Generate` disabled (the 3c treatment). Failure: `BRIEF DID NOT GENERATE · <cause>`, `Generate` enabled. Result: the populated branch with the receipt (board 4) |
| 7 | Nothing untriaged | `shots/7-nothing-untriaged-1440.png` | `shots/7-nothing-untriaged-393.png` | A brief with every row triaged: headline `Nothing material changed.`, caption, `Generate` (today: `Generate again`). Busy: `GENERATING…` under the caption (the 2a treatment). Failure: the danger line under the caption, `Generate` enabled (the 3a treatment). Result: the populated branch with the receipt |

Boards 6 and 7 show their resting state. Their busy, failure and result states use the same treatment as boards 2a, 3a, 3c and 4 (named in each row above); they have no shot of their own.

Triage across the Generate (boards 1 to 4): the new brief has new item ids, so its rows start untriaged. The day-one rows keep their triage state on the day-one brief's shelf: nothing is acknowledged or deferred by the Generate. The Arrival shows only the latest brief, so that shelf is not on this face. The build proves it by reading the old brief back (story 01 acceptance 4).

The fold count is honest: `N more` = rows − 3. It shows only when N > 0 (`ChairHome.tsx:2027`), so it is never `0 more`.

## Exact strings (ASD-STE100)

| String | Where | New or kept |
|---|---|---|
| `Generate` | head verb, every branch | kept word (the no-brief verb, A3); replaces `Generate again` |
| `THIS DEVICE` | egress badge | kept |
| `BRIEF · <n> THINGS WAITING` / `BRIEF · 1 THING WAITING` | head label | kept |
| `BRIEF` | head label when there are no rows | kept |
| `No brief yet` | no brief on the hub | kept (A3) |
| `Nothing material changed.` | the brief's own headline, nothing untriaged | kept (the brief's words) |
| `Ack` · `Defer` · `<n> more` | row verbs, fold | kept |
| `GENERATING…` | status slot while the generation is open | new (READING… idiom); replaces the Button label `Generating...` |
| `READING…` | read open | kept (PHILO-3-03) |
| `BRIEF DID NOT GENERATE · HTTP <n>` / `BRIEF DID NOT GENERATE · NO ANSWER` | generation failed, `data-tone="danger"`, no Retry | new (PHILO-3-03 idiom) |
| `BRIEF DID NOT LOAD · HTTP <n>` / `… · NO ANSWER` | read failed | kept (PHILO-3-03) |
| `Retry` | after a READ failure only | kept |
| `<period_label> · <generated_label>` e.g. `SEP 21 – 24 · GENERATED SEP 24 08:02` | caption | kept (A3 law) |
| `Brief ready · <n> items · <time>` | receipt after the click | kept (`briefReceipt`) |

**Wording fence.** `web/src/desk/chair/__tests__/briefReceiptRendered202.test.tsx:79` expects `Generate again`. The build changes that assertion to `Generate` in the same commit that changes the label.

## Seams to bind (build after ratification)

- `ChairHome.tsx:1261-1266`: pass `actions={<><BriefEgress /><Button … disabled={generating || briefLoading}>Generate</Button></>}` into `BriefSection`, which gives it to its `SurfaceSection` (`:1993`).
- `:1198-1205` (read open) and `:1208-1224` (read failed): the same head verbs; disabled while the read is open. While a generation is open after a read failure, `GENERATING…` replaces the failure line and its Retry.
- `:1242` and `:1304`: the label is `Generate` in every branch; `Generating...` becomes the `GENERATING…` status line; the fence at `briefReceiptRendered202.test.tsx:79` moves with it.
- Generate failure: today it goes to `reportWriteFailure`. The branch gets `BRIEF DID NOT GENERATE · <cause>` (use `briefLoadCause`) with no Retry.
- Story 02 (Astra's lane): `:801` puts `decisions` first; decision items carry the decision record's `created_at` and sort newest first; the other sections keep their order.

## Readable text still under 12 px (ledger, not fixed here)

From `web/src/desk/surface/*.css` and `web/src/styles/global.css` (file:line, size, selector). Some are glyphs (a mic, a dot, an arrow, a fold marker); a glyph may go below the floor when a word carries its meaning (UX-CANON, the 12 px floor). One line each; each is a species fix for its own story.

- `desk/surface/filter-tokens.css:23` 11px `.surface-filter-token.btn`
- `desk/surface/gadgets.css:26` 10px `.gadget-group-label`
- `desk/surface/gadgets.css:72` 10px `.gadget-fact`
- `desk/surface/gadgets.css:180` 11px `.gadget-check-token-face`
- `desk/surface/gadgets.css:220` 11px `.gadget-cycle-glyph` (glyph)
- `desk/surface/gadgets.css:314` 10px `.gadget-mx-caption`
- `desk/surface/gadgets.css:378` 10px `.desk-next .gadget-string .desk-mic` (glyph)
- `desk/surface/gadgets.css:403` 10px `.gadget-unit`
- `desk/surface/gadgets.css:425` 6px `.gadget-arrows button` (glyph)
- `desk/surface/gadgets.css:579` 10px `.gadget-table-head span`
- `desk/surface/gadgets.css:601` 11px `.gadget-x` (glyph)
- `desk/surface/gadgets.css:615` 11px `.gadget-table-add`
- `desk/surface/gadgets.css:640` 11px `.gadget-table-cell`
- `desk/surface/gadgets.css:653` 9px `.gadget-ledmeter-label`
- `desk/surface/gadgets.css:706` 10px `.gadget-lamp`
- `desk/surface/gadgets.css:763` 9px `.desk-next .desk-mic.gadget-transport-key` (glyph)
- `desk/surface/gadgets.css:896` 10px `.gadget-secret-label small`
- `desk/surface/gadgets.css:955` 10px `.desk-next .gadget-pad .desk-mic` (glyph)
- `desk/surface/gadgets.css:995` 0.6875rem `.gadget-fold > summary::before` (glyph)
- `desk/surface/gadgets.css:1015` 10px `.gadget-fold-token`
- `desk/surface/gadgets.css:1056` 10px `.gadget-checkline-word`
- `desk/surface/surface-footer.css:63` 10px `.desk-next .surface-footer-readiness` (already in the Phase 3 open ledger)
- `desk/surface/surface-footer.css:123` 10px `.desk-next .copy-receipt`
- `desk/surface/surface-footer.css:140` 9px `.desk-next .copy-receipt-dismiss`
- `desk/surface/surface-footer.css:159` 11px `.desk-next .undo-receipt`
- `desk/surface/surface-footer.css:182` 9px `.desk-next .undo-receipt-btn`
- `desk/surface/surface-footer.css:208` 10px `.desk-next .undo-receipt-time`
- `desk/surface/surface-footer.css:234` 10px `.desk-next .ledger-filter-label`
- `desk/surface/surface-footer.css:263` 10px `.desk-next .ledger-filter-query`
- `desk/surface/surface-footer.css:280` 11px `.desk-next .ledger-filter-well .desk-mic` (glyph)
- `desk/surface/surface-footer.css:289` 10px `.desk-next .ledger-filter-count`
- `desk/surface/surface-footer.css:302` 9px `.desk-next .ledger-filter-clear`
- `desk/surface/surface-footer.css:328` 10px `.desk-next .ledger-filter-token`
- `desk/surface/surface.css:365` 10px `.surface-well-head`
- `desk/surface/surface.css:553` 11px `.surface-traffic-empty`
- `desk/surface/surface.css:563` 11px `.surface-token`
- `desk/surface/surface.css:590` 10px `.surface-token[data-chip]`
- `desk/surface/surface.css:799` 11px `.desk-surface-body .transcript-list .transcript-speaker`
- `desk/surface/surface.css:873` 10px `.surface-group-label`
- `desk/surface/surface.css:980` 10px `.surface-panel-title`
- `desk/surface/surface.css:1023` 10px `.surface-eyebrow`
- `desk/surface/surface.css:1076` 10px `.surface-stream-day-label`
- `desk/surface/surface.css:1142` 11px `.surface-stream-entry[data-dense] .surface-stream-meta`
- `desk/surface/surface.css:1309` 11px `.surface-ledger-cell`
- `desk/surface/surface.css:1388` 10px `.surface-ledger-band`
- `desk/surface/surface.css:1399` 11px `.surface-ledger-empty`
- `desk/surface/surface.css:1416` 10px `.surface-ledger-origin`
- `desk/surface/surface.css:1613` 10px `.surface-tile-stamp`
- `desk/surface/surface.css:1796` 0.625rem `.surface-bay-tag`
- `desk/surface/surface.css:1923` 11px `.surface-detail-facts`
- `desk/surface/surface.css:2256` 10px `.prefs-hit-module`
- `desk/surface/surface.css:2331` 10px `.prefs-tile-label`
- `desk/surface/surface.css:2476` 11px `.prefs-wallpaper-copy strong`
- `desk/surface/surface.css:2480` 11px `.prefs-wallpaper-copy > span`
- `desk/surface/surface.css:2487` 9px `.prefs-wallpaper-state`
- `desk/surface/surface.css:2496` 9px `.prefs-wallpaper-fact`
- `desk/surface/surface.css:2529` 10px `.prefs-receipt`
- `desk/surface/surface.css:2553` 10px `.prefs-defaults`
- `desk/surface/surface.css:2613` 11px `.meeting-conflict-slip-facts`
- `desk/surface/surface.css:2794` 10px `.desk-next .surface-edit-mic .desk-mic` (glyph)
- `desk/surface/surface.css:3329` 10px `.assignment-candidate-added`
- `desk/surface/surface.css:3495` 11px `.prefs-token-caption`
- `desk/surface/surface.css:3588` 10px `.surface-verb-count`
- `desk/surface/surface.css:3831` 10px `.meetings-stream-fact`
- `desk/surface/surface.css:3841` 10px `.meetings-stream-dot` (glyph)
- `desk/surface/surface.css:3847` 10px `.meetings-stream-no-transcript`
- `desk/surface/surface.css:3898` 10px `.meetings-stream[data-narrowed] .meetings-stream-compact-facts`
- `desk/surface/surface.css:3945` 11px `.meetings-detail-needs-head .surface-caption`
- `desk/surface/surface.css:4037` 10px `.meetings-review-dot` (glyph)
- `desk/surface/surface.css:4042` 10px `.meetings-review-project .btn`
- `desk/surface/surface.css:4048` 11px `.meetings-review .surface-caption`
- `styles/global.css:502` 10px `.egress-badge` (the chrome badge; a separate class from `.gadget-chip`)

## Ratification asks (for the owner)

1. **Placement:** is `Generate` in the BRIEF head (after `THIS DEVICE`) right, present in every state and disabled only while a read or generation is open (boards 1, 2a, 2b, 3c, 6, 7)? One label, `Generate`, in place of `Generate again`.
2. **Order and cap:** do we keep three rows with decisions first, newest first by when each decision was recorded, and the rest behind `N more` (boards 4, 5)?
3. **Scope:** do we fix the Arrival only, and leave the brief window's Generate (`BriefView.tsx:297`) for later?
4. **One verb on a generate failure** (board 3a): Retry removed; the enabled `Generate` is the recovery. Paid this round on Astra's check; shown for your word.
