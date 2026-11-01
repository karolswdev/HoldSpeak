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

Betterment AG5: the limit is the setting ``agents.working_at_once`` (default
6), and only an agent that works or needs the owner counts
(``agent_flights.slot_holders``). At the limit a hand with ``queue`` waits
in ``agent_hand_queue`` and the heartbeat starts it when an agent is free.
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
    AGENT_BRIEF_CAP_BYTES,
    AgentBriefRefused,
    compose_agent_brief,
    parse_item_ref,
    project_for_item,
)

log = get_logger("agent_hand")

DEFAULT_PROFILE_ID = "claude-default"
#: The most HoldSpeak-launched agents that WORK at one time when the setting
#: is not read (Betterment AG5: ``agents.working_at_once``, default 6). One
#: more Hand to agent refuses ``launch_cap_reached``, or waits in the queue.
MAX_LIVE_LAUNCHES = 6
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

    if kind == "program_step":
        from ..db.programs import ProgramStore

        return ProgramStore(db).get_step(item_id) is not None
    if kind == "issue":
        from .agent_issue import read_issue

        return read_issue(db, item_id) is not None

    try:
        hydrated = hydrate_refs_detailed(db, [], [], "summary", [f"{kind}:{item_id}"])
    except Exception:
        return False
    return bool(hydrated.blocks) and not hydrated.unknown


def item_title(db: Any, kind: str, item_id: str) -> str:
    """The item's own title (its desk name), or ``""`` when it has none."""
    from ..grounding import hydrate_refs_detailed

    if kind == "program_step":
        from ..db.programs import ProgramStore

        return str((ProgramStore(db).get_step(item_id) or {}).get("title") or "")
    if kind == "issue":
        from .agent_issue import read_issue

        issue = read_issue(db, item_id) or {}
        return str(issue.get("title") or "")
    try:
        hydrated = hydrate_refs_detailed(db, [], [], "summary", [f"{kind}:{item_id}"])
    except Exception:
        return ""
    if not hydrated.blocks or hydrated.unknown:
        return ""
    title = str(hydrated.blocks[0].title or "")
    return "" if title == item_id else title


#: Betterment AG4: the most characters of a branch slug (whole words).
BRANCH_SLUG_MAX = 40
_SLUG_WORD = re.compile(r"[a-z0-9]+")


def branch_slug(title: str, max_chars: int = BRANCH_SLUG_MAX) -> str:
    """``Draft test scaffolding for flags`` -> ``draft-test-scaffolding-for-flags``:
    lower-case ASCII words joined by ``-``, cut at a whole word; ``""`` when
    the title has no such word (the branch then names the item)."""
    import unicodedata

    plain = unicodedata.normalize("NFKD", str(title or "")).encode("ascii", "ignore").decode().lower()
    slug = ""
    for word in _SLUG_WORD.findall(plain):
        joined = f"{slug}-{word}" if slug else word
        if len(joined) > max_chars:
            break
        slug = joined
    return slug or (_SLUG_WORD.findall(plain) or [""])[0][:max_chars]


def worktree_spec(kind: str, item_id: str, round_: int = 1, title: str = "") -> dict[str, str]:
    """``{mode: new, name: hs-<kind>-<id>, branch: hs/<title-slug>}``; a later
    hand-off of the same item (``round_`` 2, 3, ...) adds ``-<round>``.

    Betterment AG4 (FOLLOWUPS AG1): the branch is named by the item's title
    (``hs/draft-test-scaffolding-for-flags``), so the face reads it; with no
    title it names the item (``hs/<kind>-<id>``). The worktree folder keeps
    the item's id: a hand of the same item finds its folder again."""
    slug = _NAME_UNSAFE.sub("-", f"{kind}-{item_id}").strip("-.")[:60]
    words = branch_slug(title)
    branch = words or slug
    if round_ > 1:
        slug = f"{slug}-{round_}"
        branch = f"{branch}-{round_}"
    return {"mode": "new", "name": f"hs-{slug}", "branch": f"hs/{branch}"}


#: The most hand-offs of one item that get their own worktree name.
_MAX_ROUNDS = 50


