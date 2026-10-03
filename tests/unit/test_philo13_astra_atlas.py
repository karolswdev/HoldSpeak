"""PHILO-13 B0/B5: Astra's face paths and shared semantic contract.

The phase file owns its own case and operation-sibling count.  The shared
atlas contract still reads this file through ``ATLAS_FILES``; the mutant tests
below prove that its semantic guards reject a broken Phase 13 case before the
proper case is restored.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path
import subprocess

import pytest

from tests.unit import test_philo_graph_atlas as general


REPO = Path(__file__).resolve().parents[2]
ATLAS = REPO / "docs/internal/philo/graph/atlas-phase13-astra.json"
PRE_FIX_ATLAS_COMMIT = "e2e92c582"
EXPECTED_CASES = {
    "case.p13.directory.zone_window.op",
    "case.p13.calendar.snapshot_window",
    "case.p13.roadmap.window",
    "case.p13.repository.window",
    "case.p13.delivery.dossier_window",
    "case.p13.delivery.terminal_window",
    "case.p13.chain.pullout",
    "case.p13.coder.pullout",
    "case.p13.directory.zone",
    "case.p13.info.window",
    "case.p13.meeting.park_restore",
    "case.p13.workbench.park_restore",
    "case.p13.dock.needs_you_week",
    "case.p13.update.linked_week",
    "case.p13.update.linked_week.op",
    "case.p13.people.prep.protocol",
    "case.p13.people.prep",
}
PARKING_CASES = {"case.p13.meeting.park_restore", "case.p13.workbench.park_restore"}
NEEDS_YOU_CASES = {"case.p13.dock.needs_you_week"}
WEEK_CASES = {"case.p13.update.linked_week"}
PEOPLE_PREP_CASES = {"case.p13.people.prep", "case.p13.people.prep.protocol"}

LIVE_DOCK_CASES = {
    'case.p13.dock.send_sent',
    'case.p13.dock.send_failed',
    'case.p13.dock.send_unknown',
    'case.p13.dock.meeting_ready',
    'case.p13.dock.meeting_open_clears_ready',
    'case.p13.dock.meeting_read_survives_reload',
    'case.p13.dock.recording_refused',
    'case.p13.dock.reconnect',
}
EXPECTED_CASES |= LIVE_DOCK_CASES

LIFECYCLE_CASES = {
    "case.p13.roadmap.window": {
        "first_observe": ".desk-roadmap-window",
        "refusal_observe": '.desk-roadmap-window:has-text("Roadmap not found")',
        "reenter": "Floor",
        "reopen_selector": '[id="desk-palette-option-roadmap:roadmap:atlas-desk"]',
    },
    "case.p13.repository.window": {
        "first_observe": '.desk-repo-files .desk-sortable-table-row:has-text("atlas_repository.py")',
        "reenter": "Floor",
        "reopen_selector": '[id="desk-palette-option-repository:{repository_id}"]',
    },
    "case.p13.delivery.dossier_window": {
        "first_observe": ".desk-dlv-dossier .desk-dlv-facts-line",
        "reenter": "Delivery",
        "reopen_selector": '.desk-dlv-board .desk-mc-story-pick:has-text("ATLAS-1-01")',
    },
    "case.p13.delivery.terminal_window": {
        "first_observe": '.desk-dlv-terminal :text("Atlas terminal")',
        "reenter": "Delivery",
        "reopen_selector": '.desk-dlv-sessions .surface-ledger-line:has-text("atlas_terminal")',
    },
    "case.p13.chain.pullout": {
        "first_observe": '.desk-pullout[aria-label="Atlas B0 Sequence"] :text("No steps")',
        "reenter": "Floor",
        "reopen_selector": '[id="desk-palette-option-chain:{chain_id}"]',
        "dock_chip": ".desk-dock-chip button",
    },
    "case.p13.coder.pullout": {
        "first_observe": '.desk-pullout.is-card :text("Should I run the full suite now?")',
        "reenter": "Floor",
        "reopen_selector": '[id="desk-palette-option-coder:{coder_session_id}"]',
        "dock_chip": ".desk-dock-chip button",
    },
}

REPOSITORY_CASES = {
    "case.p13.roadmap.window",
    "case.p13.repository.window",
    "case.p13.delivery.dossier_window",
    "case.p13.delivery.terminal_window",
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


def _steps(case: dict) -> list[dict]:
    """Flatten real setup/trigger steps, including the trigger's `then` list."""
    pending = [*case.get("setup", [])]
    if case.get("trigger"):
        pending.append(case["trigger"])
    flattened: list[dict] = []
    while pending:
        step = pending.pop(0)
        flattened.append(step)
        then = step.get("then")
        if isinstance(then, list):
            pending[0:0] = then
    return flattened


