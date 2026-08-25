"""HS-143-10 subject-pointer migration uses the canonical assignment authority."""
from __future__ import annotations

from pathlib import Path

import pytest

from holdspeak.db import Database
from holdspeak.inference_capabilities import UnknownInferenceCapability
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.errors import ValidationError
from holdspeak.services.inference_adoption_service import RoutedInferenceCoordinator
from holdspeak.services.inference_assignment_service import InferenceAssignmentService
from tests.unit.test_phase143_inference_assignments import _profile, _result_claim


OWNER = Principal(PrincipalKind.OWNER, "owner")


def test_recipe_and_workbench_pointers_become_exact_subject_rows_once(tmp_path: Path) -> None:
    db = Database(tmp_path / "subject-pointers.db")
    # The four text capabilities share one exact result-schema claim.
    claims = (_result_claim("recipe.run"),)
    _profile(db, "subject-primary", claims=claims)
    db.recipes.upsert(recipe_id="recipe-one", name="One", profile_id="subject-primary")
    db.recipes.upsert(recipe_id="recipe-blank", name="Blank")
    db.workbenches.upsert(workbench_id="workbench-one", name="One", profile_id="subject-primary", resolver_profile_id="subject-primary")
    db.workbenches.upsert(workbench_id="workbench-blank", name="Blank")

    coordinator = RoutedInferenceCoordinator(db)
    first = coordinator.migrate_recipe_workbench_subject_assignments(OWNER)
    replay = coordinator.migrate_recipe_workbench_subject_assignments(OWNER)

    assert first["status"] == replay["status"] == "migrated"
    assert first["legacy_config_read"] is True and replay["legacy_config_read"] is False
    assert len(first["source_records"]) == 6
    assignments = InferenceAssignmentService(db)
    for kind, subject, capability in (
        ("recipe", "recipe-one", "recipe.run"),
        ("recipe", "recipe-one", "recipe.chat"),
        ("workbench", "workbench-one", "workbench.item"),
        ("workbench", "workbench-one", "voice.reference_resolve"),
    ):
        resolved = assignments.resolve_effective(OWNER, capability_id=capability, subject_kind=kind, subject_id=subject)
        assert resolved["status"] == "assigned"
        assert resolved["assignment"]["scope"]["kind"] == "subject"
        assert resolved["assignment"]["entries"][0]["profile_id"] == "subject-primary"
    for kind, subject, capability in (
        ("recipe", "recipe-blank", "recipe.run"),
        ("workbench", "workbench-blank", "workbench.item"),
    ):
        assert assignments.resolve_effective(OWNER, capability_id=capability, subject_kind=kind, subject_id=subject)["status"] == "no_assignment"


def test_migration_preserves_divergent_broader_policy_and_blank_inheritance(tmp_path: Path) -> None:
    """A pointer creates only its exact override; a blank keeps group inheritance."""
    db = Database(tmp_path / "subject-inheritance.db")
    claim = (_result_claim("recipe.run"),)
    _profile(db, "global-route", claims=claim)
    _profile(db, "group-route", claims=claim)
    _profile(db, "recipe-route", claims=claim)
    assignments = InferenceAssignmentService(db)
    assignments.set_assignment(OWNER, {
        "command_id": "set-global", "expected_revision": 0, "scope": {"kind": "global"},
        "entries": [{"profile_id": "global-route", "profile_revision": 1}],
    })
    assignments.set_assignment(OWNER, {
        "command_id": "set-agents", "expected_revision": 0,
        "scope": {"kind": "group", "group_id": "agents_tools"},
        "entries": [{"profile_id": "group-route", "profile_revision": 1}],
    })
    global_assignment = assignments.get_assignment(OWNER, {"kind": "global"})
    group_assignment = assignments.get_assignment(OWNER, {"kind": "group", "group_id": "agents_tools"})
    db.recipes.upsert(recipe_id="pointer", name="Pointer", profile_id="recipe-route")
    db.recipes.upsert(recipe_id="blank", name="Blank")

    RoutedInferenceCoordinator(db).migrate_recipe_workbench_subject_assignments(OWNER)

    pointed = assignments.resolve_effective(
        OWNER, capability_id="recipe.run", subject_kind="recipe", subject_id="pointer"
    )
    blank = assignments.resolve_effective(
        OWNER, capability_id="recipe.run", subject_kind="recipe", subject_id="blank"
    )
    assert pointed["inherited_from"] == "subject"
    assert pointed["assignment"]["entries"][0]["profile_id"] == "recipe-route"
    assert blank["inherited_from"] == "group"
    assert blank["assignment"]["entries"][0]["profile_id"] == "group-route"
    assert assignments.get_assignment(OWNER, {"kind": "global"}) == global_assignment
    assert assignments.get_assignment(OWNER, {"kind": "group", "group_id": "agents_tools"}) == group_assignment


