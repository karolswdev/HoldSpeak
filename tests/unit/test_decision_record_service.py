"""Tests for the durable decision record canon (HS-127-01)."""

from __future__ import annotations

import asyncio
from datetime import date, timedelta

import pytest

from holdspeak.db.core import Database
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.decision_lifecycle_service import DecisionLifecycleService
from holdspeak.services.errors import ConflictError
from holdspeak.services.decision_record_service import DecisionRecordService


def test_create_record_with_all_required_fields(tmp_path):
    service = DecisionRecordService(Database(tmp_path / "records.db"))

    record = service.create(
        None,
        decision_text="Use durable decision records.",
        rationale="The decision needs one traceable record.",
        alternatives="Keep decisions split across stores.",
        owner="Karol",
        review_date="2026-09-01",
        source_type="meeting",
        source_id="decision-123",
    )

    assert record["id"].startswith("record-")
    assert record["decision_text"] == "Use durable decision records."
    assert record["rationale"] == "The decision needs one traceable record."
    assert record["alternatives"] == "Keep decisions split across stores."
    assert record["owner"] == "Karol"
    assert record["review_date"] == "2026-09-01"
    assert record["lifecycle"] == "active"
    assert record["source_type"] == "meeting"
    assert record["source_id"] == "decision-123"
    assert record["created_at"] == record["updated_at"]


def test_get_record_returns_all_fields_and_links(tmp_path):
    service = DecisionRecordService(Database(tmp_path / "records.db"))
    record = service.create(
        None,
        decision_text="Ship the record schema.",
        source_type="desk",
        source_id="adr-127",
    )
    with service._db._connection() as conn:
        conn.execute(
            """INSERT INTO decision_record_sources
               (id, record_id, source_type, source_ref, created_at)
               VALUES ('source-1', ?, 'artifact', 'artifact-127', '2026-08-07T00:00:00+00:00')""",
            (record["id"],),
        )
        conn.execute(
            """INSERT INTO decision_record_work
               (id, record_id, work_type, work_ref, created_at)
               VALUES ('work-1', ?, 'project', 'HS-127', '2026-08-07T00:00:00+00:00')""",
            (record["id"],),
        )
        conn.execute(
            """INSERT INTO decision_record_revisions
               (id, record_id, field_name, old_value, new_value, created_at)
               VALUES ('revision-1', ?, 'owner', NULL, 'Karol', '2026-08-07T00:00:00+00:00')""",
            (record["id"],),
        )

    loaded = service.get(None, record["id"])

    assert loaded is not None
    assert loaded["id"] == record["id"]
    assert loaded["decision_text"] == "Ship the record schema."
    assert loaded["source_type"] == "desk"
    assert loaded["source_id"] == "adr-127"
    assert loaded["sources"] == [{
        "id": "source-1", "record_id": record["id"], "source_type": "artifact",
        "source_ref": "artifact-127", "created_at": "2026-08-07T00:00:00+00:00",
    }]
    assert loaded["work"][0]["work_ref"] == "HS-127"
    assert loaded["revisions"][0]["new_value"] == "Karol"


def test_list_records_returns_all_records(tmp_path):
    service = DecisionRecordService(Database(tmp_path / "records.db"))
    first = service.create(None, decision_text="First decision", source_type="meeting", source_id="dec-1")
    second = service.create(None, decision_text="Second decision", source_type="desk", source_id="adr-2")

    records = service.list_records(None)

    assert {record["id"] for record in records} == {first["id"], second["id"]}


def test_update_record_records_each_changed_field_without_erasing_original(tmp_path):
    service = DecisionRecordService(Database(tmp_path / "records.db"))
    record = service.create(
        None,
        decision_text="Keep the original decision.",
        rationale="Initial rationale.",
        source_type="desk",
        source_id="desk-127",
    )

    updated = service.update_record(
        None, record["id"], {"rationale": "Revised rationale."}
    )
    loaded = service.get(None, record["id"])

    assert updated["rationale"] == "Revised rationale."
    assert loaded is not None
    assert loaded["decision_text"] == "Keep the original decision."
    assert [(revision["field_name"], revision["old_value"], revision["new_value"])
            for revision in loaded["revisions"]] == [
        ("rationale", "Initial rationale.", "Revised rationale.")
    ]