def _assert_phase13_lifecycle_fence(atlas: dict) -> None:
    """Make each live first open and return leg belong to its trigger."""
    cases = {case["id"]: case for case in atlas["cases"]}
    for case_id, contract in LIFECYCLE_CASES.items():
        case = cases[case_id]
        setup_lifecycle = [
            step for step in case.get("setup", [])
            if step.get("action") == "reload"
            or "Close " in step.get("selector", "")
            or step.get("selector") == contract["first_observe"]
            or (
                contract.get("refusal_observe")
                and step.get("selector") == contract["refusal_observe"]
            )
            or step.get("selector") == ".desk-tools-launch"
            or step.get("selector") == contract["reopen_selector"]
            or (
                step.get("action") == "click_role"
                and step.get("name") == contract["reenter"]
            )
        ]
        assert not setup_lifecycle, f"{case_id}: setup owns live lifecycle {setup_lifecycle!r}"

        trigger_steps = _steps({"setup": [], "trigger": case["trigger"]})
        first_observations = [
            i for i, step in enumerate(trigger_steps)
            if step.get("action") == "wait_for"
            and step.get("selector") == contract["first_observe"]
            and step.get("state", "visible") == "visible"
        ]
        assert first_observations, f"{case_id}: trigger does not observe its first open"
        close_index = next(
            i for i, step in enumerate(trigger_steps)
            if "Close " in step.get("selector", "")
        )
        assert first_observations[0] < close_index, case_id
        assert trigger_steps[close_index + 1]["action"] == "wait_for", case_id
        assert trigger_steps[close_index + 1]["state"] == "hidden", case_id

        reload_index = next(
            i for i, step in enumerate(trigger_steps[close_index + 1:], close_index + 1)
            if step.get("action") == "reload"
        )
        assert reload_index > close_index, case_id
        reentry_index = next(
            i for i, step in enumerate(trigger_steps[reload_index + 1:], reload_index + 1)
            if step.get("action") == "click_role"
            and step.get("name") == contract["reenter"]
        )
        reopen_indices = [
            i for i, step in enumerate(trigger_steps)
            if step.get("selector") == contract["reopen_selector"]
        ]
        assert len(reopen_indices) >= 2, f"{case_id}: final opener is not in trigger.then"
        assert reopen_indices[-1] > reentry_index, case_id
        dock_selector = contract.get("dock_chip")
        if dock_selector:
            assert "removes its Dock chip when closed before reload" in case["expected"]["words"]
            dock_visible = [
                i for i, step in enumerate(trigger_steps)
                if step.get("action") == "wait_for"
                and step.get("selector") == dock_selector
                and step.get("state", "visible") == "visible"
            ]
            dock_hidden = [
                i for i, step in enumerate(trigger_steps)
                if step.get("action") == "wait_for"
                and step.get("selector") == dock_selector
                and step.get("state") == "hidden"
            ]
            assert len(dock_visible) >= 2 and len(dock_hidden) == 1, case_id
            assert first_observations[0] < dock_visible[0] < close_index, case_id
            assert close_index < dock_hidden[0] < reload_index, case_id
            assert dock_visible[-1] > reopen_indices[-1], case_id
        final_observations = [
            i for i in first_observations[1:]
            if i > reopen_indices[-1]
        ]
        assert final_observations, f"{case_id}: trigger does not observe its reopened face"

        refusal_selector = contract.get("refusal_observe")
        if refusal_selector:
            refusal_observations = [
                i for i, step in enumerate(trigger_steps)
                if step.get("action") == "wait_for"
                and step.get("selector") == refusal_selector
                and step.get("state", "visible") == "visible"
            ]
            assert len(refusal_observations) >= 2, (
                f"{case_id}: trigger must observe the first and final refusal"
            )
            assert first_observations[0] < refusal_observations[0] < close_index, case_id
            assert first_observations[-1] < refusal_observations[-1], case_id
            assert refusal_observations[-1] > reopen_indices[-1], case_id


