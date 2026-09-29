# PHILO-10-04 canvas A: the SEND well on a published update

**Status: DRAFT, round two, for the owner's ratification** (UX-CANON §A.2: the canvas before the build). Round two pays Codex Astra r1 DO-NOT-RATIFY on #693 (`../../checks/canvases-astra-r1.md`, committed verbatim). Nothing here is built in product code. The review page is `index.html` in this folder: every board at 1440 × 900 and 393 × 852. Canvas B, the Destinations group, is `../story-04-destinations-canvas/`. The two canvases share one harness (`harness/`).

Sources: story 04 (`../../story-04-the-send-face-and-the-destinations.md`), the charter's state/width matrix (`../../current-phase-status.md`), the design (`../../design/send-lifecycle.md`, rounds one to five), story 01 as built and merged (#692: the records, the one history table with `channel` and `outcome`, the UNKNOWN row on today's face), and the ratified Phase 9 update canvas it extends.

## Three questions for the owner

1. **The pick:** picking a destination opens its preview and Send in place, under that row (no popover, no modal)? **Recommended: yes.** (Codex Astra r1: yes; placement is the fork.)
2. **The record word:** story 01's face today (boards 0a, 0b) reads `DELIVERED ×N` and already keeps UNKNOWN apart (`RESULT UNKNOWN ×M`). Change the word to `DELIVERY ×N` (list chip) and `DELIVERY N` (history head), with the same counts? **Recommended: yes.** The record now mixes channels, and a provider's acceptance (`ACCEPTED BY SENDGRID`) is not a delivery. The counts do not change: only rows that `isDelivered` counts are counted.
3. **Prepared sends:** first in SEND, with a `PREPARED ×K` chip on the update list; ONE preview open (the first), each other one a click away with its Send and Discard; a prepared send that ended stays in place as its result? **Recommended: yes.** (Codex Astra r1: first and chip yes; not all previews forced open.)

## Round two: what changed, finding by finding

| Codex Astra r1 | The canvas now |
|---|---|
| F1 a failed prepared send and a Discard leave no result | A prepared send that ended stays in the PREPARED group as a closed result row, from its stored record: ✓ POSTED + link, FAILED + reason + NOTHING SENT, RESULT UNKNOWN, DISCARDED (boards 27–29, 33). A destination row carries its last send's result: ✓ SAVED + time, LAST SEND UNKNOWN, LAST SEND FAILED (board 17). A refused prepared row shows its refusal as a chip on the closed row (boards 30, 31). |
| F2 the first setup loop | The Room's `Add destination` asks Settings to arrive at the group: the group scrolls itself into view and opens the add form (canvas B board 1: no harness scroll). After Save and closing Settings, the Room shows the new destination at once (board 2: no reload); the well reads its destinations again on the Settings change signal and on window focus. |
| F3 boards that did not show their state | Every board names the elements that make its state, and the run asserts each one is on screen: in the viewport, inside every clipping ancestor, and on top at its centre and two inner corners (`shoot.py` `VISIBLE`). The run also fails if two shots of one width share bytes; it caught one pair at 1440 (back on update A = board 21), now a fact on board 24. The preview puts Send between its fields and its body, so the verb and its result are in view at 393. |
| F4 the history bypassed story 01 | The history is story 01's one table: `update.deliveries`, read again after each settle, each row by its own `outcome` and `channel` (the real `isDelivered` and `decodeDelivery`). The shim writes each settled send as ONE row in story 01's shape. The UNKNOWN row reads as story 01 renders it. No second list, no double count. |
| F5 missing states | COMMENTED (board 12), BLOG POSTED (15), the Confluence setup form (canvas B board 6); named read failures: `CANNOT READ DESTINATIONS` / `SENDS` / `HISTORY` + Retry (boards 37–39), a preview with no answer (40), a key save refused (canvas B board 7). Unreadable is never shown as empty. |
| F6 false simulated claims | Email Check reports the SENDER's verification, not the key (canvas B board 11: SENDER NOT VERIFIED); a send from an unverified sender settles FAILED `sender_not_verified` from that state, not from a fault (board 17). The file name is minted once with the send id, as story 01 does (`choose_path`): a prepared preview names the file and the receipt names the same file (board 29, fact `same_file`); an inline preview names only the folder. Paths, message ids, addresses and repositories keep their exact case (`p10-literal`). |
| F7 contrast | Recorded unrounded, with the element (Measurements). No colour change. |
| F8 the questions | A2 asked against story 01's current face; A3 as Codex Astra qualified it. |

## What the boards are, exactly

