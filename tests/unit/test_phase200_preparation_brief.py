"""HS-200-11 (phase200_preparation_brief): a useful Project preparation brief.

The five criteria, proven headless against a real ``Database`` and the real
``ProjectService.room`` projection:

- AC1: a purpose is enough -- no calendar source exists in the rig and the
  manifest says so from a stored fact.
- AC2: the SOURCE MANIFEST binds what was read (state, observation,
  revision), the current AND superseded decisions carried in, and every
  omission with its reason and repair; it is persisted with the brief and
  reloaded with its sha256 re-verified.
- AC3: the output is BOUNDED -- the ``Outline`` refuses more than the cap,
  the model parser truncates to it, and both drafters produce the same typed
  shape; every sentence carries the three C2 axes.
- AC4: the kept brief stays attached to its Project and lists from it.
- AC5: an unavailable model REFUSES: the purpose comes back in the refusal,
  the route state is named, and the runner is never invoked (no request
  leaves).  No deterministic fallback is silently substituted.

The route mechanics reuse the update drafter's seeded assignment chain
(``tests/unit/test_update_drafter.py``), so the model path here is the model
path the product resolves.
"""
from __future__ import annotations

import json
import re
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest

from holdspeak.db import Database, reset_database
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.errors import ConflictError, NotFound, ValidationError
from holdspeak.services.preparation_brief_service import (
    MAX_OBLIGATIONS,
    MAX_PRIORITIES,
    MAX_QUESTIONS,
    PREPARATION_BRIEF_CAPABILITY,
    ROUTE_KEY_MISSING,
    ROUTE_NOT_SET,
    ROUTE_READY,
    ROUTE_TOKENS,
    ROUTE_UNREACHABLE,
    ROUTE_STOPPED,
    SECTION_SUPERSEDED,
    STATE_AVAILABLE,
    STATE_FAILED,
    STATE_STALE,
    STATE_UNAVAILABLE,
    Outline,
    OutlineEntry,
    PreparationBriefService,
    PreparationRefused,
    build_manifest,
    draft_deterministic,
    manifest_sha256,
    parse_model_output,
)
from holdspeak.services.project_service import ProjectService
from holdspeak.services.project_update_service import (
    Claim,
    ACCEPTANCE_ACCEPTED,
    ACCEPTANCE_SUPERSEDED,
    ACCEPTANCE_UNREVIEWED,
    KIND_DECISION,
    KIND_INFERENCE,
    SUPPORT_SOURCE_LINKED,
    SUPPORT_SUPPORTED,
    SUPPORT_UNKNOWN,
)

from tests.unit.test_update_drafter import _MockBroker, _MockRunner, _seed_assignment

OWNER = Principal(PrincipalKind.OWNER, "prep-brief-test")
NOW = datetime(2026, 9, 7, 9, 12, tzinfo=timezone.utc)
NOW_ISO = "2026-09-07T09:12:00"


# ── the rig ───────────────────────────────────────────────────────────


@pytest.fixture
def db(tmp_path: Path) -> Database:
    reset_database()
    database = Database(tmp_path / "prep.db")
    yield database
    database.close()
    reset_database()


def _seed_project(db: Database, project_id: str = "proj_prep_01") -> str:
    with db._connection() as conn:
        conn.execute(
            """INSERT INTO projects
               (id, name, description, keywords_json, team_members_json,
                context_json, detection_threshold, revision, created_at, updated_at)
               VALUES (?, 'Q4 platform', '', '[]', '[]', '{}', 0.4, 7, ?, ?)""",
            (project_id, NOW_ISO, NOW_ISO),
        )
    return project_id


