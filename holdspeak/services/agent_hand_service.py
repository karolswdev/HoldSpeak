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
through ``process.input``. The tool gate decides the agent's held Bash
calls by Control mode (Conductor K5, ``tool_gate_rules``). At most
:data:`MAX_LIVE_LAUNCHES` launched agents run at one time.
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
from .errors import ServiceError
from .project_repository import (
    CLONE_HOST,
    ProjectRepositories,
    StoreNotRead,
    home_label,
    register as register_repository,
    registered_source,
    repository_state,
    watched_repositories,
)
from .agent_brief import (
    AgentBriefRefused,
    compose_agent_brief,
    parse_item_ref,
    project_for_item,
)

log = get_logger("agent_hand")

DEFAULT_PROFILE_ID = "claude-default"
#: The most HoldSpeak-launched agents that run at one time (Conductor K5).
#: One more Hand to agent refuses ``launch_cap_reached``.
MAX_LIVE_LAUNCHES = 3
#: Launch states whose agent may still run.
_LIVE_STATES = frozenset({"launched", "registered"})
#: The story-ref project token for an item that belongs to no Project.
DESK_PROJECT = "desk"

_NAME_UNSAFE = re.compile(r"[^A-Za-z0-9_.-]+")


#: Refusals that name a missing thing (HTTP 404); every other one is 409.
_NOT_FOUND_REASONS = frozenset({"item_unknown", "launch_unknown"})


class AgentHandRefused(ServiceError):
    """A typed refusal. ``code`` (also ``reason``) is machine-readable and
    rides every transport (HTTP and MCP answer ``{error, code}``); the
    message is path-free."""

    def __init__(
        self, reason: str, message: Optional[str] = None, *,
        context: Optional[dict[str, Any]] = None,
    ) -> None:
        status = 404 if reason in _NOT_FOUND_REASONS else 409
        super().__init__(reason, message or reason, context={**(context or {}), "status": status})
        self.reason = reason

    @classmethod
    def from_launch(cls, exc: Any) -> "AgentHandRefused":
        """A launch refusal, its detail kept (R3: the hooks Codex will not run)."""
        return cls(exc.reason, str(exc), context=dict(getattr(exc, "context", None) or {}))


def item_exists(db: Any, kind: str, item_id: str) -> bool:
    from ..grounding import hydrate_refs_detailed

    if kind == "issue":
        from .agent_issue import read_issue

        return read_issue(db, item_id) is not None

    try:
        hydrated = hydrate_refs_detailed(db, [], [], "summary", [f"{kind}:{item_id}"])
    except Exception:
        return False
    return bool(hydrated.blocks) and not hydrated.unknown


def worktree_spec(kind: str, item_id: str, round_: int = 1) -> dict[str, str]:
    """``{mode: new, name: hs-<kind>-<id>, branch: hs/<kind>-<id>}``; a later
    hand-off of the same item (``round_`` 2, 3, ...) adds ``-<round>``."""
    slug = _NAME_UNSAFE.sub("-", f"{kind}-{item_id}").strip("-.")[:60]
    if round_ > 1:
        slug = f"{slug}-{round_}"
    return {"mode": "new", "name": f"hs-{slug}", "branch": f"hs/{slug}"}


#: The most hand-offs of one item that get their own worktree name.
_MAX_ROUNDS = 50


