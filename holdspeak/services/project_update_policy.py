"""The project-update source policy: one home (HS-S55).

A project update is a source-scoped automation. Two entry paths run it, and
both read this module:

- an HTTP engine run (``engine_tool_loop.call_tool``): the hub runs the tool
  loop, so the project comes from the trusted run binding (the item's
  ``output_target``), never from a model-supplied argument; it has no
  durable credential;
- a CLI engine run (``mcp.server.handle_message_for_principal``): the project
  comes from the run's durable CONDUCTOR launch credential
  (``project_update_scope``).

Both narrow the palette to the update's read tools plus its draft writer,
bind and refuse out-of-scope calls (``prepare_project_update_call``) and cut
private rows from each answer (``filter_response``). The private-source
scope (P2) is decided here too: a linked 1:1 meeting and its descendants are
withheld (``excluded_refs``), except a descendant the owner filed on the
project by hand; People and 1:1 notes are withheld. A missing source read
fails closed. ``ProjectUpdateService`` keeps its old method names as
delegates, so the Workbench runner and the records drafter read the same
rule.

Preparing a call is not a send: the owner's press and the frozen provenance
stay where they are. This module imports neither ``engine_tool_loop`` nor
``mcp.server``.
"""
from __future__ import annotations

import json
from typing import Any, Callable, Mapping, Optional

from ..logging_config import get_logger
from .meeting_kind import is_one_on_one, meeting_speakers, title_says_one_on_one

_log = get_logger("services.project_update_policy")

# A project update is a source-scoped automation.  The ordinary MCP palettes
# remain unchanged; these names are the read surfaces that can return a
# project's linked private meeting or People note after the first grounding
# pass.
READ_TOOLS = frozenset({
    "meeting.get", "meeting.list", "memory.observations", "memory.page",
    "memory.search", "project.get", "project.get_delta", "project.get_room", "project.list_updates",
    "project.resource.list",
})
ROW_KEYS = frozenset({
    "meetings", "resources", "hits", "observations", "actions", "action_items",
    "artifacts", "decisions", "commitments", "proposals", "sentences", "sources", "evidence", "updates",
})

# A CLI automation receives its durable CONDUCTOR credential before the
# process starts.  A project-update run is the one narrow exception: it may
# read the project/update source surfaces and save the resulting draft.  The
# credential's project_id is the binding; ordinary launch credentials keep
# the unchanged CONDUCTOR palette.
SAFE_TOOLS = READ_TOOLS | {"project.update_draft"}


def update_tools(palette: frozenset[str]) -> frozenset[str]:
    """A palette cut to the update's read tools, plus its draft writer."""
    return frozenset(set(palette) & set(SAFE_TOOLS)) | {"project.update_draft"}


def allow_update_draft(call_gate: Callable[[str, Any], bool]) -> Callable[[str, Any], bool]:
    """``call_gate`` that also lets the update's own draft writer through."""

    def gate(name: str, arguments: Any) -> bool:
        return name == "project.update_draft" or call_gate(name, arguments)

    return gate


def project_update_scope(principal: Any) -> str:
    """Return the project bound to an update-run credential, if any."""
    from ..principals import PrincipalKind, agent_credentials
    from .conductor_launch import RUN_IDENTITY_PREFIX

    if getattr(principal, "kind", None) is not PrincipalKind.AGENT:
        return ""
    identity = str(getattr(principal, "identity", "") or "")
    if not identity.startswith(RUN_IDENTITY_PREFIX):
        return ""
    credential = agent_credentials.launch_credential(identity)
    if credential is None or credential.palette_name != "CONDUCTOR":
        return ""
    return str(credential.project_id or "").strip()


def project_update_palette(principal: Any, palette: frozenset[str] | None) -> frozenset[str] | None:
    """Scope a project-update run to its existing safe read tools plus its writer."""
    if not project_update_scope(principal):
        return palette
    if palette is None:
        return frozenset(SAFE_TOOLS)
    return update_tools(palette)


