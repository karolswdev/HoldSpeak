# PHILO-4-01 canvas: Generate is always reachable (with the PHILO-4-02 row order)

**Status: UNRATIFIED.** The owner has not seen these boards yet. Build nothing until he ratifies them (UX-CANON A.2).

`morning-brief.html` is one self-contained page, with the shots inlined and no fetch. `morning-brief.png` shows the page at 1440 and `morning-brief-393.png` shows it at 393. Each board has its own PNG in `shots/` at `<board>-1440.png` and `<board>-393.png`, taken at device scale 2 from the `[data-testid=arrival-brief]` element. `shots/labels.json` lists the exact strings for each board. `shots/facts.json` holds the facts measured in the rendered DOM for each shot: Button painted height, the 44 px band owned through `elementFromPoint`, the receipt-line font size, row geometry, the raw `<button>` count and horizontal scroll.

## Method

The method is the same as the PHILO-3-03 canvas, with one difference: no rig hub. `harness/main.tsx` renders the **real** library species with the real CSS: `SurfaceSection`, `SurfaceLedger`, `SurfaceLedgerRow`, `countToken`, the library `Button` (`components/signal/Signal`), `BriefEgress` and `Chair`, plus `styles/global.css` and `desk/desk.css`. They sit in the BRIEF section's own markup (`web/src/desk/chair/ChairHome.tsx:1196-1330` and `BriefSection` at `:1978-2040`). A Vite dev server served that markup, and Playwright shot it at 1440×900 and 393×852 (`harness/shoot.py`). `harness/vite.config.mjs` holds absolute paths from the author's machine; change them to run it again. The live shot `../../../phase-3-the-meeting-loop/assets/story-03-shots/20260923T190113Z-case.j10.route_generate_again.same_day_same_id-muaddib-1440/after.png` confirms the head geometry: the badge in the middle and the verb at the right, the same as the `Generate again` branch today.

No new species, colour, font or CSS rule. No raw `<button>` (`raw_buttons: 0` on all 16 shots). No horizontal scroll at either width. Every receipt line is 12 px. At 393, every plated Button owns its 44 px band (`owns_44_band: true` on all 16 shots at 393; its painted height stays 24 px).

## The one placement

Generate goes in the BRIEF section's **head verb slot**, after the egress badge. This is where `Generate` (no brief) and `Generate again` (nothing untriaged) sit today (`ChairHome.tsx:1231-1245,1293-1306`). `BriefSection` gets the `actions` that its `SurfaceSection` already accepts. The rows, Ack/Defer and `N more` do not change.

The rule for every branch: the head has the badge and Generate. Generate is **disabled while a read or a generation is open**, and enabled in all other states.

## The boards

| # | Board | 1440 | 393 | What it shows |
|---|---|---|---|---|
| 0 | Today (reference) | `shots/0-today-1440.png` | `shots/0-today-393.png` | The face on main: no Generate while a row is untriaged; decisions come LAST, so the decision is behind `1 more` |
| 1 | Generate is reachable | `shots/1-generate-reachable-1440.png` | `shots/1-generate-reachable-393.png` | Day-one brief, 4 untriaged rows, Ack/Defer as today; badge + `Generate` in the head; the decision row leads |
| 2a | Generating | `shots/2a-generating-1440.png` | `shots/2a-generating-393.png` | `Generate` disabled; `GENERATING…` in the receipt slot; rows and caption stay |
| 2b | Reading | `shots/2b-reading-1440.png` | `shots/2b-reading-393.png` | The read is open: `READING…` (PHILO-3-03 state 2) with `Generate` disabled |
| 3a | Did not generate | `shots/3a-did-not-generate-1440.png` | `shots/3a-did-not-generate-393.png` | `BRIEF DID NOT GENERATE · HTTP 500` + Retry (POST again); the day-one rows, triage and caption do not change |
| 3b | Did not load | `shots/3b-did-not-load-1440.png` | `shots/3b-did-not-load-393.png` | PHILO-3-03 state 3 (`BRIEF DID NOT LOAD · HTTP 500` + Retry reads again), plus the head verbs |
| 4 | Next day, one Generate | `shots/4-next-day-one-decision-1440.png` | `shots/4-next-day-one-decision-393.png` | The new decision is row 1 at both widths; caption `SEP 21 – 24 · GENERATED SEP 24 08:02`; the badge does not change; `3 more` |
| 5 | Next day, several decisions | `shots/5-next-day-several-decisions-1440.png` | `shots/5-next-day-several-decisions-393.png` | Decisions newest first by the record's `created_at` (SEP 24 07:58, SEP 23 16:10, SEP 22 11:30 visible; SEP 21 09:05 in the fold); `4 more` = 7 − 3 |

