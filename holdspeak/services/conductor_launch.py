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


# ── the shared boundary: launch ownership by canonical ref ──────────────
#
# Astra round 1 on #903: the launch rules hold at the service and kernel
# boundary, not only on MCP, and ownership is a canonical ``kind:id`` ref
# recorded where the record is INSERTED (never a bare id, never a replay).

LAUNCH_IDENTITY_PREFIX = "agent:launch:"


def launch_id_of(principal: Any) -> Optional[str]:
    """The launch id of a launch principal (live or not), else None."""
    from ..principals import PrincipalKind

    if getattr(principal, "kind", None) is not PrincipalKind.AGENT:
        return None
    identity = str(getattr(principal, "identity", "") or "")
    if not identity.startswith(LAUNCH_IDENTITY_PREFIX):
        return None
    return identity[len(LAUNCH_IDENTITY_PREFIX):] or None


def refuse(ref: str, detail: str = "") -> None:
    from .errors import ServiceError

    raise ServiceError(
        NOT_THIS_LAUNCH,
        detail or f"{ref} is not this launch's to change",
        context={"status": 403, "ref": ref, "item_id": ref},
    )


def require_new(principal: Any, ref: str, exists: Any) -> None:
    """Launch creation is INSERT-ONLY: an existing id (live or deleted) is
    refused before any write."""
    if launch_id_of(principal) is not None and exists():
        refuse(ref, f"{ref} already exists; a launch creates only new records")


def require_own(principal: Any, *refs: str) -> None:
    """A launch changes only records it created during the launch."""
    from ..principals import agent_credentials

    launch = launch_id_of(principal)
    if launch is None:
        return
    for ref in refs:
        if not agent_credentials.created_by(launch, ref):
            refuse(ref)


def record_own(principal: Any, ref: str) -> None:
    from ..principals import agent_credentials

    launch = launch_id_of(principal)
    if launch is not None and ref:
        agent_credentials.scope_add(launch, ref)


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


# ── 3. every mutating tool's launch scope (the audit; Astra round 1 #7) ──
#
# Each tool of the CONDUCTOR palette that is not a read (``tools.is_read_tool``)
# has ONE rule here. A tool with no rule is refused at the call and fails the
# fence (``test_every_conductor_tool_has_a_launch_rule``): nothing falls
# through as unrestricted. The rules:
#
# * ``create``  -- makes a NEW record; the ref it returns is recorded as the
#   launch's own. Idempotency keys are namespaced per launch, so a replay of
#   the owner's command never answers the agent (and never grants ownership).
# * ``desk``    -- a desk write: held in ``PrimitiveService`` (insert-only
#   creation, own-only edits), the boundary every transport reaches.
# * ``own``     -- changes an existing record: only one the launch created.
# * ``item``    -- the launch's origin item, or an item it created.
# * ``project`` -- the launch's own Project, adding only; held in
#   ``ProjectService`` and the kernel's project grant as well.
# * ``never``   -- the owner's state, a global run, or a target a launch can
#   never own: not offered (out of the palette) and refused at the call.
# * ``composer``-- a model answer composed over desk records: the People cut
#   cannot see a paraphrase, so it is not offered to a cloud agent.

CREATE, DESK, OWN, ITEM, PROJECT, NEVER, COMPOSER = (
    "create", "desk", "own", "item", "project", "never", "composer",
)