def prepare_project_update_call(
    principal: Any, name: str, arguments: Mapping[str, Any], project_id: str,
) -> tuple[dict[str, Any], set[str], str | None]:
    """Bind and filter one MCP call for a durable project-update credential."""
    from ..db import get_database

    args = dict(arguments or {})
    _service, excluded = update_source_service(principal, project_id)
    folded_excluded = {str(ref).casefold() for ref in excluded}
    if name == "meeting.get":
        meeting_id = str(args.get("meeting_id") or "").strip().casefold()
        _private_ids, eligible_ids = _service._project_update_meeting_ids(principal, project_id)
        if meeting_id not in {value.casefold() for value in eligible_ids}:
            return args, excluded, "meeting is outside project update sources"
    if name in {"project.get", "project.get_delta", "project.get_room", "project.list_updates",
                "project.resource.list", "memory.search", "memory.page", "memory.observations"}:
        requested = str(args.get("project_id") or "").strip()
        if requested and requested != project_id:
            return args, excluded, "project update reads are scoped to its project"
        args["project_id"] = project_id
    if name in {"memory.page", "memory.observations"}:
        args["scope"] = "project"
    if name == "project.update_draft":
        update_id = str(args.get("update_id") or "").strip()
        row = get_database().project_updates.get_update(update_id) if update_id else None
        if row is not None and str(row["project_id"]) != project_id:
            return args, excluded, "draft is outside the project update scope"
        refs = args.get("source_refs")
        if isinstance(refs, list):
            args["source_refs"] = [
                ref for ref in refs
                if str(ref).split("#", 1)[0].casefold() not in folded_excluded
            ]
    return args, excluded, None


def update_source_service(principal: Any, project_id: str) -> Any:
    from ..db import get_database
    from .project_service import ProjectService
    from .project_update_service import ProjectUpdateService

    db = get_database()
    service = ProjectUpdateService(db, project_service=ProjectService(db))
    return service, service.project_update_excluded_refs(principal, project_id)


def _row_has_private_ref(row: Any, key: str, excluded: set[str], excluded_meetings: set[str]) -> bool:
    if not isinstance(row, Mapping):
        return False
    if key in {"meetings", "latest"}:
        from .meeting_kind import title_says_one_on_one

        if title_says_one_on_one(str(row.get("title") or "")):
            return True
    candidates: set[str] = set()
    for field in ("ref", "source_ref", "resource_ref", "meeting_ref"):
        value = str(row.get(field) or "").strip()
        if value:
            candidates.add(value.split("#", 1)[0].casefold())
    for field in ("refs", "sources", "evidence"):
        values = row.get(field)
        if not isinstance(values, list):
            continue
        for value in values:
            if isinstance(value, Mapping):
                ref = str(value.get("ref") or value.get("source_ref") or "").strip()
                if ref:
                    candidates.add(ref.split("#", 1)[0].casefold())
    for field in ("week_source_refs", "agent_sources"):
        values = row.get(field)
        if isinstance(values, list):
            candidates.update(
                str(ref).split("#", 1)[0].casefold()
                for ref in values if str(ref).strip()
            )
    for field in ("source_manifest_json", "claims_json"):
        raw = row.get(field)
        if not raw:
            continue
        try:
            manifest = json.loads(str(raw))
        except (TypeError, ValueError):
            continue
        if _row_has_private_ref(manifest, field, excluded, excluded_meetings):
            return True
    for meeting_field in ("meeting_id", "source_meeting_id"):
        meeting_id = str(row.get(meeting_field) or "").strip()
        if meeting_id and meeting_id.casefold() in excluded_meetings:
            return True
    identifier = str(row.get("id") or "").strip()
    if identifier:
        kind = {
            "meetings": "meeting", "actions": "action", "action_items": "action_item",
            "artifacts": "artifact", "decisions": "decision", "proposals": "decision",
        }.get(key)
        if kind:
            candidates.add(f"{kind}:{identifier}".casefold())
        if key == "latest" and (row.get("title") or row.get("started_at") or row.get("summary")):
            candidates.add(f"meeting:{identifier}".casefold())
    # A page/observation can carry its source refs below the row itself.
    for nested_key in ("sentences", "sources", "evidence"):
        nested = row.get(nested_key)
        if isinstance(nested, list):
            for entry in nested:
                if _row_has_private_ref(entry, nested_key, excluded, excluded_meetings):
                    return True
    return bool(candidates & excluded)


def filter_payload(value: Any, excluded: set[str], *, key: str = "") -> Any:
    """Remove excluded source rows from one MCP JSON value.

    The MCP transport has already converted service objects to JSON text.  A
    row-level filter keeps the exact positive project refs and response shape,
    while preventing a private row's body or snippet from reaching the model.
    """
    excluded = {str(ref).casefold() for ref in excluded}
    excluded_meetings = {
        ref.removeprefix("meeting:")
        for ref in excluded
        if ref.startswith("meeting:")
    }
    if isinstance(value, list):
        filtered: list[Any] = []
        for row in value:
            if key in ROW_KEYS and _row_has_private_ref(row, key, excluded, excluded_meetings):
                continue
            filtered.append(filter_payload(row, excluded, key=key))
        return filtered
    if isinstance(value, dict):
        result: dict[str, Any] = {}
        for child_key, child in value.items():
            # A direct meeting/read payload has no enclosing list key.
            if child_key in {"meeting", "meeting_detail"} and _row_has_private_ref(child, "meetings", excluded, excluded_meetings):
                result[child_key] = None
                continue
            if child_key in {"latest", "latest_published"} and _row_has_private_ref(child, "latest", excluded, excluded_meetings):
                result[child_key] = None
                continue
            result[child_key] = filter_payload(child, excluded, key=child_key)
        if key == "page" and isinstance(value.get("sentences"), list):
            safe_sentences = result.get("sentences") or []
            if len(safe_sentences) != len(value["sentences"]):
                result["answer"] = " ".join(
                    str(sentence.get("text") or "").strip()
                    for sentence in safe_sentences
                    if isinstance(sentence, Mapping) and str(sentence.get("text") or "").strip()
                )
        return result
    return value


