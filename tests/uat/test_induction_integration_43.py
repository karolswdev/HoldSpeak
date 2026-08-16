"""Induction recipes that ride the .43 LAN endpoint.

`meeting-just-ended-open-actions` needs real intel to extract an open action;
the mesh lifecycle needs the mesh-node deck (intel-wired). Both self-skip when
`.43` is unreachable — CI has no LAN, so these are honestly `.43`-gated, per
the HANDOVER. Run live with `.43` up to prove real pipeline output.

HS-132-12 split that single gate, because "the LAN answers" turned out not to
be the precondition either test actually needs:

* The meeting recipe needs a `.43` model that really extracts an open action
  from the seeded war-room meeting. A reachable endpoint is not that: the last
  live attempt (2026-08-15, `.43` answering 200) spent 6m21s and ended
  `meeting_with_open_actions: timed out after 180s: meetings present but none
  with >=1 open actions`. It is now an explicit opt-in (`HOLDSPEAK_UAT_LIVE_43`)
  so a full-suite run neither reds nor pays six minutes for a live-model quality
  proof nobody asked for, and `HOLDSPEAK_UAT_LIVE_43=1 uv run pytest
  tests/uat/test_induction_integration_43.py` still runs it against the metal.
* The mesh lifecycle needs a worker that can serve at all. Since HS-131-16 a
  mesh worker authenticates as a paired NODE — `run_mesh_serve_command` exits 1
  before polling when `load_hub_pin()` finds no imported pairing, and the
  shared-owner `HOLDSPEAK_HUB_TOKEN` posture was removed rather than demoted to
  a fallback. The conductor's node harness
  (`uat/conductor/induction/nodes.py`) still spawns `mesh serve --token-env
  HOLDSPEAK_HUB_TOKEN` and never pairs, so the worker dies on start and every
  probe times out at `mesh_node_live` after 40s. That is a stale harness, not
  an absent environment; the gate names it and lifts itself the moment the
  harness learns to pair.
"""

from __future__ import annotations

import os

import httpx
import pytest

from uat.conductor.db import Database
from uat.conductor.induction import nodes as node_harness
from uat.conductor.runs import RunManager

LAN_ENDPOINT = "http://192.168.1.43:8080/v1/models"

#: Opt in to the live-model proofs: they cost minutes and their verdict is the
#: model's, not the code's.
LIVE_43_ENV = "HOLDSPEAK_UAT_LIVE_43"

#: The seam a paired-node harness has to grow: importing the hub's exported
#: pairing into the worker's HOME before `mesh serve` starts.
NODE_PAIRING_SEAM = "pair"


def _lan_up() -> bool:
    try:
        return httpx.get(LAN_ENDPOINT, timeout=5).status_code == 200
    except httpx.HTTPError:
        return False


def _harness_can_pair_a_node() -> bool:
    return hasattr(node_harness.NodeManager, NODE_PAIRING_SEAM) or hasattr(
        node_harness.MeshNode, NODE_PAIRING_SEAM
    )


pytestmark = pytest.mark.skipif(not _lan_up(), reason=".43 LAN endpoint unreachable")

live_43_only = pytest.mark.skipif(
    not os.environ.get(LIVE_43_ENV, "").strip(),
    reason=(
        f"live .43 model proof is opt-in: set {LIVE_43_ENV}=1 (it runs a real "
        "extraction on the LAN model and takes minutes)"
    ),
)

paired_node_only = pytest.mark.skipif(
    not _harness_can_pair_a_node(),
    reason=(
        "the UAT node harness cannot pair a mesh worker: since HS-131-16 "
        "`mesh serve` requires an imported node pairing (hub pin + node token) "
        "and refuses the owner token, but nodes.py still spawns it with "
        "--token-env HOLDSPEAK_HUB_TOKEN and never pairs"
    ),
)


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


@live_43_only
def test_meeting_recipe_yields_a_real_open_action(real_manager):
    run = _boot_or_skip(real_manager, "golden-43")
    result = real_manager.apply_recipe(run.id, "meeting-just-ended-open-actions")
    assert result.probe["ok"], result.probe
    meeting_check = next(
        r for r in result.probe["results"] if r["kind"] == "meeting_with_open_actions"
    )
    assert meeting_check["ok"], meeting_check


@paired_node_only
def test_mesh_node_lifecycle(real_manager):
    run = _boot_or_skip(real_manager, "mesh-node")

    alive = real_manager.apply_recipe(run.id, "mesh-node-alive")
    assert alive.probe["ok"], alive.probe

    died = real_manager.apply_recipe(run.id, "mesh-node-just-died")
    assert died.probe["ok"], died.probe
