#!/usr/bin/env python3
"""Rehearse the Phase 5 loop from ordinary language through Codex.

This is a small closing rig for PHILO-5-04.  ``graph_walk.Hub`` owns the
runtime boundary and its canonical operation adapter owns every readback.
Codex is the only writer of the meeting, decision, Thought and brief.  The
driver may prepare the real model setting and move the producer clock; it
never creates a job object on Codex's behalf.

The run keeps its own HOME under the unique output directory.  Codex keeps
the caller's authentication HOME and receives the hub HOME only in the
stdio server configuration.  This distinction is deliberate: an isolated
hub must not replace the Codex account's home, and the owner's desk must
never be used by a rehearsal.
"""
from __future__ import annotations

import argparse
from contextlib import closing
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
from typing import Any
from urllib.parse import quote


REPO = Path(__file__).resolve().parents[1]
FIXTURE = REPO / "tests/fixtures/philo3_architect_meeting.wav"
ENGINE_URL = "http://192.168.1.43:8080"
TOKEN = "philo5-04-his-words"
AS = REPO / "scripts/astra"
MCP_COMMAND = REPO / ".venv/bin/holdspeak-mcp"

# Keep prompts in one place so the structural fence can inspect exactly what
# the owner would hear.  The prompts contain no application-operation names,
# MCP tool names, argument objects or test clock instructions.
PROMPTS: dict[str, str] = {
    "import": (
        "I have an architecture review recording at {fixture}. Import it into "
        "HoldSpeak, wait until the transcript is ready, and tell me when the "
        "meeting is ready for the next request."
    ),
    "summary": (
        "Please summarize the meeting we just imported. Keep the summary on its "
        "meeting record, and tell me when it is visible."
    ),
    "decision_thought": (
        "Put this decision on my list to review tomorrow: Keep summary retrieval "
        "on the local desk. Link it to the meeting. Create a Thought titled "
        "Phase 5 rehearsal with this body: "
        "The meeting loop stays on the local desk. Then edit that Thought so "
        "the body ends with: Saved after the meeting review. Save that edit and "
        "tell me what you recorded."
    ),
    "tomorrow_brief": "Now it is tomorrow. Make my brief and tell me what is on it.",
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _json_dump(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, default=str) + "\n")


def _write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value)


def _backup_db(source: Path, target: Path) -> None:
    """Keep committed WAL rows through SQLite's read-only backup API."""
    with closing(sqlite3.connect(source.resolve().as_uri() + "?mode=ro", uri=True)) as live:
        with closing(sqlite3.connect(target)) as snapshot:
            live.backup(snapshot)


def _unique_run_dir(root: Path, engine: str) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    base = root / f"{stamp}-his-words-{engine}"
    candidate = base
    suffix = 2
    while candidate.exists():
        candidate = root / f"{base.name}-{suffix}"
        suffix += 1
    candidate.mkdir(parents=True)
    return candidate


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="mode", required=True)
    run = sub.add_parser("run", help="run one fresh Codex rehearsal")
    run.add_argument("--out", required=True, help="parent directory for the unique run")
    run.add_argument("--engine", choices=("real", "replayed"), default="real")
    run.add_argument(
        "--engine-replay",
        type=Path,
        help="recorded provider reply for an explicitly labelled replayed run",
    )
    run.add_argument(
        "--codex-timeout",
        type=float,
        default=1800,
        help="maximum seconds for each ordinary-language Codex turn",
    )
    return parser


def _preflight(run_dir: Path, engine_url: str) -> dict[str, Any]:
    """Retain the real engine preflight as a curl transcript."""
    command = ["curl", "--fail", "--show-error", "--silent", "--max-time", "20",
               f"{engine_url.rstrip('/')}/v1/models"]
    result = subprocess.run(command, cwd=str(REPO), capture_output=True, text=True)
    transcript = "$ " + " ".join(command) + "\n"
    transcript += f"exit={result.returncode}\n"
    transcript += "stdout:\n" + result.stdout
    transcript += "\nstderr:\n" + result.stderr
    _write_text(run_dir / "engine-preflight-curl.txt", transcript)
    try:
        payload = json.loads(result.stdout)
    except (TypeError, ValueError):
        payload = None
    return {
        "command": command,
        "exit_code": result.returncode,
        "payload": payload,
        "stdout_sha256": hashlib.sha256(result.stdout.encode()).hexdigest(),
        "stderr": result.stderr[-1000:],
    }


def _effective_codex_config(run_dir: Path, hub_home: Path, auth_env: dict[str, str]) -> dict[str, Any]:
    """Ask Codex for the effective server config using the exact run overrides."""
    overrides = _codex_overrides(hub_home)
    command = ["codex", "mcp", "get", "holdspeak", "--json"]
    for override in overrides:
        command.extend(["-c", override])
    result = subprocess.run(
        command,
        cwd=str(REPO),
        env=auth_env,
        capture_output=True,
        text=True,
        timeout=60,
    )
    _write_text(
        run_dir / "effective-codex-config.txt",
        "$ " + " ".join(command) + "\n"
        + f"exit={result.returncode}\n"
        + result.stdout
        + ("\nstderr:\n" + result.stderr if result.stderr else ""),
    )
    try:
        effective: Any = json.loads(result.stdout)
    except (TypeError, ValueError):
        effective = {"raw": result.stdout}
    return {
        "command": command,
        "exit_code": result.returncode,
        "requested": _requested_config(hub_home),
        "effective": effective,
        "stderr": result.stderr[-1000:],
    }


def _requested_config(hub_home: Path) -> dict[str, Any]:
    """A machine-readable record of the full config requested from Codex."""
    return {
        "name": "holdspeak",
        "transport": "stdio",
        "command": str(MCP_COMMAND),
        "cwd": str(REPO),
        "args": [],
        "env": {"HOME": str(hub_home)},
        "required": True,
        "timeout": {"startup_seconds": 60, "tool_seconds": 900},
    }


def _codex_overrides(hub_home: Path) -> list[str]:
    """The overrides passed both to ``mcp get`` and ``scripts/astra``."""
    return [
        f"mcp_servers.holdspeak.command={MCP_COMMAND}",
        f"mcp_servers.holdspeak.cwd={REPO}",
        "mcp_servers.holdspeak.args=[]",
        "mcp_servers.holdspeak.required=true",
        f"mcp_servers.holdspeak.env.HOME={hub_home}",
        "mcp_servers.holdspeak.startup_timeout_sec=60",
        "mcp_servers.holdspeak.tool_timeout_sec=900",
    ]


def _copy_codex_artifacts(stage_dir: Path, wrapper_stdout: str, wrapper_stderr: str) -> dict[str, Any]:
    """Copy the wrapper's complete per-turn record into the run directory."""
    _write_text(stage_dir / "wrapper.stdout", wrapper_stdout)
    _write_text(stage_dir / "wrapper.stderr", wrapper_stderr)
    report_match = re.search(r"astra: report=(?P<path>.+)", wrapper_stdout)
    session_match = re.search(r"astra: session=(?P<sid>[0-9a-f-]+)", wrapper_stdout)
    report_path = Path(report_match.group("path")).resolve() if report_match else None
    source_dir = report_path.parent if report_path and report_path.exists() else None
    copied: list[str] = []
    if source_dir and source_dir.is_dir():
        for source in sorted(source_dir.iterdir()):
            if source.is_file():
                target = stage_dir / source.name
                shutil.copy2(source, target)
                copied.append(source.name)
    return {
        "wrapper_output_dir": str(source_dir) if source_dir else None,
        "session_id": session_match.group("sid") if session_match else None,
        "copied": copied,
    }


