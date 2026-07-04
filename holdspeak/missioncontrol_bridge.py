"""The mission-control bridge core (HS-82-02).

The Desk island reads only same-origin ``/api/*`` routes, and the
Delivery Workbench contract (their ``docs/mission-control.md`` §5)
allows a client exactly three documents, via the dw CLI, no
scraping. This module is the whole gap: shell to the CLI of each
rails repo the operator's project map names, verify the schema at
the door, and relay the documents byte-honest — never reshaped,
never annotated.

Design: docs/MISSION_CONTROL_DESK.md §1. The runner is injectable
(the connector-runtime precedent) so tests never touch a real CLI;
schema drift and dead CLIs become typed statuses the UI renders
honestly instead of empty belts.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any, Callable, Optional

# The schema versions this client is proven against (declared per
# the counterpart's §5; drift is a compatibility note, not a break).
FEED_SCHEMA_PROVEN = 1
SESSIONS_SCHEMA_PROVEN = 1

DW_TIMEOUT_SECONDS = 30
DEFAULT_MAP_PATH = Path.home() / ".holdspeak" / "delivery_workbench.json"

Runner = Callable[..., "subprocess.CompletedProcess[str]"]


def _default_runner(argv: list[str], cwd: Optional[str] = None):
    return subprocess.run(
        argv,
        cwd=cwd,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        errors="replace",
        timeout=DW_TIMEOUT_SECONDS,
    )


def load_project_map(path: Optional[Path] = None) -> dict[str, Any]:
    """The operator's rails-repo map — the same file the Phase-12
    actuator pack reads. ``{"projects": {name: path}, "default": path}``;
    missing or unreadable yields an empty map, never an exception."""
    map_path = path or DEFAULT_MAP_PATH
    try:
        raw = json.loads(map_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, ValueError):
        return {"projects": {}, "default": None}
    if not isinstance(raw, dict):
        return {"projects": {}, "default": None}
    projects: dict[str, str] = {}
    raw_projects = raw.get("projects")
    if isinstance(raw_projects, dict):
        for name, repo in raw_projects.items():
            repo_text = str(repo or "").strip()
            if repo_text and Path(repo_text).is_dir():
                projects[str(name)] = repo_text
    default = str(raw.get("default") or "").strip() or None
    if default and not Path(default).is_dir():
        default = None
    if default is None and projects:
        default = sorted(projects.values())[0]
    return {"projects": projects, "default": default}


def dw_argv_base(repo: Path) -> Optional[list[str]]:
    """The repo's own rails first, installed dw second — the
    Phase-12 pack's recorded decision, unchanged."""
    repo_dw = repo / ".githooks" / "dw"
    if repo_dw.is_file() and os.access(repo_dw, os.X_OK):
        return [str(repo_dw)]
    path_dw = shutil.which("dw")
    if path_dw:
        return [path_dw, "--root", str(repo)]
    return None


def _fetch_document(
    repo: Path, argv_tail: list[str], runner: Optional[Runner]
) -> tuple[Optional[Any], str, str]:
    """(document, status, detail): status is live | unavailable."""
    run = runner or _default_runner
    base = dw_argv_base(repo)
    if base is None:
        return None, "unavailable", f"no dw CLI for {repo}"
    try:
        proc = run([*base, *argv_tail], str(repo))
    except (OSError, subprocess.TimeoutExpired) as exc:
        return None, "unavailable", f"dw failed to run: {exc}"
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "").strip().splitlines()
        tail = detail[-1] if detail else "unknown dw error"
        return None, "unavailable", f"dw exited {proc.returncode}: {tail[:300]}"
    try:
        return json.loads(proc.stdout), "live", ""
    except (json.JSONDecodeError, ValueError):
        return None, "unavailable", "dw did not return JSON"


def state_entry(
    name: str, repo_path: str, runner: Optional[Runner] = None
) -> dict[str, Any]:
    """One repo's feed, schema-checked at the door, relayed untouched."""
    doc, status, detail = _fetch_document(
        Path(repo_path), ["state", "--json"], runner
    )
    entry: dict[str, Any] = {"name": name, "path": repo_path}
    if doc is None:
        return {**entry, "status": status, "detail": detail}
    if not isinstance(doc, dict) or doc.get("feed_schema") != FEED_SCHEMA_PROVEN:
        found = doc.get("feed_schema") if isinstance(doc, dict) else None
        return {
            **entry,
            "status": "compatibility",
            "detail": (
                f"feed_schema {found!r} is not the schema this desk was "
                f"proven against ({FEED_SCHEMA_PROVEN})"
            ),
        }
    return {**entry, "status": "live", "feed": doc}


def state_payload(
    project_map: dict[str, Any], runner: Optional[Runner] = None
) -> dict[str, Any]:
    return {
        "repos": [
            state_entry(name, repo, runner)
            for name, repo in sorted(project_map["projects"].items())
        ]
    }


def sessions_payload(
    project_map: dict[str, Any], runner: Optional[Runner] = None
) -> dict[str, Any]:
    """The correlation document is desk-global; one relay via the
    default repo's CLI."""
    default = project_map.get("default")
    if not default:
        return {"status": "unavailable", "detail": "no rails repo configured"}
    doc, status, detail = _fetch_document(
        Path(default), ["sessions", "--json"], runner
    )
    if doc is None:
        return {"status": status, "detail": detail}
    if (
        not isinstance(doc, dict)
        or doc.get("sessions_schema") != SESSIONS_SCHEMA_PROVEN
    ):
        found = doc.get("sessions_schema") if isinstance(doc, dict) else None
        return {
            "status": "compatibility",
            "detail": (
                f"sessions_schema {found!r} is not the schema this desk "
                f"was proven against ({SESSIONS_SCHEMA_PROVEN})"
            ),
        }
    return {"status": "live", "sessions": doc}


def events_payload(
    project_map: dict[str, Any],
    tail: int = 20,
    runner: Optional[Runner] = None,
) -> dict[str, Any]:
    tail = max(1, min(int(tail), 100))
    repos = []
    for name, repo in sorted(project_map["projects"].items()):
        doc, status, detail = _fetch_document(
            Path(repo), ["events", "--json", "--tail", str(tail)], runner
        )
        entry: dict[str, Any] = {"name": name, "path": repo}
        if doc is None or not isinstance(doc, list):
            repos.append(
                {
                    **entry,
                    "status": "unavailable" if doc is None else "compatibility",
                    "detail": detail or "events document is not a list",
                }
            )
        else:
            repos.append({**entry, "status": "live", "events": doc})
    return {"repos": repos}
