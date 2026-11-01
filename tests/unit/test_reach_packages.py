"""PG-DIRECTION DIR1: the briefing package, its token and the page's answer.

A rig Program's core question makes a package; its token reads it many times
and answers it once through ``program.decide`` with ``via="page"`` (the ledger
says "decided from the briefing page"); a second answer is "answered
already"; an expired, a revoked and an unknown token read nothing, the same
way; only the token's SHA-256 is stored; the token reaches no other route
(the census over every ``/api`` route of the real app); it is never in a log
line, a frame or an egress call.
"""
from __future__ import annotations

import hashlib
import json
import logging
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest

from holdspeak.principals import (
    Principal, PrincipalKind, PrincipalRight, briefing_route, phone_device_route, required_right,
)
from holdspeak.services import briefing_service as briefing_module
from holdspeak.services.briefing_service import (
    BriefingRefused, BriefingService, is_token, later_until, mint_token, token_hash,
)
from holdspeak.services.program_service import ProgramRefused
from tests.integration.program_rig import FAKE_CHECK, OWNER, Rig

AGENT = Principal(PrincipalKind.AGENT, "agent-1")


class Clock:
    def __init__(self) -> None:
        # 06:30 UTC on today's date: the hub's page lookup reads the real
        # clock, so a fixed day turned every page expired once the real time
        # passed it (2026-11-01 06:30 UTC, red on main). The hour stays fixed.
        self.now = datetime.now(timezone.utc).replace(hour=6, minute=30, second=0, microsecond=0)

    def __call__(self) -> str:
        return self.now.isoformat()


def _core(tmp_path: Path) -> tuple[Rig, str, dict[str, Any]]:
    """A YOLO Program whose step 1 touched a file no step owns: a core question."""
    rig = Rig(tmp_path)
    pid = rig.service.create(OWNER, title="Overnight on the home box", goal="Stop the stalls.",
                             repository=str(rig.repo), check_command=f"sh {FAKE_CHECK}", template="fast-cycle",
                             control="yolo")["id"]
    rig.service.plan(OWNER, pid, steps=[{"title": "Owned", "brief": "Store the stall reason.", "owns": ["src/a.py"]}])
    rig.service.start(OWNER, pid)
    step = rig.step(pid, 1)
    rig.agent.finish(step["launch_id"], {"src/a.py": "a\n", "other/b.py": "b\n"})
    rig.tick()
    items = rig.service.needs_you_items()
    assert [item["kind"] for item in items] == ["core"], items
    return rig, pid, items[0]


def _briefing(rig: Rig, clock: Clock | None = None) -> BriefingService:
    return BriefingService(rig.db, programs=lambda: rig.service, clock=clock or Clock())


def _ref(pid: str, item: dict[str, Any]) -> str:
    return f"program:{pid}:{item['id']}"


def test_the_token_is_32_random_bytes_and_only_its_hash_is_stored(tmp_path) -> None:
    rig, pid, item = _core(tmp_path)
    made = _briefing(rig).make(OWNER, [_ref(pid, item)])
    token = made["token"]
    assert len(token) == 43 and is_token(token) and made["path"] == f"/b/{token}"
    assert len({mint_token() for _ in range(50)}) == 50
    assert token_hash(token) == hashlib.sha256(token.encode()).hexdigest()
    with rig.db._connection() as conn:
        rows = [dict(row) for row in conn.execute("SELECT * FROM briefing_packages").fetchall()]
    assert len(rows) == 1 and rows[0]["token_hash"] == token_hash(token)
    assert token not in json.dumps(rows), "the token itself is stored"


