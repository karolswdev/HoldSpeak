"""HS-159-02: WatchService facade -- lifecycle, revisions, staling,
condition validation, baseline honesty.

Tests:
- Reads: list_watches (filters), get_watch (with rules).
- Lifecycle: update_watch (material vs non-material), pause/resume/retire.
- ACT-008: material edit -> revision+1 + test_state/baseline_state staled.
- ACT-002: test_watch (zero-match semantics, passed/failed).
- ACT-005: baseline_watch never emits events (ledger-silence proof).
- ACT-009: retire_watch stops future evaluation, retains history.
- WatchCondition@1 validation (closed operators/comparisons, code refusal).
- WatchAction@1 validation (closed kinds).
- set_rules validation and replace-by-ordinal.
"""
from __future__ import annotations

import json
from typing import Any

import pytest

from holdspeak.db.core import Database
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.errors import NotFound, ServiceError, ValidationError
from holdspeak.services.reaction_service import ReactionService
from holdspeak.services.watch_service import WatchService
from holdspeak.watch_validation import (
    ACTION_KINDS,
    COMPARISONS,
    LOGICAL_OPERATORS,
    validate_action,
    validate_condition,
    validate_rule,
    validate_rules,
)


OWNER = Principal(PrincipalKind.OWNER, "test-watch-owner")


# ── Helpers ──────────────────────────────────────────────────────────

def _make_watch(db: Database, watch_id: str = "watch-01", **kwargs: Any) -> dict[str, Any]:
    """Create a watch via ReactionService (the legacy creator)."""
    svc = ReactionService(db)
    return svc.create_watch(
        OWNER,
        connector_id=kwargs.get("connector_id", "gh"),
        query_kind=kwargs.get("query_kind", "pull_requests"),
        name=kwargs.get("name", "Test watch"),
        query=kwargs.get("query", {"repository": "acme/app"}),
        watch_id=watch_id,
    )


def _watch_svc(
    db: Database,
    fetcher: Any = None,
) -> WatchService:
    return WatchService(db, snapshot_fetcher=fetcher)


# ── Reads ────────────────────────────────────────────────────────────


class TestListWatches:
    def test_list_returns_all(self, tmp_path) -> None:
        db = Database(tmp_path / "list.db")
        _make_watch(db, "watch-a")
        _make_watch(db, "watch-b", connector_id="jira", query_kind="issues")
        svc = _watch_svc(db)
        watches = svc.list_watches(OWNER)
        ids = [w["id"] for w in watches]
        assert "watch-a" in ids
        assert "watch-b" in ids

    def test_list_filters_by_connector(self, tmp_path) -> None:
        db = Database(tmp_path / "filter-conn.db")
        _make_watch(db, "watch-gh", connector_id="gh")
        _make_watch(db, "watch-jira", connector_id="jira", query_kind="issues")
        svc = _watch_svc(db)
        result = svc.list_watches(OWNER, connector="gh")
        assert len(result) == 1
        assert result[0]["id"] == "watch-gh"

    def test_list_filters_by_state(self, tmp_path) -> None:
        db = Database(tmp_path / "filter-state.db")
        _make_watch(db, "watch-act")
        svc = _watch_svc(db)
        svc.pause_watch(OWNER, "watch-act")
        active = svc.list_watches(OWNER, state="active")
        paused = svc.list_watches(OWNER, state="paused")
        assert len(active) == 0
        assert len(paused) == 1

    def test_list_filters_by_project_id(self, tmp_path) -> None:
        db = Database(tmp_path / "filter-proj.db")
        _make_watch(db, "watch-proj")
        db.automations.update_watch_spec("watch-proj", project_id="proj-1")
        svc = _watch_svc(db)
        result = svc.list_watches(OWNER, project_id="proj-1")
        assert len(result) == 1
        result2 = svc.list_watches(OWNER, project_id="proj-other")
        assert len(result2) == 0


class TestGetWatch:
    def test_get_returns_watch_with_rules(self, tmp_path) -> None:
        db = Database(tmp_path / "get.db")
        _make_watch(db, "watch-get")
        svc = _watch_svc(db)
        # Add a rule manually.
        db.automations.create_rule(
            rule_id="rule-1", watch_id="watch-get", ordinal=0,
            condition_schema="WatchCondition@1",
            condition_json='{"operator":"any","clauses":[{"field":"checks","comparison":"changed_to","value":"failure"}]}',
            action_schema="WatchAction@1",
            action_json='[{"kind":"project.observe"}]',
        )
        watch = svc.get_watch(OWNER, "watch-get")
        assert watch["id"] == "watch-get"
        assert len(watch["rules"]) == 1
        assert watch["rules"][0]["id"] == "rule-1"

    def test_get_missing_watch_raises(self, tmp_path) -> None:
        db = Database(tmp_path / "get-miss.db")
        svc = _watch_svc(db)
        with pytest.raises(NotFound):
            svc.get_watch(OWNER, "no-such-watch")


# ── Lifecycle: update_watch ──────────────────────────────────────────


class TestUpdateWatch:
    def test_non_material_edit_does_not_stale(self, tmp_path) -> None:
        """ACT-008: name/intent are non-material; revision stays."""
        db = Database(tmp_path / "nonmat.db")
        _make_watch(db, "watch-nm")
        db.automations.update_watch_spec(
            "watch-nm", revision=1, test_state="passed", baseline_state="established",
        )
        svc = _watch_svc(db)
        result = svc.update_watch(OWNER, "watch-nm", name="Renamed", intent="New intent")
        assert result["name"] == "Renamed"
        assert result.get("intent") == "New intent"
        assert int(result.get("revision") or 0) == 1  # unchanged
        assert result.get("test_state") == "passed"  # not staled
        assert result.get("baseline_state") == "established"  # not staled

    def test_material_edit_stales_and_increments_revision(self, tmp_path) -> None:
        """ACT-008: query change -> revision+1, test/baseline stale."""
        db = Database(tmp_path / "mat.db")
        _make_watch(db, "watch-mat")
        db.automations.update_watch_spec(
            "watch-mat", revision=2, test_state="passed", baseline_state="established",
        )
        svc = _watch_svc(db)
        result = svc.update_watch(
            OWNER, "watch-mat",
            query={"repository": "acme/newrepo"},
        )
        assert int(result.get("revision") or 0) == 3  # was 2, now 3
        assert result.get("test_state") == "stale"
        assert result.get("baseline_state") == "stale"
        assert result["query"] == {"repository": "acme/newrepo"}

    def test_mixed_material_and_non_material(self, tmp_path) -> None:
        """Mixed update: material field triggers staling."""
        db = Database(tmp_path / "mixed.db")
        _make_watch(db, "watch-mix")
        db.automations.update_watch_spec(
            "watch-mix", revision=1, test_state="passed", baseline_state="established",
        )
        svc = _watch_svc(db)
        result = svc.update_watch(
            OWNER, "watch-mix",
            name="Updated name",
            trigger_kind="poll",
            trigger={"every_minutes": 15},
        )
        assert result["name"] == "Updated name"
        assert int(result.get("revision") or 0) == 2  # incremented
        assert result.get("test_state") == "stale"

    def test_update_missing_watch_raises(self, tmp_path) -> None:
        db = Database(tmp_path / "up-miss.db")
        svc = _watch_svc(db)
        with pytest.raises(NotFound):
            svc.update_watch(OWNER, "no-such", name="x")

    def test_update_requires_owner(self, tmp_path) -> None:
        db = Database(tmp_path / "up-auth.db")
        _make_watch(db, "watch-auth")
        svc = _watch_svc(db)
        agent = Principal(PrincipalKind.AGENT, "agent-1")
        with pytest.raises(ServiceError, match="OWNER"):
            svc.update_watch(agent, "watch-auth", name="x")


