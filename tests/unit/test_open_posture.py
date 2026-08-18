"""HS-139-08 — Open throttle: fresh-install defaults are permissive.

The owner ruling (ledger-not-gate) requires:
  - POSTURE (control_mode) defaults to YOLO
  - allow_actuators defaults True with a permissive allowlist
  - webhook_allowed_hosts defaults permissive
  - People MCP capability defaults ON (write)

The hard boundary is untouched:
  - Encryption at rest + key custody
  - People policy hard-refusal matrix
  - Egress badges / disclosure surfaces
  - Receipt / refusal ledger
"""
import os
from pathlib import Path

import pytest


def test_fresh_config_defaults_yolo():
    """A Config() with no on-disk file defaults to YOLO."""
    from holdspeak.config.core import Config

    config = Config()
    assert config.control_mode == "yolo"


def test_fresh_config_actuators_permissive():
    """A fresh Config() has actuators on with a wildcard allowlist."""
    from holdspeak.config.core import Config

    config = Config()
    assert config.meeting.allow_actuators is True
    assert config.meeting.allowed_actuators == ["*"]


def test_fresh_config_webhook_hosts_permissive():
    """A fresh Config() has a wildcard webhook host allowlist."""
    from holdspeak.config.core import Config

    config = Config()
    assert config.meeting.webhook_allowed_hosts == ["*"]


def test_fresh_config_load_from_empty_dir(tmp_path):
    """Config.load() on a non-existent path produces the open posture."""
    from holdspeak.config.core import Config

    config = Config.load(tmp_path / "nonexistent" / "config.json")
    assert config.control_mode == "yolo"
    assert config.meeting.allow_actuators is True
    assert config.meeting.allowed_actuators == ["*"]
    assert config.meeting.webhook_allowed_hosts == ["*"]


def test_people_mcp_defaults_write():
    """With no env var, the People MCP capability defaults to write."""
    from holdspeak.mcp.families.people import access_mode

    # Simulate no env var set by passing an empty environ dict.
    mode = access_mode(environ={})
    assert mode == "write"


def test_people_mcp_explicit_off():
    """An explicit HOLDSPEAK_MCP_PEOPLE_ACCESS=off disables it."""
    from holdspeak.mcp.families.people import access_mode

    mode = access_mode(environ={"HOLDSPEAK_MCP_PEOPLE_ACCESS": "off"})
    assert mode == "off"


def test_normalize_control_mode_defaults_yolo():
    """The policy's normalize_control_mode defaults to yolo."""
    from holdspeak.operation_policy import normalize_control_mode

    assert normalize_control_mode(None) == "yolo"
    assert normalize_control_mode("") == "yolo"
    assert normalize_control_mode("bogus") == "yolo"
    # Explicit safe/neutral still honored.
    assert normalize_control_mode("safe") == "safe"
    assert normalize_control_mode("neutral") == "neutral"
    assert normalize_control_mode("yolo") == "yolo"
