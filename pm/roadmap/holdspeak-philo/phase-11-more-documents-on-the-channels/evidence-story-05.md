# Evidence - PHILO-11-05

- **Story:** PHILO-11-05 - The faces: the well on every document, Destinations with Slack
- **Status:** done
- **Date:** 2026-09-30

## Reading guide: part B (Muad'Dib's Fedaykin lane, Opus 5.5)

Story 05 was split into two lanes. Part B (merged, #710) is the meeting faces,
Destinations with Slack, the removal of the old Slack rows, and the face
words. Part A (#711) holds the done flip, after #710 merged.

- **Meetings record (C1-C5, C4, T1)**: `web/src/pages/cores/history/MeetingDetail.tsx`
  mounts `web/src/meetings/MeetingSendWell.tsx` under SUMMARY, and only when the
  meeting has a summary. It is ONE well with a library CycleGadget that picks
  Summary, Digest or Follow-up (`meeting_summary:` / `meeting_digest:` /
  `meeting_followup:<id>`).
- **Meeting window (C6)**: `web/src/desk/pullouts/MeetingPullout.tsx`, after the summary and topics.
- **Chair MEETINGS row (C6b)**: mounted by part A after #710 merged (see part A below).
- **Destinations with Slack (D1-D4)**: `web/src/pages/cores/connections/Destinations.tsx`.
  The webhook SecretRow saves through `POST /api/channels/slack-webhooks`, and
  the hub mints the key_ref. The Channel name label fills in the name. The chip
  is HOOKS.SLACK.COM. A bad webhook gives KEY NOT SAVED · WEBHOOK NOT VALID.
  Check gives WEBHOOK SET · HOST OK and makes no post.
- **Removed from the face**: the aftercare DIGEST → SLACK and FOLLOW-UP →
  SLACK mount, the Credentials "Slack webhook" label, and the free-text desk
  Slack verb (`web/src/desk/contextual.ts`). `AftercareGadgets.tsx` is
  PARKED (unmounted, unexported), not deleted: the sealed graph passes cite its
  path (`tests/unit/test_philo_graph_reference.py::test_committed_join_validates`
  goes red when the file is deleted).
- **Face words**: the 20 pairs that were still missing now have words in
  `web/src/features/channels/channels.ts`. The other 2 of the 22
  (`[refused, slack_webhook_invalid]` and `[refused, slack_webhook_missing]`)
  were already worded by story 04. `test_every_emitted_code_has_a_face_word` is green.
- **Glass**: `tests/e2e/test_philo11_05b_meeting_faces_glass.py`, real hub on
  an isolated HOME, a memory Slack key store and a recording HTTPS edge (no
  real Slack). The shots are in `assets/story-05b-shots/`, and the facts are in
  `meeting-faces-<width>.json`.
- **Named deviation (Muad'Dib's ruling on #710)**: the `✓ WEBHOOK SET` chip on
  a Slack row inside a SEND well (C1) is withheld, because the list must not read
  the secret per row. It is recorded for the owner in the story notes and in
  `assets/story-05b-shots/README.md`.

- **Astra counsel r1 (DO-NOT-RATIFY, `checks/story-05-built-astra-r1.md`), part B paid**:
  F1: Edit never says SET while the webhook is unknown. It offers Check, and a
  Check that finds none shows NO WEBHOOK. The red is in `assets/story-05b-logs/edit-set-red.txt`,
  and the glass board is D5. F2: the meeting well is lazy-loaded
  (`web/src/meetings/MeetingSendWellLazy.tsx`) and has no CSS of its own, so the
  Desk CSS is 324,838 B, equal to the base. F4: the meeting window presses Send
  (C6d); the follow-up's face target equals the hub's `file_path`; C5c is the
  digest body again (the posted result is C5d); every send leg reads its kernel
  receipt. T1's preview is admission-exempt, so it has no receipt, and its fence
  counts zero new egress operations.

## Reading guide: part A (Muad'Dib's Fedaykin lane, Opus 5.5)

Part A (#711) is the brief and decision faces, C6b on the Chair's MEETINGS
rows, A6, and this flip. The full part-A record (rounds one to four, every
board, every fact) is `assets/story-05a-proof/captures.md`; the shots are in
`assets/story-05a-proof/shots/` with their facts in `*-<width>.json`.

- **The seats** (the species unchanged; one reference file
  `web/src/desk/documentSends.tsx`, loaded on demand through
  `web/src/desk/documentSendsLazy.tsx`, so the Desk CSS stays at base):
  the Chair BRIEF section in both branches and its head chip (`monday_brief:<id>`);
  Intelligence -> BRIEF (the same pick and press as the Chair); the decision
  window (`desk_decision:<id>`); Intelligence -> DECISIONS and the Room's
  DECISIONS & COMMITMENTS rows (`decision_record:<id>`, also on
  `source="meeting"` rows; the Room row unfolds in place; its dead Open is
  withheld, G1); the Chair's MEETINGS rows in both summary branches
  (`MeetingSendWellLazy`, C6b). `meeting_decision` has no seat (design 6a).
- **A4 at 393**: the chip, THIS DEVICE and Generate are one group
  (`BriefHeadVerbs`) that wraps whole under the label; 1440 unchanged.
- **The brief's generated time** reads `30 Sep 2026, 09:02` in the preview
  and the sent bytes (`holdspeak/services/document_sources.py` `_time_text`).
- **Glass**: `tests/e2e/test_philo11_05a_brief_decision_send_glass.py`, 8
  tests (4 x 1440/393), real hub, isolated HOME, real producers, part B's
  memory Slack key store and recording HTTPS edge. Every send leg: face = hub
  row = kernel operation and its one receipt. T2 (refused `preview_changed`
  receipt, fresh preview, another press), T3 (the same receipt before and
  after the Chair's branch change, equal to the hub row), B3 (Edit, remount,
  Send again), A5 (same brief id, new People words, Send again), A6 (the Slack
  text with the People section and no Ack/Defer mark, POSTED with no link, the
  posted bytes equal the preview), C6b (both branches; at 393 the picker is
  44 px, scrolled under the capture bar and brought out by the wheel, owned on
  all nine points).
- **Bundle gate**: Desk CSS 324,838 B = base; the ratchet is untouched.
- **Generated docs**: regenerated; every Documentation Navigation command passes.
- **Shots this flip ships**: part A's `assets/story-05a-proof/shots/` (65
  boards: 65 PNG + 8 facts files; the inventory is in captures.md) and part
  B's `assets/story-05b-shots/` re-rendered by the part-B capture below on
  this tree. Part A looked at C6b, C6c, C6e, C6f, A6, A6b in this round and
  every other A board in earlier rounds; of part B's re-renders it looked at
  T1-393, C6d-1440, D5-393, C1-393, D3-393 and C3-393 (part B's lane looked at
  all of its boards on #710). T1-393 still shows the inherited Meetings-window
  footer overlap (G5, ledgered).

## Named deviation

- The `✓ WEBHOOK SET` chip on a Slack row inside a SEND well (canvas C1) is
  withheld: the destination list does not read the secret per row (Muad'Dib's
  ruling on #710; `assets/story-05b-shots/README.md`). Destinations' own row
  and Check still say WEBHOOK SET / NO WEBHOOK from a real read.

## Acceptance criteria, as met

- Every ratified board built and fenced through the real hub at 1440 and 393;
  the face's outcome equals the hub record and its kernel receipt (A: every
  send leg; B: every send leg).
- Each face sends its own `document_ref`; the prepared rows' refs are read
  (brief, decision record incl. `source="meeting"`, meeting digest).
- T1 (B: the real size and limit, never NO ANSWER), T2 and T3 (A) at both widths.
- The 22 face-word pairs (B, `test_every_emitted_code_has_a_face_word`).
- No verb offers the parked free-text Slack send (B, `contextual.test.ts`).
- Nothing covers Send at 393 or in the real 400 px decision and 640 px Meetings windows at 1440 (A, B).
- A Slack destination saved from the form; the webhook never shown again; POSTED with no link (B; A6).
- No DIGEST -> SLACK row and no Slack webhook Credentials row (B).
- Every verb the library Button; the egress chip on each leaving row; no modal; web baseline zero branch-new.

## Proof

All captures below ran on part A's merged tree (main 4c8f0e05 merged in).
The Documentation Navigation capture runs a local wrapper that invokes, each
with an isolated HOME, the 13 commands its output lists (the CI job's 11 plus
`gen_operations_json.py --check` and `philo_openapi_reference.py --check`).

### Captured run — 2026-09-30T18:04:23Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.K8dgaOekvd HOLDSPEAK_EVIDENCE_WRITE=1 PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm uv run pytest -q -p no:cacheprovider tests/e2e/test_philo11_05b_meeting_faces_glass.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 2c860456fa8df293e1bc86ee88a78754cb4fae50

```text
..                                                                       [100%]
2 passed in 109.89s (0:01:49)
```

### Captured run — 2026-09-30T18:06:20Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.WgejjGG25Y HOLDSPEAK_EVIDENCE_WRITE=1 PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm uv run pytest -q -rA -p no:cacheprovider tests/e2e/test_philo11_05a_brief_decision_send_glass.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 2c860456fa8df293e1bc86ee88a78754cb4fae50

```text
........                                                                 [100%]
==================================== PASSES ====================================
_ TestBriefAndDecisionSendGlass.test_the_brief_well_on_the_chair_and_in_intelligence[1440] _
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
_ TestBriefAndDecisionSendGlass.test_the_brief_well_on_the_chair_and_in_intelligence[393] _
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
_ TestBriefAndDecisionSendGlass.test_the_decision_window_well_and_preview_changed[1440] _
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
_ TestBriefAndDecisionSendGlass.test_the_decision_window_well_and_preview_changed[393] _
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
_ TestBriefAndDecisionSendGlass.test_the_decision_record_wells_in_the_room_and_intelligence[1440] _
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
_ TestBriefAndDecisionSendGlass.test_the_decision_record_wells_in_the_room_and_intelligence[393] _
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
_ TestChairMeetingsAndBriefToSlack.test_the_chair_meeting_wells_and_the_brief_to_slack[1440] _
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
_ TestChairMeetingsAndBriefToSlack.test_the_chair_meeting_wells_and_the_brief_to_slack[393] _
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
=========================== short test summary info ============================
PASSED tests/e2e/test_philo11_05a_brief_decision_send_glass.py::TestBriefAndDecisionSendGlass::test_the_brief_well_on_the_chair_and_in_intelligence[1440]
PASSED tests/e2e/test_philo11_05a_brief_decision_send_glass.py::TestBriefAndDecisionSendGlass::test_the_brief_well_on_the_chair_and_in_intelligence[393]
PASSED tests/e2e/test_philo11_05a_brief_decision_send_glass.py::TestBriefAndDecisionSendGlass::test_the_decision_window_well_and_preview_changed[1440]
PASSED tests/e2e/test_philo11_05a_brief_decision_send_glass.py::TestBriefAndDecisionSendGlass::test_the_decision_window_well_and_preview_changed[393]
PASSED tests/e2e/test_philo11_05a_brief_decision_send_glass.py::TestBriefAndDecisionSendGlass::test_the_decision_record_wells_in_the_room_and_intelligence[1440]
PASSED tests/e2e/test_philo11_05a_brief_decision_send_glass.py::TestBriefAndDecisionSendGlass::test_the_decision_record_wells_in_the_room_and_intelligence[393]
PASSED tests/e2e/test_philo11_05a_brief_decision_send_glass.py::TestChairMeetingsAndBriefToSlack::test_the_chair_meeting_wells_and_the_brief_to_slack[1440]
PASSED tests/e2e/test_philo11_05a_brief_decision_send_glass.py::TestChairMeetingsAndBriefToSlack::test_the_chair_meeting_wells_and_the_brief_to_slack[393]
8 passed in 206.48s (0:03:26)
```

### Captured run — 2026-09-30T18:09:59Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.F3grdtOZrr uv run pytest -q -n auto -p no:cacheprovider tests/unit/test_philo10_face_words.py tests/unit/test_philo_graph_reference.py tests/unit/test_api_surface.py tests/integration/test_history_slack_surfaces.py tests/integration/test_web_history_archive.py tests/integration/test_philo11_slack_rewrite.py tests/integration/test_web_slack_export.py tests/integration/test_actuator_presence_broadcasts.py tests/unit/test_philo4_01_atlas_contracts.py tests/unit/test_hs169_room_copy.py tests/unit/test_philo_graph_atlas.py tests/unit/test_phase143_surface_fallback_census.py tests/unit/test_native_surfaces_guard.py tests/unit/test_doc_drift_guard.py tests/unit/test_phase200_canon_guard.py tests/unit/test_phase200_doc_claims.py tests/unit/test_philo_graph_schema.py tests/unit/test_evidence_scratch_guard.py tests/unit/test_philo11_channel_contract.py tests/unit/test_philo11_document_sources.py tests/unit/test_philo11_slack_channel.py tests/unit/test_docs_navigation.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 2c860456fa8df293e1bc86ee88a78754cb4fae50

```text
bringing up nodes...
bringing up nodes...

........................................................................ [ 19%]
........................................................................ [ 39%]
........................................................................ [ 58%]
........................................................................ [ 78%]
........................................................................ [ 97%]
........                                                                 [100%]
=============================== warnings summary ===============================
tests/unit/test_evidence_scratch_guard.py::test_no_test_writes_into_tracked_evidence
  tests/e2e/test_hs202_05_first_use_type_floor.py:260: SyntaxWarning: invalid escape sequence '\s'
    ? '.' + el.className.trim().split(/\s+/)

tests/unit/test_evidence_scratch_guard.py::test_no_test_writes_into_tracked_evidence
  tests/e2e/test_hs202_05_first_use_type_floor.py:439: SyntaxWarning: invalid escape sequence '\('
    const m = /rgba?\(([^)]+)\)/.exec(s || '');

tests/unit/test_evidence_scratch_guard.py::test_no_test_writes_into_tracked_evidence
  tests/e2e/test_philo9_03_room_face_glass.py:807: SyntaxWarning: invalid escape sequence '\s'
    face = row.evaluate("""r => ({text: r.innerText.replace(/\s+/g, ' ').trim(),

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
368 passed, 3 warnings in 11.72s
```

### Captured run — 2026-09-30T18:10:12Z

- **Command:** `sh -c cd web && npx vitest run src/features/channels/__tests__/slackDestination.test.tsx src/features/channels/__tests__/resendProvider.test.tsx src/desk/__tests__/contextual.test.ts src/desk/components/DeskToolInspector.test.tsx src/desk/__tests__/philo301DecisionFace.test.tsx src/desk/chair/__tests__/generateAlwaysReachable.philo401.test.tsx src/desk/surface/send src/features/channels/__tests__/SendWell.test.tsx`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 2c860456fa8df293e1bc86ee88a78754cb4fae50

```text

 RUN  v4.1.9 /Users/karol/dev/tools/wt-philo-11-05a/web


 Test Files  9 passed (9)
      Tests  76 passed (76)
   Start at  12:10:12
   Duration  1.69s (transform 2.53s, setup 1.17s, import 4.85s, tests 1.80s, environment 4.01s)
```

### Captured run — 2026-09-30T18:10:20Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.kKqI8ZVdlc npm_config_cache=/Users/karol/.npm uv run python scripts/check_web_baseline.py --run`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 2c860456fa8df293e1bc86ee88a78754cb4fae50

```text
Running vitest...

=== Web baseline report ===

HEALED (5):
  src/desk/__tests__/containerQueryLaw.test.ts > HS-129-06 container-query law > keeps viewport-width media limited to shell exceptions
  src/desk/__tests__/writeReceiptGuard.test.ts > HS-132-06 swallowed-write guard > keeps every desk write out of a bare catch
  src/desk/components/InlineEditor.test.tsx > HS-129-08 editor windows > hosts note editing in its open pullout
  src/desk/components/MicButton.test.tsx > MicButton surfaces named refusals (HS-132-05) > never claims retention the session cannot prove
  src/desk/components/__tests__/workbenchAutomations.test.tsx > Workbench STARTS WHEN automations > tests without delivering work, then enables and pauses the trigger

Suite totals: 3004 passed, 0 failed, 0 skipped

VERDICT: baseline-subset, zero branch-new
```

### Captured run — 2026-09-30T18:10:55Z

- **Command:** `sh -c cd web && npm run build >/dev/null 2>&1 && node scripts/check-bundle.mjs`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 2c860456fa8df293e1bc86ee88a78754cb4fae50

```text
bundle gate passed (Desk JS 1337153 B; Desk CSS 324838 B; source maps 0)
```

### Captured run — 2026-09-30T18:11:00Z

- **Command:** `bash /private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/6dfcd5d2-da69-4f97-aded-020cd82d0379/scratchpad/docnav.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 2c860456fa8df293e1bc86ee88a78754cb4fae50

```text
0 -m unittest discover -s tests/unit -p test_docs_navigation.py
0 scripts/check_docs.py
0 scripts/philo_repository_census.py --check
0 scripts/philo_api_reference.py --check
0 scripts/philo_boundary_census.py --check
0 scripts/philo_doctor_reference.py --check
0 scripts/philo_config_reference.py --check
0 scripts/philo_graph_reference.py --check
0 scripts/validate_architecture.py
0 scripts/generate_capability_docs.py --check
0 scripts/check_doc_coverage.py --check
0 scripts/gen_operations_json.py --check
0 scripts/philo_openapi_reference.py --check
```

### Captured run — 2026-09-30T19:19:36Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.zTK0paU8SK uv run pytest -q -p no:cacheprovider tests/unit/test_ux_canon_ratchet.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 369d0be1f61461eec83c7c499e089cbf0003d492

```text
....                                                                     [100%]
4 passed in 0.81s
```

### Re-capture after the ux-canon ratchet fix (2026-09-30)

The ratchet flagged a comment in `web/src/desk/documentSends.tsx` (the scanner read the text between `->` and `<id>` as JSX text); the comment is reworded, no face changed, and the ceiling is untouched (raw-ids back to 17). Two captures at 19:19:38Z failed because `web/node_modules` was empty in this worktree (no build, no vitest; nothing of the tree under test); they are removed here, `npm ci` restored the modules, and the captures below re-ran.

### Captured run — 2026-09-30T19:20:18Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.kW7QcJF9Kb HOLDSPEAK_EVIDENCE_WRITE=1 PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm uv run pytest -q -rA -p no:cacheprovider tests/e2e/test_philo11_05a_brief_decision_send_glass.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 369d0be1f61461eec83c7c499e089cbf0003d492

```text
........                                                                 [100%]
==================================== PASSES ====================================
_ TestBriefAndDecisionSendGlass.test_the_brief_well_on_the_chair_and_in_intelligence[1440] _
---------------------------- Captured stdout setup -----------------------------
[glass_infra] web bundle rebuilt in 5.1s
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
_ TestBriefAndDecisionSendGlass.test_the_brief_well_on_the_chair_and_in_intelligence[393] _
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
_ TestBriefAndDecisionSendGlass.test_the_decision_window_well_and_preview_changed[1440] _
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
_ TestBriefAndDecisionSendGlass.test_the_decision_window_well_and_preview_changed[393] _
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
_ TestBriefAndDecisionSendGlass.test_the_decision_record_wells_in_the_room_and_intelligence[1440] _
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
_ TestBriefAndDecisionSendGlass.test_the_decision_record_wells_in_the_room_and_intelligence[393] _
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
_ TestChairMeetingsAndBriefToSlack.test_the_chair_meeting_wells_and_the_brief_to_slack[1440] _
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
_ TestChairMeetingsAndBriefToSlack.test_the_chair_meeting_wells_and_the_brief_to_slack[393] _
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
=========================== short test summary info ============================
PASSED tests/e2e/test_philo11_05a_brief_decision_send_glass.py::TestBriefAndDecisionSendGlass::test_the_brief_well_on_the_chair_and_in_intelligence[1440]
PASSED tests/e2e/test_philo11_05a_brief_decision_send_glass.py::TestBriefAndDecisionSendGlass::test_the_brief_well_on_the_chair_and_in_intelligence[393]
PASSED tests/e2e/test_philo11_05a_brief_decision_send_glass.py::TestBriefAndDecisionSendGlass::test_the_decision_window_well_and_preview_changed[1440]
PASSED tests/e2e/test_philo11_05a_brief_decision_send_glass.py::TestBriefAndDecisionSendGlass::test_the_decision_window_well_and_preview_changed[393]
PASSED tests/e2e/test_philo11_05a_brief_decision_send_glass.py::TestBriefAndDecisionSendGlass::test_the_decision_record_wells_in_the_room_and_intelligence[1440]
PASSED tests/e2e/test_philo11_05a_brief_decision_send_glass.py::TestBriefAndDecisionSendGlass::test_the_decision_record_wells_in_the_room_and_intelligence[393]
PASSED tests/e2e/test_philo11_05a_brief_decision_send_glass.py::TestChairMeetingsAndBriefToSlack::test_the_chair_meeting_wells_and_the_brief_to_slack[1440]
PASSED tests/e2e/test_philo11_05a_brief_decision_send_glass.py::TestChairMeetingsAndBriefToSlack::test_the_chair_meeting_wells_and_the_brief_to_slack[393]
8 passed in 213.95s (0:03:33)
```

### Captured run — 2026-09-30T19:23:56Z

- **Command:** `sh -c cd web && npx vitest run src/desk/__tests__/philo301DecisionFace.test.tsx src/desk/chair/__tests__/generateAlwaysReachable.philo401.test.tsx src/desk/surface/send src/features/channels/__tests__/SendWell.test.tsx src/desk/pullouts src/features/project-room src/desk/chair`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 369d0be1f61461eec83c7c499e089cbf0003d492

```text

 RUN  v4.1.9 /Users/karol/dev/tools/wt-philo-11-05a/web


 Test Files  59 passed (59)
      Tests  676 passed (676)
   Start at  13:23:56
   Duration  7.15s (transform 6.35s, setup 4.86s, import 23.80s, tests 21.09s, environment 17.66s)
```

### No internal id in sent text (Muad'Dib's ruling, 2026-09-30)

The decision record's Sources listed raw refs (`proposal: prop-…`,
`transcript: meeting:<id>#segment:1`, `artifact: …`) and its Successor a
record id; the meeting decision named its meeting by id. That text is what
gets SENT. `holdspeak/services/document_sources.py` now names each source by
what a person recognizes (`_source_lines`: a meeting or a transcript segment
-> the meeting's title and date, or "A meeting (removed)"; a proposal ->
"From a meeting proposal"; the desk -> "Written on the desk"; artifact and
supersession rows left out), the later decision by its words ("## Superseded
by"), and the meeting decision's meeting by title and date. The rest of each
record is unchanged. The D-<hex> prepared-row labels stay (the canvas draws
them). Fence: `tests/unit/test_philo11_document_sources.py`
`test_no_rendered_document_carries_an_internal_id` (all eight kinds: no
`prop-`, `record-`, `meeting:`, `#segment`, no source id, no hex id of 8+
characters) and `test_a_decision_record_names_its_sources_as_a_person_recognizes_them`.
Red on head 130da18d1 with the renderer unchanged:
`assets/story-05a-proof/logs/no-internal-id-red.txt` (2 failed: the
meeting decision's `philo11-meeting`, the record's `meeting:`, `record-`, hex
ids). Green below.

### Captured run — 2026-09-30T19:30:35Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.sQuRdybrXf uv run pytest -q -p no:cacheprovider tests/unit/test_philo11_document_sources.py tests/unit/test_philo11_channel_contract.py tests/unit/test_philo11_slack_channel.py tests/unit/test_decision_record_service.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** b1f869ec698a4dde39bce6cc04116969c6f2b913

```text
........................................................................ [ 79%]
...................                                                      [100%]
91 passed in 15.18s
```

### Captured run — 2026-09-30T19:30:51Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.sQuRdybrXf HOLDSPEAK_EVIDENCE_WRITE=1 PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm uv run pytest -q -rA -p no:cacheprovider tests/e2e/test_philo11_05a_brief_decision_send_glass.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** b1f869ec698a4dde39bce6cc04116969c6f2b913

```text
........                                                                 [100%]
==================================== PASSES ====================================
_ TestBriefAndDecisionSendGlass.test_the_brief_well_on_the_chair_and_in_intelligence[1440] _
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
_ TestBriefAndDecisionSendGlass.test_the_brief_well_on_the_chair_and_in_intelligence[393] _
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
_ TestBriefAndDecisionSendGlass.test_the_decision_window_well_and_preview_changed[1440] _
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
_ TestBriefAndDecisionSendGlass.test_the_decision_window_well_and_preview_changed[393] _
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
_ TestBriefAndDecisionSendGlass.test_the_decision_record_wells_in_the_room_and_intelligence[1440] _
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
_ TestBriefAndDecisionSendGlass.test_the_decision_record_wells_in_the_room_and_intelligence[393] _
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
_ TestChairMeetingsAndBriefToSlack.test_the_chair_meeting_wells_and_the_brief_to_slack[1440] _
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
_ TestChairMeetingsAndBriefToSlack.test_the_chair_meeting_wells_and_the_brief_to_slack[393] _
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
=========================== short test summary info ============================
PASSED tests/e2e/test_philo11_05a_brief_decision_send_glass.py::TestBriefAndDecisionSendGlass::test_the_brief_well_on_the_chair_and_in_intelligence[1440]
PASSED tests/e2e/test_philo11_05a_brief_decision_send_glass.py::TestBriefAndDecisionSendGlass::test_the_brief_well_on_the_chair_and_in_intelligence[393]
PASSED tests/e2e/test_philo11_05a_brief_decision_send_glass.py::TestBriefAndDecisionSendGlass::test_the_decision_window_well_and_preview_changed[1440]
PASSED tests/e2e/test_philo11_05a_brief_decision_send_glass.py::TestBriefAndDecisionSendGlass::test_the_decision_window_well_and_preview_changed[393]
PASSED tests/e2e/test_philo11_05a_brief_decision_send_glass.py::TestBriefAndDecisionSendGlass::test_the_decision_record_wells_in_the_room_and_intelligence[1440]
PASSED tests/e2e/test_philo11_05a_brief_decision_send_glass.py::TestBriefAndDecisionSendGlass::test_the_decision_record_wells_in_the_room_and_intelligence[393]
PASSED tests/e2e/test_philo11_05a_brief_decision_send_glass.py::TestChairMeetingsAndBriefToSlack::test_the_chair_meeting_wells_and_the_brief_to_slack[1440]
PASSED tests/e2e/test_philo11_05a_brief_decision_send_glass.py::TestChairMeetingsAndBriefToSlack::test_the_chair_meeting_wells_and_the_brief_to_slack[393]
8 passed in 208.43s (0:03:28)
```

The decision labels also named the saved file with the source id
(`...-decision-record-<hex>-<send>.md`): the desk, meeting and record
decisions' label is now `DECISION` (the file keeps its title slug, date and
the design's 8-character send suffix). The fence now reads each kind's
title and label as well as its body; the red log above was re-recorded
against head's renderer with this fence. Re-captured below.

### Captured run — 2026-09-30T19:39:24Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.XB51L5tQEx uv run pytest -q -p no:cacheprovider tests/unit/test_philo11_document_sources.py tests/unit/test_philo11_channel_contract.py tests/unit/test_philo11_slack_channel.py tests/unit/test_decision_record_service.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** b1f869ec698a4dde39bce6cc04116969c6f2b913

```text
........................................................................ [ 79%]
...................                                                      [100%]
91 passed in 15.35s
```

### Captured run — 2026-09-30T19:39:40Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.XB51L5tQEx HOLDSPEAK_EVIDENCE_WRITE=1 PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm uv run pytest -q -rA -p no:cacheprovider tests/e2e/test_philo11_05a_brief_decision_send_glass.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** b1f869ec698a4dde39bce6cc04116969c6f2b913

```text
........                                                                 [100%]
==================================== PASSES ====================================
_ TestBriefAndDecisionSendGlass.test_the_brief_well_on_the_chair_and_in_intelligence[1440] _
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
_ TestBriefAndDecisionSendGlass.test_the_brief_well_on_the_chair_and_in_intelligence[393] _
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
_ TestBriefAndDecisionSendGlass.test_the_decision_window_well_and_preview_changed[1440] _
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
_ TestBriefAndDecisionSendGlass.test_the_decision_window_well_and_preview_changed[393] _
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
_ TestBriefAndDecisionSendGlass.test_the_decision_record_wells_in_the_room_and_intelligence[1440] _
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
_ TestBriefAndDecisionSendGlass.test_the_decision_record_wells_in_the_room_and_intelligence[393] _
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
_ TestChairMeetingsAndBriefToSlack.test_the_chair_meeting_wells_and_the_brief_to_slack[1440] _
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
_ TestChairMeetingsAndBriefToSlack.test_the_chair_meeting_wells_and_the_brief_to_slack[393] _
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
=========================== short test summary info ============================
PASSED tests/e2e/test_philo11_05a_brief_decision_send_glass.py::TestBriefAndDecisionSendGlass::test_the_brief_well_on_the_chair_and_in_intelligence[1440]
PASSED tests/e2e/test_philo11_05a_brief_decision_send_glass.py::TestBriefAndDecisionSendGlass::test_the_brief_well_on_the_chair_and_in_intelligence[393]
PASSED tests/e2e/test_philo11_05a_brief_decision_send_glass.py::TestBriefAndDecisionSendGlass::test_the_decision_window_well_and_preview_changed[1440]
PASSED tests/e2e/test_philo11_05a_brief_decision_send_glass.py::TestBriefAndDecisionSendGlass::test_the_decision_window_well_and_preview_changed[393]
PASSED tests/e2e/test_philo11_05a_brief_decision_send_glass.py::TestBriefAndDecisionSendGlass::test_the_decision_record_wells_in_the_room_and_intelligence[1440]
PASSED tests/e2e/test_philo11_05a_brief_decision_send_glass.py::TestBriefAndDecisionSendGlass::test_the_decision_record_wells_in_the_room_and_intelligence[393]
PASSED tests/e2e/test_philo11_05a_brief_decision_send_glass.py::TestChairMeetingsAndBriefToSlack::test_the_chair_meeting_wells_and_the_brief_to_slack[1440]
PASSED tests/e2e/test_philo11_05a_brief_decision_send_glass.py::TestChairMeetingsAndBriefToSlack::test_the_chair_meeting_wells_and_the_brief_to_slack[393]
8 passed in 209.50s (0:03:29)
```
