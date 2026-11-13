"""People's verbs on the one declared contract (2026-11-08), beside ``holdspeak/operations.py``
(which imports it into ``DESCRIPTORS``), as ``meeting_operations.py`` is. ``web/routes/people.py``
produces the routes and ``mcp/families/declared.py`` the tools from these rows.

One verb, two faces (owner ruling 2026-10-06: agents READ People over MCP; every write is the
owner's, ``owner_only``): ``web_call`` (HTTP) answers the owner's whole view, as the routes did;
``call`` (MCP) passes the People MCP access gate (``HOLDSPEAK_MCP_PEOPLE_ACCESS``) and answers the
same shape cut to shared intent (``mcp/families/people.py`` ``_mcp_readable``). The arguments
schema is any object: the service validates, as it did behind the hand-written routes.
"""
from __future__ import annotations

from holdspeak.held_arguments import held_arguments, text, hidden, named, word_count, normalizer

from typing import Any, Callable, Mapping, Optional

from holdspeak.operations import _CONTRACT_REFUSALS, OperationDescriptor

Call = Callable[[Any, Any, dict[str, Any]], Any]

_PRINCIPAL = "derived by the transport (HTTP auth middleware; MCP auth resolver); the People service checks it"
_REFUSALS = _CONTRACT_REFUSALS + ("owner_required", "people_owner_required", "people_<kind>_not_found",
                                  "people_store_unavailable", "people_store_<readiness>", "people_store_busy",
                                  "people_store_write_failed", "people_mcp_access_disabled",
                                  "people_mcp_write_required", "people_mcp_private_record_refused")
_ID = {"type": "string", "minLength": 1}
_P = "/api/people"
_R = _P + "/relationships/{relationship_id}"
_C = _P + "/commitments/{commitment_id}"


def _family() -> Any:
    from holdspeak.mcp.families import people  # it imports this contract: read at call time
    return people


def _readable(record: Any) -> bool:
    return isinstance(record, dict) and _family()._mcp_readable(record)


def _service(name: str, build: Callable[[], Any]) -> Any:
    """The hub's live instance of *name* (its bus), else *build* over the database."""
    from holdspeak.db import get_database, get_observer
    from holdspeak.runtime.composition import service
    return service(name, lambda: build(get_database(), get_observer()))


def workbenches() -> Any:
    from holdspeak.services.workbench_service import WorkbenchService
    return _service("workbench_service", lambda db, obs: WorkbenchService(db, observer=obs))


def _projects() -> Any:
    from holdspeak.services.project_service import ProjectService
    return _service("project_service", lambda db, obs: ProjectService(db, observer=obs))


def _link_project(service: Any, principal: Any, args: dict[str, Any]) -> Any:
    from holdspeak.services.errors import NotFound
    from holdspeak.services.people_service import PeopleServiceError

    try:
        _projects().get_project(principal, str(args.get("project_id") or ""))
    except NotFound as exc:
        raise PeopleServiceError("people_project_not_found") from exc
    return {"relationship": service.link_project(principal, args.get("relationship_id"), args.get("project_id"))}


def _send_to_workbench(service: Any, principal: Any, args: dict[str, Any]) -> Any:
    """One commitment becomes one workbench item, grounded in the person's projects; sent once."""
    from holdspeak.services.errors import NotFound
    from holdspeak.services.people_service import PeopleServiceError

    commitment_id, workbench_id = str(args.get("commitment_id") or ""), str(args.get("workbench_id") or "").strip()
    commitment = service.get_commitment(principal, commitment_id)
    if not workbench_id:
        raise PeopleServiceError("people_workbench_required")
    wb, rooms, grounding = workbenches(), _projects(), []
    try:
        wb.get_workbench(principal, workbench_id)
    except NotFound as exc:
        raise PeopleServiceError("people_workbench_not_found") from exc
    for link in commitment.get("execution_links") or []:
        if isinstance(link, dict) and link.get("workbench_id") == workbench_id:
            try:
                return {"commitment": commitment, "created": False,
                        "item": wb.get_item(principal, workbench_id, str(link.get("item_id") or ""))}
            except NotFound:
                pass
    text = str(commitment.get("body") or "").strip()
    for project_id in service.get_relationship(principal, str(commitment.get("relationship_id") or "")).get(
            "project_refs") or []:
        try:
            project = rooms.get_project(principal, str(project_id))
            resources = rooms.list_resources(principal, str(project_id))
        except NotFound:
            continue
        grounding.append({key: project.get(key) for key in ("id", "name", "description", "keywords", "context")}
                         | {"resources": [resource.get("resource_ref") for resource in resources]})
    item = wb.add_item(
        principal, workbench_id, title=text,
        body=("Complete this relationship follow-through item. Return a concrete deliverable "
              "and a concise completion summary.\n\nCommitment:\n" + text),
        grounding={"people_commitment": text, "projects": grounding},
        context={"source": "people_commitment", "people_commitment_id": commitment_id,
                 "relationship_id": commitment.get("relationship_id"),
                 "project_ids": [project.get("id") for project in grounding]})
    try:
        linked = service.attach_execution(principal, commitment_id, workbench_id=workbench_id, item_id=str(item["id"]))
    except Exception:
        wb.delete_item(principal, workbench_id, str(item["id"]))
        raise
    return {"commitment": linked, "item": item, "created": True}


