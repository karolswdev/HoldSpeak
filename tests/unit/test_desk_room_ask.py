"""Room ▸ Ask this project (Betterment Q1, "The Room's Ask tells the truth").

The hub half. The face half is
``web/src/features/project-room/__tests__/room.app.test.tsx``.

RECON (asking/RECON.md steps 8 and 9): Ask this project failed after 100 s on a
busy one-slot LAN engine with "No assigned model completed this request", and
Resume then showed ``UNIQUE constraint failed:
inference_adoption_material_snapshots.operation_id``.  The cause of the second:
Resume dispatched again under the saved ask's invocation id, and the routed
admission stages its material under ``operation_id = invocation_id``; the
retry's material is new (memory reads again), so the second INSERT broke the
UNIQUE.  Each retry now runs as its own operation.
"""
from __future__ import annotations

import asyncio
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.errors import ServiceError

from tests.unit.test_desk_ask_ai import OWNER, _assign, _seed_routes, hub  # noqa: F401  (fixture)


class _FlakyEngine:
    """Fails the first call (the busy engine), then answers."""

    active_provider = "fixture"

    def __init__(self, model: str, plan: list[Any]) -> None:
        self.active_model = model
        self._plan = plan

    def run_prompt_stream(self, **_kw: Any) -> Any:
        from holdspeak.kernel.inference_stream import Delta

        step = self._plan.pop(0)
        if isinstance(step, Exception):
            raise step
        yield Delta(kind="text", text=step)
        yield Delta(kind="usage", meta={"prompt_tokens": 20, "completion_tokens": 20})
        yield Delta(kind="done")

    def run_prompt(self, **_kw: Any) -> str:
        step = self._plan.pop(0)
        if isinstance(step, Exception):
            raise step
        return step


def _routed(hub: Any, plan: list[Any]) -> None:
    _seed_routes(hub.db)
    hub.broker.inference_adoption_service.migrate_legacy_config(OWNER, SimpleNamespace(
        thoughts=SimpleNamespace(inference_target_id="glass-lan"),
        dictation=SimpleNamespace(runtime=SimpleNamespace(profile_id="glass-lan"))))
    _assign(hub.db, "ask.answer", ["glass-lan"], "room-ask-lan")
    hub.broker.inference_runner._engine_factory = lambda rev, **_kw: _FlakyEngine(str(rev.model), plan)


def _ask_dispatch(ask_service: Any, calls: list[str] | None = None):
    """The Resume route's transport (``projects.py``), over a given AskService."""
    async def dispatch(task: dict[str, Any]) -> Any:
        if calls is not None:
            calls.append(str(task["invocationId"]))
        return await ask_service.ask(
            OWNER, str(task["purpose"]), task.get("grounding") or None,
            lens=str(task.get("lens") or "Project"), invocation_id=str(task["invocationId"]),
        )
    return dispatch


def _saved_ask(hub: Any) -> tuple[Any, dict[str, Any]]:
    from holdspeak.services.project_service import ProjectService

    projects = ProjectService(hub.db)
    project = projects.create_project(OWNER, {"name": "Ledger migration"})
    pid = project.get("id") or project["project"]["id"]
    task = projects.save_ask(OWNER, pid, {
        "purpose": "What blocks the November 5 freeze?",
        "grounding": {"meeting_ids": [], "artifact_ids": [], "refs": [f"project:{pid}"], "expand": "summary"},
    })["task"]
    return projects, task


def _first_run_fails(hub: Any, task: dict[str, Any]) -> ServiceError:
    from holdspeak.services.ask_service import AskService

    with pytest.raises(ServiceError) as caught:
        asyncio.run(AskService(hub.db, broker=hub.broker).ask(
            OWNER, task["purpose"], task["grounding"], lens="Project",
            invocation_id=task["invocationId"]))
    return caught.value


ANSWER = "The freeze waits on the reconciliation job; it has no owner yet."


def test_resume_after_a_failed_room_ask_runs_again_and_answers(hub) -> None:
    """RECON step 9: Resume on a stopped ask runs the question again."""
    from holdspeak.services.ask_service import AskService

    plan: list[Any] = [TimeoutError("engine busy"), ANSWER]
    _routed(hub, plan)
    projects, task = _saved_ask(hub)
    failure = _first_run_fails(hub, task)
    assert failure.code == "inference_route_failed"
    assert failure.context["reason"]                     # always a reason token
    assert plan == [ANSWER]                              # the engine was called once

    calls: list[str] = []
    out = asyncio.run(projects.resume_ask(
        OWNER, task["id"], dispatcher=_ask_dispatch(AskService(hub.db, broker=hub.broker), calls)))
    assert out["dispatched"] is True
    assert out["answer"]["output"] == ANSWER
    assert plan == []                                    # the retry reached the engine
    assert out["task"]["state"] == "accepted"
    # The retry ran as its own operation, and the row keeps the key to it.
    assert calls and calls[0] != task["invocationId"]
    assert out["task"]["invocationId"] == calls[0]

    # The settled ask claims its answer; nothing runs again.
    again = asyncio.run(projects.resume_ask(
        OWNER, task["id"], dispatcher=_ask_dispatch(AskService(hub.db, broker=hub.broker), calls)))
    assert again["claimed"] is True and again["dispatched"] is False
    assert again["answer"]["output"] == ANSWER
    assert len(calls) == 1


