#!/usr/bin/env python3
"""PHILO-7-04: file it and find it from a cold-context Codex session.

The closing use of Phase 7. Codex receives the owner's ordinary words and
nothing else, and discovers the job from the MCP catalogue of an isolated
rig hub. Two legs:

- the OWNER leg: the built stdio sidecar (``holdspeak-mcp``), which forwards
  the hub's owner token; four requests in one resumed session;
- the AGENT leg: the hub's real ``POST /api/mcp`` with a DESK credential
  issued through the real settings route as the bearer; the same filing
  request in two fresh sessions, before and after the owner's grant.

The claim (R3, worded exactly) is :data:`CLAIM`. The driver reuses the
Phase 5 driver (``scripts/philo5_his_words.py``) for the rig hub, the
canonical readbacks, the MCP-exchange reconciliation and the Desk shots.
Every readback goes through the contract (``graph_walk`` ``op`` adapter),
never through Codex's own text. The hub runs under a fresh temporary HOME;
the owner's desk is never used.
"""
from __future__ import annotations

import argparse
from contextlib import closing
import copy
from datetime import datetime, timezone
import hashlib
import importlib.util
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
from typing import Any, Iterable
from urllib.parse import quote


REPO = Path(__file__).resolve().parents[1]
MCP_COMMAND = REPO / ".venv/bin/holdspeak-mcp"
ENGINE_URL = "http://192.168.1.43:8080"
TOKEN = "philo7-04-file-and-find"
AGENT_IDENTITY = "codex-desk-agent"
BEARER_ENV = "HOLDSPEAK_DESK_BEARER"
MODEL = "gpt-6-astra"
# The owner's own Codex default (``~/.codex/config.toml``: model_reasoning_effort).
# Passed as a flag because the user config is deliberately not loaded.
EFFORT = "medium"

#: R3, worded exactly for the Codex client (story-04 r3).
CLAIM_CODEX = (
    "cold context (an empty scratch dir, scratch HOME/CODEX_HOME with only the "
    "auth file, `--ignore-user-config --ignore-rules`, no preamble), ZERO "
    "repository reads in the retained log, discovery from the catalogue alone"
)
#: R3's claim reworded for the closing client by R6 ("Claude closes it",
#: 2026-09-25): the same observational claim, its qualification intact.
CLAIM = (
    "a cold-context Claude session (an empty scratch dir, a scratch HOME with only the "
    "auth file, no user or project instructions, `--strict-mcp-config` with the one "
    "holdspeak server, no preamble), ZERO repository reads in the retained log, "
    "discovery from the catalogue alone"
)
REVIEW_LABEL = "REHEARSED; OWNER REVIEW PENDING"
#: The closing client (R6); ``--client codex`` keeps the Codex path.
CLIENT: list[str] = ["claude"]
CLAUDE_CREDENTIALS: list[dict[str, Any]] = []

# The seeded desk, made through the real producers before any Codex turn.
ZONE_NAME = "Platform Migration"
OWNER_NOTE = {
    "title": "Runner capacity numbers",
    "body_markdown": "The build farm needs 40 more runner hours each week after the move.",
}
AGENT_NOTE = {
    "title": "Build cache sizing",
    "body_markdown": "The shared cache needs 2 TB to hold two weeks of build outputs.",
}
DECISION_WORDS = "move the nightly build to the shared runners"
#: The owner's reason (his review of the first closing run: "the decision is
#: thin — a decision put on my review list should carry its context").
DECISION_REASON = "our own runners are full every night and the shared pool has spare capacity after 8 PM"
#: The durable context must carry the reason's substance: every group names
#: one fact of it, in any of its words.
REASON_FACTS: tuple[tuple[str, ...], ...] = (("full",), ("shared pool", "shared runner", "spare"))

# The owner's words, and nothing else: no operation or tool name, no
# argument, no id, no clock. The zone and the notes are named by the human
# names the owner gave them.
PROMPTS: dict[str, str] = {
    "owner_file": f"File my note {OWNER_NOTE['title']} into my {ZONE_NAME} zone.",
    "owner_find": "Now find that note for me and tell me where it is.",
    "owner_decide": f"Put this decision on my review list: {DECISION_WORDS}, because {DECISION_REASON}.",
    "owner_brief": "Make my brief and tell me what is on it.",
    "agent_file": f"File my note {AGENT_NOTE['title']} into my {ZONE_NAME} zone.",
}

# Codex item types that are not an action on anything outside the MCP
# server: the model's own messages, its reasoning, its plan and client
# warnings. Every other completed item (a shell command, a file change, a web
# search, an image view, another server's tool) is a finding.
QUIET_ITEM_TYPES = frozenset({"agent_message", "reasoning", "error", "todo_list"})

# The instruction files Codex reads from a working root or a parent, and the
# directory that holds project config.
CONTEXT_FILES = ("AGENTS.md", "AGENTS.override.md", "CLAUDE.md", ".codex")

# Phrases no record of this story may use (R3; story-04 acceptance box 1).
# The literal Codex flag name is not a claim; it is stripped first.
_FLAG_TOKEN = "--dangerously-bypass-approvals-and-sandbox"
_R3_FORBIDDEN = (
    re.compile(r"sandbox", re.IGNORECASE),
    re.compile(r"repository access (?:was|is|were) (?:unavailable|not available|removed|denied)", re.IGNORECASE),
    re.compile(r"(?:could not|cannot|can't) (?:read|reach|access) the repositor", re.IGNORECASE),
    re.compile(r"no repository access", re.IGNORECASE),
)


# ── loading the reused rigs ──────────────────────────────────────────────


def _load(name: str, path: Path) -> Any:
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


p5 = _load("philo5_his_words", REPO / "scripts/philo5_his_words.py")


def _gw() -> Any:
    return _load("graph_walk", REPO / "scripts/graph_walk.py")


# ── the fences (pure functions over retained records) ────────────────────


def read_events(path: Path) -> list[dict[str, Any]]:
    return p5._read_event_file(path)


