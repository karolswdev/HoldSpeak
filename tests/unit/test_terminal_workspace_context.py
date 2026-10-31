"""Focused proofs for the connected terminal context DTO."""

from __future__ import annotations

import subprocess
from types import SimpleNamespace
from pathlib import Path

import pytest

from holdspeak.db import Database
from holdspeak.delivery.factory_launch import LaunchLedger
from holdspeak.delivery import registry as delivery_registry
from holdspeak.delivery.registry import DeliveryRegistry
from holdspeak.delivery.terminal import TerminalTargetRegistry
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.agent_hand_service import resolve_project_repository
from holdspeak.services.errors import NotFound, ServiceError
from holdspeak.services.project_service import ProjectService
from holdspeak.services.terminal_workspace import TerminalWorkspaceService
from holdspeak.services.terminal_workspace_context import TerminalWorkspaceContext


class Registry:
    def __init__(self) -> None:
        worktree = SimpleNamespace(worktree_id="wt-1", path="/work/HoldSpeak", branch="main")
        self.source = SimpleNamespace(source_id="src-1", label="HoldSpeak", worktrees=[worktree])

    def sources(self):
        return [self.source]

    def get(self, source_id):
        return self.source if source_id == self.source.source_id else None


def _issued(generation: str = "gen-1", target_id: str = "target-1") -> dict[str, str]:
    return {
        "target_id": target_id,
        "target_generation": generation,
        "pane_id": "%5",
    }


def _verify(issued):
    def verify(target_id, generation):
        return {
            "status": "ok",
            "target_id": target_id,
            "target_generation": generation,
            "pane_id": issued["pane_id"],
        }

    return verify


def _context(*, launches, db=None, **kwargs):
    return TerminalWorkspaceContext(
        db=db,
        registry_loader=lambda: Registry(),
        launch_loader=lambda: list(launches),
        **kwargs,
    )


def test_exact_target_binding_projects_program_and_safe_mcp_metadata() -> None:
    launch = {
        "launch_id": "launch-1",
        "profile_id": "codex-default",
        "state": "registered",
        "role": "builder",
        "origin_ref": {"kind": "program_step", "id": "step-1", "credential": "origin-secret"},
        "attempt_id": "attempt-1",
        "source_id": "src-1",
        "worktree_id": "wt-1",
        "target": {**_issued(), "target_generation": "gen-1"},
        "mcp": {"server": "holdspeak", "palette": "CONDUCTOR", "pre_approved": True},
        "read_only": False,
        # This must never cross the terminal wire.
        "credential": "launch-secret",
    }
    context = _context(
        launches=[launch],
        project_id_loader=lambda _db, _kind, _item: "project-1",
        project_loader=lambda _db, project_id: SimpleNamespace(id=project_id, name="Architecture"),
        program_loader=lambda _db, _launch: {
            "id": "program-1", "title": "Build the workspace", "step_id": "step-1", "step_ordinal": 2
        },
    )

    issued = _issued()
    dto = context.for_terminal(
        snapshot=context.snapshot(), issued=issued, current_path="/not/a/worktree", verify=_verify(issued)
    )

    assert dto["status"] == "bound"
    assert dto["project"] == {"id": "project-1", "name": "Architecture"}
    assert dto["source"] == {"id": "src-1", "name": "HoldSpeak"}
    assert dto["worktree"] == {"id": "wt-1", "branch": "main"}
    assert dto["launch"] == {
        "id": "launch-1", "profile_id": "codex-default", "state": "registered", "role": "builder",
        "origin_ref": {"kind": "program_step", "id": "step-1"}, "attempt_id": "attempt-1",
    }
    assert dto["program"] == {
        "id": "program-1", "title": "Build the workspace", "step_id": "step-1", "step_ordinal": 2
    }
    assert dto["mcp"] == {
        "status": "configured", "server": "holdspeak", "palette": "CONDUCTOR",
        "pre_approved": True, "read_only": False,
    }
    assert "credential" not in repr(dto)


def test_reused_target_generation_and_session_name_alone_never_bind() -> None:
    launch = {
        "launch_id": "launch-old",
        "session": "same-session",
        "source_id": "src-1",
        "worktree_id": "wt-1",
        "target": {**_issued("gen-old"), "target_generation": "gen-old"},
    }
    context = _context(launches=[launch])
    issued = _issued("gen-new")

    dto = context.for_terminal(
        snapshot=context.snapshot(), issued=issued, current_path="/elsewhere", verify=_verify(issued)
    )

    assert dto["status"] == "unbound"
    assert dto["launch"] is None


def test_duplicate_exact_candidates_refuse_binding() -> None:
    target = _issued()
    launches = [
        {"launch_id": "launch-a", "target": target},
        {"launch_id": "launch-b", "target": target},
    ]
    context = _context(launches=launches)

    dto = context.for_terminal(
        snapshot=context.snapshot(), issued=target, current_path="", verify=_verify(target)
    )

    assert dto["status"] == "unbound"
    assert dto["launch"] is None


