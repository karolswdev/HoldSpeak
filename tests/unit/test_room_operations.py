"""The Room's operations on the contract: descriptor rows, discovery and the same-key race.

Grouped by service (the fast diet, 2026-10-12). Moved verbatim from:
- test_philo9_contract.py
- test_philo9_discovery.py
- test_philo9_command_race.py
"""
from __future__ import annotations

# ── moved from tests/unit/test_philo9_contract.py ──
# PHILO-9-01: the Room's descriptor rows -- declared, bound, reached by both transports.
#
# * Every row names its real method on the hub's service and is bound to the
#   hub's ONE instance (the identity fence).
# * Every row declares its Article XI admission BY EFFECT exactly as the phase
#   status's admission table rules it (Q1); story 01 DECLARED it, PHILO-9-02
#   ENFORCES it: an admitted row makes one kernel operation with its receipt.
# * Every MCP tool and HTTP route of the slice passes through the ONE
#   ``OperationRegistry.invoke`` (a recording fence on the hub's registry).
# * The PROJECT palette refuses a tool outside it and admits the new tools,
#   through dispatch.

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
    "project.door.preview": ("admitted", ()),
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
    "project.door.preview": ("project_door_service", "preview"),
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
    # PHILO-9-02: every Room row is enforced (story 01 declared them false).
    assert admission.enforced is True, f"{name}: PHILO-9-02 enforces the Room's admission"
    exported = json.loads((Path(__file__).resolve().parents[2] / "docs" / "generated" / "operations.json").read_text())
    row = next(op for op in exported["operations"] if op["name"] == name)
    assert row["admission"]["rule"] == admission.rule and row["admission"]["enforced"] is admission.enforced


def test_the_door_create_is_admitted_only_with_sources() -> None:
    admission = _row("project.door.create").admission
    assert admission.admits({"outcome": "x"}) is False
    assert admission.admits({"outcome": "x", "sources": []}) is False
    assert admission.admits({"outcome": "x", "sources": [{"provider": "github", "scope": "o/r"}]}) is True


def test_the_door_preview_is_admitted_for_provider_validation() -> None:
    admission = _row("project.door.preview").admission
    assert admission is not None
    assert admission.admits({"outcome": "x", "pasted": "https://acme.atlassian.net/browse/KAN-1"}) is True


@pytest.mark.parametrize("name", sorted(BINDING))
def test_each_row_is_bound_to_the_hubs_one_instance(hub: Hub, name: str) -> None:
    field, method = BINDING[name]
    assert _row(name).service == field and _row(name).method == method
    assert hub.root.operations.target(name) is getattr(hub.root, field), name


def test_an_admitted_row_makes_one_kernel_operation_with_its_receipt(hub: Hub) -> None:
    """PHILO-9-02 flipped story 01's declaration: archive is now ONE operation and ONE receipt."""
    def ops() -> list[tuple[str, str]]:
        with hub.db._connection() as conn:
            return [(r[0], r[1]) for r in conn.execute(
                "SELECT o.name, r.outcome FROM kernel_operations o JOIN kernel_receipts r"
                " ON r.operation_id=o.operation_id ORDER BY o.created_at")]

    pid = hub.client.post("/api/projects", json={"name": "Declared"}).json()["project"]["id"]
    before = ops()
    is_error, archived = hub.mcp("project.archive", {"project_id": pid})
    assert not is_error, archived
    assert ops()[len(before):] == [("project.archive", "succeeded")]
    assert archived["operation_id"] and archived["receipt"]["state"] == "succeeded"


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
        ("POST", "/api/projects/door/preview", {"outcome": "Reach", "pasted": ""}, "project.door.preview"),
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


def test_preview_route_requires_owner_project_admission(hub: Hub) -> None:
    agent = _agent(hub, "PROJECT")
    refused = agent.post("/api/projects/door/preview", json={"outcome": "x", "pasted": ""})
    assert refused.status_code == 403, refused.text
    body = refused.json()
    assert body.get("code") == "project_delegation_required" or body.get("error") in {
        "owner_required", "principal_right_required",
    }, body


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


