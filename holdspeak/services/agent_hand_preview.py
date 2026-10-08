"""The launch sheet's preview: what Hand to agent would send, with no launch.

docs/internal/CONDUCTOR.md, the F faces (K3a/K3b): the sheet shows the brief
(its sources, bytes, the People cut, the acceptance checks), the repository,
the new worktree's branch and the Control mode BEFORE the owner presses
Launch. This module composes the same brief the hand composes
(``compose_agent_brief`` with the same inputs) and resolves the same
repository.

It writes nothing and starts nothing. It does NOT call the hand's launch
driver getter: that getter binds the kernel, reconciles held launches and
seeds the profile, registry and ledger files. The preview reads those files
through :class:`LaunchReads` (read only, no seed, no import, no save), reads
the Control mode from the config file without creating it, and the route is
quiet (``web/announce.py`` QUIET_ROUTES).

A thing that would refuse the launch (no repository, the agent or tmux not
installed, the worktree already there, the launch cap, a held launch of
another agent) is named in ``refused`` so the sheet can show it as a token;
the brief still shows. When the hand would RESUME a held launch, the preview
shows that launch: its agent, its held brief and its delivery state
(``resume``). An item the brief cannot carry refuses the preview itself, by
the same names the hand uses.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable, Mapping, Optional

from ..delivery import factory_launch
from ..delivery import registry as delivery_registry
from ..delivery.factory_launch import LaunchLedger, LaunchRefused, derive_worktree_path
from ..principals import PrincipalKind
from .agent_brief import AgentBriefRefused, compose_agent_brief, parse_item_ref, project_for_item
from .agent_hand_service import (
    DEFAULT_PROFILE_ID,
    AgentHandRefused,
    AgentHandService,
    _config_control_mode,
    _launch_for_origin,
    item_exists,
    live_launches,
    resolve_project_repository,
    free_worktree_spec,
    worktree_spec,
)
from .errors import ServiceError
from .project_repository import CLONE_HOST, StoreNotRead, watched_repositories


@dataclass
class LaunchReads:
    """The launch driver's state, read only: the profiles, the source registry,
    the launch ledger, PATH and tmux sessions. Nothing here seeds, imports,
    saves, binds or reconciles."""

    profiles_path: Path = field(default_factory=lambda: factory_launch.DEFAULT_PROFILES_PATH)
    registry_path: Path = field(default_factory=lambda: delivery_registry.DEFAULT_REGISTRY_PATH)
    ledger_path: Path = field(default_factory=lambda: factory_launch.DEFAULT_LAUNCHES_PATH)
    which: Callable[[str], Optional[str]] = shutil.which
    runner: Optional[Callable[..., Any]] = None

    def profile(self, profile_id: str) -> Optional[dict[str, Any]]:
        """A profile as the driver would load it; the defaults when no file is valid."""
        raw: Any = None
        try:
            raw = json.loads(Path(self.profiles_path).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            raw = None
        entries = (
            raw.get("profiles") or []
            if isinstance(raw, dict) and raw.get("agent_profiles_schema") == factory_launch.AGENT_PROFILES_SCHEMA
            else factory_launch._DEFAULT_PROFILES
        )
        for entry in entries:
            profile = factory_launch._valid_profile(entry)
            if profile is not None and profile["profile_id"] == profile_id:
                return profile
        # A later seeded default (pi-default) the stored file predates.
        return factory_launch.later_default_profile(profile_id)

    def preflight(self, profile: Mapping[str, Any]) -> Optional[str]:
        """The driver's preflight refusal by name (``tmux_absent``, ``executable_absent``)."""
        if self.which("tmux") is None:
            return "tmux_absent"
        executable = str(profile.get("executable") or "")
        if executable and self.which(executable) is None:
            return "executable_absent"
        return None

    def registry(self) -> Any:
        """The source registry as stored. No v1 import, no save (an absent file is empty)."""
        reg = object.__new__(delivery_registry.DeliveryRegistry)
        reg._path = Path(self.registry_path)
        reg._map_path = None
        reg._run = delivery_registry._default_git_runner
        reg._instance = ""
        reg._sources = []
        try:
            raw = json.loads(reg._path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            raw = None
        if isinstance(raw, dict) and raw.get("registry_schema") == delivery_registry.REGISTRY_SCHEMA:
            reg._sources = [
                delivery_registry.DeliveryRegistry._source_from_stored(entry)
                for entry in raw.get("sources") or []
                if isinstance(entry, dict)
            ]
        return _ReadOnlyRegistry(reg)

    def launcher(self) -> Any:
        """What ``live_launches`` and ``_launch_for_origin`` read: the ledger, a session check."""
        ledger = LaunchLedger(Path(self.ledger_path))  # reads only; an absent file is empty
        # A probe that failed (no tmux, a timeout) reads "not alive" here, as
        # before; it is also named, so a caller can tell "dead" from "not
        # known" (PHILO-14 C0b: ``launch_liveness``).
        probe_failed: list[str] = []

        def alive(session: str) -> bool:
            run = self.runner or (lambda argv: subprocess.run(argv, capture_output=True, text=True, timeout=5))
            try:
                return run(["tmux", "has-session", "-t", session]).returncode == 0
            except (OSError, subprocess.TimeoutExpired):
                probe_failed.append(session)
                return False

        return SimpleNamespace(_ledger=ledger, _session_alive=alive, _probe_failed=probe_failed)


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

    def register(self, path: str, label: Optional[str] = None, **_kw: Any) -> tuple[Any, bool]:
        return SimpleNamespace(source_id=None, primary_path=path, label=label or ""), False


def _home_as_tilde(path: Optional[str]) -> Optional[str]:
    """The path as the face shows it: the hub's home folder is ``~``."""
    if not path:
        return None
    for home in dict.fromkeys((str(Path.home()), str(Path.home().resolve()))):
        if path == home or path.startswith(home + "/"):
            return "~" + path[len(home):]
    return path


def _read_control_mode(service: AgentHandService) -> str:
    """The Control mode. The default reader creates config.json when it is
    absent, so the preview reads the file itself."""
    if service._control_mode is not _config_control_mode:
        return str(service._control_mode())
    from ..config.core import _active_config_file

    try:
        data = json.loads(_active_config_file().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return "yolo"
    mode = str((data or {}).get("control_mode", "yolo")).strip().lower() if isinstance(data, dict) else "yolo"
    return mode if mode in {"safe", "neutral", "yolo"} else "yolo"


def preview_hand(
    service: AgentHandService,
    principal: Any,
    kind: str,
    item_id: str,
    *,
    instruction: Optional[str] = None,
    profile: Optional[str] = None,
    project_id: Optional[str] = None,
    reads: Optional[LaunchReads] = None,
) -> dict[str, Any]:
    """``{text, refs, bytes, people_cut, sources, acceptance, repo, repo_label, branch,
    worktree, project_id, control_mode, kind, id, requested_profile, profile, resume,
    refused, engine}``; owner only; no side effect. ``engine`` is pi's engine
    for coding work (``{host, model, boundary}``), ``None`` for other agents."""
    if getattr(principal, "kind", None) is not PrincipalKind.OWNER:
        raise ServiceError("owner_required", "Only the owner previews a hand-off.", context={"status": 403})
    try:
        kind, item_id = parse_item_ref({"kind": kind, "id": item_id})
    except AgentBriefRefused as exc:
        raise AgentHandRefused(exc.reason, str(exc)) from exc
    db = service._db
    if not item_exists(db, kind, item_id):
        raise AgentHandRefused("item_unknown", f"{kind}:{item_id} is not on the desk")
    reads = reads or LaunchReads()
    requested = str(profile or DEFAULT_PROFILE_ID)
    agent = reads.profile(requested)
    if agent is None:
        raise AgentHandRefused("profile_unknown", f"unknown agent profile {requested!r}")
    refused: list[str] = []
    blocked = reads.preflight(agent)
    if blocked:
        refused.append(blocked)
    # pi (pi spike #1020): the engine it would run on (the egress the line
    # names), or the route's own refusal word.
    engine: Optional[dict[str, Any]] = None
    if str(agent.get("executable") or "") == "pi":
        from ..delivery.pi_launch import coding_engine

        try:
            engine = coding_engine(service._db).to_wire()
        except LaunchRefused as exc:
            refused.append(exc.reason)

    project_id = project_id or project_for_item(db, kind, item_id)
    registrations = getattr(service, "repositories", None)
    store_refusal: Optional[str] = None
    try:
        if registrations is not None:
            registrations.get(project_id)
    except StoreNotRead as exc:
        # NOT READ: named, and the registrations are left out of this read.
        store_refusal, registrations = exc.code, None
    source = resolve_project_repository(
        db, project_id, reads.registry(), project_map=service._project_map, registrations=registrations,
    )
    repo = str(source.primary_path) if source is not None else None
    # PHILO-15 16: a registered repository with no clone yet is cloned by the
    # hand (egress to github.com): named here, never NO REPOSITORY.
    clone: Optional[dict[str, Any]] = None
    record = registrations.get(project_id) if repo is None and registrations is not None else None
    if record is not None:
        target = str(registrations.clone_path(str(record["repository"])))
        clone = {"repository": str(record["repository"]), "host": CLONE_HOST, "state": "to_clone",
                 "label": _home_as_tilde(target)}
    spec = (
        free_worktree_spec(reads.registry(), repo, kind, item_id) if repo is not None
        else worktree_spec(kind, item_id)
    )
    launcher = reads.launcher()
    resume: Optional[dict[str, Any]] = None
    actual = requested
    held_text: Optional[str] = None
    if store_refusal:
        # The hand refuses on a store it cannot read whatever source resolves
        # (Astra r2 on PR 1000): the preview names it the same way, always.
        refused.append(store_refusal)
    if repo is None and clone is None and store_refusal:
        pass
    elif repo is None and clone is None:
        # A repository the Room watches but nobody registered: the drawer's
        # Register verb fixes it; with none at all, NO REPOSITORY.
        watched = watched_repositories(db, project_id)
        refused.append("repository_not_registered" if watched else "no_repository")
    elif repo is not None:
        try:
            exists = derive_worktree_path(repo, spec["name"]).exists()
        except LaunchRefused as exc:
            refused.append(exc.reason)
            exists = False
        if exists:
            # The hand's own rule: a launch whose brief is still held resumes
            # on that launch (its agent, its brief); any other worktree refuses.
            held = _launch_for_origin(launcher, kind, item_id)
            if held and held.get("instruction_state") != "sent" and isinstance(held.get("pending_brief"), Mapping):
                actual = str(held.get("profile_id") or requested)
                held_text = str((held.get("pending_brief") or {}).get("text") or "") or None
                resume = {
                    "launch_id": held.get("launch_id"),
                    "profile": actual,
                    "instruction_state": held.get("instruction_state"),
                }
                if actual != requested:
                    refused.append("launch_profile_mismatch")
            else:
                refused.append("worktree_duplicate")
        elif len(live_launches(launcher)) >= service._max_live:
            refused.append("launch_cap_reached")

    mode = _read_control_mode(service)
    try:
        brief = compose_agent_brief(
            db, {"kind": kind, "id": item_id}, project_id=project_id,
            instruction=instruction, control_mode=mode, repo_path=repo,
            principal=principal, issue_reads=getattr(service, "issue_reads", None),
        )
    except AgentBriefRefused as exc:
        raise AgentHandRefused(exc.reason, str(exc)) from exc
    text = held_text if held_text is not None else brief["text"]
    return {
        "text": text,
        "refs": brief["refs"],
        "bytes": len(text.encode("utf-8")),
        "people_cut": brief["people_cut"],
        "sources": brief["sources"],
        "acceptance": brief["acceptance"],
        "tracker": brief.get("tracker"),
        "repo": repo,
        "repo_label": _home_as_tilde(repo) if repo is not None else (clone or {}).get("label"),
        "clone": clone,
        "branch": spec["branch"],
        "worktree": spec["name"],
        "project_id": brief["project_id"],
        "control_mode": mode,
        "kind": kind,
        "id": item_id,
        # What the sheet asked for, and the agent the launch would really run.
        "requested_profile": requested,
        "profile": actual,
        "resume": resume,
        "refused": refused,
        "engine": engine,
    }


__all__ = ["LaunchReads", "preview_hand"]
