"""PHILO-7-02 (step 1): membership and the remaining decision operations on the one contract.

The fences, and what turns each one red:

* **Nine explicit descriptors** -- ``zone.file``, ``zone.unfile``,
  ``zone.members``, ``kb.member.add``, ``kb.member.remove``, ``kb.members``,
  ``decision.delete``, ``decision.status``, ``decision.supersede`` -- each
  naming its real ``PrimitiveService`` method and its Article XI admission as
  the phase status's admission table rules it; plus the ONE new read,
  ``kernel.receipt.read`` (the MCP tool ``kernel.receipt``).
* **One instance, one ``invoke``** -- through the REAL hub
  (``MeetingWebServer``): every HTTP route, MCP tool and the
  ``holdspeak://zones/{id}/members`` resource of these operations is recorded
  by the ONE registry's ``invoke``. Red on a ``git archive`` copy of main: the
  recording is empty (the routes and tools called the service by hand).
* **Envelopes unchanged** -- each transport answers with the envelope it gave
  on main (plus ``operation_id`` and ``receipt`` for an admitted write).
* **The residual set** -- identities 1, 6, 25, 28-33 paid; 293 -> 284; the
  public tool count 228 -> 229, reported apart (the receipt read).
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import pytest

from holdspeak.runtime import composition

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_philo5_the_loop import Hub, _boot  # noqa: E402

NINE = (
    "zone.file", "zone.unfile", "zone.members", "kb.member.add", "kb.member.remove", "kb.members",
    "decision.delete", "decision.status", "decision.supersede",
)

#: The admission table, for these rows (phase status, "Article XI as ruled").
ADMISSION = {
    "zone.file": "admitted", "zone.unfile": "admitted", "zone.members": "exempt",
    "kb.member.add": "admitted", "kb.member.remove": "admitted", "kb.members": "exempt",
    "decision.delete": "admitted", "decision.status": "admitted", "decision.supersede": "admitted",
    "decision.create": "admitted", "decision.update": "admitted",
    "decision.read": "exempt", "decision.list": "exempt", "kernel.receipt.read": "exempt",
}

METHODS = {
    "zone.file": "file_member", "zone.unfile": "unfile_member", "zone.members": "list_directory_members",
    "kb.member.add": "add_kb_member", "kb.member.remove": "remove_kb_member", "kb.members": "list_kb_members",
    "decision.delete": "delete_decision", "decision.status": "update_decision_status",
    "decision.supersede": "supersede_decision",
}

#: The enumerated identities this story pays (phase status, "The enumerated identities").
PAID_HERE = {
    ("mcp", "decision.supersede", ""),                              # 1
    ("mcp", "desk.delete", "kind=decisions"),                       # 6
    ("mcp", "desk.verb", "verb_id=desk.delete,kind=decisions"),     # 25
    ("mcp", "kb.add_member", ""),                                   # 28
    ("mcp", "kb.list_members", ""),                                 # 29
    ("mcp", "kb.remove_member", ""),                                # 30
    ("mcp", "zone.file", ""),                                       # 31
    ("mcp", "zone.list_members", ""),                               # 32
    ("mcp", "zone.unfile", ""),                                     # 33
}


def _descriptors() -> dict[str, Any]:
    from holdspeak import operations

    return {d.name: d for d in operations.DESCRIPTORS}


def _load_script(name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    sys.modules[name] = module
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


@pytest.fixture
def hub(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from holdspeak.db import reset_database

    yield _boot(tmp_path, monkeypatch)
    reset_database()
    composition.install(composition.bare(label="pytest"))


@pytest.fixture
def recorded(hub: Hub, monkeypatch: pytest.MonkeyPatch) -> list[str]:
    registry = hub.root.operations
    seen: list[str] = []
    real_invoke = registry.invoke

    def recording_invoke(principal: Any, name: str, args: Any = None, **kwargs: Any) -> Any:
        seen.append(name)
        return real_invoke(principal, name, args, **kwargs)

    monkeypatch.setattr(registry, "invoke", recording_invoke)
    return seen


# ── the rows ────────────────────────────────────────────────────────────


@pytest.mark.parametrize("name", NINE)
def test_each_row_names_its_real_method_and_its_admission(name: str) -> None:
    from holdspeak.services.primitive_service import PrimitiveService

    descriptor = _descriptors()[name]
    assert descriptor.service == "primitive_service" and descriptor.method == METHODS[name]
    assert callable(PrimitiveService.__dict__.get(descriptor.method)), name
    assert descriptor.owner_only is False, f"{name}: no owner-only refusal where main accepted"
    assert descriptor.admission is not None and descriptor.admission.rule == ADMISSION[name]
    assert descriptor.refusals[:3] == ("unknown_operation", "invalid_arguments", "authority_in_arguments")
    assert descriptor.result and descriptor.completion and descriptor.exposure


def test_the_decision_rows_and_the_receipt_read_declare_their_admission() -> None:
    rows = _descriptors()
    for name in ("decision.create", "decision.update", "decision.read", "decision.list", "kernel.receipt.read"):
        assert rows[name].admission is not None and rows[name].admission.rule == ADMISSION[name], name
    read = rows["kernel.receipt.read"]
    assert read.effect == "read" and read.exposure == ("mcp:kernel.receipt",)
    # decision.status has no separately named MCP tool (the phase status's
    # deferred question, decided): HTTP only; MCP's desk.update {status} is decision.update.
    assert [e for e in rows["decision.status"].exposure if e.startswith("mcp")] == []


def test_decision_delete_joins_the_desk_table() -> None:
    from holdspeak import operations

    assert operations.DESK_OPERATIONS[("decision", "delete")] == "decision.delete"


# ── one instance, one invoke (red on main: the recording is empty) ───────


def test_the_nine_are_bound_to_the_hubs_one_instance(hub: Hub) -> None:
    root = hub.root
    for name in NINE:
        assert root.operations.target(name) is root.primitive_service, name
    assert root.operations.target("kernel.receipt.read") is root.kernel_read_service


def test_http_routes_go_through_invoke(hub: Hub, recorded: list[str]) -> None:
    client = hub.client
    note = client.post("/api/notes", json={"title": "n"}).json()["note"]
    zone = client.post("/api/directories", json={"name": "Z"}).json()["directory"]
    kb = client.post("/api/kbs", json={"name": "K"}).json()["kb"]
    decision = client.post("/api/decisions", json={"title": "D"}).json()["decision"]
    recorded.clear()

    filed = client.put(f"/api/directories/{zone['id']}/members/note:{note['id']}")
    assert filed.status_code == 200 and filed.json()["membership"]["primitive_id"] == f"note:{note['id']}"
    listed = client.get(f"/api/directories/{zone['id']}/members")
    assert listed.status_code == 200 and listed.json()["directory_id"] == zone["id"]
    assert [m["primitive_id"] for m in listed.json()["members"]] == [f"note:{note['id']}"]
    unfiled = client.delete(f"/api/directories/{zone['id']}/members/note:{note['id']}")
    assert unfiled.status_code == 200 and unfiled.json()["success"] is True
    added = client.put(f"/api/kbs/{kb['id']}/members/note:{note['id']}")
    assert added.status_code == 200 and added.json()["member"]["resource_ref"] == f"note:{note['id']}"
    assert [m["resource_ref"] for m in client.get(f"/api/kbs/{kb['id']}/members").json()["members"]] == [f"note:{note['id']}"]
    removed = client.delete(f"/api/kbs/{kb['id']}/members/note:{note['id']}")
    assert removed.status_code == 200 and removed.json()["removed"] is True
    status = client.put(f"/api/decisions/{decision['id']}/status", json={"status": "accepted"})
    assert status.status_code == 200 and status.json()["decision"]["status"] == "accepted"
    successor = client.post(f"/api/decisions/{decision['id']}/supersede")
    assert successor.status_code == 201 and successor.json()["decision"]["title"].startswith("Superseding")
    deleted = client.delete(f"/api/decisions/{decision['id']}")
    assert deleted.status_code == 200 and deleted.json()["success"] is True

    assert recorded == [
        "zone.file", "zone.members", "zone.unfile", "kb.member.add", "kb.members", "kb.member.remove",
        "decision.status", "decision.supersede", "decision.delete",
    ]


def test_mcp_tools_verbs_and_the_resource_go_through_invoke(hub: Hub, recorded: list[str]) -> None:
    note = hub.client.post("/api/notes", json={"title": "n"}).json()["note"]
    zone = hub.client.post("/api/directories", json={"name": "Z"}).json()["directory"]
    kb = hub.client.post("/api/kbs", json={"name": "K"}).json()["kb"]
    first = hub.client.post("/api/decisions", json={"title": "D1"}).json()["decision"]
    second = hub.client.post("/api/decisions", json={"title": "D2"}).json()["decision"]
    recorded.clear()
    ref = f"note:{note['id']}"

    is_error, filed = hub.mcp("zone.file", {"directory_id": zone["id"], "primitive_id": ref})
    assert is_error is False and filed["primitive_id"] == ref and filed["directory_id"] == zone["id"]
    is_error, members = hub.mcp("zone.list_members", {"directory_id": zone["id"]})
    assert is_error is False and [m["primitive_id"] for m in members] == [ref]
    assert [m["primitive_id"] for m in hub.resource(f"holdspeak://zones/{zone['id']}/members")] == [ref]
    is_error, unfiled = hub.mcp("zone.unfile", {"directory_id": zone["id"], "primitive_id": ref})
    assert is_error is False and (unfiled["deleted"], unfiled["id"]) == (True, ref)
    is_error, added = hub.mcp("kb.add_member", {"kb_id": kb["id"], "ref": ref})
    assert is_error is False and added["resource_ref"] == ref
    is_error, listed = hub.mcp("kb.list_members", {"kb_id": kb["id"]})
    assert is_error is False and [m["resource_ref"] for m in listed] == [ref]
    is_error, removed = hub.mcp("kb.remove_member", {"kb_id": kb["id"], "ref": ref})
    assert is_error is False and (removed["deleted"], removed["id"]) == (True, ref)
    is_error, successor = hub.mcp("decision.supersede", {"decision_id": first["id"]})
    assert is_error is False and successor["title"].startswith("Superseding")
    is_error, deleted = hub.mcp("desk.delete", {"kind": "decisions", "id": first["id"]})
    assert is_error is False and (deleted["deleted"], deleted["id"]) == (True, first["id"])
    is_error, verb = hub.mcp("desk.verb", {"verb_id": "desk.delete", "arguments": {"kind": "decisions", "id": second["id"]}})
    assert is_error is False and (verb["deleted"], verb["id"]) == (True, second["id"])

    assert recorded == [
        "zone.file", "zone.members", "zone.members", "zone.unfile", "kb.member.add", "kb.members",
        "kb.member.remove", "decision.supersede", "decision.delete", "decision.delete",
    ]


# ── the residual set and the public tool count (two measurements) ───────


def test_the_residual_set_paid_exactly_the_enumerated_identities() -> None:
    census = _load_script("residual_census")
    committed = json.loads(census.SET_PATH.read_text(encoding="utf-8"))
    paid = {census._key(e) for e in committed["paid"] if e["story"] == "PHILO-7-02"}
    assert paid == PAID_HERE
    listed = {census._key(e) for e in committed["entries"]}
    assert not (paid & listed)
    assert census.check(REPO, committed) == []
    measurements = committed["measurements"]
    assert (measurements["residual_identities"], measurements["residual_mcp"], measurements["residual_http"]) == (284, 223, 61)
    # A separate measurement: the receipt read is the one new public tool.
    assert measurements["public_tools"] == 229
    added = [a for a in committed["public_tools_added"] if a["story"] == "PHILO-7-02"]
    assert added == [{"story": "PHILO-7-02", "tool": "kernel.receipt", "operation": "kernel.receipt.read"}]


def test_a_new_residual_identity_turns_the_fence_red(tmp_path: Path) -> None:
    """Structural: a set that still lists a paid identity, or misses a new one, is red."""
    census = _load_script("residual_census")
    committed = json.loads(census.SET_PATH.read_text(encoding="utf-8"))
    stale = dict(committed)
    stale["entries"] = [e for e in committed["entries"] if e["entry_point"] != "workbench.run"]
    problems = census.check(REPO, stale)
    assert any("NEW residual identity" in p and "workbench.run" in p for p in problems), problems
