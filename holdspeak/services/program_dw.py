"""Delivery Workbench at a Program's two points (PG-LANG §8; owner rule: dw at
major points only, never the engine on itself).

- **At create** (the link point): a Program made on a repository with the
  rails (``.githooks/dw``) reads ``dw context`` once and keeps a summary of
  at most 2 KB (``kind = dw_context`` on its ledger): each project, its
  active phase and stories, the next story. Every step's brief carries it as
  data (``program_brief.compose``). A failed read is one plain line; the
  Program goes on.
- **HoldSpeak's own repository** never takes ``delivery dw``
  (``delivery_own_repository``): the engine does not record its own work.
- **At Done** (``program_delivery``): a delivery to a whole phase
  (``dw <project>/<phase>``) also closes that phase in the same pull request
  (``dw phase close``); dw's refusal keeps the phase open and says so.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Optional

from ..logging_config import get_logger

log = get_logger("program_dw")

KIND = "dw_context"
#: The summary's bound (the brief carries it whole).
MAX_BYTES = 2048
TIMEOUT_SECONDS = 20


def has_rails(root: Any) -> bool:
    return bool(root) and (Path(str(root)) / ".githooks" / "dw").exists()


def own_repository(root: Any) -> bool:
    """The repository is HoldSpeak's own (its ``pyproject.toml`` names the
    ``holdspeak`` package)."""
    try:
        import tomllib

        data = tomllib.loads((Path(str(root or "")) / "pyproject.toml").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    return str((data.get("project") or {}).get("name") or "").strip().lower() == "holdspeak"


def bound(text: str, limit: int = MAX_BYTES) -> str:
    """At most ``limit`` UTF-8 bytes, whole lines, a last line saying so."""
    data = text.encode("utf-8")
    if len(data) <= limit:
        return text
    tail = "\n… (cut at 2 KB)"
    out: list[str] = []
    size = len(tail.encode("utf-8"))
    for line in text.splitlines():
        cost = len(line.encode("utf-8")) + 1
        if size + cost > limit:
            break
        out.append(line)
        size += cost
    return "\n".join(out) + tail


def summary(document: Mapping[str, Any]) -> str:
    """The roadmap in plain lines: each project, its active phases with their
    stories, and the next story."""
    lines: list[str] = []
    for project in document.get("projects") or []:
        slug = str(project.get("slug") or "?")
        phases = [row for row in project.get("phases") or [] if row.get("active")]
        nxt = project.get("next_story") or {}
        head = f"Project {slug}"
        if nxt.get("story_id"):
            head += f" · next story {nxt['story_id']} “{nxt.get('title') or ''}” ({nxt.get('status') or 'open'})"
        lines.append(head)
        for phase in phases[-2:]:
            stories = phase.get("stories") or []
            done = sum(1 for row in stories if str(row.get("status")) == "done")
            lines.append(f"- phase {phase.get('number')} {phase.get('slug')}: {done} of {len(stories)} stories done")
            for row in stories:
                if str(row.get("status")) != "done":
                    lines.append(f"  - {row.get('story_id')} “{row.get('title')}” · {row.get('status')}")
    return "\n".join(lines)


def read_context(root: Any, *, runner: Any = None) -> tuple[str, str]:
    """``(summary, failure words)`` of ``dw context --compact`` in ``root``."""
    from ..missioncontrol_bridge import dw_argv_base

    base = dw_argv_base(Path(str(root)))
    if base is None:
        return "", "Delivery Workbench is not installed"
    argv = [*base, "context", "--compact"]
    try:
        if runner is None:
            from .program_runner import _default_runner as runner  # the engine's one process site
        proc = runner(argv, cwd=str(root), timeout=TIMEOUT_SECONDS)
    except Exception as exc:
        return "", f"dw context did not run ({type(exc).__name__})"
    if proc.returncode != 0:
        return "", "dw context failed"
    try:
        document = json.loads(proc.stdout or "{}")
    except ValueError:
        return "", "dw context printed no roadmap"
    return bound(summary(document)), ""


def link(service: Any, program: Mapping[str, Any]) -> Optional[dict[str, Any]]:
    """At create: read the context once and keep it on the ledger."""
    root = program.get("repo_root")
    if not has_rails(root):
        return None
    try:
        run = service.runner()._run
    except Exception:
        run = None
    text, failed = read_context(root, runner=run)
    line = (f"Read the Delivery Workbench roadmap ({len(text.encode('utf-8'))} bytes for the briefs)" if text
            else f"Did not read the Delivery Workbench roadmap: {failed}")
    service.store.add_checkpoint(step_id="", program_id=program["id"], at=service._clock(), by="engine", line=line,
                                 kind=KIND, undo={"text": text} if text else {"failed": failed})
    return {"text": text, "failed": failed}


def context_of(store: Any, program_id: str) -> str:
    """The kept summary (the newest ``dw_context`` row), else ``""``."""
    row = next((row for row in store.list_checkpoints(program_id) if row.get("kind") == KIND), None)
    return str(((row or {}).get("undo") or {}).get("text") or "")


__all__ = ["KIND", "MAX_BYTES", "bound", "context_of", "has_rails", "link", "own_repository", "read_context",
           "summary"]
