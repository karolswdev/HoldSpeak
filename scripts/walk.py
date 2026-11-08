#!/usr/bin/env python3
"""The Walk: make a guided feedback walk on the owner's hub, and read it back.

    uv run python scripts/walk.py new docs/walks/2026-11-07-wave-two.json
    uv run python scripts/walk.py read <id>

``new`` posts the script to the local hub (the owner token from
``~/.config/holdspeak/config.json`` meeting.web_auth_token) and prints the
walk id and the two links, Tailscale first, each on its own line. ``read``
prints each answer as one plain line. Docs: docs/walks.md.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

HUB = os.environ.get("HOLDSPEAK_HUB", "http://127.0.0.1:8765")


def _tailnet() -> str:
    """The hub's address on the tailnet: HOLDSPEAK_TAILNET, else this machine's
    Tailscale IPv4 (the MagicDNS name does not resolve on every tailnet; the IP
    always does), else the local address."""
    given = os.environ.get("HOLDSPEAK_TAILNET")
    if given:
        return given
    for cli in ("tailscale", "/opt/homebrew/bin/tailscale", "/usr/local/bin/tailscale"):
        try:
            out = subprocess.run([cli, "ip", "-4"], capture_output=True, text=True, timeout=5)
        except (OSError, subprocess.TimeoutExpired):
            continue
        ip = out.stdout.strip().splitlines()[0].strip() if out.returncode == 0 and out.stdout.strip() else ""
        if ip:
            return f"http://{ip}:8765"
    return HUB


TAILNET = _tailnet()


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
    elif len(argv) == 2 and argv[0] == "read":
        read(argv[1])
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