def _copy_rollout(stage_dir: Path, session_id: str | None, auth_env: dict[str, str]) -> str | None:
    """Retain the persisted Codex rollout without changing the auth HOME."""
    if not session_id:
        return None
    roots: list[Path] = []
    codex_home = auth_env.get("CODEX_HOME")
    if codex_home:
        roots.append(Path(codex_home))
    roots.append(Path(auth_env.get("HOME", "")) / ".codex")
    for root in roots:
        if not root.exists():
            continue
        for candidate in root.rglob(f"*{session_id}*"):
            if candidate.is_file() and "rollout" in candidate.name:
                target = stage_dir / "rollout.jsonl"
                shutil.copy2(candidate, target)
                return str(candidate)
    _write_text(stage_dir / "rollout-missing.txt",
                f"No persisted rollout filename containing session {session_id!r} was found.\n")
    return None


def _mcp_catalog() -> tuple[set[str], set[str]]:
    """Read the live MCP roster and technical argument keys safely."""
    # Import catalog code under a disposable HOME.  The fence runs before the
    # client turn and must never initialize a service against the caller's
    # desk merely to discover names.
    catalog_home = Path(tempfile.mkdtemp(prefix="philo5-04-catalog-"))
    old_home = os.environ.get("HOME")
    os.environ["HOME"] = str(catalog_home)
    try:
        from holdspeak.mcp.tools import TOOLS

        names: set[str] = set()
        arguments: set[str] = set()
        for tool in TOOLS:
            if not isinstance(tool, dict):
                continue
            if tool.get("name"):
                names.add(str(tool["name"]))
            schema = tool.get("inputSchema")
            properties = schema.get("properties") if isinstance(schema, dict) else None
            if isinstance(properties, dict):
                arguments.update(
                    str(key) for key in properties
                    if "_" in str(key)
                )
        return names, arguments
    finally:
        if old_home is None:
            os.environ.pop("HOME", None)
        else:
            os.environ["HOME"] = old_home
        shutil.rmtree(catalog_home, ignore_errors=True)


def _ordinary_language_fence(text: str) -> list[str]:
    """Return forbidden technical names found in a sent Codex brief.

    The wrapper's preamble is part of the sent brief and is checked with the
    owner's words.  A fixture path is the one deliberate technical value the
    owner is allowed to name.  Dates, clock adapters and offsets are never
    allowed to leak into the request.
    """
    terms: set[str] = set()
    operations_path = REPO / "docs/generated/operations.json"
    if operations_path.exists():
        try:
            payload = json.loads(operations_path.read_text())
            terms.update(
                str(row.get("name"))
                for row in payload.get("operations", [])
                if isinstance(row, dict) and row.get("name")
            )
        except (OSError, ValueError):
            terms.add("docs/generated/operations.json")
    mcp_names, mcp_arguments = _mcp_catalog()
    terms.update(mcp_names)
    terms.update(mcp_arguments)
    if operations_path.exists():
        try:
            payload = json.loads(operations_path.read_text())
            for row in payload.get("operations", []):
                schema = row.get("args_schema") if isinstance(row, dict) else None
                properties = schema.get("properties") if isinstance(schema, dict) else None
                if isinstance(properties, dict):
                    terms.update(str(key) for key in properties if "_" in str(key))
        except (OSError, ValueError):
            pass
    lowered = text.lower()
    found = sorted(term for term in terms if term.lower() in lowered)
    for technical in (
        "clock.python_wall", "advance_days", "producer clock", "clock offset", "offset", "clock",
    ):
        if technical in lowered:
            found.append(technical)
    if re.search(r"\b20\d{2}-\d{2}-\d{2}\b", text):
        found.append("calendar date")
    return sorted(set(found))


def _read_event_file(path: Path) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    if not path.exists():
        return events
    for line in path.read_text().splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if isinstance(event, dict):
            events.append(event)
    return events


def _codex_mcp_calls(stage_dir: Path) -> list[dict[str, Any]]:
    """Read every completed Codex MCP item, including refused calls.

    A refused server result is still a transport event that must be paired
    with the server's JSON-RPC response.  Dropping it would make a broken
    turn look clean merely because the producer rejected it.
    """
    calls: list[dict[str, Any]] = []
    for event in _read_event_file(stage_dir / "events.jsonl"):
        item = event.get("item")
        if not isinstance(item, dict) or item.get("type") != "mcp_tool_call":
            continue
        if item.get("server") != "holdspeak" or event.get("type") != "item.completed":
            continue
        if "result" in item:
            result = item.get("result")
        elif "error" in item:
            result = {"error": item.get("error")}
        else:
            result = None
        event_id = item.get("id") or item.get("call_id") or event.get("id")
        calls.append({
            "tool": item.get("tool"),
            "arguments": item.get("arguments") or {},
            "result": result,
            "error": item.get("error"),
            "event_id": event_id,
            "result_sha256": hashlib.sha256(
                json.dumps(_canonical_mcp_result(result), sort_keys=True, default=str).encode()
            ).hexdigest(),
        })
    return calls


def _http_exchange_records(hub: Any) -> list[dict[str, Any]]:
    """Read the graph rig's exact bounded HTTP transcript schema."""
    path = getattr(hub, "transcript_path", None)
    if not path:
        return []
    return _read_event_file(Path(path))


def _mcp_result(response: Any) -> Any:
    """Return the JSON-RPC result, preserving error responses."""
    if not isinstance(response, dict):
        return None
    if "result" in response:
        return response["result"]
    if "error" in response:
        return {"error": response["error"]}
    return None


def _canonical_mcp_result(result: Any) -> Any:
    """Project equivalent Codex/server MCP result envelopes to one shape.

    Codex records the client result as ``content`` plus
    ``structured_content: null`` and omits a false ``isError``.  The hub
    records the server result as ``content`` plus ``isError: false`` and omits
    the structured field.  Those are wire-format omissions, not semantic
    differences.  The projection fills only these explicit defaults and
    retains all nonempty content, structured content and error fields.
    """
    if not isinstance(result, dict):
        return {
            "value": result,
            "structured_content": None,
            "isError": False,
        }
    projected = dict(result)
    if "structured_content" not in projected:
        projected["structured_content"] = projected.pop("structuredContent", None)
    else:
        projected.pop("structuredContent", None)
    if "isError" not in projected:
        projected["isError"] = bool(projected.pop("is_error", False) or "error" in projected)
    else:
        projected.pop("is_error", None)
    return projected