def test_a_core_question_reads_many_and_is_decided_once_from_the_page(tmp_path) -> None:
    rig, pid, item = _core(tmp_path)
    briefing = _briefing(rig)
    made = briefing.make(OWNER, [_ref(pid, item)])
    for _ in range(3):
        page = briefing.read(made["token"])
    shown = page["items"][0]
    assert page["package"]["head"] == "Overnight on the home box · step 1"
    assert shown["state"] == "open" and shown["kind_words"] == "Core question" and shown["level"] == "YOLO"
    # The owner's BRIEF RULE (2026-10-31): the goal, the step, what happened
    # in plain words, then the question in one sentence.
    assert shown["note"] == ["Goal: Stop the stalls.", "Step 1, “Owned”: Store the stall reason.",
                             "The step's change touches files no step owns (b.py)."]
    assert shown["question"] == "Let the step go on with this, or park it?"
    assert [(c["id"], c["label"]) for c in shown["choices"]] == [("go_on", "Go on"), ("park", "Park")]
    assert all(c["consequence"] for c in shown["choices"])
    assert page["package"]["expires_words"] == "Expires in 24 h"
    assert [row["id"] for row in page["later"]] == ["in_1h", "at_13", "tonight", "tomorrow"]
    # The Program window and Needs you say a page is open for the item.
    turn = rig.program(pid)["your_turn_items"]
    assert turn[0]["page"]["package_id"] == made["id"]

    answered = briefing.answer(made["token"], _ref(pid, item), "go_on")
    assert answered["item"]["state"] == "decided"
    # It settles to one line (rule 3).
    assert re.fullmatch(r"Go on · \d\d:\d\d\. The step goes on\. Nothing else waits on you\.",
                        answered["item"]["outcome"]["words"]), answered["item"]["outcome"]
    lines = [row for row in rig.program(pid)["checkpoints"] if row.get("via") == "page"]
    assert lines and lines[0]["line"].endswith("· decided from the briefing page"), lines
    assert lines[0]["line"].startswith("Go on: ")
    assert "core" not in [row["kind"] for row in rig.service.needs_you_items()]

    with pytest.raises(BriefingRefused) as again:
        briefing.answer(made["token"], _ref(pid, item), "park")
    assert again.value.code == "answered_already"
    assert briefing.read(made["token"])["items"][0]["state"] == "decided"  # still readable, no verbs


def test_expired_revoked_and_unknown_tokens_read_nothing_the_same_way(tmp_path) -> None:
    rig, pid, item = _core(tmp_path)
    clock = Clock()
    briefing = _briefing(rig, clock)
    first = briefing.make(OWNER, [_ref(pid, item)])
    second = briefing.make(OWNER, [_ref(pid, item)])
    briefing.revoke(OWNER, second["id"])
    answers = []
    for token in (second["token"], mint_token(), "short", "x" * 43 + "/"):
        with pytest.raises(BriefingRefused) as refused:
            briefing.read(token)
        answers.append((refused.value.code, refused.value.detail, refused.value.context))
    clock.now += timedelta(hours=24, seconds=1)
    with pytest.raises(BriefingRefused) as expired:
        briefing.read(first["token"])
    answers.append((expired.value.code, expired.value.detail, expired.value.context))
    assert len(set(json.dumps(a) for a in answers)) == 1, answers
    assert answers[0][:2] == ("page_expired", "This page has expired.")
    with pytest.raises(BriefingRefused):
        briefing.answer(first["token"], _ref(pid, item), "go_on")
    # Nothing was decided.
    assert [row["kind"] for row in rig.service.needs_you_items()] == ["core"]


def test_later_records_the_next_touch_and_decides_nothing(tmp_path) -> None:
    rig, pid, item = _core(tmp_path)
    briefing = _briefing(rig)
    made = briefing.make(OWNER, [_ref(pid, item)])
    later = briefing.answer(made["token"], _ref(pid, item), "later", later="at_13")
    assert later["item"]["state"] == "later"
    assert later["item"]["outcome"]["words"] == "Later · back at " + later_until(
        "at_13", Clock().now).astimezone().strftime("%H:%M") + "."
    assert [row["kind"] for row in rig.service.needs_you_items()] == ["core"]
    with pytest.raises(BriefingRefused) as bad:
        briefing.answer(made["token"], _ref(pid, item), "later", later="after the standup")
    assert bad.value.code == "later_invalid"
    # Later changes nothing: he can still decide on the page.
    assert briefing.answer(made["token"], _ref(pid, item), "park")["item"]["state"] == "decided"


