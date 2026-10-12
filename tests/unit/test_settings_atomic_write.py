"""PHILO-10-02 round three (Codex Astra r2 finding 1): a settings write is one transaction; its file is never partial.

Codex's probe: two concurrent ``settings.update`` calls over the REAL MCP
transport with the same ``_revision``, and a 200 ms pause before the real
``Config.save``. With every MCP tool call in the threadpool (b52bfcdb) both were
accepted, one edit vanished, and one pair left malformed JSON. Here, through a
real socket hub:

* over MCP, exactly one of each pair wins and the other is refused
  ``settings_stale``; both edits are never both "accepted";
* the settings service itself, called from two threads at once (the path a
  threadpool transport would take), still lets exactly one win -- the lock, not
  only the transport's order;
* a reader polling the file during the writes never sees invalid JSON (the
  temporary file + fsync + ``os.replace``).
"""
from __future__ import annotations

import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import pytest

TOKEN = "philo10-settings-race"


@pytest.fixture
def hub(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    import httpx

    from holdspeak.config import Config
    from tests.e2e.glass_infra import _boot

    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    real_save = Config.save

    def delayed_save(self: Any, *args: Any, **kwargs: Any) -> Any:
        time.sleep(0.2)  # Codex's pause: only the real read-modify-write interval widens
        return real_save(self, *args, **kwargs)

    monkeypatch.setattr(Config, "save", delayed_save)
    client = httpx.Client(base_url=url, headers={"Authorization": f"Bearer {TOKEN}"}, timeout=30)
    try:
        yield client, tmp_path / "home" / ".holdspeak" / "config.json"
    finally:
        client.close()
        server.stop()


def _tool(client: Any, name: str, args: dict[str, Any]) -> tuple[bool, Any]:
    resp = client.post("/api/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                                         "params": {"name": name, "arguments": args}})
    assert resp.status_code == 200, resp.text
    result = resp.json()["result"]
    return bool(result.get("isError")), json.loads(result["content"][0]["text"])


def _watch_file(path: Path, stop: threading.Event, bad: list[str]) -> None:
    while not stop.is_set():
        try:
            text = path.read_text()
        except FileNotFoundError:
            continue
        try:
            json.loads(text)
        except ValueError:
            bad.append(text[:200])


def test_concurrent_mcp_settings_updates_with_one_revision_let_exactly_one_win(hub: Any) -> None:
    client, config_file = hub
    stop, bad = threading.Event(), []
    watcher = threading.Thread(target=_watch_file, args=(config_file, stop, bad), daemon=True)
    watcher.start()
    try:
        for round_ in range(4):
            _err, before = _tool(client, "settings.get", {})
            revision = before["_revision"]
            sound = not before["ui"]["desk_sounds"]
            language = "pl" if before["model"]["language"] != "pl" else "en"
            barrier = threading.Barrier(2)

            def update(patch: dict[str, Any]) -> tuple[bool, Any]:
                barrier.wait()
                return _tool(client, "settings.update", {"patch": {"_revision": revision, **patch}})

            with ThreadPoolExecutor(2) as pool:
                futures = [pool.submit(update, {"ui": {"desk_sounds": sound}}),
                           pool.submit(update, {"model": {"language": language}})]
                answers = [f.result() for f in futures]
            accepted = [a for a in answers if not a[0]]
            refused = [a for a in answers if a[0]]
            assert len(accepted) == 1 and len(refused) == 1, (round_, answers)
            # MCP carries the refusal's words (the service's ConflictError settings_stale).
            assert "Settings changed in another surface" in json.dumps(refused[0][1]), refused
            _err, after = _tool(client, "settings.get", {})
            changed = (after["ui"]["desk_sounds"] == sound, after["model"]["language"] == language)
            assert sorted(changed) == [False, True], (round_, changed)  # exactly the winner's edit, nothing lost
            json.loads(config_file.read_text())
    finally:
        stop.set()
        watcher.join(5)
    assert bad == [], f"a reader saw a partial settings file: {bad[:1]}"


def test_the_settings_service_itself_lets_exactly_one_same_revision_write_win(hub: Any) -> None:
    """The lock, not only the loop: two threads call the service at once (what a threadpool transport does)."""
    from holdspeak.config import Config
    from holdspeak.runtime import composition
    from holdspeak.services.errors import ConflictError
    from holdspeak.services.settings_service import settings_revision

    _client, config_file = hub
    service = composition.installed().settings_service
    principal = None
    current = Config.load()
    revision = settings_revision(current)
    sound, language = not current.ui.desk_sounds, ("pl" if current.model.language != "pl" else "en")
    barrier = threading.Barrier(2)

    def update(patch: dict[str, Any]) -> str:
        barrier.wait()
        try:
            service.update_settings(principal, {"_revision": revision, **patch})
            return "accepted"
        except ConflictError as exc:
            return exc.code

    with ThreadPoolExecutor(2) as pool:
        results = sorted(pool.map(update, [{"ui": {"desk_sounds": sound}}, {"model": {"language": language}}]))
    assert results == ["accepted", "settings_stale"], results
    json.loads(config_file.read_text())


def test_a_settings_write_that_fails_midway_leaves_the_previous_file_whole(tmp_path: Path,
                                                                            monkeypatch: pytest.MonkeyPatch) -> None:
    """The atomic write: a reader sees the old file or the new one, never a torn one."""
    import holdspeak.config.core as core
    from holdspeak.config import Config

    path = tmp_path / "config.json"
    Config().save(path=path)
    before = path.read_text()
    real_dump = json.dump

    def torn_dump(obj: Any, handle: Any, **kwargs: Any) -> None:
        text = json.dumps(obj, **kwargs)
        handle.write(text[: len(text) // 2])  # half the bytes reach the file ...
        raise OSError("injected: the disk filled halfway")  # ... then the write dies

    monkeypatch.setattr(core.json, "dump", torn_dump)
    changed = Config()
    changed.ui.desk_sounds = not changed.ui.desk_sounds
    with pytest.raises(OSError):
        changed.save(path=path)
    monkeypatch.setattr(core.json, "dump", real_dump)
    assert path.read_text() == before and json.loads(path.read_text())
    assert sorted(p.name for p in tmp_path.iterdir()) == ["config.json"]  # no temporary file left behind
