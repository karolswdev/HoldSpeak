# PARKED 2026-11-09: The permanently retired tool is parked with its refusal test.
class _ParkedBody:
        # HS-151-02: recipe.chat retired — the tool refuses instead of dispatching
        # to RecipeService.chat. HS-200-45 R6: the refusal is RAISED now, so the
        # sidecar reports `isError: true`; returning it made a permanent retirement
        # read as a successful chat turn.
        retired = handle_message({
            "jsonrpc": "2.0", "id": "recipe.chat", "method": "tools/call",
            "params": {"name": "recipe.chat", "arguments": {"recipe_id": "recipe", "question": "why"}},
        })
        assert retired is not None
        assert retired["result"]["isError"] is True
        assert "retired" in retired["result"]["content"][0]["text"]
