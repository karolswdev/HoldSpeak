"""HS-200-41 (lanes A+B): the saved Room ask, proven end to end.

Suite ``phase200_task_resume``.  Everything here runs against the REAL
assembled routes and a REAL ``/api/ask`` run whose answer lands in
``ask_results`` through the kernel's own receipt-gated materializer — no
hand-seeded projection rows.

The four things this file exists to prove:

1. **A restart.** The task is written through one ``Database`` instance; that
   instance is closed and dropped, a NEW one is built over the same file, and
   the row is read back from it.  Nothing is carried in memory across.
2. **A late answer is CLAIMED, never re-run** (ruling B3).  The answer lands
   under the task's pinned ``invocation_id``; a resume after the restart finds
   it, settles the task, and dispatches NOTHING — the injected transport is a
   counter, and it must read zero.
3. **A double Resume cannot double-spend.**  Two resumes; one answer; one
   dispatch total.  And the kernel's own guard is asserted directly:
   ``ask_results.invocation_id`` / ``operation_id`` are UNIQUE, so even a
   racing dispatch cannot produce a second answer under one identity.
4. **Startup reconciliation** settles an orphaned lease to ``failed`` with a
   named reason and sends nothing anywhere.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import holdspeak.db as hsdb
from holdspeak.db import Database, reset_database
from holdspeak.db.task_resume import HOST_LOST_CODE
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.errors import ServiceError
from holdspeak.services.project_service import ProjectService
from holdspeak.web.context import WebContext
from holdspeak.web.routes import build_primitives_router, build_projects_router

OWNER = Principal(PrincipalKind.OWNER, "owner")


class _FakeIntel:
    """The hub's engine, doubled — the rig `tests/unit/test_web_routes_ask.py` uses."""

    active_provider = "local"

    def __init__(self, answer: str = "PRINTED") -> None:
        self.answer = answer
        self.calls = 0

    def run_prompt(self, *, system_prompt, user_prompt, temperature=None, max_tokens=None):
        self.calls += 1
        return self.answer


@pytest.fixture
def rig(tmp_path: Path, monkeypatch):
    """A real hub over one database file, with a doubled inference engine."""
    reset_database()
    db = Database(tmp_path / "holdspeak.db")
    monkeypatch.setattr(hsdb, "get_database", lambda *a, **k: db)

    # HS-132-09: `this_machine` readiness reads a REAL configured model file.
    hub_model = tmp_path / "HubModel-9B.gguf"
    hub_model.touch()
    monkeypatch.setattr(
        "holdspeak.intel.providers.configured_local_meeting_model_path",
        lambda: str(hub_model),
    )
    engine = _FakeIntel()
    monkeypatch.setattr("holdspeak.intel.engine.MeetingIntel", lambda **_kw: engine)
    monkeypatch.setattr("holdspeak.intel.providers._configured_engine", lambda: engine)

    app = FastAPI()

    @app.middleware("http")
    async def authenticated(request, call_next):
        request.state.principal = OWNER
        return await call_next(request)

    ctx = WebContext(get_state=lambda: {}, project_service=ProjectService(db))
    app.include_router(build_primitives_router(ctx))
    app.include_router(build_projects_router(ctx))
    yield db, TestClient(app), engine, tmp_path / "holdspeak.db"
    db.close()
    reset_database()


def _project(client: TestClient, name: str = "Architecture review") -> str:
    resp = client.post("/api/projects", json={"name": name})
    assert resp.status_code == 200, resp.text
    return str(resp.json()["project"]["id"])


