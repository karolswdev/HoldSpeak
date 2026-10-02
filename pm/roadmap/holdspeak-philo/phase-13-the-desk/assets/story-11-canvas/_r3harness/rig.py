"""PHILO-13-11 canvas rig: the hub boot, the seed through the REAL routes, and the servers.

A REAL hub (scripts/graph_walk.py serve) on HOME=tempfile.mkdtemp(prefix="p13c1-", dir="/tmp"),
seeded before boot through the product's producers (seed_db.py, the Phase 13
grounding seed) and after boot through its HTTP routes (seed_hub). The PRODUCT
app is served by vite with harness/vite.config.mjs. Nothing leaves the machine.
"""
from __future__ import annotations

import json
import os
import shutil
import socket
import subprocess
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[6]
WEB = REPO / "web"
PY = os.environ.get("CANVAS_PYTHON") or str(REPO / ".venv/bin/python")
TOKEN = "philo13-c1"


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def wait_http(url: str, headers: dict[str, str] | None = None, timeout: float = 120) -> None:
    end = time.time() + timeout
    while time.time() < end:
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=headers or {}), timeout=2) as r:
                if r.status < 500:
                    return
        except Exception:
            time.sleep(0.4)
    raise RuntimeError(f"not up: {url}")


def hub_api(base: str, method: str, path: str, body=None):
    req = urllib.request.Request(
        f"{base}{path}", method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, json.loads(r.read().decode() or "null")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:400]


def seed_hub(hub: str, home: str) -> dict:
    """The records the grounding made through routes after boot (faces-surfaces-seed_api)."""
    out: dict = {}
    s, wb = hub_api(hub, "POST", "/api/workbenches", {"name": "Ledger cutover bench", "description": "Agents on the cutover"})
    wid = wb["workbench"]["id"] if isinstance(wb, dict) and "workbench" in wb else None
    out["workbench"] = wid
    items = []
    for t in ["Draft rollback runbook", "Check reconciliation timings", "Write cutover comms", "Old sampling spike", "Rerun shard benchmark"]:
        s, it = hub_api(hub, "POST", f"/api/workbenches/{wid}/items", {"title": t})
        items.append(it.get("item", {}).get("id") if isinstance(it, dict) else None)
    out["items"] = items
    # two DONE items, so "Clear done" (bulk park) has something to park
    out["done"] = [hub_api(hub, "PUT", f"/api/workbenches/{wid}/items/{i}", {"status": "done"})[0] for i in items[1:3]]
    # Inside the scratch HOME, so the face reads ~/Documents/HoldSpeak/Team updates (the product
    # shows a home folder as ~; the canvas maps its scratch HOME the same way, vite seat channels.ts).
    folder = os.path.join(home, "Documents", "HoldSpeak", "Team updates")
    os.makedirs(folder, exist_ok=True)
    s, d = hub_api(hub, "POST", "/api/channels/destinations", {"name": "Team updates", "channel": "file", "folder": folder})
    out["destination"] = s
    return out


class Stack:
    """One hub + one vite on one scratch HOME. `with Stack() as st:` removes the HOME at exit."""

    def __init__(self, mode: str = "proposal"):
        self.mode = mode
        self.procs: list[subprocess.Popen] = []

    def __enter__(self):
        self.home = tempfile.mkdtemp(prefix="p13c1-", dir="/tmp")
        self.hub_port, self.port = free_port(), free_port()
        self.hub = f"http://127.0.0.1:{self.hub_port}"
        env = {**os.environ, "HOME": self.home, "PYTHONPATH": str(REPO),
               "HOLDSPEAK_PEOPLE_KEYSTORE_FILE": f"{self.home}/people.key"}
        seeded = subprocess.run([PY, str(HERE / "seed_db.py")], cwd=REPO, env=env, capture_output=True, text=True, timeout=300)
        if seeded.returncode:
            raise RuntimeError(f"seed_db failed: {seeded.stderr[-2000:]}")
        self.seed = json.loads(seeded.stdout.strip().splitlines()[-1])
        self.procs.append(subprocess.Popen([PY, "scripts/graph_walk.py", "serve", "--port", str(self.hub_port), "--token", TOKEN],
                                           cwd=REPO, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL))
        self.vlog = Path(self.home) / "vite.log"
        self.procs.append(subprocess.Popen([str(WEB / "node_modules/.bin/vite"), "--config", str(HERE / "vite.config.mjs")], cwd=WEB,
                                           env={**os.environ, "HUB": self.hub, "CANVAS_PORT": str(self.port), "CANVAS_MODE": self.mode},
                                           stdout=self.vlog.open("w"), stderr=subprocess.STDOUT))
        wait_http(f"{self.hub}/api/projects", {"Authorization": f"Bearer {TOKEN}"})
        wait_http(f"http://127.0.0.1:{self.port}/")
        self.guard = []
        if self.mode == "proposal":
            for _ in range(160):
                self.guard = [ln for ln in self.vlog.read_text().splitlines() if "SEAT GUARD" in ln]
                if self.guard or self.procs[-1].poll() is not None:
                    break
                time.sleep(0.5)
            if not self.guard or "every anchor met" not in self.guard[0]:
                raise RuntimeError(f"seat guard: {self.guard or self.vlog.read_text()[-1500:]}")
        self.seed.update(seed_hub(self.hub, self.home))
        self.url = f"http://127.0.0.1:{self.port}/?token={TOKEN}"
        return self

    def __exit__(self, *exc):
        for p in self.procs:
            p.terminate()
        for p in self.procs:
            try:
                p.wait(timeout=10)
            except Exception:
                p.kill()
        shutil.rmtree(self.home, ignore_errors=True)   # law: a run removes its own scratch HOME
        return False
