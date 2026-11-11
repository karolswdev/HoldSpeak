# PARKED: no live HTTP caller; MCP retains the declared intent operations.
from holdspeak.dictation_operations import _op

PARKED_HTTP_OPERATIONS = (
    _op("intents.controls", "intent_controls", ("GET", "/api/intents/control"), "api_get_intent_controls",
        lambda s, p, a: s.intent_controls(p),
        "Read intent routing controls and the last owner preview. Owner-only.", owner_only=True),
    _op("intents.profile", "set_intent_profile", ("PUT", "/api/intents/profile"), "api_set_intent_profile",
        lambda s, p, a: s.set_intent_profile(p, a["profile"]),
        "Set the owner's intent routing profile.", write=True, owner_only=True, strict=True,
        blocking_io=True, authority="config", owner_press=True,
        properties={"profile": {"type": "string"}}, required=("profile",)),
    _op("intents.preview", "preview_intent_route", ("POST", "/api/intents/preview"), "api_preview_intent_route",
        lambda s, p, a: s.preview_intent_route(p, **a),
        "Preview an owner intent route, run its plugin chain and retain its preview history.",
        strict=True, write=True, owner_only=True, blocking_io=True, authority="egress", owner_press=True,
        properties={"profile": {"type": ["string", "null"]}, "threshold": {"type": ["number", "null"]},
                    "intent_scores": {"type": ["object", "null"], "additionalProperties": {"type": "number"}},
                    **{key: {"type": ["array", "null"], "items": {"type": "string"}}
                       for key in ("override_intents", "previous_intents", "tags")},
                    "transcript": {"type": ["string", "null"]}}),
)
