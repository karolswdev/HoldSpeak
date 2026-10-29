"""Phone family (2026-10-28, design §7): reach the owner on his phone.

Every tool reaches the one service the REST routes use
(``holdspeak.phone.service.default_phone_service``), with agentring's
etiquette coded, not only written (its ``skills/agentring/SKILL.md``):

- ``phone.send_message``: one line, at most 500 characters; a Program step's
  agent sends at most 3 an hour; a secret is refused.
- ``phone.get_replies``: his new replies, each once; it waits (``wait_s``)
  instead of polling, and says that silence is never consent.
- ``phone.call``: EGRESS (``tool_authority.py``). The owner's call rings; an
  agent's call waits for his press in Needs you, unless its Program may call
  and the level is not Secure. It returns when the call is over:
  ``{transcript, end_reason, duration_s, decision}``.
- ``phone.status``: the paired phones, the line, quiet hours, the last reach.
"""
from __future__ import annotations

from typing import Any

from holdspeak.principals import Principal

TOOLS: list[dict[str, Any]] = [
    {
        "name": "phone.send_message",
        "description": (
            "Send one short line to the owner's phone; he reads it on the lock screen and can reply. Use it for "
            "anything that can wait: a task finished or failed, a summary, a question with a clear default. At "
            "most 500 characters, no secrets. A Program step may send 3 an hour. Then wait for his answer with "
            "phone.get_replies."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "minLength": 1, "maxLength": 500},
                "reply_to": {"type": ["string", "null"], "description": "The message id this answers."},
                "program_step_id": {"type": ["string", "null"], "description": "Your Program step, if you are one."},
            },
            "required": ["text"],
            "additionalProperties": False,
        },
    },
    {
        "name": "phone.get_replies",
        "description": (
            "The owner's new replies from his phone, each returned once. With wait_s, waits up to that many "
            "seconds for one (300 to 900 after a question) instead of polling. No reply is not a yes: silence "
            "is never consent, so keep the safe default."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {"wait_s": {"type": "integer", "minimum": 0, "maximum": 3600}},
            "additionalProperties": False,
        },
    },
    {
        "name": "phone.call",
        "description": (
            "Ring the owner's phone; a voice says the reason, talks from the context, and takes his answer. Use "
            "it only when it is urgent or a message got no answer. reason: one sentence. context: what happened, "
            "the options, your advice, what you need from him and what not to decide; no ids, paths or links "
            "(they are read aloud). urgent only for security or data loss. It waits for his press in Needs you "
            "unless your Program may call. Returns the transcript, the end reason, the length and his decision."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "reason": {"type": "string", "minLength": 1, "maxLength": 200},
                "context": {"type": "string", "maxLength": 4000},
                "urgent": {"type": ["boolean", "null"]},
                "program_step_id": {"type": ["string", "null"]},
            },
            "required": ["reason"],
            "additionalProperties": False,
        },
    },
    {
        "name": "phone.status",
        "description": "Read the owner's phone: the paired phones, the line, quiet hours, the reach rules at the "
                       "desk's level, and the last reach.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
]

NAMES = frozenset(tool["name"] for tool in TOOLS)


def dispatch(name: str, arguments: dict[str, Any], principal: Principal) -> Any:
    """Route a tool call. Raises LookupError for unowned names."""
    if name not in NAMES:
        raise LookupError(name)
    from holdspeak.phone import phone_on
    from holdspeak.phone.service import PhoneRefused, default_phone_service

    if not phone_on():
        raise PhoneRefused("phone_off", "The phone is off on this hub.", 409)
    service = default_phone_service()
    args = dict(arguments or {})
    if name == "phone.send_message":
        return service.send_message(principal, str(args.get("text") or ""), args.get("reply_to") or None,
                                    program_step_id=args.get("program_step_id") or None)
    if name == "phone.get_replies":
        return service.get_replies(args.get("wait_s") or 0)
    if name == "phone.call":
        return service.call(principal, reason=str(args.get("reason") or ""), context=str(args.get("context") or ""),
                            urgent=bool(args.get("urgent")), wait=True,
                            program_step_id=args.get("program_step_id") or None)
    return service.status(principal)


__all__ = ["NAMES", "TOOLS", "dispatch"]