# Codex 0.155 publishes three built-in MCP catalogue tools.  It records each
# one as an ``mcp_tool_call`` item for the named server, but on the wire each
# is a plain JSON-RPC resource method, not ``tools/call``.  Each maps to the
# JSON-RPC method and the result field that Codex echoes back.  These are
# reads: they never count as a producer for a required tool.
CODEX_RESOURCE_BUILTINS: dict[str, tuple[str, str]] = {
    "list_mcp_resource_templates": ("resources/templates/list", "resourceTemplates"),
    "list_mcp_resources": ("resources/list", "resources"),
    "read_mcp_resource": ("resources/read", "contents"),
}


def _resource_row_matches(
    call: dict[str, Any],
    request: dict[str, Any],
    response: Any,
) -> bool:
    """Pair one Codex built-in catalogue call with its exact JSON-RPC row.

    The request must carry the mapped method and the same arguments (the
    ``server`` argument names the Codex server and is not sent; ``_meta`` is
    Codex transport bookkeeping).  A Codex error item needs the hub's JSON-RPC
    error, code and message, inside the Codex message.  A Codex success needs
    a hub success whose echoed field is equal once the ``server`` labels that
    Codex adds are removed.
    """
    rpc_method, field = CODEX_RESOURCE_BUILTINS[call["tool"]]
    if request.get("method") != rpc_method or not isinstance(response, dict):
        return False
    arguments = dict(call["arguments"])
    if arguments.pop("server", None) != "holdspeak":
        return False
    params = {
        key: value for key, value in (request.get("params") or {}).items()
        if key != "_meta"
    }
    if params != arguments:
        return False
    result = call["result"]
    codex_error = call.get("error")
    if result is None and isinstance(codex_error, dict):
        error = response.get("error")
        if not isinstance(error, dict) or "result" in response:
            return False
        message = codex_error.get("message")
        return isinstance(message, str) and (
            f"{error.get('code')}: {error.get('message')}" in message
        )
    hub_result = response.get("result")
    if "error" in response or not isinstance(hub_result, dict):
        return False
    content = (result or {}).get("content") if isinstance(result, dict) else None
    if not isinstance(content, list) or len(content) != 1 \
            or not isinstance(content[0], dict) or content[0].get("type") != "text":
        return False
    try:
        echoed = json.loads(content[0].get("text", ""))
    except ValueError:
        return False
    if not isinstance(echoed, dict) or echoed.pop("server", None) != "holdspeak":
        return False
    if field == "contents" and echoed.pop("uri", None) != arguments.get("uri"):
        return False
    entries = echoed.pop(field, None)
    if not isinstance(entries, list):
        return False
    stripped: list[Any] = []
    for entry in entries:
        if isinstance(entry, dict) and "server" in entry:
            entry = dict(entry)
            if entry.pop("server") != "holdspeak":
                return False
        stripped.append(entry)
    if stripped != hub_result.get(field):
        return False
    return all(hub_result.get(key) == value for key, value in echoed.items())


def _reconcile_mcp_calls(
    stage_dir: Path,
    hub: Any,
    exchange_start: int,
) -> dict[str, Any]:
    """Match every Codex MCP result to one turn-local HTTP exchange."""
    calls = _codex_mcp_calls(stage_dir)
    all_exchanges = _http_exchange_records(hub)
    exchanges = all_exchanges[exchange_start:]
    if not exchanges:
        raise RuntimeError(
            "the graph rig did not retain full HTTP exchanges; refusing to "
            "claim that Codex writes reached POST /api/mcp"
        )
    matches: list[dict[str, Any]] = []
    used: set[int] = set()
    for call in calls:
        found_index: int | None = None
        for index, exchange in enumerate(exchanges):
            if index in used or exchange.get("method", "").upper() != "POST" \
                    or exchange.get("path") != "/api/mcp":
                continue
            request = exchange.get("request_body")
            response = exchange.get("response_body")
            if isinstance(request, str):
                try:
                    request = json.loads(request)
                except ValueError:
                    continue
            if isinstance(response, str):
                try:
                    response = json.loads(response)
                except ValueError:
                    continue
            if not isinstance(request, dict):
                continue
            if call["tool"] in CODEX_RESOURCE_BUILTINS:
                if _resource_row_matches(call, request, response):
                    found_index = index
                    break
                continue
            if request.get("method") != "tools/call":
                continue
            params = request.get("params") or {}
            if params.get("name") != call["tool"]:
                continue
            arguments = params.get("arguments") or {}
            if arguments != call["arguments"]:
                continue
            response_result = _mcp_result(response)
            response_hash = hashlib.sha256(
                json.dumps(_canonical_mcp_result(response_result), sort_keys=True, default=str).encode()
            ).hexdigest()
            if response_hash == call["result_sha256"]:
                found_index = index
                break
        if found_index is None:
            raise RuntimeError(
                f"MCP exchange reconciliation for {call['tool']!r} found "
                "no unused matching /api/mcp row"
            )
        used.add(found_index)
        matches.append({
            "kind": CODEX_RESOURCE_BUILTINS.get(call["tool"], ("tools/call",))[0],
            "tool": call["tool"],
            "arguments": call["arguments"],
            "result_sha256": call["result_sha256"],
            "exchange_index": exchange_start + found_index,
            "exchange": exchanges[found_index],
        })
    return {
        "codex_calls": len(calls),
        "turn_exchange_start": exchange_start,
        "turn_exchanges": len(exchanges),
        "matches": matches,
        "unmatched_turn_exchanges": [
            exchange for index, exchange in enumerate(exchanges)
            if index not in used
        ],
    }


