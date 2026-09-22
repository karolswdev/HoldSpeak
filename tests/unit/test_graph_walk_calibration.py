"""PHILO-2-01 — the rig calibrates, or no live pass may be run with it.

Brief §7 names six calibration cases. This runs all six through the SAME
execution engine a real case uses, against a local static page, and asserts
the six verdicts. A rig that cannot tell a dead button from a working one
would turn the whole live pass into noise, so this is the rig's own fence.

It also fences the two refusals that keep the owner's machine out of the run:
a HOME under his ~/.local, and an unexplained zero diff passing.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.graph_walk import (
    CALIBRATION_EXPECTED,
    CALIBRATION_SCHEDULER_CASE,
    FORBIDDEN_ROOTS,
    RIG_VERSION,
    VERDICTS,
    Blocked,
    Refused,
    calibrate,
    calibration_table,
    check_predicate,
    guard_home,
    guard_path,
    run_case,
    run_step,
)

REPO = Path(__file__).resolve().parents[2]
SAMPLE_ATLAS = REPO / "tests/fixtures/graph_walk_sample_atlas.json"

pytestmark = pytest.mark.timeout(300, method="thread")


# ── the six calibration cases (brief §7) ───────────────────────────────


@pytest.fixture(scope="module")
def calibration(tmp_path_factory):
    out = tmp_path_factory.mktemp("graph-walk-calibration")
    return calibrate(out), out


def test_rig_is_versioned():
    """One versioned entry point: an observation without a rig version cannot
    be compared against the other brain's."""
    assert RIG_VERSION


def test_six_calibration_cases_get_their_expected_verdicts(calibration):
    records, _ = calibration
    assert len(records) == len(CALIBRATION_EXPECTED), [r["case_id"] for r in records]
    got = {
        r["case_id"]: (r["verdict"], (r.get("terminal_outcome") or {}).get("state"))
        for r in records
    }
    assert got == CALIBRATION_EXPECTED, calibration_table(records)[0]
    assert calibration_table(records)[1] is True


def test_no_calibration_verdict_comes_from_the_presence_of_a_diff(calibration):
    """brief §3 / Astra's finding 1: a diff is evidence, not a criterion.

    The dead button (a) and the working presentation change (d) BOTH move the
    page. They get opposite verdicts, so the diff decided neither.
    """
    records, _ = calibration
    by_id = {r["case_id"]: r for r in records}
    dead = by_id["CAL-a-dead-action"]
    presentation = by_id["CAL-d-presentation-only"]
    assert dead["diff"], "the dead button did move focus; that diff is recorded"
    assert presentation["diff"]
    assert dead["verdict"] == "fail" and presentation["verdict"] == "pass"

    # (b) answered a request and still failed; (e) changed nothing and passed.
    assert by_id["CAL-b-request-without-result"]["verdict"] == "fail"
    assert by_id["CAL-e-idempotent-refresh"]["verdict"] == "pass"
    assert not by_id["CAL-e-idempotent-refresh"]["diff"].get("text")


def test_the_wrong_target_case_records_where_the_result_landed(calibration):
    records, _ = calibration
    wrong = next(r for r in records if r["case_id"] == "CAL-c-wrong-target")
    assert wrong["verdict"] == "fail"
    assert any("WRONG TARGET" in note for note in wrong["notes"]), wrong["notes"]


def test_the_operation_that_never_completes_is_incomplete_not_settled(calibration):
    records, _ = calibration
    never = next(r for r in records if r["case_id"] == "CAL-f-never-completes")
    assert never["verdict"] == "fail"
    assert never["terminal_outcome"]["state"] == "incomplete"
    assert never["terminal_outcome"]["pending_marker_present"] is True
    assert never["terminal_outcome"]["within_bound"] is False


