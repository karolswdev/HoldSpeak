"""PG-DIRECTION DIR1 on the Programs rig: the briefing page's routes, end to end.

A rig Program's core question; the owner's ``POST /api/reach/packages`` makes
its page (the token is in that answer only); ``GET /b/<token>`` serves the
page shell; ``GET /api/b/<token>`` reads the package many times; ``POST
/api/b/<token>/answer`` decides it once through ``program.decide`` with
``via=page`` (the ledger line says "decided from the briefing page"); a
second answer is "answered already"; a revoked and an expired token read
nothing; the Program window and the Needs you row say a page is open until
it is answered or revoked.

The face half replays the answers recorded here
(``web/src/briefing/__fixtures__/reach.page.json`` and
``web/src/desk/programs/__fixtures__/program.page_open.json``;
``HOLDSPEAK_WIRE_WRITE=1`` rewrites them, else this test fences their shape).
"""
from __future__ import annotations

import json
import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.testclient import TestClient

from holdspeak.services import briefing_service as briefing_module
from holdspeak.services import program_service as program_module
from holdspeak.services.briefing_service import BriefingService
from holdspeak.services.needs_you_membership import program_items
from holdspeak.web.routes.briefing import build_briefing_router
from holdspeak.web.routes.programs import build_programs_router
from tests.integration.program_rig import FAKE_CHECK, OWNER, Rig

ROOT = Path(__file__).resolve().parents[2]
PAGE_FIXTURES = ROOT / "web" / "src" / "briefing" / "__fixtures__"
PROGRAM_FIXTURES = ROOT / "web" / "src" / "desk" / "programs" / "__fixtures__"
#: The recorded token: the fixtures never carry a real one.
RECORDED_TOKEN = "Rec0rdedPageT0kenRec0rdedPageT0kenRec0rdedX"


class Clock:
    def __init__(self) -> None:
        self.now = datetime(2026, 10, 31, 6, 30, tzinfo=timezone.utc)

    def __call__(self) -> str:
        return self.now.isoformat()


def _shape(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _shape(item) for key, item in sorted(value.items())}
    if isinstance(value, list):
        return [_shape(value[0])] if value else []
    return type(value).__name__