# ── Lifecycle: pause/resume/retire ───────────────────────────────────


class TestPauseResumeRetire:
    def test_pause_sets_state(self, tmp_path) -> None:
        db = Database(tmp_path / "pause.db")
        _make_watch(db, "watch-p")
        svc = _watch_svc(db)
        result = svc.pause_watch(OWNER, "watch-p")
        assert result.get("state") == "paused"

    def test_resume_sets_active(self, tmp_path) -> None:
        db = Database(tmp_path / "resume.db")
        _make_watch(db, "watch-r")
        svc = _watch_svc(db)
        svc.pause_watch(OWNER, "watch-r")
        result = svc.resume_watch(OWNER, "watch-r")
        assert result.get("state") == "active"

    def test_retire_sets_retired(self, tmp_path) -> None:
        """ACT-009: retire stops future evaluation."""
        db = Database(tmp_path / "retire.db")
        _make_watch(db, "watch-ret")
        svc = _watch_svc(db)
        result = svc.retire_watch(OWNER, "watch-ret")
        assert result.get("state") == "retired"

    def test_retire_retains_watch_row(self, tmp_path) -> None:
        """ACT-009: retired watches retain rows and history."""
        db = Database(tmp_path / "retire-retain.db")
        _make_watch(db, "watch-rr")
        svc = _watch_svc(db)
        svc.retire_watch(OWNER, "watch-rr")
        # The watch is still readable.
        watch = svc.get_watch(OWNER, "watch-rr")
        assert watch["id"] == "watch-rr"
        assert watch.get("state") == "retired"

    def test_lifecycle_missing_watch_raises(self, tmp_path) -> None:
        db = Database(tmp_path / "lc-miss.db")
        svc = _watch_svc(db)
        for method in [svc.pause_watch, svc.resume_watch, svc.retire_watch]:
            with pytest.raises(NotFound):
                method(OWNER, "no-such")


# ── Test watch (ACT-002) ────────────────────────────────────────────


class TestTestWatch:
    def test_successful_test_persists_passed(self, tmp_path) -> None:
        db = Database(tmp_path / "test-pass.db")
        _make_watch(db, "watch-tp")

        def fetcher(principal, **kwargs):
            return [{"number": 5, "state": "open", "title": "Five"}]

        svc = _watch_svc(db, fetcher=fetcher)
        result = svc.test_watch(OWNER, "watch-tp")
        assert result["test_state"] == "passed"
        assert result["result"]["entity_count"] == 1
        assert len(result["result"]["representative_entities"]) == 1
        assert result["result"]["error"] is None

        # Graduated columns persisted.
        watch = db.automations.get_watch("watch-tp")
        assert watch.get("test_state") == "passed"
        assert watch.get("last_test_at") is not None

    def test_zero_matches_is_passed(self, tmp_path) -> None:
        """ACT-002: zero-match test with successful read = PASSED."""
        db = Database(tmp_path / "test-zero.db")
        _make_watch(db, "watch-zero")

        def fetcher(principal, **kwargs):
            return []  # Zero entities

        svc = _watch_svc(db, fetcher=fetcher)
        result = svc.test_watch(OWNER, "watch-zero")
        assert result["test_state"] == "passed"
        assert result["result"]["entity_count"] == 0
        assert "0 current matches" in result["result"]["message"]

    def test_failed_test_persists_failed(self, tmp_path) -> None:
        db = Database(tmp_path / "test-fail.db")
        _make_watch(db, "watch-tf")

        def fetcher(principal, **kwargs):
            raise RuntimeError("network down")

        svc = _watch_svc(db, fetcher=fetcher)
        result = svc.test_watch(OWNER, "watch-tf")
        assert result["test_state"] == "failed"
        assert result["result"]["error"] is not None
        assert result["result"]["error"]["type"] == "RuntimeError"
        assert "network down" in result["result"]["error"]["message"]

        # Graduated columns persisted.
        watch = db.automations.get_watch("watch-tf")
        assert watch.get("test_state") == "failed"

    def test_does_not_advance_baseline(self, tmp_path) -> None:
        db = Database(tmp_path / "test-nobase.db")
        _make_watch(db, "watch-nb")

        def fetcher(principal, **kwargs):
            return [{"number": 1, "state": "open", "title": "PR"}]

        svc = _watch_svc(db, fetcher=fetcher)
        svc.test_watch(OWNER, "watch-nb")
        watch = db.automations.get_watch("watch-nb")
        assert watch["snapshot"] == {}  # Baseline NOT advanced

    def test_representative_entities_capped_at_five(self, tmp_path) -> None:
        db = Database(tmp_path / "test-cap.db")
        _make_watch(db, "watch-cap")

        def fetcher(principal, **kwargs):
            return [{"number": i, "state": "open", "title": f"PR {i}"} for i in range(1, 11)]

        svc = _watch_svc(db, fetcher=fetcher)
        result = svc.test_watch(OWNER, "watch-cap")
        assert result["result"]["entity_count"] == 10
        assert len(result["result"]["representative_entities"]) == 5

    def test_missing_watch_raises(self, tmp_path) -> None:
        db = Database(tmp_path / "test-miss.db")
        svc = _watch_svc(db)
        with pytest.raises(NotFound):
            svc.test_watch(OWNER, "no-such")