def _assert_phase13_spatial_reload_fence(atlas: dict) -> None:
    """Require Floor and the real canvas before Spatial's second context door."""
    cases = {case["id"]: case for case in atlas["cases"]}
    for case_id in ("case.p13.directory.zone", "case.p13.info.window"):
        trigger_steps = _steps({"setup": [], "trigger": cases[case_id]["trigger"]})
        doors = [
            i for i, step in enumerate(trigger_steps)
            if step.get("action") == "world_context_menu"
        ]
        assert len(doors) == 2, f"{case_id}: expected first and post-reload context doors"
        reload_index = next(
            i for i, step in enumerate(trigger_steps)
            if step.get("action") == "reload"
        )
        floor_wait = next(
            i for i, step in enumerate(trigger_steps[reload_index + 1:], reload_index + 1)
            if step.get("action") == "wait_for"
            and step.get("selector") == '[data-testid="chair-floor-toggle"]'
            and step.get("state") == "visible"
        )
        floor_click = next(
            i for i, step in enumerate(trigger_steps[floor_wait + 1:], floor_wait + 1)
            if step.get("action") == "click_role" and step.get("name") == "Floor"
        )
        canvas_wait = next(
            i for i, step in enumerate(trigger_steps[floor_click + 1:], floor_click + 1)
            if step.get("action") == "wait_for"
            and step.get("selector") == ".desk-world-canvas"
            and step.get("state") == "visible"
        )
        assert reload_index < floor_wait < floor_click < canvas_wait < doors[1], case_id


def _assert_phase13_repository_seam_fence(atlas: dict) -> None:
    """Every repository-backed case discloses the real router seam patch."""
    cases = {case["id"]: case for case in atlas["cases"]}
    missing = []
    for case_id in REPOSITORY_CASES:
        case = cases[case_id]
        prose = json.dumps({
            "preconditions": case.get("preconditions", []),
            "setup": case.get("setup", []),
        })
        if "build_roadmaps_router" not in prose:
            missing.append(case_id)
    assert not missing, f"repository cases omit the real build_roadmaps_router seam: {sorted(missing)}"


def _assert_phase13_coder_producer_fence(atlas: dict) -> None:
    """Refresh Coder status after its real producer writes the row."""
    case = next(case for case in atlas["cases"] if case["id"] == "case.p13.coder.pullout")
    setup = case["setup"]
    assert [step.get("action") for step in setup[:2]] == [
        "goto",
        "click_role",
    ], "Coder still crosses the real arrival gate before producer work"
    assert setup[1].get("name") == "Continue later" and setup[1].get("optional") is True
    assert [step.get("action") for step in setup[-2:]] == [
        "create_repository_fixture",
        "ingest_coder_fixture",
    ], "Coder setup must mint the real repository and session before the refresh"

    trigger_steps = _steps({"setup": [], "trigger": case["trigger"]})
    assert trigger_steps[0].get("action") == "reload", (
        "Coder status must be refreshed after agent-hook ingestion"
    )
    assert trigger_steps[0].get("adapter") == "ui-navigation"

    coder_door = '[id="desk-palette-option-coder:{coder_session_id}"]'
    door_indices = [
        i for i, step in enumerate(trigger_steps)
        if step.get("action") == "click" and step.get("selector") == coder_door
    ]
    assert len(door_indices) == 2, "the same real Coder object door must open twice"
    for door_index in door_indices:
        assert any(
            step.get("action") == "fill"
            and step.get("value") == "Atlas"
            for step in trigger_steps[max(0, door_index - 2):door_index]
        ), f"Coder object door {door_index} must be searched after opening the palette"

    words = case["expected"]["words"].lower()
    for phrase in (
        "agent-hook",
        "page refreshes to read it",
        "coder object door",
        "removes its dock chip when closed before reload",
    ):
        assert phrase in words, f"Coder case words omit {phrase!r}: {case['expected']['words']!r}"


