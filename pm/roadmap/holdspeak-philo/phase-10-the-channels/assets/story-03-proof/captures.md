# Proof captures — PHILO-10-03 The email channel (a provider interface)

- **Story:** PHILO-10-03 - The email channel — a provider interface
- **Status:** in-progress (criteria 1–6 proven here; criterion 7, the owner's real-account send (Q6), is owed)
- **Date:** 2026-09-29
- **Branch:** `feat/philo-10-03` from main `eee4d9b2`, merged with main `84657927` (#694). Story 02 (#695) is not merged: this branch threads the network seam itself; the CLI seam's matching `build_gated_connector(principal, parent_operation_id, broker)` lines are the same shape as #695's, so that merge is mechanical.
- **Design:** `design/send-lifecycle.md` sections 3, 4, 4a, 6, 8 and Codex Astra r3's conditions, built as ratified.
- **Red first:** criterion 3's kernel fence and criterion 1's two-bodies probe are RED on an export of main `84657927` (captured below). The rest is new capability (main has no email code: the fence file fails to import there, captured); each behavioural rule is turned RED by a deliberate mutation of the real code (twelve, captured).

## What was built

- **The contract** (`holdspeak/services/channel_email.py`): `EmailProvider` (a Protocol: `name`, `host`, `limits`, `serialize`, `preview`, `plan`, `interpret`) and `EMAIL_PROVIDERS` (one table, SendGrid only). `EmailChannel` is registered in `CHANNELS["email"]`.
- **One byte contract:** at prepare, `serialize` makes SendGrid's exact `POST /v3/mail/send` JSON (text/plain only) from the destination's frozen sender and recipients and the published update; those bytes are the frozen payload. `preview` parses From, To, Cc, Subject and the text back from them. Dispatch refuses a plan whose request body is not the frozen bytes (`plan_refused`).
- **The network seam:** `GatedOperation.outbound(…, data_classes, payload_digest, subject_refs)` → `build_gated_connector(…, principal, parent_operation_id, broker)` → `_route` → `PermissionGate.open_outbound_socket(…)` → `run_external_egress(…, subject_refs)`. `kernel/egress_material.payload_digest_of`: `{"payload_digest": <sha256>}` is bound as itself (any other material is hashed as before). The email egress is a child of the send, under the send's principal, through its broker; its journal refs carry `destination:<id>`, `egress:api.sendgrid.com:443`, `data-class:email_message`, `payload:sha256:<digest>`. The native result now also records `payload_digest`.
- **Every egress caller:** `run_external_egress` records `sanitized_error(exc)` = the exception's type only (was `f"{type(exc).__name__}: {exc}"` at `external_egress.py:290`).
- **Key custody:** `NativeEmailKeyStore` (macOS Keychain, Secret Service, Windows Credential Manager; a chainer's first native backend; anything else `email_key_store_not_native`); `KEY_STORE` is the injection point (tests: `MemoryEmailKeyStore`). `channel.save_email_key` (config, owner only, owner press, admitted, HTTP only `PUT /api/channels/email-keys/{key_ref}`): the key is a HELD input, never an argument, so it reaches neither the kernel request nor its envelope digest. The key is read before the boundary (`email_key_missing`, `email_key_store_not_native`, `email_key_store_locked` refused by name) and again only in the dispatch opener `transmit`, which sets `Authorization`.
- **The opener:** an `OpenerDirector` with the HTTPS handler (`HTTPS_HANDLER`, the test edge), a redirect handler that refuses, and the error processors; the URL must be the admitted host and port (`url_not_admitted`); every failure leaves as `EmailTransportError(code)` raised after its handler (no text, no context); the error excerpt is bounded (64 KiB, 10 errors, 500 characters), the key removed, then cut to 240 characters before the payload-excerpt scan.
- **Outcomes (SendGrid):** `202` + `X-Message-Id` → `sent`, proof `{provider, message_id, word: "ACCEPTED BY SENDGRID", scope: "accepted for processing, not delivery"}`; FAILED only with SendGrid's own `errors` answer AND a pinned status: `400 invalid_request`, `401 api_key_invalid`, `403` split `sender_not_verified` (discriminator "verified sender identity") / `sendgrid_forbidden`, `413 payload_too_large`, `429 rate_limited`; before the request left: `connect_refused`, `dns_failed`, `tls_failed`, the key refusals, `egress_refused` (the kernel refused the child). UNKNOWN: `accepted_without_message_id`, `redirect_refused`, `unpinned_<status>`, `timeout`, `transport_error`, `interrupted`, `reaped`. The pinned strings are PROVISIONAL until the real-account send.
- **Destinations:** `channel.save_destination` takes `channel: "email"` with `provider`, `from_email`, `from_name`, `key_ref`, `to`, `cc`; the account freezes `{provider, from_email, from_name, key_ref}`; refusals by name (`email_provider_unknown`, `email_address_invalid`, `email_key_ref_invalid`, `email_recipients_missing`, `email_recipients_too_many` (20, PROVISIONAL), `email_recipient_duplicate`); `payload_too_large:email` (1 MB, PROVISIONAL) at preview, prepare and the boundary. `channel.check_destination` of an email destination: `ready` or the key refusal, no call to SendGrid.

## Criteria → fences (`tests/unit/test_philo10_email_channel.py`)

| Criterion | Fences | Red |
|---|---|---|
| 1 one egress child; wire bytes = frozen; admitted digest = its digest; two bodies, two digests; another host refused | `test_c1_one_send_is_one_egress_child_…[send_id, inline]`, `test_c1_two_different_bodies_…`, `test_c1_a_request_to_any_other_host_is_refused_by_the_kernel` | main: the probe gives ONE digest for two bodies; M4, M10 |
| 2 outcomes through the real producer; 403 split; redirect not followed, no Authorization to a second host; R1–R6 | `test_c2_each_answer_settles_by_the_pinned_list[19 cases]`, `test_c2_the_two_403_discriminators_map_apart`, `test_c2_r1_…[2]`, `test_c2_r2_…[4]`, `test_c2_r3_…[2]` (a real process killed with SIGKILL), `test_c2_r4_…`, `test_c2_r6_…[2]` | M1, M6, M7, M9, M11 |
| 3 an exception carrying a key and body leaves neither | `test_c3_every_egress_caller_records_a_sanitized_exception`, `test_c3_an_email_transport_exception_…` | main (`external_egress.py:290`); M2, M3 |
| 4 sentinel: no key, no body in the journal, a receipt, a log, an error, a file; the journal's refs | `test_c4_no_key_and_no_body_…`, `test_c4_the_key_is_never_planning_material` | M5 |
| 5 key custody (native stores and reads; fail, chainer without native, file-based refused; memory store only) | `test_c5_a_native_backend_…[3]`, `test_c5_every_other_backend_…[5]`, `test_c5_a_store_that_is_not_native_…[2]`, `test_c5_a_missing_key_…`, `test_c5_the_key_is_held_…` | M8 |
| 6 a second provider: one class, one row, no caller change | `test_c6_a_second_provider_plugs_in_with_one_class_and_one_row` | M12 |
| 7 the real-account send | owed (Q6: his account, a verified sender, his own address) | — |

The real keychain: the `store` fixture replaces `keyring.get_keyring` with a function that fails the test; no fence reached it. The network: `HTTPS_HANDLER` is a canned handler in every fence; the R3 child processes set their own.

## Changed existing tests (and why)

- `tests/unit/test_philo10_send_contract.py`: the channel operations are the nine MCP tools plus `channel.save_email_key` (HTTP only; asserted absent from `tools/list`, its route asserted present).
- `tests/unit/test_philo10_send_recovery.py`: the R6 spy takes `check_before_dispatch(target, **kw)` (the boundary passes the frozen account; the same change as #695).

## Unknown / not verified / not built

- **The real SendGrid answers** (the discriminator text, the `X-Message-Id` header on a real `202`, the limits) are pinned from SendGrid's documentation, not observed: criterion 7.
- **The Room's history face** still shows an email `sent` row with a ✓ under DELIVERED (story 01's words). The ratified story 04 canvas replaces them (`DELIVERY ×N`; the per-channel SENT word ACCEPTED BY SENDGRID); story 04 builds it. The read-back (`channel.sends`, the send answer) already says ACCEPTED BY SENDGRID.
- **The event loop:** on this branch the channel routes still call the service on the event loop; a SendGrid call can hold it up to `TIMEOUT` (30 s). #695's GATE 2 moves `channel.send` to the threadpool; after that merge the email send inherits it.
- **`destination_changed` for email** is not reachable: a destination row never changes its account; an edited sender parks the old row, and a send prepared to it is refused `destination_parked` (fenced).
- **Sender verification through SendGrid** and **a proxy** are not built (BACKLOG rows added).
- `tests/integration/test_actuator_kernel_real_hub.py` (the webhook actuator through a spawned hub) timed out twice in loaded parallel runs on this branch, then passed four times alone and in the final scoped run; it passed once on the main export. Recorded as a timing flake, not a finding.

## Round two (Codex Astra r1 DO-NOT-RATIFY on 0a965dbf, `checks/story-03-built-astra-r1.md`)

| Finding | Paid by | Red at 0a965dbf (captured below, `.tmp/r1_red.sh`) | Mutation |
|---|---|---|---|
| P1 wire debug prints the key and body | `QuietHTTPSHandler` (`channel_email.py`): `debuglevel` 0 on its own connection class, `set_debuglevel` pinned to 0; the global is untouched. Fence `test_r2_global_http_debug_on_prints_no_key_and_no_body` (the REAL edge, an offline socket, `HTTPConnection.debuglevel = 1`, stdout and stderr captured) | FAILED | M13 |
| P1 TLS failure during the body write settled FAILED | `sent_any` on the edge (set just before the first write to a connected socket); `transmit` settles FAILED only when it is False; `_classify` now calls a TLS failure left-unknown. Fence `test_r2_a_failure_is_failed_only_when_no_byte_was_written[5]` | the two write cases FAILED; handshake, refused, DNS pass (FAILED both before and after) | M14 |
| P2 the transmitter embeds SendGrid's transport | `EmailProvider.auth_headers(key)` (only the opener calls it) and `interpret(status, headers, body)` over `HttpAnswer(status, headers, body)`: every header (50, 500 characters) and a 64 KiB body, the key removed; SendGrid parses its own `errors` (`sendgrid_errors`). Fence `test_c6_a_materially_different_provider_…` with a Postmark-like TEST provider (`X-Postmark-Server-Token`, `MessageID` in the JSON body; no Bearer reaches its wire) | FAILED | M15, M16 |
| Finding 6 (the displayed word) | Criterion 2 is unticked: its displayed-word part is story 04's build; criterion 7 stays open (story 06) | — | — |

Not yet done (owed): #695 is not merged at this round (`gh pr view 695`: OPEN; origin/main `84657927`), so its merge, the CLI + email seams checked together, and the event-loop check for the email send come in the next round.

## Proof

### Captured run — 2026-09-29T05:15:14Z

- **Command:** `.tmp/iso.sh .venv/bin/python -m pytest --collect-only -q -p no:cacheprovider tests/unit/test_philo10_email_channel.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 1cf6f2dcc749954d0d18902951095ded09261069

```text
tests/unit/test_philo10_email_channel.py::test_c1_one_send_is_one_egress_child_whose_wire_bytes_and_digest_are_the_frozen_ones[send_id]
tests/unit/test_philo10_email_channel.py::test_c1_one_send_is_one_egress_child_whose_wire_bytes_and_digest_are_the_frozen_ones[inline]
tests/unit/test_philo10_email_channel.py::test_c1_two_different_bodies_are_two_different_admitted_digests
tests/unit/test_philo10_email_channel.py::test_c1_a_request_to_any_other_host_is_refused_by_the_kernel
tests/unit/test_philo10_email_channel.py::test_c2_each_answer_settles_by_the_pinned_list[accepted]
tests/unit/test_philo10_email_channel.py::test_c2_each_answer_settles_by_the_pinned_list[accepted-no-id]
tests/unit/test_philo10_email_channel.py::test_c2_each_answer_settles_by_the_pinned_list[400]
tests/unit/test_philo10_email_channel.py::test_c2_each_answer_settles_by_the_pinned_list[401]
tests/unit/test_philo10_email_channel.py::test_c2_each_answer_settles_by_the_pinned_list[403-sender]
tests/unit/test_philo10_email_channel.py::test_c2_each_answer_settles_by_the_pinned_list[403-other]
tests/unit/test_philo10_email_channel.py::test_c2_each_answer_settles_by_the_pinned_list[413]
tests/unit/test_philo10_email_channel.py::test_c2_each_answer_settles_by_the_pinned_list[429]
tests/unit/test_philo10_email_channel.py::test_c2_each_answer_settles_by_the_pinned_list[400-not-sendgrid]
tests/unit/test_philo10_email_channel.py::test_c2_each_answer_settles_by_the_pinned_list[404]
tests/unit/test_philo10_email_channel.py::test_c2_each_answer_settles_by_the_pinned_list[500]
tests/unit/test_philo10_email_channel.py::test_c2_each_answer_settles_by_the_pinned_list[503]
tests/unit/test_philo10_email_channel.py::test_c2_each_answer_settles_by_the_pinned_list[timeout]
tests/unit/test_philo10_email_channel.py::test_c2_each_answer_settles_by_the_pinned_list[timeout-url]
tests/unit/test_philo10_email_channel.py::test_c2_each_answer_settles_by_the_pinned_list[reset]
tests/unit/test_philo10_email_channel.py::test_c2_each_answer_settles_by_the_pinned_list[refused]
tests/unit/test_philo10_email_channel.py::test_c2_each_answer_settles_by_the_pinned_list[dns]
tests/unit/test_philo10_email_channel.py::test_c2_each_answer_settles_by_the_pinned_list[redirect]
tests/unit/test_philo10_email_channel.py::test_c2_each_answer_settles_by_the_pinned_list[redirect-307]
tests/unit/test_philo10_email_channel.py::test_c2_the_two_403_discriminators_map_apart
tests/unit/test_philo10_email_channel.py::test_c2_r1_a_failed_settle_is_taken_over_as_unknown_and_never_sent_again[send_id]
tests/unit/test_philo10_email_channel.py::test_c2_r1_a_failed_settle_is_taken_over_as_unknown_and_never_sent_again[inline]
tests/unit/test_philo10_email_channel.py::test_c2_r2_the_reaper_settles_a_silent_email_unknown_and_the_replay_answers_it[held-before-the-wire-send_id]
tests/unit/test_philo10_email_channel.py::test_c2_r2_the_reaper_settles_a_silent_email_unknown_and_the_replay_answers_it[held-before-the-wire-inline]
tests/unit/test_philo10_email_channel.py::test_c2_r2_the_reaper_settles_a_silent_email_unknown_and_the_replay_answers_it[held-after-the-wire-send_id]
tests/unit/test_philo10_email_channel.py::test_c2_r2_the_reaper_settles_a_silent_email_unknown_and_the_replay_answers_it[held-after-the-wire-inline]
tests/unit/test_philo10_email_channel.py::test_c2_r4_a_take_over_that_wins_leaves_the_reaper_nothing
tests/unit/test_philo10_email_channel.py::test_c2_r6_reaped_before_the_boundary_sends_nothing[send_id]
tests/unit/test_philo10_email_channel.py::test_c2_r6_reaped_before_the_boundary_sends_nothing[inline]
tests/unit/test_philo10_email_channel.py::test_c3_every_egress_caller_records_a_sanitized_exception
tests/unit/test_philo10_email_channel.py::test_c3_an_email_transport_exception_carrying_the_key_and_body_leaves_neither
tests/unit/test_philo10_email_channel.py::test_c4_no_key_and_no_body_in_the_journal_a_receipt_a_log_an_error_or_a_file
tests/unit/test_philo10_email_channel.py::test_c4_the_key_is_never_planning_material
tests/unit/test_philo10_email_channel.py::test_c5_a_native_backend_stores_and_reads_the_key[keyring.backends.macOS-Keyring]
tests/unit/test_philo10_email_channel.py::test_c5_a_native_backend_stores_and_reads_the_key[keyring.backends.SecretService-Keyring]
tests/unit/test_philo10_email_channel.py::test_c5_a_native_backend_stores_and_reads_the_key[keyring.backends.Windows-WinVaultKeyring]
tests/unit/test_philo10_email_channel.py::test_c5_every_other_backend_is_refused_not_native[fail]
tests/unit/test_philo10_email_channel.py::test_c5_every_other_backend_is_refused_not_native[chainer-without-native]
tests/unit/test_philo10_email_channel.py::test_c5_every_other_backend_is_refused_not_native[keyrings.alt-file]
tests/unit/test_philo10_email_channel.py::test_c5_every_other_backend_is_refused_not_native[keyrings.alt-encrypted]
tests/unit/test_philo10_email_channel.py::test_c5_every_other_backend_is_refused_not_native[null]
tests/unit/test_philo10_email_channel.py::test_c5_a_store_that_is_not_native_refuses_the_save_and_the_send_before_anything_leaves[send_id]
tests/unit/test_philo10_email_channel.py::test_c5_a_store_that_is_not_native_refuses_the_save_and_the_send_before_anything_leaves[inline]
tests/unit/test_philo10_email_channel.py::test_c5_a_missing_key_refuses_by_name_and_the_check_says_so
tests/unit/test_philo10_email_channel.py::test_c5_the_key_is_held_never_an_argument_and_the_owner_alone_saves_it
tests/unit/test_philo10_email_channel.py::test_the_destination_freezes_the_sender_and_refuses_bad_addresses_by_name
tests/unit/test_philo10_email_channel.py::test_an_edited_sender_parks_the_destination_and_refuses_the_prepared_send
tests/unit/test_philo10_email_channel.py::test_a_request_over_the_size_limit_is_refused_by_name
tests/unit/test_philo10_email_channel.py::test_c6_a_second_provider_plugs_in_with_one_class_and_one_row
tests/unit/test_philo10_email_channel.py::test_c2_r3_a_restart_during_an_email_send_ends_unknown_once_and_never_sends_again[killed-before-the-wire]
tests/unit/test_philo10_email_channel.py::test_c2_r3_a_restart_during_an_email_send_ends_unknown_once_and_never_sends_again[killed-after-the-wire]

55 tests collected in 0.23s
```

### Captured run — 2026-09-29T05:15:21Z

- **Command:** `.tmp/iso.sh zsh -c .venv/bin/python -m pytest -q -p no:cacheprovider -n 8 -rf --basetemp=$HOME/pt tests/unit/test_philo10_email_channel.py tests/unit/test_philo10_send_contract.py tests/unit/test_philo10_send_recovery.py tests/unit/test_philo10_send_restart.py tests/unit/test_philo10_rig_op.py tests/unit/test_external_egress_kernel.py tests/unit/test_connector_runtime.py tests/unit/test_gated_connector.py tests/unit/test_webhook_post_actuator.py tests/unit/test_github_issue_actuator.py tests/unit/test_hs151_honest_dispatch.py tests/unit/test_kernel_effect_fence.py tests/unit/test_live_proposals.py tests/unit/test_slack_export.py tests/unit/test_subprocess_exec_kernel.py tests/unit/test_voice_macro_connector.py tests/unit/test_thread_tool_gate.py tests/unit/test_694_thread_never_sends.py tests/unit/test_api_surface.py tests/unit/test_mcp_sidecar_doc_drift.py tests/unit/test_doc_drift_guard.py tests/unit/test_philo_graph_atlas.py tests/unit/test_kernel_broker.py tests/integration/test_actuator_kernel_real_hub.py tests/integration/test_web_companion_slack.py tests/integration/test_web_companion_webhook.py tests/integration/test_web_slack_export.py tests/integration/test_kernel_real_hub.py tests/integration/test_principal_separation.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 1cf6f2dcc749954d0d18902951095ded09261069

```text
bringing up nodes...
bringing up nodes...

........................................................................ [ 14%]
........................................................................ [ 29%]
........................................................................ [ 44%]
........................................................................ [ 59%]
........................................................................ [ 73%]
........................................................................ [ 88%]
........................................................                 [100%]
488 passed in 76.10s (0:01:16)
```

### Captured run — 2026-09-29T05:16:39Z

- **Command:** `zsh .tmp/main_red.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 1cf6f2dcc749954d0d18902951095ded09261069

```text
EXPORT HEAD: 84657927decfa9577a1290b1d4750cdc657fecba
== 1. the kernel fence for every egress caller (external_egress.py:290)
            raise RuntimeError(f"POST failed; Authorization: Bearer {KEY}; body={SENTINEL}")
>       assert result["error"] == "RuntimeError"
E       AssertionError: assert 'RuntimeError...gv-or-receipt' == 'RuntimeError'
E         
E         - RuntimeError
E         + RuntimeError: POST failed; Authorization: Bearer SG.syntheticKEY7c1e0000abcd.neverLeavesTheOpener0000; body=SENTINEL-7f3a-body-never-in-argv-or-receipt
1 failed, 54 deselected in 1.60s
== 2. the email fences on main (main has no email code)
E       ImportError: cannot import name 'channel_email' from 'holdspeak.services' (/private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/c59536e9-4c14-410c-8d54-e0c2beed10bc/scratchpad/main1003/holdspeak/services/__init__.py)
tests/unit/test_philo10_email_channel.py:110: ImportError
E       ImportError: cannot import name 'channel_email' from 'holdspeak.services' (/private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/c59536e9-4c14-410c-8d54-e0c2beed10bc/scratchpad/main1003/holdspeak/services/__init__.py)
tests/unit/test_philo10_email_channel.py:110: ImportError
== 3. two bodies through main's network seam
seam takes the frozen digest: False
admitted digests: ['sha256:f75ec0c339a1c627b31bfe7c468a22342bceec5383531b2057e6e6cfc4b3ee1c', 'sha256:f75ec0c339a1c627b31bfe7c468a22342bceec5383531b2057e6e6cfc4b3ee1c']
TWO BODIES -> ONE DIGEST (red)
== 3b. the same probe on this branch
seam takes the frozen digest: True
admitted digests: ['sha256:66963099c7df349259067f4546b42de73017c0d6c70037cb78b09f0eb132fb77', 'sha256:d5fbcb818beafbe0221061528e9fed9af4e3d1a4436e20c770a7f3f30c7b92e0']
TWO BODIES -> TWO DIGESTS (green)
```

### Captured run — 2026-09-29T05:16:47Z

- **Command:** `.tmp/iso.sh .venv/bin/python pm/roadmap/holdspeak-philo/phase-10-the-channels/assets/story-03-proof/mutations.py.txt`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 1cf6f2dcc749954d0d18902951095ded09261069

```text
BASELINE (no mutation): rc=0 55 passed in 73.38s (0:01:13)
RED   M1 redirects followed (the default handler): rc=1 1 failed, 53 deselected in 1.94s
RED   M2 the kernel records the exception's text (main's external_egress.py:290): rc=1 1 failed, 54 deselected in 1.12s
RED   M3 the opener lets a raw transport exception out: rc=1 1 failed, 54 deselected in 2.29s
RED   M4 the network seam hashes the destination only (main's connector_runtime.py:215): rc=1 1 failed, 50 deselected in 2.00s
RED   M5 the key becomes planning material (read at plan time, held by the sender): rc=1 1 failed, 54 deselected in 2.46s
RED   M6 any 4xx is FAILED (no pinned list): rc=1 1 failed, 8 passed, 36 deselected in 12.68s
RED   M7 403 is not split by its discriminator: rc=1 1 failed, 1 passed, 52 deselected in 4.26s
RED   M8 the key store admits any backend: rc=1 1 failed, 48 deselected in 0.81s
RED   M9 202 without X-Message-Id is SENT: rc=1 1 failed, 54 deselected in 2.85s
RED   M10 the egress child has no parent (the send's operation is not threaded): rc=1 1 failed, 53 deselected in 2.69s
RED   M11 a take-over sends again: rc=1 1 failed, 53 deselected in 2.50s
RED   M12 the channel calls SendGrid directly (no registry row): rc=1 1 failed, 54 deselected in 2.51s
MUTATIONS: 12/12 turned their fences red
```

### Captured run — 2026-09-29T05:18:59Z

- **Command:** `zsh .tmp/docs_checks.sh`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 1cf6f2dcc749954d0d18902951095ded09261069

```text
== scripts/gen_operations_json.py --check
OK docs/generated/operations.json
== scripts/gen_mcp_sidecar_doc.py --check
wrote docs/MCP_SIDECAR.md
  246 tools across 43 families
== scripts/check_docs.py
Documentation navigation: 70 files checked; local targets and Markdown headings resolve.
== scripts/philo_repository_census.py --check
Repository census: 5 outputs verified.
== scripts/philo_api_reference.py --check
API reference drift: docs/generated/api-reference.json
== scripts/philo_openapi_reference.py --check
OpenAPI: 580 paths
== scripts/philo_boundary_census.py --check
Boundary candidate census checked
== scripts/philo_doctor_reference.py --check
Doctor reference: 41 check functions
== scripts/philo_config_reference.py --check
Configuration declaration reference is current
== scripts/philo_graph_reference.py --check
graph join checked: docs/generated/graph.json; 14 subtype conflict note(s)
== scripts/validate_architecture.py
Architecture metadata: 4 shard(s), 147 record(s)
Architecture metadata validation passed.
== scripts/generate_capability_docs.py --check
Architecture documentation checked (10 outputs).
== scripts/check_doc_coverage.py --check
Documentation coverage checked.
== scripts/residual_census.py --check
RESIDUAL FENCE GREEN: 240 identities match /Users/karol/dev/tools/wt-philo-10-03
DOCS RC=1
```

### Captured run — 2026-09-29T05:19:45Z

- **Command:** `.tmp/iso.sh .venv/bin/python pm/roadmap/holdspeak-philo/phase-10-the-channels/assets/story-03-proof/redact-bench.py.txt`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 1cf6f2dcc749954d0d18902951095ded09261069

```text
email redaction worst of 5 over a 999999 byte body: 0.019 s (gate: < 1.0 s)
```

### Captured run — 2026-09-29T05:20:26Z

- **Command:** `zsh .tmp/docs_checks.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** b8e985ac6d858bfe6227fa5c068c4e8b393c30d0

```text
== scripts/gen_operations_json.py --check
OK docs/generated/operations.json
== scripts/gen_mcp_sidecar_doc.py --check
wrote docs/MCP_SIDECAR.md
  246 tools across 43 families
== scripts/check_docs.py
Documentation navigation: 70 files checked; local targets and Markdown headings resolve.
== scripts/philo_repository_census.py --check
Repository census: 5 outputs verified.
== scripts/philo_api_reference.py --check
API reference checked
== scripts/philo_openapi_reference.py --check
OpenAPI: 580 paths
== scripts/philo_boundary_census.py --check
Boundary candidate census checked
== scripts/philo_doctor_reference.py --check
Doctor reference: 41 check functions
== scripts/philo_config_reference.py --check
Configuration declaration reference is current
== scripts/philo_graph_reference.py --check
graph join checked: docs/generated/graph.json; 14 subtype conflict note(s)
== scripts/validate_architecture.py
Architecture metadata: 4 shard(s), 147 record(s)
Architecture metadata validation passed.
== scripts/generate_capability_docs.py --check
Architecture documentation checked (10 outputs).
== scripts/check_doc_coverage.py --check
Documentation coverage checked.
== scripts/residual_census.py --check
RESIDUAL FENCE GREEN: 240 identities match /Users/karol/dev/tools/wt-philo-10-03
DOCS RC=0
```

## Round two captured runs

The first mutation run below shows M13 GREEN: it removed only one of the edge's two local debug pins (the handler's `debuglevel=0` still held). M13 was strengthened to remove both; the second run shows 16/16 RED.

### Captured run — 2026-09-29T05:38:25Z

- **Command:** `zsh .tmp/r1_red.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 9c016b2a5a4faaca1e35469761ba5fca2284c2a5

```text
EXPORT HEAD: 0a965dbf
PASSED tests/unit/test_philo10_email_channel.py::test_c2_r2_the_reaper_settles_a_silent_email_unknown_and_the_replay_answers_it[held-before-the-wire-send_id]
PASSED tests/unit/test_philo10_email_channel.py::test_c2_r2_the_reaper_settles_a_silent_email_unknown_and_the_replay_answers_it[held-before-the-wire-inline]
PASSED tests/unit/test_philo10_email_channel.py::test_c2_r2_the_reaper_settles_a_silent_email_unknown_and_the_replay_answers_it[held-after-the-wire-send_id]
PASSED tests/unit/test_philo10_email_channel.py::test_c2_r2_the_reaper_settles_a_silent_email_unknown_and_the_replay_answers_it[held-after-the-wire-inline]
PASSED tests/unit/test_philo10_email_channel.py::test_r2_a_failure_is_failed_only_when_no_byte_was_written[tls-handshake-ssl-0-failed-tls_failed]
PASSED tests/unit/test_philo10_email_channel.py::test_r2_a_failure_is_failed_only_when_no_byte_was_written[connection-refused-refused-0-failed-connect_refused]
PASSED tests/unit/test_philo10_email_channel.py::test_r2_a_failure_is_failed_only_when_no_byte_was_written[dns-dns-0-failed-dns_failed]
FAILED tests/unit/test_philo10_email_channel.py::test_c6_a_materially_different_provider_plugs_in_with_one_class_and_one_row
FAILED tests/unit/test_philo10_email_channel.py::test_r2_global_http_debug_on_prints_no_key_and_no_body
FAILED tests/unit/test_philo10_email_channel.py::test_r2_a_failure_is_failed_only_when_no_byte_was_written[tls-during-the-body-write-None-2-unknown-tls_failed]
FAILED tests/unit/test_philo10_email_channel.py::test_r2_a_failure_is_failed_only_when_no_byte_was_written[tls-during-the-header-write-None-1-unknown-tls_failed
4 failed, 7 passed, 50 deselected in 10.19s
```

### Captured run — 2026-09-29T05:38:36Z

- **Command:** `.tmp/iso.sh .venv/bin/python -m pytest --collect-only -q -p no:cacheprovider tests/unit/test_philo10_email_channel.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 9c016b2a5a4faaca1e35469761ba5fca2284c2a5

```text
tests/unit/test_philo10_email_channel.py::test_c1_one_send_is_one_egress_child_whose_wire_bytes_and_digest_are_the_frozen_ones[send_id]
tests/unit/test_philo10_email_channel.py::test_c1_one_send_is_one_egress_child_whose_wire_bytes_and_digest_are_the_frozen_ones[inline]
tests/unit/test_philo10_email_channel.py::test_c1_two_different_bodies_are_two_different_admitted_digests
tests/unit/test_philo10_email_channel.py::test_c1_a_request_to_any_other_host_is_refused_by_the_kernel
tests/unit/test_philo10_email_channel.py::test_c2_each_answer_settles_by_the_pinned_list[accepted]
tests/unit/test_philo10_email_channel.py::test_c2_each_answer_settles_by_the_pinned_list[accepted-no-id]
tests/unit/test_philo10_email_channel.py::test_c2_each_answer_settles_by_the_pinned_list[400]
tests/unit/test_philo10_email_channel.py::test_c2_each_answer_settles_by_the_pinned_list[401]
tests/unit/test_philo10_email_channel.py::test_c2_each_answer_settles_by_the_pinned_list[403-sender]
tests/unit/test_philo10_email_channel.py::test_c2_each_answer_settles_by_the_pinned_list[403-other]
tests/unit/test_philo10_email_channel.py::test_c2_each_answer_settles_by_the_pinned_list[413]
tests/unit/test_philo10_email_channel.py::test_c2_each_answer_settles_by_the_pinned_list[429]
tests/unit/test_philo10_email_channel.py::test_c2_each_answer_settles_by_the_pinned_list[400-not-sendgrid]
tests/unit/test_philo10_email_channel.py::test_c2_each_answer_settles_by_the_pinned_list[404]
tests/unit/test_philo10_email_channel.py::test_c2_each_answer_settles_by_the_pinned_list[500]
tests/unit/test_philo10_email_channel.py::test_c2_each_answer_settles_by_the_pinned_list[503]
tests/unit/test_philo10_email_channel.py::test_c2_each_answer_settles_by_the_pinned_list[timeout]
tests/unit/test_philo10_email_channel.py::test_c2_each_answer_settles_by_the_pinned_list[timeout-url]
tests/unit/test_philo10_email_channel.py::test_c2_each_answer_settles_by_the_pinned_list[reset]
tests/unit/test_philo10_email_channel.py::test_c2_each_answer_settles_by_the_pinned_list[refused]
tests/unit/test_philo10_email_channel.py::test_c2_each_answer_settles_by_the_pinned_list[dns]
tests/unit/test_philo10_email_channel.py::test_c2_each_answer_settles_by_the_pinned_list[redirect]
tests/unit/test_philo10_email_channel.py::test_c2_each_answer_settles_by_the_pinned_list[redirect-307]
tests/unit/test_philo10_email_channel.py::test_c2_the_two_403_discriminators_map_apart
tests/unit/test_philo10_email_channel.py::test_c2_r1_a_failed_settle_is_taken_over_as_unknown_and_never_sent_again[send_id]
tests/unit/test_philo10_email_channel.py::test_c2_r1_a_failed_settle_is_taken_over_as_unknown_and_never_sent_again[inline]
tests/unit/test_philo10_email_channel.py::test_c2_r2_the_reaper_settles_a_silent_email_unknown_and_the_replay_answers_it[held-before-the-wire-send_id]
tests/unit/test_philo10_email_channel.py::test_c2_r2_the_reaper_settles_a_silent_email_unknown_and_the_replay_answers_it[held-before-the-wire-inline]
tests/unit/test_philo10_email_channel.py::test_c2_r2_the_reaper_settles_a_silent_email_unknown_and_the_replay_answers_it[held-after-the-wire-send_id]
tests/unit/test_philo10_email_channel.py::test_c2_r2_the_reaper_settles_a_silent_email_unknown_and_the_replay_answers_it[held-after-the-wire-inline]
tests/unit/test_philo10_email_channel.py::test_c2_r4_a_take_over_that_wins_leaves_the_reaper_nothing
tests/unit/test_philo10_email_channel.py::test_c2_r6_reaped_before_the_boundary_sends_nothing[send_id]
tests/unit/test_philo10_email_channel.py::test_c2_r6_reaped_before_the_boundary_sends_nothing[inline]
tests/unit/test_philo10_email_channel.py::test_c3_every_egress_caller_records_a_sanitized_exception
tests/unit/test_philo10_email_channel.py::test_c3_an_email_transport_exception_carrying_the_key_and_body_leaves_neither
tests/unit/test_philo10_email_channel.py::test_c4_no_key_and_no_body_in_the_journal_a_receipt_a_log_an_error_or_a_file
tests/unit/test_philo10_email_channel.py::test_c4_the_key_is_never_planning_material
tests/unit/test_philo10_email_channel.py::test_c5_a_native_backend_stores_and_reads_the_key[keyring.backends.macOS-Keyring]
tests/unit/test_philo10_email_channel.py::test_c5_a_native_backend_stores_and_reads_the_key[keyring.backends.SecretService-Keyring]
tests/unit/test_philo10_email_channel.py::test_c5_a_native_backend_stores_and_reads_the_key[keyring.backends.Windows-WinVaultKeyring]
tests/unit/test_philo10_email_channel.py::test_c5_every_other_backend_is_refused_not_native[fail]
tests/unit/test_philo10_email_channel.py::test_c5_every_other_backend_is_refused_not_native[chainer-without-native]
tests/unit/test_philo10_email_channel.py::test_c5_every_other_backend_is_refused_not_native[keyrings.alt-file]
tests/unit/test_philo10_email_channel.py::test_c5_every_other_backend_is_refused_not_native[keyrings.alt-encrypted]
tests/unit/test_philo10_email_channel.py::test_c5_every_other_backend_is_refused_not_native[null]
tests/unit/test_philo10_email_channel.py::test_c5_a_store_that_is_not_native_refuses_the_save_and_the_send_before_anything_leaves[send_id]
tests/unit/test_philo10_email_channel.py::test_c5_a_store_that_is_not_native_refuses_the_save_and_the_send_before_anything_leaves[inline]
tests/unit/test_philo10_email_channel.py::test_c5_a_missing_key_refuses_by_name_and_the_check_says_so
tests/unit/test_philo10_email_channel.py::test_c5_the_key_is_held_never_an_argument_and_the_owner_alone_saves_it
tests/unit/test_philo10_email_channel.py::test_the_destination_freezes_the_sender_and_refuses_bad_addresses_by_name
tests/unit/test_philo10_email_channel.py::test_an_edited_sender_parks_the_destination_and_refuses_the_prepared_send
tests/unit/test_philo10_email_channel.py::test_a_request_over_the_size_limit_is_refused_by_name
tests/unit/test_philo10_email_channel.py::test_c6_a_materially_different_provider_plugs_in_with_one_class_and_one_row
tests/unit/test_philo10_email_channel.py::test_r2_global_http_debug_on_prints_no_key_and_no_body
tests/unit/test_philo10_email_channel.py::test_r2_a_failure_is_failed_only_when_no_byte_was_written[tls-during-the-body-write-None-2-unknown-tls_failed]
tests/unit/test_philo10_email_channel.py::test_r2_a_failure_is_failed_only_when_no_byte_was_written[tls-during-the-header-write-None-1-unknown-tls_failed]
tests/unit/test_philo10_email_channel.py::test_r2_a_failure_is_failed_only_when_no_byte_was_written[tls-handshake-ssl-0-failed-tls_failed]
tests/unit/test_philo10_email_channel.py::test_r2_a_failure_is_failed_only_when_no_byte_was_written[connection-refused-refused-0-failed-connect_refused]
tests/unit/test_philo10_email_channel.py::test_r2_a_failure_is_failed_only_when_no_byte_was_written[dns-dns-0-failed-dns_failed]
tests/unit/test_philo10_email_channel.py::test_c2_r3_a_restart_during_an_email_send_ends_unknown_once_and_never_sends_again[killed-before-the-wire]
tests/unit/test_philo10_email_channel.py::test_c2_r3_a_restart_during_an_email_send_ends_unknown_once_and_never_sends_again[killed-after-the-wire]

61 tests collected in 0.18s
```

### Captured run — 2026-09-29T05:38:37Z

- **Command:** `.tmp/iso.sh zsh -c .venv/bin/python -m pytest -q -p no:cacheprovider -n 8 -rf --basetemp=$HOME/pt tests/unit/test_philo10_email_channel.py tests/unit/test_philo10_send_contract.py tests/unit/test_philo10_send_recovery.py tests/unit/test_philo10_send_restart.py tests/unit/test_philo10_rig_op.py tests/unit/test_external_egress_kernel.py tests/unit/test_connector_runtime.py tests/unit/test_gated_connector.py tests/unit/test_webhook_post_actuator.py tests/unit/test_github_issue_actuator.py tests/unit/test_hs151_honest_dispatch.py tests/unit/test_kernel_effect_fence.py tests/unit/test_live_proposals.py tests/unit/test_slack_export.py tests/unit/test_subprocess_exec_kernel.py tests/unit/test_voice_macro_connector.py tests/unit/test_thread_tool_gate.py tests/unit/test_694_thread_never_sends.py tests/unit/test_api_surface.py tests/unit/test_mcp_sidecar_doc_drift.py tests/unit/test_doc_drift_guard.py tests/unit/test_philo_graph_atlas.py tests/unit/test_kernel_broker.py tests/integration/test_actuator_kernel_real_hub.py tests/integration/test_web_companion_slack.py tests/integration/test_web_companion_webhook.py tests/integration/test_web_slack_export.py tests/integration/test_kernel_real_hub.py tests/integration/test_principal_separation.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 9c016b2a5a4faaca1e35469761ba5fca2284c2a5

```text
bringing up nodes...
bringing up nodes...

........................................................................ [ 14%]
........................................................................ [ 29%]
........................................................................ [ 43%]
........................................................................ [ 58%]
........................................................................ [ 72%]
........................................................................ [ 87%]
..............................................................           [100%]
494 passed in 56.80s
```

### Captured run — 2026-09-29T05:39:35Z

- **Command:** `.tmp/iso.sh .venv/bin/python pm/roadmap/holdspeak-philo/phase-10-the-channels/assets/story-03-proof/mutations.py.txt`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 9c016b2a5a4faaca1e35469761ba5fca2284c2a5

```text
BASELINE (no mutation): rc=0 61 passed in 61.30s (0:01:01)
RED   M1 redirects followed (the default handler): rc=1 1 failed, 59 deselected in 1.83s
RED   M2 the kernel records the exception's text (main's external_egress.py:290): rc=1 1 failed, 60 deselected in 0.81s
RED   M3 the opener lets a raw transport exception out: rc=1 1 failed, 60 deselected in 1.86s
RED   M4 the network seam hashes the destination only (main's connector_runtime.py:215): rc=1 1 failed, 56 deselected in 1.84s
RED   M5 the key becomes planning material (read at plan time, held by the sender): rc=1 1 failed, 60 deselected in 1.95s
RED   M6 any 4xx is FAILED (no pinned list): rc=1 1 failed, 8 passed, 42 deselected in 11.26s
RED   M7 403 is not split by its discriminator: rc=1 1 failed, 1 passed, 58 deselected in 2.71s
RED   M8 the key store admits any backend: rc=1 1 failed, 54 deselected in 0.57s
RED   M9 202 without X-Message-Id is SENT: rc=1 1 failed, 60 deselected in 1.77s
RED   M10 the egress child has no parent (the send's operation is not threaded): rc=1 1 failed, 59 deselected in 1.88s
RED   M11 a take-over sends again: rc=1 1 failed, 59 deselected in 1.75s
RED   M12 the channel calls SendGrid directly (no registry row): rc=1 1 failed, 60 deselected in 1.74s
GREEN M13 the edge inherits the global wire debug (Codex r1 P1): rc=0 1 passed, 60 deselected in 1.77s
RED   M14 a TLS failure is FAILED whatever was written (Codex r1 P1): rc=1 1 failed, 56 deselected in 1.81s
RED   M15 the transmitter hard-codes SendGrid's Bearer auth (Codex r1 P2): rc=1 1 failed, 60 deselected in 1.78s
RED   M16 a success body is not given to interpret (Codex r1 P2): rc=1 1 failed, 60 deselected in 1.73s
MUTATIONS: 15/16 turned their fences red
```

### Captured run — 2026-09-29T05:41:33Z

- **Command:** `zsh .tmp/docs_checks.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 9c016b2a5a4faaca1e35469761ba5fca2284c2a5

```text
== scripts/gen_operations_json.py --check
OK docs/generated/operations.json
== scripts/gen_mcp_sidecar_doc.py --check
wrote docs/MCP_SIDECAR.md
  246 tools across 43 families
== scripts/check_docs.py
Documentation navigation: 70 files checked; local targets and Markdown headings resolve.
== scripts/philo_repository_census.py --check
Repository census: 5 outputs verified.
== scripts/philo_api_reference.py --check
API reference checked
== scripts/philo_openapi_reference.py --check
OpenAPI: 580 paths
== scripts/philo_boundary_census.py --check
Boundary candidate census checked
== scripts/philo_doctor_reference.py --check
Doctor reference: 41 check functions
== scripts/philo_config_reference.py --check
Configuration declaration reference is current
== scripts/philo_graph_reference.py --check
graph join checked: docs/generated/graph.json; 14 subtype conflict note(s)
== scripts/validate_architecture.py
Architecture metadata: 4 shard(s), 147 record(s)
Architecture metadata validation passed.
== scripts/generate_capability_docs.py --check
Architecture documentation checked (10 outputs).
== scripts/check_doc_coverage.py --check
Documentation coverage checked.
== scripts/residual_census.py --check
RESIDUAL FENCE GREEN: 240 identities match /Users/karol/dev/tools/wt-philo-10-03
DOCS RC=0
```

### Captured run — 2026-09-29T05:42:22Z

- **Command:** `.tmp/iso.sh .venv/bin/python pm/roadmap/holdspeak-philo/phase-10-the-channels/assets/story-03-proof/mutations.py.txt`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 98086be57b61d6264958fd2405c81290d4f42fc6

```text
BASELINE (no mutation): rc=0 61 passed in 75.86s (0:01:15)
RED   M1 redirects followed (the default handler): rc=1 1 failed, 59 deselected in 2.65s
RED   M2 the kernel records the exception's text (main's external_egress.py:290): rc=1 1 failed, 60 deselected in 1.62s
RED   M3 the opener lets a raw transport exception out: rc=1 1 failed, 60 deselected in 2.05s
RED   M4 the network seam hashes the destination only (main's connector_runtime.py:215): rc=1 1 failed, 56 deselected in 1.50s
RED   M5 the key becomes planning material (read at plan time, held by the sender): rc=1 1 failed, 60 deselected in 1.56s
RED   M6 any 4xx is FAILED (no pinned list): rc=1 1 failed, 8 passed, 42 deselected in 12.79s
RED   M7 403 is not split by its discriminator: rc=1 1 failed, 1 passed, 58 deselected in 4.20s
RED   M8 the key store admits any backend: rc=1 1 failed, 54 deselected in 1.05s
RED   M9 202 without X-Message-Id is SENT: rc=1 1 failed, 60 deselected in 2.48s
RED   M10 the egress child has no parent (the send's operation is not threaded): rc=1 1 failed, 59 deselected in 2.54s
RED   M11 a take-over sends again: rc=1 1 failed, 59 deselected in 2.75s
RED   M12 the channel calls SendGrid directly (no registry row): rc=1 1 failed, 60 deselected in 3.29s
RED   M13 the edge inherits the global wire debug (Codex r1 P1; both local pins removed): rc=1 1 failed, 60 deselected in 1.77s
RED   M14 a TLS failure is FAILED whatever was written (Codex r1 P1): rc=1 1 failed, 56 deselected in 1.51s
RED   M15 the transmitter hard-codes SendGrid's Bearer auth (Codex r1 P2): rc=1 1 failed, 60 deselected in 2.12s
RED   M16 a success body is not given to interpret (Codex r1 P2): rc=1 1 failed, 60 deselected in 3.38s
MUTATIONS: 16/16 turned their fences red
```