# ── Baseline watch (ACT-005) ────────────────────────────────────────


class TestBaselineWatch:
    def test_baseline_sets_snapshot_and_state(self, tmp_path) -> None:
        db = Database(tmp_path / "base.db")
        _make_watch(db, "watch-base")

        def fetcher(principal, **kwargs):
            return [{"number": 3, "state": "open", "title": "Three"}]

        svc = _watch_svc(db, fetcher=fetcher)
        result = svc.baseline_watch(OWNER, "watch-base")
        assert result["baseline_state"] == "established"
        assert result["entity_count"] == 1

        # Snapshot persisted.
        watch = db.automations.get_watch("watch-base")
        assert watch["snapshot"] != {}

        # Graduated column persisted.
        raw = watch.get("baseline_state")
        assert raw == "established"

    def test_baseline_never_emits_events(self, tmp_path) -> None:
        """ACT-005: the service-event ledger MUST stay silent."""
        db = Database(tmp_path / "base-silent.db")
        _make_watch(db, "watch-silent")

        def fetcher(principal, **kwargs):
            return [
                {"number": 1, "state": "open", "title": "One"},
                {"number": 2, "state": "open", "title": "Two"},
            ]

        svc = _watch_svc(db, fetcher=fetcher)

        # Count events BEFORE baseline.
        events_before = db.automations.list_events()
        count_before = len(events_before)

        svc.baseline_watch(OWNER, "watch-silent")

        # Count events AFTER baseline -- must be identical.
        events_after = db.automations.list_events()
        count_after = len(events_after)
        assert count_after == count_before, (
            f"ACT-005 violation: baseline emitted {count_after - count_before} events"
        )

    def test_baseline_records_error_on_failure(self, tmp_path) -> None:
        db = Database(tmp_path / "base-err.db")
        _make_watch(db, "watch-berr")

        def fetcher(principal, **kwargs):
            raise RuntimeError("provider offline")

        svc = _watch_svc(db, fetcher=fetcher)
        with pytest.raises(RuntimeError, match="provider offline"):
            svc.baseline_watch(OWNER, "watch-berr")

        watch = db.automations.get_watch("watch-berr")
        assert watch["last_error"] == "provider offline"

    def test_missing_watch_raises(self, tmp_path) -> None:
        db = Database(tmp_path / "base-miss.db")
        svc = _watch_svc(db)
        with pytest.raises(NotFound):
            svc.baseline_watch(OWNER, "no-such")


# ── Rules (set_rules) ───────────────────────────────────────────────


class TestSetRules:
    def test_set_rules_creates_rules(self, tmp_path) -> None:
        db = Database(tmp_path / "rules.db")
        _make_watch(db, "watch-rules")
        svc = _watch_svc(db)
        result = svc.set_rules(OWNER, "watch-rules", [
            {
                "condition": {
                    "schema": "WatchCondition@1",
                    "operator": "any",
                    "clauses": [
                        {"field": "checks", "comparison": "changed_to", "value": "failure"},
                    ],
                },
                "actions": [
                    {"schema": "WatchAction@1", "kind": "project.observe"},
                ],
            },
        ])
        assert len(result["rules"]) == 1
        assert result["rules"][0]["ordinal"] == 0

    def test_set_rules_replaces_existing(self, tmp_path) -> None:
        db = Database(tmp_path / "replace.db")
        _make_watch(db, "watch-repl")
        svc = _watch_svc(db)

        # First set.
        svc.set_rules(OWNER, "watch-repl", [
            {
                "condition": {"operator": "any", "clauses": [
                    {"field": "state", "comparison": "equals", "value": "open"},
                ]},
                "actions": [{"kind": "project.observe"}],
            },
        ])
        assert len(db.automations.list_rules("watch-repl")) == 1

        # Replace with two rules.
        svc.set_rules(OWNER, "watch-repl", [
            {
                "condition": {"operator": "any", "clauses": [
                    {"field": "state", "comparison": "equals", "value": "open"},
                ]},
                "actions": [{"kind": "project.observe"}],
            },
            {
                "condition": {"operator": "all", "clauses": [
                    {"field": "checks", "comparison": "changed_to", "value": "failure"},
                ]},
                "actions": [{"kind": "project.steward.run_once"}],
            },
        ])
        rules = db.automations.list_rules("watch-repl")
        assert len(rules) == 2
        assert rules[0]["ordinal"] == 0
        assert rules[1]["ordinal"] == 1

    def test_set_rules_increments_revision_and_stales(self, tmp_path) -> None:
        """Rules are material -- ACT-008 applies."""
        db = Database(tmp_path / "rules-rev.db")
        _make_watch(db, "watch-rrev")
        db.automations.update_watch_spec(
            "watch-rrev", revision=3, test_state="passed", baseline_state="established",
        )
        svc = _watch_svc(db)
        result = svc.set_rules(OWNER, "watch-rrev", [
            {
                "condition": {"operator": "any", "clauses": [
                    {"field": "state", "comparison": "equals", "value": "open"},
                ]},
                "actions": [{"kind": "project.observe"}],
            },
        ])
        assert result["revision"] == 4
        watch = db.automations.get_watch("watch-rrev")
        assert watch.get("test_state") == "stale"
        assert watch.get("baseline_state") == "stale"

    def test_set_rules_invalid_condition_refuses(self, tmp_path) -> None:
        db = Database(tmp_path / "rules-bad.db")
        _make_watch(db, "watch-bad")
        svc = _watch_svc(db)
        with pytest.raises(ValidationError, match="Invalid watch rules"):
            svc.set_rules(OWNER, "watch-bad", [
                {
                    "condition": {"operator": "UNKNOWN", "clauses": []},
                    "actions": [{"kind": "project.observe"}],
                },
            ])

    def test_set_rules_invalid_action_refuses(self, tmp_path) -> None:
        db = Database(tmp_path / "rules-bad-act.db")
        _make_watch(db, "watch-ba")
        svc = _watch_svc(db)
        with pytest.raises(ValidationError, match="Invalid watch rules"):
            svc.set_rules(OWNER, "watch-ba", [
                {
                    "condition": {"operator": "any", "clauses": [
                        {"field": "state", "comparison": "equals", "value": "open"},
                    ]},
                    "actions": [{"kind": "totally.made.up"}],
                },
            ])

    def test_set_rules_empty_list_clears(self, tmp_path) -> None:
        db = Database(tmp_path / "rules-clear.db")
        _make_watch(db, "watch-clr")
        svc = _watch_svc(db)
        svc.set_rules(OWNER, "watch-clr", [
            {
                "condition": {"operator": "any", "clauses": [
                    {"field": "state", "comparison": "equals", "value": "open"},
                ]},
                "actions": [{"kind": "project.observe"}],
            },
        ])
        # Clear rules.
        svc.set_rules(OWNER, "watch-clr", [])
        assert db.automations.list_rules("watch-clr") == []


