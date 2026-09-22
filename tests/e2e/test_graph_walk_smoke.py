"""PHILO-2-01 — the graph rig against the real hub, one case, both viewports.

The calibration fence (`tests/unit/test_graph_walk_calibration.py`) proves the
rig can tell a dead verb from a working one on a static page. This proves the
same engine reaches a real product path: J9 — the owner's sitting defect 1 —
a heartbeat sweep receipt minted through the REAL producer
(`POST /api/settings/heartbeat/run-now` -> `HeartbeatService.run_sweep`,
holdspeak/web/routes/system/settings.py:321), opened from Desk memory, must
open the Rhythm face.

No microphone, no owner data: the hub runs in a fresh mkdtemp HOME and the rig
verifies its resolved database path before it acts.
"""
from __future__ import annotations

import json
import os
import pwd
from pathlib import Path

import pytest

from scripts.graph_walk import VERDICTS, run_case

CASE = "J9-sweep-receipt-open"
REPO = Path(__file__).resolve().parents[2]
ATLAS = REPO / "tests/fixtures/graph_walk_sample_atlas.json"

pytestmark = [pytest.mark.e2e, pytest.mark.timeout(300, method="thread")]


@pytest.mark.parametrize("viewport", [1440, 393])
def test_the_rig_drives_j9_through_the_real_hub(viewport, tmp_path):
    record = run_case(
        ATLAS, CASE, brain="muaddib", viewport=viewport, out=tmp_path,
        engine="none",
    )

    # the verdict comes from the predicate, and the predicate is the promised
    # result: a window titled Rhythm that was NOT open before the trigger.
    assert record["verdict"] == "pass", json.dumps(record["notes"], indent=2)
    assert record["terminal_outcome"]["predicate_satisfied"] is True
    assert record["terminal_outcome"]["within_bound"] is True
    titles_before = [w["title"] for w in record["before"]["windows"]]
    titles_after = [w["title"] for w in record["after"]["windows"]]
    assert "Rhythm" not in titles_before
    assert "Rhythm" in titles_after

    # the trigger was the receipt's own Open, driven at its real entry point
    assert record["trigger"]["adapter"] == "ui-pointer"
    assert record["trigger"]["done"] is True
    producer = [s for s in record["setup"] if s["kind"] == "api"]
    assert producer and producer[0]["path"] == "/api/settings/heartbeat/run-now"
    assert producer[0]["status"] == 200

    _assert_observation_shape(record, viewport, tmp_path)


def _assert_observation_shape(record, viewport, out):
    assert record["verdict"] in VERDICTS
    assert record["case_id"] == CASE
    assert record["pass"] == "live"
    assert record["brain"] == "muaddib"
    assert record["viewport"] == viewport
    assert record["complete"] is True
    assert record["edge_ids"] and record["state_id"]

    for half in ("before", "initial_feedback", "after", "terminal_outcome"):
        assert record[half], f"no {half}"
    assert record["before"]["at_utc"] < record["after"]["at_utc"]
    assert "diff" in record, "the diff is recorded as evidence beside the verdict"

    prov = record["provenance"]
    assert prov["revision"] and len(prov["revision"]) == 40
    assert isinstance(prov["dirty"], bool)
    assert prov["frontend_build"]["built"] is True
    assert prov["frontend_build"]["assets"]
    assert prov["hub"]["pid"] and prov["hub"]["port"] and prov["hub"]["url"]
    assert prov["engine_mode"] == "none"
    assert prov["rig_version"]
    assert prov["clock"]["started_utc"]
    assert prov["atlas"]["sha256"]

    # the database the hub really opened, under the run's own HOME and never
    # under the owner's — the guard that keeps his real desk out of the walk
    db = Path(prov["db_path"]).resolve()
    assert str(db).startswith(str(Path(prov["hub"]["home"]).resolve()))
    real_home = Path(pwd.getpwuid(os.getuid()).pw_dir)
    assert not str(db).startswith(str(real_home / ".local"))

    # what product wiring this hub HAS and LACKS — so no observation is read
    # as if it came from the whole product (Astra's counsel item 8)
    wiring = prov["product_wiring"]
    assert "the database owner lock" in wiring["has"]
    assert "the intelligence queue drainer" in wiring["has"]
    assert any("AudioRecorder" in lack for lack in wiring["lacks"])
    assert any("HotkeyListener" in lack for lack in wiring["lacks"])

    run_dir = out / record["run_id"]
    assert (run_dir / "observation.json").exists()
    assert (run_dir / "before.png").exists()
    assert (run_dir / "after.png").exists()
    on_disk = json.loads((run_dir / "observation.json").read_text())
    assert on_disk["verdict"] == record["verdict"]
    assert on_disk["run_id"] == record["run_id"]
    assert str(viewport) in record["run_id"] and CASE in record["run_id"]
