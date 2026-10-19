"""Betterment setup ST1: quiet hours have one store.

Settings ▸ Rhythm writes the heartbeat policy (``PUT /api/settings/heartbeat``);
the notices loop, the cadence tick, ``cadence.status`` and the Telegram brief
read it. The old ``cadence.quiet_hours_*`` config keys stay in the file and
are no longer read. Isolated database under tmp_path; never the owner's DB.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from holdspeak.config.integrations import CadenceConfig
from holdspeak.db import Database
from holdspeak.principals import Principal, PrincipalKind

OWNER = Principal(PrincipalKind.OWNER, "test-owner")


@pytest.fixture
def db(tmp_path: Path) -> Database:
    return Database(tmp_path / "quiet_hours.db")


def test_a_quiet_hours_change_in_the_heartbeat_is_what_every_reader_reads(db: Database) -> None:
    from holdspeak.cadence.service import CadenceService as CadenceTick
    from holdspeak.services.cadence_service import CadenceService
    from holdspeak.services.heartbeat_service import HeartbeatService, read_quiet_hours

    # The old config keys say 22-08; the heartbeat (what Settings writes) says 09-11.
    config = CadenceConfig(quiet_hours_start=22, quiet_hours_end=8)
    assert read_quiet_hours(db) == (22, 8)  # the defaults, before any write
    HeartbeatService(db).update_settings({"quiet_hours": {"start": 9, "end": 11}})

    assert read_quiet_hours(db) == (9, 11)
    assert HeartbeatService(db).get_settings()["quiet_hours"] == {"start": 9, "end": 11}
    # cadence.status (MCP and the Rhythm reads) and the cadence tick's scheduler.
    assert CadenceService(db, config).status(OWNER)["quiet_hours"] == {"start": 9, "end": 11}
    scheduler = CadenceTick(db, config)._scheduler_config()
    assert (scheduler.quiet_hours_start, scheduler.quiet_hours_end) == (9, 11)


def test_the_cadence_cli_prints_the_heartbeat_quiet_hours(db: Database) -> None:
    import io
    from types import SimpleNamespace

    from holdspeak.commands.cadence import _cmd_status
    from holdspeak.services.heartbeat_service import HeartbeatService

    HeartbeatService(db).update_settings({"quiet_hours": {"start": 21, "end": 7}})
    out = io.StringIO()
    _cmd_status(out, db, SimpleNamespace(cadence=CadenceConfig(quiet_hours_start=22, quiet_hours_end=8)))
    assert "quiet hours:    21:00–07:00" in out.getvalue()