# ── WatchCondition@1 validation ─────────────────────────────────────


class TestConditionValidation:
    def test_valid_logical_node(self) -> None:
        cond = {
            "schema": "WatchCondition@1",
            "operator": "any",
            "clauses": [
                {"field": "checks", "comparison": "changed_to", "value": "failure"},
            ],
        }
        assert validate_condition(cond) == []

    def test_valid_nested_tree(self) -> None:
        cond = {
            "schema": "WatchCondition@1",
            "operator": "all",
            "clauses": [
                {
                    "operator": "any",
                    "clauses": [
                        {"field": "state", "comparison": "equals", "value": "open"},
                        {"field": "state", "comparison": "equals", "value": "draft"},
                    ],
                },
                {"field": "checks", "comparison": "changed_to", "value": "failure"},
            ],
        }
        assert validate_condition(cond) == []

    def test_valid_not_operator(self) -> None:
        cond = {
            "operator": "not",
            "clauses": [
                {"field": "is_draft", "comparison": "equals", "value": True},
            ],
        }
        assert validate_condition(cond) == []

    def test_not_requires_single_clause(self) -> None:
        cond = {
            "operator": "not",
            "clauses": [
                {"field": "a", "comparison": "equals", "value": 1},
                {"field": "b", "comparison": "equals", "value": 2},
            ],
        }
        errors = validate_condition(cond)
        assert any("exactly one" in str(e) for e in errors)

    def test_unknown_operator_refused(self) -> None:
        cond = {"operator": "xor", "clauses": []}
        errors = validate_condition(cond)
        assert any("unknown operator" in str(e) for e in errors)

    def test_unknown_comparison_refused(self) -> None:
        cond = {"field": "state", "comparison": "fuzzy_match", "value": "x"}
        errors = validate_condition(cond)
        assert any("unknown comparison" in str(e) for e in errors)

    def test_unknown_keys_refused(self) -> None:
        cond = {
            "operator": "any",
            "clauses": [{"field": "x", "comparison": "equals", "value": 1}],
            "script": "import os; os.system('rm -rf /')",
        }
        errors = validate_condition(cond)
        assert any("unknown keys" in str(e) for e in errors)

    def test_code_string_in_unknown_key_is_refused(self) -> None:
        """Code refusal: the closed schema rejects unknown keys."""
        cond = {
            "field": "state",
            "comparison": "equals",
            "value": "open",
            "python": "exec('hack')",
        }
        errors = validate_condition(cond)
        assert len(errors) > 0
        assert any("unknown keys" in str(e) for e in errors)

    def test_exists_comparison_no_value_required(self) -> None:
        cond = {"field": "assignee", "comparison": "exists"}
        assert validate_condition(cond) == []

    def test_missing_comparison_no_value_required(self) -> None:
        cond = {"field": "assignee", "comparison": "missing"}
        assert validate_condition(cond) == []

    def test_changed_comparison_no_value_required(self) -> None:
        cond = {"field": "status", "comparison": "changed"}
        assert validate_condition(cond) == []

    def test_equals_requires_value(self) -> None:
        cond = {"field": "state", "comparison": "equals"}
        errors = validate_condition(cond)
        assert any("requires a 'value'" in str(e) for e in errors)

    def test_empty_field_refused(self) -> None:
        cond = {"field": "", "comparison": "equals", "value": "x"}
        errors = validate_condition(cond)
        assert any("non-empty string" in str(e) for e in errors)

    def test_not_a_dict_refused(self) -> None:
        errors = validate_condition("not a condition")
        assert any("must be an object" in str(e) for e in errors)

    def test_no_operator_or_comparison_refused(self) -> None:
        errors = validate_condition({"field": "x"})
        assert any("must have either" in str(e) for e in errors)

    def test_wrong_schema_refused(self) -> None:
        cond = {"schema": "WatchCondition@99", "operator": "any", "clauses": [
            {"field": "x", "comparison": "equals", "value": 1},
        ]}
        errors = validate_condition(cond)
        assert any("WatchCondition@1" in str(e) for e in errors)

    def test_depth_limit(self) -> None:
        """Deeply nested trees are refused."""
        node: dict = {"field": "x", "comparison": "equals", "value": 1}
        for _ in range(25):
            node = {"operator": "all", "clauses": [node]}
        errors = validate_condition(node)
        assert any("maximum depth" in str(e) for e in errors)

    @pytest.mark.parametrize("comparison", sorted(COMPARISONS))
    def test_all_closed_comparisons_accepted(self, comparison) -> None:
        no_value = {"exists", "missing", "changed", "overdue"}
        cond = {"field": "x", "comparison": comparison}
        if comparison not in no_value:
            cond["value"] = "test"
        errors = validate_condition(cond)
        assert errors == [], f"{comparison} should be accepted: {errors}"

    @pytest.mark.parametrize("operator", sorted(LOGICAL_OPERATORS))
    def test_all_closed_operators_accepted(self, operator) -> None:
        clauses = [{"field": "x", "comparison": "equals", "value": 1}]
        cond = {"operator": operator, "clauses": clauses}
        errors = validate_condition(cond)
        assert errors == [], f"{operator} should be accepted: {errors}"


# ── WatchAction@1 validation ────────────────────────────────────────


class TestActionValidation:
    @pytest.mark.parametrize("kind", sorted(ACTION_KINDS))
    def test_all_closed_kinds_accepted(self, kind) -> None:
        errors = validate_action({"schema": "WatchAction@1", "kind": kind})
        assert errors == [], f"{kind} should be accepted: {errors}"

    def test_unknown_kind_refused(self) -> None:
        errors = validate_action({"kind": "nuclear.launch"})
        assert any("unknown action kind" in str(e) for e in errors)

    def test_empty_kind_refused(self) -> None:
        errors = validate_action({"kind": ""})
        assert any("non-empty string" in str(e) for e in errors)

    def test_unknown_keys_refused(self) -> None:
        errors = validate_action({"kind": "project.observe", "sql": "DROP TABLE"})
        assert any("unknown keys" in str(e) for e in errors)

    def test_not_a_dict_refused(self) -> None:
        errors = validate_action(42)
        assert any("must be an object" in str(e) for e in errors)

    def test_wrong_schema_refused(self) -> None:
        errors = validate_action({"schema": "WatchAction@99", "kind": "project.observe"})
        assert any("WatchAction@1" in str(e) for e in errors)