#: tool -> (rule, ref kind, argument naming the target / the created id).
LAUNCH_RULES: dict[str, tuple[str, str, str]] = {
    # create
    "door.add_item": (CREATE, "action", "id"),
    "thought.create": (CREATE, "thought", "id"),
    "workbench.create": (CREATE, "workbench", "id"),
    "scheduled_recording.create": (CREATE, "schedule", "id"),
    "ask.keep": (CREATE, "artifact", "id"),
    "channel.prepare": (CREATE, "send", "id"),
    # desk (PrimitiveService)
    "desk.create": (DESK, "", ""),
    "desk.update": (DESK, "", ""),
    "desk.delete": (DESK, "", ""),
    "desk.verb": (DESK, "", ""),
    "zone.file": (DESK, "", ""),
    "zone.unfile": (DESK, "", ""),
    "kb.add_member": (DESK, "", ""),
    "kb.remove_member": (DESK, "", ""),
    "decision.supersede": (DESK, "", ""),
    # own
    "thought.adopt_note": (OWN, "note", "note_id"),
    "thought.accept_review": (OWN, "thought", "thought_id"),
    "thought.answer_review": (OWN, "thought", "thought_id"),
    "thought.attach_context": (OWN, "thought", "thought_id"),
    "thought.complete": (OWN, "thought", "thought_id"),
    "thought.detach_context": (OWN, "thought", "thought_id"),
    "thought.reconcile": (OWN, "thought", "thought_id"),
    "thought.refresh_context": (OWN, "thought", "thought_id"),
    "thought.reject_review": (OWN, "thought", "thought_id"),
    "thought.resume": (OWN, "thought", "thought_id"),
    "thought.stop_refinement": (OWN, "thought", "thought_id"),
    "thought.update_working": (OWN, "thought", "thought_id"),
    "workbench.add_item": (OWN, "workbench", "workbench_id"),
    "workbench.update": (OWN, "workbench", "workbench_id"),
    "workbench.delete": (OWN, "workbench", "workbench_id"),
    "workbench.update_item": (OWN, "workbench", "workbench_id"),
    "workbench.delete_item": (OWN, "workbench", "workbench_id"),
    "scheduled_recording.update": (OWN, "schedule", "schedule_id"),
    "scheduled_recording.delete": (OWN, "schedule", "schedule_id"),
    "scheduled_recording.cancel_armed": (OWN, "schedule", "schedule_id"),
    # item
    "follow_through.complete": (ITEM, "action", "card_id"),
    "project.item.update": (ITEM, "project_item", "item_id"),
    "project.item.transition": (ITEM, "project_item", "item_id"),
    # project
    "project.item.create": (PROJECT, "project_item", "id"),
    "project.link": (PROJECT, "", ""),
    "project.resource.add": (PROJECT, "", ""),
    "project.resource.remove": (PROJECT, "", ""),
    "project.open_review": (PROJECT, "", ""),
    # never: the owner's records and state, or a global run
    "thread.set_status": (NEVER, "thread", "thread_id"),
    "interview.change_section": (NEVER, "thread", "thread_id"),
    "interview.record_fact": (NEVER, "thread", "thread_id"),
    "cadence.set_status": (NEVER, "loop", "loop_id"),
    "cadence.snooze": (NEVER, "loop", "loop_id"),
    "cadence.apply_closeout": (NEVER, "", ""),
    "cadence.closeout": (NEVER, "", ""),
    "cadence.run_now": (NEVER, "", ""),
    "follow_through.commit_decision": (NEVER, "decision", "decision_id"),
    "meeting.delete": (NEVER, "meeting", "meeting_id"),
    "meeting.start_capture": (NEVER, "", ""),
    "meeting.stop_capture": (NEVER, "meeting", "meeting_id"),
    "nudge.dismiss": (NEVER, "", ""),
    "plugin_job.cancel": (NEVER, "", ""),
    "plugin_job.retry": (NEVER, "", ""),
    "reaction.process": (NEVER, "", ""),
    "heartbeat.run_now": (NEVER, "", ""),
    "heartbeat.notify_test": (NEVER, "", ""),
    "concierge.propose": (NEVER, "", ""),
    "connection.recheck": (NEVER, "", ""),
    "watch.refresh": (NEVER, "", ""),
    "project.watch.test": (NEVER, "", ""),
    "practice_recipe.compile": (NEVER, "", ""),
    "sequence.cancel": (NEVER, "", ""),
    "workflow.cancel": (NEVER, "", ""),
    "ask.cancel": (NEVER, "", ""),
    "project.create": (NEVER, "", ""),
    "project.update": (NEVER, "", ""),
    "project.unlink": (NEVER, "", ""),
    "project.restore": (NEVER, "", ""),
    "project.dismiss_suggested_source": (NEVER, "", ""),
    "project.run_steward": (NEVER, "", ""),
    "project.stop_steward": (NEVER, "", ""),
    "project.steward.trigger": (NEVER, "", ""),
    "project.publish_update": (NEVER, "", ""),
    "project.update_draft": (NEVER, "", ""),
    "project.setup.start": (NEVER, "", ""),
    "project.setup.resume": (NEVER, "", ""),
    "project.setup.answer": (NEVER, "", ""),
    "project.setup.suggest": (NEVER, "", ""),
    "project.setup.select_proposal": (NEVER, "", ""),
    "project.setup.deselect_proposal": (NEVER, "", ""),
    "project.setup.test_proposal": (NEVER, "", ""),
    "project.setup.clarify_jira_scope": (NEVER, "", ""),
    "project.setup.clarify_repo_scope": (NEVER, "", ""),
    # composer: model text over desk records
    "ask.run": (COMPOSER, "", ""),
    "recipe.run": (COMPOSER, "", ""),
    "recipe.chat": (COMPOSER, "", ""),
    "workflow.run": (COMPOSER, "", ""),
    "sequence.run": (COMPOSER, "", ""),
    "workbench.run": (COMPOSER, "", ""),
    "monday_brief.generate": (COMPOSER, "", ""),
    "cadence.brief": (COMPOSER, "", ""),
    "meeting.run_intelligence": (COMPOSER, "", ""),
    "thought.refine": (COMPOSER, "", ""),
    "thought.answer_and_continue": (COMPOSER, "", ""),
    "interview.suggest": (COMPOSER, "", ""),
    "project.draft_update": (COMPOSER, "", ""),
}

