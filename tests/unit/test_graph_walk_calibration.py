"""PHILO-2-01 — the rig calibrates, or no live pass may be run with it.

Brief §7 names six calibration cases. This runs all six through the SAME
execution engine a real case uses, against a local static page, and asserts
the six verdicts. A rig that cannot tell a dead button from a working one
would turn the whole live pass into noise, so this is the rig's own fence.

It also fences the two refusals that keep the owner's machine out of the run:
a HOME under his ~/.local, and an unexplained zero diff passing.
"""
from __future__ import annotations

import hashlib
import inspect
import json
from pathlib import Path

import pytest

from scripts.graph_walk import (
    CALIBRATION_EXPECTED,
    CALIBRATION_NEGATIVE_CASES,
    CALIBRATION_NEGATIVE_EXPECTED,
    CALIBRATION_PREDICATE_CASES,
    CALIBRATION_SCHEDULER_CASE,
    FORBIDDEN_ROOTS,
    RIG_VERSION,
    STEP_KINDS,
    UI_ACTIONS,
    VERDICTS,
    Blocked,
    Refused,
    _ReplayIntel,
    _read_identity,
    arm_replay_identity,
    calibrate,
    calibration_table,
    case_applicable,
    case_predicate,
    check_predicate,
    guard_home,
    guard_path,
    identity_spec,
    run_case,
    run_step,
    substitute,
    unresolved,
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


# ── the negative controls (Astra's counsel on built) ───────────────────
#
# Each case below PASSED before the fix it names. A `pass` here is a false
# pass, which is worse than no rig at all.


@pytest.fixture(scope="module")
def negatives(tmp_path_factory):
    out = tmp_path_factory.mktemp("graph-walk-negatives")
    records = calibrate(out, cases=CALIBRATION_NEGATIVE_CASES)
    return {r["case_id"]: r for r in records}


def test_every_negative_control_comes_out_as_stated(negatives):
    got = {case_id: record["verdict"] for case_id, record in negatives.items()}
    assert got == CALIBRATION_NEGATIVE_EXPECTED, {
        k: negatives[k]["notes"] for k in got
        if got[k] != CALIBRATION_NEGATIVE_EXPECTED[k]}


def test_a_refresh_with_its_handler_removed_fails(negatives):
    """(1) The replay identity must be produced by THIS operation."""
    record = negatives["NEG-1-refresh-without-handler"]
    assert record["verdict"] == "fail"
    probe = record["replay_identity_probe"]
    assert probe["value_before"] == "rev-7" and probe["cleared"] is True
    # the identity was on the page before, and the dead button never wrote it back
    assert (record["after"].get("replay_identity") or {}).get("value") is None
    # while the WORKING refresh, with the same probe, still passes
    assert CALIBRATION_EXPECTED["CAL-e-idempotent-refresh"][0] == "pass"


def test_a_replay_identity_must_name_an_attribute_or_the_response():
    """Page text cannot prove which operation wrote it."""
    with pytest.raises(Blocked) as raised:
        arm_replay_identity(None, {"kind": "unchanged", "replay_identity": "#e-out"}, {})
    assert "names no attribute" in str(raised.value)
    # a trigger-sourced identity needs no probe
    assert arm_replay_identity(
        None, {"kind": "unchanged", "replay_identity": "trigger:revision"}, {}) is None


def test_a_result_after_the_bound_is_never_a_pass(negatives):
    """(2) `within_bound: false` must make the verdict fail."""
    record = negatives["NEG-2-result-after-the-bound"]
    terminal = record["terminal_outcome"]
    assert record["verdict"] == "fail"
    assert terminal["within_bound"] is False
    assert terminal["state"] == "incomplete"
    assert terminal["late_result_s"] > terminal["completion_bound_s"]
    assert any("AFTER the bound" in note for note in record["notes"])


def test_an_absence_needs_a_scope_that_exists(negatives):
    """(3) A missing observe_at is blocked, never an absence."""
    for case_id in ("NEG-3a-absent-without-a-scope", "NEG-3b-attr-without-a-scope"):
        record = negatives[case_id]
        assert record["verdict"] == "blocked", case_id
        assert record["after"]["target_present"] is False, case_id
        assert any("observe_at not present" in note for note in record["notes"]), case_id
    # and the same predicates still decide inside a scope that DOES exist
    present = {"target_present": True, "text": "all clear", "attrs": {"aria-busy": "false"}}
    assert check_predicate({"kind": "text_absent", "value": "error"}, {}, present)[0] is True
    assert check_predicate({"kind": "text_absent", "value": "clear"}, {}, present)[0] is False
    assert check_predicate({"kind": "attr_equals", "attr": "aria-busy",
                            "value": "false"}, {}, present)[0] is True


def test_the_ui_vocabulary_is_closed_and_blocks_before_anything_fires():
    """(4) A typo must not become a silent no-op that 'passed'."""
    assert UI_ACTIONS == {"goto", "reload", "click", "click_role", "fill",
                          "press", "wait_for"}
    for action in ("tap", "doubleclick", None):
        with pytest.raises(Blocked) as raised:
            # page=None: reaching the page at all would raise AttributeError,
            # so a clean Blocked proves nothing was fired.
            run_step({"kind": "ui", "action": action, "selector": "#a"},
                     page=None, hub=None, provenance={})
        assert repr(action) in str(raised.value)
        assert "not in the rig's vocabulary" in str(raised.value)


def test_a_precondition_that_does_not_hold_blocks_the_case(negatives):
    """(5) A starting state never reached is blocked, not failed."""
    record = negatives["NEG-5-precondition-not-met"]
    assert record["verdict"] == "blocked"
    assert any("precondition not met" in note for note in record["notes"])
    # the prose precondition is recorded and says it was not checked
    prose = [c for c in record["preconditions"] if c["kind"] == "prose"]
    assert prose and prose[0]["checked"] is False
    assert "not checked" in prose[0]["note"]
    # the executable one is recorded with its reading
    checks = [c for c in record["preconditions"] if c["kind"] == "check"]
    assert checks and checks[0]["holds"] is False and checks[0]["reading"]
    # the trigger never fired
    assert record["trigger"] is None


def test_a_precondition_that_holds_lets_the_case_run(tmp_path):
    case = dict(CALIBRATION_NEGATIVE_CASES[4])
    case["id"] = "NEG-5-precondition-met"
    case["preconditions"] = [
        {"kind": "check", "observe_at": "#q-out",
         "predicate": {"kind": "text_contains", "value": "not ready"}},
    ]
    record = calibrate(tmp_path, cases=[case])[0]
    assert record["verdict"] == "pass", record["notes"]
    assert record["preconditions"][0]["holds"] is True


def test_a_words_only_case_is_blocked_and_never_a_keyerror(negatives):
    """(7) An atlas case that states only `words` earns no verdict."""
    record = negatives["NEG-7-words-only"]
    assert record["verdict"] == "blocked"
    assert any("no structured predicate" in note for note in record["notes"])
    assert case_predicate({"expected": {"words": "…"}}) is None
    assert case_predicate({}) is None
    ok, why = check_predicate(None, {}, {})
    assert ok is False and why.startswith("BLOCKED:")


def test_an_unreachable_case_keeps_its_reason_verbatim(tmp_path):
    """(7) The atlas's word plus its sibling `reason`, unaltered."""
    reason = ("UNEXERCISED by the rig: the trigger is a native global hotkey "
              "and the result is delivery into another application.")
    case = {"id": "unreachable-one", "applicability": "unreachable",
            "reason": reason, "expected": {"words": "…"}, "setup": [],
            "viewports": [], "completion_bound_s": 5}
    ok, why = case_applicable(case)
    assert ok is False
    assert why == reason

    atlas = tmp_path / "atlas.json"
    atlas.write_text(json.dumps({"cases": [case]}))
    record = run_case(atlas, "unreachable-one", brain="muaddib", viewport=1440,
                      out=tmp_path, build=False)
    assert record["verdict"] == "not_applicable"
    assert reason in record["notes"][0]


# ── variables and the `check` step kind ────────────────────────────────


def test_a_captured_value_drives_a_later_step_and_the_predicate(predicate_calibration):
    """`capture_as` → `{name}` in a later path AND in the predicate's match."""
    by_id, _ = predicate_calibration
    record = by_id["CAL-r-captured-variable"]
    assert record["verdict"] == "pass", record["notes"]
    captured = record["setup"][0]["captured"]
    assert captured["name"] == "row_id" and captured["path"] == "projections.0.id"
    row_id = captured["value"]
    assert record["variables"]["row_id"] == row_id
    # the placeholder really was filled, in the path AND in the predicate
    assert record["trigger"]["path"] == f"/state/rows/{row_id}"
    assert "{" not in record["trigger"]["path"]
    assert any(row_id in note for note in record["notes"])


def test_an_unresolved_placeholder_is_blocked_and_never_sent(negatives):
    record = negatives["NEG-9-unresolved-placeholder"]
    assert record["verdict"] == "blocked"
    assert any("never_captured" in note for note in record["notes"])
    assert any("never sent literally" in note for note in record["notes"])

    with pytest.raises(Blocked) as raised:
        run_step({"kind": "api", "method": "GET", "path": "/x/{missing}"},
                 page=None, hub=None, provenance={}, variables={"other": "1"})
    assert "'missing'" in str(raised.value)


def test_substitution_fills_only_identifiers():
    variables = {"meeting_id": "m-1", "item_id": "i-2"}
    assert substitute("/api/meetings/{meeting_id}", variables) == "/api/meetings/m-1"
    assert substitute({"path": "{item_id}"}, variables) == {"path": "i-2"}
    assert substitute(["{meeting_id}", 3, None], variables) == ["m-1", 3, None]
    # a brace that is not an identifier is left alone, and reported unfilled
    assert substitute('{"note": 1}', variables) == '{"note": 1}'
    assert unresolved("/x/{nope}") == ["nope"]
    assert unresolved({"a": ["{one}", "{two}"]}) == ["one", "two"]
    assert unresolved("/x/m-1") == []


def test_a_capture_without_a_value_blocks():
    class _Hub:
        def api(self, *_args, **_kwargs):
            return 200, {"other": "x"}

    with pytest.raises(Blocked) as raised:
        run_step({"kind": "api", "method": "GET", "path": "/x",
                  "capture_as": "row_id"},
                 page=None, hub=_Hub(), provenance={}, variables={})
    assert "no value at 'id'" in str(raised.value)


def test_a_check_step_in_setup_blocks_where_it_stands(negatives):
    record = negatives["NEG-8-check-in-setup-fails"]
    assert record["verdict"] == "blocked"
    # the step BEFORE the check ran; the trigger never did
    assert record["setup"][0]["action"] == "click"
    assert record["trigger"] is None
    assert any("precondition not met" in note for note in record["notes"])
    assert any("never written" in note for note in record["notes"])


def test_a_check_step_that_holds_lets_the_case_run(tmp_path):
    case = dict(CALIBRATION_NEGATIVE_CASES[6])
    case["id"] = "NEG-8-check-in-setup-holds"
    case["setup"] = [
        {"kind": "ui", "action": "click", "selector": "#q-btn", "adapter": "ui-pointer"},
        {"kind": "check", "observe_at": "#q-out",
         "predicate": {"kind": "text_contains", "value": "went"}},
    ]
    record = calibrate(tmp_path, cases=[case])[0]
    assert record["verdict"] == "pass", record["notes"]
    assert record["setup"][1]["holds"] is True
    assert record["setup"][1]["kind"] == "check"


def test_the_step_vocabulary_is_closed_and_exported():
    assert STEP_KINDS == {"api", "op", "ui", "fixture", "clock", "boundary", "cli", "check"}
    with pytest.raises(Blocked) as raised:
        run_step({"kind": "telekinesis"}, page=None, hub=None, provenance={})
    assert "'telekinesis'" in str(raised.value)
    assert "not in the rig's vocabulary" in str(raised.value)


# ── atlas-to-rig integration (Astra's round two) ───────────────────────


def test_a_relative_goto_resolves_against_the_hub(tmp_path):
    """An atlas case says `goto "/"`. Without a base url Chromium answers
    "Cannot navigate to invalid URL" and the whole case blocks."""
    case = {
        "id": "CAL-relative-goto", "job": "a case navigates with a bare path",
        "edge_ids": ["cal:goto"], "state_id": "cal:page",
        "applicability": "applicable", "preconditions": "the page is served",
        "setup": [{"kind": "ui", "action": "goto", "url": "/",
                   "adapter": "ui-navigation"}],
        "trigger": {"kind": "ui", "action": "click", "selector": "#c-btn",
                    "adapter": "ui-pointer"},
        "expected": {"observe_at": "#c-wrong",
                     "predicate": {"kind": "text_contains", "value": "saved"}},
        "completion_bound_s": 5, "viewports": [1440],
    }
    record = calibrate(tmp_path, cases=[case])[0]
    assert record["verdict"] == "pass", record["notes"]
    assert record["setup"][0]["done"] is True
    assert record["before"]["url"].startswith("http://127.0.0.1")


def test_a_fixture_step_captures_from_its_own_response():
    """The import route answers 202 {"meeting_id": …}, so an import case
    declares `capture_path: "meeting_id"` — and the default `id` must refuse
    rather than silently leave the placeholder unfilled."""
    class _Hub:
        def upload(self, *_args, **_kwargs):
            return 202, {"meeting_id": "m-9", "status": "importing"}

    variables = {}
    provenance = {"fixture_hashes": {}, "boundary_substitutions": [], "restarts": []}
    step = {"kind": "fixture", "path": "tests/fixtures/core_path_smoke_16k.wav",
            "route": {"method": "POST", "path": "/api/meetings/import"},
            "capture_as": "meeting_id", "capture_path": "meeting_id"}
    record = run_step(step, page=None, hub=_Hub(), provenance=provenance,
                      variables=variables)
    assert variables == {"meeting_id": "m-9"}
    assert record["captured"]["value"] == "m-9"
    assert provenance["fixture_hashes"][step["path"]]

    with pytest.raises(Blocked) as raised:
        run_step({**step, "capture_path": None} | {"capture_path": "id"},
                 page=None, hub=_Hub(), provenance=dict(provenance,
                 fixture_hashes={}), variables={})
    assert "no value at 'id'" in str(raised.value)


def test_a_trigger_identity_is_read_from_the_response_not_the_page():
    """`replay_identity: "trigger:id"` was handed to querySelector as CSS and
    raised a SyntaxError in the snapshot path."""
    spec = identity_spec({"kind": "unchanged", "replay_identity": "trigger:id"})
    assert spec == {"from": "trigger", "path": "id"}
    # nothing on the page is armed or cleared for it
    assert arm_replay_identity(None, {"kind": "unchanged",
                                      "replay_identity": "trigger:id"}, {}) is None
    # and the snapshot never treats it as a selector
    assert _read_identity(None, spec)["value"] is None

    same = {"text": "the brief", "attrs": {}}
    after = {**same, "trigger_response": {"status": 200, "body": {"id": "b-7"}}}
    ok, why = check_predicate({"kind": "unchanged", "replay_identity": "trigger:id"},
                              same, after)
    assert ok is True and "b-7" in why
    # an operation whose response carries no such identity cannot pass
    empty = {**same, "trigger_response": {"status": 200, "body": {"other": 1}}}
    assert check_predicate({"kind": "unchanged", "replay_identity": "trigger:id"},
                           same, empty)[0] is False


def test_identity_display_requires_the_returned_id_to_be_the_displayed_one():
    """J10's contract: the RETURNED brief is the one DISPLAYED — not a stale
    face beside a new receipt."""
    predicate = {"kind": "unchanged", "replay_identity": "trigger:id",
                 "identity_display": "[data-testid=arrival-brief]@data-brief-id"}
    spec = identity_spec(predicate)
    assert spec["from"] == "trigger"
    assert spec["display"] == "[data-testid=arrival-brief]"
    assert spec["display_attr"] == "data-brief-id"

    same = {"text": "the brief", "attrs": {}}
    agreeing = {**same, "trigger_response": {"body": {"id": "b-7"}},
                "identity_display": {"value": "b-7"}}
    stale = {**same, "trigger_response": {"body": {"id": "b-8"}},
             "identity_display": {"value": "b-7"}}
    missing = {**same, "trigger_response": {"body": {"id": "b-8"}},
               "identity_display": {"value": None}}
    assert check_predicate(predicate, same, agreeing)[0] is True
    ok, why = check_predicate(predicate, same, stale)
    assert ok is False and "stale face" in why
    ok, why = check_predicate(predicate, same, missing)
    assert ok is False and why.startswith("BLOCKED:")


def test_a_row_match_reaches_a_nested_field():
    predicate = {"kind": "protocol_rows", "collection": "rows", "min_new": 1,
                 "match": {"effective.status": "ready"}}
    before = {"protocol": {"status": 200, "rows": []}}
    after = {"protocol": {"status": 200,
                          "rows": [{"id": "a", "effective": {"status": "ready"}}]}}
    other = {"protocol": {"status": 200,
                          "rows": [{"id": "a", "effective": {"status": "queued"}}]}}
    assert check_predicate(predicate, before, after)[0] is True
    assert check_predicate(predicate, before, other)[0] is False
    # the prefix suffix still applies to a nested key
    prefixed = {**predicate, "match": {"effective.status__prefix": "rea"}}
    assert check_predicate(prefixed, before, after)[0] is True
    assert check_predicate(prefixed, before, other)[0] is False
    # a missing nested path is not a match
    flat = {"protocol": {"status": 200, "rows": [{"id": "a", "status": "ready"}]}}
    assert check_predicate(predicate, before, flat)[0] is False


def test_prose_in_expected_words_is_not_a_placeholder(tmp_path):
    """An atlas case's `words` says `POST …/{attempt_id}/finish` as English."""
    case = {
        "id": "CAL-prose-braces", "job": "prose braces", "edge_ids": ["cal:w"],
        "state_id": "cal:page", "applicability": "applicable",
        "preconditions": "the page is served", "setup": [],
        "trigger": {"kind": "ui", "action": "click", "selector": "#c-btn",
                    "adapter": "ui-pointer"},
        "expected": {"observe_at": "#c-wrong",
                     "predicate": {"kind": "text_contains", "value": "saved"},
                     "words": "no 4xx on POST /api/setup/first-value/{attempt_id}/finish"},
        "completion_bound_s": 5, "viewports": [1440],
    }
    record = calibrate(tmp_path, cases=[case])[0]
    assert record["verdict"] == "pass", record["notes"]


# ── (6) a boundary must PERFORM its substitution ───────────────────────


class _HubWithoutReplay:
    engine_replay = None


class _HubWithReplay:
    def __init__(self, digest):
        self.engine_replay = digest


def _provenance():
    return {"fixture_hashes": {}, "boundary_substitutions": [], "restarts": [],
            "engine_mode": "none"}


def test_a_label_only_boundary_is_refused():
    with pytest.raises(Blocked) as raised:
        run_step({"kind": "boundary", "label": "the LAN engine"},
                 page=None, hub=_HubWithoutReplay(), provenance=_provenance())
    assert "substitutes nothing" in str(raised.value)


def test_an_engine_reply_boundary_blocks_when_it_was_never_installed():
    with pytest.raises(Blocked) as raised:
        run_step({"kind": "boundary", "label": "the provider",
                  "substitute": "engine_reply"},
                 page=None, hub=_HubWithoutReplay(), provenance=_provenance())
    assert "NOT installed in the hub" in str(raised.value)


def test_an_engine_reply_boundary_records_the_installed_reply(tmp_path):
    reply = tmp_path / "reply.json"
    reply.write_text(json.dumps({"summary": "the recorded reply"}))
    digest = hashlib.sha256(reply.read_bytes()).hexdigest()
    provenance = _provenance()
    record = run_step(
        {"kind": "boundary", "label": "the provider", "substitute": "engine_reply",
         "reply": str(reply)},
        page=None, hub=_HubWithReplay(digest), provenance=provenance)
    assert record["installed_sha256"] == digest
    assert "_configured_engine" in record["seam"]
    assert provenance["engine_mode"] == "replayed"
    assert provenance["fixture_hashes"][str(reply)] == digest
    # a hub carrying a DIFFERENT reply than the case declares is refused
    with pytest.raises(Blocked) as raised:
        run_step({"kind": "boundary", "substitute": "engine_reply",
                  "reply": str(reply)},
                 page=None, hub=_HubWithReplay("0" * 64), provenance=_provenance())
    assert "not the case's" in str(raised.value)


def test_the_replay_engine_answers_the_recorded_reply():
    """The substitution is a recorded reply, not a stub of the pipeline."""
    engine = _ReplayIntel({"summary": "ship on Tuesday", "topics": ["ship"],
                           "action_items": [{"task": "ship", "owner": "karol"}],
                           "title": "Ship Tuesday", "model": "rec-1"})
    result = engine.analyze("a transcript")
    assert result.summary == "ship on Tuesday"
    assert result.topics == ["ship"]
    assert result.action_items[0].task == "ship"
    assert engine.generate_title("a transcript") == "Ship Tuesday"
    assert engine.active_model == "rec-1"
    assert engine.calls == ["analyze", "generate_title"]


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


# ── the four kinds the nine `words`-only atlas cases need ──────────────


@pytest.fixture(scope="module")
def predicate_calibration(tmp_path_factory):
    """All four new kinds, on the calibration page and its protocol surface,
    through the same engine a real case uses."""
    out = tmp_path_factory.mktemp("graph-walk-predicates")
    records = calibrate(out, cases=CALIBRATION_PREDICATE_CASES)
    return {r["case_id"]: r for r in records}, out


def test_every_new_predicate_kind_gets_its_verdict(predicate_calibration):
    by_id, _ = predicate_calibration
    assert set(by_id) == {c["id"] for c in CALIBRATION_PREDICATE_CASES}
    for case_id, record in by_id.items():
        assert record["verdict"] == "pass", (case_id, record["notes"])
        assert record["before"] and record["after"], case_id
        assert record["provenance"]["rig_version"], case_id


def test_a_refusal_status_is_read_from_the_triggers_own_response(predicate_calibration):
    by_id, _ = predicate_calibration
    record = by_id["CAL-h-refusal-status"]
    # the trigger answered 4xx and was NOT treated as a blocked precondition
    assert record["trigger"]["status"] == 422
    answer = record["after"]["trigger_response"]
    assert answer["status"] == 422 and answer["path"] == "/refuse"
    assert len(answer["body_sha256"]) == 64
    assert record["before"].get("trigger_response") is None, (
        "the response cannot exist before the trigger")
    # and the kind refuses a wrong status / a wrong route
    assert check_predicate(
        {"kind": "protocol_status", "status": 200}, {}, record["after"])[0] is False
    assert check_predicate(
        {"kind": "protocol_status", "path": "/other", "status": 422},
        {}, record["after"])[0] is False
    assert check_predicate({"kind": "protocol_status", "status": 422}, {}, {})[0] is False


def test_a_row_gone_is_named_never_merely_fewer(predicate_calibration):
    by_id, _ = predicate_calibration
    record = by_id["CAL-i-row-gone"]
    assert record["trigger"]["status"] == 200
    ids_before = {r["id"] for r in record["before"]["protocol"]["rows"]}
    ids_after = {r["id"] for r in record["after"]["protocol"]["rows"]}
    assert "cal:r2" in ids_before and "cal:r2" not in ids_after

    predicate = {"kind": "protocol_rows_gone", "collection": "projections",
                 "match": {"subject_ref": "profile:cal-p1"}, "min_gone": 1}
    kept = {"protocol": {"rows": [{"id": "a", "subject_ref": "profile:cal-p1"}]}}
    swapped = {"protocol": {"rows": [{"id": "b", "subject_ref": "profile:cal-p1"}]}}
    empty = {"protocol": {"rows": []}}
    # the SAME row still there: nothing disappeared
    assert check_predicate(predicate, kept, kept)[0] is False
    # a different row of the same shape: the named one DID disappear
    assert check_predicate(predicate, kept, swapped)[0] is True
    assert check_predicate(predicate, kept, empty)[0] is True
    # a row count that GREW still names the disappearance honestly
    grew = {"protocol": {"rows": [{"id": "b", "subject_ref": "profile:cal-p1"},
                                  {"id": "c", "subject_ref": "profile:cal-p1"}]}}
    assert check_predicate(predicate, kept, grew)[0] is True


def test_protocol_field_reads_one_named_field(predicate_calibration):
    by_id, _ = predicate_calibration
    record = by_id["CAL-j-protocol-field"]
    payload = record["after"]["protocol"]["payload"]
    assert payload["counts"]["unseen"] == 1

    snap = {"protocol": {"payload": payload}}
    assert check_predicate({"kind": "protocol_field", "path": "counts.unseen",
                            "value": 1}, {}, snap)[0] is True
    assert check_predicate({"kind": "protocol_field", "path": "/counts/unseen",
                            "value": 1}, {}, snap)[0] is True
    assert check_predicate({"kind": "protocol_field", "path": "counts.unseen",
                            "value": 9}, {}, snap)[0] is False
    # a flat object and a string field
    assert check_predicate({"kind": "protocol_field", "path": "person_sections_state",
                            "value": "unavailable"}, {}, snap)[0] is True
    assert check_predicate({"kind": "protocol_field", "path": "counts",
                            "value": payload["counts"]}, {}, snap)[0] is True
    # null is a VALUE, not an absence
    assert check_predicate({"kind": "protocol_field", "path": "nothing_here",
                            "value": None}, {}, snap)[0] is True
    assert check_predicate({"kind": "protocol_field", "path": "nothing_here",
                            "absent": True}, {}, snap)[0] is False
    assert check_predicate({"kind": "protocol_field", "path": "no_such_key",
                            "absent": True}, {}, snap)[0] is True
    assert check_predicate({"kind": "protocol_field", "path": "no_such_key",
                            "value": 1}, {}, snap)[0] is False
    # a list index resolves
    assert check_predicate({"kind": "protocol_field", "path": "projections.0.title",
                            "value": "SWEEP"}, {}, snap)[0] is True


def test_input_value_reads_the_field_not_the_dom_text(predicate_calibration):
    by_id, _ = predicate_calibration
    record = by_id["CAL-k-retained-draft"]
    assert record["trigger"]["action"] == "reload"
    assert record["after"]["field_value"]["value"] == "one sentence"
    # the words are in the VALUE and nowhere in the observed DOM text
    assert "one sentence" not in (record["after"]["text"] or "")
    assert any(entry["value"] == "one sentence" for entry in record["after"]["values"])

    present = {"field_value": {"selector": "#k", "present": True, "value": "one sentence"}}
    assert check_predicate({"kind": "input_value", "selector": "#k",
                            "contains": "one sentence"}, {}, present)[0] is True
    assert check_predicate({"kind": "input_value", "selector": "#k",
                            "equals": "one sentence"}, {}, present)[0] is True
    assert check_predicate({"kind": "input_value", "selector": "#k",
                            "equals": "one"}, {}, present)[0] is False
    missing = {"field_value": {"selector": "#k", "present": False, "value": None}}
    ok, why = check_predicate({"kind": "input_value", "selector": "#k",
                               "contains": "one"}, {}, missing)
    assert ok is False and "no form control" in why


def test_a_restart_is_a_real_restart_and_the_value_survives(predicate_calibration):
    """The `cli` restart adapter (serves case.j7.hub_restart.intel_retained).

    A restart case cannot be claimed: the record names both pids, and the rig
    refuses a 'restart' that kept its pid or changed its database.
    """
    by_id, _ = predicate_calibration
    record = by_id["CAL-l-restart-retained"]
    step = record["trigger"]
    assert step["kind"] == "cli" and step["action"] == "restart_hub"
    assert step["stopped_pid"] and step["started_pid"]
    assert step["stopped_pid"] != step["started_pid"], "nothing was restarted"
    assert step["same_db_path"] is True
    assert step["downtime_s"] >= 0
    # a protocol case is not reloaded; a face case is
    assert "page_reloaded" not in step
    assert record["provenance"]["restarts"] == [step]
    # the value written BEFORE the restart is read back AFTER it
    assert record["before"]["protocol"]["payload"]["note"] == "the summary"
    assert record["after"]["protocol"]["payload"]["note"] == "the summary"
    # and the process that answered really is a different one
    assert (record["before"]["protocol"]["payload"]["served_by_pid"]
            != record["after"]["protocol"]["payload"]["served_by_pid"])


def test_any_other_cli_command_stays_blocked_with_its_name():
    with pytest.raises(Blocked) as raised:
        run_step({"kind": "cli", "command": "holdspeak doctor --fix",
                  "adapter": "process"},
                 page=None, hub=None, provenance={"restarts": []})
    assert "holdspeak doctor --fix" in str(raised.value)
    assert "not implemented" in str(raised.value)


def test_a_refusal_must_name_what_is_missing(predicate_calibration):
    by_id, _ = predicate_calibration
    record = by_id["CAL-m-refusal-names-what-is-missing"]
    assert record["verdict"] == "pass"
    after = record["after"]
    # the right status with the WRONG words is not an intelligible refusal
    ok, why = check_predicate(
        {"kind": "protocol_status", "status": 422,
         "body_contains": "speech.transcribe"}, {}, after)
    assert ok is False and "NOT in the response body" in why
    ok, _ = check_predicate(
        {"kind": "protocol_status", "status": 422,
         "body_contains": "meeting.deferred_analysis"}, {}, after)
    assert ok is True


def test_an_asserted_absence_is_earned_by_the_named_bound(predicate_calibration):
    """`min_new: 0, max_new: 0` — the verdict comes from a named bound on a
    named row shape, never from a zero diff."""
    by_id, _ = predicate_calibration
    assert by_id["CAL-n-no-new-rows"]["verdict"] == "pass"

    base = {"kind": "protocol_rows", "collection": "projections",
            "match": {"subject_ref": "service:HeartbeatService"}}
    empty = {"protocol": {"status": 200, "rows": []}}
    one = {"protocol": {"status": 200,
                        "rows": [{"id": "x", "subject_ref": "service:HeartbeatService"}]}}

    # a bare min_new: 0 asserts nothing and may not pass
    ok, why = check_predicate({**base, "min_new": 0}, empty, empty)
    assert ok is False and "UNRESOLVED" in why
    # the bound makes the absence a claim
    assert check_predicate({**base, "min_new": 0, "max_new": 0}, empty, empty)[0] is True
    assert check_predicate({**base, "min_new": 0, "max_new": 0}, empty, one)[0] is False
    # and it never turns into a ceiling on a case that wanted a row
    assert check_predicate({**base, "min_new": 1, "max_new": 1}, empty, one)[0] is True


def test_the_new_kinds_are_branches_the_atlas_fence_can_read():
    """The atlas fence reads the supported kinds off the evaluator's source."""
    source = inspect.getsource(check_predicate)
    for kind in ("protocol_status", "protocol_rows_gone", "protocol_field",
                 "input_value"):
        assert f'kind == "{kind}"' in source, kind


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
    with pytest.raises(Blocked) as raised:
        run_step({"kind": "telepathy"}, page=None, hub=None,
                 provenance={"boundary_substitutions": []})
    assert "telepathy" in str(raised.value)


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


# ── Astra round three: findings 2 and 3 ────────────────────────────────
#
# Each fence below FAILED against the rig at 8eb866fb (the pre-fix proof is
# in the story evidence): J4 blocked before uploading, and a clicked verb
# never had a response to read its identity from.

REAL_ATLAS = REPO / "docs/internal/philo/graph/atlas.json"
J4_IMPORT = "case.j4.meetings_import.imported"


def _atlas_case(case_id):
    atlas = json.loads(REAL_ATLAS.read_text())
    return next(c for c in atlas["cases"] if c["id"] == case_id)


def test_the_real_j4_import_case_fires_the_upload_and_binds_the_meeting_id(tmp_path):
    """Finding 2: the ACTUAL atlas case, through a synthetic import boundary
    that answers like the real route (202 {"meeting_id", "status"}). Before
    the fix: BLOCKED "unresolved placeholder … meeting_id", zero uploads."""
    case = _atlas_case(J4_IMPORT)
    assert case["trigger"]["capture_as"] == "meeting_id", "the atlas case changed"
    record = calibrate(tmp_path, cases=[case])[0]
    state = json.loads(Path(record["provenance"]["db_path"]).read_text())

    assert state.get("upload_calls") == 1, record["notes"]
    assert record["verdict"] == "pass", record["notes"]
    minted = record["trigger"]["captured"]["value"]
    assert minted == state["meetings"][0]["id"]
    assert record["variables"]["meeting_id"] == minted
    # This is the calibration double's transport answer, not the fixture's
    # JSON body: the upload WAS the trigger and answered 202 before the
    # separate completion read.
    upload = record["trigger"]
    assert upload["kind"] == "fixture" and upload["status"] == 202

    completion = upload["completion_wait"]
    assert completion["matched"] is True
    assert completion["status"] == 200
    completed = completion["payload"]
    assert completed["transcription_status"] == "complete"
    assert completed["duration"] > 0
    assert len(completed["segments"]) >= 1

    # The upload's own answer travels with the after observation.
    answer = record["after"]["trigger_response"]
    assert answer["status"] == 202 and answer["path"] == "/api/meetings/import"
    assert answer["body"]["meeting_id"] == minted
    # before the trigger there was no meeting, and nothing named one
    assert record["before"]["protocol"]["rows"] == []
    assert record["pending_placeholders"] == ["meeting_id"]
    assert record["after"]["protocol"]["rows"][0]["id"] == minted
    assert any("/meetings/0/id" in note for note in record["notes"])


def test_a_placeholder_nothing_binds_blocks_before_the_trigger(negatives):
    """The other half: a name no step and not the trigger captures is refused
    BEFORE the upload — zero calls reach the boundary."""
    record = negatives["NEG-11-unbindable-placeholder-never-fires"]
    assert record["verdict"] == "blocked"
    assert record["trigger"] is None
    assert any("'meeting_id'" in n and "NOT fired" in n for n in record["notes"])
    state = json.loads(Path(record["provenance"]["db_path"]).read_text())
    assert state.get("upload_calls", 0) == 0


def test_a_placeholder_still_unbound_after_the_trigger_blocks_naming_it(tmp_path):
    """A trigger that binds one name does not excuse another."""
    case = dict(_atlas_case(J4_IMPORT))
    case["id"] = "CAL-u-bound-one-not-the-other"
    case["expected"] = {**case["expected"],
                        "observe_at": "protocol: GET /api/meetings",
                        "predicate": {"kind": "protocol_field",
                                      "path": "/meetings/0/id",
                                      "value": "{meeting_id}-{other}"}}
    record = calibrate(tmp_path, cases=[case])[0]
    assert record["verdict"] == "blocked"
    assert any("'other'" in n for n in record["notes"]), record["notes"]
    state = json.loads(Path(record["provenance"]["db_path"]).read_text())
    assert state.get("upload_calls", 0) == 0


def test_a_clicked_verb_reads_its_identity_from_its_own_response(predicate_calibration):
    """Finding 3: before the fix a `ui` trigger never set `trigger_response`
    and this case was BLOCKED "no response was recorded"."""
    by_id, _ = predicate_calibration
    record = by_id["CAL-s-clicked-identity"]
    assert record["verdict"] == "pass", record["notes"]
    answer = record["after"]["trigger_response"]
    assert (answer["method"], answer["path"], answer["status"]) == (
        "POST", "/brief/generate", 200)
    assert answer["body"]["id"] == "brief-7" and len(answer["body_sha256"]) == 64
    capture = record["trigger_response_capture"]
    assert "first same-origin" in capture["rule"] and "non-GET" in capture["rule"]
    # the GET the click fired first was seen and NOT chosen
    assert any(s["method"] == "GET" and s["path"] == "/echo" for s in capture["seen"])
    assert capture["chosen"]["path"] == "/brief/generate"
    assert record["before"].get("trigger_response") is None


def test_a_clicked_verb_status_is_read_by_its_declared_route(predicate_calibration):
    by_id, _ = predicate_calibration
    record = by_id["CAL-t-clicked-status"]
    assert record["verdict"] == "pass", record["notes"]
    assert "trigger_route POST /brief/generate" in record["trigger_response_capture"]["rule"]


def test_a_different_id_beside_unchanged_old_content_fails(negatives):
    """Astra's exact probe: the click minted brief-8; the face still shows
    brief-7 beside the old words. Before the fix it was BLOCKED, never a fail."""
    record = negatives["NEG-10-stale-id-beside-old-content"]
    assert record["verdict"] == "fail", record["notes"]
    assert record["after"]["trigger_response"]["body"]["id"] == "brief-8"
    assert record["after"]["identity_display"]["value"] == "brief-7"
    assert any("stale face" in note for note in record["notes"])


def test_a_longer_id_does_not_display_a_shorter_one():
    """`brief-77` beside unchanged content is a DIFFERENT id, not brief-7."""
    predicate = {"kind": "unchanged", "replay_identity": "trigger:id",
                 "identity_display": "#s-id"}
    same = {"text": "old words", "attrs": {}}
    answer = {"trigger_response": {"body": {"id": "brief-7", "headline": "old words"}}}
    assert check_predicate(predicate, same, {**same, **answer,
                           "identity_display": {"value": "brief-77"}})[0] is False
    assert check_predicate(predicate, same, {**same, **answer,
                           "identity_display": {"value": "Kept brief-7 at 09:00"}})[0] is True
    # the face may show the brief's WORDS: `identity_display_path` names them
    by_words = {**predicate, "identity_display_path": "headline"}
    assert check_predicate(by_words, same, {**same, **answer,
                           "identity_display": {"value": "old words"}})[0] is True
    assert check_predicate(by_words, same, {**same, **answer,
                           "identity_display": {"value": "other words"}})[0] is False