def _assert_phase13_roadmap_case_fence(atlas: dict) -> None:
    """Fence the observed Roadmap refusal as Product-red, never as success."""
    case = next(case for case in atlas["cases"] if case["id"] == "case.p13.roadmap.window")
    expected = case["expected"]
    assert expected["predicate"] == {
        "kind": "readable_text",
        "value": "Roadmap not found",
    }
    assert expected["observe_at"] == ".desk-roadmap-window"
    words = expected["words"].lower()
    for phrase in (
        "repository-fixture-producer",
        "roadmap",
        "refuses",
        "not found",
        "refusal",
        "reopen",
    ):
        assert phrase in words, f"Roadmap expected words omit {phrase!r}: {expected['words']!r}"

    for step in _steps(case):
        if step.get("kind") == "ui" and step.get("action") in {"click", "click_role"}:
            assert step.get("adapter") == "ui-by-viewport", step

    trigger_steps = _steps({"setup": [], "trigger": case["trigger"]})
    window_selector = LIFECYCLE_CASES[case["id"]]["first_observe"]
    window_observations = [
        i for i, step in enumerate(trigger_steps)
        if step.get("action") == "wait_for"
        and step.get("selector") == window_selector
        and step.get("state", "visible") == "visible"
        and step.get("adapter") == "ui-observation"
    ]
    assert len(window_observations) >= 2, (
        "case.p13.roadmap.window: window must be observed on first open and reopen"
    )
    refusal_selector = LIFECYCLE_CASES[case["id"]]["refusal_observe"]
    refusal_observations = [
        i for i, step in enumerate(trigger_steps)
        if step.get("action") == "wait_for"
        and step.get("selector") == refusal_selector
        and step.get("state", "visible") == "visible"
        and step.get("adapter") == "ui-observation"
    ]
    assert len(refusal_observations) >= 2, (
        "case.p13.roadmap.window: refusal must be observed on first open and reopen"
    )
    assert window_observations[0] < refusal_observations[0]
    assert window_observations[-1] < refusal_observations[-1]


def _committed_atlas() -> dict:
    """Read the actual r2-counsel baseline, independent of the moving HEAD."""
    atlas_path = "docs/internal/philo/graph/atlas-phase13-astra.json"
    raw = subprocess.check_output(
        ["git", "show", f"{PRE_FIX_ATLAS_COMMIT}:{atlas_path}"],
        cwd=REPO,
        text=True,
    )
    return json.loads(raw)


