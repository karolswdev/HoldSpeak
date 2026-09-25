"""PHILO-7-01: notes, zones and knowledge bases on the one contract.

The fences, and what turns each one red:

* **The slice table** — fifteen explicit descriptors, one per (kind, verb),
  each naming its real ``PrimitiveService`` method and its Article XI
  admission exactly as the phase status's admission table rules it (declared
  here; story 02 enforces). Deliberate mutations (``evidence-story-01.md``):
  drop a row from ``DESK_OPERATIONS`` -> the table fence fails; change one
  admission -> the admission fence fails.
* **One instance in the hub** — the REAL ``MeetingWebServer`` app binds all
  fifteen to the hub's ``PrimitiveService``; HTTP routes, MCP ``desk.*`` tools,
  the ``desk.verb`` aliases and the ``holdspeak://primitives/{kind}/{id}``
  resource are each recorded by the ONE registry's ``invoke``. Deliberate
  mutation: a route or MCP branch that calls the service by hand -> the
  recording misses it.
* **A Thought's note** — updated through HTTP and then MCP with its expected
  revisions; both calls are ``note.update``; the cursors move.
* **Durable state** across a new hub over the same database.
* **Authority unchanged** — an agent and a node principal write through the
  contract as they did on main (no owner-only refusal is added).
* **Palettes** — refusal through dispatch and through the JSON-RPC handler,
  and catalogue filtering, for these kinds.
* **The residual set** — exactly the enumerated identities 2-5, 7-24, 26-27
  and 34-36 are paid; the public tool count is unchanged (a separate
  measurement).
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from holdspeak import operations
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.runtime import composition

REPO = Path(__file__).resolve().parents[2]
OWNER = Principal(PrincipalKind.OWNER, "owner")
TOKEN = "philo7-01-contract"

SLICE = (
    "note.create", "note.read", "note.update", "note.delete", "note.list",
    "zone.create", "zone.read", "zone.update", "zone.delete", "zone.list",
    "kb.create", "kb.read", "kb.update", "kb.delete", "kb.list",
)

#: The phase status's admission table, row by row (story 02 enforces it).
ADMISSION_TABLE = {
    "note.create": ("exempt", ()),
    "note.read": ("exempt", ()),
    "note.update": ("exempt", ()),
    "note.delete": ("admitted_if", ()),  # a Thought's note: stored state, not an argument
    "note.list": ("exempt", ()),
    "zone.create": ("admitted_if", ("directory_id",)),
    "zone.read": ("exempt", ()),
    "zone.update": ("admitted_if", ("parent_id",)),
    "zone.delete": ("admitted", ()),
    "zone.list": ("exempt", ()),
    "kb.create": ("admitted_if", ("member_ids", "kb_id")),
    "kb.read": ("exempt", ()),
    "kb.update": ("admitted_if", ("member_ids",)),
    "kb.delete": ("exempt", ()),
    "kb.list": ("exempt", ()),
}


def _load_script(name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    sys.modules[name] = module
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


# ── the slice table ─────────────────────────────────────────────────────


def _descriptor(name: str) -> operations.OperationDescriptor:
    return {d.name: d for d in operations.DESCRIPTORS}[name]


def test_the_slice_is_fifteen_explicit_rows_each_naming_a_real_method() -> None:
    from holdspeak.services.primitive_service import PrimitiveService

    names = [d.name for d in operations.DESCRIPTORS]
    # PHILO-7-02 adds the membership rows (zone.file ... kb.members) after these.
    assert [n for n in names if n.split(".")[0] in {"note", "zone", "kb"}][:len(SLICE)] == list(SLICE)
    rows = {(kind, verb): op for (kind, verb), op in operations.DESK_OPERATIONS.items() if kind != "decision"}
    assert sorted(rows.values()) == sorted(SLICE), "a slice operation has no (kind, verb) row"
    for name in SLICE:
        descriptor = _descriptor(name)
        assert descriptor.service == "primitive_service"
        # The method is a literal attribute of the service, never built from a kind.
        assert callable(PrimitiveService.__dict__.get(descriptor.method)), (name, descriptor.method)
        assert descriptor.refusals[:3] == ("unknown_operation", "invalid_arguments", "authority_in_arguments")
        assert descriptor.owner_only is False, f"{name}: no owner-only refusal where main accepted"
        assert descriptor.result and descriptor.completion and descriptor.exposure
    # Thought-owned note behaviour is declared on the note rows.
    for name in ("note.update", "note.delete"):
        descriptor = _descriptor(name)
        assert "retry cursors" in descriptor.result
        assert any("thought_expected_revision_required" in r for r in descriptor.refusals)
    assert "thought_expected_revision_required" in " ".join(_descriptor("note.create").refusals)


@pytest.mark.parametrize("name", SLICE)
def test_each_row_declares_its_admission_as_ruled(name) -> None:
    admission = _descriptor(name).admission
    assert admission is not None, f"{name} declares no admission"
    assert (admission.rule, admission.arguments) == ADMISSION_TABLE[name]
    assert admission.condition
    for argument in admission.arguments:
        assert argument in _descriptor(name).args_schema["properties"], (name, argument)


#: Round two (Astra finding 2): the condition's SEMANTICS, not only its words.
#: (operation, validated arguments, admitted?) -- every accepted form.
ADMISSION_PROBES = [
    ("kb.create", {"name": "K"}, False),
    ("kb.create", {"name": "K", "kb_id": None, "member_ids": []}, False),  # the HTTP adapter's empty create
    ("kb.create", {"name": "K", "member_ids": ["note:a"]}, True),
    ("kb.create", {"name": "K", "member_ids": {"note:n": True}}, True),   # a mapping: its keys are filed
    ("kb.create", {"name": "K", "kb_id": "k1"}, True),
    ("kb.update", {"kb_id": "k", "name": "K2"}, False),
    ("kb.update", {"kb_id": "k", "name": "K2", "member_ids": None}, False),  # the HTTP adapter's rename
    ("kb.update", {"kb_id": "k", "member_ids": {"note:n": True}}, True),
    ("kb.update", {"kb_id": "k", "member_ids": {}}, True),                 # removes every member
    ("kb.update", {"kb_id": "k", "member_ids": []}, True),
    ("zone.create", {"name": "Z"}, False),
    ("zone.create", {"name": "Z", "directory_id": None, "parent_id": None}, False),
    ("zone.create", {"name": "Z", "directory_id": "d"}, True),
    ("zone.update", {"directory_id": "d", "name": "N"}, False),
    ("zone.update", {"directory_id": "d", "parent_id": None}, True),
    ("zone.update", {"directory_id": "d", "parent_id": "p"}, True),
    ("zone.delete", {"directory_id": "d"}, True),
    ("kb.delete", {"kb_id": "k"}, False),
    ("note.update", {"note_id": "n", "title": "t"}, False),
]


@pytest.mark.parametrize(("name", "args", "admitted"), ADMISSION_PROBES,
                         ids=[f"{p[0]}:{json.dumps(p[1], sort_keys=True)}" for p in ADMISSION_PROBES])
def test_the_admission_condition_classifies_every_accepted_form(name, args, admitted) -> None:
    from jsonschema import Draft202012Validator

    descriptor = _descriptor(name)
    Draft202012Validator(dict(descriptor.args_schema)).validate(args)  # an accepted input
    assert descriptor.admission.admits(args) is admitted


def test_a_thoughts_note_delete_is_decided_by_stored_state() -> None:
    assert _descriptor("note.delete").admission.admits({"note_id": "n"}) is None


@pytest.mark.parametrize("tool_data", [
    {"name": "K", "member_ids": {"note:n": True}},
    {"name": "K", "member_ids": ["note:n"]},
])
def test_every_membership_producing_kb_create_is_admitted(tmp_path: Path, monkeypatch, tool_data) -> None:
    """The EFFECT fence: a create that writes a live membership is never declared exempt.

    Through the real MCP dispatch (main and built accept the mapping; the
    acceptance is preserved), then the real database: a live
    ``knowledge_memberships`` row exists, and the declaration admits the call.
    """
    from holdspeak.db import Database
    from holdspeak.mcp import tools as mcp_tools
    from holdspeak.mcp.tools import dispatch

    db = Database(tmp_path / "kb-effect.db")
    monkeypatch.setattr(mcp_tools, "get_database", lambda: db)
    made = dispatch("desk.create", {"kind": "kbs", "data": tool_data}, OWNER)
    live = [m.resource_ref for m in db.knowledge_memberships.list_for_knowledge(made["id"])]
    assert live == ["note:n"], live
    assert _descriptor("kb.create").admission.admits(tool_data) is True


def test_a_mapping_kb_update_changes_memberships_and_is_admitted(tmp_path: Path, monkeypatch) -> None:
    from holdspeak.db import Database
    from holdspeak.mcp import tools as mcp_tools
    from holdspeak.mcp.tools import dispatch

    db = Database(tmp_path / "kb-update-effect.db")
    monkeypatch.setattr(mcp_tools, "get_database", lambda: db)
    made = dispatch("desk.create", {"kind": "kbs", "data": {"name": "K", "member_ids": ["note:a"]}}, OWNER)
    data = {"member_ids": {"note:b": True}}
    dispatch("desk.update", {"kind": "kbs", "id": made["id"], "data": data}, OWNER)
    assert [m.resource_ref for m in db.knowledge_memberships.list_for_knowledge(made["id"])] == ["note:b"]
    assert _descriptor("kb.update").admission.admits({"kb_id": made["id"], **data}) is True


def test_the_export_carries_the_admission() -> None:
    exported = {op["name"]: op for op in json.loads((REPO / "docs/generated/operations.json").read_text())["operations"]}
    for name in SLICE:
        rule, arguments = ADMISSION_TABLE[name]
        assert exported[name]["admission"]["rule"] == rule
        assert exported[name]["admission"]["arguments"] == list(arguments)


def test_an_id_inside_update_data_is_refused_by_name() -> None:
    for operation, field in (("note.update", "note_id"), ("zone.update", "directory_id"), ("kb.update", "kb_id")):
        with pytest.raises(operations.OperationRefused) as exc:
            operations.update_args({field: "other"}, "x", operation=operation, id_field=field)
        assert exc.value.code == "invalid_arguments" and exc.value.operation == operation


# ── the real hub ────────────────────────────────────────────────────────


@pytest.fixture
def hub(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    import holdspeak.db.core as db_core
    from holdspeak.db import reset_database
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks
    from starlette.testclient import TestClient

    monkeypatch.setattr(db_core, "DEFAULT_DB_PATH", tmp_path / "hub.db")
    reset_database()
    server = MeetingWebServer(
        WebRuntimeCallbacks(on_bookmark=MagicMock(), on_stop=MagicMock(),
                            get_state=MagicMock(return_value={})),
        auth_token=TOKEN,
    )
    root = composition.installed()
    assert root is not None and root.bare_root is False
    client = TestClient(server.app, client=("127.0.0.1", 50000))
    client.headers.update({"Authorization": f"Bearer {TOKEN}"})
    yield root, client
    reset_database()
    composition.install(composition.bare(label="pytest"))


def _mcp(client: Any, name: str, arguments: dict[str, Any]) -> tuple[bool, Any]:
    resp = client.post("/api/mcp", json={
        "jsonrpc": "2.0", "id": 1, "method": "tools/call",
        "params": {"name": name, "arguments": arguments},
    })
    assert resp.status_code == 200, resp.text
    result = resp.json()["result"]
    return result["isError"], json.loads(result["content"][0]["text"])


def _resource(client: Any, uri: str) -> Any:
    resp = client.post("/api/mcp", json={"jsonrpc": "2.0", "id": 2, "method": "resources/read", "params": {"uri": uri}})
    return json.loads(resp.json()["result"]["contents"][0]["text"])


def _record(root: Any, monkeypatch: pytest.MonkeyPatch) -> list[str]:
    seen: list[str] = []
    real_invoke = root.operations.invoke

    def recording_invoke(principal: Any, name: str, args: Any = None, **kwargs: Any) -> Any:
        seen.append(name)
        return real_invoke(principal, name, args, **kwargs)

    monkeypatch.setattr(root.operations, "invoke", recording_invoke)
    return seen


def test_every_slice_operation_is_bound_to_the_hubs_one_instance(hub) -> None:
    root, _client = hub
    ctx = root.web_context
    assert ctx.operations is root.operations
    for name in SLICE:
        assert root.operations.target(name) is root.primitive_service, name
        assert root.operations.target(name) is ctx.primitive_service, name
    assert operations.for_runtime(lambda: pytest.fail("built a fresh one")) is root.operations
    assert operations.for_context(ctx) is root.operations


_KINDS = {"notes": ("note", {"title": "N"}, {"title": "N2"}),
          "directories": ("zone", {"name": "Z"}, {"name": "Z2"}),
          "kbs": ("kb", {"name": "K"}, {"name": "K2"})}


@pytest.mark.parametrize("kind", sorted(_KINDS))
def test_http_mcp_verbs_and_the_resource_all_go_through_invoke(hub, monkeypatch, kind) -> None:
    root, client = hub
    prefix, create, rename = _KINDS[kind]
    seen = _record(root, monkeypatch)

    # HTTP: create, read, update, list, delete.
    made = client.post(f"/api/{kind}", json=create)
    assert made.status_code == 201, made.text
    made_row = made.json()[{"note": "note", "zone": "directory", "kb": "kb"}[prefix]]
    item = made_row["id"]
    assert client.get(f"/api/{kind}/{item}").status_code == 200
    assert client.put(f"/api/{kind}/{item}", json=rename).status_code == 200
    assert client.get(f"/api/{kind}").status_code == 200
    assert client.delete(f"/api/{kind}/{item}").status_code == 200
    assert seen == [f"{prefix}.{verb}" for verb in ("create", "read", "update", "list", "delete")]

    # MCP tools, the desk.verb aliases and the resource.
    seen.clear()
    is_error, over_mcp = _mcp(client, "desk.create", {"kind": kind, "data": create})
    assert is_error is False, over_mcp
    mcp_id = over_mcp["id"]
    assert _mcp(client, "desk.get", {"kind": kind, "id": mcp_id})[0] is False
    assert _mcp(client, "desk.update", {"kind": kind, "id": mcp_id, "data": rename})[0] is False
    assert _mcp(client, "desk.list", {"kind": kind})[0] is False
    read = _resource(client, f"holdspeak://primitives/{kind}/{mcp_id}")
    assert (read.get("directory") or read)["id"] == mcp_id
    field = "title" if prefix == "note" else "name"
    is_error, verb_made = _mcp(client, "desk.verb", {"verb_id": "desk.create", "arguments": {"kind": kind, "data": {field: "Third"}}})
    assert is_error is False, verb_made
    assert _mcp(client, "desk.verb", {"verb_id": "desk.update", "arguments": {"kind": kind, "id": verb_made["id"], "data": {field: "Fourth"}}})[0] is False
    assert _mcp(client, "desk.verb", {"verb_id": "desk.delete", "arguments": {"kind": kind, "id": verb_made["id"]}})[1] == {"deleted": True, "id": verb_made["id"]}
    assert _mcp(client, "desk.delete", {"kind": kind, "id": mcp_id})[1] == {"deleted": True, "id": mcp_id}
    assert seen == [f"{prefix}.{verb}" for verb in ("create", "read", "update", "list", "read", "create", "update", "delete", "delete")]


def test_a_thoughts_note_updates_through_both_transports_with_its_revisions(hub, monkeypatch) -> None:
    root, client = hub
    assert client.post("/api/directories", json={"id": "hs-seed-inbox", "name": "Inbox"}).status_code == 201
    thought = client.post("/api/thoughts", json={"request_id": "p7-1", "raw_text": "raw", "source": {"kind": "typed"}}).json()["thought"]
    note_id = thought["working_note"]["id"]
    seen = _record(root, monkeypatch)

    over_http = client.put(f"/api/notes/{note_id}", json={
        "expected_aggregate_revision": thought["aggregate_revision"],
        "expected_working_revision": thought["working_revision"], "body_markdown": "via HTTP"})
    assert over_http.status_code == 200, over_http.text
    after_http = over_http.json()["note"]
    assert after_http["working_revision"] == thought["working_revision"] + 1
    assert after_http["body_markdown"] == "via HTTP"

    is_error, after_mcp = _mcp(client, "desk.update", {"kind": "notes", "id": note_id, "data": {
        "expected_aggregate_revision": after_http["aggregate_revision"],
        "expected_working_revision": after_http["working_revision"], "body_markdown": "via MCP"}})
    assert is_error is False, after_mcp
    assert after_mcp["working_revision"] == after_http["working_revision"] + 1
    assert after_mcp["aggregate_revision"] > after_http["aggregate_revision"]
    assert {"state", "aggregate_revision", "lifecycle_revision", "working_revision", "attachment_revision"} <= after_mcp.keys()
    assert seen == ["note.update", "note.update"]

    # A stale cursor is refused by the Thought service, through the contract.
    is_error, stale = _mcp(client, "desk.update", {"kind": "notes", "id": note_id, "data": {
        "expected_aggregate_revision": after_http["aggregate_revision"],
        "expected_working_revision": after_http["working_revision"], "body_markdown": "stale"}})
    assert is_error is True and stale["code"] == "thought_revision_conflict", stale
    assert client.get(f"/api/notes/{note_id}").json()["note"]["body_markdown"] == "via MCP"


def test_durable_state_survives_a_new_hub_over_the_same_database(tmp_path: Path, monkeypatch) -> None:
    import holdspeak.db.core as db_core
    from holdspeak.db import reset_database
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks
    from starlette.testclient import TestClient

    monkeypatch.setattr(db_core, "DEFAULT_DB_PATH", tmp_path / "restart.db")

    def boot() -> tuple[Any, Any]:
        reset_database()
        server = MeetingWebServer(
            WebRuntimeCallbacks(on_bookmark=MagicMock(), on_stop=MagicMock(),
                                get_state=MagicMock(return_value={})), auth_token=TOKEN)
        client = TestClient(server.app, client=("127.0.0.1", 50000))
        client.headers.update({"Authorization": f"Bearer {TOKEN}"})
        return composition.installed(), client

    try:
        first_root, first = boot()
        made = {kind: _mcp(first, "desk.create", {"kind": kind, "data": data})[1]
                for kind, (_p, data, _r) in _KINDS.items()}
        second_root, second = boot()
        assert second_root.operations is not first_root.operations
        assert second_root.operations.target("note.read") is not first_root.operations.target("note.read")
        for kind, row in made.items():
            is_error, again = _mcp(second, "desk.get", {"kind": kind, "id": row["id"]})
            assert is_error is False, again
            assert (again.get("directory") or again)["id"] == row["id"]
            assert second.get(f"/api/{kind}/{row['id']}").status_code == 200
    finally:
        reset_database()
        composition.install(composition.bare(label="pytest"))


# ── authority, palettes ─────────────────────────────────────────────────


@pytest.mark.parametrize("kind", [PrincipalKind.AGENT, PrincipalKind.NODE])
def test_a_non_owner_principal_writes_as_it_did_on_main(tmp_path: Path, kind) -> None:
    """No owner-only refusal is added (the settled position; not a policy change)."""
    from holdspeak.db import Database
    from holdspeak.services.primitive_service import PrimitiveService

    registry = operations.bind_available({"primitive_service": PrimitiveService(Database(tmp_path / "p.db"))})
    principal = Principal(kind, "someone")
    note = registry.invoke(principal, "note.create", {"title": "n"})
    registry.invoke(principal, "note.update", {"note_id": note["id"], "title": "n2"})
    zone = registry.invoke(principal, "zone.create", {"name": "z"})
    registry.invoke(principal, "zone.update", {"directory_id": zone["id"], "name": "z2"})
    kb = registry.invoke(principal, "kb.create", {"name": "k"})
    registry.invoke(principal, "kb.update", {"kb_id": kb["id"], "name": "k2"})
    assert registry.invoke(principal, "note.delete", {"note_id": note["id"]}) is True
    assert registry.invoke(principal, "zone.delete", {"directory_id": zone["id"]}) is True
    assert registry.invoke(principal, "kb.delete", {"kb_id": kb["id"]}) is True


@pytest.mark.parametrize("kind", ["notes", "directories", "kbs"])
def test_palette_refusal_through_dispatch_writes_nothing(tmp_path: Path, monkeypatch, kind) -> None:
    from holdspeak.db import Database
    from holdspeak.mcp import tools as mcp_tools
    from holdspeak.mcp.tools import ToolError, dispatch_for_palette, tools_for_palette

    db = Database(tmp_path / "palette.db")
    monkeypatch.setattr(mcp_tools, "get_database", lambda: db)
    read_only = frozenset({"desk.list", "desk.get"})
    assert {t["name"] for t in tools_for_palette(read_only)} == set(read_only)
    data = {"notes": {"title": "x"}, "directories": {"name": "x"}, "kbs": {"name": "x"}}[kind]
    with pytest.raises(ToolError, match="not in the configured palette"):
        dispatch_for_palette("desk.create", {"kind": kind, "data": data}, OWNER, read_only)
    with pytest.raises(ToolError, match="not in the configured palette"):
        dispatch_for_palette("desk.verb", {"verb_id": "desk.create", "arguments": {"kind": kind, "data": data}}, OWNER, read_only)
    assert dispatch_for_palette("desk.list", {"kind": kind}, OWNER, read_only) == []
    made = dispatch_for_palette("desk.create", {"kind": kind, "data": data}, OWNER, read_only | {"desk.create"})
    assert [row["id"] for row in dispatch_for_palette("desk.list", {"kind": kind}, OWNER, read_only)] == [made["id"]]


def test_palette_refusal_through_the_http_jsonrpc_handler_is_mcp_005() -> None:
    from holdspeak.mcp.server import handle_message_for_principal

    for name, arguments in (("desk.update", {"kind": "directories", "id": "z", "data": {"name": "n"}}),
                            ("desk.delete", {"kind": "notes", "id": "n"})):
        response = handle_message_for_principal({
            "jsonrpc": "2.0", "id": 7, "method": "tools/call",
            "params": {"name": name, "arguments": arguments},
        }, OWNER, palette=frozenset({"desk.list"}))
        assert response["error"]["code"] == -32005
        assert response["error"]["data"] == {"code": "MCP-005", "tool": name}


def test_workflows_and_chains_keep_the_generic_path(tmp_path: Path, monkeypatch) -> None:
    from holdspeak.db import Database
    from holdspeak.mcp import tools as mcp_tools
    from holdspeak.mcp.tools import dispatch

    assert not {kind for kind, _verb in operations.DESK_OPERATIONS} & {"workflow", "chain"}
    db = Database(tmp_path / "generic.db")
    monkeypatch.setattr(mcp_tools, "get_database", lambda: db)
    chain = dispatch("desk.create", {"kind": "chains", "data": {"name": "c"}}, OWNER)
    assert dispatch("desk.get", {"kind": "chains", "id": chain["id"]}, OWNER)["name"] == "c"
    workflow = dispatch("desk.create", {"kind": "workflows", "data": {"name": "w"}}, OWNER)
    assert dispatch("desk.delete", {"kind": "workflows", "id": workflow["id"]}, OWNER) == {"deleted": True, "id": workflow["id"]}


# ── the residual set ────────────────────────────────────────────────────

#: The phase status's enumerated identities this story pays (#2-5, 7-24,
#: 26-27, 34-36): notes, directories and kbs on desk.* and desk.verb, and the
#: three route fallback constructions.
_PAID_HERE = {
    *(("mcp", tool, f"kind={kind}") for tool in ("desk.create", "desk.delete", "desk.get", "desk.list", "desk.update")
      for kind in ("notes", "kbs", "directories")),
    *(("mcp", "desk.verb", f"verb_id={verb},kind={kind}") for verb in ("desk.create", "desk.update", "desk.delete")
      for kind in ("notes", "kbs", "directories")),
    ("http", "holdspeak/web/routes/primitives/directories.py::build_directories_router._svc", "PrimitiveService"),
    ("http", "holdspeak/web/routes/primitives/kbs.py::build_kbs_router._svc", "PrimitiveService"),
    ("http", "holdspeak/web/routes/primitives/notes.py::build_notes_router._svc", "PrimitiveService"),
}


def test_the_residual_set_paid_exactly_the_enumerated_identities() -> None:
    census = _load_script("residual_census")
    committed = json.loads(census.SET_PATH.read_text(encoding="utf-8"))
    paid = {census._key(e) for e in committed["paid"] if e["story"] == "PHILO-7-01"}
    assert len(_PAID_HERE) == 27
    assert paid == _PAID_HERE
    listed = {census._key(e) for e in committed["entries"]}
    assert not (paid & listed)
    assert census.check(REPO, committed) == []
    # PHILO-7-02 paid the rest of the slice (#1, #6, #25, #28-33) and moved the
    # measurements (320 -> 293 here, then -> 284): its own fence,
    # tests/unit/test_philo7_membership_decisions.py, holds the numbers.
    assert not [a for a in committed.get("public_tools_added", []) if a["story"] == "PHILO-7-01"]
