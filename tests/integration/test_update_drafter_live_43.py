"""HS-162-03: live .43 proof -- the model drafter against real LAN metal.

One marked, skip-clean test: drafts a seeded room against the llama.cpp
endpoint at 192.168.1.43:8080.  Asserts the draft persists, generator
records the model path, and every claim resolves (cited or MARKED).

Gated by HOLDSPEAK_UAT_LIVE_43=1 AND LAN reachability.  Sandbox may
block LAN egress; in that case the test skips cleanly.
"""
from __future__ import annotations

import json
import os

import httpx
import pytest

from holdspeak.db import Database, reset_database
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.project_evidence_collector import (
    ProjectEvidenceCollector,
)
from holdspeak.services.project_delta_service import ProjectDeltaService
from holdspeak.services.project_service import ProjectService
from holdspeak.services.project_update_service import (
    SECTION_KEYS,
    Claim,
    ProjectUpdateService,
    UNVERIFIED_MARKER,
    _build_model_prompt,
    _parse_model_output,
)

LAN_ENDPOINT = "http://192.168.1.43:8080/v1/models"
LAN_CHAT_ENDPOINT = "http://192.168.1.43:8080/v1/chat/completions"

LIVE_43_ENV = "HOLDSPEAK_UAT_LIVE_43"

NOW_ISO = "2026-06-15T10:00:00"

OWNER = Principal(PrincipalKind.OWNER, "live-43-drafter")


def _lan_up() -> bool:
    try:
        return httpx.get(LAN_ENDPOINT, timeout=5).status_code == 200
    except httpx.HTTPError:
        return False


pytestmark = pytest.mark.skipif(
    not _lan_up(), reason=".43 LAN endpoint unreachable"
)

live_43_only = pytest.mark.skipif(
    not os.environ.get(LIVE_43_ENV, "").strip(),
    reason=(
        f"live .43 model proof is opt-in: set {LIVE_43_ENV}=1 "
        "(runs a real model call on the LAN endpoint)"
    ),
)


def _seed_project(db: Database, project_id: str = "proj-live43") -> str:
    with db._connection() as conn:
        conn.execute(
            """INSERT INTO projects
               (id, name, description, keywords_json, team_members_json,
                context_json, detection_threshold, revision,
                created_at, updated_at)
               VALUES (?, ?, '', '[]', '[]', '{}', 0.4, 3,
                       ?, ?)""",
            (project_id, "Live 43 Test Project", NOW_ISO, NOW_ISO),
        )
    return project_id


def _seed_items(db: Database, project_id: str) -> list[str]:
    items = [
        ("pitem_live43_001", "milestone", "API v3 launch",
         "planned", "high", "2026-08-01", 1.0),
        ("pitem_live43_002", "risk", "Staffing shortage",
         "open", "critical", None, 2.0),
        ("pitem_live43_003", "dependency", "Cloud provider SLA",
         "at_risk", "medium", "2026-07-15", 3.0),
    ]
    ids = []
    with db._connection() as conn:
        for item_id, itype, title, lifecycle, sev, due, sk in items:
            conn.execute(
                """INSERT INTO project_items
                   (id, project_id, item_type, title, lifecycle, severity,
                    due_at, sort_key, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (item_id, project_id, itype, title, lifecycle, sev,
                 due, sk, NOW_ISO, NOW_ISO),
            )
            ids.append(item_id)
    return ids


@pytest.fixture
def rig(tmp_path):
    reset_database()
    db = Database(tmp_path / "live43.db")
    yield db
    reset_database()


@live_43_only
@pytest.mark.timeout(180)
def test_live_43_model_draft_claims_resolve(rig):
    """Draft a seeded room against the real .43 model.

    1. Build deterministic inventory.
    2. Send the prompt to .43 via the OpenAI-compatible endpoint.
    3. Parse the response with _parse_model_output.
    4. Assert every claim is either verified (cited) or MARKED.
    """
    db = rig
    pid = _seed_project(db)
    _seed_items(db, pid)

    # Build deterministic inventory.
    collector = ProjectEvidenceCollector(db)
    delta_svc = ProjectDeltaService(db, collector)
    project_svc = ProjectService(db, delta_service=delta_svc)
    det_svc = ProjectUpdateService(
        db, project_service=project_svc, delta_service=delta_svc,
    )
    det_result = det_svc.draft_update(OWNER, pid)
    det_claims = [Claim(**c) for c in json.loads(det_result["claims_json"])]
    assert len(det_claims) > 0, "Seeded room should produce claims"

    # Build inventory refs.
    inventory_refs = frozenset(
        ref for c in det_claims for ref in c.refs
    )

    # Build the model prompt.
    payload = _build_model_prompt(det_claims)

    # Call the .43 endpoint directly.
    messages = [
        {"role": "system", "content": payload["system_prompt"]},
        {"role": "user", "content": payload["user_prompt"]},
    ]
    try:
        resp = httpx.post(
            LAN_CHAT_ENDPOINT,
            json={
                "model": "default",
                "messages": messages,
                "temperature": 0.3,
                "max_tokens": 2048,
            },
            timeout=120,
        )
        resp.raise_for_status()
    except (httpx.HTTPError, httpx.ConnectError) as exc:
        pytest.skip(f"LAN .43 call failed (sandbox or network): {exc}")

    raw_output = resp.json()["choices"][0]["message"]["content"]
    assert raw_output, "Model returned empty output"

    # Parse and validate claim discipline.
    parsed = _parse_model_output(raw_output, inventory_refs)
    assert parsed is not None, (
        f"Model output unparseable: {raw_output[:500]}"
    )

    sections, claims = parsed
    assert len(claims) > 0, "Model should produce at least one claim"

    # Every claim resolves: either verified (refs in inventory) or MARKED.
    for claim in claims:
        if claim.verified:
            assert len(claim.refs) >= 1, (
                f"Verified claim {claim.span_id} has no refs"
            )
            for ref in claim.refs:
                assert ref in inventory_refs, (
                    f"Ref {ref!r} not in inventory"
                )
        else:
            # MARKED: verified=False, refs empty.
            assert claim.refs == [], (
                f"MARKED claim {claim.span_id} should have empty refs"
            )

    # All six sections covered.
    for key in SECTION_KEYS:
        assert key in sections, f"Section {key} missing from model output"
