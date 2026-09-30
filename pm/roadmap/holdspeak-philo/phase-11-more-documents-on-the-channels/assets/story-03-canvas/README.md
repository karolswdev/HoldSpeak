# PHILO-11-03 — the canvases A–E and T1–T3

**Status: DRAFT, round one, for Astra's check and then the owner's ratification** (UX-CANON §A.2: the canvas before the build). Nothing here is built in product code. The review page is `index.html` in this folder: every board at 1440 × 900 (left) and 393 × 852 (right).

Sources: story 03 (`../../story-03-the-canvases.md`), the design (`../../design/document-sources.md`, §4 the wire, §5 Slack, §6 the aftercare rewrite, §6a the decision seats, §6b the failure transitions), the faces grounding (`docs/internal/philo/phase-11/grounding/faces.md`, §6 the board list, §7 the rulings R1–R9), Astra's charter check (`../../checks/charter-astra-r1.md`), and the ratified Phase 10 canvases this extends (`../../../phase-10-the-channels/assets/story-04-send-canvas/`).

## What the boards are, exactly

- **The app:** the PRODUCT app (`web/`), served by vite with `harness/vite.config.mjs`, twice: TODAY (the product as on main `332d9158`, no change) and PROPOSAL.
- **The proposal changes, all in `harness/`, none in product code:**
  - `DocSendWell.tsx` — the proposed species (story 04): the product's ratified `SendWell` with its eight update bindings (faces.md §2, B1–B8) replaced by one document reference `{ref: "<kind>:<id>", label}`. The history of a new kind is its ended sends (no Mark delivered, R8). T1: a preview refused by name shows its refusal word. T2: PREVIEW CHANGED reads a fresh preview.
  - `P11Hosts.tsx` — the seats: one small host per face. `vite.config.mjs` puts each host into its product file at a NAMED anchor (the `SEATS` table); a missing or doubled anchor stops the build, so no board shows a seat the product file does not have. The seats: the Chair BRIEF section (both branches, T3) and its head chip; Intelligence → BRIEF; the decision window; Intelligence → DECISIONS (the record); the Room's DECISIONS & COMMITMENTS rows; the Meetings record; the meeting window; the Chair's MEETINGS row; the update (E1).
  - The removals (R7): the aftercare `DIGEST → SLACK` / `FOLLOW-UP → SLACK` group on the Meetings record; the Credentials `Slack webhook` row.
  - `ProposedDestinations.tsx` — the product's Destinations group with Slack as its sixth channel (design §5).
  - `p11channels.ts` — every import of `features/channels/channels.ts` resolves here: the Slack words and egress chip, the document refusal words, and the generic wire (`document_ref`).
  - `shim.ts` — the unbuilt wire, stated in its header: the eight document renderers of design §3 over the REAL stored records (read by id through the real hub), the generic preview / send / sends, Slack destinations and the keychain stand-in, the 39,000-character limit, `preview_changed`, and `window.__p11Prepare` (the steward's / an agent's `channel.prepare`). A project update to a Phase 10 destination is forwarded to the real Phase 10 routes. The dispatch is a stand-in: **nothing leaves the machine.**
  - `nav.ts` (both modes) — navigation only (what a Dock click or a row does), so the rig reaches each window at 393.
- **The hub:** a REAL hub (`scripts/graph_walk.py serve`) on `HOME=tempfile.mkdtemp()`, removed when the run ends; the People store on a file key in that HOME. Seeded through its real routes (the project, the published update, the desk decision, the People relationship, the brief, the folder destination) and, for the records no route makes, through the product's DB layer (`harness/seed_db.py`: three meetings with stored intelligence, one with no summary, one with a 41,043-character summary; two decision records, one from a confirmed meeting proposal). Each transcript carries the sentinel `TRANSCRIPT-SENTINEL-7Q`; no well ever shows it (fact `transcript_sentinel` on every board). The TODAY boards set a Slack webhook in that HOME's `config.json` so the old rows render; nothing calls it.
- **His acts outside HoldSpeak, and fixtures** (each named on its board): the steward prepared a brief send (A4); an agent (`codex`) prepared a record send (B4); a new person signal changed the brief after a send (A5); the decision changed in another place after he read the preview (T2); all brief items but one were handled through the real shelf route (T3).

## The boards

Shots are `shots/<id>-1440.png` and `shots/<id>-393.png`. I looked at every shot at both widths.