def _audit_codex_turn(
    stage_dir: Path,
    stage: str,
    hub: Any,
    required_tools: set[str],
    exchange_start: int,
) -> dict[str, Any]:
    """Fence writes to MCP and require the producer expected for this stage."""
    sent_brief = stage_dir / "brief.md"
    if not sent_brief.exists():
        raise RuntimeError(
            f"Codex turn {stage} did not retain scripts/astra's as-sent brief"
        )
    forbidden = _ordinary_language_fence(sent_brief.read_text())
    if forbidden:
        _write_text(stage_dir / "prompt-fence-failure.txt", "\n".join(forbidden) + "\n")
        raise RuntimeError(f"ordinary-language prompt fence failed for {stage}: {forbidden}")
    events = _read_event_file(stage_dir / "events.jsonl")
    command_execs = [
        item.get("command", "") if isinstance(item.get("command", ""), str)
        else json.dumps(item.get("command", ""), sort_keys=True, default=str)
        for event in events
        for item in [event.get("item")]
        if isinstance(item, dict) and item.get("type") in {
            "command_execution", "shell_command", "exec",
        }
    ]
    hub_home_text = str(Path(hub.home).resolve())
    dangerous = re.compile(
        r"(?:sqlite3|curl\s+[^\n]*\s-X\s*(?:POST|PUT|PATCH|DELETE)|"
        r"rm\s|mv\s|cp\s|touch\s|tee\s|sed\s+-i|>>?|"
        r"\b(write_text|write_bytes|unlink|remove|rename)\b)",
        re.IGNORECASE,
    )
    home_alias = re.compile(r"(?:\$\{?HOME\}?|holdspeak\.db|\.owner\.lock|"
                            r"producer-clock\.json|rehearsal-transcript\.jsonl)")
    bad_commands = [
        command for command in command_execs
        if dangerous.search(command) and (hub_home_text in command or home_alias.search(command))
    ]
    if bad_commands:
        _write_text(stage_dir / "non-mcp-write-failure.txt", "\n".join(bad_commands) + "\n")
        raise RuntimeError(f"Codex used a non-MCP write against hub HOME during {stage}")
    calls = _codex_mcp_calls(stage_dir)
    seen_tools = {
        str(call.get("tool")) for call in calls
        if call.get("tool") not in CODEX_RESOURCE_BUILTINS
    }
    missing = sorted(required_tools - seen_tools)
    if missing:
        raise RuntimeError(f"Codex turn {stage} did not produce through MCP: {missing}")
    reconciliation = _reconcile_mcp_calls(stage_dir, hub, exchange_start)
    non_mcp_http_writes = [
        row for row in reconciliation["unmatched_turn_exchanges"]
        if str(row.get("method", "")).upper()
        in {"POST", "PUT", "PATCH", "DELETE"}
        and row.get("path") != "/api/mcp"
    ]
    result = {
        "stage": stage,
        "command_execution_count": len(command_execs),
        "command_executions": command_execs,
        "non_mcp_write_commands": bad_commands,
        "successful_mcp_calls": calls,
        "required_tools": sorted(required_tools),
        "reconciliation": reconciliation,
        "non_mcp_http_writes": non_mcp_http_writes,
        "non_mcp_http_writes_review": (
            "retained for phase review; browser activity is not a Codex MCP call"
        ),
    }
    _json_dump(stage_dir / "mcp-audit.json", result)
    if non_mcp_http_writes:
        raise RuntimeError(
            f"Codex turn {stage} produced non-MCP HTTP writes: "
            f"{[row.get('method', '') + ' ' + row.get('path', '') for row in non_mcp_http_writes]}"
        )
    return result


def _codex_turn(
    run_dir: Path,
    stage: str,
    prompt: str,
    hub_home: Path,
    auth_env: dict[str, str],
    session_id: str | None,
    timeout_s: float,
    hub: Any,
    required_tools: set[str],
) -> dict[str, Any]:
    """Run one ordinary-language turn through the repository wrapper."""
    stage_dir = run_dir / "codex" / stage
    stage_dir.mkdir(parents=True, exist_ok=True)
    exchange_start = len(_http_exchange_records(hub))
    started_at = datetime.now(timezone.utc)
    started_mono = time.monotonic()
    _json_dump(stage_dir / "transcript-window.json", {
        "exchange_start": exchange_start,
        "transcript_path": str(getattr(hub, "transcript_path", "")),
    })
    prompt_path = stage_dir / "owner-prompt.txt"
    _write_text(prompt_path, prompt + "\n")
    command = [str(AS), "ask", str(prompt_path), "--cd", str(REPO), "--tag", f"philo5-04-{stage}"]
    if session_id:
        command.extend(["--resume", session_id])
    for override in _codex_overrides(hub_home):
        command.extend(["-c", override])
    _write_text(stage_dir / "command.txt", "$ " + " ".join(command) + "\n")
    try:
        result = subprocess.run(
            command,
            cwd=str(REPO),
            env=auth_env,
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )
    except subprocess.TimeoutExpired as exc:
        finished_at = datetime.now(timezone.utc)
        _json_dump(stage_dir / "timing.json", {
            "started_at": started_at.isoformat(),
            "finished_at": finished_at.isoformat(),
            "elapsed_s": round(time.monotonic() - started_mono, 3),
            "outcome": "timeout",
        })
        _write_text(stage_dir / "timeout.txt", f"Codex turn timed out after {timeout_s}s: {exc}\n")
        raise RuntimeError(f"Codex turn {stage!r} timed out") from exc
    finished_at = datetime.now(timezone.utc)
    timing = {
        "started_at": started_at.isoformat(),
        "finished_at": finished_at.isoformat(),
        "elapsed_s": round(time.monotonic() - started_mono, 3),
        "outcome": "process_failed" if result.returncode else "process_completed",
    }
    _json_dump(stage_dir / "timing.json", timing)
    copied = _copy_codex_artifacts(stage_dir, result.stdout, result.stderr)
    copied["rollout"] = _copy_rollout(stage_dir, copied.get("session_id"), auth_env)
    copied["exit_code"] = result.returncode
    copied["prompt_path"] = str(prompt_path)
    copied["timing"] = timing
    if result.returncode != 0:
        raise RuntimeError(f"Codex turn {stage!r} exited {result.returncode}: {result.stderr[-1200:]}")
    copied["mcp_audit"] = _audit_codex_turn(
        stage_dir, stage, hub, required_tools, exchange_start,
    )
    return copied


def _hub_proof(hub: Any, home: Path) -> dict[str, Any]:
    """Guard every resolved path before any producer or client acts."""
    hub._verify_paths()
    db_path = Path(str(hub.db_path)).resolve()
    config_path = Path(str(hub.config_path)).resolve()
    if not db_path.is_relative_to(home.resolve()):
        raise RuntimeError(f"database escaped hub HOME: {db_path}")
    if not config_path.is_relative_to(home.resolve()):
        raise RuntimeError(f"config escaped hub HOME: {config_path}")
    from holdspeak.runtime_lock import owner_lock_path, read_owner

    lock_path = owner_lock_path(db_path).resolve()
    if not lock_path.is_relative_to(home.resolve()):
        raise RuntimeError(f"owner lock escaped hub HOME: {lock_path}")
    lock = read_owner(db_path)
    if not isinstance(lock, dict) or not lock.get("alive"):
        raise RuntimeError(f"hub owner lock is not alive: {lock!r}")
    if lock.get("port") != hub.port:
        raise RuntimeError(f"hub lock port is not this hub: {lock!r}")
    return {
        "home": str(home),
        "db_path": str(db_path),
        "config_path": str(config_path),
        "lock_path": str(lock_path),
        "lock": {key: value for key, value in lock.items() if key != "token"},
        "hub_url": hub.url,
        "port": hub.port,
        "pid": hub.proc.pid if hub.proc else None,
    }


def _read_op(gw: Any, hub: Any, name: str, args: dict[str, Any], provenance: dict[str, Any]) -> dict[str, Any]:
    """Use the graph rig's canonical read adapter; no direct service reads."""
    return gw.run_step(
        {"kind": "op", "name": name, "args": args, "adapter": "mcp-http-read"},
        page=None,
        hub=hub,
        provenance=provenance,
        variables={},
    )


def _response(record: dict[str, Any]) -> Any:
    if record.get("refusal"):
        raise RuntimeError(f"readback {record.get('name')} refused: {record['refusal']}")
    return record.get("response")


def _poll_read(
    gw: Any,
    hub: Any,
    name: str,
    args: dict[str, Any],
    provenance: dict[str, Any],
    predicate: Any,
    timeout_s: float = 900,
) -> dict[str, Any]:
    """Poll a read operation, retaining every canonical read record."""
    started = time.monotonic()
    reads: list[dict[str, Any]] = []
    while time.monotonic() - started < timeout_s:
        record = _read_op(gw, hub, name, args, provenance)
        reads.append(record)
        if predicate(_response(record)):
            return {"reads": reads, "elapsed_s": round(time.monotonic() - started, 3), "final": record}
        time.sleep(1)
    raise RuntimeError(f"readback {name} did not reach its expected state after {timeout_s}s")


