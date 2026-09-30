# PHILO-11-03 — the canvases A–E and T1–T3

**Status: DRAFT, round two, for the owner's ratification** (UX-CANON §A.2: the canvas before the build). Round two pays Codex Astra r1 RATIFY-WITH-CONDITIONS (`../../checks/canvas-astra-r1.md`, committed verbatim). Nothing here is built in product code. The review page is `index.html` in this folder: every board at 1440 × 900 (left) and 393 × 852 (right).

Sources: story 03 (`../../story-03-the-canvases.md`), the design (`../../design/document-sources.md`, §4 the wire, §5 Slack, §6 the aftercare rewrite, §6a the decision seats, §6b the failure transitions), the faces grounding (`docs/internal/philo/phase-11/grounding/faces.md`, §6 the board list, §7 the rulings R1–R9), Astra's charter check (`../../checks/charter-astra-r1.md`), and the ratified Phase 10 canvases this extends (`../../../phase-10-the-channels/assets/story-04-send-canvas/`).

## Round two: Codex Astra r1 (`../../checks/canvas-astra-r1.md`)

| Astra r1 | The canvas now |
|---|---|
| F1 393 fit: A4 crushes the brief heading; C6b's picker misses 6 of 9 points; SEND/SENDS heads at 10 px, excluded from the count as "inherited"; covered controls excluded | The Chair BRIEF heading wraps its chips and Generate under the label at narrow width (A4 at 393). The form picker is 44 px on all nine points in every host (C6b at 393: 0 misses). SEND / SENDS heads are 12 px in every host, and `shoot.py` now counts EVERY word the well adds, its heads included (no exclusion): 0 under 12 px. A control under the host's own sticky bar is reached by ORDINARY scrolling (the mouse wheel over it, 1–2 steps) and probed again on all nine points; a control not reached is a miss (9 reached, 0 missed). Board T3c shows the scroll that clears the Chair's capture bar at 393. |
| F2 Canvas E exposes G3, does not settle the shared appearance | Drawn and decided: `harness/species.css`, the settled appearance story 04 builds. The well carries its own type (UI face 14 px, display face for preview headings, mono only for fields, paths and chips) and ONE row grammar in every host at every width: line 1 the lead and the name, line 2 the chips at the name's edge; an open preview at the name's indent. No host rule reaches in (the pullout's section grid and hairline, its 10 px h3, its list padding, the receipt view's monospace). Fences on every board: rows in the one grammar 274 of 274; preview text in a mono face 0. E1a–d each show an open preview. |
| F3 the dead Open | The Room's decision row unfolds in place — that is the seat — and its `Open` is withheld (fact `room_open_verbs` = 0 on B4, B4b). The routing repair is ledgered (G1). |
| F4 unseen content | T2a2: the changed passage (Nov 6) on screen at both widths. C5c: the digest body on screen at both widths. Each is a fact on the board (`changed_passage_on_screen`, `digest_body_on_screen`). |
| F5 the questions | Cut to the face choices below; the settled ones are recorded as decisions. |
| F6 coverage and harness boundary sound | Unchanged. |

**Where the rest goes (Astra r1 conditions):** story 04 builds G2 (the named preview refusal, never NO ANSWER), G3 (the species' isolated type and row grammar, `harness/species.css`), G4 (the 44 px picker on every host) and the heading layout and type (12 px heads; a head's chips wrap under its label at narrow width). Story 05 builds the host integration and the rendered-transition fences at both widths — T1, T2 and T3, including the prepared-send receipt surviving the Chair's branch change — with real producers and atlas cases that fail before the fixes. G1's routing repair and G5 go to the ledger.

## What the boards are, exactly

