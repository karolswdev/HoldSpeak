"""The Room's web verbs on the one declared contract (2026-11-09, ops/projects).

Carved beside ``holdspeak/operations.py`` (which imports it into
``DESCRIPTORS``), as ``meeting_operations.py`` is. Each row states one verb
of a Room service once: its call, its HTTP method and path, and its MCP tool
schema. The route modules (``projects.py``, ``project_briefs.py``,
``project_updates.py``, ``proposals.py``, ``project_reviews.py``,
``steward.py``, ``cadence.py``) produce their routes and
``mcp/families/declared.py`` the tools from these rows, both through
``OperationRegistry.invoke``.

A row's answer is the HTTP answer (``{"meetings": [...]}``,
``{"success": true, "brief": ...}``), so the two transports read one shape.
The arguments schema is any object: the services validate, as they did
behind the hand-written routes. Reads are evidence and stay MCP and HTTP
only (the ``project.`` prefix; ``thread_modes._thread_side``).
"""
from __future__ import annotations

from holdspeak.held_arguments import held_arguments, text, hidden, named, word_count, normalizer

from datetime import datetime, timezone
from typing import Any, Callable, Mapping, Optional

from holdspeak.operations import _CONTRACT_REFUSALS, OperationDescriptor
from holdspeak.services.errors import ValidationError
from holdspeak.services.room_binding import BINDING_SCHEMA

Call = Callable[[Any, Any, dict[str, Any]], Any]

_PRINCIPAL = "derived by the transport (HTTP auth middleware; MCP auth resolver) and passed to the service unchanged"
_REFUSALS = _CONTRACT_REFUSALS + ("NotFound: unknown project, meeting, brief, update, job or proposal",
                                  "ValidationError", "ConflictError")
_ID = {"type": "string", "minLength": 1}


def _ids(path: str) -> list[str]:
    return [part[1:-1].split(":", 1)[0] for part in path.split("/") if part.startswith("{")]


def _op(name: str, service: str, method: str, http: tuple[str, str], handler: str, call: Call, description: str,
        *, write: bool = False, properties: Optional[Mapping[str, Any]] = None, required: tuple[str, ...] = (),
        status: int = 200, owner_only: bool = False, authority: str = "work", announces: bool = False,
        result: str = "the service's answer, as the HTTP route answers it", facts: Optional[Mapping[str, Any]] = None) -> OperationDescriptor:
    """One verb; its tool requires the path's ids and ``required``."""
    ids = _ids(http[1])
    tool = {**dict(facts or {}), "type": "object", "properties": {**{key: _ID for key in ids}, **dict(properties or {})},
            "required": ids + list(required), "additionalProperties": False}
    work = authority == "work"
    return OperationDescriptor(
        name=name, version=1, description=description, args_schema={"type": "object"}, principal=_PRINCIPAL,
        effect="write" if write else "read", result=result, refusals=_REFUSALS,
        completion="synchronous; a write is one desk_changed frame on the hub bus",
        exposure=(f"http:{http[0]} {http[1]}", f"mcp:{name}"), service=service, method=method,
        call=call, http=http, http_status=status, handler=handler, tool_schema=tool,
        owner_only=owner_only, owner_press=not work, authority=authority, announces_changes=announces,
        # A tool that is not work (egress, authority) is never a thread tool.
        thread=None if not work else ("effect_proposal" if write else "evidence_read"),
    )


def _int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _text(args: Mapping[str, Any], key: str) -> str:
    return str(args.get(key) or "")


def generation_arguments(args: dict[str, Any], *, default: str, strip: bool = False) -> dict[str, Any]:
    generator = str(args.get("generator") or default)
    return {**args, "generator": (generator.strip() or default) if strip else generator}


def apply_arguments(args: dict[str, Any]) -> dict[str, Any]:
    return {**args, "force": bool(args.get("force"))}


# ── the Room's reads and its saved asks (ProjectService) ────────────────


def _host() -> tuple[str, int]:
    """This hub's refinement lease, for a saved ask's custody token (HS-200-41 B7).

    No hub (an MCP sidecar, a route rig, a coordinator not started): custody
    is unknown and the row draws no token."""
    from holdspeak.runtime import composition

    try:
        coordinator = getattr(composition.current(), "refinement_coordinator", None)
    except composition.NoRuntimeError:
        coordinator = None
    if coordinator is None:
        return "", 0
    return str(getattr(coordinator, "host_id", "") or ""), int(getattr(coordinator, "_lease_epoch", 0) or 0)