def program_step_spec(db: Any, step_id: str) -> Optional[dict[str, str]]:
    """Programs (design §11): a step's worktree ``hs-program-<step id>`` on the
    branch ``program/<program slug>/<ordinal>-<step slug>``, from the
    Program's base branch."""
    from ..db.programs import ProgramStore

    store = ProgramStore(db)
    step = store.get_step(step_id)
    program = store.get_program(step["program_id"]) if step else None
    if step is None or program is None:
        return None
    name = _NAME_UNSAFE.sub("-", f"hs-program-{step_id}").strip("-.")[:64]
    words = branch_slug(step["title"], 32) or "step"
    branch = f"program/{branch_slug(program['title'], 32) or 'program'}/{int(step['ordinal'])}-{words}"
    if step.get("race_of"):
        branch += f"-{_NAME_UNSAFE.sub('-', step_id)[-6:]}"
    spec = {"mode": "new", "name": name, "branch": branch}
    if program.get("base_branch"):
        spec["start_point"] = str(program["base_branch"])
    # PG20: a step started from a checkpoint starts at its pinned ref.
    start_from = ((step.get("facts") or {}).get("start_from") or {}).get("ref")
    if start_from:
        spec["start_point"] = str(start_from)
    return spec


def program_step_source(db: Any, step_id: str, registry: Any) -> Any:
    """The Delivery Source of a step's Program repository (registered when
    it is not one yet)."""
    from ..db.programs import ProgramStore

    store = ProgramStore(db)
    step = store.get_step(step_id)
    program = store.get_program(step["program_id"]) if step else None
    root = str((program or {}).get("repo_root") or "")
    if not root:
        return None
    try:
        source, _ = registry.register(root, label=Path(root).name)
    except RegistryError:
        return None
    return source