def test_target_generation_verification_failure_refuses_binding() -> None:
    launch = {"launch_id": "launch-stale", "target": _issued()}
    context = _context(launches=[launch])

    def generation_mismatch(_target_id, _generation):
        return {"status": "generation_mismatch", "current_generation": "gen-new"}

    dto = context.for_terminal(
        snapshot=context.snapshot(), issued=_issued(), current_path="", verify=generation_mismatch
    )

    assert dto["status"] == "unbound"
    assert dto["launch"] is None


def test_database_failure_degrades_bound_context_instead_of_claiming_unfiled() -> None:
    class BrokenDatabase:
        def _connection(self):
            raise OSError("fixture database unavailable")

    launch = {
        "launch_id": "launch-db-failure",
        "origin_ref": {"kind": "note", "id": "note-1"},
        "target": _issued(),
    }
    context = _context(launches=[launch], db=BrokenDatabase())
    issued = _issued()

    dto = context.for_terminal(
        snapshot=context.snapshot(), issued=issued, current_path="", verify=_verify(issued)
    )

    assert dto["status"] == "unavailable"
    assert dto["project"] is None
    assert dto["launch"] is None


def test_registered_contained_worktree_is_not_a_fake_project_or_launch() -> None:
    context = _context(launches=[])
    dto = context.for_terminal(
        snapshot=context.snapshot(),
        issued=_issued(),
        current_path="/work/HoldSpeak/web/src",
        verify=_verify(_issued()),
    )

    assert dto["status"] == "worktree"
    assert dto["source"] == {"id": "src-1", "name": "HoldSpeak"}
    assert dto["worktree"] == {"id": "wt-1", "branch": "main"}
    assert dto["project"] is None
    assert dto["launch"] is None
    assert dto["program"] is None
    assert dto["mcp"] is None


def test_unknown_mcp_metadata_is_not_reported_as_a_handshake() -> None:
    launch = {
        "launch_id": "launch-unknown-mcp",
        "target": _issued(),
        "source_id": "src-1",
        "worktree_id": "wt-1",
    }
    context = _context(launches=[launch])
    issued = _issued()
    dto = context.for_terminal(
        snapshot=context.snapshot(), issued=issued, current_path="", verify=_verify(issued)
    )

    assert dto["status"] == "bound"
    assert dto["mcp"] == {
        "status": "unknown", "server": None, "palette": None,
        "pre_approved": None, "read_only": None,
    }


def test_degraded_context_is_typed_and_does_not_require_a_pane_failure() -> None:
    context = TerminalWorkspaceContext(
        registry_loader=lambda: (_ for _ in ()).throw(RuntimeError("registry unreadable")),
        launch_loader=lambda: [],
    )
    issued = _issued()
    dto = context.for_terminal(
        snapshot=context.snapshot(), issued=issued, current_path="/work/HoldSpeak", verify=_verify(issued)
    )

    assert dto == {
        "status": "unavailable", "project": None, "source": None, "worktree": None,
        "launch": None, "program": None, "mcp": None,
    }


def test_default_paths_are_resolved_from_delivery_modules_at_construction(monkeypatch, tmp_path) -> None:
    from holdspeak.delivery import factory_launch, registry as delivery_registry

    registry_path = tmp_path / "sources.json"
    launches_path = tmp_path / "launches.json"
    monkeypatch.setattr(delivery_registry, "DEFAULT_REGISTRY_PATH", registry_path)
    monkeypatch.setattr(factory_launch, "DEFAULT_LAUNCHES_PATH", launches_path)

    context = TerminalWorkspaceContext()

    assert context.registry_path == registry_path
    assert context.launches_path == launches_path


def _private_repo(path: Path) -> Path:
    path.mkdir()
    def git(*args: str) -> None:
        subprocess.run(["git", "-C", str(path), *args], check=True, capture_output=True, text=True)

    git("init")
    git("config", "user.email", "fixture@example.test")
    git("config", "user.name", "Fixture")
    (path / "README.md").write_text("fixture\n", encoding="utf-8")
    git("add", "-A")
    git("commit", "-m", "fixture")
    return path


