# PHILO-10-04 canvas A: the SEND well on a published update

**Status: DRAFT, for the owner's ratification** (UX-CANON §A.2: the canvas before the build). Nothing here is built in product code. The review page is `index.html` in this folder: every board at 1440 × 900 and 393 × 852. Canvas B, the Destinations group, is `../story-04-destinations-canvas/`. The two canvases share one harness (`harness/`).

Sources: story 04 (`../../story-04-the-send-face-and-the-destinations.md`), the charter's state/width matrix (`../../current-phase-status.md`, "The state/width matrix"), the design (`../../design/send-lifecycle.md`, rounds one to five, merged in #691 at `98ea2cfa`), and the ratified Phase 9 update canvas it extends (the Copy and Mark delivered row; Q2 `DELIVERED ×N`; Q3 To and Mark delivered above the body).

## Three questions for the owner

1. **The pick:** picking a destination opens its preview and Send in place, under that row (no popover, no modal)? **Recommended: yes.** The preview sits next to the verb that sends it, and one row is open at a time.
2. **The record words:** `DELIVERY N` (history head) and `DELIVERY ×N` (list chip), replacing the ratified `DELIVERED ×N` (Phase 9 Q2)? **Recommended: yes.** An email that SendGrid accepted is not delivered, and the history now holds such rows. Each row keeps its own word (`SAVED`, `POSTED`, `COMMENTED`, `BLOG POSTED`, `ACCEPTED BY SENDGRID`, and `DELIVERED` for the manual row).
3. **Prepared sends:** prepared sends sit first in SEND, open, with a `PREPARED ×K` chip on the update list? **Recommended: yes.** A send that the steward or an agent prepared waits for your press, so it comes first.

## What the boards are, exactly

- **The app:** the PRODUCT app (`web/`), served by vite with `harness/vite.config.mjs`. The config swaps two modules for the harness copies: `./update/UpdatePosture` → `harness/ProposedUpdatePosture.tsx` (the real module with the SEND well and the one DELIVERY history added) and `./connections` → `harness/ProposedConnections.tsx` (canvas B). Everything else is the product. A second vite serves the product unchanged for board 0 ("today").
- **StrictMode:** the harness mounts the app without `<StrictMode>`, as the production build does. Under StrictMode in `vite dev`, `useResource` never loads (`web/src/pages/pageSupport.tsx:35-39`; BACKLOG row). The built bundle is not affected.
- **The hub:** a REAL hub (`scripts/graph_walk.py serve`) with `HOME=tempfile.mkdtemp()`, removed when the run ends. The project, two items, two published updates and the Jira account are made through the real routes (`shots/facts.json`, `_seed`).
- **The wire (unbuilt, stories 01–03):** `harness/shim.ts` stands in for it, and its header says how. It keeps the destination and send records (design section 1). It freezes the transport bytes per channel and returns the readable preview PARSED BACK FROM THOSE BYTES (section 3; the email is the SendGrid request JSON, text only). It implements one command id = one send (section 2), the refusals before the boundary, the boundary itself, and the settle (section 4). At load, a row still `dispatching` settles `unknown` with reason `interrupted` and is never dispatched again (section 4a). Every face state is derived from stored rows; no board poses a state.
- **Fixture faults** (each named on its board): no answer (board 9), SendGrid's pinned 403 `sender_not_verified` (board 13), a changed gh login (15), a lost answer (16), a restart after the boundary (20), a moved folder and a parked destination (23).
- **Words:** `harness/p10.ts` (`SEND_WORDS`, `SENT_WORD`, the refusal, failure and unknown tables).

## The state/width matrix, board by board

| Matrix state | Boards |
|---|---|
| No destination saved | 1 |
| Destinations listed | 2 |
| Destination picked | 3, 5, 8, 10, 12 |
| Sending | 6 |
| SENT | 4, 7, 14 (email: `ACCEPTED BY SENDGRID` + `ID <message id>`), 19 |
| REFUSED | 11 (not signed in), 15 (GitHub account changed) |
| FAILED | 13 (`sender_not_verified`: a FAILED outcome, the pinned whole-request 403, design section 8) |
| UNKNOWN | 9 (`Check PAY-121`); 16–18 (the lost answer, bound to update A; update B clean) |
| UNKNOWN after a restart | 20 (`INTERRUPTED`; no second dispatch) |
| DESTINATION CHANGED | 23 (`destination_changed`, `destination_parked`; only Discard stays), 24, 25 |
| PREPARED | 21, 22 |
| Manual | 26 (`Mark delivered` kept as the manual channel: `DELIVERED · MANUAL`) |
| Several sends | 26, 27 |
| (not a matrix row) | 0 today; 28 a draft has no SEND well |