def _save(client: TestClient, project_id: str, purpose: str, **body: Any) -> dict[str, Any]:
    resp = client.post(
        f"/api/projects/{project_id}/ask-tasks", json={"purpose": purpose, **body},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["task"]


class _Counter:
    """A transport that records every dispatch it is asked to make."""

    def __init__(self, answer: dict[str, Any] | None = None, raises: Exception | None = None):
        self.calls: list[dict[str, Any]] = []
        self.answer = answer or {"output": "LATE ANSWER"}
        self.raises = raises

    async def __call__(self, task: dict[str, Any]) -> dict[str, Any]:
        self.calls.append(task)
        if self.raises is not None:
            raise self.raises
        return self.answer


# ── 1. the invocation-identity seam ──────────────────────────────────


def test_api_ask_runs_under_the_identity_the_saved_ask_pinned(rig) -> None:
    """The seam this story needed: `/api/ask` had never accepted an id.

    `AskService.ask` has always taken one; only the transport never offered it.
    The response has ALWAYS carried the id back (the kernel's materializer
    stamps it onto the published projection) — so the web client can read it.
    """
    db, client, _engine, _path = rig
    project_id = _project(client)
    task = _save(client, project_id, "the architecture review brief")

    resp = client.post("/api/ask", json={
        "prompt": task["purpose"], "lens": "Project",
        "invocation_id": task["invocationId"],
    })
    assert resp.status_code == 200, resp.text
    assert resp.json()["invocation_id"] == task["invocationId"]

    with db._connection() as conn:
        rows = conn.execute("SELECT invocation_id FROM ask_results").fetchall()
    assert [str(row["invocation_id"]) for row in rows] == [task["invocationId"]]


def test_ask_still_mints_its_own_identity_when_none_is_offered(rig) -> None:
    _db, client, _engine, _path = rig
    resp = client.post("/api/ask", json={"prompt": "Go"})
    assert resp.status_code == 200, resp.text
    assert resp.json()["invocation_id"].startswith("ask_")


# ── 2. the restart ───────────────────────────────────────────────────


def test_an_unfinished_ask_survives_a_process_restart(rig) -> None:
    """AC1's restart half, for real: the service is dropped and rebuilt.

    Nothing crosses in memory — the second ``Database`` opens the same file
    from scratch and every field of the ratified row is read back from it.
    """
    db, client, _engine, db_path = rig
    project_id = _project(client)
    saved = _save(
        client, project_id, "the architecture review brief",
        lens="Project", recipe_key="review-brief", state="failed",
        stopped_reason="192.168.1.43 is unreachable",
        stopped_code="target_unavailable",
        grounding={"refs": ["note:abc"]},
    )

    db.close()                       # the hub goes away
    restarted = Database(db_path)    # a new process opens the same file
    try:
        service = ProjectService(restarted)
        items = service.list_unfinished_asks(OWNER)["items"]
        assert len(items) == 1
        row = items[0]
        assert row["id"] == saved["id"]
        assert row["purpose"] == "the architecture review brief"   # its purpose
        assert row["projectId"] == project_id                      # its Project
        assert row["state"] == "failed"                            # its state
        assert row["stoppedReason"] == "192.168.1.43 is unreachable"  # why stopped
        assert row["stoppedCode"] == "target_unavailable"
        assert row["savedAt"] == saved["savedAt"]                  # when saved
        assert row["invocationId"] == saved["invocationId"]
        assert row["recipeKey"] == "review-brief"
        assert row["grounding"] == {"refs": ["note:abc"]}
    finally:
        restarted.close()


# ── 3. a late answer is claimed, never re-run ────────────────────────


def test_a_late_answer_is_claimed_across_a_restart_and_nothing_dispatches(rig) -> None:
    """The heart of ruling B3.

    The answer lands through the REAL kernel path while the tab is gone; the
    hub restarts; the resume finds the receipt-gated ``ask_results`` row under
    the pinned identity, settles the task, and dispatches nothing.
    """
    db, client, engine, db_path = rig
    project_id = _project(client)
    task = _save(client, project_id, "what did we settle about the gateway?")

    # The answer arrives while he is away — a real /api/ask under the saved id.
    ask = client.post("/api/ask", json={
        "prompt": task["purpose"], "invocation_id": task["invocationId"],
    })
    assert ask.status_code == 200, ask.text
    assert engine.calls == 1

    db.close()
    restarted = Database(db_path)
    try:
        service = ProjectService(restarted)
        transport = _Counter()
        import asyncio
        out = asyncio.run(service.resume_ask(
            OWNER, task["id"], dispatcher=transport,
        ))
        assert transport.calls == []          # nothing dispatched
        assert engine.calls == 1              # the model was never asked twice
        assert out["claimed"] is True
        assert out["dispatched"] is False
        assert out["answer"]["output"] == "PRINTED"
        assert out["answer"]["invocation_id"] == task["invocationId"]
        assert out["task"]["state"] == "accepted"
        assert out["task"]["settledAt"]
        # A settled ask leaves the Resume projection.
        assert service.list_unfinished_asks(OWNER)["items"] == []
    finally:
        restarted.close()


def test_a_double_resume_cannot_double_spend(rig) -> None:
    """Two resumes, one answer, one dispatch."""
    db, client, engine, _path = rig
    project_id = _project(client)
    task = _save(client, project_id, "run me once")

    service = ProjectService(db)
    import asyncio

    async def real_ask(dto: dict[str, Any]) -> dict[str, Any]:
        resp = client.post("/api/ask", json={
            "prompt": dto["purpose"], "invocation_id": dto["invocationId"],
        })
        assert resp.status_code == 200, resp.text
        return resp.json()

    dispatched: list[str] = []

    async def counted(dto: dict[str, Any]) -> dict[str, Any]:
        dispatched.append(dto["invocationId"])
        return await real_ask(dto)

    first = asyncio.run(service.resume_ask(OWNER, task["id"], dispatcher=counted))
    assert first["dispatched"] is True
    assert first["claimed"] is False
    assert len(dispatched) == 1
    assert engine.calls == 1

    second = asyncio.run(service.resume_ask(OWNER, task["id"], dispatcher=counted))
    assert second["dispatched"] is False
    assert second["claimed"] is True
    assert len(dispatched) == 1          # never a second dispatch
    assert engine.calls == 1             # never a second engine run
    assert second["answer"]["output"] == first["answer"]["output"]


def test_one_identity_can_only_ever_hold_one_answer(rig) -> None:
    """The kernel's own guard, asserted rather than assumed.

    ``ask_results.invocation_id`` and ``operation_id`` are UNIQUE, so even a
    dispatch that raced past the service could not publish a second answer.
    """
    db, client, _engine, _path = rig
    project_id = _project(client)
    task = _save(client, project_id, "unique")
    assert client.post("/api/ask", json={
        "prompt": "unique", "invocation_id": task["invocationId"],
    }).status_code == 200

    import sqlite3
    with db._connection() as conn:
        row = dict(conn.execute("SELECT * FROM ask_results").fetchone())
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO ask_results (projection_stage_id, invocation_id, "
                "operation_id, receipt_id, payload_json, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (row["projection_stage_id"] + "_2", row["invocation_id"],
                 row["operation_id"], row["receipt_id"], row["payload_json"], 1.0),
            )


