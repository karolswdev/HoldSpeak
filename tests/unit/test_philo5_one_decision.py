"""PHILO-5-01: one decision through one contract.

The fences, and what turns each one red:

* **In-hub identity** (:class:`TestOneInstanceInTheHub`) — the REAL hub app
  (``MeetingWebServer``) composes the contract once; the HTTP routes and MCP
  ``/api/mcp`` reach the same registry, bound to the same ``PrimitiveService``
  the hub composed. Deliberate mutation: bind a fresh ``PrimitiveService`` in
  ``composition.install_from_web_context`` -> the identity assertion fails.
* **Both transports go through invoke** — every decision call over HTTP and
  over MCP is recorded by the registry's own ``invoke``. Deliberate mutation:
  a route or the MCP branch that calls the service by hand -> the recording
  misses it.
* **Contract refusals** — unknown operation, authority in the arguments,
  invalid arguments: named ``OperationRefused`` codes, surfaced through both
  transports' existing envelopes.
* **Compatibility** — tool names, input schemas and palette behaviour unchanged;
  palette refusal proved THROUGH dispatch (``tools.py`` ``dispatch_for_palette``)
  and through the HTTP JSON-RPC handler (MCP-005), plus catalogue filtering.
* **The export** — ``docs/generated/operations.json`` equals the catalogue.
* **The residual set** — the committed identities equal the tree's census.
* **The Codex seams** live in ``test_philo5_codex_seams.py`` (it imports no
  new symbol, so it runs unchanged on a copy of main for its red).
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
TOKEN = "philo5-01-token"


def _load_script(name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    sys.modules[name] = module
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


# ── the real hub, in-process ────────────────────────────────────────────


@pytest.fixture
def hub(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """The REAL hub app over an isolated database; the root it installed."""
    import holdspeak.db.core as db_core
    from holdspeak.db import reset_database
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    monkeypatch.setattr(db_core, "DEFAULT_DB_PATH", tmp_path / "hub.db")
    reset_database()
    server = MeetingWebServer(
        WebRuntimeCallbacks(on_bookmark=MagicMock(), on_stop=MagicMock(),
                            get_state=MagicMock(return_value={})),
        auth_token=TOKEN,
    )
    root = composition.installed()
    assert root is not None and root.bare_root is False, "the hub installed no root"
    from starlette.testclient import TestClient

    client = TestClient(server.app, client=("127.0.0.1", 50000))
    client.headers.update({"Authorization": f"Bearer {TOKEN}"})
    yield server, root, client
    reset_database()
    composition.install(composition.bare(label="pytest"))


def _mcp(client: Any, name: str, arguments: dict[str, Any]) -> Any:
    resp = client.post("/api/mcp", json={
        "jsonrpc": "2.0", "id": 1, "method": "tools/call",
        "params": {"name": name, "arguments": arguments},
    })
    assert resp.status_code == 200, resp.text
    result = resp.json()["result"]
    return result["isError"], json.loads(result["content"][0]["text"])


class TestOneInstanceInTheHub:
    def test_both_transports_hold_the_one_registry_bound_to_the_hubs_instance(self, hub) -> None:
        _server, root, _client = hub
        ctx = root.web_context
        assert root.operations is not None
        assert ctx.operations is root.operations, "HTTP and MCP hold different registries"
        for name in ("decision.create", "decision.update", "decision.read", "decision.list"):
            assert root.operations.target(name) is root.primitive_service, name
            assert root.operations.target(name) is ctx.primitive_service, name
        # MCP dispatch resolves the SAME object, not a fresh binding.
        assert operations.for_runtime(lambda: pytest.fail("built a fresh one")) is root.operations
        assert operations.for_context(ctx) is root.operations

    def test_every_decision_call_over_http_and_mcp_goes_through_invoke(self, hub, monkeypatch) -> None:
        _server, root, client = hub
        registry = root.operations
        seen: list[str] = []
        real_invoke = registry.invoke

        def recording_invoke(principal: Any, name: str, args: Any = None) -> Any:
            seen.append(name)
            return real_invoke(principal, name, args)

        monkeypatch.setattr(registry, "invoke", recording_invoke)

        # HTTP: create, update, read, list (the hub's real route order).
        created = client.post("/api/decisions", json={"title": "Over HTTP", "status": "proposed"})
        assert created.status_code == 201, created.text
        http_id = created.json()["decision"]["id"]
        updated = client.put(f"/api/decisions/{http_id}", json={"status": "accepted"})
        assert updated.status_code == 200 and updated.json()["decision"]["status"] == "accepted"
        read = client.get(f"/api/decisions/{http_id}")
        assert read.status_code == 200 and read.json()["decision"]["id"] == http_id
        listed = client.get("/api/decisions")
        assert http_id in [d["id"] for d in listed.json()["decisions"]]
        http_calls = list(seen)
        assert http_calls == ["decision.create", "decision.update", "decision.read", "decision.list"]

        # MCP over /api/mcp: the same four, and they see the HTTP write.
        seen.clear()
        is_error, mcp_created = _mcp(client, "desk.create", {"kind": "decisions", "data": {"title": "Over MCP"}})
        assert is_error is False, mcp_created
        is_error, mcp_updated = _mcp(client, "desk.update", {"kind": "decisions", "id": mcp_created["id"], "data": {"status": "accepted"}})
        assert is_error is False and mcp_updated["status"] == "accepted"
        is_error, got = _mcp(client, "desk.get", {"kind": "decisions", "id": http_id})
        assert is_error is False and got["title"] == "Over HTTP"
        is_error, rows = _mcp(client, "desk.list", {"kind": "decisions"})
        assert {http_id, mcp_created["id"]} <= {row["id"] for row in rows}
        assert seen == ["decision.create", "decision.update", "decision.read", "decision.list"]

        # And HTTP reads the MCP write back (one database, one instance).
        back = client.get(f"/api/decisions/{mcp_created['id']}")
        assert back.status_code == 200 and back.json()["decision"]["status"] == "accepted"

    def test_the_http_envelopes_are_unchanged(self, hub) -> None:
        _server, _root, client = hub
        assert client.get("/api/decisions/nope").status_code == 404
        missing = client.put("/api/decisions/nope", json={"title": "x"})
        assert missing.status_code == 404 and missing.json() == {"error": "Unknown decision: nope"}
        bad = client.post("/api/decisions", json={"title": "t", "status": "nonsense"})
        assert bad.status_code == 400 and bad.json() == {"error": "invalid decision status: nonsense"}
        # The desk's rename sends `name` for a decision; it was accepted and
        # ignored before this contract and still is (not a new 400).
        made = client.post("/api/decisions", json={"title": "Keep"}).json()["decision"]
        renamed = client.put(f"/api/decisions/{made['id']}", json={"name": "ignored"})
        assert renamed.status_code == 200 and renamed.json()["decision"]["title"] == "Keep"
        assert client.post("/api/decisions", content=b"[]", headers={"Content-Type": "application/json"}).status_code == 400


def test_durable_state_survives_a_new_hub_over_the_same_database(tmp_path: Path, monkeypatch) -> None:
    """Across a restart the object differs; the durable row does not."""
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
        is_error, made = _mcp(first, "desk.create", {"kind": "decisions", "data": {"title": "Before restart"}})
        assert is_error is False
        second_root, second = boot()
        assert second_root.operations is not first_root.operations
        is_error, again = _mcp(second, "desk.get", {"kind": "decisions", "id": made["id"]})
        assert is_error is False and again["title"] == "Before restart"
        assert second.get(f"/api/decisions/{made['id']}").json()["decision"] == again
    finally:
        reset_database()
        composition.install(composition.bare(label="pytest"))


# ── the contract's own refusals ─────────────────────────────────────────


class _Primitives:
    """A bare real service over a real database (the registry binds to it)."""


@pytest.fixture
def registry(tmp_path: Path):
    from holdspeak.db import Database
    from holdspeak.services.primitive_service import PrimitiveService

    # PHILO-5-02: the catalogue grew past decisions; bind only what this
    # fixture holds (the lawful partial composition).
    return operations.bind_available({"primitive_service": PrimitiveService(Database(tmp_path / "r.db"))})


def test_the_catalogue_is_explicit_descriptors() -> None:
    names = [d.name for d in operations.DESCRIPTORS]
    # PHILO-5-01's four, then PHILO-5-02's loop, then PHILO-7-01's desk slice
    # -- an explicit list, no framework.
    assert names == [
        "decision.create", "decision.update", "decision.read", "decision.list",
        "meeting.list", "meeting.read", "meeting.import", "meeting.summary.run",
        "brief.generate", "brief.latest", "brief.shelf.write", "brief.shelf.read",
        "thought.create", "thought.save", "thought.read", "thought.workbench.read", "thought.list",
        # PHILO-7-01: the desk slice, one row per (kind, verb).
        "note.create", "note.read", "note.update", "note.delete", "note.list",
        "zone.create", "zone.read", "zone.update", "zone.delete", "zone.list",
        "kb.create", "kb.read", "kb.update", "kb.delete", "kb.list",
        # PHILO-7-02: membership, the remaining decision operations, the receipt read.
        "zone.file", "zone.unfile", "zone.members", "kb.member.add", "kb.member.remove", "kb.members",
        "decision.delete", "decision.status", "decision.supersede",
        "kernel.receipt.read",
    ]
    # decision.list takes the empty object; its one optional argument is the
    # HTTP limit (round two: it passes through instead of slicing 500 rows).
    from jsonschema import Draft202012Validator

    list_schema = dict(operations.DECISION_LIST.args_schema)
    Draft202012Validator(list_schema).validate({})
    assert set(list_schema["properties"]) == {"limit"} and list_schema["additionalProperties"] is False
    for descriptor in operations.DESCRIPTORS:
        assert descriptor.version == 1
        assert descriptor.effect in {"read", "write"}
        assert descriptor.refusals[:3] == ("unknown_operation", "invalid_arguments", "authority_in_arguments")
        assert descriptor.completion and descriptor.result and descriptor.exposure


def test_unknown_operation_is_a_named_refusal(registry) -> None:
    with pytest.raises(operations.OperationRefused) as exc:
        registry.invoke(OWNER, "decision.explode", {})
    assert exc.value.code == "unknown_operation"


@pytest.mark.parametrize("field", sorted(operations.AUTHORITY_FIELDS))
def test_an_authority_field_in_the_arguments_is_refused(registry, field) -> None:
    with pytest.raises(operations.OperationRefused) as exc:
        registry.invoke(OWNER, "decision.update", {"decision_id": "d", field: "owner"})
    assert exc.value.code == "authority_in_arguments"


def test_authority_is_refused_through_the_mcp_transport_too() -> None:
    from holdspeak.mcp.server import handle_message_for_principal

    response = handle_message_for_principal({
        "jsonrpc": "2.0", "id": 1, "method": "tools/call",
        "params": {"name": "desk.create", "arguments": {"kind": "decisions", "data": {"title": "x", "principal": "owner"}}},
    }, OWNER)
    result = response["result"]
    assert result["isError"] is True
    assert "the principal comes from the transport" in json.loads(result["content"][0]["text"])["error"]


def test_binding_fails_at_composition_not_on_first_call() -> None:
    with pytest.raises(RuntimeError, match="no primitive_service"):
        operations.bind({})
    with pytest.raises(RuntimeError, match="has no create_decision"):
        operations.bind({"primitive_service": _Primitives()})


# ── MCP compatibility: schemas, the decisions branch, palettes ─────────


def test_mcp_decisions_branch_validates_with_the_descriptor_schema() -> None:
    """The effective schema of ``desk.create kind=decisions`` IS the descriptor's.

    Pre-contract, an unknown field reached ``create_decision(**data)`` and
    failed as a Python ``TypeError``; now the descriptor refuses it by name.
    Deliberate mutation: bypass ``invoke`` in ``tools._primitive_create`` and
    this message disappears.
    """
    from holdspeak.mcp.tools import ToolError, dispatch

    with pytest.raises(ValueError) as exc:
        dispatch("desk.create", {"kind": "decisions", "data": {"title": "t", "bogus": 1}}, OWNER)
    assert not isinstance(exc.value, ToolError)
    assert isinstance(exc.value, operations.OperationRefused)
    assert exc.value.operation == "decision.create" and exc.value.code == "invalid_arguments"
    made = dispatch("desk.create", {"kind": "decisions", "data": {"title": "t"}}, OWNER)
    assert made["title"] == "t"


def test_published_desk_tool_schemas_are_unchanged_and_admit_every_contract_payload() -> None:
    from jsonschema import Draft202012Validator

    from holdspeak.mcp.tools import PRIMITIVE_KINDS, TOOLS

    by_name = {t["name"]: t["inputSchema"] for t in TOOLS}
    kind = {"type": "string", "enum": list(PRIMITIVE_KINDS)}
    assert by_name["desk.list"] == {"type": "object", "properties": {"kind": kind},
                                    "required": ["kind"], "additionalProperties": False}
    assert by_name["desk.get"]["required"] == ["kind", "id"]
    assert by_name["desk.create"]["properties"]["data"]["type"] == "object"
    assert by_name["desk.update"]["required"] == ["kind", "id", "data"]
    payload = {"title": "t", "status": "accepted", "tags": ["a"], "decided_at": None}
    Draft202012Validator(dict(operations.DECISION_CREATE.args_schema)).validate(payload)
    Draft202012Validator(by_name["desk.create"]).validate({"kind": "decisions", "data": payload})
    Draft202012Validator(by_name["desk.update"]).validate({"kind": "decisions", "id": "d", "data": payload})


def test_palette_refusal_through_dispatch_writes_nothing(tmp_path: Path, monkeypatch) -> None:
    from holdspeak.db import Database
    from holdspeak.mcp import tools as mcp_tools
    from holdspeak.mcp.tools import ToolError, dispatch_for_palette, tools_for_palette

    db = Database(tmp_path / "palette.db")
    monkeypatch.setattr(mcp_tools, "get_database", lambda: db)
    read_only = frozenset({"desk.list", "desk.get"})
    assert {t["name"] for t in tools_for_palette(read_only)} == set(read_only)
    with pytest.raises(ToolError, match="not in the configured palette"):
        dispatch_for_palette("desk.create", {"kind": "decisions", "data": {"title": "x"}}, OWNER, read_only)
    assert db.desk_decisions.list() == []
    assert dispatch_for_palette("desk.list", {"kind": "decisions"}, OWNER, read_only) == []
    writable = read_only | {"desk.create"}
    made = dispatch_for_palette("desk.create", {"kind": "decisions", "data": {"title": "x"}}, OWNER, writable)
    assert [d.id for d in db.desk_decisions.list()] == [made["id"]]


def test_palette_refusal_through_the_http_jsonrpc_handler_is_mcp_005() -> None:
    from holdspeak.mcp.server import handle_message_for_principal

    response = handle_message_for_principal({
        "jsonrpc": "2.0", "id": 7, "method": "tools/call",
        "params": {"name": "desk.update", "arguments": {"kind": "decisions", "id": "d", "data": {}}},
    }, OWNER, palette=frozenset({"desk.list"}))
    assert response["error"]["code"] == -32005
    assert response["error"]["data"] == {"code": "MCP-005", "tool": "desk.update"}


def test_other_kinds_still_take_the_generic_path(tmp_path: Path, monkeypatch) -> None:
    from holdspeak.db import Database
    from holdspeak.mcp import tools as mcp_tools
    from holdspeak.mcp.tools import dispatch

    db = Database(tmp_path / "notes.db")
    monkeypatch.setattr(mcp_tools, "get_database", lambda: db)
    note = dispatch("desk.create", {"kind": "notes", "data": {"title": "n"}}, OWNER)
    assert dispatch("desk.get", {"kind": "notes", "id": note["id"]}, OWNER)["title"] == "n"
    decision = dispatch("desk.create", {"kind": "decisions", "data": {"title": "d"}}, OWNER)
    assert dispatch("desk.delete", {"kind": "decisions", "id": decision["id"]}, OWNER) == {"deleted": True, "id": decision["id"]}


# ── the export and the residual set ─────────────────────────────────────


def test_operations_export_matches_the_catalogue() -> None:
    gen = _load_script("gen_operations_json")
    committed = (REPO / "docs" / "generated" / "operations.json").read_text(encoding="utf-8")
    assert committed == gen.render(), "regenerate: uv run python scripts/gen_operations_json.py"
    exported = json.loads(committed)["operations"]
    assert [op["name"] for op in exported] == [d.name for d in operations.DESCRIPTORS]
    for op, descriptor in zip(exported, operations.DESCRIPTORS):
        assert op["args_schema"] == json.loads(json.dumps(dict(descriptor.args_schema)))
        assert op["exposure"] == list(descriptor.exposure)


def test_the_residual_set_equals_the_trees_census() -> None:
    census = _load_script("residual_census")
    committed = json.loads(census.SET_PATH.read_text(encoding="utf-8"))
    assert census.check(REPO, committed) == []
    for entry in committed["entries"]:
        assert entry["reason"], entry


def test_the_residual_set_shrank_by_exactly_the_paid_decision_entries() -> None:
    census = _load_script("residual_census")
    committed = json.loads(census.SET_PATH.read_text(encoding="utf-8"))
    listed = {census._key(e) for e in committed["entries"]}
    paid = {census._key(e) for e in committed["paid"]}
    assert paid and not (paid & listed), "a paid entry is still listed"
    assert committed["baseline"]["residual_identities"] - len(paid) == len(listed)
    story01 = {census._key(e) for e in committed["paid"] if e["story"] == "PHILO-5-01"}
    assert len(story01) == 7
    assert all("decision" in key[2] or "decisions.py" in key[1] for key in story01)
    # Two measurements, never one: story 01 added no public tool; every tool a
    # later story exposed is named in public_tools_added.
    from holdspeak.mcp.tools import TOOLS

    added = committed.get("public_tools_added", [])
    assert not [a for a in added if a["story"] == "PHILO-5-01"]
    assert len({t["name"] for t in TOOLS}) == committed["baseline"]["public_tools"] + len(added)


def test_the_residual_fence_names_a_new_identity_and_a_stale_one() -> None:
    census = _load_script("residual_census")
    committed = json.loads(census.SET_PATH.read_text(encoding="utf-8"))
    dropped = dict(committed, entries=committed["entries"][1:])
    problems = census.check(REPO, dropped)
    assert len(problems) == 1 and problems[0].startswith("NEW residual identity")
    stale = dict(committed, entries=committed["entries"] + [
        {"transport": "mcp", "entry_point": "desk.create", "discriminator": "kind=decisions", "reason": "x"}])
    problems = census.check(REPO, stale)
    assert len(problems) == 1 and problems[0].startswith("PAID entry still listed")
