"""HS-52-02: the voice command macro model + its config persistence.

Pins the schema the `/commands` board (HS-52-05) and the dispatcher (HS-52-04) build
on: a `VoiceMacro` is a keyword + a deterministic action (one of open_url /
launch_app / shell / type_text + a single payload), off by default, round-tripping
through `Config` save/load config-version-safe.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from holdspeak.config import (
    Config,
    MacrosConfig,
    VoiceMacro,
    VoiceMacroAction,
    VoiceMacroError,
)


def test_off_by_default_and_empty() -> None:
    macros = Config().dictation.macros
    assert macros.enabled is False
    assert macros.items == []


@pytest.mark.parametrize(
    "kind,payload,preview",
    [
        ("open_url", "https://example.com", "opens https://example.com"),
        ("launch_app", "Terminal", "launches Terminal"),
        ("shell", "git push origin HEAD", "runs: git push origin HEAD"),
        ("type_text", "## Standup", "types: ## Standup"),
    ],
)
def test_action_kinds_and_preview(kind: str, payload: str, preview: str) -> None:
    action = VoiceMacroAction(kind=kind, payload=payload)
    assert action.kind == kind
    assert action.preview() == preview


def test_action_kind_is_normalized() -> None:
    assert VoiceMacroAction(kind="  Shell  ", payload="ls").kind == "shell"


def test_action_rejects_unknown_kind() -> None:
    with pytest.raises(VoiceMacroError, match="unknown voice macro action kind"):
        VoiceMacroAction(kind="rm_rf_everything", payload="x")


def test_action_rejects_empty_payload() -> None:
    with pytest.raises(VoiceMacroError, match="non-empty payload"):
        VoiceMacroAction(kind="shell", payload="   ")


def test_macro_rejects_empty_keyword() -> None:
    with pytest.raises(VoiceMacroError, match="keyword must not be empty"):
        VoiceMacro(keyword="  ", action=VoiceMacroAction(kind="shell", payload="ls"))


def test_macro_coerces_action_dict() -> None:
    macro = VoiceMacro(keyword="ship it", action={"kind": "shell", "payload": "git push"})
    assert isinstance(macro.action, VoiceMacroAction)
    assert macro.action.kind == "shell"


def test_macro_match_is_normalized_whole_utterance() -> None:
    macro = VoiceMacro(keyword="Terminal", action={"kind": "launch_app", "payload": "Terminal"})
    assert macro.matches("terminal")
    assert macro.matches("  Terminal.  ")  # case + trailing punctuation
    assert not macro.matches("open the terminal please")  # not whole-utterance


def test_macros_config_coerces_item_dicts() -> None:
    cfg = MacrosConfig(
        enabled=True,
        items=[{"keyword": "docs", "action": {"kind": "open_url", "payload": "https://docs"}}],
    )
    assert cfg.enabled is True
    assert len(cfg.items) == 1
    assert isinstance(cfg.items[0], VoiceMacro)
    assert cfg.items[0].action.kind == "open_url"


def test_macros_config_rejects_bad_item() -> None:
    with pytest.raises(VoiceMacroError):
        MacrosConfig(items=[{"keyword": "x", "action": {"kind": "nope", "payload": "y"}}])


def test_config_save_load_round_trip(tmp_path: Path) -> None:
    path = tmp_path / "config.json"
    cfg = Config()
    cfg.dictation.macros = MacrosConfig(
        enabled=True,
        items=[
            VoiceMacro(keyword="terminal", action=VoiceMacroAction("launch_app", "Terminal")),
            VoiceMacro(keyword="ship it", action=VoiceMacroAction("shell", "git push origin HEAD")),
        ],
    )
    cfg.save(path)

    reloaded = Config.load(path)
    macros = reloaded.dictation.macros
    assert macros.enabled is True
    assert [m.keyword for m in macros.items] == ["terminal", "ship it"]
    assert macros.items[1].action.kind == "shell"
    assert macros.items[1].action.payload == "git push origin HEAD"
    # The rest of the config is untouched.
    assert reloaded.dictation.pipeline.enabled is False


def test_load_is_config_version_safe_with_macros(tmp_path: Path) -> None:
    """An older/unversioned config with a macros section loads without dropping
    other fields (Phase 50 forward coercion)."""
    path = tmp_path / "config.json"
    path.write_text(
        json.dumps(
            {
                # no config_version (pre-versioning), a custom model, and macros
                "model": {"name": "small"},
                "dictation": {
                    "macros": {
                        "enabled": True,
                        "items": [
                            {"keyword": "docs", "action": {"kind": "open_url", "payload": "https://x"}}
                        ],
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    cfg = Config.load(path)
    assert cfg.model.name == "small"  # other section preserved
    assert cfg.dictation.macros.enabled is True
    assert cfg.dictation.macros.items[0].keyword == "docs"