| Board | What it shows | Answers |
|---|---|---|
| 0a-today-aftercare-slack-rows | TODAY: the Meetings record shows AFTERCARE · DIGEST → SLACK · FOLLOW-UP → SLACK, each with a Send that only proposes. | R7: what goes |
| 0b-today-credentials-slack-row | TODAY: Credentials shows `Slack webhook hooks.slack.com SET`. | R7: what goes |
| 0c-today-room-record-open | TODAY: the Room's DECISIONS & COMMITMENTS rows (both decision records). Open pressed on the MTG row: **no window opens** (1 window before, 1 after; no console line). | design §6a unknown → a defect (G1) |
| A1-brief-chair-no-destination | Chair: BRIEF · 9 THINGS WAITING, then SEND · NO DESTINATION + Add destination. Each unfolded meeting row with a summary carries its own well. | R4; faces §6 A1 |
| D1-slack-form | Destinations, Channel SLACK: Webhook (SecretRow), Channel name `#leads`, Name `Slack #leads` (filled, editable), Save, HOOKS.SLACK.COM. | R6; design §5 |
| D2b-webhook-refused | `https://example.com/hooks/abc` typed: KEY NOT SAVED · WEBHOOK NOT VALID. | design §5 host rule |
| D2a-webhook-saved | The webhook kept: SET; the URL never shown again (fact). | design §5 secret |
| D3-slack-row-checked | Row: SLACK · #leads · WEBHOOK SET · HOOKS.SLACK.COM. Open: CHANNEL NAME, WEBHOOK SET · hooks.slack.com; Check → WEBHOOK SET · HOST OK (no test post); Edit; Remove. | design §5 Check |
| D4-credentials-no-slack-row | Credentials: Web pairing token … Custom webhook; no Slack webhook row. | R7 |
| A2-brief-picked-folder | Intelligence → BRIEF, after PEOPLE: SEND; Team folder open: FOLDER, Send + THIS DEVICE, the brief as Markdown. At 1440 the Chair behind shows the same row open (Q7). | R4; faces §6 A2 |
| A3-brief-saved-history | ✓ SAVED on the row; SENDS 1 with the exact file path. No Mark delivered. | R8; F8 (Q1) |
| A6-brief-slack-person-sections | Slack picked; the Slack-text preview scrolled to `*People*` · Priya Nair: they owe 1 (0d). No Ack/Defer marks in the text (fact). | R1 |
| A5-brief-changed-send-again | Same-day Generate returned the same brief id (fact); a new person signal changed its words; the preview shows `Marek Wolny: they owe 1`. No old-version word. | R9; Astra r1 F4 |
| A5b-brief-changed-verb | The same row: Send again + ✓ SAVED (the last send). | R9 |
| A4-brief-prepared-chair | Chair head: BRIEF · 9 THINGS WAITING · ◆ PREPARED ×1 · THIS DEVICE · Generate. **At 393 the chip crushes the head text into a column** (Q5). | faces §6 A4 |
| A4b-brief-prepared-row | First in SEND: ◆ Slack #leads · PREPARED · BY STEWARD · BRIEF SEP 29 · time · WEBHOOK SET · HOOKS.SLACK.COM; open: Send, HOOKS.SLACK.COM, Discard. | faces §6 A4 |
| A4c-brief-prepared-posted | The row stays as its result: ✓ POSTED · #leads · BY STEWARD; SENDS 2. No link. | R6 |
| T3a-chair-last-item | BRIEF · 1 THING WAITING with Ack, Defer; SEND below with its rows and SENDS 2. | T3 |
| T3b-chair-after-last-ack | Ack pressed on glass: the Chair changed branch (headline, ALL 9 HANDLED); SEND and SENDS 2 stay on the section (fact). | T3 |
| B1-decision-window-picked | The decision window (400 px at 1440): after CONSEQUENCES, SEND; Slack open: CHANNEL, WEBHOOK, Send + HOOKS.SLACK.COM, the Slack text. Copy, Dictate, Edit stay in the footer. | R2, R4, R8; F7 |
| B2-decision-posted-slack | Send again + ✓ POSTED · #leads; the row ✓ POSTED 21:20. | R6 |
| B2b-decision-history | SENDS 1: ✓ Slack #leads · POSTED · #leads · time. | R8 |
| B3-decision-edited-send-again | Edited on glass (Edit, Done): the preview shows Nov 5; the verb is Send again. | R9; F6 |
| T2a-preview-changed-fresh-preview | Changed elsewhere after he read it; Send: REFUSED · PREVIEW CHANGED · NOTHING SENT, and the well already holds the fresh preview (Nov 6). | T2 |
| T2b-preview-changed-sent | Send again: ✓ POSTED; the text that went has Nov 6 (fact); SENDS 2. | T2 |
| B5-record-intelligence-picked | Intelligence → DECISIONS, the record: SEND after its fields; Team folder open: decision, Why, Alternatives, Owner, Review, From, State. The body draws in the host's monospace (G3). | R2; design §6a |
| B4-room-row-prepared-chip | Room: MTG Finance runs one more reconciliation… · CONFIRMED 21:18 · ◆ PREPARED ×1 · Open. | faces §6 B4; §6a |
| B4b-room-row-open-prepared | The row opens in place (Open stays): SEND · ◆ Team folder · PREPARED · BY CODEX · D-… · time; Send, Discard; the record body. | B4; Q3 |
| C1-meetings-record-send | The Meetings record (640 px at 1440): SUMMARY, then SEND with the form picker (SUMMARY) and the destinations, then TRANSCRIPT. | R3, R4; F7 |
| C2-summary-slack-picked | The summary in Slack text: title, date, summary, Topics. Never the transcript. | R3 |
| C3-summary-posted-slack | Send again + ✓ POSTED · #leads; the row ✓ POSTED. | R6 |
| C3b-summary-history | SENDS 1: ✓ Slack #leads · POSTED · #leads. | R8 |
| C5-digest-form-slack | The picker on DIGEST: What we decided, Still open. No DIGEST → SLACK rows on the record (fact). | R3, R7 |
| C5b-followup-form-folder | The picker on FOLLOW-UP to the folder: the follow-up draft. | R3 |
| C4-no-summary-no-well | Vendor call has no summary: no SEND well (fact `send_wells` = 0). | faces §6 C4 |
| T1-over-slack-limit-refused | A 41,099-character summary to Slack: ✗ REFUSED · TOO LARGE FOR SLACK · 41,099 / 39,000 CHARACTERS · NOTHING SENT · HOOKS.SLACK.COM. No Send; never NO ANSWER (fact). | T1; Q1 (39,000) |
| C6-meeting-window-well | The meeting window (400 px): SEND with the picker, the rows, SENDS 1, then ACTION ITEMS. | R4 |
| C6b-chair-meetings-row-well | The Chair's unfolded Ledger cutover sync row: SUMMARY, then SEND and SENDS 1. | R4 |
| E1a-update-well | The update composes the same species: SEND rows, then DELIVERY with To + Mark delivered (the update only). | UX-CANON §D; R8 |
| E1b-brief-well | The same species in Intelligence → BRIEF. | UX-CANON §D |
| E1c-decision-well | The same species in the decision window. | UX-CANON §D |
| E1d-meeting-well | The same species in the meeting window, with the picker. | UX-CANON §D |

