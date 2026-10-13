#!/usr/bin/env python3
"""Record the hub's own answers for the Room app's face tests (the test diet, 2026-10-11).

The face tests (``web/src/features/project-room/__tests__/room.app.test.tsx``,
``steward/__tests__/steward.app.test.tsx`` and
``door/__tests__/newProject.app.test.tsx``) replay these answers through a
mocked ``apiFetch``. Every answer comes from the real hub (``MeetingWebServer``
through ``TestClient``, the rig of ``tests/integration/test_desk_project_room.py``)
on an isolated HOME and database, seeded with the browser tests' own seeds.
Nothing is typed by hand, so no field the face reads can be invented (the
SCAR LAW). The few seams a browser test patched (the gh process edge, the acli
runner, the People alias resolver) are patched the same way here.

Run it again when an answer's shape changes:

    HOME=$(mktemp -d) uv run python scripts/record_room_wires.py

It writes the JSON files under ``web/src/features/project-room/**/room-*wires/``.
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import uuid
from types import SimpleNamespace
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tests" / "integration"))

import test_desk_project_room as rig  # noqa: E402

ROOM_DIR = REPO / "web" / "src" / "features" / "project-room" / "__tests__" / "room-wires"
STEWARD_DIR = REPO / "web" / "src" / "features" / "project-room" / "steward" / "__tests__" / "room-steward-wires"
DOOR_DIR = REPO / "web" / "src" / "features" / "project-room" / "door" / "__tests__" / "room-door-wires"

# The reads the Room window makes when it opens (found by replaying the face
# with an empty table and listing every path it asked for).
ROOM_GETS = (
    "/api/projects/{pid}/room",
    "/api/coders/sessions?include_ended=false",
    "/api/memory/pages?project_id={pid}",
    "/api/projects/{pid}/briefs?lifecycle=kept",
    "/api/projects/{pid}/meetings?limit=200",
    "/api/decisions?project_id={pid}&limit=500",
    "/api/projects/{pid}/artifacts",
    "/api/projects/{pid}/since-last-meeting",
    "/api/projects/{pid}/items?limit=200",
    "/api/projects/{pid}/people",
    "/api/projects/{pid}/resources",
    "/api/projects/{pid}/proposals?state=proposed",
    "/api/projects/{pid}/suggested-sources",
    "/api/projects/{pid}/nudges?state=proposed",
    "/api/projects/{pid}/repository",
    "/api/connections",
    "/api/inference/assignments",
    "/api/inference-targets",
)
UPDATE_GETS = ("/api/projects/{pid}/updates",)


def _update_gets(hub: Any, pid: str) -> dict[str, Any]:
    """The Update editor's own reads: each update's channel sends."""
    from urllib.parse import quote

    out: dict[str, Any] = {}
    for update in hub.ok("GET", f"/api/projects/{pid}/updates").get("updates", []):
        path = f"/api/channels/sends?document_ref={quote('project_update:' + update['id'], safe='')}"
        out[path] = _answer(hub.client.get(path))
    return out
STEWARD_GETS = (
    "/api/projects/{pid}/steward/runs",
    "/api/projects/{pid}/steward/policy",
    "/api/projects/{pid}/watches",
)


# ── Seeds copied verbatim from the browser tests (parked by the test diet) ──


# copied verbatim from tests/e2e/test_hs173_update_glass.py

def _seed_model_draft(project_id: str) -> str:
    """Insert a model-drafted update with one unverified claim."""
    from holdspeak.db import get_database
    db = get_database()
    update_id = "pupd_173_model_glass_01"
    claims = [
        {"span_id": "s1", "text": "The API schema migration merged with zero rollback risk.",
         "refs": ["item:pr-612"], "section": "progress", "verified": True},
        {"span_id": "s2", "text": "Payments cut-over runbook overdue by 2 days.",
         "refs": ["item:kan-7"], "section": "progress", "verified": True},
        {"span_id": "s3", "text": "Team agreed to target Oct 12 for the cut-over.",
         "refs": ["meeting:2026-09-05"], "section": "progress", "verified": True},
        {"span_id": "s4", "text": "Sprint velocity improved 15% over the trailing average.",
         "refs": [], "section": "progress", "verified": False},
    ]
    body_md = (
        "## Progress\n\n"
        "The API schema migration merged with zero rollback risk.\n"
        "Payments cut-over runbook overdue by 2 days.\n"
        "Team agreed to target Oct 12 for the cut-over.\n"
        "Sprint velocity improved 15% over the trailing average.\n"
    )
    now_iso = datetime.now().isoformat()
    with db._connection() as conn:
        conn.execute(
            """INSERT INTO project_updates
               (id, project_id, project_revision, review_id,
                lifecycle, draft_revision, body_md, claims_json,
                source_manifest_json, generator,
                generator_host, generator_model,
                created_at, updated_at)
               VALUES (?, ?, ?, ?, 'draft', ?, ?, ?, ?, ?,
                       ?, ?, ?, ?)""",
            (update_id, project_id, 0, None, 3, body_md,
             json.dumps(claims, separators=(",", ":")),
             "{}", "model:qwen3-32b",
             "192.168.1.43", "QWEN3 32B Q6",
             now_iso, now_iso),
        )
    return update_id

def _seed_deterministic_draft(project_id: str) -> str:
    """Insert a deterministic draft with all verified claims."""
    from holdspeak.db import get_database
    db = get_database()
    update_id = "pupd_173_det_glass_01"
    claims = [
        {"span_id": "s1", "text": "API schema migration merged.",
         "refs": ["item:pr-612"], "section": "progress", "verified": True},
    ]
    body_md = "## Progress\n\nAPI schema migration merged.\n"
    now_iso = datetime.now().isoformat()
    with db._connection() as conn:
        conn.execute(
            """INSERT INTO project_updates
               (id, project_id, project_revision, review_id,
                lifecycle, draft_revision, body_md, claims_json,
                source_manifest_json, generator,
                created_at, updated_at)
               VALUES (?, ?, ?, ?, 'draft', ?, ?, ?, ?, ?,
                       ?, ?)""",
            (update_id, project_id, 0, None, 2, body_md,
             json.dumps(claims, separators=(",", ":")),
             "{}", "deterministic",
             now_iso, now_iso),
        )
    return update_id


# copied verbatim from tests/e2e/test_hs200_claim_support_glass.py

def _seed_mixed_update(project_id: str) -> str:
    """One update carrying the whole support vocabulary.

    The last claim is written in the PRE-HS-200-06 shape (a citation and
    a `verified` flag, no axes); the read path maps it conservatively.
    """
    from holdspeak.db import get_database
    db = get_database()
    update_id = "pupd_200_mixed_glass_01"
    claims = [
        {
            "span_id": "s1",
            "text": "Milestone [high]: Launch v2.0 -- planned",
            "refs": ["item:pr-612"],
            "section": "progress",
            "kind": "observation",
            "support": "supported",
            "acceptance": "unreviewed",
            "support_record": {
                "method": "field_mapping",
                "source_version": "project:p1@r5",
                "source_refs": ["item:pr-612"],
                "fields": ["item_type", "severity", "title", "lifecycle"],
            },
        },
        {
            "span_id": "s2",
            "text": "Priya expects the cut-over at 95% by 2026-12-31",
            "refs": ["meeting:2026-09-05"],
            "section": "progress",
            "kind": "inference",
            "support": "source_linked",
            "acceptance": "unreviewed",
            "unknowns": [
                {"type": "deadline", "value": "2026-12-31"},
                {"type": "name", "value": "Priya"},
                {"type": "number", "value": "95%"},
            ],
        },
        {
            "span_id": "s3",
            "text": "Sprint velocity improved over the trailing average",
            "refs": [],
            "section": "progress",
            "kind": "inference",
            "support": "unknown",
            "acceptance": "unreviewed",
            "verified": False,
        },
        {
            "span_id": "s4",
            "text": "API Gateway degraded (risk_attention) -- accepted",
            "refs": ["decision:kan-7"],
            "section": "decisions",
            "kind": "decision",
            "support": "supported",
            "acceptance": "accepted",
            "support_record": {
                "method": "field_mapping",
                "source_version": "project:p1@r5",
                "source_refs": ["decision:kan-7"],
                "fields": ["title", "proposal_kind", "lifecycle"],
                "reviewer_ref": "principal:owner",
            },
        },
        {
            "span_id": "s5",
            "text": "Dependency: API Gateway -- at_risk",
            "refs": ["item:kan-7"],
            "section": "dependencies",
        },
    ]
    body_md = (
        "## Progress\n\n"
        "- Milestone [high]: Launch v2.0 -- planned\n"
        "- Priya expects the cut-over at 95% by 2026-12-31\n"
        "- **[UNVERIFIED]** Sprint velocity improved over the trailing average\n\n"
        "## Decisions\n\n"
        "- API Gateway degraded (risk_attention) -- accepted\n\n"
        "## Dependencies\n\n"
        "- Dependency: API Gateway -- at_risk\n"
    )
    now_iso = datetime.now().isoformat()
    with db._connection() as conn:
        conn.execute(
            """INSERT INTO project_updates
               (id, project_id, project_revision, review_id,
                lifecycle, draft_revision, body_md, claims_json,
                source_manifest_json, generator,
                generator_host, generator_model,
                created_at, updated_at)
               VALUES (?, ?, ?, ?, 'draft', ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (update_id, project_id, 0, None, 2, body_md,
             json.dumps(claims, separators=(",", ":")),
             "{}", "model:qwen3-32b", "192.168.1.43", "QWEN3 32B Q6",
             now_iso, now_iso),
        )
    return update_id


