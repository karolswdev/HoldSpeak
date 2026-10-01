"""PHILO-11-06 — real document source to file-send atlas contracts."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.unit import test_philo_graph_atlas as general


REPO = Path(__file__).resolve().parents[2]
ATLAS = REPO / "docs/internal/philo/graph/atlas-phase11.json"
SLACK = REPO / "docs/internal/philo/graph/atlas-phase11-slack.json"
KINDS = {
    "monday_brief",
    "desk_decision",
    "decision_record",
    "meeting_decision",
    "meeting_summary",
    "meeting_digest",
    "meeting_followup",
}
FACE_CASE_IDS = {
    *(f"case.p11.monday_brief.{seat}.{state}"
      for seat in ("chair", "intelligence")
      for state in ("picked", "sent", "prepared")),
    *(f"case.p11.desk_decision.window.{state}"
      for state in ("picked", "sent", "prepared")),
    *(f"case.p11.decision_record.{seat}.{state}"
      for seat in ("intelligence", "room")
      for state in ("picked", "sent", "prepared")),
    *(f"case.p11.meeting_summary.{seat}.{state}"
      for seat in ("window", "chair", "meetings_record")
      for state in ("picked", "sent", "prepared")),
    *(f"case.p11.{kind}.meetings_record.{state}"
      for kind in ("meeting_digest", "meeting_followup")
      for state in ("picked", "sent", "prepared")),
    "case.p11.slack.posted.face",
    "case.p11.slack.failed.face",
    "case.p11.slack.unknown.face",
    "case.p11.slack.too_large.face",
    "case.p11.meeting_summary.meetings_record.no_summary",
    "case.p11.r7.no_digest_slack",
    "case.p11.r7.no_credentials_slack",
    *(f"case.p11.slack.destination.{suffix}" for suffix in ("d1", "d2a", "d2b", "d3")),
    "case.p11.transition.slack_limit",
    "case.p11.transition.preview_changed",
    "case.p11.transition.brief_last_ack",
    "case.p11.transition.brief_last_defer",
}


# ``test_philo_graph_atlas`` parametrizes only the checks that are safe to run
# against its default ``atlas`` fixture.  Phase 11 owns two extension files,
# so apply the complete structural fences to each one here as Phase 10 does.
GENERAL = [
    general.test_every_case_state_id_resolves,
    general.test_every_case_reference_inside_the_atlas_resolves,
    general.test_every_clock_a_case_uses_is_declared,
    general.test_every_applicable_case_carries_one_trigger,
    general.test_face_cases_carry_both_ruled_viewports,
    general.test_every_applicable_predicate_is_a_kind_the_rig_implements,
    general.test_every_predicate_observes_a_selector_or_a_route,
    general.test_every_source_reference_lands_on_its_symbol,
    general.test_every_case_keeps_its_human_sentence,
    general.test_every_ui_action_is_one_the_rig_implements,
    general.test_every_boundary_names_its_substitution,
    general.test_no_precondition_check_compares_two_snapshots,
    general.test_every_precondition_check_observes_a_selector_or_a_route,
    general.test_no_check_asserts_the_result_the_trigger_must_produce,
    general.test_no_step_acts_on_a_root_placeholder,
    general.test_navigation_steps_carry_no_selector,
    general.test_every_desk_face_case_crosses_the_gate_first,
    general.test_every_captured_id_names_the_field_it_reads,
    general.test_ids_are_unique,
]


@pytest.mark.parametrize("atlas_path", (ATLAS, SLACK), ids=lambda path: path.name)
@pytest.mark.parametrize("fence", GENERAL, ids=lambda fence: fence.__name__)
def test_phase11_atlases_keep_the_general_graph_fences(atlas_path: Path, fence) -> None:
    fence(json.loads(atlas_path.read_text()))


@pytest.mark.parametrize("atlas_path", (ATLAS, SLACK), ids=lambda path: path.name)
def test_phase11_atlases_validate_against_schema_and_openapi(atlas_path: Path) -> None:
    atlas = json.loads(atlas_path.read_text())
    schema = json.loads(general.SCHEMA_PATH.read_text())
    general.test_atlas_validates_against_its_schema(atlas, schema)
    general.test_every_api_setup_step_exists_in_the_generated_openapi(
        atlas, json.loads(general.OPENAPI_PATH.read_text())
    )


def _doc_cases() -> list[dict]:
    return [
        case for case in json.loads(ATLAS.read_text())["cases"]
        if case["id"].startswith("case.p11.document.")
    ]


def _doc_operation_cases() -> list[dict]:
    return [case for case in _doc_cases() if case["trigger"].get("kind") == "op"]


def _all_face_cases() -> list[dict]:
    return [
        case
        for path in (ATLAS, SLACK)
        for case in json.loads(path.read_text())["cases"]
        if case.get("viewports")
    ]


def _steps(case: dict) -> list[dict]:
    return [*case["setup"], case["trigger"]]


def test_atlas_has_one_headless_case_for_each_new_source_kind() -> None:
    cases = _doc_operation_cases()
    assert len(cases) == 7
    names = {case["id"].split(".")[3] for case in cases}
    assert names == KINDS
    assert all(case["viewports"] == [] for case in cases)
    assert all(case["trigger"]["kind"] == "op" for case in cases)


def test_face_case_manifest_covers_every_planned_seat_and_transition() -> None:
    cases = _all_face_cases()
    actual = {case["id"] for case in cases}
    assert actual == FACE_CASE_IDS
    assert all(case["viewports"] == [1440, 393] for case in cases)
    assert all(case["trigger"].get("kind") == "ui" for case in cases)


def test_meeting_form_faces_observe_the_rendered_send_state_in_each_seat() -> None:
    data = json.loads(SLACK.read_text())
    cases = {case["id"]: case for case in data["cases"]}
    for kind, seat in (
        ("meeting_summary", "window"),
        ("meeting_summary", "chair"),
        ("meeting_summary", "meetings_record"),
        ("meeting_digest", "meetings_record"),
        ("meeting_followup", "meetings_record"),
    ):
        for state in ("picked", "sent", "prepared"):
            case = cases[f"case.p11.{kind}.{seat}.{state}"]
            observed = case["expected"]["observe_at"]
            assert "[data-testid=meeting-send-well]" in observed, case["id"]
            if state == "prepared":
                assert observed.endswith("[data-testid=prepared-row]"), case["id"]
            else:
                assert observed.endswith("[data-testid=send-verbs]"), case["id"]

    chair = [cases[f"case.p11.meeting_summary.chair.{state}"]
             for state in ("picked", "sent", "prepared")]
    assert all("[data-testid=arrival-meeting-row] + .surface-ledger-open [data-testid=meeting-send-well]" in json.dumps(case)
               for case in chair)
    assert all(".desk-window [data-testid=meeting-send-well]" not in json.dumps(case)
               for case in chair)
    assert all(not any(step.get("kind") == "ui" and step.get("action") == "click"
                       and step.get("selector") == "[data-testid=arrival-meeting-row]"
                       for step in case["setup"])
               for case in chair)


def test_slack_face_outcomes_observe_the_post_click_rendered_send_receipt() -> None:
    data = json.loads(SLACK.read_text())
    cases = {case["id"]: case for case in data["cases"]}
    for case_id in (
        "case.p11.slack.posted.face",
        "case.p11.slack.failed.face",
        "case.p11.slack.unknown.face",
    ):
        case = cases[case_id]
        assert case["expected"]["observe_at"] == (
            ".desk-window [data-testid=meeting-send-well] [data-testid=send-verbs]"
        )
        assert case["trigger"]["selector"].endswith("[data-testid=send-verb]")
        assert any(predicate.get("kind") == "protocol_reads"
                   for predicate in case["expected"]["predicate"]["predicates"])


def test_each_source_uses_real_producer_preview_prepare_send_and_durable_reads() -> None:
    for case in _doc_operation_cases():
        steps = _steps(case)
        names = [step.get("name") for step in steps if step.get("kind") == "op"]
        assert "channel.preview" in names, case["id"]
        assert "channel.prepare" in names, case["id"]
        assert case["trigger"]["name"] == "channel.send"
        assert case["trigger"].get("capture_path") == "operation_id"
        reads = case["expected"]["reads"]
        receipt_reads = [r for r in reads if r.get("name") == "kernel.receipt.read"]
        assert len(receipt_reads) == 2, case["id"]
        assert any(r.get("name") == "channel.sends" for r in reads)
        facts = case["expected"]["predicate"]["facts"]
        required = {
            ("observe", "sends.0.id"),
            ("observe", "sends.0.channel"),
            ("observe", "sends.0.payload_digest"),
            ("observe", "sends.0.proof.path"),
            ("observe", "sends.0.file_path"),
        }
        assert required <= {(f.get("source"), f.get("path")) for f in facts}, case["id"]
        owners = [f for f in facts if f.get("path", "").endswith("actor_kind")]
        assert len(owners) == 2 and all(f["value"] == "owner" for f in owners)


def test_meeting_cases_use_import_and_engine_replay_boundary() -> None:
    fixture = (REPO / "tests/fixtures/philo11_documents/meeting_transcript.vtt").read_text()
    assert fixture.startswith("WEBVTT")
    for case in _doc_operation_cases():
        if case["id"].split(".")[3] not in {"meeting_summary", "meeting_digest", "meeting_followup", "meeting_decision", "decision_record"}:
            continue
        steps = _steps(case)
        assert any(s.get("name") == "meeting.import" for s in steps)
        assert any(s.get("substitute") == "engine_reply" for s in steps)
        assert "tests/fixtures/philo11_documents/meeting_transcript.vtt" in json.dumps(case)
        assert "tests/fixtures/philo11_documents/meeting_summary_reply.json" in json.dumps(case)


def test_meeting_decision_and_record_are_confirmed_by_real_proposal_route() -> None:
    for case in _doc_operation_cases():
        kind = case["id"].split(".")[3]
        if kind not in {"meeting_decision", "decision_record"}:
            continue
        # Explicit summary Run excludes plugins by design (HS-201). The
        # imported meeting must enter the real Stop-style queue instead.
        assert not any(s.get("name") == "meeting.summary.run" for s in case["setup"])
        assert any(s.get("action") == "queue_meeting_intelligence"
                   and s.get("meeting_id") == "{meeting_id}" for s in case["setup"])
        assert any(s.get("body", {}).get("scope", {}).get("capability_id")
                   == "meeting.plugin.decision_capture"
                   for s in case["setup"] if isinstance(s.get("body"), dict))
        assert any(
            s.get("kind") == "api" and s.get("method") == "POST"
            and s.get("path") == "/api/proposals/{proposal_id}/confirm"
            for s in case["setup"]
        )


def test_room_record_face_cases_mint_the_meeting_row_through_its_producer() -> None:
    for case in _doc_cases():
        if not case["id"].startswith("case.p11.decision_record.room."):
            continue
        setup = case["setup"]
        assert any(s.get("kind") == "op" and s.get("name") == "meeting.import" for s in setup), case["id"]
        assert any(
            s.get("kind") == "api"
            and s.get("path") == "/api/projects/{project_id}/meetings/{meeting_id}"
            for s in setup
        ), case["id"]
        assert any(
            s.get("kind") == "cli" and s.get("action") == "queue_meeting_intelligence"
            for s in setup
        ), case["id"]
        assert any(
            s.get("kind") == "api" and s.get("path") == "/api/proposals/{proposal_id}/confirm"
            for s in setup
        ), case["id"]
        assert any(
            s.get("kind") == "api" and s.get("method") == "GET"
            and s.get("path") == "/api/decision-records"
            and s.get("capture_as") == "record_id"
            for s in setup
        ), case["id"]
        attach = next(
            s for s in setup if s.get("kind") == "op" and s.get("name") == "project.resource.add"
        )
        assert attach["args"]["resource_ref"] == "decision_record:{record_id}", case["id"]


def test_long_slack_refusal_keeps_integer_limits_and_zero_history() -> None:
    data = json.loads(SLACK.read_text())
    case = next(c for c in data["cases"] if c["id"] == "case.p11.slack.too_large.op")
    draft = next(s for s in case["setup"] if s.get("name") == "project.update_draft")
    body = draft["args"]["body_md"]
    assert isinstance(body, str) and len(body.encode()) == 39001
    assert case["trigger"]["name"] == "channel.prepare"
    assert case["trigger"]["capture_from"] == "refusal"
    assert case["trigger"]["capture_path"] == "operation_id"
    assert any(r.get("name") == "kernel.receipt.read" for r in case["expected"]["reads"])
    facts = case["expected"]["predicate"]["predicates"][0]["facts"]
    limit = next(f for f in facts if f["path"] == "limit")
    size = next(f for f in facts if f["path"] == "size")
    assert limit == {"source": "trigger", "path": "limit", "value": 39000, "integer": True, "refused": {"code": "payload_too_large:slack"}}
    assert size == {"source": "trigger", "path": "size", "value": 39001, "integer": True, "refused": {"code": "payload_too_large:slack"}}
    assert {"source": "observe", "path": "sends", "length": 0} in facts
    assert {"kind": "cli_calls", "argv_prefix": ["https", "POST", "hooks.slack.com"], "count": 0} in case["expected"]["predicate"]["predicates"]


def test_meeting_summary_face_refusal_reads_preview_top_level_integer_limits() -> None:
    data = json.loads(SLACK.read_text())
    fixture = json.loads(
        (REPO / "tests/fixtures/philo11_documents/meeting_summary_over_limit_reply.json").read_text()
    )
    assert len(fixture["summary"]) == 40998
    for case_id in ("case.p11.transition.slack_limit", "case.p11.slack.too_large.face"):
        case = next(c for c in data["cases"] if c["id"] == case_id)
        assert case["trigger"]["trigger_route"] == {
            "method": "POST",
            "path": "/api/channels/preview",
        }
        assert any(
            step.get("kind") == "boundary"
            and step.get("substitute") == "engine_reply"
            and step.get("reply") == "tests/fixtures/philo11_documents/meeting_summary_over_limit_reply.json"
            for step in case["setup"]
        )
        assert any(step.get("name") == "meeting.summary.run" for step in case["setup"])
        assert any(step.get("name") == "channel.save_destination" for step in case["setup"])
        predicates = case["expected"]["predicate"]["predicates"]
        refusal = next(p for p in predicates if p.get("kind") == "protocol_status")
        assert refusal["body_integer_fields"] == ["size", "limit"]
        assert refusal["body_fields"] == {"size": 41097, "limit": 39000}
        assert any(p.get("value") == "TOO LARGE FOR SLACK" for p in predicates)
        assert any(p.get("kind") == "protocol_reads" for p in predicates)


def test_no_summary_case_reads_the_transcript_and_proves_no_send_well() -> None:
    data = json.loads(SLACK.read_text())
    case = next(c for c in data["cases"]
                if c["id"] == "case.p11.meeting_summary.meetings_record.no_summary")
    assert case["trigger"]["action"] == "fill"
    assert case["trigger"]["value"] == "Document source review"
    predicates = case["expected"]["predicate"]["predicates"]
    assert {"kind": "selector_presence", "selector": "[data-testid=meeting-send-well]",
            "present": False} in predicates
    assert {"kind": "text_contains", "value": "TRANSCRIPT"} in predicates
    assert any(p.get("kind") == "text_absent" and p.get("value") == "SEND"
               for p in predicates)


def test_slack_destination_save_uses_recording_edge_memory_store_and_hub_receipt() -> None:
    data = json.loads(SLACK.read_text())
    case = next(c for c in data["cases"]
                if c["id"] == "case.p11.slack.destination.d2a")
    assert any(step.get("kind") == "boundary"
               and step.get("substitute") == "cli_runner"
               and step.get("adapter") == "slack-https-edge"
               for step in case["setup"])
    assert case["trigger"]["trigger_route"] == {
        "method": "POST", "path": "/api/channels/slack-webhooks"
    }
    status = next(p for p in case["expected"]["predicate"]["predicates"]
                  if p.get("kind") == "protocol_status")
    assert status["status"] == 200
    assert status["body_fields"]["key_ref"] == {"nonempty": True}
    assert {"kind": "cli_calls", "argv_prefix": ["https", "POST", "hooks.slack.com"],
            "count": 0} in case["expected"]["predicate"]["predicates"]


def test_slack_destination_check_reads_the_visible_result_at_mobile_width() -> None:
    data = json.loads(SLACK.read_text())
    case = next(c for c in data["cases"]
                if c["id"] == "case.p11.slack.destination.d3")
    assert case["expected"]["observe_at"] == "[data-testid=dest-check-result]"
    assert case["trigger"]["then"][0]["selector"] == "[data-testid=dest-check-result]"


def test_preview_changed_case_fences_refusal_refresh_and_successful_second_press() -> None:
    data = json.loads(SLACK.read_text())
    case = next(c for c in data["cases"]
                if c["id"] == "case.p11.transition.preview_changed")
    predicates = case["expected"]["predicate"]["predicates"]
    sequence = next(p for p in predicates if p.get("kind") == "protocol_sequence")
    assert sequence["expect"] == [
        {"method": "POST", "path": "/api/channels/send", "status": 409},
        {"method": "POST", "path": "/api/channels/preview", "status": 200},
        {"method": "POST", "path": "/api/channels/send", "status": 200},
    ]
    assert case["expected"]["observe_at"].endswith("[data-testid=send-history]")
    assert case["trigger"]["then"][-1]["action"] == "scroll_into_view"


def test_transition_decision_setup_uses_the_route_creation_status() -> None:
    data = json.loads(SLACK.read_text())
    for case_id in (
        "case.p11.transition.preview_changed",
        "case.p11.transition.brief_last_ack",
        "case.p11.transition.brief_last_defer",
    ):
        case = next(c for c in data["cases"] if c["id"] == case_id)
        create = next(
            step for step in case["setup"]
            if step.get("kind") == "api" and step.get("method") == "POST"
            and step.get("path") == "/api/decisions"
        )
        assert create["expect_status"] == 201, case_id
        assert create["capture_path"] == "decision.id", case_id


def test_last_brief_item_transitions_keep_the_same_send_receipt() -> None:
    data = json.loads(SLACK.read_text())
    for case_id in (
        "case.p11.transition.brief_last_ack",
        "case.p11.transition.brief_last_defer",
    ):
        case = next(c for c in data["cases"] if c["id"] == case_id)
        assert case["expected"]["observe_at"].endswith("[data-testid=send-history]"), case_id
        predicates = case["expected"]["predicate"]["predicates"]
        assert any(p.get("kind") == "readable_text" and p.get("value") == "POSTED"
                   for p in predicates), case_id
        reads = next(p for p in predicates if p.get("kind") == "protocol_reads")
        assert reads["expect"][0]["row"]["match"]["channel"] == "slack", case_id
        assert any(p.get("kind") == "protocol_rows_same"
                   and p.get("match", {}).get("document_ref") == "monday_brief:{brief_id}"
                   for p in predicates), case_id
        sent = next(step for step in case["setup"]
                    if step.get("kind") == "api" and step.get("path") == "/api/channels/sends")
        assert sent["capture_as"] == "send_id" and sent["capture_path"] == "send.id", case_id


@pytest.mark.parametrize(
    ("case_id", "reason"),
    [
        ("case.p11.slack.failed.op", "invalid_payload"),
        ("case.p11.slack.unknown.op", "rollup_error"),
    ],
)
def test_slack_terminal_cases_pin_the_recorded_transport_reason(case_id: str, reason: str) -> None:
    data = json.loads(SLACK.read_text())
    case = next(c for c in data["cases"] if c["id"] == case_id)
    facts = next(
        part["facts"]
        for part in case["expected"]["predicate"]["predicates"]
        if part.get("kind") == "op_facts"
    )
    assert {"source": "observe", "path": "sends.0.reason", "value": reason} in facts


def test_posted_slack_proof_has_no_provider_identity_fields() -> None:
    data = json.loads(SLACK.read_text())
    case = next(c for c in data["cases"] if c["id"] == "case.p11.slack.posted.op")
    facts = case["expected"]["predicate"]["predicates"][0]["facts"]
    for field in ("url", "link", "id", "provider_id", "message_id", "ts"):
        assert {"source": "observe", "path": f"sends.0.proof.{field}", "absent": True} in facts