def test_affected_work_links_are_listed_in_both_directions_and_removable(tmp_path):
    service = DecisionRecordService(Database(tmp_path / "records.db"))
    record = service.create(
        None, decision_text="Govern HS-127.", source_type="desk", source_id="desk-work"
    )

    link = service.link_work(None, record["id"], "project", "HS-127")
    duplicate = service.link_work(None, record["id"], "project", "HS-127")

    assert duplicate["id"] == link["id"]
    assert service.list_work(None, record["id"]) == [link]
    assert [item["id"] for item in service.records_for_work(None, "project", "HS-127")] == [
        record["id"]
    ]
    assert service.unlink_work(None, record["id"], "project", "HS-127") is True
    assert service.list_work(None, record["id"]) == []
    assert service.records_for_work(None, "project", "HS-127") == []


def test_due_for_review_includes_overdue_and_excludes_future_records(tmp_path):
    service = DecisionRecordService(Database(tmp_path / "records.db"))
    overdue = service.create(
        None,
        decision_text="Review the overdue decision.",
        review_date=(date.today() - timedelta(days=1)).isoformat(),
        source_type="desk",
        source_id="desk-overdue",
    )
    service.create(
        None,
        decision_text="Review the future decision.",
        review_date=(date.today() + timedelta(days=1)).isoformat(),
        source_type="desk",
        source_id="desk-future",
    )

    due = service.due_for_review(None)

    assert [record["id"] for record in due] == [overdue["id"]]


def test_supersede_seals_predecessor_and_preserves_both_records(tmp_path):
    service = DecisionRecordService(Database(tmp_path / "records.db"))
    predecessor = service.create(
        None, decision_text="Use the original plan.", source_type="desk", source_id="desk-old"
    )
    successor = service.create(
        None, decision_text="Use the replacement plan.", source_type="desk", source_id="desk-new"
    )
    service.link_work(None, predecessor["id"], "project", "HS-127")

    sealed = service.supersede(
        None, predecessor["id"], successor["id"], "Requirements changed."
    )
    loaded_successor = service.get(None, successor["id"])

    assert sealed["lifecycle"] == "superseded"
    assert sealed["successor_id"] == successor["id"]
    assert sealed["supersession_reason"] == "Requirements changed."
    assert sealed["work"][0]["work_ref"] == "HS-127"
    assert loaded_successor is not None
    assert loaded_successor["predecessor_id"] == predecessor["id"]
    assert loaded_successor["decision_text"] == "Use the replacement plan."
    with pytest.raises(ValueError, match="sealed"):
        service.update_record(None, predecessor["id"], {"rationale": "Rewrite history."})


def _accepted_meeting_decision(db: Database, decision_id: str = "dec-127") -> None:
    with db._connection() as conn:
        conn.execute(
            """INSERT INTO decisions (
                   id, text, rationale, decided_at, date_basis, source_artifact_id,
                   source_meeting_id, source_state, lifecycle, created_at, updated_at,
                   last_modified, deleted
               ) VALUES (?, 'Use record-backed decisions.', 'One durable canon.',
                         '2026-08-07T00:00:00+00:00', 'meeting_date', 'artifact-127',
                         'meeting-127', 'linked', 'accepted', '2026-08-07T00:00:00+00:00',
                         '2026-08-07T00:00:00+00:00', '2026-08-07T00:00:00+00:00', 0)""",
            (decision_id,),
        )