def _latest_row(response: Any, key: str) -> dict[str, Any]:
    rows: Any = response.get(key) if isinstance(response, dict) else response
    if not isinstance(rows, list) or not rows:
        raise RuntimeError(f"{key} read returned no rows: {response!r}")
    return rows[-1]


def _brief_items(payload: Any) -> list[dict[str, Any]]:
    """Flatten the named brief items while retaining their source refs."""
    if not isinstance(payload, dict):
        return []
    brief = payload.get("brief") if isinstance(payload.get("brief"), dict) else payload
    direct = brief.get("items") if isinstance(brief, dict) else None
    if isinstance(direct, list):
        return [item for item in direct if isinstance(item, dict)]
    sections = brief.get("sections") if isinstance(brief, dict) else None
    if not isinstance(sections, dict):
        return []
    return [
        item
        for section in sections.values()
        if isinstance(section, list)
        for item in section
        if isinstance(item, dict)
    ]


def _working_revision(payload: Any) -> int | None:
    """Find the durable working revision in a Thought response."""
    if not isinstance(payload, dict):
        return None
    thought = payload.get("thought") if isinstance(payload.get("thought"), dict) else payload
    value = thought.get("working_revision") if isinstance(thought, dict) else None
    return int(value) if isinstance(value, (int, float)) else None


def _setup_engine(hub: Any, engine_url: str, run_dir: Path) -> dict[str, Any]:
    """Use the same real producer settings path as atlas Phase 3 S1."""
    status, discovered = hub.api("POST", "/api/setup/discover-models", {"base_url": engine_url})
    if status >= 400 or not isinstance(discovered, dict) or not discovered.get("models"):
        raise RuntimeError(f"real engine discovery failed ({status}): {discovered!r}")
    model = str(discovered["models"][0])
    draft = {
        "request_id": "philo5-04-his-words-model",
        "profile_id": "engine-192-168-1-43-8080",
        "expected_profile_revision": 0,
        "label": "192.168.1.43:8080",
        "provider_family": "openai_compatible",
        "model": model,
        "endpoint": engine_url,
        "requires_key": False,
    }
    profile_status, profile = hub.api(
        "POST", "/api/inference/model-library/define-endpoint",
        {"draft": draft, "secret": None},
    )
    if profile_status >= 400 or not isinstance(profile, dict):
        raise RuntimeError(f"engine profile setup failed ({profile_status}): {profile!r}")
    provider = profile.get("provider") if isinstance(profile.get("provider"), dict) else profile
    profile_id = str(provider.get("profile_id") or draft["profile_id"])
    profile_revision = int(provider.get("profile_revision") or 1)
    selection_status, selection = hub.api(
        "POST", "/api/concierge/summary-selection",
        {
            "commandId": "philo5-04-his-words-selection",
            "expectedAssignmentRevision": 0,
            "profileId": profile_id,
            "profileRevision": profile_revision,
        },
    )
    if selection_status >= 400:
        raise RuntimeError(f"summary engine selection failed ({selection_status}): {selection!r}")
    result = {
        "discover": {"status": status, "response": discovered},
        "define_endpoint": {"status": profile_status, "response": profile},
        "summary_selection": {"status": selection_status, "response": selection},
        "endpoint": engine_url,
        "model": model,
        "profile_id": profile_id,
        "profile_revision": profile_revision,
    }
    _json_dump(run_dir / "engine-setup.json", result)
    return result


def _open_pages(play: Any, hub: Any) -> tuple[Any, Any, Any, Any]:
    """Open the Arrival meeting row in two pages before summary runs."""
    browser = play.chromium.launch(
        headless=True,
        args=["--use-fake-device-for-media-stream", "--use-fake-ui-for-media-stream"],
    )
    context1440 = browser.new_context(viewport={"width": 1440, "height": 900}, device_scale_factor=1)
    context393 = browser.new_context(viewport={"width": 393, "height": 852}, device_scale_factor=1)
    page1440 = context1440.new_page()
    page393 = context393.new_page()
    for page in (page1440, page393):
        page.goto(f"{hub.url}/?token={quote(hub.token)}", wait_until="networkidle")
        try:
            page.get_by_role("button", name="Continue later", exact=True).click(timeout=1000)
        except Exception:
            pass
        rows = page.get_by_test_id("arrival-meeting-row")
        rows.first.wait_for(timeout=60_000)
        page.locator('[data-testid="arrival-meetings"] .surface-ledger-open').first.wait_for(
            timeout=60_000
        )
    return browser, context1440, context393, (page1440, page393)


def _page_snapshot(page: Any) -> dict[str, Any]:
    text = page.locator("body").inner_text(timeout=10_000)
    arrival = page.get_by_test_id("arrival-meetings")
    summary = arrival.get_by_test_id("meeting-summary-text")
    if summary.count():
        summary_metrics = summary.first.evaluate(
            """el => {
                const r = el.getBoundingClientRect();
                const x = Math.max(r.left + 1, Math.min(r.right - 1, r.left + r.width / 2));
                const y = Math.max(r.top + 1, Math.min(r.bottom - 1, r.top + r.height / 2));
                const owner = document.elementFromPoint(x, y);
                return {
                    visible: !!(r.width && r.height && getComputedStyle(el).visibility !== 'hidden'
                                && getComputedStyle(el).display !== 'none'),
                    in_viewport: r.top >= 0 && r.left >= 0
                        && r.bottom <= window.innerHeight && r.right <= window.innerWidth,
                    hit: !!owner && (owner === el || el.contains(owner)),
                    viewport: {width: window.innerWidth, height: window.innerHeight},
                };
            }"""
        )
    else:
        summary_metrics = {
            "visible": False,
            "in_viewport": False,
            "hit": False,
            "viewport": page.viewport_size,
        }
    return {
        "url": page.url,
        "summary_present": summary.count() > 0,
        "summary_text": summary.first.inner_text() if summary.count() else "",
        "summary_metrics": summary_metrics,
        "summary_host_text": arrival.get_by_test_id("summary-record-attempts").inner_text()
        if arrival.get_by_test_id("summary-record-attempts").count() else "",
        "body_sha256": hashlib.sha256(text.encode()).hexdigest(),
        "body_text_excerpt": text[:1200],
    }


