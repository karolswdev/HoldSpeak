"""The Walk (2026-11-07): one link, one guided feedback walk on the desk.

The owner's ``POST /api/walks`` stores a script and answers a token once;
``GET /w/<token>`` sends the desk to ``/?walk=<token>``; a wrong token gets
the desk shell with 404; ``GET /api/w/<token>`` reads the script and the
answers; ``POST /api/w/<token>/answer`` stores a choice and the window PNG
in the feedback folder; ``GET /api/walks/<id>`` gives the owner everything.

The desk half replays the answers recorded here
(``web/src/desk/walk/__fixtures__/walk.page.json`` and ``walk.answer.json``;
``HOLDSPEAK_WIRE_WRITE=1`` rewrites them, else this test fences their shape).
"""
from __future__ import annotations

import base64
import json
import os
import struct
import zlib
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.testclient import TestClient

from holdspeak import principals
from holdspeak.principals import Principal, PrincipalKind, PrincipalRight
from holdspeak.services import briefing_service as briefing_module
from holdspeak.services import walk_service as walk_module
from holdspeak.services.walk_service import WalkService
from holdspeak.web.routes.walks import build_walks_router

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "web" / "src" / "desk" / "walk" / "__fixtures__"
RECORDED_TOKEN = "Rec0rdedWalkT0kenRec0rdedWalkT0kenRec0rdedX"
OWNER = Principal(PrincipalKind.OWNER, "owner-session")

SCRIPT = {
    "title": "Wave two",
    "steps": [
        {"open": {"app": "surface-programs"}},
        {"highlight": {"target": "programs-new", "words": "Press New program. The well opens."}},
        {"highlight": {"target": "programs-make-rows", "words": "The project rows."},
         "ask": {"ref": "s11-well", "question": "Does the well read clearly?", "choices": ["Keep", "Redo"]}},
        {"open": {"app": "chair:needs"},
         "highlight": {"target": "needs-open-people", "words": "People, in the toolbar."},
         "ask": {"ref": "needs-coverage", "question": "Is the line clear?", "choices": ["Keep", "Redo"]}},
    ],
}


def _png() -> bytes:
    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)

    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(b"\x00\x34\x56\x78")) + chunk(b"IEND", b""))


def _shape(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _shape(item) for key, item in sorted(value.items())}
    if isinstance(value, list):
        return [_shape(value[0])] if value else []
    return type(value).__name__


