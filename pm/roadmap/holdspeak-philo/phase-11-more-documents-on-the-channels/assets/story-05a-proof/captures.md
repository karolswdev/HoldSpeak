# PHILO-11-05a — the SEND well on the brief and decision faces: captures

Part A of story 05 (lane `feat/philo-11-05a`, base main `8a6b807d`). Part B
(the meeting faces, Destinations with Slack, the removals, the 22 face words)
and the story's evidence file and done flip belong to the sibling lane. This
file is progress evidence only. **No story status changes here.**

Built to the ratified canvases (story 03: boards A1–A6, B1–B5, T2, T3). The
species (`web/src/desk/surface/send/`) is unchanged; every face composes it.

## What changed

| Face | Seat | Document |
|---|---|---|
| Chair BRIEF section | `web/src/desk/chair/ChairHome.tsx:1397` (untriaged branch), `:1435` (the branch after the last item is triaged); both keyed `brief-send`, so the same well instance survives the branch change | `monday_brief:<id>` |
| Chair BRIEF head chip | `web/src/desk/chair/ChairHome.tsx:747-749` (`BriefHeadVerbs`: `PREPARED ×K` before the egress badge and Generate) | `monday_brief:<id>` |
| Intelligence → BRIEF | `web/src/desk/pullouts/views/BriefView.tsx:463` (after PEOPLE); one pick and press state with the Chair (the species' store) | `monday_brief:<id>` |
| The decision window | `web/src/desk/pullouts/DecisionPullout.tsx:150` (under the record, not while editing; the footer Copy, Dictate, Edit unchanged, R8) | `desk_decision:<id>` |
| Intelligence → DECISIONS | `web/src/desk/pullouts/views/DecisionsView.tsx:260` (after the record's fields) | `decision_record:<id>` |
| The Room's DECISIONS & COMMITMENTS rows | `web/src/features/project-room/ProjectRoomCore.tsx:1437` (`RoomDecisionRow`: unfolds in place, holds the well, carries `PREPARED ×K`); both row shapes at `:1500`, `:1528`; the dead `Open` withheld (G1), a row with a real URL keeps its Open (`:1542`) | `decision_record:<id>`, also for `source="meeting"` rows |

The document references and labels live in one place:
`web/src/desk/documentSends.tsx` (`briefDoc`, `deskDecisionDoc`,
`decisionRecordDoc`; labels `BRIEF <day>`, `DECISION <6>`, `D-<6>` as the
canvas drew them). `meeting_decision` has no face seat (design §6a).

Two web unit tests read "every h3 / every Retry in this section" and now
exclude the well's own (`[data-send]`):
`web/src/desk/__tests__/philo301DecisionFace.test.tsx:112-115`,
`web/src/desk/chair/__tests__/generateAlwaysReachable.philo401.test.tsx:195-198`.
The atlas source anchors that the inserted lines shifted are re-anchored
(pure line shifts, diff-mapped, symbol checked): `atlas.json` 17,
`atlas-phase7.json` 2, `atlas-phase8.json` 1, `atlas-phase9.json` 1.

## The glass (real hub, isolated HOME, 1440×900 and 393×852)

`tests/e2e/test_philo11_05a_brief_decision_send_glass.py`, machinery
`tests/e2e/_doc_send_glass.py` (ported from the canvas rig with `[data-send]`
for `[data-p11]`). Real producers: `POST /api/brief/generate`;
`POST /api/decisions` and `PUT /api/decisions/<id>`; the decision_capture
artifact through `ProposalBridgeService.bridge_meeting_artifacts` and
`POST /api/proposals/<id>/confirm` (the `MTG` record);
`DecisionRecordService.create_from_meeting` (the plain record, the service the
MCP tool calls); `channel.prepare` (`POST /api/channels/sends`) by a remote
agent credential issued through the real Settings route. Folder destinations
only: nothing leaves the machine.

Collect:

```
tests/e2e/test_philo11_05a_brief_decision_send_glass.py::TestBriefAndDecisionSendGlass::test_the_brief_well_on_the_chair_and_in_intelligence[1440]
tests/e2e/test_philo11_05a_brief_decision_send_glass.py::TestBriefAndDecisionSendGlass::test_the_brief_well_on_the_chair_and_in_intelligence[393]
tests/e2e/test_philo11_05a_brief_decision_send_glass.py::TestBriefAndDecisionSendGlass::test_the_decision_window_well_and_preview_changed[1440]
tests/e2e/test_philo11_05a_brief_decision_send_glass.py::TestBriefAndDecisionSendGlass::test_the_decision_window_well_and_preview_changed[393]
tests/e2e/test_philo11_05a_brief_decision_send_glass.py::TestBriefAndDecisionSendGlass::test_the_decision_record_wells_in_the_room_and_intelligence[1440]
tests/e2e/test_philo11_05a_brief_decision_send_glass.py::TestBriefAndDecisionSendGlass::test_the_decision_record_wells_in_the_room_and_intelligence[393]

6 tests collected in 0.03s
```

Run (`HOME=$(mktemp -d) HOLDSPEAK_EVIDENCE_WRITE=1 PLAYWRIGHT_BROWSERS_PATH=… uv run pytest -v tests/e2e/test_philo11_05a_brief_decision_send_glass.py`):

```
...::test_the_brief_well_on_the_chair_and_in_intelligence[1440] PASSED [ 16%]
...::test_the_brief_well_on_the_chair_and_in_intelligence[393] PASSED [ 33%]
...::test_the_decision_window_well_and_preview_changed[1440] PASSED [ 50%]
...::test_the_decision_window_well_and_preview_changed[393] PASSED [ 66%]
...::test_the_decision_record_wells_in_the_room_and_intelligence[1440] PASSED [ 83%]
...::test_the_decision_record_wells_in_the_room_and_intelligence[393] PASSED [100%]
======================== 6 passed in 154.46s (0:02:34) =========================
```

### Each face: its fence

- **Chair BRIEF (A1, A4, A4b, A4c).** A1: the well's `data-doc` is
  `monday_brief:<id>` of the generated brief; `NO DESTINATION` + Add
  destination. A4: head chip `◆ PREPARED ×1`. A4b: the agent's prepared row
  reads `◆ Ledger folder ◆ PREPARED BY REMOTE-PROJECT-AGENT BRIEF <day>` +
  `THIS DEVICE`; the hub's row has `document_ref == monday_brief:<id>`, state
  `prepared`. A4c: Send on the prepared row; the hub's row is `sent`, its
  `proof.path` exists in the Ledger folder, and the face's result row starts
  `· Ledger folder ✓ SAVED <that path> BY REMOTE-PROJECT-AGENT`; `SENDS 1`;
  the chip is gone (no counter at zero).
- **Intelligence → BRIEF (A2, A3).** The well's `data-doc` equals the brief's
  ref; the preview field is `FOLDER <team dir>`; the Chair's seat of the same
  brief shows the same pick (1 open row). Send: exactly one `sent` row for
  the Team folder, every hub row `document_ref == monday_brief:<id>`; the
  face's receipt is `✓ SAVED <hub proof.path>`; `SENDS 2`, the history row
  starts `✓ Team folder SAVED <path>`.
- **The decision window (B1, B2, B2b).** The window is 400 px at 1440; the
  footer still holds Copy, Dictate about this, Edit. Send: the hub has one row
  `(desk_decision:<id>, sent)`; its file holds `Nov 3`; the face's receipt is
  `✓ SAVED <path>`; `SENDS 1` = `✓ Team folder SAVED <path> <stamp(settled_at)>`.
  Nothing covers Send (the on-screen law's elementFromPoint at 3 points).
- **The Room (B4, B4b, B4c, B4d).** Two decision rows (`MTG` and `Decided`);
  the `MTG` row carries `◆ PREPARED ×1`; `Open` on the decision rows: `[0, 0]`.
  The agent's prepare of the MTG record answers `document_ref ==
  decision_record:<record id>` (never `meeting_decision:`). The row unfolds in
  place: the well's `data-doc` is `decision_record:<mtg id>`, the prepared row
  starts `◆ Team folder ◆ PREPARED BY REMOTE-PROJECT-AGENT D-<6>`. Send: the
  hub's row is that send, `sent`, its file holds the record's text; the face
  shows `· Team folder ✓ SAVED <path>`, `SENDS 1`. The plain row unfolds, picks,
  sends: the hub has `(decision_record:<plain id>, sent)` and the face's
  receipt is `✓ SAVED <its path>`.
- **Intelligence → DECISIONS (B5, B5b).** The well's `data-doc` is
  `decision_record:<plain id>`; the verb is `Send again` (the Room's send of
  the same record); Send makes one new `sent` row; `SENDS 2` shows its path.

### The transitions

- **T2 (decision window, both widths).** He reads the preview (`Nov 3`); the
  decision changes through `PUT /api/decisions/<id>` (`Nov 6`); Send answers
  `✗ REFUSED PREVIEW CHANGED NOTHING SENT` (`data-code=preview_changed`), never
  NO ANSWER; the well reads a fresh preview (the `Nov 6` passage on screen,
  board T2a2); the hub still has exactly one `sent` row (the refused press sent
  nothing); another press sends: one new `sent` row, and the file's Decision
  section holds `Nov 6` and not `Nov 3`; the face's receipt equals `✓ SAVED
  <that path>`.
- **T3 (Chair, both widths).** All brief items but one handled through the real
  shelf route; the Chair shows `1 THING WAITING`; the Team folder row is open
  with its receipt. Ack pressed on glass: the Chair changes branch (the Ack is
  gone; the headline/handled line shows). The receipt read before and after
  is identical and equals the hub's send row:
  `latest = ✓ SAVED <hub proof.path>`, `state = sent`,
  `row chip = ✓ SAVED <HH:MM of settled_at>`,
  `history = ✓ Team folder SAVED <path> <stamp(settled_at)>` (recorded on the
  board as `receipt_before`, `receipt_after`, `hub_row`). At the same scroll
  seat, T3a2 and T3b2 are the same pixels with the clock masked (declared, not
  a failure). T3c: the mouse wheel over the page brings the history row out
  from under the capture bar; the receipt is unchanged after the scroll.

### The laws on every board (round one: 46 boards; the final inventory is in "Inventory (final)" below)

- Named elements on screen (viewport, every clipping ancestor, on top): **78 of 78**.
- Pointer (nine points, elementFromPoint and a real pointer move; the 44 × 44
  target at 393): **83** well controls owned, **8** of them after ordinary
  scrolling from under the host's sticky bar (the wheel over the page), **0**
  missed. At 393: 38 controls, smallest target 44 px.
- Rows in the one grammar: **136 of 136**. Text the well adds under 12 px: **0**.
  Raw `<button>` in the well: **0**. Modals: **0**. Horizontal overflow: **0**.
  Stale-version words: **0**. Mark delivered on a new kind: **0**. `Open` on a
  Room decision row: **0**. Page errors: **0**. Identical shots (clock masked):
  only the declared T3a2/T3b2 pair.

### The heading at 393 (A4) — round two, Muad'Dib's ruling 1

Round one found the chip staying on the label's line at 393 (the library's
item-by-item wrap). Ruling: build what was ratified, in the host. The BRIEF
head's actions are now ONE element (`web/src/desk/chair/ChairHome.tsx:728-749`,
`.arrival-brief-verbs`), styled in `web/src/desk/chair/chair.css` (tail). Round
three moved this into `BriefHeadVerbs` (`web/src/desk/documentSends.tsx`) and
`web/src/desk/documentSends.css`, see below: with no PREPARED send the verbs
render as before (no wrapper); with one, the chip and the verbs are one flex item, so it sits beside the label
when it fits and otherwise wraps as a whole under the label, spread across the
line (the label out-grows the group 1000:1 on a shared line). No library
change, no width query.

Facts (`A4-brief-prepared-chair-*.json`, `head`):

- 393: label `BRIEF · 2 THINGS WAITING`, 12 px, one line; `chip_below_label:
  true`, `generate_below_label: true` (the fence asserts both: the chip's top
  is below the label's bottom). The shot shows `◆ PREPARED ×1`, `THIS DEVICE`,
  Generate on the line under the label, left / centre / right, as canvas A4.
- 1440: `chip_right_of_label: true`, `generate_below_label: false`; the shot
  is the round-one layout (chip, badge, Generate packed at the right of the
  label line).

## The brief's generated time — ruling 2

`holdspeak/services/document_sources.py:60-74` (`_time_text`) and `:132`: the
brief document now says `Generated: 30 Sep 2026, 08:25` (the stored clock, no
zone change; an unparsable value is shown as stored). The preview and the sent
bytes both come from this one document. Fences:

- `tests/unit/test_philo11_document_sources.py:69-73`: the `Generated:` line
  matches `\d{1,2} Mon YYYY, HH:MM`, and the brief holds no ISO `T` and no
  microseconds. Red on the old line (`AssertionError: Generated:
  2026-09-29T10:00:00`, 1 failed, 19 passed); green now: `20 passed`.
- The glass (A4b/A4c): the prepared preview on the Chair shows the readable
  line with no `T` and no microseconds, and the sent file's `Generated:` line
  equals the preview's.

## The rig, round two

- The pointer pass's wheel now goes over a point whose scroller is the
  control's OUTERMOST scroller (the Chair, the window body). Round one wheeled
  over the page's middle, which at 393 could land on a nested preview
  scroller and move the control inside it instead of out from under the bar.
- The browser runs with `--disable-smooth-scrolling`, and the probe waits
  until the control stands still after each wheel step.

Run (round two, isolated HOME, `HOLDSPEAK_EVIDENCE_WRITE=1`): `6 passed in
153.67s`. Laws (round two, 46 boards): named 78/78; 83 controls owned, 8 after ordinary
scrolling, 0 missed; 393 minimum target 44 px (38 controls); rows 136/136.

## Round three — Astra counsel r1 (story 05) findings 2 and 4

### Finding 2: the bundle gate

The overrun was not lane CSS: the eager Desk faces (the Chair, Intelligence,
the decision window) imported the SEND well species, which pulled
`send-well.css` (5,594 B) and `channels.css` (2,811 B) into the Desk entry
chunk. Fix, without touching the ratchet:

- `web/src/desk/documentSendsLazy.tsx`: every seat loads the wells through
  `React.lazy` + `Suspense` (fallback: nothing; the brief head's fallback is
  its verbs as they were). The species and its CSS ride their own chunk
  (`documentSends-*.css`, `documentSends-*.js`).
- The A4 group rules moved out of `chair.css` (now byte-identical to base)
  into `web/src/desk/documentSends.css`, loaded with that chunk: the group
  exists only when a prepared send is shown, which only the lazy module draws.
- Hosts import from `documentSendsLazy`: ChairHome, BriefView,
  DecisionPullout, DecisionsView, ProjectRoomCore.

```
bundle gate passed (Desk JS 1336735 B; Desk CSS 324838 B; source maps 0)
```

Desk CSS delta over base (324,838 B): **0 B**.

### Finding 4: face = row = receipt, B3, A5

- Every face leg now reads the kernel's own record of the send operation
  (`kernel_operations` + `kernel_receipts`, by the row's `send_operation_id`):
  name `channel.send`, state and receipt `succeeded`, exactly one receipt,
  `result_ref == channel_send:<row id>`, `target_ref == document:<ref>` (or the
  prepared send), principal `owner` — beside the hub row and the face's text.
  Prepared rows also read their `channel.prepare` receipt (succeeded, principal
  `remote-project-agent`). T2's refused press reads its receipt: `refused`,
  outcome `preview_changed`, `target_ref == document:desk_decision:<id>`.
  Legs: A4c, A3, A5, T3 (brief); B2, B3, T2 (decision window); B4c, B4d, B5
  (records). Recorded on the boards as `kernel_send` / `kernel_prepare` /
  `kernel_refusal`.
- **B3** (both widths): Edit on glass unmounts the well (it sends the stored
  decision); Done stores the edit (Nov 5) and mounts it again; the preview
  shows Nov 5 (board B3), the verb is `Send again`; the press sends a file
  whose Decision section holds Nov 5 and not Nov 3 (board B3b); T2 then runs
  from Nov 5 to Nov 6.
- **A5** (both widths): an agenda item for Priya's 1:1 (the routes BriefView's
  "Add to 1:1 agenda" uses) changes the brief's People section, which is
  read at render time; a same-day `POST /api/brief/generate` returns the same
  brief id; the well's fresh preview holds `Priya Nair` (board A5), the verb is
  `Send again` (board A5b); the press sends a file with `Priya Nair`, and the
  first send's file does not have it.
- A6 (the Slack preview's person sections) waits for #710 with C6b.

Run (isolated HOME, `HOLDSPEAK_EVIDENCE_WRITE=1`): 6 collected, `6 passed in
172.05s`. Laws (round three, 54 boards): named 88/88; 93 controls owned, 8 after ordinary scrolling, 0 missed; 393 minimum target 44 px (43 controls); rows 182/182; kernel records on boards: 22.

## Round four — after #710 merged (C6b, A6, the done flip)

- **C6b**: `MeetingSendWellLazy` (part B's, on main) mounts in
  `ArrivalMeetingWells` (`web/src/desk/chair/ChairHome.tsx`) whenever the row
  shows a summary: the healthy slab AND the retained summary with its status
  facts. No summary, no well. The retained branch is produced by the intel
  queue's own `enqueue_intel_job` -> `claim_next_intel_job` -> `fail_intel_job`
  (FAILED · LAST ERROR · ENGINE ANSWERED 500 on the row; board C6e).
  The Chair send leg (C6c): the hub has `(meeting_summary:c6-sync, sent)`,
  the face's receipt is `✓ SAVED <its path>`, and the kernel operation is
  `channel.send` succeeded with one receipt.
- **Chair picker at 393 (G4)**: the Summary/Digest/Follow-up picker is a
  SELECT 104 x 44 px. The rig scrolls the Chair so the picker sits UNDER the
  capture bar (`elementFromPoint` at its centre = `arrival-capture-bar`), then
  wheels the Chair: 2 wheel steps bring it out, and all nine points of its
  44 x 44 target are owned by elementFromPoint AND a real pointer move (fact
  `picker_after_scroll` on `C6b-chair-meetings-row-well-393`; board C6f).
- **A6**: a Slack destination saved through the real routes
  (`POST /api/channels/slack-webhooks`, then the destination) on part B's
  memory key store and recording HTTPS edge. With an agenda item on Priya's
  1:1 and one brief item acknowledged, the Slack-text preview carries
  `*People*` / `*Priya Nair*` / `- Agenda: 1` and no ACKNOWLEDGED, DEFERRED,
  Ack or Defer mark; the person line itself is on screen (range fence). Send:
  exactly one request to `hooks.slack.com`, its `text` equal (whitespace
  normalized) to the preview; the face `✓ POSTED #leads`, no link; the hub
  row `sent`; the kernel receipt succeeded. The webhook never appears in the
  page or the row.
- **Generated docs**: `philo_api_reference.py`, `philo_boundary_census.py`,
  `philo_graph_reference.py` regenerated; all 13 Documentation Navigation
  commands (and `gen_operations_json --check`, `philo_openapi_reference
  --check`) exit 0.

### Inventory (final, this head)

- `shots/`: **65 boards** = 32 boards at both widths + 1 at 393 only
  (`C6f-chair-picker-scrolled-clear`); **65 PNG files** (one per board and
  width) and **8 facts files** (`brief-send`, `decision-send`, `record-send`,
  `chair-meetings-slack`, each `-1440.json` and `-393.json`): **73 files**.
- Laws over the 65 boards: named elements on screen **105/105**; **130**
  well controls owned, **13** of them after ordinary scrolling, **0** missed;
  at 393 the smallest target is **44 px** (60 controls); rows in the one
  grammar **244/244**; **26** kernel records (send, prepare, refusal)
  recorded on boards.
- Earlier counts in this file (46, 54) are the inventories of rounds one to
  three; they are superseded by this one.
- Looked at: every board of rounds one to three at the time (re-rendered in
  this run by the same code), and in this round C6b, C6c, C6e (both widths),
  C6f, A6 and A6b (both widths).

## Web baseline

```
=== Web baseline report ===
HEALED (5): (inherited reds that pass; unchanged by this lane)
Suite totals: 2995 passed, 0 failed, 0 skipped   (rounds one, two and three)
VERDICT: baseline-subset, zero branch-new
```

## Scoped guards

- `tests/unit/test_philo4_01_atlas_contracts.py`, `test_hs169_room_copy.py`,
  `test_philo_graph_atlas.py`, `test_phase143_surface_fallback_census.py`,
  `test_native_surfaces_guard.py`: `128 passed in 4.04s` (5 failed before the
  atlas re-anchor: pure line shifts). Round two: 6 more `atlas.json` anchors
  in `ChairHome.tsx` re-anchored; these guards with the doc guards, the graph
  schema, the evidence guard and the document-source test: `255 passed`;
  all `test_philo11*.py`: `65 passed`. Round three (6 more `atlas.json`
  anchors re-pointed): the same set `300 passed`.
- `test_doc_drift_guard.py`, `test_phase200_canon_guard.py`,
  `test_phase200_doc_claims.py`: `86 passed in 5.43s`.
- `test_philo_graph_schema.py`: `19 passed`; `scripts/philo_graph_validate.py
  docs/generated/graph.json`: `OK`.
- `test_evidence_scratch_guard.py`: `2 passed`.
- `web: npx tsc --noEmit`: clean.

## Shots (`shots/`, each at -1440 and -393)

A1-brief-chair-no-destination, A4-brief-prepared-chair,
A4b-brief-prepared-row, A4c-brief-prepared-saved, A2-brief-picked-folder,
A3-brief-saved-history, T3a-chair-last-item, T3a2-chair-last-item-receipt,
T3b-chair-after-last-ack, T3b2-chair-after-last-ack-receipt,
T3c-scrolled-clear-of-capture-bar, B1-decision-window-picked, B2-decision-saved,
B2b-decision-history, T2a-preview-changed-fresh-preview,
T2a2-preview-changed-passage, T2b-preview-changed-sent,
B4-room-row-prepared-chip, B4b-room-row-open-prepared,
B4c-room-row-prepared-saved, B4d-room-plain-row-saved,
B5-record-intelligence-picked, B5b-record-intelligence-history.

## Not in this lane / owed

- **C6b (the Chair's MEETINGS row well)** mounts part B's `MeetingSendWell`
  (PR #710, not merged when this lane ran). The mount in `ChairHome.tsx`
  after that row's `MeetingSummarySlab` is a follow-up commit after #710 merges.
- **A6** (the brief's person sections in a Slack preview) needs a Slack
  destination: after #710 merges, with C6b (mounting `MeetingSendWellLazy` in
  both Chair MEETINGS branches, with the picker's 44 px ownership fence).
- Temp HOMEs: the 32 `$TMPDIR/tmp.*` HOMEs this worktree left (identified by
  the `wt-philo-11-05a` interpreter path in their uv cache) are removed; 25
  with no such mark were left alone (not provably this lane's).