def test_resume_with_new_material_never_shows_a_database_error(hub, monkeypatch) -> None:
    """The exact RECON error: the retry's material differs from the first run's.

    Under the old identity the second admission broke
    ``UNIQUE constraint failed: inference_adoption_material_snapshots.operation_id``.
    """
    import holdspeak.services.ask_service as ask_module
    from holdspeak.services.ask_service import AskService

    plan: list[Any] = [TimeoutError("engine busy"), ANSWER]
    _routed(hub, plan)
    projects, task = _saved_ask(hub)
    _first_run_fails(hub, task)
    # Memory read again between the two runs: the material changed.
    monkeypatch.setattr(ask_module, "_ASK_SYSTEM_PROMPT", ask_module._ASK_SYSTEM_PROMPT + " ")

    out = asyncio.run(projects.resume_ask(
        OWNER, task["id"], dispatcher=_ask_dispatch(AskService(hub.db, broker=hub.broker))))
    assert out["answer"]["output"] == ANSWER
    assert out["task"]["state"] == "accepted"


def test_a_run_still_going_is_never_run_twice(hub, monkeypatch) -> None:
    projects, task = _saved_ask(hub)
    monkeypatch.setattr(type(hub.db.project_ask_tasks), "invocation_run_state", lambda self, _id: "running")
    calls: list[str] = []

    async def dispatch(dto: dict[str, Any]) -> Any:
        calls.append(dto["invocationId"])
        return {"output": "never"}

    with pytest.raises(ServiceError) as caught:
        asyncio.run(projects.resume_ask(OWNER, task["id"], dispatcher=dispatch))
    assert caught.value.code == "ask_task_still_running"
    assert caught.value.context["reason"] == "still_running"
    assert calls == []
    assert hub.db.project_ask_tasks.get(task["id"]).dispatch_host_id == ""   # lease released


def test_a_failed_resume_stores_the_reason_token_on_the_row(hub) -> None:
    """The row says why in words: its code is the face reason token."""
    projects, task = _saved_ask(hub)

    async def dispatch(_dto: dict[str, Any]) -> Any:
        raise ServiceError("inference_route_failed", "No assigned model completed this request",
                           context={"reason": "engine_busy", "status": 409})

    with pytest.raises(ServiceError):
        asyncio.run(projects.resume_ask(OWNER, task["id"], dispatcher=dispatch))
    row = hub.db.project_ask_tasks.get(task["id"])
    assert row.state == "failed"
    assert row.stopped_code == "engine_busy"


# ── every refusal carries a reason (ask.ts never falls back) ────────────────


@pytest.fixture
def ask_client(hub):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from holdspeak.web.context import WebContext
    from holdspeak.web.routes import build_primitives_router

    app = FastAPI()

    @app.middleware("http")
    async def authenticated(request, call_next):
        request.state.principal = OWNER
        return await call_next(request)

    app.include_router(build_primitives_router(WebContext(get_state=lambda: {})))
    return TestClient(app)


@pytest.mark.parametrize(("body", "reason"), [
    ({"prompt": ""}, "not_sent"),
    ({"prompt": "x", "grounding": {"meeting_ids": [], "artifact_ids": [], "refs": ["note:gone"],
                                   "expand": "summary"}}, "source_gone"),
    ({"prompt": "x", "invocation_id": "not valid!"}, "not_sent"),
])
def test_every_ask_refusal_names_a_reason(ask_client, body, reason) -> None:
    resp = ask_client.post("/api/ask", json=body)
    assert resp.status_code >= 400
    assert resp.json()["reason"] == reason


def test_a_routed_failure_names_its_reason_on_the_wire(hub, ask_client) -> None:
    _routed(hub, [TimeoutError("engine busy")])
    resp = ask_client.post("/api/ask", json={"prompt": "What blocks the freeze?"})
    assert resp.status_code == 409
    assert resp.json()["reason"] in {"did_not_answer", "timed_out", "engine_busy"}


def test_an_engine_that_cannot_be_reached_is_not_no_engine() -> None:
    """FOLLOWUPS (from Q0): "Engine not reachable" showed as "No engine for answers"."""
    from holdspeak.services.ask_service import AskService

    unready = {"considerations": [{"status": "skipped", "disposition": "preflight_unavailable",
                                   "reason_code": "binding_not_ready", "physical_attempts": 0}],
               "terminal_disposition": "preflight_unavailable"}
    assert AskService._route_reason(unready) == "not_reachable"
    disabled = {"considerations": [{"status": "skipped", "disposition": "preflight_unavailable",
                                    "reason_code": "binding_disabled", "physical_attempts": 0}],
                "terminal_disposition": "preflight_unavailable"}
    assert AskService._route_reason(disabled) == "no_engine"
    assert AskService.refusal_reason(ServiceError("no_assignment", "x")) == "no_engine"
    assert AskService.refusal_reason(ServiceError("grounding_not_found", "x")) == "source_gone"


