# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_steward_effects.py to restore.

# ruff: noqa


# --- TestSTW008Bounds::test_cooldown_recorded_in_policy: P1: reads back a policy field it just wrote (cooldown_seconds == 60)
# (was a method of class TestSTW008Bounds)
def test_cooldown_recorded_in_policy(self, tmp_path: Path) -> None:
    """Cooldown is a policy field, enforced at the scheduling layer."""
    conn = _make_conn(tmp_path)
    policy_id = _make_policy(conn, cooldown=60)
    repos = _make_repos(conn)
    policy = repos[0].get_policy(policy_id)
    assert policy["cooldown_seconds"] == 60
