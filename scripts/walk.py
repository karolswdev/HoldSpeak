#!/usr/bin/env python3
"""The Walk: make a guided feedback walk on the owner's hub, and read it back.

    uv run python scripts/walk.py new docs/walks/2026-11-07-wave-two.json
    uv run python scripts/walk.py apps
    uv run python scripts/walk.py read <id>

``new`` posts the script to the local hub (the owner token from
``~/.config/holdspeak/config.json`` meeting.web_auth_token) and prints the
walk id and the two links, Tailscale first, each on its own line. ``read``
prints each answer as one plain line. ``apps`` posts every app's own walk
(``web/src/desk/walks/<name>.walk.json``, declared in
``web/src/desk/applications.ts``) as one linked walk, each app opened first,
and prints its two links. Docs: docs/walks.md.
"""
from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APPLICATIONS = ROOT / "web" / "src" / "desk" / "applications.ts"
WALKS = ROOT / "web" / "src" / "desk" / "walks"
# `"chair:needs": "needs"` in CHAIR_WALKS and `walk: "programs"` on a manifest
# row: the walks the desk declares, in the order of the file.
_DECLARED = re.compile(r'"chair:[a-z-]+":\s*"([a-z0-9-]+)"|\bwalk:\s*"([a-z0-9-]+)"')

HUB = os.environ.get("HOLDSPEAK_HUB", "http://127.0.0.1:8765")


# The hub's address on the tailnet (owner, 2026-11-08: "Need the tailscale dns.
# Not the ip."): Tailscale Serve proxies https://<MagicDNS name> (443) to the
# hub, a secure context for the mic and the viewport capture. The name
# resolves through Tailscale's resolver on his devices (a plain `host` on the
# Mac says NXDOMAIN; that is the system resolver, not the tailnet).
TAILNET = os.environ.get("HOLDSPEAK_TAILNET", "https://karols-macbook-pro.tailad9943.ts.net")


def _token() -> str:
    path = Path.home() / ".config" / "holdspeak" / "config.json"
    try:
        token = json.loads(path.read_text(encoding="utf-8"))["meeting"]["web_auth_token"]
    except (OSError, KeyError, TypeError, ValueError):
        sys.exit(f"No owner token in {path} (meeting.web_auth_token).")
    return str(token)


def _call(method: str, path: str, body: object | None = None) -> dict:
    data = json.dumps(body).encode("utf-8") if body is not None else None
    request = urllib.request.Request(f"{HUB}{path}", data=data, method=method, headers={
        "X-HoldSpeak-Token": _token(), "Content-Type": "application/json", "Accept": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")
        sys.exit(f"The hub refused ({exc.code}): {detail}")
    except urllib.error.URLError as exc:
        sys.exit(f"The hub at {HUB} does not answer: {exc.reason}")


def new(script_path: str) -> None:
    script = json.loads(Path(script_path).read_text(encoding="utf-8"))
    made = _call("POST", "/api/walks", script)
    print(f"walk {made['id']}")
    print(f"{TAILNET}{made['url_path']}")
    print(f"{HUB}{made['url_path']}")


def declared_walks(root: Path = ROOT) -> list[str]:
    """The app walks the desk declares, in the order of applications.ts."""
    text = (root / "web" / "src" / "desk" / "applications.ts").read_text(encoding="utf-8")
    return [chair or row for chair, row in _DECLARED.findall(text)]


def compose_apps(root: Path = ROOT) -> dict:
    """One linked walk of every app's own walk: each opens its app first."""
    steps: list[dict] = []
    for name in declared_walks(root):
        script = json.loads((root / "web" / "src" / "desk" / "walks" / f"{name}.walk.json").read_text(encoding="utf-8"))
        first, *rest = script["steps"]
        steps.append({"open": dict(script["open"]), **first})
        steps.extend(rest)
        steps[-1] = {**steps[-1], "ask": dict(script["review"])}
    return {"title": "Every app, its own walk", "steps": steps}


def apps() -> None:
    made = _call("POST", "/api/walks", compose_apps())
    print(f"walk {made['id']}")
    print(f"{TAILNET}{made['url_path']}")
    print(f"{HUB}{made['url_path']}")


def read(walk_id: str) -> None:
    walk = _call("GET", f"/api/walks/{walk_id}")
    answers = walk.get("answers") or {}
    print(f"{walk.get('title')} · {len(answers)} of {sum(1 for s in walk.get('steps', []) if 'ask' in s)} asked")
    for step in walk.get("steps", []):
        ask = step.get("ask")
        if not ask:
            continue
        got = answers.get(ask["ref"])
        if not got:
            print(f"{ask['ref']}: no answer")
            continue
        line = f"{ask['ref']}: {got['choice']}"
        if got.get("words"):
            line += f" · {got['words']}"
        if got.get("shot"):
            line += f" · {Path(walk['directory']) / got['shot']}"
        print(line)


def main(argv: list[str]) -> None:
    if len(argv) == 2 and argv[0] == "new":
        new(argv[1])
    elif argv == ["apps"]:
        apps()
    elif len(argv) == 2 and argv[0] == "read":
        read(argv[1])
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
