# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_calendar_ingest.py to restore.

# ruff: noqa


# --- TestSettingOnHubRead::test_hub_read_exposes_auto_record: P1: builds a MeetingConfig and reads back the fields it set / the defaults; nothing serializes
# (was a method of class TestSettingOnHubRead)
def test_hub_read_exposes_auto_record(self, db_recordings: Database) -> None:
    """The MeetingConfig carries auto_record; verify it serializes."""
    cfg = MeetingConfig(auto_record="all_calendar", auto_record_lead_minutes=10)
    assert cfg.auto_record == "all_calendar"
    assert cfg.auto_record_lead_minutes == 10


# --- TestSettingOnHubRead::test_default_is_off: P1: builds a MeetingConfig and reads back the fields it set / the defaults; nothing serializes
# (was a method of class TestSettingOnHubRead)
def test_default_is_off(self) -> None:
    cfg = MeetingConfig()
    assert cfg.auto_record == "off"
    assert cfg.auto_record_lead_minutes == 5


# --- TestNoDoubleRefresh: P8: phase-era (HS-175-02) check that a private _thread stays None
class TestNoDoubleRefresh:
    def test_conductor_start_does_not_spawn_thread(self, db_wire: Database, ics_file: Path) -> None:
        """After HS-175-02, start_calendar_ingest_conductor does NOT spawn
        the standalone thread."""
        from holdspeak.calendar_ingest_conductor import CalendarIngestConductor

        conductor = _make_conductor(db_wire, str(ics_file))
        # The conductor's thread should be None (never started).
        assert conductor._thread is None
        # Calling refresh() directly works.
        result = conductor.refresh()
        assert result is True
        # Thread still None.
        assert conductor._thread is None


# --- test_the_descriptor_is_owner_only_http_only_and_admitted: P1/P5: reads descriptor constants; test_an_agent_never_opens_it proves the refusal
def test_the_descriptor_is_owner_only_http_only_and_admitted() -> None:
    from holdspeak.kernel.project import ONBOARDING_ADMITTED
    from holdspeak.onboarding_operations import CALENDAR_OPEN_SETTINGS as op

    assert op.owner_only and op.owner_press and op.admission.rule == "admitted"
    assert op.exposure == ("http:POST /api/onboarding/calendar/macos/settings",)
    assert "calendar.open_settings" in ONBOARDING_ADMITTED


# --- test_reader_is_on_by_default: P1/P2: an env default and the test rigs' own isolation env; tests may touch this machine (owner 2026-11-09)
def test_reader_is_on_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("HOLDSPEAK_MACOS_CALENDAR", raising=False)
    assert macos_calendar.reader_enabled() is True
    monkeypatch.setenv("HOLDSPEAK_MACOS_CALENDAR", "1")
    assert macos_calendar.reader_enabled() is True




