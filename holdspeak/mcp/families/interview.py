"""Interview tools use the same durable controller as the Desk."""
from __future__ import annotations

from typing import Any

from jsonschema import Draft202012Validator

from holdspeak.db import get_database
from holdspeak.principals import Principal
from holdspeak.services.errors import ValidationError
from holdspeak.services.interview_contracts import SECTION_BY_ID
from holdspeak.services.interview_service import InterviewService

_STRING = {"type": "string", "minLength": 1, "maxLength": 1000}
_ID = {"type": "string", "minLength": 1, "maxLength": 128}
_BASE = {"thread_id": _ID, "expected_revision": {"type": "integer", "minimum": 0}}


def _tool(name: str, description: str, fields: dict[str, Any]) -> dict[str, Any]:
    return {"name": name, "description": description, "inputSchema": {
        "$id": f"holdspeak://mcp/{name}@1", "type": "object", "properties": fields,
        "required": list(fields), "additionalProperties": False,
    }}


TOOLS = [
    _tool("interview.get", "Read the current section, revision, saved facts, suggestion choices, and setup continuation.", {"thread_id": _ID}),
    _tool("interview.change_section", "Revisit a section without losing prior context. New section tools are offered on the next user turn.", {**_BASE, "section": {"enum": list(SECTION_BY_ID)}}),
    _tool("interview.record_fact", "Record or correct a scoped fact using an exact quote from a user message. Keep assumptions inferred. This does not authorize any action.", {
        **_BASE, "fact_id": _ID, "text": _STRING, "basis": {"enum": ["stated", "inferred"]},
        "source_message_id": _ID, "quote": _STRING,
    }),
    _tool("interview.suggest", "Save a useful suggestion connected to known facts. Describe evidence or hypotheses and prerequisites. Manual means conversational draft work; it does not install or authorize automation.", {
        **_BASE, "suggestion_id": _ID, "title": _STRING, "benefit": _STRING,
        "behavior": _STRING, "basis": _STRING, "prerequisites": _STRING,
        "fact_ids": {"type": "array", "items": _ID, "minItems": 1, "maxItems": 20, "uniqueItems": True},
        "feasibility": {"enum": ["manual", "needs_input", "needs_connection", "unsupported_idea"]},
    }),
]


def dispatch(name: str, arguments: dict[str, Any], principal: Principal) -> Any:
    InterviewService.require_owner(principal)
    tool = next((tool for tool in TOOLS if tool["name"] == name), None)
    if tool is None:
        raise LookupError(name)
    error = next(Draft202012Validator(tool["inputSchema"]).iter_errors(arguments), None)
    if error:
        raise ValidationError(error.message)
    service = InterviewService(get_database())
    def model_view() -> dict[str, Any]:
        path = service._db.threads.list_path(arguments["thread_id"])
        user_id = next((message.id for message in reversed(path) if message.role == "user" and not service._db.threads.is_draft_message(message.id)), "")
        return service.context(arguments["thread_id"], user_id)
    if name == "interview.get":
        return model_view()
    event = {key: value for key, value in arguments.items() if key not in _BASE}
    event["kind"] = {"interview.change_section": "section", "interview.record_fact": "fact", "interview.suggest": "suggestion"}[name]
    # The revision is the logical write slot. The controller supplies replay
    # identity so the model cannot accidentally borrow another domain's ID.
    result = service.command(principal, arguments["thread_id"], command_id=f"interview-mcp-revision-{arguments['expected_revision']}", expected_revision=arguments["expected_revision"], event=event)
    receipt = {key: result[key] for key in ("thread_id", "revision", "replayed")}
    if event["kind"] == "fact":
        receipt["fact"] = {key: result["facts"][event["fact_id"]][key] for key in ("id", "text", "basis")}
    elif event["kind"] == "suggestion":
        saved = next((s for s in result["suggestions"].values() if s["section"] == result["section"] and s["title"].casefold() == event["title"].strip().casefold()), result["suggestions"].get(event["suggestion_id"]))
        receipt["suggestion"] = {key: saved[key] for key in ("id", "title", "disposition", "feasibility")}
    else:
        receipt.update(section=result["section"], status=result["status"])
    return receipt
