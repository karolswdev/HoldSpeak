# PARKED 2026-11-09: The retired recipe.chat tool has no client; threads replaced it.
class _ParkedBody:
    _RECIPE_CHAT_OPTIONS_SCHEMA: dict[str, Any] = {
        "type": "object",
        "properties": {
            "history": {"type": "array"}, "grounding": {"type": "object"},
            "egress_context": {},
        },
        "additionalProperties": False,
    }
    
    TOOLS = [
        _workbench_tool("recipe.chat", "Ask an Agent recipe a question.", {"recipe_id": {"type": "string"}, "question": {"type": "string"}, "options": _RECIPE_CHAT_OPTIONS_SCHEMA}, ["recipe_id", "question"]),
    ]
    
    def dispatch():
        if name == "recipe.chat":
            # HS-151-02: recipe.chat RETIRED. The tool definition stays so tool
            # counts documented elsewhere remain stable.
            # HS-200-45 R6: it RAISES now. Returning the refusal made the sidecar
            # answer `isError: false`, so a caller read a permanent retirement as a
            # successful chat turn.
            raise ToolError(
                "recipe.chat is retired (HS-151-02) and will never run: threads "
                "replaced it. Post the turn to /api/threads/{id}/turns instead, or "
                "call thought.* for the refinement loop."
            )
