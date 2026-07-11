from __future__ import annotations

from types import SimpleNamespace

import pytest

import holdspeak.main as main_module


def _patch_logging(monkeypatch: pytest.MonkeyPatch) -> list[bool]:
    verbose_calls: list[bool] = []
    monkeypatch.setattr(main_module, "setup_logging", lambda *, verbose: verbose_calls.append(bool(verbose)))
    return verbose_calls


def test_main_defaults_to_web_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    verbose_calls = _patch_logging(monkeypatch)
    web_calls: list[bool] = []
    monkeypatch.setattr(main_module, "_run_web_mode", lambda *, no_open=False: web_calls.append(bool(no_open)))
    monkeypatch.setattr(main_module, "_run_meeting_mode", lambda _args: (_ for _ in ()).throw(AssertionError("unexpected meeting mode")))
    monkeypatch.setattr(main_module, "run_history_command", lambda _args: (_ for _ in ()).throw(AssertionError("unexpected history")))
    monkeypatch.setattr(main_module, "run_actions_command", lambda _args: (_ for _ in ()).throw(AssertionError("unexpected actions")))
    monkeypatch.setattr(main_module, "run_intel_command", lambda _args: (_ for _ in ()).throw(AssertionError("unexpected intel")))
    monkeypatch.setattr(main_module, "run_agent_hook_command", lambda _args: (_ for _ in ()).throw(AssertionError("unexpected agent-hook")))
    monkeypatch.setattr(main_module, "run_doctor_command", lambda _args: (_ for _ in ()).throw(AssertionError("unexpected doctor")))
    monkeypatch.setattr("sys.argv", ["holdspeak"])

    main_module.main()

    assert web_calls == [False]
    assert verbose_calls == [False]


def test_main_web_subcommand_supports_no_open(monkeypatch: pytest.MonkeyPatch) -> None:
    verbose_calls = _patch_logging(monkeypatch)
    web_calls: list[bool] = []
    monkeypatch.setattr(main_module, "_run_web_mode", lambda *, no_open=False: web_calls.append(bool(no_open)))
    monkeypatch.setattr("sys.argv", ["holdspeak", "web", "--no-open"])

    main_module.main()

    assert web_calls == [True]
    assert verbose_calls == [False]


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


def test_doctor_subcommand_still_exits_with_command_return_code(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_logging(monkeypatch)
    monkeypatch.setattr(main_module, "run_doctor_command", lambda _args: 7)
    monkeypatch.setattr("sys.argv", ["holdspeak", "doctor"])

    with pytest.raises(SystemExit) as exc:
        main_module.main()

    assert exc.value.code == 7


def test_agent_hook_subcommand_exits_with_command_return_code(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_logging(monkeypatch)
    monkeypatch.setattr(main_module, "run_agent_hook_command", lambda _args: 9)
    monkeypatch.setattr("sys.argv", ["holdspeak", "agent-hook", "templates", "--agent", "claude"])

    with pytest.raises(SystemExit) as exc:
        main_module.main()

    assert exc.value.code == 9


def test_meeting_subcommand_is_unchanged(monkeypatch: pytest.MonkeyPatch) -> None:
    verbose_calls = _patch_logging(monkeypatch)
    calls: list[SimpleNamespace] = []
    monkeypatch.setattr(main_module, "_run_meeting_mode", lambda args: calls.append(args))
    monkeypatch.setattr("sys.argv", ["holdspeak", "meeting", "--setup", "--verbose"])

    main_module.main()

    assert len(calls) == 1
    assert calls[0].setup is True
    assert calls[0].list_devices is False
    assert verbose_calls == [True]


def test_control_mode_cli_sets_future_policy_and_reports_precedence(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    config = main_module.Config()
    saved: list[str] = []
    monkeypatch.setattr(
        main_module.Config, "load", classmethod(lambda cls: config)
    )
    monkeypatch.setattr(config, "save", lambda: saved.append(config.control_mode))
    monkeypatch.setattr(
        "holdspeak.db.get_database",
        lambda: SimpleNamespace(
            actuators=SimpleNamespace(revoke_active_grants=lambda **kwargs: 0)
        ),
    )
    _patch_logging(monkeypatch)
    monkeypatch.setattr("sys.argv", ["holdspeak", "control-mode", "secure"])

    with pytest.raises(SystemExit) as exc:
        main_module.main()

    assert exc.value.code == 0
    assert saved == ["safe"]
    output = capsys.readouterr().out
    assert "Control mode: Secure" in output
    assert "future operations only" in output
    assert "Hard invariants:" in output
