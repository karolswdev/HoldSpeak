# Evidence - HS-201-05

- **Story:** HS-201-05 - One engine and one assignment from the face
- **Status:** done
- **Date:** 2026-09-19

## Proof

### Captured run — 2026-09-19T22:54:53Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.ngxwJHSTKp uv run --extra dev pytest -q tests/unit/test_hs201_summary_assignment.py tests/e2e/test_hs201_summary_assignment.py tests/unit/test_hs170_concierge_wire.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 387bab5dfde6ff0f3f6539c18cb3ecf906bba24e

```text
...............................................                          [100%]
47 passed in 2.56s
```

## Lane A acceptance boundary

One explicit selection writes the exact `meeting.deferred_analysis` assignment
through the assignment service, with the selected real profile revision. The
real binder test freezes that selected revision. A real model-library connection
test leaves every assignment row unchanged; the summary selection preserves the
speech assignment. Conflict and failure responses name the outcome, and the
response exposes the selected engine through `summaryAssignment`.

Models controls and the two face widths are lane B story 06 work. No claim is
made here that its UI displays these fields. See `lane-a-handoff.md`.

## Baseline red fences independently repeated by Astra

Pre-fix source: charter `fdc3fc45`. The command used an isolated HOME,
`PYTHONPATH=.tmp/hs201-baseline`, and the dev venv via
`UV_PROJECT_ENVIRONMENT`; `uv run --no-sync python` imported the module shown
below and called pytest on the two named tests. The first asserts exact
capability scope and real revision; the second rejects a text-only profile
whose label contains Whisper. These are behavioral failures, not missing imports.

```text
BASELINE SOURCE: /Users/karol/dev/tools/wt-201-a/.tmp/hs201-baseline/holdspeak/services/concierge_service.py
FF                                                                       [100%]
=================================== FAILURES ===================================
_ test_apply_meetings_uses_exact_summary_capability_and_selected_profile_revision _

    def test_apply_meetings_uses_exact_summary_capability_and_selected_profile_revision():
        """The existing Use these gesture must bind the SERVICE-visible capability."""
        from holdspeak.services.concierge_service import apply, STATE_READY
    
        mock_svc = MagicMock()
        mock_svc.get_assignment.return_value = {"revision": 0, "entries": []}
        mock_svc.set_assignment.return_value = {
            "revision": 1,
            "entries": [
                {
                    "profile_id": "summary-profile",
                    "profile_revision": 2,
                    "label": "Summary model",
                    "boundary": "local",
                    "readiness": "ready",
                }
            ],
        }
        result = apply(
            rows=[{"group": "meetings", "engineId": "lan:summary", "state": STATE_READY}],
            engines=[
                {
                    "id": "lan:summary",
                    "kind": "lan",
                    "profileId": "summary-profile",
                    "profileRevision": 2,
                }
            ],
            assignment_service=mock_svc,
            principal=MagicMock(),
            db=FakeDB(),
        )
    
>       assert result["results"] == [
            {
                "group": "meetings",
                "capabilityId": "meeting.deferred_analysis",
                "state": "READY",
                "profileId": "summary-profile",
                "profileRevision": 2,
            }
        ]
E       AssertionError: assert [{'group': 'm...te': 'READY'}] == [{'capability...ion': 2, ...}]
E         
E         At index 0 diff: {'group': 'meetings', 'state': 'READY'} != {'group': 'meetings', 'capabilityId': 'meeting.deferred_analysis', 'state': 'READY', 'profileId': 'summary-profile', 'profileRevision': 2}
E         Use -v to get more diff

tests/unit/test_hs170_concierge_wire.py:467: AssertionError
______ test_propose_does_not_offer_a_text_only_whisper_profile_to_speech _______

    def test_propose_does_not_offer_a_text_only_whisper_profile_to_speech():
        """Speech requires an audio-capable profile, even when its label says Whisper."""
        from holdspeak.services.concierge_service import propose
    
        rows = propose(engines=[{
            "id": "local:whisper-text-only",
            "kind": "local",
            "name": "whisper-text-only",
            "host": "THIS DEVICE",
            "state": "READY",
            "profileId": "text-only",
            "profileRevision": 1,
            "audioCapable": False,
        }])["rows"]
        speech = next(row for row in rows if row["group"] == "speech_recognition")
>       assert speech["state"] == "WAITING"
E       AssertionError: assert 'READY' == 'WAITING'
E         
E         - WAITING
E         + READY

tests/unit/test_hs170_concierge_wire.py:296: AssertionError
=========================== short test summary info ============================
FAILED tests/unit/test_hs170_concierge_wire.py::test_apply_meetings_uses_exact_summary_capability_and_selected_profile_revision
FAILED tests/unit/test_hs170_concierge_wire.py::test_propose_does_not_offer_a_text_only_whisper_profile_to_speech
2 failed in 0.25s
```

