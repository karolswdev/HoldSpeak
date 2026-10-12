"""HS-201-07 — startup names the loaded runtime identity."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from holdspeak import runtime_identity
from holdspeak.db import core as db_core
from holdspeak.runtime.ownership import DatabaseOwnershipMixin
from holdspeak.runtime_lock import release_database


def test_startup_line_uses_the_captured_commit_build_and_database_path(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    """The boot line reports the same identity that the runtime captured."""
    database_path = tmp_path / "holdspeak.db"
    bundle = tmp_path / "_built"
    bundle.mkdir()
    (bundle / runtime_identity.BUILD_STAMP_NAME).write_text(
        json.dumps({"build_id": "frontend-build-201"}), encoding="utf-8"
    )
    monkeypatch.setattr(db_core, "DEFAULT_DB_PATH", database_path)
    monkeypatch.setattr(runtime_identity, "built_dir", lambda: bundle)
    monkeypatch.setenv("HOLDSPEAK_BACKEND_REVISION", "backend-commit-201")
    runtime_identity.reset_runtime_identity()

    class Runtime(DatabaseOwnershipMixin):
        runtime_started_at = datetime(2026, 9, 19, 12, 0, 0)

        def __init__(self) -> None:
            self.owns_database = None

    runtime = Runtime()
    try:
        runtime._capture_identity_and_claim()
        identity = runtime_identity.current_runtime_identity()
        output = capsys.readouterr().out
    finally:
        release_database()
        runtime_identity.reset_runtime_identity()

    assert output.splitlines() == [
        "HoldSpeak runtime identity: "
        f"backend_commit={identity.backend_revision} "
        f"frontend_build={identity.frontend_build} "
        f"database_path={identity.database_path}"
    ]
    assert "backend-commit-201" in output
    assert "frontend-build-201" in output
    assert str(database_path) in output
