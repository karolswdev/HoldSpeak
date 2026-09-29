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
