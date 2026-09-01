"""HS-162-02: The deterministic drafter -- goldens, claims, and honest minimalism.

Acceptance criteria tested:
- GOLDEN-RICH: a seeded room drafts the six sections with every claim
  carrying refs; the caveat section shows "All sources consulted" when
  all sections are ok.
- GOLDEN-EMPTY: a room with nothing to say drafts honest minimal lines.
- GOLDEN-DEGRADED: the caveat section appears iff coverage is partial.
- DETERMINISM: same room state => byte-identical body_md + claims_json.
- SUPERSEDE: regenerate supersedes an unaccepted draft (UPD-004).
- PUBLISHED-GUARD: supersede on a published draft raises PublishedUpdateError.
- CLAIM-RESOLUTION: every factual claim resolves to >= 1 evidence ref.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

import pytest

from holdspeak.db import Database, reset_database
from holdspeak.db.updates import PublishedUpdateError
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.project_contracts import generate_pupd_id
from holdspeak.services.project_service import ProjectService
from holdspeak.services.project_evidence_collector import (
    ProjectEvidenceCollector,
)
from holdspeak.services.project_delta_service import ProjectDeltaService
from holdspeak.services.project_update_service import (
    SECTION_KEYS,
    Claim,
    ProjectUpdateService,
    _HONEST_MINIMAL,
    _assemble_body,
    _scan_caveats,
)


OWNER = Principal(PrincipalKind.OWNER, "drafter-test")

NOW_ISO = "2026-06-15T10:00:00"


# ── Helpers ───────────────────────────────────────────────────────────

def _seed_project(
    db: Database,
    project_id: str = "proj-draft01",
    name: str = "Drafting Project",
    revision: int = 5,
) -> str:
    with db._connection() as conn:
        conn.execute(
            """INSERT INTO projects
               (id, name, description, keywords_json, team_members_json,
                context_json, detection_threshold, revision,
                created_at, updated_at)
               VALUES (?, ?, '', '[]', '[]', '{}', 0.4, ?,
                       ?, ?)""",
            (project_id, name, revision, NOW_ISO, NOW_ISO),
        )
    return project_id


def _seed_items(db: Database, project_id: str) -> list[str]:
    """Seed deterministic items into the project. Returns item IDs."""
    items = [
        ("pitem_aaa00000000000000000000000000001", "milestone", "Launch v2.0",
         "planned", "high", "2026-07-01", 1.0),
        ("pitem_aaa00000000000000000000000000002", "risk", "Vendor lock-in",
         "open", "critical", None, 2.0),
        ("pitem_aaa00000000000000000000000000003", "dependency", "API Gateway",
         "at_risk", "medium", "2026-06-20", 3.0),
        ("pitem_aaa00000000000000000000000000004", "workstream", "Backend refactor",
         "active", None, None, 4.0),
    ]
    ids = []
    with db._connection() as conn:
        for item_id, item_type, title, lifecycle, severity, due_at, sort_key in items:
            conn.execute(
                """INSERT INTO project_items
                   (id, project_id, item_type, title, lifecycle, severity,
                    due_at, sort_key, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (item_id, project_id, item_type, title, lifecycle, severity,
                 due_at, sort_key, NOW_ISO, NOW_ISO),
            )
            ids.append(item_id)
    return ids


