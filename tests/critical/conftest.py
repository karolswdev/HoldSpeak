"""HS-200-03 — the G0 critical journey harness.

Every journey here runs the REAL product: the real FastAPI application, the
real database and reconciled schema, the real repositories and routes. Only
what lives outside the machine is substituted — the inference engine, the
speech engine and the typing target — because a release check that needs a
developer's `~/Models` tree, a microphone or macOS proves nothing about a
cold installation.

Two invariants are enforced here rather than trusted:

* the journey cannot reach the owner's database or configuration, and
* no local model file is present while a journey runs,

so "cold" is a fact of the run and not a claim in a docstring.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

pytestmark = pytest.mark.critical


@pytest.fixture(autouse=True)
def cold_install(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """A fresh data root, a fresh config, and no model anywhere.

    `holdspeak.config.core.CONFIG_DIR` and `holdspeak.db.core.DEFAULT_DB_PATH`
    freeze at import time, so setting HOME alone is not enough for a process
    that has already imported the product — both constants are redirected too.
    """
    import holdspeak.config as config_module
    import holdspeak.db.core as db_core
    from holdspeak.db import reset_database
    from holdspeak import runtime_identity as ri
    from holdspeak import runtime_lock as rl

    home = tmp_path / "home"
    (home / ".config" / "holdspeak").mkdir(parents=True, exist_ok=True)
    (home / ".local" / "share" / "holdspeak").mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setattr(
        config_module, "CONFIG_FILE", home / ".config" / "holdspeak" / "config.json"
    )
    db_path = home / ".local" / "share" / "holdspeak" / "holdspeak.db"
    monkeypatch.setattr(db_core, "DEFAULT_DB_PATH", db_path)

    reset_database()
    ri.reset_runtime_identity()
    rl.release_database()
    yield Cold(home=home, db_path=db_path)
    reset_database()
    ri.reset_runtime_identity()
    rl.release_database()


class Cold:
    """The isolated installation one journey runs against."""

    def __init__(self, *, home: Path, db_path: Path) -> None:
        self.home = home
        self.db_path = db_path


@pytest.fixture(autouse=True)
def no_local_model(monkeypatch: pytest.MonkeyPatch):
    """Assert the cold condition instead of assuming it.

    A journey that quietly starts depending on a model file on the developer's
    disk would pass here and fail on every runner. The readiness predicate is
    forced to False for the whole journey, so any path that needs a local
    artifact refuses the way it refuses on a bare machine.
    """
    import holdspeak.inference_targets as inference_targets

    monkeypatch.setattr(
        inference_targets, "local_model_file_present", lambda _path: False
    )


@pytest.fixture
def db(cold_install):
    """The real database, reconciled at the cold installation's own path."""
    from holdspeak.db import Database

    return Database(cold_install.db_path)


@pytest.fixture
def client(db):
    """A TestClient over the REAL application, on the cold database."""
    from fastapi.testclient import TestClient

    import holdspeak.db as hsdb
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    # The app resolves its database through `get_database`; point that at the
    # cold one rather than letting each route open its own.
    original = hsdb.get_database
    hsdb.get_database = lambda *a, **k: db
    try:
        # The same durable wiring `holdspeak.web_runtime` performs at
        # web_runtime.py:588-593. A bare server leaves the journal and the
        # correction store as no-ops, which would let a "kept sentence"
        # journey pass without anything being kept.
        server = MeetingWebServer(
            WebRuntimeCallbacks(
                on_bookmark=MagicMock(),
                on_stop=MagicMock(),
                get_state=MagicMock(return_value={}),
            ),
            dictation_corrections_repository=db.dictation_corrections,
            dictation_journal_repository=db.dictation_journal,
        )
        with TestClient(server.app) as test_client:
            yield test_client
    finally:
        hsdb.get_database = original
