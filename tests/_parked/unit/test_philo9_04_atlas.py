"""PHILO-9-04: the atlas cases for the desk debts (docs/internal/philo/graph/atlas-phase9.json).

The cases run through the rig (``scripts/graph_walk.py run``) at 1440 and 393;
their red on main and green on the branch are recorded in the story's evidence.
This file fences the cases' shape: every named case exists at both widths, face
checks read what is readable, and the general atlas fences hold for the file.
The selection contrast and the 12 px floor are not atlas cases (the rig has no
computed-style predicate); the file says so in ``excluded`` and the glass
(tests/e2e/test_philo9_04_desk_debts_glass.py) fences them.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.unit import test_philo_graph_atlas as general

REPO = Path(__file__).resolve().parents[2]
ATLAS9 = REPO / "docs/internal/philo/graph/atlas-phase9.json"

NAMED = {
    "case.p9.list_status.shown",
    "case.p9.list_columns.in_view",
    "case.p9.list_sort.zone_pressed",
    "case.p9.list_row_menu.delete_in_view",
}
FACE_KINDS = {"readable_text", "hit_target", "input_value", "attr_equals"}


@pytest.fixture(scope="module")
def atlas9() -> dict:
    return json.loads(ATLAS9.read_text())


def _cases(atlas: dict) -> dict[str, dict]:
    return {case["id"]: case for case in atlas["cases"]}


def test_every_named_case_is_in_the_atlas(atlas9) -> None:
    assert NAMED <= set(_cases(atlas9)), sorted(NAMED - set(_cases(atlas9)))


def test_every_case_runs_at_both_widths(atlas9) -> None:
    for cid in NAMED:
        assert _cases(atlas9)[cid]["viewports"] == [1440, 393], cid


def test_face_checks_read_what_is_readable(atlas9) -> None:
    for cid in NAMED:
        predicate = _cases(atlas9)[cid]["expected"]["predicate"]
        assert predicate["kind"] in FACE_KINDS, (cid, predicate["kind"])


def test_the_menu_case_asks_44px_at_393_only(atlas9) -> None:
    predicate = _cases(atlas9)["case.p9.list_row_menu.delete_in_view"]["expected"]["predicate"]
    assert predicate["kind"] == "hit_target"
    assert predicate["min_height_by_viewport"] == {"393": 44} and predicate["min_height"] == 28


def test_every_face_case_without_an_op_is_excluded_with_a_reason(atlas9) -> None:
    excluded = " ".join(entry["combination"] for entry in atlas9["excluded"])
    for cid in NAMED:
        assert cid in excluded, cid


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
def test_the_general_fences_hold_for_phase9(fence, atlas9) -> None:
    fence(atlas9)


def test_every_api_setup_step_exists_in_the_generated_openapi(atlas9) -> None:
    openapi = json.loads(general.OPENAPI_PATH.read_text())
    general.test_every_api_setup_step_exists_in_the_generated_openapi(atlas9, openapi)
