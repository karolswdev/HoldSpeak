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
| B4 GitHub, B6 Confluence forms SAVE (the concrete gh login read at save; the Jira/Confluence account from Connections); B5 REFUSED (one key only); B9 the remote rows; B10 a Jira row checked (the hub's state) | story 02 wire, canned process edge | built + fenced (`b04`, `b05-jira-one-key`, `b06`, `b09b-list-remote`, `b10b-jira-checked`) |
| B9 list; B10 CHECKED; B12 Edit; B13 old row parked; B14 Remove armed; B15 parked; B16 CANNOT READ DESTINATIONS | real routes | built + fenced |
| 7 GitHub picked; 9 POSTED + the comment link (a double click = one create); 20 REFUSED GITHUB ACCOUNT CHANGED (no create) | story 02 GitHub channel, canned `gh` at `channel_cli.CLI_RUNNER` | built + fenced |
| 10 Jira picked; 11 UNKNOWN TIMED OUT + Check PAY-121, no automatic re-send; 12 Send again → COMMENTED + the work item link | story 02 Jira channel, canned `acli` | built + fenced |
| 13 Confluence picked (SPACE, TITLE, ACCOUNT); 14 the account signed out: **REFUSED · NOT SIGNED IN · NOTHING SENT** as ratified (the wire now checks sign-in before the boundary: no row crosses it, no create); 15 BLOG POSTED + the post link; the remote history rows | story 02 Confluence channel + the pre-boundary sign-in check, canned `acli` | built + fenced (`14-refused-confluence-sign-in`); red on the story 02 wire first |
| 8 SENDING (a create held at the process edge; Send busy and disabled, one create for a double click); 26b a prepared send running survives Back → return (stored `dispatching`); 26c its destination: SENDING, Send disabled; 27 released → POSTED stays as its result | story 02 off-loop dispatch, canned `gh` held on an Event | built + fenced |
| 25 UNKNOWN after a restart: a REAL hub process killed with SIGKILL mid-send (the file written, the dispatch held), a second hub on the same HOME: LAST SEND UNKNOWN, ⚠ RESULT UNKNOWN · CHECK Folder Payments · INTERRUPTED, one file, never sent again | story 01's restart rig (`HubProcess`), the Room's own Send | built + fenced (`25-unknown-after-restart`) |

## Limits

- Board 29's prepared preview names the FOLDER, not the file: story 01 mints the file name at the dispatch boundary (`choose_path` in `ChannelService._boundary`), so no file name exists while a send is prepared. The receipt names the file.
- The destination row clamps a very long target path to two lines (its title and the open preview carry it whole): story 01's ENAMETOOLONG recipe path (~1000 characters) otherwise made a row taller than the 393 viewport.
- The steward policy face lists `prepare_send` (unit-fenced); choosing the run's `send_destination_ids` is not on the face (story 02's bound).

## Round two, part two: story 02 merged (main 3965c5e1)

The channel boards above run on story 02's real channels with only the process edge canned (its own rig, `tests/unit/_philo10_cli.py`). Glass 16/16 at both widths, every board measured (on-screen, clock-masked byte fence, nine-point pointer pass), the SENDING boards included.

## Board 14 as ratified (Muad'Dib's ruling on #697)

The wire, not the face: the Jira and Confluence channels check the saved account's sign-in BEFORE the dispatch boundary (switch-and-verify as classified reads under the acli lock) → REFUSED `atlassian_not_signed_in` / `atlassian_switch_failed` / `atlassian_identity_unverified`, with the receipt, nothing sent. A sign-out after the check stays the post-boundary known failure. Fences: `tests/unit/test_philo10_04_atlassian_sign_in.py` (both products refused before the boundary, zero creates, the row still `prepared`; the race case FAILED after it) and glass board 14 at both widths — red on the story 02 wire, green now. Story 02's proof notes the follow-up (`../story-02-proof/captures.md`).

## Story 03 merged (main e22b1b95): the email boards

