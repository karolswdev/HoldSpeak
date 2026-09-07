"""HS-200-06 (phase200_claim_support): citation, support and acceptance
are three INDEPENDENT axes.

Phase 200 CONTRACTS §C2, proved here:

- A valid reference establishes SOURCE LINKAGE only.  A real but
  irrelevant citation can never mark invented prose supported.
- Observation, inference, proposal and accepted domain decision stay
  distinct on the kind axis.
- A support record names the exact source version and either the
  validation method (deterministic field mapping) or the reviewer.
- Editing a supported sentence invalidates its support and KEEPS its
  provenance (the record, stamped; `verified` untouched).
- Citation-only `verified` records written before this story migrate
  conservatively, with the mapping version recorded, and are never
  presented as reviewed by a human.
- A model score can never move acceptance.
"""
from __future__ import annotations

import json
from typing import Any

import pytest

from holdspeak.db import Database, reset_database
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.project_contracts import generate_pupd_id
from holdspeak.services.errors import NotFound, ValidationError
from holdspeak.services.project_delta_service import ProjectDeltaService
from holdspeak.services.project_evidence_collector import (
    ProjectEvidenceCollector,
)
from holdspeak.services.project_service import ProjectService
from holdspeak.services.project_update_service import (
    ACCEPTANCE_ACCEPTED,
    ACCEPTANCE_REJECTED,
    ACCEPTANCE_UNREVIEWED,
    CLAIM_SUPPORT_MAPPING_VERSION,
    INVALIDATION_TEXT_EDITED,
    KIND_DECISION,
    KIND_INFERENCE,
    KIND_OBSERVATION,
    KIND_PROPOSAL,
    METHOD_FIELD_MAPPING,
    METHOD_REVIEWER,
    SUPPORT_DISPUTED,
    SUPPORT_SOURCE_LINKED,
    SUPPORT_SUPPORTED,
    SUPPORT_UNKNOWN,
    Claim,
    ProjectUpdateService,
    _parse_model_output,
    _typed_unknowns,
    migrate_claims_json,
    migrate_legacy_claim,
)

OWNER = Principal(PrincipalKind.OWNER, "claim-support-test")
AGENT = Principal(PrincipalKind.AGENT, "some-agent")

NOW_ISO = "2026-06-15T10:00:00"


# ── Seeding (mirrors tests/unit/test_update_drafter.py) ───────────────

def _seed_project(
    db: Database,
    project_id: str = "proj-c2-01",
    revision: int = 5,
) -> str:
    with db._connection() as conn:
        conn.execute(
            """INSERT INTO projects
               (id, name, description, keywords_json, team_members_json,
                context_json, detection_threshold, revision,
                created_at, updated_at)
               VALUES (?, 'C2 Project', '', '[]', '[]', '{}', 0.4, ?, ?, ?)""",
            (project_id, revision, NOW_ISO, NOW_ISO),
        )
    return project_id


