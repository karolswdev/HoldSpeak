#!/usr/bin/env python3
"""A fake ai-phone CLI for the Calls tests: a real separate process.

The shapes are ai-phone's own (github.com/oxnw/ai-phone at 436f9f1b:
``docs/usage.md#agent-commands``, ``src/ai_phone/cli_call.py``,
``calls.py`` ``CallRecord.result()``, ``daemon.py`` ``_cmd_listen`` /
``_cmd_say`` / ``_cmd_hangup``, ``control/protocol.py`` EXIT). No ai-phone
code is copied; this replays what its commands print.

    FAKE_AI_PHONE_SCRIPT=<script.json>  the scenario (read once, then kept in the state file)
    FAKE_AI_PHONE_STATE=<state.json>    what has happened (each command reads and writes it)

The scenario: ``{"listen": [<event>, ...], "call": <event>?}``. A listen
event is ``{"kind": "incoming", "remote": ...}``, ``{"kind": "heard", "text": ...}``,
``{"kind": "ended"}`` (them), or ``{"exit": 10}`` (a timeout) / ``{"exit": 9}``.
With nothing left, ``listen`` on a call ends it (they hung up); without a
call it times out (exit 10) after a short wait. ``call`` answers unless the
scenario's ``call`` says ``{"exit": 6}`` (no answer) or another code.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

EXIT_USAGE, EXIT_NOT_RUNNING, EXIT_LISTEN_TIMEOUT, EXIT_NO_CALL = 2, 9, 10, 11


def _paths() -> tuple[Path, Path]:
    return Path(os.environ["FAKE_AI_PHONE_SCRIPT"]), Path(os.environ["FAKE_AI_PHONE_STATE"])


def _load() -> dict:
    script, state = _paths()
    if state.exists():
        return json.loads(state.read_text())
    scenario = json.loads(script.read_text())
    return {"listen": list(scenario.get("listen") or []), "call": scenario.get("call"),
            "active": None, "calls": {}, "log": [], "seq": 0}


def _save(doc: dict) -> None:
    _, state = _paths()
    tmp = state.with_suffix(".tmp")
    tmp.write_text(json.dumps(doc))
    tmp.replace(state)


def _emit(obj: dict) -> None:
    print(json.dumps(obj), flush=True)


def _fail(error: str, code: int) -> int:
    _emit({"ok": False, "error": error, "code": code})
    return code


def _new_call(doc: dict, *, direction: str, remote: str, mode: str = "relay") -> dict:
    doc["seq"] += 1
    call_id = f"{0xc0f000 + doc['seq']:06x}"
    now = time.time()
    record = {"call_id": call_id, "mode": mode, "direction": direction, "line": "main", "remote": remote,
              "outcome": None, "detail": "", "ended_by": None, "created_at": now, "answered_at": now,
              "ended_at": None, "transcript": []}
    doc["calls"][call_id] = record
    doc["active"] = call_id
    return record


def _end(doc: dict, record: dict, ended_by: str) -> dict:
    if record["ended_at"] is None:
        record["ended_at"] = time.time()
        record["outcome"] = "completed"
        record["ended_by"] = ended_by
    if doc.get("active") == record["call_id"]:
        doc["active"] = None
    result = dict(record)
    result["duration_sec"] = round(record["ended_at"] - record["answered_at"], 1)
    return result


def _call_of(doc: dict, call_id: str | None) -> dict | None:
    return doc["calls"].get(call_id) if call_id else doc["calls"].get(doc.get("active") or "")


def cmd_listen(a, doc: dict) -> int:
    record = _call_of(doc, a.call)
    if a.call and record is None:
        return _fail(f"no call {a.call}", EXIT_NO_CALL)
    if not doc["listen"]:
        if record is not None and record["ended_at"] is None:
            result = _end(doc, record, "them")
            _emit({"ok": True, "kind": "ended", **result})
            return 0
        time.sleep(min(float(a.timeout_sec), 0.2))
        _emit({"ok": True, "kind": "timeout"})
        return EXIT_LISTEN_TIMEOUT
    event = doc["listen"].pop(0)
    if "exit" in event:
        code = int(event["exit"])
        if code == EXIT_LISTEN_TIMEOUT:
            _emit({"ok": True, "kind": "timeout"})
        else:
            _emit({"ok": False, "error": event.get("error") or "fake failure", "code": code})
        return code
    kind = event.get("kind")
    if kind == "incoming":
        record = _new_call(doc, direction="in", remote=str(event.get("remote") or "sip:+15555550100@sip.carrier.example"))
        _emit({"ok": True, "kind": "incoming", "call_id": record["call_id"], "line": record["line"], "remote": record["remote"]})
        return 0
    if record is None:
        return _fail("no call in progress", EXIT_NO_CALL)
    if kind == "heard":
        text = str(event.get("text") or "")
        record["transcript"].append({"who": "them", "text": text, "at": time.time(), "interrupted": False})
        _emit({"ok": True, "kind": "heard", "text": text})
        return 0
    if kind == "ended":
        result = _end(doc, record, "them")
        _emit({"ok": True, "kind": "ended", **result})
        return 0
    return _fail(f"unknown scenario event {event!r}", EXIT_USAGE)


def cmd_say(a, doc: dict) -> int:
    text = " ".join(a.text).strip()
    if not text or len(text) > 2000:
        return _fail("say needs 1 to 2000 characters of text", EXIT_USAGE)
    record = _call_of(doc, a.call)
    if record is None:
        return _fail("no call in progress", EXIT_NO_CALL)
    if record["ended_at"] is not None:
        return _fail(f"call {record['call_id']} has ended", EXIT_NO_CALL)
    record["transcript"].append({"who": "agent", "text": text, "at": time.time(), "interrupted": False})
    _emit({"ok": True, "result": "said", "call_id": record["call_id"]})
    return 0


def cmd_hangup(a, doc: dict) -> int:
    record = _call_of(doc, a.call)
    if record is None:
        return _fail("no call in progress", EXIT_NO_CALL)
    if a.say:
        record["transcript"].append({"who": "agent", "text": a.say, "at": time.time(), "interrupted": False})
    result = _end(doc, record, "hangup_command")
    _emit({"ok": True, **result})
    return 0


def cmd_call(a, doc: dict) -> int:
    planned = doc.get("call") or {}
    code = int(planned.get("exit", 0))
    if code:
        _emit({"ok": False, "outcome": planned.get("outcome") or "no_answer",
               "detail": planned.get("detail") or "", "code": code})
        return code
    record = _new_call(doc, direction="out", remote=a.target)
    print(json.dumps({"event": "created", "call_id": record["call_id"]}), file=sys.stderr, flush=True)
    _emit({"ok": True, "call_id": record["call_id"], "mode": "relay", "outcome": "answered"})
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="ai-phone")
    sub = p.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("call"); c.add_argument("target"); c.add_argument("--relay", action="store_true")
    c.add_argument("--line"); c.add_argument("--timeout-sec", type=float, default=30); c.add_argument("--json", action="store_true")
    ls = sub.add_parser("listen"); ls.add_argument("--call"); ls.add_argument("--timeout-sec", type=float, default=60)
    ls.add_argument("--json", action="store_true")
    sy = sub.add_parser("say"); sy.add_argument("text", nargs="+"); sy.add_argument("--call"); sy.add_argument("--json", action="store_true")
    hu = sub.add_parser("hangup"); hu.add_argument("--call"); hu.add_argument("--say"); hu.add_argument("--json", action="store_true")
    a = p.parse_args(argv)
    if os.environ.get("FAKE_AI_PHONE_DOWN") == "1":
        return _fail("ai-phone is not running (start it with `ai-phone run`)", EXIT_NOT_RUNNING)
    doc = _load()
    doc["log"].append(list(argv if argv is not None else sys.argv[1:]))
    try:
        return {"listen": cmd_listen, "say": cmd_say, "hangup": cmd_hangup, "call": cmd_call}[a.cmd](a, doc)
    finally:
        _save(doc)


if __name__ == "__main__":
    sys.exit(main())