def test_a_routed_answer_is_claimed_and_never_run_twice(hub) -> None:
    """The Room settles a finished ask through Resume; on the routed path the
    answer is stored under the winning child's identity, and the settle used
    to find nothing and run the question a second time."""
    from holdspeak.services.ask_service import AskService

    plan: list[Any] = [ANSWER, "a second, paid-for answer"]
    _routed(hub, plan)
    projects, task = _saved_ask(hub)
    asyncio.run(AskService(hub.db, broker=hub.broker).ask(
        OWNER, task["purpose"], task["grounding"], lens="Project", invocation_id=task["invocationId"]))
    calls: list[str] = []
    out = asyncio.run(projects.resume_ask(
        OWNER, task["id"], dispatcher=_ask_dispatch(AskService(hub.db, broker=hub.broker), calls)))
    assert out["claimed"] is True and out["dispatched"] is False
    assert out["answer"]["output"] == ANSWER
    assert calls == [] and plan == ["a second, paid-for answer"]


# ── the recorded wire the Room face replays (room.app.test.tsx) ────────────

ROOM_WIRES = Path(__file__).resolve().parents[2] / "web" / "src" / "features" / "project-room" / "__tests__" / "room-wires"


def test_record_the_room_ask_that_fails_then_answers(hub, tmp_path) -> None:
    """Ask this project on an engine that does not answer, then Ask again.

    The hub's answers are recorded for the face test
    (``room-wires/roomAskQ1.json``; HOLDSPEAK_WIRE_WRITE=1 rewrites it).
    """
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from holdspeak.services.project_service import ProjectService
    from holdspeak.web.context import WebContext
    from holdspeak.web.routes import build_primitives_router, build_projects_router
    from tests.unit.test_desk_speak import _record

    plan: list[Any] = [TimeoutError("engine busy"), ANSWER]
    _routed(hub, plan)
    app = FastAPI()

    @app.middleware("http")
    async def authenticated(request, call_next):
        request.state.principal = OWNER
        return await call_next(request)

    ctx = WebContext(get_state=lambda: {}, project_service=ProjectService(hub.db))
    app.include_router(build_primitives_router(ctx))
    app.include_router(build_projects_router(ctx))
    client = TestClient(app)

    created = client.post("/api/projects", json={"name": "Ledger migration"})
    assert created.status_code == 200, created.text
    pid = created.json()["project"]["id"]
    room = client.get(f"/api/projects/{pid}/room")
    assert room.status_code == 200, room.text
    grounding = {"meeting_ids": [], "artifact_ids": [], "refs": [f"project:{pid}"], "expand": "summary"}
    purpose = "What blocks the November 5 freeze?"
    saved = client.post(f"/api/projects/{pid}/ask-tasks", json={"purpose": purpose, "lens": "Project", "grounding": grounding})
    assert saved.status_code == 201, saved.text
    task = saved.json()["task"]
    failed = client.post("/api/ask", json={
        "prompt": purpose, "lens": "Project",
        "context": [{"id": pid, "kind": "project", "title": "Ledger migration", "ref": f"project:{pid}"}],
        "grounding": grounding, "invocation_id": task["invocationId"],
    })
    assert failed.status_code == 409, failed.text
    body = failed.json()
    assert body["reason"] and "code" not in body          # no target code: the face sends the reason
    stopped = client.post(f"/api/ask-tasks/{task['id']}/stopped", json={"code": body["reason"]})
    assert stopped.status_code == 200, stopped.text
    listed = client.get(f"/api/ask-tasks?state=unfinished&project_id={pid}&limit=5")
    assert listed.json()["items"][0]["stoppedCode"] == body["reason"]
    resumed = client.post(f"/api/ask-tasks/{task['id']}/resume")
    assert resumed.status_code == 200, resumed.text
    assert resumed.json()["answer"]["output"] == ANSWER
    after = client.get(f"/api/ask-tasks?state=unfinished&project_id={pid}&limit=5")
    assert after.json()["items"] == []
    # The failure body the face must never print (RECON step 8).
    assert body["error"] == "No assigned model completed this request"

    _record("roomAskQ1", {
        "project_id": pid,
        "room": room.json(),
        "save": saved.json(),
        "ask_failed": {"status": failed.status_code, "body": {k: v for k, v in body.items() if k in {"error", "reason", "route"}}},
        "stopped": stopped.json(),
        "unfinished_after_stop": listed.json(),
        "resume": resumed.json(),
        "unfinished_after_resume": after.json(),
    }, tmp_path, "tests/unit/test_desk_room_ask.py::test_record_the_room_ask_that_fails_then_answers",
        folder=ROOM_WIRES)
