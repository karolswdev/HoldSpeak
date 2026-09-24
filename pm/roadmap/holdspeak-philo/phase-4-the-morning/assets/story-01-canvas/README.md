# PHILO-4-01 canvas: Generate is always reachable (with the PHILO-4-02 row order)

**Status: UNRATIFIED, round three.** Astra checked round one and bounced it (six findings); round two paid them. Astra checked round two: RATIFY-WITH-CONDITIONS (four conditions). Round three pays them. The owner has not seen these boards. Build nothing until he ratifies them (UX-CANON A.2).

**Canvas:** https://claude.ai/artifact/LHjuHKL1pVZuh4aK5J9qRU

`morning-brief.html` is one self-contained page (rebuilt in round three with all 16 boards and the two library probes), with the shots inlined and no fetch. `morning-brief.png` shows the page at 1440 and `morning-brief-393.png` shows it at 393. Each board has its own PNG in `shots/` at `<board>-1440.png` and `<board>-393.png`, taken at device scale 2 from the `[data-testid=arrival-brief]` element. `shots/labels.json` lists the exact strings for each board. `shots/facts.json` holds the facts measured in the rendered DOM for each shot.

## Round three: what changed

1. **Board 7 split** (condition 1). The producer writes `Nothing material changed.` only when the brief has zero items (`holdspeak/services/monday_brief_service.py:340-341`). Triage writes the shelf (`shelve`, `:1110-1139`, into `monday_brief_item_shelf`); it does not rewrite the stored headline. So "empty" and "fully triaged" are two faces:
   - **7a, empty brief.** Zero items. Today the headline is the producer's sentence. UX-CANON A.3 applies to it (it is product copy, not the owner's data). **Proposed: `No changes`.** The build changes the producer string and its wording fences in the same commit, or the owner keeps the sentence. The fences that name the sentence today: `holdspeak/services/monday_brief_service.py`, `web/src/desk/chair/ChairHome.tsx`, `web/src/desk/pullouts/views/BriefView.tsx`, `web/src/desk/chair/__tests__/briefReceiptRendered202.test.tsx`, `web/src/desk/chair/__tests__/briefLoadAndDate.philo303.test.tsx`, `tests/unit/test_monday_brief_service.py`, `tests/unit/test_walk_monday_brief_126.py`, `tests/unit/test_hs171_aggregate_notify.py`, `tests/unit/test_philo_graph_atlas.py`, `tests/integration/test_phase200_attention_coverage.py`, `tests/fixtures/graph_walk_calibration.html`.
   - **7b, fully triaged.** The day-one brief (4 items), every row Ack'd or Defer'd. `untriagedBrief` is empty (`ChairHome.tsx:806-808`), so the quiet branch renders (`:1286-1328`): the rows leave the Arrival, the head label is `BRIEF` with no count, the **stored headline** shows (`1 commitment due, 1 thing changed, 1 thing waiting, 1 decision waiting.`, composed at `monday_brief_service.py:346-387`), then the caption. Today the verb is `Generate again`; proposed `Generate`. **Observation, not a proposal:** that headline still counts the four items the owner has triaged. It is a sentence, and its counts are stale after triage. The owner decides whether it stays.
