# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_rails_observer.py to restore.

# ruff: noqa


# --- test_observer_is_off_by_default: P1/P3/P8: a default is False, Config saves and loads, and a source grep for six function names
def test_observer_is_off_by_default() -> None:
    assert RailsObserverConfig().enabled is False
    assert Config().rails_observer.enabled is False


# --- test_observer_config_roundtrips: P1/P3/P8: a default is False, Config saves and loads, and a source grep for six function names
def test_observer_config_roundtrips(tmp_path) -> None:
    cfg_path = tmp_path / "config.json"
    c = Config()
    c.rails_observer.enabled = True
    c.rails_observer.profile_id = "p1"
    c.save(cfg_path)
    loaded = Config.load(cfg_path)
    assert loaded.rails_observer.enabled is True
    assert loaded.rails_observer.profile_id == "p1"


# --- test_observer_module_has_no_rails_write_path: P1/P3/P8: a default is False, Config saves and loads, and a source grep for six function names
def test_observer_module_has_no_rails_write_path() -> None:
    """The observer READS and journals; it must never carry a path that
    writes to the rails. The rails write seams are the story connector
    and the gate — neither may appear in this module."""
    src = (Path(__file__).resolve().parents[2] / "holdspeak" / "rails_observer.py").read_text()
    # Code-level write markers (not prose): the gated story connector, the
    # tmux steer transport, the proposal executor, and the dw commit gate.
    for forbidden in (
        "build_dw_story_connector",
        "decide_proposal",
        "record_proposal",  # the observer journals; it does not itself propose
        "send_text_to_pane",
        '"story", "status"',  # a dw story-status argv
        "coder_steering.deliver",
    ):
        assert forbidden not in src, (
            f"rails_observer.py names a write path ({forbidden!r}) — the "
            "observer is read-only; a suggested action is a proposal made "
            "elsewhere, never a write from here."
        )