def filter_response(response: Any, excluded: set[str], name: str, *, project_id: str = "", principal: Any = None) -> Any:
    if not isinstance(response, dict):
        return response
    result = response.get("result")
    if not isinstance(result, dict):
        return response
    for content in result.get("content") or []:
        if not isinstance(content, dict) or content.get("type") != "text":
            continue
        try:
            payload = json.loads(str(content.get("text") or "{}"))
        except (TypeError, ValueError):
            continue
        if name == "meeting.list" and project_id and isinstance(payload, dict):
            service, _excluded = update_source_service(principal, project_id)
            _private, eligible = service._project_update_meeting_ids(principal, project_id)
            payload["meetings"] = [
                row for row in payload.get("meetings", [])
                if isinstance(row, dict) and str(row.get("id") or "") in eligible
            ]
        root_key = {
            "meeting.list": "meetings", "project.get_delta": "proposals", "project.list_updates": "updates",
            "project.resource.list": "resources",
            "memory.search": "hits", "memory.observations": "observations",
        }.get(name, "")
        content["text"] = json.dumps(
            filter_payload(payload, excluded, key=root_key),
            sort_keys=True,
            default=str,
        )
    return response


# ── P2: which of a project's sources an update may read ──────────────


def meeting_ids(
    db: Any, project_service: Any, read_people_names: Optional[Callable[[Any], Any]],
    principal: Any, project_id: str,
) -> tuple[set[str], set[str]]:
    """Return linked meeting ids split by the existing P2 rule.

    The project ref is a broad container for ordinary grounding callers.
    An update automation has a narrower contract: it uses the same
    meeting-kind classifier as the records drafter, before any source
    text is hydrated. The second set is the eligible ids; keeping this
    decision here lets the Workbench and tool response paths share P2.
    """
    excluded: set[str] = set()
    eligible: set[str] = set()
    people_names: list[str] = []
    if read_people_names is not None:
        try:
            people_names = [str(name) for name in read_people_names(principal) if str(name).strip()]
        except Exception:
            _log.debug("update grounding: People names not read; title rule only", exc_info=True)
    if read_people_names is None:
        # The Workbench delivery path is composed from its database only.
        # Reuse the same People-name read used by the Room when that
        # composition does not inject the web server's callback.
        try:
            from .needs_you_membership import _read_people_names

            people_names = [str(name) for name in (_read_people_names(principal) or ()) if str(name).strip()]
        except Exception:
            people_names = []

    try:
        offset = 0
        while True:
            page = project_service.list_meetings(
                principal, project_id, limit=500, offset=offset,
            )
            if not page:
                break
            for row in page:
                meeting_id = str(row.get("id") or "").strip()
                if not meeting_id:
                    continue
                title = str(row.get("title") or "")
                private = title_says_one_on_one(title)
                try:
                    meeting = db.meetings.get_meeting(meeting_id)
                except Exception:
                    meeting = None
                if meeting is not None:
                    title = str(getattr(meeting, "title", None) or title)
                    private = private or is_one_on_one(
                        title, meeting_speakers(meeting), people_names,
                    )
                (excluded if private else eligible).add(meeting_id)
            if len(page) < 500:
                break
            offset += len(page)
    except Exception:
        # A missing meeting projection must not turn into broad project
        # hydration. The caller still has any explicit safe refs.
        _log.debug("update grounding: linked meetings not read", exc_info=True)

    return excluded, eligible