def _save_ask(s: Any, p: Any, a: dict[str, Any]) -> Any:
    host_id, lease_epoch = _host()
    payload = {key: value for key, value in a.items() if key != "project_id"}
    return s.save_ask(p, _text(a, "project_id"), payload, host_id=host_id, lease_epoch=lease_epoch)


def _list_asks(s: Any, p: Any, a: dict[str, Any]) -> Any:
    # A closed ``state``: the Resume projection is the only view.
    if (a.get("state") or "unfinished") != "unfinished":
        raise ValidationError("state must be 'unfinished'", code="ask_task_state_invalid")
    return s.list_unfinished_asks(p, limit=_int(a.get("limit"), 20), cursor=a.get("cursor") or None,
                                  project_id=a.get("project_id") or None, host_id=_host()[0])


_P = "/api/projects/{project_id}"
_ROOM: tuple[OperationDescriptor, ...] = (
    _op("project.mark_room_read", "project_service", "mark_room_read", ("POST", _P + "/room/read"),
        "api_mark_room_read", lambda s, p, a: s.mark_room_read(p, _text(a, "project_id")),
        # A read marker: no window is told (Astra, #785 finding 1), so it announces nothing.
        "Mark the Room as read now (its new-since marker).", write=True, announces=True,
        facts=held_arguments('Mark a project room read',
                named('project_id', 'Project', 'project.get', {'project_id': 'project_id'}, 'project.name|name'))),
    _op("project.meetings", "project_service", "list_meetings", ("GET", _P + "/meetings"), "api_project_meetings",
        lambda s, p, a: {"meetings": s.list_meetings(p, _text(a, "project_id"), limit=_int(a.get("limit"), 50),
                                                     offset=_int(a.get("offset"), 0))},
        "List the meetings linked to one project, newest first.",
        properties={"limit": {"type": "integer", "minimum": 1}, "offset": {"type": "integer", "minimum": 0}}),
    _op("project.for_meeting", "project_service", "list_meeting_projects", ("GET", "/api/meetings/{meeting_id}/projects"),
        "api_meeting_projects", lambda s, p, a: {"projects": s.list_meeting_projects(p, _text(a, "meeting_id"))},
        "List the projects one meeting is linked to."),
    _op("project.since_last_meeting", "project_service", "since_last_meeting", ("GET", _P + "/since-last-meeting"),
        "api_project_since_last_meeting", lambda s, p, a: s.since_last_meeting(p, _text(a, "project_id")),
        "What changed in one project since its last meeting."),
    _op("project.artifacts", "project_service", "list_artifacts", ("GET", _P + "/artifacts"), "api_project_artifacts",
        lambda s, p, a: {"artifacts": s.list_artifacts(p, _text(a, "project_id"))},
        "List the plugin artifacts of one project's meetings."),
    _op("project.resource.relationships", "project_service", "list_resource_relationships",
        ("GET", "/api/desk/relationships/{resource_ref:path}"), "api_resource_relationships",
        lambda s, p, a: s.list_resource_relationships(p, _text(a, "resource_ref")),
        "List the projects and the place on the desk of one object (kind:id)."),
    _op("project.ask.save", "project_service", "save_ask", ("POST", _P + "/ask-tasks"), "api_save_ask_task",
        _save_ask, "Save an ask for a project so it can be resumed (purpose, lens, grounding).", write=True,
        status=201, properties={"purpose": {"type": "string"}, "lens": {"type": "string"},
                                "grounding": {"type": ["object", "array", "null"]}}, required=("purpose",),
        facts={**normalizer('holdspeak.services.project_service:ProjectService.effective_fields', record='ask'), **held_arguments('Save a project Ask',
                named('project_id', 'Project', 'project.get', {'project_id': 'project_id'}, 'project.name|name'),
                word_count('purpose', 'Question'),
                hidden('grounding', 'Sources', 'secret'),
                text('lens', 'View'))}),
    _op("project.ask.list", "project_service", "list_unfinished_asks", ("GET", "/api/ask-tasks"), "api_list_ask_tasks",
        _list_asks, "List the saved asks that did not finish (the Resume list).",
        properties={"state": {"enum": ["unfinished"]}, "limit": {"type": "integer", "minimum": 1},
                    "cursor": {"type": "string"}, "project_id": _ID}),
    _op("project.ask.stopped", "project_service", "record_ask_stop", ("POST", "/api/ask-tasks/{task_id}/stopped"),
        "api_record_ask_stop",
        lambda s, p, a: s.record_ask_stop(p, _text(a, "task_id"), _text(a, "code"), host_id=_host()[0]),
        "Record why a saved ask stopped, by its refusal code.", write=True,
        properties={"code": {"type": "string"}}, required=("code",),
        facts=held_arguments('Record a stopped project Ask',
                hidden('task_id', 'Ask', 'secret'),
                text('code', 'Reason'))),
    _op("project.ask.discard", "project_service", "discard_ask", ("POST", "/api/ask-tasks/{task_id}/discard"),
        "api_discard_ask_task", lambda s, p, a: s.discard_ask(p, _text(a, "task_id"), host_id=_host()[0]),
        "Discard a saved ask.", write=True,
        facts=held_arguments('Discard a saved project Ask',
                hidden('task_id', 'Ask', 'secret'))),
)

