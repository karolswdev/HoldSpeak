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
    return json.loads(ATLAS.read_text())["cases"]


def _steps(case: dict) -> list[dict]:
    return [*case["setup"], case["trigger"]]


def test_atlas_has_one_headless_case_for_each_new_source_kind() -> None:
    cases = _doc_cases()
    assert len(cases) == 7
    names = {case["id"].split(".")[3] for case in cases}
    assert names == KINDS
    assert all(case["viewports"] == [] for case in cases)
    assert all(case["trigger"]["kind"] == "op" for case in cases)


def test_each_source_uses_real_producer_preview_prepare_send_and_durable_reads() -> None:
    for case in _doc_cases():
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
    for case in _doc_cases():
        if case["id"].split(".")[3] not in {"meeting_summary", "meeting_digest", "meeting_followup", "meeting_decision", "decision_record"}:
            continue
        steps = _steps(case)
        assert any(s.get("name") == "meeting.import" for s in steps)
        assert any(s.get("substitute") == "engine_reply" for s in steps)
        assert "tests/fixtures/philo11_documents/meeting_transcript.vtt" in json.dumps(case)
        assert "tests/fixtures/philo11_documents/meeting_summary_reply.json" in json.dumps(case)


def test_meeting_decision_and_record_are_confirmed_by_real_proposal_route() -> None:
    for case in _doc_cases():
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
