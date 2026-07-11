"""CAD-1-06 — the trust-boundary guards.

Phase 1's hard invariants, mechanically enforced before any surface builds on the
substrate: the cadence package performs NO external side effect, and it is off by
default (the runtime starts no cadence thread when disabled).
"""
from __future__ import annotations

import re
from pathlib import Path

from holdspeak.config import CadenceConfig, Config


CADENCE_DIR = Path(__file__).resolve().parents[2] / "holdspeak" / "cadence"

# Forbidden in Phase 1: any outbound side effect or actuator EXECUTION. (Reading
# proposals is fine; PROPOSING/executing is Phase 6+.) The collector reaches the
# actuator repo only through db.actuators.list_proposals — never record_proposal,
# transition_proposal, or a connector/network call.
_FORBIDDEN = [
    r"record_proposal",
    r"transition_proposal",
    r"execute_proposal",
    r"requests\.",
    r"urllib",
    r"httpx",
    r"socket\.",
    r"subprocess",
    r"os\.system",
    r"tmux",
]


def test_cadence_package_has_no_external_side_effects():
    offenders = []
    for path in CADENCE_DIR.rglob("*.py"):
        text = path.read_text()
        for pat in _FORBIDDEN:
            if re.search(pat, text):
                offenders.append(f"{path.name}: {pat}")
    assert not offenders, (
        "The cadence package must perform no external side effect in Phase 1 "
        f"(outbound actions go through the actuator path in later phases): {offenders}"
    )


def test_cadence_is_off_by_default():
    assert Config().cadence.enabled is False


def test_cadence_config_clamps_invalid_values():
    c = CadenceConfig(pressure="wild", tick_interval_seconds=1, quiet_hours_start=99)
    assert c.pressure == "normal"          # invalid pressure falls back
    assert c.tick_interval_seconds >= 30   # floored
    assert 0 <= c.quiet_hours_start <= 23  # wrapped


def test_runtime_gate_reflects_config():
    # The WebRuntime start guard reads config.cadence.enabled via _cadence_enabled().
    from holdspeak.runtime.cadence import CadenceMixin

    class _Stub(CadenceMixin):
        def __init__(self, enabled):
            self.config = Config()
            self.config.cadence.enabled = enabled

    assert _Stub(False)._cadence_enabled() is False
    assert _Stub(True)._cadence_enabled() is True
    strict = _Stub(True)
    strict.config.control_mode = "safe"
    assert strict._cadence_enabled() is False
