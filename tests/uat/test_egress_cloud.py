"""HSU-3-02: a falsifiable local -> named-cloud egress contrast."""

from __future__ import annotations

import pytest

from uat.conductor.db import Database
from uat.conductor.runs import RunManager


@pytest.fixture
def real_manager(tmp_path, monkeypatch):
    monkeypatch.setenv("UAT_RUNS_ROOT", str(tmp_path / "_runs"))
    monkeypatch.setenv("UAT_DB_PATH", str(tmp_path / "_runs" / "uat.db"))
    monkeypatch.delenv("UAT_REAL_HOME", raising=False)
    mgr = RunManager(Database(), boot_timeout=60.0, link_caches=True)
    try:
        yield mgr
    finally:
        mgr.teardown_all()


def _boot_or_skip(mgr):
    run = mgr.create_run(deck="golden-local")
    if run.status != "up":
        logs = mgr.logs(run.id, 60)
        pytest.skip(
            f"product did not boot: {run.error}\nstderr:\n{logs.get('stderr', '')}"
        )
    return run


def test_cloud_card_names_target_and_remains_unexecuted(real_manager):
    run = _boot_or_skip(real_manager)

    # Genuine OFF state first: the same setup route that feeds the chrome says
    # local, and the local control note exists.
    control = real_manager.apply_recipe(run.id, "seeded-desk")
    assert control.probe["ok"], control.probe
    control_by_kind = {row["kind"]: row for row in control.probe["results"]}
    assert control_by_kind["egress_scope_is"]["ok"]

    # Treatment: restart onto the explicit cloud deck, stage the proposal via
    # public sync+aftercare routes, and read it back through the product API.
    treatment = real_manager.apply_recipe(run.id, "egress-cloud-card")
    assert treatment.probe["ok"], treatment.probe
    by_kind = {row["kind"]: row for row in treatment.probe["results"]}
    assert by_kind["egress_scope_is"]["ok"], by_kind["egress_scope_is"]
    assert by_kind["proposal_egress_names_target"]["ok"], by_kind[
        "proposal_egress_names_target"
    ]

    proposals = real_manager.product_client(run.id).get_json(
        "/api/meetings/uat-egress-meeting/proposals"
    )["proposals"]
    assert len(proposals) == 1
    proposal = proposals[0]
    assert proposal["target"] == "github"
    assert proposal["payload"]["repo"] == "acme/holdspeak-uat"
    assert proposal["status"] == "proposed"
    assert proposal["executed_at"] is None
    assert proposal["result"] is None

    # Probe-first idempotency: a second apply does not create another card.
    again = real_manager.apply_recipe(run.id, "egress-cloud-card")
    assert again.already_satisfied is True
    proposals_again = real_manager.product_client(run.id).get_json(
        "/api/meetings/uat-egress-meeting/proposals"
    )["proposals"]
    assert [row["id"] for row in proposals_again] == [proposal["id"]]