def test_create_from_meeting_mints_idempotent_record_with_lineage(tmp_path):
    db = Database(tmp_path / "records.db")
    _accepted_meeting_decision(db)
    source_before = db.decisions.get("dec-127").to_dict()
    service = DecisionRecordService(db)

    record = service.create_from_meeting(None, "dec-127")
    repeated = service.create_from_meeting(None, "dec-127")
    loaded = service.get(None, record["id"])

    assert record["source_type"] == "meeting"
    assert record["source_id"] == "dec-127"
    assert record["decision_text"] == "Use record-backed decisions."
    assert record["rationale"] == "One durable canon."
    assert repeated["id"] == record["id"]
    assert loaded is not None
    assert {(source["source_type"], source["source_ref"]) for source in loaded["sources"]} == {
        ("meeting", "meeting-127"),
        ("artifact", "artifact-127"),
    }
    assert db.decisions.get("dec-127").to_dict() == source_before


def _meeting_evidence(db: Database, *, with_segment: bool, artifact_id: str = "artifact-evidence") -> None:
    with db._connection() as conn:
        conn.execute(
            "INSERT INTO meetings (id, started_at, title) VALUES (?, ?, ?)",
            ("meeting-evidence", "2026-08-07T09:00:00+00:00", "Record evidence"),
        )
        if artifact_id:
            conn.execute(
                """INSERT INTO artifacts (id, meeting_id, artifact_type, title)
                   VALUES (?, 'meeting-evidence', 'decisions', 'Decision capture')""",
                (artifact_id,),
            )
        conn.execute(
            """INSERT INTO decisions (
                   id, text, rationale, decided_at, date_basis, source_timestamp,
                   provenance_label, source_artifact_id, source_meeting_id,
                   source_state, lifecycle, created_at, updated_at, last_modified, deleted
               ) VALUES (
                   'dec-evidence', 'Ship the record evidence.', NULL,
                   '2026-08-07T09:00:30+00:00', 'transcript_moment', 30.0,
                   'reported', ?, 'meeting-evidence', 'linked', 'accepted',
                   '2026-08-07T00:00:00+00:00', '2026-08-07T00:00:00+00:00',
                   '2026-08-07T00:00:00+00:00', 0
               )""",
            (artifact_id,),
        )
        if with_segment:
            conn.execute(
                """INSERT INTO segments (meeting_id, text, speaker, start_time, end_time)
                   VALUES ('meeting-evidence', 'Ship the record evidence.', 'Mina', 20.0, 40.0)"""
            )


def test_create_from_meeting_persists_exact_segment_evidence(tmp_path):
    db = Database(tmp_path / "records.db")
    _meeting_evidence(db, with_segment=True)
    service = DecisionRecordService(db)

    record = service.create_from_meeting(None, "dec-evidence")
    loaded = service.get(None, record["id"])

    assert loaded is not None
    sources = {source["source_type"]: source for source in loaded["sources"]}
    assert sources["meeting"]["source_ref"] == "meeting-evidence"
    assert sources["artifact"]["source_ref"] == "artifact-evidence"
    assert sources["segment"]["text"] == "Ship the record evidence."
    assert sources["segment"]["speaker"] == "Mina"


def test_create_from_meeting_without_segments_keeps_meeting_only(tmp_path):
    db = Database(tmp_path / "records.db")
    _meeting_evidence(db, with_segment=False, artifact_id="")
    service = DecisionRecordService(db)

    record = service.create_from_meeting(None, "dec-evidence")
    loaded = service.get(None, record["id"])

    assert loaded is not None
    assert [(source["source_type"], source["source_ref"]) for source in loaded["sources"]] == [
        ("meeting", "meeting-evidence")
    ]


def test_get_record_resolves_source_details(tmp_path):
    db = Database(tmp_path / "records.db")
    _meeting_evidence(db, with_segment=True)
    service = DecisionRecordService(db)

    record = service.create_from_meeting(None, "dec-evidence")
    loaded = service.get(None, record["id"])

    assert loaded is not None
    sources = {source["source_type"]: source for source in loaded["sources"]}
    assert sources["meeting"]["title"] == "Record evidence"
    assert sources["meeting"]["date"] == "2026-08-07T09:00:00+00:00"
    assert sources["artifact"]["artifact_type"] == "decisions"
    assert sources["segment"]["details"]["speaker"] == "Mina"