def free_worktree_spec(
    registry: Any, repo_path: Any, kind: str, item_id: str, title: str = "",
) -> dict[str, str]:
    """The spec of this hand-off (Conductor R4, R1's walk).

    K4's cleanup removes a merged worktree but keeps its branch, so a second
    hand-off of the same item cannot reuse its branch (``git worktree add
    -b`` refuses an existing branch). The first round whose worktree folder
    exists (a held or live launch: the caller's own rules apply) or whose
    branch and folder are both free is the one used. Two items with the same
    title get the same words: the second takes the next round."""
    for round_ in range(1, _MAX_ROUNDS + 1):
        spec = worktree_spec(kind, item_id, round_, title)
        try:
            folder = derive_worktree_path(repo_path, spec["name"])
        except LaunchRefused:
            return spec
        if folder.exists():
            return spec
        branch = registry._git(Path(repo_path), "rev-parse", "--verify", "--quiet", f"refs/heads/{spec['branch']}")
        if not branch:
            return spec
    return worktree_spec(kind, item_id, 1, title)


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
        max_live: Optional[int] = None,
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
        #: ``None``: the setting, read at each hand (a change applies at once).
        self._max_live = None if max_live is None else int(max_live)

    def _launch_mode(self, kind: str, item_id: str, helper_of: Optional[str] = None) -> str:
        """The Control mode word of this hand's launch (``control_level.mode_for_request``)."""
        from .control_level import mode_for_request

        request = {"origin_ref": {"kind": kind, "id": item_id}, **({"helper_of": helper_of} if helper_of else {})}
        return mode_for_request(request, db=self._db, desk=self._control_mode)

    @property
    def working_at_once(self) -> int:
        """The limit now: the set override, else ``agents.working_at_once``."""
        if self._max_live is not None:
            return self._max_live
        return working_at_once()

    def working_count(self, launcher: Any = None) -> int:
        """How many launched agents hold a slot now (AG5: working or
        needing the owner; done, quiet and stopped agents do not count)."""
        return len(working_launches(launcher or self._launch_service(), self._db))

    def has_free_slot(self) -> bool:
        return self.working_count() < self.working_at_once

    def hand(
        self,
        principal: Any,
        kind: str,
        item_id: str,
        *,
        instruction: Optional[str] = None,
        profile: Optional[str] = None,
        project_id: Optional[str] = None,
        queue: bool = False,
        helper_of: Optional[str] = None,
        helper_round: int = 1,
        start_point: Optional[str] = None,
        review: Optional[Mapping[str, Any]] = None,
        review_by: Optional[str] = None,
        engine: Optional[str] = None,
        handoff_brief: Optional[str] = None,
    ) -> dict[str, Any]:
        """Hand the item. A clone this hand made is named on the answer AND on
        a later refusal (the launch can still fail after it): the face shows
        CLONED either way (Astra r1 on #1000, finding 4)."""
        if review is None and review_by:
            from .agent_review import initial_review

            review = initial_review(review_by)
        made: dict[str, Any] = {}
        try:
            answer = self._hand(
                principal, kind, item_id, made,
                instruction=instruction, profile=profile, project_id=project_id,
                queue=queue, helper_of=helper_of, helper_round=helper_round, review=review, review_by=review_by,
                start_point=start_point, engine=engine, handoff_brief=handoff_brief,
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
        queue: bool = False,
        helper_of: Optional[str] = None,
        helper_round: int = 1,
        start_point: Optional[str] = None,
        review: Optional[Mapping[str, Any]] = None,
        review_by: Optional[str] = None,
        engine: Optional[str] = None,
        handoff_brief: Optional[str] = None,
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
            if engine:
                launcher._preflight(agent, str(engine))
            else:
                launcher._preflight(agent)
        except LaunchRefused as exc:
            raise AgentHandRefused.from_launch(exc) from exc

        project_id = project_id or project_for_item(self._db, kind, item_id)
        _reload_registry(launcher._registry)
        if kind == "program_step":
            # Programs: the repository is the Program's own (a path or its
            # Project's), whatever the Project's Room watches.
            source = program_step_source(self._db, item_id, launcher._registry)
        else:
            try:
                source = resolve_project_repository(
                    self._db, project_id, launcher._registry, project_map=self._project_map,
                    registrations=self.repositories,
                )
            except StoreNotRead as exc:
                raise AgentHandRefused(exc.code, exc.detail) from exc
        clone: Optional[dict[str, Any]] = None
        if source is None and kind != "program_step":
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
        spec = (program_step_spec(self._db, item_id) if kind == "program_step" else None) or free_worktree_spec(
            launcher._registry, source.primary_path, kind, item_id, item_title(self._db, kind, item_id),
        )
        parent: Optional[Mapping[str, Any]] = None
        if helper_of:
            # Betterment AG11: a helper works in its own worktree, on a branch
            # that starts at its parent's branch.
            parent = launcher._ledger.get(helper_of) or {}
            round_suffix = f"-{max(1, int(helper_round))}" if int(helper_round) > 1 else ""
            spec = {
                "mode": "new", "name": f"{spec['name']}{round_suffix}-helper", "branch": f"{spec['branch']}{round_suffix}-helper",
                **({"start_point": str(start_point or parent.get("branch"))} if start_point or parent.get("branch") else {}),
            }
        try:
            worktree_path = derive_worktree_path(source.primary_path, spec["name"])
        except LaunchRefused as exc:
            raise AgentHandRefused.from_launch(exc) from exc
        if worktree_path.exists() and helper_of:
            raise AgentHandRefused("helper_exists", "this agent already has its one helper")
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
                    spec, source, None, kind, item_id, project_id,
                    str(record.get("control_mode") or self._launch_mode(kind, item_id, helper_of)),
                    resumed=True,
                )
            again_of = _hand_again_of(existing)
            if again_of is None:
                raise AgentHandRefused(
                    "worktree_duplicate", f"worktree {spec['name']!r} already exists"
                )
            # Betterment AG7 gaps, Hand again: the earlier agent of this item
            # stopped (a restart, a failed Resume, his Stop, or it ended); a
            # new agent continues in the same worktree, on its branch.
            spec = {"mode": "existing", "worktree_id": again_of[1], "again_of": again_of[0],
                    "name": spec["name"], "branch": spec["branch"]}
        working = len(working_launches(launcher, self._db))
        limit = self.working_at_once
        if working >= limit:
            if queue:
                # AG5: "Start when one is free": the press waits in the queue
                # and the heartbeat starts it (agent_hand_queue.start_queued).
                from .agent_hand_queue import HandQueue

                entry = HandQueue().add(
                    kind, item_id, instruction=instruction, profile=profile, project_id=project_id,
                    review_by=review_by,
                )
                return {
                    "status": "queued",
                    "queue_id": entry["queue_id"],
                    "queued_at": entry["queued_at"],
                    "profile": profile_id,
                    "origin_ref": {"kind": kind, "id": item_id},
                    "project_id": project_id,
                    "working": working,
                    "working_at_once": limit,
                }
            raise AgentHandRefused(
                "launch_cap_reached",
                f"{working} agents work now; the limit is {limit}",
            )

        # Programs PG13b: a step's launch runs at its Program's control and a
        # helper at its parent's level (the brief says the same mode the
        # launch flags carry); every other hand at the desk's Control mode.
        mode = self._launch_mode(kind, item_id, helper_of)
        try:
            if kind == "program_step" and not helper_of:
                from .program_brief import compose as compose_program_step

                brief = compose_program_step(
                    self._db, item_id, control_mode=mode, repo_path=source.primary_path,
                    worktree=str(worktree_path), branch=spec["branch"],
                )
            elif kind == "program_step" and str(instruction or "").strip():
                # A step's helper (its reviewer): the instruction first, the
                # step as data (never the builder's brief alone).
                from .program_brief import compose_review

                brief = compose_review(self._db, item_id, str(instruction))
            else:
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
        if handoff_brief and kind == "program_step":
            # Programs PG19: the next agent of a step that was handed off
            # starts on the handoff brief (the record of where the step
            # stands), in the same worktree on the same branch.
            size = len(handoff_brief.encode("utf-8"))
            if size > AGENT_BRIEF_CAP_BYTES:
                raise AgentHandRefused("brief_over_cap", f"the handoff brief is {size} bytes; the limit is {AGENT_BRIEF_CAP_BYTES}")
            brief = {**brief, "text": handoff_brief, "bytes": size}
        if isinstance(review, Mapping):
            from ..delivery.factory_launch import agent_of_profile

            review = {
                **dict(review),
                "builder": str(review.get("builder") or agent_of_profile(profile_id)),
                "item": {
                    "kind": kind,
                    "id": item_id,
                    "title": item_title(self._db, kind, item_id),
                },
                "acceptance": list(brief.get("acceptance") or []),
            }

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
            **({"helper_of": helper_of} if helper_of else {}),
            **({"review": dict(review)} if isinstance(review, Mapping) else {}),
            # Programs: a step's Runs on engine (pi only; empty: agent.code).
            **({"engine_id": str(engine)} if engine and str(agent.get("executable") or "") == "pi" else {}),
        }
        if isinstance(review, Mapping) and str(review.get("role") or "") == "reviewer":
            # The profile's existing option slots enforce read-only process
            # mode before spawn.  The reviewer palette is carried in the
            # same review envelope for the factory credential seam.
            if str(agent.get("executable") or "") == "claude":
                request["options"] = {"permission_mode": "plan"}
            elif str(agent.get("executable") or "") == "codex":
                request["options"] = {"sandbox": "read-only"}
        if agent.get("executable") in ("claude", "codex", "pi"):
            # Conductor R3: Codex is gated like Claude Code (its -c hooks);
            # pi through its extension (pi spike #1020).
            result = self._launch_gated(launcher, request, brief["text"], principal, worktree_path, spec["name"])
        else:
            result = self._launch_ungated(launcher, request, brief["text"], principal)
        answer = self._answer(result, spec, source, brief, kind, item_id, project_id, mode)
        if review and answer.get("launch_id"):
            # Review metadata is hub state. Keep it beside the launch so the
            # review loop survives a process restart and the flight wire can
            # show the pair without a second store.
            try:
                launcher._ledger.update(str(answer["launch_id"]), review=dict(review))
            except Exception as exc:
                log.warning("review metadata not retained (%s)", exc)
        return answer

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
        queue: Optional[bool] = None,
        review_by: Optional[str] = None,
    ) -> dict[str, Any]:
        """The ``agent.hand`` operation (``agent_operations.AGENT_HAND``)."""
        return self.hand(
            principal, kind, id,
            instruction=instruction, profile=profile, project_id=project_id,
            queue=bool(queue), review_by=review_by,
        )

    # ── Claude Code and Codex: process.spawn, the gate armed for this worktree ──

    def _launch_gated(
        self, launcher: Any, request: dict[str, Any], text: str, principal: Any,
        worktree_path: Path, name: str,
    ) -> dict[str, Any]:
        prior = self._arm_gate(worktree_path, name)
        parent_operation_id = ""
        helper_of = str(request.get("helper_of") or "").strip()
        if helper_of and getattr(getattr(principal, "kind", None), "value", "") == "agent":
            # A helper is a causal child of the launch that requested it.  The
            # parent's owner decided operation supplies the signed warrant;
            # the broker checks that the launch credential is its named
            # continuation identity before approving this child.
            parent = launcher.launch_record(helper_of) or {}
            parent_operation_id = str(parent.get("operation_id") or "").strip()
            if not parent_operation_id:
                self._release_gate(worktree_path, name, prior, "the parent launch has no live operation")
                raise AgentHandRefused("helper_parent_missing", "the parent launch has no live operation")
        try:
            # The brief is held and typed once the rider registers the
            # session, so a folder-trust prompt or a slow start cannot eat it.
            result = launcher.submit_process_spawn(
                request, text, principal, after_registration=True,
                parent_operation_id=parent_operation_id,
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

    def resume_after_restart(self, principal: Any, launch_id: str) -> dict[str, Any]:
        """Betterment AG6: Resume an agent a restart stopped, in its own
        worktree and conversation (``LaunchService.resume_session``). The
        owner's press only; nothing resumes by itself."""
        from ..principals import PrincipalKind

        if getattr(principal, "kind", None) is not PrincipalKind.OWNER:
            raise ServiceError(
                "owner_required", "Only the owner resumes an agent.", context={"status": 403}
            )
        launcher = self._launch_service()
        try:
            record = launcher.resume_session(str(launch_id))
        except LaunchRefused as exc:
            raise AgentHandRefused.from_launch(exc) from exc
        return _resume_answer(record)


def _resume_answer(record: Mapping[str, Any]) -> dict[str, Any]:
    resume = record.get("resume") or {}
    return {
        "launch_id": record.get("launch_id"),
        "state": record.get("state"),
        "resume": {key: resume.get(key) for key in ("state", "at", "command", "outcome")},
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


def working_launches(launcher: Any, db: Any = None, sessions: Any = None) -> list[dict[str, Any]]:
    """Betterment AG5: the running launches that hold a "working at once"
    slot: the agent starts, works or needs the owner. A done or quiet turn,
    and a stopped launch, never block a new hand."""
    from .agent_flights import slot_holders

    live = live_launches(launcher)
    if not live:
        return []
    if db is None:
        from ..db import get_database

        db = get_database()
    return [dict(record) for record in slot_holders(db, live, sessions)]


def working_at_once() -> int:
    """The setting ``agents.working_at_once`` (default 6)."""
    from ..config import Config
    from ..config.agents import DEFAULT_WORKING_AT_ONCE

    try:
        return int(Config.load().agents.working_at_once)
    except Exception:
        return DEFAULT_WORKING_AT_ONCE


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


#: Launch states whose agent no longer runs: its worktree takes Hand again.
_STOPPED_LAUNCH_STATES = frozenset({
    "stopped_by_restart", "stopped_by_owner", "resume_failed", "complete", "ended_undelivered",
    "failed_to_register",
    # Programs PG19: a step's agent at its usage limit, handed to the next.
    "handed_off",
})


def _hand_again_of(existing: Optional[Mapping[str, Any]]) -> Optional[tuple[str, str]]:
    """``(launch_id, worktree_id)`` of the item's earlier launch when its
    agent stopped and its worktree is known; else ``None``."""
    if not existing:
        return None
    state = str(existing.get("state") or "")
    resume = existing.get("resume") or {}
    if isinstance(resume, Mapping) and resume.get("state") == "resuming":
        return None
    if state not in _STOPPED_LAUNCH_STATES and not (isinstance(resume, Mapping) and resume.get("outcome") == "failed"):
        return None
    launch_id, worktree_id = str(existing.get("launch_id") or ""), str(existing.get("worktree_id") or "")
    return (launch_id, worktree_id) if launch_id and worktree_id else None


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
    "working_at_once",
    "working_launches",
    "default_agent_hand_service",
    "resolve_project_repository",
    "worktree_spec",
    "branch_slug",
    "item_title",
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
