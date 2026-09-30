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
    # PHILO-10-05: the Send's cases (the Phase 9 files unchanged).
    "atlas-phase10.json": 32,  # PHILO-10-07: five Resend face cases
    "atlas-phase11-slack.json": 3,  # PHILO-11-02: real Slack backend outcomes
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
    face_parts = {p["kind"]: p for p in cases["case.p9.update.delivered_row"]["expected"]["predicate"]["predicates"]}
    assert face_parts["readable_text"]["value"] == typed
    assert face_parts["protocol_status"]["body_fields"]["delivery.delivered_to"] == typed
    op = cases["case.p9.update.delivered_row.op"]
    assert op["trigger"]["args"]["delivered_to"] == typed
    assert {"source": "observe", "path": "updates.0.deliveries.0.delivered_to", "value": typed} \
        in op["expected"]["predicate"]["facts"]
    grant, route = (json.dumps(cases[c]) for c in ("case.p9.grant.project_allowed",
                                                    "case.p9.grant_route.project_allowed"))
    for text in ('"LIVE"', "/api/settings/remote/delegations/{identity}/projects/{project_id}", '"sweep-runner"'):
        assert text in grant and text in route, text
    # Codex Astra r1 finding 3: BOTH predicates, face and twin, name the same
    # provider in the same state with no check time.
    face_rows = [part["expect"][0]["row"]["match"]
                 for part in cases["case.p9.connections.never_checked_face"]["expected"]["predicate"]["predicates"]
                 if part["kind"] == "protocol_reads"]
    twin_facts = [fact["contains"] for fact in cases["case.p9.connections.never_checked"]["expected"]["predicate"]["facts"]
                  if isinstance(fact.get("contains"), dict) and fact["contains"].get("provider_id") == "github"]
    assert face_rows == [{"provider_id": "github", "state": "never_checked", "last_checked_at": None}]
    assert twin_facts and all(f["state"] == face_rows[0]["state"] for f in twin_facts), twin_facts
    assert any(f.get("last_checked_at", "absent") is None for f in twin_facts), twin_facts


def test_the_delivery_face_reads_its_own_clicks_durable_outcome() -> None:
    """Codex Astra r1 finding 3: the browser case reads the click's own answer
    (the delivery row and the owner's receipt) and the hub's stored row, not
    only the words on the face."""
    case = _all_cases()["case.p9.update.delivered_row"]
    parts = {p["kind"]: p for p in case["expected"]["predicate"]["predicates"]}
    assert case["trigger"]["trigger_route"] == {"method": "POST", "path": "/api/updates/{update_id}/delivered"}
    status = parts["protocol_status"]
    assert status["path"] == case["trigger"]["trigger_route"]["path"] and status["status"] == 200
    assert status["body_fields"]["delivery.delivered_to"] == "Priya"
    assert status["body_fields"]["receipt.state"] == "succeeded"
    assert status["body_fields"]["receipt.actor_kind"] == "owner"
    row = parts["protocol_reads"]["expect"][0]["row"]["match"]
    assert row["id"] == "{update_id}" and row["deliveries.0.delivered_to"] == "Priya"
    assert parts["readable_text"]["value"] == "Priya"


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


# ── Codex Astra r1 finding 1: every claimed run keeps its own record ──

SHOTS = REPO / "pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-05-shots"
RETAINED = ("p9-merged", "p78-merged")
# The base atlas and Phase 3 (194 runs per product): the observation of every
# run is kept; its shots are not (about 200 MB), which the evidence says.
OBSERVATION_ONLY = ("base-294632c0", "base-merged")


@pytest.mark.parametrize("label", RETAINED + OBSERVATION_ONLY)
def test_every_claimed_run_keeps_its_own_observation(label) -> None:
    """One runs.tsv row = one directory = one observation of THAT case at THAT
    width with THAT verdict. A copier that lets one run overwrite another
    (round one: 1 of 28 kept) fails here."""
    rows = [line.split("\t") for line in (SHOTS / label / "runs.tsv").read_text().splitlines()[1:]]
    assert rows
    dirs = [row[7] for row in rows]
    assert len(set(dirs)) == len(dirs), "two rows share one run directory"
    for f, cid, width, verdict, *_rest, run_dir in rows:
        obs = json.loads((SHOTS / label / run_dir / "observation.json").read_text())
        assert obs["case_id"] == cid, (run_dir, obs["case_id"])
        assert obs["verdict"] == verdict, (run_dir, obs["verdict"], verdict)
        if width != "op" and label not in OBSERVATION_ONLY:
            assert obs["viewport"] == int(width), (run_dir, obs["viewport"])
            shots = [p for p in (SHOTS / label / run_dir).iterdir() if p.suffix in (".png", ".jpg")]
            assert shots, f"{run_dir}: a face run kept no shot"
    on_disk = {f"{p.parent.name}/{p.name}" for p in (SHOTS / label).glob("*/*") if p.is_dir()}
    assert on_disk == set(dirs), sorted(on_disk ^ set(dirs))