def _satisfy(service: Any, principal: Any, args: dict[str, Any]) -> Any:
    """Done, with each linked workbench item as its evidence."""
    from holdspeak.services.errors import NotFound

    commitment_id = str(args.get("commitment_id") or "")
    commitment, wb, evidence = service.get_commitment(principal, commitment_id), workbenches(), []
    for link in commitment.get("execution_links") or []:
        if not isinstance(link, dict) or link.get("kind") != "workbench_item":
            continue
        try:
            item = wb.get_item(principal, str(link.get("workbench_id") or ""), str(link.get("item_id") or ""))
        except NotFound:
            continue
        evidence.append({"kind": "workbench_item", "workbench_id": item["workbench_id"], "item_id": item["id"],
                         "status": item["status"], "artifact_id": item.get("result_artifact_id"),
                         "completed_at": item.get("completed_at")})
    return {"commitment": service.satisfy_commitment(
        principal, commitment_id, rationale=str(args.get("rationale") or ""), evidence=evidence)}


def _mcp(call: Call, *, write: bool, shared: bool = False, after: Optional[Callable[[Any], Any]] = None) -> Call:
    """The MCP face: the access gate, a shared-intent commitment only (``shared``), the call, the cut."""

    def gated(service: Any, principal: Any, args: dict[str, Any]) -> Any:
        _family()._require_access(write=write)
        if shared:  # people.commitment.transition's rule
            _family()._require_shared(service.get_commitment(principal, str(args.get("commitment_id") or "")))
        result = call(service, principal, args)
        return after(result) if after is not None else result

    return gated


def _op(name: str, method: str, http: tuple[str, str], handler: str, call: Call, description: str, *,
        write: bool = True, status: int = 200, properties: Optional[Mapping[str, Any]] = None,
        required: tuple[str, ...] = (), authority: str = "work", mcp: Optional[Call] = None, facts: Optional[Mapping[str, Any]] = None) -> OperationDescriptor:
    """One verb; its tool requires the path's ids and ``required``. ``mcp``: the MCP face, else ``call`` gated."""
    ids = [part[1:-1] for part in http[1].split("/") if part.startswith("{")]
    tool = {**dict(facts or {}), "type": "object", "properties": {**{key: _ID for key in ids}, **dict(properties or {})},
            "required": ids + list(required), "additionalProperties": False}
    return OperationDescriptor(
        name=name, version=1, description=description, args_schema={"type": "object"}, principal=_PRINCIPAL,
        effect="write" if write else "read", result="the PeopleService answer", refusals=_REFUSALS,
        completion="synchronous; a write is one desk_changed frame (kind person) on the hub bus",
        exposure=(f"http:{http[0]} {http[1]}", f"mcp:{name}"), service="people_service", method=method,
        owner_only=write, call=mcp or _mcp(call, write=write), web_call=call, http=http, http_status=status,
        handler=handler, tool_schema=tool, authority=authority,
        # A read stays MCP and HTTP only (thread_modes._MCP_ONLY): a thread
        # reads a person through people.relationship.get, so no palette grows.
        thread="effect_proposal" if write else "evidence_read",
    )


def _one_on_ones(service: Any, principal: Any, args: dict[str, Any]) -> Any:
    return {"one_on_ones": service.list_one_on_ones(principal, args.get("relationship_id"))}


def _shared_sessions(answer: dict[str, Any]) -> dict[str, Any]:
    """The shared-intent 1:1s with their shared agenda (``people.relationship.get``'s cut)."""
    return {"one_on_ones": [{**_family()._shared_session(s), "agenda": [i for i in s.get("agenda") or [] if _readable(i)]}
                            for s in answer["one_on_ones"] if _readable(s)]}


def _notes(service: Any, principal: Any, args: dict[str, Any]) -> Any:
    return {"notes": service.list_notes(principal, args.get("relationship_id"))}


def _owed(service: Any, principal: Any, args: dict[str, Any]) -> Any:
    payload = {key: value for key, value in args.items() if key != "relationship_id"}
    return {"commitment": service.create_owed_to_you(principal, args.get("relationship_id"), payload)}


def _agenda(service: Any, principal: Any, args: dict[str, Any]) -> Any:
    return {"agenda_item": service.transition_agenda_item(principal, args.get("item_id"), {"to": args.get("to")})}


