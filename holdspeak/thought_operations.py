"""The Thought window's reads and its Open on the one declared contract (2026-11-09).

Carved beside ``holdspeak/operations.py`` (which imports it into
``DESCRIPTORS``), as ``automation_operations.py`` is. Each row states one verb
of the note window once: its call, its HTTP method and path, and its MCP tool
schema. ``web/routes/primitives/thoughts.py`` produces the routes and
``mcp/families/declared.py`` the tools from these rows, both through
``OperationRegistry.invoke``. The model-calling verbs (refine, stop,
answer-and-continue) stay where they are; no row here calls a model.

Each call answers the shape the hand-written route answered. Imported only
through ``holdspeak.operations``.
"""
from __future__ import annotations

from typing import Any, Callable, Mapping, Optional

from holdspeak.operations import _CONTRACT_REFUSALS, OperationDescriptor
from holdspeak.services.errors import ValidationError

Call = Callable[[Any, Any, dict[str, Any]], Any]

_PRINCIPAL = "derived by the transport (HTTP auth middleware; MCP auth resolver) and passed to the service unchanged"
_REFUSALS = _CONTRACT_REFUSALS + ("NotFound: unknown thought, note or review", "ServiceError: the service's codes")
_ID = {"type": "string", "minLength": 1}


def _open_note(service: Any, principal: Any, args: dict[str, Any]) -> Any:
    if set(args) - {"note_id"}:
        raise ValidationError("thought open-note schema is closed", code="note_open_request_invalid")
    return service.open_note(principal, note_id=args.get("note_id"))


def _op(name: str, service: str, method: str, http: tuple[str, str], handler: str, call: Call, description: str,
        *, write: bool = False, properties: Optional[Mapping[str, Any]] = None,
        required: tuple[str, ...] = ()) -> OperationDescriptor:
    ids = [part[1:-1] for part in http[1].split("/") if part.startswith("{")]
    tool = {"type": "object", "properties": {**{key: _ID for key in ids}, **dict(properties or {})},
            "required": ids + list(required), "additionalProperties": False}
    return OperationDescriptor(
        name=name, version=1, description=description, args_schema={"type": "object"}, principal=_PRINCIPAL,
        effect="write" if write else "read", result="the service answer, in the route's envelope",
        refusals=_REFUSALS, completion="synchronous" + ("; one desk_changed frame (kind thought)" if write else ""),
        exposure=(f"http:{http[0]} {http[1]}", f"mcp:{name}"), service=service, method=method, call=call,
        http=http, handler=handler, tool_schema=tool,
        thread="effect_proposal" if write else "evidence_read",
    )


THOUGHT_OPERATIONS: tuple[OperationDescriptor, ...] = (
    _op("thought.for_note", "refinement_thought_service", "for_note", ("GET", "/api/thoughts/for-note/{note_id}"),
        "for_note", lambda s, p, a: s.for_note(p, a.get("note_id")),
        "Read which thought holds one note, and what it needs before it opens (owner only)."),
    _op("thought.open_note", "refinement_service", "open_note", ("POST", "/api/thoughts/open-note"), "open_note",
        _open_note,
        "Open a note in the note window: its thought, adopting a plain note and resuming a finished one.",
        write=True, properties={"note_id": _ID}, required=("note_id",)),
    _op("thought.original", "refinement_service", "get_original", ("GET", "/api/thoughts/{thought_id}/original"),
        "original", lambda s, p, a: s.get_original(p, thought_id=a.get("thought_id")),
        "Read one thought with its original words (the raw text it began as)."),
    _op("thought.review", "refinement_service", "review",
        ("GET", "/api/thoughts/{thought_id}/reviews/{review_result_id}"), "review",
        lambda s, p, a: s.review(p, thought_id=a.get("thought_id"), review_result_id=a.get("review_result_id")),
        "Read one review of a thought: its questions, findings and proposed text."),
)

__all__ = ["THOUGHT_OPERATIONS"]