# copied verbatim from tests/e2e/test_hs175_room_glass.py

def _seed_project(name: str = "Ship the Q4 platform on schedule") -> str:
    from holdspeak.db import get_database
    db = get_database()
    project_id = f"proj-{uuid.uuid4().hex[:12]}"
    with db._connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO projects "
            "(id, name, description, keywords_json, team_members_json, "
            "context_json, detection_threshold, is_archived, revision, "
            "target_at, created_at, updated_at) "
            "VALUES (?, ?, '', '[]', '[]', '{}', 0.5, 0, 1, NULL, "
            "'2026-09-01T00:00:00', '2026-09-05T10:00:00')",
            (project_id, name),
        )
    return project_id

def _seed_meeting(
    meeting_id: str,
    title: str = "Standup",
    started_at: str = "2026-09-05T09:35:00",
    intel_status: str = "complete",
) -> None:
    from holdspeak.db import get_database
    db = get_database()
    now = started_at
    ended_at_dt = datetime.fromisoformat(started_at) + timedelta(minutes=30)
    ended_at = ended_at_dt.isoformat()
    with db._connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO meetings "
            "(id, started_at, ended_at, title, duration_seconds, "
            " intel_status, capture_status, transcription_status, "
            " provenance, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, 'finalized', "
            "'active', 'desktop', ?)",
            (meeting_id, now, ended_at, title, 1800.0, intel_status, now),
        )

def _link_meeting_project(meeting_id: str, project_id: str) -> None:
    from holdspeak.db import get_database
    db = get_database()
    with db._connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO meeting_projects (meeting_id, project_id) "
            "VALUES (?, ?)",
            (meeting_id, project_id),
        )