def _add_suggestion(service: Any, principal: Any, args: dict[str, Any]) -> Any:
    from holdspeak.db import get_database
    from holdspeak.runtime.composition import db_or

    kind = args.get("relationship_kind")
    return {"relationship": service.add_suggestion(principal, str(args.get("key") or ""), db=db_or(get_database),
                                                   relationship_kind=str(kind) if kind else None)}


def _words(*keys: str) -> Callable[[dict[str, Any]], list[str]]:
    return lambda a: [str(a.get(key) or "") for key in keys]


_SERIES_LINK, _SERIES_KEY, _ALIAS_KEY = _words("uid", "source_id", "label"), _words("uid", "source_id"), _words("alias")


def _wrapped(call: Call) -> Call:
    """The HTTP answer names the relationship; the MCP answer is the relationship (both as before)."""
    return lambda s, p, a: {"relationship": call(s, p, a)}


_SERIES = {"uid": {**_ID, "description": "Calendar event UID (series-level)."},
           "source_id": {**_ID, "description": "Calendar source identifier."}}
_ALIAS = {"alias": {**_ID, "description": "The exact owner string (from action items) that names this person."}}
_CAL, _ALIASES = _R + "/calendar-links", _R + "/owner-aliases"
#: (name, method and handler, HTTP, MCP call, description, tool properties, required, authority)
_LINKS = (
    ("people.calendar.link", "link_calendar_series", ("POST", _CAL),
     lambda s, p, a: s.link_calendar_series(p, a.get("relationship_id"), *_SERIES_LINK(a)),
     "Link a recurring calendar series to a Person. A series another Person holds is refused "
     "(series_already_linked).", {**_SERIES, "label": {"type": "string"}}, ("uid", "source_id"), "work"),
    ("people.calendar.unlink", "unlink_calendar_series", ("DELETE", _CAL),
     lambda s, p, a: s.unlink_calendar_series(p, a.get("relationship_id"), *_SERIES_KEY(a)),
     "Unlink a calendar series from a Person.", _SERIES, ("uid", "source_id"), "work"),
    ("people.owner_alias.link", "link_owner_alias", ("POST", _ALIASES),
     lambda s, p, a: s.link_owner_alias(p, a.get("relationship_id"), *_ALIAS_KEY(a)),
     "Link an owner string to a Person. An alias another Person holds is refused (owner_alias_taken); "
     "Me, Remote and you are reserved.", _ALIAS, ("alias",), "authority"),
    ("people.owner_alias.unlink", "unlink_owner_alias", ("DELETE", _ALIASES),
     lambda s, p, a: s.unlink_owner_alias(p, a.get("relationship_id"), *_ALIAS_KEY(a)),
     "Unlink an owner string from a Person.", _ALIAS, ("alias",), "authority"),
)
PEOPLE_OPERATIONS: tuple[OperationDescriptor, ...] = (
    _op("people.setup", "setup", ("POST", _P + "/setup"), "setup", lambda s, p, a: s.setup(p),
        "Create the encrypted People store (the one deliberate setup press).", authority="config"),
    _op("people.suggestion.add", "add_suggestion", ("POST", _P + "/suggestions/add"), "add_suggestion",
        _add_suggestion, "Add one suggested name (people.suggestions) as a Person.", status=201,
        properties={"key": _ID, "relationship_kind": {"enum": ["direct_report", "peer", "extended"]}},
        required=("key",),
        facts=held_arguments('Add a suggested person',
                named('key', 'Person', 'people.suggestions', {}, 'display_name|name', rows='suggestions', match={'key': 'key'}),
                hidden('relationship_kind', 'Relationship kind', 'secret'))),
    _op("people.suggestion.hide", "hide_suggestion", ("POST", _P + "/suggestions/hide"), "hide_suggestion",
        lambda s, p, a: s.hide_suggestion(p, str(a.get("key") or "")),
        "Hide one suggested name; it is not suggested again.", properties={"key": _ID}, required=("key",),
        facts=held_arguments('Hide a suggested person',
                named('key', 'Person', 'people.suggestions', {}, 'display_name|name', rows='suggestions', match={'key': 'key'}))),
    _op("people.relationship.archive", "archive_relationship", ("POST", _R + "/archive"), "archive_relationship",
        lambda s, p, a: {"relationship": s.archive_relationship(p, a.get("relationship_id"))},
        "Archive one Person.", authority="authority"),
    _op("people.relationship.restore", "restore_relationship", ("POST", _R + "/restore"), "restore_relationship",
        lambda s, p, a: {"relationship": s.restore_relationship(p, a.get("relationship_id"))},
        "Restore an archived Person with their notes and links. Owner only.", authority="authority"),
    _op("people.project.link", "link_project", ("POST", _R + "/projects/{project_id}"), "link_project",
        _link_project, "Link a Project to a Person.",
        facts=held_arguments('Link a project and person',
                named('relationship_id', 'Person', 'people.relationship.get', {'relationship_id': 'relationship_id'}, 'display_name'),
                named('project_id', 'Project', 'project.get', {'project_id': 'project_id'}, 'project.name|name'))),
    _op("people.project.unlink", "unlink_project", ("DELETE", _R + "/projects/{project_id}"), "unlink_project",
        lambda s, p, a: {"relationship": s.unlink_project(p, a.get("relationship_id"), a.get("project_id"))},
        "Unlink a Project from a Person.",
        facts=held_arguments('Unlink a project and person',
                named('relationship_id', 'Person', 'people.relationship.get', {'relationship_id': 'relationship_id'}, 'display_name'),
                named('project_id', 'Project', 'project.get', {'project_id': 'project_id'}, 'project.name|name'))),
    _op("people.one_on_one.list", "list_one_on_ones", ("GET", _R + "/one-on-ones"), "one_on_ones", _one_on_ones,
        "List the 1:1s of one Person with their agenda (over MCP: shared intent only).", write=False,
        mcp=_mcp(_one_on_ones, write=False, after=_shared_sessions)),
    _op("people.agenda.transition", "transition_agenda_item", ("POST", _P + "/agenda/{item_id}/transition"),
        "transition_agenda_item", _agenda, "Take an open agenda item off the 1:1 (removed) or mark it raised (done).",
        properties={"to": {"enum": ["done", "removed"]}}, required=("to",),
        mcp=_mcp(_agenda, write=True, after=lambda r: r if _readable(r["agenda_item"]) else {"agenda_item": {
            key: r["agenda_item"].get(key) for key in ("id", "state", "visibility")}}),
        facts=held_arguments('Change an agenda item',
                hidden('item_id', 'Agenda item', 'secret'),
                text('to', 'State'))),
    _op("people.owed.create", "create_owed_to_you", ("POST", _R + "/owed"), "create_owed_to_you", _owed,
        "Record what a Person owes you (over MCP: shared intent).", status=201, properties={"body": _ID},
        required=("body",), mcp=_mcp(lambda s, p, a: _owed(s, p, {**a, "visibility": "shared_intent"}), write=True),
        facts=held_arguments('Add what a person owes you',
                named('relationship_id', 'Person', 'people.relationship.get', {'relationship_id': 'relationship_id'}, 'display_name'),
                word_count('body', 'Commitment'))),
    _op("people.note.list", "list_notes", ("GET", _R + "/notes"), "notes", _notes,
        "List the grounding notes of one Person (over MCP: shared intent only).", write=False,
        mcp=_mcp(_notes, write=False, after=lambda r: {"notes": [n for n in r["notes"] if _readable(n)]})),
    _op("people.commitment.send_to_workbench", "attach_execution", ("POST", _C + "/workbench"),
        "send_commitment_to_workbench", _send_to_workbench,
        "Send one commitment to a workbench as an item grounded in the Person's projects (once).", status=201,
        properties={"workbench_id": _ID}, required=("workbench_id",),
        mcp=_mcp(_send_to_workbench, write=True, shared=True),
        facts=held_arguments('Send a commitment to an automation',
                hidden('commitment_id', 'Commitment', 'secret'),
                named('workbench_id', 'Automation', 'automation.get', {'workbench_id': 'workbench_id'}, 'automation.name|name'))),
    _op("people.commitment.satisfy", "satisfy_commitment", ("POST", _C + "/satisfy"), "satisfy_commitment",
        _satisfy, "Mark one commitment done, with its workbench items as evidence.",
        properties={"rationale": {"type": "string"}}, mcp=_mcp(_satisfy, write=True, shared=True),
        facts={**normalizer('holdspeak.services.people_service:PeopleService.effective_fields', record='satisfy'), **held_arguments('Mark a commitment done',
                hidden('commitment_id', 'Commitment', 'secret'),
                word_count('rationale', 'Reason'))}),
) + tuple(_op(name, method, http, method, _wrapped(call), description, properties=properties, required=required,
                 authority=authority, mcp=_mcp(call, write=True),
                 facts=(held_arguments("Link a calendar and person" if name.endswith(".link") else "Unlink a calendar and person",
                     named('relationship_id', 'Person', 'people.relationship.get', {'relationship_id': 'relationship_id'}, 'display_name'),
                     hidden('uid', 'Calendar series', 'secret'),
                     hidden('source_id', 'Calendar source', 'secret'),
                     *([hidden('label', 'Label', 'secret')] if 'label' in properties else []))
                     if name.startswith("people.calendar.") else None))
          for name, method, http, call, description, properties, required, authority in _LINKS)

__all__ = ["PEOPLE_OPERATIONS"]
