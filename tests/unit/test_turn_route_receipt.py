"""Owner pick 2026-10-05 (route in footer): a turn's lamp, host and model come
from its route execution receipt (the winning attempt's deployment, the #855
loopback rule), never the admitted plan.  A turn with no model call has no
lamp.  The Ask projection carries the same route on ``egress``."""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from holdspeak.db.core import Database
from holdspeak.inference_locality import served_route
from holdspeak.services.ask_service import AskService


def _deployment(db: Database, rid: str, *, boundary: str, endpoint: str = "", node: str = "", model: str = "m") -> None:
    with db._connection() as conn:
        conn.execute(
            "INSERT INTO deployment_revisions (id,destination_id,kind,engine,model,boundary,endpoint,node)"
            " VALUES (?,?,?,?,?,?,?,?)",
            (rid, "dest", "endpoint", "openai_compatible", model, boundary, endpoint, node),
        )


@pytest.fixture()
def db(tmp_path):
    db = Database(tmp_path / "route.db")
    _deployment(db, "lan", boundary="private_network", endpoint="http://192.168.1.43:8080/v1", model="qwen3.8-27b")
    _deployment(db, "loop", boundary="private_network", endpoint="http://127.0.0.1:11434/v1", model="qwen3.5-4b")
    _deployment(db, "loopdot", boundary="private_network", endpoint="http://localhost.:11434/v1", model="qwen3.5-4b")
    _deployment(db, "cloud", boundary="external_service", endpoint="https://api.openai.com/v1", model="gpt-5-mini")
    _deployment(db, "inproc", boundary="same_device", model="Qwen3.5 4B")
    _deployment(db, "mesh", boundary="private_mesh", node="studio-mac", model="qwen-mesh")
    return db


def _won(rid: str, boundary: str) -> dict:
    return {
        "attempts": [{"deployment_revision_id": rid, "boundary": boundary, "send_phase": "provider_returned"}],
        "winning_deployment_revision_id": rid,
        "winning_boundary": boundary,
    }


@pytest.mark.parametrize(
    ("rid", "boundary", "expected"),
    [
        ("lan", "private_network", {"lamp": "private_network", "host": "192.168.1.43", "model": "qwen3.8-27b"}),
        ("loop", "private_network", {"lamp": "local", "host": "", "model": "qwen3.5-4b"}),
        # #855: "localhost." is not pinned to loopback, so it is never LOCAL;
        # loopback_http.endpoint_lamp names an unknown name CLOUD.
        ("loopdot", "private_network", {"lamp": "cloud", "host": "localhost.", "model": "qwen3.5-4b"}),
        ("cloud", "external_service", {"lamp": "cloud", "host": "api.openai.com", "model": "gpt-5-mini"}),
        ("inproc", "same_device", {"lamp": "local", "host": "", "model": "Qwen3.5 4B"}),
        ("mesh", "private_mesh", {"lamp": "mesh", "host": "studio-mac", "model": "qwen-mesh"}),
    ],
)
def test_the_winning_deployment_names_the_route(db, rid, boundary, expected) -> None:
    with db._connection() as conn:
        assert served_route(conn, _won(rid, boundary)) == expected


def test_a_failed_turn_names_the_last_sent_attempt(db) -> None:
    receipt = {
        "attempts": [
            {"deployment_revision_id": "lan", "boundary": "private_network", "send_phase": "provider_returned"},
            {"deployment_revision_id": "cloud", "boundary": "external_service", "send_phase": "dispatch_intent"},
            {"deployment_revision_id": "inproc", "boundary": "same_device", "send_phase": "pre_send"},
        ],
        "winning_deployment_revision_id": None,
    }
    with db._connection() as conn:
        assert served_route(conn, receipt)["lamp"] == "cloud"


def test_no_model_call_no_lamp(db) -> None:
    receipt = {"attempts": [{"deployment_revision_id": "lan", "boundary": "private_network", "send_phase": "pre_send"}]}
    with db._connection() as conn:
        assert served_route(conn, receipt) == {"lamp": "", "host": "", "model": ""}
        assert served_route(conn, {"attempts": []}) == {"lamp": "", "host": "", "model": ""}