2. **The missing compositions** (condition 2): `6b` (no brief yet, the generation failed: the failure line takes the place of `No brief yet`, Generate enabled, no Retry), `8a` (the quiet branch while generating: `GENERATING…` under the caption, Generate disabled), `8b` (the quiet branch after a failed generation: the danger line under the caption, Generate enabled, no Retry) and `9` (a successful Generate that made an empty brief: the quiet branch holds the receipt, `ChairHome.tsx:1315`). 8a and 8b are drawn on 7b; on 7a only the headline line differs, so they have no second shot.
3. **The `0 items` ruling** (condition 2, board 9). `0 items` is a counter of zero (UX-CANON: no counters of zero). The product already drops it: `briefReceipt` pushes the count only when it is above 0 (`web/src/desk/chair/briefEgress.tsx:51-56`). Board 9 shows `Brief ready · 8:02 AM`. There is no change to make.
4. **Library containment** (condition 3), in the species:
   - `web/src/desk/surface/surface.css:72-74` `.surface-section-head h3`: `min-width: 0` and `overflow-wrap: anywhere` (new). A long single word breaks inside the label; it does not push the head wider than its section.
   - `web/src/desk/surface/surface.css:59-67`: the head no-shrink rule adds `.surface-section-head > .quiet`. With the label able to shrink, flex squeezed the `123 members` fact onto two lines; now the fact keeps its width.
   - `web/src/desk/surface/gadgets.css:830-851` `.gadget-chip`: `display: inline-flex; align-items: center` → `display: inline-block; vertical-align: middle`, plus `max-width: 32ch; overflow: hidden; text-overflow: ellipsis`, and `font: 600 12px / 1` → `600 12px / 16px` (16 px line + the 1 px border keeps the 18 px chip). An ellipsis paints only in a block container, so the chip is inline-block now (the same shape `.surface-record-id > .gadget-chip` already uses, `surface.css:487-493`). A `max-width` in percent does not help here: the Jira action row is content-sized (`connections.css:72-78`, `flex-shrink: 0`), so a percentage is cyclic and ignored for its width. `32ch` is a length.
   - **Proof (rendered, Playwright, 393):** two probes render the REAL `DirectoryPullout` and the REAL `ConnectionsPane` (a stubbed `fetch`): `shots/lib-directory-393.png`, `shots/lib-jira-chip-393.png`, facts in `shots/facts.json` (`lib-directory-393`, `lib-jira-chip-393`). `shoot.py` fails the run on horizontal overflow, a probe outside the viewport, or a Button whose text leaves its box. **Before the fix both probes FAILED** (Directory head 413 px in a 365 px section, right edge 413 > 393; Jira row 435 px in a 365 px group, the chip 344 px wide). **After:** Directory head 365 px, label 268 px on 2 lines, no overflowing element; Jira row 365 px, chip 230 px with `text-overflow: ellipsis` (scroll 342 > client 228), `Recheck` 68 px with its 50 px word inside its box.
   - **The Directory probe uses a longer name** than Astra's (`ArchitectureDecisionReviewWorkspace2026PlatformGuild`). Inside a pullout, the head label is **10 px**, not 12 px: `web/src/desk/components/window-chrome.css:207-216` (`.desk-next .desk-pullout-body h3`) overrides the species. At 10 px Astra's 39-character name fits at 393 today (257 px), so the probe needs a longer word to fail without containment. The 10 px pullout label is in the ledger below.
   - **The 20 shots of the ten unchanged boards are byte-identical to round two** (git sees no change in them): the chip and label changes move no pixel on the BRIEF section.
5. **Healed floor allowances removed** (condition 4): `tests/e2e/test_hs202_05_first_use_type_floor.py` `FLOOR_LEDGER`: 24 entries deleted (every `h3@10px` and every `.gadget-chip.gadget-chip-egress@10px`, at 393 and 1440). A regression to 10 px is now `M7 NEW` and fails (`:710-715` after the deletion: `if sig not in FLOOR_LEDGER` → `M7 NEW`). The other residue stays. I did not run that e2e test (it boots the product).

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

