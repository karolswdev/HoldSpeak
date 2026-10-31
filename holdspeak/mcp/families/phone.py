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
- ``phone.brief`` (PG-DIRECTION DIR1): the owner makes a briefing page for
  one held item of a Program and gets its link (the token is in the link
  only). Owner only; it reads nothing of the phone, so it works with the
  phone off. ``send: telegram`` also sends it to his paired chat (DIR5).
- ``phone.later`` (DIR4): Later on his own held item; owner only.
- ``phone.status`` gains ``telegram``, ``ladder`` and ``open_packages``.
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
        "name": "phone.brief",
        "description": (
            "Owner only. Make a briefing page for one held item (a Needs you row id, program:<program>:<item>) "
            "and return its page path /b/<token>, open for 24 hours, decided once. send telegram also sends it to "
            "his paired Telegram chat (eight lines, the choices as buttons, Later, the page link); none makes only "
            "the page. The phone push is not built yet."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "refs": {"type": "array", "items": {"type": "string"}, "minItems": 1, "maxItems": 1},
                "kind": {"type": ["string", "null"], "enum": ["item", None]},
                "send": {"type": ["string", "null"], "enum": ["none", "telegram", None]},
            },
            "required": ["refs"],
            "additionalProperties": False,
        },
    },
    {
        "name": "phone.later",
        "description": (
            "Owner only. Later on one held item (program:<program>:<item>): it leaves the Needs you count and comes "
            "back at the next touch. later is his words: empty (his default), in 1 hour, later 2h, at 13:00, at one, "
            "tonight, tomorrow. It decides nothing; at YOLO a core question's step is parked for now, Overturnable."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "ref": {"type": "string", "minLength": 1},
                "later": {"type": ["string", "null"]},
            },
            "required": ["ref"],
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
    if name == "phone.brief":
        from holdspeak.services.briefing_service import default_briefing_service

        args = dict(arguments or {})
        return default_briefing_service().make(principal, args.get("refs"), kind=args.get("kind") or "item",
                                               send=args.get("send"))
    if name == "phone.later":
        from holdspeak.services.reach_service import default_reach_service

        args = dict(arguments or {})
        return default_reach_service().later(principal, args.get("ref"), args.get("later"), via="desk")
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
    from holdspeak.services.reach_service import default_reach_service

    return {**service.status(principal), **default_reach_service().summary()}


__all__ = ["NAMES", "TOOLS", "dispatch"]
