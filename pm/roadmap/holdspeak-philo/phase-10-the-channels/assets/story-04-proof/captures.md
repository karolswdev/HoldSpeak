# PHILO-10-04 — build proof (the evidence file comes with the done flip)

Built to the owner's ratified canvases (`../story-04-send-canvas/`, `../story-04-destinations-canvas/`, "Ratify as drawn", 2026-09-29). Shots: `../story-04-shots/` (1440 × 900 and 393 × 852, each board's facts in the `*-<width>.json` next to them). The glass: `tests/e2e/test_philo10_04_send_face_glass.py` (helpers `tests/e2e/_send_face_glass.py`), through the real hub on an isolated HOME; every board asserts its named elements on screen (in the viewport, inside every clipping ancestor, on top at the centre and two inner corners), no two shots of one test and width share bytes with the menu-bar clock masked, no text under 12 px in the window, no raw `<button>` in the touched face, no modal, no overflow, no raw JSON or XHTML in a preview, and a nine-point pointer pass (elementFromPoint AND a real pointer move; the 44 × 44 target at 393) on every touched control.

## Round two: Codex Astra r1 on #697 (`../../checks/story-04-built-astra-r1.md`, DO-NOT-RATIFY)

| r1 | Paid |
|---|---|
| F1 a known FAILED hidden by a failed or stale sends read | The hub's returned record joins the ONE result source (`mergeKnown`, `SendWell.tsx`): a read replaces it only when as far along. Fence `r1-failed-read-keeps-failure` (SAVED → folder 0555 → every sends read fails → Send again: header LAST SEND FAILED, receipt FAILED `permission_denied`, CANNOT READ SENDS named) at both widths; red on the old face. |
| F2 a failed Remove closed the row silently | The row stays open: ✗ NOT REMOVED + the reason + Retry. Fence `b14b-remove-failed` (DELETE with no answer; hub still active) then Retry → parked, both widths. |
| F3 microseconds are not an order | `channel_sends.dispatch_seq` (additive), allocated inside the boundary transaction (MAX + 1 under BEGIN IMMEDIATE); `latestFor` orders by it; the microsecond stamp stays for display. Fence: Codex's sequence with the boundary clock PINNED (equal `dispatch_started_at`): A's FAILED is latest (28b, 28c), both widths; red on the old face. Unit: `SendWell.test.tsx`. |
| F4 B10 lost the Checked time | Restored: the open row shows Checked + the time the hub answered the Check. |
| F5 four armed shots bypassed the board checks | 32 and B14 armed are now measured boards (on-screen, byte, pointer). |

## The ratified boards: built and fenced, or owed