## Facts the boards prove (`shots/facts.json`)

- A double-click on Send makes one dispatch (`7-posted-github-*`: `dispatches_after_double_click` = 1).
- Retry after a lost answer reuses the key and does not dispatch again (`19-retried-one-dispatch-*`: `dispatches_with_lost_key` = 1).
- The lost answer stays on update A (`17-update-b-clean-*`: `b_state` = no lost line, no Retry, no open row, no history).
- A restart after the boundary gives `unknown` / `interrupted` (`20-unknown-after-restart-*`: `rows`).
- No preview shows raw JSON or XHTML, and no email row says DELIVERED (`preview_has_raw`, `words_delivered_on_email`: false on every render).

## Measurements

58 renders (29 boards × 1440 × 900 and 393 × 852), `shots/facts.json`; the scans cover the whole Room window and any portal:

- Text under 12 px: **0** in the proposal, **0** inherited.
- Raw `<button>` without the library `.btn`: **0** in the proposal, **0** inherited.
- Horizontal overflow (page or window body): **0**.
- Contrast, every text-bearing element inside the proposal against its composited background: lowest **4.5:1** (board 27, the list chips); none under 4.5:1. The probe records the lowest ratio per board, not the element.
- Pointer (UX-CANON C): **828** proposal controls (every Button, every destination and prepared row line, every field), **7452** points (nine per control; the painted face at 1440, the 44 × 44 target at 393), each by `elementFromPoint` AND a real pointer move: **all owned**. Of the untouched window chrome, **116** controls miss points: the ROOM tab's right edge at both widths, and the Close and Minimize traffic lights at 393. Board 0 (the unchanged product) shows the same (BACKLOG row).
- Modals **0**; raw JSON or XHTML in a preview **0**; DELIVERED on an email row **0**; browser errors **0**.

## Limits (what the boards are not)

- The wire is the shim's statement of the design, not a server response. The dispatch sends nothing anywhere. Proofs (paths, comment links, SendGrid message ids) are fixture values.
- The GitHub account (`kwork`, CONNECTED) and one Confluence account (SIGN IN) are overlaid on the Connections read; an isolated HOME has no gh login and no Confluence add route exists. The Jira account is real (`POST /api/providers/jira/connections`, NEVER CHECKED).
- `Check <target>` opens the far side's URL. On the canvas it points at the fixture site.
- At 393 the history rows wrap the ✓ lead token onto its own line above the name. That is the inherited `SurfaceLedgerRow` wrap, not canvas code.

## Proposed library repairs (the build moves each into the named file)

`harness/canvas.css`, "PROPOSED LIBRARY REPAIRS", names each rule's product file and line:

- The 12 px floor: the SYNCED token (`gadgets.css:173`), and in the Settings window the provenance host (`patterns/provenance.css:30`), the TransportKey word (`gadgets.tsx:734`) and the PARKED fold count (`gadgets.css:1028`).
- The 44 px narrow target for gadget controls under a 420 px container: the string well and its input (`gadgets.css:324`), the docked mic (`gadgets.css:365`), the check token (`gadgets.css:173`) and the cycle select (`gadgets.css:226`). The 393 pointer pass failed each one on the Destinations form before this repair.

## Reproduce

```bash
# from the worktree root; each run removes its own HOME
ONLY_WIDTH=1440 PLAYWRIGHT_BROWSERS_PATH=$HOME/Library/Caches/ms-playwright \
  .venv/bin/python pm/roadmap/holdspeak-philo/phase-10-the-channels/assets/story-04-send-canvas/harness/shoot.py
ONLY_WIDTH=393 PLAYWRIGHT_BROWSERS_PATH=$HOME/Library/Caches/ms-playwright \
  .venv/bin/python pm/roadmap/holdspeak-philo/phase-10-the-channels/assets/story-04-send-canvas/harness/shoot.py
python3 pm/roadmap/holdspeak-philo/phase-10-the-channels/assets/story-04-send-canvas/harness/build_review.py
```
