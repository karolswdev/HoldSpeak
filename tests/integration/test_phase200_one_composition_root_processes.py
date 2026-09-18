"""HS-200-45 fences (c) and (d): the real stdio sidecar, as a real process.

The unit fences prove the in-hub route and the pragmas. These two prove the
part that needed a second OS process to be provable at all -- that
``holdspeak-mcp`` is a CLIENT of the hub:

* (c) **No hub.** Every call but the handshake answers a JSON-RPC error naming
  the remedy, and the database is not opened: no ``holdspeak.db`` appears under
  the isolated HOME. Pre-fix this test failed on exactly that assertion -- the
  sidecar created ``~/.local/share/holdspeak/holdspeak.db`` and ran
  ``reconcile_schema`` into it before answering anything.
* (d) **A hub.** The sidecar discovers it through the owner lock, forwards a
  ``desk.create``, and the row is readable over the hub's own HTTP API -- one
  writer, one database file, and one ``desk_changed`` frame on the bus.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import urllib.request
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
TOKEN = "hs200-45-composition-root-token"


def _sidecar(home: Path, messages: list[dict[str, Any]], *, timeout: float = 150.0,
             standalone: bool = False) -> subprocess.CompletedProcess[str]:
    """Run the REAL stdio sidecar as its own process against *home*."""
    env = dict(os.environ)
    env["HOME"] = str(home)
    env.pop("HOLDSPEAK_ALLOW_REAL_HOME", None)
    if standalone:
        env["HOLDSPEAK_MCP_STANDALONE"] = "1"
    else:
        env.pop("HOLDSPEAK_MCP_STANDALONE", None)
    payload = "".join(json.dumps(m) + "\n" for m in messages)
    return subprocess.run(
        [sys.executable, "-c",
         "import sys; from holdspeak.mcp.server import main; sys.exit(main())"],
        input=payload, capture_output=True, text=True, env=env,
        cwd=str(REPO_ROOT), timeout=timeout,
    )


def _responses(proc: subprocess.CompletedProcess[str]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for line in proc.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:  # pragma: no cover - surfaced by the caller
            continue
    return out


# ── (c) the sidecar with no hub ─────────────────────────────────────────


@pytest.mark.timeout(240)
def test_sidecar_with_no_hub_refuses_and_opens_no_database(tmp_path: Path) -> None:
    home = tmp_path / "home"
    home.mkdir()

    proc = _sidecar(home, [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/call",
         "params": {"name": "desk.list", "arguments": {"kind": "notes"}}},
    ])

    # THE fence: nothing was opened, so nothing was created -- and (counsel
    # P1-2) nothing else either: the sidecar used to SAVE a default
    # ~/.config/holdspeak/config.json through Config.load on a machine that
    # had never run the hub. The whole HOME must be exactly as it was, minus
    # the caches Python and uv keep for themselves.
    created = sorted(
        str(p.relative_to(home)) for p in home.rglob("*") if p.is_file()
        and not any(part in {".cache", "__pycache__"} for part in p.relative_to(home).parts)
    )
    assert created == [], (
        f"the sidecar wrote files with no hub running: {created}. "
        "A client of the hub creates nothing on its own."
    )
    assert not list(home.rglob("holdspeak.db"))
    assert not list(home.rglob("*.owner.lock"))

    responses = _responses(proc)
    assert len(responses) >= 2, proc.stdout + proc.stderr

    # The handshake succeeds locally, so the client connects and can be told
    # the truth on its first real call instead of failing to start.
    handshake = responses[0]
    assert handshake["id"] == 1
    assert handshake["result"]["serverInfo"]["name"] == "holdspeak-mcp"

    refusal = responses[1]
    assert refusal["id"] == 2
    assert "error" in refusal, refusal
    message = refusal["error"]["message"]
    assert "No running HoldSpeak hub owns" in message, message
    assert "holdspeak web" in message, message
    assert "holdspeak.db" in message, message


@pytest.mark.timeout(240)
def test_the_standalone_hatch_claims_the_owner_lock(tmp_path: Path) -> None:
    """The diagnosis hatch is honest about being a writer."""
    home = tmp_path / "home"
    home.mkdir()

    proc = _sidecar(home, [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
    ], standalone=True)

    locks = sorted(home.rglob("*.owner.lock"))
    assert locks, (
        "standalone mode opens the database, so it must claim the owner lock "
        f"-- nothing was claimed. stderr: {proc.stderr[-2000:]}"
    )
    body = json.loads(locks[0].read_text())
    assert body["label"] == "holdspeak-mcp", body
    assert body["pid"]


# ── (d) the sidecar with a hub ──────────────────────────────────────────


@pytest.mark.timeout(300)
def test_sidecar_with_a_hub_writes_through_the_one_writer(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import holdspeak.config as config_module
    import holdspeak.db.core as db_core
    from holdspeak.db import reset_database
    from holdspeak.runtime_lock import claim_database, release_database
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    home = tmp_path / "home"
    home.mkdir()
    db_path = home / ".local" / "share" / "holdspeak" / "holdspeak.db"
    config_file = home / ".config" / "holdspeak" / "config.json"
    config_file.parent.mkdir(parents=True, exist_ok=True)
    config_file.write_text(json.dumps({"meeting": {"web_auth_token": TOKEN}}))

    # The sidecar subprocess resolves these from ITS env; the in-process hub
    # must be pointed at the same two files or they are not the same install.
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setattr(db_core, "DEFAULT_DB_PATH", db_path)
    monkeypatch.setattr(config_module, "CONFIG_FILE", config_file)
    reset_database()

    frames: list[tuple[str, Any]] = []
    server = MeetingWebServer(
        WebRuntimeCallbacks(
            on_bookmark=lambda *_: None,
            on_stop=lambda: None,
            get_state=lambda: {},
        ),
        auth_token=TOKEN,
    )
    url = server.start()
    port = int(str(url).rsplit(":", 1)[-1].strip("/"))

    # The two steps `holdspeak web`'s runtime performs around `start()`
    # (DatabaseOwnershipMixin._claim_database + _note_serving_port). Without
    # them there is no owner lock for the sidecar to discover, which is the
    # whole discovery mechanism.
    claim_database(db_path, port=port)
    original_broadcast = server.broadcast
    server.broadcast = lambda message_type, data: (  # type: ignore[method-assign]
        frames.append((message_type, data)), original_broadcast(message_type, data)
    )[1]

    try:
        proc = _sidecar(home, [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/call",
             "params": {"name": "desk.create",
                        "arguments": {"kind": "notes",
                                      "data": {"title": "Written by the sidecar"}}}},
        ])
        responses = _responses(proc)
        assert len(responses) >= 2, (
            f"stdout={proc.stdout!r} stderr={proc.stderr[-3000:]!r}"
        )
        created = responses[1]
        assert "error" not in created, created
        result = created["result"]
        assert result["isError"] is False, result
        note = json.loads(result["content"][0]["text"])
        note_id = note["id"]

        # Read it back over the hub's OWN HTTP API: if the sidecar had written
        # to a database of its own, this would be empty.
        req = urllib.request.Request(f"http://127.0.0.1:{port}/api/notes")
        req.add_header("Authorization", f"Bearer {TOKEN}")
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        notes = body if isinstance(body, list) else body.get("notes", body.get("items", []))
        titles = {n.get("title") for n in notes}
        assert "Written by the sidecar" in titles, body

        # ONE writer: one database file under the isolated HOME, claimed once.
        db_files = sorted(p for p in home.rglob("holdspeak.db"))
        assert db_files == [db_path], db_files
        lock_body = json.loads((db_path.parent / "holdspeak.db.owner.lock").read_text())
        assert lock_body["port"] == port
        assert lock_body["label"] == "holdspeak web"

        # And the write reached the bus. NOTE: this harness subscribes at the
        # server's `broadcast` seam, not over a real `/ws` socket -- the e2e
        # glass rigs are the only harness that opens one, and they drive a
        # browser rather than a sidecar. What is proven here is that the frame
        # is produced for an out-of-process MCP write; `tests/e2e` covers the
        # socket carrying frames to a browser.
        changed = [f for f in frames if f[0] == "desk_changed"]
        assert len(changed) == 1, f"expected ONE desk_changed frame, saw {frames!r}"
        assert changed[0][1]["id"] == note_id
        assert changed[0][1]["op"] == "create"
    finally:
        server.broadcast = original_broadcast  # type: ignore[method-assign]
        try:
            server.stop()
        except Exception:  # pragma: no cover
            pass
        release_database()
        reset_database()
