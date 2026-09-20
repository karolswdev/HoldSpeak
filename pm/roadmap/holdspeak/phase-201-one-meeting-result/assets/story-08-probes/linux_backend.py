"""Temporary probe: make backend resolution behave like Linux CI."""

import holdspeak.transcribe as transcribe


def pytest_configure(config):
    transcribe._is_darwin_arm64 = lambda: False
    transcribe._module_available = lambda _module: False