- **The app:** the PRODUCT app (`web/`), served by vite with `harness/vite.config.mjs`. The config swaps two modules for the harness copies: `./update/UpdatePosture` → `harness/ProposedUpdatePosture.tsx` and `./connections` → `harness/ProposedConnections.tsx` (canvas B). A second vite serves the product unchanged for boards 0a and 0b.
- **StrictMode:** the harness mounts the app without `<StrictMode>`, as the production build does (BACKLOG: `useResource` under StrictMode).
- **The hub:** a REAL hub (`scripts/graph_walk.py serve`) with `HOME=tempfile.mkdtemp()`, removed when the run ends. The project, two items, three published updates and the Jira account are made through the real routes. Update C also carries story 01's REAL records, made through story 01's routes: a file send that SENT, a file send that ended UNKNOWN (story 01's own ENAMETOOLONG recipe), and a manual row (`shots/facts.json`, `_seed.story01_real_on_c`).
- **The wire the canvas adds:** `harness/shim.ts` stands in for it, and its header says how: the destination and send records; the frozen transport bytes and the readable preview parsed back from them; one command id = one send; refusals before the boundary; the boundary; the settle; recovery after a restart; each settled send written as one row of story 01's history table; the file name minted once; email sender verification. Its argument names follow story 01 (`update_id`, `destination_id`, `preview_digest`, `send_id`, `command_id`; `DELETE /api/channels/destinations/{id}`).
- **Fixture faults and his own acts outside HoldSpeak** (each named on its board): no answer (11), a lost answer (21), a restart after the boundary (25), a changed gh login (20), a moved folder (30), SendGrid refusing the key (28), reads and a preview that get no answer (37–40); he signs in to Atlassian again (15) and verifies the sender in SendGrid (18).
- **What the build adds beyond the face:** the controller reads the open update's history again after a settle (today `current` is a snapshot of the list read); `Delivery` gains `proof` and `sendId` (`proof_json` and `send_id` are on the wire since story 01).

## Facts the boards prove (`shots/facts.json`)

- A double-click on Send makes one dispatch (`9-posted-github-*`: `dispatches_after_double_click` = 1).
- Retry after a lost answer reuses the key and does not dispatch again (`24-retried-one-dispatch-*`: `dispatches_with_lost_key` = 1).
- The lost answer stays on update A and never shows on B (`22-update-b-clean-*`: `b_state`). Back on A, the lost line and Retry are on screen (`24-retried-one-dispatch-*`: `back_on_a_before_retry.named`). At 1440 that screen is board 21 byte for byte (`same_pixels_as_board_21` true), so the byte fence refused it as a separate board and it is recorded as a fact; at 393 the bytes differ (not investigated; the menu-bar clock is one candidate).
- A restart after the boundary gives `unknown` / `interrupted` (`25-unknown-after-restart-*`: `rows`).
- A prepared file send's preview and receipt name the same file (`29-prepared-file-sent-*`: `same_file`).
- Every prepared send's end state is stored and shown (`33-discarded-*`: `prepared_rows`).
- A draft has no SEND well (`36-draft-no-send-*`: `send_well_on_draft` = 0).
- No preview shows raw JSON or XHTML, and no email row says DELIVERED (`preview_has_raw`, `words_delivered_on_email`).

## Measurements

84 renders (42 boards × 1440 × 900 and 393 × 852), `shots/facts.json`; both runs exit 0 with the fences on:

- Named elements on screen (in the viewport, inside every clipping ancestor, on top at the centre and two inner corners): **162 of 162**. Byte-identical shots within a width: **none**.
- Text under 12 px: **0** in the proposal, **0** inherited. Raw `<button>`: **0** in the proposal, **0** inherited.
- Horizontal overflow: **0**.
- Contrast, unrounded (Codex Astra r1 F7): lowest **4.50444771:1**: the PREPARED chip's colour on its fill, measured on its `◆` glyph (11 px) in the SEND well on boards 26–32 and on the `◆ PREPARED ×1` list chip (12 px) on board 35, Codex's "A27 PREPARED chip"; none under 4.5:1. No colour change.
- Pointer (UX-CANON C): **1588** proposal controls × 9 points = **14292**, each by `elementFromPoint` AND a real pointer move: **all owned**. Of the untouched window chrome, **168** controls miss points (the ROOM tab's right edge; at 393 the traffic lights), as on the unchanged product (BACKLOG).
- Modals **0**; raw JSON or XHTML in a preview **0**; DELIVERED on an email row **0**; browser errors **0**.

## Limits (what the boards are not)

- Beyond story 01's records on update C, the wire is the shim's statement of the design, not a server response. The dispatch sends nothing anywhere; proofs are fixture values.
- The GitHub account (`kwork`, CONNECTED) and one Confluence account are overlaid on the Connections read; the Jira account is real (NEVER CHECKED).
- At 393 the history rows wrap the ✓ lead token onto its own line above the name. That is the inherited `SurfaceLedgerRow` wrap; Codex Astra r1 F7 found it readable. No repair is proposed on this canvas.

## Proposed library repairs (the build moves each into the named file)

`harness/canvas.css`, "PROPOSED LIBRARY REPAIRS", names each rule's product file and line: the 12 px floor (the SYNCED token, the provenance host, the TransportKey word, the PARKED fold count) and the 44 px narrow target for gadget controls under a 420 px container. Canvas-only rules above that block: the literal token (`text-transform: none` on paths, ids, addresses, repositories) and the group's `scroll-margin-top` for the arrival.

## Reproduce

```bash
# from the worktree root; each run removes its own HOME and exits 2 on a hidden named element or byte-identical shots
ONLY_WIDTH=1440 PLAYWRIGHT_BROWSERS_PATH=$HOME/Library/Caches/ms-playwright \
  .venv/bin/python pm/roadmap/holdspeak-philo/phase-10-the-channels/assets/story-04-send-canvas/harness/shoot.py
ONLY_WIDTH=393 PLAYWRIGHT_BROWSERS_PATH=$HOME/Library/Caches/ms-playwright \
  .venv/bin/python pm/roadmap/holdspeak-philo/phase-10-the-channels/assets/story-04-send-canvas/harness/shoot.py
python3 pm/roadmap/holdspeak-philo/phase-10-the-channels/assets/story-04-send-canvas/harness/build_review.py
```
