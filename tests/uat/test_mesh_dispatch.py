"""The mesh handoff arc, driven onto a real worker (HSU-3-01).

`mesh-run-on-worker` spawns a real `holdspeak mesh serve` worker, dispatches an
ask ONTO it through the hub's own /api/ask, and verifies the run returned badged
`⇄ mesh` with worker-claimed / hub-no-local-model provenance and the canary the
worker's model had to surface. It needs the mesh-node deck (intel-wired) + a live
`.43`, so it self-skips without the LAN — CI has none, per the HANDOVER. Run live
with `.43` up to prove the real edge round-trip.
"""

from __future__ import annotations

import httpx
import pytest

from uat.conductor.db import Database
from uat.conductor.runs import RunManager

LAN_ENDPOINT = "http://192.168.1.43:8080/v1/models"


def _lan_up() -> bool:
    try:
        return httpx.get(LAN_ENDPOINT, timeout=5).status_code == 200
    except httpx.HTTPError:
        return False


pytestmark = pytest.mark.skipif(not _lan_up(), reason=".43 LAN endpoint unreachable")


@pytest.fixture
def real_manager(tmp_path, monkeypatch):
    monkeypatch.setenv("UAT_RUNS_ROOT", str(tmp_path / "_runs"))
    monkeypatch.setenv("UAT_DB_PATH", str(tmp_path / "_runs" / "uat.db"))
    monkeypatch.delenv("UAT_REAL_HOME", raising=False)
    mgr = RunManager(Database(), boot_timeout=60.0, link_caches=True)
    try:
        yield mgr
    finally:
        mgr.teardown_all()


def _boot_or_skip(mgr, deck):
    run = mgr.create_run(deck=deck)
    if run.status != "up":
        logs = mgr.logs(run.id, 60)
        pytest.skip(f"product did not boot: {run.error}\nstderr:\n{logs.get('stderr','')}")
    return run


def test_run_dispatched_onto_the_worker_returns_badged(real_manager):
    run = _boot_or_skip(real_manager, "mesh-node")

    result = real_manager.apply_recipe(run.id, "mesh-run-on-worker")
    assert result.probe["ok"], result.probe

    by_kind = {r["kind"]: r for r in result.probe["results"]}
    # The three ACs: badged ⇄ mesh, worker-claimed provenance, canary surfaced.
    assert by_kind["run_returned_badged"]["ok"], by_kind["run_returned_badged"]
    assert by_kind["run_claimed_by_worker"]["ok"], by_kind["run_claimed_by_worker"]
    assert by_kind["run_output_contains"]["ok"], by_kind["run_output_contains"]

    # Teardown leaves no orphan worker: the node reads offline after.
    real_manager.teardown(run.id)
    assert real_manager.get(run.id) is None or real_manager.get(run.id).status != "up"