# ── Rule validation (condition + actions) ────────────────────────────


class TestRuleValidation:
    def test_valid_rule(self) -> None:
        rule = {
            "condition": {
                "operator": "any",
                "clauses": [{"field": "checks", "comparison": "changed_to", "value": "failure"}],
            },
            "actions": [{"kind": "project.observe"}],
        }
        assert validate_rule(rule) == []

    def test_missing_condition_refused(self) -> None:
        errors = validate_rule({"actions": [{"kind": "project.observe"}]})
        assert any("must have a 'condition'" in str(e) for e in errors)

    def test_missing_actions_refused(self) -> None:
        errors = validate_rule({
            "condition": {"operator": "any", "clauses": [
                {"field": "x", "comparison": "equals", "value": 1},
            ]},
        })
        assert any("non-empty array" in str(e) for e in errors)

    def test_rules_list_validation(self) -> None:
        errors = validate_rules("not a list")
        assert any("must be an array" in str(e) for e in errors)


# ── HS-161-03: GitHub test payload (SS8.1) ─────────────────────────


class TestGitHubTestPayload:
    """SS8.1: the github test carries provider/connection, repo, query,
    entity count, up to 5 representative PRs, matched conditions,
    supported transitions, observation time, duration, and typed error.
    """

    @staticmethod
    def _github_fetcher(principal, **kwargs):
        """Fake runner returning 3 open PRs with varied states."""
        return [
            {
                "number": 10, "title": "Add login",
                "url": "https://github.com/acme/app/pull/10",
                "state": "open", "isDraft": False,
                "reviewRequests": [], "reviewDecision": "",
                "checks": "success", "headRefOid": "aaa111",
                "updatedAt": "2026-09-01T00:00:00Z",
            },
            {
                "number": 11, "title": "Fix CI",
                "url": "https://github.com/acme/app/pull/11",
                "state": "open", "isDraft": True,
                "reviewRequests": ["alice"], "reviewDecision": "",
                "checks": "failure", "headRefOid": "bbb222",
                "updatedAt": "2026-09-01T01:00:00Z",
            },
            {
                "number": 12, "title": "Refactor DB",
                "url": "https://github.com/acme/app/pull/12",
                "state": "open", "isDraft": False,
                "reviewRequests": [], "reviewDecision": "APPROVED",
                "checks": "success", "headRefOid": "ccc333",
                "updatedAt": "2026-09-01T02:00:00Z",
            },
        ]

    def test_ss81_fields_present(self, tmp_path) -> None:
        """Every SS8.1 display field is present in the test result."""
        db = Database(tmp_path / "gh-ss81.db")
        _make_watch(db, "watch-gh-ss81")
        svc = _watch_svc(db, fetcher=self._github_fetcher)
        result = svc.test_watch(OWNER, "watch-gh-ss81")

        r = result["result"]
        assert result["test_state"] == "passed"

        # SS8.1 fields
        assert r["provider"] == "github"
        assert "connection" in r
        assert r["repository"] == "acme/app"
        assert r["normalized_query"] == {"repository": "acme/app"}
        assert r["entity_count"] == 3
        assert len(r["representative_entities"]) == 3
        assert "matched_conditions" in r
        assert "supported_transitions" in r
        assert r["observed_at"] != ""
        assert "duration_ms" in r
        assert r["error"] is None

    def test_matched_conditions_summary(self, tmp_path) -> None:
        """Matched conditions summarize PR states correctly."""
        db = Database(tmp_path / "gh-cond.db")
        _make_watch(db, "watch-gh-cond")
        svc = _watch_svc(db, fetcher=self._github_fetcher)
        result = svc.test_watch(OWNER, "watch-gh-cond")

        cond = result["result"]["matched_conditions"]
        assert cond["states"]["open"] == 3
        assert cond["checks"]["success"] == 2
        assert cond["checks"]["failure"] == 1
        assert cond["drafts"] == 1

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

    def test_zero_matches_honest_label(self, tmp_path) -> None:
        """ACT-002: zero-match test for github = PASSED with honest label."""
        db = Database(tmp_path / "gh-zero.db")
        _make_watch(db, "watch-gh-zero")

        def empty_fetcher(principal, **kwargs):
            return []

        svc = _watch_svc(db, fetcher=empty_fetcher)
        result = svc.test_watch(OWNER, "watch-gh-zero")

        assert result["test_state"] == "passed"
        r = result["result"]
        assert r["entity_count"] == 0
        assert "0 current matches" in r["message"]
        assert r["provider"] == "github"
        assert r["error"] is None

    def test_failure_typed_prov009(self, tmp_path) -> None:
        """PROV-009: failures carry typed error codes."""
        db = Database(tmp_path / "gh-fail.db")
        _make_watch(db, "watch-gh-fail")

        def fail_fetcher(principal, **kwargs):
            raise ServiceError(
                "connector_unavailable",
                "GitHub CLI is not installed",
            )

        svc = _watch_svc(db, fetcher=fail_fetcher)
        result = svc.test_watch(OWNER, "watch-gh-fail")

        assert result["test_state"] == "failed"
        err = result["result"]["error"]
        assert err["code"] == "unavailable"
        assert err["type"] == "ServiceError"
        assert result["result"]["provider"] == "github"


# ── HS-161-03: GitHub baseline (ACT-005) ──────────────────────────


class TestGitHubBaseline:
    """ACT-005: baseline for github watches emits zero events."""

    def test_github_baseline_ledger_silence(self, tmp_path) -> None:
        db = Database(tmp_path / "gh-base-silent.db")
        _make_watch(db, "watch-gh-bs")

        def fetcher(principal, **kwargs):
            return [
                {"number": 1, "state": "open", "title": "PR1",
                 "url": "http://gh/1", "checks": "success"},
                {"number": 2, "state": "open", "title": "PR2",
                 "url": "http://gh/2", "checks": "failure"},
            ]

        svc = _watch_svc(db, fetcher=fetcher)

        events_before = db.automations.list_events()
        count_before = len(events_before)

        result = svc.baseline_watch(OWNER, "watch-gh-bs")

        events_after = db.automations.list_events()
        count_after = len(events_after)
        assert count_after == count_before, (
            f"ACT-005 violation: github baseline emitted "
            f"{count_after - count_before} events"
        )
        assert result["baseline_state"] == "established"
        assert result["entity_count"] == 2


