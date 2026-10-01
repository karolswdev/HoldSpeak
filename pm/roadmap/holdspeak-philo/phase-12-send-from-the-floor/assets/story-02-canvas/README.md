# PHILO-12-02 — the canvases F–J

**Status: DRAFT, round one, for Astra's check and the owner's ratification** (UX-CANON §A.2: the canvas before the build). Nothing here is built in product code: every change lives under `harness/`. The review page is `index.html` in this folder: every board at 1440 × 900 (left) and 393 × 852 (right), the art sheet first.

Sources: the story (`../../story-02-the-canvases.md`, with the r2 boards H6, H7, G7, G8, G9), the design (`../../design/floor-send.md`), the eleven ratified defaults (`../../current-phase-status.md`, "The one question"), Astra's charter check (`../../checks/charter-astra-r1.md`), the faces grounding (`docs/internal/philo/phase-12/grounding/faces.md` §3; `Open` only supersedes its F2), `docs/internal/UX-CANON.md` and `web/ICON-DISCIPLINE.md`.

## What the boards are, exactly

- **The app:** the PRODUCT app (`web/`), served by vite with `harness/vite.config.mjs` against a REAL hub (`scripts/graph_walk.py serve`) on `HOME=tempfile.mkdtemp()`, removed when the run ends. Each width runs on its own hub and HOME.
- **The seats** (`vite.config.mjs`, the `SEATS` table): each product file the Floor send touches gets ONE named hook into `harness/p12.ts` at a NAMED anchor. A missing or doubled anchor STOPS THE BUILD, so no board shows a seat the product file does not have. Files seated: `desk/sprites.ts` (the art), `desk/gl/sceneModel.ts` (the Floor layer), `desk/gl/engine.ts` (the drop rule, the open of an icon), `desk/gl/WorldStage.tsx` (the tag), `desk/components/AskPanel.tsx` (the selection bar), `desk/floorMenu.ts` (the one object menu), `desk/components/DeskMenuBar.tsx` (Object and the compact Go), `desk/components/DeskListView.tsx` (the brief row), `desk/surface/send/SendWell.tsx` (the pushed pick), `meetings/MeetingSendWell.tsx` (the pick kept across forms), `desk/pullouts/views/BriefView.tsx` (the exact brief id), `features/project-room/ProjectRoomCore.tsx` (the Room link), `pages/cores/connections/Destinations.tsx` (Settings at a row). `desk/pullouts/ArtifactPullout.tsx` resolves to `harness/ProposedArtifactPullout.tsx` (J1).
- **The wire the shim stands in for** (`harness/p12.ts` header, W1–W4): `artifact:<id>` rendered from the stored body with only the synthesis-owned source footer left out (story 01); `GET /api/brief/{id}` (story 01); the Fact<T> reads, a meeting's summary presence and a project's latest published update, both REAL reads, with a fixture that holds one `loading` or `failed` (H7); and five **stand-in destinations** (Slack, GitHub, Jira, Confluence, email). Each channel ships on main, but its account would need the owner's keychain or logins, which a canvas never touches. Their preview body is the real hub's render of the same document (asked through the real folder destination; Slack's minimal text conversion applied); their Send is answered by the shim. **Nothing leaves the machine.** The folder destination ("Team folder") is fully real: a real preview, a real Send that writes into the run's temp folder.
- **The art** (`harness/draw_sprites.py`): eight 64 × 64 sprites drawn pixel by pixel in the house palette, each with `_sel` and `_stale` derived by the PRODUCT's own `web/scripts/gen-sprite-states.py`. Served from `harness/sprites/` at `/desk/sprites/p12/`; nothing lands in `web/public`. Sheet: `shots/sprite-sheet.png` (rows: decision, brief, FILE, GITHUB, JIRA, CONFLUENCE, EMAIL, SLACK; columns: rest, _sel, _stale).
- **The seed:** through the hub's real routes (`harness/rig.py`: two projects, one with two published updates and one with none, the desk decision, the brief, the folder destination) and, for what no route makes, the product's DB layer (`harness/seed_db.py`: a meeting with a summary, one with none, a requirements artifact whose body ends with the synthesis source footer). The fresh HOME's own presets (zones, notes, personas) stay.
- **His acts, stated on the boards:** the rig places two Floor icons (Vendor call, the decision) where he would drag them, because the default grid puts Vendor call under the Reference drawer (inherited). The rig reaches 393 menus by a touch long-press (CDP touch events), and an object "selected" through the store before the menu bar's Object or Go menu.

## The boards

| F1-destinations-column | 1440: the folder, Slack and GitHub destinations in one column at the right edge, the brief icon on top; parked ones absent. 393: the list, no destination row, the brief row. | [1440](shots/F1-destinations-column-1440.png) · [393](shots/F1-destinations-column-393.png) | defaults 1, 2, 6, 7 |
| F2-destination-menu | 1440: Slack #leads selected, its menu holds Open, nothing else (Park and Remove stay in Settings). 393: the phone has no icon; Settings is the door. | [1440](shots/F2-destination-menu-1440.png) · [393](shots/F2-destination-menu-393.png) | default 8; Open only supersedes grounding F2 |
| F2b-open-lands-on-row | Settings → Destinations opened at Slack #leads, the row open (not the add form). | [1440](shots/F2b-open-lands-on-row-1440.png) · [393](shots/F2b-open-lands-on-row-393.png) | default 8; Astra r1 finding 6 |
| F3-no-destinations | The folder parked through the real route, no stand-ins: no icon and nothing in their place. The brief stays. | [1440](shots/F3-no-destinations-1440.png) · [393](shots/F3-no-destinations-393.png) | UX-CANON A.8 |
| F4-decision-sprite | 1440: the decision wears the gavel (selected: the _sel image, the accent label chip) among notes. 393: the list row carries the same art. | [1440](shots/F4-decision-sprite-1440.png) · [393](shots/F4-decision-sprite-393.png) | faces F2 (red on main: the note sprite) |
| F5-six-channels | 1440: one destination per channel: folder, Slack, GitHub, Jira, Confluence, email; at the foot the column wraps into a second column to its left. 393: the same six in Send to ▸, each with its channel word. | [1440](shots/F5-six-channels-1440.png) · [393](shots/F5-six-channels-393.png) | default 7 |
| G1-decision-held-over-slack | 1440: the tag Preview for Slack #leads, opened to the left near the edge, one line; the target lit. 393: the menu path, Send to ▸ open. | [1440](shots/G1-decision-held-over-slack-1440.png) · [393](shots/G1-decision-held-over-slack-393.png) | default 4; faces F4 |
| G2-released-preview-open | The decision window opens at the drop point with Slack #leads picked, the preview loaded, Send and the egress chip HOOKS.SLACK.COM in the well. Nothing sent. | [1440](shots/G2-released-preview-open-1440.png) · [393](shots/G2-released-preview-open-393.png) | default 10; design §6 |
| G7-second-pick-in-place | The decision dropped again on Team folder (393: the Go menu, the window covering the list): the same window changes its pick in place (no second window). | [1440](shots/G7-second-pick-in-place-1440.png) · [393](shots/G7-second-pick-in-place-393.png) | Astra r1 finding 4 |
| G3-sent | He pressed Send: POSTED in the same well (the stand-in dispatch; nothing left the machine). | [1440](shots/G3-sent-1440.png) · [393](shots/G3-sent-393.png) | design §6 |
| G4-no-summary-tag | 1440: the tag NO SUMMARY in the warning look, the target not lit; release opens nothing. 393: Send to ▸ withheld on that meeting. | [1440](shots/G4-no-summary-tag-1440.png) · [393](shots/G4-no-summary-tag-393.png) | faces F5; default 3 |
| G4b-no-published-update-tag | 1440: the tag NO PUBLISHED UPDATE. 393: Send to ▸ withheld on that project. | [1440](shots/G4b-no-published-update-tag-1440.png) · [393](shots/G4b-no-published-update-tag-393.png) | default 5 |
| G4c-parked-tag | 1440: the tag PARKED over the GitHub icon still on the Floor. 393: after the read, Send to ▸ no longer lists it. | [1440](shots/G4c-parked-tag-1440.png) · [393](shots/G4c-parked-tag-393.png) | design §6 |
| G5-meeting-summary-picked | The meeting window, the picker on SUMMARY, Slack #leads picked and its preview. | [1440](shots/G5-meeting-summary-picked-1440.png) · [393](shots/G5-meeting-summary-picked-393.png) | default 9 |
| G8-digest-keeps-destination | The picker moved to DIGEST: Slack #leads stays picked and the digest's preview loads for it. | [1440](shots/G8-digest-keeps-destination-1440.png) · [393](shots/G8-digest-keeps-destination-393.png) | Astra r1 finding 4 |
| G6-project-latest-update | The Room at the Update posture on the latest published update, Team folder picked, its preview. | [1440](shots/G6-project-latest-update-1440.png) · [393](shots/G6-project-latest-update-393.png) | default 5; Astra r1 finding 1 |
| G9a-room-on-older-update | Before: he has the older published update open in the Room (one milestone in its Progress). | [1440](shots/G9a-room-on-older-update-1440.png) · [393](shots/G9a-room-on-older-update-393.png) | Astra r1 finding 1 |
| G9b-room-switched-to-linked-update | A pick on the project from the menu bar (the open Room covers its icon at 1440 and the list at 393): the open Room switches to the latest published update (Old ledger frozen in its Progress), Slack #leads picked. | [1440](shots/G9b-room-switched-to-linked-update-1440.png) · [393](shots/G9b-room-switched-to-linked-update-393.png) | Astra r1 finding 1 |
| H1-decision-menu | 1440: right-click on the decision: Open, Send to ▸, then the rest. 393: the list row menu, opened by a touch long-press. | [1440](shots/H1-decision-menu-1440.png) · [393](shots/H1-decision-menu-393.png) | faces F1; Astra r1 finding 5 |
| H2-send-to-open | 1440: the submenu beside the panel, each destination with its channel word. 393: the submenu replaces the panel, the back row first. | [1440](shots/H2-send-to-open-1440.png) · [393](shots/H2-send-to-open-393.png) | design §3 |
| H2b-list-send-to | The list view at desktop width: the row menu with Send to ▸ open. | [1440](shots/H2b-list-send-to-1440.png) · [393](shots/H2b-list-send-to-393.png) | Astra r1 finding 2 (one composition) |
| H3-add-destination | Send to ▸ holds one row, Add destination. | [1440](shots/H3-add-destination-1440.png) · [393](shots/H3-add-destination-393.png) | Phase 10 B2 |
| H3b-add-destination-opens-form | Settings → Destinations with the add form open. | [1440](shots/H3b-add-destination-opens-form-1440.png) · [393](shots/H3b-add-destination-opens-form-393.png) | Phase 10 B2 |
| H4-note-withheld | The note's menu has no Send to ▸ (not a ghost row). | [1440](shots/H4-note-withheld-1440.png) · [393](shots/H4-note-withheld-393.png) | default 3; UX-CANON A.11 |
| H5-menu-bar-send-to | 1440: the Object menu, the decision selected, Send to ▸ right after Open. 393: the compact Go menu, the same entry. | [1440](shots/H5-menu-bar-send-to-1440.png) · [393](shots/H5-menu-bar-send-to-393.png) | Astra r1 finding 2 |
| H6-brief-row-send-to | The brief row (BRIEF <day>) in the list with Send to ▸ open. | [1440](shots/H6-brief-row-send-to-1440.png) · [393](shots/H6-brief-row-send-to-393.png) | default 6; Astra r1 finding 5 |
| H7a-read-loading | The meeting's summary read held loading: the row reads Send to · CHECKING and stays. | [1440](shots/H7a-read-loading-1440.png) · [393](shots/H7a-read-loading-393.png) | design §2 (pending is never a refusal) |
| H7b-read-failed | The read failed: Send to · CAN'T CHECK; the rows stay pickable. | [1440](shots/H7b-read-failed-1440.png) · [393](shots/H7b-read-failed-393.png) | design §2; UX-CANON A.10 |
| H7c-failed-pick-opens-window | Team folder picked on the failed read: the meeting window opens; its well tells the truth (a summary: the preview). | [1440](shots/H7c-failed-pick-opens-window-1440.png) · [393](shots/H7c-failed-pick-opens-window-393.png) | design §2 |
| I4-no-brief | Before any brief: no brief icon on the Floor (1440) and no brief row in the list (393). | [1440](shots/I4-no-brief-1440.png) · [393](shots/I4-no-brief-393.png) | default 6 |
| I1-brief-icon | 1440: the brief icon BRIEF <day> at the top of the column, selected. 393: the brief row in the list. | [1440](shots/I1-brief-icon-1440.png) · [393](shots/I1-brief-icon-393.png) | default 6 |
| I2-brief-opened | Intelligence → BRIEF on the exact stored id (read by id, GET /api/brief/{id}). | [1440](shots/I2-brief-opened-1440.png) · [393](shots/I2-brief-opened-393.png) | default 6; Astra r1 finding 4 |
| I3-brief-dropped | Intelligence → BRIEF with Slack #leads picked and the brief's preview. | [1440](shots/I3-brief-dropped-1440.png) · [393](shots/I3-brief-dropped-393.png) | default 6 |
| J1-artifact-window-well | The artifact window: the body, then SEND with the destinations; its three raw buttons are library Buttons. | [1440](shots/J1-artifact-window-well-1440.png) · [393](shots/J1-artifact-window-well-393.png) | faces F10; default 11 |
| J2-artifact-dropped-on-folder | Team folder picked; the preview is the stored body with the synthesis source footer left out. | [1440](shots/J2-artifact-dropped-on-folder-1440.png) · [393](shots/J2-artifact-dropped-on-folder-393.png) | default 11; design §4 |
| J2b-artifact-saved | He pressed Send: SAVED in the same well. | [1440](shots/J2b-artifact-saved-1440.png) · [393](shots/J2b-artifact-saved-393.png) | design §4 |

The art sheet heads `index.html`. At 393 a Floor-only board shows the phone's own face for the same intent: the list (F1, F3, F4, I1, I4), Settings at the row (F2, F2b, identical by design), or `Send to ▸` (F5, G1, G4–G4c).

## What the canvas draws beyond the design (settled here unless Astra or the owner objects)

1. **The tag at the right edge.** Every destination sits at the right edge, and the product's tag (`WorldStage.tsx:280`, `left: x + 14`) ran off the screen and wrapped onto four lines (seen on glass in round one). Drawn: within 280 px of the right edge the tag opens to the LEFT of the cursor and holds one line. A refusal tag (`NO SUMMARY`, `NO PUBLISHED UPDATE`, `PARKED`) wears the warning look, not the accent of an act, and does not light the target (G4–G4c). Story 04.
2. **Destination and brief icons are not Ask context.** Selecting one raised `1 SELECTED · Ask AI` (seen on glass); Ask has nothing to read on a destination. Drawn: the selection bar stays away while only those are selected (F2, I1). Story 04.
3. **`Send to ▸` sits right after Open** in every entry point: the spatial menu, the list row menu, the menu bar's Object menu and the compact Go menu (one composition; H1, H2b, H5). Round one's menu bar put it after Delete; fixed.
4. **The pending words sit on the `Send to` row:** `Send to · CHECKING` while the read loads, `Send to · CAN'T CHECK` on a failed read; the rows stay pickable (H7a, H7b). A pick on a failed meeting read opens the meeting window with the pick on its Summary, and the well tells the truth (H7c).
5. **Each destination row carries its channel word:** `Slack #leads · SLACK` (the species' quiet suffix).
6. **The brief icon heads the destination column** ("beside", design §5). The column lives in the strip right of the zone band. It tightens from 128 px down to 106 px a cell (a label's foot then meets the next sprite's head) before it wraps; past that it wraps into a second column to its LEFT, so no icon sits under the Dock (F5: the brief and six destinations fit one column). Round one wrapped at once and put the email icon on the Personal drawer (seen on glass); fixed.
7. **The art:** the decision is a gavel on its block, the brief a folded broadsheet with an orange masthead, and the channels a manila folder, a three-commit branch graph (GitHub), a notched ticket stub (Jira), a pinned board on a stand (Confluence), an envelope (email) and a speech bubble with a hash (Slack). No brand marks.

## Notes for stories 03 and 04 (found on glass; none fixed in product code)

- **N1 — the menu species takes a string label.** A submenu's label also names its panel for a screen reader (`web/src/desk/components/DeskMenu.tsx:638`: the panel's `aria-label` is `sub.label` + ` submenu`). Round one passed a React node and the panel was named `[object Object] submenu`. The canvas uses a string (`Send to · CHECKING`). The channel word on a destination row is drawn as the quiet suffix the ghost reason already uses. Story 03 should give `WorkMenuEntry` an optional `detail` (a quiet suffix) rather than pass markup as the label.
- **N2 — an open menu does not re-render when a read lands.** `objectMenuEntries` runs at render, so a `CHECKING` row stays `CHECKING` until the menu reopens (the pick still waits for the read and then opens the right window). Story 03: re-render the open menu on a read.
- **N3 — "latest published update" can tie.** Publishing a second update does not supersede the first, so two updates of one project can both be `published`. `published_at` is stored to the second (`holdspeak/db/updates.py:324`, `isoformat(timespec="seconds")`), and the list orders by `draft_revision DESC, created_at DESC` (`:195`), so two publishes in one second tie, and the tie falls to an order the query does not define. Seen on glass in round one: the canvas's "latest" was the FIRST of two updates published in the same second. The rig now publishes the second update 1.2 s later. Story 03 must pin the tie-break (for example `published_at DESC, rowid DESC`) in the read that names the update.
- **N4 — inherited:** the default grid puts the meeting "Vendor call" under the Reference drawer (zones are hit first), so it cannot be dragged where it lands; the rig placed it. The phone's selection bar wraps `1 SELECTED` onto two lines (H5 at 393). Ledger candidates, not this phase.
- **N5 — the rig, not the product:** Playwright's mouse cursor rests where the last click was, and a phone menu panel that opened under it took its hover intent and opened `Send to ▸` by itself. The rig parks the cursor before a long-press. The touch long-press itself swallows the lifting finger's click (`p12.ts`, 700 ms) and leaves the panel at its top level (checked with an event log).

## The owner's choice

One question: **Ratify the canvases F–J as drawn**, including the seven settled points above (the tag at the edge, icons outside Ask, `Send to` after Open, the pending words, the channel word, the brief atop a wrapping column, the art)? **Recommended: yes.**

## Measurements (`shots/facts.json`)

- Renders: **71** (36 at 1440, 35 at 393), each width on its own hub and HOME. Fence failures: **0**.
- Named elements on screen (in the viewport, inside every clipping ancestor, on top): **69 of 69**.
- Menu rows at 393 (the chrome strip rule: 44 px high, nine points owned, measured with elementFromPoint): **84 of 84**.
- Drop tags drawn: **4** (NO PUBLISHED UPDATE, NO SUMMARY, PARKED, Preview for Slack #leads); tags with the word Send: **0**; egress chips on a tag: **0**.
- Raw `<button>` in the proposal (menus, tag, artifact window): **0**. Text under 12 px in the proposal: **0**. Counters of zero: **0**. Modals: **0**. Horizontal overflow: **0**.
- Browser errors (page errors and console errors other than 4xx reads): **0**.
- The fences each board carries (`harness/shoot.py`, `shoot()`): the tag never says Send and carries no egress chip; the destination menu is `Open` only; a note's menu and a known-absent object's menu have no `Send to`; a second pick changes the pick in the same window; Summary → Digest keeps the destination; the Room shows the linked update; the brief well is on the handed id; the artifact preview has no synthesis footer; F3 draws no destination icon. H2b is a 1440-only board (the list at desktop width), so 393 has 35 renders.

## Limits (what the boards are not)

- The wire is the shim's statement of the design, not a server answer: the artifact renderer, the brief by id and the Fact reads' composition are the shim's; story 01 and story 03 build the real ones. A stand-in destination's preview is the folder render (Slack's text converted minimally), and its Send is a stand-in.
- The touch long-press is a harness listener on the list rows (story 03 builds it). The proof is CDP touch events on headless Chromium, not a phone.
- The positions the rig set (Vendor call, the decision) are per-browser positions he would make by dragging; nothing else moved.

## Reproduce

```bash
# from the worktree root; .venv with playwright and web/node_modules installed (npm ci).
.venv/bin/python pm/roadmap/holdspeak-philo/phase-12-send-from-the-floor/assets/story-02-canvas/harness/draw_sprites.py
PLAYWRIGHT_BROWSERS_PATH=$HOME/Library/Caches/ms-playwright \
  .venv/bin/python pm/roadmap/holdspeak-philo/phase-12-send-from-the-floor/assets/story-02-canvas/harness/shoot.py
.venv/bin/python pm/roadmap/holdspeak-philo/phase-12-send-from-the-floor/assets/story-02-canvas/harness/build_review.py
# the shots as committed: pngquant at quality 80-98 (the city backdrop made them 76 MB; checked side by side, no visible change)
pngquant --quality=80-98 --speed 1 --ext .png --force pm/roadmap/holdspeak-philo/phase-12-send-from-the-floor/assets/story-02-canvas/shots/*-1440.png pm/roadmap/holdspeak-philo/phase-12-send-from-the-floor/assets/story-02-canvas/shots/*-393.png
```

## Checks and ratification

- Astra's check: owed.
- The owner's word: owed (recorded verbatim here before story 03 or 04 commits a face change).