| Board | Real producer | State |
|---|---|---|
| 0a/0b today (DELIVERED word) | main's bundle | RED on main, captured below |
| 1 no destination; B1 arrive from the Room (form open, no harness scroll); B2 add folder; B3 name from target; 2 back in the Room, no reload | real routes, real Settings | built + fenced (`01`, `b01`, `b02`, `02`) |
| 3 destinations listed; 4 picked (A1); 5 SAVED + exact path (double click = one send); 6 SAVED in the history | file channel | built + fenced (`03`–`06`) |
| FAILED (pinned: EACCES `permission_denied`), LAST SEND FAILED | file channel, folder mode 0555 | built + fenced (`17-failed-folder`) |
| UNKNOWN (story 01's ENAMETOOLONG recipe), LAST SEND UNKNOWN, no automatic re-send, Send again | file channel | built + fenced (`11-unknown-folder`) |
| 21 lost answer; 24 Retry reuses the key (one file), update B clean, back on A | fetch seam (reply dropped after commit) | built + fenced |
| 26 PREPARED first, ONE open (A3), BY REMOTE-PROJECT-AGENT / BY YOU, PREPARED ×K list chip | `channel.prepare` by a remote agent credential + the owner | built + fenced (`26`, `35b`) |
| 28 prepared FAILED; 28b latest by `dispatch_started_at`; 28c reopened receipt = header | file channel (inline SAVED, then the older preparation FAILS) | built + fenced |
| 29 prepared file SAVED, stays as its result | file channel | built + fenced (the prepared preview names the FOLDER only; see Limits) |
| 30 DESTINATION CHANGED (folder resolves elsewhere); 31 DESTINATION PARKED; 32 Discard armed; 33 DISCARDED stays | real refusals | built + fenced |
| 34 several; 34b manual (DELIVERED · MANUAL kept); 35 DELIVERY ×N (A2) + RESULT UNKNOWN ×M | story 01's one table | built + fenced |
| 36 a draft has no Send | — | built + fenced |
| 37 CANNOT READ DESTINATIONS; 38 SENDS; 39 HISTORY; 40 NO PREVIEW (Send not offered) | fetch seam (no answer) | built + fenced |
| B4 GitHub, B6 Confluence, B8 email forms (the name from the target; the key only present or absent) | the forms as drawn | built + shot; SAVE owed: story 02 (GitHub/Jira/Confluence), story 03 (email, the key route) |
| B9 list; B10 CHECKED; B12 Edit; B13 old row parked; B14 Remove armed; B15 parked; B16 CANNOT READ DESTINATIONS | real routes | built + fenced |
| 7–10, 12–16, 18–20 (GitHub POSTED, Jira COMMENTED, Confluence BLOG POSTED, email ACCEPTED BY SENDGRID, sign-in / account refusals), B5 ONE KEY ONLY, B7 KEY NOT SAVED, B11 SENDER NOT VERIFIED | stories 02 / 03 channels | face built (words, proof cells, account chips); NOT fenced: owed when 02 (#695) and 03 merge |
| 8 SENDING, 26b running prepared across Back → return, 26c its destination Send disabled | a held dispatch | face built (polls while `dispatching`; Send disabled while running); NOT fenced: on main the send route runs on the event loop, so a held dispatch blocks every read; story 02's GATE 2 moves it to the threadpool |
| 25 UNKNOWN after a restart | story 01 recovery | face renders any UNKNOWN row (fenced by `11`); the restart itself is story 01's unit fence, not re-shot here |

## Limits

- Board 29's prepared preview names the FOLDER, not the file: story 01 mints the file name at the dispatch boundary (`choose_path` in `ChannelService._boundary`), so no file name exists while a send is prepared. The receipt names the file.
- The destination row clamps a very long target path to two lines (its title and the open preview carry it whole): story 01's ENAMETOOLONG recipe path (~1000 characters) otherwise made a row taller than the 393 viewport.
- The steward policy face lists `prepare_send` (unit-fenced); choosing the run's `send_destination_ids` is not on the face (story 02's bound).

## Captured runs

### Captured run — 2026-09-29T05:48:27Z (RED on main: `web/src` laid from HEAD 84657927 by `git archive`, main's bundle built; the exit code is the pipeline's `grep`, pytest reads 4 failed)

- **Command:** `bash -c H=$(mktemp -d); trap "rm -rf $H" EXIT INT TERM; HOME=$H PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm .venv/bin/python -m pytest -q --basetemp=$H/pt -p no:randomly tests/e2e/test_philo10_01_unknown_send_face.py "tests/e2e/test_philo10_04_send_face_glass.py::TestSendFaceGlass::test_the_first_setup_loop_and_every_file_state" -rf 2>&1 | grep -E "^(FAILED|ERROR|E   )|passed|failed" | cut -c1-300`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** eed50ad4ddb39305e79450e7bd63771b070f3c59

```text
E               AssertionError: ['✓ DELIVERED ×1']
E               assert ['✓ DELIVERED ×1'] == ['✓ DELIVERY ×1']
E                 
E                 At index 0 diff: '✓ DELIVERED ×1' != '✓ DELIVERY ×1'
E                 Use -v to get more diff
E               AssertionError: ['✓ DELIVERED ×1']
E               assert ['✓ DELIVERED ×1'] == ['✓ DELIVERY ×1']
E                 
E                 At index 0 diff: '✓ DELIVERED ×1' != '✓ DELIVERY ×1'
E                 Use -v to get more diff
E           playwright._impl._errors.TimeoutError: Locator.wait_for: Timeout 20000ms exceeded.
E           Call log:
E             - waiting for locator("[data-testid=send-well]") to be visible
E           playwright._impl._errors.TimeoutError: Locator.wait_for: Timeout 20000ms exceeded.
E           Call log:
E             - waiting for locator("[data-testid=send-well]") to be visible
FAILED tests/e2e/test_philo10_01_unknown_send_face.py::TestUnknownSendFace::test_an_unknown_send_is_never_shown_as_delivered[1440]
FAILED tests/e2e/test_philo10_01_unknown_send_face.py::TestUnknownSendFace::test_an_unknown_send_is_never_shown_as_delivered[393]
FAILED tests/e2e/test_philo10_04_send_face_glass.py::TestSendFaceGlass::test_the_first_setup_loop_and_every_file_state[1440]
FAILED tests/e2e/test_philo10_04_send_face_glass.py::TestSendFaceGlass::test_the_first_setup_loop_and_every_file_state[393]
4 failed in 66.98s (0:01:06)
```

### Captured run — 2026-09-29T05:50:22Z

- **Command:** `bash -c set -o pipefail; H=$(mktemp -d); trap "rm -rf $H" EXIT INT TERM; HOLDSPEAK_EVIDENCE_WRITE=1 HOME=$H PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm .venv/bin/python -m pytest -q --basetemp=$H/pt tests/e2e/test_philo10_04_send_face_glass.py -rA 2>&1 | grep -E "^(PASSED|FAILED|ERROR)|passed|failed"`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** eed50ad4ddb39305e79450e7bd63771b070f3c59

```text
PASSED tests/e2e/test_philo10_04_send_face_glass.py::TestSendFaceGlass::test_the_first_setup_loop_and_every_file_state[1440]
PASSED tests/e2e/test_philo10_04_send_face_glass.py::TestSendFaceGlass::test_the_first_setup_loop_and_every_file_state[393]
PASSED tests/e2e/test_philo10_04_send_face_glass.py::TestSendFaceGlass::test_prepared_sends_and_the_latest_result[1440]
PASSED tests/e2e/test_philo10_04_send_face_glass.py::TestSendFaceGlass::test_prepared_sends_and_the_latest_result[393]
PASSED tests/e2e/test_philo10_04_send_face_glass.py::TestSendFaceGlass::test_a_lost_answer_and_every_unreadable_read_are_named[1440]
PASSED tests/e2e/test_philo10_04_send_face_glass.py::TestSendFaceGlass::test_a_lost_answer_and_every_unreadable_read_are_named[393]
PASSED tests/e2e/test_philo10_04_send_face_glass.py::TestSendFaceGlass::test_the_destinations_group[1440]
PASSED tests/e2e/test_philo10_04_send_face_glass.py::TestSendFaceGlass::test_the_destinations_group[393]
8 passed in 260.25s (0:04:20)
```

### Captured run — 2026-09-29T05:55:00Z

- **Command:** `bash -c set -o pipefail; H=$(mktemp -d); trap "rm -rf $H" EXIT INT TERM; HOME=$H PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm .venv/bin/python -m pytest -q -n 4 --basetemp=$H/pt tests/e2e/test_philo10_01_unknown_send_face.py tests/e2e/test_philo9_03_room_face_glass.py tests/e2e/test_hs173_policy_glass.py tests/e2e/test_philo9_b1_connections_glass.py tests/e2e/test_hs170_settings_hub_glass.py tests/unit/test_philo10_send_contract.py tests/unit/test_philo10_send_recovery.py tests/unit/test_philo10_send_restart.py tests/unit/test_philo10_rig_op.py tests/unit/test_694_thread_never_sends.py 2>&1 | tail -3`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** eed50ad4ddb39305e79450e7bd63771b070f3c59

```text
........................................................................ [ 63%]
..........................................                               [100%]
114 passed in 112.19s (0:01:52)
```

### Captured run — 2026-09-29T05:56:58Z

- **Command:** `bash -c H=$(mktemp -d); trap "rm -rf $H" EXIT INT TERM; HOME=$H npm_config_cache=/Users/karol/.npm .venv/bin/python scripts/check_web_baseline.py --run 2>&1 | tail -12`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** eed50ad4ddb39305e79450e7bd63771b070f3c59

```text
=== Web baseline report ===

HEALED (5):
  src/desk/__tests__/containerQueryLaw.test.ts > HS-129-06 container-query law > keeps viewport-width media limited to shell exceptions
  src/desk/__tests__/writeReceiptGuard.test.ts > HS-132-06 swallowed-write guard > keeps every desk write out of a bare catch
  src/desk/components/InlineEditor.test.tsx > HS-129-08 editor windows > hosts note editing in its open pullout
  src/desk/components/MicButton.test.tsx > MicButton surfaces named refusals (HS-132-05) > never claims retention the session cannot prove
  src/desk/components/__tests__/workbenchAutomations.test.tsx > Workbench STARTS WHEN automations > tests without delivering work, then enables and pauses the trigger

Suite totals: 2958 passed, 0 failed, 0 skipped

VERDICT: baseline-subset, zero branch-new
```

### Captured run — 2026-09-29T05:58:44Z

- **Command:** `bash -c set -e; P=.venv/bin/python; python3 -m unittest discover -s tests/unit -p test_docs_navigation.py 2>&1 | tail -1; $P scripts/check_docs.py; $P scripts/check_docs.py docs/internal/philo/*.md docs/internal/philo/adr/*.md docs/internal/philo/checks/*.md docs/internal/philo/visuals/README.md docs/internal/philo/desktop-prototypes/README.md agent/skills/*/SKILL.md; $P scripts/philo_repository_census.py --check; $P scripts/philo_api_reference.py --check; $P scripts/philo_boundary_census.py --check; $P scripts/philo_doctor_reference.py --check; $P scripts/philo_config_reference.py --check; $P scripts/philo_graph_reference.py --check 2>&1 | tail -1; $P scripts/validate_architecture.py; $P scripts/generate_capability_docs.py --check; $P scripts/check_doc_coverage.py --check`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** eed50ad4ddb39305e79450e7bd63771b070f3c59

```text
OK
Documentation navigation: 70 files checked; local targets and Markdown headings resolve.
Documentation navigation: 33 files checked; local targets and Markdown headings resolve.
Repository census: 5 outputs verified.
API reference checked
Boundary candidate census checked
Doctor reference: 41 check functions
Configuration declaration reference is current
graph join checked: docs/generated/graph.json; 14 subtype conflict note(s)
Architecture metadata: 4 shard(s), 147 record(s)
Architecture metadata validation passed.
Architecture documentation checked (10 outputs).
Documentation coverage checked.
```

### Captured run — 2026-09-29T06:19:26Z (RED on #697's head face: `SendWell.tsx` and `Destinations.tsx` laid from 8d7fa1ea; r1 F1 and B10 red at both widths; the exit is the pipeline's `grep`)

- **Command:** `bash -c H=$(mktemp -d); trap "rm -rf $H" EXIT INT TERM; HOME=$H PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm .venv/bin/python -m pytest -q -n 4 --basetemp=$H/pt tests/e2e/test_philo10_04_send_face_glass.py -k "outlives or prepared or destinations_group" -rf 2>&1 | grep -E "^(FAILED|E   )|passed|failed" | cut -c1-300 | head -40`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 3d2bad7a4a41a19e0887ff62b1c1b34ea9edb32b

```text
__ TestSendFaceGlass.test_a_known_failure_outlives_a_failed_sends_read[1440] ___
    def test_a_known_failure_outlives_a_failed_sends_read(self, width: int) -> None:
>               page.locator(f"{self._open_sel('Folder Payments')} [data-receipt=latest][data-state=failed]").wait_for(timeout=T)
E           playwright._impl._errors.TimeoutError: Locator.wait_for: Timeout 20000ms exceeded.
E           Call log:
E             - waiting for locator("[data-testid=send-open][data-destination='Folder Payments'] [data-receipt=latest][data-state=failed]") to be visible
___ TestSendFaceGlass.test_a_known_failure_outlives_a_failed_sends_read[393] ___
    def test_a_known_failure_outlives_a_failed_sends_read(self, width: int) -> None:
>               page.locator(f"{self._open_sel('Folder Payments')} [data-receipt=latest][data-state=failed]").wait_for(timeout=T)
E           playwright._impl._errors.TimeoutError: Locator.wait_for: Timeout 20000ms exceeded.
E           Call log:
E             - waiting for locator("[data-testid=send-open][data-destination='Folder Payments'] [data-receipt=latest][data-state=failed]") to be visible
E               assert 'CHECKED' in 'CHANNEL\nFILE\nFOLDER\n/PRIVATE/VAR/FOLDERS/Q7/5DZZ5G2116B3LQ8RHG7HWJRR0000GN/T/TMP.VOSYKDJ0AG/PT/POPEN-GW1/TEST_THE_DESTINATIONS_GROUP_390/REPORTS\nSYNCED\nNO\nSAVED\nSEP 29 00:20'
E                +  where 'CHANNEL\nFILE\nFOLDER\n/PRIVATE/VAR/FOLDERS/Q7/5DZZ5G2116B3LQ8RHG7HWJRR0000GN/T/TMP.VOSYKDJ0AG/PT/POPEN-GW1/TEST_THE_DESTINATIONS_GROUP_390/REPORTS\nSYNCED\nNO\nSAVED\nSEP 29 00:20' = <built-in method upper of str object at 0x12148fbb0>()
E                +    where <built-in method upper of str object at 0x12148fbb0> = 'CHANNEL\nFILE\nFOLDER\n/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.vosYkdJ0AG/pt/popen-gw1/test_the_destinations_group_390/Reports\nSYNCED\nNO\nSAVED\nSEP 29 00:20'.upper
E                +      where 'CHANNEL\nFILE\nFOLDER\n/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.vosYkdJ0AG/pt/popen-gw1/test_the_destinations_group_390/Reports\nSYNCED\nNO\nSAVED\nSEP 29 00:20' = inner_text()
E                +        where inner_text = <Locator frame=<Frame name= url='http://127.0.0.1:65119/'> selector="li.surface-ledger-row:has(> [data-testid=dest-row] [data-destination='Folder Reports']) [data-testid=dest-open] dl">.inner_text
E                +          where <Locator frame=<Frame name= url='http://127.0.0.1:65119/'> selector="li.surface-ledger-row:has(> [data-testid=dest-row] [data-destination='Folder Reports']) [data-testid=dest-open] dl"> = locator("li.surface-ledger-row:has(> [data-testid=dest-row] [data-destination=
E                +            where locator = <Page url='http://127.0.0.1:65119/'>.locator
E               assert 'CHECKED' in 'CHANNEL\nFILE\nFOLDER\n/PRIVATE/VAR/FOLDERS/Q7/5DZZ5G2116B3LQ8RHG7HWJRR0000GN/T/TMP.VOSYKDJ0AG/PT/POPEN-GW0/TEST_THE_DESTINATIONS_GROUP_140/REPORTS\nSYNCED\nNO\nSAVED\nSEP 29 00:20'
E                +  where 'CHANNEL\nFILE\nFOLDER\n/PRIVATE/VAR/FOLDERS/Q7/5DZZ5G2116B3LQ8RHG7HWJRR0000GN/T/TMP.VOSYKDJ0AG/PT/POPEN-GW0/TEST_THE_DESTINATIONS_GROUP_140/REPORTS\nSYNCED\nNO\nSAVED\nSEP 29 00:20' = <built-in method upper of str object at 0x1104ebad0>()
E                +    where <built-in method upper of str object at 0x1104ebad0> = 'CHANNEL\nFILE\nFOLDER\n/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.vosYkdJ0AG/pt/popen-gw0/test_the_destinations_group_140/Reports\nSYNCED\nNO\nSAVED\nSEP 29 00:20'.upper
E                +      where 'CHANNEL\nFILE\nFOLDER\n/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.vosYkdJ0AG/pt/popen-gw0/test_the_destinations_group_140/Reports\nSYNCED\nNO\nSAVED\nSEP 29 00:20' = inner_text()
E                +        where inner_text = <Locator frame=<Frame name= url='http://127.0.0.1:65118/'> selector="li.surface-ledger-row:has(> [data-testid=dest-row] [data-destination='Folder Reports']) [data-testid=dest-open] dl">.inner_text
E                +          where <Locator frame=<Frame name= url='http://127.0.0.1:65118/'> selector="li.surface-ledger-row:has(> [data-testid=dest-row] [data-destination='Folder Reports']) [data-testid=dest-open] dl"> = locator("li.surface-ledger-row:has(> [data-testid=dest-row] [data-destination=
E                +            where locator = <Page url='http://127.0.0.1:65118/'>.locator
FAILED tests/e2e/test_philo10_04_send_face_glass.py::TestSendFaceGlass::test_a_known_failure_outlives_a_failed_sends_read[1440]
FAILED tests/e2e/test_philo10_04_send_face_glass.py::TestSendFaceGlass::test_a_known_failure_outlives_a_failed_sends_read[393]
FAILED tests/e2e/test_philo10_04_send_face_glass.py::TestSendFaceGlass::test_the_destinations_group[393]
FAILED tests/e2e/test_philo10_04_send_face_glass.py::TestSendFaceGlass::test_the_destinations_group[1440]
4 failed, 2 passed in 56.91s
```

### Captured run — 2026-09-29T06:20:46Z (RED on #697's head `SendWell.tsx`: the equal-clock sequence, r1 F3, shows the older SAVED as latest at both widths)

- **Command:** `bash -c H=$(mktemp -d); trap "rm -rf $H" EXIT INT TERM; HOME=$H PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm .venv/bin/python -m pytest -q -n 2 --basetemp=$H/pt tests/e2e/test_philo10_04_send_face_glass.py -k "prepared" -rf 2>&1 | grep -E "^(FAILED|E   )|passed|failed" | cut -c1-300 | head -20`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 3d2bad7a4a41a19e0887ff62b1c1b34ea9edb32b

```text
                    .some((e) => e.dataset.state === 'failed')""", timeout=T)
                shots.shoot(page, "28-prepared-failed", ["[data-testid=prepared-result] [data-state=failed]"])
                assert [s["state"] for s in ledger] == ["sent", "failed"], ledger
                latest = shots.shoot(page, "28b-destination-latest-failed",
                                     [f"{self._row('Folder Ledger')} [data-testid=send-last-failed]"])
                                       [f"{self._open_sel('Folder Ledger')} [data-testid=send-failed]"])
>               assert [r["state"] for r in reopened["receipts"]] == ["failed"], reopened["receipts"]
E               AssertionError: [{'code': None, 'state': 'sent', 'text': '✓ SAVED /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.Ixreo440Zr/pt/popen-gw1/test_prepared_sends_and_the_la0/Ledger/2026-09-29-payments-ledger-cutover-r1-a1961074.md'}]
E               assert ['sent'] == ['failed']
E                 
E                 At index 0 diff: 'sent' != 'failed'
E                 Use -v to get more diff
                    .some((e) => e.dataset.state === 'failed')""", timeout=T)
                shots.shoot(page, "28-prepared-failed", ["[data-testid=prepared-result] [data-state=failed]"])
                assert [s["state"] for s in ledger] == ["sent", "failed"], ledger
                latest = shots.shoot(page, "28b-destination-latest-failed",
                                     [f"{self._row('Folder Ledger')} [data-testid=send-last-failed]"])
                                       [f"{self._open_sel('Folder Ledger')} [data-testid=send-failed]"])
>               assert [r["state"] for r in reopened["receipts"]] == ["failed"], reopened["receipts"]
E               AssertionError: [{'code': None, 'state': 'sent', 'text': '✓ SAVED /private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.Ixreo440Zr/pt/popen-gw0/test_prepared_sends_and_the_la0/Ledger/2026-09-29-payments-ledger-cutover-r1-3c307c9a.md'}]
```

### Captured run — 2026-09-29T06:21:48Z

- **Command:** `bash -c set -o pipefail; H=$(mktemp -d); trap "rm -rf $H" EXIT INT TERM; HOLDSPEAK_EVIDENCE_WRITE=1 HOME=$H PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm .venv/bin/python -m pytest -q -n 4 --basetemp=$H/pt tests/e2e/test_philo10_04_send_face_glass.py tests/unit/test_philo10_send_contract.py tests/unit/test_philo10_send_recovery.py tests/unit/test_philo10_send_restart.py "tests/unit/test_db.py::TestDatabaseShape" 2>&1 | tail -2 && cd web && npx vitest run src/features/channels src/features/project-room 2>&1 | grep -E "Test Files|Tests |Errors"`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 3d2bad7a4a41a19e0887ff62b1c1b34ea9edb32b

```text
.....................................................................    [100%]
69 passed in 158.62s (0:02:38)
 Test Files  24 passed (24)
      Tests  459 passed (459)
```