def test_an_item_answered_on_the_desk_first_is_answered_already_on_the_page(tmp_path) -> None:
    rig, pid, item = _core(tmp_path)
    briefing = _briefing(rig)
    made = briefing.make(OWNER, [_ref(pid, item)])
    rig.service.decide(OWNER, pid, item["step_id"], kind="core", choice="go_on")
    assert briefing.read(made["token"])["items"][0]["state"] == "gone"
    with pytest.raises(BriefingRefused) as refused:
        briefing.answer(made["token"], _ref(pid, item), "park")
    assert refused.value.code == "answered_already"
    desk = [row for row in rig.program(pid)["checkpoints"] if row["line"].startswith("Go on: ")]
    assert desk and desk[0].get("via") is None and "briefing" not in desk[0]["line"]


def test_only_the_owner_makes_or_revokes_and_a_bad_ref_is_refused(tmp_path) -> None:
    rig, pid, item = _core(tmp_path)
    briefing = _briefing(rig)
    with pytest.raises(BriefingRefused) as agent:
        briefing.make(AGENT, [_ref(pid, item)])
    assert agent.value.code == "owner_only"
    for refs, code in (([f"program:{pid}:nothing"], "not_waiting"), (["decision:1"], "not_waiting"),  # DIR10: a decision is a source; this one does not exist
                       ([_ref(pid, item), _ref(pid, item)], "refs_invalid")):
        with pytest.raises(BriefingRefused) as refused:
            briefing.make(OWNER, refs)
        assert refused.value.code == code
    with pytest.raises(BriefingRefused) as phone:
        briefing.make(OWNER, [_ref(pid, item)], send="phone")
    assert phone.value.code == "send_unavailable"
    # DIR5: send telegram needs a paired chat (this HOME has none).
    with pytest.raises(Exception) as telegram:
        briefing.make(OWNER, [_ref(pid, item)], send="telegram")
    assert telegram.value.code == "telegram_not_paired"
    made = briefing.make(OWNER, [_ref(pid, item)])
    with pytest.raises(BriefingRefused):
        briefing.revoke(AGENT, made["id"])
    assert [row["id"] for row in briefing.packages(OWNER, pid)] == [made["id"]]
    briefing.revoke(OWNER, made["id"])
    assert briefing.packages(OWNER, pid) == []
    assert "page" not in rig.program(pid)["your_turn_items"][0]


def test_program_decide_names_its_channel_and_refuses_an_unknown_one(tmp_path) -> None:
    rig, pid, item = _core(tmp_path)
    with pytest.raises(ProgramRefused) as refused:
        rig.service.decide(OWNER, pid, item["step_id"], kind="core", choice="go_on", via="fax")
    assert refused.value.code == "via_invalid"
    rig.service.decide(OWNER, pid, item["step_id"], kind="core", choice="go_on", via="call")
    line = next(row for row in rig.program(pid)["checkpoints"] if row["line"].startswith("Go on: "))
    assert line["via"] == "call" and line["line"].endswith("· decided on a call")


# ── the edge ────────────────────────────────────────────────────────


