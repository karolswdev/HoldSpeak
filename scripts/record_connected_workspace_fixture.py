#!/usr/bin/env python3
"""Record connected workspace answers from isolated real domain producers.

The tmux edge is the existing deterministic fixture producer. Git, registry,
launch ledger, hub DB, Project/Program/Note producers and repository HTTP are
real and private. No agent CLI, provider, owner state or remote Git is used.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from holdspeak.db import Database
from holdspeak.delivery import DeliveryRegistry
from holdspeak.delivery.factory_launch import LaunchLedger
from holdspeak.delivery.terminal import TerminalTargetRegistry
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.program_service import ProgramService
from holdspeak.services.project_service import ProjectService
from holdspeak.services.agent_hand_queue import HandQueue, queued_flights
from holdspeak.services.terminal_workspace import TerminalWorkspaceService
from holdspeak.services.terminal_workspace_context import TerminalWorkspaceContext
from holdspeak.web.context import WebContext
from holdspeak.web.routes.repositories import build_repositories_router
from scripts.record_terminal_workspace_fixture import FixtureTmux

OWNER = Principal(PrincipalKind.OWNER, "connected-fixture")
PROJECT = "proj-000000000001"
LOCAL_PROJECT = "proj-000000000002"
NOTE = "note-connected-brief"
DECISION = "decision-connected-workspace"
LAUNCH = "launch-connected-fixture"


def git(root: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-C", str(root), *args], check=True, capture_output=True, text=True
    )


def seed_connected_records(
    db, registry, ledger, source, worktree, target, repo_root, *, session="review"
) -> dict:
    """Seed the same connected producer graph for fixture and real-shell walk."""
    db.projects.create_project(project_id=PROJECT, name="Workspace fixture")
    db.projects.create_project(project_id=LOCAL_PROJECT, name="Local workspace")
    db.notes.upsert(
        note_id=NOTE,
        title="Build the connected workspace",
        body_markdown="Keep the file, context and review beside the agent.",
    )
    projects = ProjectService(db)
    projects.add_resource(OWNER, PROJECT, f"note:{NOTE}")
    projects.add_resource(OWNER, PROJECT, f"repository:{source.source_id}")
    db.desk_decisions.upsert(
        decision_id=DECISION,
        title="Keep one Desk",
        status="accepted",
        decision_markdown="Use the existing windows and worktree records.",
    )
    projects.add_resource(OWNER, PROJECT, f"desk_decision:{DECISION}")
    queue = HandQueue(Path(repo_root).parent / "workspace-queue.json")
    queued_entry = queue.add("note", NOTE, profile="codex-default", project_id=PROJECT)
    queued = {"entry": queued_entry, "flights": queued_flights(db, queue)}
    queue.remove(queued_entry["queue_id"])

    programs = ProgramService(
        db, profiles=lambda: ["claude-default", "codex-default", "pi-default"]
    )
    made = programs.create(
        OWNER,
        title="Connected workspace",
        repository=str(repo_root),
        project_id=PROJECT,
        default_profile="codex-default",
        check_command="true",
        control="normal",
    )
    planned = programs.plan(
        OWNER,
        made["id"],
        steps=[
            {
                "title": "Build the workspace",
                "brief": "Keep the work connected.",
                "owns": ["app.txt"],
                "gate_review": "none",
            }
        ],
    )
    step = programs.store.get_step(planned["steps"][0]["id"])
    step.update(
        launch_id=LAUNCH,
        state="working",
        worktree=str(worktree.path),
        branch="work/review",
    )
    programs.store.save_step(step)

    attempt = db.work_attempts.create(
        source_id=source.source_id,
        worktree_id=worktree.worktree_id,
        project=PROJECT,
        story_id="note-connected-brief",
        node_id="local",
        session_id="codex:fixture-agent",
        target_id=target["target_id"],
        kind="launch",
        exact=True,
        claimed_by="launch:codex-default",
        state="working",
        origin_ref=f"note:{NOTE}",
    )
    ledger.record(
        {
            "launch_schema": 1,
            "launch_id": LAUNCH,
            "state": "registered",
            "node_id": "local",
            "profile_id": "codex-default",
            "role": "builder",
            "read_only": False,
            "source_id": source.source_id,
            "worktree_id": worktree.worktree_id,
            "story_ref": {"project": PROJECT, "story_id": "note-connected-brief"},
            "origin_ref": {"kind": "note", "id": NOTE},
            "attempt_id": attempt.attempt_id,
            "session": session,
            "target": target,
            "branch": "work/review",
            "instruction_state": "sent",
            "brief_text": "Keep the file, context and review beside the agent.",
            "mcp": {
                "server": "holdspeak",
                "palette": "CONDUCTOR",
                "pre_approved": True,
            },
        }
    )
    return {
        "project_id": PROJECT,
        "registration_project_id": LOCAL_PROJECT,
        "note_id": NOTE,
        "launch_id": LAUNCH,
        "program_id": made["id"],
        "step_id": step["id"],
        "queued": queued,
    }


def record(root: Path) -> dict:
    clone = root / "repository"
    clone.mkdir()
    git(clone, "init", "-b", "main")
    git(clone, "config", "user.email", "fixture@example.test")
    git(clone, "config", "user.name", "Workspace fixture")
    (clone / "README.md").write_text("# Workspace fixture\n", encoding="utf-8")
    (clone / "app.txt").write_text("main checkout\n", encoding="utf-8")
    git(clone, "add", "README.md", "app.txt")
    git(clone, "commit", "-m", "Seed workspace")
    work = root / "review"
    scratch = root / "scratch"
    git(clone, "worktree", "add", "-b", "work/review", str(work))
    git(clone, "worktree", "add", "-b", "work/scratch", str(scratch))
    (work / "app.txt").write_text("review worktree\n", encoding="utf-8")
    (scratch / "app.txt").write_text("scratch worktree\n", encoding="utf-8")

    import holdspeak.delivery.registry as registry_module

    registry_module.DEFAULT_REGISTRY_PATH = root / "registry.json"
    registry = DeliveryRegistry(
        root / "registry.json", map_path=root / "no-project-map.json"
    )
    source, _ = registry.register(str(clone), label="Workspace fixture")
    _, worktree = registry.register(str(work))
    registry.register(str(scratch))
    db = Database(root / "hub.db")
    tmux = FixtureTmux()
    tmux.panes[0]["current_path"] = str(work)
    tmux.panes[1]["current_path"] = str(scratch)
    targets = TerminalTargetRegistry(runner=tmux)
    target = targets.issue("pane:%5")
    ledger = LaunchLedger(root / "launches.json")
    seeded = seed_connected_records(
        db, registry, ledger, source, worktree, target, clone
    )
    projects = ProjectService(db)
    programs = ProgramService(db)
    context = TerminalWorkspaceContext(
        db, registry_path=root / "registry.json", launches_path=root / "launches.json"
    )
    inventory = TerminalWorkspaceService(
        targets,
        pane_loader=lambda: {"status": "ok", "panes": tmux.panes},
        session_loader=lambda: [],
        context=context,
    ).discover()
    app = FastAPI()
    app.include_router(
        build_repositories_router(WebContext(get_state=lambda: {}), registry=registry)
    )
    with TestClient(app) as client:
        base = f"/api/repositories/{source.source_id}"
        scope = {"worktree_id": worktree.worktree_id}
        repository = {}
        for name, suffix, extra in (
            ("tree", "/tree", {}),
            ("file", "/file/app.txt", {}),
            ("status", "/status", {}),
            ("diff", "/diff", {"path": "app.txt"}),
            ("staged_diff", "/diff", {"staged": "true"}),
        ):
            response = client.get(base + suffix, params={**scope, **extra})
            response.raise_for_status()
            repository[name] = response.json()
        (work / "app.txt").write_text("agent changed after open\n", encoding="utf-8")
        conflict = client.put(base + "/file/app.txt", json={
            "content": "owner draft kept\n", "expected_sha256": repository["file"]["sha256"],
            "worktree_id": worktree.worktree_id,
        })
        assert conflict.status_code == 409
        repository["conflict"] = {"status": conflict.status_code, "body": conflict.json()}
        latest = client.get(base + "/file/app.txt", params=scope)
        latest.raise_for_status()
        repository["file_latest"] = latest.json()
        reviewed = client.put(base + "/file/app.txt", json={
            "content": "owner reviewed change\n", "expected_sha256": latest.json()["sha256"],
            "worktree_id": worktree.worktree_id,
        })
        reviewed.raise_for_status()
        repository["save_reviewed"] = reviewed.json()
    return {
        "provenance": {
            "producer": "TerminalWorkspaceService + TerminalWorkspaceContext + repository HTTP",
            "engine_mode": "none",
            "tmux": "injected fixture edge",
            "git": "private real worktrees",
        },
        "inventory": inventory,
        "repository": repository,
        "projects": {"projects": projects.list_projects(OWNER)},
        "resources": {"resources": projects.list_resources(OWNER, PROJECT)},
        "note": {"note": db.notes.get(NOTE).to_dict()},
        "notes": {note.id: {"note": note.to_dict()} for note in db.notes.list()},
        "decisions": {"decisions": [db.desk_decisions.get(DECISION).to_dict()]},
        "program": programs.get(OWNER, seeded["program_id"]),
        "queued": seeded["queued"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "web/src/desk/terminals/__tests__/fixtures/connected.recorded.json"
        ),
    )
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(
        prefix="hs-connected-fixture-", dir="/tmp"
    ) as scratch:
        answer = record(Path(scratch))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(answer, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
