"""Workbench agent memory: append-only JSONL per workbench (HS-116-16).

Each workbench accumulates observations from completed runs. The conductor
writes back after each item; the conductor reads before each run. Memory is
advisory — it informs, never authorizes.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from .logging_config import get_logger

log = get_logger("workbench_memory")

MAX_ENTRIES = 100
RECALL_ENTRIES = 20
RECALL_BUDGET_BYTES = 2048
WORKBENCH_DIR = Path.home() / ".holdspeak" / "workbenches"


def _memory_path(workbench_id: str) -> Path:
    return WORKBENCH_DIR / workbench_id / "memory.jsonl"


def read_memory(workbench_id: str) -> list[dict]:
    """Read all memory entries for a workbench, newest first."""
    path = _memory_path(workbench_id)
    if not path.is_file():
        return []
    entries = []
    try:
        for line in path.read_text(encoding="utf-8").strip().splitlines():
            if line.strip():
                entries.append(json.loads(line))
    except (OSError, json.JSONDecodeError) as exc:
        log.warning(f"Memory read failed for {workbench_id}: {exc}")
        return []
    entries.reverse()
    return entries


def append_memory(
    workbench_id: str,
    run_id: str,
    kind: str,
    content: str,
    item_title: str = "",
    provenance: Optional[dict] = None,
) -> dict:
    """Append a memory entry. Evicts oldest if over MAX_ENTRIES."""
    path = _memory_path(workbench_id)
    path.parent.mkdir(parents=True, exist_ok=True)

    entry = {
        "run_id": run_id,
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "kind": kind,
        "content": content.strip(),
        "item_title": item_title,
        "provenance": provenance or {},
    }

    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except OSError as exc:
        log.warning(f"Memory append failed for {workbench_id}: {exc}")
        return entry

    _enforce_limit(path)
    return entry


def recall_for_prompt(workbench_id: str) -> str:
    """Build the [MEMORY] block for prompt injection. Most recent RECALL_ENTRIES,
    bounded by RECALL_BUDGET_BYTES."""
    entries = read_memory(workbench_id)[:RECALL_ENTRIES]
    if not entries:
        return ""

    lines: list[str] = []
    total = 0
    for entry in entries:
        line = f"- [{entry.get('kind', 'observation')}] {entry.get('content', '')}"
        line_bytes = len(line.encode("utf-8"))
        if total + line_bytes > RECALL_BUDGET_BYTES:
            break
        lines.append(line)
        total += line_bytes

    if not lines:
        return ""
    return "[MEMORY]\n" + "\n".join(lines)


def clear_memory(workbench_id: str) -> bool:
    """Clear all memory for a workbench."""
    path = _memory_path(workbench_id)
    try:
        if path.is_file():
            path.unlink()
        return True
    except OSError as exc:
        log.warning(f"Memory clear failed for {workbench_id}: {exc}")
        return False


def _enforce_limit(path: Path) -> None:
    """Keep only the last MAX_ENTRIES lines."""
    try:
        lines = path.read_text(encoding="utf-8").strip().splitlines()
        if len(lines) > MAX_ENTRIES:
            path.write_text(
                "\n".join(lines[-MAX_ENTRIES:]) + "\n",
                encoding="utf-8",
            )
    except OSError:
        pass
