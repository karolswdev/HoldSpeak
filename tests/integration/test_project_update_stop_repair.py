"""Focused first-Write Stop regressions.

These tests keep the real Project Room DB, Workbench parent and producer
boundaries.  The model boundary is the existing recorded local endpoint from
``test_desk_project_room``; no live provider is used.
"""
from __future__ import annotations

import json
import threading
import time
from pathlib import Path
from typing import Any, Iterator

import pytest

from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.errors import ConflictError
from holdspeak.services.project_update_service import ProjectUpdateService

from tests.integration.test_desk_project_room import (
    ENGINE_UPDATE,
    FakeLLM,
    _define_route,
    _hub,
    _poll_job,
)


@pytest.fixture
def llm() -> Iterator[FakeLLM]:
    server = FakeLLM()
    try:
        yield server
    finally:
        server.stop()


def _real_project_run(
    hub: Any, llm: FakeLLM, *, profile_id: str,
) -> tuple[str, dict[str, Any], Any]:
    """Seed one real project-update Workbench and its recorded engine route."""
    from tests.e2e.glass_infra import assign_engine, engine_profile

    project_id = hub.ok("POST", "/api/projects", {"name": "Stop fence"})["project"]["id"]
    _define_route(hub.home, llm.endpoint, profile_id)
    engine_profile(automation=True)
    assign_engine("workbench.item", 11)
    records = hub.ok(
        "POST", f"/api/projects/{project_id}/updates/draft", {"generator": "deterministic"},
    )["update"]
    automation = next(
        wb for wb in hub.db.workbenches.list()
        if wb.output_target == f"project_updates:{project_id}"
    )
    return project_id, records, automation


def _insert_job(hub: Any, project_id: str, update_id: str, job_id: str) -> None:
    with hub.db._connection() as conn:
        conn.execute(
            """INSERT INTO project_update_jobs
               (id, project_id, base_update_id, state, started_at)
               VALUES (?, ?, ?, 'running', datetime('now'))""",
            (job_id, project_id, update_id),
        )


def test_stop_before_parent_admission_fences_children_and_provider(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, llm: FakeLLM,
) -> None:
    """Stop won while parent admission was paused: no child or provider runs."""
    entered = threading.Event()
    release = threading.Event()
    llm.reply = ENGINE_UPDATE
    project_id = ""
    with _hub(tmp_path, monkeypatch, lifespan=True) as hub:
        project_id, records, automation = _real_project_run(hub, llm, profile_id="stop-before-parent")
        from holdspeak.services.inference_parent_route_bundle_service import (
            InferenceParentRouteBundleService,
        )

        original_start = InferenceParentRouteBundleService.start

        def delayed_start(self: Any, *args: Any, **kwargs: Any) -> Any:
            entered.set()
            assert release.wait(timeout=10), "parent admission was not released"
            return original_start(self, *args, **kwargs)

        monkeypatch.setattr(InferenceParentRouteBundleService, "start", delayed_start)
        job = hub.ok(
            "POST", f"/api/updates/{records['id']}/engine-pass",
            {"automation_id": automation.id},
        )["job"]
        assert entered.wait(timeout=10), "the run did not reach parent admission"

        stopped = hub.ok("POST", f"/api/update-jobs/{job['id']}/stop")["job"]
        assert (stopped["state"], stopped["reason"]) == ("stopped", "stopped"), stopped
        release.set()
        done = _poll_job(hub, job["id"], until=("stopped", "failed"), timeout=20)

        assert done["state"] == "stopped", done
        assert done["result_update_id"] is None, done
        assert llm.posts == [], "Stop-before-admission reached the provider"
        assert [row["id"] for row in hub.db.project_updates.list_updates(project_id)] == [records["id"]]
        with hub.db._connection() as conn:
            assert conn.execute(
                "SELECT COUNT(*) FROM workbench_runs WHERE workbench_id=?", (automation.id,)
            ).fetchone()[0] == 0


def test_stop_during_provider_answer_discards_late_delivery_without_revision(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, llm: FakeLLM,
) -> None:
    """A late recorded answer cannot deliver after Stop wins the job fence."""
    llm.reply = ENGINE_UPDATE
    llm.delay_s = 1.5
    with _hub(tmp_path, monkeypatch, lifespan=True) as hub:
        project_id, records, automation = _real_project_run(hub, llm, profile_id="stop-late-answer")
        job = hub.ok(
            "POST", f"/api/updates/{records['id']}/engine-pass",
            {"automation_id": automation.id},
        )["job"]
        deadline = time.monotonic() + 10
        while not llm.posts and time.monotonic() < deadline:
            time.sleep(0.05)
        assert llm.posts, "the recorded provider did not receive the child"

        stopped = hub.ok("POST", f"/api/update-jobs/{job['id']}/stop")["job"]
        assert stopped["state"] == "stopped", stopped
        done = _poll_job(hub, job["id"], until=("stopped", "failed"), timeout=20)
        time.sleep(0.4)  # let the recorded late answer reach the delivery seam

        assert done["state"] == "stopped", done
        assert hub.ok("GET", f"/api/update-jobs/{job['id']}")["job"]["state"] == "stopped"
        assert done["result_update_id"] is None, done
        updates = hub.db.project_updates.list_updates(project_id)
        assert [row["id"] for row in updates] == [records["id"]], updates


