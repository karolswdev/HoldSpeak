"""Conductor K6: what an agent HoldSpeak launched may do, for the life of its launch.

The orchestrator's rulings on PR #903 (the owner wants the agent to do
meaningful work; egress, authority and config stay at his press):

1. **Memory recall.** A launch-bound credential reads ``memory.*`` while it
   is live (``principals.launch_reader``). What it reads passes the brief's
   People cut (``agent_brief._PeopleClassifier``): a hit, observation or page
   sentence whose source carries People content is left out.
2. **Decision proposals.** At launch the owner's press on Hand to agent
   grants the launch identity a desk delegation for ``decision.create`` only.
   The CONDUCTOR call gate admits only a ``proposed`` decision
   (``mcp/palettes.py``), so the decision waits for the owner. Every other
   desk write stays ``desk_delegation_required``; the tools that confirm on
   the owner's behalf are not in the palette. The grant is revoked when the
   credential goes.
3. **Item scope.** An item-state tool acts only on the launch's origin item
   and the items the agent created during the launch; any other id is
   refused ``not_this_launch``.
4. **The owner's records.** A desk write that edits, files, unfiles or
   deletes a record (``desk.update``, ``desk.delete``, ``desk.verb``, zone and
   KB membership, workbench, thought, meeting and schedule writes) acts only
   on what the agent created during the launch; anything else is
   ``not_this_launch``. Creating new Notes and proposed decisions stays open.
5. **Projects.** The agent ADDS to the launch's own Project (a link or a
   resource, under the launch's project grant) and removes only a resource
   it added; ``project.update``, ``unlink``, ``restore`` and
   ``archive`` are refused on every Project, and any write on another
   Project (or one naming none: create, setup, a global trigger) is
   ``not_this_launch``. Reads stay open.
"""
from __future__ import annotations

from typing import Any, Mapping, Optional

from ..logging_config import get_logger

log = get_logger("services.conductor_launch")

#: The one desk write a launch may make: a decision, always ``proposed``.
PROPOSAL_OPERATIONS: tuple[str, ...] = ("decision.create",)

#: Item-state tools and the argument that names the item.
SCOPED_ITEM_TOOLS: dict[str, str] = {
    "follow_through.complete": "card_id",
    "project.item.transition": "item_id",
    "project.item.update": "item_id",
}

NOT_THIS_LAUNCH = "not_this_launch"

_HOOK_INSTALLED = False


# ── the hub database (never a default database outside a hub) ──────────


def _hub_database() -> Any:
    from ..runtime import composition

    root = composition.installed()
    if root is None or getattr(root, "bare_root", True) or getattr(root, "db", None) is None:
        return None
    return root.db


# ── 2. the launch's decision-proposal grant ──────────────────────────────


def grant_decision_proposals(
    principal: Any, identity: str, *, ttl_seconds: float, database: Any = None,
) -> Optional[dict[str, Any]]:
    """Grant *identity* ``decision.create`` for the life of the launch.

    The owner's press on Hand to agent is the gesture: *principal* must be
    the OWNER. Returns the grant's kernel answer, or None when there is no
    hub database or no owner press (the launch runs; the agent's decision
    proposals are then refused ``desk_delegation_required``)."""
    from ..principals import PrincipalKind
    from . import desk_delegation

    if getattr(principal, "kind", None) is not PrincipalKind.OWNER:
        return None
    database = database or _hub_database()
    if database is None:
        return None
    install_revoke_hook()
    expires_at = desk_delegation._now(database) + float(ttl_seconds)
    return desk_delegation.grant(
        principal, identity, {"expires_at": expires_at},
        database=database, operations=PROPOSAL_OPERATIONS,
    )