def _seed_watch(
    db: Database, project_id: str, watch_id: str, connector: str, *,
    query: dict[str, Any], snapshot: dict[str, Any] | None = None,
    last_success_at: str | None = None, next_evaluation_at: str | None = None,
    last_error: str | None = None, state: str = "", enabled: int = 1,
    query_kind: str = "pull_requests",
) -> None:
    with db._connection() as conn:
        conn.execute(
            """INSERT INTO connector_watches
               (id, connector_id, query_kind, name, query_json, snapshot_json, enabled,
                last_success_at, last_error, project_id, state, next_evaluation_at,
                created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                watch_id, connector, query_kind, watch_id, json.dumps(query),
                json.dumps(snapshot) if snapshot is not None else None, enabled,
                last_success_at, last_error, project_id, state, next_evaluation_at,
                NOW_ISO, NOW_ISO,
            ),
        )


def _seed_decisions(db: Database, project_id: str) -> tuple[str, str]:
    """One current decision and one superseded one, both sourced from a
    meeting linked to the Project (the Room's own join)."""
    meeting_id = "mtg_prep_0905"
    with db._connection() as conn:
        conn.execute("PRAGMA foreign_keys = OFF")
        conn.execute(
            "INSERT INTO meetings (id, title, started_at, ended_at, created_at) VALUES (?, ?, ?, ?, ?)",
            (meeting_id, "Cut-over sync", NOW_ISO, NOW_ISO, NOW_ISO),
        )
        conn.execute(
            "INSERT INTO meeting_projects (meeting_id, project_id) VALUES (?, ?)",
            (meeting_id, project_id),
        )
        rows = [
            ("decrec_current", "Cut-over runs on the read replica first", "active"),
            ("decrec_superseded", "Cut-over runs under a full freeze", "superseded"),
        ]
        for rid, text, lifecycle in rows:
            conn.execute(
                """INSERT INTO decision_records
                   (id, decision_text, lifecycle, source_type, source_id, created_at, updated_at)
                   VALUES (?, ?, ?, 'meeting', ?, ?, ?)""",
                (rid, text, lifecycle, meeting_id, NOW_ISO, NOW_ISO),
            )
            conn.execute(
                """INSERT INTO decision_record_sources (id, record_id, source_type, source_ref, created_at)
                   VALUES (?, ?, 'meeting', ?, ?)""",
                (f"src_{rid}", rid, meeting_id, NOW_ISO),
            )
    # Outside any transaction: a PRAGMA inside one is a no-op, and the cached
    # connection would carry FKs OFF into the tests that assert the cascade.
    with db._connection() as conn:
        conn.execute("PRAGMA foreign_keys = ON")
    return "decrec_current", "decrec_superseded"


def _room_with_sources(db: Database) -> tuple[ProjectService, str]:
    project_id = _seed_project(db)
    checked = (NOW - timedelta(minutes=2)).isoformat()
    # A read GitHub source: available.
    _seed_watch(
        db, project_id, "watch_gh", "gh",
        query={"repository": "karolswdev/HoldSpeak"},
        snapshot={"entities": {"pr_1": {"state": "open", "title": "Cut-over runbook"}}},
        last_success_at=checked, next_evaluation_at=(NOW + timedelta(hours=1)).isoformat(),
    )
    # A Jira source that missed its check: stale.
    _seed_watch(
        db, project_id, "watch_kan", "jira", query_kind="issues",
        query={"projects": ["KAN"], "connection_ref": "acme.atlassian.net|me@acme.com"},
        snapshot={"entities": {}},
        last_success_at=(NOW - timedelta(hours=6)).isoformat(),
        next_evaluation_at=(NOW - timedelta(hours=5)).isoformat(),
    )
    # A confluence source whose credential expired: cant_check.
    _seed_watch(
        db, project_id, "watch_cnf", "confluence", query_kind="pages",
        query={"connection_ref": "acme.atlassian.net|me@acme.com"},
        last_success_at=(NOW - timedelta(hours=1)).isoformat(),
        last_error="Confluence rejected the token (401)",
    )
    # A paused meeting source.
    _seed_watch(
        db, project_id, "watch_mtg", "meeting", query_kind="meetings",
        query={}, snapshot={"entities": {}},
        last_success_at=checked, state="paused",
    )
    _seed_decisions(db, project_id)
    return ProjectService(db), project_id


def _service(db: Database, project_service: ProjectService, **kw: Any) -> PreparationBriefService:
    return PreparationBriefService(db, project_service=project_service, clock=lambda: NOW, **kw)


# ── AC1: a purpose, no calendar ───────────────────────────────────────


def test_a_purpose_alone_prepares_a_brief_with_no_calendar_source(db: Database) -> None:
    projects, project_id = _room_with_sources(db)
    svc = _service(db, projects)
    brief = svc.prepare(OWNER, project_id, "architecture review, cut-over sequencing",
                        generator="deterministic")
    assert brief["purpose"] == "architecture review, cut-over sequencing"
    assert brief["manifest"]["calendar"] == {"present": False}
    assert brief["project_id"] == project_id


def test_an_empty_purpose_is_refused_by_name(db: Database) -> None:
    projects, project_id = _room_with_sources(db)
    with pytest.raises(ValidationError) as caught:
        _service(db, projects).prepare(OWNER, project_id, "   ")
    assert caught.value.code == "purpose_required"


# ── AC2: the source manifest ──────────────────────────────────────────


def test_the_manifest_names_every_source_with_its_state_and_observation(db: Database) -> None:
    projects, project_id = _room_with_sources(db)
    brief = _service(db, projects).prepare(OWNER, project_id, "cut-over", generator="deterministic")
    manifest = brief["manifest"]
    by_kind = {row["kind"]: row for row in manifest["sources"]}
    assert set(by_kind) == {"github", "jira", "confluence", "meeting"}
    assert by_kind["github"]["state"] == STATE_AVAILABLE
    assert by_kind["github"]["observed_at"]
    assert by_kind["github"]["revision"] == by_kind["github"]["observed_at"]
    assert by_kind["jira"]["state"] == STATE_STALE
    assert by_kind["confluence"]["state"] == STATE_FAILED
    assert by_kind["meeting"]["state"] == STATE_UNAVAILABLE
    # N in N OF M is the available count and nothing else (design D1).
    assert manifest["coverage"] == {"expected": 4, "available": 1, "complete": False}


def test_every_omission_is_named_with_a_reason_and_a_repair(db: Database) -> None:
    projects, project_id = _room_with_sources(db)
    brief = _service(db, projects).prepare(OWNER, project_id, "cut-over", generator="deterministic")
    omitted = {row["kind"]: row for row in brief["manifest"]["omitted"]}
    assert set(omitted) == {"jira", "confluence", "meeting"}
    assert omitted["jira"]["repair"] == {"token": "STALE", "verb": "Retry", "href": "/"}
    assert omitted["confluence"]["reason"]
    assert omitted["confluence"]["repair"]["verb"] == "Reconnect"
    assert omitted["meeting"]["repair"]["verb"] == "Resume"
    for row in omitted.values():
        assert row["reason"], row


def test_the_manifest_carries_current_and_superseded_decisions(db: Database) -> None:
    projects, project_id = _room_with_sources(db)
    brief = _service(db, projects).prepare(OWNER, project_id, "cut-over", generator="deterministic")
    decisions = {d["ref"]: d for d in brief["manifest"]["decisions"]}
    assert decisions["decision_record:decrec_current"]["lifecycle"] == "current"
    assert decisions["decision_record:decrec_superseded"]["lifecycle"] == "superseded"


def test_the_manifest_is_persisted_and_reloaded_with_its_freeze_verified(db: Database) -> None:
    projects, project_id = _room_with_sources(db)
    svc = _service(db, projects)
    brief = svc.prepare(OWNER, project_id, "cut-over", generator="deterministic")
    # A NEW service over the same file -- the read is from disk, not memory.
    again = PreparationBriefService(db, project_service=ProjectService(db)).get_brief(OWNER, brief["id"])
    assert again["manifest"] == brief["manifest"]
    assert again["manifest_revision"] == 1
    assert again["integrity"] == "verified"
    assert again["manifest_sha256"] == manifest_sha256(
        json.dumps(brief["manifest"], sort_keys=True, separators=(",", ":"), ensure_ascii=True, default=str)
    )


def test_a_tampered_manifest_is_named_a_mismatch_and_cannot_be_kept(db: Database) -> None:
    projects, project_id = _room_with_sources(db)
    svc = _service(db, projects)
    brief = svc.prepare(OWNER, project_id, "cut-over", generator="deterministic")
    with db._connection() as conn:
        conn.execute(
            "UPDATE project_briefs SET manifest_json = ? WHERE id = ?",
            (json.dumps({"forged": True}), brief["id"]),
        )
    assert svc.get_brief(OWNER, brief["id"])["integrity"] == "mismatch"
    with pytest.raises(ConflictError) as caught:
        svc.keep(OWNER, brief["id"])
    assert caught.value.code == "manifest_mismatch"


# ── AC3: bounded output on three axes ─────────────────────────────────


def test_the_outline_refuses_more_than_its_bound() -> None:
    too_many = [OutlineEntry(f"p{i}", f"s_priorities_{i}") for i in range(MAX_PRIORITIES + 1)]
    with pytest.raises(ValueError):
        Outline(priorities=too_many)
    with pytest.raises(ValueError):
        Outline(questions=[OutlineEntry(f"q{i}", f"s_questions_{i}") for i in range(MAX_QUESTIONS + 1)])
    with pytest.raises(ValueError):
        Outline(obligations=[OutlineEntry(f"o{i}", f"s_obligations_{i}") for i in range(MAX_OBLIGATIONS + 1)])


def test_the_deterministic_drafter_stays_within_the_bound_over_a_large_source_set(db: Database) -> None:
    projects, project_id = _room_with_sources(db)
    # Many decisions and commitments: far more than the caps.
    with db._connection() as conn:
        conn.execute("PRAGMA foreign_keys = OFF")
        for i in range(12):
            rid = f"decrec_many_{i}"
            conn.execute(
                """INSERT INTO decision_records
                   (id, decision_text, lifecycle, source_type, source_id, created_at, updated_at)
                   VALUES (?, ?, 'active', 'meeting', 'mtg_prep_0905', ?, ?)""",
                (rid, f"Decision number {i}", NOW_ISO, NOW_ISO),
            )
            conn.execute(
                """INSERT INTO decision_record_sources (id, record_id, source_type, source_ref, created_at)
                   VALUES (?, ?, 'meeting', 'mtg_prep_0905', ?)""",
                (f"src_{rid}", rid, NOW_ISO),
            )
    with db._connection() as conn:
        conn.execute("PRAGMA foreign_keys = ON")
    brief = _service(db, projects).prepare(OWNER, project_id, "cut-over", generator="deterministic")
    outline = brief["outline"]
    assert len(outline["priorities"]) <= MAX_PRIORITIES
    assert len(outline["questions"]) <= MAX_QUESTIONS
    assert len(outline["obligations"]) <= MAX_OBLIGATIONS
    assert len(outline["priorities"]) == MAX_PRIORITIES  # the cap is reached, not exceeded
    assert "Decision number 11" not in brief["body_md"]  # not a source dump
    # P1-3: what the bound left out is in the manifest, newest first named.
    left = brief["manifest"]["not_included"]
    assert len(left) == 10, len(left)
    assert all("newest first" in n["why"] for n in left)
    assert all(n["ref"].startswith("decision_record:") for n in left)


def test_every_deterministic_sentence_carries_the_three_axes(db: Database) -> None:
    projects, project_id = _room_with_sources(db)
    brief = _service(db, projects).prepare(OWNER, project_id, "cut-over", generator="deterministic")
    claims = json.loads(brief["claims_json"])
    assert claims, "the seeded room drafts at least one sentence"
    by_span = {c["span_id"]: c for c in claims}
    for claim in claims:
        assert claim["kind"] and claim["support"] and claim["acceptance"]
        assert claim["refs"], claim
    current = by_span["s_priorities_0"]
    assert (current["kind"], current["support"], current["acceptance"]) == (
        KIND_DECISION, SUPPORT_SUPPORTED, ACCEPTANCE_ACCEPTED,
    )
    assert current["refs"] == ["decision_record:decrec_current"]
    superseded = next(c for c in claims if "decision_record:decrec_superseded" in c["refs"])
    assert superseded["acceptance"] == ACCEPTANCE_SUPERSEDED
    assert superseded["section"] == "questions"
    # The outline and the claims are ONE shape: every outline line has its claim.
    for key in ("priorities", "questions", "obligations"):
        for entry in brief["outline"][key]:
            assert entry["span_id"] in by_span


def test_the_document_is_the_outline_and_nothing_else(db: Database) -> None:
    projects, project_id = _room_with_sources(db)
    brief = _service(db, projects).prepare(OWNER, project_id, "cut-over", generator="deterministic")
    body = brief["body_md"]
    assert body.startswith("## DECIDE TODAY")
    assert "## ASK THEM" in body
    lines = [ln for ln in body.splitlines() if ln.startswith("- ")]
    total = sum(len(brief["outline"][k]) for k in ("priorities", "questions", "obligations"))
    assert len(lines) == total


def test_the_model_parser_truncates_to_the_bound_and_types_every_sentence() -> None:
    refs = frozenset({"decision_record:decrec_current", "source:watch_gh"})
    texts = {"decision_record:decrec_current": "Cut-over runs on the read replica first",
             "source:watch_gh": "karolswdev/HoldSpeak 12 OPEN PRS"}
    raw = json.dumps({
        "priorities": [
            {"text": f"Priority {i} on the replica", "cited_refs": ["decision_record:decrec_current"]}
            for i in range(MAX_PRIORITIES + 2)
        ],
        "questions": [
            {"text": "Priya expects the cut-over at 95% by 2026-12-31", "cited_refs": ["source:watch_gh"]},
            {"text": "Sprint velocity improved over the trailing average", "cited_refs": []},
        ],
        "obligations": [],
    })
    parsed = parse_model_output(raw, refs, texts)
    assert parsed is not None
    outline, claims = parsed.outline, parsed.claims
    # P1-3: the two over the bound are NAMED, never silently dropped.
    assert [n["title"] for n in parsed.not_included] == ["Priority 3 on the replica", "Priority 4 on the replica"]
    assert all(n["why"].startswith("over the bound of 3") for n in parsed.not_included)
    assert len(outline.priorities) == MAX_PRIORITIES
    linked = next(c for c in claims if c.text.startswith("Priya"))
    assert (linked.kind, linked.support, linked.acceptance) == (
        KIND_INFERENCE, SUPPORT_SOURCE_LINKED, ACCEPTANCE_UNREVIEWED,
    )
    unknown_types = {(u["type"], u["value"]) for u in linked.unknowns}
    assert ("deadline", "2026-12-31") in unknown_types
    assert ("number", "95%") in unknown_types
    # A sentence-initial single word is grammar, not a name, unless the desk
    # KNOWS the person (counsel's NAME rule); this rig names nobody.
    assert ("name", "Priya") not in unknown_types
    unsupported = next(c for c in claims if c.text.startswith("Sprint"))
    assert unsupported.refs == []
    assert unsupported.support == SUPPORT_UNKNOWN
    assert unsupported.verified is False


def test_unparseable_model_output_is_none_not_a_partial_brief() -> None:
    assert parse_model_output("not json at all", frozenset(), {}) is None
    assert parse_model_output(json.dumps({"sections": []}), frozenset(), {}) is None


def test_the_model_drafter_produces_the_same_typed_shape(db: Database) -> None:
    projects, project_id = _room_with_sources(db)
    _seed_assignment(db, PREPARATION_BRIEF_CAPABILITY)
    output = json.dumps({
        "priorities": [{"text": "Decide the replica-first cut-over", "cited_refs": ["decision_record:decrec_current"]}],
        "questions": [{"text": "Who owns the rollback call after 04:00?", "cited_refs": []}],
        "obligations": [],
    })
    runner = _MockRunner(output=output)
    svc = _service(db, projects, broker=_MockBroker(db, runner))
    brief = svc.prepare(OWNER, project_id, "cut-over", generator="model")
    assert brief["generator"].startswith("model:")
    assert len(runner.invoke_calls) == 1
    assert set(brief["outline"]) == {"priorities", "questions", "obligations"}
    claims = {c["span_id"]: c for c in json.loads(brief["claims_json"])}
    assert claims["s_priorities_0"]["support"] == SUPPORT_SOURCE_LINKED
    assert claims["s_questions_0"]["support"] == SUPPORT_UNKNOWN
    assert claims["s_questions_0"]["refs"] == []
    # The manifest is bound regardless of which drafter wrote the words.
    assert brief["manifest"]["coverage"]["expected"] == 4


# ── AC4: attached to its Project, kept by a flip ──────────────────────


def test_the_kept_brief_lists_from_its_project(db: Database) -> None:
    projects, project_id = _room_with_sources(db)
    other = _seed_project(db, "proj_other")
    svc = _service(db, projects)
    draft = svc.prepare(OWNER, project_id, "cut-over", generator="deterministic")
    assert draft["lifecycle"] == "draft"
    kept = svc.keep(OWNER, draft["id"])
    assert kept["lifecycle"] == "kept"
    assert kept["kept_at"] == NOW.isoformat()
    assert kept["id"] == draft["id"]  # a flip on the same row, never a copy
    assert kept["manifest_sha256"] == draft["manifest_sha256"]
    listed = svc.list_briefs(OWNER, project_id, lifecycle="kept")
    assert [b["id"] for b in listed] == [draft["id"]]
    assert svc.list_briefs(OWNER, other) == []
    # Keeping twice is a no-op, not a second write.
    assert svc.keep(OWNER, draft["id"])["kept_at"] == kept["kept_at"]


def test_discard_is_a_state_that_leaves_the_list(db: Database) -> None:
    projects, project_id = _room_with_sources(db)
    svc = _service(db, projects)
    draft = svc.prepare(OWNER, project_id, "cut-over", generator="deterministic")
    svc.discard(OWNER, draft["id"])
    assert svc.list_briefs(OWNER, project_id) == []
    assert svc.get_brief(OWNER, draft["id"])["lifecycle"] == "discarded"
    with pytest.raises(ConflictError):
        svc.keep(OWNER, draft["id"])


def test_an_unknown_brief_or_project_is_a_not_found(db: Database) -> None:
    projects, _project_id = _room_with_sources(db)
    svc = _service(db, projects)
    with pytest.raises(NotFound):
        svc.get_brief(OWNER, "pbrief_missing")
    with pytest.raises(NotFound):
        svc.prepare(OWNER, "proj_missing", "anything", generator="deterministic")


def test_the_brief_goes_with_its_project(db: Database) -> None:
    projects, project_id = _room_with_sources(db)
    svc = _service(db, projects)
    brief = svc.prepare(OWNER, project_id, "cut-over", generator="deterministic")
    with db._connection() as conn:
        conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
        left = conn.execute("SELECT COUNT(*) c FROM project_briefs WHERE id = ?", (brief["id"],)).fetchone()["c"]
    assert left == 0


# ── AC5: unavailable AI keeps the purpose and refuses ─────────────────


def test_no_route_refuses_with_the_purpose_and_dispatches_nothing(db: Database) -> None:
    projects, project_id = _room_with_sources(db)
    runner = _MockRunner(output="{}")
    svc = _service(db, projects, broker=_MockBroker(db, runner))  # no assignment seeded
    with pytest.raises(PreparationRefused) as caught:
        svc.prepare(OWNER, project_id, "architecture review, cut-over sequencing")
    refusal = caught.value
    assert refusal.purpose == "architecture review, cut-over sequencing"
    assert refusal.route["state"] == ROUTE_NOT_SET
    assert refusal.route["token"] == ROUTE_TOKENS[ROUTE_NOT_SET]
    assert refusal.route["repair"] == "Set up model"
    assert runner.invoke_calls == [], "no request left the machine"
    # Nothing was written for a refused run.
    assert svc.list_briefs(OWNER, project_id) == []


def test_a_broken_endpoint_refuses_as_unreachable_and_writes_nothing(db: Database) -> None:
    projects, project_id = _room_with_sources(db)
    _seed_assignment(db, PREPARATION_BRIEF_CAPABILITY)
    runner = _MockRunner(error=ConnectionError("192.168.1.43:8080 refused the connection"))
    svc = _service(db, projects, broker=_MockBroker(db, runner))
    with pytest.raises(PreparationRefused) as caught:
        svc.prepare(OWNER, project_id, "cut-over")
    assert caught.value.route["state"] == ROUTE_UNREACHABLE
    assert caught.value.route["token"] == "ENDPOINT UNREACHABLE"
    assert "192.168.1.43" in caught.value.route["reason"]
    # P0: the runner raised before any operation existed -> nothing was sent.
    assert caught.value.route["invoke"]["sent"] is False
    assert svc.list_briefs(OWNER, project_id) == []
    # The purpose survives in the refusal, verbatim.
    assert caught.value.purpose == "cut-over"


def test_the_route_probe_names_the_state_without_dispatching(db: Database) -> None:
    projects, project_id = _room_with_sources(db)
    runner = _MockRunner(output="{}")
    svc = _service(db, projects, broker=_MockBroker(db, runner))
    assert svc.route(OWNER, project_id)["state"] == ROUTE_NOT_SET
    _seed_assignment(db, PREPARATION_BRIEF_CAPABILITY)
    route = svc.route(OWNER, project_id)
    assert route["state"] == ROUTE_READY
    assert route["token"] == "READY"
    assert runner.invoke_calls == []


def test_no_broker_at_all_is_not_set(db: Database) -> None:
    projects, project_id = _room_with_sources(db)
    svc = _service(db, projects)
    assert svc.route(OWNER, project_id)["state"] == ROUTE_NOT_SET
    with pytest.raises(PreparationRefused):
        svc.prepare(OWNER, project_id, "cut-over")


def _define_real_endpoint(db: Database, home: Path, *, endpoint: str, requires_key: bool) -> str:
    """A hub-defined endpoint through the product's OWN services (no
    hand-seeded ids), assigned to the brief capability.  Returns the profile
    id the route will name."""
    from holdspeak.config import Config
    from holdspeak.services.inference_acquisition_service import InferenceAcquisitionApplicationService
    from holdspeak.services.inference_assignment_service import InferenceAssignmentService
    from holdspeak.services.inference_setup_service import InferenceSetupApplicationService
    from holdspeak.services.model_library_service import ModelLibraryApplicationService

    profile_id = "hosted-brief-endpoint"
    setup = InferenceSetupApplicationService(db, config_provider=Config, home_provider=lambda: home)
    acquisition = InferenceAcquisitionApplicationService(
        db, setup_service=setup, model_root=home / "models", home_provider=lambda: home,
    )
    ModelLibraryApplicationService(db, setup_service=setup, acquisition_service=acquisition).define_endpoint(
        OWNER,
        {
            "request_id": "prep-brief-endpoint",
            "profile_id": profile_id,
            "expected_profile_revision": 0,
            "label": "Hosted brief endpoint",
            "provider_family": "openai_compatible" if requires_key else "private_endpoint",
            "model": "qwen3-35b",
            "endpoint": endpoint,
            "requires_key": requires_key,
        },
        {"value": "sk-test-key"} if requires_key else None,
    )
    assignments = InferenceAssignmentService(db)
    assignments.set_assignment(OWNER, {
        "command_id": "prep-brief-global", "expected_revision": 0,
        "scope": {"kind": "global"},
        "entries": [{"profile_id": profile_id, "profile_revision": 1}],
    })
    assignments.set_assignment(OWNER, {
        "command_id": "prep-brief-capability", "expected_revision": 0,
        "scope": {"kind": "capability", "capability_id": PREPARATION_BRIEF_CAPABILITY},
        "entries": [{"profile_id": profile_id, "profile_revision": 1}],
    })
    return profile_id


def test_a_key_that_is_not_set_is_named_through_the_real_route(db: Database, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """P1-1: a REAL hosted endpoint whose key the owner removed.  The route
    is read through the product's planner and the leg's own deployment
    revision (its secret slot), never a hand-seeded profile id."""
    from holdspeak.kernel import runtime
    from holdspeak.profile_key_store import _default_profile_key_store

    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    projects, project_id = _room_with_sources(db)
    _define_real_endpoint(db, home, endpoint="https://api.example.test/v1", requires_key=True)
    broker = runtime._configure(db)
    svc = _service(db, projects, broker=broker)
    ready = svc.route(OWNER, project_id)
    assert ready["state"] == ROUTE_READY, ready
    assert ready["model"] == "QWEN3 35B", ready  # the profile's own label, not the engine kind
    assert ready["host"] == "api.example.test", ready
    assert ready["boundary"] == "external_service", ready
    # The owner removes the key: the SAME slot the runner would read.
    with db._connection() as conn:
        slot = conn.execute(
            "SELECT secret_slot FROM deployment_revisions WHERE secret_slot != '' ORDER BY rowid DESC LIMIT 1"
        ).fetchone()["secret_slot"]
    assert slot
    _default_profile_key_store().delete(slot)
    route = svc.route(OWNER, project_id)
    assert route["state"] == ROUTE_KEY_MISSING, route
    assert route["token"] == "KEY NOT SET"
    with pytest.raises(PreparationRefused) as caught:
        svc.prepare(OWNER, project_id, "cut-over")
    assert caught.value.route["state"] == ROUTE_KEY_MISSING
    assert caught.value.route["invoke"]["sent"] is False
    assert caught.value.purpose == "cut-over"


def test_a_closed_port_is_unreachable_through_the_real_route(db: Database, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """P1-1 + P0: a REAL private endpoint at a closed port.  READY before the
    run (the probe sends nothing); the run refuses ENDPOINT UNREACHABLE with
    a kernel operation on the receipt -- a request LEFT."""
    from holdspeak.kernel import runtime

    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    projects, project_id = _room_with_sources(db)
    _define_real_endpoint(db, home, endpoint="http://127.0.0.1:1/v1", requires_key=False)
    broker = runtime._configure(db)
    svc = _service(db, projects, broker=broker)
    route = svc.route(OWNER, project_id)
    assert route["state"] == ROUTE_READY and route["host"] == "127.0.0.1" and route["model"] == "QWEN3 35B", route
    assert route["boundary"] == "private_network", route
    with pytest.raises(PreparationRefused) as caught:
        svc.prepare(OWNER, project_id, "cut-over", attempt_id="att_closed")
    refused = caught.value.route
    assert refused["state"] == ROUTE_UNREACHABLE, refused
    assert refused["invoke"]["sent"] is True, refused
    assert refused["invoke"]["operation_id"], refused
    assert refused["invoke"]["host"] == "127.0.0.1"
    assert svc.list_briefs(OWNER, project_id) == []


# ── restart: the brief reopens by id with the same freeze ─────────────


def test_a_kept_brief_survives_a_reopen_from_the_file(db: Database, tmp_path: Path) -> None:
    projects, project_id = _room_with_sources(db)
    svc = _service(db, projects)
    kept = svc.keep(OWNER, svc.prepare(OWNER, project_id, "cut-over", generator="deterministic")["id"])
    db.close()
    reset_database()
    reopened = Database(tmp_path / "prep.db")
    try:
        again = PreparationBriefService(reopened, project_service=ProjectService(reopened)).get_brief(OWNER, kept["id"])
        assert again["lifecycle"] == "kept"
        assert again["manifest_revision"] == kept["manifest_revision"]
        assert again["manifest_sha256"] == kept["manifest_sha256"]
        assert again["integrity"] == "verified"
        assert again["manifest"]["omitted"] == kept["manifest"]["omitted"]
    finally:
        reopened.close()


# ── the schema: additive, self-reconciling ────────────────────────────


def test_reconcile_adds_the_table_to_a_pre_200_11_database(tmp_path: Path) -> None:
    from holdspeak.db.schema import SCHEMA_SQL

    before = re.sub(
        r"CREATE TABLE IF NOT EXISTS project_briefs \(.*?\);\s*"
        r"CREATE INDEX IF NOT EXISTS idx_project_briefs_project.*?;",
        "", SCHEMA_SQL, flags=re.S,
    )
    assert "project_briefs" not in before
    path = tmp_path / "pre.db"
    conn = sqlite3.connect(str(path))
    conn.executescript(before)
    conn.execute("INSERT INTO projects (id, name) VALUES ('project_legacy', 'Old room')")
    conn.commit()
    conn.close()
    reset_database()
    database = Database(path)
    try:
        with database._connection() as live:
            names = {
                str(row["name"]) for row in live.execute(
                    "SELECT name FROM sqlite_master WHERE name LIKE '%project_briefs%'"
                ).fetchall()
            }
        assert names >= {"project_briefs", "idx_project_briefs_project"}
        svc = PreparationBriefService(database, project_service=ProjectService(database), clock=lambda: NOW)
        brief = svc.prepare(OWNER, "project_legacy", "carried over", generator="deterministic")
        assert brief["project_id"] == "project_legacy"
        assert brief["manifest"]["coverage"] == {"expected": 0, "available": 0, "complete": True}
    finally:
        database.close()
        reset_database()


# ── the pure builders, headless ───────────────────────────────────────


def test_build_manifest_marks_a_missed_check_stale_and_a_fresh_one_available() -> None:
    room = {
        "project_id": "p", "revision": 3,
        "sources": {"state": "ok", "items": [
            {"watchId": "w1", "watchIds": ["w1"], "provider": "github", "scope": "a/b", "tokens": ["2 OPEN PRS"],
             "checkedAt": (NOW - timedelta(minutes=1)).isoformat(),
             "nextCheckAt": (NOW + timedelta(minutes=30)).isoformat(),
             "host": "github.com", "state": "live", "plainReason": None, "suggested": False},
            {"watchId": "w2", "watchIds": ["w2"], "provider": "jira", "scope": "KAN", "tokens": [],
             "checkedAt": (NOW - timedelta(hours=6)).isoformat(),
             "nextCheckAt": (NOW - timedelta(hours=5)).isoformat(),
             "host": "acme.atlassian.net", "state": "live", "plainReason": None, "suggested": False},
            {"watchId": "w3", "watchIds": ["w3"], "provider": "github", "scope": "sug", "tokens": [],
             "checkedAt": None, "nextCheckAt": None, "host": "", "state": "live",
             "plainReason": None, "suggested": True},
        ]},
        "decisions": {"state": "degraded"},
        "commitments": {"state": "ok", "items": []},
    }
    manifest = build_manifest(room, "why", now=NOW)
    states = {r["source_id"]: r["state"] for r in manifest["sources"]}
    assert states == {"w1": STATE_AVAILABLE, "w2": STATE_STALE}  # the suggestion is not a source
    assert [r["source_id"] for r in manifest["omitted"]] == ["w2"]
    assert manifest["decisions"] == []  # a degraded section contributes nothing, silently never
    assert manifest["coverage"] == {"expected": 2, "available": 1, "complete": False}


def test_draft_deterministic_asks_about_an_ownerless_commitment() -> None:
    room = {
        "project_id": "p", "revision": 1,
        "sources": {"state": "ok", "items": []},
        "decisions": {"state": "ok", "items": []},
        "commitments": {"state": "ok", "items": [
            {"id": "c1", "text": "Priya confirms the freeze window", "owner": None, "dueAt": None},
            {"id": "c2", "text": "Rollback runbook reviewed", "owner": "Marek", "dueAt": "2026-09-12T00:00:00"},
        ]},
        "needsYou": {"state": "ok", "items": []},
    }
    manifest = build_manifest(room, "why", now=NOW)
    draft = draft_deterministic(room, manifest)
    outline, claims = draft.outline, draft.claims
    assert outline.questions[0].text == "Who owns: Priya confirms the freeze window?"
    assert [o.text for o in outline.obligations] == [
        "Priya confirms the freeze window",
        "Rollback runbook reviewed -- owner Marek -- due 09-12",
    ]
    question = next(c for c in claims if c.span_id == "s_questions_0")
    assert question.kind == KIND_INFERENCE
    assert question.support == SUPPORT_SOURCE_LINKED
    assert question.refs == ["commitment:c1"]


def test_a_verbatim_carried_decision_keeps_its_axes_through_the_model() -> None:
    """A sentence the model returns unchanged, citing the decision it came
    from, IS that decision: DECISION · SUPPORTED · ACCEPTED (board P3Brief).
    One changed word and it is model prose: INFERENCE · LINKED."""
    from holdspeak.services.project_update_service import _field_mapping_support

    ref = "decision_record:decrec_current"
    carried = Claim(
        span_id="s_priorities_0", text="Cut-over runs on the read replica first", refs=[ref],
        section="priorities", kind=KIND_DECISION, support=SUPPORT_SUPPORTED,
        acceptance=ACCEPTANCE_ACCEPTED,
        support_record=_field_mapping_support("project:p@1", [ref], ["decision_text"]),
    )
    raw = json.dumps({
        "priorities": [
            {"text": "Cut-over runs on the read replica first", "cited_refs": [ref]},
            {"text": "Cut-over runs on the read replica first, then the primary", "cited_refs": [ref]},
        ],
        "questions": [], "obligations": [],
    })
    parsed = parse_model_output(raw, frozenset({ref}), {ref: carried.text}, [carried])
    assert parsed is not None
    claims = parsed.claims
    assert (claims[0].kind, claims[0].support, claims[0].acceptance) == (
        KIND_DECISION, SUPPORT_SUPPORTED, ACCEPTANCE_ACCEPTED,
    )
    assert claims[0].support_record is not None
    assert (claims[1].kind, claims[1].support) == (KIND_INFERENCE, SUPPORT_SOURCE_LINKED)


# ── counsel-on-built fences (2026-09-17) ──────────────────────────────


COUNSEL_SENTENCES = [
    "Sprint velocity improved over the trailing average",
    "Confirm the freeze window before Friday",
    "Cut-over runs on the read replica first",
    "Decide the rollback owner today",
    "Ask whether KAN-7 rides the freeze",
    "Ship the runbook before the window opens",
    "Rollback rehearsal is still unscheduled",
    "Migration of the ledger tables waits on sign-off",
    "Payments will fail over to the secondary region",
    "Read replica lag is unmeasured",
    "Who owns the rollback call after 04:00?",
    "When is it due: rehearse the cut-over?",
    "Superseded -- does anyone still act on: full freeze?",
    "Two open pull requests wait on the runbook",
    "Priya expects the cut-over at 95% by 2026-12-31",
    "Kubernetes upgrade lands in the same window",
    "Postgres 16 is not yet validated",
    "GitHub Actions minutes are close to the cap",
    "Marek confirmed the DNS cut-over",
    "The Saturday window has no on-call cover",
    "Jira board KAN has twelve open tickets",
    "Confluence runbook is behind the token wall",
    "Agree the go/no-go call time",
    "Schedule the dry run",
    "Runbook step 7 references the old hostname",
    "Freeze starts Friday 18:00 CET",
    "QA sign-off is missing for the ledger service",
    "Nobody owns the comms plan",
    "Stakeholders in Finance were not told",
    "API gateway limits stay unchanged",
]


def test_the_name_heuristic_does_not_fire_on_counsels_thirty_sentences() -> None:
    """Counsel's 30 realistic sentences: 28 minted a false NAME under the old
    regex.  With NO known person on the desk, none may -- a sentence-initial
    verb, a hyphen half, an acronym, a weekday: not a name."""
    from holdspeak.services.project_update_service import _typed_unknowns

    false_names = {
        s: [u["value"] for u in _typed_unknowns(s, "the source says nothing relevant") if u["type"] == "name"]
        for s in COUNSEL_SENTENCES
    }
    fired = {s: v for s, v in false_names.items() if v}
    # The two multi-word capitalised sequences are the only survivors, and
    # they are real names of things the source does not carry.
    assert set(fired) <= {"GitHub Actions minutes are close to the cap"}, fired
    # `hh:mm` is ONE number, never two.
    numbers = [u["value"] for u in _typed_unknowns("Who owns the rollback call after 04:00?", "x") if u["type"] == "number"]
    assert numbers == ["04:00"], numbers
    # A hyphenated word is never split into halves.
    assert not [u for u in _typed_unknowns("Cut-over runs on the read replica first", "x") if u["type"] == "name"]
    # A sentence with NO source mints no NAME at all: its face says NO SOURCE.
    assert not [u for u in _typed_unknowns("Priya expects the cut-over at 95%", "") if u["type"] == "name"]


def test_a_real_name_the_desk_knows_still_lands_as_an_unknown() -> None:
    from holdspeak.services.project_update_service import _typed_unknowns

    known = ("Priya", "Marek")
    assert {"type": "name", "value": "Priya"} in _typed_unknowns(
        "Priya expects the cut-over at 95% by 2026-12-31", "nothing relevant", known,
    )
    assert {"type": "name", "value": "Marek"} in _typed_unknowns(
        "Marek confirmed the DNS cut-over", "nothing relevant", known,
    )
    # ...and NOT when the cited source carries the name.
    assert not [u for u in _typed_unknowns("Marek confirmed the DNS cut-over", "owner Marek", known) if u["type"] == "name"]


def test_a_superseded_citation_goes_to_the_superseded_ledger_never_the_outline() -> None:
    """P1-2: the model cites the superseded decision as a priority."""
    current = "decision_record:decrec_current"
    old = "decision_record:decrec_superseded"
    manifest = {"decisions": [
        {"ref": current, "text": "Cut-over runs on the read replica first", "lifecycle": "current"},
        {"ref": old, "text": "Cut-over runs under a full freeze", "lifecycle": "superseded", "successor_ref": current},
    ]}
    raw = json.dumps({
        "priorities": [
            {"text": "Cut-over runs on the read replica first", "cited_refs": [current]},
            {"text": "Cut-over runs under a full freeze", "cited_refs": [old]},
        ],
        "questions": [], "obligations": [],
    })
    parsed = parse_model_output(raw, frozenset({current, old}), {current: "x", old: "y"}, None, manifest)
    assert parsed is not None
    assert [e.text for e in parsed.outline.priorities] == ["Cut-over runs on the read replica first"]
    stale = [c for c in parsed.claims if c.section == SECTION_SUPERSEDED]
    assert len(stale) == 1
    assert (stale[0].kind, stale[0].acceptance) == (KIND_DECISION, ACCEPTANCE_SUPERSEDED)
    assert stale[0].refs == [old]
    assert {"type": "superseded_by", "value": current} in stale[0].unknowns


def test_the_manifest_names_a_superseded_decisions_successor(db: Database) -> None:
    projects, project_id = _room_with_sources(db)
    with db._connection() as conn:
        conn.execute(
            """INSERT INTO decision_record_revisions (id, record_id, field_name, old_value, new_value, created_at)
               VALUES ('rev_succ', 'decrec_superseded', 'successor_id', NULL, 'decrec_current', ?)""",
            (NOW_ISO,),
        )
    manifest = _service(db, projects).preview_manifest(OWNER, project_id)
    old = next(d for d in manifest["decisions"] if d["lifecycle"] == "superseded")
    assert old["successor_ref"] == "decision_record:decrec_current"


def test_a_stopped_attempt_writes_no_draft(db: Database) -> None:
    """P1-4: the owner stopped while the request was out; the run that still
    completes refuses as STOPPED and leaves no row."""
    projects, project_id = _room_with_sources(db)
    _seed_assignment(db, PREPARATION_BRIEF_CAPABILITY)
    output = json.dumps({"priorities": [{"text": "x", "cited_refs": []}], "questions": [], "obligations": []})

    class _StoppingRunner(_MockRunner):
        def __init__(self, svc_ref: list[Any]) -> None:
            super().__init__(output=output)
            self._svc_ref = svc_ref

        def invoke(self, request: Any, adapter: Any, publish: Any = None) -> Any:
            # The Stop lands while the request is out.
            self._svc_ref[0].stop("att_stop_1")
            return super().invoke(request, adapter, publish)

    holder: list[Any] = []
    runner = _StoppingRunner(holder)
    svc = _service(db, projects, broker=_MockBroker(db, runner))
    holder.append(svc)
    with pytest.raises(PreparationRefused) as caught:
        svc.prepare(OWNER, project_id, "cut-over", attempt_id="att_stop_1")
    assert caught.value.route["state"] == ROUTE_STOPPED
    assert svc.list_briefs(OWNER, project_id) == []
    # The stop knew the invocation and asked the runner to cancel it.
    assert svc.stop("att_stop_1")["stopped"] is True


def test_an_invoke_that_returned_an_outcome_is_reported_as_sent(db: Database) -> None:
    """P0: a request that LEFT and came back unusable is `sent`, with the
    operation and the host on the receipt -- never NOTHING SENT."""
    projects, project_id = _room_with_sources(db)
    _seed_assignment(db, PREPARATION_BRIEF_CAPABILITY)

    class _ProseRunner(_MockRunner):
        def invoke(self, request: Any, adapter: Any, publish: Any = None) -> Any:
            if publish is not None:
                publish({"output": "Sure! Here is a brief in prose."})

            class _Outcome:
                operation_id = "op_prose_1"
                invocation_id = request.invocation_id
                outcome = "succeeded"
                send_phase = "provider_returned"
                result = None
                error = ""
            return _Outcome()

    svc = _service(db, projects, broker=_MockBroker(db, _ProseRunner()))
    with pytest.raises(PreparationRefused) as caught:
        svc.prepare(OWNER, project_id, "cut-over", attempt_id="att_prose")
    route = caught.value.route
    assert route["state"] == "unusable_output"
    assert route["invoke"]["sent"] is True
    assert route["invoke"]["operation_id"] == "op_prose_1"
    assert route["invoke"]["outcome"] == "succeeded"
    assert route["invoke"]["host"] == route["host"]
    assert svc.list_briefs(OWNER, project_id) == []


def test_a_credential_failure_is_credential_expired_with_reconnect(db: Database) -> None:
    """P2 i: a 401/403 reason maps to CREDENTIAL EXPIRED · <PROVIDER> + Reconnect."""
    projects, project_id = _room_with_sources(db)
    manifest = _service(db, projects).preview_manifest(OWNER, project_id)
    cnf = next(s for s in manifest["sources"] if s["kind"] == "confluence")
    assert cnf["repair"] == {"token": "CREDENTIAL EXPIRED · CONFLUENCE", "verb": "Reconnect", "href": "/settings"}


def test_a_needs_you_row_is_cited_by_its_watch_id_not_its_provider_kind() -> None:
    """P2 vi: two GitHub sources, one read; the row from the other is not cited."""
    from holdspeak.services.preparation_brief_service import _source_ref_for

    manifest = {"sources": [
        {"source_id": "w_a", "state": STATE_AVAILABLE, "kind": "github", "watch_ids": ["w_a"]},
        {"source_id": "w_b", "state": STATE_STALE, "kind": "github", "watch_ids": ["w_b"]},
    ]}
    assert _source_ref_for({"source": "github", "watchId": "w_a"}, manifest) == "source:w_a"
    assert _source_ref_for({"source": "github", "watchId": "w_b"}, manifest) is None
    assert _source_ref_for({"source": "github"}, manifest) is None
