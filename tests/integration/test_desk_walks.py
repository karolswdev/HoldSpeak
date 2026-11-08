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
        {"highlight": {"target": "[data-testid='programs-make'] .gadget-row", "words": "The project choice."},
         "ask": {"ref": "s11-well", "question": "Does the well read clearly?", "choices": ["Keep", "Redo"]}},
        {"open": {"app": "chair:needs"},
         "highlight": {"target": "needs-people-coverage", "words": "Whose obligations the list shows."},
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

    # Skip is always a choice; a second answer keeps the first.
    assert client.post(f"/api/w/{token}/answer", json={"ref": "needs-coverage", "choice": "skip"}).status_code == 200
    again = client.post(f"/api/w/{token}/answer", json={
        "ref": "s11-well", "choice": "Keep", "window_png": base64.b64encode(png).decode("ascii")})
    assert again.json()["shot"] == "s11-well-2.png"

    owner = client.get(f"/api/walks/{walk_id}")
    assert owner.status_code == 200
    full = owner.json()
    assert full["answers"]["s11-well"]["choice"] == "Keep"
    assert full["answers"]["s11-well"]["earlier"][0]["words"] == "The project name is cut."
    assert full["answers"]["needs-coverage"]["choice"] == "skip"
    assert full["directory"].endswith(walk_id) and "token_sha256" not in full
    assert client.get(f"/api/w/{token}").json()["answers"]["s11-well"]["choice"] == "Keep"


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