def grant_project_additions(
    principal: Any, identity: str, project_id: str, *, ttl_seconds: float, database: Any = None,
) -> Optional[dict[str, Any]]:
    """Grant *identity* the launch's additions in its own Project (round 4):
    ``project.link``, ``project.resource.add`` and ``project.resource.remove``
    (the MCP gate lets the agent remove only a resource it added)."""
    from ..kernel.project_grant import LAUNCH_GRANT_OPERATIONS
    from ..principals import PrincipalKind
    from . import project_delegation

    if getattr(principal, "kind", None) is not PrincipalKind.OWNER or not str(project_id or "").strip():
        return None
    database = database or _hub_database()
    if database is None:
        return None
    install_revoke_hook()
    expires_at = project_delegation._now(database) + float(ttl_seconds)
    return project_delegation.grant(
        principal, identity, str(project_id), {"expires_at": expires_at},
        database=database, operations=LAUNCH_GRANT_OPERATIONS,
    )


def revoke_decision_grant(launch_id: str, identity: str, *, database: Any = None) -> bool:
    """End the launch's grants, desk and project, that are LIVE (a hook on
    the credential's revoke)."""
    from ..principals import Principal, PrincipalKind
    from . import desk_delegation, project_delegation

    database = database or _hub_database()
    if database is None:
        return False
    owner = Principal(PrincipalKind.OWNER, "conductor-launch")
    revoked = False
    if desk_delegation.live_grant(identity, database=database):
        desk_delegation.revoke(owner, identity, "credential_revoked", database=database)
        revoked = True
    if project_delegation.live_projects(identity, database=database):
        project_delegation.revoke_for_credential(owner, identity, database=database)
        revoked = True
    return revoked


def install_revoke_hook() -> None:
    """Every revoke of a launch-bound credential also ends its grant."""
    global _HOOK_INSTALLED
    from ..principals import agent_credentials

    if _HOOK_INSTALLED:
        return
    agent_credentials.launch_revoked_hooks.append(
        lambda launch_id, identity: revoke_decision_grant(launch_id, identity)
    )
    _HOOK_INSTALLED = True


# ── 1. the People cut on memory reads ────────────────────────────────────


def _classifier(db: Any) -> Any:
    from .agent_brief import _PeopleClassifier

    return _PeopleClassifier(db)


def _people_kind(kind: Any) -> bool:
    from .agent_brief import PEOPLE_KINDS

    return str(kind or "") in PEOPLE_KINDS


def cut_memory(db: Any, method: str, result: Any) -> Any:
    """The People cut over one memory read's result (a launch reader's)."""
    if not isinstance(result, Mapping):
        return result
    people = _classifier(db)
    out = dict(result)
    if method == "search":
        kept = []
        for hit in result.get("hits") or []:
            refs = [str(hit.get("source_ref") or "")] + [str(r) for r in hit.get("evidence") or []]
            if _people_kind(hit.get("kind")) or any(people.carries_people(ref) for ref in refs if ref):
                continue
            kept.append(hit)
        cut = len(result.get("hits") or []) - len(kept)
        out["hits"] = kept
        page = dict(out.get("page") or {})
        if page:
            page["count"] = len(kept)
            page["total"] = max(0, int(page.get("total") or 0) - cut)
            out["page"] = page
        out["people_cut"] = cut
        return out
    if method == "observations":
        kept = [
            row for row in result.get("observations") or []
            if not any(
                people.carries_people(str((ev or {}).get("ref") or ""))
                for ev in row.get("evidence") or [] if (ev or {}).get("ref")
            )
        ]
        out["observations"] = kept
        out["count"] = len(kept)
        return out
    if method == "page":
        out["page"] = _cut_page(people, result.get("page"))
        return out
    if method == "standing_pages":
        pages = [_cut_page(people, page) for page in result.get("pages") or []]
        out["pages"] = [page for page in pages if page]
        return out
    return out