def test_the_briefing_exception_admits_exactly_the_page_routes() -> None:
    token = mint_token()
    assert briefing_route("GET", f"/api/b/{token}")
    assert briefing_route("POST", f"/api/b/{token}/answer")
    assert briefing_route("GET", f"/api/b/{token}/evidence/program:p:s:core/log")
    for verb, path in (("POST", f"/api/b/{token}"), ("GET", f"/api/b/{token}/answer"),
                       ("DELETE", f"/api/b/{token}"), ("GET", "/api/b/short"), ("GET", f"/api/b/{token}/other"),
                       ("GET", f"/api/b/{token}x"), ("POST", f"/api/b/{token}/answer/x"),
                       ("GET", f"/api/programs/{token}")):
        assert not briefing_route(verb, path), (verb, path)
    assert required_right("GET", f"/api/b/{token}") is None
    assert required_right("POST", "/api/reach/packages") is PrincipalRight.OWNER
    assert required_right("POST", "/api/reach/packages/pkg-1/revoke") is PrincipalRight.OWNER
    briefing = Principal(PrincipalKind.BRIEFING, "pkg-1")
    assert briefing.permits(PrincipalRight.BRIEFING_ANSWER)
    assert not any(briefing.permits(right) for right in PrincipalRight if right is not PrincipalRight.BRIEFING_ANSWER)


#: The routes the edge admits with no right at all (their own handlers judge).
_PUBLIC = {"/health", "/api/devices/audio", "/api/mesh/info", "/api/calls/line/enrol", "/api/mcp"}


def test_a_page_token_reaches_no_other_route(tmp_path, monkeypatch) -> None:
    """The census: every ``/api`` route of the real app, called with a page
    token as the bearer, as ``?token=`` and as each path parameter, is refused
    at the edge (401), except the page's own three routes."""
    pytest.importorskip("fastapi.testclient")
    from fastapi.routing import APIRoute
    from fastapi.testclient import TestClient

    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    rig, pid, item = _core(tmp_path)
    briefing = _briefing(rig)
    token = briefing.make(OWNER, [_ref(pid, item)])["token"]
    server = MeetingWebServer(WebRuntimeCallbacks(on_bookmark=lambda *_a, **_k: None,
                                                  on_stop=lambda *_a, **_k: None, get_state=lambda: None),
                              host="127.0.0.1")
    client = TestClient(server.app)
    client.headers.pop("X-HoldSpeak-Token", None)  # the harness's owner header (tests/conftest.py)
    walked, own = 0, 0
    for route in server.app.routes:
        if not isinstance(route, APIRoute) or not route.path.startswith("/api/"):
            continue
        path = route.path
        for name in route.param_convertors:
            path = path.replace("{" + name + ":path}", token).replace("{" + name + "}", token)
        for verb in sorted(route.methods - {"HEAD", "OPTIONS"}):
            if briefing_route(verb, path):
                own += 1
                continue
            if route.path in _PUBLIC:
                continue
            answer = client.request(verb, f"{path}?token={token}", headers={"Authorization": f"Bearer {token}"})
            walked += 1
            if phone_device_route(verb, path):
                # Admitted at the edge for a paired phone; its handler refuses the page token.
                assert answer.status_code >= 400, f"{verb} {route.path}: {answer.status_code}"
                continue
            assert required_right(verb, path) is not None, f"{verb} {route.path} is open at the edge"
            assert answer.status_code in (401, 403), f"{verb} {route.path}: {answer.status_code}"
    assert own == 3, own
    assert walked > 300, walked


# ── never in a log, a frame or an egress call ───────────────────────


