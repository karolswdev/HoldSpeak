"""Protocol-level MCP catalogue checks."""

import json
from types import SimpleNamespace

from holdspeak.mcp import server
from holdspeak.mcp import tools as mcp_tools
from holdspeak.mcp.server import handle_message


REQUIRED_TOOLS = {
    "workbench.list", "workbench.get", "workbench.create", "workbench.update",
    "workbench.delete", "workbench.update_item", "workbench.delete_item",
    "workbench.list_runs", "recipe.list", "recipe.get", "recipe.run", "recipe.chat",
    "zone.file", "zone.unfile", "zone.list_members", "kb.add_member",
    "kb.remove_member", "kb.list_members",
    "plugin_job.list", "plugin_job.summary", "plugin_job.retry", "plugin_job.cancel",
    "coder.list", "coder.get", "coder.audit", "memory.search",
    "settings.get", "settings.update",
    "cadence.status", "cadence.loops", "cadence.get_loop", "cadence.brief",
    "cadence.closeout", "cadence.history", "cadence.audit", "cadence.snooze",
    "cadence.set_status", "cadence.run_now", "cadence.apply_closeout",
    "sequence.run", "sequence.cancel", "workflow.run", "workflow.cancel",
}


def test_tools_list_exposes_pipeline_mcp_tools_with_closed_schemas() -> None:
    response = handle_message({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
    assert response is not None
    tools = response["result"]["tools"]
    names = {tool["name"] for tool in tools}
    assert REQUIRED_TOOLS <= names
    for tool in tools:
        schema = tool["inputSchema"]
        assert schema["type"] == "object"
        assert schema["additionalProperties"] is False


def test_pipeline_tools_dispatch_through_mcp_protocol(monkeypatch) -> None:
    class Workbenches:
        def __init__(self, db, **kw): pass
        def create_workbench(self, principal, *, name, **fields): return {"id": fields.get("id", "wb"), "name": name}
        def update_workbench(self, principal, workbench_id, **fields): return {"id": workbench_id, **fields}
        def update_item(self, principal, workbench_id, item_id, **fields): return {"id": item_id, **fields}
        def list_runs(self, principal, workbench_id): return [{"workbench_id": workbench_id}]

    class Recipes:
        def __init__(self, db, **kw): pass
        def list_recipes(self, principal): return [{"id": "recipe"}]
        def get_recipe(self, principal, recipe_id): return {"id": recipe_id}
        async def run(self, principal, recipe_id, *, input="", **options): return {"recipe_id": recipe_id, "input": input, **options}
        async def chat(self, principal, recipe_id, *, question, **options): return {"recipe_id": recipe_id, "question": question, **options}

    class Primitives:
        def __init__(self, db, **kw): pass
        def file_member(self, principal, directory_id, primitive_id): return {"directory_id": directory_id, "primitive_id": primitive_id}
        def unfile_member(self, principal, directory_id, primitive_id): return True
        def list_directory_members(self, principal, directory_id): return [{"directory_id": directory_id}]
        def add_kb_member(self, principal, kb_id, resource_ref): return {"kb_id": kb_id, "resource_ref": resource_ref}
        def remove_kb_member(self, principal, kb_id, resource_ref): return True
        def list_kb_members(self, principal, kb_id): return [{"kb_id": kb_id}]

    monkeypatch.setattr(mcp_tools, "get_database", lambda: object())
    monkeypatch.setattr(mcp_tools, "get_observer", lambda: None)
    monkeypatch.setattr(mcp_tools, "WorkbenchService", Workbenches)
    monkeypatch.setattr(mcp_tools, "RecipeService", Recipes)
    monkeypatch.setattr(mcp_tools, "PrimitiveService", Primitives)
    monkeypatch.setattr(mcp_tools, "MeetingService", lambda db, **kw: object())
    monkeypatch.setattr(mcp_tools, "ProfileService", lambda db, **kw: object())
    monkeypatch.setattr(mcp_tools, "DictationService", lambda db, **kw: object())
    monkeypatch.setattr(mcp_tools, "DeskService", lambda db, **kw: object())
    monkeypatch.setattr(server, "resolve_auth", lambda: SimpleNamespace(principal=object()))

    def call(name, arguments):
        response = handle_message({"jsonrpc": "2.0", "id": name, "method": "tools/call", "params": {"name": name, "arguments": arguments}})
        assert response is not None
        result = response["result"]
        assert result["isError"] is False
        return json.loads(result["content"][0]["text"])

    assert call("workbench.create", {"name": "Morning", "fields": {"id": "wb"}})["id"] == "wb"
    assert call("workbench.update", {"workbench_id": "wb", "fields": {"name": "Later"}})["id"] == "wb"
    assert call("workbench.update_item", {"workbench_id": "wb", "item_id": "item", "fields": {"status": "done"}})["id"] == "item"
    assert call("workbench.list_runs", {"workbench_id": "wb"}) == [{"workbench_id": "wb"}]
    assert call("recipe.list", {}) == [{"id": "recipe"}]
    assert call("recipe.get", {"recipe_id": "recipe"})["id"] == "recipe"
    assert call("recipe.run", {"recipe_id": "recipe", "input": "go", "options": {"max_tokens": 10}})["max_tokens"] == 10
    assert call("recipe.chat", {"recipe_id": "recipe", "question": "why", "options": {"egress_context": {"source": "mcp"}}})["egress_context"] == {"source": "mcp"}
    assert call("zone.file", {"directory_id": "dir", "primitive_id": "note:1"})["directory_id"] == "dir"
    assert call("zone.unfile", {"directory_id": "dir", "primitive_id": "note:1"}) == {"deleted": True, "id": "note:1"}
    assert call("zone.list_members", {"directory_id": "dir"}) == [{"directory_id": "dir"}]
    assert call("kb.add_member", {"kb_id": "kb", "ref": "note:1"})["resource_ref"] == "note:1"
    assert call("kb.remove_member", {"kb_id": "kb", "ref": "note:1"}) == {"deleted": True, "id": "note:1"}
    assert call("kb.list_members", {"kb_id": "kb"}) == [{"kb_id": "kb"}]
