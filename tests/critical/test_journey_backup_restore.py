"""Critical journey: P200-A02 — the installation is recoverable.

Work that cannot be recovered is work that can be lost, and "silent loss of
accepted or kept work" is a critical defect by ACCEPTANCE.md's own list. So a
cold installation must be able to back itself up, come back from that backup,
and reopen the SAME records through the product.

HS-200-02's `tests/integration/test_phase200_runtime_identity.py` rehearses the
real 75 -> 76 upgrade across the boundary. This journey is the cold,
version-independent half: whatever the current schema is, a round trip returns
the same rows.
"""

from __future__ import annotations

import pytest

from holdspeak.db import Database, reset_database
from holdspeak.db.core import backup_database, read_schema_version, restore_database
from holdspeak.db.schema import SCHEMA_VERSION

pytestmark = pytest.mark.critical

KEPT = "The sentence the owner kept before the backup."
LOST = "The sentence written after the backup, which the restore must undo."


def test_backup_then_restore_reopens_the_same_kept_work(cold_install, db) -> None:
    db.notes.upsert(
        note_id="critical-kept",
        title="Kept before the backup",
        body_markdown=KEPT,
    )
    assert read_schema_version(cold_install.db_path) == SCHEMA_VERSION

    backup = backup_database(cold_install.db_path)
    assert backup.exists()

    # Work continues after the backup, and is then lost by the restore. Both
    # halves matter: a restore that changed nothing would pass a weaker test.
    db.notes.upsert(
        note_id="critical-after", title="Written after", body_markdown=LOST
    )
    assert db.notes.get("critical-after") is not None
    reset_database()

    safety = restore_database(backup, cold_install.db_path)
    assert safety is not None and safety.exists(), (
        "a restore must snapshot what it is about to overwrite"
    )

    # Reopen through the product, not by reading the file.
    reopened = Database(cold_install.db_path)
    kept = reopened.notes.get("critical-kept")
    assert kept is not None and kept.body_markdown == KEPT
    assert reopened.notes.get("critical-after") is None
    assert read_schema_version(cold_install.db_path) == SCHEMA_VERSION


def test_an_interrupted_restore_leaves_the_installation_openable(
    cold_install, db, tmp_path
) -> None:
    """A half-finished restore must not leave an installation that cannot open."""
    db.notes.upsert(
        note_id="critical-kept", title="Kept", body_markdown=KEPT
    )
    reset_database()

    truncated = tmp_path / "truncated-backup.db"
    truncated.write_bytes(b"this is not a database")

    with pytest.raises(Exception):
        restore_database(truncated, cold_install.db_path)

    reopened = Database(cold_install.db_path)
    kept = reopened.notes.get("critical-kept")
    assert kept is not None and kept.body_markdown == KEPT, (
        "a refused restore must leave the original installation intact"
    )