def test_the_token_is_never_logged_framed_or_sent(tmp_path, monkeypatch, caplog) -> None:
    pytest.importorskip("fastapi.testclient")
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from holdspeak.kernel import external_egress
    from holdspeak.runtime import composition
    from holdspeak.web import announce
    from holdspeak.web.routes.briefing import PAGE_HEADERS, build_briefing_router

    rig, pid, item = _core(tmp_path)
    briefing = _briefing(rig)
    monkeypatch.setattr(briefing_module, "default_briefing_service", lambda db=None: briefing)
    monkeypatch.setenv("HOLDSPEAK_RECORDINGS", "off")  # no Tailscale read for the link
    frames: list[tuple[str, str, str]] = []
    monkeypatch.setattr(composition, "notify_desk_changed", lambda *args: frames.append(tuple(map(str, args))))
    sent: list[Any] = []
    monkeypatch.setattr(external_egress, "run_external_egress", lambda *a, **k: sent.append((a, k)))
    app = FastAPI()
    announced: list[tuple[str, str, str]] = []

    @app.middleware("http")
    async def _owner(request, call_next):  # the edge sets the owner for /api/reach
        request.state.principal = OWNER
        return await call_next(request)

    monkeypatch.setattr(announce, "announce_scope", _recording_scope(announced))
    announce.install(app)
    app.include_router(build_briefing_router(None))  # type: ignore[arg-type]
    client = TestClient(app)
    caplog.set_level(logging.DEBUG)

    made = client.post("/api/reach/packages", json={"refs": [_ref(pid, item)]})
    assert made.status_code == 201, made.text
    token = made.json()["token"]
    shell = client.get(f"/b/{token}")
    read = client.get(f"/api/b/{token}")
    pane = client.get(f"/api/b/{token}/evidence/{_ref(pid, item)}/text")
    answer = client.post(f"/api/b/{token}/answer", json={"ref": _ref(pid, item), "choice": "go_on"})
    again = client.post(f"/api/b/{token}/answer", json={"ref": _ref(pid, item), "choice": "park"})
    gone = client.get(f"/api/b/{mint_token()}")
    assert (read.status_code, pane.status_code, answer.status_code, again.status_code, gone.status_code) == (
        200, 200, 200, 409, 404)
    assert "Overnight on the home box" in pane.json()["text"]
    assert again.json()["code"] == "answered_already"
    for response in (shell, read, pane, answer, again, gone):
        for key, value in PAGE_HEADERS.items():
            assert response.headers.get(key) == value, (key, response.url)
        assert "set-cookie" not in response.headers
    assert ("POST", "/api/b/{token}/answer") in announce.QUIET_ROUTES
    assert frames and all(token not in " ".join(frame) for frame in frames), frames
    assert "reach" in {frame[0] for frame in frames}
    assert announced and all(token not in " ".join(frame) for frame in announced), announced
    assert not sent, "the page sent something out"
    # Every hub log line (the test client's own httpx line is the browser's side).
    leaked = [f"{record.name}: {record.getMessage()}" for record in caplog.records
              if token in record.getMessage() and not record.name.startswith("httpx")]
    assert not leaked, leaked


def test_the_hub_keeps_no_access_log() -> None:
    """§6 "Never in a log": the hub's server runs with its access log off, so
    a page path (it carries the token) is never written by uvicorn."""
    import inspect

    from holdspeak import web_server

    assert "access_log=False" in inspect.getsource(web_server.MeetingWebServer)


def _recording_scope(out: list[tuple[str, str, str]]) -> Any:
    from contextlib import contextmanager

    @contextmanager
    def scope():
        yield lambda *args: out.append(tuple(map(str, args)))

    return scope


def test_ten_wrong_tokens_a_minute_are_refused_for_a_minute(tmp_path, monkeypatch) -> None:
    pytest.importorskip("fastapi.testclient")
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from holdspeak.web.routes.briefing import build_briefing_router

    rig, pid, item = _core(tmp_path)
    briefing = _briefing(rig)
    monkeypatch.setattr(briefing_module, "default_briefing_service", lambda db=None: briefing)
    monkeypatch.setattr(briefing_module, "MISSES", briefing_module._Misses())
    token = briefing.make(OWNER, [_ref(pid, item)])["token"]
    app = FastAPI()
    app.include_router(build_briefing_router(None))  # type: ignore[arg-type]
    client = TestClient(app)
    assert [client.get(f"/api/b/{mint_token()}").status_code for _ in range(10)] == [404] * 10
    assert client.get(f"/api/b/{token}").status_code == 429