# ── moved from tests/unit/test_philo9_discovery.py ──
# PHILO-9-01 DISCOVERY: the catalogue names his project jobs (F12).
#
# The fence reads ONLY the real ``tools/list`` answer of a real hub (the
# ``MeetingWebServer`` app, over ``/api/mcp``): no source file, no repository
# file, no import of the tool module. From that answer alone it maps each of the
# owner's job phrases to one tool and its argument path, checks that every id
# argument of the Room's tools says where its value comes from (naming a tool
# the same answer lists), and checks that no project tool says or implies that
# the product sends, emails or posts the update (the Q0 ruling: delivery is his
# act, by copy and confirm).
#
# What this proves: the words are in the catalogue a client receives. What it
# does not prove: that a model finds them (story 06's cold-context Codex run).
#
# "mark it delivered" is story 02's criterion (Muad'Dib's ruling on PR #680,
# 2026-09-27, R4-2); it was pinned here as a strict expected failure, and
# PHILO-9-02 turned it red-to-green when it landed
# ``project.mark_update_delivered`` and removed the mark.
#
# This file imports no symbol the story adds, so it runs unchanged on an export
# of main (red there: the catalogue has none of the job words, and no item tool).

import re
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from holdspeak.runtime import composition

TOKEN = "philo9-01-discovery"

#: job phrase -> (tool, argument path: (argument, a word the path must name, or None)).
JOBS: dict[str, tuple[str, tuple[tuple[str, str | None], ...]]] = {
    "make a project": ("project.create", (("name", None),)),
    # PHILO-9-06 (the closing use): a cold Codex session asked to find a
    # project by name took memory.search, which never returns a project.
    "find a project by its name": ("project.list", ()),
    "add a milestone or a risk to a project": (
        "project.item.create", (("project_id", None), ("item_type", "milestone"), ("title", None), ("due_at", None)),
    ),
    "what needs me": ("desk.needs_you", ()),
    "draft my update": ("project.draft_update", (("project_id", None),)),
    "publish my update in the room": ("project.publish_update", (("update_id", None),)),
    "copy my update for delivery": ("project.list_updates", (("project_id", "body_md"),)),
}

#: The Room's tools whose id arguments must say where the value comes from.
ROOM_TOOLS = (
    "project.get", "project.get_room", "project.update", "project.archive", "project.restore",
    "project.link", "project.unlink", "project.open_review", "project.get_delta",
    "project.decide_proposal", "project.accept_review", "project.list_updates",
    "project.draft_update", "project.update_draft", "project.publish_update",
    "project.item.list", "project.item.create", "project.item.update", "project.item.transition",
    "project.resource.list", "project.resource.add", "project.resource.remove",
)
_ID_ARGUMENT = re.compile(r"(^id$|_id$)")
_FROM_TOOL = re.compile(r"\b(?:from|of an? [a-z ]+ from) ([a-z_]+\.[a-z_.]+)")
_SEND_WORDS = re.compile(r"\b(send|sends|sending|sent|email|emails|emailed|mail|mails|mailed|post|posts|posted|posting)\b")