- **The 12 px floor.** `shoot.py` walks EVERY painted text node inside `[data-testid=arrival-brief]` and reads its computed `font-size` (`facts.json` `texts`, `min_text_px`, `floor_ok`). It fails the run if any shot is under 12 px. Result: `min_text_px: 12` on all 32 brief shots (round three). It reads text nodes only; it does not read `::before`/`::after` content.
- **The hit probe.** For each Button, `elementFromPoint` at the center and at four points 1 px inside the left and right edges, 21 px above and below the center (`owns_44_band`). It does not probe edge midpoints, and it is not a real pointer. Result: `true` for every Button at 393; `false` at 1440, where the halo is not applied (the same as round one).
- **The head.** `head.label_lines`, `head.chip_h`, and for each Button `w`, `content_w`, `text_w` and `text_fits` (the text range inside the Button box).
- **Scope of the render.** The harness renders only the BRIEF section inside `Chair`, not the full Arrival. So the viewport numbers (`rows[].in_viewport`) do not prove clearance from the real Arrival footer or the sections above. That clearance is for the build to prove on the real face.
- **Order.** The `created_at` values of boards 4 and 5 live only in code comments in `harness/main.tsx` and in `labels.json`. The harness shows the proposed order; it does not prove that the producer or a reload keeps that order. Story 02 proves it.
- Also on every shot: `raw_buttons: 0`, no horizontal scroll (`scrollW` = `vw`), no console errors.
- **The library probes** (round three) measure `scrollWidth` against `clientWidth` on every element inside the probe (a truncated chip with `text-overflow: ellipsis` is not counted as overflow), the probe's box against the viewport, and each Button's text range against its box. jsdom cannot measure layout, so this is a Playwright check, not a vitest test. The probe widths come from the real pullout body at a 393 viewport (14 px padding, a 365 px section); a pullout window narrower than the viewport is not probed.

## The one placement

Generate goes in the BRIEF section's **head verb slot**, after the egress badge (`THIS DEVICE` before `Generate`). This is where `Generate` (no brief) and `Generate again` (nothing untriaged) sit today (`ChairHome.tsx:1231-1245,1293-1306`). It is the smallest lawful placement: the slot exists, and `SurfaceSection` already accepts `actions`. `BriefSection` passes them. The rows, Ack/Defer and `N more` do not change.

The rule for every branch: the head has the badge and Generate. Generate is **disabled while a read or a generation is open**, and enabled in all other states. The status slot under the section holds one line: the open request (`READING…`, `GENERATING…`) or the last failure.

## The boards (16 boards × 2 widths = 32 shots, plus 2 library probes at 393)

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
| 6 | No brief yet | `shots/6-null-brief-1440.png` | `shots/6-null-brief-393.png` | No brief on the hub: `No brief yet` (A3) and `Generate` in the head. Busy: the 3c composition (`GENERATING…` in place of `No brief yet`). Failure: board 6b. Result: the populated branch with the receipt (board 4), or board 9 when the brief is empty |
| 6b | No brief yet, did not generate | `shots/6b-null-brief-did-not-generate-1440.png` | `shots/6b-null-brief-did-not-generate-393.png` | `BRIEF DID NOT GENERATE · HTTP 500` in place of `No brief yet`; `Generate` enabled; no Retry |
| 7a | Empty brief (zero items) | `shots/7a-empty-brief-1440.png` | `shots/7a-empty-brief-393.png` | **Proposed** headline `No changes` (today `Nothing material changed.`), the caption, `Generate` |
| 7b | Fully triaged | `shots/7b-fully-triaged-1440.png` | `shots/7b-fully-triaged-393.png` | Day-one brief, all rows Ack'd/Defer'd: no rows, head `BRIEF`, the stored headline (it still counts the four items), the caption, `Generate` (today `Generate again`) |
| 8a | Quiet branch, generating | `shots/8a-quiet-generating-1440.png` | `shots/8a-quiet-generating-393.png` | 7b while the generation is open: `GENERATING…` under the caption, `Generate` disabled |
| 8b | Quiet branch, did not generate | `shots/8b-quiet-did-not-generate-1440.png` | `shots/8b-quiet-did-not-generate-393.png` | 7b after a failed generation: `BRIEF DID NOT GENERATE · HTTP 500` under the caption, `Generate` enabled, no Retry |
| 9 | Empty brief, receipt | `shots/9-empty-success-receipt-1440.png` | `shots/9-empty-success-receipt-393.png` | A successful Generate that made zero items: `No changes`, the caption, `Brief ready · 8:02 AM` (no `0 items`) |
| lib | Directory head | — | `shots/lib-directory-393.png` | The real `DirectoryPullout`: a long one-word name wraps inside the label; `123 members` on one line |
| lib | Jira chip | — | `shots/lib-jira-chip-393.png` | The real `ConnectionsPane` Jira row: the host chip ends in `…` at 32ch; `Recheck` keeps its width |