### Captured run — 2026-09-19T23:59:20Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.UOx7KEcQWO uv run --extra dev pytest -q tests/unit/test_hs201_summary_assignment.py tests/unit/test_hs201_summary_producer.py tests/e2e/test_hs201_summary_assignment.py tests/e2e/test_hs201_summary_producer_chain.py tests/unit/test_hs170_concierge_wire.py tests/unit/test_model_library_providers.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 18f67176b9146ddd441b13c60b70687674c1230f

```text
...........................................................              [100%]
59 passed in 5.37s
```

## Real producer gap — red before the adapter claim

The real Model Library producer originally emitted only `language`. The
HTTP summary gesture returned `partial`, leaving the route unavailable. The
new immutable manifest names adapter support, not observed model quality.
The producer's existing runtime/readiness mapping excludes Anthropic, paired
devices, and future backends; these exclusions were already correct before
the new claim and are retained as passing fences, not described as old bugs.

```text
F                                                                        [100%]
=================================== FAILURES ===================================
_ test_model_library_producer_revision_survives_summary_route_and_queue_freeze _

monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x10e3883e0>
tmp_path = PosixPath('/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-8833/test_model_library_producer_re0')

    def test_model_library_producer_revision_survives_summary_route_and_queue_freeze(
        monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
    ) -> None:
        """Connect, detect, select over HTTP, project, and bind one exact revision."""
        monkeypatch.setattr(
            "holdspeak.setup_runtime.discover_endpoint_models",
            lambda *_args, **_kwargs: {"ok": True, "models": ["fixture"]},
        )
        library = _library(tmp_path, store_path=tmp_path / "isolated-keys.json")
        db = library._db
        first = library.define_endpoint(
            OWNER,
            _draft(
                request_id="producer-chain-r1",
                profile_id="producer-chain",
                provider_family="openai_compatible",
                requires_key=False,
            ),
            None,
        )
        detected_r1 = next(item for item in detect(db=db, home=tmp_path / "home")["engines"] if item.get("profileId") == "producer-chain")
        assert detected_r1["profileRevision"] == first["provider"]["profile_revision"]
    
        # This is the baseline old revision: the producer cannot route it because
        # its v1 manifest has no structured result-schema claim.
        old = assign_summary(
            assignment_service=InferenceAssignmentService(db),
            principal=OWNER,
            db=db,
            profile_id=first["provider"]["profile_id"],
            profile_revision=first["provider"]["profile_revision"],
            expected_assignment_revision=0,
            command_id="producer-chain-old-summary",
        )
        assert old["status"] == "partial"
        assert old["result"]["code"] == "inference_assignment_incompatible"
    
        second = library.define_endpoint(
            OWNER,
            {
                **_draft(
                    request_id="producer-chain-r2",
                    profile_id="producer-chain",
                    provider_family="openai_compatible",
                    label="Fixture v2",
                    requires_key=False,
                ),
                "expected_profile_revision": 1,
            },
            None,
        )
        assert second["provider"]["profile_revision"] == 2
        detected = detect(db=db, home=tmp_path / "home")
        engine = next(item for item in detected["engines"] if item.get("profileId") == "producer-chain")
        assert engine["profileId"] == second["provider"]["profile_id"]
        assert engine["profileRevision"] == second["provider"]["profile_revision"]
    
        client = _client(db, tmp_path / "home")
        response = client.post(
            "/api/concierge/summary-selection",
            json={
                "commandId": "producer-chain-summary",
                "expectedAssignmentRevision": 0,
                "profileId": engine["profileId"],
                "profileRevision": engine["profileRevision"],
            },
        )
        assert response.status_code == 200, response.text
>       assert response.json()["status"] == "succeeded"
E       AssertionError: assert 'partial' == 'succeeded'
E         
E         - succeeded
E         + partial

tests/e2e/test_hs201_summary_producer_chain.py:119: AssertionError
=========================== short test summary info ============================
FAILED tests/e2e/test_hs201_summary_producer_chain.py::test_model_library_producer_revision_survives_summary_route_and_queue_freeze
1 failed in 1.49s

```