- **The app:** the PRODUCT app (`web/`), served by vite with `harness/vite.config.mjs`, twice: TODAY (the product as on main `332d9158`, no change) and PROPOSAL.
- **The proposal changes, all in `harness/`, none in product code:**
  - `species.css` (round two) — the SETTLED appearance of the species: its own type and its one row grammar, isolated from every host; the 12 px head; the 44 px picker; a head whose chips wrap under its label at narrow width.
  - `DocSendWell.tsx` — the proposed species (story 04): the product's ratified `SendWell` with its eight update bindings (faces.md §2, B1–B8) replaced by one document reference `{ref: "<kind>:<id>", label}`. The history of a new kind is its ended sends (no Mark delivered, R8). T1: a preview refused by name shows its refusal word. T2: PREVIEW CHANGED reads a fresh preview.
  - `P11Hosts.tsx` — the seats: one small host per face. `vite.config.mjs` puts each host into its product file at a NAMED anchor (the `SEATS` table); a missing or doubled anchor stops the build, so no board shows a seat the product file does not have. The seats: the Chair BRIEF section (both branches, T3) and its head chip; Intelligence → BRIEF; the decision window; Intelligence → DECISIONS (the record); the Room's DECISIONS & COMMITMENTS rows (unfolded in place; the dead Open withheld); the Meetings record; the meeting window; the Chair's MEETINGS row; the update (E1).
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
| A2-brief-picked-folder | Intelligence → BRIEF, after PEOPLE: SEND; Team folder open: FOLDER, Send + THIS DEVICE, the brief as Markdown. At 1440 the Chair behind shows the same row open (shared pick and press state, settled). | R4; faces §6 A2 |
| A3-brief-saved-history | ✓ SAVED on the row; SENDS 1 with the exact file path. No Mark delivered. | R8; F8 (SENDS, settled) |
| A6-brief-slack-person-sections | Slack picked; the Slack-text preview scrolled to `*People*` · Priya Nair: they owe 1 (0d). No Ack/Defer marks in the text (fact). | R1 |
| A5-brief-changed-send-again | Same-day Generate returned the same brief id (fact); a new person signal changed its words; the preview shows `Marek Wolny: they owe 1`. No old-version word. | R9; Astra r1 F4 |
| A5b-brief-changed-verb | The same row: Send again + ✓ SAVED (the last send). | R9 |
| A4-brief-prepared-chair | Chair head: BRIEF · 9 THINGS WAITING · ◆ PREPARED ×1 · THIS DEVICE · Generate. At 393 the label keeps its line; the chips and Generate wrap under it (round two). | faces §6 A4; r1 F1 |
| A4b-brief-prepared-row | First in SEND: ◆ Slack #leads · PREPARED · BY STEWARD · BRIEF SEP 29 · time · WEBHOOK SET · HOOKS.SLACK.COM; open: Send, HOOKS.SLACK.COM, Discard. | faces §6 A4 |
| A4c-brief-prepared-posted | The row stays as its result: ✓ POSTED · #leads · BY STEWARD; SENDS 2. No link. | R6 |
| T3a-chair-last-item | BRIEF · 1 THING WAITING with Ack, Defer; SEND below with its rows and SENDS 2. | T3 |
| T3b-chair-after-last-ack | Ack pressed on glass: the Chair changed branch (headline, ALL 9 HANDLED); SEND and SENDS 2 stay on the section (fact). | T3 |
| T3c-scrolled-clear-of-capture-bar | Round two: after the branch change, the wheel scrolls the Chair; at 393 the rows and SENDS clear the sticky capture bar; the POSTED receipt is still there. | T3; r1 F1 |
| B1-decision-window-picked | The decision window (400 px at 1440): after CONSEQUENCES, SEND; Slack open: CHANNEL, WEBHOOK, Send + HOOKS.SLACK.COM, the Slack text. Copy, Dictate, Edit stay in the footer. | R2, R4, R8; F7 |
| B2-decision-posted-slack | Send again + ✓ POSTED · #leads; the row ✓ POSTED 21:20. | R6 |
| B2b-decision-history | SENDS 1: ✓ Slack #leads · POSTED · #leads · time. | R8 |
| B3-decision-edited-send-again | Edited on glass (Edit, Done): the preview shows Nov 5; the verb is Send again. | R9; F6 |
| T2a-preview-changed-fresh-preview | Changed elsewhere after he read it; Send: REFUSED · PREVIEW CHANGED · NOTHING SENT, and the well already holds the fresh preview (Nov 6). | T2 |
| T2a2-preview-changed-passage | Round two: the same fresh preview scrolled — *Decision* · Freeze the old ledger on Nov 6 on screen at both widths. | T2; r1 F4 |
| T2b-preview-changed-sent | Send again: ✓ POSTED; the text that went has Nov 6 (fact); SENDS 2. | T2 |
| B5-record-intelligence-picked | Intelligence → DECISIONS, the record: SEND after its fields; Team folder open: decision, Why, Alternatives, Owner, Review, From, State — in the well's own face (round two; round one drew the receipt view's monospace, G3). | R2; design §6a; r1 F2 |
| B4-room-row-prepared-chip | Room: MTG Finance runs one more reconciliation… · CONFIRMED · ◆ PREPARED ×1. No Open on either decision row (withheld, G1). | faces §6 B4; §6a; r1 F3 |
| B4b-room-row-open-prepared | The row unfolds in place — the seat: SEND · ◆ Team folder · PREPARED · BY CODEX · D-… · time; Send, THIS DEVICE, Discard; the record body. | B4; r1 F3 |
| C1-meetings-record-send | The Meetings record (640 px at 1440): SUMMARY, then SEND with the form picker (SUMMARY) and the destinations, then TRANSCRIPT. | R3, R4; F7 |
| C2-summary-slack-picked | The summary in Slack text: title, date, summary, Topics. Never the transcript. | R3 |
| C3-summary-posted-slack | Send again + ✓ POSTED · #leads; the row ✓ POSTED. | R6 |
| C3b-summary-history | SENDS 1: ✓ Slack #leads · POSTED · #leads. | R8 |
| C5-digest-form-slack | The picker on DIGEST: What we decided, Still open. No DIGEST → SLACK rows on the record (fact). | R3, R7 |
| C5c-digest-body | Round two: the digest preview scrolled — *What we decided* and *Still open* with their items on screen at both widths. | R3; r1 F4 |
| C5b-followup-form-folder | The picker on FOLLOW-UP to the folder: the follow-up draft. | R3 |
| C4-no-summary-no-well | Vendor call has no summary: no SEND well (fact `send_wells` = 0). | faces §6 C4 |
| T1-over-slack-limit-refused | A 41,099-character summary to Slack: ✗ REFUSED · TOO LARGE FOR SLACK · 41,099 / 39,000 CHARACTERS · NOTHING SENT · HOOKS.SLACK.COM. No Send; never NO ANSWER (fact). | T1; charter Q1 (39,000) |
| C6-meeting-window-well | The meeting window (400 px): SEND with the picker, the rows, SENDS 1, then ACTION ITEMS. | R4 |
| C6b-chair-meetings-row-well | The Chair's unfolded Ledger cutover sync row: SUMMARY, then SEND (the picker 44 px at 393, all nine points) and SENDS 1. | R4; G4 |
| E1a-update-well | The settled species on the update, Team folder open: the one row grammar, the preview in the well's own type (Progress, Decisions … as headings); the update's DELIVERY with To + Mark delivered stays below (R8). | UX-CANON §D; R8; r1 F2 |
| E1b-brief-well | The settled species in Intelligence → BRIEF, a preview open. | UX-CANON §D; r1 F2 |
| E1c-decision-well | The settled species in the decision window, a preview open (Context, Decision, Consequences as headings, not `*bold*` text). | UX-CANON §D; r1 F2 |
| E1d-meeting-well | The settled species in the meeting window, with the picker, a preview open. | UX-CANON §D; r1 F2 |