# ── HS-161-03: evaluate_once ──────────────────────────────────────


class TestEvaluateOnce:
    """evaluate_once: snapshot -> diff -> evaluation -> observations."""

    @staticmethod
    def _seed_project_and_watch(db, project_id="proj-eval",
                                watch_id="watch-eval"):
        """Seed a project, a watch, and a project_sources binding."""
        with db._connection() as conn:
            conn.execute(
                """INSERT INTO projects
                   (id, name, description, keywords_json,
                    team_members_json, context_json,
                    detection_threshold, revision,
                    created_at, updated_at)
                   VALUES (?, 'Eval Project', '', '[]', '[]', '{}',
                           0.4, 1, datetime('now'), datetime('now'))""",
                (project_id,),
            )
        from holdspeak.services.reaction_service import ReactionService
        rs = ReactionService(db)
        rs.create_watch(
            OWNER, connector_id="gh", query_kind="pull_requests",
            name="Eval Watch",
            query={"repository": "acme/app"},
            watch_id=watch_id,
        )
        db.automations.update_watch_spec(
            watch_id, project_id=project_id, revision=1,
        )
        db.automations.create_project_source(
            source_id=f"psrc_{watch_id}",
            project_id=project_id,
            source_ref=f"watch:{watch_id}",
            label="Eval Watch",
            semantic_role="watch",
        )
        return project_id, watch_id

    def test_transitions_yield_evaluation_and_observations(
        self, tmp_path,
    ) -> None:
        """Changed PR snapshot -> transitions -> evaluation row + obs."""
        db = Database(tmp_path / "eval-trans.db")
        project_id, watch_id = self._seed_project_and_watch(db)

        # Phase 1: baseline with one PR open.
        baseline_entities = [
            {"number": 1, "state": "open", "title": "PR One",
             "url": "http://gh/1", "checks": "success",
             "headRefOid": "aaa"},
        ]
        call_count = [0]

        def fetcher(principal, **kwargs):
            call_count[0] += 1
            if call_count[0] <= 1:
                return baseline_entities
            # Phase 2: checks changed to failure.
            return [
                {"number": 1, "state": "open", "title": "PR One",
                 "url": "http://gh/1", "checks": "failure",
                 "headRefOid": "aaa"},
            ]

        svc = _watch_svc(db, fetcher=fetcher)
        svc.baseline_watch(OWNER, watch_id)

        # Evaluate: checks changed -> transition.
        result = svc.evaluate_once(OWNER, watch_id)

        assert result["state"] == "completed"
        assert result["transitions"] >= 1
        assert len(result["observation_ids"]) >= 1

        # Evaluation row persisted.
        eval_row = db.automations.get_evaluation(result["evaluation_id"])
        assert eval_row is not None
        assert eval_row["watch_id"] == watch_id
        assert eval_row["state"] == "completed"

        # Observations persisted in project_observations.
        obs = db.project_observations.list_observations(project_id)
        watch_obs = [
            o for o in obs
            if o["observation_kind"] == "watch.transition"
        ]
        assert len(watch_obs) >= 1

    def test_unchanged_snapshot_noop(self, tmp_path) -> None:
        """Identical re-evaluation = typed no-op, never a crash."""
        db = Database(tmp_path / "eval-noop.db")
        project_id, watch_id = self._seed_project_and_watch(db)

        entities = [
            {"number": 1, "state": "open", "title": "PR One",
             "url": "http://gh/1"},
        ]

        def fetcher(principal, **kwargs):
            return entities

        svc = _watch_svc(db, fetcher=fetcher)
        svc.baseline_watch(OWNER, watch_id)

        # First evaluate: same as baseline -> no transitions but creates eval.
        r1 = svc.evaluate_once(OWNER, watch_id)
        assert r1["state"] == "completed"
        assert r1["transitions"] == 0

        # Second evaluate: identical snapshot -> no_op.
        r2 = svc.evaluate_once(OWNER, watch_id)
        assert r2["state"] == "no_op"
        assert r2["evaluation_id"] == r1["evaluation_id"]
        assert r2["observation_ids"] == []

    def test_uniqueness_law(self, tmp_path) -> None:
        """UNIQUE(watch_id, revision, source_revision) proven."""
        db = Database(tmp_path / "eval-uniq.db")
        project_id, watch_id = self._seed_project_and_watch(db)

        entities = [
            {"number": 5, "state": "open", "title": "Five",
             "url": "http://gh/5"},
        ]

        def fetcher(principal, **kwargs):
            return entities

        svc = _watch_svc(db, fetcher=fetcher)
        svc.baseline_watch(OWNER, watch_id)

        r1 = svc.evaluate_once(OWNER, watch_id)
        r2 = svc.evaluate_once(OWNER, watch_id)

        # Both return the same evaluation ID -- second is no_op.
        assert r1["evaluation_id"] == r2["evaluation_id"]
        assert r2["state"] == "no_op"

        # Only one evaluation row exists.
        evals = db.automations.list_evaluations(watch_id)
        assert len(evals) == 1

    def test_no_project_binding_still_evaluates(self, tmp_path) -> None:
        """A watch without a project binding still creates the eval row."""
        db = Database(tmp_path / "eval-noproj.db")
        _make_watch(db, "watch-noproj")
        db.automations.update_watch_spec("watch-noproj", revision=1)

        entities = [
            {"number": 1, "state": "open", "title": "Solo",
             "url": "http://gh/1"},
        ]

        def fetcher(principal, **kwargs):
            return entities

        svc = _watch_svc(db, fetcher=fetcher)
        svc.baseline_watch(OWNER, "watch-noproj")
        result = svc.evaluate_once(OWNER, "watch-noproj")

        assert result["state"] == "completed"
        assert result["evaluation_id"] is not None
        # No observations (no project binding).
        assert result["observation_ids"] == []

    def test_baseline_advanced_after_evaluate(self, tmp_path) -> None:
        """After evaluate_once, the baseline reflects the new snapshot."""
        db = Database(tmp_path / "eval-advance.db")
        _make_watch(db, "watch-advance")
        db.automations.update_watch_spec("watch-advance", revision=1)

        call_count = [0]

        def fetcher(principal, **kwargs):
            call_count[0] += 1
            if call_count[0] <= 1:
                return [{"number": 1, "state": "open", "title": "One",
                         "url": "http://gh/1"}]
            return [
                {"number": 1, "state": "open", "title": "One",
                 "url": "http://gh/1"},
                {"number": 2, "state": "open", "title": "Two",
                 "url": "http://gh/2"},
            ]

        svc = _watch_svc(db, fetcher=fetcher)
        svc.baseline_watch(OWNER, "watch-advance")
        svc.evaluate_once(OWNER, "watch-advance")

        watch = db.automations.get_watch("watch-advance")
        assert len(watch["snapshot"].get("entities", {})) == 2

    def test_evaluate_once_toctou_integrity_error_returns_no_op(
        self, tmp_path, monkeypatch,
    ) -> None:
        """S-3 counsel: concurrent evaluation races past the idempotency
        check (find_evaluation_by_source returns None while a row exists).
        evaluate_once catches the IntegrityError and returns no_op instead
        of 500ing."""
        db = Database(tmp_path / "eval-toctou.db")
        _make_watch(db, "watch-toctou")
        db.automations.update_watch_spec("watch-toctou", revision=1)

        entities = [
            {"number": 1, "state": "open", "title": "PR",
             "url": "http://gh/1", "checks": "success",
             "headRefOid": "aaa"},
        ]

        def fetcher(principal, **kwargs):
            return entities

        svc = _watch_svc(db, fetcher=fetcher)
        svc.baseline_watch(OWNER, "watch-toctou")

        # First evaluation succeeds normally.
        r1 = svc.evaluate_once(OWNER, "watch-toctou")
        assert r1["state"] == "completed" or r1["state"] == "no_op"

        # Monkeypatch find_evaluation_by_source to return None on the
        # first call (simulating the TOCTOU window), then restore.
        original_find = db.automations.find_evaluation_by_source
        call_count = [0]

        def lying_find(watch_id, watch_revision, source_revision):
            call_count[0] += 1
            if call_count[0] == 1:
                # Simulate the TOCTOU: claim no existing row.
                return None
            # On the recovery re-read, tell the truth.
            return original_find(watch_id, watch_revision, source_revision)

        monkeypatch.setattr(
            db.automations, "find_evaluation_by_source", lying_find,
        )

        # Second evaluation: the lying find returns None, so
        # evaluate_once tries to INSERT and hits IntegrityError.
        # It should catch and return no_op, not raise.
        r2 = svc.evaluate_once(OWNER, "watch-toctou")
        assert r2["state"] == "no_op", (
            f"TOCTOU collision should return no_op; got {r2['state']}"
        )
        assert "concurrent" in r2.get("message", "").lower() or "already" in r2.get("message", "").lower(), (
            f"Message should indicate concurrent/duplicate; got {r2['message']!r}"
        )