| Board | Real producer | State |
|---|---|---|
| 16 email picked: FROM, TO, CC, SUBJECT parsed back from the frozen SendGrid request; API.SENDGRID.COM | story 03's email channel | built + fenced |
| 17 FAILED · SENDER NOT VERIFIED · NOTHING SENT (SendGrid's pinned 403), LAST SEND FAILED | story 03's canned HTTPS edge (`channel_email.HTTPS_HANDLER`) under the real opener, admission and allow-list | built + fenced |
| 18 Send again → ✓ ACCEPTED BY SENDGRID · ID sg-Msg-04AbCd (exact case; never DELIVERED) | same | built + fenced |
| 19 the history row ACCEPTED BY SENDGRID + the id; DELIVERY 1 | story 01's table | built + fenced |
| B7 KEY NOT SAVED · NO SAFE KEY STORE (nothing kept) | a key store with no native backend | built + fenced |
| B8 the email form, the key saved through `PUT /api/channels/email-keys/{key_ref}` into the in-memory store: SET, never the key on the face; the destination saved with its `key_ref`, To, Cc | the in-memory store (a guard fails the test if the real keychain is reached) | built + fenced |
| B11 Check reports the SENDER: SENDER NOT CHECKED before any answer; SENDER NOT VERIFIED after SendGrid's pinned 403 for that from address | `channel.check_destination` | built + fenced — see the note |

**B11, the wire change:** story 03's email Check answered key presence only. The ratified canvas asks for the sender's verification. `ChannelService._email_state` now reads the key (as before), then the provider's LAST answer for a send from that from address (by `dispatch_seq`): `sender_verified` (accepted), `sender_not_verified` (the pinned 403), or `ready` (no answer yet: SENDER NOT CHECKED). No call to SendGrid: a live verified-senders probe would be admitted egress, which the check (an exempt read) does not carry; that probe is not built.

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

### Captured run — 2026-09-29T06:36:30Z

- **Command:** `bash -c set -o pipefail; H=$(mktemp -d); trap "rm -rf $H" EXIT INT TERM; HOLDSPEAK_EVIDENCE_WRITE=1 HOME=$H PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm .venv/bin/python -m pytest -q -n 4 --basetemp=$H/pt tests/e2e/test_philo10_04_send_face_glass.py -rA 2>&1 | grep -E "^(PASSED|FAILED|ERROR)|passed|failed"`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 95a5f0ee43fb62d5861495afc000c0ecfebf9a32

```text
__ TestSendFaceGlass.test_a_known_failure_outlives_a_failed_sends_read[1440] ___
___ TestSendFaceGlass.test_a_known_failure_outlives_a_failed_sends_read[393] ___
PASSED tests/e2e/test_philo10_04_send_face_glass.py::TestSendFaceGlass::test_a_known_failure_outlives_a_failed_sends_read[1440]
PASSED tests/e2e/test_philo10_04_send_face_glass.py::TestSendFaceGlass::test_a_lost_answer_and_every_unreadable_read_are_named[1440]
PASSED tests/e2e/test_philo10_04_send_face_glass.py::TestSendFaceGlass::test_a_known_failure_outlives_a_failed_sends_read[393]
PASSED tests/e2e/test_philo10_04_send_face_glass.py::TestSendFaceGlass::test_prepared_sends_and_the_latest_result[1440]
PASSED tests/e2e/test_philo10_04_send_face_glass.py::TestSendFaceGlass::test_the_first_setup_loop_and_every_file_state[1440]
PASSED tests/e2e/test_philo10_04_send_face_glass.py::TestSendFaceGlass::test_a_lost_answer_and_every_unreadable_read_are_named[393]
PASSED tests/e2e/test_philo10_04_send_face_glass.py::TestSendFaceGlass::test_the_destinations_group[1440]
PASSED tests/e2e/test_philo10_04_send_face_glass.py::TestSendFaceGlass::test_the_first_setup_loop_and_every_file_state[393]
PASSED tests/e2e/test_philo10_04_send_face_glass.py::TestSendFaceGlass::test_prepared_sends_and_the_latest_result[393]
PASSED tests/e2e/test_philo10_04_send_face_glass.py::TestSendChannelsGlass::test_github_sending_posted_and_a_running_prepared_send[1440]
PASSED tests/e2e/test_philo10_04_send_face_glass.py::TestSendFaceGlass::test_the_destinations_group[393]
PASSED tests/e2e/test_philo10_04_send_face_glass.py::TestSendChannelsGlass::test_the_remote_destination_forms_save[1440]
PASSED tests/e2e/test_philo10_04_send_face_glass.py::TestSendChannelsGlass::test_github_sending_posted_and_a_running_prepared_send[393]
PASSED tests/e2e/test_philo10_04_send_face_glass.py::TestSendChannelsGlass::test_jira_and_confluence[1440]
PASSED tests/e2e/test_philo10_04_send_face_glass.py::TestSendChannelsGlass::test_jira_and_confluence[393]
PASSED tests/e2e/test_philo10_04_send_face_glass.py::TestSendChannelsGlass::test_the_remote_destination_forms_save[393]
16 passed in 183.97s (0:03:03)
```

### Captured run — 2026-09-29T06:39:46Z

- **Command:** `bash -c set -o pipefail; H=$(mktemp -d); trap "rm -rf $H" EXIT INT TERM; HOME=$H PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm .venv/bin/python -m pytest -q -n 4 --basetemp=$H/pt tests/e2e/test_philo10_01_unknown_send_face.py tests/e2e/test_philo9_03_room_face_glass.py tests/e2e/test_philo10_02_nudge_unknown_glass.py tests/e2e/test_hs173_policy_glass.py tests/e2e/test_hs173_health_glass.py tests/e2e/test_philo9_b1_connections_glass.py tests/e2e/test_hs170_settings_hub_glass.py tests/unit/test_philo10_send_contract.py tests/unit/test_philo10_send_recovery.py tests/unit/test_philo10_send_restart.py tests/unit/test_philo10_rig_op.py tests/unit/test_philo10_cli_channels.py tests/unit/test_philo10_settings_atomic.py tests/unit/test_694_thread_never_sends.py "tests/unit/test_db.py::TestDatabaseShape" 2>&1 | tail -3`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 95a5f0ee43fb62d5861495afc000c0ecfebf9a32

```text
........................................................................ [ 82%]
...............................                                          [100%]
175 passed in 160.63s (0:02:40)
```

### Captured run — 2026-09-29T06:42:32Z (one vitest test failed under load; the script did not name it here; the next two runs, one below, are 2966/2966 with zero branch-new — the load flake noted in round one)

- **Command:** `bash -c H=$(mktemp -d); trap "rm -rf $H" EXIT INT TERM; HOME=$H npm_config_cache=/Users/karol/.npm .venv/bin/python scripts/check_web_baseline.py --run 2>&1 | tail -4`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 95a5f0ee43fb62d5861495afc000c0ecfebf9a32

```text

Suite totals: 2965 passed, 1 failed, 0 skipped

VERDICT: BRANCH-NEW FAILURES: 1
```

### Captured run — 2026-09-29T06:43:59Z

- **Command:** `bash -c H=$(mktemp -d); trap "rm -rf $H" EXIT INT TERM; HOME=$H npm_config_cache=/Users/karol/.npm .venv/bin/python scripts/check_web_baseline.py --run 2>&1 | grep -A3 "BRANCH-NEW\|Suite totals"`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 95a5f0ee43fb62d5861495afc000c0ecfebf9a32

```text
Suite totals: 2966 passed, 0 failed, 0 skipped

VERDICT: baseline-subset, zero branch-new
```

### Captured run — 2026-09-29T06:47:31Z (RED on the story 02 wire: a signed-out account crosses the boundary and settles FAILED; the exit is the pipeline's `grep`)

- **Command:** `bash -c H=$(mktemp -d); trap "rm -rf $H" EXIT INT TERM; HOME=$H PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm .venv/bin/python -m pytest -q -n 3 --basetemp=$H/pt tests/unit/test_philo10_04_atlassian_sign_in.py tests/e2e/test_philo10_04_send_face_glass.py -k "sign or jira_and_confluence" -rf 2>&1 | grep -E "^(FAILED|E   )|passed|failed" | cut -c1-240 | head -24`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a8a00ccb41d20cff87cec37b2fbf8525d8b27d04

```text
E       AssertionError: {"send":{"id":"chs_a31e61c9ec57afdf9cee4d1f","document_ref":"project_update:pupd_7fb64a31a8b44a4385ec2b749894c73b","destination_id":"chd_1d0aa59e27ab8ef1d700f310","destination_name":"confluence scratch","channel":"co
E       assert (200 == 409)
E        +  where 200 = <Response [200 OK]>.status_code
E       AssertionError: {"send":{"id":"chs_9dc7eed749377ff39fadee7a","document_ref":"project_update:pupd_8e499ad3af304762b5a40d878022bceb","destination_id":"chd_395d5460d68174665b87a3b4","destination_name":"jira scratch","channel":"jira","b
E       assert (200 == 409)
E        +  where 200 = <Response [200 OK]>.status_code
>       assert (body["outcome"], body["send"]["reason"]) == ("failed", "atlassian_not_logged_in"), body
E       AssertionError: {'operation_id': 'op_8543476cb6d640a1992bf8da38442c1e', 'outcome': 'sent', 'receipt': {'actor_identity': 'owner-sessio...te': 'acme.atlassian.net'}, 'badge': 'cloud', 'channel': 'confluence', 'created_at': '2026-09-2
E       assert ('sent', None) == ('failed', 'a...ot_logged_in')
E         
E         At index 0 diff: 'sent' != 'failed'
E         Use -v to get more diff
E           playwright._impl._errors.TimeoutError: Locator.wait_for: Timeout 20000ms exceeded.
E           Call log:
E             - waiting for locator("[data-testid=send-open][data-destination='Confluence space 98304'] [data-testid=send-refused]") to be visible
E           playwright._impl._errors.TimeoutError: Locator.wait_for: Timeout 20000ms exceeded.
E           Call log:
E             - waiting for locator("[data-testid=send-open][data-destination='Confluence space 98304'] [data-testid=send-refused]") to be visible
FAILED tests/unit/test_philo10_04_atlassian_sign_in.py::test_a_signed_out_account_is_refused_before_the_boundary[confluence]
FAILED tests/unit/test_philo10_04_atlassian_sign_in.py::test_a_signed_out_account_is_refused_before_the_boundary[jira]
FAILED tests/unit/test_philo10_04_atlassian_sign_in.py::test_a_sign_out_after_the_check_is_the_post_boundary_known_failure
FAILED tests/e2e/test_philo10_04_send_face_glass.py::TestSendChannelsGlass::test_jira_and_confluence[393]
FAILED tests/e2e/test_philo10_04_send_face_glass.py::TestSendChannelsGlass::test_jira_and_confluence[1440]
5 failed in 47.08s
```

### Captured run — 2026-09-29T06:55:36Z

- **Command:** `bash -c set -o pipefail; H=$(mktemp -d); trap "rm -rf $H" EXIT INT TERM; HOLDSPEAK_EVIDENCE_WRITE=1 HOME=$H PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm .venv/bin/python -m pytest -q -n 4 --basetemp=$H/pt tests/e2e/test_philo10_04_send_face_glass.py tests/unit/test_philo10_04_atlassian_sign_in.py tests/unit/test_philo10_cli_channels.py tests/unit/test_philo10_send_contract.py tests/unit/test_philo10_send_recovery.py tests/unit/test_philo10_send_restart.py tests/unit/test_philo5_one_decision.py 2>&1 | tail -2`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a8a00ccb41d20cff87cec37b2fbf8525d8b27d04

```text
....                                                                     [100%]
148 passed in 255.30s (0:04:15)
```

### Captured run — 2026-09-29T07:02:06Z

- **Command:** `bash -c set -o pipefail; H=$(mktemp -d); trap "rm -rf $H" EXIT INT TERM; HOLDSPEAK_EVIDENCE_WRITE=1 HOME=$H PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm .venv/bin/python -m pytest -q -n 2 --basetemp=$H/pt tests/e2e/test_philo10_04_send_face_glass.py -k board_25 -rA 2>&1 | grep -E "^(PASSED|FAILED)|passed|failed"`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 4e9ad95c988eb4daa6393242f9969da46f9552b5

```text
PASSED tests/e2e/test_philo10_04_send_face_glass.py::test_board_25_unknown_after_a_real_restart[393]
PASSED tests/e2e/test_philo10_04_send_face_glass.py::test_board_25_unknown_after_a_real_restart[1440]
2 passed in 18.78s
```