def _summary_observation(run_dir: Path, pages: tuple[Any, Any], meeting_id: str, before: list[dict[str, Any]]) -> dict[str, Any]:
    observations: list[dict[str, Any]] = []
    for viewport, page, baseline in zip((1440, 393), pages, before):
        page.wait_for_function(
            """() => Boolean(document.querySelector('[data-testid="arrival-meetings"] [data-testid="meeting-summary-text"]')?.textContent?.trim())""",
            timeout=900_000,
        )
        arrival = page.get_by_test_id("arrival-meetings")
        summary = arrival.get_by_test_id("meeting-summary-text").first
        summary.scroll_into_view_if_needed(timeout=10_000)
        page.wait_for_timeout(100)
        after = _page_snapshot(page)
        shot = run_dir / "shots" / "summary" / f"{viewport}-after.png"
        shot.parent.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(shot), full_page=True)
        if not after["summary_text"]:
            raise RuntimeError(f"summary did not render at {viewport}px")
        if page.viewport_size["width"] != viewport:
            raise RuntimeError(f"summary page viewport drifted: {page.viewport_size}")
        metrics = after["summary_metrics"]
        if not metrics["visible"] or not metrics["in_viewport"] or not metrics["hit"]:
            raise RuntimeError(
                f"summary is not visibly hit-testable in the {viewport}px viewport: {metrics}"
            )
        if "192.168.1.43" not in arrival.inner_text(timeout=10_000):
            raise RuntimeError(f"summary host is not visible at {viewport}px")
        attempts = arrival.get_by_test_id("summary-record-attempts")
        if not attempts.count() or not attempts.first.is_visible():
            raise RuntimeError(f"summary host receipt is not visible at {viewport}px")
        observations.append({
            "viewport": viewport,
            "before": baseline,
            "after": after,
            "shot": str(shot),
            "manual_refresh": False,
            "navigation_after_open": 0,
            "updated_without_refresh": bool(after["summary_text"])
            and baseline["url"] == after["url"],
        })
        if not observations[-1]["updated_without_refresh"]:
            raise RuntimeError(f"summary did not update in-place at {viewport}px")
    result = {"meeting_id": meeting_id, "pages": observations}
    _json_dump(run_dir / "observations" / "summary.json", result)
    return result


def _reopen_stage(
    pages: tuple[Any, Any],
    hub: Any,
    run_dir: Path,
    stage: str,
    ref: str,
    expected_text: str = "",
    expected_source_ref: str = "",
) -> dict[str, Any]:
    """Reopen a Desk object for a fresh browser read and capture both widths."""
    observations: list[dict[str, Any]] = []
    first_validation_error: str | None = None
    for viewport, page in zip((1440, 393), pages):
        receipt_text = ""
        row_texts: list[str] = []
        receipt_shot = run_dir / "shots" / stage / f"{viewport}-receipt.png"
        row_shot = run_dir / "shots" / stage / f"{viewport}-row.png"
        if stage == "brief":
            page.goto(f"{hub.url}/?token={quote(hub.token)}", wait_until="networkidle")
            section = page.get_by_test_id("arrival-brief")
            section.wait_for(timeout=60_000)
            section.scroll_into_view_if_needed(timeout=10_000)
            page.screenshot(path=str(receipt_shot), full_page=False)
            rows = section.get_by_test_id("arrival-brief-row")
            if rows.count():
                rows.first.scroll_into_view_if_needed(timeout=10_000)
            page.screenshot(path=str(row_shot), full_page=False)
        else:
            page.goto(
                f"{hub.url}/?token={quote(hub.token)}&open={quote(ref)}",
                wait_until="networkidle",
            )
            page.wait_for_timeout(1500)
        body = page.locator("body").inner_text(timeout=10_000)
        validation_error: str | None = None
        if stage == "brief":
            section = page.get_by_test_id("arrival-brief")
            receipt = section.get_by_test_id("arrival-brief-receipt")
            receipt_text = receipt.inner_text(timeout=10_000) if receipt.count() else ""
            rows = section.get_by_test_id("arrival-brief-row")
            row_texts = [rows.nth(index).inner_text(timeout=10_000) for index in range(rows.count())]
            if not receipt.count() or not receipt.is_visible() or "Brief ready" not in receipt_text:
                validation_error = f"brief ready receipt is not visible at {viewport}px: {receipt_text!r}"
            elif not row_texts:
                validation_error = f"brief has no visible decision row at {viewport}px"
            elif expected_text and not any(expected_text in row for row in row_texts):
                validation_error = (
                    f"brief decision row at {viewport}px does not contain "
                    f"{expected_text!r}: {row_texts!r}"
                )
        elif expected_text and expected_text not in body:
            validation_error = f"{stage} reopened read does not contain its expected content at {viewport}px"
        shot = run_dir / "shots" / stage / f"{viewport}.png"
        shot.parent.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(shot), full_page=True)
        observations.append({
            "viewport": viewport,
            "ref": ref,
            "shot": str(shot),
            "receipt_shot": str(receipt_shot) if stage == "brief" else None,
            "row_shot": str(row_shot) if stage == "brief" else None,
            "receipt_text": receipt_text if stage == "brief" else None,
            "row_texts": row_texts if stage == "brief" else None,
            "receipt_present": bool(receipt_text) if stage == "brief" else None,
            "validation_error": validation_error,
            "reopened": True,
            "expected_text_present": (
                (not expected_text or any(expected_text in row for row in row_texts))
                if stage == "brief" else (not expected_text or expected_text in body)
            ),
            "body_sha256": hashlib.sha256(body.encode()).hexdigest(),
            "body_text_excerpt": body[:1200],
        })
        _json_dump(run_dir / "observations" / f"{stage}.json", {"stage": stage, "ref": ref, "pages": observations})
        if validation_error and first_validation_error is None:
            first_validation_error = validation_error
    result = {"stage": stage, "ref": ref, "pages": observations}
    _json_dump(run_dir / "observations" / f"{stage}.json", result)
    if first_validation_error:
        raise RuntimeError(first_validation_error)
    return result


def _thought_ref(*values: Any) -> str:
    """Use the canonical Thought detail/workbench working-note identity."""
    for value in values:
        if not isinstance(value, dict):
            continue
        candidates = [value]
        if isinstance(value.get("thought"), dict):
            candidates.append(value["thought"])
        for candidate in candidates:
            working = candidate.get("working_note")
            if isinstance(working, dict) and working.get("id"):
                return f"note:{working['id']}"
            if candidate.get("working_note_id"):
                return f"note:{candidate['working_note_id']}"
            if candidate.get("note_id"):
                return f"note:{candidate['note_id']}"
    raise RuntimeError(f"Thought readback has no working note identity: {values!r}")