def _cut_page(people: Any, page: Any) -> Any:
    if not isinstance(page, Mapping):
        return page
    sentences = [s for s in page.get("sentences") or [] if people.sentence(s)]
    if not sentences:
        return None
    cut = dict(page)
    cut["sentences"] = sentences
    if "answer" in cut:
        cut["answer"] = "\n".join(f"- {s.get('text')}" for s in sentences)
    if "sources" in cut:
        refs = list(dict.fromkeys(r.get("ref") for s in sentences for r in s.get("refs") or []))
        cut["sources"] = [src for src in cut.get("sources") or [] if src.get("ref") in refs]
    return cut


# ── 3. item scope ────────────────────────────────────────────────────────


def _ref_id(value: Any) -> str:
    """``kind:id`` -> ``id``; a bare id stays."""
    text = str(value or "").strip()
    return text.split(":", 1)[1] if ":" in text else text


#: The owner's desk records (ruling on #903, round 3): a launched agent edits
#: or deletes only the desk objects it created during the launch. Each tool
#: names the argument(s) that point at the record it changes.
_OWN_OBJECT_ARGS: dict[str, tuple[str, ...]] = {
    "desk.update": ("id",),
    "desk.delete": ("id",),
    "zone.file": ("primitive_id",),
    "zone.unfile": ("primitive_id",),
    "kb.add_member": ("ref",),
    "kb.remove_member": ("ref",),
    "workbench.add_item": ("workbench_id",),
    "workbench.update": ("workbench_id",),
    "workbench.delete": ("workbench_id",),
    "workbench.update_item": ("workbench_id",),
    "workbench.delete_item": ("workbench_id",),
    "meeting.delete": ("meeting_id",),
    "scheduled_recording.update": ("schedule_id",),
    "scheduled_recording.delete": ("schedule_id",),
    "scheduled_recording.cancel_armed": ("schedule_id",),
    "thought.adopt_note": ("note_id",),
}
#: Every thought tool that changes a thought names it by ``thought_id``.
_THOUGHT_WRITES = frozenset({
    "thought.refine", "thought.reconcile", "thought.stop_refinement", "thought.attach_context",
    "thought.detach_context", "thought.refresh_context", "thought.answer_review",
    "thought.accept_review", "thought.reject_review", "thought.answer_and_continue",
    "thought.update_working", "thought.complete", "thought.resume",
})
#: desk.verb server verbs that make something new or only run: not scoped.
_VERB_FREE = frozenset({"desk.create", "workbench.run"})


def _owned_ids(name: str, arguments: Mapping[str, Any]) -> Optional[list[str]]:
    """The record ids a desk write names; None when the tool is not scoped."""
    if name == "desk.verb":
        verb = str(arguments.get("verb_id") or "")
        if verb in _VERB_FREE:
            return None
        inner = arguments.get("arguments") if isinstance(arguments.get("arguments"), Mapping) else {}
        ids = _owned_ids(verb, inner)
        return ids if ids is not None else [""]  # any other verb: refused unless named and own
    if name in _THOUGHT_WRITES:
        return [_ref_id(arguments.get("thought_id"))]
    keys = _OWN_OBJECT_ARGS.get(name)
    if keys is None:
        return None
    return [_ref_id(arguments.get(key)) for key in keys]


#: Project reads and watch checks: open on every Project.
_PROJECT_FREE = frozenset({
    "project.list", "project.get", "project.get_room", "project.get_delta",
    "project.list_updates", "project.item.list", "project.resource.list",
    "project.get_steward_run", "project.suggested_sources",
    "project.watch.inspect", "project.watch.test", "project.watch.evaluate",
})
#: Never, on any Project (round 4 ruling on #903): the owner's metadata,
#: his links and his lifecycle.
_PROJECT_NEVER = frozenset({
    "project.update", "project.unlink", "project.restore", "project.archive",
})
#: Writes named by an id the agent must have made (its draft, its run).
_PROJECT_BY_OWN_ID: dict[str, str] = {
    "project.update_draft": "update_id",
    "project.publish_update": "update_id",
    "project.stop_steward": "run_id",
}


def _resource_key(project_id: Any, resource_ref: Any) -> str:
    return f"resource:{project_id}:{resource_ref}"