# ── HS-166-03: Jira leg through the real WatchService path ───────────
# Zero-fork proof: baseline/evaluate/dedup/effects stay untouched.


class TestJiraLeg:
    """A jira watch tests, baselines, evaluates through unchanged WatchService."""

    def _jira_fetcher(self, phase_entities):
        """Return a fetcher cycling through entity phases."""
        call_count = [0]
        def fetcher(principal, *, connector_id, query_kind, query):
            idx = min(call_count[0], len(phase_entities) - 1)
            call_count[0] += 1
            return list(phase_entities[idx])
        return fetcher

    def test_jira_test_watch_display_block(self, tmp_path) -> None:
        """test_watch for a jira watch populates the SS8.2 display payload."""
        db = Database(tmp_path / "jira-leg-test.db")
        entities = [
            {"id": "KAN-1", "key": "KAN-1", "title": "Task 1",
             "status": "In Progress", "status_category": "indeterminate",
             "assignee": "alice", "priority": "high", "resolution": "",
             "due_at": "2026-09-10", "updated_at": "2026-09-01T00:00:00Z",
             "issue_type": "Task", "labels": [], "project_key": "KAN",
             "url": "https://alpha.atlassian.net/browse/KAN-1",
             "status_changed_at": "2026-09-01T00:00:00Z", "created_at": "2026-08-01"},
        ]
        fetcher = self._jira_fetcher([entities])
        _make_watch(db, "watch-jira-01", connector_id="jira",
                    query_kind="issues", query={
                        "connection_ref": "alpha.atlassian.net|user@example.com",
                        "projects": ["KAN"],
                    })
        svc = _watch_svc(db, fetcher)
        result = svc.test_watch(OWNER, "watch-jira-01")
        assert result["test_state"] == "passed"
        r = result["result"]
        assert r["provider"] == "jira"
        assert r["connection"]["site"] == "alpha.atlassian.net"
        assert r["connection"]["email"] == "user@example.com"
        assert r["projects"] == ["KAN"]
        assert "normalized_jql" in r
        assert r["entity_count"] == 1
        assert len(r["representative_entities"]) == 1
        assert "matched_conditions" in r
        assert "supported_transitions" in r
        assert "jira.issue.status_changed" in r["supported_transitions"]

    def test_jira_test_watch_error_twin(self, tmp_path) -> None:
        """test_watch for a failing jira watch carries provider context."""
        db = Database(tmp_path / "jira-leg-err.db")
        def failing_fetcher(principal, **kwargs):
            from holdspeak.services.errors import ServiceError
            raise ServiceError("connector_query_invalid", "bad JQL")
        _make_watch(db, "watch-jira-err", connector_id="jira",
                    query_kind="issues", query={
                        "connection_ref": "alpha.atlassian.net|user@example.com",
                    })
        svc = _watch_svc(db, failing_fetcher)
        result = svc.test_watch(OWNER, "watch-jira-err")
        assert result["test_state"] == "failed"
        r = result["result"]
        assert r["provider"] == "jira"
        assert r["connection"]["site"] == "alpha.atlassian.net"

    def test_jira_baseline(self, tmp_path) -> None:
        """baseline_watch for a jira watch writes snapshot without events."""
        db = Database(tmp_path / "jira-baseline.db")
        entities = [
            {"id": "KAN-1", "key": "KAN-1", "title": "Task 1",
             "status": "todo", "status_category": "new",
             "assignee": "", "priority": "", "resolution": "",
             "due_at": "", "updated_at": "2026-09-01T00:00:00Z",
             "issue_type": "Task", "labels": [], "project_key": "KAN",
             "url": "https://a.atlassian.net/browse/KAN-1",
             "status_changed_at": "", "created_at": ""},
        ]
        fetcher = self._jira_fetcher([entities])
        _make_watch(db, "watch-jira-bl", connector_id="jira",
                    query_kind="issues", query={
                        "connection_ref": "a.atlassian.net|u@x.com",
                    })
        svc = _watch_svc(db, fetcher)
        svc.baseline_watch(OWNER, "watch-jira-bl")
        watch = db.automations.get_watch("watch-jira-bl")
        # _payload parses snapshot_json into "snapshot" key
        snapshot = watch.get("snapshot", {})
        assert "KAN-1" in snapshot.get("entities", {})

    def test_jira_evaluate_dedup(self, tmp_path) -> None:
        """Same source_revision evaluates once (idempotency)."""
        db = Database(tmp_path / "jira-dedup.db")
        entities = [
            {"id": "KAN-1", "key": "KAN-1", "title": "Task 1",
             "status": "todo", "status_category": "new",
             "assignee": "", "priority": "", "resolution": "",
             "due_at": "", "updated_at": "2026-09-01T00:00:00Z",
             "issue_type": "Task", "labels": [], "project_key": "KAN",
             "url": "https://a.atlassian.net/browse/KAN-1",
             "status_changed_at": "", "created_at": ""},
        ]
        fetcher = self._jira_fetcher([entities])
        _make_watch(db, "watch-jira-dd", connector_id="jira",
                    query_kind="issues", query={
                        "connection_ref": "a.atlassian.net|u@x.com",
                    })
        svc = _watch_svc(db, fetcher)
        # baseline first
        svc.baseline_watch(OWNER, "watch-jira-dd")
        # first evaluate
        r1 = svc.evaluate_once(OWNER, "watch-jira-dd")
        # same snapshot -> no_op
        r2 = svc.evaluate_once(OWNER, "watch-jira-dd")
        assert r2["state"] == "no_op"

    def test_jira_status_transition_creates_effect(self, tmp_path) -> None:
        """A jira status transition through evaluate_due records ONE effect."""
        db = Database(tmp_path / "jira-effect.db")
        baseline = [
            {"id": "KAN-1", "key": "KAN-1", "title": "Task 1",
             "status": "todo", "status_category": "new",
             "assignee": "", "priority": "", "resolution": "",
             "due_at": "", "updated_at": "2026-09-01T00:00:00Z",
             "issue_type": "Task", "labels": [], "project_key": "KAN",
             "url": "https://a.atlassian.net/browse/KAN-1",
             "status_changed_at": "", "created_at": ""},
        ]
        changed = [
            {"id": "KAN-1", "key": "KAN-1", "title": "Task 1",
             "status": "in progress", "status_category": "indeterminate",
             "assignee": "", "priority": "", "resolution": "",
             "due_at": "", "updated_at": "2026-09-01T12:00:00Z",
             "issue_type": "Task", "labels": [], "project_key": "KAN",
             "url": "https://a.atlassian.net/browse/KAN-1",
             "status_changed_at": "2026-09-01T12:00:00Z", "created_at": ""},
        ]
        fetcher = self._jira_fetcher([baseline, changed])

        # Create a project for observations
        from holdspeak.services.project_service import ProjectService
        ps = ProjectService(db)
        project = ps.create_project(OWNER, {"name": "Effect test", "description": "d"})
        project_id = project["id"]

        _make_watch(db, "watch-jira-fx", connector_id="jira",
                    query_kind="issues", query={
                        "connection_ref": "a.atlassian.net|u@x.com",
                    })
        # Graduate the watch
        db.automations.update_watch_spec(
            "watch-jira-fx",
            state="active",
            schema_version="WatchSpec@1",
            evaluation_cadence_minutes=60,
            next_evaluation_at="2020-01-01T00:00:00",
        )
        # Bind watch to project
        with db._connection() as conn:
            conn.execute(
                "UPDATE connector_watches SET project_id=? WHERE id=?",
                (project_id, "watch-jira-fx"),
            )

        # Create a rule that matches status_changed
        from holdspeak.watch_validation import CONDITION_SCHEMA, ACTION_SCHEMA
        svc = _watch_svc(db, fetcher)
        svc.set_rules(OWNER, "watch-jira-fx", [{
            "condition": {
                "schema": CONDITION_SCHEMA,
                "operator": "any",
                "clauses": [
                    {"field": "status", "comparison": "changed"},
                ],
            },
            "actions": [
                {"schema": ACTION_SCHEMA, "kind": "project.observe"},
            ],
        }])

        # Baseline
        svc.baseline_watch(OWNER, "watch-jira-fx")
        # Evaluate via evaluate_due (the scheduled path)
        outcomes = svc.evaluate_due(OWNER)
        assert len(outcomes) == 1
        outcome = outcomes[0]
        assert outcome["outcome"] in ("evaluated", "probe_half_open")
        assert outcome["transitions"] > 0
        # The effect was recorded
        assert "effects" in outcome
        assert len(outcome["effects"]) >= 1

    def test_jira_unchanged_yields_no_op(self, tmp_path) -> None:
        """Re-evaluate unchanged snapshot -> no new effects (zero-fork proof)."""
        db = Database(tmp_path / "jira-noop.db")
        entities = [
            {"id": "KAN-1", "key": "KAN-1", "title": "Task 1",
             "status": "todo", "status_category": "new",
             "assignee": "", "priority": "", "resolution": "",
             "due_at": "", "updated_at": "2026-09-01T00:00:00Z",
             "issue_type": "Task", "labels": [], "project_key": "KAN",
             "url": "https://a.atlassian.net/browse/KAN-1",
             "status_changed_at": "", "created_at": ""},
        ]
        fetcher = self._jira_fetcher([entities])
        _make_watch(db, "watch-jira-noop", connector_id="jira",
                    query_kind="issues", query={
                        "connection_ref": "a.atlassian.net|u@x.com",
                    })
        db.automations.update_watch_spec(
            "watch-jira-noop",
            state="active",
            schema_version="WatchSpec@1",
            evaluation_cadence_minutes=60,
            next_evaluation_at="2020-01-01T00:00:00",
        )
        svc = _watch_svc(db, fetcher)
        svc.baseline_watch(OWNER, "watch-jira-noop")
        outcomes = svc.evaluate_due(OWNER)
        assert len(outcomes) == 1
        # no_op or zero transitions
        outcome = outcomes[0]
        assert outcome.get("transitions", 0) == 0 or outcome["outcome"] == "evaluated"
        assert "effects" not in outcome or len(outcome.get("effects", [])) == 0