Every state of every branch now has its own shot, except where two states are identical (8a and 8b on 7a differ from 7b only in the headline).

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
| `No changes` | the headline of a brief with zero items (boards 7a, 9) | **proposed**; replaces the producer's `Nothing material changed.` (`monday_brief_service.py:341`), with its fences, or the owner keeps the sentence |
| `<n> <thing> …, <n> <thing> ….` | the stored headline of a populated brief, shown when every row is triaged (7b, 8a, 8b) | kept (the producer's words); observation: its counts are stale after triage |
| `Ack` · `Defer` · `<n> more` | row verbs, fold | kept |
| `GENERATING…` | status slot while the generation is open | new (READING… idiom); replaces the Button label `Generating...` |
| `READING…` | read open | kept (PHILO-3-03) |
| `BRIEF DID NOT GENERATE · HTTP <n>` / `BRIEF DID NOT GENERATE · NO ANSWER` | generation failed, `data-tone="danger"`, no Retry | new (PHILO-3-03 idiom) |
| `BRIEF DID NOT LOAD · HTTP <n>` / `… · NO ANSWER` | read failed | kept (PHILO-3-03) |
| `Retry` | after a READ failure only | kept |
| `<period_label> · <generated_label>` e.g. `SEP 21 – 24 · GENERATED SEP 24 08:02` | caption | kept (A3 law) |
| `Brief ready · <n> items · <time>` / `Brief ready · <time>` | receipt after the click; the count is dropped at 0 (`briefEgress.tsx:51-56`) | kept (`briefReceipt`) |

**Wording fence.** `web/src/desk/chair/__tests__/briefReceiptRendered202.test.tsx:79` expects `Generate again`. The build changes that assertion to `Generate` in the same commit that changes the label.

## Seams to bind (build after ratification)

- `ChairHome.tsx:1261-1266`: pass `actions={<><BriefEgress /><Button … disabled={generating || briefLoading}>Generate</Button></>}` into `BriefSection`, which gives it to its `SurfaceSection` (`:1993`).
- `:1198-1205` (read open) and `:1208-1224` (read failed): the same head verbs; disabled while the read is open. While a generation is open after a read failure, `GENERATING…` replaces the failure line and its Retry.
- `:1242` and `:1304`: the label is `Generate` in every branch; `Generating...` becomes the `GENERATING…` status line; the fence at `briefReceiptRendered202.test.tsx:79` moves with it.
- Generate failure: today it goes to `reportWriteFailure`. The branch gets `BRIEF DID NOT GENERATE · <cause>` (use `briefLoadCause`) with no Retry.
- Story 02 (Astra's lane): `:801` puts `decisions` first; decision items carry the decision record's `created_at` and sort newest first; the other sections keep their order.

## Readable text still under 12 px (ledger, not fixed here)

- `desk/components/window-chrome.css:210` 10px `.desk-next .desk-pullout-body h3` (round three: overrides the 12 px section-head label inside every pullout; found by the Directory probe)

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
4. **One verb on a generate failure** (boards 3a, 6b, 8b): Retry removed; the enabled `Generate` is the recovery. Paid on Astra's round-one check; shown for your word.
5. **`No changes`** (boards 7a, 9): do we replace the producer's `Nothing material changed.` with `No changes` (the build changes the producer string and its fences together), or keep the sentence?
6. **The fully-triaged headline** (board 7b): the stored headline still counts rows you triaged. Keep it, or ask for a later story?
