"""PHILO-9-07 canvas: capture the REAL `GET /api/settings/remote` wire and the
REAL project list from a real hub on an isolated HOME.

The hub is the rig's own (`scripts/graph_walk.py serve`), booted with
HOME=tempfile.mkdtemp(): the owner's HOME and database are never touched.
Through the real routes it:
  1. turns Remote Access ON (PUT /api/settings/remote);
  2. issues `desk-agent` (palette DESK, 12 H) and `sweep-runner` (PROJECT, 24 H)
     (POST /api/settings/remote/credentials);
  3. uses `desk-agent` once over /api/mcp, so `last_used_at` is real;
  4. grants `desk-agent` the Phase 7 desk grant (PUT .../delegations/desk-agent),
     so board 0 shows today's built grant face;
  5. creates two projects (POST /api/projects);
  6. saves GET /api/settings/remote and GET /api/projects to fixtures/.

The project grant does NOT exist on main (story 07 builds it); nothing here
fabricates it. Run from the repo root:
  uv run --extra test python pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-07-grant-canvas/harness/produce_wire.py
"""
from __future__ import annotations

import json
import os
import socket
import subprocess
import tempfile
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[6]
FIX = HERE / "fixtures"
TOKEN = "philo9-07-canvas"


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def call(base: str, method: str, path: str, body=None, token: str = TOKEN):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(f"{base}{path}", data=data, method=method,
                                 headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read().decode() or "null")
    except urllib.error.HTTPError as e:  # type: ignore[attr-defined]
        return e.code, e.read().decode()[:400]


def main() -> None:
    FIX.mkdir(parents=True, exist_ok=True)
    home = tempfile.mkdtemp(prefix="philo9-07-wire-")
    port = free_port()
    base = f"http://127.0.0.1:{port}"
    hub = subprocess.Popen(
        ["uv", "run", "--extra", "test", "python", "scripts/graph_walk.py", "serve", "--port", str(port), "--token", TOKEN],
        cwd=REPO, env={**os.environ, "HOME": home}, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
    )
    log: list = []
    try:
        for _ in range(90):
            try:
                if call(base, "GET", "/api/projects")[0] == 200:
                    break
            except Exception:
                pass
            time.sleep(1)
        log.append(("remote on", call(base, "PUT", "/api/settings/remote", {"enabled": True})))
        s, desk = call(base, "POST", "/api/settings/remote/credentials",
                       {"identity": "desk-agent", "palette": "DESK", "ttl_seconds": 43200})
        log.append(("issue desk-agent", s, {k: v for k, v in desk.items() if k != "token"}))
        s, sweep = call(base, "POST", "/api/settings/remote/credentials",
                        {"identity": "sweep-runner", "palette": "PROJECT", "ttl_seconds": 86400})
        log.append(("issue sweep-runner", s, {k: v for k, v in sweep.items() if k != "token"}))
        used = call(base, "POST", "/api/mcp", {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                                               "params": {"name": "meeting.list", "arguments": {}}}, token=desk["token"])
        log.append(("desk-agent uses /api/mcp", used[0]))
        log.append(("desk grant desk-agent", call(base, "PUT", "/api/settings/remote/delegations/desk-agent", {})[0]))
        for name in ("Payments ledger cutover", "Hiring loop"):
            s, body = call(base, "POST", "/api/projects", {"name": name})
            log.append((f"create {name}", s, (body or {}).get("project", {}).get("id") if isinstance(body, dict) else body))
        s, wire = call(base, "GET", "/api/settings/remote")
        s2, projects = call(base, "GET", "/api/projects")
        (FIX / "remote-wire.json").write_text(json.dumps(wire, indent=2, sort_keys=True) + "\n")
        slim = [{"id": p["id"], "name": p["name"], "is_archived": p.get("is_archived")} for p in projects["projects"]]
        (FIX / "projects.json").write_text(json.dumps(slim, indent=2) + "\n")
        (FIX / "produce-log.json").write_text(json.dumps({"home_is_isolated": home, "steps": log}, indent=2, default=str) + "\n")
        print(json.dumps(log, indent=2, default=str))
        print(json.dumps(wire, indent=2))
    finally:
        hub.terminate()
        try:
            hub.communicate(timeout=20)
        except Exception:
            hub.kill()


if __name__ == "__main__":
    main()