def _assert_phase13_case_fence(atlas: dict) -> None:
    """Keep each corrected door live and reject the three old case paths."""
    cases = {case["id"]: case for case in atlas["cases"]}
    calendar = cases["case.p13.calendar.snapshot_window"]
    assert calendar["applicability"] == "applicable"
    expected = calendar["expected"]
    assert expected["predicate"] == {
        "kind": "readable_text",
        "value": "no_vision_model_assigned",
    }
    assert expected["observe_at"] == "[role=region][aria-label^=Calendar]"

    press_actions = {"click", "click_role", "focus", "press", "scroll_into_view", "set_input_files"}
    for step in _steps(calendar):
        if step.get("kind") == "ui" and step.get("action") in press_actions:
            assert step.get("adapter") == "ui-by-viewport", step

    trigger_steps = _steps({"setup": [], "trigger": calendar["trigger"]})
    close_index = next(
        i for i, step in enumerate(trigger_steps)
        if step.get("action") == "click"
        and '[role="region"][aria-label="Calendar snapshot"] button[aria-label^="Close "]' in step.get("selector", "")
    )
    assert trigger_steps[close_index + 1]["action"] == "wait_for"
    assert trigger_steps[close_index + 1]["state"] == "hidden"
    reload_index = next(
        i for i, step in enumerate(trigger_steps[close_index + 1:], close_index + 1)
        if step.get("action") == "reload"
    )
    assert reload_index > close_index
    assert any(
        step.get("action") == "wait_for"
        and step.get("selector") == '[role="region"][aria-label="Calendar snapshot"]'
        for step in trigger_steps[reload_index + 1:]
    )

    directory = cases["case.p13.directory.zone"]
    assert directory["applicability"] == "applicable"
    assert directory["expected"]["predicate"] == {
        "kind": "readable_text",
        "value": "Atlas Phase 13 Zone",
    }
    assert directory["expected"]["observe_at"] == ".desk-zone-window"
    assert "should open its real ZoneWindow" in directory["expected"]["words"]
    assert directory["trigger"]["action"] == "world_context_menu"
    zone_doors = [
        step for step in _steps(directory)
        if step.get("action") == "world_context_menu"
    ]
    assert len(zone_doors) == 2, directory["id"]
    assert all(
        step.get("selector") == ".desk-world-canvas"
        and step.get("world_target") == "zone"
        and step.get("world_ref") == "{zone_id}"
        and step.get("adapter") == "ui-by-viewport"
        for step in zone_doors
    ), directory["id"]
    assert all(
        step.get("action") == "click_role" and step.get("name") == "Open"
        for door in zone_doors for step in door.get("then", [])[:1]
    ), directory["id"]
    assert "[data-zone-id=" not in json.dumps(directory), f"{directory['id']}: hidden zone selector is forbidden"

    info = cases["case.p13.info.window"]
    assert info["applicability"] == "applicable"
    assert info["expected"]["predicate"] == {"kind": "readable_text", "value": "IDENTITY"}
    assert info["expected"]["observe_at"] == ".desk-info-window"
    assert info["completion_bound_s"] == 75
    assert any("52.465 s" in text and "75 s" in text for text in info["preconditions"])
    assert info["trigger"]["action"] == "world_context_menu"
    info_doors = [
        step for step in _steps(info)
        if step.get("action") == "world_context_menu"
    ]
    assert len(info_doors) == 2, info["id"]
    assert all(
        step.get("selector") == ".desk-world-canvas"
        and step.get("world_target") == "object"
        and step.get("world_ref") == "sequence:{info_chain_id}"
        and step.get("adapter") == "ui-by-viewport"
        for step in info_doors
    ), info["id"]
    assert all(
        step.get("action") == "click_role" and step.get("name") == "Get Info"
        for door in info_doors for step in door.get("then", [])[:1]
    ), info["id"]
    assert "desk-list-name-cell" not in json.dumps(info), f"{info['id']}: List is not the Spatial door"

    # At 1440 the Floor's unset view is already Spatial; a palette action
    # named "Spatial view" would toggle it back to List.  The compact phone
    # path alone needs the real palette toggle from its dense List default.
    for case in (directory, info):
        mode_steps = [
            step for step in case["setup"]
            if step.get("at_width") in (1440, 393)
            and (
                step.get("selector") == ".desk-tools-launch"
                or step.get("selector") == 'input[placeholder="Search tools and Desk items"]'
                or step.get("selector") == '[id="desk-palette-option-desk.toggle-view"]'
            )
        ]
        assert not [step for step in mode_steps if step.get("at_width") == 1440], case["id"]
        assert [
            (step.get("action"), step.get("selector"), step.get("value"))
            for step in mode_steps if step.get("at_width") == 393
        ] == [
            ("click", ".desk-tools-launch", None),
            ("fill", 'input[placeholder="Search tools and Desk items"]', "Spatial view"),
            ("click", '[id="desk-palette-option-desk.toggle-view"]', None),
        ], case["id"]


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
    # C6 is already folded: this atlas owns the B0 and B5 .op siblings; the
    # historical 69 stays only in the shared Phase 1–12 population fence.
    assert sum(case["id"].endswith(".op") for case in cases.values()) == 2
    faces = [
        case for case in cases.values()
        if not case["id"].endswith(".op")
        and case["id"] not in PARKING_CASES | NEEDS_YOU_CASES | LIVE_DOCK_CASES | WEEK_CASES | PEOPLE_PREP_CASES
    ]
    assert len(faces) == 9
    for case in faces:
        assert case["viewports"] == [1440, 393]
        assert case["applicability"] == "applicable", case["id"]
        # A DOM-only text match passed an off-screen Repository in the real walk.
        assert case["expected"]["predicate"]["kind"] == "readable_text", case["id"]
        steps = _steps(case)
        close_index = next(i for i, step in enumerate(steps) if 'Close ' in step.get("selector", ""))
        assert steps[close_index + 1]["state"] == "hidden", case["id"]
        reload_indices = [
            i for i, step in enumerate(steps[close_index + 2:], close_index + 2)
            if step.get("action") == "reload"
        ]
        assert reload_indices, case["id"]