def _fixture(path: Path, answer: Any, tmp_path: Path, token: str) -> Any:
    """The hub's own answer, stored for the face (never typed by hand)."""
    text = json.dumps(answer).replace(token, RECORDED_TOKEN)
    text = re.sub(re.escape(str(tmp_path)), "/tmp/rig", text).replace(str(ROOT), "/repo")
    scrubbed = json.loads(text)
    if os.environ.get("HOLDSPEAK_WIRE_WRITE") == "1":
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(scrubbed, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    assert path.exists(), f"no stored answer {path}; run with HOLDSPEAK_WIRE_WRITE=1"
    assert _shape(json.loads(path.read_text())) == _shape(scrubbed), f"{path.name}: not the hub's shape"
    return scrubbed


def _rig(tmp_path: Path, monkeypatch, clock: Clock) -> tuple[Rig, str, TestClient]:
    rig = Rig(tmp_path)
    pid = rig.service.create(OWNER, title="Overnight on the home box", goal="Stop the stalls.",
                             repository=str(rig.repo), check_command=f"sh {FAKE_CHECK}", template="fast-cycle",
                             control="yolo")["id"]
    rig.service.plan(OWNER, pid, steps=[{"title": "Store the stall reason", "brief": "Store the stall reason in its "
                                         "own column.\nKeep the old reads.", "owns": ["src/a.py"]}])
    rig.service.start(OWNER, pid)
    step = rig.step(pid, 1)
    rig.agent.finish(step["launch_id"], {"src/a.py": "a\n", "holdspeak/db/schema.py": "b\n"})
    rig.tick()
    briefing = BriefingService(rig.db, programs=lambda: rig.service, clock=clock)
    monkeypatch.setattr(program_module, "default_program_service", lambda db=None: rig.service)
    monkeypatch.setattr(briefing_module, "default_briefing_service", lambda db=None: briefing)
    monkeypatch.setattr(briefing_module, "MISSES", briefing_module._Misses())
    monkeypatch.setattr(briefing_module, "hub_name", lambda: "the rig hub")
    monkeypatch.setenv("HOLDSPEAK_RECORDINGS", "off")  # the rig reads no Tailscale
    app = FastAPI()

    @app.middleware("http")
    async def _edge(request, call_next):
        # The page routes carry no owner; every other route here is his.
        if not request.url.path.startswith(("/b/", "/api/b/")):
            request.state.principal = OWNER
        return await call_next(request)

    app.include_router(build_programs_router(None))  # type: ignore[arg-type]
    app.include_router(build_briefing_router(None))  # type: ignore[arg-type]
    return rig, pid, TestClient(app)


def test_the_page_reads_a_core_question_and_decides_it_once(tmp_path, monkeypatch) -> None:
    clock = Clock()
    rig, pid, client = _rig(tmp_path, monkeypatch, clock)
    before = client.get(f"/api/programs/{pid}").json()
    item = next(row for row in before["your_turn_items"] if row["kind"] == "core")
    assert "page" not in item
    ref = f"program:{pid}:{item['id']}"
    needs_before = program_items(rig.service.needs_you_items())
    assert needs_before[0]["id"] == ref and "page" not in needs_before[0]["program"]
    made = client.post("/api/reach/packages", json={"refs": [ref]})
    assert made.status_code == 201, made.text
    token = made.json()["token"]
    assert made.json()["path"] == f"/b/{token}"
    assert made.json()["link"] is None  # a rig reads no Tailscale; the desk joins its own origin
    _fixture(PROGRAM_FIXTURES / "program.page_none.json", before, tmp_path, token)
    _fixture(PROGRAM_FIXTURES / "needs_you.page_none.json", {"items": needs_before}, tmp_path, token)
    _fixture(PROGRAM_FIXTURES / "reach.package.json", made.json(), tmp_path, token)

    shell = client.get(f"/b/{token}")
    assert shell.status_code == 200 and "<html" in shell.text.lower()
    assert client.get(f"/b/{briefing_module.mint_token()}").status_code == 404

    opened = client.get(f"/api/b/{token}").json()
    assert opened["items"][0]["state"] == "open"
    assert opened["items"][0]["question"].startswith("Step 1 asks you: it touches files no step owns")
    assert [pane["pane"] for pane in opened["items"][0]["evidence"]] == ["log", "brief", "text"]

    # The desk says the page is open: the Program window and the Needs you row.
    program = client.get(f"/api/programs/{pid}").json()
    turn = next(row for row in program["your_turn_items"] if row["kind"] == "core")
    assert turn["page"]["package_id"] == made.json()["id"]
    needs = program_items(rig.service.needs_you_items())
    assert needs[0]["id"] == ref and needs[0]["program"]["page"]["package_id"] == made.json()["id"]
    _fixture(PROGRAM_FIXTURES / "program.page_open.json", program, tmp_path, token)
    _fixture(PROGRAM_FIXTURES / "needs_you.page_open.json", {"items": needs}, tmp_path, token)

    brief = client.get(f"/api/b/{token}/evidence/{ref}/brief").json()
    assert brief["kind"] == "code" and brief["text"].startswith("Store the stall reason")
    text = client.get(f"/api/b/{token}/evidence/{ref}/text").json()
    assert "Overnight on the home box" in text["text"]
    log = client.get(f"/api/b/{token}/evidence/{ref}/log").json()
    assert log["kind"] == "code" and log["text"]
    assert client.get(f"/api/b/{token}/evidence/{ref}/pr").status_code == 404  # no PR yet

    later = client.post(f"/api/b/{token}/answer", json={"ref": ref, "choice": "later", "later": "at_13"}).json()
    assert later["item"]["state"] == "later" and later["item"]["outcome"]["words"].startswith("Later · back at ")
    decided = client.post(f"/api/b/{token}/answer", json={"ref": ref, "choice": "go_on"})
    assert decided.status_code == 200, decided.text
    assert decided.json()["item"]["outcome"]["words"].startswith("Go on · decided here · ")
    again = client.post(f"/api/b/{token}/answer", json={"ref": ref, "choice": "park"})
    assert again.status_code == 409 and again.json()["code"] == "answered_already"
    after = client.get(f"/api/b/{token}").json()
    assert after["items"][0]["state"] == "decided"

    ledger = client.get(f"/api/programs/{pid}").json()
    line = next(row for row in ledger["checkpoints"] if row["line"].startswith("Go on: "))
    assert line["via"] == "page" and line["line"].endswith("· decided from the briefing page")
    assert not any(row.get("page") for row in ledger["your_turn_items"])

    clock.now += timedelta(hours=24, seconds=1)
    expired = client.get(f"/api/b/{token}")
    assert expired.status_code == 404 and expired.json()["code"] == "page_expired"
    assert set(expired.json()) == {"error", "code", "detail"}  # no data

    _fixture(PAGE_FIXTURES / "reach.page.json", {
        "made": made.json(), "open": opened, "later": later, "decided": decided.json(), "again": again.json(),
        "after": after, "expired": expired.json(), "brief": brief, "text": text, "log": log,
    }, tmp_path, token)


def test_a_revoked_page_reads_nothing_and_leaves_the_item_held(tmp_path, monkeypatch) -> None:
    clock = Clock()
    rig, pid, client = _rig(tmp_path, monkeypatch, clock)
    item = next(row for row in rig.service.needs_you_items() if row["kind"] == "core")
    ref = f"program:{pid}:{item['id']}"
    made = client.post("/api/reach/packages", json={"refs": [ref]}).json()
    listed = client.get(f"/api/reach/packages?program_id={pid}").json()["packages"]
    assert [row["id"] for row in listed] == [made["id"]] and "token" not in json.dumps(listed)
    opened = client.get(f"/api/programs/{pid}").json()
    _fixture(PROGRAM_FIXTURES / "program.revoke_open.json", opened, tmp_path, made["token"])
    revoked = client.post(f"/api/reach/packages/{made['id']}/revoke").json()
    assert revoked == {"id": made["id"], "revoked": True}
    after = client.get(f"/api/programs/{pid}").json()
    assert not any(row.get("page") for row in after["your_turn_items"])
    _fixture(PROGRAM_FIXTURES / "reach.revoked.json", revoked, tmp_path, made["token"])
    _fixture(PROGRAM_FIXTURES / "program.page_revoked.json", after, tmp_path, made["token"])
    assert client.get(f"/api/b/{made['token']}").status_code == 404
    assert client.post(f"/api/b/{made['token']}/answer", json={"ref": ref, "choice": "go_on"}).status_code == 404
    assert client.get(f"/b/{made['token']}").status_code == 404
    assert [row["kind"] for row in rig.service.needs_you_items()] == ["core"]
    assert client.get(f"/api/reach/packages?program_id={pid}").json() == {"packages": []}
