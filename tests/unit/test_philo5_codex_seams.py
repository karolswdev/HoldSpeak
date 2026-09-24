"""PHILO-5-01: the Codex seams, through the rig's hub and the REAL proxy.

A hub started the rig's way (``scripts/graph_walk.py`` ``Hub``) publishes its
loopback port through the product's lock producer (``claim_database(...,
port=...)``) and persists its token to ``meeting.web_auth_token`` in the config
file under its isolated HOME. The REAL stdio proxy, launched with ``HOME`` =
that HOME, then discovers the hub (``discover_hub``), authenticates
(``_owner_token``), writes one decision, and -- after a rig restart --
rediscovers the hub and reads the decision back.

Pre-fix (main): the rig claimed the lock with no port, so ``discover_hub()``
returned ``None`` and the proxy answered "No running HoldSpeak hub owns ...".
This file imports no symbol the fix adds, so it runs unchanged on a copy of
main for its red.
"""
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

REPO = Path(__file__).resolve().parents[2]
TOKEN = "philo5-01-token"


def _load_script(name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    sys.modules[name] = module
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


def _proxy(home: Path, messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    env = dict(os.environ)
    env["HOME"] = str(home)
    env.pop("HOLDSPEAK_ALLOW_REAL_HOME", None)
    payload = "".join(json.dumps(m) + "\n" for m in messages)
    proc = subprocess.run(
        [sys.executable, "-c", "import sys; from holdspeak.mcp.server import main; sys.exit(main())"],
        input=payload, capture_output=True, text=True, env=env, cwd=str(REPO), timeout=150,
    )
    out = [json.loads(line) for line in proc.stdout.splitlines() if line.strip()]
    assert len(out) == len(messages), proc.stdout + proc.stderr[-3000:]
    return out


def _call(rpc_id: int, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": rpc_id, "method": "tools/call",
            "params": {"name": name, "arguments": arguments}}


@pytest.mark.timeout(420)
def test_a_rig_hub_is_found_and_accepted_by_the_real_proxy_across_a_restart(tmp_path: Path) -> None:
    walk = _load_script("graph_walk")
    home = (tmp_path / "rig-home")
    home.mkdir()
    hub = walk.Hub(home, token=TOKEN).start()
    try:
        # (a) the port is published through the product's own lock producer.
        from holdspeak.runtime_lock import read_owner
        from holdspeak.mcp.server import discover_hub

        db_path = Path(hub.db_path)
        assert db_path.is_relative_to(home.resolve()), db_path
        owner = read_owner(db_path)
        assert owner and owner.get("alive"), owner
        assert owner.get("port") == hub.port, f"the rig hub published no port: {owner}"
        found = discover_hub(db_path)
        assert found is not None and found["port"] == hub.port, found
        # (b) the token is persisted through the isolated config path.
        config_path = Path(hub.config_path)
        assert config_path.is_relative_to(home.resolve()), config_path
        assert json.loads(config_path.read_text())["meeting"]["web_auth_token"] == TOKEN

        # The REAL stdio proxy, HOME = the hub's HOME: discovery, auth, a write.
        first = _proxy(home, [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
            _call(2, "desk.create", {"kind": "decisions", "data": {"title": "Through the proxy"}}),
        ])
        assert "error" not in first[1], first[1]
        assert first[1]["result"]["isError"] is False, first[1]
        made = json.loads(first[1]["result"]["content"][0]["text"])

        before_pid = hub.proc.pid
        record = hub.restart()
        assert record["same_db_path"] and hub.proc.pid != before_pid

        again = _proxy(home, [_call(3, "desk.get", {"kind": "decisions", "id": made["id"]})])
        assert again[0]["result"]["isError"] is False, again[0]
        assert json.loads(again[0]["result"]["content"][0]["text"])["title"] == "Through the proxy"
    finally:
        hub.stop()
