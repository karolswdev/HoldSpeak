# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_pi_harness.py to restore.

# ruff: noqa


# --- test_pi_is_a_gate_agent_and_its_sessions_are_pi_keys: P1: re-types the GATE_AGENTS tuple and an id format
def test_pi_is_a_gate_agent_and_its_sessions_are_pi_keys() -> None:
    assert coder_gate.GATE_AGENTS == ("claude", "codex", "pi")
    assert coder_gate.agent_identity("01a11d46", "pi") == "pi:01a11d46"
    assert "pi" in KNOWN_EXECUTABLES
    assert [agent_of_profile(p) for p in ("pi-default", "codex-default", "claude-default", None)] == [
        "pi", "codex", "claude", "claude",
    ]
