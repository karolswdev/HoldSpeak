"""The Dreaming backlog's third source: the canon (PG-JOURNEYS J2; 2026-11-01).

A night with no "dream" task still has work. By rule, no model, from the
night Program's own repository at the night's start:

1. the desk sweep's known reds (``KNOWN_REDS`` in
   ``tests/e2e/test_desk_sweep.py``, read as Python syntax, never run): one
   item per named red;
2. the UX-canon scanner's findings (``scripts/ux_canon_scan.py --json``, run
   by the engine's process site): one item per finding, file and line.

Each item becomes a Door task (``source_type canon``, ``source_ref
canon:<key>``) the night then takes like any backlog task. At most
``CANON_PER_NIGHT`` (5) a night, inside the Program's ``within`` folders;
an item whose task is still open is never filed again.
"""
from __future__ import annotations

import ast
import hashlib
import json
import sys
import tempfile
from pathlib import Path
from typing import Any, Mapping, Optional

from ..logging_config import get_logger

log = get_logger("program_canon")

CANON_PER_NIGHT = 5
SOURCE_TYPE = "canon"
SWEEP_FILE = "tests/e2e/test_desk_sweep.py"
SCANNER = "scripts/ux_canon_scan.py"
#: The scanner's paths are under web/src.
SCANNER_ROOT = "web/src/"


def key_of(*parts: Any) -> str:
    return hashlib.sha256("|".join(str(part) for part in parts).encode("utf-8")).hexdigest()[:16]


def known_reds(root: Path) -> list[dict[str, str]]:
    """``[{key, task, path}]`` of the sweep's known reds (the AST of the dict)."""
    path = root / SWEEP_FILE
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError, ValueError):
        return []
    out: list[dict[str, str]] = []
    for node in ast.walk(tree):
        target = node.target if isinstance(node, ast.AnnAssign) else (
            node.targets[0] if isinstance(node, ast.Assign) and node.targets else None)
        if not (isinstance(target, ast.Name) and target.id == "KNOWN_REDS" and isinstance(node.value, ast.Dict)):
            continue
        for key, value in zip(node.value.keys, node.value.values):
            try:
                case, width = ast.literal_eval(key) if key is not None else ("", 0)
            except ValueError:
                continue
            for red in value.elts if isinstance(value, ast.List) else []:
                if not (isinstance(red, ast.Call) and len(red.args) >= 3):
                    continue
                try:
                    reason = ast.literal_eval(red.args[2])
                except ValueError:
                    continue
                reason = " ".join(str(reason).split())
                out.append({"key": key_of("sweep", case, width, reason),
                            "task": f"Fix the desk sweep's known red ({case} at {width}): {reason}"[:300],
                            "path": "web/src/desk/"})  # the fix is in a face; the list is the sweep's
    return out


def scanner_findings(runner: Any, root: Path) -> list[dict[str, str]]:
    """``[{key, task, path}]`` of the UX-canon scanner's findings, the faces
    with the most findings first."""
    if not (root / SCANNER).exists():
        return []
    with tempfile.TemporaryDirectory(prefix="hs-canon-") as scratch:
        out_file = Path(scratch) / "violations.json"
        try:
            proc = runner._run([sys.executable, SCANNER, "--root", str(root), "--json", str(out_file)], cwd=str(root))
            data = json.loads(out_file.read_text(encoding="utf-8")) if proc.returncode == 0 else {}
        except Exception as exc:
            log.info(f"the canon scanner did not run: {exc}")
            return []
    faces = data.get("faces") if isinstance(data, dict) else None
    if not isinstance(faces, dict):
        return []
    out: list[dict[str, str]] = []
    for _face, rows in sorted(faces.items(), key=lambda pair: (-len(pair[1] or []), pair[0])):
        for row in rows or []:
            file = str(row.get("file") or "")
            text = " ".join(str(row.get("text") or "").split())
            rule = str(row.get("rule") or "")
            path = SCANNER_ROOT + file
            out.append({"key": key_of("canon", file, rule, text),
                        "task": f"Fix the UX-canon finding ({rule}) in {path}:{row.get('line')}: {text}"[:300],
                        "path": path})
    return out


def _within(path: str, within: list[str]) -> bool:
    return not within or any(path.startswith(str(bound).strip().rstrip("/") + "/") or path == bound for bound in within)


def _open_keys(db: Any) -> set[str]:
    try:
        rows = db.meetings.list_action_items(include_completed=False)
    except Exception:
        return set()
    return {str(getattr(row, "source_ref", "") or "")[len("canon:"):] for row in rows
            if str(getattr(row, "source_type", "") or "") == SOURCE_TYPE}


def file_items(runner: Any, program: Mapping[str, Any], *, limit: int = CANON_PER_NIGHT) -> list[dict[str, str]]:
    """File up to ``limit`` canon items as Door tasks; ``[{kind, id, task}]``
    in the backlog's shape."""
    from ..principals import Principal, PrincipalKind
    from .door_service import DoorService
    from .follow_through_service import FollowThroughService

    root = Path(str(program.get("repo_root") or ""))
    if limit <= 0 or not root.is_dir():
        return []
    within = list(program.get("within") or [])
    service = runner.service
    seen = _open_keys(service.db)
    picked: list[dict[str, str]] = []
    for item in [*known_reds(root), *scanner_findings(runner, root)]:
        if len(picked) >= min(limit, CANON_PER_NIGHT):
            break
        if item["key"] in seen or not _within(item["path"], within):
            continue
        seen.add(item["key"])
        picked.append(item)
    out = []
    door = DoorService(FollowThroughService(service.db), None, None, None, db=service.db)  # type: ignore[arg-type]
    for item in picked:
        try:
            made = door.add_item(Principal(PrincipalKind.OWNER, "program-engine"), item["task"], owner="me",
                                 source_type=SOURCE_TYPE, source_ref=f"canon:{item['key']}")
        except Exception as exc:
            log.info(f"canon item not filed: {exc}")
            continue
        out.append({"kind": "action", "id": str(made.get("id")), "task": item["task"]})
    return out


__all__ = ["CANON_PER_NIGHT", "SOURCE_TYPE", "file_items", "known_reds", "scanner_findings"]