def test_not_a_route_receipt_returns_none(db) -> None:
    with db._connection() as conn:
        assert served_route(conn, {"id": "receipt_test", "outcome": "succeeded"}) is None
        assert served_route(conn, None) is None


def _route(rid: str, boundary: str) -> dict:
    return {"entries": [{"ordinal": 1, "profile_id": "p1", "deployment_revision_id": rid, "boundary": boundary}]}


def _payload() -> dict:
    return {"lens": "Ask", "context_ids": [], "context_titles": []}


@pytest.mark.parametrize(
    ("rid", "boundary", "egress"),
    [
        ("lan", "private_network", {"scope": "private_network", "host": "192.168.1.43"}),
        ("loop", "private_network", {"scope": "local"}),
        ("cloud", "external_service", {"scope": "cloud", "host": "api.openai.com"}),
    ],
)
def test_the_ask_projection_carries_the_served_route(db, rid, boundary, egress) -> None:
    receipt = {**_won(rid, boundary), "execution_id": "exec-0000a91f"}
    receipt["attempts"][0]["route_leg_ordinal"] = 1
    result = AskService._routed_projection(
        SimpleNamespace(_db=db), {"output": "answer"}, _payload(), receipt, _route(rid, boundary),
    )
    assert result["egress"] == egress
    # The receipt boundary stays on the placement, unchanged.
    assert result["actual_placement"]["boundary"] == boundary
    assert result["route_execution_receipt"]["execution_id"] == "exec-0000a91f"


# ── The chat turn: the receipt, not the admitted plan ──────────────────────


def _thread_service(db, broadcasts, receipt):
    import uuid

    from holdspeak.services.thread_service import ThreadService
    from tests.unit.test_thread_service import FakeAdoptionService

    class _Adoption(FakeAdoptionService):
        def execute_stream(self, *args, **kwargs):
            routed = super().execute_stream(*args, **kwargs)
            routed["receipt"] = {**receipt, "execution_id": "exec-" + uuid.uuid4().hex[:4] + "a91f"}
            return routed

    class _Broker:
        inference_adoption_service = _Adoption()

    return ThreadService(db, broadcast=lambda t, d: broadcasts.append((t, d)), broker=_Broker())


def _run_turn(svc):
    import asyncio
    import time

    from tests.unit.test_thread_service import OWNER

    thread = svc.create(title="Cutover risks")
    started = asyncio.run(svc.start_turn(OWNER, thread["id"], "List the risks."))
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        msg = svc._db.threads.get_message(started["assistant_message_id"])
        if msg and not msg.streaming:
            break
        time.sleep(0.05)
    return thread["id"], started["assistant_message_id"]


def test_a_chat_turn_names_where_its_bytes_went(db) -> None:
    # Admitted on same_device (the fake plan); the receipt says the LAN won.
    broadcasts: list = []
    svc = _thread_service(db, broadcasts, _won("lan", "private_network"))
    tid, mid = _run_turn(svc)
    done = [d for t, d in broadcasts if t == "thread_turn_done"][-1]
    assert (done["egress"], done["host"], done["model"]) == ("private_network", "192.168.1.43", "qwen3.8-27b")
    msg = db.threads.get_message(mid)
    assert (msg.egress_scope, msg.egress_host, msg.model_id) == ("private_network", "192.168.1.43", "qwen3.8-27b")
    wire = [m for m in svc.get(tid)["messages"] if m["id"] == mid][0]
    assert (wire["egress_scope"], wire["egress_host"]) == ("private_network", "192.168.1.43")


def test_a_chat_turn_with_no_model_call_has_no_lamp(db) -> None:
    broadcasts: list = []
    receipt = {"attempts": [{"deployment_revision_id": "lan", "boundary": "private_network", "send_phase": "pre_send"}]}
    svc = _thread_service(db, broadcasts, receipt)
    _, mid = _run_turn(svc)
    done = [d for t, d in broadcasts if t == "thread_turn_done"][-1]
    assert done["egress"] == ""
    assert db.threads.get_message(mid).egress_scope == ""