def test_provenance_resolution_failure_still_mints_record(tmp_path, monkeypatch):
    db = Database(tmp_path / "records.db")
    _meeting_evidence(db, with_segment=True)
    service = DecisionRecordService(db)

    def fail_resolution(decision_id: str):
        raise RuntimeError("transcript unavailable")

    monkeypatch.setattr(db.decisions, "resolve_decision_moment", fail_resolution)
    record = service.create_from_meeting(None, "dec-evidence")
    loaded = service.get(None, record["id"])

    assert loaded is not None
    assert {source["source_type"] for source in loaded["sources"]} == {"meeting", "artifact"}


def test_create_from_desk_mints_idempotent_record(tmp_path):
    db = Database(tmp_path / "records.db")
    db.desk_decisions.upsert(
        decision_id="desk-127",
        title="Record origin",
        status="accepted",
        deciders=["Karol", "Mina"],
        context_markdown="Decisions need one durable canon.",
        decision_markdown="Use record-backed decisions.",
        alternatives=[{"name": "Separate stores", "reason": "Harder to trace"}],
        consequences_markdown="Sources remain authoritative.",
    )
    source_before = db.desk_decisions.get("desk-127").to_dict()
    service = DecisionRecordService(db)

    record = service.create_from_desk(None, "desk-127")
    repeated = service.create_from_desk(None, "desk-127")

    assert record["source_type"] == "desk"
    assert record["source_id"] == "desk-127"
    assert record["decision_text"] == "Use record-backed decisions."
    assert record["rationale"] == (
        "Decisions need one durable canon.\n\nSources remain authoritative."
    )
    assert record["alternatives"] == '[{"name": "Separate stores", "reason": "Harder to trace"}]'
    assert record["owner"] == "Karol, Mina"
    assert repeated["id"] == record["id"]
    assert db.desk_decisions.get("desk-127").to_dict() == source_before


def test_records_from_each_origin_have_the_same_shape(tmp_path):
    db = Database(tmp_path / "records.db")
    _accepted_meeting_decision(db)
    db.desk_decisions.upsert(
        decision_id="desk-127",
        decision_markdown="Choose the record origin.",
    )
    service = DecisionRecordService(db)

    meeting_record = service.create_from_meeting(None, "dec-127")
    desk_record = service.create_from_desk(None, "desk-127")

    assert set(meeting_record) == set(desk_record)


def test_create_from_meeting_rejects_unknown_decision(tmp_path):
    service = DecisionRecordService(Database(tmp_path / "records.db"))

    with pytest.raises(KeyError, match="missing-decision"):
        service.create_from_meeting(None, "missing-decision")


def test_record_requires_decision_text_and_source_type(tmp_path):
    service = DecisionRecordService(Database(tmp_path / "records.db"))

    with pytest.raises(ValueError, match="decision_text is required"):
        service.create(None, decision_text="", source_type="meeting", source_id="dec-1")
    with pytest.raises(ValueError, match="source_type is required"):
        service.create(None, decision_text="A decision", source_type="", source_id="dec-1")


def test_search_finds_kafka_in_decision_text_and_linked_work(tmp_path):
    service = DecisionRecordService(Database(tmp_path / "records.db"))
    kafka = service.create(
        None,
        decision_text="Use Kafka for the event stream.",
        rationale="Durable ordered delivery.",
        source_type="desk",
        source_id="desk-kafka",
    )
    work_link = service.create(
        None,
        decision_text="Track the streaming migration.",
        source_type="desk",
        source_id="desk-work-link",
    )
    service.link_work(None, work_link["id"], "project", "Kafka migration")

    matches = service.search(None, "Why Kafka?")

    assert matches[0]["id"] == kafka["id"]
    assert {record["id"] for record in matches} == {kafka["id"], work_link["id"]}