def test_b5_week_cases_keep_the_real_producer_and_deterministic_ui_contract() -> None:
    case = _cases()["case.p13.update.linked_week"]
    assert case["edge_ids"] == ["edge.face.room_updates"]
    assert case["state_id"] == "state.desk_presentation.p13_week"
    steps = _steps(case)
    assert any(
        step.get("kind") == "boundary"
        and step.get("reply") == "tests/fixtures/philo13_b5_week_summary_reply.json"
        for step in steps
    )
    meeting_import = next(
        step for step in steps
        if step.get("kind") == "op" and step.get("name") == "meeting.import"
    )
    assert meeting_import["args"]["path"] == "tests/fixtures/philo13_b5_week_transcript.vtt"
    assert any(
        step.get("kind") == "cli"
        and step.get("action") == "queue_meeting_intelligence"
        for step in steps
    )
    assert any(
        step.get("kind") == "op"
        and step.get("name") == "project.resource.add"
        and step.get("args", {}).get("resource_ref") == "decision_record:{record_id}"
        for step in steps
    )
    assert case["trigger"]["selector"] == "[data-testid=update-verb-draft-deterministic]"
    assert case["trigger"]["adapter"] == "ui-by-viewport"
    assert case["trigger"]["trigger_route"] == {
        "method": "POST",
        "path": "/api/projects/{project_id}/updates/draft",
    }
    assert case["expected"]["observe_at"] == "[data-testid=update-body-editor]"
    expected = case["expected"]["predicate"]
    assert expected["kind"] == "all_of"
    text_values = {
        part["value"] for part in expected["predicates"]
        if part.get("kind") == "text_contains"
    }
    for value in (
        "The ledger cutover is ready for the controlled migration.",
        "Decision: Use the controlled migration window",
        "Action: Confirm the migration window",
        "owner Avery",
        "Action: Send the rollback checklist",
        "owner Morgan",
    ):
        assert value in text_values
    assert any(
        part.get("kind") == "protocol_reads"
        for part in expected["predicates"]
    )
    assert case["expected"]["reads"] == [{
        "method": "GET",
        "path": "/api/projects/{project_id}/updates",
    }]
    for step in steps:
        if step.get("kind") == "ui" and step.get("action") in {"click", "click_role"}:
            assert step.get("adapter") == "ui-by-viewport", step
        if step.get("kind") == "ui" and step.get("action") == "wait_for":
            assert step.get("adapter") != "ui-by-viewport", step


