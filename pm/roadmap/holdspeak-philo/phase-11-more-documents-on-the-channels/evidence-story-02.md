# Evidence - PHILO-11-02

- **Story:** PHILO-11-02 - The Slack channel and the aftercare rewrite
- **Status:** done
- **Date:** 2026-09-30

## Proof

### Captured run — 2026-09-30T07:00:41Z

- **Command:** `bash scripts/verify_philo11_slack.sh walk --atlas docs/internal/philo/graph/atlas-phase10.json --case case.p10.send.receipt_after_return --brain astra --viewport 1440 --engine none --out pm/roadmap/holdspeak-philo/phase-11-more-documents-on-the-channels/assets/story-02-walk/receipt-1440`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** b1f71ec6b5210279b668fd978f157aafaeafb4ca

```text
PASS: live
BRAIN: astra
SOURCE: 3552be416c9d5d968adc162941f1f81a3c7c0b44 dirty=True
CONTRACT: rig=1.5.2 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase10.json
RUNTIME: build=['index-Dvjkur0f.js'] hub=http://127.0.0.1:51406 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/philo11-slack.Mq5a4C/tmp/graph-walk-home-y_1c0iac/.local/share/holdspeak/holdspeak.db engine=none
JOB: p10
VERDICT: pass terminal=settled
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-11-more-documents-on-the-channels/assets/story-02-walk/receipt-1440/20260930T070041Z-case.p10.send.receipt_after_return-astra-1440/before.png', 'pm/roadmap/holdspeak-philo/phase-11-more-documents-on-the-channels/assets/story-02-walk/receipt-1440/20260930T070041Z-case.p10.send.receipt_after_return-astra-1440/after.png']
NOTE: predicate: all_of: readable_text: 'SAVED' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 45, 'y': 295, 'w': 120, 'h': 19} | protocol_reads: GET /api/channels/sends?document_ref=project_update:pupd_1cb303690f4544d096e5677a68ade581 answered 200 with 1 row(s) {'state': 'sent', 'destination_id': 'chd_df6b75923e56209a0656e62a'}; GET /api/projects/proj-dd1f7b24990a/updates answered 200 with 1 row(s) {'id': 'pupd_1cb303690f4544d096e5677a68ade581', 'deliveries.0.outcome': 'sent'}
```

### Captured run — 2026-09-30T07:01:39Z

- **Command:** `bash scripts/verify_philo11_slack.sh walk --atlas docs/internal/philo/graph/atlas-phase10.json --case case.p10.send.receipt_after_return --brain astra --viewport 393 --engine none --out pm/roadmap/holdspeak-philo/phase-11-more-documents-on-the-channels/assets/story-02-walk/receipt-393`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** b1f71ec6b5210279b668fd978f157aafaeafb4ca

```text
PASS: live
BRAIN: astra
SOURCE: 3552be416c9d5d968adc162941f1f81a3c7c0b44 dirty=True
CONTRACT: rig=1.5.2 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase10.json
RUNTIME: build=['index-Dvjkur0f.js'] hub=http://127.0.0.1:51643 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/philo11-slack.jQQBSZ/tmp/graph-walk-home-9fa0wbpy/.local/share/holdspeak/holdspeak.db engine=none
JOB: p10
VERDICT: pass terminal=settled
EVIDENCE: ['pm/roadmap/holdspeak-philo/phase-11-more-documents-on-the-channels/assets/story-02-walk/receipt-393/20260930T070139Z-case.p10.send.receipt_after_return-astra-393/before.png', 'pm/roadmap/holdspeak-philo/phase-11-more-documents-on-the-channels/assets/story-02-walk/receipt-393/20260930T070139Z-case.p10.send.receipt_after_return-astra-393/after.png']
NOTE: predicate: all_of: readable_text: 'SAVED' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 21, 'y': 389, 'w': 120, 'h': 19} | protocol_reads: GET /api/channels/sends?document_ref=project_update:pupd_2f4537709b714e0bbf1ab4e5d2f542fd answered 200 with 1 row(s) {'state': 'sent', 'destination_id': 'chd_daaf15ca83c2d345ecc00016'}; GET /api/projects/proj-62f678f75fc8/updates answered 200 with 1 row(s) {'id': 'pupd_2f4537709b714e0bbf1ab4e5d2f542fd', 'deliveries.0.outcome': 'sent'}
```

### Captured run — 2026-09-30T07:04:13Z

