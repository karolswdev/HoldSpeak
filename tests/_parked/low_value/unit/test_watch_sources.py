# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_watch_sources.py to restore.

# ruff: noqa


# --- TestCompileJql::test_deterministic_ordering: P1/P3: '_compile_jql(q) == _compile_jql(q)' and reads of two constant dicts
# (was a method of class TestCompileJql)
def test_deterministic_ordering(self) -> None:
    """Multiple calls produce the same string."""
    q = {"projects": ["B", "A"], "priorities": ["High"]}
    assert _compile_jql(q) == _compile_jql(q)


# --- TestProjectServiceMaps: P1/P3: '_compile_jql(q) == _compile_jql(q)' and reads of two constant dicts
class TestProjectServiceMaps:
    """The provider-to-connector and subject-to-query-kind maps are complete."""

    def test_provider_to_connector_jira(self) -> None:
        from holdspeak.services.project_service import _PROVIDER_TO_CONNECTOR
        assert _PROVIDER_TO_CONNECTOR["github"] == "gh"
        assert _PROVIDER_TO_CONNECTOR["jira"] == "jira"

    def test_subject_to_query_kind_issue(self) -> None:
        from holdspeak.services.project_service import _SUBJECT_TO_QUERY_KIND
        assert _SUBJECT_TO_QUERY_KIND["pull_request"] == "pull_requests"
        assert _SUBJECT_TO_QUERY_KIND["issue"] == "issues"
