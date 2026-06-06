"""HS-43-04: desktop presence is config-backed (no env var as the only path)."""
from __future__ import annotations

import json
import threading
from pathlib import Path
from types import SimpleNamespace

import pytest

import holdspeak.config as config_module
import holdspeak.web_runtime as web_runtime
from holdspeak.config import Config, PresenceConfig
from holdspeak.desktop_presence import build_desktop_presence_host, desktop_presence_enabled


@pytest.fixture
def isolated_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    target = tmp_path / "config.json"
    monkeypatch.setattr(config_module, "CONFIG_FILE", target)
    return target


# ── config field ──
def test_presence_defaults_off_and_round_trips(isolated_config) -> None:
    assert Config().presence.enabled is False
    cfg = Config()
    cfg.presence.enabled = True
    cfg.save(isolated_config)
    assert json.loads(isolated_config.read_text())["presence"]["enabled"] is True
    assert Config.load(isolated_config).presence.enabled is True


# ── gating: config OR env, neither => off ──
def test_enabled_by_config_or_env_override() -> None:
    assert desktop_presence_enabled({}, config_enabled=True) is True
    assert desktop_presence_enabled({"HOLDSPEAK_DESKTOP_PRESENCE": "1"}) is True
    assert desktop_presence_enabled({}, config_enabled=False) is False


def test_build_host_off_by_default_is_none() -> None:
    # flag off + no env override => no host (byte-identical default).
    assert build_desktop_presence_host({}, config_enabled=False) is None


# ── live start/stop on a settings change ──
def _runtime(monkeypatch, presence_enabled=False):
    import holdspeak.db as db_module

    cfg = Config()
    cfg.presence.enabled = presence_enabled
    monkeypatch.setattr(web_runtime.Config, "load", lambda: cfg)
    monkeypatch.setattr(web_runtime, "TextTyper", lambda: SimpleNamespace(type_text=lambda *a, **k: None))
    monkeypatch.setattr(db_module, "get_database", lambda *a, **k: SimpleNamespace(
        projects=SimpleNamespace(get_all_projects_for_detector=lambda: []),
    ))
    monkeypatch.setattr(web_runtime, "build_desktop_presence_host", lambda *a, **k: None)
    rt = web_runtime.WebRuntime(no_open=True, stop_event=threading.Event(), register_signal_handlers=False)
    return rt, cfg


def test_toggling_off_closes_a_running_host(monkeypatch) -> None:
    rt, cfg = _runtime(monkeypatch, presence_enabled=True)
    closed = {"v": False}
    rt.desktop_presence = SimpleNamespace(close=lambda: closed.update(v=True))
    cfg.presence.enabled = False
    rt._apply_updated_config(cfg)
    assert closed["v"] is True
    assert rt.desktop_presence is None


def test_toggling_on_builds_a_host(monkeypatch) -> None:
    rt, cfg = _runtime(monkeypatch, presence_enabled=False)
    assert rt.desktop_presence is None
    built = {"v": False}
    monkeypatch.setattr(
        web_runtime, "build_desktop_presence_host",
        lambda *a, **k: (built.update(v=True) or SimpleNamespace(close=lambda: None)),
    )
    cfg.presence.enabled = True
    rt._apply_updated_config(cfg)
    assert built["v"] is True
    assert rt.desktop_presence is not None
