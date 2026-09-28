"""PHILO-9-05: the Phase 9 atlas, assembled (docs/internal/philo/graph/atlas-phase9*.json).

Phase 9's cases live in two files: ``atlas-phase9.json`` (stories 03, 04 and
this story's census gaps) and ``atlas-phase9-steward.json`` (story 02's
operation cases, kept in their own file: their retained observations under
``docs/internal/philo/graph/observations/`` name that path and its sha256, and
the owner's ruling is "never delete, park instead").

The general fences of ``tests/unit/test_philo_graph_atlas.py`` read
``atlas.json`` by default (the Phase 8 law), so this file applies them to BOTH
Phase 9 files itself, and fences what story 05 owns: the named cases, their
widths, the face / operation pairs, the exclusions and the counts. The cases'
verdicts are the rig's (``scripts/graph_walk.py run``), recorded in the
story's evidence.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.unit import test_philo_graph_atlas as general

REPO = Path(__file__).resolve().parents[2]
GRAPH = REPO / "docs/internal/philo/graph"
PHASE9 = ("atlas-phase9.json", "atlas-phase9-steward.json")

# The counts over every atlas file at this story's commit (face cases run at
# 1440 and 393; operation and route cases run once, headless).
COUNTS = {
    "atlas.json": 85,
    "atlas-phase3.json": 36,
    "atlas-phase7.json": 27,
    "atlas-phase8.json": 19,
    "atlas-phase9.json": 13,
    "atlas-phase9-steward.json": 4,
}

# The census's proven gaps, authored here (story 05).
STORY05 = {
    "case.p9.grant.project_allowed",
    "case.p9.grant_route.project_allowed",
    "case.p9.grant.desk_reads_desk",
    "case.p9.connections.never_checked_face",
    "case.p9.update.delivered_row.op",
}

# Each face case with a durable outcome and the non-face case that proves the
# same outcome through the hub (the equivalence pairs).
PAIRS = {
    "case.p9.update.delivered_row": "case.p9.update.delivered_row.op",
    "case.p9.grant.project_allowed": "case.p9.grant_route.project_allowed",
    "case.p9.connections.never_checked_face": "case.p9.connections.never_checked",
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
    general.test_every_desk_face_case_crosses_the_gate_first,
    general.test_every_captured_id_names_the_field_it_reads,
]


def _load(name: str) -> dict:
    return json.loads((GRAPH / name).read_text())


def _all_cases() -> dict[str, dict]:
    return {case["id"]: case for name in PHASE9 for case in _load(name)["cases"]}


@pytest.mark.parametrize("name", PHASE9)
@pytest.mark.parametrize("fence", GENERAL, ids=lambda f: f.__name__)
def test_the_general_fences_hold_for_each_phase9_file(fence, name) -> None:
    fence(_load(name))


@pytest.mark.parametrize("name", PHASE9)
def test_every_api_step_exists_in_the_generated_openapi(name) -> None:
    openapi = json.loads(general.OPENAPI_PATH.read_text())
    general.test_every_api_setup_step_exists_in_the_generated_openapi(_load(name), openapi)


def test_the_counts_over_every_atlas_file() -> None:
    have = {path.name: len(json.loads(path.read_text())["cases"]) for path in general.ATLAS_FILES}
    assert have == COUNTS


def test_every_story05_case_is_in_the_phase_file() -> None:
    ids = {case["id"] for case in _load("atlas-phase9.json")["cases"]}
    assert STORY05 <= ids, sorted(STORY05 - ids)


def test_face_cases_run_at_both_widths_and_the_rest_headless() -> None:
    for cid, case in _all_cases().items():
        face = case["trigger"]["kind"] == "ui"
        assert case["viewports"] == ([1440, 393] if face else []), cid


def test_every_pair_exists_and_proves_the_same_outcome() -> None:
    cases = _all_cases()
    for face, twin in PAIRS.items():
        assert cases[face]["trigger"]["kind"] == "ui", face
        assert cases[twin]["trigger"]["kind"] in ("op", "api"), twin
        assert cases[twin]["viewports"] == [], twin


def test_the_pairs_read_the_same_values() -> None:
    """The face and its twin name the same recipient, grant and state."""
    cases = _all_cases()
    typed = next(s["value"] for s in cases["case.p9.update.delivered_row"]["setup"]
                 if s.get("selector") == "[data-testid=deliver-to]")
    assert cases["case.p9.update.delivered_row"]["expected"]["predicate"]["value"] == typed
    op = cases["case.p9.update.delivered_row.op"]
    assert op["trigger"]["args"]["delivered_to"] == typed
    assert {"source": "observe", "path": "updates.0.deliveries.0.delivered_to", "value": typed} \
        in op["expected"]["predicate"]["facts"]
    grant, route = (json.dumps(cases[c]) for c in ("case.p9.grant.project_allowed",
                                                    "case.p9.grant_route.project_allowed"))
    for text in ('"LIVE"', "/api/settings/remote/delegations/{identity}/projects/{project_id}", '"sweep-runner"'):
        assert text in grant and text in route, text
    connections = json.dumps(cases["case.p9.connections.never_checked_face"])
    assert '"never_checked"' in connections and '"github"' in connections


def test_every_admitted_write_twin_reads_its_receipt_with_its_actor() -> None:
    """The charter: each admitted write's kernel receipt, read with its actor."""
    for twin in ("case.p9.update.delivered_row.op", "case.p9.grant_route.project_allowed"):
        text = json.dumps(_all_cases()[twin]["expected"])
        assert "actor_kind" in text and '"owner"' in text, twin
        assert "kernel.receipt.read" in text or "/api/kernel/read" in text, twin


def test_every_face_case_without_a_twin_is_excluded_with_a_reason() -> None:
    atlas = _load("atlas-phase9.json")
    excluded = " ".join(entry["combination"] for entry in atlas["excluded"])
    twins = {case["id"][:-3] for case in atlas["cases"] if case["id"].endswith(".op")} | set(PAIRS)
    for case in atlas["cases"]:
        if case["trigger"]["kind"] == "ui" and case["id"] not in twins:
            assert case["id"] in excluded, case["id"]


def test_no_trigger_is_optional_and_no_optional_step_is_the_outcome() -> None:
    """Law: an optional step is never the outcome. The only optional step in a
    Phase 9 case is the first-use gate's Continue later."""
    for cid, case in _all_cases().items():
        assert not case["trigger"].get("optional"), cid
        optional = [s for s in general._acts(case) if s.get("optional")]
        assert all(s.get("name") == "Continue later" for s in optional), cid


def test_every_new_face_case_is_new_or_red_on_main_in_its_words() -> None:
    """Each story 05 face case says what main showed: a red, or new (no red claimed)."""
    cases = _all_cases()
    for cid in STORY05:
        if cases[cid]["trigger"]["kind"] != "ui":
            continue
        words = cases[cid]["expected"]["words"]
        assert "Red on main" in words or "New (no red claimed)" in words, cid
