"""The startup assignment migration: old Config into assignment rows, once."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from holdspeak.db import Database
from holdspeak.services.assignment_migration import AssignmentMigration
from holdspeak.services.inference_assignment_service import InferenceAssignmentService
from tests.unit.test_phase143_inference_assignments import OWNER, _profile, _result_claim


def test_config_migration_is_one_way_and_builtin_sentinel_nominates_one_repair(
    tmp_path: Path,
) -> None:
    db = Database(tmp_path / "migration.db")
    service = AssignmentMigration(db)
    missing = SimpleNamespace(
        thoughts=SimpleNamespace(inference_target_id=None),
        dictation=SimpleNamespace(runtime=SimpleNamespace(profile_id=None)),
    )
    issue = service.migrate_legacy_config(OWNER, missing)
    assert (issue["reason_code"], issue["repair"]) == (
        "builtin_profile_required", "choose_model_profile",
    )
    assert InferenceAssignmentService(db).migration_marker(
        OWNER, family="thoughts-writing-route-assignments"
    ) is None

    _profile(db, "thought-v2", claims=("language", _result_claim("thought.interview")))
    _profile(db, "writing-v2", claims=("language", _result_claim("speech.intent_classify")))
    configured = SimpleNamespace(
        thoughts=SimpleNamespace(inference_target_id="thought-v2"),
        dictation=SimpleNamespace(runtime=SimpleNamespace(profile_id="writing-v2")),
    )
    first = service.migrate_legacy_config(OWNER, configured)
    configured.thoughts.inference_target_id = "changed-after-marker"
    replay = service.migrate_legacy_config(OWNER, configured)
    assert first["status"] == replay["status"] == "migrated"
    assert replay["legacy_config_read"] is False
    assert replay["source_sha256"] == first["source_sha256"]


def test_config_migration_rolls_back_every_assignment_when_one_is_incompatible(
    tmp_path: Path,
) -> None:
    db = Database(tmp_path / "migration-atomic.db")
    _profile(
        db,
        "thought-v2",
        claims=("language", _result_claim("thought.interview"), _result_claim("ask.answer")),
    )
    _profile(db, "writing-incompatible", claims=("language",))
    configured = SimpleNamespace(
        thoughts=SimpleNamespace(inference_target_id="thought-v2"),
        dictation=SimpleNamespace(
            runtime=SimpleNamespace(profile_id="writing-incompatible")
        ),
    )
    with pytest.raises(Exception):
        AssignmentMigration(db).migrate_legacy_config(OWNER, configured)
    with db._connection() as conn:
        assert conn.execute(
            "SELECT COUNT(*) FROM inference_assignment_heads WHERE assignment_key LIKE 'capability:%'"
        ).fetchone()[0] == 0
        assert conn.execute(
            "SELECT COUNT(*) FROM inference_assignment_migrations"
        ).fetchone()[0] == 0