def free_worktree_spec(registry: Any, repo_path: Any, kind: str, item_id: str) -> dict[str, str]:
    """The spec of this hand-off (Conductor R4, R1's walk).

    K4's cleanup removes a merged worktree but keeps its branch, so a second
    hand-off of the same item cannot reuse ``hs/<kind>-<id>`` (``git worktree
    add -b`` refuses an existing branch). The first round whose worktree
    folder exists (a held or live launch: the caller's own rules apply) or
    whose branch and folder are both free is the one used."""
    for round_ in range(1, _MAX_ROUNDS + 1):
        spec = worktree_spec(kind, item_id, round_)
        try:
            folder = derive_worktree_path(repo_path, spec["name"])
        except LaunchRefused:
            return spec
        if folder.exists():
            return spec
        branch = registry._git(Path(repo_path), "rev-parse", "--verify", "--quiet", f"refs/heads/{spec['branch']}")
        if not branch:
            return spec
    return worktree_spec(kind, item_id)


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
    registrations: Optional[ProjectRepositories] = None,
) -> Any:
    """The Delivery Source of a Project's repository, registered if absent.

    In order: a repository filed in the Project (``repository:<source_id>``);
    the clone of the Project's registered repository (PHILO-15 16); the
    GitHub repositories the Project's Room watches (and the registered one),
    matched by origin against the registered sources; the one registered
    clone labelled with the Project's name; then the project map (by watch
    origin or name). ``None`` when nothing names a local clone."""
    if not project_id:
        return None
    record = registrations.get(project_id) if registrations is not None else None
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
    if record and str(record["repository"]) not in repositories:
        repositories.append(str(record["repository"]))

    for source_id in filed:
        source = registry.get(source_id)
        if source is not None and source.primary_path:
            return source
    source = registered_source(record, registry)
    if source is not None:
        return source
    if repositories:
        for source in registry.sources():
            if source.primary_path and _matches_repo(registry, source.primary_path, repositories):
                return source
    if project_name:
        # A clone registered under the Project's own name (the label the
        # repository drawer or the project map gave it), when only one is.
        named = [
            source for source in registry.sources()
            if source.primary_path and source.label.strip().lower() == project_name.strip().lower()
        ]
        if len(named) == 1:
            return named[0]
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
        max_live: int = MAX_LIVE_LAUNCHES,
        issue_reads: Optional[Mapping[str, Any]] = None,
        repositories: Optional[ProjectRepositories] = None,
    ) -> None:
        self._db = db
        #: PHILO-15 16: the Projects' registered repositories and their clones.
        self.repositories = repositories or ProjectRepositories()
        #: The tracker reads of an issue brief (``gh_runner``, ``jira_adapter``);
        #: empty in production (the real CLIs).
        self.issue_reads: Mapping[str, Any] = dict(issue_reads or {})
        self._launch_service = launch_service
        self._control_mode = control_mode or _config_control_mode
        self._gate_path = gate_path
        self._project_map = project_map
        self._max_live = int(max_live)

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
        """Hand the item. A clone this hand made is named on the answer AND on
        a later refusal (the launch can still fail after it): the face shows
        CLONED either way (Astra r1 on #1000, finding 4)."""
        made: dict[str, Any] = {}
        try:
            answer = self._hand(
                principal, kind, item_id, made,
                instruction=instruction, profile=profile, project_id=project_id,
            )
        except ServiceError as exc:
            if made.get("clone"):
                exc.context["clone"] = made["clone"]
            raise
        if made.get("clone"):
            answer["clone"] = made["clone"]
        return answer

    def _hand(
        self,
        principal: Any,
        kind: str,
        item_id: str,
        made: dict[str, Any],
        *,
        instruction: Optional[str] = None,
        profile: Optional[str] = None,
        project_id: Optional[str] = None,
    ) -> dict[str, Any]:
        try:
            kind, item_id = parse_item_ref({"kind": kind, "id": item_id})
        except AgentBriefRefused as exc:
            raise AgentHandRefused.from_launch(exc) from exc
        # The item first: an unknown item is item_unknown, whatever else is missing.
        if not item_exists(self._db, kind, item_id):
            raise AgentHandRefused("item_unknown", f"{kind}:{item_id} is not on the desk")
        launcher = self._launch_service()
        profile_id = str(profile or DEFAULT_PROFILE_ID)
        agent = launcher._profiles.get(profile_id)
        if agent is None:
            raise AgentHandRefused("profile_unknown", f"unknown agent profile {profile_id!r}")
        try:
            launcher._preflight(agent)
        except LaunchRefused as exc:
            raise AgentHandRefused.from_launch(exc) from exc

        project_id = project_id or project_for_item(self._db, kind, item_id)
        _reload_registry(launcher._registry)
        try:
            source = resolve_project_repository(
                self._db, project_id, launcher._registry, project_map=self._project_map,
                registrations=self.repositories,
            )
        except StoreNotRead as exc:
            raise AgentHandRefused(exc.code, exc.detail) from exc
        clone: Optional[dict[str, Any]] = None
        if source is None:
            # PHILO-15 16: the Project's registered repository, cloned on its
            # first hand (one receipt), then registered as a Delivery Source.
            source, clone = self._clone_registered(principal, project_id, launcher._registry)
            if clone is not None:
                made["clone"] = clone
        if source is None:
            if watched_repositories(self._db, project_id):
                raise AgentHandRefused(
                    "repository_not_registered", "the Project's Room watches a repository nobody registered"
                )
            raise AgentHandRefused(
                "no_repository", "the item's Project names no local repository"
            )
        spec = free_worktree_spec(launcher._registry, source.primary_path, kind, item_id)
        try:
            worktree_path = derive_worktree_path(source.primary_path, spec["name"])
        except LaunchRefused as exc:
            raise AgentHandRefused.from_launch(exc) from exc
        if worktree_path.exists():
            # Handed before: an earlier launch of this item whose brief is
            # still held resumes on that launch; it is never relaunched.
            existing = _launch_for_origin(launcher, kind, item_id)
            if existing is not None and existing.get("instruction_state") != "sent" and isinstance(
                existing.get("pending_brief"), Mapping
            ):
                held_profile = str(existing.get("profile_id") or "")
                if profile and held_profile and str(profile) != held_profile:
                    # The held launch runs its own agent: a hand-off that names
                    # another one would resume an agent the owner did not pick.
                    raise AgentHandRefused(
                        "launch_profile_mismatch",
                        f"the held launch of this item runs {held_profile!r}",
                    )
                try:
                    record = launcher.resume_delivery(str(existing["launch_id"]))
                except LaunchRefused as exc:
                    raise AgentHandRefused.from_launch(exc) from exc
                return self._answer(
                    {"launch": record, "operation_id": record.get("operation_id")},
                    spec, source, None, kind, item_id, project_id, self._control_mode(),
                    resumed=True,
                )
            raise AgentHandRefused(
                "worktree_duplicate", f"worktree {spec['name']!r} already exists"
            )
        live = live_launches(launcher)
        if len(live) >= self._max_live:
            raise AgentHandRefused(
                "launch_cap_reached",
                f"{len(live)} agents run now; the limit is {self._max_live}",
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
                principal=principal,
                issue_reads=self.issue_reads,
            )
        except AgentBriefRefused as exc:
            raise AgentHandRefused.from_launch(exc) from exc

        try:
            story_ref = derived_story_ref(project_id or DESK_PROJECT, kind, item_id)
        except LaunchRefused as exc:
            raise AgentHandRefused.from_launch(exc) from exc
        request = {
            "agent_profile_id": profile_id,
            "source_id": source.source_id,
            "worktree": spec,
            "story_ref": story_ref,
            "origin_ref": {"kind": kind, "id": item_id},
        }
        if agent.get("executable") in ("claude", "codex", "pi"):
            # Conductor R3: Codex is gated like Claude Code (its -c hooks);
            # pi through its extension (pi spike #1020).
            result = self._launch_gated(launcher, request, brief["text"], principal, worktree_path, spec["name"])
        else:
            result = self._launch_ungated(launcher, request, brief["text"], principal)
        return self._answer(result, spec, source, brief, kind, item_id, project_id, mode)

    # ── PHILO-15 16: the Project's repository ───────────────────────

    def _clone_registered(
        self, principal: Any, project_id: Optional[str], registry: Any,
    ) -> tuple[Any, Optional[dict[str, Any]]]:
        """Clone the Project's registered repository (``project.repository.clone``,
        an admitted kernel operation: one receipt) and register the clone as a
        Delivery Source. ``(None, None)`` when the Project registered none."""
        record = self.repositories.get(project_id)
        if record is None:
            return None, None
        repository = str(record["repository"])
        from . import project_kernel

        # The receipt's target names the egress: repository:github.com/<owner>/<name>.
        payload = {"project_id": str(project_id), "repository": repository, "host": CLONE_HOST}
        try:
            path, kernel = project_kernel.run(
                self._db, principal, "project.repository.clone", payload,
                lambda _minted: self.repositories.clone(repository),
            )
        except ServiceError as exc:
            raise AgentHandRefused(exc.code, exc.detail, context={
                key: value for key, value in exc.context.items() if key in ("operation_id", "receipt")
            }) from exc
        try:
            source, _ = registry.register(str(path), label=repository.split("/", 1)[1])
        except RegistryError as exc:
            raise AgentHandRefused("clone_not_registered", str(exc)) from exc
        cloned_at = record.get("cloned_at") or _iso_now()
        self.repositories.put(str(project_id), {**record, "source_id": source.source_id, "cloned_at": cloned_at})
        return source, {
            "repository": repository,
            "host": CLONE_HOST,
            "state": "cloned",
            "cloned_at": cloned_at,
            "folder": home_label(str(path)),
            "operation_id": (kernel or {}).get("operation_id"),
            "receipt": (kernel or {}).get("receipt"),
        }

    def register_project_repository(
        self, principal: Any, *, project_id: str, repository: str, command_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """``project.repository.register`` (PHILO-15 16, B38): the Door's GitHub
        row (or the drawer's Register) names the Project's repository. Owner
        only; an admitted kernel operation (one receipt). Nothing is cloned
        here: the first hand clones it."""
        from . import project_kernel
        from ..principals import PrincipalKind

        if project_kernel.current() is None:
            raise RuntimeError("project.repository.register runs only as an admitted kernel operation")
        if getattr(principal, "kind", None) is not PrincipalKind.OWNER:
            raise ServiceError("owner_required", "Only the owner registers a repository.", context={"status": 403})
        register_repository(self._db, self.repositories, project_id, repository)
        return self.repository_state(principal, project_id)

    def repository_state(self, principal: Any, project_id: str, *, registry: Any = None) -> dict[str, Any]:
        """The Project's repository as the drawer's Get Info shows it."""
        return repository_state(self._db, project_id, self.repositories, registry)

    def _answer(
        self, result: Mapping[str, Any], spec: Mapping[str, str], source: Any,
        brief: Optional[Mapping[str, Any]], kind: str, item_id: str,
        project_id: Optional[str], mode: str, *, resumed: bool = False,
    ) -> dict[str, Any]:
        launch = result.get("launch") or {}
        story_ref = launch.get("story_ref") or derived_story_ref(project_id or DESK_PROJECT, kind, item_id)
        return {
            "status": "launched" if launch.get("state") in ("launched", "registered") else "failed",
            "resumed": resumed,
            "profile": launch.get("profile_id"),
            # The receipt decides: "sent" only after a delivered process.input.
            "instruction_state": launch.get("instruction_state"),
            "trust_state": launch.get("trust_state"),
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
            } if brief else None,
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

    # ── Claude Code and Codex: process.spawn, the gate armed for this worktree ──

    def _launch_gated(
        self, launcher: Any, request: dict[str, Any], text: str, principal: Any,
        worktree_path: Path, name: str,
    ) -> dict[str, Any]:
        prior = self._arm_gate(worktree_path, name)
        try:
            # The brief is held and typed once the rider registers the
            # session, so a folder-trust prompt or a slow start cannot eat it.
            result = launcher.submit_process_spawn(
                request, text, principal, after_registration=True
            )
        except LaunchRefused as exc:
            self._release_gate(worktree_path, name, prior, "the launch refused before it ran")
            raise AgentHandRefused.from_launch(exc) from exc
        except Exception:
            self._release_gate(worktree_path, name, prior, "the launch failed before it ran")
            raise
        launch = result.get("launch") or {}
        stage = str((launch.get("failure") or {}).get("stage") or "")
        if launch.get("state") == "failed" and stage in ("worktree_create", "spawn"):
            # No process runs there: this call's hold goes, the rest stays.
            self._release_gate(worktree_path, name, prior, f"the launch failed at {stage}")
        return result

    def _arm_gate(self, worktree_path: Path, name: str) -> dict[str, Any]:
        """Hold Bash for exactly the new worktree path; the press on the
        verb is the consent. One locked read-modify-write; audited. Returns
        what the path held before, so a failed launch restores exactly it."""
        from .. import coder_gate

        key = str(worktree_path)

        def arm(config: Any) -> dict[str, Any]:
            prior = {"tools": config.repos.get(key), "own": key in config.armed_paths}
            config.repos[key] = list(coder_gate.DEFAULT_TOOLS)
            # Armed on its own: the master switch is not touched, so no
            # other listed repo becomes held.
            if key not in config.armed_paths:
                config.armed_paths.append(key)
            return prior

        prior = coder_gate.update_gate_config(arm, self._gate_path)
        self._audit(name, outcome="gate_armed", detail=f"hold Bash for worktree {name} only")
        return prior

    def _release_gate(self, worktree_path: Path, name: str, prior: Mapping[str, Any], why: str) -> None:
        """Undo this call's arm, and only it: the path's prior entry returns."""
        from .. import coder_gate

        key = str(worktree_path)

        def release(config: Any) -> None:
            if prior.get("tools") is None:
                config.repos.pop(key, None)
            else:
                config.repos[key] = list(prior["tools"])
            if not prior.get("own"):
                config.armed_paths = [path for path in config.armed_paths if path != key]

        coder_gate.update_gate_config(release, self._gate_path)
        self._audit(name, outcome="gate_released", detail=why)

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
        """An agent with no gate hook (none since Conductor R3, which gates
        Codex): the ungated launch. The brief is held and typed only when
        Codex's rider hooks register the session (its readiness); with no
        hooks installed it stays held as ``hooks_missing`` (K1's one-press
        install, then resume on the same launch)."""
        try:
            record = launcher.launch(request, principal=principal)
        except LaunchRefused as exc:
            raise AgentHandRefused.from_launch(exc) from exc
        if record.get("state") != "launched":
            return {"launch": record}
        ready = codex_hooks_installed()
        record = launcher.first_message.hold(
            str(record["launch_id"]), text, principal,
            agent=str(request.get("agent_profile_id") or "codex-default"),
            trust=False, state="pending" if ready else "hooks_missing",
        ) or record
        if ready:
            launcher.first_message.start(str(record["launch_id"]))
        launcher.first_message.watch(str(record["launch_id"]))
        return {"launch": record}

    def resume(self, principal: Any, launch_id: str) -> dict[str, Any]:
        """Deliver the held brief of an existing launch (no relaunch). The
        owner's press only, as ``agent.hand`` is."""
        from ..principals import PrincipalKind

        if getattr(principal, "kind", None) is not PrincipalKind.OWNER:
            raise ServiceError(
                "owner_required", "Only the owner resumes a launch's brief.", context={"status": 403}
            )
        launcher = self._launch_service()
        try:
            record = launcher.resume_delivery(str(launch_id))
        except LaunchRefused as exc:
            raise AgentHandRefused.from_launch(exc) from exc
        return {
            "launch_id": record.get("launch_id"),
            "state": record.get("state"),
            "instruction_state": record.get("instruction_state"),
            "trust_state": record.get("trust_state"),
        }


def _iso_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat()


def _reload_registry(registry: Any) -> None:
    """Read the source registry file again: the launch driver is shared for the
    process, and a repository registered since it loaded (the Delivery drawer's
    own registry instance) is otherwise invisible to it until a restart."""
    reload = getattr(registry, "reload", None)
    if callable(reload):
        try:
            reload()
        except Exception as exc:  # the cached read still answers
            log.warning("delivery registry not read again (%s)", exc)


def live_launches(launcher: Any) -> list[dict[str, Any]]:
    """The HoldSpeak launches whose agent runs now: launched or registered,
    follow-through not done, and the tmux session alive."""
    rows: list[dict[str, Any]] = []
    for record in launcher._ledger.list():
        if str(record.get("state") or "") not in _LIVE_STATES:
            continue
        if (record.get("follow_through") or {}).get("done"):
            continue
        if not launcher._session_alive(str(record.get("session") or "")):
            continue
        rows.append(record)
    return rows


def launch_liveness(launcher: Any) -> Optional[bool]:
    """Whether a HoldSpeak launch runs now: ``True``, ``False``, or ``None``
    when it is not known (a tmux probe failed or timed out and no other
    launch is alive). The spool timer (PHILO-14 C0b) drains on ``None`` and
    asks again, and never takes a failed probe for "none live"."""
    if live_launches(launcher):
        return True
    if getattr(launcher, "_probe_failed", None):
        return None
    return False


def codex_hooks_installed(path: Optional[Path] = None) -> bool:
    """Whether Codex's hook file carries HoldSpeak's rider hooks.

    The file Codex reads: ``$CODEX_HOME/hooks.json`` when ``CODEX_HOME`` is
    set, the same resolver the one-press install writes through (Conductor
    R1: this read ``~/.codex`` only, so a launch read hooks as missing right
    after the install had written them)."""
    from ..agent_context.hooks import AGENT_HOOK_COMMAND_MARKER, agent_settings_path

    target = path or agent_settings_path("codex")
    try:
        return AGENT_HOOK_COMMAND_MARKER in target.read_text(encoding="utf-8")
    except OSError:
        return False


def _launch_for_origin(launcher: Any, kind: str, item_id: str) -> Optional[dict[str, Any]]:
    """The newest launch whose origin is this item."""
    for record in reversed(launcher._ledger.list()):
        origin = record.get("origin_ref") or {}
        if origin.get("kind") == kind and origin.get("id") == item_id:
            return record
    return None


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
    "MAX_LIVE_LAUNCHES",
    "launch_liveness",
    "live_launches",
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