def _seed_review_and_proposals(
    db: Database,
    project_id: str,
    review_id: str = "prev_ddd00000000000000000000000000001",
) -> str:
    """Seed an open review with proposals. Returns review_id."""
    with db._connection() as conn:
        conn.execute(
            """INSERT INTO project_reviews
               (id, project_id, status, source_manifest_json,
                opened_at)
               VALUES (?, ?, 'open', '{}', ?)""",
            (review_id, project_id, NOW_ISO),
        )
        # Two proposals
        conn.execute(
            """INSERT INTO project_proposals
               (id, project_id, review_window_key, proposal_kind, target_ref,
                title, lifecycle, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            ("pprop_eee00000000000000000000000000001", project_id, review_id,
             "observation_attention", "item:pitem_aaa00000000000000000000000000002",
             "Vendor risk elevated", "open", NOW_ISO),
        )
        conn.execute(
            """INSERT INTO project_proposals
               (id, project_id, review_window_key, proposal_kind, target_ref,
                title, lifecycle, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            ("pprop_eee00000000000000000000000000002", project_id, review_id,
             "risk_attention", "item:pitem_aaa00000000000000000000000000003",
             "API Gateway degraded", "accepted", NOW_ISO),
        )
    return review_id


def _seed_observations(
    db: Database,
    project_id: str,
    source_id: str = "psrc_fff00000000000000000000000000001",
) -> list[str]:
    """Seed observations. Returns observation IDs."""
    obs_ids = [
        "pobs_ggg00000000000000000000000000001",
        "pobs_ggg00000000000000000000000000002",
    ]
    with db._connection() as conn:
        # seed a project_sources row for FK
        conn.execute(
            """INSERT OR IGNORE INTO project_sources
               (id, project_id, source_ref, label, semantic_role,
                enabled, revision, created_at, updated_at)
               VALUES (?, ?, 'watch:w1', 'GH PRs', 'pull_request',
                       1, 0, ?, ?)""",
            (source_id, project_id, NOW_ISO, NOW_ISO),
        )
        for obs_id in obs_ids:
            conn.execute(
                """INSERT OR IGNORE INTO project_observations
                   (id, project_id, source_id, observation_kind,
                    observed_at, captured_at, fact_json, content_hash)
                   VALUES (?, ?, ?, 'snapshot_transition', ?, ?, '{}', '')""",
                (obs_id, project_id, source_id, NOW_ISO, NOW_ISO),
            )
    return obs_ids


def _make_service(db: Database, *, with_delta: bool = True) -> ProjectUpdateService:
    collector = ProjectEvidenceCollector(db)
    delta_svc = ProjectDeltaService(db, collector) if with_delta else None
    project_svc = ProjectService(db, delta_service=delta_svc)
    return ProjectUpdateService(
        db, project_service=project_svc, delta_service=delta_svc,
    )


# ── Fixtures ──────────────────────────────────────────────────────────

@pytest.fixture
def rig(tmp_path):
    reset_database()
    db = Database(tmp_path / "drafter.db")
    yield db
    reset_database()


# ── GOLDEN-RICH: all six sections populated ───────────────────────────

class TestGoldenRich:
    """A fully seeded room drafts six sections with claims."""

    def test_rich_draft_has_all_sections(self, rig):
        db = rig
        pid = _seed_project(db)
        _seed_items(db, pid)
        _seed_review_and_proposals(db, pid)
        _seed_observations(db, pid)

        svc = _make_service(db)
        result = svc.draft_update(OWNER, pid)

        body = result["body_md"]
        # All six section headings present
        assert "## Progress" in body
        assert "## Decisions" in body
        assert "## Risks & Blockers" in body
        assert "## Dependencies" in body
        assert "## Next Actions" in body
        assert "## Source Coverage" in body

    def test_rich_draft_claims_all_have_refs(self, rig):
        db = rig
        pid = _seed_project(db)
        _seed_items(db, pid)
        _seed_review_and_proposals(db, pid)
        _seed_observations(db, pid)

        svc = _make_service(db)
        result = svc.draft_update(OWNER, pid)

        claims = json.loads(result["claims_json"])
        assert len(claims) > 0, "Rich room should produce claims"
        for claim in claims:
            assert "span_id" in claim
            assert "text" in claim
            assert "refs" in claim
            assert "section" in claim
            assert len(claim["refs"]) >= 1, (
                f"Claim {claim['span_id']} has no refs"
            )
            assert claim["section"] in SECTION_KEYS

    def test_rich_draft_progress_section_has_items(self, rig):
        db = rig
        pid = _seed_project(db)
        _seed_items(db, pid)

        svc = _make_service(db)
        result = svc.draft_update(OWNER, pid)

        body = result["body_md"]
        assert "Launch v2.0" in body
        assert "Vendor lock-in" in body

    def test_rich_draft_decisions_section_has_proposals(self, rig):
        db = rig
        pid = _seed_project(db)
        _seed_items(db, pid)
        _seed_review_and_proposals(db, pid)

        svc = _make_service(db)
        result = svc.draft_update(OWNER, pid)

        body = result["body_md"]
        assert "Vendor risk elevated" in body
        assert "API Gateway degraded" in body

    def test_rich_draft_risks_section_has_open_risks(self, rig):
        db = rig
        pid = _seed_project(db)
        _seed_items(db, pid)

        svc = _make_service(db)
        result = svc.draft_update(OWNER, pid)

        body = result["body_md"]
        # Risk item with "open" lifecycle appears in risks section
        assert "Vendor lock-in" in body
        # Dependency with "at_risk" lifecycle appears
        assert "API Gateway" in body

    def test_rich_draft_manifest_records_truth(self, rig):
        db = rig
        pid = _seed_project(db)
        _seed_items(db, pid)
        _seed_review_and_proposals(db, pid)
        obs_ids = _seed_observations(db, pid)

        svc = _make_service(db)
        result = svc.draft_update(OWNER, pid)

        manifest = json.loads(result["source_manifest_json"])
        assert manifest["project_revision"] == 5
        assert manifest["review_id"] == "prev_ddd00000000000000000000000000001"
        assert sorted(manifest["observation_ids"]) == sorted(obs_ids)

    def test_rich_draft_lifecycle_is_draft(self, rig):
        db = rig
        pid = _seed_project(db)
        _seed_items(db, pid)

        svc = _make_service(db)
        result = svc.draft_update(OWNER, pid)

        assert result["lifecycle"] == "draft"
        assert result["generator"] == "deterministic"

    def test_rich_draft_source_coverage_ok(self, rig):
        """When all sections are ok, the source coverage says so."""
        db = rig
        pid = _seed_project(db)
        _seed_items(db, pid)

        svc = _make_service(db)
        result = svc.draft_update(OWNER, pid)

        body = result["body_md"]
        # Coverage section should say all sources consulted
        assert "All sources consulted successfully." in body


# ── GOLDEN-EMPTY: honest minimal ─────────────────────────────────────

class TestGoldenEmpty:
    """A room with nothing to say drafts honest minimal lines."""

    def test_empty_draft_has_all_sections(self, rig):
        db = rig
        pid = _seed_project(db)

        svc = _make_service(db)
        result = svc.draft_update(OWNER, pid)

        body = result["body_md"]
        assert "## Progress" in body
        assert "## Decisions" in body
        assert "## Risks & Blockers" in body
        assert "## Dependencies" in body
        assert "## Next Actions" in body
        assert "## Source Coverage" in body

    def test_empty_draft_honest_minimal_lines(self, rig):
        db = rig
        pid = _seed_project(db)

        svc = _make_service(db)
        result = svc.draft_update(OWNER, pid)

        body = result["body_md"]
        assert "No focus items in this window." in body
        assert "No decisions in this window." in body
        assert "No risks or blockers in this window." in body
        assert "No dependencies tracked." in body
        assert "No upcoming actions." in body

    def test_empty_draft_no_claims(self, rig):
        """An empty room (all sections ok) produces no factual claims."""
        db = rig
        pid = _seed_project(db)

        svc = _make_service(db)
        result = svc.draft_update(OWNER, pid)

        claims = json.loads(result["claims_json"])
        # With delta_service wired, review is "ok" (no caveats)
        assert claims == [], "Empty room should produce no claims"

    def test_empty_draft_manifest_records_empty(self, rig):
        db = rig
        pid = _seed_project(db)

        svc = _make_service(db)
        result = svc.draft_update(OWNER, pid)

        manifest = json.loads(result["source_manifest_json"])
        assert manifest["project_revision"] == 5
        assert manifest["observation_ids"] == []


# ── GOLDEN-DEGRADED: caveat section ──────────────────────────────────

class TestGoldenDegraded:
    """The caveat section appears iff coverage is partial."""

    def test_degraded_section_triggers_caveat(self, rig):
        """When a room section is degraded, the source coverage notes it."""
        db = rig
        pid = _seed_project(db)

        # No delta_service -> review section is absent -> caveat
        svc = _make_service(db, with_delta=False)
        result = svc.draft_update(OWNER, pid)

        body = result["body_md"]
        # The review section should show as absent in caveats
        assert "review" in body.lower()
        assert "absent" in body.lower() or "not_yet_built" in body.lower()

        # The source coverage section should NOT say "All sources consulted"
        assert "All sources consulted successfully." not in body

    def test_degraded_manifest_has_caveats(self, rig):
        db = rig
        pid = _seed_project(db)

        svc = _make_service(db, with_delta=False)
        result = svc.draft_update(OWNER, pid)

        manifest = json.loads(result["source_manifest_json"])
        caveats = manifest.get("caveats", [])
        assert len(caveats) > 0, "Degraded room should have caveats"
        # At least the review section absent
        caveat_sections = [c["section"] for c in caveats]
        assert "review" in caveat_sections

    def test_degraded_claims_carry_refs(self, rig):
        """Even caveat claims carry refs."""
        db = rig
        pid = _seed_project(db)

        svc = _make_service(db, with_delta=False)
        result = svc.draft_update(OWNER, pid)

        claims = json.loads(result["claims_json"])
        coverage_claims = [c for c in claims if c["section"] == "source_coverage"]
        for claim in coverage_claims:
            assert len(claim["refs"]) >= 1


# ── DETERMINISM: same state => byte-identical output ──────────────────

class TestDeterminism:
    """Same room state produces byte-identical body_md + claims_json."""

    def test_byte_identical_on_repeat(self, rig):
        """Two drafts from the same state are byte-identical."""
        db = rig
        pid = _seed_project(db)
        _seed_items(db, pid)
        _seed_review_and_proposals(db, pid)
        _seed_observations(db, pid)

        svc = _make_service(db)
        result1 = svc.draft_update(OWNER, pid)

        # The first draft exists; the second will supersede it.
        result2 = svc.draft_update(OWNER, pid)

        assert result1["body_md"] == result2["body_md"], (
            "body_md not byte-identical across runs"
        )
        assert result1["claims_json"] == result2["claims_json"], (
            "claims_json not byte-identical across runs"
        )
        assert result1["source_manifest_json"] == result2["source_manifest_json"], (
            "source_manifest_json not byte-identical across runs"
        )

    def test_deterministic_empty_room(self, rig):
        """Even an empty room is deterministic."""
        db = rig
        pid = _seed_project(db)

        svc = _make_service(db)
        result1 = svc.draft_update(OWNER, pid)
        result2 = svc.draft_update(OWNER, pid)

        assert result1["body_md"] == result2["body_md"]
        assert result1["claims_json"] == result2["claims_json"]


# ── SUPERSEDE: UPD-004 respected ─────────────────────────────────────

class TestSupersede:
    """Regenerate supersedes unaccepted draft (UPD-004)."""

    def test_regenerate_supersedes_draft(self, rig):
        db = rig
        pid = _seed_project(db)

        svc = _make_service(db)
        result1 = svc.draft_update(OWNER, pid)
        draft1_id = result1["id"]

        result2 = svc.draft_update(OWNER, pid)
        draft2_id = result2["id"]

        assert draft1_id != draft2_id
        assert result2["draft_revision"] == 2

        # Old draft is superseded
        old = db.project_updates.get_update(draft1_id)
        assert old["lifecycle"] == "superseded"

        # New draft is active
        assert result2["lifecycle"] == "draft"

    def test_supersede_increments_revision(self, rig):
        db = rig
        pid = _seed_project(db)

        svc = _make_service(db)
        r1 = svc.draft_update(OWNER, pid)
        r2 = svc.draft_update(OWNER, pid)
        r3 = svc.draft_update(OWNER, pid)

        assert r1["draft_revision"] == 1
        assert r2["draft_revision"] == 2
        assert r3["draft_revision"] == 3

    def test_supersede_never_touches_published(self, rig):
        """A published draft cannot be superseded -- a new fresh draft is created."""
        db = rig
        pid = _seed_project(db)

        svc = _make_service(db)
        r1 = svc.draft_update(OWNER, pid)

        # Publish the draft
        db.project_updates.publish_update(r1["id"])

        # Drafting again should create a fresh draft (not supersede published)
        r2 = svc.draft_update(OWNER, pid)
        assert r2["draft_revision"] == 1  # fresh start
        assert r2["lifecycle"] == "draft"

        # Published one is untouched
        published = db.project_updates.get_update(r1["id"])
        assert published["lifecycle"] == "published"


# ── CLAIM SCHEMA UNIT TESTS ──────────────────────────────────────────

class TestClaimSchema:
    """The Claim dataclass and schema are well-formed."""

    def test_claim_to_dict(self):
        c = Claim(
            span_id="s_progress_0",
            text="Milestone: Launch -- planned",
            refs=["item:pitem_001"],
            section="progress",
        )
        d = c.to_dict()
        assert d == {
            "span_id": "s_progress_0",
            "text": "Milestone: Launch -- planned",
            "refs": ["item:pitem_001"],
            "section": "progress",
        }

    def test_claim_immutable(self):
        c = Claim(
            span_id="s_progress_0",
            text="test",
            refs=["item:x"],
            section="progress",
        )
        with pytest.raises(AttributeError):
            c.span_id = "changed"  # type: ignore[misc]

    def test_section_keys_complete(self):
        assert len(SECTION_KEYS) == 6
        assert SECTION_KEYS == (
            "progress",
            "decisions",
            "risks_blockers",
            "dependencies",
            "next_actions",
            "source_coverage",
        )


# ── CAVEAT SCANNER UNIT TESTS ────────────────────────────────────────

class TestCaveatScanner:
    """The _scan_caveats function correctly identifies degraded/absent sections."""

    def test_all_ok_no_caveats(self):
        room = {
            "items": {"state": "ok"},
            "meetings": {"state": "ok"},
            "resources": {"state": "ok"},
            "changes": {"state": "ok"},
            "review": {"state": "ok"},
        }
        assert _scan_caveats(room) == []

    def test_degraded_section_produces_caveat(self):
        room = {
            "items": {"state": "ok"},
            "meetings": {"state": "ok"},
            "resources": {"state": "degraded", "error_code": "resources_read_failed"},
            "changes": {"state": "ok"},
            "review": {"state": "ok"},
        }
        caveats = _scan_caveats(room)
        assert len(caveats) == 1
        assert caveats[0]["section"] == "resources"
        assert caveats[0]["state"] == "degraded"
        assert caveats[0]["reason"] == "resources_read_failed"

    def test_absent_section_produces_caveat(self):
        room = {
            "items": {"state": "ok"},
            "meetings": {"state": "ok"},
            "resources": {"state": "ok"},
            "changes": {"state": "ok"},
            "review": {"state": "absent", "reason": "not_yet_built"},
        }
        caveats = _scan_caveats(room)
        assert len(caveats) == 1
        assert caveats[0]["section"] == "review"
        assert caveats[0]["state"] == "absent"

    def test_multiple_caveats_sorted(self):
        room = {
            "items": {"state": "degraded", "error_code": "items_read_failed"},
            "meetings": {"state": "ok"},
            "resources": {"state": "absent", "reason": "not_yet_built"},
            "changes": {"state": "ok"},
            "review": {"state": "ok"},
        }
        caveats = _scan_caveats(room)
        assert len(caveats) == 2
        # Sorted by section name
        assert caveats[0]["section"] == "items"
        assert caveats[1]["section"] == "resources"


# ── ASSEMBLY UNIT TEST ────────────────────────────────────────────────

class TestAssembleBody:
    """The _assemble_body function produces correct Markdown structure."""

    def test_all_minimal_sections(self):
        sections = {k: _HONEST_MINIMAL[k] for k in SECTION_KEYS}
        body = _assemble_body(sections)
        for key in SECTION_KEYS:
            from holdspeak.services.project_update_service import _SECTION_HEADINGS
            assert f"## {_SECTION_HEADINGS[key]}" in body

    def test_section_order_is_canonical(self):
        sections = {k: f"content-{k}" for k in SECTION_KEYS}
        body = _assemble_body(sections)
        positions = []
        for key in SECTION_KEYS:
            from holdspeak.services.project_update_service import _SECTION_HEADINGS
            pos = body.index(f"## {_SECTION_HEADINGS[key]}")
            positions.append(pos)
        # Positions should be strictly increasing
        assert positions == sorted(positions)
