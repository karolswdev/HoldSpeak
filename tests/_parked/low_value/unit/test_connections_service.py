# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_connections_service.py to restore.

# ruff: noqa


# --- TestRecheck::test_jira_recheck_all_connections: P7: counts calls on a MagicMock adapter; the recheck result is never read
# (was a method of class TestRecheck)
def test_jira_recheck_all_connections(self) -> None:
    ja = _jira_adapter([
        {
            "state": "connected",
            "external_connection_ref": "s1.atlassian.net|u1@x.com",
        },
        {
            "state": "disconnected",
            "external_connection_ref": "s2.atlassian.net|u2@x.com",
        },
    ])
    svc = ConnectionsService(jira_adapter=ja)
    result = svc.recheck(OWNER, "jira")
    # connection_status was called for each connection
    assert ja.connection_status.call_count >= 2


# --- TestRecheck::test_jira_recheck_specific_ref: P7: counts calls on a MagicMock adapter; the recheck result is never read
# (was a method of class TestRecheck)
def test_jira_recheck_specific_ref(self) -> None:
    ja = _jira_adapter([
        {
            "state": "connected",
            "external_connection_ref": "s.atlassian.net|u@x.com",
        },
    ])
    svc = ConnectionsService(jira_adapter=ja)
    result = svc.recheck(OWNER, "jira", ref="s.atlassian.net|u@x.com")
    # connection_status called once for the specific ref
    ja.connection_status.assert_called_once_with(OWNER, "s.atlassian.net|u@x.com")


# --- TestShape::test_every_entry_has_required_fields: P6: checks each row has keys, not the values the face shows
# (was a method of class TestShape)
def test_every_entry_has_required_fields(self) -> None:
    svc = ConnectionsService()
    result = svc.list_tools(OWNER)
    required = {"provider_id", "state", "account", "next_action",
                 "recovery_hint", "error_detail", "last_checked_at",
                 "egress_host"}
    for tool in result["tools"]:
        missing = required - set(tool.keys())
        assert not missing, f"{tool['provider_id']} missing {missing}"