## `meeting_decision` on glass (design §6a)

Confirmed: **no face renders a lifecycle `decisions` row.** Code: nothing in `web/src` consumes `openMoment` or `transition` outside `useProjectRoomController.ts`, and the only caller of `/api/decisions?project_id=` is `web/src/features/project-room/api.ts:45`. Glass: the lifecycle-only decision "Cut over by space, not by region" (in the `decisions` table from the meeting's artifact, with no decision record) is absent from the Room (fact `lifecycle_row_text_in_room` = false on 0c and B4, both widths). It does appear as TEXT inside other documents (a brief item "Review decision: …", the digest's "What we decided"): those are other documents rendering it, not a seat of the row. So `meeting_decision` gets no board and no well, as design §6a says.

## Settled by the brains' check (recorded, not asked)

Astra r1 finding 5, adopted by Muad'Dib:

- **The history head word** (faces.md F8): a new kind's history is headed **`SENDS N`** (N = sent rows; no counter at zero). The update keeps its ratified `DELIVERY N`, because its history also holds the manual Mark delivered rows (R8).
- **The meeting's three forms** (R3, R7): one well per meeting; a library CycleGadget first inside SEND picks Summary / Digest / Follow-up (C1, C5, C5c, C5b).
- **The Room's decision row:** it unfolds in place and holds the record's well (the seat); the dead `Open` is withheld (B4, B4b; G1 ledgered).
- **The Chair carries the full well** (R4, "In all those"): no question.
- **The Chair BRIEF heading at 393:** drawn (A4); not a question.
- **The size on the Slack refusal:** the refusal answer carries `size` and `limit` so the face shows `41,099 / 39,000 CHARACTERS` (T1). This is a design-wire amendment for stories 01 and 02 (design §5, `payload_too_large:slack`); it does not reopen his limit ruling (39,000).
- **Two seats of one document share their visible pick and press state** (the Chair's brief well and the Intelligence brief well; A2 at 1440). How the store holds it is story 04's engineering.

## The owner's choice

One question remains, and it is a face choice:

1. **Ratify the canvas as drawn** — the well on every face where each document lives, in the settled appearance (`species.css`: its own type, one row grammar in every host at every width), Slack in Destinations, the old Slack rows gone, and the three failure transitions T1–T3? **Recommended: yes.**

## What did not survive the glass (findings; none fixed in product code)

- **G1 — the Room's `Open` on a decision row opens nothing** (0c). `ProjectRoomCore.tsx:1504`, `:1525` call `openPrimitive("decision:<record id>")`; the desk has no such primitive, and `/api/decisions/<record id>` answers `404 decision_not_found` (checked against the isolated hub). The design §6a unknown is answered: it renders nothing. **Ledgered** (routing repair; `pm/roadmap/holdspeak/BACKLOG.md`). The proposed face withholds the verb (round two); the unfolded row is the seat.
- **G2 (story 04) — the product preview error collapses to NO ANSWER** (`web/src/features/channels/SendWell.tsx:476-481`), and `payload_too_large:` has only the generic word `TOO LARGE` (`channels.ts`, `REFUSED_PREFIX`). T1 draws the change story 04/05 owes: the named word, the size, no Send.
- **G3 (story 04) — the host's styles reached into the species** in round one: the receipt view's monospace in B5; rows inline in some ~400 px windows and stacked in others. Round two draws the correction (`harness/species.css`); story 04 moves it into the library.
- **G4 (story 04) — the form picker was under the 44 px target on the Chair at 393** in round one (6 of 9 points missed): the library's narrow-target rule is a container query, and the Chair is not a surface container. Round two draws the rule by viewport too; 0 misses.
- **G5 (ledger) — the Meetings window footer at 393: its status text runs under its own buttons.** `NO SUMMARY ROUTE · NO ASSIGNMENT` is drawn under `MD` and `SRT` (`shots/T1-over-slack-limit-refused-393.png`; the same footer on every Meetings-window board at 393: C1, C2, C3, C3b, C5, C5c, C5b). Inherited (the product's own footer), and against the standing rule that text never overlaps controls. The well's boards do not need that footer on screen: every well element they name is above it and passes the on-screen fence, so it does not count against the well's reach. Ledgered (`pm/roadmap/holdspeak/BACKLOG.md`), not fixed here.
- **Inherited, noted:** the host's own section heads stay 10 px in a pullout (DECISION CONTEXT, PEOPLE); the Chair's sticky capture bar and the Room's sticky ask well cover rows scrolled under them — the well's rows are reached by ordinary scrolling (9 controls, 1–2 wheel steps; T3c).
- **Confirmed as designed:** same-day Generate returns the same brief id (A5 fact); the preview reads the stored brief with the real person overlay (A6); no meeting form carries the transcript (every board); POSTED has no link (every board); no Mark delivered on a new kind (every board); no stale-version word (every board).

## Measurements (`shots/facts.json`, computed by `harness/build_review.py`)

90 renders (45 boards × 1440 × 900 and 393 × 852), each width on its own hub and HOME; both runs exit 0 with every fence on:

- Named elements on screen (in the viewport, inside every clipping ancestor, on top): **142 of 142**. A block taller than its scroller counts by its first 40 px; where the board's point is a line inside a long preview (A5, A6, B3, T2a2, C5c), the fact is that line's own box on screen.
- Pointer (UX-CANON C; 9 points; the 44 × 44 target at 393): **241** proposal controls owned on all nine points, **9** of them after ordinary scrolling from under the host's sticky bar; **0** with misses.
- Rows in the one grammar: **274 of 274**. Preview text in a mono face: **0**. Open on a proposed Room decision row: **0**.
- Text under 12 px in the proposal, its SEND / SENDS heads included: **0**. Raw `<button>` in the proposal: **0**. Modals: **0**. Horizontal overflow: **0**. Browser errors: **0**.
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

- Astra's check r1: RATIFY-WITH-CONDITIONS (`../../checks/canvas-astra-r1.md`, verbatim); paid in round two (table above).
- The owner's word: owed (recorded verbatim here before story 04 or 05 commits a face change).
