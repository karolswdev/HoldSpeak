# Evidence - PHILO-10-07

- **Story:** PHILO-10-07 - Resend, the second email provider
- **Status:** done
- **Date:** 2026-09-29
- **Branch:** `feat/philo-10-07` from main `05d01ffb`.
- **Ruling:** "the changes will include also plugging in 'resend' client, okay? We can have SendGrid and Resend (I happen to actually have that.)" (the owner, the Phase 10 closing review).

## What was built

- `holdspeak/services/channel_email.py`: `ResendProvider` (one class) and its `EMAIL_PROVIDERS` row; `resend_error` / `resend_id` (bounded reads of Resend's answer); `key_slot(provider, key_ref)` = `<provider>:<key_ref>`, read and written by `read_key` / `save_key` with the provider.
- `holdspeak/services/channel_service.py`: the key save writes its provider's slot and names it in the receipt; the email Check reads the latest answer of its own provider and the key-saved receipt of its own slot.
- `holdspeak/channel_operations.py` + `docs/generated/operations.json`: the descriptions name SendGrid and Resend.
- The face: `web/src/features/channels/channels.ts` (one `EMAIL_PROVIDERS` face table: label, word, host, activity page; `sentWord` names the provider; the Resend codes' words; `email_key_missing` reads NO KEY), `SendWell.tsx` (the SENT word from the proof's provider), `web/src/pages/cores/connections/Destinations.tsx` (the Provider cycle with SendGrid and Resend, the key row and the key name per provider).
- Fences: `tests/unit/test_philo10_email_channel.py` `test_c7_*` (30 collected); `tests/unit/_philo10_codes.py` follows `self.PINNED[status, name]`; `tests/unit/test_philo10_face_words.py` sees two Resend codes; `web/src/features/channels/__tests__/resendProvider.test.tsx` (4). The story 03 fences and the story 04 glass assertion move to the `<provider>:<key_ref>` slot.

## The Resend contract (read from resend.com/docs/api-reference on 2026-09-29)

- Request: `POST https://api.resend.com/emails`; `Authorization: Bearer <key>`; `User-Agent: HoldSpeak` ("All API requests must include a User-Agent header. Requests without this header will be rejected with a 403 status code."); `Content-Type: application/json`; body `{"from": "Name <address>", "to": [...], "cc": [...], "subject", "text"}`.
- Success: `200` `{"id": "49a3999c-..."}`.
- Errors: `{statusCode, name, message}`; the pinned pairs are in `ResendProvider.PINNED`.
- Not verified here: a real send (no key in a lane; story 06's real-account leg).

## Captures

### Captured run — 2026-09-29T20:12:04Z

- **Command:** `uv run --extra test pytest -q -n 6 tests/unit/test_philo10_email_channel.py tests/unit/test_philo10_face_words.py tests/unit/test_philo10_atlas.py tests/unit/test_philo10_send_contract.py tests/unit/test_philo10_cli_channels.py tests/unit/test_philo5_the_loop_r2.py tests/unit/test_philo5_one_decision.py tests/unit/test_philo5_graph_op.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** b3ba01c26beac960f17474e1c3625bf179af3265

```text
bringing up nodes...
bringing up nodes...

........................................................................ [ 22%]
........................................................................ [ 44%]
........................................................................ [ 66%]
........................................................................ [ 89%]
...................................                                      [100%]
323 passed in 40.28s
```

### Captured run — 2026-09-29T20:12:53Z

- **Command:** `bash -c cd web && npx vitest run src/features/channels`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** b3ba01c26beac960f17474e1c3625bf179af3265

```text

 RUN  v4.1.9 /Users/karol/dev/tools/wt-philo-10-07/web


 Test Files  2 passed (2)
      Tests  20 passed (20)
   Start at  14:12:53
   Duration  911ms (transform 622ms, setup 122ms, import 879ms, tests 287ms, environment 381ms)
```

### Captured run — 2026-09-29T20:12:54Z

- **Command:** `uv run python scripts/check_web_baseline.py --run`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** b3ba01c26beac960f17474e1c3625bf179af3265

```text
Running vitest...

=== Web baseline report ===

HEALED (5):
  src/desk/__tests__/containerQueryLaw.test.ts > HS-129-06 container-query law > keeps viewport-width media limited to shell exceptions
  src/desk/__tests__/writeReceiptGuard.test.ts > HS-132-06 swallowed-write guard > keeps every desk write out of a bare catch
  src/desk/components/InlineEditor.test.tsx > HS-129-08 editor windows > hosts note editing in its open pullout
  src/desk/components/MicButton.test.tsx > MicButton surfaces named refusals (HS-132-05) > never claims retention the session cannot prove
  src/desk/components/__tests__/workbenchAutomations.test.tsx > Workbench STARTS WHEN automations > tests without delivering work, then enables and pauses the trigger

BRANCH-NEW (1):
  BRANCH-NEW: src/pages/cores/__tests__/ModelLibraryCore.test.tsx > ModelLibraryCore > keeps radio selection inert, restores Add focus, and maps Mod+Enter to the sole action

Suite totals: 2969 passed, 1 failed, 0 skipped

VERDICT: BRANCH-NEW FAILURES: 1
```

### Captured run — 2026-09-29T20:13:40Z

- **Command:** `uv run python scripts/check_web_baseline.py --run`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** b3ba01c26beac960f17474e1c3625bf179af3265

```text
Running vitest...

=== Web baseline report ===

HEALED (5):
  src/desk/__tests__/containerQueryLaw.test.ts > HS-129-06 container-query law > keeps viewport-width media limited to shell exceptions
  src/desk/__tests__/writeReceiptGuard.test.ts > HS-132-06 swallowed-write guard > keeps every desk write out of a bare catch
  src/desk/components/InlineEditor.test.tsx > HS-129-08 editor windows > hosts note editing in its open pullout
  src/desk/components/MicButton.test.tsx > MicButton surfaces named refusals (HS-132-05) > never claims retention the session cannot prove
  src/desk/components/__tests__/workbenchAutomations.test.tsx > Workbench STARTS WHEN automations > tests without delivering work, then enables and pauses the trigger

Suite totals: 2970 passed, 0 failed, 0 skipped

VERDICT: baseline-subset, zero branch-new
```

### Captured run — 2026-09-29T20:14:17Z

- **Command:** `uv run --extra test pytest -q tests/e2e/test_philo10_04_send_face_glass.py::TestSendEmailGlass tests/e2e/test_philo10_04_send_face_glass.py::TestSendFaceGlass::test_the_destinations_group`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** b3ba01c26beac960f17474e1c3625bf179af3265

```text
......                                                                   [100%]
6 passed in 106.90s (0:01:46)
```

## Notes on the captures

- The first web-baseline capture (20:12:54Z) named one BRANCH-NEW failure in `src/pages/cores/__tests__/ModelLibraryCore.test.tsx` (focus after Add). That file does not import the channel face; alone it passed 8/8 three times, and the next full baseline capture (20:13:40Z) is zero branch-new. Recorded as a load flake, not paid here.
- The glass run is the story 04 SendGrid email boards and the destinations group at 1440 and 393 on this branch's bundle: the provider-aware face keeps them green. No Resend glass board was drawn (the Resend face is fenced by vitest).

### Captured run — 2026-09-29T21:34:23Z

- **Command:** `uv run --extra test pytest -q -n 6 tests/unit/test_philo10_email_channel.py tests/unit/test_philo10_face_words.py tests/unit/test_philo10_atlas.py tests/unit/test_philo_graph_atlas.py tests/unit/test_philo9_atlas.py tests/unit/test_philo10_send_contract.py tests/unit/test_philo10_cli_channels.py tests/unit/test_philo5_the_loop_r2.py tests/unit/test_philo5_one_decision.py tests/unit/test_philo5_graph_op.py tests/unit/test_graph_walk_calibration.py tests/unit/test_graph_walk_first_paint.py tests/unit/test_graph_walk_http_fault.py tests/unit/test_graph_walk_producer_clock.py tests/unit/test_philo10_rig_op.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a6a5d649cf6ca6dcabc5797570a586619e142262

```text
bringing up nodes...
bringing up nodes...

........................................................................ [ 12%]
........................................................................ [ 25%]
........................................................................ [ 38%]
........................................................................ [ 51%]
........................................................................ [ 64%]
........................................................................ [ 77%]
........................................................................ [ 90%]
..................................................                       [100%]
554 passed in 135.15s (0:02:15)
```

### Captured run — 2026-09-29T21:36:46Z

- **Command:** `bash -c cd web && npx vitest run src/features/channels`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a6a5d649cf6ca6dcabc5797570a586619e142262

```text

 RUN  v4.1.9 /Users/karol/dev/tools/wt-philo-10-07/web


 Test Files  2 passed (2)
      Tests  20 passed (20)
   Start at  15:36:47
   Duration  935ms (transform 613ms, setup 127ms, import 895ms, tests 285ms, environment 406ms)
```

### Captured run — 2026-09-29T21:36:48Z

- **Command:** `uv run python scripts/check_web_baseline.py --run`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a6a5d649cf6ca6dcabc5797570a586619e142262

```text
Running vitest...

=== Web baseline report ===

HEALED (5):
  src/desk/__tests__/containerQueryLaw.test.ts > HS-129-06 container-query law > keeps viewport-width media limited to shell exceptions
  src/desk/__tests__/writeReceiptGuard.test.ts > HS-132-06 swallowed-write guard > keeps every desk write out of a bare catch
  src/desk/components/InlineEditor.test.tsx > HS-129-08 editor windows > hosts note editing in its open pullout
  src/desk/components/MicButton.test.tsx > MicButton surfaces named refusals (HS-132-05) > never claims retention the session cannot prove
  src/desk/components/__tests__/workbenchAutomations.test.tsx > Workbench STARTS WHEN automations > tests without delivering work, then enables and pauses the trigger

Suite totals: 2970 passed, 0 failed, 0 skipped

VERDICT: baseline-subset, zero branch-new
```

### Captured run — 2026-09-29T21:37:21Z

- **Command:** `uv run --extra test pytest -q tests/e2e/test_philo10_04_send_face_glass.py::TestSendEmailGlass tests/e2e/test_philo10_04_send_face_glass.py::TestSendFaceGlass::test_the_destinations_group`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a6a5d649cf6ca6dcabc5797570a586619e142262

```text
......                                                                   [100%]
6 passed in 107.41s (0:01:47)
```

## Round two — Codex Astra r1 on #701 DO-NOT-RATIFY (`checks/story-07-built-astra-r1.md`), every condition paid

### P1: FAILED only on Resend's whole, consistent error envelope

- `resend_error(raw, status)` (`holdspeak/services/channel_email.py`) now returns `(name, message)` only for a JSON object with an integer `statusCode` (a bool is refused) EQUAL to the HTTP status, a string `name` and a string `message`; anything else is None. `interpret` is FAILED only when that envelope is present AND `(status, name)` is on `PINNED`. The domain / test-sender discriminators match only a pinned `403 validation_error` with a string message. The catch-all `resend_forbidden` for any named 403 is gone: `resend_forbidden` is now the pinned `(403, invalid_permission)` and `(403, validation_error)` pairs only. An unknown name, a name of another status, a malformed or inconsistent body is UNKNOWN `unpinned_<status>`.
- Fences: `test_c7_r1_an_answer_that_is_not_resends_consistent_envelope_is_unknown_never_failed` (11 cases) through the REAL save → prepare → send routes (a prepared send, then the send by `send_id`), with the read-back and the history row (outcome unknown). Codex's three probes are the first three cases (`403-unpinned-name` `{"name":"edge_error"}`, `429-status-mismatch` statusCode 500 + `rate_limit_exceeded`, `403-object-message` an object message with the domain text).
- Red before the fix (on this branch's 1ac9a5f3 code, the fences added first): **8 failed, 3 passed** — `403-unpinned-name`, `403-no-status`, `403-status-bool`, `403-object-message`, `429-status-mismatch`, `403-status-string`, `403-no-message`, `403-unknown-name` settled `failed`. The three that passed before (`422-name-of-another-status`, `400-array-body`, `403-name-not-string`) were already UNKNOWN. Green after: in the 554-test capture above (`-k c7` collects 41).

### P2: Resend on the atlas, at 1440 and 393

- The rig (`scripts/graph_walk.py`): the `cli_runner` script may now name `https` answers; `_install_email_edge` sets `channel_email.HTTPS_HANDLER` to a RECORDING edge and `channel_email.KEY_STORE` to a MEMORY store inside the hub's own process (the OS keychain is never read or written). Each request is logged as argv `["https", method, host, path]` with the body sha256, the auth scheme and the User-Agent, never the key (fenced: `test_the_email_edge_records_before_it_answers_and_never_the_key`; and `test_every_email_case_boots_the_memory_key_store_before_a_key_is_saved`). Scripts: `tests/fixtures/philo10_atlas/resend-accepted.json`, `resend-unknown.json`.
- Five face cases (`assets/story-07-proof/add_resend_cases.py`, appended to `atlas-phase10.json`; 27 → 32 cases; `excluded.p10.resend_op` names why they have no `.op` twin): `resend_setup` (the Room's Add destination → the form; Email, then Resend by the select's own type-ahead; the key row reads `Resend key` and `SET`; Save; the row reads `API.RESEND.COM`; the hub holds provider resend, key name `resend-karol@example.com`; zero requests), `resend_accepted` (ACCEPTED BY RESEND; proof provider, word and id; one history row; ONE `https POST api.resend.com /emails`), `resend_prepared` (PREPARED → ACCEPTED BY RESEND on the prepared row), `resend_history` (the DELIVERY row: ACCEPTED BY RESEND + `ID re-atlas-4ef9-0001`), `resend_unknown` (a 503 page: RESULT UNKNOWN, receipt indeterminate; `Check priya@example.com` whose `data-href` is `https://resend.com/emails`).
- Two small face changes the walk needed: the Check verbs carry `data-href` (the far side, observable); after a Save the Destinations group scrolls itself into view (at 393 the closed form left the new row above the window: the first walk of `resend_setup` at 393 failed "outside the viewport").
- Retained (every shot looked at, 20 of 20): `assets/story-07-shots/resend-r2/` — 10/10 pass. The whole Phase 10 file on this tree, observations only: `assets/story-07-shots/p10-all-r2/` — **52/52 pass** (the story 05 cases unchanged by the data-href and scroll changes).

### The orchestrator's full-suite reds on 1ac9a5f3b, classified

- `tests/unit/test_philo_graph_atlas.py::test_every_source_reference_lands_on_its_symbol[atlas-phase10.json]` — BRANCH-NEW, mine: channel_service.py grew four lines, and `def send` / `def discard` moved (396 → 400, 376 → 380). Paid: `add_resend_cases.py` anchors every state source again from the tree (it also moved the graph_walk.py anchor 2744 when the rig grew). Green in the capture above.
- `tests/unit/test_one_path_cardinality.py::test_cancellation_after_provider_return_is_one_child_one_receipt_one_physical_attempt` — NOT branch-new: serial, isolated HOME, 3/3 pass on this branch and 3/3 pass on an export of origin/main 05d01ffb. The test drives decision promotion's inference runner (no channel code). A load flake of the parallel full run.
- CI "DeskOS Web Quality", `web/src/desk/chair/arrivalAttention.test.tsx:119` (17 rows expected after Show all, 5 got) — NOT branch-new: the branch touches no file under `web/src/desk/chair/` and nothing it imports; 3/3 pass on this branch and 3/3 on the 05d01ffb export (with its own node_modules copy); the same job was green on main's last three completed runs (98ea2cfa, 920e6189, 14866bc7); main's run at 05d01ffb is still queued, so CI inheritance is not proved. The CI log shows the test took 717 ms (a loaded runner): a timing flake, not paid here.
