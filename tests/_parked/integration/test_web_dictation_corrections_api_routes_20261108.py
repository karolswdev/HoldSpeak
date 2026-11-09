"""PARKED 20261108 (evening): tests of routes parked with the unreached-routes census.

From ``tests/integration/test_web_dictation_corrections_api.py`` (its fixtures
``persistent_db``, ``settings_path`` and ``_persistent_client`` stay there).
DELETE /api/dictation/corrections was parked by dd8ef618c
(``holdspeak/web/routes/_parked/dictation_pipeline_20261108.py``).
Not collected (tests/_parked). Restore with ``git revert``.
"""
from __future__ import annotations

from pathlib import Path

from holdspeak.db import Database


def test_clear_all_corrections(persistent_db: Database, settings_path: Path) -> None:
    persistent_db.dictation_corrections.record_correction(
        kind="intent", gist="one", value="code_exercise"
    )
    persistent_db.dictation_corrections.record_correction(
        kind="target", gist="two", value="codex_cli"
    )
    client = _persistent_client(persistent_db)
    resp = client.request("DELETE", "/api/dictation/corrections")
    assert resp.status_code == 200
    assert resp.json() == {"cleared": True, "size": 0}
    assert persistent_db.dictation_corrections.recent_corrections() == []
    assert client.get("/api/dictation/corrections").json()["size"] == 0
