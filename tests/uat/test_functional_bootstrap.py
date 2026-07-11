"""Exact, local bootstrap worlds used by the owner functional campaigns."""

from __future__ import annotations

import pytest

from uat.conductor.db import Database
from uat.conductor.runs import RunManager


@pytest.fixture
def real_manager(tmp_path, monkeypatch):
    monkeypatch.setenv("UAT_RUNS_ROOT", str(tmp_path / "_runs"))
    monkeypatch.setenv("UAT_DB_PATH", str(tmp_path / "_runs" / "uat.db"))
    monkeypatch.delenv("UAT_REAL_HOME", raising=False)
    manager = RunManager(Database(), boot_timeout=60.0, link_caches=True)
    try:
        yield manager
    finally:
        manager.teardown_all()


def test_functional_meeting_proposal_and_queue_are_exact(real_manager):
    run = real_manager.create_run(deck="golden-local")
    if run.status != "up":
        pytest.skip(f"product did not boot: {run.error}")

    meeting_world = real_manager.apply_recipe(run.id, "functional-aftercare-review")
    assert meeting_world.probe["ok"], meeting_world.probe
    meeting = real_manager.product_client(run.id).get_json(
        "/api/meetings/uat-functional-aftercare"
    )
    actions = {
        item["id"]: item
        for item in meeting["intel"]["action_items"]
    }
    assert actions["uat-functional-action-pending"]["review_state"] == "pending"
    assert actions["uat-functional-action-accepted"]["review_state"] == "accepted"

    proposal_world = real_manager.apply_recipe(run.id, "functional-proposal-review")
    assert proposal_world.probe["ok"], proposal_world.probe
    proposals = real_manager.product_client(run.id).get_json(
        "/api/meetings/uat-functional-aftercare/proposals"
    )["proposals"]
    assert [(item["status"], item["payload"]["repo"]) for item in proposals] == [
        ("proposed", "acme/holdspeak-owner-uat")
    ]

    queue_world = real_manager.apply_recipe(run.id, "functional-qlippy-queue")
    assert queue_world.probe["ok"], queue_world.probe
    for meeting_id, repo in (
        ("uat-qlippy-one", "acme/holdspeak-qlippy-one"),
        ("uat-qlippy-two", "acme/holdspeak-qlippy-two"),
    ):
        rows = real_manager.product_client(run.id).get_json(
            f"/api/meetings/{meeting_id}/proposals"
        )["proposals"]
        assert len(rows) == 1
        assert rows[0]["status"] == "proposed"
        assert rows[0]["payload"]["repo"] == repo

    # Probe-first idempotency: reapplying does not add a second card.
    again = real_manager.apply_recipe(run.id, "functional-proposal-review")
    assert again.already_satisfied is True