def test_b5_week_operation_sibling_binds_the_stored_deterministic_draft() -> None:
    case = _cases()["case.p13.update.linked_week.op"]
    assert case["viewports"] == []
    assert not any(step.get("kind") == "ui" for step in _steps(case))
    assert case["trigger"]["name"] == "project.draft_update"
    assert case["trigger"]["args"] == {
        "project_id": "{project_id}",
        "generator": "deterministic",
    }
    assert case["trigger"]["capture_path"] == "update.id"
    assert case["expected"]["observe_at"] == {
        "kind": "op",
        "name": "project.list_updates",
        "args": {"project_id": "{project_id}"},
    }
    facts = case["expected"]["predicate"]["facts"]
    assert {fact["path"] for fact in facts} >= {
        "update.id",
        "update.generator",
        "update.lifecycle",
        "update.body_md",
        "update.claims_json",
        "updates",
        "updates.0.body_md",
        "updates.0.claims_json",
    }
    assert case["expected"]["reads"] == [{
        "kind": "op",
        "name": "project.list_updates",
        "args": {"project_id": "{project_id}"},
    }]


def test_needs_you_case_reads_six_before_real_mutation_and_five_after_reload() -> None:
    case = _cases()["case.p13.dock.needs_you_week"]
    assert case["viewports"] == [1440, 393]
    setup = case["setup"]
    seed_index = next(i for i, step in enumerate(setup) if step.get("action") == "seed_needs_you_week")
    six_index = next(i for i, step in enumerate(setup) if step.get("predicate") == {"kind": "readable_text", "value": "6"})
    done_index = next(i for i, step in enumerate(setup) if step.get("path") == "/api/all-action-items/{item_id}")
    assert seed_index < six_index < done_index
    assert setup[six_index]["capture_shot"] is True
    assert setup[done_index]["method"] == "PATCH"
    assert setup[done_index]["body"] == {"status": "done"}
    assert case["trigger"]["action"] == "reload"
    assert case["expected"]["predicate"] == {"kind": "readable_text", "value": "5"}
    assert "desk-dock-badge" in case["expected"]["observe_at"]


def test_people_prep_cases_fence_suggestion_link_and_owned_prep_data() -> None:
    op = _cases()["case.p13.people.prep.protocol"]
    setup = op["setup"]
    seed = next(i for i, step in enumerate(setup) if step.get("action") == "seed_people_prep")
    suggestion = next(i for i, step in enumerate(setup) if step.get("capture_as") == "people_suggestion_uid")
    link = next(i for i, step in enumerate(setup) if step.get("path", "").endswith("/calendar-links"))
    brief_check = next(i for i, step in enumerate(setup) if step.get("kind") == "check" and "brief" in step.get("observe_at", ""))
    assert seed < suggestion < link < brief_check
    assert setup[suggestion]["capture_match"] == {
        "uid": "{people_event_uid}", "source_id": "{people_event_source_id}",
    }
    fields = {part["path"] for part in setup[brief_check]["predicate"]["predicates"]}
    assert {
        "brief.next_one_on_one.uid",
        "brief.open_meeting_actions.0.id",
        "brief.agenda_items.0.body",
        "brief.projects.0.id",
    } <= fields
    face = _cases()["case.p13.people.prep"]
    assert face["viewports"] == [1440, 393]
    assert face["expected"]["predicate"] == {
        "kind": "readable_text", "value": "Send the dry-run report",
    }


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