def _project_refused(launch_id: str, name: str, args: Mapping[str, Any]) -> Optional[str]:
    """A project.* write: only on the launch's own Project, and there only
    adding (links, resources, items, drafts) or changing what the agent
    made. Reads stay open."""
    from .. import coder_factory
    from ..principals import agent_credentials

    if not name.startswith("project.") or name in _PROJECT_FREE:
        return None
    named = str(args.get("project_id") or "").strip()
    if name in _PROJECT_NEVER:
        return named or name
    if name in _PROJECT_BY_OWN_ID:
        own = str(args.get(_PROJECT_BY_OWN_ID[name]) or "").strip()
        return None if own and agent_credentials.created_by(launch_id, own) else (own or name)
    credential = agent_credentials.launch_credential(coder_factory.launch_identity(launch_id))
    project = credential.project_id if credential is not None else None
    if not named or project is None or named != project:
        # Another Project, or a write that names none (create, setup, a
        # steward trigger over every Project).
        return named or name
    if name == "project.resource.remove":
        key = _resource_key(named, args.get("resource_ref"))
        return None if agent_credentials.created_by(launch_id, key) else str(args.get("resource_ref") or name)
    return None


def item_refused(launch_id: str, name: str, arguments: Any) -> Optional[str]:
    """The id a scoped tool names, when it is not this launch's to change."""
    from ..principals import agent_credentials

    from ..mcp.palettes import CONDUCTOR, resolve_palette

    if name not in resolve_palette(CONDUCTOR):
        return None  # the palette refuses it first (MCP-005)
    args = arguments if isinstance(arguments, Mapping) else {}
    project_refusal = _project_refused(launch_id, name, args)
    if project_refusal is not None:
        return project_refusal
    key = SCOPED_ITEM_TOOLS.get(name)
    if key is not None:
        item_id = str(args.get(key) or "").strip()
        return None if agent_credentials.in_scope(launch_id, item_id) else (item_id or "(none)")
    ids = _owned_ids(name, args)
    if ids is None:
        return None
    for object_id in ids:
        if not object_id or not agent_credentials.created_by(launch_id, object_id):
            return object_id or "(none)"
    return None


_CREATED_KEYS = ("id", "thought_id", "schedule_id", "workbench_id", "note_id", "update_id", "run_id")
_CREATED_NESTS = ("item", "note", "workbench", "thought", "schedule", "decision", "primitive", "update", "run")
_CREATING_TOOLS = frozenset({
    "door.add_item", "project.item.create", "desk.create", "desk.verb", "workbench.create",
    "thought.create", "scheduled_recording.create", "project.draft_update", "project.run_steward",
})


def record_created(launch_id: str, name: str, result: Any, arguments: Any = None) -> None:
    """What the agent created joins the launch's scope, as its own."""
    from ..principals import agent_credentials

    args = arguments if isinstance(arguments, Mapping) else {}
    if name == "project.resource.add":
        agent_credentials.scope_add(launch_id, _resource_key(args.get("project_id"), args.get("resource_ref")))
        return
    if name == "project.link":
        agent_credentials.scope_add(launch_id, f"link:{args.get('project_id')}:{args.get('meeting_id')}")
        return
    if name not in _CREATING_TOOLS or not isinstance(result, Mapping):
        return
    for holder in [result, *(result.get(n) for n in _CREATED_NESTS)]:
        if not isinstance(holder, Mapping):
            continue
        for key in _CREATED_KEYS:
            if holder.get(key):
                agent_credentials.scope_add(launch_id, _ref_id(holder[key]))


__all__ = [
    "NOT_THIS_LAUNCH",
    "PROPOSAL_OPERATIONS",
    "SCOPED_ITEM_TOOLS",
    "cut_memory",
    "grant_decision_proposals",
    "install_revoke_hook",
    "item_refused",
    "record_created",
    "revoke_decision_grant",
]