def _seed_intel_attempt(
    meeting_id: str,
    outcome: str = "success",
    created_at: str = "2026-09-05T10:00:00",
) -> None:
    from holdspeak.db import get_database
    db = get_database()
    with db._connection() as conn:
        job_id = f"job-{uuid.uuid4().hex[:8]}"
        conn.execute(
            "INSERT INTO intel_jobs "
            "(job_id, meeting_id, work_descriptor_sha256, transcript_hash, status) "
            "VALUES (?, ?, 'abc', 'def', 'completed')",
            (job_id, meeting_id),
        )
        conn.execute(
            "INSERT INTO intel_job_attempts "
            "(meeting_id, job_id, attempt, outcome, created_at) "
            "VALUES (?, ?, 1, ?, ?)",
            (meeting_id, job_id, outcome, created_at),
        )

def _seed_decision(meeting_id: str, text: str = "Refactor the API") -> str:
    from holdspeak.db import get_database
    db = get_database()
    rid = f"dr-{uuid.uuid4().hex[:8]}"
    sid = f"drs-{uuid.uuid4().hex[:8]}"
    with db._connection() as conn:
        conn.execute(
            "INSERT INTO decision_records "
            "(id, decision_text, source_type, source_id, created_at, updated_at) "
            "VALUES (?, ?, 'meeting', ?, datetime('now'), datetime('now'))",
            (rid, text, meeting_id),
        )
        conn.execute(
            "INSERT INTO decision_record_sources "
            "(id, record_id, source_type, source_ref, created_at) "
            "VALUES (?, ?, 'meeting', ?, datetime('now'))",
            (sid, rid, meeting_id),
        )
    return rid

def _seed_gh_watch(project_id: str) -> str:
    """Seed one GitHub Watch so GH + MTG rows appear together."""
    from holdspeak.db import get_database
    db = get_database()
    watch_id = f"w_gh_{uuid.uuid4().hex[:12]}"
    now_iso = datetime.now().isoformat(timespec="seconds")
    query = {"repository": "karolswdev/HoldSpeak"}
    with db._connection() as conn:
        db.automations.create_watch_in_transaction(
            conn,
            watch_id=watch_id,
            connector_id="gh",
            query_kind="pull_requests",
            name="GitHub PRs",
            query_json=json.dumps(query, sort_keys=True),
            enabled=True,
            schema_version="WatchSpec@1",
            project_id=project_id,
            intent="Track PRs",
            subject_kind="pull_requests",
            trigger_kind="poll",
            trigger_json="{}",
            mode="yolo",
            state="active",
            revision=1,
            baseline_state="",
            test_state="",
            created_at=now_iso,
            updated_at=now_iso,
        )
    return watch_id

def _ensure_meeting_watch(project_id: str) -> str | None:
    """Create the meeting Watch via the real seam."""
    from holdspeak.db import get_database
    from holdspeak.services.watch_service import ensure_meeting_watch
    db = get_database()
    result = ensure_meeting_watch(db, project_id)
    return result.get("id") if result else None

def _seed_future_linked_event(project_id: str) -> "datetime":
    """A calendar event two days out at 14:00Z linked to the Room -- the
    product's own source of NEXT (C9c).  Returns the aware start instant."""
    from datetime import timezone
    from holdspeak.db import get_database
    db = get_database()
    starts = (datetime.now(timezone.utc) + timedelta(days=2)).replace(
        hour=14, minute=0, second=0, microsecond=0,
    )
    ends = starts + timedelta(hours=1)
    fmt = lambda d: d.isoformat().replace("+00:00", "Z")  # noqa: E731 -- verbatim
    eid = f"ce_{uuid.uuid4().hex[:12]}"
    with db._connection() as conn:
        conn.execute(
            """INSERT INTO calendar_events
               (id, uid, title, starts_at, ends_at, last_seen_at,
                subscription_revision, source_id, source_label)
               VALUES (?, ?, 'Sprint Planning', ?, ?, ?, 'rev', 'src-1', 'WORK')""",
            (eid, f"uid-{eid}", fmt(starts), fmt(ends), datetime.now().timestamp()),
        )
        conn.execute(
            "INSERT INTO calendar_event_projects (calendar_event_id, project_id, match_source) "
            "VALUES (?, ?, 'title')",
            (eid, project_id),
        )
    return starts

def _seed_room_with_meetings(project_id: str) -> tuple[str, str]:
    """Seed two RECORDED meetings (both in the past -- the only state the
    product produces) and one FUTURE calendar event linked to the Room.

    Creates the meeting Watch through the real seam (ensure_meeting_watch).
    Also seeds one GH Watch so all source rows appear together.

    Returns (past_meeting_id, recent_meeting_id).
    """
    now = datetime.now()
    # Past meeting: two days ago
    past_dt = now - timedelta(days=2)
    past_iso = past_dt.replace(hour=10, minute=0, second=0, microsecond=0).isoformat()
    past_mid = f"mtg-past-{uuid.uuid4().hex[:8]}"
    _seed_meeting(past_mid, title="Architecture Review", started_at=past_iso)
    _link_meeting_project(past_mid, project_id)
    _seed_intel_attempt(past_mid, created_at=past_iso)
    _seed_decision(past_mid, text="Refactor the API layer")

    # Recent meeting: yesterday (recorded; intel off)
    recent_dt = now - timedelta(days=1)
    recent_iso = recent_dt.replace(hour=14, minute=0, second=0, microsecond=0).isoformat()
    recent_mid = f"mtg-recent-{uuid.uuid4().hex[:8]}"
    _seed_meeting(recent_mid, title="Sprint Planning", started_at=recent_iso,
                  intel_status="disabled")
    _link_meeting_project(recent_mid, project_id)

    # Create the meeting Watch via the real seam
    _ensure_meeting_watch(project_id)

    # Seed one GH Watch so GH + MTG rows appear together
    _seed_gh_watch(project_id)

    return past_mid, recent_mid


# copied verbatim from tests/e2e/room_glass_helpers.py (it seeded the parked
# test_philo10_02_nudge_unknown_glass.py); `_api` below speaks to the
# recorder's hub instead of a page.
TOKEN = "hs173-health"
_NUDGE_HUB: list[Any] = []


