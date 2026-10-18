"""Fake ``claude`` and ``codex`` executables for CLI engine tests (Betterment E1).

Tests never run the owner's real agent CLIs: they would use his sign-in and
bill him. ``install_fake_agent_clis(bin_dir)`` writes two scripts into a
folder inside the test's temp dir; the test puts that folder first on PATH.

Each call appends one JSON line to ``<bin>/<name>-calls.jsonl``: argv, cwd,
the cwd's entries, the stdin prompt and the pid. ``set_mode(bin_dir, name,
mode)`` picks the behaviour: ``answer`` (default), ``sleep`` (60 s, for the
timeout kill), ``fail`` (exit 1) or ``error`` (Claude's ``is_error`` result).
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
import json, os, sys, time, pathlib
here = pathlib.Path(__file__).resolve().parent
name = {name!r}
prompt = sys.stdin.read()
with (here / (name + "-calls.jsonl")).open("a") as log:
    log.write(json.dumps({{"argv": sys.argv[1:], "cwd": os.getcwd(), "cwd_entries": os.listdir("."),
                          "prompt": prompt, "pid": os.getpid()}}) + "\\n")
mode_file = here / (name + "-mode")
mode = mode_file.read_text().strip() if mode_file.exists() else "answer"
if mode == "sleep":
    time.sleep(60)
if mode == "fail":
    print("Invalid API key. Please run /login", file=sys.stderr)
    sys.exit(1)
if name == "claude":
    if mode == "error":
        print(json.dumps({{"type": "result", "subtype": "error_max_budget_usd", "is_error": True}}))
        sys.exit(0)
    answer = (here / "claude-answer").read_text() if (here / "claude-answer").exists() else {claude_answer!r}
    print(json.dumps({{"type": "result", "subtype": "success", "is_error": False, "result": answer,
                      "total_cost_usd": {cost!r}, "usage": {{"input_tokens": 11, "output_tokens": 5}},
                      "modelUsage": {{"claude-fake-1": {{}}}}}}))
else:
    print({codex_answer!r})
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
