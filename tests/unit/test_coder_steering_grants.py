"""The arming grant (HS-87-02) — consent with a countdown.

The whole lifecycle runs against a fake runner and an injected
monotonic clock: grant, expire, revoke, mismatch. The rule under
test is the phase's reason to exist: a recycled or retargeted pane
must never receive text meant for its predecessor — refuse AND
revoke, each failure a distinct typed reason.
"""

from __future__ import annotations

import subprocess
from types import SimpleNamespace

import pytest

from holdspeak import coder_steering
from holdspeak.coder_steering import (
    ARM_DEFAULT_TTL_SECONDS,
    ARM_MAX_TTL_SECONDS,
    ARM_MIN_TTL_SECONDS,
    active_grants,
    arm,
    clamp_ttl,
    clear_grants,
    disarm,
    require_grant,
    resolve_pane_identity,
    sweep_expired,
)


@pytest.fixture(autouse=True)
def _fresh_store():
    clear_grants()
    yield
    clear_grants()


def _identity_runner(pane_id: str = "%5"):
    def run(argv, cwd=None):
        assert argv[:3] == ["tmux", "display-message", "-p"]
        return SimpleNamespace(stdout=f"{pane_id}\n", returncode=0, stderr="")

    return run


def _gone_runner():
    return lambda argv, cwd=None: SimpleNamespace(
        stdout="", returncode=1, stderr="can't find pane"
    )


class _Clock:
    def __init__(self, start: float = 1000.0) -> None:
        self.now = start

    def __call__(self) -> float:
        return self.now


# --- resolve_pane_identity -------------------------------------------------


def test_identity_resolves_the_unique_pane_id() -> None:
    result = resolve_pane_identity("hs:0.0", runner=_identity_runner("%42"))
    assert result == {"status": "ok", "pane_id": "%42"}


def test_identity_dead_target_is_pane_gone() -> None:
    assert resolve_pane_identity("hs:0.0", runner=_gone_runner())["status"] == "pane_gone"


def test_identity_without_tmux_is_tmux_absent(monkeypatch) -> None:
    monkeypatch.setattr(coder_steering.shutil, "which", lambda _n: None)
    assert resolve_pane_identity("hs:0.0") == {"status": "tmux_absent"}


def test_identity_silent_empty_expansion_is_pane_gone() -> None:
    # tmux 3.6 answers a dead target with rc 0 and an empty expansion
    # when the server is otherwise alive (found by the live rig) — an
    # unprovable pane must read as gone, or a recycled-session check
    # would refuse without revoking.
    run = lambda argv, cwd=None: SimpleNamespace(stdout="\n", returncode=0, stderr="")
    result = resolve_pane_identity("dead:0.0", runner=run)
    assert result["status"] == "pane_gone"


# --- arm -------------------------------------------------------------------


def test_arm_pins_the_pane_identity_not_the_target_string() -> None:
    clock = _Clock()
    result = arm("claude:a", "hs:0.0", runner=_identity_runner("%9"), clock=clock)
    assert result["status"] == "armed"
    assert result["pane_id"] == "%9"
    assert result["expires_in_seconds"] == ARM_DEFAULT_TTL_SECONDS
    grants = active_grants(clock=clock)
    assert grants["claude:a"]["pane_id"] == "%9"


def test_arm_refuses_a_pane_that_cannot_prove_itself() -> None:
    result = arm("claude:a", "hs:0.0", runner=_gone_runner())
    assert result["status"] == "pane_gone"
    assert active_grants() == {}


def test_ttl_clamps_to_the_upstream_bounds() -> None:
    assert clamp_ttl(5) == ARM_MIN_TTL_SECONDS
    assert clamp_ttl(999_999) == ARM_MAX_TTL_SECONDS
    assert clamp_ttl("nope") == ARM_DEFAULT_TTL_SECONDS
    assert clamp_ttl(300) == 300


# --- require_grant: the chokepoint check -----------------------------------


def test_require_grant_without_a_grant_is_unarmed() -> None:
    assert require_grant("claude:a", "hs:0.0", runner=_identity_runner()) == {
        "status": "unarmed"
    }