def test_real_producers_project_note_attempt_registry_and_ledger_bind(tmp_path) -> None:
    repo = _private_repo(tmp_path / "private-repo")
    registry_path = tmp_path / "delivery_sources.json"
    launches_path = tmp_path / "agent_launches.json"
    registry = DeliveryRegistry(registry_path, map_path=tmp_path / "absent-map.json")
    source, worktree = registry.register(str(repo), label="Private fixture")

    db = Database(tmp_path / "hub.db")
    db.projects.create_project(project_id="project-1", name="Connected workspace")
    db.notes.upsert(note_id="note-1", title="Launch origin", body_markdown="fixture")
    db.project_relationships.upsert(project_id="project-1", resource_ref="note:note-1")

    def resolve(_ref, runner=None):
        return {"status": "ok", "pane_id": "%7", "fingerprint": "sha256:fixture"}

    targets = TerminalTargetRegistry(resolver=resolve)
    issued = targets.issue("pane:%7")
    assert issued["status"] == "issued"
    attempt = db.work_attempts.create(
        source_id=source.source_id,
        worktree_id=worktree.worktree_id,
        project="project-1",
        story_id="note-1",
        kind="launch",
        exact=True,
        node_id="local",
        session_id="agent-session",
        target_id=issued["target_id"],
        state="working",
        origin_ref="note:note-1",
    )
    LaunchLedger(launches_path).record(
        {
            "launch_id": "launch-1",
            "profile_id": "codex-default",
            "state": "registered",
            "role": "builder",
            "origin_ref": {"kind": "note", "id": "note-1"},
            "attempt_id": attempt.attempt_id,
            "source_id": source.source_id,
            "worktree_id": worktree.worktree_id,
            "target": issued,
            "mcp": {"server": "holdspeak", "palette": "CONDUCTOR", "pre_approved": False},
            "read_only": True,
        }
    )
    context = TerminalWorkspaceContext(
        db,
        registry_path=registry_path,
        launches_path=launches_path,
    )
    service = TerminalWorkspaceService(
        targets,
        pane_loader=lambda: {
            "status": "ok",
            "panes": [{
                "pane_id": "%7", "session": "fixture", "window": "0", "pane_index": "0",
                "command": "bash", "current_path": str(repo),
            }],
        },
        session_loader=lambda: [],
        context=context,
    )

    result = service.discover()
    dto = result["sessions"][0]["context"]
    assert dto["status"] == "bound"
    assert dto["project"] == {"id": "project-1", "name": "Connected workspace"}
    assert dto["source"] == {"id": source.source_id, "name": "Private fixture"}
    assert dto["worktree"] == {"id": worktree.worktree_id, "branch": worktree.branch}
    assert dto["launch"]["id"] == "launch-1"
    assert dto["launch"]["attempt_id"] == attempt.attempt_id
    assert dto["mcp"] == {
        "status": "configured", "server": "holdspeak", "palette": "CONDUCTOR",
        "pre_approved": False, "read_only": True,
    }
    assert str(repo) not in repr(dto)
    db.close()


def test_owner_files_registered_source_and_hand_resolves_exact_filed_source(tmp_path, monkeypatch) -> None:
    repo = _private_repo(tmp_path / "private-repo")
    registry_path = tmp_path / "delivery_sources.json"
    registry = DeliveryRegistry(registry_path, map_path=tmp_path / "absent-map.json")
    source, _worktree = registry.register(str(repo), label="A label that is not the Project name")
    monkeypatch.setattr(delivery_registry, "DEFAULT_REGISTRY_PATH", registry_path)

    db = Database(tmp_path / "hub.db")
    owner = Principal(PrincipalKind.OWNER, "owner")
    project = ProjectService(db).create_project(owner, name="Architecture")
    service = ProjectService(db)

    filed = service.add_resource(owner, project["id"], f"repository:{source.source_id}")
    resolved = resolve_project_repository(
        db, project["id"], DeliveryRegistry.read_only_snapshot(registry_path)
    )

    assert filed["resource_ref"] == f"repository:{source.source_id}"
    assert resolved is not None
    assert resolved.source_id == source.source_id
    assert resolved.primary_path == str(repo.resolve())
    db.close()


def test_repository_binding_rejects_unknown_source_and_non_owner_principals(tmp_path, monkeypatch) -> None:
    repo = _private_repo(tmp_path / "private-repo")
    registry_path = tmp_path / "delivery_sources.json"
    registry = DeliveryRegistry(registry_path, map_path=tmp_path / "absent-map.json")
    source, _worktree = registry.register(str(repo), label="Fixture")
    monkeypatch.setattr(delivery_registry, "DEFAULT_REGISTRY_PATH", registry_path)

    db = Database(tmp_path / "hub.db")
    owner = Principal(PrincipalKind.OWNER, "owner")
    project = ProjectService(db).create_project(owner, name="Architecture")
    service = ProjectService(db)

    with pytest.raises(NotFound, match="delivery source"):
        service.add_resource(owner, project["id"], "repository:src_missing")

    for principal in (
        Principal(PrincipalKind.AGENT, "agent:launch:L1"),
        Principal(PrincipalKind.AGENT, "launch:L1"),
    ):
        with pytest.raises(ServiceError) as refusal:
            service.add_resource(principal, project["id"], f"repository:{source.source_id}")
        assert refusal.value.code == "owner_required"
        assert refusal.value.context["status"] == 403
    db.close()


def test_repository_binding_does_not_change_note_resource_behavior(tmp_path, monkeypatch) -> None:
    registry_path = tmp_path / "delivery_sources.json"
    monkeypatch.setattr(delivery_registry, "DEFAULT_REGISTRY_PATH", registry_path)
    db = Database(tmp_path / "hub.db")
    owner = Principal(PrincipalKind.OWNER, "owner")
    project = ProjectService(db).create_project(owner, name="Notes")
    db.notes.upsert(note_id="note-1", title="Origin", body_markdown="Keep this filing path")

    filed = ProjectService(db).add_resource(owner, project["id"], "note:note-1")

    assert filed["resource_ref"] == "note:note-1"
    db.close()