#: Not offered to a launch at all (the palette leaves them out).
NOT_OFFERED: frozenset[str] = frozenset(n for n, (rule, _k, _a) in LAUNCH_RULES.items() if rule in (NEVER, COMPOSER))

#: Kept for callers of the round-2 name.
SCOPED_ITEM_TOOLS: dict[str, str] = {n: a for n, (rule, _k, a) in LAUNCH_RULES.items() if rule == ITEM}

#: Idempotency keys a launch's call carries: namespaced per launch.
_IDEMPOTENCY_KEYS = ("command_id", "request_id")

#: desk.verb server verbs, and the tool each one is.
_VERB_TOOLS = {"desk.create": "desk.create", "desk.update": "desk.update",
               "desk.delete": "desk.delete", "workbench.add_item": "workbench.add_item",
               "workbench.run": "workbench.run"}


def _ref_id(value: Any) -> str:
    """``kind:id`` -> ``id``; a bare id stays."""
    text = str(value or "").strip()
    return text.split(":", 1)[1] if ":" in text else text


_DESK_KINDS = {"notes": "note", "decisions": "decision", "kbs": "kb", "directories": "directory",
               "workflows": "workflow", "chains": "chain"}


def _qualified(value: Any) -> str:
    text = str(value or "").strip()
    kind, sep, rest = text.partition(":")
    return f"{kind.strip().lower()}:{rest.strip()}" if sep else f"?:{text}"


def _desk_targets(name: str, args: Mapping[str, Any]) -> list[str]:
    """The existing records a desk write changes, as canonical refs."""
    if name in ("desk.update", "desk.delete"):
        return [f"{_DESK_KINDS.get(str(args.get('kind') or ''), str(args.get('kind') or '?'))}:{args.get('id') or ''}"]
    if name in ("zone.file", "zone.unfile"):
        return [f"directory:{args.get('directory_id') or ''}", _qualified(args.get("primitive_id"))]
    if name in ("kb.add_member", "kb.remove_member"):
        return [f"kb:{args.get('kb_id') or ''}"]
    if name == "decision.supersede":
        return [f"decision:{args.get('decision_id') or ''}"]
    return []  # desk.create: insert-only, held in PrimitiveService


def _launch_project(launch_id: str) -> Optional[str]:
    from .. import coder_factory
    from ..principals import agent_credentials

    credential = agent_credentials.launch_credential(coder_factory.launch_identity(launch_id))
    return credential.project_id if credential is not None else None


