"""HS-200-06 real-hub glass: the three claim axes on the update face.

Two legs, both against a real booted hub with an isolated HOME:

  1. REAL DRAFT (1440): a project with three items drafts a real
     deterministic update through the product's own routes.  Every claim
     reads OBSERVATION + SUPPORTED (a field mapping over recorded
     statuses).  The owner then edits one sentence through PUT and that
     claim alone drops to LINKED · EDITED -- support invalidated, the
     record kept.
  2. MIXED CLAIMS (1440 + 393): one update carrying every state the
     service can serve -- a cited model sentence (INFERENCE · LINKED)
     with its typed unknowns, an unsupported model sentence, an accepted
     domain decision, and a citation-only record written before
     HS-200-06 that reads LINKED · MIGRATED.

Shots to: pm/roadmap/holdspeak/phase-200-the-working-practice/assets/story-06-shots/
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest

from .glass_infra import _boot, _api, _normal_chair, _ensure_build

pytest.importorskip("playwright.sync_api", reason="Claim glass needs Playwright")

TOKEN = "hs200-claim-glass"
REPO = Path(__file__).resolve().parents[2]
SHOTS = (
    REPO
    / "pm/roadmap/holdspeak/phase-200-the-working-practice/assets/story-06-shots"
)


# ── Helpers ─────────────────────────────────────────────────────────


def _init_desk(page: Any, url: str) -> None:
    page.goto(f"{url}/?token={TOKEN}", wait_until="load")
    _api(page, "POST", "/api/desk/seed", token=TOKEN)
    _api(page, "PUT", "/api/setup/onboarding",
         {"disposition": "completed"}, token=TOKEN)


def _open_project_room(page: Any, url: str, project_id: str) -> None:
    page.evaluate(
        """([key, scope]) => {
          sessionStorage.setItem(
            "hs.desk.staged-surface-open",
            JSON.stringify({key, scope})
          );
        }""",
        ["open-project-memory", f"project:{project_id}"],
    )
    page.reload(wait_until="load")
    _normal_chair(page)


def _create_project(page: Any, name: str, command_id: str) -> str:
    created = _api(page, "POST", "/api/projects", {
        "name": name,
        "description": "Seeded for HS-200-06 claim support glass.",
        "command_id": command_id,
    }, token=TOKEN)
    return created["project"]["id"]


def _open_first_update(page: Any) -> None:
    page.click('[data-testid="updates-verb"]')
    page.wait_for_selector('[data-testid="update-posture"]')
    items = page.query_selector_all('[data-testid="update-list-item"]')
    assert len(items) >= 1, "no update in the ledger"
    items[0].click()
    page.wait_for_selector('[data-testid="update-editor"]')


def _show_claims(page: Any) -> None:
    """Scroll the claim ledger into frame -- it lives in the window's
    own scroll container, so a full-page shot alone would clip it."""
    rows = page.query_selector_all('[data-testid="update-inline-claim"]')
    assert rows, "no claim rows rendered"
    rows[-1].scroll_into_view_if_needed()
    page.wait_for_timeout(150)


def _chip_labels(page: Any, test_id: str) -> list[str]:
    """The accessible labels of a StateChip row (the glyph is decor)."""
    return [
        el.get_attribute("aria-label") or ""
        for el in page.query_selector_all(
            f'[data-testid="{test_id}"] .surface-state-chip'
        )
    ]


def _token_labels(page: Any, test_id: str) -> list[str]:
    return [
        (el.text_content() or "").strip()
        for el in page.query_selector_all(f'[data-testid="{test_id}"]')
    ]


# ── Leg 1: a REAL draft, then a REAL edit ───────────────────────────


@pytest.mark.timeout(180)
def test_real_draft_supported_then_edited_1440(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    _ensure_build()
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    SHOTS.mkdir(parents=True, exist_ok=True)
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": 1440, "height": 1200})
            _init_desk(page, url)

            pid = _create_project(
                page, "Claim Axes Glass", "hs200-claim-glass-proj-1",
            )
            seeded_items = (
                ("milestone", "Launch v2.0", "planned", "high", {}),
                ("risk", "Vendor lock-in", "open", "critical",
                 {"likelihood": "medium", "impact": "high"}),
                ("dependency", "API Gateway", "at_risk", "medium",
                 {"direction": "upstream",
                  "counterpart_ref": "project:platform"}),
            )
            for ordinal, (item_type, title, lifecycle, severity, details) in (
                enumerate(seeded_items)
            ):
                _api(page, "POST", f"/api/projects/{pid}/items", {
                    "item_type": item_type,
                    "title": title,
                    "lifecycle": lifecycle,
                    "severity": severity,
                    "details": details,
                    "command_id": f"hs200-claim-glass-item-{ordinal}",
                }, token=TOKEN)

            drafted = _api(page, "POST", f"/api/projects/{pid}/updates/draft", {
                "generator": "deterministic",
                "command_id": "hs200-claim-glass-draft-1",
            }, token=TOKEN)["update"]
            claims = json.loads(drafted["claims_json"])
            assert claims, "the seeded room drafts claims"
            assert all(c["support"] == "supported" for c in claims), claims

            # The owner rewrites ONE sentence: that claim loses support.
            edited_body = drafted["body_md"].replace(
                claims[0]["text"], "Launch slipped, the owner rewrote this",
            )
            assert edited_body != drafted["body_md"]
            _api(page, "PUT", f"/api/updates/{drafted['id']}", {
                "body_md": edited_body,
                "command_id": "hs200-claim-glass-save-1",
            }, token=TOKEN)

            _open_project_room(page, url, pid)
            _open_first_update(page)

            kinds = _token_labels(page, "update-claim-kind")
            assert kinds and set(kinds) == {"OBSERVATION"}, kinds

            # The edited sentence appears in every section that stated
            # it; each of those claims loses its support, no other does.
            edited_count = sum(
                1 for c in claims if c["text"] == claims[0]["text"]
            )
            support = _chip_labels(page, "update-claim-support")
            assert support.count("LINKED · EDITED") == edited_count, support
            assert support.count("SUPPORTED") == len(claims) - edited_count, (
                support
            )
            _show_claims(page)
            assert _chip_labels(page, "update-claim-acceptance") == (
                ["UNREVIEWED"] * len(claims)
            )

            page.screenshot(
                path=str(SHOTS / "build-claim-axes-real-1440.png"),
                full_page=True,
            )
            browser.close()
    finally:
        server.stop()


# ── Leg 2: every state the service can serve ────────────────────────


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


def _assert_mixed_axes(page: Any) -> None:
    kinds = _token_labels(page, "update-claim-kind")
    assert kinds == [
        "OBSERVATION", "INFERENCE", "INFERENCE", "DECISION", "INFERENCE",
    ], kinds

    support = _chip_labels(page, "update-claim-support")
    assert support == [
        "SUPPORTED", "LINKED", "UNSUPPORTED", "SUPPORTED",
        "LINKED · MIGRATED",
    ], support

    acceptance = _chip_labels(page, "update-claim-acceptance")
    assert acceptance == ["UNREVIEWED"] * 3 + ["ACCEPTED", "UNREVIEWED"], (
        acceptance
    )

    unknowns = _chip_labels(page, "update-claim-unknown")
    assert unknowns == [
        "DEADLINE · 2026-12-31", "NAME · Priya", "NUMBER · 95%",
    ], unknowns


@pytest.mark.timeout(180)
def test_mixed_claims_axes_1440(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    _ensure_build()
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    SHOTS.mkdir(parents=True, exist_ok=True)
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": 1440, "height": 1200})
            _init_desk(page, url)

            pid = _create_project(
                page, "Mixed Claims Glass", "hs200-claim-glass-proj-2",
            )
            _seed_mixed_update(pid)
            _open_project_room(page, url, pid)
            _open_first_update(page)

            _assert_mixed_axes(page)
            _show_claims(page)

            page.screenshot(
                path=str(SHOTS / "build-claim-axes-mixed-1440.png"),
                full_page=True,
            )
            browser.close()
    finally:
        server.stop()


@pytest.mark.timeout(180)
def test_mixed_claims_axes_393(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    _ensure_build()
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    SHOTS.mkdir(parents=True, exist_ok=True)
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": 393, "height": 852})
            _init_desk(page, url)

            pid = _create_project(
                page, "Mixed Claims Glass", "hs200-claim-glass-proj-3",
            )
            _seed_mixed_update(pid)
            _open_project_room(page, url, pid)
            _open_first_update(page)

            _assert_mixed_axes(page)
            _show_claims(page)

            page.screenshot(
                path=str(SHOTS / "build-claim-axes-mixed-393.png"),
                full_page=True,
            )
            browser.close()
    finally:
        server.stop()
