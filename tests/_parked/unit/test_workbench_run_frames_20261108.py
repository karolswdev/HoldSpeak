"""HS-132-03 — a workbench run is audible.

WorkbenchWindow has subscribed to five ``workbench.*`` frames since
HS-116-07 and no code path ever sent one: the conductor's ``_emit`` was
wired to the hub's broadcast and never called. These tests drive the real
runner through the real kernel and read the frames off the wire.
"""

from __future__ import annotations

import asyncio

import pytest

from holdspeak import workbench_conductor
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.workbench_runner import WorkbenchRunner

from .test_workbench_runner_migration import _setup_runner

OWNER = Principal(PrincipalKind.OWNER, "workbench-owner")


@pytest.fixture
def wire(monkeypatch):
    """Capture everything the conductor puts on the hub's broadcast."""
    frames: list[tuple[str, dict]] = []
    workbench_conductor.set_broadcast(lambda kind, data: frames.append((kind, data)))
    yield frames
    workbench_conductor.set_broadcast(None)


def _run(db, broker, workbench_id: str, *, memory_enabled: bool = False):
    return asyncio.run(
        WorkbenchRunner(db, broker).run(
            OWNER, workbench_id, memory_enabled=memory_enabled
        )
    )


def _kinds(frames: list[tuple[str, dict]]) -> list[str]:
    return [kind for kind, _ in frames if kind.startswith("workbench.")]


def test_a_two_item_run_narrates_every_transition(tmp_path, monkeypatch, wire):
    db, broker, workbench, items, _ = _setup_runner(tmp_path, monkeypatch, item_count=2)
    result = _run(db, broker, workbench.id)

    assert _kinds(wire) == [
        "workbench.run_start",
        "workbench.item_claimed",
        "workbench.item_done",
        "workbench.item_claimed",
        "workbench.item_done",
        "workbench.run_complete",
    ]
    payloads = {kind: data for kind, data in wire}
    assert payloads["workbench.run_start"]["workbench_id"] == workbench.id
    assert payloads["workbench.run_start"]["item_count"] == 2
    assert payloads["workbench.run_start"]["run_id"] == result["run_id"]

    claims = [d for k, d in wire if k == "workbench.item_claimed"]
    assert [(c["index"], c["total"]) for c in claims] == [(1, 2), (2, 2)]
    assert {c["item_id"] for c in claims} == {item.id for item in items}
    assert all(c["run_id"] == result["run_id"] for c in claims)

    done = payloads["workbench.run_complete"]
    assert done["disposition"] == "succeeded"
    assert (done["attempted"], done["completed"], done["failed"]) == (2, 2, 0)
    assert done["pending_count"] == 0


def test_an_empty_run_still_opens_and_closes(tmp_path, monkeypatch, wire):
    db, broker, workbench, items, _ = _setup_runner(tmp_path, monkeypatch, item_count=1)
    _run(db, broker, workbench.id)  # drains the one pending item
    wire.clear()

    _run(db, broker, workbench.id)  # nothing left to claim
    assert _kinds(wire) == ["workbench.run_start", "workbench.run_complete"]
    payloads = {kind: data for kind, data in wire}
    assert payloads["workbench.run_start"]["item_count"] == 0
    assert payloads["workbench.run_complete"]["disposition"] == "succeeded"


def test_every_frame_names_the_workbench_it_is_about(tmp_path, monkeypatch, wire):
    """A window decides a frame is its own by workbench_id — it is never absent."""
    db, broker, workbench, _, _ = _setup_runner(tmp_path, monkeypatch, item_count=1)
    _run(db, broker, workbench.id)
    workbench_frames = [(k, d) for k, d in wire if k.startswith("workbench.")]
    assert workbench_frames
    for kind, data in workbench_frames:
        assert data["workbench_id"] == workbench.id, kind
        assert data["run_id"], kind
        assert data["at"], kind


def test_a_deaf_hub_never_fails_a_run(tmp_path, monkeypatch):
    """The desk hearing the run is a courtesy; the run is the obligation."""
    def explode(kind: str, data: dict) -> None:
        raise RuntimeError("no listeners")

    workbench_conductor.set_broadcast(explode)
    try:
        db, broker, workbench, _, _ = _setup_runner(tmp_path, monkeypatch, item_count=1)
        result = _run(db, broker, workbench.id)
        assert result["receipt_id"]
    finally:
        workbench_conductor.set_broadcast(None)


def test_no_frames_without_a_wired_hub(tmp_path, monkeypatch):
    """A hub that never called set_broadcast is silent, not broken."""
    workbench_conductor.set_broadcast(None)
    db, broker, workbench, _, _ = _setup_runner(tmp_path, monkeypatch, item_count=1)
    assert _run(db, broker, workbench.id)["receipt_id"]
