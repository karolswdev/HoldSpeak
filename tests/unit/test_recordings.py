"""Recordings (2026-10-28): the hub half of record-a-session.

The store's state machine (chunks in order, stop, the stale close), the encoder
with a fake ffmpeg (progress, the mp4, the poster), a missing ffmpeg (kept as
webm), the Note with both links, the shared link (Range, the share token, a
parked recording), the keep sweep (parks, never deletes) and the Tailscale
Serve read.
"""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from holdspeak.recordings import service as rec_service
from holdspeak.recordings.store import RecordingRefused, RecordingStore
from holdspeak.recordings.tailnet import base_from_status

FAKE_FFMPEG = Path(__file__).resolve().parents[1] / "fixtures" / "fake_ffmpeg.sh"


@pytest.fixture
def store(tmp_path: Path) -> RecordingStore:
    return RecordingStore(root=lambda: tmp_path / "recordings")


class Desk:
    """The two MCP calls the service makes, recorded."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def __call__(self, name: str, args: dict[str, Any], principal: Any) -> dict[str, Any]:
        self.calls.append((name, args))
        return {"note": {"id": "n42"}} if name == "desk.create" else {"ok": True}


@pytest.fixture
def svc(store: RecordingStore, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("HOLDSPEAK_RECORDINGS", "on")
    monkeypatch.setenv("HOLDSPEAK_FFMPEG", str(FAKE_FFMPEG))
    frames: list[tuple[str, dict[str, Any]]] = []
    desk = Desk()
    service = rec_service.RecordingsService(store)
    service.configure(broadcast=lambda kind, data: frames.append((kind, data)), dispatch=desk)
    service._bases = {"local": "http://127.0.0.1:8765", "tailnet": "https://mac.tail.ts.net"}
    return SimpleNamespace(service=service, store=store, frames=frames, desk=desk)


def _recorded(svc, payload: bytes = b"AAAABBBBCCCC") -> str:
    row = svc.service.start(width=1440, height=900, project_id="p1")
    for part in (payload[:4], payload[4:8], payload[8:]):
        svc.service.chunk(row["id"], part)
    return row["id"]


def test_chunks_append_in_order_and_stop_moves_to_encoding(svc) -> None:
    rid = _recorded(svc)
    assert svc.store.input_path(rid).read_bytes() == b"AAAABBBBCCCC"
    rec = svc.store.require(rid)
    assert (rec.chunks, rec.bytes_in, rec.state) == (3, 12, "recording")
    stopped, changed = svc.store.stop(rid)
    assert changed and stopped.state == "encoding"
    again, changed = svc.store.stop(rid)
    assert not changed and again.state == "encoding"
    with pytest.raises(RecordingRefused) as refused:
        svc.store.append_chunk(rid, b"late")
    assert refused.value.code == "not_recording"


def test_one_recording_at_a_time_and_an_empty_one_fails(svc) -> None:
    row = svc.service.start()
    with pytest.raises(RecordingRefused) as busy:
        svc.service.start()
    assert busy.value.code == "busy"
    stopped = svc.service.stop(row["id"])
    assert stopped["state"] == "failed" and stopped["error"] == "Nothing was recorded."


def test_a_recording_with_no_chunk_for_two_minutes_is_closed(svc) -> None:
    row = svc.service.start()
    svc.service.chunk(row["id"], b"data")
    last = svc.store.require(row["id"]).last_chunk_ts
    svc.service._queue = lambda _rid: None  # the encode is another test
    assert svc.service.close_stale(now=last + 60) == []
    assert svc.service.close_stale(now=last + 121) == [row["id"]]
    assert svc.store.require(row["id"]).state == "encoding"


def test_the_encoder_writes_the_mp4_the_poster_and_the_note_with_both_links(svc) -> None:
    rid = _recorded(svc)
    svc.service._queue = lambda _rid: None
    svc.service.stop(rid)
    svc.store.update(rid, duration_s=5.0)
    done = svc.service.encode_now(rid)
    assert done["state"] == "ready" and done["encoder"] == "mp4" and done["progress"] == 100
    assert svc.store.output_path(rid).read_bytes() == b"AAAABBBBCCCC"
    assert svc.store.poster_path(rid).read_bytes() == b"JPEG"
    progress = [data["recording"]["progress"] for kind, data in svc.frames if data["reason"] == "progress"]
    assert progress and progress == sorted(progress) and 20 <= progress[0] <= 50
    assert {kind for kind, _ in svc.frames} == {"recording_state"}
    assert [data["reason"] for _, data in svc.frames][-1] == "ready"
    name, args = svc.desk.calls[0]
    assert name == "desk.create"
    body = args["data"]["body_markdown"]
    tok = svc.store.require(rid).share_token
    phone = f"https://mac.tail.ts.net/r/{rid}/{tok}/{done['video_name']}"
    mac = f"http://127.0.0.1:8765/r/{rid}/{tok}/{done['video_name']}"
    assert phone in body and mac in body and body.index(phone) < body.index(mac)
    assert args["data"]["title"].startswith("Recording · ")
    assert svc.desk.calls[1] == ("project.resource.add", {"project_id": "p1", "resource_ref": "note:n42"})
    assert done["links"] == {"tailnet": phone, "local": mac}
    assert svc.store.require(rid).note_ref == "note:n42"


def test_no_ffmpeg_keeps_the_webm_as_the_video(svc, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HOLDSPEAK_FFMPEG", "none")
    rid = _recorded(svc)
    svc.service._queue = lambda _rid: None
    svc.service.stop(rid)
    done = svc.service.encode_now(rid)
    assert done["state"] == "ready" and done["encoder"] == "webm"
    assert done["video_name"].endswith(".webm")
    assert not svc.store.output_path(rid).exists()
    assert "brew install ffmpeg" in svc.desk.calls[0][1]["data"]["body_markdown"]
    assert svc.service.payload()["encoder"] == "none"


def test_the_switch_off_runs_no_ffmpeg(svc, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HOLDSPEAK_RECORDINGS", "off")
    rid = _recorded(svc)
    svc.service._queue = lambda _rid: None
    svc.service.stop(rid)
    assert svc.service.encode_now(rid)["encoder"] == "webm"


def test_a_failed_encode_says_why_and_retry_encodes_again(svc, monkeypatch: pytest.MonkeyPatch) -> None:
    rid = _recorded(svc)
    svc.service._queue = lambda _rid: None
    svc.service.stop(rid)
    monkeypatch.setenv("FAKE_FFMPEG_FAIL", "1")
    failed = svc.service.encode_now(rid)
    assert failed["state"] == "failed" and "Invalid data" in failed["error"]
    assert not svc.store.output_path(rid).exists()
    monkeypatch.delenv("FAKE_FFMPEG_FAIL")
    assert svc.service.retry(rid)["state"] == "encoding"
    assert svc.service.encode_now(rid)["state"] == "ready"
    with pytest.raises(RecordingRefused):
        svc.service.retry(rid)


@pytest.fixture
def client(svc, monkeypatch: pytest.MonkeyPatch):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from holdspeak.web.routes import recordings as routes

    monkeypatch.setattr(routes, "RECORDINGS", svc.service)
    app = FastAPI()
    app.include_router(routes.build_recordings_router(SimpleNamespace(broadcast=None)))
    return TestClient(app)


def _ready(svc) -> tuple[str, str, str]:
    rid = _recorded(svc, b"0123456789" * 10)
    svc.service._queue = lambda _rid: None
    svc.service.stop(rid)
    done = svc.service.encode_now(rid)
    return rid, svc.store.require(rid).share_token, done["video_name"]


def test_the_shared_link_serves_byte_ranges_without_the_hub_token(svc, client) -> None:
    rid, tok, name = _ready(svc)
    whole = client.get(f"/r/{rid}/{tok}/{name}")
    assert whole.status_code == 200 and whole.content == b"0123456789" * 10
    assert whole.headers["content-type"] == "video/mp4"
    assert whole.headers["accept-ranges"] == "bytes"
    part = client.get(f"/r/{rid}/{tok}/{name}", headers={"Range": "bytes=10-19"})
    assert part.status_code == 206
    assert part.content == b"0123456789"
    assert part.headers["content-range"] == "bytes 10-19/100"
    assert part.headers["content-length"] == "10"


def test_the_share_token_refuses_a_wrong_token_a_stopped_share_and_a_parked_recording(svc, client) -> None:
    rid, tok, name = _ready(svc)
    assert client.get(f"/r/{rid}/wrong-token/{name}").status_code == 404
    assert client.get(f"/r/{rid}/{tok}/other.mp4").status_code == 404
    assert client.post(f"/api/recordings/{rid}/unshare").json()["shared"] is False
    assert client.get(f"/r/{rid}/{tok}/{name}").status_code == 404
    shared = client.post(f"/api/recordings/{rid}/share").json()
    new = svc.store.require(rid).share_token
    assert shared["shared"] and new != tok
    assert client.get(f"/r/{rid}/{new}/{name}").status_code == 200
    assert client.post(f"/api/recordings/{rid}/park").json() == {"id": rid, "parked": True}
    assert client.get(f"/r/{rid}/{new}/{name}").status_code == 404
    assert client.get("/api/recordings").json()["recordings"] == []


def test_the_routes_start_append_stop_and_list(svc, client) -> None:
    svc.service._queue = lambda _rid: None
    started = client.post("/api/recordings", json={"width": 1440, "height": 900, "voice": True})
    assert started.status_code == 201
    rid = started.json()["id"]
    assert client.post("/api/recordings", json={}).status_code == 409
    chunk = client.post(f"/api/recordings/{rid}/chunks", content=b"webm-bytes",
                        headers={"content-type": "video/webm"})
    assert chunk.json() == {"id": rid, "bytes_in": 10, "chunks": 1, "state": "recording"}
    assert client.post(f"/api/recordings/{rid}/stop").json()["state"] == "encoding"
    assert client.post(f"/api/recordings/{rid}/chunks", content=b"x").status_code == 409
    assert client.post("/api/recordings/nope/stop").status_code == 404
    listed = client.get("/api/recordings").json()
    assert [row["id"] for row in listed["recordings"]] == [rid]
    assert listed["usage"]["keep_days"] == 30 and listed["usage"]["bytes"] >= 10
    assert listed["recordings"][0]["voice"] is True
    assert "share_token" not in listed["recordings"][0]


def test_the_keep_sweep_parks_old_recordings_and_deletes_nothing(svc) -> None:
    old = svc.store.create(now=1_000_000.0)
    svc.store.append_chunk(old.id, b"old", now=1_000_005.0)
    svc.store.stop(old.id, now=1_000_010.0)
    svc.store.update(old.id, state="ready", encoder="webm")
    new = svc.store.create()
    svc.store.append_chunk(new.id, b"new")
    svc.store.stop(new.id)
    svc.store.update(new.id, state="ready", encoder="webm")
    before = svc.store.usage()
    assert svc.store.sweep(now=1_000_000.0 + 31 * 86400) == [old.id]
    assert [rec.id for rec in svc.store.list()] == [new.id]
    parked = svc.store.root() / "_parked" / old.id
    assert (parked / "in.webm").read_bytes() == b"old" and (parked / "meta.json").is_file()
    assert svc.store.usage() == before


def test_the_tailnet_link_is_the_serve_host_that_proxies_to_this_hub() -> None:
    status = {"TCP": {"443": {"HTTPS": True}}, "Web": {
        "other.tail.ts.net:443": {"Handlers": {"/": {"Proxy": "http://127.0.0.1:9000"}}},
        "karols-macbook-pro.tailad9943.ts.net:443": {"Handlers": {"/": {"Proxy": "http://127.0.0.1:8765"}}},
    }}
    assert base_from_status(status, 8765) == "https://karols-macbook-pro.tailad9943.ts.net"
    assert base_from_status(status, 8000) is None
    assert base_from_status(None, 8765) is None