def test_phase13_case_fence_rejects_old_doors_then_accepts_current_atlas() -> None:
    proper = _atlas()
    _assert_phase13_case_fence(proper)

    old_calendar = copy.deepcopy(proper)
    calendar = next(case for case in old_calendar["cases"] if case["id"] == "case.p13.calendar.snapshot_window")
    calendar["expected"]["predicate"]["value"] = "CONFIRM"
    with pytest.raises(AssertionError):
        _assert_phase13_case_fence(old_calendar)

    old_directory = copy.deepcopy(proper)
    directory = next(case for case in old_directory["cases"] if case["id"] == "case.p13.directory.zone")
    directory["trigger"] = {
        "kind": "ui",
        "action": "focus",
        "adapter": "ui-input",
        "selector": '[data-zone-id="{zone_id}"]',
    }
    with pytest.raises(AssertionError, match="world_context_menu"):
        _assert_phase13_case_fence(old_directory)

    old_info = copy.deepcopy(proper)
    info = next(case for case in old_info["cases"] if case["id"] == "case.p13.info.window")
    info["setup"] = [{
        "kind": "ui",
        "action": "click",
        "adapter": "ui-by-viewport",
        "selector": '.desk-list-name-cell[aria-label="Atlas B0 Info Sequence"]',
        "button": "right",
    }]
    with pytest.raises(AssertionError, match="world_context_menu"):
        _assert_phase13_case_fence(old_info)


def test_phase13_lifecycle_fence_accepts_only_trigger_owned_sequences() -> None:
    _assert_phase13_lifecycle_fence(_atlas())


def test_phase13_coder_fence_rejects_stale_page_then_accepts_produced_door() -> None:
    """The real committed case omits a post-ingestion refresh; the fixed case owns it."""
    with pytest.raises(AssertionError):
        _assert_phase13_coder_producer_fence(_committed_atlas())
    _assert_phase13_coder_producer_fence(_atlas())


def test_phase13_roadmap_fence_rejects_committed_pre_fix_atlas_then_accepts_current() -> None:
    """The real pre-fix Atlas is red; the observed refusal is green after the fix."""
    pre_fix = _committed_atlas()
    with pytest.raises(AssertionError):
        _assert_phase13_lifecycle_fence(pre_fix)
    with pytest.raises(AssertionError):
        _assert_phase13_roadmap_case_fence(pre_fix)

    current = _atlas()
    _assert_phase13_lifecycle_fence(current)
    _assert_phase13_roadmap_case_fence(current)

    wrong_words = copy.deepcopy(current)
    roadmap = next(case for case in wrong_words["cases"] if case["id"] == "case.p13.roadmap.window")
    roadmap["expected"]["words"] = "The Roadmap opens successfully and is ready to use."
    with pytest.raises(AssertionError):
        _assert_phase13_roadmap_case_fence(wrong_words)

    wrong_selector = copy.deepcopy(current)
    roadmap = next(case for case in wrong_selector["cases"] if case["id"] == "case.p13.roadmap.window")
    roadmap["expected"]["observe_at"] = ".desk-roadmap-phase-row"
    with pytest.raises(AssertionError):
        _assert_phase13_roadmap_case_fence(wrong_selector)


def test_phase13_spatial_reload_fence_accepts_only_floor_reentry() -> None:
    _assert_phase13_spatial_reload_fence(_atlas())


def test_phase13_repository_cases_name_the_real_router_seam() -> None:
    _assert_phase13_repository_seam_fence(_atlas())


def test_live_dock_cases_keep_real_producers_and_no_reload_after_send():
    cases = _cases()
    for outcome in ("sent", "failed", "unknown"):
        case = cases[f"case.p13.dock.send_{outcome}"]
        assert case["trigger"]["name"] == "channel.send"
        assert case["expected"]["reads"][0]["name"] == "channel.sends"
        assert not case["trigger"].get("then")
        assert any(step.get("substitute") == "cli_runner" for step in case["setup"])
    ready = cases["case.p13.dock.meeting_ready"]
    assert ready["trigger"]["action"] == "queue_meeting_intelligence"
    assert any(step.get("name") == "meeting.import" for step in ready["setup"])
    reconnect = cases["case.p13.dock.reconnect"]
    assert any(step.get("action") == "stop_hub" for step in reconnect["setup"])
    assert any(step.get("capture_shot") and step.get("observe_at") == "[data-testid=desk-dock-offline]" for step in reconnect["setup"])
    assert reconnect["trigger"]["action"] == "restart_hub"
