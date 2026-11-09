# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_watch_service.py to restore.

# ruff: noqa


# --- TestGitHubTestPayload::test_supported_transitions_closed_set: P1: checks a constant list of transition names has seven entries
# (was a method of class TestGitHubTestPayload)
def test_supported_transitions_closed_set(self, tmp_path) -> None:
    db = Database(tmp_path / "gh-trans.db")
    _make_watch(db, "watch-gh-trans")
    svc = _watch_svc(db, fetcher=self._github_fetcher)
    result = svc.test_watch(OWNER, "watch-gh-trans")

    transitions = result["result"]["supported_transitions"]
    assert "github.pr.checks_changed" in transitions
    assert "github.pr.merged" in transitions
    assert "github.pr.review_decision_changed" in transitions
    assert len(transitions) >= 7
