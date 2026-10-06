"""Hand to agent: one item in, one coding agent working on it out.

docs/internal/CONDUCTOR.md, steps 2 to 4. The verb joins parts that exist:

1. the item's Project and its repository, registered as a Delivery Source
   when it is not one yet (``no_repository`` by name otherwise);
2. the brief (``services.agent_brief.compose_agent_brief``);
3. a new git worktree ``hs-<kind>-<id>`` on branch ``hs/<kind>-<id>``,
   through the launch engine's own ``worktree.create`` envelope;
4. the launch, with ``origin_ref`` on the launch record and the Work
   attempt, and a story ref derived from the item when no dw story exists.

Claude Code launches through ``process.spawn``: the owner's press on the
verb is the consent, so the tool gate is armed for exactly the new
worktree path (audited) and the brief is the first ``process.input``.
Codex is not gated today (``process.spawn`` takes Claude only), so it
launches on the ungated path and the brief is typed as its first input
through ``process.input``. The Control-mode tool-gate mapping is lane K5;
this module keeps today's gate decisions (Bash calls wait for a human).
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Callable, Mapping, Optional

from ..delivery.factory_launch import (
    LaunchRefused,
    derive_worktree_path,
    derived_story_ref,
)
from ..delivery.registry import RegistryError, normalize_git_url
from ..logging_config import get_logger
from .agent_brief import (
    AgentBriefRefused,
    compose_agent_brief,
    parse_item_ref,
    project_for_item,
)

log = get_logger("agent_hand")

DEFAULT_PROFILE_ID = "claude-default"
#: The story-ref project token for an item that belongs to no Project.
DESK_PROJECT = "desk"

_NAME_UNSAFE = re.compile(r"[^A-Za-z0-9_.-]+")


class AgentHandRefused(ValueError):
    """A typed refusal; ``reason`` is machine-readable, the message is
    path-free."""

    def __init__(self, reason: str, message: Optional[str] = None) -> None:
        super().__init__(message or reason)
        self.reason = reason


def worktree_spec(kind: str, item_id: str) -> dict[str, str]:
    """``{mode: new, name: hs-<kind>-<id>, branch: hs/<kind>-<id>}``."""
    slug = _NAME_UNSAFE.sub("-", f"{kind}-{item_id}").strip("-.")[:60]
    return {"mode": "new", "name": f"hs-{slug}", "branch": f"hs/{slug}"}


def _matches_repo(registry: Any, path: str, repositories: list[str]) -> bool:
    """The clone at ``path`` has a GitHub ``owner/repo`` origin. Read
    through the registry's own git runner (the one git read it already
    makes for a fingerprint)."""
    origin = normalize_git_url(
        registry._git(Path(path), "config", "--get", "remote.origin.url") or ""
    ).lower()
    return bool(origin) and any(
        origin.endswith("/" + repo.strip("/").lower()) for repo in repositories if repo
    )


def resolve_project_repository(
    db: Any,
    project_id: Optional[str],
    registry: Any,
    *,
    project_map: Optional[Mapping[str, Any]] = None,
) -> Any:
    """The Delivery Source of a Project's repository, registered if absent.

    In order: a repository filed in the Project (``repository:<source_id>``);
    the GitHub repositories the Project's Room watches, matched by origin
    against the registered sources and then against the project map; a
    project-map entry named like the Project. ``None`` when nothing names a
    local clone."""
    if not project_id:
        return None
    with db._connection() as conn:
        filed = [
            str(row[0]).split(":", 1)[1]
            for row in conn.execute(
                "SELECT resource_ref FROM project_resources WHERE project_id=? "
                "AND deleted=0 AND resource_ref LIKE 'repository:%'",
                (project_id,),
            )
        ]
        repositories: list[str] = []
        for row in conn.execute(
            "SELECT query_json FROM connector_watches WHERE project_id=? "
            "AND connector_id IN ('gh','github')",
            (project_id,),
        ):
            try:
                repo = (json.loads(row[0] or "{}") or {}).get("repository")
            except ValueError:
                repo = None
            if repo and str(repo) not in repositories:
                repositories.append(str(repo))
        name_row = conn.execute("SELECT name FROM projects WHERE id=?", (project_id,)).fetchone()
    project_name = str(name_row[0]) if name_row else ""

    for source_id in filed:
        source = registry.get(source_id)
        if source is not None and source.primary_path:
            return source
    if repositories:
        for source in registry.sources():
            if source.primary_path and _matches_repo(registry, source.primary_path, repositories):
                return source
    if project_map is None:
        from ..missioncontrol_bridge import load_project_map

        project_map = load_project_map()
    entries = dict((project_map or {}).get("projects") or {})
    for name, path in sorted(entries.items()):
        named = project_name and name.strip().lower() == project_name.strip().lower()
        if named or (repositories and _matches_repo(registry, path, repositories)):
            try:
                source, _ = registry.register(path, label=name)
            except RegistryError:
                continue
            return source
    return None


class AgentHandService:
    """The Hand to agent verb, transport-neutral (route, MCP, Thread)."""

    def __init__(
        self,
        db: Any,
        *,
        launch_service: Callable[[], Any],
        control_mode: Optional[Callable[[], str]] = None,
        gate_path: Optional[Path] = None,
        project_map: Optional[Mapping[str, Any]] = None,
    ) -> None:
        self._db = db
        self._launch_service = launch_service
        self._control_mode = control_mode or _config_control_mode
        self._gate_path = gate_path
        self._project_map = project_map

    def hand(
        self,
        principal: Any,
        kind: str,
        item_id: str,
        *,
        instruction: Optional[str] = None,
        profile: Optional[str] = None,
        project_id: Optional[str] = None,
    ) -> dict[str, Any]:
        try:
            kind, item_id = parse_item_ref({"kind": kind, "id": item_id})
        except AgentBriefRefused as exc:
            raise AgentHandRefused(exc.reason, str(exc)) from exc
        launcher = self._launch_service()
        profile_id = str(profile or DEFAULT_PROFILE_ID)
        agent = launcher._profiles.get(profile_id)
        if agent is None:
            raise AgentHandRefused("profile_unknown", f"unknown agent profile {profile_id!r}")
        try:
            launcher._preflight(agent)
        except LaunchRefused as exc:
            raise AgentHandRefused(exc.reason, str(exc)) from exc

        project_id = project_id or project_for_item(self._db, kind, item_id)
        source = resolve_project_repository(
            self._db, project_id, launcher._registry, project_map=self._project_map
        )
        if source is None:
            raise AgentHandRefused(
                "no_repository", "the item's Project names no local repository"
            )
        spec = worktree_spec(kind, item_id)
        try:
            worktree_path = derive_worktree_path(source.primary_path, spec["name"])
        except LaunchRefused as exc:
            raise AgentHandRefused(exc.reason, str(exc)) from exc
        if worktree_path.exists():
            raise AgentHandRefused(
                "worktree_duplicate", f"worktree {spec['name']!r} already exists"
            )

        mode = self._control_mode()
        try:
            brief = compose_agent_brief(
                self._db,
                {"kind": kind, "id": item_id},
                project_id=project_id,
                instruction=instruction,
                control_mode=mode,
                repo_path=source.primary_path,
            )
        except AgentBriefRefused as exc:
            raise AgentHandRefused(exc.reason, str(exc)) from exc

        try:
            story_ref = derived_story_ref(project_id or DESK_PROJECT, kind, item_id)
        except LaunchRefused as exc:
            raise AgentHandRefused(exc.reason, str(exc)) from exc
        request = {
            "agent_profile_id": profile_id,
            "source_id": source.source_id,
            "worktree": spec,
            "story_ref": story_ref,
            "origin_ref": {"kind": kind, "id": item_id},
        }
        if agent.get("executable") == "claude":
            result = self._launch_gated(launcher, request, brief["text"], principal, worktree_path, spec["name"])
        else:
            result = self._launch_ungated(launcher, request, brief["text"], principal)
        launch = result.get("launch") or {}
        return {
            "status": "launched" if launch.get("state") == "launched" else "failed",
            "instruction_state": launch.get("instruction_state")
            or ("sent" if (launch.get("commands") or {}).get("instruction") else None),
            "launch_id": launch.get("launch_id"),
            "attempt_id": launch.get("attempt_id"),
            "operation_id": result.get("operation_id"),
            "state": launch.get("state"),
            "failure": launch.get("failure"),
            "gate": launch.get("gate"),
            "session": launch.get("session"),
            "worktree": {"name": spec["name"], "branch": spec["branch"]},
            "source_id": source.source_id,
            "story_ref": story_ref,
            "origin_ref": {"kind": kind, "id": item_id},
            "project_id": project_id,
            "control_mode": mode,
            "brief": {
                "bytes": brief["bytes"],
                "refs": brief["refs"],
                "people_cut": brief["people_cut"],
            },
        }

    def hand_item(
        self,
        principal: Any,
        *,
        kind: str,
        id: str,  # noqa: A002 - the declared argument name (agent.hand)
        instruction: Optional[str] = None,
        profile: Optional[str] = None,
        project_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """The ``agent.hand`` operation (``agent_operations.AGENT_HAND``)."""
        return self.hand(
            principal, kind, id,
            instruction=instruction, profile=profile, project_id=project_id,
        )

    # ── Claude: process.spawn, the gate armed for this worktree ──────

    def _launch_gated(
        self, launcher: Any, request: dict[str, Any], text: str, principal: Any,
        worktree_path: Path, name: str,
    ) -> dict[str, Any]:
        armed = self._arm_gate(worktree_path, name)
        try:
            # The brief is typed once the rider registers the session, so a
            # folder-trust dialog or a slow start cannot eat it.
            return launcher.submit_process_spawn(
                request, text, principal, after_registration=True
            )
        except LaunchRefused as exc:
            if armed and not worktree_path.exists():
                self._disarm_gate(worktree_path, name)  # nothing launched there
            raise AgentHandRefused(exc.reason, str(exc)) from exc

    def _arm_gate(self, worktree_path: Path, name: str) -> bool:
        """Hold Bash for exactly the new worktree path; the press on the
        verb is the consent. Audited. Returns whether this call added it."""
        from .. import coder_gate

        config = coder_gate.load_gate_config(self._gate_path)
        key = str(worktree_path)
        added = key not in config.repos
        config.repos[key] = list(coder_gate.DEFAULT_TOOLS)
        # Armed on its own: the master switch is not touched, so no other
        # listed repo becomes held.
        if key not in config.armed_paths:
            config.armed_paths.append(key)
        coder_gate.save_gate_config(config, self._gate_path)
        self._audit(name, outcome="gate_armed", detail=f"hold Bash for worktree {name} only")
        return added

    def _disarm_gate(self, worktree_path: Path, name: str) -> None:
        from .. import coder_gate

        config = coder_gate.load_gate_config(self._gate_path)
        key = str(worktree_path)
        config.armed_paths = [path for path in config.armed_paths if path != key]
        if config.repos.pop(key, None) is not None:
            coder_gate.save_gate_config(config, self._gate_path)
            self._audit(name, outcome="gate_released", detail="the launch refused before it ran")

    def _audit(self, name: str, *, outcome: str, detail: str) -> None:
        try:
            self._db.steering.record(
                session_key=f"factory:gate:{name}", agent="factory", pane_id=None,
                text=f"gate {name}", grounding=[], submit=False,
                outcome=outcome, detail=detail,
            )
        except Exception as exc:  # the audit row never blocks the launch
            log.warning("gate audit not written (%s)", exc)

    # ── Codex: the ungated launch, the brief typed as first input ────

    def _launch_ungated(
        self, launcher: Any, request: dict[str, Any], text: str, principal: Any,
    ) -> dict[str, Any]:
        from .. import coder_steering

        try:
            record = launcher.launch(request)
        except LaunchRefused as exc:
            raise AgentHandRefused(exc.reason, str(exc)) from exc
        if record.get("state") != "launched":
            return {"launch": record}
        target = record.get("target") or {}
        armed = coder_steering.arm(
            str(record.get("session") or ""), str(target.get("pane_id") or ""),
            runner=launcher._runner,
        )
        if armed.get("status") != "armed":
            raise AgentHandRefused(str(armed.get("status") or "arm_refused"), "the agent pane could not be armed")
        sent = launcher._commands.submit_process_input(
            {
                "node_id": str(record.get("node_id") or "local"),
                "target_id": target.get("target_id"),
                "target_generation": target.get("target_generation"),
                "operation": {"family": "coder_steering", "verb": "terminal.text"},
                "payload": {
                    "text": text,
                    "submit": True,
                    "session_key": record.get("session"),
                    "agent": str(request.get("agent_profile_id") or "agent"),
                },
            },
            principal,
        )
        commands = dict(record.get("commands") or {})
        commands["instruction"] = sent.get("command_id")
        record = launcher._ledger.update(record["launch_id"], commands=commands) or record
        return {"launch": record, "operation_id": sent.get("operation_id")}


def _config_control_mode() -> str:
    from ..config import Config

    try:
        return str(Config.load().control_mode or "yolo")
    except Exception:
        return "yolo"


__all__ = [
    "AgentHandRefused",
    "AgentHandService",
    "DEFAULT_PROFILE_ID",
    "default_agent_hand_service",
    "resolve_project_repository",
    "worktree_spec",
]


def default_agent_hand_service(db: Any = None, *, delivery_service: Any = None) -> AgentHandService:
    """The production composition: the process database and the one
    shared launch driver (``DeliveryService.default_launch_service``)."""
    if db is None:
        from ..db import get_database

        db = get_database()
    if delivery_service is None:
        from .delivery_service import DeliveryService

        delivery_service = DeliveryService(db)
    return AgentHandService(db, launch_service=delivery_service.default_launch_service)
