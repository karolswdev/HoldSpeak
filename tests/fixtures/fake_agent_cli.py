"""Fake ``claude`` and ``codex`` executables for CLI engine tests (Betterment E1).

Tests never run the owner's real agent CLIs: they would use his sign-in and
bill him. ``install_fake_agent_clis(bin_dir)`` writes two scripts into a
folder inside the test's temp dir; the test puts that folder first on PATH.

Each call appends one JSON line to ``<bin>/<name>-calls.jsonl``: argv, cwd,
the cwd's entries, the stdin prompt, the pid, and (M1) the run credential,
hub URL and ``--mcp-config`` path (with its mode) the child was given. ``set_mode(bin_dir, name,
mode)`` picks the behaviour: ``answer`` (default), ``sleep`` (60 s, for the
timeout kill), ``fail`` (exit 1) or ``error`` (Claude's ``is_error`` result).

Betterment M1: the fakes speak MCP to the hub the way the real CLIs are told
to. ``set_tool_plan(bin_dir, name, [{"name": ..., "arguments": ...}])`` makes
each next run (``once=True``: only the next one) call those tools over the HoldSpeak server its argv names
(Claude Code: the ``--mcp-config`` file, ``${VAR}`` expanded from the
environment; Codex: ``-c mcp_servers.holdspeak.url`` and its
``bearer_token_env_var``). Each call's HTTP status and JSON-RPC answer go to
``<bin>/<name>-mcp.jsonl`` with the token and config the run used, and the
answer is the JSON list of the tool results (for Claude, unless
``set_claude_answer`` gave one). With ``--json`` the fake Codex
prints ``codex exec --json`` events (``item.completed`` agent_message,
``turn.completed`` usage).
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

CLAUDE_ANSWER = "FAKE CLAUDE ANSWER"
CODEX_ANSWER = "FAKE CODEX ANSWER"
CLAUDE_COST_USD = 0.0123

_SCRIPT = '''#!{python}
import json, os, re, sys, time, pathlib, urllib.request, urllib.error
here = pathlib.Path(__file__).resolve().parent
name = {name!r}
prompt = sys.stdin.read()
with (here / (name + "-calls.jsonl")).open("a") as log:
    argv = sys.argv[1:]
    config = argv[argv.index("--mcp-config") + 1] if "--mcp-config" in argv else None
    log.write(json.dumps({{"argv": argv, "cwd": os.getcwd(), "cwd_entries": os.listdir("."),
                          "prompt": prompt, "pid": os.getpid(),
                          "credential": os.environ.get("HOLDSPEAK_AGENT_CREDENTIAL", ""),
                          "hub_url": os.environ.get("HOLDSPEAK_HUB_URL", ""),
                          "mcp_config": config,
                          "mcp_config_mode": oct(os.stat(config).st_mode & 0o777) if config else None}}) + "\\n")
mode_file = here / (name + "-mode")
mode = mode_file.read_text().strip() if mode_file.exists() else "answer"
if mode == "sleep":
    time.sleep(60)
if mode == "fail":
    print("Invalid API key. Please run /login", file=sys.stderr)
    sys.exit(1)

def expand(text):
    return re.sub(r"\\$\\{{(\\w+)\\}}", lambda m: os.environ.get(m.group(1), ""), text)

def server():
    argv = sys.argv[1:]
    if name == "claude":
        if "--mcp-config" not in argv:
            return None
        path = argv[argv.index("--mcp-config") + 1]
        entry = json.loads(pathlib.Path(path).read_text())["mcpServers"]["holdspeak"]
        headers = {{k: expand(v) for k, v in entry.get("headers", {{}}).items()}}
        return {{"url": expand(entry["url"]), "headers": headers, "config": path}}
    settings = {{}}
    for i, part in enumerate(argv):
        if part == "-c" and i + 1 < len(argv) and "=" in argv[i + 1]:
            key, _, value = argv[i + 1].partition("=")
            settings[key] = value
    url = settings.get("mcp_servers.holdspeak.url")
    if url is None:
        return None
    variable = json.loads(settings["mcp_servers.holdspeak.bearer_token_env_var"])
    return {{"url": json.loads(url), "headers": {{"Authorization": "Bearer " + os.environ.get(variable, "")}},
            "config": None}}

def rpc(target, message, timeout):
    request = urllib.request.Request(target["url"], data=json.dumps(message).encode(), method="POST",
                                     headers={{**target["headers"], "Content-Type": "application/json"}})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
            return response.status, (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        try:
            return exc.code, json.loads(raw) if raw else None
        except ValueError:
            return exc.code, None
    except Exception as exc:
        return 0, {{"transport_error": type(exc).__name__ + ": " + str(exc)}}

answer = None
plan_file = here / (name + "-plan.json")
if plan_file.exists():
    plan = json.loads(plan_file.read_text())
    if plan.get("once"):
        plan_file.unlink()
    target = server()
    results = []
    record = {{"server": None if target is None else {{"url": target["url"], "config": target["config"]}},
              "token": os.environ.get("HOLDSPEAK_AGENT_CREDENTIAL", ""), "calls": []}}
    if target is not None:
        timeout = float(plan.get("timeout", 30))
        status, init = rpc(target, {{"jsonrpc": "2.0", "id": 0, "method": "initialize", "params": {{
            "protocolVersion": "2025-06-18", "capabilities": {{}}, "clientInfo": {{"name": "fake-" + name}}}}}}, timeout)
        record["initialize"] = status
        for n, step in enumerate(plan["calls"], start=1):
            started = time.time()
            status, reply = rpc(target, {{"jsonrpc": "2.0", "id": n, "method": "tools/call", "params": {{
                "name": step["name"], "arguments": step.get("arguments", {{}})}}}}, timeout)
            record["calls"].append({{"name": step["name"], "status": status, "reply": reply,
                                    "seconds": round(time.time() - started, 3)}})
            results.append({{"name": step["name"], "status": status, "reply": reply}})
    with (here / (name + "-mcp.jsonl")).open("a") as log:
        log.write(json.dumps(record) + "\\n")
    answer = json.dumps(results)
    if (here / "claude-answer").exists() and name == "claude":
        answer = None  # set_claude_answer wins over the tool results
if name == "claude":
    if mode == "error":
        # Claude Code reports what a run cost even when it stops at its limit.
        print(json.dumps({{"type": "result", "subtype": "error_max_budget_usd", "is_error": True,
                          "total_cost_usd": {cost!r}}}))
        sys.exit(0)
    if answer is None:
        answer = (here / "claude-answer").read_text() if (here / "claude-answer").exists() else {claude_answer!r}
    print(json.dumps({{"type": "result", "subtype": "success", "is_error": False, "result": answer,
                      "total_cost_usd": {cost!r}, "usage": {{"input_tokens": 11, "output_tokens": 5}},
                      "modelUsage": {{"claude-fake-1": {{}}}}}}))
else:
    if answer is None:
        answer = {codex_answer!r}
    if "--json" in sys.argv[1:]:
        for event in (
            {{"type": "thread.started", "thread_id": "fake-thread"}},
            {{"type": "turn.started"}},
            {{"type": "item.completed", "item": {{"id": "item_0", "type": "agent_message", "text": answer}}}},
            {{"type": "turn.completed", "usage": {{"input_tokens": 46, "cached_input_tokens": 40,
                                                 "output_tokens": 7}}}},
        ):
            print(json.dumps(event))
    else:
        print(answer)
'''


def install_fake_agent_clis(bin_dir: Path) -> Path:
    bin_dir.mkdir(parents=True, exist_ok=True)
    for name in ("claude", "codex"):
        path = bin_dir / name
        path.write_text(_SCRIPT.format(
            python=sys.executable, name=name, claude_answer=CLAUDE_ANSWER,
            codex_answer=CODEX_ANSWER, cost=CLAUDE_COST_USD,
        ))
        path.chmod(0o755)
    return bin_dir


def set_mode(bin_dir: Path, name: str, mode: str) -> None:
    (bin_dir / f"{name}-mode").write_text(mode)


def set_tool_plan(
    bin_dir: Path, name: str, tool_calls: list[dict], *, timeout: float = 30.0, once: bool = False,
) -> None:
    """The next runs of *name* call these tools over the server their argv names
    (``once``: only the next run; an automation's memory call after it calls none)."""
    (bin_dir / f"{name}-plan.json").write_text(json.dumps({"calls": tool_calls, "timeout": timeout, "once": once}))


def mcp_runs(bin_dir: Path, name: str) -> list[dict]:
    """One record per run that had a tool plan: server, token, each call."""
    log = bin_dir / f"{name}-mcp.jsonl"
    if not log.exists():
        return []
    return [json.loads(line) for line in log.read_text().splitlines() if line.strip()]


def set_claude_answer(bin_dir: Path, text: str) -> None:
    (bin_dir / "claude-answer").write_text(text)


def calls(bin_dir: Path, name: str) -> list[dict]:
    log = bin_dir / f"{name}-calls.jsonl"
    if not log.exists():
        return []
    return [json.loads(line) for line in log.read_text().splitlines() if line.strip()]


def path_with(bin_dir: Path) -> str:
    return f"{bin_dir}{os.pathsep}{os.environ.get('PATH', '')}"


def process_gone(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return True
    except PermissionError:
        return False
    return False
