"""HS-166-03: Jira Watch templates -- truth table, validation, scope threading.

Acceptance criteria tested:
- All five templates compile to valid WatchSpec@1 drafts
- Every compiled output passes watch_validation (definition of "compiles")
- Template table is closed (unknown ID refused)
- All comparisons used are members of the closed COMPARISONS set
- Provider is "jira", subject kind is "issue"
- Compiled spec carries connection_ref, projects, issue_types in scope
- LIVE FINDING: delivery_flow conditions on status_category changed_to done
  (team-managed sites carry resolution:null on Done issues)
"""
from __future__ import annotations

import pytest

from holdspeak.jira_templates import (
    JIRA_TEMPLATES,
    TEMPLATE_IDS,
    compile as compile_template,
)
from holdspeak.watch_validation import COMPARISONS, validate_rules


_SITE_SCOPE = {
    "connection_ref": "alpha.atlassian.net|user@example.com",
    "projects": ["KAN"],
    "issue_types": ["Task"],
}


# ── Template truth table ─────────────────────────────────────────────


class TestTemplateTruthTable:
    """All five templates compile to valid WatchSpec@1 drafts."""

    def test_five_templates_exist(self) -> None:
        assert len(JIRA_TEMPLATES) == 5
        assert TEMPLATE_IDS == {
            "watch.jira.blockers",
            "watch.jira.delivery_flow",
            "watch.jira.due_risk",
            "watch.jira.scope_intake",
            "watch.jira.transformation",
        }

    @pytest.mark.parametrize("tmpl", JIRA_TEMPLATES, ids=lambda t: t.template_id)
    def test_template_compiles_valid(self, tmpl) -> None:
        """Every template compiles to a WatchSpec@1 that passes validation."""
        spec = compile_template(tmpl.template_id, _SITE_SCOPE)
        assert spec["schema"] == "WatchSpec@1"
        assert spec["provider"]["id"] == "jira"
        assert spec["subject"]["kind"] == "issue"
        assert spec["subject"]["scope"]["connection_ref"] == _SITE_SCOPE["connection_ref"]
        assert spec["subject"]["scope"]["projects"] == ["KAN"]
        assert spec["subject"]["scope"]["issue_types"] == ["Task"]
        assert spec["trigger"]["kind"] == "poll"

        errors = validate_rules(spec["rules"])
        assert errors == [], f"Validation errors: {errors}"

    @pytest.mark.parametrize("tmpl", JIRA_TEMPLATES, ids=lambda t: t.template_id)
    def test_template_comparisons_in_closed_set(self, tmpl) -> None:
        """Every comparison used by a template must be a COMPARISONS member."""
        for rule in tmpl.rules:
            condition = rule.get("condition", {})
            for clause in condition.get("clauses", []):
                comp = clause.get("comparison", "")
                assert comp in COMPARISONS, (
                    f"Template {tmpl.template_id} uses unknown comparison {comp!r}"
                )

    def test_unknown_template_refused(self) -> None:
        with pytest.raises(ValueError, match="Unknown template"):
            compile_template("watch.jira.does_not_exist", _SITE_SCOPE)


# ── LIVE FINDING: team-managed resolution:null ───────────────────────


class TestLiveFindingResolutionNull:
    """delivery_flow conditions on status_category, not resolution."""

    def test_delivery_flow_conditions_on_status_category(self) -> None:
        spec = compile_template("watch.jira.delivery_flow", _SITE_SCOPE)
        clauses = spec["rules"][0]["condition"]["clauses"]
        category_clauses = [
            c for c in clauses
            if c.get("field") == "status_category"
            and c.get("comparison") == "changed_to"
            and c.get("value") == "done"
        ]
        assert len(category_clauses) == 1, (
            "delivery_flow MUST condition on status_category changed_to done"
        )

    def test_delivery_flow_no_resolution_condition(self) -> None:
        spec = compile_template("watch.jira.delivery_flow", _SITE_SCOPE)
        clauses = spec["rules"][0]["condition"]["clauses"]
        resolution_clauses = [
            c for c in clauses if c.get("field") == "resolution"
        ]
        assert resolution_clauses == [], (
            "delivery_flow MUST NOT condition on resolution (team-managed: null)"
        )


# ── Scope threading ──────────────────────────────────────────────────


class TestScopeThreading:
    """Compiled spec threads connection_ref into provider and query."""

    def test_provider_carries_connection_ref(self) -> None:
        spec = compile_template("watch.jira.blockers", _SITE_SCOPE)
        assert spec["provider"]["connection_ref"] == _SITE_SCOPE["connection_ref"]

    def test_query_carries_connection_ref(self) -> None:
        spec = compile_template("watch.jira.blockers", _SITE_SCOPE)
        assert spec["subject"]["query"]["connection_ref"] == _SITE_SCOPE["connection_ref"]

    def test_query_carries_projects(self) -> None:
        spec = compile_template("watch.jira.blockers", _SITE_SCOPE)
        assert spec["subject"]["query"]["projects"] == ["KAN"]

    def test_empty_scope_compiles(self) -> None:
        spec = compile_template("watch.jira.blockers", {})
        assert spec["schema"] == "WatchSpec@1"
        assert spec["subject"]["scope"]["projects"] == []
        errors = validate_rules(spec["rules"])
        assert errors == []


# ── Cadence presets ──────────────────────────────────────────────────


class TestCadencePresets:
    """Custom cadence overrides work."""

    def test_default_cadence(self) -> None:
        spec = compile_template("watch.jira.blockers", _SITE_SCOPE)
        assert spec["trigger"]["every_minutes"] == 15  # active_work

    def test_custom_cadence_key(self) -> None:
        spec = compile_template(
            "watch.jira.blockers", _SITE_SCOPE, options={"cadence": "daily"},
        )
        assert spec["trigger"]["every_minutes"] == 1440

    def test_custom_cadence_dict(self) -> None:
        custom = {"kind": "poll", "every_minutes": 42}
        spec = compile_template(
            "watch.jira.blockers", _SITE_SCOPE, options={"cadence": custom},
        )
        assert spec["trigger"]["every_minutes"] == 42
