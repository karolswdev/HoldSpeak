"""Focused PHILO-3-02 checks for the graph walker seams."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


REPO = Path(__file__).resolve().parents[2]
RIG_PATH = REPO / "scripts/graph_walk.py"
SPEC = importlib.util.spec_from_file_location("philo3_summary_rig", RIG_PATH)
assert SPEC and SPEC.loader
rig = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(rig)


class _Hub:
    def __init__(self, answers):
        self.answers = iter(answers)

    def api(self, method, path):
        return next(self.answers)


class _UploadHub:
    def __init__(self, status, payload):
        self.status = status
        self.payload = payload

    def upload(self, method, path, wav, field, form=None):
        return self.status, self.payload


def test_import_completion_rejects_a_successful_but_malformed_payload(monkeypatch):
    monkeypatch.setattr(rig.time, "sleep", lambda _seconds: None)
    clock = iter([0.0, 0.0, 1.0, 1.0])
    monkeypatch.setattr(rig.time, "monotonic", lambda: next(clock))
    hub = _Hub([(200, {"id": "meeting-1", "segments": []})] * 2)
    result = rig.wait_for_fixture_completion(
        hub,
        {
            "method": "GET",
            "path": "/api/meetings/meeting-1",
            "fields": {
                "/transcription_status": "complete",
                "/duration": {"positive": True},
                "/segments": {"min_items": 1},
            },
            "timeout_s": 0.1,
            "poll_s": 0,
        },
        {},
    )
    assert result["matched"] is False
    assert result["payload"]["segments"] == []


def test_import_completion_rejects_successful_nonobject_payloads(monkeypatch):
    """A 2xx list/string is not a completed meeting read."""
    monkeypatch.setattr(rig.time, "sleep", lambda _seconds: None)
    clock = iter([0.0, 0.0, 0.0, 0.0, 1.0, 1.0])
    monkeypatch.setattr(rig.time, "monotonic", lambda: next(clock))
    hub = _Hub([(200, []), (200, "still working"), (200, "still working")])
    result = rig.wait_for_fixture_completion(
        hub,
        {
            "method": "GET",
            "path": "/api/meetings/meeting-1",
            "fields": {"/transcription_status": "complete"},
            "timeout_s": 0.1,
            "poll_s": 0,
        },
        {},
    )
    assert result["matched"] is False
    assert result["payload"] == "still working"


def test_fixture_boundary_enforces_declared_admission_status():
    with pytest.raises(rig.Blocked, match="wanted 202"):
        rig.run_step(
            {
                "kind": "fixture",
                "path": "tests/fixtures/philo3_architect_meeting.wav",
                "route": {"method": "POST", "path": "/api/meetings/import"},
                "expect_status": 202,
            },
            None,
            _UploadHub(201, {"meeting_id": "meeting-1"}),
            {"fixture_hashes": {}},
        )


def test_admission_response_requires_queued_state_and_job_identity():
    predicate = {
        "kind": "protocol_status",
        "method": "POST",
        "path": "/api/meetings/meeting-1/intelligence/run",
        "status": 200,
        "body_contains": '"state": "queued"',
        "body_fields": {"jobId": {"nonempty": True}},
    }
    good = {
        "trigger_response": {
            "method": "POST",
            "path": "/api/meetings/meeting-1/intelligence/run",
            "status": 200,
            "body": {"jobId": "job-1", "state": "queued"},
        }
    }
    ok, _reading = rig.check_predicate(predicate, {}, good)
    assert ok
    stale = {
        "trigger_response": {
            "method": "POST",
            "path": "/api/meetings/meeting-1/intelligence/run",
            "status": 200,
            "body": {"jobId": "job-old", "state": "claimed"},
        }
    }
    ok, _reading = rig.check_predicate(predicate, {}, stale)
    assert not ok
    missing_identity = {
        "trigger_response": {
            **good["trigger_response"],
            "body": {"state": "queued"},
        }
    }
    ok, _reading = rig.check_predicate(predicate, {}, missing_identity)
    assert not ok


def test_hit_target_requires_all_interior_points_and_phone_sized_control():
    before = {}
    after = {
        "target_present": True,
        "visible": True,
        "hit_test": {
            "viewport": {"width": 393, "height": 852},
            "rect": {"x": 20, "y": 40, "w": 120, "h": 44},
            "in_viewport": True,
            "all_owned": True,
            "samples": [{"owned": True}] * 9,
        },
    }
    ok, reading = rig.check_predicate(
        {"kind": "hit_target", "min_width": 44, "min_height": 44},
        before,
        after,
    )
    assert ok, reading


def test_hit_target_rejects_occlusion_short_control_and_out_of_viewport():
    base = {
        "target_present": True,
        "visible": True,
        "hit_test": {
            "viewport": {"width": 393, "height": 852},
            "rect": {"x": 20, "y": 40, "w": 120, "h": 44},
            "in_viewport": True,
            "all_owned": True,
            "samples": [{"owned": True}] * 9,
        },
    }
    for mutate in (
        lambda value: value["hit_test"].update(all_owned=False),
        lambda value: value["hit_test"]["rect"].update(h=43),
        lambda value: value["hit_test"].update(in_viewport=False),
    ):
        candidate = {
            "target_present": base["target_present"],
            "visible": base["visible"],
            "hit_test": {
                "viewport": dict(base["hit_test"]["viewport"]),
                "rect": dict(base["hit_test"]["rect"]),
                "in_viewport": base["hit_test"]["in_viewport"],
                "all_owned": base["hit_test"]["all_owned"],
                "samples": list(base["hit_test"]["samples"]),
            },
        }
        mutate(candidate)
        ok, _reading = rig.check_predicate(
            {"kind": "hit_target", "min_width": 44, "min_height": 44},
            {},
            candidate,
        )
        assert not ok


def test_phone_target_requires_44_pixels_without_changing_desktop_size():
    predicate = {"kind": "hit_target", "min_height": 24,
                 "min_height_by_viewport": {"393": 44}}
    observation = {
        "target_present": True, "visible": True,
        "hit_test": {"in_viewport": True, "all_owned": True,
                     "viewport": {"width": 393}, "rect": {"w": 97, "h": 24}},
    }
    assert not rig.check_predicate(predicate, {}, observation)[0]
    observation["hit_test"]["rect"]["h"] = 44
    assert rig.check_predicate(predicate, {}, observation)[0]
    observation["hit_test"]["viewport"]["width"] = 1440
    observation["hit_test"]["rect"]["h"] = 24
    assert rig.check_predicate(predicate, {}, observation)[0]


def test_scheduler_wait_keeps_a_producer_state_already_reached_in_setup(monkeypatch):
    clock = {"now": 0.0}
    monkeypatch.setattr(rig.time, "monotonic", lambda: clock["now"])
    monkeypatch.setattr(rig.time, "sleep", lambda seconds: clock.update(now=clock["now"] + seconds))
    monkeypatch.setattr(rig, "snapshot", lambda *_args: {
        "protocol": {"payload": {"jobs": [{"status": "claimed"}]},
                     "payload_sha256": "claimed-state"},
    })
    result = rig.scheduler_wait(
        {"adapter": "scheduler-wait", "poll_s": 0.1, "max_wait_s": 0.2},
        {"completion_bound_s": 0.2, "expected": {
            "observe_at": "protocol: GET /api/intel/jobs",
            "predicate": {"kind": "protocol_field", "path": "/jobs/0/status",
                          "value": "claimed"},
        }}, None, _Hub([]), {"clock": {}},
    )
    assert result["polls"] == 0
    assert result["state_satisfied_at_entry"] is True


def test_restart_predicate_requires_summary_receipt_and_identity():
    after = {
        "protocol": {"payload": {"intel": {"summary": "kept"}}},
        "restart": {
            "summary_retained": True,
            "receipt_retained": True,
            "meeting_identity_retained": True,
        },
    }
    ok, reading = rig.check_predicate(
        {
            "kind": "protocol_field",
            "path": "/intel/summary",
            "value": "kept",
            "nonempty": True,
            "restart_required": True,
        },
        {},
        after,
    )
    assert ok, reading


def test_restart_predicate_rejects_each_missing_retention_flag_and_changed_summary():
    predicate = {
        "kind": "protocol_field",
        "path": "/intel/summary",
        "value": "kept",
        "nonempty": True,
        "restart_required": True,
    }
    for missing in ("summary_retained", "receipt_retained", "meeting_identity_retained"):
        restart = {
            "summary_retained": True,
            "receipt_retained": True,
            "meeting_identity_retained": True,
        }
        restart[missing] = False
        ok, _reading = rig.check_predicate(
            predicate,
            {},
            {"protocol": {"payload": {"intel": {"summary": "kept"}}},
             "restart": restart},
        )
        assert not ok

    ok, _reading = rig.check_predicate(
        predicate,
        {},
        {
            "protocol": {"payload": {"intel": {"summary": "changed"}}},
            "restart": {
                "summary_retained": True,
                "receipt_retained": True,
                "meeting_identity_retained": True,
            },
        },
    )
    assert not ok


def test_engine_replay_is_declared_only_by_the_failure_boundary():
    case = {
        "setup": [
            {
                "kind": "boundary",
                "substitute": "engine_reply",
                "reply": "tests/fixtures/philo3_summary_failure_reply.json",
            }
        ],
        "trigger": {"kind": "ui", "action": "click", "selector": "#run"},
    }
    assert rig.case_engine_replay(case) == "tests/fixtures/philo3_summary_failure_reply.json"


def test_optional_framing_keeps_raw_verdict_independent_and_names_scroll_failure(tmp_path):
    class Page:
        def locator(self, selector):
            raise RuntimeError('target disappeared after the raw observation')
    case = {'expected': {'frame_selector': '[data-testid=meeting-summary-text]'}}
    result = rig.capture_framed_view(Page(), case, None, tmp_path)
    assert result['done'] is False
    assert result['selector'] == '[data-testid=meeting-summary-text]'
    assert 'target disappeared' in result['error']
    assert not (tmp_path / 'framed.png').exists()
    assert rig.capture_framed_view(Page(), {'expected': {}}, None, tmp_path) is None