def _seed_items(db: Database, project_id: str) -> None:
    items = [
        ("pitem_c200000000000000000000000000001", "milestone", "Launch v2.0",
         "planned", "high", "2026-07-01", 1.0),
        ("pitem_c200000000000000000000000000002", "risk", "Vendor lock-in",
         "open", "critical", None, 2.0),
        ("pitem_c200000000000000000000000000003", "dependency", "API Gateway",
         "at_risk", "medium", "2026-06-20", 3.0),
    ]
    with db._connection() as conn:
        for item_id, kind, title, lifecycle, severity, due_at, sort_key in items:
            conn.execute(
                """INSERT INTO project_items
                   (id, project_id, item_type, title, lifecycle, severity,
                    due_at, sort_key, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (item_id, project_id, kind, title, lifecycle, severity,
                 due_at, sort_key, NOW_ISO, NOW_ISO),
            )


def _seed_review_and_proposals(
    db: Database,
    project_id: str,
    review_id: str = "prev_c2000000000000000000000000001",
) -> str:
    with db._connection() as conn:
        conn.execute(
            """INSERT INTO project_reviews
               (id, project_id, status, source_manifest_json, opened_at)
               VALUES (?, ?, 'open', '{}', ?)""",
            (review_id, project_id, NOW_ISO),
        )
        conn.execute(
            """INSERT INTO project_proposals
               (id, project_id, review_window_key, proposal_kind, target_ref,
                title, lifecycle, created_at)
               VALUES (?, ?, ?, 'observation_attention',
                       'item:pitem_c200000000000000000000000000002',
                       'Vendor risk elevated', 'open', ?)""",
            ("pprop_c2000000000000000000000000001", project_id, review_id,
             NOW_ISO),
        )
        conn.execute(
            """INSERT INTO project_proposals
               (id, project_id, review_window_key, proposal_kind, target_ref,
                title, lifecycle, decided_by_ref, created_at)
               VALUES (?, ?, ?, 'risk_attention',
                       'item:pitem_c200000000000000000000000000003',
                       'API Gateway degraded', 'accepted',
                       'principal:owner', ?)""",
            ("pprop_c2000000000000000000000000002", project_id, review_id,
             NOW_ISO),
        )
        conn.execute(
            """INSERT INTO project_proposals
               (id, project_id, review_window_key, proposal_kind, target_ref,
                title, lifecycle, created_at)
               VALUES (?, ?, ?, 'observation_attention',
                       'item:pitem_c200000000000000000000000000001',
                       'Launch date questioned', 'dismissed', ?)""",
            ("pprop_c2000000000000000000000000003", project_id, review_id,
             NOW_ISO),
        )
    return review_id


def _make_service(db: Database) -> ProjectUpdateService:
    collector = ProjectEvidenceCollector(db)
    delta_svc = ProjectDeltaService(db, collector)
    project_svc = ProjectService(db, delta_service=delta_svc)
    return ProjectUpdateService(
        db, project_service=project_svc, delta_service=delta_svc,
    )


def _claims(update: dict[str, Any]) -> list[dict[str, Any]]:
    return json.loads(update["claims_json"])


def _by_span(update: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {c["span_id"]: c for c in _claims(update)}


@pytest.fixture
def rig(tmp_path):
    reset_database()
    db = Database(tmp_path / "claim-support.db")
    yield db
    reset_database()


# ── A REAL BUT IRRELEVANT CITATION ───────────────────────────────────

class TestIrrelevantCitation:
    """A valid reference buys SOURCE LINKAGE and nothing more."""

    INVENTORY = frozenset({"item:pitem_real_001"})
    TEXTS = {
        "item:pitem_real_001":
            "Dependency [medium]: API Gateway -- at_risk",
    }

    def _parse(self, text: str, refs: list[str]):
        raw = json.dumps({"sections": [{
            "key": "progress",
            "sentences": [{"text": text, "cited_refs": refs}],
        }]})
        result = _parse_model_output(raw, self.INVENTORY, self.TEXTS)
        assert result is not None
        _, claims = result
        return claims[0]

    def test_irrelevant_citation_never_supports_invented_prose(self):
        claim = self._parse(
            "Marketing signed off on the rollout.", ["item:pitem_real_001"],
        )
        assert claim.support == SUPPORT_SOURCE_LINKED
        assert claim.support != SUPPORT_SUPPORTED
        assert claim.refs == ["item:pitem_real_001"]
        assert claim.acceptance == ACCEPTANCE_UNREVIEWED

    def test_invented_owner_lands_as_a_typed_unknown(self):
        claim = self._parse(
            "The gateway work is owned by Priya.", ["item:pitem_real_001"],
        )
        assert claim.support == SUPPORT_SOURCE_LINKED
        assert {"type": "name", "value": "Priya"} in claim.unknowns

    def test_altered_figure_lands_as_a_typed_unknown(self):
        claim = self._parse(
            "API Gateway is 95% complete.", ["item:pitem_real_001"],
        )
        assert claim.support == SUPPORT_SOURCE_LINKED
        assert {"type": "number", "value": "95%"} in claim.unknowns

    def test_invented_deadline_lands_as_a_typed_unknown(self):
        claim = self._parse(
            "API Gateway lands on 2026-12-31.", ["item:pitem_real_001"],
        )
        assert {"type": "deadline", "value": "2026-12-31"} in claim.unknowns

    def test_corroborated_prose_records_no_unknown(self):
        claim = self._parse(
            "API Gateway is at_risk.", ["item:pitem_real_001"],
        )
        assert claim.unknowns == []
        # Still only source-linked: generated prose needs its own check.
        assert claim.support == SUPPORT_SOURCE_LINKED

    def test_mixed_valid_and_invalid_refs_keep_only_the_valid(self):
        claim = self._parse(
            "API Gateway is at_risk.",
            ["item:pitem_real_001", "item:pitem_invented_999"],
        )
        assert claim.refs == ["item:pitem_real_001"]
        assert claim.support == SUPPORT_SOURCE_LINKED

    def test_no_valid_ref_leaves_support_unknown(self):
        claim = self._parse(
            "Everything is fine.", ["item:pitem_invented_999"],
        )
        assert claim.refs == []
        assert claim.support == SUPPORT_UNKNOWN
        assert claim.verified is False

    def test_model_output_never_moves_acceptance(self):
        for text, refs in (
            ("API Gateway is at_risk.", ["item:pitem_real_001"]),
            ("Everything is fine.", []),
        ):
            assert self._parse(text, refs).acceptance == ACCEPTANCE_UNREVIEWED


class TestTypedUnknowns:
    """The deterministic literal check."""

    def test_number_present_in_source_is_not_unknown(self):
        assert _typed_unknowns("Team shipped 3 items.", "shipped 3 items") == []

    def test_name_present_in_source_is_not_unknown(self):
        assert _typed_unknowns(
            "Launch v2.0 is planned.", "Milestone: Launch v2.0 -- planned",
        ) == []

    def test_unknowns_are_sorted_and_typed(self):
        found = _typed_unknowns(
            "Priya owes 40% by 2026-12-31.", "nothing relevant",
        )
        assert found == [
            {"type": "deadline", "value": "2026-12-31"},
            {"type": "name", "value": "Priya"},
            {"type": "number", "value": "40%"},
        ]

    def test_report_vocabulary_is_not_a_name(self):
        # Grammar and report words are never reported as invented names.
        assert _typed_unknowns("Progress holds. Delivery is open.", "x") == []

    def test_a_sentence_initial_proper_noun_is_still_checked(self):
        # "Priya owes ..." must not hide behind sentence-initial grammar.
        assert _typed_unknowns("Priya owns it.", "nothing") == [
            {"type": "name", "value": "Priya"},
        ]
        assert _typed_unknowns("Priya owns it.", "Priya owns the item") == []


# ── THE FOUR KINDS STAY DISTINCT ─────────────────────────────────────

class TestKindsStayDistinct:
    """Observation, inference, proposal and decision are separate."""

    def test_deterministic_draft_separates_the_kinds(self, rig):
        db = rig
        pid = _seed_project(db)
        _seed_items(db, pid)
        _seed_review_and_proposals(db, pid)
        svc = _make_service(db)

        update = svc.draft_update(OWNER, pid)
        claims = _claims(update)
        kinds = {c["span_id"]: c["kind"] for c in claims}

        decisions = [c for c in claims if c["section"] == "decisions"]
        assert decisions, "the seeded review has proposals"
        by_title = {c["text"]: c for c in decisions}

        accepted = next(
            c for t, c in by_title.items() if t.startswith("API Gateway degraded")
        )
        assert accepted["kind"] == KIND_DECISION
        assert accepted["acceptance"] == ACCEPTANCE_ACCEPTED

        open_prop = next(
            c for t, c in by_title.items() if t.startswith("Vendor risk elevated")
        )
        assert open_prop["kind"] == KIND_PROPOSAL
        assert open_prop["acceptance"] == ACCEPTANCE_UNREVIEWED

        dismissed = next(
            c for t, c in by_title.items() if t.startswith("Launch date questioned")
        )
        assert dismissed["kind"] == KIND_PROPOSAL
        assert dismissed["acceptance"] == ACCEPTANCE_REJECTED

        progress = [c for c in claims if c["section"] == "progress"]
        assert progress
        assert all(kinds[c["span_id"]] == KIND_OBSERVATION for c in progress)

    def test_model_prose_is_an_inference(self):
        raw = json.dumps({"sections": [{
            "key": "progress",
            "sentences": [{"text": "Launch v2.0 is planned.",
                           "cited_refs": ["item:p1"]}],
        }]})
        result = _parse_model_output(
            raw, frozenset({"item:p1"}),
            {"item:p1": "Milestone: Launch v2.0 -- planned"},
        )
        assert result is not None
        _, claims = result
        assert claims[0].kind == KIND_INFERENCE


# ── SUPPORT RECORDS NAME THEIR SOURCE ────────────────────────────────

class TestSupportRecords:
    """A supported claim names the source version and the method."""

    def test_deterministic_claims_name_version_fields_and_method(self, rig):
        db = rig
        pid = _seed_project(db, revision=5)
        _seed_items(db, pid)
        svc = _make_service(db)

        update = svc.draft_update(OWNER, pid)
        claims = _claims(update)
        assert claims
        for claim in claims:
            assert claim["support"] == SUPPORT_SUPPORTED
            record = claim["support_record"]
            assert record["method"] == METHOD_FIELD_MAPPING
            assert record["source_version"] == (
                f"project:{pid}@r{update['project_revision']}"
            )
            assert record["source_refs"] == claim["refs"]
            assert record["fields"], "the mapping names the fields it read"
            # A field mapping is not a person.
            assert "reviewer_ref" not in record or record["reviewer_ref"]

    def test_accepted_decision_names_the_deciding_reviewer(self, rig):
        db = rig
        pid = _seed_project(db)
        _seed_items(db, pid)
        _seed_review_and_proposals(db, pid)
        svc = _make_service(db)

        update = svc.draft_update(OWNER, pid)
        accepted = next(
            c for c in _claims(update)
            if c["text"].startswith("API Gateway degraded")
        )
        assert accepted["support_record"]["reviewer_ref"] == "principal:owner"

    def test_no_wall_clock_in_a_deterministic_draft(self, rig):
        db = rig
        pid = _seed_project(db)
        _seed_items(db, pid)
        svc = _make_service(db)

        first = svc.draft_update(OWNER, pid)
        second = svc.draft_update(OWNER, pid)
        assert first["claims_json"] == second["claims_json"]
        assert "checked_at" not in first["claims_json"]


# ── THE REVIEWER PATH ────────────────────────────────────────────────

class TestReviewerPath:
    """Acceptance is a person's act, recorded with the reviewer."""

    def _drafted(self, db):
        pid = _seed_project(db)
        _seed_items(db, pid)
        svc = _make_service(db)
        return svc, svc.draft_update(OWNER, pid)

    def test_owner_acceptance_names_the_reviewer_and_the_version(self, rig):
        svc, update = self._drafted(rig)
        span = _claims(update)[0]["span_id"]

        after = svc.review_claim(
            OWNER, update["id"], span,
            acceptance=ACCEPTANCE_ACCEPTED, support=SUPPORT_SUPPORTED,
        )
        claim = _by_span(after)[span]
        assert claim["acceptance"] == ACCEPTANCE_ACCEPTED
        assert claim["support"] == SUPPORT_SUPPORTED
        record = claim["support_record"]
        assert record["method"] == METHOD_REVIEWER
        assert record["reviewer_ref"] == "principal:claim-support-test"
        assert record["checked_at"]
        assert record["source_version"].startswith("project:")

    def test_an_agent_can_never_move_acceptance(self, rig):
        svc, update = self._drafted(rig)
        span = _claims(update)[0]["span_id"]
        with pytest.raises(ValidationError) as exc:
            svc.review_claim(
                AGENT, update["id"], span, acceptance=ACCEPTANCE_ACCEPTED,
            )
        assert exc.value.code == "claim_review_forbidden"

    def test_reviewer_cannot_support_a_claim_with_no_source(self, rig):
        db = rig
        pid = _seed_project(db)
        svc = _make_service(db)
        update = svc.draft_update(OWNER, pid)
        # An empty room drafts no claims; write one sourceless claim.
        claim = Claim(
            span_id="s_progress_0", text="Sourceless.", refs=[],
            section="progress", verified=False, support=SUPPORT_UNKNOWN,
        )
        db.project_updates.update_draft(
            update["id"],
            claims_json=json.dumps([claim.to_dict()], sort_keys=True),
        )
        with pytest.raises(ValidationError) as exc:
            svc.review_claim(
                OWNER, update["id"], "s_progress_0", support=SUPPORT_SUPPORTED,
            )
        assert exc.value.code == "claim_support_no_source"

    def test_reviewer_can_dispute(self, rig):
        svc, update = self._drafted(rig)
        span = _claims(update)[0]["span_id"]
        after = svc.review_claim(
            OWNER, update["id"], span, support=SUPPORT_DISPUTED,
        )
        assert _by_span(after)[span]["support"] == SUPPORT_DISPUTED

    def test_unknown_span_is_not_found(self, rig):
        svc, update = self._drafted(rig)
        with pytest.raises(NotFound):
            svc.review_claim(
                OWNER, update["id"], "s_nope_9",
                acceptance=ACCEPTANCE_ACCEPTED,
            )


# ── EDITING INVALIDATES SUPPORT ──────────────────────────────────────

class TestEditInvalidatesSupport:
    """An edited sentence loses support and keeps its provenance."""

    def _drafted(self, db):
        pid = _seed_project(db)
        _seed_items(db, pid)
        svc = _make_service(db)
        return svc, svc.draft_update(OWNER, pid)

    def test_edited_sentence_drops_to_source_linked_and_keeps_the_record(
        self, rig,
    ):
        svc, update = self._drafted(rig)
        before = _claims(update)
        target = before[0]
        assert target["support"] == SUPPORT_SUPPORTED

        edited = update["body_md"].replace(
            target["text"], "Something the owner wrote instead",
        )
        assert edited != update["body_md"]
        saved = svc.save_update(OWNER, update["id"], body_md=edited)

        after = _by_span(saved)[target["span_id"]]
        assert after["support"] == SUPPORT_SOURCE_LINKED
        record = after["support_record"]
        # Provenance intact: the original method, version and refs stay.
        assert record["method"] == METHOD_FIELD_MAPPING
        assert record["source_version"] == (
            target["support_record"]["source_version"]
        )
        assert record["source_refs"] == target["support_record"]["source_refs"]
        assert record["invalidated_at"]
        assert record["invalidation_reason"] == INVALIDATION_TEXT_EDITED
        # `verified` is never rewritten.
        assert after.get("verified") == target.get("verified")

    def test_untouched_sentences_keep_their_support(self, rig):
        svc, update = self._drafted(rig)
        before = _claims(update)
        target, survivor = before[0], before[1]

        edited = update["body_md"].replace(target["text"], "Rewritten line")
        saved = svc.save_update(OWNER, update["id"], body_md=edited)

        after = _by_span(saved)
        assert after[survivor["span_id"]]["support"] == SUPPORT_SUPPORTED
        assert "invalidated_at" not in (
            after[survivor["span_id"]]["support_record"]
        )

    def test_reviewer_support_is_invalidated_by_an_edit_too(self, rig):
        svc, update = self._drafted(rig)
        target = _claims(update)[0]
        span = target["span_id"]
        svc.review_claim(
            OWNER, update["id"], span,
            acceptance=ACCEPTANCE_ACCEPTED, support=SUPPORT_SUPPORTED,
        )
        edited = update["body_md"].replace(target["text"], "Owner rewrote it")
        saved = svc.save_update(OWNER, update["id"], body_md=edited)
        after = _by_span(saved)[span]
        assert after["support"] == SUPPORT_SOURCE_LINKED
        assert after["support_record"]["method"] == METHOD_REVIEWER
        assert after["support_record"]["reviewer_ref"]
        assert after["support_record"]["invalidation_reason"] == (
            INVALIDATION_TEXT_EDITED
        )
        # Acceptance is a separate axis: the edit does not revoke it.
        assert after["acceptance"] == ACCEPTANCE_ACCEPTED

    def test_saving_the_same_body_changes_nothing(self, rig):
        svc, update = self._drafted(rig)
        saved = svc.save_update(
            OWNER, update["id"], body_md=update["body_md"],
        )
        assert saved["claims_json"] == update["claims_json"]


# ── THE CONSERVATIVE MIGRATION OF OLD RECORDS ────────────────────────

_LEGACY_CLAIMS = [
    {
        "refs": ["item:pitem_old_001"],
        "section": "progress",
        "span_id": "s_progress_0",
        "text": "Milestone: Launch -- planned",
    },
    {
        "refs": [],
        "section": "risks_blockers",
        "span_id": "s_risks_blockers_0",
        "text": "Model commentary with no backing.",
        "verified": False,
    },
]


def _seed_legacy_update(
    db: Database,
    project_id: str,
    *,
    generator: str = "deterministic",
) -> str:
    """Write a pre-HS-200-06 row: four-key claims, no axes."""
    update_id = generate_pupd_id()
    db.project_updates.insert_update(
        update_id=update_id,
        project_id=project_id,
        project_revision=5,
        review_id=None,
        draft_revision=1,
        body_md="## Progress\n\n- Milestone: Launch -- planned\n",
        claims_json=json.dumps(_LEGACY_CLAIMS),
        source_manifest_json="{}",
        generator=generator,
    )
    return update_id


class TestLegacyMigration:
    """Citation-only `verified` records map conservatively."""

    def test_citation_only_record_becomes_source_linked_not_supported(self):
        migrated = migrate_legacy_claim(_LEGACY_CLAIMS[0])
        assert migrated["support"] == SUPPORT_SOURCE_LINKED
        assert migrated["support"] != SUPPORT_SUPPORTED
        assert migrated["acceptance"] == ACCEPTANCE_UNREVIEWED
        assert migrated["kind"] == KIND_OBSERVATION
        assert migrated["support_mapping_version"] == (
            CLAIM_SUPPORT_MAPPING_VERSION
        )
        # No support record: nothing here was checked by anyone.
        assert "support_record" not in migrated

    def test_marked_record_becomes_unknown(self):
        migrated = migrate_legacy_claim(_LEGACY_CLAIMS[1])
        assert migrated["support"] == SUPPORT_UNKNOWN
        assert migrated["verified"] is False  # provenance kept verbatim

    def test_a_model_generated_legacy_record_maps_to_inference(self):
        migrated = migrate_legacy_claim(
            _LEGACY_CLAIMS[0], generator="model:assign_1",
        )
        assert migrated["kind"] == KIND_INFERENCE

    def test_migration_is_idempotent_and_leaves_new_claims_alone(self, rig):
        db = rig
        pid = _seed_project(db)
        _seed_items(db, pid)
        svc = _make_service(db)
        update = svc.draft_update(OWNER, pid)
        once = migrate_claims_json(update["claims_json"])
        assert once == update["claims_json"]
        assert migrate_claims_json(once) == once

    def test_reading_an_old_row_shows_the_axes_without_rewriting_history(
        self, rig,
    ):
        db = rig
        pid = _seed_project(db)
        svc = _make_service(db)
        update_id = _seed_legacy_update(db, pid)

        read = svc.get_update(OWNER, update_id)
        claims = {c["span_id"]: c for c in json.loads(read["claims_json"])}
        assert claims["s_progress_0"]["support"] == SUPPORT_SOURCE_LINKED
        assert claims["s_progress_0"]["acceptance"] == ACCEPTANCE_UNREVIEWED
        assert claims["s_progress_0"]["support_mapping_version"] == (
            CLAIM_SUPPORT_MAPPING_VERSION
        )
        assert claims["s_risks_blockers_0"]["support"] == SUPPORT_UNKNOWN

        # The STORED bytes are untouched -- history is not rewritten.
        with db._connection() as conn:
            stored = conn.execute(
                "SELECT claims_json FROM project_updates WHERE id = ?",
                (update_id,),
            ).fetchone()[0]
        assert json.loads(stored) == _LEGACY_CLAIMS

    def test_a_migrated_record_never_claims_a_human_reviewed_it(self, rig):
        db = rig
        pid = _seed_project(db)
        svc = _make_service(db)
        update_id = _seed_legacy_update(db, pid)
        read = svc.get_update(OWNER, update_id)
        for claim in json.loads(read["claims_json"]):
            assert claim["acceptance"] == ACCEPTANCE_UNREVIEWED
            assert claim["support"] != SUPPORT_SUPPORTED
            assert "reviewer_ref" not in json.dumps(claim)

    def test_listing_migrates_too(self, rig):
        db = rig
        pid = _seed_project(db)
        svc = _make_service(db)
        _seed_legacy_update(db, pid)
        rows = svc.list_updates(OWNER, pid)
        assert rows
        for claim in json.loads(rows[0]["claims_json"]):
            assert claim["support"] in (
                SUPPORT_SOURCE_LINKED, SUPPORT_UNKNOWN,
            )

    def test_editing_a_migrated_row_leaves_its_provenance_alone(self, rig):
        db = rig
        pid = _seed_project(db)
        svc = _make_service(db)
        update_id = _seed_legacy_update(db, pid)
        saved = svc.save_update(
            OWNER, update_id, body_md="## Progress\n\n- Owner text\n",
        )
        for claim in json.loads(saved["claims_json"]):
            # Nothing was supported, so nothing is invalidated.
            assert "support_record" not in claim
            assert claim["support"] != SUPPORT_SUPPORTED