@pytest.fixture(scope="module")
def catalogue(tmp_path_factory: pytest.TempPathFactory) -> list[dict[str, Any]]:
    """The real hub's ``tools/list`` answer, and nothing else."""
    import holdspeak.db.core as db_core
    from holdspeak.db import reset_database
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks
    from starlette.testclient import TestClient

    mp = pytest.MonkeyPatch()
    mp.setattr(db_core, "DEFAULT_DB_PATH", Path(tmp_path_factory.mktemp("discovery9")) / "hub.db")
    reset_database()
    try:
        server = MeetingWebServer(
            WebRuntimeCallbacks(on_bookmark=MagicMock(), on_stop=MagicMock(),
                                get_state=MagicMock(return_value={})),
            auth_token=TOKEN,
        )
        client = TestClient(server.app, client=("127.0.0.1", 50000))
        client.headers.update({"Authorization": f"Bearer {TOKEN}"})
        resp = client.post("/api/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}})
        assert resp.status_code == 200, resp.text
        return resp.json()["result"]["tools"]
    finally:
        reset_database()
        composition.install(composition.bare(label="pytest"))
        mp.undo()


def _by_name(catalogue: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {tool["name"]: tool for tool in catalogue}


@pytest.mark.parametrize("phrase", sorted(JOBS))
def test_each_job_phrase_maps_to_one_tool_and_its_argument_path(catalogue, phrase) -> None:
    tool_name, path = JOBS[phrase]
    naming = [t["name"] for t in catalogue if phrase in t.get("description", "").lower()]
    assert naming == [tool_name], f"{phrase!r} is named by {naming}, expected [{tool_name!r}]"
    tool = _by_name(catalogue)[tool_name]
    description = tool["description"].lower()
    properties = tool["inputSchema"]["properties"]
    for argument, value in path:
        assert argument in properties, f"{tool_name} has no argument {argument!r}"
        if value is None:
            continue
        words = description + " " + properties[argument].get("description", "").lower()
        assert value in words or value in (properties[argument].get("enum") or []), (phrase, argument, value)


def test_mark_it_delivered_maps_to_its_tool(catalogue) -> None:
    """PHILO-9-02 landed project.mark_update_delivered (R4-2): the strict expected failure is removed."""
    naming = [t["name"] for t in catalogue if "mark it delivered" in t.get("description", "").lower()]
    assert naming == ["project.mark_update_delivered"]


@pytest.mark.parametrize("tool_name", ROOM_TOOLS)
def test_every_id_argument_names_where_its_value_comes_from(catalogue, tool_name) -> None:
    tools = _by_name(catalogue)
    properties = tools[tool_name]["inputSchema"]["properties"]
    id_arguments = [name for name in properties if _ID_ARGUMENT.search(name) and name != "command_id"]
    assert id_arguments, tool_name
    for argument in id_arguments:
        description = properties[argument].get("description", "")
        sources = [s.rstrip(".") for s in _FROM_TOOL.findall(description)]
        assert sources, f"{tool_name}.{argument} does not say where its value comes from: {description!r}"
        assert all(source in tools for source in sources), (tool_name, argument, sources)


def test_memory_search_does_not_offer_to_find_a_project(catalogue) -> None:
    """PHILO-9-06: memory.search returns items, notes and meetings, never a
    project; its words send a project search to project.list."""
    description = _by_name(catalogue)["memory.search"]["description"].lower()
    assert "project.list" in description, description
    for phrase in ("find a project", "find your project", "search projects", "projects by"):
        assert phrase not in description, (phrase, description)


def test_no_project_tool_says_the_product_sends_the_update(catalogue) -> None:
    offenders = []
    for tool in catalogue:
        if not (tool["name"].startswith("project.") or tool["name"] == "desk.needs_you"):
            continue
        texts = [tool.get("description", "")] + [
            spec.get("description", "") for spec in tool["inputSchema"].get("properties", {}).values()]
        for text in texts:
            lowered = text.lower()
            if "update" in lowered and _SEND_WORDS.search(lowered):
                offenders.append((tool["name"], text))
    assert offenders == [], offenders


# ── moved from tests/unit/test_philo9_command_race.py ──
# PHILO-9-02 (law 9): the same-key race closed as a CLASS, not one site at a time.
#
# Carried from PHILO-9-01 (Codex Astra r3 on PR #680, finding 3, MISSED): the
# replay lookup ran BEFORE the write's transaction, so two callers with one key
# could both find it absent and both write. Two sites share the shape:
#
# * ``JournalStore.create_operation`` -- the kernel's replay by ``(principal,
#   idempotency_key)``: the loser's INSERT hit the UNIQUE constraint and raised
#   a raw ``IntegrityError`` (never a replay).
# * ``ProjectService`` -- ``_check_idempotency`` then ``_record_command ... ON
#   CONFLICT DO UPDATE``: two revisions and two change rows for one command.
#
# Each fence makes the interleaving deterministic, the same way on main and on
# the branch: both callers are held just past their lookup until the other has
# arrived (or one second has passed). On main both write; with the write lock
# taken before the lookup, the second caller cannot pass it until the first
# committed, finds the first's record, and replays.

import threading
import uuid
from pathlib import Path
from typing import Any

import pytest


class _Meet:
    """Hold each caller until both arrived, or ``timeout`` passed (never a deadlock)."""

    def __init__(self, parties: int = 2, timeout: float = 1.0) -> None:
        self._lock = threading.Lock()
        self._count = 0
        self._parties = parties
        self._all = threading.Event()
        self._timeout = timeout

    def arrive(self) -> None:
        with self._lock:
            self._count += 1
            if self._count >= self._parties:
                self._all.set()
        self._all.wait(self._timeout)


def _run_both(target: Any) -> list[Any]:
    results: list[Any] = [None, None]

    def worker(index: int) -> None:
        try:
            results[index] = target()
        except Exception as exc:  # the loser's raw failure is the red
            results[index] = exc

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(30)
    return results


def test_the_kernel_replay_lookup_holds_the_write_lock(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from holdspeak.db.core import Database
    from holdspeak.kernel import journal_atomic
    from holdspeak.kernel.journal import JournalStore

    database = Database(tmp_path / "race.db")
    store = JournalStore(database._connection)
    meet = _Meet()
    real_insert = journal_atomic.insert_operation

    def held_insert(conn: Any, values: Any, now: float) -> None:
        meet.arrive()  # past the lookup; the other caller now reaches its own
        real_insert(conn, values, now)

    monkeypatch.setattr(journal_atomic, "insert_operation", held_insert)

    def create() -> Any:
        operation_id = "op_" + uuid.uuid4().hex
        return store.create_operation({
            "operation_id": operation_id, "request_id": "req-1", "idempotency_key": "same-key",
            "name": "project.archive", "version": 1, "principal_kind": "owner",
            "principal_identity": "owner-session", "target_ref": "project:p1", "placement": "node:x",
            "envelope_sha256": "sha256:same", "policy_version": "1", "authority_basis": "b",
            "state": "admitting", "native_id": "n1",
        })

    results = _run_both(create)
    failures = [r for r in results if isinstance(r, Exception)]
    assert failures == [], f"the loser raised instead of replaying: {failures!r}"
    assert results[0]["operation_id"] == results[1]["operation_id"], "two callers, two operations for one key"
    with database._connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM kernel_operations WHERE idempotency_key='same-key'").fetchone()[0] == 1


def test_a_room_command_replay_holds_the_write_lock(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from holdspeak.db.core import Database
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services.project_service import ProjectService

    database = Database(tmp_path / "race.db")
    service = ProjectService(database)
    owner = Principal(PrincipalKind.OWNER, "owner-session")
    project = service.create_project(owner, {"name": "Race"})
    pid = project["id"]
    with database._connection() as conn:
        start = conn.execute("SELECT revision FROM projects WHERE id=?", (pid,)).fetchone()[0]
    note = "note:n-race"
    meet = _Meet()
    real_check = ProjectService._check_idempotency

    def held_check(self: Any, *args: Any, **kwargs: Any) -> Any:
        replay = real_check(self, *args, **kwargs)
        if replay is None:
            meet.arrive()  # both found the command absent
        return replay

    monkeypatch.setattr(ProjectService, "_check_idempotency", held_check)
    results = _run_both(lambda: service.add_resource(owner, pid, note, command_id="cmd-race-1"))
    failures = [r for r in results if isinstance(r, Exception)]
    assert failures == [], f"a caller raised: {failures!r}"
    with database._connection() as conn:
        revisions = conn.execute("SELECT revision FROM projects WHERE id=?", (pid,)).fetchone()[0]
        changes = conn.execute(
            "SELECT COUNT(*) FROM project_changes WHERE project_id=? AND change_kind='project.resource.linked'", (pid,),
        ).fetchone()[0]
    assert changes == 1, f"one command wrote {changes} change rows"
    assert revisions == start + 1, "one command bumped the revision twice"
    assert results[0] == results[1], "the replay did not answer the original response"


def test_a_room_command_race_on_a_delete_answers_the_original_true_twice(tmp_path: Path,
                                                                         monkeypatch: pytest.MonkeyPatch) -> None:
    """Astra r3's DELETE shape: the first answers true, the second false, the replay false. One answer: true."""
    from holdspeak.db.core import Database
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services.project_service import ProjectService

    database = Database(tmp_path / "race.db")
    service = ProjectService(database)
    owner = Principal(PrincipalKind.OWNER, "owner-session")
    pid = service.create_project(owner, {"name": "Race"})["id"]
    service.add_resource(owner, pid, "note:n-del")
    meet = _Meet()
    real_check = ProjectService._check_idempotency

    def held_check(self: Any, *args: Any, **kwargs: Any) -> Any:
        replay = real_check(self, *args, **kwargs)
        if replay is None:
            meet.arrive()
        return replay

    monkeypatch.setattr(ProjectService, "_check_idempotency", held_check)
    results = _run_both(lambda: service.remove_resource(owner, pid, "note:n-del", command_id="cmd-race-del"))
    assert results == [True, True], results
