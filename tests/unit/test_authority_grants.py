from __future__ import annotations

import pytest

from holdspeak.db import Database


def test_grant_binds_scope_and_records_every_use(tmp_path) -> None:
    db = Database(tmp_path / "authority.db")
    grant = db.actuators.issue_grant(
        actor="karol",
        operation_family="external_write",
        effect_class="github/create_issue",
        destination="github:sha256:fixed",
        data_classes=["proposed_content", "connector_metadata"],
        project_scope="acme/app",
        resource_scope="meeting-1",
        ttl_seconds=600,
        max_uses=2,
        control_mode="yolo",
    )
    assert grant.state == "active"
    assert grant.remaining_uses == 2
    assert grant.binding_hash

    first = db.actuators.consume_grant(grant.id, operation_id="actuator:p1")
    second = db.actuators.consume_grant(grant.id, operation_id="actuator:p2")
    assert first.remaining_uses == 1
    assert second.state == "revoked"
    assert second.revoke_reason == "count_exhausted"
    assert [row["operation_id"] for row in db.actuators.list_grant_uses(grant.id)] == [
        "actuator:p2",
        "actuator:p1",
    ]
    with pytest.raises(PermissionError):
        db.actuators.consume_grant(grant.id, operation_id="actuator:p3")


def test_configuration_revocation_is_visible_and_idempotent(tmp_path) -> None:
    db = Database(tmp_path / "authority.db")
    grant = db.actuators.issue_grant(
        actor="owner",
        operation_family="external_write",
        effect_class="slack/post_message",
        destination="slack:fixed",
        data_classes=["proposed_content"],
        ttl_seconds=600,
        max_uses=3,
    )
    assert (
        db.actuators.revoke_active_grants(reason="destination_configuration_changed")
        == 1
    )
    assert (
        db.actuators.revoke_active_grants(reason="destination_configuration_changed")
        == 0
    )
    updated = db.actuators.get_grant(grant.id)
    assert updated is not None
    assert updated.state == "revoked"
    assert updated.revoke_reason == "destination_configuration_changed"


def test_proposal_axes_are_separate_and_queryable(tmp_path) -> None:
    db = Database(tmp_path / "authority.db")
    proposed = db.actuators.record_proposal(
        meeting_id=None,
        origin="desk",
        window_id="desk:1",
        plugin_id="slack_export",
        plugin_version="1",
        idempotency_key="axes-1",
        target="slack",
        action="post_message",
        preview="Send the digest",
        payload={"text": "digest"},
    )
    assert (
        proposed.review_decision,
        proposed.authorization_state,
        proposed.execution_state,
    ) == ("unreviewed", "proposed", "not_started")
    reviewed = db.actuators.record_review_decision(
        proposed.id, "accepted", actor="reviewer"
    )
    assert reviewed.status == "proposed"
    assert reviewed.review_decision == "accepted"
    assert reviewed.authorization_state == "proposed"
    approved = db.actuators.transition_proposal(
        proposed.id, to_status="approved", actor="karol"
    )
    assert (
        approved.review_decision,
        approved.authorization_state,
        approved.execution_state,
    ) == ("accepted", "approved", "not_started")
    running = db.actuators.mark_execution_state(approved.id, "running")
    assert running.status == "approved"
    assert running.execution_state == "running"
