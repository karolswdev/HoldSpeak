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
| Chair BRIEF section | `web/src/desk/chair/ChairHome.tsx:1394` (untriaged branch), `:1432` (the branch after the last item is triaged); both keyed `brief-send`, so the same well instance survives the branch change | `monday_brief:<id>` |
| Chair BRIEF head chip | `web/src/desk/chair/ChairHome.tsx:734` (`PREPARED ×K`, before the egress badge and Generate) | `monday_brief:<id>` |
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

### The laws on every board (46 boards, `shots/*-{1440,393}.json`)

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

### The heading at 393 (A4) — what the glass shows

Facts (`A4-brief-prepared-chair-393`): label `BRIEF · 2 THINGS WAITING`, 12 px,
**one line**; `THIS DEVICE` and Generate wrap **under** the label; Generate
76 × 24 painted, owned on its 44 px target. **The chip `◆ PREPARED ×1` stays on
the label's line** (`chip_right_of_label: true`, `chip_below_label: false`).
Canvas A4 at 393 drew the chip under the label as well. The cause is the
library's intrinsic head rule (`web/src/desk/surface/surface.css:81-88`,
`flex-wrap` item by item): the chip alone fits beside the label, so only the
items after it wrap. The canvas harness had a viewport rule that gave the
label the full line (`story-03-canvas/harness/species.css:156-163`), which the
kit may not use. **Not changed here** (a species rule, out of this lane);
reported to Muad'Dib. The fence asserts what holds (the label whole on one
line, nothing overlapping it, the verbs under it at 393) and records the chip
fact on the board.

## Web baseline

```
=== Web baseline report ===
HEALED (5): (inherited reds that pass; unchanged by this lane)
Suite totals: 2995 passed, 0 failed, 0 skipped
VERDICT: baseline-subset, zero branch-new
```

## Scoped guards

- `tests/unit/test_philo4_01_atlas_contracts.py`, `test_hs169_room_copy.py`,
  `test_philo_graph_atlas.py`, `test_phase143_surface_fallback_census.py`,
  `test_native_surfaces_guard.py`: `128 passed in 4.04s` (5 failed before the
  atlas re-anchor: pure line shifts).
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
- **A5/A6 (brief changed / Slack person sections)** and **B3 (Edit after a
  send)** were not re-fenced here: they need a Slack destination (part B) or
  repeat T2's mechanism; T2 covers "changed → fresh preview → another press".
- **The heading chip at 393** (above).
- Seen, not this lane's: the brief's Markdown shows `Generated:
  2026-09-30T07:59:49.670256` raw (story 01's renderer).
