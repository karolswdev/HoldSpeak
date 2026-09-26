"""PHILO-8-03: the atlas cases for the Floor repairs, and the rig's 1.5.0 steps.

Three kinds of fence:

* the rig's two new predicates (``scripts/graph_walk.py``): ``protocol_reads``
  (the hub's status for each declared read, the FINDING's "HTTP-status
  predicate") and ``all_of`` (a face half and a hub half of one outcome); and
  the right-click on ``click``/``click_role`` (the FINDING's other unchecked
  assumption);
* the Phase 8 atlas file (``docs/internal/philo/graph/atlas-phase8.json``):
  the named cases exist at 1440 and 393, face checks are readable, the delete
  cases read the hub, and the ``.op`` siblings pair the durable outcomes;
* the general atlas fences of ``test_philo_graph_atlas.py`` applied to this
  file (they read ``atlas.json`` by default).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from scripts import graph_walk as gw
from tests.unit import test_philo_graph_atlas as general

REPO = Path(__file__).resolve().parents[2]
ATLAS8 = REPO / "docs/internal/philo/graph/atlas-phase8.json"

#: The face cases this story names (story file "Scope" + the lane's brief).
NAMED_FACE = {
    "case.p8.zone_create.second_unnamed",
    "case.p8.zone_create.second_unnamed_floor",
    "case.p8.zone_rename.list",
    "case.p8.zone_rename.name_taken_list",
    "case.p8.zone_rename.name_taken_floor",
    "case.p8.zone_rename.f2_row",
    "case.p8.chair.no_new_zone",
    "case.p8.list_delete.gone",
    "case.p8.list_delete.undo",
    "case.p8.list_delete.long_list_393",
    "case.p8.delete_twice.both_gone",
    "case.p8.delete_then_leave.gone",
    "case.p8.chair.delete_withheld",
    "case.p8.decision_heads.hidden",
}
NAMED_OP = {
    "case.p8.zone_create.second_unnamed.op",
    "case.p8.zone_rename.list.op",
    "case.p8.zone_rename.name_taken_list.op",
    "case.p8.list_delete.gone.op",
    "case.p8.delete_twice.both_gone.op",
}
#: Face predicate kinds that read what the owner sees without text
#: containment: readable text, a control's own geometry, a field's value, an
#: attribute. Protocol kinds read the hub. ``text_absent`` is allowed only as
#: a part beside a readable one (an absence has no readable form).
FACE_KINDS = {"readable_text", "hit_target", "input_value", "attr_equals"}


# ─────────────────────────── protocol_reads ──────────────────────────────

def _reads(*statuses: int, payload: Any = None) -> dict[str, Any]:
    return {"api_reads": [{"method": "GET", "path": f"/api/decisions/d{i}", "status": s,
                           "payload": payload} for i, s in enumerate(statuses)]}


def test_protocol_reads_passes_on_every_declared_status() -> None:
    ok, why = gw.check_predicate({"kind": "protocol_reads", "expect": [{"status": 404}, {"status": 404}]},
                                 {}, _reads(404, 404))
    assert ok, why


def test_protocol_reads_fails_when_one_object_is_still_on_the_hub() -> None:
    ok, why = gw.check_predicate({"kind": "protocol_reads", "expect": [{"status": 404}, {"status": 404}]},
                                 {}, _reads(404, 200))
    assert not ok and "answered 200, wanted 404" in why


def test_protocol_reads_fails_on_a_read_never_sent() -> None:
    after = {"api_reads": [{"method": "GET", "path": "/api/decisions/{x}", "skipped": "unresolved"}]}
    ok, why = gw.check_predicate({"kind": "protocol_reads", "expect": [{"status": 404}]}, {}, after)
    assert not ok and "not sent" in why


def test_protocol_reads_fails_on_a_missing_read() -> None:
    ok, why = gw.check_predicate({"kind": "protocol_reads", "expect": [{"status": 404}]}, {}, {})
    assert not ok and "0 read(s) observed" in why


def test_protocol_reads_without_expectations_is_blocked() -> None:
    ok, why = gw.check_predicate({"kind": "protocol_reads", "expect": []}, {}, _reads(200))
    assert not ok and why.startswith("BLOCKED")


def test_protocol_reads_row_needs_exactly_one_match() -> None:
    row = {"path": "directories", "match": {"name": "New zone 2"}}
    one = {"directories": [{"name": "New zone"}, {"name": "New zone 2"}]}
    two = {"directories": [{"name": "New zone 2"}, {"name": "New zone 2"}]}
    none = {"directories": [{"name": "New zone"}]}
    pred = {"kind": "protocol_reads", "expect": [{"status": 200, "row": row}]}
    assert gw.check_predicate(pred, {}, _reads(200, payload=one))[0]
    assert not gw.check_predicate(pred, {}, _reads(200, payload=two))[0]
    assert not gw.check_predicate(pred, {}, _reads(200, payload=none))[0]


def test_protocol_reads_is_decidable_headless() -> None:
    ok, _ = gw.check_predicate({"kind": "protocol_reads", "expect": [{"status": 404}]},
                               {}, {"headless": True, **_reads(404)})
    assert ok


# ─────────────────────────────── all_of ──────────────────────────────────

def _readable(text: str) -> dict[str, Any]:
    return {"target_present": True, "visible": True, "text": text,
            "hit_test": {"in_viewport": True, "all_owned": True, "rect": {"w": 10, "h": 10}}}


def test_all_of_needs_every_part() -> None:
    pred = {"kind": "all_of", "predicates": [
        {"kind": "readable_text", "value": "Removal committed"},
        {"kind": "protocol_reads", "expect": [{"status": 404}]}]}
    assert gw.check_predicate(pred, {}, {**_readable("Removal committed"), **_reads(404)})[0]
    ok, why = gw.check_predicate(pred, {}, {**_readable("Removal committed"), **_reads(200)})
    assert not ok and "protocol_reads" in why
    ok, why = gw.check_predicate(pred, {}, {**_readable("Removed A"), **_reads(404)})
    assert not ok and "readable_text" in why


@pytest.mark.parametrize("parts", [
    [],
    [{"kind": "readable_text", "value": "x"}],
    [{"kind": "readable_text", "value": "x"}, {"kind": "all_of", "predicates": []}],
    [{"kind": "readable_text", "value": "x"}, {"kind": "unchanged"}],
    [{"kind": "readable_text", "value": "x"}, "prose"],
])
def test_all_of_refuses_a_shape_it_cannot_decide(parts) -> None:
    ok, why = gw.check_predicate({"kind": "all_of", "predicates": parts}, {}, _readable("x"))
    assert not ok and why.startswith("BLOCKED")


def test_all_of_hands_its_input_value_selector_to_the_snapshot() -> None:
    pred = {"kind": "all_of", "predicates": [
        {"kind": "protocol_status", "status": 201},
        {"kind": "input_value", "selector": "input.desk-zone-rename", "equals": "New zone 2"}]}
    assert gw._value_selector(pred) == "input.desk-zone-rename"
    assert gw._value_selector({"kind": "input_value", "selector": "input.x"}) == "input.x"


# ──────────────────────────── the right-click ────────────────────────────

class _Locator:
    def __init__(self, log: list) -> None:
        self.log = log
        self.first = self

    def click(self, timeout: float, button: str = "left") -> None:
        self.log.append(button)


class _Page:
    viewport_size = {"width": 1440}

    def __init__(self) -> None:
        self.log: list[str] = []

    def locator(self, _selector: str) -> _Locator:
        return _Locator(self.log)

    def get_by_role(self, _role: str, name: str, exact: bool) -> _Locator:
        return _Locator(self.log)


def test_a_right_click_reaches_the_page_as_a_right_click() -> None:
    page = _Page()
    record = gw._ui_step(page, {"kind": "ui", "action": "click_role", "role": "button",
                                "name": "Atlas list delete", "button": "right"})
    assert page.log == ["right"] and record["button"] == "right" and record["done"]
    gw._ui_step(page, {"kind": "ui", "action": "click", "selector": ".desk-x"})
    assert page.log == ["right", "left"]


@pytest.mark.parametrize("step", [
    {"kind": "ui", "action": "click", "selector": ".desk-x", "button": "middle"},
    {"kind": "ui", "action": "press", "key": "Delete", "button": "right"},
])
def test_a_button_the_rig_cannot_press_is_blocked(step) -> None:
    with pytest.raises(gw.Blocked):
        gw._ui_step(_Page(), step)


# ─────────────────────────────── the atlas ───────────────────────────────

@pytest.fixture(scope="module")
def atlas8() -> dict:
    return json.loads(ATLAS8.read_text())


def _cases(atlas: dict) -> dict[str, dict]:
    return {case["id"]: case for case in atlas["cases"]}


def _parts(predicate: dict) -> list[dict]:
    return predicate["predicates"] if predicate.get("kind") == "all_of" else [predicate]


def test_every_named_case_is_in_the_atlas(atlas8) -> None:
    ids = set(_cases(atlas8))
    assert NAMED_FACE | NAMED_OP == ids, sorted(ids ^ (NAMED_FACE | NAMED_OP))


def test_every_face_case_runs_at_both_widths_and_every_op_headless(atlas8) -> None:
    for cid, case in _cases(atlas8).items():
        want = [] if cid in NAMED_OP else [1440, 393]
        assert case["viewports"] == want, cid


def test_every_op_sibling_pairs_a_face_case(atlas8) -> None:
    ids = set(_cases(atlas8))
    for cid in NAMED_OP:
        assert cid.removesuffix(".op") in ids, cid


def test_every_face_case_without_an_op_is_excluded_with_a_reason(atlas8) -> None:
    excluded = " ".join(entry["combination"] for entry in atlas8["excluded"])
    for cid in NAMED_FACE:
        if f"{cid}.op" not in NAMED_OP:
            assert cid in excluded, cid


def test_face_checks_read_what_is_readable_never_text_containment(atlas8) -> None:
    for cid in NAMED_FACE:
        parts = _parts(_cases(atlas8)[cid]["expected"]["predicate"])
        kinds = [part["kind"] for part in parts]
        face = [k for k in kinds if not k.startswith("protocol_")]
        assert "text_contains" not in kinds and "text_equals" not in kinds, cid
        for kind in face:
            assert kind in FACE_KINDS or (kind == "text_absent" and "readable_text" in kinds), (cid, kind)


def test_every_new_predicate_part_is_a_kind_the_rig_implements(atlas8) -> None:
    kinds = general._rig_predicate_kinds()
    for case in atlas8["cases"]:
        for part in _parts(case["expected"]["predicate"]):
            assert part["kind"] in kinds, (case["id"], part["kind"])


def test_every_delete_case_reads_the_hub(atlas8) -> None:
    """A delete is proved on the hub: 404 gone, 200 kept, never by the face alone."""
    for cid in NAMED_FACE:
        if "delete" not in cid:
            continue
        expected = _cases(atlas8)[cid]["expected"]
        reads = [p for p in _parts(expected["predicate"]) if p["kind"] == "protocol_reads"]
        assert reads, cid
        statuses = [e["status"] for e in reads[0]["expect"]]
        assert len(statuses) == len(expected["reads"]), cid
        paths = [r["path"] for r in expected["reads"]]
        assert all(p.startswith("/api/decisions/{") for p in paths), cid


def test_two_deletes_read_both_objects(atlas8) -> None:
    case = _cases(atlas8)["case.p8.delete_twice.both_gone"]
    reads = [p for p in _parts(case["expected"]["predicate"]) if p["kind"] == "protocol_reads"][0]
    assert [e["status"] for e in reads["expect"]] == [404, 404]
    assert {r["path"] for r in case["expected"]["reads"]} == {"/api/decisions/{a_id}", "/api/decisions/{b_id}"}


@pytest.mark.parametrize("cid", ["case.p8.delete_twice.both_gone", "case.p8.delete_then_leave.gone",
                                 "case.p8.list_delete.undo"])
def test_an_in_window_case_is_one_gesture(atlas8, cid) -> None:
    """Under load the rig's before-capture can outlast the 8 s window: main
    PASSED both cases at 1440 (load 20-30) when the second act was the
    trigger, because the timer had committed the first delete before it (and the
    phase build failed the list Undo at 393: the Undo came after the commit).
    The first Delete is the trigger; the rest of the gesture is its `then`,
    and the receipt is read pending right before the second act."""
    trigger = _cases(atlas8)[cid]["trigger"]
    assert trigger.get("key") == "Delete" or trigger.get("name") == "Delete"
    then = trigger["then"]
    assert all(step["kind"] == "ui" for step in then)
    pending = [i for i, step in enumerate(then) if step.get("selector") == ".undo-receipt.is-pending"]
    assert pending and pending[-1] == len(then) - 2, then


@pytest.mark.parametrize("then", [[{"kind": "api", "method": "DELETE", "path": "/x"}], "press Delete", [None]])
def test_then_takes_ui_steps_only(then) -> None:
    with pytest.raises(gw.Blocked):
        gw.trigger_then({"kind": "ui", "action": "press", "key": "Delete", "then": then})
    assert gw.trigger_then({"kind": "ui", "action": "press", "key": "Delete"}) == []


def test_the_list_cases_right_click_the_row(atlas8) -> None:
    for cid in ("case.p8.list_delete.gone", "case.p8.list_delete.undo", "case.p8.list_delete.long_list_393"):
        rights = [s for s in _cases(atlas8)[cid]["setup"] if s.get("button") == "right"]
        assert len(rights) == 1 and rights[0]["action"] == "click_role", cid


def test_optional_steps_never_decide_a_verdict(atlas8) -> None:
    """A step marked optional (so main runs to a verdict) is never the only
    carrier of the outcome: its case's predicate reads the outcome itself."""
    for case in atlas8["cases"]:
        optional = [s for s in general._acts(case) if s.get("optional")
                    and s.get("name") != "Continue later"]
        if optional:
            assert case["expected"]["predicate"]["kind"] == "all_of", case["id"]