# ── the preparation brief (PreparationBriefService) ─────────────────────

_B = "project_brief_service"
_BRIEFS: tuple[OperationDescriptor, ...] = (
    _op("project.brief.route", _B, "route", ("GET", _P + "/briefs/route"), "api_brief_route",
        lambda s, p, a: {"route": s.route(p, _text(a, "project_id"))},
        "Read the engine route a brief would use for a project (nothing runs)."),
    _op("project.brief.manifest", _B, "preview_manifest", ("GET", _P + "/briefs/manifest"), "api_brief_manifest",
        lambda s, p, a: {"manifest": s.preview_manifest(p, _text(a, "project_id"))},
        "Read the sources a brief would bind now (nothing is written)."),
    _op("project.brief.prepare", _B, "prepare", ("POST", _P + "/briefs/prepare"), "api_prepare_brief",
        lambda s, p, a: {"success": True, "brief": s.prepare(
            p, _text(a, "project_id"), _text(a, "purpose"), generator=generation_arguments(a, default="model")["generator"],
            attempt_id=_text(a, "attempt_id").strip())},
        "Prepare a brief for a project from its sources: purpose, generator (model or deterministic).", write=True,
        properties={"purpose": {"type": "string"}, "generator": {"enum": ["model", "deterministic"]},
                    "attempt_id": {"type": "string"}}, required=("purpose",),
        facts={**normalizer('holdspeak.project_operations:generation_arguments', default='model'), **held_arguments('Prepare a project brief',
                named('project_id', 'Project', 'project.get', {'project_id': 'project_id'}, 'project.name|name'),
                word_count('purpose', 'Purpose'),
                text('generator', 'Requested generator'),
                hidden('attempt_id', 'Attempt', 'token'))}),
    _op("project.brief.stop", _B, "stop", ("POST", _P + "/briefs/stop"), "api_stop_brief",
        lambda s, p, a: s.stop(_text(a, "attempt_id")),
        "Stop a brief that is being prepared; it writes no draft.", write=True,
        properties={"attempt_id": _ID}, required=("attempt_id",),
        facts=held_arguments('Stop a brief preparation',
                hidden('attempt_id', 'Preparation', 'secret'),
                hidden('project_id', 'Route', 'secret'))),
    _op("project.brief.list", _B, "list_briefs", ("GET", _P + "/briefs"), "api_list_briefs",
        lambda s, p, a: {"briefs": s.list_briefs(p, _text(a, "project_id"), lifecycle=a.get("lifecycle") or None,
                                                 limit=_int(a.get("limit"), 20))},
        "List the briefs of a project (discarded ones are hidden).",
        properties={"lifecycle": {"type": "string"}, "limit": {"type": "integer", "minimum": 1}}),
    _op("project.brief.get", _B, "get_brief", ("GET", "/api/briefs/{brief_id}"), "api_get_brief",
        lambda s, p, a: {"brief": s.get_brief(p, _text(a, "brief_id"))},
        "Read one brief; its sources are checked again."),
    _op("project.brief.keep", _B, "keep", ("POST", "/api/briefs/{brief_id}/keep"), "api_keep_brief",
        lambda s, p, a: {"success": True, "brief": s.keep(p, _text(a, "brief_id"))}, "Keep a brief.", write=True,
        facts=held_arguments('Keep a project brief',
                named('brief_id', 'Project', 'project.brief.get', {'brief_id': 'brief_id'}, 'project.name|name', through={'tool': 'project.get', 'arguments': {'project_id': 'brief.project_id'}}))),
    _op("project.brief.discard", _B, "discard", ("POST", "/api/briefs/{brief_id}/discard"), "api_discard_brief",
        lambda s, p, a: {"success": True, "brief": s.discard(p, _text(a, "brief_id"), binding=a.get("binding"))},
        "Discard a brief (a state; nothing is deleted).", write=True,
        properties={"binding": BINDING_SCHEMA}, required=("binding",),
        facts=held_arguments('Discard a project brief',
                named('brief_id', 'Project', 'project.brief.get', {'brief_id': 'brief_id'}, 'project.name|name', through={'tool': 'project.get', 'arguments': {'project_id': 'brief.project_id'}}),
                hidden('binding', 'Saved question', 'token'))),
)

