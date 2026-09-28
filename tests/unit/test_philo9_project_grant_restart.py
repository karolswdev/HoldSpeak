"""PHILO-9-07 A7: a LIVE project grant survives a REAL hub restart and a credential reissue.

A hub is a PROCESS here (Phase 7's F13 rig, ``test_philo7_grant_restart.py``):
the credential store is a module singleton, so only a new process is a real
restart. The fence boots the real ``MeetingWebServer`` in a child process over
an isolated HOME, grants G1 on one project through the real route, kills the
process (SIGKILL), boots a NEW process on the same database, issues a new
PROJECT credential for the same identity through the real Settings route, and
publishes a draft over ``/api/mcp`` under G1. After the restart the lost
credential's grant shows as a project orphan beside nothing else, until the
new credential names it again.

Red on main: the grant route is a 404, and the agent's publish succeeds with
no operation and no receipt.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_philo7_grant_restart import AGENT_ID, HubProcess  # noqa: E402


@pytest.mark.timeout(300)
def test_a_live_project_grant_survives_a_real_restart_and_a_reissue(tmp_path: Path) -> None:
    home = tmp_path / "home"
    home.mkdir()
    first = HubProcess(home)
    try:
        status, project = first.call("POST", "/api/projects", {"name": "Payments ledger cutover"})
        assert status in (200, 201), project
        pid = project["project"]["id"]
        status, update = first.call("POST", f"/api/projects/{pid}/updates/draft", {})
        update_id = update["update"]["id"]
        status, granted = first.call("PUT", f"/api/settings/remote/delegations/{AGENT_ID}/projects/{pid}", {})
        assert status == 200, granted
        g1 = granted["grant_id"]
        first.credential()
    finally:
        first.kill()

    second = HubProcess(home)
    try:
        # The old token died with the old process: the grant is a LIVE orphan.
        assert second.call("PUT", "/api/settings/remote", {"enabled": True})[0] == 200
        ledger = second.call("GET", "/api/settings/remote")[1]
        assert ledger["credentials"] == []
        assert [(o["identity"], o["project_id"], o["state"], o["grant_id"]) for o in ledger["project_delegations"]] == [
            (AGENT_ID, pid, "LIVE", g1)]
        # A new credential for the same identity: the grant is its own again.
        status, issued = second.call("POST", "/api/settings/remote/credentials",
                                     {"identity": AGENT_ID, "palette": "PROJECT"})
        assert status == 200, issued
        is_error, published = second.tool(issued["token"], "project.publish_update", {"update_id": update_id})
        assert is_error is False, published
        status, receipt = second.call("GET", f"/api/kernel/read?refs=operation:{published['operation_id']}&view=receipt")
        assert status == 200, receipt
        assert receipt["objects"][0]["receipt"]["authority_basis"].split(":", 2)[1] == g1
        ledger = second.call("GET", "/api/settings/remote")[1]
        assert ledger["project_delegations"] == []
        [cred] = ledger["credentials"]
        assert [(g["project_id"], g["state"], g["grant_id"]) for g in cred["project_delegations"]] == [(pid, "LIVE", g1)]
        assert cred["palette"] == "PROJECT"
    finally:
        second.kill()