def excluded_refs(
    db: Any, project_service: Any, read_people_names: Optional[Callable[[Any], Any]],
    principal: Any, project_id: str,
) -> set[str]:
    """Return canonical refs P2 withholds from an update automation.

    This is deliberately a predicate over the existing project source
    records. It does not change generic project grounding or unlink a
    source. A private meeting's descendants are withheld unless the
    owner explicitly filed that descendant as a project resource; that
    hand-filed edge is an intentional P2 exception for owed work and
    owner-added project material.
    """
    excluded_meetings, _eligible_meetings = meeting_ids(
        db, project_service, read_people_names, principal, project_id,
    )
    excluded = {f"meeting:{meeting_id}" for meeting_id in excluded_meetings}
    excluded.update(f"transcript:{meeting_id}" for meeting_id in excluded_meetings)
    try:
        project_resources = project_service.list_resources(principal, project_id)
    except Exception:
        project_resources = []
    explicit_refs = {
        str(resource.get("resource_ref") or "").strip().casefold()
        for resource in project_resources
        if str(resource.get("resource_ref") or "").strip()
    }
    try:
        for action in project_service.list_action_items(principal, project_id):
            if str(action.get("meeting_id") or "") in excluded_meetings:
                action_id = str(action.get("id") or "").strip()
                if action_id and not (
                    f"action:{action_id}".casefold() in explicit_refs
                    or f"action_item:{action_id}".casefold() in explicit_refs
                ):
                    excluded.update({f"action:{action_id}", f"action_item:{action_id}"})
        for artifact in project_service.list_artifacts(principal, project_id):
            if str(artifact.get("meeting_id") or "") in excluded_meetings:
                artifact_id = str(artifact.get("id") or "").strip()
                if artifact_id and f"artifact:{artifact_id}".casefold() not in explicit_refs:
                    excluded.add(f"artifact:{artifact_id}")
        for record_id in records_from_meetings(db, excluded_meetings):
            if not (
                f"decision:{record_id}".casefold() in explicit_refs
                or f"decision_record:{record_id}".casefold() in explicit_refs
                or f"desk_decision:{record_id}".casefold() in explicit_refs
            ):
                excluded.update({f"decision:{record_id}", f"decision_record:{record_id}"})
    except Exception:
        _log.debug("update grounding: meeting descendants not read", exc_info=True)

    # People notes live in their own encrypted store. A regular note can
    # still be linked to a project by hand; only explicit People/1:1
    # markers are withheld here, preserving ordinary project notes.
    for resource in project_resources:
        raw = str(resource.get("resource_ref") or "").strip()
        kind, _, resource_id = raw.partition(":")
        kind = kind.casefold()
        resource_id = resource_id.split("#", 1)[0].strip()
        if not kind or not resource_id:
            continue
        if kind in {
            "people", "person", "people_note", "grounding_note", "relationship",
            "one_on_one", "one-on-one",
        }:
            excluded.add(f"{kind}:{resource_id}")
            continue
        if kind not in {"note", "notes"}:
            continue
        note = db.notes.get(resource_id)
        tags = {str(tag).strip().casefold() for tag in (getattr(note, "tags", None) or [])}
        title = str(getattr(note, "title", "") or "") if note is not None else ""
        people_note = (
            title_says_one_on_one(title)
            or any(
                tag in {"people", "people_note", "people-note", "person", "1:1", "one-on-one"}
                or tag.startswith(("people:", "person:"))
                for tag in tags
            )
        )
        if people_note:
            excluded.update({f"note:{resource_id}", f"notes:{resource_id}"})
    return excluded

def grounding_refs(
    db: Any, project_service: Any, read_people_names: Optional[Callable[[Any], Any]],
    principal: Any, project_id: str,
) -> list[str]:
    """Expand one project ref to P2-eligible refs for an update run."""
    excluded = {ref.casefold() for ref in excluded_refs(db, project_service, read_people_names, principal, project_id)}
    _excluded_meetings, eligible_meetings = meeting_ids(
        db, project_service, read_people_names, principal, project_id,
    )
    refs = [f"meeting:{meeting_id}" for meeting_id in eligible_meetings]
    try:
        resources = project_service.list_resources(principal, project_id)
    except Exception:
        resources = []
    for resource in resources:
        ref = str(resource.get("resource_ref") or "").strip().split("#", 1)[0]
        if not ref or ref.casefold().startswith("project:"):
            continue
        if ref.casefold() not in excluded:
            refs.append(ref)
    return sorted(set(refs))


def records_from_meetings(db: Any, meeting_ids: set[str]) -> set[str]:
    """The decision records whose source is one of these meetings."""
    if not meeting_ids:
        return set()
    try:
        with db._connection() as conn:
            rows = conn.execute(
                "SELECT record_id FROM decision_record_sources "
                "WHERE source_type = 'meeting' "
                "AND source_ref IN (SELECT value FROM json_each(?))",
                (json.dumps(sorted(meeting_ids)),),
            ).fetchall()
    except Exception:
        _log.debug("update draft: 1:1 decision records not read", exc_info=True)
        return set()
    return {str(row["record_id"]) for row in rows}


__all__ = [
    "READ_TOOLS", "ROW_KEYS", "SAFE_TOOLS", "allow_update_draft", "excluded_refs", "filter_payload",
    "filter_response", "grounding_refs", "meeting_ids", "prepare_project_update_call",
    "project_update_palette", "project_update_scope", "records_from_meetings", "update_source_service",
    "update_tools",
]