def test_dangling_pointer_refuses_without_marker_or_partial_subject_rows(tmp_path: Path) -> None:
    db = Database(tmp_path / "dangling-subject.db")
    _profile(db, "good-route", claims=(_result_claim("recipe.run"),))
    db.recipes.upsert(recipe_id="good", name="Good", profile_id="good-route")
    db.recipes.upsert(recipe_id="dangling", name="Dangling", profile_id="gone-route")
    coordinator = RoutedInferenceCoordinator(db)
    assignments = InferenceAssignmentService(db)

    with pytest.raises(ValidationError) as refused:
        coordinator.migrate_recipe_workbench_subject_assignments(OWNER)

    assert refused.value.code == "inference_assignment_profile_missing"
    assert assignments.migration_marker(OWNER, family="recipe-workbench-subject-route-assignments") is None
    assert assignments.resolve_effective(
        OWNER, capability_id="recipe.run", subject_kind="recipe", subject_id="good"
    )["status"] == "no_assignment"


def test_atomic_helper_rolls_back_rows_when_later_subject_is_invalid(tmp_path: Path) -> None:
    """The marker cannot survive a partial list of migrated subject rows."""
    db = Database(tmp_path / "subject-rollback.db")
    _profile(db, "good-route", claims=(_result_claim("recipe.run"),))
    assignments = InferenceAssignmentService(db)
    rows = (
        {"subject_kind": "recipe", "subject_id": "first", "capability_id": "recipe.run", "entry": {"profile_id": "good-route", "profile_revision": 1}},
        {"subject_kind": "recipe", "subject_id": "second", "capability_id": "not.a.capability", "entry": {"profile_id": "good-route", "profile_revision": 1}},
    )
    records = (
        {"record_kind": "recipe", "record_id": "first", "field": "profile_id", "legacy_value": "good-route", "legacy_read": True},
        {"record_kind": "recipe", "record_id": "second", "field": "profile_id", "legacy_value": "good-route", "legacy_read": True},
    )

    with pytest.raises(UnknownInferenceCapability):
        assignments.migrate_subject_assignments_atomically(
            OWNER, family="recipe-workbench-subject-rollback", source_sha256="sha256:" + "0" * 64,
            subject_entries=rows, source_records=records,
        )

    assert assignments.migration_marker(OWNER, family="recipe-workbench-subject-rollback") is None
    assert assignments.resolve_effective(
        OWNER, capability_id="recipe.run", subject_kind="recipe", subject_id="first"
    )["status"] == "no_assignment"


def test_post_marker_recipe_write_updates_assignment_and_workbench_write_refuses(tmp_path: Path) -> None:
    """Legacy field controls cannot silently become execution-dead after cutover."""
    from holdspeak.kernel.runtime import _configure
    from holdspeak.services.recipe_service import RecipeService
    from holdspeak.services.workbench_service import WorkbenchService

    db = Database(tmp_path / "post-marker.db")
    claim = (_result_claim("recipe.run"),)
    _profile(db, "before", claims=claim)
    _profile(db, "after", claims=claim)
    db.recipes.upsert(recipe_id="recipe", name="Recipe", profile_id="before")
    db.workbenches.upsert(workbench_id="workbench", name="Workbench", profile_id="before")
    broker = _configure(db)
    coordinator = RoutedInferenceCoordinator(db)
    coordinator.migrate_recipe_workbench_subject_assignments(OWNER)
    assignments = InferenceAssignmentService(db)
    assignments.set_assignment(OWNER, {
        "command_id": "unchanged-global", "expected_revision": 0, "scope": {"kind": "global"},
        "entries": [{"profile_id": "before", "profile_revision": 1}],
    })
    global_assignment = assignments.get_assignment(OWNER, {"kind": "global"})

    RecipeService(db, broker=broker).update_recipe(OWNER, "recipe", profile_id="after")
    changed = assignments.resolve_effective(
        OWNER, capability_id="recipe.run", subject_kind="recipe", subject_id="recipe"
    )
    assert changed["assignment"]["entries"][0]["profile_id"] == "after"
    assert assignments.get_assignment(OWNER, {"kind": "global"}) == global_assignment

    workbenches = WorkbenchService(db)
    with pytest.raises(ValidationError) as refused:
        workbenches.update_workbench(OWNER, "workbench", profile_id="after")
    assert refused.value.code == "inference_legacy_selector_retired"
    assert db.workbenches.get("workbench").profile_id == "before"

    template_id = str(workbenches.list_templates(OWNER)[0]["id"])
    with pytest.raises(ValidationError) as template_refused:
        workbenches.instantiate_template(OWNER, template_id, profile_id="after")
    assert template_refused.value.code == "inference_legacy_selector_retired"
    assert len(db.recipes.list()) == 1 and len(db.workbenches.list()) == 1