def test_stopped_job_refuses_late_http_and_cli_tool_writes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Both in-process HTTP and cross-process CLI identity hit the DB fence."""
    from holdspeak.mcp.palettes import CONDUCTOR, resolve_palette
    from holdspeak.principals import agent_credentials
    from holdspeak.services.conductor_launch import RUN_IDENTITY_PREFIX
    from holdspeak.services.engine_tool_loop import call_tool

    with _hub(tmp_path, monkeypatch, lifespan=True) as hub:
        project_id = hub.ok("POST", "/api/projects", {"name": "Late writes"})["project"]["id"]
        records = hub.ok(
            "POST", f"/api/projects/{project_id}/updates/draft", {"generator": "deterministic"},
        )["update"]
        job_id = "pujob_late_tools"
        _insert_job(hub, project_id, records["id"], job_id)
        hub.ok("POST", f"/api/update-jobs/{job_id}/stop") if False else None
        with hub.db._connection() as conn:
            conn.execute(
                "UPDATE project_update_jobs SET state='stopped', reason='stopped', finished_at=datetime('now') WHERE id=?",
                (job_id,),
            )

        args = {"update_id": records["id"], "body_md": "late words"}
        http_reply = json.loads(call_tool(
            "late-http", "late-http", "project.update_draft", args, 1,
            allow_project_update=True, project_id=project_id,
            project_update_job_id=job_id,
        ))
        assert "error" in http_reply, http_reply

        run_id = "late-cli"
        identity = f"{RUN_IDENTITY_PREFIX}{run_id}"
        credential = agent_credentials.issue(
            identity,
            palette=resolve_palette(CONDUCTOR), palette_name=CONDUCTOR,
            launch_id=run_id, project_id=project_id,
            scope_items=(f"project_update_job:{job_id}",),
        )
        try:
            response = hub.client.post(
                "/api/mcp", headers={"X-HoldSpeak-Token": credential.token},
                json={"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                      "params": {"name": "project.update_draft", "arguments": args}},
            )
            assert response.status_code == 200, response.text
            payload = response.json()
            assert payload["result"]["isError"] is True, payload
        finally:
            agent_credentials.revoke(identity, "stop-repair-proof")

        assert hub.db.project_updates.get_update(records["id"])["body_md"] == records["body_md"]
        assert len(hub.db.project_updates.list_updates(project_id)) == 1


def test_write_stop_orderings_preserve_committed_identity_and_leave_legacy_runs_alive(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The producer and Stop transaction orderings are both explicit."""
    with _hub(tmp_path, monkeypatch, lifespan=True) as hub:
        project_id = hub.ok("POST", "/api/projects", {"name": "Orderings"})["project"]["id"]
        records = hub.ok(
            "POST", f"/api/projects/{project_id}/updates/draft", {"generator": "deterministic"},
        )["update"]
        first, second = "pujob_write_wins", "pujob_stop_wins"
        _insert_job(hub, project_id, records["id"], first)
        _insert_job(hub, project_id, records["id"], second)
        service = ProjectUpdateService(hub.db)
        agent = Principal(PrincipalKind.AGENT, "agent:run:ordering")
        owner = Principal(PrincipalKind.OWNER, "local-owner")

        committed = service.write_agent_update(
            agent, project_id, body_md="committed agent words", job_id=first,
        )
        stopped = service.stop_engine_pass(owner, first)
        assert stopped["state"] == "stopped"
        assert stopped["result_update_id"] == committed["id"], stopped
        assert hub.ok("GET", f"/api/update-jobs/{first}")["job"]["result_update_id"] == committed["id"]
        assert hub.db.project_updates.get_update(committed["id"])["body_md"].rstrip() == "committed agent words"

        with pytest.raises(ConflictError, match="stopped"):
            service.write_agent_update(
                agent, project_id, body_md="late agent words", job_id=first,
            )
        stopped_second = service.stop_engine_pass(owner, second)
        with pytest.raises(ConflictError, match="stopped"):
            service.write_agent_update(
                agent, project_id, body_md="second late words", job_id=second,
            )
        assert stopped_second["state"] == "stopped"

        # No runner job context is the existing scheduled/legacy delivery
        # path; stopping one manual job does not fence that independent write.
        legacy = service.write_agent_update(
            owner, project_id, body_md="scheduled words", generator="agent:automation:scheduled",
        )
        assert legacy["id"] != committed["id"]
        assert hub.db.project_updates.get_update(legacy["id"])["body_md"].rstrip() == "scheduled words"