## `meeting_decision` on glass (design §6a)

Confirmed: **no face renders a lifecycle `decisions` row.** Code: nothing in `web/src` consumes `openMoment` or `transition` outside `useProjectRoomController.ts`, and the only caller of `/api/decisions?project_id=` is `web/src/features/project-room/api.ts:45`. Glass: the lifecycle-only decision "Cut over by space, not by region" (in the `decisions` table from the meeting's artifact, with no decision record) is absent from the Room (fact `lifecycle_row_text_in_room` = false on 0c and B4, both widths). It does appear as TEXT inside other documents (a brief item "Review decision: …", the digest's "What we decided"): those are other documents rendering it, not a seat of the row. So `meeting_decision` gets no board and no well, as design §6a says.

## Open questions for the owner (each with a recommendation)

1. **The history head word (faces.md F8).** The Dock has `Delivery` (the roadmap board); the Phase 10 history head is `DELIVERY`. Proposed: a new kind's history head is **`SENDS N`** (N = sent rows; no counter at zero); the update keeps its ratified `DELIVERY N`, because its history also holds the manual Mark delivered rows (R8). **Recommended: yes.**
2. **The meeting's three forms (R3, R7).** One well per meeting, with a library CycleGadget first inside SEND: Summary / Digest / Follow-up (boards C1, C5, C5b). The pick is remembered per meeting. **Recommended: yes.**
3. **The Room's decision row.** The row opens in place and holds the record's well; `Open` stays in its slot; the row carries `◆ PREPARED ×K` when a send waits (B4, B4b). **Recommended: yes.** (Separately, `Open` opens nothing today: G1, ledgered, not fixed here.)
4. **The Chair carries the full well** under the brief and in each unfolded meeting row with a summary (A1, C6b, T3), as R4 reads. The alternative is a PREPARED chip only on the Chair and the well in Intelligence. **Recommended: the full well (R4: "In all those").**
5. **The PREPARED ×K chip in the Chair BRIEF head at 393** squeezes `BRIEF · 9 THINGS WAITING` into a one-word column (A4 at 393). **Recommended:** keep the chip in the head at 1440; at narrow width the head's chips wrap under the label (a SurfaceSection head fix in story 04, not a move).
6. **T1 shows the size:** `41,099 / 39,000 CHARACTERS` beside TOO LARGE FOR SLACK. This needs the refusal answer to carry `size` and `limit` (a small addition to design §5's named refusal). **Recommended: yes** — he sees by how much, and picks another channel.
7. **Two seats of one document share one state.** The Chair's brief well and the Intelligence brief well are one object: a pick or a press in one shows in the other (A2 at 1440). **Recommended: yes** — one object, one state (UX-CANON §D).

## What did not survive the glass (findings; none fixed in product code)

- **G1 — the Room's `Open` on a decision row opens nothing** (0c). `ProjectRoomCore.tsx:1504`, `:1525` call `openPrimitive("decision:<record id>")`; the desk has no such primitive, and `/api/decisions/<record id>` answers `404 decision_not_found` (checked against the isolated hub). The design §6a unknown is answered: it renders nothing. Ledger it; the canvas's row-opens-in-place (Q3) does not depend on it.
- **G2 — the product preview error collapses to NO ANSWER** (`web/src/features/channels/SendWell.tsx:476-481`), and `payload_too_large:` has only the generic word `TOO LARGE` (`channels.ts`, `REFUSED_PREFIX`). T1 draws the change story 04/05 owes: the named word, the size, no Send.
- **G3 — the host's styles reach into the species.** In Intelligence → DECISIONS the preview body draws in the receipt view's monospace (B5); at about 400 px the destination rows draw inline in some windows (A2, B1, B5) and stacked in others (C6, E1b–d; fact `_row_layout_*`). Canvas E's law ("the same object never drawn two ways") needs the species to isolate its layout and type from the host (story 04).
- **G4 — the form picker (CycleGadget) on the Chair at 393 is under the 44 px target** (C6b at 393: 6 of 9 points miss). The Meetings window's picker at 393 passes. Story 04: the narrow-target rule on the Chair too.
- **G5 — inherited, not this canvas's:** the SurfaceSection head is 10 px in a pullout, the same as the host's own heads (recorded as the species' size); the Chair's sticky capture bar and the Room's sticky ask well cover controls scrolled under them at 393 (17 controls recorded `under_host_bar`, not counted as misses).
- **Confirmed as designed:** same-day Generate returns the same brief id (A5 fact); the preview reads the stored brief with the real person overlay (A6); no meeting form carries the transcript (every board); POSTED has no link (every board); no Mark delivered on a new kind (every board); no stale-version word (every board).

## Measurements (`shots/facts.json`, computed by `harness/build_review.py`)

84 renders (42 boards × 1440 × 900 and 393 × 852), each width on its own hub and HOME:

- Named elements on screen (in the viewport, inside every clipping ancestor, on top): **132 of 132**. A block taller than its scroller counts by its first 40 px. Where the board's point is a line inside a long preview (A5, A6, B3), the fact is that line's own box on screen (`new_line_on_screen`, `people_line_on_screen`, `new_text_on_screen`).
- Pointer (UX-CANON C; 9 points; the 44 × 44 target at 393): **232** proposal controls owned; **1** with misses (G4); **17** under the host's own sticky bar.
- Text under 12 px in the proposal: **0**. Raw `<button>` in the proposal: **0**. Modals: **0**. Horizontal overflow: **0**. Browser errors: **0**.
- Stale-version words: **0**. Links on a Slack post: **0**. Mark delivered on a new kind: **0**. Transcript sentinel in a well: **0**.
- Identical shots within a width (clock masked): **none**.

## Limits (what the boards are not)

- The wire is the shim's statement of design §§3–5, not a server answer. The renderers are the shim's; story 01 builds the real ones. Proofs are fixture values; nothing was dispatched.
- The brief renderer reads `/api/brief/latest` and refuses any other id (`document_not_found`); story 01 reads by id.
- The Slack text conversion is the shim's minimal reading of design §5 (headings and bold to `*bold*`, lists to `•`); story 02 fixes the exact rules.
- No real Slack workspace, no real webhook; the 39,000 limit is the ruled number, applied by the shim.

## Reproduce

```bash
# from the worktree root; a python with playwright (CANVAS_PYTHON) and web/node_modules installed.
# Both widths, each on its own hub and HOME (removed when it ends); exit 2 on a failed fence.
PLAYWRIGHT_BROWSERS_PATH=$HOME/Library/Caches/ms-playwright CANVAS_PYTHON=<python> \
  <python> pm/roadmap/holdspeak-philo/phase-11-more-documents-on-the-channels/assets/story-03-canvas/harness/shoot.py
<python> pm/roadmap/holdspeak-philo/phase-11-more-documents-on-the-channels/assets/story-03-canvas/harness/build_review.py
```

## Checks and ratification

- Astra's check: owed.
- The owner's word: owed (recorded verbatim here before story 04 or 05 commits a face change).