def _fixture(name: str, answer: Any, token: str) -> None:
    """The hub's own answer, stored for the desk test (never typed by hand)."""
    scrubbed = json.loads(json.dumps(answer).replace(token, RECORDED_TOKEN))
    path = FIXTURES / name
    if os.environ.get("HOLDSPEAK_WIRE_WRITE") == "1":
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(scrubbed, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    assert path.exists(), f"no stored answer {path}; run with HOLDSPEAK_WIRE_WRITE=1"
    assert _shape(json.loads(path.read_text())) == _shape(scrubbed), f"{name}: not the hub's shape"


def _client(tmp_path: Path, monkeypatch) -> tuple[TestClient, WalkService]:
    service = WalkService(home=tmp_path)
    monkeypatch.setattr(walk_module, "default_walk_service", lambda: service)
    monkeypatch.setattr(briefing_module, "MISSES", briefing_module._Misses())
    app = FastAPI()

    @app.middleware("http")
    async def _edge(request, call_next):
        # The walk's token routes carry no owner; every other route here is his.
        if not request.url.path.startswith(("/w/", "/api/w/")):
            request.state.principal = OWNER
        return await call_next(request)

    app.include_router(build_walks_router(None))  # type: ignore[arg-type]
    return TestClient(app, follow_redirects=False), service


def test_a_walk_is_made_served_by_its_token_and_answered(tmp_path, monkeypatch) -> None:
    client, service = _client(tmp_path, monkeypatch)
    made = client.post("/api/walks", json=SCRIPT)
    assert made.status_code == 201, made.text
    body = made.json()
    token, walk_id = body["token"], body["id"]
    assert len(token) == 43 and body["url_path"] == f"/w/{token}"

    served = client.get(f"/w/{token}")
    assert served.status_code == 303
    assert served.headers["location"] == f"/?walk={token}"
    assert served.headers["cache-control"] == "no-store"

    page = client.get(f"/api/w/{token}")
    assert page.status_code == 200
    read = page.json()
    assert read["title"] == "Wave two" and len(read["steps"]) == 4 and read["answers"] == {}
    assert "token_sha256" not in json.dumps(read) and "id" not in read
    _fixture("walk.page.json", read, token)

    png = _png()
    answered = client.post(f"/api/w/{token}/answer", json={
        "ref": "s11-well", "choice": "Redo", "words": "The project name is cut.",
        "window_png": base64.b64encode(png).decode("ascii"),
    })
    assert answered.status_code == 200, answered.text
    receipt = answered.json()
    assert receipt["ref"] == "s11-well" and receipt["choice"] == "Redo" and receipt["shot"] == "s11-well.png"
    _fixture("walk.answer.json", receipt, token)

    # The PNG lands where feedback bundles land: the feedback folder.
    shot = tmp_path / ".local" / "share" / "holdspeak" / "feedback" / "walks" / walk_id / "s11-well.png"
    assert shot.read_bytes() == png

    # Skip is always a choice; a second answer keeps the first answer's text
    # and replaces its image (one image per question).
    assert client.post(f"/api/w/{token}/answer", json={"ref": "needs-coverage", "choice": "skip"}).status_code == 200
    again = client.post(f"/api/w/{token}/answer", json={
        "ref": "s11-well", "choice": "Keep", "window_png": base64.b64encode(png).decode("ascii")})
    assert again.json()["shot"] == "s11-well.png"

    owner = client.get(f"/api/walks/{walk_id}")
    assert owner.status_code == 200
    full = owner.json()
    assert full["answers"]["s11-well"]["choice"] == "Keep"
    assert full["answers"]["s11-well"]["earlier"][0]["words"] == "The project name is cut."
    assert "shot" not in full["answers"]["s11-well"]["earlier"][0]
    assert full["answers"]["needs-coverage"]["choice"] == "skip"
    assert full["directory"].endswith(walk_id) and "token_sha256" not in full
    assert client.get(f"/api/w/{token}").json()["answers"]["s11-well"]["choice"] == "Keep"


def test_words_without_a_pressed_choice_are_stored_as_words_never_as_a_choice(tmp_path, monkeypatch) -> None:
    # First run 2026-11-07: every answer came back "Keep" while his words said
    # no. Words he sends without a choice are stored as the choice "words".
    client, _service = _client(tmp_path, monkeypatch)
    made = client.post("/api/walks", json=SCRIPT).json()
    token, walk_id = made["token"], made["id"]
    sent = client.post(f"/api/w/{token}/answer", json={"ref": "s11-well", "choice": "words",
                                                       "words": "No, broken."})
    assert sent.status_code == 200, sent.text
    assert sent.json()["choice"] == "words" and sent.json()["words"] == "No, broken."
    assert client.get(f"/api/walks/{walk_id}").json()["answers"]["s11-well"] == {
        "choice": "words", "words": "No, broken.", "at": sent.json()["at"]}
    # "words" with no words is no answer.
    empty = client.post(f"/api/w/{token}/answer", json={"ref": "needs-coverage", "choice": "words", "words": " "})
    assert empty.status_code == 422 and empty.json()["code"] == "walk_words_empty"


def test_a_wrong_token_reads_nothing_and_a_bad_answer_is_refused(tmp_path, monkeypatch) -> None:
    client, _service = _client(tmp_path, monkeypatch)
    token = client.post("/api/walks", json=SCRIPT).json()["token"]
    wrong = "x" * 43

    shell = client.get(f"/w/{wrong}")
    assert shell.status_code == 404 and "location" not in shell.headers
    assert client.get(f"/api/w/{wrong}").status_code == 404
    assert client.post(f"/api/w/{wrong}/answer", json={"ref": "s11-well", "choice": "Keep"}).status_code == 404
    assert client.get("/api/walks/" + "0" * 32).status_code == 404

    unknown_ref = client.post(f"/api/w/{token}/answer", json={"ref": "nope", "choice": "Keep"})
    assert unknown_ref.status_code == 422 and unknown_ref.json()["code"] == "walk_unknown_ask"
    unknown_choice = client.post(f"/api/w/{token}/answer", json={"ref": "s11-well", "choice": "Maybe"})
    assert unknown_choice.status_code == 422
    bad_png = client.post(f"/api/w/{token}/answer", json={
        "ref": "s11-well", "choice": "Keep", "window_png": base64.b64encode(b"not png").decode("ascii")})
    assert bad_png.status_code == 422 and bad_png.json()["code"] == "walk_shot_invalid"

    for script in ({}, {"title": "x", "steps": []}, {"title": "x", "steps": [{"press": "a"}]},
                   {"title": "x", "steps": [{"ask": {"ref": "a", "question": "q", "choices": []}}]}):
        assert client.post("/api/walks", json=script).status_code == 422


def test_the_edge_admits_the_walk_token_on_its_two_routes_only() -> None:
    token = "A" * 43
    assert principals.required_right("GET", f"/api/w/{token}") is None
    assert principals.required_right("POST", f"/api/w/{token}/answer") is None
    assert principals.required_right("POST", f"/api/w/{token}") is PrincipalRight.OWNER
    assert principals.required_right("GET", f"/api/w/{token}/answer") is PrincipalRight.OWNER
    assert principals.required_right("GET", f"/api/w/{token}/other") is PrincipalRight.OWNER
    assert principals.required_right("POST", "/api/walks") is PrincipalRight.OWNER
    assert principals.required_right("GET", "/api/walks/" + "0" * 32) is PrincipalRight.OWNER


# ── the bounds (Codex review of #1808) ──────────────────────────────


def _b64(raw: bytes) -> str:
    return base64.b64encode(raw).decode("ascii")


def test_one_walk_keeps_one_image_per_question_five_earlier_texts_and_a_byte_budget(tmp_path, monkeypatch) -> None:
    client, _service = _client(tmp_path, monkeypatch)
    made = client.post("/api/walks", json=SCRIPT).json()
    token, walk_id = made["token"], made["id"]
    folder = tmp_path / ".local" / "share" / "holdspeak" / "feedback" / "walks" / walk_id
    png = _png()

    for number in range(8):
        answered = client.post(f"/api/w/{token}/answer", json={
            "ref": "s11-well", "choice": "Redo", "words": f"Try {number}.", "window_png": _b64(png)})
        assert answered.status_code == 200 and answered.json()["shot"] == "s11-well.png", answered.text
    assert sorted(entry.name for entry in folder.glob("*.png")) == ["s11-well.png"]
    stored = client.get(f"/api/walks/{walk_id}").json()["answers"]["s11-well"]
    assert stored["words"] == "Try 7."
    assert [row["words"] for row in stored["earlier"]] == [f"Try {n}." for n in range(2, 7)]
    assert walk_module.MAX_EARLIER == 5 and walk_module.WALK_BYTES == 64 * 1024 * 1024

    # Past the walk's byte budget an image is refused by name; the text lands.
    monkeypatch.setattr(walk_module, "WALK_BYTES", len(png) + 10)
    full = client.post(f"/api/w/{token}/answer", json={
        "ref": "needs-coverage", "choice": "Keep", "words": "Clear.", "window_png": _b64(png)})
    assert full.status_code == 200, full.text
    receipt = full.json()
    assert receipt["choice"] == "Keep" and "shot" not in receipt
    assert receipt["shot_refused"]["code"] == "walk_shot_budget"
    assert not (folder / "needs-coverage.png").exists()
    assert client.get(f"/api/walks/{walk_id}").json()["answers"]["needs-coverage"]["words"] == "Clear."
    # Its own image is replaced, so the same question still fits the budget.
    assert client.post(f"/api/w/{token}/answer", json={
        "ref": "s11-well", "choice": "Keep", "window_png": _b64(png)}).json()["shot"] == "s11-well.png"


def test_the_answer_route_reads_no_body_for_a_blocked_address_or_an_unknown_token(tmp_path, monkeypatch) -> None:
    from holdspeak.web.routes import walks as walks_routes

    client, service = _client(tmp_path, monkeypatch)
    token = client.post("/api/walks", json=SCRIPT).json()["token"]
    monkeypatch.setattr(walks_routes, "WALK_BODY_BYTES", 1024)

    def must_not_answer(*_args: Any, **_kwargs: Any) -> Any:
        raise AssertionError("the handler read an over-size body")

    monkeypatch.setattr(service, "answer", must_not_answer)
    big = json.dumps({"ref": "s11-well", "choice": "Keep", "words": "x" * 4096})
    declared = client.post(f"/api/w/{token}/answer", content=big, headers={"Content-Type": "application/json"})
    assert declared.status_code == 413 and declared.json()["code"] == "body_too_large"
    assert declared.headers["cache-control"] == "no-store"
    streamed = client.post(f"/api/w/{token}/answer", content=iter([big[:800].encode(), big[800:].encode()]))
    assert streamed.status_code == 413

    # An unknown token is a 404 and one miss before the body; a blocked address is 429.
    wrong = "y" * 43
    for _ in range(40):
        answer = client.post(f"/api/w/{wrong}/answer", content=big, headers={"Content-Type": "application/json"})
        if answer.status_code == 429:
            break
        assert answer.status_code == 404 and answer.json()["code"] == "walk_not_found"
    assert answer.status_code == 429
    assert client.post(f"/api/w/{token}/answer", content=big).status_code == 429


def test_the_walk_token_through_the_real_edge_reaches_only_its_two_routes(tmp_path, monkeypatch) -> None:
    """The real app and its principal gate, no owner header: the walk token
    reads its walk and nothing else; a briefing page token reads no walk."""
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks
    from tests.unit.test_reach_packages import OWNER as PROGRAM_OWNER, _briefing, _core, _ref

    service = WalkService(home=tmp_path)
    monkeypatch.setattr(walk_module, "default_walk_service", lambda: service)
    monkeypatch.setattr(briefing_module, "MISSES", briefing_module._Misses())
    made = service.create(SCRIPT)
    token = made["token"]

    rig, pid, item = _core(tmp_path / "rig")
    briefing = _briefing(rig)
    monkeypatch.setattr(briefing_module, "default_briefing_service", lambda db=None: briefing)
    page_token = briefing.make(PROGRAM_OWNER, [_ref(pid, item)])["token"]

    server = MeetingWebServer(WebRuntimeCallbacks(on_bookmark=lambda *_a, **_k: None,
                                                  on_stop=lambda *_a, **_k: None, get_state=lambda: None),
                              host="127.0.0.1")
    client = TestClient(server.app, follow_redirects=False)
    client.headers.pop("X-HoldSpeak-Token", None)  # the harness's owner header (tests/conftest.py)

    assert client.get(f"/api/w/{token}").json()["title"] == "Wave two"
    assert client.post(f"/api/w/{token}/answer", json={"ref": "s11-well", "choice": "Keep"}).status_code == 200
    bearer = {"Authorization": f"Bearer {token}"}
    # A sampled owner route: refused at the edge.
    for verb, path in (("GET", f"/api/walks/{made['id']}"), ("POST", "/api/walks"), ("GET", "/api/programs"),
                       ("GET", f"/api/reach/packages?token={token}")):
        assert client.request(verb, path, headers=bearer).status_code in (401, 403), (verb, path)
    # The briefing page's routes: the edge admits any page-shaped token there,
    # and the briefing handler reads nothing for a walk token (its one 404).
    read = client.get(f"/api/b/{token}")
    assert read.status_code == 404 and "Wave two" not in read.text
    assert client.post(f"/api/b/{token}/answer", json={"ref": "x", "choice": "y"}).status_code == 404

    # A briefing page token reads no walk: 404, and each try counts a miss.
    assert client.get(f"/api/b/{page_token}").status_code == 200  # the page token itself is good
    before = len(briefing_module.MISSES._seen.get("testclient", []))
    assert client.get(f"/api/w/{page_token}").status_code == 404
    assert client.post(f"/api/w/{page_token}/answer", json={"ref": "s11-well", "choice": "Keep"}).status_code == 404
    assert len(briefing_module.MISSES._seen.get("testclient", [])) == before + 2

    # An unknown walk token is a 404 and a miss; enough misses block the address.
    unknown = "z" * 43
    codes = [client.get(f"/api/w/{unknown}").status_code for _ in range(40)]
    assert codes[0] == 404 and codes[-1] == 429

    # An over-size body is a 413 before the handler reads it.
    def must_not_answer(*_args: Any, **_kwargs: Any) -> Any:
        raise AssertionError("the handler read an over-size body")

    monkeypatch.setattr(briefing_module, "MISSES", briefing_module._Misses())
    monkeypatch.setattr(service, "answer", must_not_answer)
    over = client.post(f"/api/w/{token}/answer", content=b"{" + b" " * (25 * 1024 * 1024) + b"}",
                       headers={"Content-Type": "application/json"})
    assert over.status_code == 413 and over.json()["code"] == "body_too_large"