def zero_read_findings(events: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Every completed Codex action that is not a holdspeak MCP call.

    ZERO findings is the observational proof that the session read no
    repository file, source or roadmap document: its only actions were calls
    to the one MCP server. Started/completed duplicates are counted once
    (completed items only).
    """
    findings: list[dict[str, Any]] = []
    for event in events:
        if event.get("type") != "item.completed":
            continue
        item = event.get("item")
        if not isinstance(item, dict):
            continue
        kind = item.get("type")
        if kind in QUIET_ITEM_TYPES:
            continue
        if kind == "mcp_tool_call" and item.get("server") == "holdspeak":
            continue
        detail = (
            item.get("command") or item.get("changes") or item.get("query")
            or item.get("path") or item.get("server") or ""
        )
        findings.append({
            "item_id": item.get("id"),
            "type": kind,
            "server": item.get("server"),
            "detail": detail if isinstance(detail, str) else json.dumps(detail, default=str)[:400],
        })
    return findings


def listed_tools(exchanges: Iterable[dict[str, Any]]) -> set[str]:
    """The tool names of every ``tools/list`` answer in these server rows."""
    names: set[str] = set()
    for row in exchanges:
        if row.get("path") != "/api/mcp":
            continue
        request = row.get("request_body")
        response = row.get("response_body")
        if not isinstance(request, dict) or request.get("method") != "tools/list":
            continue
        result = response.get("result") if isinstance(response, dict) else None
        for tool in (result or {}).get("tools") or []:
            if isinstance(tool, dict) and tool.get("name"):
                names.add(str(tool["name"]))
    return names


def unlisted_tool_findings(calls: Iterable[dict[str, Any]], listed: set[str]) -> list[str]:
    """Chosen tools absent from the session's own ``tools/list`` answer.

    Codex's three catalogue built-ins (resource list/read) are JSON-RPC
    resource methods, not tools; they are paired separately by the
    reconciliation and never satisfy this check.
    """
    return sorted({
        str(call.get("tool")) for call in calls
        if call.get("tool") not in p5.CODEX_RESOURCE_BUILTINS
        and str(call.get("tool")) not in listed
    })


def r3_wording_findings(text: str) -> list[str]:
    """Forbidden claim wording in a record (R3)."""
    stripped = text.replace(_FLAG_TOKEN, "")
    return sorted({match.group(0) for pattern in _R3_FORBIDDEN for match in pattern.finditer(stripped)})


_ID_LIKE = re.compile(
    r"(?:\b(?:note|directory|decision|kb|zone|operation|op|thought|brief)[:_-][0-9a-z]{4,}\b"
    r"|\b[0-9a-f]{8,}\b|\bdirectory_id\b|\bprimitive_id\b|\{|\})",
    re.IGNORECASE,
)


def prompt_findings(text: str) -> list[str]:
    """Technical words in an owner's prompt: operation/tool/argument names
    (the Phase 5 fence over the live catalogue), ids, JSON and clocks."""
    found = list(p5._ordinary_language_fence(text))
    found += [match.group(0) for match in _ID_LIKE.finditer(text)]
    if re.search(r"test clock|tomorrow", text, re.IGNORECASE):
        found.append("clock")
    return sorted(set(found))


def _walk_files(root: Path) -> list[str]:
    if not root.exists():
        return []
    return sorted(
        str(path.relative_to(root)) for path in root.rglob("*")
        if path.is_file() or path.is_symlink()
    )


def _chain(path: Path) -> list[Path]:
    """The path and every parent up to ``/``, both as given and resolved."""
    seen: list[Path] = []
    for start in (path.absolute(), path.resolve()):
        for candidate in (start, *start.parents):
            if candidate not in seen:
                seen.append(candidate)
    return seen


def launch_setup_findings(
    *,
    work: Path,
    codex_home: Path,
    codex_process_home: Path,
    servers: Any,
    leg: str,
    hub_home: Path,
    hub_url: str,
    mcp_command: Path = MCP_COMMAND,
) -> tuple[list[str], dict[str, Any]]:
    """The launch-setup check (story-04 steps 1, 2 and 4). Empty = lawful."""
    findings: list[str] = []
    record: dict[str, Any] = {"work": str(work), "parents_checked": []}
    if not work.is_dir():
        findings.append(f"working root {work} is not a directory")
    elif any(work.iterdir()):
        findings.append(f"working root {work} is not empty: {sorted(p.name for p in work.iterdir())}")
    for parent in _chain(work):
        present = [name for name in (*CONTEXT_FILES, ".git") if (parent / name).exists()]
        record["parents_checked"].append({"path": str(parent), "present": present})
        for name in present:
            findings.append(f"{name} exists at {parent}")
    try:
        inside = subprocess.run(
            ["git", "-C", str(work), "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, timeout=30,
        )
        record["git_rev_parse"] = {"exit_code": inside.returncode, "stdout": inside.stdout.strip(),
                                   "stderr": inside.stderr.strip()[-300:]}
        if inside.returncode == 0:
            findings.append(f"working root is inside the checkout {inside.stdout.strip()}")
    except (OSError, subprocess.SubprocessError) as exc:
        record["git_rev_parse"] = {"error": str(exc)}
    for checkout in (REPO,):
        for candidate in _chain(work):
            if candidate == checkout.resolve() or candidate == checkout:
                findings.append(f"working root is under the repository {checkout}")
    codex_files = _walk_files(codex_home)
    record["codex_home"] = {"path": str(codex_home), "files": codex_files}
    if codex_files != ["auth.json"]:
        findings.append(f"CODEX_HOME holds {codex_files}, not the auth file alone")
    home_files = _walk_files(codex_process_home)
    record["codex_process_home"] = {"path": str(codex_process_home), "files": home_files}
    try:
        relative_codex = str(codex_home.relative_to(codex_process_home))
    except ValueError:
        relative_codex = None
    allowed_home = [f"{relative_codex}/auth.json"] if relative_codex else []
    if home_files != allowed_home:
        findings.append(f"the Codex process HOME holds {home_files}, not the auth file alone")
    record["servers"] = servers
    rows = servers if isinstance(servers, list) else []
    names = [str(row.get("name")) for row in rows if isinstance(row, dict)]
    if names != ["holdspeak"]:
        findings.append(f"configured MCP servers are {names}, not holdspeak alone")
    else:
        transport = rows[0].get("transport") or {}
        if leg == "owner":
            if transport.get("type") != "stdio" or transport.get("command") != str(mcp_command):
                findings.append(f"the OWNER server is not the built sidecar: {transport}")
            if (transport.get("env") or {}).get("HOME") != str(hub_home):
                findings.append(f"the OWNER sidecar HOME is not the isolated hub's: {transport.get('env')}")
        else:
            if transport.get("type") != "streamable_http" or transport.get("url") != f"{hub_url}/api/mcp":
                findings.append(f"the AGENT server is not the hub's /api/mcp: {transport}")
            if transport.get("bearer_token_env_var") != BEARER_ENV:
                findings.append(f"the AGENT server carries no bearer variable: {transport}")
        if rows[0].get("enabled") is False:
            findings.append("the holdspeak server is disabled")
    return findings, record


def initial_context_findings(rollout: list[dict[str, Any]]) -> tuple[list[str], list[dict[str, Any]]]:
    """The model-visible context before the owner's first words.

    Returns (findings, the retained initial-context lines). The repository
    path, an instruction file or a non-empty ``agents_md`` in it is a finding.
    """
    initial: list[dict[str, Any]] = []
    findings: list[str] = []
    for line in rollout:
        payload = line.get("payload") if isinstance(line.get("payload"), dict) else {}
        if line.get("type") == "response_item" and payload.get("role") == "user" and not any(
            str(part.get("text", "")).lstrip().startswith("<")
            for part in payload.get("content") or [] if isinstance(part, dict)
        ):
            break  # the owner's own words start here
        initial.append(line)
    text = json.dumps(initial, default=str)
    # Codex's own system text names AGENTS.md as a concept; an instruction
    # FILE arrives under its own header and in ``world_state.agents_md``.
    for needle in (str(REPO), str(REPO.resolve()), "AGENTS.md instructions", "CLAUDE.md",
                   "pm/roadmap", "HoldSpeak/", "holdspeak/"):
        if needle in text:
            findings.append(f"the initial context mentions {needle!r}")
    for line in initial:
        if line.get("type") == "world_state":
            state = (line.get("payload") or {}).get("state") or {}
            if state.get("agents_md"):
                findings.append(f"world_state.agents_md is not empty: {state.get('agents_md')!r}")
    return findings, initial


def agent_receipt_findings(
    refused: dict[str, Any] | None,
    granted: dict[str, Any] | None,
    *,
    identity: str,
    grant_id: str | None,
) -> list[str]:
    """The AGENT leg's two receipts (R1): refused without the grant, the
    delegation named with it; the agent identity is the actor on both."""
    findings: list[str] = []
    if not isinstance(refused, dict):
        findings.append("no refusal receipt for the ungranted run")
    else:
        if refused.get("outcome") != "desk_delegation_required":
            findings.append(f"the ungranted receipt outcome is {refused.get('outcome')!r}")
        if refused.get("state") not in {"refused"}:
            findings.append(f"the ungranted receipt state is {refused.get('state')!r}")
        if refused.get("actor_identity") != identity:
            findings.append(f"the ungranted receipt actor is {refused.get('actor_identity')!r}")
    if not isinstance(granted, dict):
        findings.append("no receipt for the granted run")
    else:
        if granted.get("state") != "succeeded":
            findings.append(f"the granted receipt state is {granted.get('state')!r}")
        basis = str(granted.get("authority_basis") or "")
        if not grant_id or not basis.startswith(f"desk-delegation:{grant_id}:sha256:"):
            findings.append(f"the granted receipt does not name the grant: {basis!r}")
        if granted.get("delegator_kind") != "owner":
            findings.append(f"the granted receipt delegator is {granted.get('delegator_kind')!r}")
        if granted.get("actor_identity") != identity:
            findings.append(f"the granted receipt actor is {granted.get('actor_identity')!r}")
    return findings


# ── the run's records ────────────────────────────────────────────────────


def _json_dump(path: Path, value: Any) -> None:
    p5._json_dump(path, value)


def _write_text(path: Path, value: str) -> None:
    p5._write_text(path, value)


def _unique_run_dir(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    candidate = root / f"{stamp}-file-and-find"
    suffix = 2
    while candidate.exists():
        candidate = root / f"{stamp}-file-and-find-{suffix}"
        suffix += 1
    candidate.mkdir(parents=True)
    return candidate


def _toml(value: Any) -> str:
    return json.dumps(value)


def mcp_overrides(leg: str, hub_home: Path, hub_url: str) -> list[str]:
    """The ``-c`` overrides naming the one MCP server for a leg."""
    common = [
        "mcp_servers.holdspeak.required=true",
        "mcp_servers.holdspeak.startup_timeout_sec=60",
        "mcp_servers.holdspeak.tool_timeout_sec=900",
    ]
    if leg == "owner":
        return [
            f"mcp_servers.holdspeak.command={_toml(str(MCP_COMMAND))}",
            "mcp_servers.holdspeak.args=[]",
            f"mcp_servers.holdspeak.env.HOME={_toml(str(hub_home))}",
            f"mcp_servers.holdspeak.cwd={_toml(str(hub_home))}",
            *common,
        ]
    return [
        f"mcp_servers.holdspeak.url={_toml(hub_url + '/api/mcp')}",
        f"mcp_servers.holdspeak.bearer_token_env_var={_toml(BEARER_ENV)}",
        *common,
    ]


# Codex's own connectors and plugins would be further MCP servers; the
# story allows one server only.
DISABLED_FEATURES = ("apps", "plugins")


def codex_flags(leg: str, hub_home: Path, hub_url: str) -> list[str]:
    flags = [
        "--skip-git-repo-check", "--ignore-user-config", "--ignore-rules",
        _FLAG_TOKEN,
        "-m", MODEL, "-c", f"model_reasoning_effort={_toml(EFFORT)}",
    ]
    for feature in DISABLED_FEATURES:
        flags += ["--disable", feature]
    for override in mcp_overrides(leg, hub_home, hub_url):
        flags += ["-c", override]
    return flags


class Cold:
    """One cold-context launch root: work dir, Codex HOME, CODEX_HOME."""

    def __init__(self, root: Path, name: str, auth: Path) -> None:
        self.root = root / name
        self.work = self.root / "work"
        self.home = self.root / "home"
        self.codex_home = self.home / ".codex"
        for path in (self.work, self.codex_home):
            path.mkdir(parents=True, exist_ok=True)
        if not auth.exists():
            raise RuntimeError(f"the Codex auth file is missing: {auth}")
        shutil.copy2(auth, self.codex_home / "auth.json")
        os.chmod(self.codex_home / "auth.json", 0o600)
        self.auth_sha256_before = p5._sha256(self.codex_home / "auth.json")

    def env(self, bearer: str | None = None) -> dict[str, str]:
        codex_bin = shutil.which("codex") or "/usr/local/bin/codex"
        env = {
            "PATH": f"{Path(codex_bin).parent}:/usr/bin:/bin:/usr/sbin:/sbin",
            "HOME": str(self.home),
            "CODEX_HOME": str(self.codex_home),
            "TMPDIR": os.environ.get("TMPDIR", "/tmp"),
            "LANG": "en_US.UTF-8",
            "USER": os.environ.get("USER", "owner"),
        }
        if bearer is not None:
            env[BEARER_ENV] = bearer
        return env


def _redacted_env(env: dict[str, str]) -> dict[str, str]:
    out = dict(env)
    if BEARER_ENV in out:
        out[BEARER_ENV] = "<redacted sha256:" + hashlib.sha256(out[BEARER_ENV].encode()).hexdigest()[:12] + ">"
    return out


def effective_config(cold: Cold, leg: str, hub_home: Path, hub_url: str, out: Path,
                     env: dict[str, str]) -> dict[str, Any]:
    """Dump the effective MCP config from a SEPARATE probe CODEX_HOME (same
    auth file, same overrides) so the session's own CODEX_HOME stays the auth
    file alone at launch."""
    probe_home = cold.root / "config-probe-home"
    probe_codex = probe_home / ".codex"
    probe_codex.mkdir(parents=True, exist_ok=True)
    shutil.copy2(cold.codex_home / "auth.json", probe_codex / "auth.json")
    probe_env = {**env, "HOME": str(probe_home), "CODEX_HOME": str(probe_codex)}
    overrides: list[str] = []
    for override in mcp_overrides(leg, hub_home, hub_url):
        overrides += ["-c", override]
    for feature in DISABLED_FEATURES:
        overrides += ["--disable", feature]
    results: dict[str, Any] = {}
    for label, command in (
        ("mcp_list", ["codex", "mcp", "list", "--json", *overrides]),
        ("mcp_get", ["codex", "mcp", "get", "holdspeak", "--json", *overrides]),
        ("features", ["codex", "features", "list", *overrides]),
    ):
        result = subprocess.run(command, cwd=str(cold.work), env=probe_env,
                                capture_output=True, text=True, timeout=60)
        try:
            parsed: Any = json.loads(result.stdout)
        except ValueError:
            parsed = result.stdout
        results[label] = {"command": command, "exit_code": result.returncode,
                          "output": parsed, "stderr": result.stderr[-800:]}
    shutil.rmtree(probe_home, ignore_errors=True)
    _json_dump(out, results)
    return results


def _find_rollout(codex_home: Path, session_id: str | None) -> Path | None:
    if not session_id:
        return None
    for candidate in sorted(codex_home.rglob(f"rollout-*{session_id}*.jsonl")):
        return candidate
    return None


def _usage_limit(events: list[dict[str, Any]]) -> str | None:
    """Codex's usage-limit refusal, when the account has no usage left."""
    for event in events:
        messages = [event.get("message")]
        if isinstance(event.get("error"), dict):
            messages.append(event["error"].get("message"))
        for message in messages:
            if isinstance(message, str) and "usage limit" in message.lower():
                return message
    return None


def _mcp_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [row for row in rows if row.get("path") == "/api/mcp"]


def codex_turn(
    *,
    run_dir: Path,
    stage: str,
    prompt: str,
    cold: Cold,
    leg: str,
    hub: Any,
    session_id: str | None,
    bearer: str | None,
    timeout_s: float,
) -> dict[str, Any]:
    """One ordinary-language Codex turn from the cold root; retain everything."""
    stage_dir = run_dir / "codex" / stage
    stage_dir.mkdir(parents=True, exist_ok=True)
    exchange_start = len(p5._http_exchange_records(hub))
    _json_dump(stage_dir / "transcript-window.json", {
        "exchange_start": exchange_start,
        "transcript_path": str(getattr(hub, "transcript_path", "")),
    })
    findings = prompt_findings(prompt)
    _write_text(stage_dir / "owner-prompt.txt", prompt + "\n")
    # No preamble: the as-sent text IS the owner's words.
    _write_text(stage_dir / "brief.md", prompt + "\n")
    if findings:
        _write_text(stage_dir / "prompt-fence-failure.txt", "\n".join(findings) + "\n")
        raise RuntimeError(f"ordinary-language prompt fence failed for {stage}: {findings}")
    env = cold.env(bearer)
    flags = codex_flags(leg, Path(hub.home), hub.url)
    if session_id:
        command = ["codex", "exec", "resume", session_id, *flags, "--json",
                   "-o", str(stage_dir / "last.md"), "-"]
    else:
        command = ["codex", "exec", "-C", str(cold.work), *flags, "--json",
                   "-o", str(stage_dir / "last.md"), "-"]
    _write_text(stage_dir / "command.txt", "$ " + " ".join(command) + "\n")
    _json_dump(stage_dir / "environment.json", {
        "env": _redacted_env(env), "cwd": str(cold.work), "stdin": "owner-prompt.txt",
    })
    _json_dump(stage_dir / "codex-home-at-launch.json", {
        "codex_home": _walk_files(cold.codex_home),
        "codex_process_home": _walk_files(cold.home),
        "work": _walk_files(cold.work),
    })
    started_at = datetime.now(timezone.utc)
    started = time.monotonic()
    try:
        result = subprocess.run(command, cwd=str(cold.work), env=env, input=prompt,
                                capture_output=True, text=True, timeout=timeout_s)
        outcome = "process_failed" if result.returncode else "process_completed"
        stdout, stderr, returncode = result.stdout, result.stderr, result.returncode
    except subprocess.TimeoutExpired as exc:
        outcome = "timeout"
        stdout = exc.stdout.decode() if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = exc.stderr.decode() if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        returncode = None
    _write_text(stage_dir / "events.jsonl", stdout)
    _write_text(stage_dir / "stderr.log", stderr)
    timing = {
        "started_at": started_at.isoformat(),
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "elapsed_s": round(time.monotonic() - started, 3),
        "outcome": outcome,
        "exit_code": returncode,
    }
    _json_dump(stage_dir / "timing.json", timing)
    events = read_events(stage_dir / "events.jsonl")
    sid = next((str(e.get("thread_id")) for e in events if e.get("type") == "thread.started"), session_id)
    _write_text(stage_dir / "session-id", f"{sid}\n")
    rollout_path = _find_rollout(cold.codex_home, sid)
    rollout: list[dict[str, Any]] = []
    if rollout_path:
        shutil.copy2(rollout_path, stage_dir / "rollout.jsonl")
        rollout = read_events(stage_dir / "rollout.jsonl")
    context_findings, initial = initial_context_findings(rollout)
    _write_text(stage_dir / "initial-context.jsonl",
                "".join(json.dumps(line, default=str) + "\n" for line in initial))
    rows = p5._http_exchange_records(hub)[exchange_start:]
    listed = listed_tools(rows)
    calls = p5._codex_mcp_calls(stage_dir)
    audit: dict[str, Any] = {
        "stage": stage,
        "leg": leg,
        "timing": timing,
        "session_id": sid,
        "resumed": bool(session_id),
        "usage_limit": _usage_limit(events),
        "zero_read_findings": zero_read_findings(events),
        "initial_context_findings": context_findings,
        "rollout": str(rollout_path) if rollout_path else None,
        "tools_listed": len(listed),
        "chosen_tools": [call.get("tool") for call in calls],
        "unlisted_tools": unlisted_tool_findings(calls, listed),
        "mcp_statuses": [
            {"status": row.get("status"),
             "method": (row.get("request_body") or {}).get("method")
             if isinstance(row.get("request_body"), dict) else None}
            for row in _mcp_rows(rows) if str(row.get("method", "")).upper() == "POST"
        ],
        "mcp_other_methods": [
            {"method": row.get("method"), "status": row.get("status")}
            for row in _mcp_rows(rows) if str(row.get("method", "")).upper() != "POST"
        ],
        "non_mcp_http_writes": [
            f"{row.get('method')} {row.get('path')}" for row in rows
            if str(row.get("method", "")).upper() in {"POST", "PUT", "PATCH", "DELETE"}
            and row.get("path") != "/api/mcp"
        ],
        "auth_file_changed": p5._sha256(cold.codex_home / "auth.json") != cold.auth_sha256_before,
    }
    try:
        reconciliation = p5._reconcile_mcp_calls(stage_dir, hub, exchange_start)
        # The unmatched rows are the handshake (initialize, tools/list); the
        # full bodies stay in rehearsal-transcript.jsonl, indexed from
        # ``exchange_start``.
        reconciliation["unmatched_turn_exchanges"] = [
            {"method": row.get("method"), "path": row.get("path"), "status": row.get("status"),
             "rpc_method": (row.get("request_body") or {}).get("method")
             if isinstance(row.get("request_body"), dict) else None}
            for row in reconciliation["unmatched_turn_exchanges"]
        ]
        audit["reconciliation"] = reconciliation
        audit["reconciliation_error"] = None
    except RuntimeError as exc:
        audit["reconciliation"] = None
        audit["reconciliation_error"] = str(exc)
    _json_dump(stage_dir / "mcp-audit.json", audit)
    return audit


def _slim(audit: dict[str, Any]) -> dict[str, Any]:
    """The turn's audit without the paired rows (kept in mcp-audit.json)."""
    slim = {key: value for key, value in audit.items() if key != "reconciliation"}
    rec = audit.get("reconciliation") or {}
    slim["reconciliation"] = {
        "codex_calls": rec.get("codex_calls"),
        "matched": len(rec.get("matches") or []),
        "turn_exchange_start": rec.get("turn_exchange_start"),
        "turn_exchanges": rec.get("turn_exchanges"),
    }
    return slim


def client_turn(*, cold: Any, bearer: str | None, **kwargs: Any) -> dict[str, Any]:
    if isinstance(cold, ClaudeCold):
        return claude_turn(cold=cold, **kwargs)
    return codex_turn(cold=cold, bearer=bearer, **kwargs)


def turn_blockers(audit: dict[str, Any]) -> list[str]:
    """What stops a turn from counting toward the claim."""
    blockers: list[str] = []
    if audit.get("init_findings"):
        blockers.append(f"init: {audit['init_findings']}")
    if audit.get("result_is_error"):
        blockers.append(f"the client ended in an error: {str(audit.get('result_text'))[:300]}")
    if audit.get("usage_limit"):
        blockers.append(f"codex_usage_limit: {audit['usage_limit']}")
    if audit["timing"].get("outcome") != "process_completed" and not audit.get("usage_limit"):
        blockers.append(f"codex process {audit['timing'].get('outcome')} (exit {audit['timing'].get('exit_code')})")
    if audit["zero_read_findings"]:
        blockers.append(f"zero-read fence: {len(audit['zero_read_findings'])} non-MCP action(s)")
    if audit["initial_context_findings"]:
        blockers.append(f"initial context: {audit['initial_context_findings']}")
    if audit["unlisted_tools"]:
        blockers.append(f"tools not in tools/list: {audit['unlisted_tools']}")
    if audit.get("reconciliation_error"):
        blockers.append(f"pairing audit: {audit['reconciliation_error']}")
    if audit.get("non_mcp_http_writes"):
        blockers.append(f"non-MCP HTTP writes in the turn: {audit['non_mcp_http_writes']}")
    return blockers


# ── the Claude client (R6: "Claude closes it") ───────────────────────────
#
# The closing client is a cold-context Claude session on Opus 5.5. The
# launch discipline is the Codex one: an empty working root outside every
# checkout, a scratch HOME holding only the auth material, no user or project
# instructions, the one holdspeak MCP server (``--strict-mcp-config``), no
# preamble, every event retained.

CLAUDE_MODEL = "claude-opus-5-5"
CLAUDE_KEYCHAIN_SERVICE = "Claude Code-credentials"
#: Claude-side name of every holdspeak tool.
CLAUDE_MCP_PREFIX = "mcp__holdspeak__"
#: Client-local catalogue tools: they read the MCP server's own catalogue
#: (tool search over the listed tools; the server's resources), never a file.
CLAUDE_CATALOGUE_TOOLS = frozenset({"ToolSearch", "ListMcpResourcesTool", "ReadMcpResourceTool",
                                    "ReadMcpResourceDirTool"})
#: Instruction markers in Claude's retained initial context: a loaded
#: CLAUDE.md or memory file arrives as "Contents of <path>" or as one of
#: these attachment types.
CLAUDE_INSTRUCTION_ATTACHMENTS = frozenset({
    "nested_memory", "claude_md", "memory", "relevant_memories", "directory_instructions",
})
CLAUDE_CONTEXT_FILES = ("CLAUDE.md", "CLAUDE.local.md", "AGENTS.md", ".claude", ".codex", ".git")


def claude_sanitized(name: str) -> str:
    """Claude's name for an MCP tool name (every character outside
    ``[A-Za-z0-9_-]`` becomes ``_``)."""
    return re.sub(r"[^A-Za-z0-9_-]", "_", name)


def claude_tool_uses(events: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Every ``tool_use`` block of the main thread and of any sub-agent,
    each joined to its ``tool_result``."""
    uses: list[dict[str, Any]] = []
    results: dict[str, dict[str, Any]] = {}
    for event in events:
        message = event.get("message") if isinstance(event.get("message"), dict) else None
        if not message:
            continue
        for block in message.get("content") or []:
            if not isinstance(block, dict):
                continue
            if block.get("type") == "tool_use":
                uses.append({"id": block.get("id"), "name": str(block.get("name")),
                             "input": block.get("input") or {},
                             "parent": event.get("parent_tool_use_id")})
            elif block.get("type") == "tool_result":
                results[str(block.get("tool_use_id"))] = block
    for use in uses:
        result = results.get(str(use["id"]))
        content = result.get("content") if result else None
        if isinstance(content, list):
            text = "".join(str(part.get("text", "")) for part in content
                           if isinstance(part, dict) and part.get("type") == "text")
        else:
            text = content if isinstance(content, str) else None
        use["result_text"] = text
        use["is_error"] = bool(result.get("is_error")) if result else None
    return uses


def claude_zero_read_findings(events: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Every Claude tool use that is not a holdspeak MCP call or a catalogue
    read of the holdspeak server (Read, Glob, Grep, Bash, WebFetch, Task…)."""
    findings: list[dict[str, Any]] = []
    for use in claude_tool_uses(events):
        name = use["name"]
        if name.startswith(CLAUDE_MCP_PREFIX):
            continue
        if name == "ToolSearch":
            continue
        if name in {"ListMcpResourcesTool", "ReadMcpResourceTool", "ReadMcpResourceDirTool"} and \
                use["input"].get("server") in (None, "holdspeak"):
            continue
        findings.append({"item_id": use["id"], "type": "tool_use", "server": None,
                         "detail": f"{name} {json.dumps(use['input'], default=str)[:300]}"})
    return findings


def is_claude_log(events: list[dict[str, Any]]) -> bool:
    return any(e.get("type") == "system" and e.get("subtype") == "init" for e in events)


def any_zero_read_findings(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """The zero-read fence over either client's retained event log."""
    return claude_zero_read_findings(events) if is_claude_log(events) else zero_read_findings(events)


def claude_init(events: list[dict[str, Any]]) -> dict[str, Any]:
    return next((e for e in events if e.get("type") == "system" and e.get("subtype") == "init"), {})


def claude_unlisted(events: list[dict[str, Any]]) -> list[str]:
    """Chosen holdspeak tools absent from the session's init tool list."""
    listed = set(claude_init(events).get("tools") or [])
    return sorted({use["name"] for use in claude_tool_uses(events)
                   if use["name"].startswith(CLAUDE_MCP_PREFIX) and use["name"] not in listed})


def claude_init_findings(init: dict[str, Any], leg: str) -> list[str]:
    """The init event: the one holdspeak server, connected; no instruction
    source; the auth kind."""
    findings: list[str] = []
    servers = init.get("mcp_servers") or []
    names = [s.get("name") for s in servers if isinstance(s, dict)]
    if names != ["holdspeak"]:
        findings.append(f"init MCP servers are {names}, not holdspeak alone")
    elif servers[0].get("status") != "connected":
        findings.append(f"the holdspeak server is {servers[0].get('status')!r}")
    if not any(str(t).startswith(CLAUDE_MCP_PREFIX) for t in init.get("tools") or []) and \
            "ToolSearch" not in (init.get("tools") or []):
        findings.append("the init tool list reaches no holdspeak tool")
    if init.get("apiKeySource") not in (None, "none"):
        findings.append(f"an API key from {init.get('apiKeySource')!r} (the auth is the scratch credentials file)")
    return findings


def claude_context_findings(transcript: list[dict[str, Any]]) -> tuple[list[str], list[dict[str, Any]]]:
    """The model-visible context of the session (Claude's own transcript:
    the prompt snapshot and every attachment before the first answer)."""
    initial: list[dict[str, Any]] = []
    for line in transcript:
        if line.get("type") == "assistant":
            break
        initial.append(line)
    findings: list[str] = []
    for line in initial:
        attachment = line.get("attachment") if isinstance(line.get("attachment"), dict) else {}
        if attachment.get("type") in CLAUDE_INSTRUCTION_ATTACHMENTS:
            findings.append(f"an instruction attachment was loaded: {attachment.get('type')}")
    text = json.dumps(initial, default=str)
    for needle in (str(REPO), str(REPO.resolve()), "HoldSpeak/", "pm/roadmap"):
        if needle in text:
            findings.append(f"the initial context mentions {needle!r}")
    if re.search(r"Contents of [^\"]*(?:CLAUDE|AGENTS)(?:\.local)?\.md", text):
        findings.append("the initial context carries an instruction file's contents")
    if re.search(r"Contents of [^\"]*MEMORY\.md", text):
        findings.append("the initial context carries a memory file's contents")
    return findings, initial


def claude_launch_findings(
    *, work: Path, home: Path, mcp_config: dict[str, Any], leg: str, hub_home: Path,
    hub_url: str, mcp_command: Path = MCP_COMMAND,
) -> tuple[list[str], dict[str, Any]]:
    """The launch-setup check for a Claude session. Empty = lawful."""
    findings: list[str] = []
    record: dict[str, Any] = {"work": str(work), "parents_checked": []}
    if not work.is_dir():
        findings.append(f"working root {work} is not a directory")
    elif any(work.iterdir()):
        findings.append(f"working root {work} is not empty")
    for parent in _chain(work):
        present = [name for name in CLAUDE_CONTEXT_FILES if (parent / name).exists()]
        record["parents_checked"].append({"path": str(parent), "present": present})
        findings += [f"{name} exists at {parent}" for name in present]
    inside = subprocess.run(["git", "-C", str(work), "rev-parse", "--show-toplevel"],
                            capture_output=True, text=True, timeout=30)
    record["git_rev_parse"] = {"exit_code": inside.returncode, "stdout": inside.stdout.strip()}
    if inside.returncode == 0:
        findings.append(f"working root is inside the checkout {inside.stdout.strip()}")
    home_files = _walk_files(home)
    record["home"] = {"path": str(home), "files": home_files}
    if home_files != [".claude/.credentials.json"]:
        findings.append(f"the scratch HOME holds {home_files}, not the credentials file alone")
    servers = (mcp_config.get("mcpServers") or {})
    record["mcp_config"] = redact_mcp_config(mcp_config)
    if list(servers) != ["holdspeak"]:
        findings.append(f"the MCP config names {list(servers)}, not holdspeak alone")
    else:
        server = servers["holdspeak"]
        if leg == "owner":
            if server.get("type") != "stdio" or server.get("command") != str(mcp_command):
                findings.append(f"the OWNER server is not the built sidecar: {record['mcp_config']}")
            if (server.get("env") or {}).get("HOME") != str(hub_home):
                findings.append("the OWNER sidecar HOME is not the isolated hub's")
        else:
            if server.get("type") != "http" or server.get("url") != f"{hub_url}/api/mcp":
                findings.append(f"the AGENT server is not the hub's /api/mcp: {record['mcp_config']}")
            auth = str((server.get("headers") or {}).get("Authorization") or "")
            if not auth.startswith("Bearer ") or len(auth) <= len("Bearer "):
                findings.append("the AGENT server carries no bearer")
    return findings, record


def redact_mcp_config(config: dict[str, Any]) -> dict[str, Any]:
    redacted = copy.deepcopy(config)
    for server in (redacted.get("mcpServers") or {}).values():
        headers = server.get("headers") if isinstance(server, dict) else None
        if isinstance(headers, dict) and headers.get("Authorization"):
            value = str(headers["Authorization"])
            headers["Authorization"] = "Bearer <redacted sha256:" + \
                hashlib.sha256(value.removeprefix("Bearer ").encode()).hexdigest()[:12] + ">"
    return redacted


def claude_mcp_config(leg: str, hub_home: Path, hub_url: str, bearer: str | None) -> dict[str, Any]:
    if leg == "owner":
        server: dict[str, Any] = {"type": "stdio", "command": str(MCP_COMMAND), "args": [],
                                  "env": {"HOME": str(hub_home)}}
    else:
        server = {"type": "http", "url": f"{hub_url}/api/mcp",
                  "headers": {"Authorization": f"Bearer {bearer}"}}
    return {"mcpServers": {"holdspeak": server}}


def read_claude_credentials() -> tuple[dict[str, Any], dict[str, Any]]:
    """The owner's Claude login from the macOS keychain, reduced to the
    access token: the refresh token is dropped, so a scratch session can never
    rotate the owner's login. Returns (credentials, a secret-free record)."""
    # The login keychain is found through HOME; the run's own HOME is a
    # throwaway, so ``security`` reads with the account's home directory.
    import pwd

    account_home = pwd.getpwuid(os.getuid()).pw_dir
    result = subprocess.run(
        ["security", "find-generic-password", "-s", CLAUDE_KEYCHAIN_SERVICE, "-w"],
        capture_output=True, text=True, timeout=30, env={**os.environ, "HOME": account_home},
    )
    if result.returncode != 0:
        raise RuntimeError(f"no Claude login in the keychain ({CLAUDE_KEYCHAIN_SERVICE}): {result.stderr[-200:]}")
    payload = json.loads(result.stdout)
    oauth = dict(payload.get("claudeAiOauth") or {})
    oauth.pop("refreshToken", None)
    oauth.pop("refreshTokenExpiresAt", None)
    expires = float(oauth.get("expiresAt") or 0) / 1000
    record = {
        "source": f"macOS login keychain, generic password service {CLAUDE_KEYCHAIN_SERVICE!r}",
        "kept": sorted(oauth),
        "dropped": ["refreshToken", "refreshTokenExpiresAt"],
        "access_token_expires_at": datetime.fromtimestamp(expires, timezone.utc).isoformat(),
        "minutes_left_at_read": round((expires - time.time()) / 60, 1),
    }
    if expires - time.time() < 20 * 60:
        raise RuntimeError(f"the Claude access token expires in under 20 minutes: {record}")
    return {"claudeAiOauth": oauth}, record


class ClaudeCold:
    """One cold-context Claude launch root: an empty work dir and a scratch
    HOME holding only ``.claude/.credentials.json``."""

    def __init__(self, root: Path, name: str, credentials: dict[str, Any]) -> None:
        self.root = root / name
        self.work = self.root / "work"
        self.home = self.root / "home"
        self.work.mkdir(parents=True, exist_ok=True)
        (self.home / ".claude").mkdir(parents=True, exist_ok=True)
        path = self.home / ".claude" / ".credentials.json"
        old = os.umask(0o077)
        try:
            path.write_text(json.dumps(credentials))
        finally:
            os.umask(old)
        os.chmod(path, 0o600)
        self.mcp_config_path = self.root / "mcp-config.json"

    def env(self) -> dict[str, str]:
        claude_bin = shutil.which("claude") or "/usr/local/bin/claude"
        return {
            "PATH": f"{Path(claude_bin).parent}:/usr/bin:/bin:/usr/sbin:/sbin",
            "HOME": str(self.home),
            "TMPDIR": os.environ.get("TMPDIR", "/tmp"),
            "LANG": "en_US.UTF-8",
            "USER": os.environ.get("USER", "owner"),
        }


def claude_flags(cold: ClaudeCold) -> list[str]:
    return [
        "-p", "--model", CLAUDE_MODEL,
        "--output-format", "stream-json", "--verbose",
        "--strict-mcp-config", "--mcp-config", str(cold.mcp_config_path),
        "--permission-mode", "bypassPermissions",
    ]


def _claude_transcript(cold: ClaudeCold, session_id: str | None) -> Path | None:
    if not session_id:
        return None
    for candidate in sorted((cold.home / ".claude" / "projects").rglob(f"{session_id}.jsonl")):
        return candidate
    return None


def claude_pairing(events: list[dict[str, Any]], rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Pair every holdspeak tool use with one server ``tools/call`` row by
    tool name, arguments and the answer text Claude received."""
    listed: dict[str, str] = {}
    for row in rows:
        request = row.get("request_body")
        if isinstance(request, dict) and request.get("method") == "tools/list":
            for tool in ((row.get("response_body") or {}).get("result") or {}).get("tools") or []:
                listed[claude_sanitized(str(tool.get("name")))] = str(tool.get("name"))
    matches: list[dict[str, Any]] = []
    used: set[int] = set()
    uses = [u for u in claude_tool_uses(events) if u["name"].startswith(CLAUDE_MCP_PREFIX)]
    for use in uses:
        server_name = listed.get(use["name"][len(CLAUDE_MCP_PREFIX):])
        found = None
        for index, row in enumerate(rows):
            request = row.get("request_body")
            if index in used or row.get("path") != "/api/mcp" or not isinstance(request, dict):
                continue
            params = request.get("params") or {}
            if request.get("method") != "tools/call" or params.get("name") != server_name \
                    or (params.get("arguments") or {}) != use["input"]:
                continue
            result = (row.get("response_body") or {}).get("result") or {}
            text = "".join(str(part.get("text", "")) for part in result.get("content") or []
                           if isinstance(part, dict))
            if use["result_text"] is not None and use["result_text"] != text:
                continue
            found = index
            break
        if found is None:
            raise RuntimeError(f"MCP exchange reconciliation for {use['name']!r} found no unused matching /api/mcp row")
        used.add(found)
        matches.append({"tool": use["name"], "server_tool": server_name, "exchange_index": found})
    return {"claude_calls": len(uses), "matches": matches,
            "unmatched_turn_exchanges": [
                {"method": row.get("method"), "path": row.get("path"), "status": row.get("status"),
                 "rpc_method": (row.get("request_body") or {}).get("method")
                 if isinstance(row.get("request_body"), dict) else None}
                for index, row in enumerate(rows) if index not in used]}


def claude_turn(
    *, run_dir: Path, stage: str, prompt: str, cold: ClaudeCold, leg: str, hub: Any,
    session_id: str | None, timeout_s: float,
) -> dict[str, Any]:
    """One ordinary-language Claude turn from the cold root; retain everything."""
    stage_dir = run_dir / "claude" / stage
    stage_dir.mkdir(parents=True, exist_ok=True)
    exchange_start = len(p5._http_exchange_records(hub))
    _json_dump(stage_dir / "transcript-window.json", {"exchange_start": exchange_start})
    findings = prompt_findings(prompt)
    _write_text(stage_dir / "owner-prompt.txt", prompt + "\n")
    if findings:
        raise RuntimeError(f"ordinary-language prompt fence failed for {stage}: {findings}")
    command = ["claude", *claude_flags(cold)]
    if session_id:
        command += ["--resume", session_id]
    _write_text(stage_dir / "command.txt", "$ " + " ".join(command) + "  < owner-prompt.txt\n")
    env = cold.env()
    _json_dump(stage_dir / "environment.json", {"env": env, "cwd": str(cold.work), "stdin": "owner-prompt.txt"})
    _json_dump(stage_dir / "home-at-launch.json", {"home": _walk_files(cold.home), "work": _walk_files(cold.work)})
    started_at = datetime.now(timezone.utc)
    started = time.monotonic()
    try:
        result = subprocess.run(command, cwd=str(cold.work), env=env, input=prompt,
                                capture_output=True, text=True, timeout=timeout_s)
        stdout, stderr, returncode = result.stdout, result.stderr, result.returncode
        outcome = "process_failed" if returncode else "process_completed"
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout.decode() if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = exc.stderr.decode() if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        returncode, outcome = None, "timeout"
    _write_text(stage_dir / "events.jsonl", stdout)
    _write_text(stage_dir / "stderr.log", stderr)
    events = read_events(stage_dir / "events.jsonl")
    final = next((e for e in reversed(events) if e.get("type") == "result"), {})
    _write_text(stage_dir / "last.md", str(final.get("result") or "") + "\n")
    timing = {"started_at": started_at.isoformat(), "finished_at": datetime.now(timezone.utc).isoformat(),
              "elapsed_s": round(time.monotonic() - started, 3), "outcome": outcome, "exit_code": returncode,
              "client_duration_ms": final.get("duration_ms"), "num_turns": final.get("num_turns")}
    _json_dump(stage_dir / "timing.json", timing)
    init = claude_init(events)
    sid = str(init.get("session_id") or final.get("session_id") or session_id or "")
    _write_text(stage_dir / "session-id", sid + "\n")
    transcript_path = _claude_transcript(cold, sid)
    context_findings: list[str] = ["no Claude session transcript was retained"]
    if transcript_path:
        shutil.copy2(transcript_path, stage_dir / "session-transcript.jsonl")
        context_findings, initial = claude_context_findings(read_events(stage_dir / "session-transcript.jsonl"))
        if not session_id:
            _write_text(stage_dir / "initial-context.jsonl",
                        "".join(json.dumps(line, default=str) + "\n" for line in initial))
        else:
            context_findings = [f for f in context_findings]  # the same session, resumed
    rows = p5._http_exchange_records(hub)[exchange_start:]
    uses = claude_tool_uses(events)
    audit: dict[str, Any] = {
        "stage": stage, "leg": leg, "client": "claude", "timing": timing, "session_id": sid,
        "resumed": bool(session_id), "usage_limit": None,
        "result_is_error": bool(final.get("is_error")), "result_text": final.get("result"),
        "init": {"tools": init.get("tools"), "mcp_servers": init.get("mcp_servers"),
                 "model": init.get("model"), "permissionMode": init.get("permissionMode"),
                 "apiKeySource": init.get("apiKeySource"), "memory_paths": init.get("memory_paths"),
                 "plugins": init.get("plugins"), "cwd": init.get("cwd")},
        "init_findings": claude_init_findings(init, leg),
        "zero_read_findings": claude_zero_read_findings(events),
        "initial_context_findings": context_findings,
        "chosen_tools": [u["name"] for u in uses],
        "tool_uses": [{"name": u["name"], "input": u["input"], "is_error": u["is_error"]} for u in uses],
        "unlisted_tools": claude_unlisted(events),
        "tools_listed": len([t for t in init.get("tools") or [] if str(t).startswith(CLAUDE_MCP_PREFIX)]),
        "mcp_statuses": [
            {"status": row.get("status"), "method": (row.get("request_body") or {}).get("method")
             if isinstance(row.get("request_body"), dict) else None}
            for row in _mcp_rows(rows) if str(row.get("method", "")).upper() == "POST"],
        "mcp_other_methods": [{"method": row.get("method"), "status": row.get("status")}
                              for row in _mcp_rows(rows) if str(row.get("method", "")).upper() != "POST"],
        "non_mcp_http_writes": [f"{row.get('method')} {row.get('path')}" for row in rows
                                if str(row.get("method", "")).upper() in {"POST", "PUT", "PATCH", "DELETE"}
                                and row.get("path") != "/api/mcp"],
        "auth_file_changed": False,
    }
    try:
        audit["reconciliation"] = claude_pairing(events, rows)
        audit["reconciliation_error"] = None
    except RuntimeError as exc:
        audit["reconciliation"], audit["reconciliation_error"] = None, str(exc)
    _json_dump(stage_dir / "mcp-audit.json", audit)
    return audit


# ── account redaction at capture time (the repository is public) ─────────
#
# A Claude session's own records carry the signed-in account: its e-mail
# (``session_context``), its organisation id (``credential_org``, the synced
# skill folders) and the names of the account's synced skills. None of it is
# repository material and none of it is read by a fence. Every retained text
# file of a run is rewritten with these replaced; tool names, the MCP server
# list and the attachment types stay.

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
SECRET_RES = {
    "jwt": re.compile(r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"),
    "sk-ant": re.compile(r"sk-ant-[A-Za-z0-9_-]{10,}"),
    "bearer": re.compile(r"Bearer (?!<redacted)[A-Za-z0-9._~+/=-]{16,}"),
}
_UUID = r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
_SYNCED_RE = re.compile(r"\.claude/(?:skills|plugins)/synced/(" + _UUID + r")_(" + _UUID + r")(?:/([^/\"]+))?")
ACCOUNT_EMAIL = "<owner-account-email>"
OTHER_EMAIL = "<email-address>"
ACCOUNT_ID = "<account-id>"
REDACTABLE_SUFFIXES = (".json", ".jsonl", ".txt", ".md", ".log")


def account_markers(run_dir: Path, extra_skills: Iterable[str] = ()) -> dict[str, Any]:
    """What to redact in a run: the account's ids and synced skill names,
    found in the run's own records (never hard-coded)."""
    ids: set[str] = set()
    skills: set[str] = set(extra_skills)
    for path in run_dir.rglob("*"):
        if not path.is_file() or path.suffix not in REDACTABLE_SUFFIXES:
            continue
        text = path.read_text(errors="replace")
        for match in _SYNCED_RE.finditer(text):
            ids.update({match.group(1), match.group(2)})
            if match.group(3) and not match.group(3).startswith("."):
                skills.add(match.group(3))
        for match in re.finditer(r'"organizationUuid":\s*"(' + _UUID + r')"', text):
            ids.add(match.group(1))
    return {"ids": ids, "skills": skills}


def _skill_named(value: Any, skills: set[str]) -> bool:
    name = value.get("name") if isinstance(value, dict) else value
    if not isinstance(name, str):
        return False
    return name in skills or name.startswith("anthropic-skills:")


def _redact_text(text: str, markers: dict[str, Any]) -> str:
    def email(match: re.Match[str]) -> str:
        return OTHER_EMAIL if match.group(0).lower().endswith("@anthropic.com") else ACCOUNT_EMAIL
    text = EMAIL_RE.sub(email, text)
    for value in markers["ids"]:
        text = text.replace(value, ACCOUNT_ID)
    skills = markers["skills"]
    if skills and "\n- " in "\n" + text:
        kept: list[str] = []
        dropped = 0
        for line in text.split("\n"):
            head = line[2:].split(":", 1)[0].strip() if line.startswith("- ") else None
            if head is not None and (head in skills or head.startswith("anthropic-skills:")):
                dropped += 1
                continue
            kept.append(line)
        if dropped:
            kept.append(f"- <{dropped} account skills, names redacted>")
            text = "\n".join(kept)
    return text


def redact_value(value: Any, markers: dict[str, Any]) -> Any:
    if isinstance(value, str):
        return _redact_text(value, markers)
    if isinstance(value, list):
        skills = markers["skills"]
        kept = [item for item in value if not _skill_named(item, skills)]
        dropped = len(value) - len(kept)
        out = [redact_value(item, markers) for item in kept]
        if dropped:
            marker = f"<{dropped} account skills, names redacted>"
            out.append({"name": marker} if value and isinstance(value[0], dict) else marker)
        return out
    if isinstance(value, dict):
        return {key: redact_value(item, markers) for key, item in value.items()}
    return value


def _synced_listing(value: Any) -> Any:
    """Collapse file listings of the synced skill/plugin folders to a count."""
    if isinstance(value, list) and value and all(isinstance(v, str) for v in value):
        synced = [v for v in value if "/synced/" in v]
        if synced:
            return [v for v in value if "/synced/" not in v] + \
                [f"<{len(synced)} account skill and plugin files, names redacted>"]
        return value
    if isinstance(value, dict):
        return {key: _synced_listing(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_synced_listing(item) for item in value]
    return value


def redact_run(run_dir: Path, extra_skills: Iterable[str] = ()) -> dict[str, Any]:
    """Rewrite every retained text file of a run with the account redacted."""
    markers = account_markers(run_dir, extra_skills)
    changed: list[str] = []
    for path in sorted(run_dir.rglob("*")):
        if not path.is_file() or path.suffix not in REDACTABLE_SUFFIXES:
            continue
        original = path.read_text(errors="replace")
        if path.suffix == ".jsonl":
            lines = []
            for line in original.splitlines():
                try:
                    parsed = json.loads(line)
                except ValueError:
                    lines.append(_redact_text(line, markers))
                    continue
                redacted = _synced_listing(redact_value(parsed, markers))
                # A line with nothing to redact keeps its exact bytes.
                lines.append(line if redacted == parsed else json.dumps(redacted, ensure_ascii=False))
            new = "".join(line + "\n" for line in lines)
        elif path.suffix == ".json":
            try:
                parsed = json.loads(original)
                redacted = _synced_listing(redact_value(parsed, markers))
                new = original if redacted == parsed else \
                    json.dumps(redacted, indent=2, sort_keys=True, default=str) + "\n"
            except ValueError:
                new = _redact_text(original, markers)
        else:
            new = _redact_text(original, markers)
        if new != original:
            path.write_text(new)
            changed.append(str(path.relative_to(run_dir)))
    return {"files_changed": changed, "ids": len(markers["ids"]), "skills": len(markers["skills"])}


def account_leak_findings(root: Path) -> list[dict[str, Any]]:
    """Every retained file under ``root`` holding an e-mail address or a
    token-shaped string. The finding names the file and the kind, never the
    value."""
    findings: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        # Every file, binary ones (a DB snapshot, a shot) read as bytes too.
        text = path.read_bytes().decode("utf-8", errors="replace")
        kinds = {"email": len(EMAIL_RE.findall(text))}
        kinds.update({kind: len(pattern.findall(text)) for kind, pattern in SECRET_RES.items()})
        hits = {kind: count for kind, count in kinds.items() if count}
        if hits:
            findings.append({"file": str(path.relative_to(root)), **hits})
    return findings


# ── the hub, the seed, the readbacks ─────────────────────────────────────


def _ops_since(hub: Any, rowid: int) -> list[dict[str, Any]]:
    """Kernel operations made after ``rowid`` (read-only; provenance only —
    each receipt is then read back through the contract)."""
    uri = Path(str(hub.db_path)).resolve().as_uri() + "?mode=ro"
    with closing(sqlite3.connect(uri, uri=True)) as conn:
        conn.row_factory = sqlite3.Row
        return [dict(row) for row in conn.execute(
            "SELECT rowid AS rid, operation_id, name, state, principal_kind, principal_identity,"
            " authority_basis, delegator_kind FROM kernel_operations WHERE rowid > ? ORDER BY rowid",
            (rowid,),
        )]


def _max_op_rowid(hub: Any) -> int:
    uri = Path(str(hub.db_path)).resolve().as_uri() + "?mode=ro"
    with closing(sqlite3.connect(uri, uri=True)) as conn:
        row = conn.execute("SELECT COALESCE(MAX(rowid), 0) FROM kernel_operations").fetchone()
    return int(row[0])


def _read(gw: Any, hub: Any, name: str, args: dict[str, Any], provenance: dict[str, Any]) -> dict[str, Any]:
    return p5._read_op(gw, hub, name, args, provenance)


def _receipt(gw: Any, hub: Any, operation_id: str, provenance: dict[str, Any]) -> dict[str, Any]:
    record = _read(gw, hub, "kernel.receipt.read", {"operation_id": operation_id}, provenance)
    response = p5._response(record)
    objects = response.get("objects") if isinstance(response, dict) else None
    receipt = (objects or [{}])[0].get("receipt") if objects else None
    operation = (objects or [{}])[0].get("operation") if objects else None
    return {"record": record, "receipt": dict(receipt or {}), "operation": operation}


def decision_reason_findings(decision: dict[str, Any]) -> list[str]:
    """A decision on the review list carries its reason in its context, not
    only a title (the owner's review of the first closing run)."""
    findings: list[str] = []
    context = str(decision.get("context_markdown") or "").strip()
    title = str(decision.get("title") or "")
    if not context:
        findings.append("the decision has no context: its reason is missing")
    else:
        lowered = context.lower()
        for group in REASON_FACTS:
            if not any(word in lowered for word in group):
                findings.append(f"the decision context does not carry the reason ({' / '.join(group)})")
    if "because" in title.lower() or len(title) > 120:
        findings.append(f"the reason is in the title: {title!r}")
    return findings


def _context_phrase(context: str) -> str:
    """A run of plain words from the context, as the face shows it."""
    words = re.findall(r"[A-Za-z0-9']+", context)
    return " ".join(words[:4])


def _receipts_for(gw: Any, hub: Any, ops: list[dict[str, Any]], provenance: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for op in ops:
        read = _receipt(gw, hub, str(op["operation_id"]), provenance)
        out.append({"operation": op, "receipt": read["receipt"], "read": read["record"]})
    return out


def _seed(hub: Any) -> dict[str, str]:
    """The zone and the two notes, through the real HTTP producers."""
    status, zone = hub.api("POST", "/api/directories", {"name": ZONE_NAME})
    if status >= 400:
        raise RuntimeError(f"zone seed failed ({status}): {zone!r}")
    ids = {"zone": str(zone["directory"]["id"])}
    for key, note in (("owner_note", OWNER_NOTE), ("agent_note", AGENT_NOTE)):
        status, made = hub.api("POST", "/api/notes", note)
        if status >= 400:
            raise RuntimeError(f"note seed failed ({status}): {made!r}")
        ids[key] = str(made["note"]["id"])
    return ids


def _members(gw: Any, hub: Any, zone_id: str, provenance: dict[str, Any]) -> tuple[list[str], dict[str, Any]]:
    record = _read(gw, hub, "zone.members", {"directory_id": zone_id}, provenance)
    response = p5._response(record)
    rows = response.get("members") if isinstance(response, dict) else response
    refs: list[str] = []
    for row in rows or []:
        if isinstance(row, dict):
            refs.append(str(row.get("primitive_id") or row.get("ref") or row.get("id")))
        else:
            refs.append(str(row))
    return refs, record


def _preflight_engine(run_dir: Path) -> dict[str, Any]:
    return p5._preflight(run_dir, ENGINE_URL)


# ── the Desk ─────────────────────────────────────────────────────────────


def _open_desk(play: Any, hub: Any) -> tuple[Any, tuple[Any, Any]]:
    browser = play.chromium.launch(headless=True)
    pages = []
    for width, height in ((1440, 900), (393, 852)):
        context = browser.new_context(viewport={"width": width, "height": height}, device_scale_factor=1)
        page = context.new_page()
        page.goto(f"{hub.url}/?token={quote(hub.token)}", wait_until="networkidle")
        try:
            page.get_by_role("button", name="Continue later", exact=True).click(timeout=1500)
        except Exception:
            pass
        pages.append(page)
    return browser, (pages[0], pages[1])


def _shoot_owner(run_dir: Path, hub: Any, ids: dict[str, str], owner: dict[str, Any]) -> None:
    """The OWNER leg's result, labelled ``owner-*``: the zone with the owner's
    note alone, the decision with its reason readable, the brief row."""
    from playwright.sync_api import sync_playwright

    decision = owner.get("decision") or {}
    title = str(decision.get("title") or "")
    phrase = _context_phrase(str(decision.get("context_markdown") or ""))
    with sync_playwright() as play:
        browser, pages = _open_desk(play, hub)
        try:
            shots: dict[str, Any] = {"label": "OWNER leg, before the agent leg files"}
            shots["zone"] = p5._reopen_stage(pages, hub, run_dir, "owner-zone", f"zone:{ids['zone']}",
                                             expected_text=OWNER_NOTE["title"])
            shots["zone"]["pullouts"] = _pullout_proof(pages, OWNER_NOTE["title"], absent=AGENT_NOTE["title"])
            shots["decision"] = p5._reopen_stage(pages, hub, run_dir, "owner-decision",
                                                 f"decision:{owner['decision_id']}", expected_text=title)
            shots["decision"]["pullouts"] = _pullout_proof(pages, phrase, readable=True)
            shots["brief"] = p5._reopen_stage(pages, hub, run_dir, "brief", "intelligence:desk",
                                              expected_text=title,
                                              expected_source_ref=f"decision:{owner['decision_id']}")
            _json_dump(run_dir / "observations" / "owner-desk.json", shots)
        finally:
            browser.close()


def _shoot_agent(run_dir: Path, hub: Any, ids: dict[str, str]) -> None:
    """The AGENT leg's result, labelled ``agent-zone``: both notes filed."""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as play:
        browser, pages = _open_desk(play, hub)
        try:
            shots: dict[str, Any] = {"label": "AGENT leg, after the delegated filing"}
            shots["zone"] = p5._reopen_stage(pages, hub, run_dir, "agent-zone", f"zone:{ids['zone']}",
                                             expected_text=AGENT_NOTE["title"])
            shots["zone"]["pullouts"] = _pullout_proof(pages, AGENT_NOTE["title"])
            _json_dump(run_dir / "observations" / "agent-desk.json", shots)
        finally:
            browser.close()


_READABLE_JS = r"""(phrase) => {
    const bodies = [...document.querySelectorAll('.desk-pullout-body')];
    const walker = (root) => document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    for (const body of bodies) {
        const w = walker(body);
        let node;
        while ((node = w.nextNode())) {
            const text = node.textContent.replace(/\s+/g, ' ');
            if (!text.toLowerCase().includes(phrase.toLowerCase())) continue;
            const el = node.parentElement;
            el.scrollIntoView({block: 'center'});
            const r = el.getBoundingClientRect();
            const cs = getComputedStyle(el);
            const x = r.left + Math.min(r.width / 2, 20), y = r.top + Math.min(r.height / 2, 8);
            const hit = document.elementFromPoint(x, y);
            return {found: true, text: text.slice(0, 200),
                    visible: r.width > 0 && r.height > 0 && cs.visibility !== 'hidden' && cs.display !== 'none',
                    in_viewport: r.top >= 0 && r.left >= 0 && r.bottom <= innerHeight && r.right <= innerWidth,
                    hit: !!hit && (hit === el || el.contains(hit) || hit.contains(el)),
                    font_px: parseFloat(cs.fontSize), opacity: parseFloat(cs.opacity)};
        }
    }
    return {found: false};
}"""


def _pullout_proof(pages: tuple[Any, Any], must_contain: str, *, absent: str | None = None,
                   readable: bool = False) -> list[dict[str, Any]]:
    """The reopened object's window is open and shows ``must_contain`` at both
    widths (the Chair's own rows can carry the same words, so the body text
    alone is not proof)."""
    proof: list[dict[str, Any]] = []
    for width, page in zip((1440, 393), pages):
        bodies = page.locator(".desk-pullout-body")
        texts = [bodies.nth(i).inner_text(timeout=5_000) for i in range(bodies.count())]
        flat = [" ".join(text.split()) for text in texts]
        ok = any(must_contain.lower() in text.lower() for text in flat)
        row: dict[str, Any] = {"viewport": width, "pullout_texts": texts, "contains": must_contain, "ok": ok}
        if absent is not None:
            row["absent"] = absent
            if any(absent in text for text in texts):
                raise RuntimeError(f"the window shows {absent!r} too early at {width}px")
        if readable and ok:
            row["readable"] = page.evaluate(_READABLE_JS, must_contain)
            r = row["readable"]
            if not (r.get("found") and r.get("visible") and r.get("in_viewport") and r.get("hit")
                    and r.get("font_px", 0) >= 12 and r.get("opacity", 0) >= 0.5):
                raise RuntimeError(f"the context is not readable at {width}px: {r}")
        proof.append(row)
        if not ok:
            raise RuntimeError(f"no open window shows {must_contain!r} at {width}px: {texts!r}")
    return proof


# ── the run ──────────────────────────────────────────────────────────────


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="mode", required=True)
    run = sub.add_parser("run", help="one fresh cold-context rehearsal, both legs")
    run.add_argument("--out", required=True, help="parent directory for the unique run")
    run.add_argument("--codex-timeout", type=float, default=900)
    run.add_argument("--legs", default="owner,agent")
    run.add_argument("--client", choices=("claude", "codex"), default="claude",
                     help="the cold-context client (R6: claude closes the phase)")
    run.add_argument("--codex-auth", type=Path, default=Path.home() / ".codex" / "auth.json",
                     help="the Codex auth file copied (alone) into each scratch CODEX_HOME")
    return parser


#: The auth file the scratch CODEX_HOME receives; set from ``--codex-auth``.
CODEX_AUTH: list[Path] = [Path.home() / ".codex" / "auth.json"]


def _run(args: argparse.Namespace) -> int:
    CODEX_AUTH[0] = Path(args.codex_auth).expanduser().resolve()
    CLIENT[0] = args.client
    global AGENT_IDENTITY
    AGENT_IDENTITY = f"{args.client}-desk-agent"
    run_dir = _unique_run_dir(Path(args.out).resolve())
    legs = [leg.strip() for leg in args.legs.split(",") if leg.strip()]
    started_at = datetime.now(timezone.utc)
    started = time.monotonic()
    temp_root = Path(tempfile.mkdtemp(prefix="philo7-04-"))
    hub_home = temp_root / "hub-home"
    hub_home.mkdir()
    gw = _gw()
    provenance = gw.base_provenance(engine_mode="none")
    provenance["engine_mode_reason"] = (
        "the four jobs call no model: filing, finding and recording a decision are "
        "desk writes and reads, and the brief producer is deterministic "
        "(holdspeak/services/monday_brief_service.py generate)"
    )
    _json_dump(run_dir / "run.json", {
        "claim": CLAIM if CLIENT[0] == "claude" else CLAIM_CODEX,
        "client": CLIENT[0],
        "model": CLAUDE_MODEL if CLIENT[0] == "claude" else MODEL,
        "label": REVIEW_LABEL,
        "observed_sitting": False,
        "engine_mode": "none",
        "temp_root": str(temp_root),
        "hub_home": str(hub_home),
        "reasoning_effort": EFFORT if CLIENT[0] == "codex" else None,
        "legs": legs,
        "prompts": PROMPTS,
    })
    legs_out: dict[str, Any] = {}
    blocked: list[str] = []
    hub = None
    browser = None
    try:
        if CLIENT[0] == "claude":
            credentials, auth_record = read_claude_credentials()
            CLAUDE_CREDENTIALS[:] = [credentials]
            _json_dump(run_dir / "claude-auth.json", auth_record)
        preflight = _preflight_engine(run_dir)
        hub = gw.Hub(hub_home, token=TOKEN, record_rehearsal=True,
                     transcript_path=hub_home / "rehearsal-transcript.jsonl").start()
        proof = p5._hub_proof(hub, hub_home)
        _json_dump(run_dir / "hub-proof.json", proof)
        provenance.update({"hub": proof, "db_path": proof["db_path"], "engine_preflight": {
            "exit_code": preflight.get("exit_code"),
            "models": [m.get("model") or m.get("name") for m in ((preflight.get("payload") or {}).get("models") or [])
                       if isinstance(m, dict)],
        }})
        ids = _seed(hub)
        _json_dump(run_dir / "seed.json", {"ids": ids, "zone": ZONE_NAME, "notes": [OWNER_NOTE, AGENT_NOTE],
                                          "how": "POST /api/directories and POST /api/notes as the owner"})
        members_before, members_before_read = _members(gw, hub, ids["zone"], provenance)

        if "owner" in legs:
            legs_out["owner"] = _owner_leg(run_dir, temp_root, hub, gw, ids, provenance, args.codex_timeout)
            blocked += [f"OWNER: {b}" for b in legs_out["owner"]["blocked"]]
            # The OWNER leg's result is shot BEFORE the agent leg files.
            owner = legs_out["owner"]
            if owner.get("readbacks_ok"):
                _shoot_owner(run_dir, hub, ids, owner)
            else:
                _write_text(run_dir / "shots-not-taken.txt",
                            "The Desk was not shot: the OWNER leg's readbacks did not complete.\n")
        if "agent" in legs:
            legs_out["agent"] = _agent_leg(run_dir, temp_root, hub, gw, ids, provenance, args.codex_timeout)
            blocked += [f"AGENT: {b}" for b in legs_out["agent"]["blocked"]]
        _json_dump(run_dir / "legs.json", legs_out)

        agent = legs_out.get("agent") or {}
        if "agent" in legs and not agent.get("blocked"):
            _shoot_agent(run_dir, hub, ids)
        _json_dump(run_dir / "members-before.json", {"members": members_before, "read": members_before_read})
    except Exception as exc:
        blocked.append(f"driver: {type(exc).__name__}: {exc}")
        _write_text(run_dir / "run-error.txt", f"{type(exc).__name__}: {exc}\n")
    finally:
        if browser is not None:
            try:
                browser.close()
            except Exception:
                pass
        if hub is not None:
            _json_dump(run_dir / "hub-proof-final.json", p5._hub_proof(hub, hub_home))
            if hub.db_path and Path(str(hub.db_path)).exists():
                p5._backup_db(Path(str(hub.db_path)), run_dir / "db-proof.sqlite")
                from holdspeak.runtime_lock import owner_lock_path

                lock = owner_lock_path(Path(str(hub.db_path)))
                if lock.exists():
                    shutil.copy2(lock, run_dir / "db-owner.lock")
            hub.stop()
            _write_text(run_dir / "hub.log", "\n".join(hub.lines) + "\n")
            transcript = getattr(hub, "transcript_path", None)
            if transcript and Path(transcript).exists():
                shutil.copy2(transcript, run_dir / "rehearsal-transcript.jsonl")
        # The scratch Codex homes hold a copy of the owner's Codex auth file;
        # it never outlives the run.
        # The account's synced skill names, from every scratch HOME, then the
        # redaction of every retained file (the repository is public).
        synced = {path.name for path in temp_root.glob("cold-*/home/.claude/skills/synced/*/*")
                  if path.is_dir()}
        for auth in [*temp_root.glob("cold-*/home/.codex/auth.json"),
                     *temp_root.glob("cold-*/home/.claude/.credentials.json"),
                     *temp_root.glob("cold-*/mcp-config.json")]:
            auth.unlink(missing_ok=True)
        CLAUDE_CREDENTIALS.clear()
        _json_dump(run_dir / "provenance.json", provenance)
        _json_dump(run_dir / "run-status.json", {
            "started_at": started_at.isoformat(),
            "finished_at": datetime.now(timezone.utc).isoformat(),
            "elapsed_s": round(time.monotonic() - started, 3),
            "outcome": "blocked" if blocked else "completed",
            "blocked": blocked,
            "label": REVIEW_LABEL,
            "claim": CLAIM if CLIENT[0] == "claude" else CLAIM_CODEX,
        })
    redaction = redact_run(run_dir, synced)
    _json_dump(run_dir / "redaction.json", {
        "rule": "e-mail addresses -> <owner-account-email> (other addresses <email-address>); "
                "account/organisation ids -> <account-id>; the account's synced skill names -> a count",
        **redaction,
    })
    print(f"RUN_DIR {run_dir}")
    print(f"PROOF {REVIEW_LABEL}")
    print(f"OUTCOME {'BLOCKED' if blocked else 'COMPLETED'}")
    for line in blocked:
        print(f"BLOCKED {line}")
    return 0 if not blocked else 3


def _leg_setup(run_dir: Path, temp_root: Path, hub: Any, leg: str, bearer: str | None,
               label: str) -> tuple[Any, dict[str, Any]]:
    if CLIENT[0] == "claude":
        cold = ClaudeCold(temp_root, f"cold-{label}", CLAUDE_CREDENTIALS[0])
        config = claude_mcp_config(leg, Path(hub.home), hub.url, bearer)
        old = os.umask(0o077)
        try:
            cold.mcp_config_path.write_text(json.dumps(config))
        finally:
            os.umask(old)
        findings, record = claude_launch_findings(
            work=cold.work, home=cold.home, mcp_config=config, leg=leg,
            hub_home=Path(hub.home), hub_url=hub.url,
        )
        record["findings"] = findings
        record["flags"] = claude_flags(cold)
        record["env_keys"] = sorted(cold.env())
        record["mcp_config_path"] = str(cold.mcp_config_path)
        record["claude_version"] = subprocess.run(["claude", "--version"], capture_output=True,
                                                  text=True, timeout=30).stdout.strip()
        _json_dump(run_dir / label / "launch-setup.json", record)
        _json_dump(run_dir / label / "mcp-config.redacted.json", redact_mcp_config(config))
        return cold, {"findings": findings, "record": record}
    cold = Cold(temp_root, f"cold-{label}", CODEX_AUTH[0])
    env = cold.env(bearer)
    config = effective_config(cold, leg, Path(hub.home), hub.url, run_dir / label / "effective-codex-config.json", env)
    servers = (config.get("mcp_list") or {}).get("output")
    findings, record = launch_setup_findings(
        work=cold.work, codex_home=cold.codex_home, codex_process_home=cold.home,
        servers=servers, leg=leg, hub_home=Path(hub.home), hub_url=hub.url,
    )
    record["findings"] = findings
    _json_dump(run_dir / label / "launch-setup.json", record)
    return cold, {"findings": findings, "record": record}


def _owner_leg(run_dir: Path, temp_root: Path, hub: Any, gw: Any, ids: dict[str, str],
               provenance: dict[str, Any], timeout_s: float) -> dict[str, Any]:
    out: dict[str, Any] = {"blocked": [], "turns": {}, "readbacks_ok": False}
    cold, setup = _leg_setup(run_dir, temp_root, hub, "owner", None, "owner")
    out["launch_setup"] = setup
    if setup["findings"]:
        out["blocked"].append(f"launch setup: {setup['findings']}")
        return out
    rowid = _max_op_rowid(hub)
    session: str | None = None
    for stage in ("owner_file", "owner_find", "owner_decide", "owner_brief"):
        audit = client_turn(run_dir=run_dir, stage=stage, prompt=PROMPTS[stage], cold=cold, leg="owner",
                            hub=hub, session_id=session, bearer=None, timeout_s=timeout_s)
        out["turns"][stage] = _slim(audit)
        session = audit.get("session_id") or session
        stops = turn_blockers(audit)
        if stops:
            out["blocked"] += [f"{stage}: {s}" for s in stops]
            return out
    ops = _ops_since(hub, rowid)
    out["operations"] = ops
    out["receipts"] = _receipts_for(gw, hub, ops, provenance)
    members, members_read = _members(gw, hub, ids["zone"], provenance)
    note_read = _read(gw, hub, "note.read", {"note_id": ids["owner_note"]}, provenance)
    decisions_read = _read(gw, hub, "decision.list", {}, provenance)
    decisions = p5._response(decisions_read)
    rows = decisions.get("decisions") if isinstance(decisions, dict) else decisions
    matching = [row for row in rows or [] if isinstance(row, dict)
                and "nightly build" in json.dumps(row, default=str).lower()]
    brief_read = _read(gw, hub, "brief.latest", {}, provenance)
    brief_items = p5._brief_items(p5._response(brief_read))
    out["readbacks"] = {"zone_members": members_read, "note_read": note_read,
                        "decision_list": decisions_read, "brief_latest": brief_read}
    problems: list[str] = []
    if f"note:{ids['owner_note']}" not in members:
        problems.append(f"the note is not in its zone: {members}")
    if len(matching) != 1:
        problems.append(f"{len(matching)} decisions carry the words")
    else:
        decision = matching[0]
        out["decision_id"] = str(decision.get("id"))
        if decision.get("status") != "proposed":
            problems.append(f"the decision status is {decision.get('status')!r}, not on the review list")
        if not any(item.get("source_ref") == f"decision:{out['decision_id']}" for item in brief_items):
            problems.append("the brief has no row for the decision")
        # The owner's review: the decision carries its reason in its context,
        # read back durably through the contract (never from the client's text).
        detail_read = _read(gw, hub, "decision.read", {"decision_id": out["decision_id"]}, provenance)
        out["readbacks"]["decision_read"] = detail_read
        detail = p5._response(detail_read) or {}
        detail = detail.get("decision") if isinstance(detail.get("decision"), dict) else detail
        out["decision"] = {key: detail.get(key) for key in (
            "id", "title", "status", "context_markdown", "decision_markdown", "consequences_markdown")}
        problems += decision_reason_findings(detail)
    find_rows = p5._http_exchange_records(hub)
    window = json.loads((run_dir / CLIENT[0] / "owner_find" / "transcript-window.json").read_text())
    end = json.loads((run_dir / CLIENT[0] / "owner_decide" / "transcript-window.json").read_text())["exchange_start"]
    found = [row for row in find_rows[window["exchange_start"]:end]
             if row.get("path") == "/api/mcp" and ids["owner_note"] in json.dumps(row.get("response_body"), default=str)
             and ids["zone"] in json.dumps(row.get("response_body"), default=str)]
    out["find_server_rows"] = len(found)
    if not found:
        problems.append("no server answer in the find turn names both the note and its zone (by id)")
    names = [op["name"] for op in ops]
    out["operation_names"] = names
    for required in ("zone.file", "decision.create"):
        if names.count(required) != 1:
            problems.append(f"{names.count(required)} {required} operations, not one")
    for item in out["receipts"]:
        receipt = item["receipt"]
        if receipt.get("state") not in {"succeeded", "refused", "failed", "indeterminate"}:
            problems.append(f"a non-terminal receipt: {item['operation']['operation_id']} {receipt.get('state')!r}")
        if receipt.get("actor_kind") != "owner" or item["operation"].get("principal_kind") != "owner":
            problems.append(f"a receipt whose actor is not the OWNER: {item['operation']['operation_id']}")
    out["readback_problems"] = problems
    out["readbacks_ok"] = not problems
    if problems:
        out["blocked"] += [f"readback: {p}" for p in problems]
    return out


def _agent_leg(run_dir: Path, temp_root: Path, hub: Any, gw: Any, ids: dict[str, str],
               provenance: dict[str, Any], timeout_s: float) -> dict[str, Any]:
    out: dict[str, Any] = {"blocked": [], "runs": {}}
    status, enabled = hub.api("PUT", "/api/settings/remote", {"enabled": True})
    status_c, issued = hub.api("POST", "/api/settings/remote/credentials",
                               {"identity": AGENT_IDENTITY, "palette": "DESK"})
    if status >= 400 or status_c >= 400 or not isinstance(issued, dict) or not issued.get("token"):
        out["blocked"].append(f"credential issue failed ({status}, {status_c}): {issued!r}")
        return out
    bearer = str(issued["token"])
    out["credential"] = {k: v for k, v in issued.items() if k != "token"}
    out["credential"]["token_sha256_12"] = hashlib.sha256(bearer.encode()).hexdigest()[:12]
    out["credential"]["route"] = "POST /api/settings/remote/credentials"
    _json_dump(run_dir / "agent" / "credential.json", out["credential"])

    def one_run(label: str) -> dict[str, Any]:
        cold, setup = _leg_setup(run_dir, temp_root, hub, "agent", bearer, label)
        record: dict[str, Any] = {"launch_setup": setup}
        if setup["findings"]:
            record["blocked"] = [f"launch setup: {setup['findings']}"]
            return record
        rowid = _max_op_rowid(hub)
        audit = client_turn(run_dir=run_dir, stage=label, prompt=PROMPTS["agent_file"], cold=cold,
                            leg="agent", hub=hub, session_id=None, bearer=bearer, timeout_s=timeout_s)
        record["audit"] = _slim(audit)
        statuses = [row.get("status") for row in audit["mcp_statuses"]]
        record["bearer_answer"] = {
            "mcp_statuses": audit["mcp_statuses"],
            "sent_and_accepted": bool(statuses) and all(s == 200 or s == 204 for s in statuses),
            "unauthenticated": any(s == 401 for s in statuses),
        }
        status_r, remote = hub.api("GET", "/api/settings/remote")
        listed_credentials = remote.get("credentials") if isinstance(remote, dict) else None
        record["credential_after"] = [
            {k: v for k, v in c.items() if k != "token"}
            for c in listed_credentials or [] if c.get("identity") == AGENT_IDENTITY
        ]
        record["blocked"] = turn_blockers(audit)
        if record["bearer_answer"]["unauthenticated"] or not statuses:
            record["blocked"].append("the AGENT session did not authenticate on /api/mcp with the DESK bearer")
        ops = _ops_since(hub, rowid)
        record["operations"] = ops
        record["receipts"] = _receipts_for(gw, hub, ops, provenance)
        members, members_read = _members(gw, hub, ids["zone"], provenance)
        record["zone_members"] = members
        record["zone_members_read"] = members_read
        with closing(sqlite3.connect(Path(str(hub.db_path)).resolve().as_uri() + "?mode=ro", uri=True)) as conn:
            record["awaiting_decision"] = conn.execute(
                "SELECT COUNT(*) FROM kernel_operations WHERE state='awaiting_decision'").fetchone()[0]
        return record

    ungranted = one_run("agent_ungranted")
    out["runs"]["ungranted"] = ungranted
    status_g, granted = hub.api("PUT", f"/api/settings/remote/delegations/{AGENT_IDENTITY}", {})
    out["grant"] = {"status": status_g, "response": granted,
                    "route": f"PUT /api/settings/remote/delegations/{AGENT_IDENTITY}"}
    grant_id = granted.get("grant_id") if isinstance(granted, dict) else None
    if isinstance(granted, dict) and granted.get("operation_id"):
        out["grant"]["receipt"] = _receipt(gw, hub, str(granted["operation_id"]), provenance)["receipt"]
    granted_run = one_run("agent_granted")
    out["runs"]["granted"] = granted_run
    _json_dump(run_dir / "agent" / "grant.json", out["grant"])

    for label, record in (("ungranted", ungranted), ("granted", granted_run)):
        out["blocked"] += [f"{label}: {b}" for b in record.get("blocked") or []]
    if out["blocked"]:
        return out
    refused = [r["receipt"] for r in ungranted["receipts"] if r["operation"]["name"] == "zone.file"]
    filed = [r["receipt"] for r in granted_run["receipts"] if r["operation"]["name"] == "zone.file"]
    findings = agent_receipt_findings(refused[0] if len(refused) == 1 else None,
                                      filed[0] if len(filed) == 1 else None,
                                      identity=AGENT_IDENTITY, grant_id=grant_id)
    if f"note:{ids['agent_note']}" in ungranted["zone_members"]:
        findings.append("the note was filed without the grant")
    if f"note:{ids['agent_note']}" not in granted_run["zone_members"]:
        findings.append("the note was not filed with the grant")
    if ungranted["awaiting_decision"] or granted_run["awaiting_decision"]:
        findings.append("an operation is held in awaiting_decision")
    out["receipt_findings"] = findings
    out["blocked"] += [f"receipts: {f}" for f in findings]
    return out


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        return _run(args)
    except Exception as exc:
        print(f"PHILO7_FILE_AND_FIND_BLOCKED {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
