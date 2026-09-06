"""HS-173-02 real-hub Update glass: the drafted update in the editor.

Three legs:
  1. MODEL DRAFT: footer shows model name token + EgressChip with host,
     claims render inline with per-claim UNVERIFIED badges.
  2. DETERMINISTIC DRAFT: footer shows only verbs, no model/host chips,
     no UNVERIFIED badges on all-verified claims.
  3. PHONE WIDTH: 393 stacking -- footer host row above verbs.

Seeding: a project with a model-drafted update (generator, generatorHost,
generatorModel set) and a deterministic update.  Claims include one
verified=False to trigger the UNVERIFIED badge.

Shots to: assets/story-02-shots/
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest

from .glass_infra import _boot, _api, _normal_chair, _ensure_build

pytest.importorskip("playwright.sync_api", reason="Update glass needs Playwright")

TOKEN = "hs173-update-glass"
REPO = Path(__file__).resolve().parents[2]
SHOTS = REPO / "pm/roadmap/holdspeak/phase-173-the-stewards-hand-and-voice/assets/story-02-shots"


# ── Boot / helpers ──────────────────────────────────────────────────


def _init_desk(page: Any, url: str) -> None:
    page.goto(f"{url}/?token={TOKEN}", wait_until="load")
    _api(page, "POST", "/api/desk/seed", token=TOKEN)
    _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)


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


def _create_project(page: Any) -> str:
    created = _api(page, "POST", "/api/projects", {
        "name": "Update 173 Glass Project",
        "description": "Seeded for HS-173-02 update glass.",
        "command_id": "hs173-update-create-proj",
    }, token=TOKEN)
    return created["project"]["id"]


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


# ── Leg 1: MODEL DRAFT -- model name + host + UNVERIFIED ────────────


@pytest.mark.timeout(120)
def test_model_draft_footer_and_claims_1440(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    _ensure_build()
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    SHOTS.mkdir(parents=True, exist_ok=True)
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            _init_desk(page, url)

            project_id = _create_project(page)
            _seed_model_draft(project_id)

            _open_project_room(page, url, project_id)

            # Enter updates
            page.click('[data-testid="updates-verb"]')
            page.wait_for_selector('[data-testid="update-posture"]')

            # Open the model draft
            items = page.query_selector_all('[data-testid="update-list-item"]')
            assert len(items) >= 1
            items[0].click()
            page.wait_for_selector('[data-testid="update-editor"]')

            # Footer: model name token
            model_token = page.query_selector('[data-testid="update-footer-model"]')
            assert model_token is not None, "Model name token missing in footer"
            assert "QWEN3 32B Q6" in model_token.text_content()

            # Footer: EgressChip with LAN host
            egress_chips = page.query_selector_all('.gadget-chip-egress')
            host_chip = None
            for chip in egress_chips:
                text = chip.text_content() or ""
                if "192.168.1.43" in text:
                    host_chip = chip
                    break
            assert host_chip is not None, "Host EgressChip missing in footer"
            assert "LAN" in (host_chip.text_content() or "")

            # UNVERIFIED badge(s)
            unverified = page.query_selector_all('[data-testid="update-claim-unverified"]')
            assert len(unverified) >= 1, "UNVERIFIED badge missing for unverified claim"

            # Ref chips show identity labels (PR #612, KAN-7, MTG 09-05)
            ref_chips = page.query_selector_all('[data-testid="update-claim-ref"]')
            chip_labels = [c.text_content() for c in ref_chips]
            assert "PR #612" in chip_labels, f"PR chip missing, got {chip_labels}"
            assert "KAN-7" in chip_labels, f"Jira chip missing, got {chip_labels}"
            assert "MTG 09-05" in chip_labels, f"Meeting chip missing, got {chip_labels}"

            page.screenshot(path=str(SHOTS / "build-update-drafted-1440.png"), full_page=True)
            browser.close()
    finally:
        server.stop()
        


@pytest.mark.timeout(120)
def test_model_draft_footer_393(
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

            project_id = _create_project(page)
            _seed_model_draft(project_id)

            _open_project_room(page, url, project_id)

            page.click('[data-testid="updates-verb"]')
            page.wait_for_selector('[data-testid="update-posture"]')

            items = page.query_selector_all('[data-testid="update-list-item"]')
            assert len(items) >= 1
            items[0].click()
            page.wait_for_selector('[data-testid="update-editor"]')

            model_token = page.query_selector('[data-testid="update-footer-model"]')
            assert model_token is not None

            page.screenshot(path=str(SHOTS / "build-update-drafted-393.png"), full_page=True)
            browser.close()
    finally:
        server.stop()
        


# ── Leg 2: DETERMINISTIC -- no model/host in footer ─────────────────


@pytest.mark.timeout(120)
def test_deterministic_no_model_footer(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    _ensure_build()
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    SHOTS.mkdir(parents=True, exist_ok=True)
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            _init_desk(page, url)

            project_id = _create_project(page)
            _seed_deterministic_draft(project_id)

            _open_project_room(page, url, project_id)

            page.click('[data-testid="updates-verb"]')
            page.wait_for_selector('[data-testid="update-posture"]')

            items = page.query_selector_all('[data-testid="update-list-item"]')
            assert len(items) >= 1
            items[0].click()
            page.wait_for_selector('[data-testid="update-editor"]')

            model_token = page.query_selector('[data-testid="update-footer-model"]')
            assert model_token is None, "Model token should not appear for deterministic drafts"

            unverified = page.query_selector_all('[data-testid="update-claim-unverified"]')
            assert len(unverified) == 0, "No UNVERIFIED badges expected for all-verified claims"

            page.screenshot(path=str(SHOTS / "build-update-deterministic-1440.png"), full_page=True)
            browser.close()
    finally:
        server.stop()
        