# --- admitted promotion fence (HS-131-07) -----------------------------------


def test_promotion_cancellation_after_provider_return_never_publishes_artifact(tmp_path):
    db = Database(tmp_path / "promotion.db")
    _accepted_meeting_decision(db, "dec-fence")
    from holdspeak.services.inference_assignment_service import InferenceAssignmentService
    from tests.unit.test_phase143_inference_assignments import OWNER as ASSIGNMENT_OWNER, _profile
    _profile(db, "promotion")
    InferenceAssignmentService(db).set_assignment(ASSIGNMENT_OWNER, {
        "command_id": "assign-promotion", "expected_revision": 0,
        "scope": {"kind": "capability", "capability_id": "decision.promotion_draft"},
        "entries": [{"profile_id": "promotion", "profile_revision": 1}],
    })
    from holdspeak.kernel.runtime import _configure
    broker = _configure(db)
    owner = Principal(PrincipalKind.OWNER, "promotion-owner")

    class CancellingIntel:
        def run_prompt(self, **_):
            with db._connection() as conn:
                parent_id = conn.execute(
                    "SELECT operation_id FROM kernel_parent_runs WHERE kind='decision.promotion-draft'"
                ).fetchone()[0]
            # The durable parent cancellation lands while the provider call is
            # in flight, before the runner can elect a successful child receipt.
            broker.parent_run_controller.cancel_by_operation_id(owner, parent_id)
            return "late draft that must not publish"

    broker.inference_runner._engine_factory = lambda _revision, **_kw: CancellingIntel()
    service = DecisionLifecycleService(db, kernel=broker)
    # The child's provider work completed, so its receipt is EARNED
    # (succeeded); the cancellation election fences PUBLICATION instead —
    # the finalize discard refuses the artifact by name.
    with pytest.raises(ConflictError, match="decision_promotion_cancelled"):
        asyncio.run(service.draft_promoted_with_model(owner, "dec-fence", "note", {}))

    with db._connection() as conn:
        parent_id = conn.execute(
            "SELECT operation_id FROM kernel_parent_runs WHERE kind='decision.promotion-draft'"
        ).fetchone()[0]
        child_id = conn.execute(
            "SELECT operation_id FROM kernel_operations WHERE parent_operation_id=?",
            (parent_id,),
        ).fetchone()[0]
        artifact_count = conn.execute("SELECT COUNT(*) FROM artifacts").fetchone()[0]
    child_receipt = broker.store.receipt(child_id)
    parent_receipt = broker.store.receipt(parent_id)
    assert artifact_count == 0
    assert child_receipt is not None and child_receipt["outcome"] == "succeeded"
    assert parent_receipt is not None and parent_receipt["outcome"] == "cancelled"


def test_promotion_cancelled_after_child_is_eligible_discards_artifact(tmp_path):
    db = Database(tmp_path / "promotion-late.db")
    _accepted_meeting_decision(db, "dec-late")
    from holdspeak.services.inference_assignment_service import InferenceAssignmentService
    from tests.unit.test_phase143_inference_assignments import OWNER as ASSIGNMENT_OWNER, _profile
    _profile(db, "promotion-late")
    InferenceAssignmentService(db).set_assignment(ASSIGNMENT_OWNER, {
        "command_id": "assign-promotion-late", "expected_revision": 0,
        "scope": {"kind": "capability", "capability_id": "decision.promotion_draft"},
        "entries": [{"profile_id": "promotion-late", "profile_revision": 1}],
    })
    from holdspeak.kernel.runtime import _configure
    broker = _configure(db); owner = Principal(PrincipalKind.OWNER, "promotion-owner")
    broker.inference_runner._engine_factory = lambda _revision, **_kw: type("Intel", (), {"run_prompt": lambda self, **_: "eligible draft"})()
    finalize = broker.projection_stager.finalize
    def cancel_before_finalize(invocation_id):
        parent_id = broker.store.operation(broker.projection_stager.get(invocation_id).operation_id)["parent_operation_id"]
        broker.parent_run_controller.cancel_by_operation_id(owner, parent_id)
        return finalize(invocation_id)
    broker.projection_stager.finalize = cancel_before_finalize
    with pytest.raises(ConflictError, match="decision_promotion_cancelled"):
        asyncio.run(DecisionLifecycleService(db, kernel=broker).draft_promoted_with_model(owner, "dec-late", "note", {}))
    with db._connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM artifacts").fetchone()[0] == 0


