"""PHILO-13 B0: Astra's preparatory atlas contract.

The phase file owns its own case and operation-sibling count.  The shared
atlas contract still reads this file through ``ATLAS_FILES``; the mutant tests
below prove that its semantic guards reject a broken Phase 13 case before the
proper case is restored.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from tests.unit import test_philo_graph_atlas as general


REPO = Path(__file__).resolve().parents[2]
ATLAS = REPO / "docs/internal/philo/graph/atlas-phase13-astra.json"
EXPECTED_CASES = {
    "case.p13.directory.zone_window.op",
}


GENERAL = [
    general.test_every_case_state_id_resolves,
    general.test_every_case_reference_inside_the_atlas_resolves,
    general.test_every_clock_a_case_uses_is_declared,
    general.test_every_applicable_case_carries_one_trigger,
    general.test_face_cases_carry_both_ruled_viewports,
    general.test_every_applicable_predicate_is_a_kind_the_rig_implements,
    general.test_every_predicate_observes_a_selector_or_a_route,
    general.test_every_source_reference_lands_on_its_symbol,
    general.test_every_case_keeps_its_human_sentence,
    general.test_every_ui_action_is_one_the_rig_implements,
    general.test_every_boundary_names_its_substitution,
    general.test_no_precondition_check_compares_two_snapshots,
    general.test_every_precondition_check_observes_a_selector_or_a_route,
    general.test_no_check_asserts_the_result_the_trigger_must_produce,
    general.test_no_step_acts_on_a_root_placeholder,
    general.test_navigation_steps_carry_no_selector,
    general.test_every_desk_face_case_crosses_the_gate_first,
    general.test_every_captured_id_names_the_field_it_reads,
    general.test_ids_are_unique,
]


def _atlas() -> dict:
    return json.loads(ATLAS.read_text())


def _cases() -> dict[str, dict]:
    return {case["id"]: case for case in _atlas()["cases"]}


@pytest.mark.parametrize("fence", GENERAL, ids=lambda fence: fence.__name__)
def test_phase13_atlas_keeps_the_shared_graph_fences(fence) -> None:
    fence(_atlas())


def test_phase13_atlas_validates_against_schema_and_openapi() -> None:
    atlas = _atlas()
    schema = json.loads(general.SCHEMA_PATH.read_text())
    general.test_atlas_validates_against_its_schema(atlas, schema)
    general.test_every_api_setup_step_exists_in_the_generated_openapi(
        atlas, json.loads(general.OPENAPI_PATH.read_text())
    )


def test_phase13_case_and_sibling_manifest_is_local() -> None:
    cases = _cases()
    assert set(cases) == EXPECTED_CASES
    assert cases["case.p13.directory.zone_window.op"]["viewports"] == []
    assert sum(case["id"].endswith(".op") for case in cases.values()) == 1


def test_phase13_shared_semantic_guards_show_red_then_green(tmp_path, monkeypatch) -> None:
    """The shared guards really inspect this file, including its .op sibling."""
    proper = _atlas()
    broken_words = copy.deepcopy(proper)
    broken_words["cases"][0]["expected"]["words"] = ""
    words_path = tmp_path / "atlas-phase13-broken-words.json"
    words_path.write_text(json.dumps(broken_words))

    other_files = [path for path in general.ATLAS_FILES if path.name != ATLAS.name]
    monkeypatch.setattr(general, "ATLAS_FILES", [*other_files, words_path])
    with pytest.raises(AssertionError):
        general.test_every_case_keeps_its_human_sentence(json.loads(words_path.read_text()))

    broken_binding = copy.deepcopy(proper)
    broken_binding["cases"][0]["expected"]["observe_at"]["args"]["directory_id"] = "{missing_zone_id}"
    binding_path = tmp_path / "atlas-phase13-broken-binding.json"
    binding_path.write_text(json.dumps(broken_binding))
    monkeypatch.setattr(general, "ATLAS_FILES", [*other_files, binding_path])
    with pytest.raises(AssertionError, match="missing_zone_id"):
        general.test_named_pair_observations_bind_their_read_arguments()

    broken_semantics = copy.deepcopy(proper)
    broken_semantics["cases"][0]["expected"]["observe_at"]["name"] = "zone.create"
    semantics_path = tmp_path / "atlas-phase13-broken-semantics.json"
    semantics_path.write_text(json.dumps(broken_semantics))
    monkeypatch.setattr(general, "ATLAS_FILES", [*other_files, semantics_path])
    with pytest.raises(AssertionError, match="zone.create"):
        general.test_operation_siblings_use_headless_reads_and_canonical_steps()

    # Restore the proper Phase 13 file in the shared glob and prove both
    # semantic guards pass against it.
    monkeypatch.setattr(general, "ATLAS_FILES", [*other_files, ATLAS])
    general.test_every_case_keeps_its_human_sentence(proper)
    general.test_named_pair_observations_bind_their_read_arguments()
    general.test_operation_siblings_use_headless_reads_and_canonical_steps()


def test_phase13_shared_operation_count_excludes_only_phase13_files() -> None:
    siblings = [
        case
        for path in general.ATLAS_FILES
        if not path.name.startswith("atlas-phase13-")
        for case in json.loads(path.read_text())["cases"]
        if case["id"].endswith(".op") or case["id"].endswith(".op.replayed")
    ]
    assert len(siblings) == 69