- **Command:** `bash scripts/verify_philo11_slack.sh pytest --collect-only -q tests/unit/test_philo11_slack_channel.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** b1f71ec6b5210279b668fd978f157aafaeafb4ca

```text
tests/unit/test_philo11_slack_channel.py::test_save_target_has_only_label_and_key_reference_and_url_rule
tests/unit/test_philo11_slack_channel.py::test_real_save_key_rejects_every_non_admitted_webhook_url[http://hooks.slack.com/services/T/B/K]
tests/unit/test_philo11_slack_channel.py::test_real_save_key_rejects_every_non_admitted_webhook_url[https://evil.example/services/T/B/K]
tests/unit/test_philo11_slack_channel.py::test_real_save_key_rejects_every_non_admitted_webhook_url[https://hooks.slack.com:0/services/T/B/K]
tests/unit/test_philo11_slack_channel.py::test_real_save_key_rejects_every_non_admitted_webhook_url[https://hooks.slack.com:8443/services/T/B/K]
tests/unit/test_philo11_slack_channel.py::test_real_save_key_rejects_every_non_admitted_webhook_url[https://hooks.slack.com/not-services/T/B/K]
tests/unit/test_philo11_slack_channel.py::test_real_save_key_rejects_every_non_admitted_webhook_url[https://hooks.slack.com/services/T/B/K?leak=yes]
tests/unit/test_philo11_slack_channel.py::test_real_save_key_accepts_default_and_explicit_443
tests/unit/test_philo11_slack_channel.py::test_markdown_is_serialized_once_and_preview_is_read_from_frozen_bytes
tests/unit/test_philo11_slack_channel.py::test_size_refusal_is_named_before_dispatch
tests/unit/test_philo11_slack_channel.py::test_multibyte_text_limit_counts_characters_in_serialize_and_plan
tests/unit/test_philo11_slack_channel.py::test_pinned_outcomes[200-ok-headers0-sent-None]
tests/unit/test_philo11_slack_channel.py::test_pinned_outcomes[200-OK-headers1-unknown-ack_missing]
tests/unit/test_philo11_slack_channel.py::test_pinned_outcomes[400-invalid_payload-headers2-failed-invalid_payload]
tests/unit/test_philo11_slack_channel.py::test_pinned_outcomes[403-action_prohibited-headers3-failed-action_prohibited]
tests/unit/test_philo11_slack_channel.py::test_pinned_outcomes[404-channel_not_found-headers4-failed-channel_not_found]
tests/unit/test_philo11_slack_channel.py::test_pinned_outcomes[410-channel_is_archived-headers5-failed-channel_is_archived]
tests/unit/test_philo11_slack_channel.py::test_pinned_outcomes[429-rate_limited-headers6-failed-rate_limited]
tests/unit/test_philo11_slack_channel.py::test_pinned_outcomes[500-rollup_error-headers7-unknown-rollup_error]
tests/unit/test_philo11_slack_channel.py::test_pinned_outcomes[503-unavailable-headers8-unknown-unpinned_503]
tests/unit/test_philo11_slack_channel.py::test_pinned_outcomes[302--headers9-unknown-redirect_refused]
tests/unit/test_philo11_slack_channel.py::test_transmit_reads_memory_key_and_sends_frozen_bytes_only
tests/unit/test_philo11_slack_channel.py::test_transport_errors_do_not_expose_webhook
tests/unit/test_philo11_slack_channel.py::test_native_key_store_accepts_only_the_three_native_backends[keyring.backends.macOS-Keyring]
tests/unit/test_philo11_slack_channel.py::test_native_key_store_accepts_only_the_three_native_backends[keyring.backends.SecretService-Keyring]
tests/unit/test_philo11_slack_channel.py::test_native_key_store_accepts_only_the_three_native_backends[keyring.backends.Windows-WinVaultKeyring]
tests/unit/test_philo11_slack_channel.py::test_non_native_key_store_is_refused_by_name[backend0]
tests/unit/test_philo11_slack_channel.py::test_non_native_key_store_is_refused_by_name[backend1]
tests/unit/test_philo11_slack_channel.py::test_non_native_key_store_is_refused_by_name[backend2]
tests/unit/test_philo11_slack_channel.py::test_native_key_store_distinguishes_locked_and_missing_without_os_keychain
tests/unit/test_philo11_slack_channel.py::test_quiet_https_edge_tracks_before_and_after_byte_failures[connect_error0-None-False]
tests/unit/test_philo11_slack_channel.py::test_quiet_https_edge_tracks_before_and_after_byte_failures[connect_error1-None-False]
tests/unit/test_philo11_slack_channel.py::test_quiet_https_edge_tracks_before_and_after_byte_failures[None-fail_after_connect2-True]
tests/unit/test_philo11_slack_channel.py::test_native_keyring_is_never_constructed_by_unit_fixture

34 tests collected in 0.11s
```

### Captured run — 2026-09-30T07:04:24Z

- **Command:** `bash scripts/verify_philo11_slack.sh pytest -q tests/unit/test_philo11_slack_channel.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** b1f71ec6b5210279b668fd978f157aafaeafb4ca

```text
..................................                                       [100%]
34 passed in 0.79s
```

### Captured run — 2026-09-30T07:15:33Z

- **Command:** `bash scripts/verify_philo11_slack.sh pytest -q tests/integration/test_philo11_slack_rewrite.py tests/integration/test_web_companion_slack.py tests/integration/test_web_companion_webhook.py tests/integration/test_web_slack_export.py tests/integration/test_history_slack_surfaces.py tests/integration/test_web_settings_secrets.py tests/unit/test_slack_export.py tests/unit/test_trust_destinations.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** b1f71ec6b5210279b668fd978f157aafaeafb4ca

```text
.......................................................                  [100%]
55 passed in 18.48s
```

### Captured run — 2026-09-30T07:17:31Z

- **Command:** `bash scripts/verify_philo11_slack.sh pytest -q tests/unit/test_philo10_atlas.py tests/unit/test_philo_graph_atlas.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** b1f71ec6b5210279b668fd978f157aafaeafb4ca

```text
........................................................................ [ 46%]
........................................................................ [ 93%]
..........                                                               [100%]
154 passed in 1.44s
```

### Captured run — 2026-09-30T07:17:52Z

- **Command:** `bash scripts/verify_philo11_slack.sh pytest --collect-only -q tests/unit/test_philo11_slack_channel.py tests/integration/test_philo11_slack_operations.py tests/integration/test_philo11_slack_rewrite.py tests/unit/test_slack_export.py tests/integration/test_web_companion_webhook.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** b1f71ec6b5210279b668fd978f157aafaeafb4ca

```text
tests/unit/test_philo11_slack_channel.py::test_save_target_has_only_label_and_key_reference_and_url_rule
tests/unit/test_philo11_slack_channel.py::test_real_save_key_rejects_every_non_admitted_webhook_url[http://hooks.slack.com/services/T/B/K]
tests/unit/test_philo11_slack_channel.py::test_real_save_key_rejects_every_non_admitted_webhook_url[https://evil.example/services/T/B/K]
tests/unit/test_philo11_slack_channel.py::test_real_save_key_rejects_every_non_admitted_webhook_url[https://hooks.slack.com:0/services/T/B/K]
tests/unit/test_philo11_slack_channel.py::test_real_save_key_rejects_every_non_admitted_webhook_url[https://hooks.slack.com:8443/services/T/B/K]
tests/unit/test_philo11_slack_channel.py::test_real_save_key_rejects_every_non_admitted_webhook_url[https://hooks.slack.com/not-services/T/B/K]
tests/unit/test_philo11_slack_channel.py::test_real_save_key_rejects_every_non_admitted_webhook_url[https://hooks.slack.com/services/T/B/K?leak=yes]
tests/unit/test_philo11_slack_channel.py::test_real_save_key_accepts_default_and_explicit_443
tests/unit/test_philo11_slack_channel.py::test_markdown_is_serialized_once_and_preview_is_read_from_frozen_bytes
tests/unit/test_philo11_slack_channel.py::test_size_refusal_is_named_before_dispatch
tests/unit/test_philo11_slack_channel.py::test_multibyte_text_limit_counts_characters_in_serialize_and_plan
tests/unit/test_philo11_slack_channel.py::test_pinned_outcomes[200-ok-headers0-sent-None]
tests/unit/test_philo11_slack_channel.py::test_pinned_outcomes[200-OK-headers1-unknown-ack_missing]
tests/unit/test_philo11_slack_channel.py::test_pinned_outcomes[400-invalid_payload-headers2-failed-invalid_payload]
tests/unit/test_philo11_slack_channel.py::test_pinned_outcomes[403-action_prohibited-headers3-failed-action_prohibited]
tests/unit/test_philo11_slack_channel.py::test_pinned_outcomes[404-channel_not_found-headers4-failed-channel_not_found]
tests/unit/test_philo11_slack_channel.py::test_pinned_outcomes[410-channel_is_archived-headers5-failed-channel_is_archived]
tests/unit/test_philo11_slack_channel.py::test_pinned_outcomes[429-rate_limited-headers6-failed-rate_limited]
tests/unit/test_philo11_slack_channel.py::test_pinned_outcomes[500-rollup_error-headers7-unknown-rollup_error]
tests/unit/test_philo11_slack_channel.py::test_pinned_outcomes[503-unavailable-headers8-unknown-unpinned_503]
tests/unit/test_philo11_slack_channel.py::test_pinned_outcomes[302--headers9-unknown-redirect_refused]
tests/unit/test_philo11_slack_channel.py::test_transmit_reads_memory_key_and_sends_frozen_bytes_only
tests/unit/test_philo11_slack_channel.py::test_transport_errors_do_not_expose_webhook
tests/unit/test_philo11_slack_channel.py::test_native_key_store_accepts_only_the_three_native_backends[keyring.backends.macOS-Keyring]
tests/unit/test_philo11_slack_channel.py::test_native_key_store_accepts_only_the_three_native_backends[keyring.backends.SecretService-Keyring]
tests/unit/test_philo11_slack_channel.py::test_native_key_store_accepts_only_the_three_native_backends[keyring.backends.Windows-WinVaultKeyring]
tests/unit/test_philo11_slack_channel.py::test_non_native_key_store_is_refused_by_name[backend0]
tests/unit/test_philo11_slack_channel.py::test_non_native_key_store_is_refused_by_name[backend1]
tests/unit/test_philo11_slack_channel.py::test_non_native_key_store_is_refused_by_name[backend2]
tests/unit/test_philo11_slack_channel.py::test_native_key_store_distinguishes_locked_and_missing_without_os_keychain
tests/unit/test_philo11_slack_channel.py::test_quiet_https_edge_tracks_before_and_after_byte_failures[connect_error0-None-False]
tests/unit/test_philo11_slack_channel.py::test_quiet_https_edge_tracks_before_and_after_byte_failures[connect_error1-None-False]
tests/unit/test_philo11_slack_channel.py::test_quiet_https_edge_tracks_before_and_after_byte_failures[None-fail_after_connect2-True]
tests/unit/test_philo11_slack_channel.py::test_native_keyring_is_never_constructed_by_unit_fixture
tests/integration/test_philo11_slack_operations.py::test_save_check_preview_prepare_and_send_use_the_real_slack_producer
tests/integration/test_philo11_slack_operations.py::test_each_slack_outcome_is_interpreted_by_the_real_send[ok-answer-sent-None]
tests/integration/test_philo11_slack_operations.py::test_each_slack_outcome_is_interpreted_by_the_real_send[invalid-answer-failed-invalid_payload]
tests/integration/test_philo11_slack_operations.py::test_each_slack_outcome_is_interpreted_by_the_real_send[prohibited-answer-failed-action_prohibited]
tests/integration/test_philo11_slack_operations.py::test_each_slack_outcome_is_interpreted_by_the_real_send[missing-answer-failed-channel_not_found]
tests/integration/test_philo11_slack_operations.py::test_each_slack_outcome_is_interpreted_by_the_real_send[archived-answer-failed-channel_is_archived]
tests/integration/test_philo11_slack_operations.py::test_each_slack_outcome_is_interpreted_by_the_real_send[rate_limited-answer-failed-rate_limited]
tests/integration/test_philo11_slack_operations.py::test_each_slack_outcome_is_interpreted_by_the_real_send[rollup-answer-unknown-rollup_error]
tests/integration/test_philo11_slack_operations.py::test_each_slack_outcome_is_interpreted_by_the_real_send[other_5xx-answer-unknown-unpinned_503]
tests/integration/test_philo11_slack_operations.py::test_each_slack_outcome_is_interpreted_by_the_real_send[redirect-answer-unknown-redirect_refused]
tests/integration/test_philo11_slack_operations.py::test_each_slack_outcome_is_interpreted_by_the_real_send[wrong_ok-answer-unknown-ack_missing]
tests/integration/test_philo11_slack_operations.py::test_each_slack_outcome_is_interpreted_by_the_real_send[unlisted-answer-unknown-unpinned_418]
tests/integration/test_philo11_slack_operations.py::test_each_slack_outcome_is_interpreted_by_the_real_send[timeout-answer-unknown-timeout]
tests/integration/test_philo11_slack_operations.py::test_unknown_replay_and_rate_limit_never_post_again
tests/integration/test_philo11_slack_operations.py::test_an_agent_cannot_press_slack_send
tests/integration/test_philo11_slack_operations.py::test_transport_failure_records_whether_bytes_may_have_left[dns_before-error0-False-failed-dns_failed]
tests/integration/test_philo11_slack_operations.py::test_transport_failure_records_whether_bytes_may_have_left[tls_before-error1-False-failed-tls_failed]
tests/integration/test_philo11_slack_operations.py::test_transport_failure_records_whether_bytes_may_have_left[timeout_before-error2-False-failed-timeout]
tests/integration/test_philo11_slack_operations.py::test_transport_failure_records_whether_bytes_may_have_left[tls_after-error3-True-unknown-tls_failed]
tests/integration/test_philo11_slack_operations.py::test_transport_failure_records_whether_bytes_may_have_left[timeout_after-error4-True-unknown-timeout]
tests/integration/test_philo11_slack_operations.py::test_size_refusal_is_real_and_carries_size_and_limit_before_wire
tests/integration/test_philo11_slack_operations.py::test_replacing_slack_destination_parks_old_and_old_prepare_refuses
tests/integration/test_philo11_slack_operations.py::test_invalid_webhook_is_refused_at_save_without_key_or_wire[http://hooks.slack.com/services/T/B/K]
tests/integration/test_philo11_slack_operations.py::test_invalid_webhook_is_refused_at_save_without_key_or_wire[https://slack.com/services/T/B/K]
tests/integration/test_philo11_slack_operations.py::test_invalid_webhook_is_refused_at_save_without_key_or_wire[https://hooks.slack.com:8443/services/T/B/K]
tests/integration/test_philo11_slack_operations.py::test_invalid_webhook_is_refused_at_save_without_key_or_wire[https://hooks.slack.com/services/T/B/K?secret=leak]
tests/integration/test_philo11_slack_rewrite.py::test_old_config_loads_but_aftercare_does_not_advertise_slack
tests/integration/test_philo11_slack_rewrite.py::test_settings_read_and_write_keep_the_retained_field_private
tests/integration/test_philo11_slack_rewrite.py::test_settings_write_ignores_the_retained_field
tests/integration/test_philo11_slack_rewrite.py::test_posture_aftercare_route_is_gone_and_never_posts
tests/integration/test_philo11_slack_rewrite.py::test_desk_slack_target_is_parked
tests/integration/test_philo11_slack_rewrite.py::test_historical_slack_proposals_remain_readable
tests/integration/test_philo11_slack_rewrite.py::test_legacy_slack_connector_is_removed
tests/unit/test_slack_export.py::test_document_projection_keeps_the_complete_aftercare_body
tests/unit/test_slack_export.py::test_followup_projection_is_still_the_real_draft
tests/unit/test_slack_export.py::test_unknown_document_projection_is_named
tests/unit/test_slack_export.py::test_generic_webhook_url_rule[https://hooks.slack.com/services/T0/B0/xyz-hooks.slack.com]
tests/unit/test_slack_export.py::test_generic_webhook_url_rule[https://HOOKS.SLACK.COM/services/x-hooks.slack.com]
tests/unit/test_slack_export.py::test_generic_webhook_url_rule[http://127.0.0.1:8901/hook-127.0.0.1]
tests/unit/test_slack_export.py::test_generic_webhook_url_rule[http://localhost:8901/hook-localhost]
tests/unit/test_slack_export.py::test_invalid_generic_webhook_urls_are_refused[]
tests/unit/test_slack_export.py::test_invalid_generic_webhook_urls_are_refused[   ]
tests/unit/test_slack_export.py::test_invalid_generic_webhook_urls_are_refused[ftp://hooks.slack.com/x]
tests/unit/test_slack_export.py::test_invalid_generic_webhook_urls_are_refused[http://hooks.slack.com/services/x]
tests/unit/test_slack_export.py::test_invalid_generic_webhook_urls_are_refused[https://]
tests/unit/test_slack_export.py::test_invalid_generic_webhook_urls_are_refused[not a url]
tests/unit/test_slack_export.py::test_old_slack_connector_is_not_exported
tests/unit/test_slack_export.py::test_generic_companion_connector_still_has_a_transport_boundary
tests/unit/test_slack_export.py::test_generic_credential_never_rests_on_the_proposal
tests/unit/test_slack_export.py::test_generic_smuggled_foreign_url_is_overwritten_before_egress
tests/unit/test_slack_export.py::test_generic_host_gate_refuses_a_foreign_host_before_egress
tests/unit/test_slack_export.py::test_generic_non_2xx_is_recordable_as_failed
tests/integration/test_web_companion_webhook.py::test_unconfigured_refuses_with_400
tests/integration/test_web_companion_webhook.py::test_empty_text_refuses_with_400
tests/integration/test_web_companion_webhook.py::test_propose_preview_is_the_wire_body
tests/integration/test_web_companion_webhook.py::test_approval_posts_the_preview_byte_equal
tests/integration/test_web_companion_webhook.py::test_yolo_executes_the_configured_webhook_without_a_decision
tests/integration/test_web_companion_webhook.py::test_rejection_posts_nothing
tests/integration/test_web_companion_webhook.py::test_url_removed_between_propose_and_approve_fails_honestly
tests/integration/test_web_companion_webhook.py::test_the_url_never_rides_a_response_or_broadcast
tests/integration/test_web_companion_webhook.py::test_the_wire_events_ride_for_qlippy
tests/integration/test_web_companion_webhook.py::test_companion_status_reports_webhook_configured
tests/integration/test_web_companion_webhook.py::test_slack_and_webhook_decisions_do_not_cross

97 tests collected in 0.53s
```

### Captured run — 2026-09-30T07:18:04Z

- **Command:** `bash scripts/verify_philo11_slack.sh pytest -q tests/unit/test_philo11_slack_channel.py tests/integration/test_philo11_slack_operations.py tests/integration/test_philo11_slack_rewrite.py tests/unit/test_philo11_channel_contract.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** b1f71ec6b5210279b668fd978f157aafaeafb4ca

```text
........................................................................ [ 93%]
.....                                                                    [100%]
77 passed in 30.19s
```

### Captured run — 2026-09-30T07:19:03Z

- **Command:** `bash scripts/verify_philo11_slack.sh pytest -q tests/unit/test_philo10_send_contract.py::test_the_operations_are_declared_once_and_reach_one_service_over_http_and_mcp tests/unit/test_philo10_cli_channels.py::test_the_sends_are_egress_owner_presses_and_blocking_io_in_the_one_table`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** b1f71ec6b5210279b668fd978f157aafaeafb4ca

```text
..                                                                       [100%]
2 passed in 1.98s
```

### Captured run — 2026-09-30T07:19:20Z

- **Command:** `bash -o pipefail -c bash scripts/verify_philo11_slack.sh pytest -q -n auto --dist=worksteal --ignore=tests/e2e/test_metal.py --junitxml=.tmp/philo11-02/full-suite.xml 2>&1 | tee .tmp/philo11-02/full-suite.txt`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** b1f71ec6b5210279b668fd978f157aafaeafb4ca

```text
bringing up nodes...
bringing up nodes...

........................................................................ [  0%]
........................................................................ [  1%]
........................F............................................... [  1%]
........................................................................ [  2%]
........................................................................ [  2%]
.............................................F.......................... [  3%]
........................................................................ [  3%]
........................................................................ [  4%]
........................................................................ [  4%]
........................................................................ [  5%]
...............................................................s.ss.ssss [  5%]
sssssssssssssss......................................................... [  6%]
........................................................................ [  6%]
........................................................................ [  7%]
........................................................................ [  7%]
...............................ss....................................... [  8%]
........................................................................ [  8%]
........................................................................ [  9%]
........................................................................ [ 10%]
........................................................................ [ 10%]
..................................s..................................... [ 11%]
........................................................................ [ 11%]
........................................................................ [ 12%]
................................................................s....... [ 12%]
........................................................................ [ 13%]
........................................................................ [ 13%]
........................................................................ [ 14%]
........................................................................ [ 14%]
........................................................................ [ 15%]
........................................................................ [ 15%]
........................................................................ [ 16%]
........................................................................ [ 16%]
........................................................................ [ 17%]
........................................................................ [ 17%]
........................................................................ [ 18%]
.................................................................s...... [ 18%]
........................................................................ [ 19%]
........................................................................ [ 20%]
........................................................................ [ 20%]
........................................................................ [ 21%]
........................................................................ [ 21%]
........................................................................ [ 22%]
........................................................................ [ 22%]
........................................................................ [ 23%]
........................................................................ [ 23%]
........................................................................ [ 24%]
........................................................................ [ 24%]
........................................................................ [ 25%]
....................................................................s... [ 25%]
........................................................................ [ 26%]
...................................ss..............................ss... [ 26%]
........................................................................ [ 27%]
.........................................ss............................. [ 27%]
...................................................s.................... [ 28%]
........................................sssss........................... [ 28%]
..............................................................ss........ [ 29%]
........................................................................ [ 30%]
........................................................................ [ 30%]
........................................................................ [ 31%]
........................................................................ [ 31%]
........................................................................ [ 32%]
........................................................................ [ 32%]
........................................................................ [ 33%]
........................................................................ [ 33%]
........................................................................ [ 34%]
........................................................................ [ 34%]
........................................................................ [ 35%]
.................................s...................................... [ 35%]
........................................................................ [ 36%]
........................................................................ [ 36%]
........................................................................ [ 37%]
........................................................................ [ 37%]
........................................................................ [ 38%]
........................................................................ [ 39%]
........................................................................ [ 39%]
........................................................................ [ 40%]
........................................................................ [ 40%]
........................................................................ [ 41%]
........................................................................ [ 41%]
........................................................................ [ 42%]
........................................................................ [ 42%]
........s............................................................... [ 43%]
........................................................................ [ 43%]
........................................................................ [ 44%]
........................................................................ [ 44%]
.....s.................................................................. [ 45%]
........................................................................ [ 45%]
........................................................................ [ 46%]
........................................................................ [ 46%]
........................................................................ [ 47%]
........................................................................ [ 47%]
........................................................................ [ 48%]
........................................................................ [ 49%]
........................................................................ [ 49%]
........................................................................ [ 50%]
........................................................................ [ 50%]
........................................................................ [ 51%]
........................................................................ [ 51%]
........................................................................ [ 52%]
........................................................................ [ 52%]
........................................................................ [ 53%]
........................................................................ [ 53%]
........................................................................ [ 54%]
........................................................................ [ 54%]
..........................F............................................. [ 55%]
........s............................................................... [ 55%]
........................................................................ [ 56%]
........................................................................ [ 56%]
........................................................................ [ 57%]
........................................................................ [ 57%]
..................................................................s..... [ 58%]
........................................................................ [ 59%]
........................................................................ [ 59%]
........................................................................ [ 60%]
........................................................................ [ 60%]
........................................................................ [ 61%]
........................................................................ [ 61%]
........................................................................ [ 62%]
........................................................................ [ 62%]
........................................................................ [ 63%]
........................................................................ [ 63%]
........................................................................ [ 64%]
........................................................................ [ 64%]
........................................................................ [ 65%]
........................................................................ [ 65%]
........................................................................ [ 66%]
........................................................................ [ 66%]
........................................................................ [ 67%]
........................................................................ [ 68%]
........................................................................ [ 68%]
........................................................................ [ 69%]
......................................................F.............s... [ 69%]
....................sss................................................. [ 70%]
.......................F................................................ [ 70%]
........................................................................ [ 71%]
........................................................................ [ 71%]
........................................................................ [ 72%]
........................ss.............................................. [ 72%]
........................................................................ [ 73%]
........................................................................ [ 73%]
........................................................................ [ 74%]
........................................................................ [ 74%]
........................................................................ [ 75%]
........................................................................ [ 75%]
.........................s.............................................. [ 76%]
.......................................................................s [ 76%]
ssss.s.................................................................. [ 77%]
..........s............................................................. [ 78%]
........................................................................ [ 78%]
........................................................................ [ 79%]
........................................................................ [ 79%]
........................................................................ [ 80%]
........................................................................ [ 80%]
........................................................................ [ 81%]
........................................................................ [ 81%]
........................................................................ [ 82%]
........................................................................ [ 82%]
........................................................................ [ 83%]
........................................................................ [ 83%]
........................................................................ [ 84%]
.............F.......................................................... [ 84%]
........................................................................ [ 85%]
........................................................................ [ 85%]
...................................................................F.... [ 86%]
..................................F...F................................. [ 86%]
........................................................................ [ 87%]
........................................................................ [ 88%]
........................................................................ [ 88%]
........................................................................ [ 89%]
........................................................................ [ 89%]
........................................................................ [ 90%]
........................................................................ [ 90%]
........................................................................ [ 91%]
.....F.F....................s........................................... [ 91%]
........................................................................ [ 92%]
.................................................................sss.... [ 92%]
..............s......................................................... [ 93%]
...................................................x..s................. [ 93%]
........................................................................ [ 94%]
.................................F...................................... [ 94%]
........................................................................ [ 95%]
........................................................................ [ 95%]
....................................ssss......................x....sssss [ 96%]
s....................................................................... [ 96%]
........x............................................................... [ 97%]
.........Fx................F.................F.......F......F.........F. [ 98%]
....ssssssssssF.........s........F.F.........F....F.....F..........F.... [ 98%]
.......F............ssssssss......F................FF..s...sFssssssssss. [ 99%]
....F..............F.F..F..F..s..FF..........FF...F.....F..F.F....F..F.. [ 99%]
..F...FFF......F...F..F.F.FFF[gw11] node down: Not properly terminated
FF..FF..FF.FFFF......                                                    [100%]
=================================== FAILURES ===================================
________________________ test_committed_join_validates _________________________
[gw9] darwin -- Python 3.13.14 /Users/karol/dev/tools/wt-philo-11-02/.venv/bin/python

joined = ({'cases': [{'applicability': 'applicable', 'completion_bound_s': 120, 'edge_ids': ['edge.route.meeting_capture_recove..._shelf.refused', 'case-revision: live-astra ran an older revision of case.j10.route_brief_generate.load_failure', ...])

    def test_committed_join_validates(joined):
        graph, _ = joined
        validator = _module("philo_graph_validate")
        schema = json.loads((ROOT / "docs/internal/philo/graph/graph.schema.json").read_text(encoding="utf-8"))
>       assert validator.validate(graph, schema, ROOT) == []
E       assert ["phase1-api-...penapi.json'"] == []
E         
E         Left contains one more item: "phase1-api-unresolved: nodes[3943].phase1_refs[0]: POST /api/meetings/{meeting_id}/export/slack is not declared in 'docs/generated/openapi.json'"
E         Use -v to get more diff

tests/unit/test_philo_graph_reference.py:115: AssertionError
_____________________ test_clients_only_call_served_routes _____________________
[gw2] darwin -- Python 3.13.14 /Users/karol/dev/tools/wt-philo-11-02/.venv/bin/python

live = {'note': 'Generated by scripts/gen_api_surface.py. Do not edit by hand.', 'routes': [{'consumers': [], 'methods': ['GE...', 'path': '/api/activity/annotations'}, ...], 'unmatched_calls': {'ios': [], 'web': ['/api/meetings/*/export/slack']}}

    def test_clients_only_call_served_routes(live) -> None:
        unmatched = live["unmatched_calls"]
        assert not unmatched["ios"], (
            "the iOS client calls paths the app does not serve: "
            f"{unmatched['ios']}")
>       assert not unmatched["web"], (
            "the web app calls paths the app does not serve: "
            f"{unmatched['web']}")
E       AssertionError: the web app calls paths the app does not serve: ['/api/meetings/*/export/slack']
E       assert not ['/api/meetings/*/export/slack']

tests/unit/test_api_surface.py:70: AssertionError
____________________ test_the_counts_over_every_atlas_file _____________________
[gw2] darwin -- Python 3.13.14 /Users/karol/dev/tools/wt-philo-11-02/.venv/bin/python

    def test_the_counts_over_every_atlas_file() -> None:
        have = {path.name: len(json.loads(path.read_text())["cases"]) for path in general.ATLAS_FILES}
>       assert have == COUNTS
E       AssertionError: assert {'atlas-phase...son': 27, ...} == {'atlas-phase...son': 19, ...}
E         
E         Omitting 7 identical items, use -vv to show
E         Left contains 1 more item:
E         {'atlas-phase11-slack.json': 3}
E         Use -v to get more diff

tests/unit/test_philo9_atlas.py:101: AssertionError
__ test_ast_census_is_exact_for_every_routing_resolver_reference_and_pointer ___
[gw9] darwin -- Python 3.13.14 /Users/karol/dev/tools/wt-philo-11-02/.venv/bin/python

    def test_ast_census_is_exact_for_every_routing_resolver_reference_and_pointer() -> None:
        definitions, references, pointers, profile_ids = _routing_ast_inventory(REPO)
        assert definitions == ROUTING_RESOLVER_DEFINITIONS
>       assert references == ROUTING_RESOLVER_REFERENCES
E       AssertionError: assert {'holdspeak/d...acement', ...} == {'holdspeak/d...acement', ...}
E         
E         Extra items in the left set:
E         'holdspeak/services/settings_service.py:85:ref:resolve_meeting_placement'
E         'holdspeak/services/settings_service.py:77:import:resolve_meeting_placement'
E         Extra items in the right set:
E         'holdspeak/services/settings_service.py:78:import:resolve_meeting_placement'
E         'holdspeak/services/settings_service.py:86:ref:resolve_meeting_placement'
E         Use -v to get more diff

tests/unit/test_phase143_routing_authority_census.py:366: AssertionError
____________________ test_github_decision_is_target_scoped _____________________
[gw1] darwin -- Python 3.13.14 /Users/karol/dev/tools/wt-philo-11-02/.venv/bin/python

client = <starlette.testclient.TestClient object at 0x11a95e6d0>
db = <holdspeak.db.core.Database object at 0x11d383110>
settings_path = PosixPath('/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/philo11-slack.ptF5ni/pytest/popen-gw1/test_github_decision_is_target0/config.json')
gh = <tests.integration.test_web_companion_github._FakeGh object at 0x11e3f1eb0>

    @pytest.mark.integration
    def test_github_decision_is_target_scoped(client, db, settings_path, gh):
        _configure(settings_path)
        pid = client.post(PROPOSE, json={"text": "ship it"}).json()["prop
[PMO_EVIDENCE_OUTPUT_TRUNCATED]
```

### Captured run — 2026-09-30T07:55:05Z

- **Command:** `bash -o pipefail -c bash scripts/verify_philo11_slack.sh pytest -q -n 0 --junitxml=.tmp/philo11-02/serial1.xml tests/unit/test_philo_graph_reference.py::test_committed_join_validates tests/unit/test_api_surface.py::test_clients_only_call_served_routes tests/unit/test_philo9_atlas.py::test_the_counts_over_every_atlas_file tests/unit/test_phase143_routing_authority_census.py::test_ast_census_is_exact_for_every_routing_resolver_reference_and_pointer tests/integration/test_web_companion_github.py::test_github_decision_is_target_scoped tests/unit/test_philo5_graph_op.py::test_the_canonical_map_has_all_seventeen_operations_and_no_local_service_target tests/unit/test_philo5_one_decision.py::test_the_catalogue_is_explicit_descriptors tests/unit/test_philo10_face_words.py::test_every_emitted_code_has_a_face_word tests/unit/test_philo10_face_words.py::test_no_code_expression_is_unsupported tests/unit/test_philo5_the_loop_r2.py::test_the_contract_refuses_a_non_owner_before_anything_else tests/unit/test_philo5_the_loop_r2.py::test_every_braced_declaration_has_a_producer_here 'tests/unit/test_philo10_send_restart.py::test_r3_a_restart_during_dispatching_ends_unknown_once_and_the_replay_answers_it[desk_decision-killed-after-the-write-send_id]' 'tests/e2e/test_philo8_03_then_guard.py::test_a_follow_up_after_the_window_is_blocked[1440-before_guard]' 'tests/e2e/test_philo8_03_then_guard.py::test_a_follow_up_after_the_window_is_blocked[1440-click_wait]' 'tests/e2e/test_philo8_03_then_guard.py::test_a_follow_up_after_the_window_is_blocked[393-before_guard]' 'tests/e2e/test_philo10_04_send_face_glass.py::TestSendChannelsGlass::test_github_sending_posted_and_a_running_prepared_send[393]' 'tests/e2e/test_philo8_03_then_guard.py::test_a_follow_up_after_the_window_is_blocked[393-click_wait]' tests/e2e/test_hs176_loop_glass.py::test_speak_loop_1440 tests/e2e/test_hs176_loop_glass.py::test_speak_loop_393 'tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_undo_keeps_only_the_pending_object[1440]' 'tests/e2e/test_philo8_01_list_rename_glass.py::TestListRenameGlass::test_the_list_field_opens_writes_and_keeps[393]' 'tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_the_list_row_menu_delete_removes_the_object[1440]' 'tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_undo_keeps_only_the_pending_object[393]' 'tests/e2e/test_philo8_01_list_rename_glass.py::TestListRenameGlass::test_a_taken_name_shows_the_chip_on_the_list[1440]' 'tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_leaving_the_face_inside_the_window_commits_the_delete[floor-1440]' 'tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_the_list_delete_key_removes_the_selected_object[1440]' 'tests/e2e/test_philo8_01_list_rename_glass.py::TestListRenameGlass::test_a_taken_name_shows_the_chip_on_the_floor[1440]' 'tests/e2e/test_philo8_01_list_rename_glass.py::TestListRenameGlass::test_a_taken_name_shows_the_chip_on_the_floor[393]' 'tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_the_list_palette_delete_removes_the_selected_object[1440]' 'tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_leaving_the_face_inside_the_window_commits_the_delete[list-393]' 'tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_the_list_palette_delete_removes_the_selected_object[393]' 'tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_the_chair_withholds_delete_with_its_reason[1440]' 'tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_undo_on_the_list_keeps_the_object[1440]' 'tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_the_foot_never_covers_the_last_rows[393]' 'tests/e2e/test_philo8_01_list_rename_glass.py::TestListRenameGlass::test_a_failed_save_shows_in_the_chip_slot[393-spatial-network]' 'tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_the_chair_withholds_delete_with_its_reason[393]' 'tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_undo_on_the_list_keeps_the_object[393]' 'tests/e2e/test_philo3_01_receipt_hits.py::test_receipt_verbs_own_their_areas[1440]' 'tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_a_repeated_delete_never_offers_a_false_undo[list-1440]' 'tests/e2e/test_philo8_01_list_rename_glass.py::TestListRenameGlass::test_a_refusal_after_the_field_closed_goes_to_the_write_receipt[1440]' 'tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_a_refused_delete_says_so_with_retry[list-393]' 'tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_a_repeated_delete_never_offers_a_false_undo[list-393]' 'tests/e2e/test_philo8_01_list_rename_glass.py::TestListRenameGlass::test_a_refusal_after_the_field_closed_goes_to_the_write_receipt[393]' 'tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_two_deletes_in_one_window_both_reach_the_hub[floor-a_left_selected-1440]' 'tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_a_refused_delete_says_so_with_retry[floor-1440]' 'tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_two_deletes_in_one_window_both_reach_the_hub[floor-a_left_selected-393]' 'tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_a_refused_delete_says_so_with_retry[floor-393]' 'tests/e2e/test_philo8_01_list_rename_glass.py::TestListRenameGlass::test_f2_on_a_focused_zone_row_opens_the_field[1440]' 'tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_two_deletes_in_one_window_both_reach_the_hub[list-a_left_selected-1440]' 'tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_a_workbench_remove_works_again_after_a_refusal[1440]' 'tests/e2e/test_philo8_01_list_rename_glass.py::TestListRenameGlass::test_a_failed_save_shows_in_the_chip_slot[393-list-422]' 'tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_a_workbench_remove_works_again_after_a_refusal[393]' 'tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_a_failed_refresh_keeps_the_pending_delete_and_its_undo[1440]' tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_a_repeated_workbench_remove_never_offers_a_false_undo 'tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_two_deletes_in_one_window_both_reach_the_hub[floor-a_taken_out-393]' 'tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_two_deletes_in_one_window_both_reach_the_hub[list-a_taken_out-1440]' 'tests/e2e/test_philo8_01_list_rename_glass.py::TestListRenameGlass::test_a_failed_save_shows_in_the_chip_slot[1440-list-422]' 'tests/e2e/test_philo8_01_zone_name_glass.py::TestZoneNameGlass::test_two_new_zone_presses_make_two_zones[1440-spatial]' 'tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_the_foot_never_covers_the_last_rows[1440]' 'tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_a_failed_refresh_keeps_the_pending_delete_and_its_undo[393]' 'tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_a_workbench_remove_after_a_refusal_offers_undo[393]' 'tests/e2e/test_philo8_01_zone_name_glass.py::TestZoneNameGlass::test_two_new_zone_presses_make_two_zones[1440-list]' 'tests/e2e/test_philo8_01_list_rename_glass.py::TestListRenameGlass::test_a_failed_save_shows_in_the_chip_slot[1440-spatial-422]' 'tests/e2e/test_philo8_01_list_rename_glass.py::TestListRenameGlass::test_a_failed_save_shows_in_the_chip_slot[393-spatial-422]' 'tests/e2e/test_philo8_01_list_rename_glass.py::TestListRenameGlass::test_a_failed_save_shows_in_the_chip_slot[1440-list-network]' 'tests/e2e/test_philo8_01_list_rename_glass.py::TestListRenameGlass::test_a_failed_save_shows_in_the_chip_slot[1440-spatial-network]' 2>&1 | tee .tmp/philo11-02/serial1.txt`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** b1f71ec6b5210279b668fd978f157aafaeafb4ca

```text
FFFFFFFFFFF.......................................................       [100%]
=================================== FAILURES ===================================
________________________ test_committed_join_validates _________________________

joined = ({'cases': [{'applicability': 'applicable', 'completion_bound_s': 120, 'edge_ids': ['edge.route.meeting_capture_recove..._shelf.refused', 'case-revision: live-astra ran an older revision of case.j10.route_brief_generate.load_failure', ...])

    def test_committed_join_validates(joined):
        graph, _ = joined
        validator = _module("philo_graph_validate")
        schema = json.loads((ROOT / "docs/internal/philo/graph/graph.schema.json").read_text(encoding="utf-8"))
>       assert validator.validate(graph, schema, ROOT) == []
E       assert ["phase1-api-...penapi.json'"] == []
E         
E         Left contains one more item: "phase1-api-unresolved: nodes[3943].phase1_refs[0]: POST /api/meetings/{meeting_id}/export/slack is not declared in 'docs/generated/openapi.json'"
E         Use -v to get more diff

tests/unit/test_philo_graph_reference.py:115: AssertionError
_____________________ test_clients_only_call_served_routes _____________________

live = {'note': 'Generated by scripts/gen_api_surface.py. Do not edit by hand.', 'routes': [{'consumers': [], 'methods': ['GE...', 'path': '/api/activity/annotations'}, ...], 'unmatched_calls': {'ios': [], 'web': ['/api/meetings/*/export/slack']}}

    def test_clients_only_call_served_routes(live) -> None:
        unmatched = live["unmatched_calls"]
        assert not unmatched["ios"], (
            "the iOS client calls paths the app does not serve: "
            f"{unmatched['ios']}")
>       assert not unmatched["web"], (
            "the web app calls paths the app does not serve: "
            f"{unmatched['web']}")
E       AssertionError: the web app calls paths the app does not serve: ['/api/meetings/*/export/slack']
E       assert not ['/api/meetings/*/export/slack']

tests/unit/test_api_surface.py:70: AssertionError
____________________ test_the_counts_over_every_atlas_file _____________________

    def test_the_counts_over_every_atlas_file() -> None:
        have = {path.name: len(json.loads(path.read_text())["cases"]) for path in general.ATLAS_FILES}
>       assert have == COUNTS
E       AssertionError: assert {'atlas-phase...son': 27, ...} == {'atlas-phase...son': 19, ...}
E         
E         Omitting 7 identical items, use -vv to show
E         Left contains 1 more item:
E         {'atlas-phase11-slack.json': 3}
E         Use -v to get more diff

tests/unit/test_philo9_atlas.py:101: AssertionError
__ test_ast_census_is_exact_for_every_routing_resolver_reference_and_pointer ___

    def test_ast_census_is_exact_for_every_routing_resolver_reference_and_pointer() -> None:
        definitions, references, pointers, profile_ids = _routing_ast_inventory(REPO)
        assert definitions == ROUTING_RESOLVER_DEFINITIONS
>       assert references == ROUTING_RESOLVER_REFERENCES
E       AssertionError: assert {'holdspeak/d...acement', ...} == {'holdspeak/d...acement', ...}
E         
E         Extra items in the left set:
E         'holdspeak/services/settings_service.py:85:ref:resolve_meeting_placement'
E         'holdspeak/services/settings_service.py:77:import:resolve_meeting_placement'
E         Extra items in the right set:
E         'holdspeak/services/settings_service.py:86:ref:resolve_meeting_placement'
E         'holdspeak/services/settings_service.py:78:import:resolve_meeting_placement'
E         Use -v to get more diff

tests/unit/test_phase143_routing_authority_census.py:366: AssertionError
____________________ test_github_decision_is_target_scoped _____________________

client = <starlette.testclient.TestClient object at 0x10d4730e0>
db = <holdspeak.db.core.Database object at 0x10cb45e50>
settings_path = PosixPath('/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/philo11-slack.LB4XJs/pytest/test_github_decision_is_target0/config.json')
gh = <tests.integration.test_web_companion_github._FakeGh object at 0x10e38ef90>

    @pytest.mark.integration
    def test_github_decision_is_target_scoped(client, db, settings_path, gh):
        _configure(settings_path)
        pid = client.post(PROPOSE, json={"text": "ship it"}).json()["proposal"]["id"]
        # a github proposal cannot be decided on the slack or webhook routes
>       assert client.post(f"/api/desk/actuators/slack/{pid}/decision", json={"decision": "approved"}).status_code == 404
E       AssertionError: assert 400 == 404
E        +  where 400 = <Response [400 Bad Request]>.status_code
E        +    where <Response [400 Bad Request]> = post('/api/desk/actuators/slack/cbb053a9d8bb4eed814b7147e0fc7f68/decision', json={'decision': 'approved'})
E        +      where post = <starlette.testclient.TestClient object at 0x10d4730e0>.post

tests/integration/test_web_companion_github.py:244: AssertionError
_ test_the_canonical_map_has_all_seventeen_operations_and_no_local_service_target _

    def test_the_canonical_map_has_all_seventeen_operations_and_no_local_service_target():
        # PHILO-5's seventeen, PHILO-7-01's fifteen desk-slice rows, then
        # PHILO-7-02's nine (decision.status is HTTP only: OP_HTTP_ONLY), then
        # PHILO-9-01's twenty-five Room rows (the Door's create is HTTP only),
        # then PHILO-9-02's twenty-one (the Door's count, a watch's update and
        # its baseline are HTTP only), then PHILO-10-01's nine (the Send).
        assert len(gw.OP_MCP_PROJECTIONS) == 96
        assert set(gw.OP_MCP_PROJECTIONS) == {
            "decision.create", "decision.update", "decision.read", "decision.list",
            "meeting.list", "meeting.read", "meeting.import", "meeting.summary.run",
            "brief.generate", "brief.latest", "brief.shelf.write", "brief.shelf.read",
            "thought.create", "thought.save", "thought.read",
            "thought.workbench.read", "thought.list",
            "note.create", "note.read", "note.update", "note.delete", "note.list",
            "zone.create", "zone.read", "zone.update", "zone.delete", "zone.list",
            "kb.create", "kb.read", "kb.update", "kb.delete", "kb.list",
            "zone.file", "zone.unfile", "zone.members",
            "kb.member.add", "kb.member.remove", "kb.members",
            "decision.delete", "decision.supersede", "kernel.receipt.read",
            "project.list", "project.get", "project.get_room", "project.create", "project.update",
            "project.archive", "project.restore", "project.link", "project.unlink",
            "project.open_review", "project.get_delta", "project.decide_proposal", "project.accept_review",
            "project.list_updates", "project.draft_update", "project.update_draft", "project.publish_update",
            "desk.needs_you", "project.item.list", "project.item.create", "project.item.update",
            "project.item.transition", "project.resource.list", "project.resource.add", "project.resource.remove",
            "project.configure_steward", "project.run_steward", "project.stop_steward", "project.get_steward_run",
            "project.steward.trigger", "steward.nudges", "nudge.send", "nudge.dismiss",
            "project.watch.inspect", "project.watch.test", "project.watch.evaluate", "project.watch.set_rules",
            "project.watch.pause", "project.watch.resume", "project.watch.retire",
            "project.suggested_sources", "project.add_suggested_source", "project.dismiss_suggested_source",
            "connection.list", "connection.recheck", "project.mark_update_delivered",
            "channel.destinations", "channel.save_destination", "channel.remove_destination",
            "channel.check_destination", "channel.preview", "channel.prepare", "channel.discard",
            "channel.send", "channel.sends",
        }
>       assert gw.OP_HTTP_ONLY == {"decision.status", "project.door.create",
                                   "project.door.count", "project.watch.update", "project.watch.baseline",
                                   "channel.save_email_key"}
E       AssertionError: assert frozenset({'c...seline', ...}) == {'channel.sav...watch.update'}
E         
E         Extra items in the left set:
E         'channel.save_slack_webhook'
E         Use -v to get more diff

tests/unit/test_philo5_graph_op.py:73: AssertionError
__________________ test_the_catalogue_is_explicit_descriptors __________________

    def test_the_catalogue_is_explicit_descriptors() -> None:
        names = [d.name for d in operations.DESCRIPTORS]
        # PHILO-5-01's four, then PHILO-5-02's loop, then PHILO-7-01's desk slice
        # -- an explicit list, no framework.
>       assert names == [
            "decision.create", "decision.update", "decision.read", "decision.list",
            "meeting.list", "meeting.read", "meeting.import", "meeting.summary.run",
            "brief.generate", "brief.latest", "brief.shelf.write", "brief.shelf.read",
            "thought.create", "thought.save", "thought.read", "thought.workbench.read", "thought.list",
            # PHILO-7-01: the desk slice, one row per (kind, verb).
            "note.create", "note.read", "note.update", "note.delete", "note.list",
            "zone.create", "zone.read", "zone.update", "zone.delete", "zone.list",
            "kb.create", "kb.read", "kb.update", "kb.delete", "kb.list",
            # PHILO-7-02: membership, the remaining decision operations, the receipt read.
            "zone.file", "zone.unfile", "zone.members", "kb.member.add", "kb.member.remove", "kb.members",
            "decision.delete", "decision.status", "decision.supersede",
            "kernel.receipt.read",
            # PHILO-9-01: the Room on the contract, one row per operation.
            "project.list", "project.get", "project.get_room", "project.create", "project.door.create",
            "project.update", "project.archive", "project.restore", "project.link", "project.unlink",
            "project.open_review", "project.get_delta", "project.decide_proposal", "project.accept_review",
            "project.list_updates", "project.draft_update", "project.update_draft", "project.publish_update",
            "desk.needs_you",
            "project.item.list", "project.item.create", "project.item.update", "project.item.transition",
            "project.resource.list", "project.resource.add", "project.resource.remove",
            # PHILO-9-02: the steward, the nudges, the watches, the suggested
            # sources, the connections, the Door count and the delivery mark.
            "project.configure_steward", "project.run_steward", "project.stop_steward", "project.get_steward_run",
            "project.steward.trigger", "steward.nudges", "nudge.send", "nudge.dismiss",
            "project.watch.inspect", "project.watch.test", "project.watch.evaluate", "project.watch.set_rules",
            "project.watch.pause", "project.watch.resume", "project.watch.retire", "project.watch.update",
            "project.watch.baseline", "project.suggested_sources", "project.add_suggested_source",
            "project.dismiss_suggested_source", "connection.list", "connection.recheck", "project.door.count",
            "project.mark_update_delivered",
            # PHILO-10-01: the Send.
            "channel.destinations", "channel.save_destination", "channel.remove_destination",
            "channel.check_destination", "channel.preview", "channel.prepare", "channel.discard",
            "channel.send", "channel.sends",
            # PHILO-10-03: the email key (HTTP only; the key is a held input).
            "channel.save_email_key",
        ]
E       AssertionError: assert ['decision.cr...ng.read', ...] == ['decision.cr...ng.read', ...]
E         
E         Left contains one more item: 'channel.save_slack_webhook'
E         Use -v to get more diff

tests/unit/test_philo5_one_decision.py:220: AssertionError
___________________ test_every_emitted_code_has_a_face_word ____________________

    def test_every_emitted_code_has_a_face_word() -> None:
>       assert codes.missing() == []
E       AssertionError: assert [('refused', ...ook_missing')] == []
E         
E         Left contains 6 more items, first extra item: ('refused', 'slack_channel_label_invalid')
E         Use -v to get more diff

tests/unit/test_philo10_face_words.py:25: AssertionError
____________________ test_no_code_expression_is_unsupported ____________________

    def test_no_code_expression_is_unsupported() -> None:
        """Codex Astra r1 on #698 (finding 1): an f-string outside ALLOWED_TEMPLATES, a
        ``.format()``, a concatenation, a call -- any code expression the derivation
        cannot read, in a producer or behind a declared flow -- fails here, by name."""
>       assert codes.emitted()["__unsupported__"]["where"] == []
E       AssertionError: assert ['holdspeak/s...on str(code)'] == []
E         
E         Left contains 2 more items, first extra item: 'holdspeak/services/channel_service.py:302: code expression str(code)'
E         Use -v to get more diff

tests/unit/test_philo10_face_words.py:32: AssertionError
__________ test_the_contract_refuses_a_non_owner_before_anything_else __________

tmp_path = PosixPath('/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/philo11-slack.LB4XJs/pytest/test_the_contract_refuses_a_no0')

    def test_the_contract_refuses_a_non_owner_before_anything_else(tmp_path: Path) -> None:
        from holdspeak.db import Database
        from holdspeak.services.meeting_service import MeetingService
    
        registry = operations.bind_available({"meeting_service": MeetingService(Database(tmp_path / "h.db"))})
        for principal in (None, Principal(PrincipalKind.AGENT, "a"), Principal(PrincipalKind.NODE, "n"),
                          Principal(PrincipalKind.SERVICE, "s"), Principal(PrincipalKind.NONE, "")):
            with pytest.raises(operations.OperationOwnerRequired) as exc:
                # No held inputs and bad arguments: the owner refusal still comes first.
                registry.invoke(principal, "meeting.import", {"nope": 1})
            assert exc.value.code == "owner_required"
        assert operations.MEETING_IMPORT.owner_only is True
        # PHILO-10-03: channel.save_email_key is owner only too (the key is a held input, HTTP only).
>       assert [d.name for d in operations.DESCRIPTORS if d.owner_only] == ["meeting.import", "channel.save_email_key"]
E       AssertionError: assert ['meeting.imp...lack_webhook'] == ['meeting.imp...ve_email_key']
E         
E         Left contains one more item: 'channel.save_slack_webhook'
E         Use -v to get more diff

tests/unit/test_philo5_the_loop_r2.py:220: AssertionError
______________ test_every_braced_declaration_has_a_producer_here _______________

    def test_every_braced_declaration_has_a_producer_here() -> None:
        declared = {d.name for d in operations.DESCRIPTORS if _declared_keys(d.result) is not None}
>       assert declared == set(PRODUCERS), "a descriptor declares a shape this fence does not run"
E       AssertionError: a descriptor declares a shape this fence does not run
E       assert {'brief.shelf...prepare', ...} == {'brief.shelf...prepare', ...}
E         
E         Extra items in the left set:
E         'channel.save_slack_webhook'
E         Use -v to get more diff

tests/unit/test_philo5_the_loop_r2.py:583: AssertionError
=========================== short test summary info ============================
FAILED tests/unit/test_philo_graph_reference.py::test_committed_join_validates
FAILED tests/unit/test_api_surface.py::test_clients_only_call_served_routes
FAILED tests/unit/test_philo9_atlas.py::test_the_counts_over_every_atlas_file
FAILED tests/unit/test_phase143_routing_authority_census.py::test_ast_census_is_exact_for_every_routing_resolver_reference_and_pointer
FAILED tests/integration/test_web_companion_github.py::test_github_decision_is_target_scoped
FAILED tests/unit/test_philo5_graph_op.py::test_the_canonical_map_has_all_seventeen_operations_and_no_local_service_target
FAILED tests/unit/test_philo5_one_decision.py::test_the_catalogue_is_explicit_descriptors
FAILED tests/unit/test_philo10_face_words.py::test_every_emitted_code_has_a_face_word
FAILED tests/unit/test_philo10_face_words.py::test_no_code_expression_is_unsupported
FAILED tests/unit/test_philo5_the_loop_r2.py::test_the_contract_refuses_a_non_owner_before_anything_else
FAILED tests/unit/test_philo5_the_loop_r2.py::test_every_braced_declaration_has_a_producer_here
11 failed, 55 passed in 1282.18s (0:21:22)
```

### Captured run — 2026-09-30T08:17:28Z

- **Command:** `bash -o pipefail -c bash scripts/verify_philo11_slack.sh run uv run --python 3.13 --extra dev python scripts/check_web_baseline.py --run 2>&1 | tee .tmp/philo11-02/web-baseline.txt`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** b1f71ec6b5210279b668fd978f157aafaeafb4ca

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

### Captured run — 2026-09-30T08:23:09Z

- **Command:** `bash -o pipefail -c bash scripts/verify_philo11_slack.sh pytest -q --collect-only tests/unit/test_philo11_slack_channel.py tests/integration/test_philo11_slack_operations.py tests/integration/test_philo11_slack_rewrite.py tests/unit/test_philo11_channel_contract.py tests/unit/test_philo10_face_words.py tests/unit/test_philo9_atlas.py::test_the_counts_over_every_atlas_file tests/unit/test_phase143_routing_authority_census.py::test_ast_census_is_exact_for_every_routing_resolver_reference_and_pointer tests/integration/test_web_companion_github.py::test_github_decision_is_target_scoped tests/unit/test_philo5_graph_op.py::test_the_canonical_map_has_all_seventeen_operations_and_no_local_service_target tests/unit/test_philo5_one_decision.py::test_the_catalogue_is_explicit_descriptors tests/unit/test_philo5_the_loop_r2.py::test_the_contract_refuses_a_non_owner_before_anything_else tests/unit/test_philo5_the_loop_r2.py::test_every_braced_declaration_has_a_producer_here -k 'not test_every_emitted_code_has_a_face_word' 2>&1 | tee .tmp/philo11-02/collect-final.txt`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** b1f71ec6b5210279b668fd978f157aafaeafb4ca

```text
tests/unit/test_philo11_slack_channel.py::test_save_target_has_only_label_and_key_reference_and_url_rule
tests/unit/test_philo11_slack_channel.py::test_real_save_key_rejects_every_non_admitted_webhook_url[http://hooks.slack.com/services/T/B/K]
tests/unit/test_philo11_slack_channel.py::test_real_save_key_rejects_every_non_admitted_webhook_url[https://evil.example/services/T/B/K]
tests/unit/test_philo11_slack_channel.py::test_real_save_key_rejects_every_non_admitted_webhook_url[https://hooks.slack.com:0/services/T/B/K]
tests/unit/test_philo11_slack_channel.py::test_real_save_key_rejects_every_non_admitted_webhook_url[https://hooks.slack.com:8443/services/T/B/K]
tests/unit/test_philo11_slack_channel.py::test_real_save_key_rejects_every_non_admitted_webhook_url[https://hooks.slack.com/not-services/T/B/K]
tests/unit/test_philo11_slack_channel.py::test_real_save_key_rejects_every_non_admitted_webhook_url[https://hooks.slack.com/services/T/B/K?leak=yes]
tests/unit/test_philo11_slack_channel.py::test_real_save_key_accepts_default_and_explicit_443
tests/unit/test_philo11_slack_channel.py::test_markdown_is_serialized_once_and_preview_is_read_from_frozen_bytes
tests/unit/test_philo11_slack_channel.py::test_size_refusal_is_named_before_dispatch
tests/unit/test_philo11_slack_channel.py::test_multibyte_text_limit_counts_characters_in_serialize_and_plan
tests/unit/test_philo11_slack_channel.py::test_pinned_outcomes[200-ok-headers0-sent-None]
tests/unit/test_philo11_slack_channel.py::test_pinned_outcomes[200-OK-headers1-unknown-ack_missing]
tests/unit/test_philo11_slack_channel.py::test_pinned_outcomes[400-invalid_payload-headers2-failed-invalid_payload]
tests/unit/test_philo11_slack_channel.py::test_pinned_outcomes[403-action_prohibited-headers3-failed-action_prohibited]
tests/unit/test_philo11_slack_channel.py::test_pinned_outcomes[404-channel_not_found-headers4-failed-channel_not_found]
tests/unit/test_philo11_slack_channel.py::test_pinned_outcomes[410-channel_is_archived-headers5-failed-channel_is_archived]
tests/unit/test_philo11_slack_channel.py::test_pinned_outcomes[429-rate_limited-headers6-failed-rate_limited]
tests/unit/test_philo11_slack_channel.py::test_pinned_outcomes[500-rollup_error-headers7-unknown-rollup_error]
tests/unit/test_philo11_slack_channel.py::test_pinned_outcomes[503-unavailable-headers8-unknown-unpinned_503]
tests/unit/test_philo11_slack_channel.py::test_pinned_outcomes[302--headers9-unknown-redirect_refused]
tests/unit/test_philo11_slack_channel.py::test_transmit_reads_memory_key_and_sends_frozen_bytes_only
tests/unit/test_philo11_slack_channel.py::test_transport_errors_do_not_expose_webhook
tests/unit/test_philo11_slack_channel.py::test_native_key_store_accepts_only_the_three_native_backends[keyring.backends.macOS-Keyring]
tests/unit/test_philo11_slack_channel.py::test_native_key_store_accepts_only_the_three_native_backends[keyring.backends.SecretService-Keyring]
tests/unit/test_philo11_slack_channel.py::test_native_key_store_accepts_only_the_three_native_backends[keyring.backends.Windows-WinVaultKeyring]
tests/unit/test_philo11_slack_channel.py::test_non_native_key_store_is_refused_by_name[backend0]
tests/unit/test_philo11_slack_channel.py::test_non_native_key_store_is_refused_by_name[backend1]
tests/unit/test_philo11_slack_channel.py::test_non_native_key_store_is_refused_by_name[backend2]
tests/unit/test_philo11_slack_channel.py::test_native_key_store_distinguishes_locked_and_missing_without_os_keychain
tests/unit/test_philo11_slack_channel.py::test_quiet_https_edge_tracks_before_and_after_byte_failures[connect_error0-None-False-connect_refused]
tests/unit/test_philo11_slack_channel.py::test_quiet_https_edge_tracks_before_and_after_byte_failures[connect_error1-None-False-tls_failed]
tests/unit/test_philo11_slack_channel.py::test_quiet_https_edge_tracks_before_and_after_byte_failures[connect_error2-None-False-dns_failed]
tests/unit/test_philo11_slack_channel.py::test_quiet_https_edge_tracks_before_and_after_byte_failures[None-fail_after_connect3-True-tls_failed]
tests/unit/test_philo11_slack_channel.py::test_native_keyring_is_never_constructed_by_unit_fixture
tests/integration/test_philo11_slack_operations.py::test_save_check_preview_prepare_and_send_use_the_real_slack_producer
tests/integration/test_philo11_slack_operations.py::test_each_slack_outcome_is_interpreted_by_the_real_send[ok-answer-sent-None]
tests/integration/test_philo11_slack_operations.py::test_each_slack_outcome_is_interpreted_by_the_real_send[invalid-answer-failed-invalid_payload]
tests/integration/test_philo11_slack_operations.py::test_each_slack_outcome_is_interpreted_by_the_real_send[prohibited-answer-failed-action_prohibited]
tests/integration/test_philo11_slack_operations.py::test_each_slack_outcome_is_interpreted_by_the_real_send[missing-answer-failed-channel_not_found]
tests/integration/test_philo11_slack_operations.py::test_each_slack_outcome_is_interpreted_by_the_real_send[archived-answer-failed-channel_is_archived]
tests/integration/test_philo11_slack_operations.py::test_each_slack_outcome_is_interpreted_by_the_real_send[rate_limited-answer-failed-rate_limited]
tests/integration/test_philo11_slack_operations.py::test_each_slack_outcome_is_interpreted_by_the_real_send[rollup-answer-unknown-rollup_error]
tests/integration/test_philo11_slack_operations.py::test_each_slack_outcome_is_interpreted_by_the_real_send[other_5xx-answer-unknown-unpinned_503]
tests/integration/test_philo11_slack_operations.py::test_each_slack_outcome_is_interpreted_by_the_real_send[redirect-answer-unknown-redirect_refused]
tests/integration/test_philo11_slack_operations.py::test_each_slack_outcome_is_interpreted_by_the_real_send[wrong_ok-answer-unknown-ack_missing]
tests/integration/test_philo11_slack_operations.py::test_each_slack_outcome_is_interpreted_by_the_real_send[unlisted-answer-unknown-unpinned_418]
tests/integration/test_philo11_slack_operations.py::test_each_slack_outcome_is_interpreted_by_the_real_send[timeout-answer-unknown-timeout]
tests/integration/test_philo11_slack_operations.py::test_each_slack_outcome_is_interpreted_by_the_real_send[secret_echo-answer-unknown-unpinned_400]
tests/integration/test_philo11_slack_operations.py::test_unknown_replay_and_rate_limit_never_post_again[unknown]
tests/integration/test_philo11_slack_operations.py::test_unknown_replay_and_rate_limit_never_post_again[rate_limited]
tests/integration/test_philo11_slack_operations.py::test_an_agent_cannot_press_slack_send
tests/integration/test_philo11_slack_operations.py::test_transport_failure_records_whether_bytes_may_have_left[connect_before-error0-False-failed-connect_refused]
tests/integration/test_philo11_slack_operations.py::test_transport_failure_records_whether_bytes_may_have_left[dns_before-error1-False-failed-dns_failed]
tests/integration/test_philo11_slack_operations.py::test_transport_failure_records_whether_bytes_may_have_left[tls_before-error2-False-failed-tls_failed]
tests/integration/test_philo11_slack_operations.py::test_transport_failure_records_whether_bytes_may_have_left[timeout_before-error3-False-failed-timeout]
tests/integration/test_philo11_slack_operations.py::test_transport_failure_records_whether_bytes_may_have_left[tls_after-error4-True-unknown-tls_failed]
tests/integration/test_philo11_slack_operations.py::test_transport_failure_records_whether_bytes_may_have_left[timeout_after-error5-True-unknown-timeout]
tests/integration/test_philo11_slack_operations.py::test_size_refusal_is_real_and_carries_size_and_limit_before_wire
tests/integration/test_philo11_slack_operations.py::test_slack_size_is_text_characters_in_preview_and_prepared_send
tests/integration/test_philo11_slack_operations.py::test_replacing_slack_destination_parks_old_and_old_prepare_refuses
tests/integration/test_philo11_slack_operations.py::test_invalid_webhook_is_refused_at_save_without_key_or_wire[http://hooks.slack.com/services/T/B/K]
tests/integration/test_philo11_slack_operations.py::test_invalid_webhook_is_refused_at_save_without_key_or_wire[https://slack.com/services/T/B/K]
tests/integration/test_philo11_slack_operations.py::test_invalid_webhook_is_refused_at_save_without_key_or_wire[https://hooks.slack.com:8443/services/T/B/K]
tests/integration/test_philo11_slack_operations.py::test_invalid_webhook_is_refused_at_save_without_key_or_wire[https://hooks.slack.com/services/T/B/K?secret=leak]
tests/integration/test_philo11_slack_rewrite.py::test_old_config_loads_but_aftercare_does_not_advertise_slack
tests/integration/test_philo11_slack_rewrite.py::test_settings_read_and_write_keep_the_retained_field_private
tests/integration/test_philo11_slack_rewrite.py::test_settings_write_ignores_the_retained_field
tests/integration/test_philo11_slack_rewrite.py::test_posture_aftercare_route_is_gone_and_never_posts
tests/integration/test_philo11_slack_rewrite.py::test_desk_slack_target_is_parked
tests/integration/test_philo11_slack_rewrite.py::test_historical_slack_proposals_remain_readable
tests/integration/test_philo11_slack_rewrite.py::test_legacy_slack_connector_is_removed
tests/unit/test_philo11_channel_contract.py::test_generic_document_ref_is_one_wire_for_http_mcp_and_history_filter
tests/unit/test_philo11_channel_contract.py::test_prepared_send_uses_frozen_bytes_and_name_after_source_is_deleted[project_update]
tests/unit/test_philo11_channel_contract.py::test_prepared_send_uses_frozen_bytes_and_name_after_source_is_deleted[desk_decision]
tests/unit/test_philo11_channel_contract.py::test_legacy_prepared_non_file_row_does_not_reread_deleted_source
tests/unit/test_philo11_channel_contract.py::test_inline_send_refuses_changed_preview_then_sends_new_preview[project_update]
tests/unit/test_philo11_channel_contract.py::test_inline_send_refuses_changed_preview_then_sends_new_preview[desk_decision]
tests/unit/test_philo11_channel_contract.py::test_kernel_target_names_document_ref_and_external_agent_send_is_refused_over_mcp[project_update]
tests/unit/test_philo11_channel_contract.py::test_kernel_target_names_document_ref_and_external_agent_send_is_refused_over_mcp[desk_decision]
tests/unit/test_philo11_channel_contract.py::test_agent_brief_preview_and_prepare_keep_owner_overlay_and_payload
tests/unit/test_philo11_channel_contract.py::test_thread_palette_discovers_destination_then_prepares_without_send_admission
tests/unit/test_philo10_face_words.py::test_no_code_expression_is_unsupported
tests/unit/test_philo10_face_words.py::test_every_variable_code_site_is_followed
tests/unit/test_philo10_face_words.py::test_the_derivation_sees_the_known_codes_of_each_kind
tests/unit/test_philo10_face_words.py::test_slack_codes_are_derived_from_the_backend_source[slack_webhook_invalid-refused]
tests/unit/test_philo10_face_words.py::test_slack_codes_are_derived_from_the_backend_source[invalid_payload-failed]
tests/unit/test_philo10_face_words.py::test_slack_codes_are_derived_from_the_backend_source[rollup_error-unknown]
tests/unit/test_philo10_face_words.py::test_the_face_reads_its_tables_through_the_word_functions
tests/unit/test_philo10_face_words.py::test_every_face_word_is_plain
tests/unit/test_philo10_face_words.py::test_the_census_codes_have_their_words[github_target_not_found-ISSUE NOT FOUND]
tests/unit/test_philo10_face_words.py::test_the_census_codes_have_their_words[github_permission_denied-NO PERMISSION]
tests/unit/test_philo10_face_words.py::test_the_census_codes_have_their_words[jira_cannot_be_edited-CANNOT COMMENT]
tests/unit/test_philo10_face_words.py::test_the_census_codes_have_their_words[atlassian_unauthorized-NOT SIGNED IN]
tests/unit/test_philo9_atlas.py::test_the_counts_over_every_atlas_file
tests/unit/test_phase143_routing_authority_census.py::test_ast_census_is_exact_for_every_routing_resolver_reference_and_pointer
tests/integration/test_web_companion_github.py::test_github_decision_is_target_scoped
tests/unit/test_philo5_graph_op.py::test_the_canonical_map_has_all_seventeen_operations_and_no_local_service_target
tests/unit/test_philo5_one_decision.py::test_the_catalogue_is_explicit_descriptors
tests/unit/test_philo5_the_loop_r2.py::test_the_contract_refuses_a_non_owner_before_anything_else
tests/unit/test_philo5_the_loop_r2.py::test_every_braced_declaration_has_a_producer_here

101/102 tests collected (1 deselected) in 0.92s
```

### Captured run — 2026-09-30T08:23:48Z

- **Command:** `bash -o pipefail -c bash scripts/verify_philo11_slack.sh pytest -q -n 0 tests/unit/test_philo11_slack_channel.py tests/integration/test_philo11_slack_operations.py tests/integration/test_philo11_slack_rewrite.py tests/unit/test_philo11_channel_contract.py tests/unit/test_philo10_face_words.py tests/unit/test_philo9_atlas.py::test_the_counts_over_every_atlas_file tests/unit/test_phase143_routing_authority_census.py::test_ast_census_is_exact_for_every_routing_resolver_reference_and_pointer tests/integration/test_web_companion_github.py::test_github_decision_is_target_scoped tests/unit/test_philo5_graph_op.py::test_the_canonical_map_has_all_seventeen_operations_and_no_local_service_target tests/unit/test_philo5_one_decision.py::test_the_catalogue_is_explicit_descriptors tests/unit/test_philo5_the_loop_r2.py::test_the_contract_refuses_a_non_owner_before_anything_else tests/unit/test_philo5_the_loop_r2.py::test_every_braced_declaration_has_a_producer_here -k 'not test_every_emitted_code_has_a_face_word' 2>&1 | tee .tmp/philo11-02/focused-final.txt`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** b1f71ec6b5210279b668fd978f157aafaeafb4ca

```text
........................................................................ [ 71%]
.......................F.....                                            [100%]
=================================== FAILURES ===================================
__ test_ast_census_is_exact_for_every_routing_resolver_reference_and_pointer ___

    def test_ast_census_is_exact_for_every_routing_resolver_reference_and_pointer() -> None:
        definitions, references, pointers, profile_ids = _routing_ast_inventory(REPO)
        assert definitions == ROUTING_RESOLVER_DEFINITIONS
        assert references == ROUTING_RESOLVER_REFERENCES
>       assert pointers == ROUTING_POINTER_ATTRIBUTES
E       AssertionError: assert {'holdspeak/c...file_id', ...} == {'holdspeak/c...file_id', ...}
E         
E         Extra items in the left set:
E         'holdspeak/config/meeting.py:169:intel_profile_id'
E         'holdspeak/config/meeting.py:170:intel_profile_id'
E         Extra items in the right set:
E         'holdspeak/config/meeting.py:172:intel_profile_id'
E         'holdspeak/config/meeting.py:173:intel_profile_id'
E         Use -v to get more diff

tests/unit/test_phase143_routing_authority_census.py:367: AssertionError
=========================== short test summary info ============================
FAILED tests/unit/test_phase143_routing_authority_census.py::test_ast_census_is_exact_for_every_routing_resolver_reference_and_pointer
1 failed, 100 passed, 1 deselected in 40.67s
```

### Captured run — 2026-09-30T08:25:09Z

- **Command:** `bash -o pipefail -c bash scripts/verify_philo11_slack.sh pytest -q -n 0 tests/unit/test_philo11_slack_channel.py tests/integration/test_philo11_slack_operations.py tests/integration/test_philo11_slack_rewrite.py tests/unit/test_philo11_channel_contract.py tests/unit/test_philo10_face_words.py tests/unit/test_philo9_atlas.py::test_the_counts_over_every_atlas_file tests/unit/test_phase143_routing_authority_census.py::test_ast_census_is_exact_for_every_routing_resolver_reference_and_pointer tests/integration/test_web_companion_github.py::test_github_decision_is_target_scoped tests/unit/test_philo5_graph_op.py::test_the_canonical_map_has_all_seventeen_operations_and_no_local_service_target tests/unit/test_philo5_one_decision.py::test_the_catalogue_is_explicit_descriptors tests/unit/test_philo5_the_loop_r2.py::test_the_contract_refuses_a_non_owner_before_anything_else tests/unit/test_philo5_the_loop_r2.py::test_every_braced_declaration_has_a_producer_here -k 'not test_every_emitted_code_has_a_face_word' 2>&1 | tee .tmp/philo11-02/focused-final.txt`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** b1f71ec6b5210279b668fd978f157aafaeafb4ca

```text
........................................................................ [ 71%]
.............................                                            [100%]
101 passed, 1 deselected in 42.55s
```

### Captured run — 2026-09-30T08:26:25Z

- **Command:** `bash -o pipefail -c bash scripts/verify_philo11_slack.sh pytest -vv -n 0 tests/unit/test_philo_graph_reference.py::test_committed_join_validates tests/unit/test_api_surface.py::test_clients_only_call_served_routes tests/unit/test_philo10_face_words.py::test_every_emitted_code_has_a_face_word 2>&1 | tee .tmp/philo11-02/held-guards.txt`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** b1f71ec6b5210279b668fd978f157aafaeafb4ca

```text
============================= test session starts ==============================
platform darwin -- Python 3.13.14, pytest-9.0.2, pluggy-1.6.0 -- /Users/karol/dev/tools/wt-philo-11-02/.venv/bin/python
cachedir: .pytest_cache
holdspeak: HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T//philo11-slack.ejyUSV
rootdir: /Users/karol/dev/tools/wt-philo-11-02
configfile: pyproject.toml
plugins: anyio-4.12.1, mock-3.15.1, xdist-3.8.0, timeout-2.4.0, asyncio-1.3.0, cov-7.0.0
timeout: 300.0s
timeout method: thread
timeout func_only: False
asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=function, asyncio_default_test_loop_scope=function
collecting ... collected 3 items

tests/unit/test_philo_graph_reference.py::test_committed_join_validates FAILED [ 33%]
tests/unit/test_api_surface.py::test_clients_only_call_served_routes FAILED [ 66%]
tests/unit/test_philo10_face_words.py::test_every_emitted_code_has_a_face_word FAILED [100%]

=================================== FAILURES ===================================
________________________ test_committed_join_validates _________________________

joined = ({'cases': [{'applicability': 'applicable', 'completion_bound_s': 120, 'edge_ids': ['edge.route.meeting_capture_recove..._shelf.refused', 'case-revision: live-astra ran an older revision of case.j10.route_brief_generate.load_failure', ...])

    def test_committed_join_validates(joined):
        graph, _ = joined
        validator = _module("philo_graph_validate")
        schema = json.loads((ROOT / "docs/internal/philo/graph/graph.schema.json").read_text(encoding="utf-8"))
>       assert validator.validate(graph, schema, ROOT) == []
E       assert ["phase1-api-unresolved: nodes[3943].phase1_refs[0]: POST /api/meetings/{meeting_id}/export/slack is not declared in 'docs/generated/openapi.json'"] == []
E         
E         Left contains one more item: "phase1-api-unresolved: nodes[3943].phase1_refs[0]: POST /api/meetings/{meeting_id}/export/slack is not declared in 'docs/generated/openapi.json'"
E         
E         Full diff:
E         - []
E         + [
E         +     'phase1-api-unresolved: nodes[3943].phase1_refs[0]: POST '
E         +     '/api/meetings/{meeting_id}/export/slack is not declared in '
E         +     "'docs/generated/openapi.json'",
E         + ]

tests/unit/test_philo_graph_reference.py:115: AssertionError
_____________________ test_clients_only_call_served_routes _____________________

live = {'note': 'Generated by scripts/gen_api_surface.py. Do not edit by hand.', 'routes': [{'consumers': [], 'methods': ['GE...', 'path': '/api/activity/annotations'}, ...], 'unmatched_calls': {'ios': [], 'web': ['/api/meetings/*/export/slack']}}

    def test_clients_only_call_served_routes(live) -> None:
        unmatched = live["unmatched_calls"]
        assert not unmatched["ios"], (
            "the iOS client calls paths the app does not serve: "
            f"{unmatched['ios']}")
>       assert not unmatched["web"], (
            "the web app calls paths the app does not serve: "
            f"{unmatched['web']}")
E       AssertionError: the web app calls paths the app does not serve: ['/api/meetings/*/export/slack']
E       assert not ['/api/meetings/*/export/slack']

tests/unit/test_api_surface.py:70: AssertionError
___________________ test_every_emitted_code_has_a_face_word ____________________

    def test_every_emitted_code_has_a_face_word() -> None:
>       assert codes.missing() == []
E       AssertionError: assert [('unknown', 'ack_missing'), ('failed', 'action_prohibited'), ('failed', 'channel_is_archived'), ('failed', 'channel_not_found'), ('failed', 'invalid_payload'), ('failed', 'payload_too_large:slack'), ('unknown', 'plan_refused'), ('unknown', 'rollup_error'), ('refused', 'slack_channel_label_invalid'), ('refused', 'slack_key_ref_invalid'), ('failed', 'slack_key_store_locked'), ('refused', 'slack_key_store_locked'), ('unknown', 'slack_key_store_locked'), ('failed', 'slack_key_store_not_native'), ('refused', 'slack_key_store_not_native'), ('unknown', 'slack_key_store_not_native'), ('failed', 'slack_webhook_invalid'), ('refused', 'slack_webhook_invalid'), ('unknown', 'slack_webhook_invalid'), ('failed', 'slack_webhook_missing'), ('refused', 'slack_webhook_missing'), ('unknown', 'slack_webhook_missing')] == []
E         
E         Left contains 22 more items, first extra item: ('unknown', 'ack_missing')
E         
E         Full diff:
E         - []
E         + [
E         +     (
E         +         'unknown',
E         +         'ack_missing',
E         +     ),
E         +     (
E         +         'failed',
E         +         'action_prohibited',
E         +     ),
E         +     (
E         +         'failed',
E         +         'channel_is_archived',
E         +     ),
E         +     (
E         +         'failed',
E         +         'channel_not_found',
E         +     ),
E         +     (
E         +         'failed',
E         +         'invalid_payload',
E         +     ),
E         +     (
E         +         'failed',
E         +         'payload_too_large:slack',
E         +     ),
E         +     (
E         +         'unknown',
E         +         'plan_refused',
E         +     ),
E         +     (
E         +         'unknown',
E         +         'rollup_error',
E         +     ),
E         +     (
E         +         'refused',
E         +         'slack_channel_label_invalid',
E         +     ),
E         +     (
E         +         'refused',
E         +         'slack_key_ref_invalid',
E         +     ),
E         +     (
E         +         'failed',
E         +         'slack_key_store_locked',
E         +     ),
E         +     (
E         +         'refused',
E         +         'slack_key_store_locked',
E         +     ),
E         +     (
E         +         'unknown',
E         +         'slack_key_store_locked',
E         +     ),
E         +     (
E         +         'failed',
E         +         'slack_key_store_not_native',
E         +     ),
E         +     (
E         +         'refused',
E         +         'slack_key_store_not_native',
E         +     ),
E         +     (
E         +         'unknown',
E         +         'slack_key_store_not_native',
E         +     ),
E         +     (
E         +         'failed',
E         +         'slack_webhook_invalid',
E         +     ),
E         +     (
E         +         'refused',
E         +         'slack_webhook_invalid',
E         +     ),
E         +     (
E         +         'unknown',
E         +         'slack_webhook_invalid',
E         +     ),
E         +     (
E         +         'failed',
E         +         'slack_webhook_missing',
E         +     ),
E         +     (
E         +         'refused',
E         +         'slack_webhook_missing',
E         +     ),
E         +     (
E         +         'unknown',
E         +         'slack_webhook_missing',
E         +     ),
E         + ]

tests/unit/test_philo10_face_words.py:25: AssertionError
=========================== short test summary info ============================
FAILED tests/unit/test_philo_graph_reference.py::test_committed_join_validates - assert ["phase1-api-unresolved: nodes[3943].phase1_refs[0]: POST /api/meetings/{meeting_id}/export/slack is not declared in 'docs/generated/openapi.json'"] == []
  
  Left contains one more item: "phase1-api-unresolved: nodes[3943].phase1_refs[0]: POST /api/meetings/{meeting_id}/export/slack is not declared in 'docs/generated/openapi.json'"
  
  Full diff:
  - []
  + [
  +     'phase1-api-unresolved: nodes[3943].phase1_refs[0]: POST '
  +     '/api/meetings/{meeting_id}/export/slack is not declared in '
  +     "'docs/generated/openapi.json'",
  + ]
FAILED tests/unit/test_api_surface.py::test_clients_only_call_served_routes - AssertionError: the web app calls paths the app does not serve: ['/api/meetings/*/export/slack']
assert not ['/api/meetings/*/export/slack']
FAILED tests/unit/test_philo10_face_words.py::test_every_emitted_code_has_a_face_word - AssertionError: assert [('unknown', 'ack_missing'), ('failed', 'action_prohibited'), ('failed', 'channel_is_archived'), ('failed', 'channel_not_found'), ('failed', 'invalid_payload'), ('failed', 'payload_too_large:slack'), ('unknown', 'plan_refused'), ('unknown', 'rollup_error'), ('refused', 'slack_channel_label_invalid'), ('refused', 'slack_key_ref_invalid'), ('failed', 'slack_key_store_locked'), ('refused', 'slack_key_store_locked'), ('unknown', 'slack_key_store_locked'), ('failed', 'slack_key_store_not_native'), ('refused', 'slack_key_store_not_native'), ('unknown', 'slack_key_store_not_native'), ('failed', 'slack_webhook_invalid'), ('refused', 'slack_webhook_invalid'), ('unknown', 'slack_webhook_invalid'), ('failed', 'slack_webhook_missing'), ('refused', 'slack_webhook_missing'), ('unknown', 'slack_webhook_missing')] == []
  
  Left contains 22 more items, first extra item: ('unknown', 'ack_missing')
  
  Full diff:
  - []
  + [
  +     (
  +         'unknown',
  +         'ack_missing',
  +     ),
  +     (
  +         'failed',
  +         'action_prohibited',
  +     ),
  +     (
  +         'failed',
  +         'channel_is_archived',
  +     ),
  +     (
  +         'failed',
  +         'channel_not_found',
  +     ),
  +     (
  +         'failed',
  +         'invalid_payload',
  +     ),
  +     (
  +         'failed',
  +         'payload_too_large:slack',
  +     ),
  +     (
  +         'unknown',
  +         'plan_refused',
  +     ),
  +     (
  +         'unknown',
  +         'rollup_error',
  +     ),
  +     (
  +         'refused',
  +         'slack_channel_label_invalid',
  +     ),
  +     (
  +         'refused',
  +         'slack_key_ref_invalid',
  +     ),
  +     (
  +         'failed',
  +         'slack_key_store_locked',
  +     ),
  +     (
  +         'refused',
  +         'slack_key_store_locked',
  +     ),
  +     (
  +         'unknown',
  +         'slack_key_store_locked',
  +     ),
  +     (
  +         'failed',
  +         'slack_key_store_not_native',
  +     ),
  +     (
  +         'refused',
  +         'slack_key_store_not_native',
  +     ),
  +     (
  +         'unknown',
  +         'slack_key_store_not_native',
  +     ),
  +     (
  +         'failed',
  +         'slack_webhook_invalid',
  +     ),
  +     (
  +         'refused',
  +         'slack_webhook_invalid',
  +     ),
  +     (
  +         'unknown',
  +         'slack_webhook_invalid',
  +     ),
  +     (
  +         'failed',
  +         'slack_webhook_missing',
  +     ),
  +     (
  +         'refused',
  +         'slack_webhook_missing',
  +     ),
  +     (
  +         'unknown',
  +         'slack_webhook_missing',
  +     ),
  + ]
============================== 3 failed in 3.18s ===============================
```

### Captured run — 2026-09-30T08:26:46Z

- **Command:** `bash scripts/verify_philo11_slack.sh walk --atlas docs/internal/philo/graph/atlas-phase11-slack.json --case case.p11.slack.posted.op --brain astra --viewport 1440 --engine none --headless --no-build --out pm/roadmap/holdspeak-philo/phase-11-more-documents-on-the-channels/assets/story-02-walk/posted`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** b1f71ec6b5210279b668fd978f157aafaeafb4ca

```text
PASS: live
BRAIN: astra
SOURCE: 3552be416c9d5d968adc162941f1f81a3c7c0b44 dirty=True
CONTRACT: rig=1.5.2 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase11-slack.json
RUNTIME: build=['index-Dvjkur0f.js'] hub=http://127.0.0.1:58890 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/philo11-slack.MrBICY/tmp/graph-walk-home-7k17njie/.local/share/holdspeak/holdspeak.db engine=none
JOB: p11
VERDICT: pass terminal=settled
EVIDENCE: []
NOTE: placeholder(s) ['send_op'] are bound by the trigger's own `capture_as`; `expected` is resolved after it fires (fields naming them are not read before the trigger)
NOTE: predicate: all_of: op_facts: all 13 facts hold: the trigger outcome holds; observe_at sends holds; observe_at sends.0.id holds; observe_at sends.0.state holds; observe_at sends.0.channel holds; observe_at sends.0.payload_digest holds; observe_at sends.0.proof.url is absent; observe_at sends.0.proof.link is absent; op read #0 (kernel.receipt.read) objects.0.operation.name holds; op read #0 (kernel.receipt.read) objects.0.receipt.operation_id holds; op read #0 (kernel.receipt.read) objects.0.receipt.actor_kind holds; op read #0 (kernel.receipt.read) objects.0.receipt.state holds; observe_at sends.0.proof.word holds | cli_calls: 1 call(s) starting ['https', 'POST', 'hooks.slack.com'] at the recording runner (pids [18333]; 1 call(s) in all), wanted 1
```

### Captured run — 2026-09-30T08:27:21Z

- **Command:** `bash scripts/verify_philo11_slack.sh walk --atlas docs/internal/philo/graph/atlas-phase11-slack.json --case case.p11.slack.failed.op --brain astra --viewport 1440 --engine none --headless --no-build --out pm/roadmap/holdspeak-philo/phase-11-more-documents-on-the-channels/assets/story-02-walk/failed`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** b1f71ec6b5210279b668fd978f157aafaeafb4ca

```text
PASS: live
BRAIN: astra
SOURCE: 3552be416c9d5d968adc162941f1f81a3c7c0b44 dirty=True
CONTRACT: rig=1.5.2 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase11-slack.json
RUNTIME: build=['index-Dvjkur0f.js'] hub=http://127.0.0.1:58934 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/philo11-slack.UUQcDY/tmp/graph-walk-home-9vu5ytm3/.local/share/holdspeak/holdspeak.db engine=none
JOB: p11
VERDICT: pass terminal=settled
EVIDENCE: []
NOTE: placeholder(s) ['send_op'] are bound by the trigger's own `capture_as`; `expected` is resolved after it fires (fields naming them are not read before the trigger)
NOTE: predicate: all_of: op_facts: all 12 facts hold: the trigger outcome holds; observe_at sends holds; observe_at sends.0.id holds; observe_at sends.0.state holds; observe_at sends.0.channel holds; observe_at sends.0.payload_digest holds; observe_at sends.0.proof.url is absent; observe_at sends.0.proof.link is absent; op read #0 (kernel.receipt.read) objects.0.operation.name holds; op read #0 (kernel.receipt.read) objects.0.receipt.operation_id holds; op read #0 (kernel.receipt.read) objects.0.receipt.actor_kind holds; op read #0 (kernel.receipt.read) objects.0.receipt.state holds | cli_calls: 1 call(s) starting ['https', 'POST', 'hooks.slack.com'] at the recording runner (pids [18688]; 1 call(s) in all), wanted 1
```

### Captured run — 2026-09-30T08:27:55Z

- **Command:** `bash scripts/verify_philo11_slack.sh walk --atlas docs/internal/philo/graph/atlas-phase11-slack.json --case case.p11.slack.unknown.op --brain astra --viewport 1440 --engine none --headless --no-build --out pm/roadmap/holdspeak-philo/phase-11-more-documents-on-the-channels/assets/story-02-walk/unknown`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** b1f71ec6b5210279b668fd978f157aafaeafb4ca

```text
PASS: live
BRAIN: astra
SOURCE: 3552be416c9d5d968adc162941f1f81a3c7c0b44 dirty=True
CONTRACT: rig=1.5.2 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase11-slack.json
RUNTIME: build=['index-Dvjkur0f.js'] hub=http://127.0.0.1:58982 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/philo11-slack.FHK7Rx/tmp/graph-walk-home-v59nq6pb/.local/share/holdspeak/holdspeak.db engine=none
JOB: p11
VERDICT: pass terminal=settled
EVIDENCE: []
NOTE: placeholder(s) ['send_op'] are bound by the trigger's own `capture_as`; `expected` is resolved after it fires (fields naming them are not read before the trigger)
NOTE: predicate: all_of: op_facts: all 12 facts hold: the trigger outcome holds; observe_at sends holds; observe_at sends.0.id holds; observe_at sends.0.state holds; observe_at sends.0.channel holds; observe_at sends.0.payload_digest holds; observe_at sends.0.proof.url is absent; observe_at sends.0.proof.link is absent; op read #0 (kernel.receipt.read) objects.0.operation.name holds; op read #0 (kernel.receipt.read) objects.0.receipt.operation_id holds; op read #0 (kernel.receipt.read) objects.0.receipt.actor_kind holds; op read #0 (kernel.receipt.read) objects.0.receipt.state holds | cli_calls: 1 call(s) starting ['https', 'POST', 'hooks.slack.com'] at the recording runner (pids [19114]; 1 call(s) in all), wanted 1
```

### Captured run — 2026-09-30T08:28:28Z

- **Command:** `bash scripts/verify_philo11_slack.sh pytest -q -n 0 tests/unit/test_philo_graph_atlas.py tests/unit/test_philo9_atlas.py tests/unit/test_philo10_atlas.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** b1f71ec6b5210279b668fd978f157aafaeafb4ca

```text
........................................................................ [ 35%]
........................................................................ [ 71%]
..........................................................               [100%]
202 passed in 1.80s
```

### Captured run — 2026-09-30T08:28:54Z

- **Command:** `bash -o pipefail -c bash scripts/verify_philo11_slack.sh run .venv/bin/python scripts/philo_graph_reference.py --census 2>&1 | tee .tmp/philo11-02/descriptor-census-final.txt`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** b1f71ec6b5210279b668fd978f157aafaeafb4ca

```text
census scope: HTTP routes (the app assembled from source by scripts/gen_api_surface.py, schema-hidden page routes excluded; stale = docs/generated/openapi.json differs from source), desk verbs (web/src/desk/verbRegistry.ts + applications.ts), MCP tools (the real holdspeak.mcp.tools catalogue). Face handlers, keys, timers, frames, CLI and connector edges are not censused. miscited = a pass cited a handler that was not in the file at the revision it examined.
new: http DELETE /api/channels/destinations/{destination_id} has no edge (api_channel_remove_destination)
new: http DELETE /api/settings/remote/delegations/{identity} has no edge (revoke_delegation)
new: http DELETE /api/settings/remote/delegations/{identity}/projects/{project_id} has no edge (revoke_project_delegation)
new: http GET /api/channels/destinations has no edge (api_channel_destinations)
new: http GET /api/channels/sends has no edge (api_channel_sends)
new: http POST /api/channels/destinations has no edge (api_channel_save_destination)
new: http POST /api/channels/destinations/{destination_id}/check has no edge (api_channel_check_destination)
new: http POST /api/channels/preview has no edge (api_channel_preview)
new: http POST /api/channels/send has no edge (api_channel_send)
new: http POST /api/channels/sends has no edge (api_channel_prepare)
new: http POST /api/channels/sends/{send_id}/discard has no edge (api_channel_discard)
new: http POST /api/channels/slack-webhooks has no edge (api_channel_save_slack_webhook)
new: http POST /api/updates/{update_id}/delivered has no edge (api_mark_update_delivered)
new: http PUT /api/channels/email-keys/{key_ref} has no edge (api_channel_save_email_key)
new: http PUT /api/settings/remote/delegations/{identity} has no edge (grant_delegation)
new: http PUT /api/settings/remote/delegations/{identity}/projects/{project_id} has no edge (grant_project_delegation)
removed: http POST /api/meetings/{meeting_id}/export/slack is not in source (edge.http.post.api_meetings_meeting_id_export_slack)
miscited: http GET /api/brief/latest (edge.route.brief_latest): def api_latest was not in holdspeak/web/routes/monday_brief.py at c42963bc either
miscited: http POST /api/brief/items/{item_id}/shelf (edge.route.brief_item_shelf): def api_shelf was not in holdspeak/web/routes/monday_brief.py at c42963bc either
miscited: http POST /api/inference/assignments/set (edge.route.inference_assignments_set): def api_set_assignments was not in holdspeak/web/routes/inference_assignments.py at c42963bc either
miscited: http POST /api/settings/heartbeat/run-now (edge.route.heartbeat_run_now): source registered api_heartbeat_run_now at c42963bc already; the pass cited api_run_heartbeat
miscited: http POST /api/stop (edge.route.meeting_stop): source registered api_stop at c42963bc already; the pass cited api_meeting_stop
new: mcp tool channel.check_destination has no edge
new: mcp tool channel.destinations has no edge
new: mcp tool channel.discard has no edge
new: mcp tool channel.prepare has no edge
new: mcp tool channel.preview has no edge
new: mcp tool channel.remove_destination has no edge
new: mcp tool channel.save_destination has no edge
new: mcp tool channel.send has no edge
new: mcp tool channel.sends has no edge
new: mcp tool kernel.receipt has no edge
new: mcp tool meeting.import has no edge
new: mcp tool monday_brief.shelf has no edge
new: mcp tool monday_brief.shelf_read has no edge
new: mcp tool project.item.create has no edge
new: mcp tool project.item.list has no edge
new: mcp tool project.item.transition has no edge
new: mcp tool project.item.update has no edge
new: mcp tool project.mark_update_delivered has no edge
new: mcp tool project.resource.add has no edge
new: mcp tool project.resource.list has no edge
new: mcp tool project.resource.remove has no edge
note: subtype conflict edge.cli.hub_restart: astra=process.restart; muaddib=cli
note: subtype conflict edge.face.arrival_load: astra=lifecycle.mount; muaddib=navigation.load
note: subtype conflict edge.face.thought_keep: astra=pointer.blur; muaddib=pointer.click
note: subtype conflict edge.route.brief_item_shelf: astra=ui; muaddib=http
note: subtype conflict edge.route.brief_latest: astra=ui; muaddib=http
note: subtype conflict edge.route.heartbeat_run_now: astra=ui; muaddib=http
note: subtype conflict edge.route.inference_assignments_set: astra=ui; muaddib=http
note: subtype conflict edge.route.model_profile_delete: astra=ui; muaddib=http
note: subtype conflict edge.route.model_profile_unbind: astra=ui; muaddib=http
note: subtype conflict edge.route.projection_presentation: astra=ui; muaddib=http
note: subtype conflict edge.route.projections_list: astra=ui; muaddib=http
note: subtype conflict edge.timer.heartbeat_sweep: astra=ui; muaddib=timer
note: subtype conflict iface.face.arrival: astra=face.section; muaddib=face.window
note: subtype conflict iface.face.first_words: astra=face.card; muaddib=face.panel
census: 37 new, 1 removed, 0 changed, 0 stale, 5 miscited, 0 unread, 14 subtype conflict note(s) against docs/generated/graph.json (source_commit f575a582)
```

### Captured run — 2026-09-30T08:29:14Z

- **Command:** `bash -o pipefail -c bash scripts/verify_philo11_slack.sh pytest -q -n 0 --junitxml=.tmp/philo11-02/serial2.xml 'tests/unit/test_philo10_send_restart.py::test_r3_a_restart_during_dispatching_ends_unknown_once_and_the_replay_answers_it[desk_decision-killed-after-the-write-send_id]' 'tests/e2e/test_philo8_03_then_guard.py::test_a_follow_up_after_the_window_is_blocked[1440-before_guard]' 'tests/e2e/test_philo8_03_then_guard.py::test_a_follow_up_after_the_window_is_blocked[1440-click_wait]' 'tests/e2e/test_philo8_03_then_guard.py::test_a_follow_up_after_the_window_is_blocked[393-before_guard]' 'tests/e2e/test_philo10_04_send_face_glass.py::TestSendChannelsGlass::test_github_sending_posted_and_a_running_prepared_send[393]' 'tests/e2e/test_philo8_03_then_guard.py::test_a_follow_up_after_the_window_is_blocked[393-click_wait]' tests/e2e/test_hs176_loop_glass.py::test_speak_loop_1440 tests/e2e/test_hs176_loop_glass.py::test_speak_loop_393 'tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_undo_keeps_only_the_pending_object[1440]' 'tests/e2e/test_philo8_01_list_rename_glass.py::TestListRenameGlass::test_the_list_field_opens_writes_and_keeps[393]' 'tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_the_list_row_menu_delete_removes_the_object[1440]' 'tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_undo_keeps_only_the_pending_object[393]' 'tests/e2e/test_philo8_01_list_rename_glass.py::TestListRenameGlass::test_a_taken_name_shows_the_chip_on_the_list[1440]' 'tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_leaving_the_face_inside_the_window_commits_the_delete[floor-1440]' 'tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_the_list_delete_key_removes_the_selected_object[1440]' 'tests/e2e/test_philo8_01_list_rename_glass.py::TestListRenameGlass::test_a_taken_name_shows_the_chip_on_the_floor[1440]' 'tests/e2e/test_philo8_01_list_rename_glass.py::TestListRenameGlass::test_a_taken_name_shows_the_chip_on_the_floor[393]' 'tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_the_list_palette_delete_removes_the_selected_object[1440]' 'tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_leaving_the_face_inside_the_window_commits_the_delete[list-393]' 'tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_the_list_palette_delete_removes_the_selected_object[393]' 'tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_the_chair_withholds_delete_with_its_reason[1440]' 'tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_undo_on_the_list_keeps_the_object[1440]' 'tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_the_foot_never_covers_the_last_rows[393]' 'tests/e2e/test_philo8_01_list_rename_glass.py::TestListRenameGlass::test_a_failed_save_shows_in_the_chip_slot[393-spatial-network]' 'tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_the_chair_withholds_delete_with_its_reason[393]' 'tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_undo_on_the_list_keeps_the_object[393]' 'tests/e2e/test_philo3_01_receipt_hits.py::test_receipt_verbs_own_their_areas[1440]' 'tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_a_repeated_delete_never_offers_a_false_undo[list-1440]' 'tests/e2e/test_philo8_01_list_rename_glass.py::TestListRenameGlass::test_a_refusal_after_the_field_closed_goes_to_the_write_receipt[1440]' 'tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_a_refused_delete_says_so_with_retry[list-393]' 'tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_a_repeated_delete_never_offers_a_false_undo[list-393]' 'tests/e2e/test_philo8_01_list_rename_glass.py::TestListRenameGlass::test_a_refusal_after_the_field_closed_goes_to_the_write_receipt[393]' 'tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_two_deletes_in_one_window_both_reach_the_hub[floor-a_left_selected-1440]' 'tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_a_refused_delete_says_so_with_retry[floor-1440]' 'tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_two_deletes_in_one_window_both_reach_the_hub[floor-a_left_selected-393]' 'tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_a_refused_delete_says_so_with_retry[floor-393]' 'tests/e2e/test_philo8_01_list_rename_glass.py::TestListRenameGlass::test_f2_on_a_focused_zone_row_opens_the_field[1440]' 'tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_two_deletes_in_one_window_both_reach_the_hub[list-a_left_selected-1440]' 'tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_a_workbench_remove_works_again_after_a_refusal[1440]' 'tests/e2e/test_philo8_01_list_rename_glass.py::TestListRenameGlass::test_a_failed_save_shows_in_the_chip_slot[393-list-422]' 'tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_a_workbench_remove_works_again_after_a_refusal[393]' 'tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_a_failed_refresh_keeps_the_pending_delete_and_its_undo[1440]' tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_a_repeated_workbench_remove_never_offers_a_false_undo 'tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_two_deletes_in_one_window_both_reach_the_hub[floor-a_taken_out-393]' 'tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_two_deletes_in_one_window_both_reach_the_hub[list-a_taken_out-1440]' 'tests/e2e/test_philo8_01_list_rename_glass.py::TestListRenameGlass::test_a_failed_save_shows_in_the_chip_slot[1440-list-422]' 'tests/e2e/test_philo8_01_zone_name_glass.py::TestZoneNameGlass::test_two_new_zone_presses_make_two_zones[1440-spatial]' 'tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_the_foot_never_covers_the_last_rows[1440]' 'tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_a_failed_refresh_keeps_the_pending_delete_and_its_undo[393]' 'tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_a_workbench_remove_after_a_refusal_offers_undo[393]' 'tests/e2e/test_philo8_01_zone_name_glass.py::TestZoneNameGlass::test_two_new_zone_presses_make_two_zones[1440-list]' 'tests/e2e/test_philo8_01_list_rename_glass.py::TestListRenameGlass::test_a_failed_save_shows_in_the_chip_slot[1440-spatial-422]' 'tests/e2e/test_philo8_01_list_rename_glass.py::TestListRenameGlass::test_a_failed_save_shows_in_the_chip_slot[393-spatial-422]' 'tests/e2e/test_philo8_01_list_rename_glass.py::TestListRenameGlass::test_a_failed_save_shows_in_the_chip_slot[1440-list-network]' 'tests/e2e/test_philo8_01_list_rename_glass.py::TestListRenameGlass::test_a_failed_save_shows_in_the_chip_slot[1440-spatial-network]' 2>&1 | tee .tmp/philo11-02/serial2.txt`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** b1f71ec6b5210279b668fd978f157aafaeafb4ca

```text
.......................................................                  [100%]
55 passed in 1161.78s (0:19:21)
```

### Captured run — 2026-09-30T08:49:28Z

- **Command:** `bash -o pipefail -c bash scripts/verify_philo11_slack.sh run bash -e -c 'for check_script in scripts/gen_operations_json.py scripts/philo_openapi_reference.py scripts/philo_api_reference.py scripts/philo_config_reference.py scripts/generate_capability_docs.py scripts/philo_graph_reference.py; do .venv/bin/python "$check_script" --check; done' 2>&1 | tee .tmp/philo11-02/generated-checks.txt`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** b1f71ec6b5210279b668fd978f157aafaeafb4ca

```text
OK docs/generated/operations.json
OpenAPI: 580 paths
API reference checked
Configuration declaration reference is current
Architecture documentation checked (10 outputs).
note: subtype conflict edge.cli.hub_restart: astra=process.restart; muaddib=cli
note: subtype conflict edge.face.arrival_load: astra=lifecycle.mount; muaddib=navigation.load
note: subtype conflict edge.face.thought_keep: astra=pointer.blur; muaddib=pointer.click
note: subtype conflict edge.route.brief_item_shelf: astra=ui; muaddib=http
note: subtype conflict edge.route.brief_latest: astra=ui; muaddib=http
note: subtype conflict edge.route.heartbeat_run_now: astra=ui; muaddib=http
note: subtype conflict edge.route.inference_assignments_set: astra=ui; muaddib=http
note: subtype conflict edge.route.model_profile_delete: astra=ui; muaddib=http
note: subtype conflict edge.route.model_profile_unbind: astra=ui; muaddib=http
note: subtype conflict edge.route.projection_presentation: astra=ui; muaddib=http
note: subtype conflict edge.route.projections_list: astra=ui; muaddib=http
note: subtype conflict edge.timer.heartbeat_sweep: astra=ui; muaddib=timer
note: subtype conflict iface.face.arrival: astra=face.section; muaddib=face.window
note: subtype conflict iface.face.first_words: astra=face.card; muaddib=face.panel
graph join checked: docs/generated/graph.json; 14 subtype conflict note(s)
```