def test_every_observation_carries_provenance_and_before_after(calibration):
    records, out = calibration
    for record in records:
        where = record["case_id"]
        assert record["verdict"] in VERDICTS, where
        assert record["pass"] == "live" and record["brain"] == "muaddib", where
        assert record["complete"] is True, where
        for half in ("before", "after", "initial_feedback"):
            assert record[half] is not None, f"{where}: no {half}"
            assert "url" in record[half], f"{where}: {half} has no url"
        assert record["before"]["at_utc"] < record["after"]["at_utc"], where
        prov = record["provenance"]
        for field in ("revision", "dirty", "frontend_build", "hub", "db_path",
                      "fixture_hashes", "clock", "engine_mode", "rig_version"):
            assert field in prov, f"{where}: provenance has no {field}"
        assert prov["engine_mode"] == "none"
        assert prov["fixture_hashes"], where
        assert prov["clock"]["started_utc"]

        # one run-specific directory per observation, never overwritten
        run_dir = out / record["run_id"]
        assert (run_dir / "observation.json").exists(), where
        assert (run_dir / "before.png").exists() and (run_dir / "after.png").exists()
        on_disk = json.loads((run_dir / "observation.json").read_text())
        assert on_disk["verdict"] == record["verdict"]


def test_run_ids_are_unique_per_case_brain_viewport(calibration):
    records, _ = calibration
    ids = [r["run_id"] for r in records]
    assert len(set(ids)) == len(ids)
    for record in records:
        assert record["case_id"] in record["run_id"]
        assert "muaddib" in record["run_id"] and "1440" in record["run_id"]


# ── the refusals ───────────────────────────────────────────────────────


def test_home_under_the_owners_local_share_is_refused():
    """The one guard that keeps the owner's real database out of every run."""
    for root in FORBIDDEN_ROOTS:
        with pytest.raises(Refused):
            guard_home(root / "share" / "holdspeak")
        with pytest.raises(Refused):
            guard_path(root / "share" / "holdspeak" / "holdspeak.db", "the db")
    assert "/.local" in str(FORBIDDEN_ROOTS[0])


def test_a_temporary_home_is_accepted(tmp_path):
    assert guard_home(tmp_path) == tmp_path.resolve()


# ── the outcome law, at the evaluator ──────────────────────────────────


def test_an_unexplained_zero_diff_is_not_a_pass():
    """brief §3: an unchanged result passes only with a source-backed contract
    AND a proven replay identity."""
    same = {"text": "3 items", "attrs": {}, "replay_identity": None}
    ok, why = check_predicate({"kind": "unchanged"}, same, dict(same))
    assert ok is False and "UNRESOLVED" in why

    ok, _ = check_predicate(
        {"kind": "unchanged", "replay_identity": "#x@data-rev"},
        {**same, "replay_identity": {"spec": "#x@data-rev", "value": "rev-7"}},
        {**same, "replay_identity": {"spec": "#x@data-rev", "value": "rev-7"}},
    )
    assert ok is True

    ok, why = check_predicate(
        {"kind": "unchanged", "replay_identity": "#x@data-rev"},
        {**same, "replay_identity": {"spec": "#x@data-rev", "value": "rev-7"}},
        {**same, "replay_identity": {"spec": "#x@data-rev", "value": "rev-8"}},
    )
    assert ok is False and "replay identity moved" in why


def test_a_window_already_open_before_the_trigger_is_not_the_trigger_opening_it():
    already = {"windows": [{"title": "Rhythm", "visible": True, "rect": {}}]}
    ok, why = check_predicate({"kind": "window_titled", "value": "Rhythm"}, already, already)
    assert ok is False and "ALREADY open" in why


# ── the step kinds that must refuse rather than pretend ────────────────


def test_the_scheduler_wait_adapter_lets_a_timer_edge_produce_the_result(tmp_path):
    """The ONE implemented clock mechanism (W2's `clock.heartbeat_scheduler`).

    Setup arms a stand-in timer — as the real case lowers `sweep_every_minutes`
    to its floor — and then NOTHING is pressed: the scheduler alone must write
    the promised result. No clock is moved, and a substitute button is never
    used in place of the timer.
    """
    records = calibrate(tmp_path, cases=[CALIBRATION_SCHEDULER_CASE])
    record = records[0]
    assert record["verdict"] == "pass", record["notes"]
    assert record["before"]["text"] == "no tick yet"
    assert "tick" in record["after"]["text"]

    trigger = record["trigger"]
    assert trigger["kind"] == "clock"
    assert trigger["adapter"] == "scheduler-wait"
    assert trigger["observe_at_changed"] is True
    assert trigger["polls"] >= 1

    clock = record["provenance"]["clock"]
    assert clock["adapter"] == "scheduler-wait"
    assert clock["clock"] == "cal.stand_in_timer"
    assert clock["machine_clock_moved"] is False
    assert clock["tick_seconds"] == 60
    assert clock["waited_s"] > 0
    assert clock["conductor_ticks_waited"] >= 1
    assert clock["max_wait_s"] <= CALIBRATION_SCHEDULER_CASE["completion_bound_s"]