def test_promotion_missing_assignment_records_one_refusal_and_no_artifact(tmp_path):
    """E2: no exact OWNER assignment still leaves a terminal parent receipt."""
    db = Database(tmp_path / "promotion-missing-assignment.db")
    _accepted_meeting_decision(db, "dec-missing")
    from holdspeak.kernel.runtime import _configure
    broker = _configure(db)
    owner = Principal(PrincipalKind.OWNER, "promotion-owner")

    with pytest.raises(ConflictError) as refused:
        asyncio.run(DecisionLifecycleService(db, kernel=broker).draft_promoted_with_model(
            owner, "dec-missing", "note", {}
        ))

    assert refused.value.code == "decision_promotion_draft_refused"
    assert refused.value.context["parent_receipt"]["outcome"] == "refused"
    with db._connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM kernel_parent_runs").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM inference_parent_route_bundles").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM inference_route_plans").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM kernel_operations WHERE name='inference.invoke'").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM artifacts").fetchone()[0] == 0

    # E-F2: creating exact authority after a refusal repairs the same decision
    # revision instead of replaying its zero-budget refusal parent.
    from holdspeak.services.inference_assignment_service import InferenceAssignmentService
    from tests.unit.test_phase143_inference_assignments import OWNER as ASSIGNMENT_OWNER, _profile
    with db._connection() as conn:
        conn.execute(
            "INSERT INTO meetings (id, started_at, title) VALUES (?, ?, ?)",
            ("meeting-127", "2026-08-07T00:00:00+00:00", "Promotion retry"),
        )
    _profile(db, "promotion-retry")
    InferenceAssignmentService(db).set_assignment(ASSIGNMENT_OWNER, {
        "command_id": "assign-promotion-retry", "expected_revision": 0,
        "scope": {"kind": "capability", "capability_id": "decision.promotion_draft"},
        "entries": [{"profile_id": "promotion-retry", "profile_revision": 1}],
    })
    calls: list[str] = []

    class Engine:
        def run_prompt(self, **_):
            calls.append("physical")
            return "Recovered from missing assignment."

    broker.inference_runner._engine_factory = lambda _revision, **_kw: Engine()
    recovered = asyncio.run(DecisionLifecycleService(db, kernel=broker).draft_promoted_with_model(
        owner, "dec-missing", "note", {}
    ))
    assert calls == ["physical"]
    assert recovered["artifact"] is not None
    assert recovered["parent_receipt"]["outcome"] == "succeeded"


def test_promotion_known_preflight_failure_stays_failed_at_owner_parent(tmp_path):
    """E-F4 through a shared OWNER adopter: only uncertainty is indeterminate."""
    from holdspeak.kernel.runtime import _configure
    from holdspeak.services.inference_assignment_service import InferenceAssignmentService
    from tests.unit.test_phase143_inference_assignments import OWNER as ASSIGNMENT_OWNER, _profile

    db = Database(tmp_path / "promotion-known-unavailable.db")
    with db._connection() as conn:
        conn.execute(
            "INSERT INTO meetings (id, started_at, title) VALUES (?, ?, ?)",
            ("meeting-127", "2026-08-07T00:00:00+00:00", "Known unavailable"),
        )
    _accepted_meeting_decision(db, "dec-known-unavailable")
    _profile(db, "promotion-unavailable", ready=False)
    InferenceAssignmentService(db).set_assignment(ASSIGNMENT_OWNER, {
        "command_id": "assign-promotion-unavailable", "expected_revision": 0,
        "scope": {"kind": "capability", "capability_id": "decision.promotion_draft"},
        "entries": [{"profile_id": "promotion-unavailable", "profile_revision": 1}],
    })
    broker = _configure(db)
    owner = Principal(PrincipalKind.OWNER, "promotion-owner")
    with pytest.raises(ConflictError) as refused:
        asyncio.run(DecisionLifecycleService(db, kernel=broker).draft_promoted_with_model(
            owner, "dec-known-unavailable", "note", {}
        ))
    assert refused.value.code == "decision_promotion_draft_refused"
    assert refused.value.context["parent_receipt"]["outcome"] == "failed"
    with db._connection() as conn:
        route = conn.execute(
            "SELECT terminal_outcome FROM inference_route_executions"
        ).fetchone()
        assert conn.execute("SELECT COUNT(*) FROM inference_route_attempts").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM kernel_operations WHERE name='inference.invoke'").fetchone()[0] == 0
    assert route["terminal_outcome"] == "failed"