def _api(_page: Any, method: str, path: str, body: Any = None, token: str | None = None) -> Any:
    return _NUDGE_HUB[-1].ok(method, path, body)


def _seed_nudge_project_and_step(page: Any) -> tuple[str, str]:
    """Seed a project, People relationship with alias, Watch PRs,
    steward policy enabling github_comment, and a proposed nudge step.
    Returns (project_id, step_id)."""
    from holdspeak.db import get_database
    from datetime import datetime, timedelta, timezone as _tz
    db = get_database()
    now = datetime.now(_tz.utc)
    project_id = f"proj-nudge-{uuid.uuid4().hex[:8]}"

    # 1. Seed project
    with db._connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO projects "
            "(id, name, description, keywords_json, team_members_json, "
            "context_json, detection_threshold, is_archived, revision, "
            "target_at, created_at, updated_at) "
            "VALUES (?, ?, '', '[]', '[]', '{}', 0.5, 0, 1, NULL, ?, ?)",
            (project_id,
             "Ship the Q4 platform on schedule with zero incidents",
             now.isoformat(), now.isoformat()),
        )

    # 2. Seed Watch with PR entities (reviewer = ania-k)
    pr_entities = [
        {
            "number": 612,
            "title": "Rig settles animations before every shot",
            "url": "https://github.com/org/repo/pull/612",
            "state": "OPEN",
            "isDraft": False,
            "reviewRequests": ["ania-k"],
            "reviewDecision": None,
            "checks": "success",
            "headRefOid": "abc123",
            "updatedAt": (now - timedelta(hours=6)).isoformat(),
            "createdAt": (now - timedelta(days=3)).isoformat(),
        },
    ]
    snapshot = json.dumps(pr_entities)
    watch_id = f"watch-{project_id}-pr"
    with db._connection() as conn:
        conn.execute(
            "INSERT INTO connector_watches "
            "(id, connector_id, query_kind, name, query_json, snapshot_json, "
            " enabled, last_success_at, last_error, project_id, "
            " created_at, updated_at) "
            "VALUES (?, 'gh', 'pull_requests', 'PRs', "
            "'{}', ?, 1, datetime('now'), NULL, ?, datetime('now'), datetime('now'))",
            (watch_id, snapshot, project_id),
        )

    # 3. Set up People store and create a relationship via API
    _api(page, "POST", "/api/people/setup", {}, token=TOKEN)
    result = _api(page, "POST", "/api/people/relationships", {
        "display_name": "Ania Kowalska",
        "relationship_kind": "direct_report",
    }, token=TOKEN)
    payload = result.get("payload", result)
    rel_id = payload["relationship"]["id"]

    # Add owner alias matching the reviewer login
    _api(page, "POST", f"/api/people/relationships/{rel_id}/owner-aliases", {
        "alias": "ania-k",
    }, token=TOKEN)

    # 4. Seed steward policy with github_comment eligible
    policy_id = f"pol-{uuid.uuid4().hex[:8]}"
    now_iso = now.isoformat(timespec="seconds")
    with db._connection() as conn:
        conn.execute(
            "INSERT INTO steward_policies "
            "(id, project_id, eligible_effect_kinds_json, yolo_flags_json, "
            " max_retries, max_actions_per_run, cooldown_seconds, "
            " bounds_json, enabled, unattended_enabled, nudge_template, "
            " created_at, updated_at) "
            'VALUES (?, ?, \'["github_comment"]\', \'{}\', 3, 10, 0, '
            "'{}', 1, 0, '', ?, ?)",
            (policy_id, project_id, now_iso, now_iso),
        )

    # 5. Seed a steward run + proposed nudge step
    run_id = f"run-{uuid.uuid4().hex[:8]}"
    step_id = f"step-{uuid.uuid4().hex[:8]}"
    with db._connection() as conn:
        conn.execute(
            "INSERT INTO steward_runs "
            "(id, project_id, state, phase, summary_json, created_at, updated_at) "
            "VALUES (?, ?, 'running', 'act', '{}', ?, ?)",
            (run_id, project_id, now_iso, now_iso),
        )
        nudge_payload = json.dumps({
            "repo": "org/repo",
            "pr_number": 612,
            "pr_title": "Rig settles animations before every shot",
            "pr_url": "https://github.com/org/repo/pull/612",
            "reviewer_login": "ania-k",
            "display_name": "Ania Kowalska",
            "days": 3,
            "comment_text": "This PR has been waiting for review for 3 days. Flagged by HoldSpeak.",
            "host": "github.com",
        })
        conn.execute(
            "INSERT INTO steward_steps "
            "(id, run_id, phase, seq, effect_kind, state, "
            " expected_state_json, observed_state_json, "
            " idempotency_key, receipt_json, created_at, updated_at) "
            "VALUES (?, ?, 'act', 1, 'github_comment', 'proposed', "
            " ?, '{}', ?, '{}', ?, ?)",
            (step_id, run_id, nudge_payload,
             f"nudge:{project_id}:org/repo:612:ania-k",
             now_iso, now_iso),
        )

    return project_id, step_id


def _patch_resolve_review_people(monkeypatch: pytest.MonkeyPatch) -> None:
    """Patch _resolve_review_people to return a resolved bottleneck person
    matching reviewer login 'ania-k' to display name 'Ania Kowalska'.
    In isolated HOME the encrypted People store may not match the alias."""
    import holdspeak.services.project_service as ps

    _orig = ps.ProjectService._resolve_review_people

    def _patched(self: Any, project_id: str, per_reviewer: list, threshold_days: float = 2.0) -> list:
        # Try the real resolver first
        result = _orig(self, project_id, per_reviewer, threshold_days)
        if result:
            return result
        # Fall back: synthesize from per_reviewer for the test alias
        for rev in per_reviewer:
            login = rev.get("login", "")
            if login == "ania-k" and rev.get("median_days", 0) >= threshold_days:
                result.append({
                    "relationship_id": "rel-ania-test",
                    "display_name": "Ania Kowalska",
                    "login": "ania-k",
                    "median_days": rev["median_days"],
                    "count": rev["count"],
                })
        return result

    monkeypatch.setattr(ps.ProjectService, "_resolve_review_people", _patched)



