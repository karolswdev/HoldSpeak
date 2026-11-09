# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_main_modes.py to restore.

# ruff: noqa


# --- test_unknown_tui_subcommand_is_rejected: P8: guards that a subcommand retired in HS-32 stays retired
def test_unknown_tui_subcommand_is_rejected(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The retired `tui` subcommand no longer parses (HS-32-07)."""
    _patch_logging(monkeypatch)
    monkeypatch.setattr("sys.argv", ["holdspeak", "tui"])

    with pytest.raises(SystemExit) as exc:
        main_module.main()

    # argparse exits 2 on an unrecognized subcommand.
    assert exc.value.code == 2
