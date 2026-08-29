"""Protocol-level MCP catalogue checks."""

import json
from types import SimpleNamespace

import pytest

from holdspeak.mcp import server
from holdspeak.mcp import tools as mcp_tools
from holdspeak.mcp.server import handle_message


REQUIRED_TOOLS = {
    "workbench.list", "workbench.get", "workbench.create", "workbench.update",
    "workbench.delete", "workbench.update_item", "workbench.delete_item",
    "workbench.list_runs", "recipe.list", "recipe.get", "recipe.run", "recipe.chat",
    "zone.file", "zone.unfile", "zone.list_members", "kb.add_member",
    "kb.remove_member", "kb.list_members",
    "ask.resolve_grounding", "ask.run", "ask.cancel", "ask.keep",
    "plugin_job.list", "plugin_job.summary", "plugin_job.retry", "plugin_job.cancel",
    "coder.list", "coder.get", "coder.audit", "memory.search",
    "settings.get", "settings.update",
    "cadence.status", "cadence.loops", "cadence.get_loop", "cadence.brief",
    "cadence.closeout", "cadence.history", "cadence.audit", "cadence.snooze",
    "cadence.set_status", "cadence.run_now", "cadence.apply_closeout",
    "sequence.run", "sequence.cancel", "workflow.run", "workflow.cancel",
    "people.readiness", "people.relationship.list", "people.relationship.get",
    "people.grounding.get", "people.note.create",
    "people.relationship.create", "people.one_on_one.create", "people.agenda.add",
    "people.request.create", "people.request.accept", "people.commitment.transition",
    "watch.list", "watch.create", "watch.set_enabled", "watch.refresh", "watch.preview",
    "event.list", "reaction.presets", "reaction.list", "reaction.create", "reaction.set_enabled",
    "reaction.process",
    "model_library.get", "model_library.download", "model_library.add_to_library",
    "model_library.use_model_file", "model_library.connect_hosted_model",
    "model_library.define_endpoint", "model_library.connect_paired_device",
    "inference_assignment.summary", "inference_assignment.editor", "inference_assignment.set",
    "inference_assignment.preview_use_default", "inference_assignment.clear",
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


def test_retired_router_tools_are_absent_from_the_catalogue() -> None:
    names = {tool["name"] for tool in mcp_tools.TOOLS}
    retired = {
        "ask.models",
        "inference.download_and_use", "inference.use_existing_model",
        "destination.list", "destination.get", "destination.create",
        "destination.update", "destination.delete",
        "model_profile.list", "model_profile.get", "model_profile.create",
        "model_profile.bind", "model_profile.probe", "model_profile.unbind",
        "model_profile.delete",
    }
    assert not (names & retired)
    assert "inference.cancel_model_acquisition" in names


def test_retired_shapes_refuse_before_mcp_dispatch(monkeypatch) -> None:
    touched = []

    def no_database():
        touched.append("database")
        raise AssertionError("a retired shape reached MCP composition")

    monkeypatch.setattr(mcp_tools, "get_database", no_database)
    for name in (
        "inference.download_and_use", "inference.use_existing_model",
        "destination.list", "model_profile.bind", "ask.models",
    ):
        with pytest.raises(mcp_tools.ToolError, match="Unknown tool"):
            mcp_tools.dispatch(name, {}, object())
    for name, arguments in (
        ("ask.run", {"question": "no", "inference_target_id": "retired"}),
        ("sequence.run", {"chain_id": "chain", "inference_target_id": "retired"}),
        ("workflow.run", {"workflow_id": "workflow", "inference_target_id": "retired"}),
        ("recipe.run", {"recipe_id": "recipe", "options": {"inference_target_id": "retired"}}),
        # HS-150-02: recipe.chat retired — returns 410 before argument validation.
        ("workbench.create", {"name": "No", "fields": {"profile_id": "retired"}}),
        ("workbench.update", {"workbench_id": "wb", "fields": {"resolver_profile_id": "retired"}}),
    ):
        with pytest.raises(mcp_tools.ToolError, match="Invalid arguments"):
            mcp_tools.dispatch(name, arguments, object())
    assert touched == []


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
    # HS-150-02: recipe.chat retired — tool returns retired error instead
    # of dispatching to RecipeService.chat.
    assert call("recipe.chat", {"recipe_id": "recipe", "question": "why"})["error"] == "recipe_chat_retired"
    assert call("zone.file", {"directory_id": "dir", "primitive_id": "note:1"})["directory_id"] == "dir"
    assert call("zone.unfile", {"directory_id": "dir", "primitive_id": "note:1"}) == {"deleted": True, "id": "note:1"}
    assert call("zone.list_members", {"directory_id": "dir"}) == [{"directory_id": "dir"}]
    assert call("kb.add_member", {"kb_id": "kb", "ref": "note:1"})["resource_ref"] == "note:1"
    assert call("kb.remove_member", {"kb_id": "kb", "ref": "note:1"}) == {"deleted": True, "id": "note:1"}
    assert call("kb.list_members", {"kb_id": "kb"}) == [{"kb_id": "kb"}]
