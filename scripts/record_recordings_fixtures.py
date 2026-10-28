"""Record the Recordings window's fixtures through the real routes.

    uv run python scripts/record_recordings_fixtures.py

Boots ``holdspeak/web/routes/recordings.py`` in a scratch HOME with the fake
ffmpeg (``tests/fixtures/fake_ffmpeg.sh``) and a Tailscale Serve status that
proxies ``karols-macbook-pro.tailad9943.ts.net`` to this hub, then walks one
recording through its states and writes each answer (and the
``recording_state`` frames) to ``web/src/desk/recordings/__fixtures__/``.
The web tests replay these (THE TEST DIET: recorded, never typed).
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace
from typing import Any

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "web" / "src" / "desk" / "recordings" / "__fixtures__"
FAKE_FFMPEG = REPO / "tests" / "fixtures" / "fake_ffmpeg.sh"
SERVE = {"Web": {"karols-macbook-pro.tailad9943.ts.net:443": {"Handlers": {"/": {"Proxy": "http://127.0.0.1:8765"}}}}}


def write(name: str, const: str, value: Any, kind: str) -> None:
    text = (
        "// Recorded by scripts/record_recordings_fixtures.py through the real\n"
        "// /api/recordings routes (fake ffmpeg, a recorded Tailscale Serve answer).\n"
        f"import type {{ {kind} }} from \"../types\";\n\n"
        f"export const {const}: {kind} = {json.dumps(value, indent=2, ensure_ascii=False)};\n"
    )
    (OUT / f"{name}.ts").write_text(text, encoding="utf-8")


def main() -> int:
    home = Path(tempfile.mkdtemp(prefix="hs-rec-fixtures-"))
    os.environ["HOME"] = str(home)
    os.environ["HOLDSPEAK_RECORDINGS"] = "on"
    os.environ["HOLDSPEAK_FFMPEG"] = str(FAKE_FFMPEG)
    sys.path.insert(0, str(REPO))
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from holdspeak.recordings import service as rec_service
    from holdspeak.recordings import tailnet
    from holdspeak.recordings.store import RecordingStore
    from holdspeak.web.routes import recordings as routes

    tailnet._serve_status = lambda: SERVE  # type: ignore[assignment]
    tailnet.tailnet_base.__defaults__ = (lambda: SERVE,)  # the default reader
    frames: list[dict[str, Any]] = []
    svc = rec_service.RecordingsService(RecordingStore(root=lambda: home / "recordings"))
    svc.configure(dispatch=lambda name, args, principal: {"note": {"id": "n-rec-1"}} if name == "desk.create" else {})
    routes.RECORDINGS = svc
    app = FastAPI()
    app.include_router(routes.build_recordings_router(SimpleNamespace(broadcast=None)))
    svc.configure(broadcast=lambda kind, data: frames.append(json.loads(json.dumps(data))))
    svc._queue = lambda _rid: None  # encode in this thread, step by step
    client = TestClient(app, base_url="http://127.0.0.1:8765")

    empty = client.get("/api/recordings").json()
    started = client.post("/api/recordings", json={"width": 2880, "height": 1800, "view": "view-mac"}).json()
    rid = started["id"]
    for part in (b"\x1aE\xdf\xa3" * 64, b"chunk-two" * 64):
        client.post(f"/api/recordings/{rid}/chunks", content=part, headers={"content-type": "video/webm"})
    recording = client.get(f"/api/recordings/{rid}").json()
    stopped = client.post(f"/api/recordings/{rid}/stop").json()
    # A 2.4 s recording: the fake ffmpeg's first progress (1 s) is 42 %.
    svc.store.update(rid, duration_s=1 / 0.42)
    svc.encode_now(rid)
    encoding = next(f for f in frames if f["reason"] == "progress" and f["recording"]["progress"] == 42)
    ready = client.get(f"/api/recordings/{rid}").json()
    ready_frame = next(f for f in frames if f["reason"] == "ready")
    # A second one that fails to encode.
    second = client.post("/api/recordings", json={"width": 1440, "height": 900, "view": "view-mac"}).json()
    client.post(f"/api/recordings/{second['id']}/chunks", content=b"broken" * 32)
    client.post(f"/api/recordings/{second['id']}/stop")
    os.environ["FAKE_FFMPEG_FAIL"] = "1"
    svc.encode_now(second["id"])
    del os.environ["FAKE_FFMPEG_FAIL"]
    failed = client.get(f"/api/recordings/{second['id']}").json()
    listed = client.get("/api/recordings").json()
    started_frame = next(f for f in frames if f["reason"] == "started")
    remote = json.loads(json.dumps(started_frame))
    remote["recording"]["view"] = "view-other"

    OUT.mkdir(parents=True, exist_ok=True)
    write("recordings.empty", "recordingsEmpty", empty, "RecordingsPayload")
    write("recordings.list", "recordingsList", listed, "RecordingsPayload")
    write("recording.recording", "recordingLive", recording, "Recording")
    write("recording.stopped", "recordingStopped", stopped, "Recording")
    write("recording.ready", "recordingReady", ready, "Recording")
    write("recording.failed", "recordingFailed", failed, "Recording")
    write("frame.encoding", "frameEncoding", encoding, "RecordingStateFrame")
    write("frame.ready", "frameReady", ready_frame, "RecordingStateFrame")
    write("frame.remoteStarted", "frameRemoteStarted", remote, "RecordingStateFrame")
    print(f"wrote {len(list(OUT.glob('*.ts')))} fixtures to {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