# ───────────── the general fences of test_philo_graph_atlas.py ─────────────

GENERAL = [
    general.test_every_case_state_id_resolves,
    general.test_every_case_reference_inside_the_atlas_resolves,
    general.test_every_clock_a_case_uses_is_declared,
    general.test_every_applicable_case_carries_one_trigger,
    general.test_face_cases_carry_both_ruled_viewports,
    general.test_every_applicable_predicate_is_a_kind_the_rig_implements,
    general.test_every_predicate_observes_a_selector_or_a_route,
    general.test_every_case_keeps_its_human_sentence,
    general.test_every_ui_action_is_one_the_rig_implements,
    general.test_no_precondition_check_compares_two_snapshots,
    general.test_every_precondition_check_observes_a_selector_or_a_route,
    general.test_no_check_asserts_the_result_the_trigger_must_produce,
    general.test_no_step_acts_on_a_root_placeholder,
    general.test_navigation_steps_carry_no_selector,
    general.test_every_desk_face_case_crosses_the_gate_first,
    general.test_every_captured_id_names_the_field_it_reads,
]


@pytest.mark.parametrize("fence", GENERAL, ids=lambda f: f.__name__)
def test_the_general_fences_hold_for_phase8(fence, atlas8) -> None:
    fence(atlas8)


def test_every_click_and_fill_names_a_control(atlas8) -> None:
    """The general fence's control tokens, plus the palette's own names:
    `aria-controls` (the shelf and the search field) and an option's `id`
    (the Phase 7 atlas aims at the same controls)."""
    tokens = ("data-testid", "aria-label", "aria-controls", "[id=", "title=", "button",
              "input", "textarea", ".desk-", ".undo-", ".surface-")
    problems = [
        f"{case['id']}: {step['action']} selector {step['selector']!r} names no control"
        for case in atlas8["cases"]
        for step in general._acts(case)
        if step.get("kind") == "ui" and step.get("action") in ("click", "fill")
        and not any(token in step["selector"] for token in tokens)
    ]
    assert not problems, problems


def test_every_api_setup_step_exists_in_the_generated_openapi(atlas8) -> None:
    openapi = json.loads(general.OPENAPI_PATH.read_text())
    general.test_every_api_setup_step_exists_in_the_generated_openapi(atlas8, openapi)