def test_promotion_request_target_override_is_named_terminal_refusal(tmp_path):
    """E3: the body target neither retargets nor vanishes silently."""
    db = Database(tmp_path / "promotion-retired-override.db")
    _accepted_meeting_decision(db, "dec-override")
    from holdspeak.kernel.runtime import _configure
    broker = _configure(db)
    owner = Principal(PrincipalKind.OWNER, "promotion-owner")

    with pytest.raises(ConflictError) as refused:
        asyncio.run(DecisionLifecycleService(db, kernel=broker).draft_promoted_with_model(
            owner, "dec-override", "note", {"inference_target_id": "legacy-target"}
        ))

    assert refused.value.code == "inference_request_target_override_retired"
    assert refused.value.context["parent_receipt"]["outcome"] == "refused"
    with db._connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM inference_parent_route_bundles").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM inference_route_plans").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM kernel_operations WHERE name='inference.invoke'").fetchone()[0] == 0


def test_promotion_refusal_identity_never_seals_or_relabels_the_routed_request(tmp_path):
    """E-F2 via the product service: refusal and executable identities diverge."""
    from holdspeak.kernel.runtime import _configure
    from holdspeak.services.inference_assignment_service import InferenceAssignmentService
    from tests.unit.test_phase143_inference_assignments import OWNER as ASSIGNMENT_OWNER, _profile

    db = Database(tmp_path / "promotion-refusal-identity.db")
    with db._connection() as conn:
        conn.execute(
            "INSERT INTO meetings (id, started_at, title) VALUES (?, ?, ?)",
            ("meeting-127", "2026-08-07T00:00:00+00:00", "Promotion identity"),
        )
    _accepted_meeting_decision(db, "dec-repair")
    _accepted_meeting_decision(db, "dec-success")
    _profile(db, "promotion-route")
    InferenceAssignmentService(db).set_assignment(ASSIGNMENT_OWNER, {
        "command_id": "assign-promotion-route", "expected_revision": 0,
        "scope": {"kind": "capability", "capability_id": "decision.promotion_draft"},
        "entries": [{"profile_id": "promotion-route", "profile_revision": 1}],
    })
    broker = _configure(db)
    physical: list[str] = []

    class Engine:
        def run_prompt(self, **_):
            physical.append("physical")
            return "A routed promotion draft."

    broker.inference_runner._engine_factory = lambda _revision, **_kw: Engine()
    owner = Principal(PrincipalKind.OWNER, "promotion-owner")
    service = DecisionLifecycleService(db, kernel=broker)

    # A retired override creates one refusal, but a blank retry of the same
    # decision revision gets its own executable parent and physical child.
    with pytest.raises(ConflictError) as first_refusal:
        asyncio.run(service.draft_promoted_with_model(
            owner, "dec-repair", "note", {"inference_target_id": "retired"}
        ))
    repaired = asyncio.run(service.draft_promoted_with_model(owner, "dec-repair", "note", {}))
    assert first_refusal.value.code == "inference_request_target_override_retired"
    assert first_refusal.value.context["parent_receipt"]["outcome"] == "refused"
    assert repaired["parent_receipt"]["outcome"] == "succeeded"
    assert repaired["parent_receipt"]["receipt_id"] != first_refusal.value.context["parent_receipt"]["receipt_id"]

    # Conversely an already succeeded execution cannot be returned as a stale
    # override's refusal receipt.
    succeeded = asyncio.run(service.draft_promoted_with_model(owner, "dec-success", "note", {}))
    with pytest.raises(ConflictError) as stale_refusal:
        asyncio.run(service.draft_promoted_with_model(
            owner, "dec-success", "note", {"inference_target_id": "retired"}
        ))
    assert stale_refusal.value.code == "inference_request_target_override_retired"
    assert stale_refusal.value.context["parent_receipt"]["outcome"] == "refused"
    assert stale_refusal.value.context["parent_receipt"]["receipt_id"] != succeeded["parent_receipt"]["receipt_id"]
    # Exact valid replay preserves the single physical operation/artifact.
    replay = asyncio.run(service.draft_promoted_with_model(owner, "dec-success", "note", {}))
    assert replay["artifact"]["id"] == succeeded["artifact"]["id"]
    assert physical == ["physical", "physical"]
    with db._connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM artifacts").fetchone()[0] == 2
        assert conn.execute("SELECT COUNT(*) FROM inference_route_attempts").fetchone()[0] == 2


