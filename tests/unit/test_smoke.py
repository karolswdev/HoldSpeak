"""Smoke test to verify pytest setup works."""

import pytest


def test_pytest_works():
    """Verify pytest is configured correctly."""
    assert True


def test_fixtures_available(fixtures_dir):
    """Verify fixtures directory fixture works."""
    assert fixtures_dir.exists()


def test_audio_fixture(silence_1s):
    """Verify audio fixtures work."""
    assert len(silence_1s) == 16000
    assert silence_1s.dtype.name == "float32"


def test_config_fixture(default_config):
    """Verify config fixture works."""
    assert default_config.hotkey.key == "alt_r"
