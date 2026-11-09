# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_jira_templates.py to restore.

# ruff: noqa


# --- TestTemplateTruthTable::test_five_templates_exist: P1: asserts the template constant has five entries with five literal ids
# (was a method of class TestTemplateTruthTable)
def test_five_templates_exist(self) -> None:
    assert len(JIRA_TEMPLATES) == 5
    assert TEMPLATE_IDS == {
        "watch.jira.blockers",
        "watch.jira.delivery_flow",
        "watch.jira.due_risk",
        "watch.jira.scope_intake",
        "watch.jira.transformation",
    }
