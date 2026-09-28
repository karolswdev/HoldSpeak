"""PHILO-9-01: the Room's descriptor rows -- declared, bound, reached by both transports.

* Every row names its real method on the hub's service and is bound to the
  hub's ONE instance (the identity fence).
* Every row declares its Article XI admission BY EFFECT exactly as the phase
  status's admission table rules it (Q1); story 01 DECLARES it, PHILO-9-02
  ENFORCES it: until then an admitted row makes no kernel operation.
* Every MCP tool and HTTP route of the slice passes through the ONE
  ``OperationRegistry.invoke`` (a recording fence on the hub's registry).
* The PROJECT palette refuses a tool outside it and admits the new tools,
  through dispatch.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pytest

from holdspeak import operations
from holdspeak.runtime import composition

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_philo5_the_loop import Hub, _boot  # noqa: E402

REMOTE_HOST = "192.0.2.125"

#: The phase status's admission table (Q1, by effect), row by row.
ADMISSION_TABLE: dict[str, tuple[str, tuple[str, ...]]] = {
    "project.list": ("exempt", ()), "project.get": ("exempt", ()), "project.get_room": ("exempt", ()),
    "project.get_delta": ("exempt", ()), "project.list_updates": ("exempt", ()), "desk.needs_you": ("exempt", ()),
    "project.item.list": ("exempt", ()), "project.resource.list": ("exempt", ()),
    "project.create": ("exempt", ()),
    "project.door.create": ("admitted_if", ("sources",)),
    "project.update": ("exempt", ()),
    "project.archive": ("admitted", ()),
    "project.restore": ("exempt", ()),
    "project.link": ("admitted", ()), "project.unlink": ("admitted", ()),
    "project.open_review": ("exempt", ()),
    "project.decide_proposal": ("admitted", ()), "project.accept_review": ("admitted", ()),
    "project.draft_update": ("exempt", ()), "project.update_draft": ("exempt", ()),
    "project.publish_update": ("admitted", ()),
    "project.item.create": ("exempt", ()), "project.item.update": ("exempt", ()), "project.item.transition": ("exempt", ()),
    "project.resource.add": ("admitted", ()), "project.resource.remove": ("admitted", ()),
}

#: row -> (the RuntimeServices field, the method).
BINDING: dict[str, tuple[str, str]] = {
    "project.list": ("project_service", "list_projects"), "project.get": ("project_service", "get_project"),
    "project.get_room": ("project_service", "room"), "project.create": ("project_service", "create_project"),
    "project.door.create": ("project_door_service", "create"),
    "project.update": ("project_service", "update_project"), "project.archive": ("project_service", "archive_project"),
    "project.restore": ("project_service", "restore_project"), "project.link": ("project_service", "associate_meeting"),
    "project.unlink": ("project_service", "disassociate_meeting"),
    "project.open_review": ("project_delta_service", "open_review"),
    "project.get_delta": ("project_delta_service", "get_delta"),
    "project.decide_proposal": ("project_delta_service", "decide_proposal"),
    "project.accept_review": ("project_delta_service", "accept_review"),
    "project.list_updates": ("project_update_service", "list_updates"),
    "project.draft_update": ("project_update_service", "draft_update_command"),
    "project.update_draft": ("project_update_service", "save_update"),
    "project.publish_update": ("project_update_service", "publish_update"),
    "desk.needs_you": ("project_service", "needs_you"),
    "project.item.list": ("project_service", "list_items"), "project.item.create": ("project_service", "create_item"),
    "project.item.update": ("project_service", "update_item"),
    "project.item.transition": ("project_service", "transition_item"),
    "project.resource.list": ("project_service", "list_resources"),
    "project.resource.add": ("project_service", "add_resource"),
    "project.resource.remove": ("project_service", "remove_resource"),
}


@pytest.fixture
def hub(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from holdspeak.db import reset_database

    hub = _boot(tmp_path, monkeypatch)
    store = hub.server.app.state.agent_credentials
    for credential in store.list_credentials():
        store.revoke(credential.principal.identity)
    yield hub
    reset_database()
    composition.install(composition.bare(label="pytest"))


def _row(name: str) -> operations.OperationDescriptor:
    return {d.name: d for d in operations.DESCRIPTORS}[name]


def test_the_room_rows_are_the_charters_rows() -> None:
    assert [d.name for d in operations.ROOM_OPERATIONS] == list(BINDING)
    assert set(ADMISSION_TABLE) == set(BINDING)


@pytest.mark.parametrize("name", sorted(ADMISSION_TABLE))
def test_each_row_declares_its_admission_by_effect_and_story_02_enforces_it(name: str) -> None:
    admission = _row(name).admission
    assert admission is not None, name
    assert (admission.rule, admission.arguments) == ADMISSION_TABLE[name]
    assert admission.condition
    if admission.rule != "exempt":
        assert admission.enforced is False, f"{name}: PHILO-9-02 enforces the Room's admission"
    exported = json.loads((Path(__file__).resolve().parents[2] / "docs" / "generated" / "operations.json").read_text())
    row = next(op for op in exported["operations"] if op["name"] == name)
    assert row["admission"]["rule"] == admission.rule and row["admission"]["enforced"] is admission.enforced


def test_the_door_create_is_admitted_only_with_sources() -> None:
    admission = _row("project.door.create").admission
    assert admission.admits({"outcome": "x"}) is False
    assert admission.admits({"outcome": "x", "sources": []}) is False
    assert admission.admits({"outcome": "x", "sources": [{"provider": "github", "scope": "o/r"}]}) is True


@pytest.mark.parametrize("name", sorted(BINDING))
def test_each_row_is_bound_to_the_hubs_one_instance(hub: Hub, name: str) -> None:
    field, method = BINDING[name]
    assert _row(name).service == field and _row(name).method == method
    assert hub.root.operations.target(name) is getattr(hub.root, field), name


def test_an_admitted_row_makes_no_kernel_operation_until_story_02(hub: Hub) -> None:
    def ops() -> int:
        with hub.db._connection() as conn:
            return conn.execute("SELECT COUNT(*) FROM kernel_operations").fetchone()[0]

    pid = hub.client.post("/api/projects", json={"name": "Declared"}).json()["project"]["id"]
    before = ops()
    is_error, archived = hub.mcp("project.archive", {"project_id": pid})
    assert not is_error, archived
    assert ops() == before


@pytest.fixture
def recorded(hub: Hub, monkeypatch: pytest.MonkeyPatch) -> list[str]:
    registry = hub.root.operations
    names: list[str] = []
    real = registry.invoke

    def spy(principal: Any, name: str, args: Any = None, **kwargs: Any) -> Any:
        names.append(name)
        return real(principal, name, args, **kwargs)

    monkeypatch.setattr(registry, "invoke", spy)
    return names


def test_every_mcp_tool_and_http_route_of_the_slice_reaches_the_one_registry(hub: Hub, recorded: list[str]) -> None:
    c = hub.client
    pid = c.post("/api/projects", json={"name": "Reach"}).json()["project"]["id"]
    note = c.post("/api/notes", json={"title": "n"}).json()["note"]["id"]
    item = c.post(f"/api/projects/{pid}/items", json={"item_type": "milestone", "title": "M"}).json()["item"]["id"]
    update = c.post(f"/api/projects/{pid}/updates/draft", json={}).json()["update"]["id"]
    http = [
        ("GET", "/api/projects", None, "project.list"),
        ("GET", f"/api/projects/{pid}", None, "project.get"),
        ("GET", f"/api/projects/{pid}/room", None, "project.get_room"),
        ("PATCH", f"/api/projects/{pid}", {"description": "d"}, "project.update"),
        ("GET", f"/api/projects/{pid}/items", None, "project.item.list"),
        ("PATCH", f"/api/projects/{pid}/items/{item}", {"summary": "s"}, "project.item.update"),
        ("POST", f"/api/projects/{pid}/items/{item}/transition", {"verb": "missed"}, "project.item.transition"),
        ("PUT", f"/api/projects/{pid}/resources/note:{note}", {}, "project.resource.add"),
        ("GET", f"/api/projects/{pid}/resources", None, "project.resource.list"),
        ("DELETE", f"/api/projects/{pid}/resources/note:{note}", None, "project.resource.remove"),
        ("POST", f"/api/projects/{pid}/reviews", None, "project.open_review"),
        ("GET", f"/api/projects/{pid}/delta", None, "project.get_delta"),
        ("GET", f"/api/projects/{pid}/updates", None, "project.list_updates"),
        ("PUT", f"/api/updates/{update}", {"body_md": "Text"}, "project.update_draft"),
        ("POST", f"/api/updates/{update}/publish", {}, "project.publish_update"),
        ("GET", "/api/desk/needs-you?fresh=1", None, "desk.needs_you"),
    ]
    for method, path, body, name in http:
        recorded.clear()
        resp = c.request(method, path, json=body) if body is not None else c.request(method, path)
        assert resp.status_code == 200, (path, resp.text)
        assert name in recorded, f"HTTP {method} {path} left the registry: {recorded}"
    mcp = [
        ("project.list", {}), ("project.get", {"project_id": pid}), ("project.get_room", {"project_id": pid}),
        ("project.create", {"name": "Via MCP"}), ("project.update", {"project_id": pid, "patch": {"description": "e"}}),
        ("project.get_delta", {"project_id": pid}), ("project.list_updates", {"project_id": pid}),
        ("project.draft_update", {"project_id": pid}), ("desk.needs_you", {}),
        ("project.item.list", {"project_id": pid}),
        ("project.item.create", {"project_id": pid, "item_type": "risk", "title": "R",
                                 "details": {"likelihood": "low", "impact": "low"}}),
        ("project.resource.list", {"project_id": pid}),
    ]
    for tool, args in mcp:
        recorded.clear()
        is_error, value = hub.mcp(tool, args)
        assert not is_error, (tool, value)
        assert recorded == [tool], f"MCP {tool} left the registry: {recorded}"


def _agent(hub: Hub, palette: str) -> Any:
    from starlette.testclient import TestClient

    assert hub.client.put("/api/settings/remote", json={"enabled": True}).status_code == 200
    issued = hub.client.post("/api/settings/remote/credentials", json={"identity": f"philo9-{palette.lower()}", "palette": palette})
    client = TestClient(hub.server.app, client=(REMOTE_HOST, 50000))
    client.headers.pop("x-holdspeak-token", None)
    client.headers.update({"Authorization": f"Bearer {issued.json()['token']}"})
    return client


def test_the_project_palette_refuses_outside_and_admits_the_new_tools_through_dispatch(hub: Hub) -> None:
    agent = _agent(hub, "PROJECT")
    pid = hub.client.post("/api/projects", json={"name": "Palette"}).json()["project"]["id"]
    refused = agent.post("/api/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                                           "params": {"name": "desk.create", "arguments": {"kind": "notes", "data": {}}}}).json()
    assert refused["error"]["data"]["code"] == "MCP-005", refused
    answered = agent.post("/api/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                                            "params": {"name": "project.item.list", "arguments": {"project_id": pid}}}).json()
    assert answered["result"]["isError"] is False, answered
    assert json.loads(answered["result"]["content"][0]["text"]) == {"items": [], "limit": 200, "offset": 0}


def test_the_named_difference_http_bodies_close_their_argument_names(hub: Hub) -> None:
    """The one recorded HTTP difference (the Phase 5 rule): an unknown body field
    was ignored before; the declared operation refuses it by name (400)."""
    c = hub.client
    refused = c.post("/api/projects", json={"name": "Named", "colour": "red"})
    assert refused.status_code == 400 and refused.json()["success"] is False, refused.text
    pid = c.post("/api/projects", json={"name": "Named"}).json()["project"]["id"]
    item = c.post(f"/api/projects/{pid}/items", json={"item_type": "milestone", "title": "M", "colour": "red"})
    assert item.status_code == 400 and item.json()["success"] is False, item.text
    made = c.post(f"/api/projects/{pid}/items", json={"item_type": "milestone", "title": "M"}).json()["item"]["id"]
    patch = c.patch(f"/api/projects/{pid}/items/{made}", json={"colour": "red"})
    assert patch.status_code == 400, patch.text
    # The fields HTTP accepted before are still accepted (created_by_ref, provenance_kind).
    kept = c.post(f"/api/projects/{pid}/items", json={"item_type": "milestone", "title": "M", "provenance_kind": "owner"})
    assert kept.status_code == 200, kept.text


#: Codex Astra r1 (P5): each newly CLOSED descriptor whose HTTP body used to be
#: passed whole to the service, and the service method that consumed it.
_CLOSED_BODIES = {
    "project.create": ("create_project", "payload"),
    "project.item.create": ("create_item", "payload"),
    "project.item.update": ("update_item", "patch"),
    "project.resource.add": ("add_resource", "body"),
}


def _consumed_keys(method: str, variable: str) -> set[str]:
    """Every ``<variable>.get("k")`` / ``"k" in <variable>`` / ``<variable>["k"]`` the method reads (AST census)."""
    import ast
    import inspect
    import textwrap

    from holdspeak.services.project_service import ProjectService

    tree = ast.parse(textwrap.dedent(inspect.getsource(getattr(ProjectService, method))))
    keys: set[str] = set()
    for node in ast.walk(tree):
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "get"
                and isinstance(node.func.value, ast.Name) and node.func.value.id == variable
                and node.args and isinstance(node.args[0], ast.Constant)):
            keys.add(node.args[0].value)
        elif (isinstance(node, ast.Compare) and isinstance(node.left, ast.Constant) and isinstance(node.left.value, str)
              and any(isinstance(op, ast.In) for op in node.ops)
              and any(isinstance(c, ast.Name) and c.id == variable for c in node.comparators)):
            keys.add(node.left.value)
        elif (isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name) and node.value.id == variable
              and isinstance(node.slice, ast.Constant)):
            keys.add(node.slice.value)
    return keys


@pytest.mark.parametrize("name", sorted(_CLOSED_BODIES))
def test_every_field_the_service_consumed_is_still_accepted(name: str) -> None:
    """Codex Astra r1 (P5): closing the argument names keeps every field the
    service CONSUMED before; only fields it never read are refused."""
    method, variable = _CLOSED_BODIES[name]
    consumed = _consumed_keys(method, variable)
    assert consumed, (name, method)
    schema = _row(name).args_schema
    accepted = set(schema["properties"])
    if name == "project.item.update":
        accepted = set(schema["properties"]["patch"]["properties"])
    missing = sorted(consumed - accepted)
    assert missing == [], f"{name} refuses fields {method} consumed: {missing}"