def test_a_refused_resume_records_the_targets_own_words(rig) -> None:
    """B5: the refusal is quoted verbatim onto the row, never composed."""
    db, client, _engine, _path = rig
    project_id = _project(client)
    task = _save(client, project_id, "no engine here")

    service = ProjectService(db)
    refusal = ServiceError(
        "target_unavailable", "192.168.1.43:8080 did not answer",
        context={"status": 409},
    )
    transport = _Counter(raises=refusal)
    import asyncio
    with pytest.raises(ServiceError) as caught:
        asyncio.run(service.resume_ask(OWNER, task["id"], dispatcher=transport))
    assert caught.value.code == "target_unavailable"

    row = db.project_ask_tasks.get(task["id"])
    assert row.state == "failed"
    assert row.stopped_reason == "192.168.1.43:8080 did not answer"
    assert row.stopped_code == "target_unavailable"
    assert row.dispatch_host_id == ""     # the lease is released
    # A failed ask is still unfinished work, and still resumable.
    assert [item["id"] for item in service.list_unfinished_asks(OWNER)["items"]] == [task["id"]]


# ── 4. startup reconciliation ────────────────────────────────────────


def test_startup_reconciliation_settles_an_orphan_and_dispatches_nothing(rig) -> None:
    db, client, engine, db_path = rig
    project_id = _project(client)
    task = _save(client, project_id, "the hub died holding this")
    db.project_ask_tasks.claim_dispatch(task["id"], "refhost_gone", 4)

    db.close()
    restarted = Database(db_path)
    try:
        service = ProjectService(restarted)
        settled = service.recover_ask_tasks_on_startup()
        assert settled == [task["id"]]
        assert engine.calls == 0          # nothing was re-dispatched

        row = restarted.project_ask_tasks.get(task["id"])
        assert row.state == "failed"
        assert row.stopped_code == HOST_LOST_CODE
        assert row.dispatch_host_id == ""

        # Twice is idempotent — a settled row is not an orphan.
        assert service.recover_ask_tasks_on_startup() == []
    finally:
        restarted.close()


