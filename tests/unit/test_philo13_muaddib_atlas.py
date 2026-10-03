"""PHILO-13 faces lane -- the atlas cases of ``atlas-phase13-muaddib.json``.

The faces lane owns its own atlas file (charter, "File ownership"; handoff
H-B0a). This file holds its count and names, and applies the general atlas
fences of ``test_philo_graph_atlas.py`` to it (they read ``atlas.json`` by
default). The shared ``.op`` sibling count (``test_philo_graph_atlas.py:492``)
is Astra's (H-B0b); this lane adds no ``.op`` sibling.

* PHILO-13-05 (A4): ``case.p13.close.intelligence_gone``
* PHILO-13-04 (A3): ``case.p13.record.refused_not_recording``
* PHILO-13-16 (C6): ``case.p13.capture.titled_by_first_words``
* PHILO-13-17 (C7): ``case.p13.phone.switcher_two_taps``,
  ``case.p13.phone.go_desk_menu``
* PHILO-13-15 (C5): ``case.p13.send_to.window_menu_opens_preview``
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from tests.unit import test_philo_graph_atlas as general

REPO = Path(__file__).resolve().parents[2]
ATLAS = REPO / "docs/internal/philo/graph/atlas-phase13-muaddib.json"

#: Every case this lane has added, by story. A new case changes this set in
#: the same commit (one count, one owner).
CASES = {
    "case.p13.close.intelligence_gone",  # PHILO-13-05
    "case.p13.record.refused_not_recording",  # PHILO-13-04
    "case.p13.capture.titled_by_first_words",  # PHILO-13-16
    "case.p13.phone.switcher_two_taps",  # PHILO-13-17
    "case.p13.phone.go_desk_menu",  # PHILO-13-17
    "case.p13.send_to.window_menu_opens_preview",  # PHILO-13-15
}

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
    general.test_every_click_and_fill_names_a_control,
    general.test_every_desk_face_case_crosses_the_gate_first,
    general.test_every_captured_id_names_the_field_it_reads,
    general.test_ids_are_unique,
]


@pytest.fixture(scope="module")
def atlas() -> dict:
    return json.loads(ATLAS.read_text())


@pytest.mark.parametrize("fence", GENERAL, ids=lambda fence: fence.__name__)
def test_the_general_fences_hold_on_this_file(fence, atlas: dict) -> None:
    fence(atlas)


def test_every_api_step_exists_in_the_generated_openapi(atlas: dict) -> None:
    openapi = json.loads(general.OPENAPI_PATH.read_text())
    general.test_every_api_setup_step_exists_in_the_generated_openapi(atlas, openapi)


def test_every_case_is_a_legal_graph_case(atlas: dict) -> None:
    graph_case_schema = json.loads(general.GRAPH_SCHEMA_PATH.read_text())
    general.test_every_case_validates_against_the_graph_case_schema(atlas, graph_case_schema)


def test_the_file_validates_against_the_atlas_schema(atlas: dict) -> None:
    schema = json.loads(general.SCHEMA_PATH.read_text())
    errors = [error.message for error in Draft202012Validator(schema).iter_errors(atlas)]
    assert not errors, errors[:5]


def test_the_lane_case_count_and_names(atlas: dict) -> None:
    ids = {case["id"] for case in atlas["cases"]}
    assert ids == CASES
    assert len(atlas["cases"]) == 6
    # No `.op` sibling here: the shared count at test_philo_graph_atlas.py:492
    # stays Astra's (H-B0b).
    assert not [i for i in ids if i.endswith(".op") or i.endswith(".op.replayed")]


def test_both_cases_are_face_cases_at_both_widths(atlas: dict) -> None:
    for case in atlas["cases"]:
        assert case["applicability"] == "applicable", case["id"]
        assert sorted(case["viewports"]) == [393, 1440], case["id"]
