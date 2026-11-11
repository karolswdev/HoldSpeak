"""The remaining hub adapters, declared at their service boundary.

A protocol, credential check or encrypted owner projection stays HTTP-only.
Plain reads also have an MCP tool; authority does not come from arguments.
"""
from __future__ import annotations

from holdspeak.operations import OperationDescriptor, _CONTRACT_REFUSALS


def _op(name, service, method, http, handler, description, *, properties=None, required=(),
        owner=False, press=False, write=False, reason=None, held=(), call=None, web_call=None, authority="work",
        refusals=(), result="the service answer in the existing HTTP envelope", announces=False):
    schema = {"type": "object", "properties": properties or {}, "required": list(required),
              "additionalProperties": name == "setup.discover_models"}
    return OperationDescriptor(
        name=name, version=1, description=description, args_schema=schema,
        principal="authenticated transport principal; never caller data", effect="write" if write else "read",
        result=result, refusals=_CONTRACT_REFUSALS + ("owner_required",) + refusals,
        completion="synchronous; protocol calls keep each invoked operation's completion",
        exposure=(f"http:{http[0]} {http[1]}",) + (() if reason else (f"mcp:{name}",)),
        service=service, method=method, owner_only=owner, owner_press=press, blocking_io=True,
        authority=authority, http=http, handler=handler, tool_schema=None if reason else schema,
        http_only_reason=reason, held=held, call=call, web_call=web_call,
        announces_changes=announces,
        thread="evidence_read" if not reason and not owner and not write else None,
    )


def _review(service, principal, args):
    from holdspeak.services.errors import ServiceError
    status, body = service.draft_review(principal, **args)
    if status >= 400:
        code = str(body.get("error") or "delivery_pr_review_draft_refused")
        raise ServiceError(code, code, context={"status": status, **body})
    return body


PARITY_OPERATIONS = (
    _op("desk.actuators.status", "actuator_service", "status", ("GET", "/api/desk/actuators/status"),
        "api_desk_actuators_status", "Read whether webhook and GitHub delivery are configured."),
    _op("delivery.belt.state", "delivery_service", "belt_state", ("GET", "/api/missioncontrol/state"),
        "api_missioncontrol_state", "Read the configured repositories for the iPad belt.", owner=True,
        authority="authority"),
    _op("delivery.belt.journal", "delivery_service", "belt_journal", ("GET", "/api/missioncontrol/rails/journal"),
        "api_missioncontrol_rails_journal", "Read the belt journal, newest first.",
        properties={"limit": {"type": "integer"}}, owner=True, authority="authority"),
    _op("project.people", "project_service", "people_preparation", ("GET", "/api/projects/{project_id}/people"),
        "api_project_people", "Read the people and open commitments linked to one project.",
        properties={"project_id": {"type": "string"}}, required=("project_id",), owner=True,
        reason="The owner's Room reads names and private commitments from the encrypted People store.", held=("people_service",)),
    _op("setup.discover_models", "setup_service", "discover_models", ("POST", "/api/setup/discover-models"),
        "api_discover_models", "Check the owner's endpoint with its typed or saved key.", owner=True, press=True,
        authority="egress", call=lambda s, p, a: s.discover_models(p, **a),
        reason="An owner press may read a saved credential and send it to the named endpoint.",
        properties={"base_url": {}, "profile_id": {}, "api_key": {}, "check_tools": {}, "my_server": {}}),
    _op("meeting.slack_export", "meeting_aftercare_service", "slack_export",
        ("POST", "/api/meetings/{meeting_id}/export/slack"), "api_export_meeting_to_slack",
        "Refuse the retired Slack export with its channel migration code.",
        properties={"meeting_id": {"type": "string"}}, required=("meeting_id",),
        reason="Compatibility refusal only; Slack sends use the channel operations."),
    _op("meeting.mic_check", "meeting_service", "check_microphone", ("POST", "/api/meeting/mic-check"),
        "api_meeting_mic_check", "Sample the meeting microphone after the owner's press.", owner=True, press=True,
        reason="The browser holds the device permission and the running meeting state.", held=("meeting_active",)),
    _op("project.ask_task.resume", "project_service", "resume_ask", ("POST", "/api/ask-tasks/{task_id}/resume"),
        "api_resume_ask_task", "Resume the saved Ask with its invocation identity and hub custody.",
        properties={"task_id": {"type": "string"}}, required=("task_id",), owner=True, press=True, write=True,
        authority="egress", reason="The owner's Ask window holds its dispatch coroutine and refinement lease.",
        held=("dispatcher", "host_id", "lease_epoch")),
    _op("follow_through.owner_board", "follow_through_service", "owner_board", ("GET", "/api/follow-through/board"),
        "board", "Read the owner's board with private People labels.", owner=True,
        properties={k: {"type": ["string", "null"]} for k in ("project_id", "owner_filter", "state", "focus_id")},
        reason="The browser view enriches cards with private names; agents use follow_through.board without them."),
    _op("people.commitment.execution", "people_service", "commitment_execution",
        ("GET", "/api/people/commitments/{commitment_id}/execution"), "commitment_execution",
        "Read the owner's commitment and its linked work items.", owner=True,
        properties={"commitment_id": {"type": "string"}}, required=("commitment_id",),
        reason="This read includes private commitments and their complete workbench artifacts."),
    _op("delivery.pr_draft_review", "delivery_service", "draft_review",
        ("POST", "/api/delivery/prs/{source_id}/{number}/draft-review"), "api_delivery_pr_draft_review",
        "Draft a PR review on its assigned engine. The draft is retained and never posted.", owner=True, press=True,
        write=True, authority="egress", properties={"source_id": {"type": "string"}, "number": {"type": "integer"}},
        required=("source_id", "number"), call=_review,
        web_call=lambda s, p, a: s.draft_review(p, **a), result="the retained draft artifact and its engine receipt",
        refusals=("unknown_pr", "verb_unavailable", "diff_unavailable", "delivery_pr_review_draft_refused")),
    _op("decision_record.create_desk_command", "decision_record_service", "create_desk_command",
        ("POST", "/api/decision-records/from-desk"), "create_from_desk",
        "Create a Desk decision through its admitted operation and return the canonical record.", write=True, owner=True,
        properties={"body": {"type": "object"}}, required=("body",), held=("registry_factory",),
        reason="The form supplies About/Why fields; agents use the admitted decision.create operation directly."),
    _op("system.mcp_message", "system_service", "mcp_message", ("POST", "/api/mcp"), "mcp_http_endpoint",
        "Dispatch an authenticated MCP protocol message through the hub's services.", write=True, announces=True,
        reason="JSON-RPC transport, with authenticated palette and gates held by the edge; never an MCP tool itself.",
        properties={"message": {"type": "object"}}, required=("message",),
        held=("palette", "call_gate", "resource_gate", "run_agent", "client_host", "identity_label", "credential_identity", "origin_value")),
)