# ── the routes ───────────────────────────────────────────────────────


def test_the_four_routes_are_thin_adapters_over_the_service(rig) -> None:
    _db, client, engine, _path = rig
    project_id = _project(client)

    saved = client.post(
        f"/api/projects/{project_id}/ask-tasks",
        json={"purpose": "through the wire", "lens": "Project"},
    )
    assert saved.status_code == 201, saved.text
    task = saved.json()["task"]

    listed = client.get("/api/ask-tasks")
    assert listed.status_code == 200
    assert [item["id"] for item in listed.json()["items"]] == [task["id"]]
    assert listed.json()["next_cursor"] is None

    resumed = client.post(f"/api/ask-tasks/{task['id']}/resume")
    assert resumed.status_code == 200, resumed.text
    body = resumed.json()
    assert body["dispatched"] is True
    assert body["task"]["state"] == "accepted"
    assert body["answer"]["output"] == "PRINTED"
    assert engine.calls == 1

    # Resumed again over the wire: claimed, not re-run.
    again = client.post(f"/api/ask-tasks/{task['id']}/resume")
    assert again.status_code == 200
    assert again.json()["dispatched"] is False
    assert again.json()["claimed"] is True
    assert engine.calls == 1


def test_the_routes_refuse_what_the_service_refuses(rig) -> None:
    _db, client, _engine, _path = rig
    project_id = _project(client)
    task = _save(client, project_id, "binned over the wire")

    assert client.post(
        f"/api/projects/{project_id}/ask-tasks", json={"purpose": "  "},
    ).status_code == 400
    assert client.post(
        "/api/projects/project_nope/ask-tasks", json={"purpose": "x"},
    ).status_code == 404
    assert client.get("/api/ask-tasks?limit=0").status_code == 400
    assert client.get("/api/ask-tasks?state=everything").status_code == 400
    assert client.post("/api/ask-tasks/asktask_nope/resume").status_code == 404

    discarded = client.post(f"/api/ask-tasks/{task['id']}/discard")
    assert discarded.status_code == 200
    assert discarded.json()["task"]["state"] == "discarded"
    assert client.get("/api/ask-tasks").json()["items"] == []
    # A discarded ask is not resumable — a conflict, not a silent re-run.
    assert client.post(f"/api/ask-tasks/{task['id']}/resume").status_code == 409


# ── the browser-observed stop, over the wire ─────────────────────────


