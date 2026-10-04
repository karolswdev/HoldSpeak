"""Meaning search on a real hub, with the real model (adopt path).

The hub is the real ``MeetingWebServer``; the model is the real
``nomic-embed-text-v1.5`` GGUF, already on this device (the test never
downloads 146 MB).  Nothing is replaced.

Run:
  HOLDSPEAK_MEMORY_EMBED_MODEL=~/.cache/holdspeak-models/embed/nomic-embed-text-v1.5.Q8_0.gguf \
    HOME=$(mktemp -d) uv run pytest -q tests/integration/test_meaning_search_real_hub.py
"""
from __future__ import annotations

import json
import os
import time
import urllib.request
from pathlib import Path
from typing import Any

import pytest

from tests.memory_bench import bench
from tests.memory_bench.corpus import build_corpus

TOKEN = "meaning-search-real-hub"

pytestmark = [pytest.mark.slow, pytest.mark.requires_llama_cpp, pytest.mark.timeout(240)]


def _call(url: str, method: str, path: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
    request = urllib.request.Request(
        url + path, method=method,
        data=json.dumps(body).encode() if body is not None else (b"" if method == "POST" else None),
        headers={"authorization": f"Bearer {TOKEN}", "content-type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode())


def _search(url: str, question: str) -> dict[str, Any]:
    return _call(url, "GET", "/api/memory/search?query=" + urllib.request.quote(question))


def _wait(read, done, seconds: float) -> Any:
    deadline = time.time() + seconds
    value = read()
    while not done(value) and time.time() < deadline:
        time.sleep(0.25)
        value = read()
    return value


def test_turn_on_then_a_paraphrase_finds_its_source_then_turn_off(tmp_path: Path, monkeypatch) -> None:
    model_path = os.environ.get("HOLDSPEAK_MEMORY_EMBED_MODEL", "")
    if not model_path or not Path(model_path).is_file():
        pytest.skip("set HOLDSPEAK_MEMORY_EMBED_MODEL to nomic-embed-text-v1.5.Q8_0.gguf")
    pytest.importorskip("llama_cpp")

    import holdspeak.config as config_module
    import holdspeak.db.core as db_core
    from holdspeak.db import get_database, reset_database
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setattr(config_module, "CONFIG_FILE", home / ".holdspeak" / "config.json")
    monkeypatch.setattr(db_core, "DEFAULT_DB_PATH", tmp_path / "holdspeak.db")
    reset_database()
    # The hub that owns the database runs the conductors (as `holdspeak` does).
    from holdspeak import runtime_lock

    runtime_lock.claim_database(tmp_path / "holdspeak.db", label="meaning-search-test")
    refs = build_corpus(get_database())
    server = MeetingWebServer(
        WebRuntimeCallbacks(on_bookmark=lambda *_: None, on_stop=lambda: None, get_state=lambda: {}),
        auth_token=TOKEN,
    )
    url = server.start()
    try:
        question = next(q for q in bench.load_questions() if q["id"] == "p03")
        expected = refs[question["expect"][0]]

        # OFF: the file is on this device, so the press sends nothing out.
        status = _call(url, "GET", "/api/memory/meaning-search")
        assert status["state"] == "off" and status["model"]["on_device"] is True and status["egress"] is None
        before = _search(url, question["q"])
        assert before["ranking"].get("engine", {}).get("outcome") != "fused"
        assert expected not in [hit["source_ref"].split("#")[0] for hit in before["hits"][:5]]

        # The press: adopt -> profile -> assignment -> conductor.
        pressed = time.time()
        status = _call(url, "POST", "/api/memory/meaning-search/turn-on")
        assert status["state"] in {"indexing", "on"}, status
        status = _wait(lambda: _call(url, "GET", "/api/memory/meaning-search"), lambda s: s["state"] == "on", 120)
        assert status["state"] == "on" and status["indexed"] == status["total"] > 0, status
        print(f"\nturn on -> ON: {time.time() - pressed:.1f} s, {status['total']} chunks")

        # A paraphrase question finds its source by meaning.
        fused = _wait(
            lambda: _search(url, question["q"]),
            lambda r: r["ranking"].get("engine", {}).get("outcome") == "fused", 30,
        )
        assert fused["ranking"]["engine"]["outcome"] == "fused", fused["ranking"]
        assert fused["ranking"]["engine"]["boundary"] == "local"
        assert expected in [hit["source_ref"].split("#")[0] for hit in fused["hits"][:5]]

        # A new note (a real producer, over HTTP) is found by meaning in seconds.
        written = time.time()
        _call(url, "POST", "/api/notes", {
            "id": "kiln", "title": "Pottery studio",
            "body_markdown": "The kiln is fired on the first Tuesday of each month.",
        })
        late = _wait(
            lambda: _search(url, "when do we heat the ceramics oven"),
            lambda r: "note:kiln" in [hit["source_ref"].split("#")[0] for hit in r["hits"][:5]], 20,
        )
        assert "note:kiln" in [hit["source_ref"].split("#")[0] for hit in late["hits"][:5]]
        print(f"new note searchable by meaning: {time.time() - written:.1f} s")

        # Turn off: the assignment is cleared; the keyword search continues.
        status = _call(url, "POST", "/api/memory/meaning-search/turn-off")
        assert status["state"] == "off"
        after = _search(url, question["q"])
        assert after["ranking"].get("engine", {}).get("outcome") != "fused"
        assert expected not in [hit["source_ref"].split("#")[0] for hit in after["hits"][:5]]
        keyword = _search(url, "database backups every six hours")
        assert keyword["hits"], "the keyword search stopped"
    finally:
        server.stop()
        runtime_lock.release_database()
        reset_database()
