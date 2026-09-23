"""PHILO-3-03: the rig's `producer-clock` moves the brief producer's day in its own hub, or blocks."""
from __future__ import annotations

import importlib.util
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location("graph_walk_producer_clock", REPO / "scripts/graph_walk.py")
gw = importlib.util.module_from_spec(_spec)
sys.modules["graph_walk_producer_clock"] = gw
_spec.loader.exec_module(gw)

STEP = {"kind": "clock", "clock": "clock.python_wall", "adapter": "producer-clock",
        "advance_days": 1, "how": "the brief producer's day, one day on"}


class _Hub:
    def __init__(self, home: Path, *, seam: bool = True) -> None:
        self.producer_clock_path = home / "graph-walk-producer-clock.json"
        self.producer_clock = str(self.producer_clock_path) if seam else None


def _provenance() -> dict:
    return gw.base_provenance(engine_mode="none")


def test_the_advance_writes_a_cumulative_offset_the_hub_clock_reads(tmp_path, capsys):
    hub = _Hub(tmp_path)
    prov = _provenance()
    first = gw.run_step(dict(STEP), None, hub, prov)
    second = gw.run_step(dict(STEP), None, hub, prov)
    assert first["advance_days_total"] == 1 and second["advance_days_total"] == 2
    assert json.loads(hub.producer_clock_path.read_text()) == {"advance_days": 2}
    assert prov["clock"]["machine_clock_moved"] is False
    assert prov["clock"]["advance_days"] == 2

    clock = gw._producer_clock(hub.producer_clock_path)
    reading = clock()
    assert reading - datetime.now() > timedelta(days=1, hours=23)
    assert "PRODUCER_CLOCK_READ advance_days=2" in capsys.readouterr().out


def test_no_offset_file_is_the_wall_clock(tmp_path):
    clock = gw._producer_clock(tmp_path / "absent.json")
    assert abs((clock() - datetime.now()).total_seconds()) < 5


def test_a_hub_without_the_seam_blocks(tmp_path):
    with pytest.raises(gw.Blocked, match="not booted with the producer clock seam"):
        gw.run_step(dict(STEP), None, _Hub(tmp_path, seam=False), _provenance())
    with pytest.raises(gw.Blocked, match="not booted"):
        gw.run_step(dict(STEP), None, None, _provenance())


def test_only_the_python_wall_clock_and_whole_days(tmp_path):
    hub = _Hub(tmp_path)
    with pytest.raises(gw.Blocked, match="clock.python_wall only"):
        gw.run_step({**STEP, "clock": "clock.sqlite_now"}, None, hub, _provenance())
    with pytest.raises(gw.Blocked, match="advance_days"):
        gw.run_step({**STEP, "advance_days": 0}, None, hub, _provenance())


def test_a_case_with_the_step_boots_the_hub_with_the_seam():
    case = {"setup": [STEP], "trigger": {"kind": "api"}}
    assert gw.case_needs_producer_clock(case)
    assert not gw.case_needs_producer_clock({"setup": [], "trigger": {"kind": "api"}})


def test_body_excludes_fails_a_body_that_carries_the_old_id():
    predicate = {"kind": "protocol_status", "method": "POST", "path": "/api/brief/generate",
                 "status": 200, "body_contains": "Review decision: X", "body_excludes": "brief-old"}

    def after(body):
        return {"trigger_response": {"method": "POST", "path": "/api/brief/generate",
                                     "status": 200, "body": body, "body_sha256": "0"}}

    ok, why = gw.check_predicate(predicate, {}, after({"id": "brief-new", "t": "Review decision: X"}))
    assert ok, why
    ok, why = gw.check_predicate(predicate, {}, after({"id": "brief-old", "t": "Review decision: X"}))
    assert not ok and "IS in the response body" in why
    ok, why = gw.check_predicate(predicate, {}, after({"id": "brief-new"}))
    assert not ok and "NOT in" in why