def test_the_stopped_route_quotes_the_hubs_own_words_and_resumes_after(rig, tmp_path, monkeypatch) -> None:
    """AC1's "why it is stopped", on the failure path the Room actually hits.

    The engine is taken away, so the hub's live placement reports a real
    refusal.  The client sends only the CODE it would have received in the
    /api/ask body (`target_refusal` mints `inference_target_<state>`); the
    server resolves it to the destination's own `readiness_reason`.  Then the
    engine comes back and the very same row resumes.
    """
    from holdspeak.inference_targets import target_refusal, this_machine_target

    _db, client, engine, _path = rig
    project_id = _project(client)
    task = _save(client, project_id, "the architecture review brief")

    # The engine is gone: no configured model file at all.
    monkeypatch.setattr(
        "holdspeak.intel.providers.configured_local_meeting_model_path", lambda: "",
    )
    unready = this_machine_target()
    assert not unready.ready
    refusal = target_refusal(unready)
    code, words = str(refusal["code"]), str(refusal["error"])
    assert words                                   # the target has words to quote

    stopped = client.post(f"/api/ask-tasks/{task['id']}/stopped", json={"code": code})
    assert stopped.status_code == 200, stopped.text
    body = stopped.json()
    assert body["changed"] is True
    assert body["task"]["state"] == "failed"
    assert body["task"]["stoppedCode"] == code
    assert body["task"]["stoppedReason"] == words  # the hub's words, verbatim

    # Still unfinished work, still carrying its purpose and its identity.
    listed = client.get("/api/ask-tasks").json()["items"]
    assert [item["id"] for item in listed] == [task["id"]]
    assert listed[0]["purpose"] == "the architecture review brief"
    assert listed[0]["invocationId"] == task["invocationId"]

    # A repeat is a no-op, not an error, and never rewrites the quoted reason.
    again = client.post(
        f"/api/ask-tasks/{task['id']}/stopped", json={"code": "inference_target_needs_setup"},
    )
    assert again.status_code == 200
    assert again.json()["changed"] is False
    assert again.json()["task"] == body["task"]

    # The engine comes back; the failed row is exactly what he returns to.
    # (Restore the path rather than monkeypatch.undo() — the rig shares this
    # monkeypatch instance, and undo() would take the engine doubles with it.)
    hub_model = tmp_path / "HubModel-9B.gguf"
    monkeypatch.setattr(
        "holdspeak.intel.providers.configured_local_meeting_model_path",
        lambda: str(hub_model),
    )
    resumed = client.post(f"/api/ask-tasks/{task['id']}/resume")
    assert resumed.status_code == 200, resumed.text
    assert resumed.json()["dispatched"] is True
    assert resumed.json()["task"]["state"] == "accepted"
    assert engine.calls == 1
    assert client.get("/api/ask-tasks").json()["items"] == []


def test_the_stopped_route_takes_a_code_and_never_a_sentence(rig) -> None:
    _db, client, _engine, _path = rig
    project_id = _project(client)
    task = _save(client, project_id, "guarded over the wire")

    for bad in ("", "192.168.1.43 is unreachable", "Inference_Target_Unavailable"):
        resp = client.post(f"/api/ask-tasks/{task['id']}/stopped", json={"code": bad})
        assert resp.status_code == 400, (bad, resp.text)
        assert resp.json()["error_code"] == "ask_task_stop_code_invalid"
    # No caller-supplied reason field exists at all; sending one changes nothing.
    resp = client.post(
        f"/api/ask-tasks/{task['id']}/stopped",
        json={"code": "inference_target_unavailable", "reason": "PROSE FROM A CLIENT"},
    )
    assert resp.status_code == 200
    assert "PROSE FROM A CLIENT" not in resp.text

    assert client.post(
        "/api/ask-tasks/asktask_nope/stopped", json={"code": "inference_target_unavailable"},
    ).status_code == 404


def test_the_stopped_route_will_not_move_a_row_it_does_not_own(rig) -> None:
    _db, client, _engine, _path = rig
    project_id = _project(client)
    task = _save(client, project_id, "binned")
    assert client.post(f"/api/ask-tasks/{task['id']}/discard").status_code == 200

    refused = client.post(
        f"/api/ask-tasks/{task['id']}/stopped", json={"code": "inference_target_unavailable"},
    )
    assert refused.status_code == 409
    assert refused.json()["error_code"] == "ask_task_not_stoppable"
