"""A tmux double at the process boundary, for the launch-receipt boards (shoot_built.py).

Installed as `tmux` (and this file's `claude` twin, CLAUDE=1) first on the HUB's PATH
only. The hub runs it exactly as it runs tmux; it keeps its sessions in a state folder
(F1_TMUX_STATE) and logs every argv there. Nothing reaches a real tmux or a real agent.

- `new-session ... CMD` records the session and runs CMD in the background with this
  folder first on PATH, so CMD's `exec claude ...` runs the claude twin.
- The claude twin waits for `<state>/register` and then reports SessionStart through the
  product's own hook ingest (`holdspeak agent-hook ingest --agent claude`); the hub's
  rider binding then registers the launch (first_message.py) and types the brief.
- Typing the brief (load-buffer / paste-buffer / send-keys) waits while `<state>/hold`
  exists (the receipt reads DELIVERING), and fails while `<state>/fail` exists (the
  receipt reads NOT SENT).
"""
from __future__ import annotations

import fcntl
import json
import os
import re
import shlex
import subprocess
import sys
import time
from pathlib import Path

STATE = Path(os.environ.get("F1_TMUX_STATE") or "/tmp/f1-tmux-state")
HERE = Path(__file__).resolve().parent


def _load() -> dict:
    try:
        return json.loads((STATE / "sessions.json").read_text())
    except (OSError, ValueError):
        return {"sessions": {}, "next": 1}


def _save(doc: dict) -> None:
    (STATE / "sessions.json").write_text(json.dumps(doc))


def _fmt(fmt: str, name: str, pane: dict) -> str:
    values = {"pane_id": pane["id"], "session_name": name, "pane_current_path": pane["path"],
              "pane_pid": str(pane.get("pid") or 0), "pane_current_command": "claude", "pane_dead": "0",
              "window_index": "0", "pane_index": "0", "session_id": "$1", "window_id": "@1"}
    return re.sub(r"#\{([a-z_]+)\}", lambda m: values.get(m.group(1), ""), fmt)


def _target(doc: dict, target: str) -> tuple[str, dict] | None:
    for name, pane in doc["sessions"].items():
        if target in (pane["id"], name) or target.split(":")[0] == name:
            return name, pane
    return None


def tmux(argv: list[str]) -> int:
    STATE.mkdir(parents=True, exist_ok=True)
    with (STATE / "argv.log").open("a") as log:
        log.write(json.dumps(argv) + "\n")
    with (STATE / "lock").open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        doc = _load()
        verb = argv[0] if argv else ""
        opt = lambda flag: argv[argv.index(flag) + 1] if flag in argv else ""  # noqa: E731
        if verb == "new-session":
            name = opt("-s")
            if name in doc["sessions"]:
                print(f"duplicate session: {name}", file=sys.stderr)
                return 1
            command = argv[-1]
            path = shlex.split(command)[1] if command.startswith("cd ") else str(Path.home())
            pane = {"id": f"%{doc['next']}", "path": path}
            doc["next"] += 1
            env = {**os.environ, "PATH": f"{STATE / 'bin'}:{os.environ.get('PATH', '')}", "TMUX_PANE": pane["id"]}
            proc = subprocess.Popen(["/bin/bash", "-c", command], env=env, stdout=subprocess.DEVNULL,
                                    stderr=subprocess.DEVNULL, start_new_session=True)
            pane["pid"] = proc.pid
            doc["sessions"][name] = pane
            _save(doc)
            return 0
        if verb in ("has-session",):
            return 0 if _target(doc, opt("-t")) else 1
        if verb == "list-panes":
            fmt = opt("-F") or "#{pane_id}"
            rows = list(doc["sessions"].items()) if "-a" in argv else ([_target(doc, opt("-t"))] if _target(doc, opt("-t")) else [])
            if not rows:
                return 1
            print("\n".join(_fmt(fmt, name, pane) for name, pane in rows))
            return 0
        if verb == "display-message":
            hit = _target(doc, opt("-t"))
            if not hit:
                return 1
            print(_fmt(argv[-1] if argv[-1].startswith("#") else "#{pane_id}", *hit))
            return 0
        if verb == "capture-pane":
            print("claude up")
            return 0
        if verb == "kill-session":
            hit = _target(doc, opt("-t"))
            if hit:
                doc["sessions"].pop(hit[0], None)
                _save(doc)
            return 0
    if verb in ("load-buffer", "paste-buffer", "send-keys", "set-buffer"):
        while (STATE / "hold").exists():
            time.sleep(0.2)
        if (STATE / "fail").exists():
            print("can't find pane", file=sys.stderr)
            return 1
        if verb == "load-buffer" and argv[-1] == "-":
            sys.stdin.read()
        return 0
    return 0


def claude() -> int:
    """The agent twin: waits for the rig's word, then reports SessionStart."""
    while not (STATE / "register").exists():
        time.sleep(0.3)
    payload = {"session_id": f"f1-{os.getpid()}", "cwd": os.getcwd(), "hook_event_name": "SessionStart"}
    holdspeak = os.environ.get("F1_HOLDSPEAK") or "holdspeak"
    subprocess.run([holdspeak, "agent-hook", "ingest", "--agent", "claude"], input=json.dumps(payload), text=True,
                   capture_output=True, timeout=60)
    while True:
        time.sleep(5)


if __name__ == "__main__":
    sys.exit(claude() if os.environ.get("F1_TWIN") == "claude" or Path(sys.argv[0]).name == "claude"
             else tmux(sys.argv[1:]))
