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
    monkeypatch.setattr(main_module, "_run_tui_mode", lambda: (_ for _ in ()).throw(AssertionError("unexpected tui mode")))
    monkeypatch.setattr(main_module, "_run_meeting_mode", lambda _args: (_ for _ in ()).throw(AssertionError("unexpected meeting mode")))
    monkeypatch.setattr(main_module, "_emit_no_tui_deprecation", lambda: (_ for _ in ()).throw(AssertionError("unexpected deprecation")))
    monkeypatch.setattr(main_module, "run_history_command", lambda _args: (_ for _ in ()).throw(AssertionError("unexpected history")))
    monkeypatch.setattr(main_module, "run_actions_command", lambda _args: (_ for _ in ()).throw(AssertionError("unexpected actions")))
    monkeypatch.setattr(main_module, "run_intel_command", lambda _args: (_ for _ in ()).throw(AssertionError("unexpected intel")))
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


def test_main_tui_subcommand_routes_to_tui_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_logging(monkeypatch)
    tui_calls: list[bool] = []
    monkeypatch.setattr(main_module, "_run_tui_mode", lambda: tui_calls.append(True))
    monkeypatch.setattr(main_module, "_run_web_mode", lambda *, no_open=False: (_ for _ in ()).throw(AssertionError("unexpected web mode")))
    monkeypatch.setattr("sys.argv", ["holdspeak", "tui"])

    main_module.main()

    assert tui_calls == [True]


def test_no_tui_is_deprecated_and_aliases_to_web_headless(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _patch_logging(monkeypatch)
    web_calls: list[bool] = []
    monkeypatch.setattr(main_module, "_run_web_mode", lambda *, no_open=False: web_calls.append(bool(no_open)))
    warnings: list[str] = []
    monkeypatch.setattr(main_module.log, "warning", lambda message: warnings.append(str(message)))
    monkeypatch.setattr("sys.argv", ["holdspeak", "--no-tui"])

    main_module.main()

    captured = capsys.readouterr()
    assert web_calls == [True]
    assert "DEPRECATION" in captured.err
    assert "holdspeak web --no-open" in captured.err
    assert warnings and "deprecated" in warnings[0].lower()


def test_no_tui_flag_aliases_to_no_open_for_explicit_web(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_logging(monkeypatch)
    web_calls: list[bool] = []
    monkeypatch.setattr(main_module, "_run_web_mode", lambda *, no_open=False: web_calls.append(bool(no_open)))
    monkeypatch.setattr(main_module.log, "warning", lambda _message: None)
    monkeypatch.setattr("sys.argv", ["holdspeak", "--no-tui", "web"])

    main_module.main()

    assert web_calls == [True]


def test_doctor_subcommand_still_exits_with_command_return_code(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_logging(monkeypatch)
    monkeypatch.setattr(main_module, "run_doctor_command", lambda _args: 7)
    monkeypatch.setattr("sys.argv", ["holdspeak", "doctor"])

    with pytest.raises(SystemExit) as exc:
        main_module.main()

    assert exc.value.code == 7


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