def test_a_prose_predicate_is_blocked_not_guessed():
    """W2's atlas states its expected results in prose. The rig records the
    whole run and refuses a verdict rather than reading prose."""
    ok, why = check_predicate(
        "a pipeline_event row exists with service 'HeartbeatService'",
        {"text": "a"}, {"text": "b"},
    )
    assert ok is False
    assert "UNDECIDABLE" in why and "structured predicate" in why


def test_protocol_rows_needs_a_NEW_matching_row_not_any_change():
    """The protocol predicate names the row it promises; an unrelated new row
    is not the promised result."""
    predicate = {
        "kind": "protocol_rows", "collection": "projections", "min_new": 1,
        "match": {"subject_ref": "service:HeartbeatService",
                  "attention_state": "resolved", "title__prefix": "SWEEP"},
    }
    sweep = {"subject_ref": "service:HeartbeatService",
             "attention_state": "resolved", "title": "SWEEP 2 ROOMS"}
    other = {"subject_ref": "service:WatchService",
             "attention_state": "resolved", "title": "WATCH"}
    before = {"protocol": {"path": "/api/desk/projections", "status": 200, "rows": []}}
    unrelated = {"protocol": {"path": "/api/desk/projections", "status": 200,
                              "rows": [other]}}
    minted = {"protocol": {"path": "/api/desk/projections", "status": 200,
                           "rows": [other, sweep]}}

    assert check_predicate(predicate, before, unrelated)[0] is False
    assert check_predicate(predicate, before, minted)[0] is True
    # already there before the trigger: nothing NEW was produced
    assert check_predicate(predicate, minted, minted)[0] is False


def test_a_clock_step_blocks_instead_of_claiming_the_state():
    """brief §7: if no mechanism exists within scope, record tooling debt
    rather than claiming the state."""
    with pytest.raises(Blocked) as raised:
        run_step({"kind": "clock", "mechanism": "advance the sweep clock by 15 min"},
                 page=None, hub=None, provenance={"boundary_substitutions": []})
    assert "not implemented" in str(raised.value)
    assert "advance the sweep clock" in str(raised.value)


def test_a_fixture_step_without_a_declared_boundary_blocks():
    """The rig never opens a microphone: with no documented input boundary the
    case is blocked, not walked."""
    provenance = {"fixture_hashes": {}, "boundary_substitutions": []}

    class _NoHub:
        pass

    with pytest.raises(Blocked) as raised:
        run_step({"kind": "fixture", "path": "tests/fixtures/core_path_smoke_16k.wav"},
                 page=None, hub=_NoHub(), provenance=provenance)
    assert "no documented input boundary" in str(raised.value)
    # the fixture is hashed into the provenance before it is refused
    assert provenance["fixture_hashes"]["tests/fixtures/core_path_smoke_16k.wav"]


def test_an_unknown_step_kind_blocks():
    with pytest.raises(Blocked):
        run_step({"kind": "telepathy"}, page=None, hub=None,
                 provenance={"boundary_substitutions": []})


# ── applicability (no hub, no browser) ─────────────────────────────────


def test_a_not_applicable_case_is_recorded_not_skipped(tmp_path):
    record = run_case(
        SAMPLE_ATLAS, "J8-voice-typing-other-app", brain="astra", viewport=1440,
        out=tmp_path, build=False,
    )
    assert record["verdict"] == "not_applicable"
    assert record["complete"] is True
    assert any("UNEXERCISED" in note for note in record["notes"]), record["notes"]
    assert (tmp_path / record["run_id"] / "observation.json").exists()