SEEDS173 = SimpleNamespace(_seed_model_draft=_seed_model_draft, _seed_deterministic_draft=_seed_deterministic_draft)
SEEDS200 = SimpleNamespace(_seed_mixed_update=_seed_mixed_update)
SEEDS10 = SimpleNamespace(_seed_nudge_project_and_step=_seed_nudge_project_and_step,
                          _patch_resolve_review_people=_patch_resolve_review_people)
SEEDS175 = SimpleNamespace(_seed_project=_seed_project, _seed_meeting=_seed_meeting, _link_meeting_project=_link_meeting_project, _seed_intel_attempt=_seed_intel_attempt, _seed_decision=_seed_decision, _seed_gh_watch=_seed_gh_watch, _ensure_meeting_watch=_ensure_meeting_watch, _seed_future_linked_event=_seed_future_linked_event, _seed_room_with_meetings=_seed_room_with_meetings)


def _answer(resp: Any) -> Any:
    body = resp.json() if resp.content else {}
    if resp.status_code >= 400:
        return {"__status": resp.status_code, "body": body}
    return body


def _gets(hub: Any, pid: str, *groups: tuple[str, ...]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for group in groups:
        for template in group:
            path = template.format(pid=pid)
            out[path] = _answer(hub.client.get(path))
    # The Room's model-route read is a POST that reads (assignmentExperience.ts).
    editor = {"scope": {"kind": "subject", "subject_kind": "project", "subject_id": pid,
                        "capability_id": "ask.answer"}, "capability_id": "ask.answer"}
    out["POST /api/inference/assignments/editor"] = _answer(
        hub.client.post("/api/inference/assignments/editor", json=editor))
    if UPDATE_GETS in groups:
        out.update(_update_gets(hub, pid))
    # The SEND well of each decision record the Room lists (documentSends.tsx).
    from urllib.parse import quote

    room = out.get(f"/api/projects/{pid}/room")
    for item in ((room or {}).get("decisions") or {}).get("items") or []:
        if item.get("kind") == "decision" and item.get("id"):
            path = f"/api/channels/sends?document_ref={quote('decision_record:' + item['id'], safe='')}"
            out[path] = _answer(hub.client.get(path))
    # The read marker the Room posts after its first paint (last: it moves
    # the Room's since-read line).
    if any("/room" in t for group in groups for t in group):
        out[f"POST /api/projects/{pid}/room/read"] = _answer(hub.client.post(f"/api/projects/{pid}/room/read"))
    return out


def _call(hub: Any, method: str, path: str, body: Any = None) -> dict[str, Any]:
    resp = hub.client.request(method, path, json=body)
    return {"method": method, "path": path, "request": body, "status": resp.status_code, "answer": _answer(resp)}


def _boot(name: str, **kwargs: Any) -> tuple[pytest.MonkeyPatch, Any, Any]:
    mp = pytest.MonkeyPatch()
    tmp = Path(tempfile.mkdtemp(prefix=f"room-wires-{name}-"))
    cm = rig._hub(tmp, mp, **kwargs)
    hub = cm.__enter__()
    return mp, cm, hub


def _run(name: str, body: Callable[[Any, pytest.MonkeyPatch], dict[str, Any]], **kwargs: Any) -> dict[str, Any]:
    mp, cm, hub = _boot(name, **kwargs)
    try:
        return body(hub, mp)
    finally:
        cm.__exit__(None, None, None)
        mp.undo()


def _project(hub: Any, name: str, command_id: str) -> str:
    created = hub.ok("POST", "/api/projects", {"name": name, "description": f"Seeded for {command_id}.",
                                                 "command_id": command_id})
    return created["project"]["id"]


# ── HS-173-02: the Update editor, a model draft and a deterministic one ──


def update173(hub: Any, _mp: pytest.MonkeyPatch) -> dict[str, Any]:
    seeds = SEEDS173
    model = _project(hub, "Update 173 Glass Project", "hs173-update-create-proj")
    seeds._seed_model_draft(model)
    det = _project(hub, "Update 173 Deterministic", "hs173-update-create-det")
    seeds._seed_deterministic_draft(det)
    return {
        "model": {"pid": model, "gets": _gets(hub, model, ROOM_GETS, UPDATE_GETS)},
        "deterministic": {"pid": det, "gets": _gets(hub, det, ROOM_GETS, UPDATE_GETS)},
    }


# ── HS-200-06: the claim axes, a real draft then a real edit; every state ──


def claims200(hub: Any, _mp: pytest.MonkeyPatch) -> dict[str, Any]:
    seeds = SEEDS200
    real = _project(hub, "Claim Axes Glass", "hs200-claim-glass-proj-1")
    for ordinal, (item_type, title, lifecycle, severity, details) in enumerate((
        ("milestone", "Launch v2.0", "planned", "high", {}),
        ("risk", "Vendor lock-in", "open", "critical", {"likelihood": "medium", "impact": "high"}),
        ("dependency", "API Gateway", "at_risk", "medium",
         {"direction": "upstream", "counterpart_ref": "project:platform"}),
    )):
        hub.ok("POST", f"/api/projects/{real}/items", {
            "item_type": item_type, "title": title, "lifecycle": lifecycle, "severity": severity,
            "details": details, "command_id": f"hs200-claim-glass-item-{ordinal}"})
    drafted = hub.ok("POST", f"/api/projects/{real}/updates/draft",
                     {"generator": "deterministic", "command_id": "hs200-claim-glass-draft-1"})["update"]
    claims = json.loads(drafted["claims_json"])
    edited = drafted["body_md"].replace(claims[0]["text"], "Launch slipped, the owner rewrote this")
    put = _call(hub, "PUT", f"/api/updates/{drafted['id']}",
                {"body_md": edited, "command_id": "hs200-claim-glass-save-1"})
    mixed = _project(hub, "Mixed Claims Glass", "hs200-claim-glass-proj-2")
    seeds._seed_mixed_update(mixed)
    return {
        "real": {"pid": real, "drafted": drafted, "edit": put, "gets": _gets(hub, real, ROOM_GETS, UPDATE_GETS)},
        "mixed": {"pid": mixed, "gets": _gets(hub, mixed, ROOM_GETS, UPDATE_GETS)},
    }


# ── PHILO-10-02: the nudge whose gh answer never came back ──


def nudge10(hub: Any, mp: pytest.MonkeyPatch) -> dict[str, Any]:
    import holdspeak.services.channel_cli as channel_cli
    import holdspeak.services.project_steward_service as pss
    seeds = SEEDS10

    calls: list[list[str]] = []

    def gh(argv: Any, **_kwargs: Any) -> Any:  # the browser test's gh edge: the process times out
        calls.append(list(argv))
        raise subprocess.TimeoutExpired(list(argv), 30)

    mp.setattr(channel_cli, "CLI_RUNNER", gh)
    original = pss.ProjectStewardService.send_nudge

    def send_nudge(self: Any, principal: Any, step_id: str, text: str) -> dict:
        self._subprocess_runner = gh
        return original(self, principal, step_id, text)

    mp.setattr(pss.ProjectStewardService, "send_nudge", send_nudge)
    seeds._patch_resolve_review_people(mp)
    _NUDGE_HUB.append(hub)
    pid, step = seeds._seed_nudge_project_and_step(None)
    before = _gets(hub, pid, ROOM_GETS)
    nudges = hub.ok("GET", f"/api/projects/{pid}/nudges?state=proposed")
    text = next(n for n in nudges["nudges"] if n["step_id"] == step)["comment_text"]
    send = _call(hub, "POST", f"/api/nudges/{step}/send", {"text": text})
    after = _gets(hub, pid, ROOM_GETS)
    return {"pid": pid, "step": step, "before": before, "send": send, "after": after,
            "gh_comment_calls": len([c for c in calls if c[:3] == ["gh", "pr", "comment"]])}


# ── HS-175-04: the meeting source row, Pause and Resume; a Room with none ──


def hs175(hub: Any, _mp: pytest.MonkeyPatch) -> dict[str, Any]:
    seeds = SEEDS175
    pid = seeds._seed_project()
    seeds._seed_room_with_meetings(pid)
    starts = seeds._seed_future_linked_event(pid)
    before = _gets(hub, pid, ROOM_GETS)
    from holdspeak.db import get_database

    watch = next(w for w in get_database().automations.list_project_watches(pid) if w.get("connector_id") == "meeting")
    pause = _call(hub, "POST", f"/api/watches/{watch['id']}/pause", {})
    paused = _gets(hub, pid, ROOM_GETS)
    resume = _call(hub, "POST", f"/api/watches/{watch['id']}/resume", {})
    resumed = _gets(hub, pid, ROOM_GETS)
    empty = seeds._seed_project("Empty Room")
    return {
        "pid": pid, "next_starts": starts.isoformat(), "watch": watch["id"],
        "before": before, "pause": pause, "paused": paused, "resume": resume, "resumed": resumed,
        "empty": {"pid": empty, "gets": _gets(hub, empty, ROOM_GETS)},
    }


# ── HS-173-04: the Steward policy's sixth row, checked and saved ──


def policy173(hub: Any, _mp: pytest.MonkeyPatch) -> dict[str, Any]:
    pid = _project(hub, "Policy 173 Glass Project", "hs173-policy-create-proj")
    before = _gets(hub, pid, ROOM_GETS, STEWARD_GETS)
    policy = before[f"/api/projects/{pid}/steward/policy"].get("policy")
    watches = before[f"/api/projects/{pid}/watches"].get("watches") or []
    # The face's PUT (useStewardController.ts savePolicy): its draft, the
    # sixth kind checked. The test asserts the face sends exactly this.
    draft = {
        "eligible_effect_kinds": list(policy["eligible_effect_kinds"]) if policy else [],
        "max_retries": policy["max_retries"] if policy else 3,
        "max_actions_per_run": policy["max_actions_per_run"] if policy else 10,
        "cooldown_seconds": policy["cooldown_seconds"] if policy else 0,
        "enabled": policy["enabled"] if policy else True,
        "unattended_enabled": policy["unattended_enabled"] if policy else False,
        "evaluation_cadence_minutes": watches[0]["evaluation_cadence_minutes"] if watches else 60,
        "nudge_template": policy.get("nudge_template") if policy else None,
    }
    draft["eligible_effect_kinds"].append("github_comment")
    save = _call(hub, "PUT", f"/api/projects/{pid}/steward/policy", draft)
    after = _gets(hub, pid, STEWARD_GETS)
    return {"pid": pid, "before": before, "save": save, "after": after}


# ── HS-164-06: two unattended ticks; a source whose circuit opens and heals ──


def _steward_detail(hub: Any, pid: str) -> dict[str, Any]:
    out = _gets(hub, pid, ROOM_GETS, STEWARD_GETS)
    for run in out[f"/api/projects/{pid}/steward/runs"].get("runs", []):
        out[f"/api/steward/runs/{run['id']}"] = _answer(hub.client.get(f"/api/steward/runs/{run['id']}"))
    return out


def hs164(name: str) -> dict[str, Any]:
    from holdspeak.services.watch_service import CIRCUIT_FAILURE_THRESHOLD

    tmp = Path(tempfile.mkdtemp(prefix=f"room-wires-{name}-"))
    fixture = tmp / "gh_fixture.json"
    rig.hs164_write_fixture(fixture, {"stdout": rig.HS164_GH_PR_SNAPSHOT_BASELINE, "returncode": 0})
    mp = pytest.MonkeyPatch()
    try:
        with rig._hub(tmp, mp, gh_runner=rig.hs164_fixture_runner(fixture)) as hub, \
                rig.hs164_conductor(hub) as tick:
            pid = rig.hs164_seed_room(hub)
            if name == "hs164_gate":
                watch = rig.hs164_seed_graduated_watch(hub.db, pid)
                outcomes = []
                for snapshot in (rig.HS164_GH_PR_SNAPSHOT_TICK1, rig.HS164_GH_PR_SNAPSHOT_TICK2):
                    rig.hs164_write_fixture(fixture, {"stdout": snapshot, "returncode": 0})
                    rig.hs164_due_now(hub.db, watch)
                    outcomes.append(tick())
                return {"pid": pid, "ticks": outcomes, "gets": _steward_detail(hub, pid)}
            watch = rig.hs164_seed_graduated_watch(hub.db, pid, watch_id="cw_circuit_glass_001")
            rig.hs164_write_fixture(fixture, {"stdout": "", "returncode": 1, "stderr": "Connection timeout"})
            failing = []
            for _ in range(CIRCUIT_FAILURE_THRESHOLD):
                rig.hs164_due_now(hub.db, watch)
                failing.append(tick()[0])
            opened = _gets(hub, pid, ROOM_GETS, STEWARD_GETS)
            rig.hs164_write_fixture(fixture, {"stdout": rig.HS164_GH_PR_SNAPSHOT_TICK1, "returncode": 0})
            with hub.db._connection() as conn:  # the glass's own cooldown bypass
                conn.execute("UPDATE connector_watches SET circuit_opened_at=?, next_evaluation_at=? WHERE id=?",
                             ((datetime.now() - timedelta(hours=1)).isoformat(),
                              (datetime.now() - timedelta(minutes=5)).isoformat(), watch))
            recovery = tick()[0]
            healed = _gets(hub, pid, ROOM_GETS, STEWARD_GETS)
            return {"pid": pid, "failing": failing, "opened": opened, "recovery": recovery, "healed": healed}
    finally:
        mp.undo()


# ── HS-174-07: the Door's Confluence row, signed in and not ──


def _fake_acli_runner(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
    """Copied verbatim from tests/e2e/test_hs174_door_confluence_glass.py (parked)."""
    cmd = args[0] if args else kwargs.get("args", [])
    cmd_str = " ".join(str(c) for c in cmd) if isinstance(cmd, (list, tuple)) else str(cmd)
    if "auth" in cmd_str and "status" in cmd_str:
        return subprocess.CompletedProcess(
            cmd, 0, stdout='{"authenticated":true,"site":"karolswdev.atlassian.net","email":"karolsane@gmail.com"}',
            stderr="")
    if "space" in cmd_str and "list" in cmd_str:
        return subprocess.CompletedProcess(cmd, 0, stdout='[{"key":"GOV","name":"Governance","type":"global"}]',
                                           stderr="")
    return subprocess.CompletedProcess(cmd, 0, stdout="{}", stderr="")


def _seed_confluence_connection(db: Any, state: str) -> None:
    """The glass's own row (test_hs174_door_confluence_glass.py `_seed_confluence_connection`)."""
    ref = "karolswdev.atlassian.net|karolsane@gmail.com"
    with db._connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO watch_provider_connections "
            "(id, provider_id, external_connection_ref, state, "
            " last_connected_at, last_checked_at, created_at, updated_at) "
            "VALUES (?, 'confluence', ?, ?, "
            " datetime('now'), datetime('now'), datetime('now'), datetime('now'))",
            (f"wpc-confluence-{ref}", ref, state),
        )


def door174(hub: Any, _mp: pytest.MonkeyPatch) -> dict[str, Any]:
    out: dict[str, Any] = {}
    _seed_confluence_connection(hub.db, "connected")
    out["connected"] = {"/api/connections": _answer(hub.client.get("/api/connections"))}
    with hub.db._connection() as conn:
        conn.execute("UPDATE watch_provider_connections SET state='owner_action_required' "
                     "WHERE provider_id='confluence'")
    out["not_connected"] = {"/api/connections": _answer(hub.client.get("/api/connections"))}
    return out


# ── PHILO-17 sources: Add a repository in the Room; Go ▸ Projects ──


# The Door's rows as the face sends them (useDoorController.ts: GITHUB_DEFAULTS
# OPEN PRS + CI on, adjust {base: "main"}); the test asserts the face sends these.
ADD_SOURCES = [{"provider": "github", "scope": "acme/app", "watches": ["open_prs", "ci"], "adjust": {"base": "main"}}]


def sources17(hub: Any, _mp: pytest.MonkeyPatch) -> dict[str, Any]:
    pid = hub.ok("POST", "/api/projects/door", {"outcome": "Ledger cutover"})["projectId"]
    hub.ok("POST", "/api/connections/github/recheck", {})
    before = _gets(hub, pid, ROOM_GETS)
    before["/api/providers/github/discover"] = _answer(hub.client.get("/api/providers/github/discover"))
    before["/api/projects"] = _answer(hub.client.get("/api/projects"))
    count = _call(hub, "POST", "/api/projects/door/count", COUNT_BODY)
    add = _call(hub, "POST", "/api/projects/door", {"project_id": pid, "sources": ADD_SOURCES})
    after = _gets(hub, pid, ROOM_GETS)
    after["/api/providers/github/discover"] = before["/api/providers/github/discover"]
    again = _call(hub, "POST", "/api/projects/door", {"project_id": pid, "sources": ADD_SOURCES})
    return {"pid": pid, "before": before, "count": count, "add": add, "after": after, "again": again}


COUNT_BODY: dict[str, Any] = {"provider": "github", "scope": "acme/app", "watches": ["open_prs", "ci"], "adjust": {"base": "main"}}


# ── HS-174-04: the Room's writes, one remote and one local ──


def receipts174(hub: Any, _mp: pytest.MonkeyPatch) -> dict[str, Any]:
    """The seed of tests/e2e/_parked/test_hs174_receipts_glass.py::_room_receipts_leg:
    the LOCAL write is minted by the real route (POST items -> create_item, observed
    into pipeline_events); the REMOTE write is a seeded pipeline event (minting it for
    real needs the remote listener and a non-loopback client)."""
    import time as _time

    pid = _project(hub, "Q4 Platform", "hs174-receipts-proj")
    hub.ok("POST", f"/api/projects/{pid}/items", {
        "item_type": "milestone", "title": "Write the cutover runbook", "command_id": "hs174-item"})
    with hub.db._connection() as conn:
        conn.execute(
            """INSERT INTO pipeline_events
               (event_id, timestamp, service, method,
                principal_kind, principal_identity, args_summary,
                result_summary, error, error_code, duration_ms,
                correlation_id, is_async, origin, caller, caller_identity)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (f"ev-{uuid.uuid4().hex[:12]}", _time.time(), "ProjectService", "update_project",
             "agent", "sweep-runner", json.dumps({"project_id": pid}), json.dumps({"id": pid}),
             None, None, 42.0, str(uuid.uuid4()), 0, "remote", "192.168.1.43", "sweep-runner"),
        )
    return {"pid": pid, "gets": _gets(hub, pid, ROOM_GETS)}


# ── PHILO-17 sources: Park from FILES; the row leaves on the hub's frame ──


def files17(name: str) -> dict[str, Any]:
    """The browser test's lone meeting (test_desk_project_room.py's copy of
    `_seed_lone_meeting`); Park through the Meeting delete route, with the
    desk_changed frames the hub broadcasts for it captured; Restore."""
    from holdspeak.meeting_session import IntelSnapshot, MeetingState, TranscriptSegment
    from holdspeak.web_server import MeetingWebServer

    frames: list[dict[str, Any]] = []
    mp = pytest.MonkeyPatch()
    mp.setattr(MeetingWebServer, "broadcast", lambda _self, kind, data: frames.append({"type": kind, "data": data}))
    tmp = Path(tempfile.mkdtemp(prefix=f"room-wires-{name}-"))
    try:
        with rig._hub(tmp, mp, gh_runner=rig._gh_not_signed_in) as hub:
            db = hub.db
            start = datetime.now().replace(microsecond=0) - timedelta(hours=2)
            db.projects.create_project(project_id="p-lone", name="Vendor review", description="One meeting.",
                                       keywords=["vendor"])
            db.meetings.save_meeting(MeetingState(
                id="m-lone", started_at=start, ended_at=start + timedelta(minutes=30), title="Vendor call",
                segments=[TranscriptSegment(text="We pick the vendor.", speaker="Me", start_time=1.0, end_time=4.0)],
                intel=IntelSnapshot(timestamp=1.0, topics=["vendor"], summary="Pick it.", action_items=[]),
                intel_status="completed"))
            db.projects.associate_meeting_project(meeting_id="m-lone", project_id="p-lone", source="manual",
                                                  confidence=1.0)
            before = _gets(hub, "p-lone", ROOM_GETS)
            frames.clear()
            park = _call(hub, "DELETE", "/api/meetings/m-lone")
            park_frames = list(frames)
            parked = _gets(hub, "p-lone", ROOM_GETS)
            frames.clear()
            restore = _call(hub, "POST", "/api/meetings/m-lone/restore")
            restore_frames = list(frames)
            restored = _gets(hub, "p-lone", ROOM_GETS)
            return {"pid": "p-lone", "before": before, "park": park, "park_frames": park_frames, "parked": parked,
                    "restore": restore, "restore_frames": restore_frames, "restored": restored}
    finally:
        mp.undo()


def main() -> int:
    ROOM_DIR.mkdir(parents=True, exist_ok=True)
    STEWARD_DIR.mkdir(parents=True, exist_ok=True)
    DOOR_DIR.mkdir(parents=True, exist_ok=True)
    wanted = set(sys.argv[1:])
    jobs: list[tuple[Path, str, Callable[..., dict[str, Any]], dict[str, Any]]] = [
        (ROOM_DIR, "update173", update173, {}),
        (ROOM_DIR, "claims200", claims200, {}),
        (ROOM_DIR, "nudge10", nudge10, {}),
        (ROOM_DIR, "hs175", hs175, {}),
        (STEWARD_DIR, "policy173", policy173, {}),
        (DOOR_DIR, "door174", door174, {"acli_runner": _fake_acli_runner}),
        (ROOM_DIR, "sources17", sources17, {"gh_runner": rig._gh_signed_in}),
        (ROOM_DIR, "receipts174", receipts174, {}),
    ]
    for name, folder, job in (("hs164_gate", STEWARD_DIR, hs164), ("hs164_circuit", STEWARD_DIR, hs164),
                              ("files17", ROOM_DIR, files17)):
        if wanted and name not in wanted:
            continue
        data = {"schema": "room-recorded@1", "recordedBy": "scripts/record_room_wires.py", **job(name)}
        out = folder / f"{name}.json"
        out.write_text(json.dumps(data, indent=1, sort_keys=True, default=str) + "\n", encoding="utf-8")
        print(f"wrote {out.relative_to(REPO)} ({out.stat().st_size} bytes)")
    for folder, name, job, kwargs in jobs:
        if wanted and name not in wanted:
            continue
        data = {"schema": "room-recorded@1", "recordedBy": "scripts/record_room_wires.py", **_run(name, job, **kwargs)}
        out = folder / f"{name}.json"
        out.write_text(json.dumps(data, indent=1, sort_keys=True, default=str) + "\n", encoding="utf-8")
        print(f"wrote {out.relative_to(REPO)} ({out.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
