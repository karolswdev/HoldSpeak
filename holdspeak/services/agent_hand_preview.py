"""The launch sheet's preview: what Hand to agent would send, with no launch.

docs/internal/CONDUCTOR.md, the F faces (K3a/K3b): the sheet shows the brief
(its sources, bytes, the People cut, the acceptance checks), the repository,
the new worktree's branch and the Control mode BEFORE the owner presses
Launch. This module composes the same brief the hand composes
(``compose_agent_brief`` with the same inputs) and resolves the same
repository, and writes nothing: no worktree, no gate, no registration, no
launch, no receipt.

A thing that would refuse the launch (no repository, the agent or tmux not
installed, the worktree already there) is named in ``refused`` so the sheet
can show it as a token; the brief still shows. An item the brief cannot
carry refuses the preview itself, by the same names the hand uses.
"""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any, Optional

from ..delivery.factory_launch import LaunchRefused, derive_worktree_path
from ..principals import PrincipalKind
from .agent_brief import AgentBriefRefused, compose_agent_brief, parse_item_ref, project_for_item
from .agent_hand_service import (
    DEFAULT_PROFILE_ID,
    AgentHandRefused,
    AgentHandService,
    _launch_for_origin,
    _reload_registry,
    item_exists,
    resolve_project_repository,
    worktree_spec,
)
from .errors import ServiceError


class _ReadOnlyRegistry:
    """The Delivery registry for a preview: it reads, and it never registers.

    ``resolve_project_repository`` registers a project-map clone the first
    time a hand finds it; the preview names the same clone without the write."""

    def __init__(self, registry: Any) -> None:
        self._registry = registry

    def get(self, source_id: str) -> Any:
        return self._registry.get(source_id)

    def sources(self) -> Any:
        return self._registry.sources()

    def _git(self, *args: Any) -> Any:
        return self._registry._git(*args)

    def register(self, path: str, label: Optional[str] = None) -> tuple[Any, bool]:
        return SimpleNamespace(source_id=None, primary_path=path, label=label or ""), False


def _home_as_tilde(path: Optional[str]) -> Optional[str]:
    """The path as the face shows it: the hub's home folder is ``~``."""
    if not path:
        return None
    for home in dict.fromkeys((str(Path.home()), str(Path.home().resolve()))):
        if path == home or path.startswith(home + "/"):
            return "~" + path[len(home):]
    return path


def preview_hand(
    service: AgentHandService,
    principal: Any,
    kind: str,
    item_id: str,
    *,
    instruction: Optional[str] = None,
    profile: Optional[str] = None,
    project_id: Optional[str] = None,
) -> dict[str, Any]:
    """``{text, refs, bytes, people_cut, sources, acceptance, repo, repo_label, branch,
    worktree, project_id, control_mode, profile, refused}``; owner only; no side effect."""
    if getattr(principal, "kind", None) is not PrincipalKind.OWNER:
        raise ServiceError("owner_required", "Only the owner previews a hand-off.", context={"status": 403})
    try:
        kind, item_id = parse_item_ref({"kind": kind, "id": item_id})
    except AgentBriefRefused as exc:
        raise AgentHandRefused(exc.reason, str(exc)) from exc
    db = service._db
    if not item_exists(db, kind, item_id):
        raise AgentHandRefused("item_unknown", f"{kind}:{item_id} is not on the desk")
    launcher = service._launch_service()
    profile_id = str(profile or DEFAULT_PROFILE_ID)
    agent = launcher._profiles.get(profile_id)
    if agent is None:
        raise AgentHandRefused("profile_unknown", f"unknown agent profile {profile_id!r}")
    refused: list[str] = []
    try:
        launcher._preflight(agent)
    except LaunchRefused as exc:
        refused.append(exc.reason)

    project_id = project_id or project_for_item(db, kind, item_id)
    _reload_registry(launcher._registry)
    source = resolve_project_repository(
        db, project_id, _ReadOnlyRegistry(launcher._registry), project_map=service._project_map
    )
    repo = str(source.primary_path) if source is not None else None
    spec = worktree_spec(kind, item_id)
    if repo is None:
        refused.append("no_repository")
    else:
        try:
            if derive_worktree_path(repo, spec["name"]).exists():
                # The hand resumes a launch whose brief is still held; any
                # other existing worktree refuses it (the hand's own rule).
                held = _launch_for_origin(launcher, kind, item_id)
                if not (held and held.get("instruction_state") != "sent" and isinstance(held.get("pending_brief"), dict)):
                    refused.append("worktree_duplicate")
        except LaunchRefused as exc:
            refused.append(exc.reason)

    mode = service._control_mode()
    try:
        brief = compose_agent_brief(
            db, {"kind": kind, "id": item_id}, project_id=project_id,
            instruction=instruction, control_mode=mode, repo_path=repo,
        )
    except AgentBriefRefused as exc:
        raise AgentHandRefused(exc.reason, str(exc)) from exc
    return {
        "text": brief["text"],
        "refs": brief["refs"],
        "bytes": brief["bytes"],
        "people_cut": brief["people_cut"],
        "sources": brief["sources"],
        "acceptance": brief["acceptance"],
        "repo": repo,
        "repo_label": _home_as_tilde(repo),
        "branch": spec["branch"],
        "worktree": spec["name"],
        "project_id": brief["project_id"],
        "control_mode": mode,
        "profile": profile_id,
        "refused": refused,
    }


__all__ = ["preview_hand"]