# ── the update and its engine pass (ProjectUpdateService) ───────────────


def enrich_update(update: dict[str, Any]) -> dict[str, Any]:
    """Add the camelCase provenance keys the face reads (HS-173-02)."""
    update["generatorHost"] = update.get("generator_host")
    update["generatorModel"] = update.get("generator_model")
    return update


def _review_claim(s: Any, p: Any, a: dict[str, Any]) -> Any:
    acceptance = _text(a, "acceptance")
    if acceptance not in ("accepted", "rejected"):
        raise ValidationError("acceptance is accepted or rejected", code="claim_acceptance_unknown")
    update = s.review_claim(p, _text(a, "update_id"), _text(a, "span_id"), acceptance=acceptance)
    return {"success": True, "update": enrich_update(update),
            "reviewed_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}


_U = "project_update_service"
# Where an agent finds each id it must pass (the Room's id paths, R1 P3).
_UPDATE = {"update_id": {**_ID, "description": (
    "The update id: updates[].id from project.list_updates, or update.id from project.draft_update.")}}
_JOB = {"job_id": {**_ID, "description": "The engine pass id: job.id from project.update.engine_pass."}}
_SPAN = {"span_id": {**_ID, "description": (
    "The claim id: update.claims_json[].span_id from project.draft_update (claims_json is JSON text).")}}
_AUTOMATION = {"automation_id": {"type": "string", "description": (
    "The project's update automation: updates.automation.id from project.get_room.")}}
_UPDATES: tuple[OperationDescriptor, ...] = (
    _op("project.update.get", _U, "get_update", ("GET", "/api/updates/{update_id}"), "api_get_update",
        lambda s, p, a: {"update": enrich_update(s.get_update(p, _text(a, "update_id")))},
        "Read one project update by id.", properties=_UPDATE),
    _op("project.update.regenerate", _U, "regenerate_update", ("POST", "/api/updates/{update_id}/regenerate"),
        "api_regenerate_update",
        lambda s, p, a: {"success": True, "update": enrich_update(s.regenerate_update(
            p, _text(a, "update_id"), generator=generation_arguments(a, default="deterministic", strip=True)["generator"],
            command_id=a.get("command_id")))},
        "Replace a draft update with a fresh draft (generator: deterministic or model).", write=True,
        properties={**_UPDATE, "generator": {"enum": ["deterministic", "model"]}, "command_id": {"type": "string"}},
        facts={**normalizer('holdspeak.project_operations:generation_arguments', default='deterministic', strip=True), **held_arguments('Make a new update draft',
                named('update_id', 'Project', 'project.update.get', {'update_id': 'update_id'}, 'project.name|name', through={'tool': 'project.get', 'arguments': {'project_id': 'update.project_id'}}),
                text('generator', 'Requested generator'),
                hidden('command_id', 'Command', 'token'))}),
    _op("project.update.engine_pass", _U, "start_engine_pass", ("POST", "/api/updates/{update_id}/engine-pass"),
        "api_start_engine_pass",
        lambda s, p, a: {"success": True, "job": s.start_engine_pass(
            p, _text(a, "update_id"), automation_id=_text(a, "automation_id").strip() or None)},
        "Let an engine improve a draft update in the background. Read the job with project.update.job.",
        write=True, properties={**_UPDATE, **_AUTOMATION},
        facts=held_arguments('Improve a project update draft',
                named('update_id', 'Project', 'project.update.get', {'update_id': 'update_id'}, 'project.name|name', through={'tool': 'project.get', 'arguments': {'project_id': 'update.project_id'}}),
                named('automation_id', 'Automation', 'automation.get', {'workbench_id': 'automation_id'}, 'automation.name|name'))),
    _op("project.update.job", _U, "get_engine_pass", ("GET", "/api/update-jobs/{job_id}"), "api_get_engine_pass",
        lambda s, p, a: {"job": s.get_engine_pass(_text(a, "job_id"))},
        "Read an engine pass on an update: its state and its draft.", properties=_JOB),
    _op("project.update.job_stop", _U, "stop_engine_pass", ("POST", "/api/update-jobs/{job_id}/stop"),
        "api_stop_engine_pass",
        lambda s, p, a: {"success": True, "job": s.stop_engine_pass(p, _text(a, "job_id"))},
        "Stop an engine pass; its late answer is dropped.", write=True, properties=_JOB,
        facts=held_arguments('Stop an update engine pass',
                named('job_id', 'Project', 'project.update.job', {'job_id': 'job_id'}, 'project.name|name', through={'tool': 'project.get', 'arguments': {'project_id': 'job.project_id'}}))),
    _op("project.update.job_apply", _U, "apply_engine_pass", ("POST", "/api/update-jobs/{job_id}/apply"),
        "api_apply_engine_pass",
        lambda s, p, a: {"success": True, "update": enrich_update(s.apply_engine_pass(
            p, _text(a, "job_id"), force=apply_arguments(a)["force"]))},
        "Save an engine pass's draft as the next revision (refused if you edited, unless force).", write=True,
        properties={**_JOB, "force": {"type": "boolean"}},
        facts={**normalizer('holdspeak.project_operations:apply_arguments'), **held_arguments('Save an update engine pass',
                named('job_id', 'Project', 'project.update.job', {'job_id': 'job_id'}, 'project.name|name', through={'tool': 'project.get', 'arguments': {'project_id': 'job.project_id'}}),
                text('force', 'Replace edits'))}),
    _op("project.update.review_claim", _U, "review_claim", ("POST", "/api/updates/{update_id}/claims/{span_id}/review"),
        "api_review_claim", _review_claim,
        "Accept or reject one claim of an update (the owner's judgment).", write=True,
        properties={**_UPDATE, **_SPAN, "acceptance": {"enum": ["accepted", "rejected"]}}, required=("acceptance",),
        facts=held_arguments('Review an update claim',
                named('update_id', 'Project', 'project.update.get', {'update_id': 'update_id'}, 'project.name|name', through={'tool': 'project.get', 'arguments': {'project_id': 'update.project_id'}}),
                hidden('span_id', 'Claim', 'secret'),
                text('acceptance', 'Answer'))),
)

# ── the follow-through proposals (ProposalBridgeService) ────────────────

_PB = "proposal_bridge_service"
_PROPOSALS: tuple[OperationDescriptor, ...] = (
    _op("proposal.confirm", _PB, "confirm_proposal", ("POST", "/api/proposals/{proposal_id}/confirm"),
        "api_confirm_proposal", lambda s, p, a: s.confirm_proposal(
            p, _text(a, "proposal_id"), binding=a.get("binding"), text=a.get("text"), owner=a.get("who"), due=a.get("due")),
        "Confirm the proposal you read. A missing or stale binding changes nothing.", write=True,
        properties={"binding": BINDING_SCHEMA, "text": {"type": "string"}, "who": {"type": "string"}, "due": {"type": "string"}},
        required=("binding",)),
    _op("proposal.dismiss", _PB, "dismiss_proposal", ("POST", "/api/proposals/{proposal_id}/dismiss"),
        "api_dismiss_proposal", lambda s, p, a: s.dismiss_proposal(p, _text(a, "proposal_id"), binding=a.get("binding")),
        "Dismiss the proposal you read. A missing or stale binding changes nothing.", write=True,
        properties={"binding": BINDING_SCHEMA}, required=("binding",)),
    _op("project.proposals", _PB, "list_project_proposals", ("GET", _P + "/proposals"), "api_project_proposals",
        lambda s, p, a: {"project_id": _text(a, "project_id"),
                         "proposals": s.list_project_proposals(_text(a, "project_id"), state=a.get("state") or None)},
        "List the follow-through proposals of one project.", properties={"state": {"type": "string"}}),
    _op("meeting.outcome_review", _PB, "meeting_review", ("GET", "/api/meetings/{meeting_id}/outcome-review"),
        "api_meeting_outcome_review", lambda s, p, a: s.meeting_review(_text(a, "meeting_id")),
        "Read the outcome review of one meeting: its proposals and what each needs."),
    _op("meeting.accept_reviewed", _PB, "accept_reviewed", ("POST", "/api/meetings/{meeting_id}/proposals/accept-reviewed"),
        "api_accept_reviewed", lambda s, p, a: s.accept_reviewed(p, _text(a, "meeting_id"), bindings=a.get("bindings")),
        "Confirm every reviewed proposal of one meeting; the rest are named with their reason.", write=True,
        properties={"bindings": {"type": "array", "items": BINDING_SCHEMA}}, required=("bindings",)),
    _op("proposal.edit", _PB, "edit_proposal", ("POST", "/api/proposals/{proposal_id}/edit"), "api_edit_proposal",
        lambda s, p, a: s.edit_proposal(p, _text(a, "proposal_id"), text=a.get("text"), owner=a.get("who"),
                                        due=a.get("due")),
        "Edit a proposal in place: its text, its person (who), its due date.", write=True,
        properties={"text": {"type": "string"}, "who": {"type": "string"}, "due": {"type": "string"}}),
    _op("proposal.restore", _PB, "restore_proposal", ("POST", "/api/proposals/{proposal_id}/restore"),
        "api_restore_proposal", lambda s, p, a: s.restore_proposal(p, _text(a, "proposal_id")),
        "Undo a dropped proposal: it is proposed again.", write=True),
    _op("proposal.defer", _PB, "defer_proposal", ("POST", "/api/proposals/{proposal_id}/defer"), "api_defer_proposal",
        lambda s, p, a: s.defer_proposal(p, _text(a, "proposal_id"), until=a.get("until")),
        "Defer a proposal until a date.", write=True, properties={"until": {"type": "string"}}),
)

# ── the steward's run list and a review (blind routes made services) ────

_ROOM_READS: tuple[OperationDescriptor, ...] = (
    _op("project.steward_runs", "project_steward_service", "list_runs", ("GET", _P + "/steward/runs"),
        "api_list_steward_runs",
        lambda s, p, a: {"runs": s.list_runs(p, _text(a, "project_id"), state=a.get("state") or None,
                                             limit=_int(a.get("limit"), 100))},
        "List the steward runs of one project, newest first.",
        properties={"state": {"type": "string"}, "limit": {"type": "integer", "minimum": 1}}),
    _op("project.get_review", "project_delta_service", "get_review", ("GET", _P + "/reviews/{review_id}"), "get_review",
        lambda s, p, a: s.get_review(p, _text(a, "project_id"), _text(a, "review_id")),
        "Read one review of a project: its frozen window and its proposals."),
)

# ── the cadence loop's reply (CadenceService) ───────────────────────────

_CADENCE: tuple[OperationDescriptor, ...] = (
    _op("cadence.reply", "cadence_service", "reply", ("POST", "/api/cadence/loops/{loop_id}/reply"), "reply",
        lambda s, p, a: s.reply(p, _text(a, "loop_id"), {k: v for k, v in a.items() if k != "loop_id"}),
        "Answer a waiting agent with your typed words, then close its loop. Never automatic.", write=True,
        properties={"text": {"type": "string"}}, required=("text",), owner_only=True, authority="authority"),
)

PROJECT_OPERATIONS: tuple[OperationDescriptor, ...] = _ROOM + _BRIEFS + _UPDATES + _PROPOSALS + _ROOM_READS + _CADENCE

__all__ = ["PROJECT_OPERATIONS", "enrich_update"]