def test_require_grant_ok_when_the_pane_still_proves_itself() -> None:
    clock = _Clock()
    arm("claude:a", "hs:0.0", runner=_identity_runner("%9"), clock=clock)
    clock.now += 60
    result = require_grant(
        "claude:a", "hs:0.0", runner=_identity_runner("%9"), clock=clock
    )
    assert result["status"] == "ok"
    assert result["pane_id"] == "%9"
    assert result["expires_in_seconds"] == ARM_DEFAULT_TTL_SECONDS - 60


def test_require_grant_expired_is_refused_and_removed() -> None:
    clock = _Clock()
    arm("claude:a", "hs:0.0", runner=_identity_runner(), clock=clock)
    clock.now += ARM_DEFAULT_TTL_SECONDS + 1
    result = require_grant(
        "claude:a", "hs:0.0", runner=_identity_runner(), clock=clock
    )
    assert result == {"status": "expired", "revoked": True}
    assert active_grants(clock=clock) == {}


def test_require_grant_recycled_pane_is_refused_and_revoked() -> None:
    clock = _Clock()
    arm("claude:a", "hs:0.0", runner=_identity_runner("%9"), clock=clock)
    # The same target string now resolves to a DIFFERENT pane id.
    result = require_grant(
        "claude:a", "hs:0.0", runner=_identity_runner("%13"), clock=clock
    )
    assert result["status"] == "pane_mismatch"
    assert result["revoked"] is True
    assert "nothing was typed" in result["detail"]
    assert active_grants(clock=clock) == {}  # REVOKED, not just refused


def test_require_grant_dead_pane_is_refused_and_revoked() -> None:
    clock = _Clock()
    arm("claude:a", "hs:0.0", runner=_identity_runner("%9"), clock=clock)
    result = require_grant("claude:a", "hs:0.0", runner=_gone_runner(), clock=clock)
    assert result["status"] == "pane_gone"
    assert result["revoked"] is True
    assert active_grants(clock=clock) == {}


def test_require_grant_registry_lost_the_pane_revokes() -> None:
    clock = _Clock()
    arm("claude:a", "hs:0.0", runner=_identity_runner("%9"), clock=clock)
    result = require_grant("claude:a", None, runner=_identity_runner("%9"), clock=clock)
    assert result["status"] == "pane_gone"
    assert result["revoked"] is True


def test_require_grant_transient_error_refuses_but_keeps_the_grant() -> None:
    clock = _Clock()
    arm("claude:a", "hs:0.0", runner=_identity_runner("%9"), clock=clock)

    def timeout_runner(argv, cwd=None):
        raise subprocess.TimeoutExpired(cmd=argv, timeout=5)

    result = require_grant("claude:a", "hs:0.0", runner=timeout_runner, clock=clock)
    assert result["status"] == "error"
    assert "revoked" not in result
    assert "claude:a" in active_grants(clock=clock)  # nothing typed, nothing burned


# --- disarm / sweep / fail-closed ------------------------------------------


def test_disarm_is_one_act_and_idempotent() -> None:
    arm("claude:a", "hs:0.0", runner=_identity_runner())
    assert disarm("claude:a") is True
    assert disarm("claude:a") is False
    assert active_grants() == {}


def test_sweep_returns_the_expired_keys_for_their_frames() -> None:
    clock = _Clock()
    arm("claude:a", "hs:0.0", runner=_identity_runner(), clock=clock, ttl_seconds=60)
    arm("codex:b", "hs:0.1", runner=_identity_runner("%7"), clock=clock)
    clock.now += 61
    assert sweep_expired(clock=clock) == ["claude:a"]
    assert list(active_grants(clock=clock)) == ["codex:b"]


def test_a_fresh_store_holds_zero_grants_fail_closed() -> None:
    # A hub restart constructs this module fresh: nothing survives.
    assert active_grants() == {}


def test_wall_clock_jumps_cannot_extend_a_grant() -> None:
    # The store keys expiry off the injected monotonic clock alone —
    # moving it forward expires; nothing else is consulted.
    clock = _Clock()
    arm("claude:a", "hs:0.0", runner=_identity_runner(), clock=clock, ttl_seconds=60)
    clock.now += 59
    assert "claude:a" in active_grants(clock=clock)
    clock.now += 2
    assert active_grants(clock=clock) == {}
