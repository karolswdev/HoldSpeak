#!/usr/bin/env python3
"""Record the hub's own Phone speech answers for the Engines face test (RECIPE LINE-6).

``web/src/features/runson/__tests__/engines.app.test.tsx`` (Phone speech) replays them.
The real concierge routes (``holdspeak/web/routes/concierge.py``) run on a
FastAPI ``TestClient`` with the Line's folder in a temporary HOME; the real
fetch (``holdspeak/line/models.py``) fills it. Nothing reaches Hugging Face:
the fetch is a fake that serves zero bytes of each file's pinned size. The
real weights' SHA-256 cannot be made from zeros, so the recording accepts a
file by its size (``models._matches``); the face reads the state, the size
and the licences, never a digest (the SHA-256 check is
``tests/unit/test_line_models.py``'s).

    HOME=$(mktemp -d) uv run python scripts/record_speech_fixture.py

It writes ``web/src/features/runson/__tests__/fixtures/speech.recorded.json``:
``start`` (speech in Ready, the voice Not downloaded), ``download`` (the
press and the hub's answer), ``downloading`` (a read mid-way), ``ready``.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import threading
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Iterator

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

OUT = REPO / "web" / "src" / "features" / "runson" / "__tests__" / "fixtures" / "speech.recorded.json"
GET = "/api/concierge/speech"
POST = "/api/concierge/download"


def _app() -> Any:
    from fastapi import FastAPI, Request

    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.web.routes.concierge import build_concierge_router

    app = FastAPI()

    @app.middleware("http")
    async def owner(request: Request, call_next: Any) -> Any:
        request.state.principal = Principal(PrincipalKind.OWNER, "owner")
        return await call_next(request)

    app.include_router(build_concierge_router(SimpleNamespace(model_library_service=None)))  # type: ignore[arg-type]
    return app


def record(root: Path) -> dict[str, Any]:
    os.environ["HOLDSPEAK_LINE_HOME"] = str(root / "line")
    from fastapi.testclient import TestClient

    from holdspeak.line import models

    models._matches = lambda item, size, digest: size == item["bytes"]  # zeros cannot carry the real digest
    stt, tts = (next(row for row in models.presets() if row["role"] == role) for role in ("stt", "tts"))

    def zeros(url: str) -> Iterator[bytes]:
        item = next(i for row in models.presets() for i in row["source"]["files"] if url == models.file_url(row, i["path"]))
        left = int(item["bytes"])
        while left:
            step = min(left, 1 << 20)
            left -= step
            yield bytes(step)

    models.fetch(stt, fetch=zeros)
    client = TestClient(_app())
    out: dict[str, Any] = {"start": {GET: client.get(GET).json()}}

    halfway, go = threading.Event(), threading.Event()

    def slow(url: str) -> Iterator[bytes]:
        sent = 0
        for chunk in zeros(url):
            yield chunk
            sent += len(chunk)
            if url.endswith("model.safetensors") and sent >= 100 << 20 and not go.is_set():
                halfway.set()
                go.wait(30)

    import holdspeak.services.concierge_service as concierge

    real = concierge.download_speech
    concierge.download_speech = lambda preset_id, fetch=None: real(preset_id, fetch=slow)
    body = {"presetId": tts["id"]}
    answer = client.post(POST, json=body)
    assert answer.status_code == 202, answer.text
    out["download"] = {"post": POST, "body": body, "answer": answer.json()}
    assert halfway.wait(30), "the fake fetch did not get half way"
    out["downloading"] = {GET: client.get(GET).json()}
    go.set()
    models.wait(tts["id"], 60)
    out["ready"] = {GET: client.get(GET).json()}
    states = [row["state"] for row in out["ready"][GET]["rows"]]
    assert states == ["ready", "ready"], states
    return out


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        recorded = record(Path(tmp))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(recorded, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
