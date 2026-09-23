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


# ── THE INTEGRATION FENCE ──────────────────────────────────────────────
#
# Five cases from the REAL atlas (docs/internal/philo/graph/atlas.json), one
# hub each, serial, at 1440. A rig that only ever runs its own sample atlas
# proves nothing about the pass it was built for.
#
# At round two, two of the first three were BLOCKED, by the atlas, not the rig.
# Both were confirmed against a live desk (counts queried on a fresh HOME):
#
#   behind the first-value gate   after "Continue later"
#   .chair-first-value        1        0
#   [title='Desk memory']     0        1
#   [data-testid=arrival-headline] 0   1
#   role=button "Continue later"  1    0
#
# So `[title='Desk memory']` is a CORRECT selector that does not exist until
# the gate is crossed, and "Continue later" is gone once it has been pressed.
REAL_ATLAS = REPO / "docs/internal/philo/graph/atlas.json"
ATLAS_FENCE = {
    "case.j9.shade_receipt_open.rhythm_face": (
        "pass", "", "the sweep receipt's own Open reaches the Rhythm face (the "
        "atlas crosses the first-value gate before the bell since round three)",
    ),
    "case.j1.first_words_continue_later.idle": (
        "pass", "", "Continue later is the trigger, pressed by nothing in setup; "
        "the desk (the arrival headline) is the promised result",
    ),
    "case.j10.arrival_generate_brief.generated_empty": (
        "pass", "", "the empty brief says so on the face",
    ),
    # Astra round three, MISSED: the import path and the response-identity
    # path changed in round three and were in no integration case.
    "case.j4.meetings_import.imported": (
        "pass", "", "the fixture WAV through the REAL import route mints a "
        "meeting; the trigger binds {meeting_id} and the row carries it",
    ),
    "case.j10.arrival_generate_again.same_day_idempotent": (
        "pass", "", "the clicked Generate again's OWN response is the identity, "
        "and the face shows what it returned",
    ),
}


@pytest.mark.parametrize("case_id", sorted(ATLAS_FENCE))
def test_the_rig_drives_the_real_atlas(case_id, tmp_path):
    want_verdict, names, why = ATLAS_FENCE[case_id]
    record = run_case(REAL_ATLAS, case_id, brain="muaddib", viewport=1440,
                      out=tmp_path, engine="none")

    assert record["verdict"] == want_verdict, (
        f"{case_id}: {why}\n" + json.dumps(record["notes"], indent=2))
    assert record["complete"] is True
    assert record["provenance"]["revision"]
    assert (tmp_path / record["run_id"] / "observation.json").exists()

    if want_verdict == "blocked":
        # a named block: the record says WHAT could not be reached
        blocked = [n for n in record["notes"] if n.startswith("BLOCKED:")]
        assert blocked, record["notes"]
        assert names in blocked[0], blocked[0]
    else:
        assert record["terminal_outcome"]["within_bound"] is True
        assert record["before"] and record["after"]

    if case_id == "case.j4.meetings_import.imported":
        # the upload FIRED (finding 2) and bound the id its own 202 returned
        answer = record["after"]["trigger_response"]
        assert answer["status"] == 202, answer
        assert answer["path"] == "/api/meetings/import"
        assert record["variables"]["meeting_id"] == answer["body"]["meeting_id"]
    if case_id == "case.j10.arrival_generate_again.same_day_idempotent":
        # the identity came from the click's own POST (finding 3)
        chosen = record["trigger_response_capture"]["chosen"]
        assert chosen and (chosen["method"], chosen["path"]) == (
            "POST", "/api/brief/generate"), record["trigger_response_capture"]


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