## Producer verification

The 59-test staged capture above was run by Astra. The real producer makes
revision 1 and reconnects to revision 2; detect passes that exact reference to
the real HTTP gesture, SERVICE projection and binder. No test qualification
is added on this path. A separate old-v1 reconnect test preserves revision 1
bytes and refuses its assignment before reconnect makes revision 2 compatible.
Connection leaves assignment tables unchanged; summary selection adds no
live-analysis assignment. Deferred and live analysis share a schema hash.

The malformed-output test uses the real producer profile and queue, controlling
only provider output. It asserts a failed durable job, `invalid_typed_output`,
`provider_returned`, a failed receipt naming `127.0.0.1`, and no saved summary.
This is the runtime check behind the adapter support declaration.

Collection inspected by Astra:

```text
tests/unit/test_hs201_summary_producer.py::test_detect_carries_the_model_library_revision_from_the_producer
tests/unit/test_hs201_summary_producer.py::test_detect_does_not_invent_revision_for_a_legacy_endpoint
tests/unit/test_hs201_summary_producer.py::test_old_v1_manifest_stays_incompatible_while_producer_mints_v2
tests/unit/test_hs201_summary_producer.py::test_manifest_result_schema_claim_excludes_unexecuted_provider_families
tests/unit/test_hs201_summary_producer.py::test_summary_apply_refuses_a_profile_without_an_immutable_revision
tests/e2e/test_hs201_summary_producer_chain.py::test_model_library_producer_revision_survives_summary_route_and_queue_freeze
tests/e2e/test_hs201_summary_producer_chain.py::test_real_producer_bad_output_is_failed_with_contact_receipt_and_no_summary
tests/unit/test_hs201_summary_assignment.py::test_summary_gesture_writes_exact_capability_with_real_profile_revision_and_preserves_speech
tests/unit/test_hs201_summary_assignment.py::test_summary_gesture_rejects_stale_profile_revision_after_profile_head_moves
tests/unit/test_hs201_summary_assignment.py::test_summary_projection_names_the_engine_that_service_will_run
tests/unit/test_hs201_summary_assignment.py::test_summary_gesture_reports_revision_conflict_without_silent_success
tests/unit/test_hs201_summary_assignment.py::test_summary_gesture_reports_partial_failure_for_incompatible_text_profile
tests/unit/test_hs201_summary_assignment.py::test_speech_assignment_cannot_use_text_only_profile
tests/unit/test_hs201_summary_assignment.py::test_summary_proposal_never_offers_text_only_engine_to_speech
tests/unit/test_hs201_summary_assignment.py::test_summary_selection_then_real_queue_binder_freezes_selected_revision
tests/unit/test_hs201_summary_assignment.py::test_model_library_connection_keeps_assignment_rows_byte_equivalent
tests/e2e/test_hs201_summary_assignment.py::test_summary_selection_is_owner_only_and_returns_one_visible_receipt
tests/e2e/test_hs201_summary_assignment.py::test_summary_selection_conflict_is_truthful_over_http
tests/unit/test_hs170_concierge_wire.py::test_detect_lists_lan_endpoint_local_file_cloud_key_preset
tests/unit/test_hs170_concierge_wire.py::test_propose_whisper_on_speech_recognition_only_and_waiting
tests/unit/test_hs170_concierge_wire.py::test_propose_chat_label_is_chat
tests/unit/test_hs170_concierge_wire.py::test_propose_does_not_offer_a_text_only_whisper_profile_to_speech
tests/unit/test_hs170_concierge_wire.py::test_probe_cloud_without_generate_no_network
tests/unit/test_hs170_concierge_wire.py::test_probe_cloud_not_set
tests/unit/test_hs170_concierge_wire.py::test_apply_refuses_with_waiting
tests/unit/test_hs170_concierge_wire.py::test_apply_succeeds_with_off
tests/unit/test_hs170_concierge_wire.py::test_apply_writes_receipt
tests/unit/test_hs170_concierge_wire.py::test_apply_meetings_uses_exact_summary_capability_and_selected_profile_revision
tests/unit/test_hs170_concierge_wire.py::test_download_returns_job_shape
tests/unit/test_hs170_concierge_wire.py::TestEngineDisplayName::test_gguf_qwen36_35b
tests/unit/test_hs170_concierge_wire.py::TestEngineDisplayName::test_gguf_qwythos_9b
tests/unit/test_hs170_concierge_wire.py::TestEngineDisplayName::test_gguf_gemma_4_e4b
tests/unit/test_hs170_concierge_wire.py::TestEngineDisplayName::test_mlx_qwen3_8b
tests/unit/test_hs170_concierge_wire.py::TestEngineDisplayName::test_openrouter_qwen_slash
tests/unit/test_hs170_concierge_wire.py::TestEngineDisplayName::test_gpt5_mini
tests/unit/test_hs170_concierge_wire.py::TestEngineDisplayName::test_migrated_label_with_served_model
tests/unit/test_hs170_concierge_wire.py::TestEngineDisplayName::test_whisper_base_unchanged
tests/unit/test_hs170_concierge_wire.py::TestEngineDisplayName::test_openrouter_label_preserved
tests/unit/test_hs170_concierge_wire.py::TestMmprojFiltering::test_mmproj_detected
tests/unit/test_hs170_concierge_wire.py::TestMmprojFiltering::test_mmproj_base_name_extraction
tests/unit/test_hs170_concierge_wire.py::TestResolveProfileId::test_double_prefix_resolves
tests/unit/test_hs170_concierge_wire.py::TestResolveProfileId::test_exact_match_returns_as_is
tests/unit/test_hs170_concierge_wire.py::TestResolveProfileId::test_no_match_returns_original
tests/unit/test_hs170_concierge_wire.py::TestResolveProfileId::test_apply_writes_real_profile_id
tests/unit/test_hs170_concierge_wire.py::TestIsLanHost::test_private_ip_is_lan
tests/unit/test_hs170_concierge_wire.py::TestIsLanHost::test_loopback_is_lan
tests/unit/test_hs170_concierge_wire.py::TestIsLanHost::test_cloud_host_is_not_lan
tests/unit/test_hs170_concierge_wire.py::TestIsLanHost::test_tailnet_is_lan
tests/unit/test_hs170_concierge_wire.py::TestIsLanHost::test_cgnat_tailscale_is_lan
tests/unit/test_hs170_concierge_wire.py::TestIsLanHost::test_ten_network_is_lan
tests/unit/test_hs170_concierge_wire.py::TestDetectNameResolution::test_lan_endpoint_resolves_name_from_models
tests/unit/test_hs170_concierge_wire.py::TestDetectNameResolution::test_lan_endpoint_timeout_falls_back_to_host_port
tests/unit/test_hs170_concierge_wire.py::TestDetectNameResolution::test_cloud_endpoint_stays_cloud
tests/unit/test_hs170_concierge_wire.py::TestDetectNameResolution::test_192_168_classified_as_lan_not_cloud
tests/unit/test_model_library_providers.py::test_hosted_custom_private_and_anthropic_rows_use_server_truth
tests/unit/test_model_library_providers.py::test_paired_device_row_uses_existing_liveness_truth
tests/unit/test_model_library_providers.py::test_provider_cas_changed_payload_replay_and_restart
tests/unit/test_model_library_providers.py::test_delayed_key_store_confirmation_leaves_command_retriable
tests/unit/test_model_library_providers.py::test_each_broken_provider_row_has_exactly_one_server_repair

59 tests collected in 0.67s

```


## Capture provenance clarification

The runs executed the combined lane worktree, not an isolated index snapshot.
The early captures stamped `387bab5d` are superseded for index provenance;
their raw output and original stamps are retained. No capture stamp was edited.
The quiet full suite used product/test index tree
`18f67176b9146ddd441b13c60b70687674c1230f`. Follow-up test-contract updates
and their focused verification are recorded below; no full-suite green is claimed.


## Producer fence scope

`test_manifest_result_schema_claim_excludes_unexecuted_provider_families` is a
regression fence, green on baseline by design; the discriminating red is the
real producer-chain test recorded above. The manifest claim means adapter
support, not observed quality. The invalid-output chain proves the job fails
with a contacted-host receipt and no partial summary.


## Final contract artifacts

The API manifest now includes the summary-selection route. The private-helper
census classifies the two immutable revision read/projection helpers and its
companion artifact records the same ownership. Astra's final 03 capture
includes these guards (176 passed, four ratified xfails). No product code
changed after the 59-test producer/assignment capture or the full suite.