def gate_call(name: str, arguments: Any, principal: Any) -> Any:
    """The launch rule of one tool call, BEFORE it runs (``tools.dispatch``).

    Returns the arguments to dispatch (idempotency keys namespaced), or
    raises ``not_this_launch``. Not a launch: the arguments, untouched."""
    from ..mcp.tools import is_read_tool

    launch = launch_id_of(principal)
    if launch is None:
        return arguments
    args = dict(arguments) if isinstance(arguments, Mapping) else {}
    if name == "desk.verb":
        verb = str(args.get("verb_id") or "")
        inner_tool = _VERB_TOOLS.get(verb)
        if inner_tool is None:
            refuse(verb or name, f"desk.verb {verb!r} is not open to a launch")
        if inner_tool != "desk.verb":
            inner = args.get("arguments") if isinstance(args.get("arguments"), Mapping) else {}
            args["arguments"] = gate_call(inner_tool, inner, principal)
        return args
    rule = LAUNCH_RULES.get(name)
    if rule is None:
        if is_read_tool(name):
            return args
        refuse(name, f"{name} has no launch rule; a launch may not call it")
    if rule[0] == DESK:
        # Held in PrimitiveService too; named here first, so the answer is
        # the launch rule, never a later kernel code.
        require_own(principal, *_desk_targets(name, args))
    kind, key = rule[1], rule[2]
    for idem in _IDEMPOTENCY_KEYS:
        if args.get(idem):
            args[idem] = f"{launch}:{args[idem]}"
    if rule[0] in (NEVER, COMPOSER):
        refuse(f"{kind}:{args.get(key)}" if kind and key and args.get(key) else name,
               f"{name} is not open to a launch")
    if rule[0] == OWN:
        require_own(principal, f"{kind}:{_ref_id(args.get(key))}")
    elif rule[0] == ITEM:
        from ..principals import agent_credentials

        ref = f"{kind}:{_ref_id(args.get(key))}"
        if not agent_credentials.in_scope(launch, ref):
            refuse(ref)
    if rule[0] == PROJECT or rule[1] == "project_item":
        named = str(args.get("project_id") or "").strip()
        project = _launch_project(launch)
        if name in ("project.item.update", "project.item.transition", "project.item.create",
                    "project.link", "project.resource.add", "project.resource.remove", "project.open_review"):
            if not named or project is None or named != project:
                refuse(f"project:{named or '(none)'}", "a launch adds only to its own Project")
    return args


def after_call(name: str, arguments: Any, result: Any, principal: Any) -> None:
    """Record what a ``create`` tool made as the launch's own (desk and
    Project records are recorded where they are inserted)."""
    launch = launch_id_of(principal)
    rule = LAUNCH_RULES.get(name)
    if launch is None or rule is None or not isinstance(result, Mapping):
        return
    if rule[0] not in (CREATE, PROJECT) or not rule[1]:
        return
    kind = rule[1]
    for holder in (result, result.get("item"), result.get(kind), result.get("thought"),
                   result.get("workbench"), result.get("schedule"), result.get("send")):
        if isinstance(holder, Mapping):
            for key in ("id", f"{kind}_id", "thought_id", "schedule_id", "workbench_id", "send_id"):
                if holder.get(key):
                    record_own(principal, f"{kind}:{_ref_id(holder[key])}")
                    return


# ── 4. the People cut on every read a launch reaches ─────────────────────


def _people_text(text: str) -> str:
    from .agent_brief import _people_section_cut

    return _people_section_cut(text)


def cut_people_everywhere(value: Any) -> Any:
    """The brief's People classification over ANY read payload: a People
    record is dropped, a People-marked line or a Brief People section is cut
    from every string (JSON carried inside a string included)."""
    from .agent_brief import PEOPLE_KINDS, _PEOPLE_MARKERS

    if isinstance(value, str):
        stripped = value.lstrip()
        if stripped[:1] in ("{", "["):
            import json

            try:
                parsed = json.loads(value)
            except ValueError:
                return _people_text(value)
            return json.dumps(cut_people_everywhere(parsed), default=str)
        return _people_text(value)
    if isinstance(value, Mapping):
        kind = str(value.get("kind") or "")
        refs = [str(value.get(k) or "") for k in ("ref", "source_ref", "uri", "resource_ref")]
        if kind in PEOPLE_KINDS or any(
            r.startswith(_PEOPLE_MARKERS) or r.startswith("holdspeak://people/") for r in refs if r
        ):
            return _DROP
        out = {}
        for key, item in value.items():
            kept = cut_people_everywhere(item)
            if kept is not _DROP:
                out[key] = kept
        return out
    if isinstance(value, (list, tuple)):
        return [kept for kept in (cut_people_everywhere(v) for v in value) if kept is not _DROP]
    return value


def cut_for(principal: Any, value: Any) -> Any:
    """What a launch principal reads, after the People cut; others: as is."""
    if launch_id_of(principal) is None:
        return value
    kept = cut_people_everywhere(value)
    return None if kept is _DROP else kept


class _Drop:
    def __repr__(self) -> str:  # pragma: no cover
        return "<dropped People record>"


_DROP = _Drop()


__all__ = [
    "LAUNCH_RULES",
    "NOT_OFFERED",
    "after_call",
    "cut_people_everywhere",
    "gate_call",
    "NOT_THIS_LAUNCH",
    "PROPOSAL_OPERATIONS",
    "SCOPED_ITEM_TOOLS",
    "cut_memory",
    "grant_decision_proposals",
    "install_revoke_hook",
    "revoke_decision_grant",
]
