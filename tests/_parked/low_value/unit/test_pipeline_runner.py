# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_pipeline_runner.py to restore.

# ruff: noqa


# --- test_first_party_packs_expose_run_callables: P6: checks modules have a callable attribute; the run tests dispatch to them
def test_first_party_packs_expose_run_callables():
    """gh / jira / calendar packs all carry a `run(db)` entry
    point that pipelines can dispatch to. Firefox is event-
    driven and intentionally omits one."""
    from holdspeak.connector_packs import (
        calendar_activity,
        firefox_ext,
        github_cli,
        jira_cli,
    )

    assert callable(getattr(github_cli, "run", None))
    assert callable(getattr(jira_cli, "run", None))
    assert callable(getattr(calendar_activity, "run", None))
    assert getattr(firefox_ext, "run", None) is None