def _run(args: argparse.Namespace) -> int:
    if not FIXTURE.exists():
        raise RuntimeError(f"fixture is missing: {FIXTURE}")
    if args.engine == "replayed" and not args.engine_replay:
        raise RuntimeError("--engine replayed requires --engine-replay")
    if args.engine_replay and not args.engine_replay.exists():
        raise RuntimeError(f"replay file is missing: {args.engine_replay}")

    run_dir = _unique_run_dir(Path(args.out).resolve(), args.engine)
    run_started_at = datetime.now(timezone.utc)
    run_started_mono = time.monotonic()
    run_error: dict[str, Any] | None = None
    # ``guard_home`` accepts a system temporary HOME. Keep the live HOME
    # outside the evidence tree, then retain DB and lock proof separately.
    hub_home = Path(tempfile.mkdtemp(prefix="philo5-04-hub-"))
    auth_home = Path(os.environ.get("HOME", "")).resolve()
    auth_env = dict(os.environ)
    auth_env["HOME"] = str(auth_home)
    _json_dump(run_dir / "requested-codex-config.json", _requested_config(hub_home))
    _json_dump(run_dir / "fixture.json", {"path": str(FIXTURE), "sha256": _sha256(FIXTURE)})
    _json_dump(run_dir / "run.json", {
        "engine_mode": args.engine,
        "fixture": str(FIXTURE),
        "hub_home": str(hub_home),
        "codex_auth_home": str(auth_home),
        "owner_review_label": "REHEARSED; OWNER REVIEW PENDING",
        "observed_sitting": False,
    })

    import importlib.util

    spec = importlib.util.spec_from_file_location("graph_walk", REPO / "scripts/graph_walk.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load graph_walk")
    gw = importlib.util.module_from_spec(spec)
    sys.modules.setdefault("graph_walk", gw)
    spec.loader.exec_module(gw)

    preflight = _preflight(run_dir, ENGINE_URL) if args.engine == "real" else {
        "skipped": True, "reason": "provider replay explicitly selected"
    }
    hub = None
    browser = None
    pages: tuple[Any, Any] | None = None
    provenance = gw.base_provenance(engine_mode=args.engine)
    session_id: str | None = None
    codex_turns: dict[str, Any] = {}
    stage_observations: dict[str, Any] = {}
    try:
        replay = args.engine_replay.resolve() if args.engine_replay else None
        hub = gw.Hub(
            hub_home,
            token=TOKEN,
            engine_replay=replay,
            producer_clock=True,
            record_rehearsal=True,
            transcript_path=hub_home / "rehearsal-transcript.jsonl",
        ).start()
        proof = _hub_proof(hub, hub_home)
        _json_dump(run_dir / "hub-proof.json", proof)
        provenance["hub"] = proof
        provenance["db_path"] = proof["db_path"]
        provenance["engine_mode"] = args.engine
        provenance["fixture_hashes"] = {str(FIXTURE): _sha256(FIXTURE)}
        _json_dump(run_dir / "preflight.json", preflight)
        config = _effective_codex_config(run_dir, hub_home, auth_env)
        _json_dump(run_dir / "effective-codex-config.json", config)
        if config["exit_code"] != 0:
            raise RuntimeError(f"effective Codex config failed: {config}")

        # The replay seam is explicit, but still uses the real producer setup
        # when the LAN model is available. This keeps the selected assignment
        # and the provider boundary honest in either labelled run.
        engine_setup = _setup_engine(hub, ENGINE_URL, run_dir)
        _json_dump(run_dir / "provenance.json", {
            **provenance,
            "preflight": preflight,
            "engine_setup": engine_setup,
        })

        def turn(stage: str, template: str) -> dict[str, Any]:
            nonlocal session_id
            prompt = template.format(fixture=FIXTURE)
            result = _codex_turn(
                run_dir, stage, prompt, hub_home, auth_env, session_id, args.codex_timeout,
                hub,
                {
                    "import": {"meeting.import"},
                    "summary": {"meeting.run_intelligence"},
                    "decision_thought": {"desk.create", "thought.create", "thought.update_working"},
                    "tomorrow_brief": {"monday_brief.generate"},
                }[stage],
            )
            session_id = result.get("session_id") or session_id
            codex_turns[stage] = result
            _json_dump(run_dir / "codex-turns.json", codex_turns)
            return result

        before_meetings = _read_op(gw, hub, "meeting.list", {}, provenance)
        import_turn = turn("import", PROMPTS["import"])
        imported = _poll_read(
            gw, hub, "meeting.list", {}, provenance,
            lambda response: isinstance(response, dict) and bool(response.get("meetings")),
            timeout_s=300,
        )
        rows_before = (_response(before_meetings) or {}).get("meetings", [])
        rows_after = (_response(imported["final"]) or {}).get("meetings", [])
        before_ids = {str(row.get("id")) for row in rows_before if isinstance(row, dict)}
        new_rows = [row for row in rows_after if isinstance(row, dict) and str(row.get("id")) not in before_ids]
        meeting = new_rows[-1] if new_rows else _latest_row(_response(imported["final"]), "meetings")
        meeting_id = str(meeting.get("id"))
        import_read = _poll_read(
            gw, hub, "meeting.read", {"meeting_id": meeting_id}, provenance,
            lambda response: isinstance(response, dict)
            and response.get("transcription_status") == "complete"
            and bool(response.get("segments")),
            timeout_s=600,
        )
        stage_observations["import"] = {
            "codex": import_turn,
            "meeting_id": meeting_id,
            "meeting_list_before": before_meetings,
            "meeting_list_after": imported,
            "meeting_read": import_read,
        }
        _json_dump(run_dir / "observations" / "import.json", stage_observations["import"])

        from playwright.sync_api import sync_playwright

        with sync_playwright() as play:
            browser, _context1440, _context393, opened = _open_pages(play, hub)
            pages = opened
            summary_before: list[dict[str, Any]] = []
            for viewport, page in zip((1440, 393), pages):
                shot = run_dir / "shots" / "summary" / f"{viewport}-before.png"
                shot.parent.mkdir(parents=True, exist_ok=True)
                page.screenshot(path=str(shot), full_page=True)
                summary_before.append({**_page_snapshot(page), "viewport": viewport, "shot": str(shot)})

            summary_turn = turn("summary", PROMPTS["summary"])
            summary_read = _poll_read(
                gw, hub, "meeting.read", {"meeting_id": meeting_id}, provenance,
                lambda response: isinstance(response, dict)
                and isinstance(response.get("intel"), dict)
                and bool(str(response["intel"].get("summary") or "").strip())
                and any(
                    str(attempt.get("host") or "") == "192.168.1.43"
                    for attempt in ((response.get("run_receipt") or {}).get("attempts") or [])
                    if isinstance(attempt, dict)
                ),
                timeout_s=900,
            )
            summary_observation = _summary_observation(run_dir, pages, meeting_id, summary_before)
            stage_observations["summary"] = {
                "codex": summary_turn,
                "meeting_read": summary_read,
                "browser": summary_observation,
            }
            _json_dump(run_dir / "observations" / "summary.json", stage_observations["summary"])

            decision_turn = turn("decision_thought", PROMPTS["decision_thought"])
            decision_read = _poll_read(
                gw, hub, "decision.list", {}, provenance,
                lambda response: isinstance(response, list) and bool(response),
                timeout_s=300,
            )
            decisions = _response(decision_read["final"])
            decision = _latest_row(decisions, "decisions")
            decision_id = str(decision.get("id"))
            decision_detail = _read_op(gw, hub, "decision.read", {"decision_id": decision_id}, provenance)
            decision_payload = _response(decision_detail)
            decision_content = json.dumps(decision_payload, sort_keys=True, default=str)
            if "local desk" not in decision_content.lower():
                raise RuntimeError(
                    f"decision readback does not contain the requested content: {decision_payload!r}"
                )
            thought_list = _read_op(gw, hub, "thought.list", {}, provenance)
            thought = _latest_row(_response(thought_list), "items")
            thought_id = str(thought.get("id"))
            thought_read = _read_op(gw, hub, "thought.read", {"thought_id": thought_id}, provenance)
            thought_workbench = _read_op(gw, hub, "thought.workbench.read", {"thought_id": thought_id}, provenance)
            thought_payload = _response(thought_read)
            thought_content = json.dumps(thought_payload, sort_keys=True, default=str)
            final_sentence = "Saved after the meeting review."
            final_revision = _working_revision(thought_payload)
            thought_calls = _codex_mcp_calls(run_dir / "codex" / "decision_thought")
            save_call = next(
                (call for call in thought_calls if call.get("tool") == "thought.update_working"),
                None,
            )
            expected_revision = (
                save_call.get("arguments", {}).get("expected_working_revision")
                if save_call else None
            )
            if final_sentence not in thought_content:
                raise RuntimeError(
                    f"Thought readback does not contain the final saved sentence: {thought_payload!r}"
                )
            if final_revision is None or final_revision < 2 or (
                isinstance(expected_revision, (int, float)) and final_revision <= expected_revision
            ):
                raise RuntimeError(
                    f"Thought save did not advance working revision: "
                    f"expected_before={expected_revision!r}, final={final_revision!r}"
                )
            decision_observation = {
                "codex": decision_turn,
                "decision_id": decision_id,
                "decision_list": decision_read,
                "decision_read": decision_detail,
            }
            thought_observation_record = {
                "codex": decision_turn,
                "thought_id": thought_id,
                "thought_list": thought_list,
                "thought_read": thought_read,
                "thought_workbench_read": thought_workbench,
                "saved_sentence": final_sentence,
                "working_revision_before_save": expected_revision,
                "working_revision_after_save": final_revision,
            }
            _json_dump(run_dir / "observations" / "decision.json", decision_observation)
            stage_observations["decision"] = decision_observation
            stage_observations["thought"] = thought_observation_record

            thought_observation = _reopen_stage(
                pages, hub, run_dir, "thought",
                _thought_ref(thought, _response(thought_read), _response(thought_workbench)),
                expected_text=final_sentence,
            )
            stage_observations["thought"]["browser"] = thought_observation
            _json_dump(run_dir / "observations" / "thought.json", stage_observations["thought"])
            decision_browser = _reopen_stage(
                pages, hub, run_dir, "decision", f"decision:{decision_id}",
                expected_text=str(
                    decision.get("decision_markdown")
                    or decision.get("context_markdown")
                    or decision.get("title")
                    or "Keep summary retrieval on the local desk"
                ),
            )
            stage_observations["decision"]["browser"] = decision_browser
            _json_dump(run_dir / "observations" / "decision.json", stage_observations["decision"])

            # This is the only clock movement, and it uses the graph rig's
            # producer-clock adapter. It never mentions a clock to Codex.
            clock = gw.producer_clock_advance(
                {"kind": "clock", "adapter": "producer-clock", "clock": "clock.python_wall",
                 "advance_days": 1, "how": "the rig advances its own producer clock"},
                hub,
                provenance,
            )
            _json_dump(run_dir / "clock-advance.json", clock)
            brief_turn = turn("tomorrow_brief", PROMPTS["tomorrow_brief"])
            brief_read = _read_op(gw, hub, "brief.latest", {}, provenance)
            brief_payload = _response(brief_read)
            if not isinstance(brief_payload, dict) or not all(
                brief_payload.get(field) for field in ("id", "generated_at", "period_start", "period_end")
            ):
                raise RuntimeError(f"brief latest did not return a ready dated brief: {brief_payload!r}")
            brief_id = str(brief_payload.get("id") or brief_payload.get("brief_id") or "")
            if not brief_id:
                raise RuntimeError(f"brief read returned no id: {brief_payload!r}")
            decision_source_ref = f"decision:{decision_id}"
            brief_items = _brief_items(brief_payload)
            matching_brief_items = [
                item for item in brief_items if item.get("source_ref") == decision_source_ref
            ]
            if not matching_brief_items:
                raise RuntimeError(
                    f"brief latest has no item with source_ref={decision_source_ref!r}: "
                    f"{brief_payload!r}"
                )
            brief_db = gw.brief_db_snapshot(hub, brief_id)
            brief_browser = _reopen_stage(
                pages, hub, run_dir, "brief", "intelligence:desk",
                expected_text=str(decision.get("title") or "Keep summary retrieval on the local desk"),
                expected_source_ref=decision_source_ref,
            )
            stage_observations["brief"] = {
                "codex": brief_turn,
                "brief_read": brief_read,
                "brief_db": brief_db,
                "brief_id": brief_id,
                "brief_items": brief_items,
                "decision_source_ref": decision_source_ref,
                "matching_brief_items": matching_brief_items,
                "producer_clock": provenance["clock"],
                "browser": brief_browser,
            }
            _json_dump(run_dir / "observations" / "brief.json", stage_observations["brief"])

            _json_dump(run_dir / "observations.json", stage_observations)
    except Exception as exc:
        run_error = {"type": type(exc).__name__, "message": str(exc)}
        _write_text(run_dir / "run-error.txt", f"{type(exc).__name__}: {exc}\n")
        raise
    finally:
        if browser is not None:
            try:
                browser.close()
            except Exception:
                pass
        if hub is not None:
            time.sleep(0.3)
            _write_text(run_dir / "hub.log", "\n".join(hub.lines) + "\n")
            provenance["clock"]["producer_clock_reads"] = list(
                getattr(hub, "producer_clock_reads", [])
            )
            if getattr(hub, "producer_clock_path", None):
                clock_source = Path(str(hub.producer_clock_path))
                if clock_source.exists():
                    shutil.copy2(clock_source, run_dir / "producer-clock.json")
            _json_dump(run_dir / "hub-proof-final.json", _hub_proof(hub, hub_home))
            if hub.db_path:
                db_source = Path(str(hub.db_path))
                if db_source.exists():
                    _backup_db(db_source, run_dir / "db-proof.sqlite")
                from holdspeak.runtime_lock import owner_lock_path

                lock_source = owner_lock_path(db_source)
                if lock_source.exists():
                    shutil.copy2(lock_source, run_dir / "db-owner.lock")
            hub.stop()
            _write_text(run_dir / "hub.log", "\n".join(hub.lines) + "\n")
            transcript_source = getattr(hub, "transcript_path", None)
            if transcript_source and Path(transcript_source).exists():
                shutil.copy2(transcript_source, run_dir / "rehearsal-transcript.jsonl")
        _json_dump(run_dir / "provenance-final.json", provenance)
        _json_dump(run_dir / "codex-turns.json", codex_turns)
        run_finished_at = datetime.now(timezone.utc)
        _json_dump(run_dir / "run-status.json", {
            "started_at": run_started_at.isoformat(),
            "finished_at": run_finished_at.isoformat(),
            "elapsed_s": round(time.monotonic() - run_started_mono, 3),
            "outcome": "blocked" if run_error else "completed",
            "error": run_error,
        })

    print(f"RUN_DIR {run_dir}")
    print("PROOF REHEARSED; OWNER REVIEW PENDING")
    print(f"ENGINE {args.engine}")
    print(f"DB {provenance.get('db_path')}")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.mode != "run":
        raise SystemExit(2)
    try:
        return _run(args)
    except Exception as exc:  # retain a concise command-line failure
        print(f"PHILO5_HIS_WORDS_BLOCKED {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
