"""PHILO-12-02 canvas rig: the hub calls and the seed through its REAL routes."""
from __future__ import annotations

import json
import time
import os
import urllib.error
import urllib.request
from pathlib import Path

TOKEN = "philo12-canvas"
PROJECT = "Payments ledger cutover"
BARE_PROJECT = "Vendor onboarding"


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


def seed_hub(hub: str, folder: str, brief: bool = True) -> dict:
    seed: dict = {}
    s, p = hub_api(hub, "POST", "/api/projects", {"name": PROJECT})
    pid = p["project"]["id"]
    hub_api(hub, "POST", f"/api/projects/{pid}/meetings/m-sync", {})
    hub_api(hub, "POST", f"/api/projects/{pid}/items", {"item_type": "milestone", "title": "Cutover rehearsal"})
    steps = []
    for n in range(2):   # two published updates: the latest is the one a send names (G6, G9)
        if n:   # the second update carries one more line, so the boards tell the two apart; and it is
            # published a second later: published_at ties at the second, and on a tie the list order is
            # not defined (README N3)
            time.sleep(1.2)
            hub_api(hub, "POST", f"/api/projects/{pid}/items", {"item_type": "milestone", "title": "Old ledger frozen"})
        s1, d = hub_api(hub, "POST", f"/api/projects/{pid}/updates/draft", {"generator": "deterministic"})
        s2, r = hub_api(hub, "POST", f"/api/updates/{d['update']['id']}/publish", {})
        steps.append([s1, s2, d["update"]["id"], r if s2 >= 400 else None])
    _, lst = hub_api(hub, "GET", f"/api/projects/{pid}/updates")
    pub = [u for u in lst["updates"] if (u.get("lifecycle") or u.get("status")) == "published"]
    seed["project"], seed["update_steps"] = pid, steps
    # The latest published update: the newest published_at; on a tie the list's own order (newest
    # first), exactly as the Floor's read (p12.ts) chooses. seed["updates"] = [the other one, the latest].
    latest = max(pub, key=lambda u: str(u.get("published_at") or ""))["id"] if pub else steps[-1][2]
    seed["updates"] = [next(st[2] for st in steps if st[2] != latest), latest]
    _, p2 = hub_api(hub, "POST", "/api/projects", {"name": BARE_PROJECT})
    seed["bare_project"] = p2["project"]["id"]   # no published update (the NO PUBLISHED UPDATE tag)
    s, dec = hub_api(hub, "POST", "/api/decisions", {
        "title": "Freeze the old ledger on Nov 3", "status": "accepted", "deciders": ["Karol", "Priya"],
        "context_markdown": "The cutover rehearsal showed two write paths into the old ledger.",
        "decision_markdown": "Freeze the old ledger on Nov 3. All writes go to the new ledger after that day.",
        "consequences_markdown": "- Finance runs one extra reconciliation.\n- Rollback window closes Nov 10."})
    seed["decision"] = dec["decision"]["id"]
    if brief:
        s, b = hub_api(hub, "POST", "/api/brief/generate", {})
        seed["brief"] = b.get("id") if isinstance(b, dict) else None
    s, fd = hub_api(hub, "POST", "/api/channels/destinations", {"name": "Team folder", "channel": "file", "folder": folder})
    seed["folder_destination"] = fd["destination"]["id"]
    return seed