def test_promotion_assignment_freeze_uses_elected_draft_only(tmp_path, monkeypatch):
    db = Database(tmp_path / "promotion-frozen-assignment.db")
    with db._connection() as conn:
        conn.execute(
            "INSERT INTO meetings (id, started_at, title) VALUES (?, ?, ?)",
            ("meeting-127", "2026-08-07T00:00:00+00:00", "Frozen assignment"),
        )
    _accepted_meeting_decision(db, "dec-frozen")
    from holdspeak.services.inference_assignment_service import InferenceAssignmentService
    from tests.unit.test_phase143_inference_assignments import OWNER as ASSIGNMENT_OWNER, _profile
    _profile(db, "promotion-initial")
    _profile(db, "promotion-edited")
    assignments = InferenceAssignmentService(db)
    assignments.set_assignment(ASSIGNMENT_OWNER, {
        "command_id": "assign-promotion-initial", "expected_revision": 0,
        "scope": {"kind": "capability", "capability_id": "decision.promotion_draft"},
        "entries": [{"profile_id": "promotion-initial", "profile_revision": 1}],
    })
    from holdspeak.kernel.runtime import _configure
    broker = _configure(db)
    broker.inference_runner._engine_factory = lambda _revision, **_kw: type(
        "Intel", (), {"run_prompt": lambda self, **_: "only elected draft"}
    )()
    owner = Principal(PrincipalKind.OWNER, "promotion-owner")
    real_admit = broker.inference_adoption_service.admit_on_frozen_route

    def admit_after_edit(*args, **kwargs):
        assignments.set_assignment(ASSIGNMENT_OWNER, {
            "command_id": "replace-promotion-route", "expected_revision": 1,
            "scope": {"kind": "capability", "capability_id": "decision.promotion_draft"},
            "entries": [{"profile_id": "promotion-edited", "profile_revision": 1}],
        })
        return real_admit(*args, **kwargs)

    monkeypatch.setattr(broker.inference_adoption_service, "admit_on_frozen_route", admit_after_edit)
    result = asyncio.run(DecisionLifecycleService(db, kernel=broker).draft_promoted_with_model(
        owner, "dec-frozen", "note", {}
    ))

    assert result["artifact"]["body_markdown"] == "only elected draft"
    assert result["placement"]["egress"] == {"scope": "local"}
    with db._connection() as conn:
        assert [row[0] for row in conn.execute(
            "SELECT profile_id FROM inference_route_plan_entries"
        ).fetchall()] == ["promotion-initial"]
