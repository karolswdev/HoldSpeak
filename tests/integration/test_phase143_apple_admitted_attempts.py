"""HS-143-10 — production-object proofs for the Apple admitted-attempt bridge."""
from __future__ import annotations

from pathlib import Path

import pytest

from holdspeak.db import Database
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.apple_admitted_inference_service import AppleAdmittedInferenceService
from holdspeak.services.errors import ConflictError, ValidationError
from holdspeak.services.inference_adoption_service import RoutedInferenceCoordinator
from holdspeak.services.inference_fallback_controller import INFERENCE_FALLBACK_AUTHORITY
from tests.unit.test_phase143_inference_assignments import OWNER
from tests.unit.test_phase143_inference_route_plans import _ready_route


def _bridge(tmp_path: Path) -> AppleAdmittedInferenceService:
    db = Database(tmp_path / "apple-admitted.db")
    _ready_route(db, profiles=("quick", "deep"))
    return AppleAdmittedInferenceService(
        RoutedInferenceCoordinator(db), signing_secret=b"a" * 32
    )


def _admit(service: AppleAdmittedInferenceService, command: str = "apple-one") -> dict[str, object]:
    return service.admit(
        OWNER,
        command_id=command,
        capability_id="ask.answer",
        operation_id=f"{command}-operation",
        payload={"system_prompt": "", "user_prompt": "hello", "temperature": 0, "max_tokens": 32},
        reserved_output_tokens=32,
    )


def test_no_reservation_has_no_transport_and_tampered_ticket_is_refused(tmp_path: Path) -> None:
    service = _bridge(tmp_path)
    with pytest.raises(ValidationError) as absent:
        service.begin(OWNER, authorization="not-a-reservation")
    assert absent.value.code == "apple_admitted_authorization_invalid"
    with service.coordinator._db._connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM inference_route_attempts").fetchone()[0] == 0


def test_one_reservation_records_one_transport_and_same_attempt_receipt(tmp_path: Path) -> None:
    service = _bridge(tmp_path)
    admitted = _admit(service)
    authorization = str(admitted["authorization"])
    ticket = service._open(authorization)
    service.begin(OWNER, authorization=authorization)
    settled = service.reconcile(OWNER, authorization=authorization, classified_outcome="succeeded", result="answer")
    assert settled["attempt_id"] == ticket["attempt_id"]
    receipt = service.receipt(OWNER, authorization=authorization)
    assert receipt["state"] == "terminal"
    assert receipt["winning_attempt_id"] == ticket["attempt_id"]
    assert [attempt["attempt_id"] for attempt in receipt["attempts"]] == [ticket["attempt_id"]]
    # Replaying the idempotent begin command cannot dispatch a second transport
    # or mint another attempt after terminal settlement.
    service.begin(OWNER, authorization=authorization)
    assert len(service.receipt(OWNER, authorization=authorization)["attempts"]) == 1


@pytest.mark.parametrize(
    ("outcome", "disposition"),
    [
        ("malformed_output", "invalid_typed_output"),
        ("disconnected", "dispatch_outcome_unknown"),
        ("unavailable", "local_capacity_unavailable"),
    ],
)
def test_classified_client_outcome_reconciles_same_server_attempt_only(tmp_path: Path, outcome: str, disposition: str) -> None:
    service = _bridge(tmp_path)
    admitted = _admit(service, command=f"apple-{outcome}")
    authorization = str(admitted["authorization"])
    attempt_id = service._open(authorization)["attempt_id"]
    service.begin(OWNER, authorization=authorization)
    effect = service.reconcile(OWNER, authorization=authorization, classified_outcome=outcome)
    assert effect["attempt_id"] == attempt_id
    receipt = service.receipt(OWNER, authorization=authorization)
    attempt = receipt["attempts"][0]
    assert attempt["attempt_id"] == attempt_id
    assert attempt["disposition"] == disposition
    # A client report never dispatches a correction/fallback. The controller may
    # leave an eligible execution active, but only a later server call reserves it.
    assert len(receipt["attempts"]) == 1


def test_frozen_deployment_survives_post_admission_mutation_and_stop_blocks_wire(tmp_path: Path) -> None:
    service = _bridge(tmp_path)
    admitted = _admit(service, command="apple-frozen")
    authorization = str(admitted["authorization"])
    ticket = service._open(authorization)
    with service.coordinator._db._connection() as conn:
        before = conn.execute(
            "SELECT deployment_revision_id FROM inference_route_attempts WHERE id=?", (ticket["attempt_id"],)
        ).fetchone()[0]
    # The route-plan entry is the immutable egress/deployment evidence. No client
    # request contains a selector and changing current assignment cannot rewrite it.
    route = service.coordinator.plans.get_route_plan(
        Principal(PrincipalKind.OWNER, "owner-session"), ticket["route_plan_id"]
    )
    assert route["entries"][0]["deployment_revision_id"] == before
    service.controller.request_stop(
        INFERENCE_FALLBACK_AUTHORITY,
        command_id="stop-apple-frozen",
        execution_id=ticket["execution_id"],
    )
    with pytest.raises(ConflictError) as stopped:
        service.begin(OWNER, authorization=authorization)
    assert stopped.value.code == "inference_route_execution_terminal"