Triage across the Generate (boards 1 to 4): the new brief has new item ids, so its rows start untriaged. The day-one rows keep their triage state on the day-one brief's shelf: nothing is acknowledged or deferred by the Generate. The Arrival shows only the latest brief, so that shelf is not on this face. The build proves it by reading the old brief back (story 01 acceptance 4).

The fold count is honest: `N more` = rows − 3. It shows only when N > 0 (`ChairHome.tsx:2027`), so it is never `0 more`.

## Exact strings (ASD-STE100)

| String | Where | New or kept |
|---|---|---|
| `Generate` | head verb, every branch that has a brief | kept word (the no-brief verb); replaces `Generate again` in the head (see asks) |
| `THIS DEVICE` | egress badge | kept |
| `BRIEF · <n> THINGS WAITING` / `BRIEF · 1 THING WAITING` | head label | kept |
| `BRIEF` | head label when there are no rows | kept |
| `Ack` · `Defer` · `<n> more` | row verbs, fold | kept |
| `GENERATING…` | receipt slot while the generation is open | new (READING… idiom); replaces the Button label `Generating...` |
| `READING…` | read open | kept (PHILO-3-03) |
| `BRIEF DID NOT GENERATE · HTTP <n>` / `BRIEF DID NOT GENERATE · NO ANSWER` | generation failed, `data-tone="danger"` | new (PHILO-3-03 idiom) |
| `BRIEF DID NOT LOAD · HTTP <n>` / `… · NO ANSWER` | read failed | kept (PHILO-3-03) |
| `Retry` | after a failure line | kept |
| `<period_label> · <generated_label>` e.g. `SEP 21 – 24 · GENERATED SEP 24 08:02` | caption | kept (A3 law) |
| `Brief ready · <n> items · <time>` | receipt after the click | kept (`briefReceipt`) |

## Seams to bind (build after ratification)

- `ChairHome.tsx:1261-1266`: pass `actions={<><BriefEgress /><Button … disabled={generating || briefLoading}>Generate</Button></>}` into `BriefSection`, which gives it to its `SurfaceSection` (`:1993`).
- `:1198-1205` (read open) and `:1208-1224` (read failed): the same head verbs; disabled while the read is open.
- `:1304`: the label `Generate again` becomes `Generate`, and `Generating...` becomes the `GENERATING…` receipt line.
- Generate failure: today it goes to `reportWriteFailure`. The branch gets `BRIEF DID NOT GENERATE · <cause>` (use `briefLoadCause`) + Retry.
- Story 02 (Astra's lane): `:801` puts `decisions` first; decision items carry the decision record's `created_at` and sort newest first; the other sections keep their order.

## Ratification asks (for the owner)

1. **Placement:** is `Generate` in the BRIEF head (after `THIS DEVICE`) right, present in every state and disabled only while a read or generation is open (boards 1, 2a, 2b)? One label, `Generate`, in place of `Generate again`, because `Generate again` wraps to two lines at 393 beside `4 THINGS WAITING`.
2. **Order and cap:** do we keep three rows with decisions first, newest first by when each decision was recorded, and the rest behind `N more` (boards 4, 5)?
3. **Scope:** do we fix the Arrival only, and leave the brief window's Generate (`BriefView.tsx:297`) for later?
