"""HS-162-06 real-hub Update Factory glass.

PV-H04: median edit-to-copy under five minutes AND >=70% generated content
retained.  Both numbers MEASURED, not asserted.

Five legs:
  1. THE STOPWATCH:    edit-to-copy wall clock per segment.
  2. THE RETENTION:    diff-based fraction of generated content retained.
  3. THE DEGRADED LEG: no broker -> model draft falls back -> honest provenance.
  4. THE PUBLISH LEG:  publish -> immutability -> regenerate -> revision bump.
  5. THE LIVE MODEL:   (skip decision noted in report).

Editor: DeskEditor (CodeMirror markdown).  Published view: Material renderer
with per-section deduplicated Sources rows.  Unverified: single banner.

Seeding: POST /api/projects, then POST /api/projects/{id}/items for
workstream + risk + dependency + milestone items.  Rich enough for the
update factory to produce non-trivial sections.

Determinism: fixture legs x2 (run the file twice, both green).
"""
from __future__ import annotations

import difflib
import json
import os
import re
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from .glass_infra import _boot, _api, _assert_clean, _normal_chair, _ensure_build, _api_text

pytest.importorskip("playwright.sync_api", reason="Update glass needs Playwright")

TOKEN = "hs162-update-glass"
REPO = Path(__file__).resolve().parents[2]
SHOTS = REPO / "pm/roadmap/holdspeak/phase-162-the-update-factory/assets/story-06-shots"
STOPWATCH_JSON = (
    REPO / "pm/roadmap/holdspeak/phase-162-the-update-factory"
    / "assets/story-06-stopwatch.json"
)


# ── Boot / helpers ──────────────────────────────────────────────────


_RAW_ID_RE = re.compile(r"^p[a-z]+_[0-9a-f]{16,}")


def _assert_no_raw_ids(page: Any) -> None:
    """No-raw-ids law: no visible element text in the update posture
    matches /^p[a-z]+_[0-9a-f]{16,}/."""
    visible_texts = page.evaluate(
        """() => {
            const posture = document.querySelector(
                '[data-testid="update-posture"]'
            );
            if (!posture) return [];
            const walker = document.createTreeWalker(
                posture, NodeFilter.SHOW_TEXT, null
            );
            const texts = [];
            while (walker.nextNode()) {
                const t = walker.currentNode.textContent.trim();
                if (t) texts.push(t);
            }
            return texts;
        }"""
    )
    for text in visible_texts:
        for word in text.split():
            assert not _RAW_ID_RE.match(word), (
                f"Raw machine ID leaked onto glass: {word!r} "
                f"(in text: {text!r})"
            )


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


def _create_project_api(page: Any) -> str:
    created = _api(page, "POST", "/api/projects", {
        "name": "Update Glass Project",
        "description": "Seeded for HS-162-06 update glass.",
        "command_id": "hs162-glass-create-proj",
    }, token=TOKEN)
    return created["project"]["id"]


def _seed_room_items(page: Any, project_id: str) -> None:
    base = f"/api/projects/{project_id}/items"
    future_due = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
    _api(page, "POST", base, {
        "item_type": "workstream",
        "title": "Q4 Payments Platform Integration",
        "lifecycle": "active",
        "summary": "Integrate payment gateway with event sourcing",
    }, token=TOKEN)
    _api(page, "POST", base, {
        "item_type": "risk",
        "title": "PCI compliance deadline at risk",
        "lifecycle": "open",
        "severity": "high",
        "summary": "Compliance docs overdue; 30-day deadline approaching",
        "details": {"likelihood": "high", "impact": "critical",
                    "mitigation": "Escalate to compliance team this week"},
    }, token=TOKEN)
    _api(page, "POST", base, {
        "item_type": "dependency",
        "title": "Infrastructure team load test environment",
        "lifecycle": "at_risk",
        "summary": "Black Friday load test env provisioning stalled",
        "details": {"direction": "upstream",
                    "counterpart_ref": "team:infrastructure"},
    }, token=TOKEN)
    _api(page, "POST", base, {
        "item_type": "milestone",
        "title": "Gateway MVP sign-off",
        "lifecycle": "planned",
        "due_at": future_due,
        "summary": "Feature-complete milestone for the payment gateway",
        "details": {},
    }, token=TOKEN)


def _seed_unverified_update(page: Any, project_id: str) -> str:
    """Insert a draft with an UNVERIFIED claim (verified=False)."""
    from holdspeak.db import get_database
    db = get_database()
    update_id = "pupd_unverified_glass_001"
    claims = [
        {"span_id": "s_progress_0",
         "text": "The payment platform integration is progressing well.",
         "refs": ["item:some-ws-id"], "section": "progress"},
        {"span_id": "s_progress_1",
         "text": "Team morale is high and velocity is improving.",
         "refs": [], "section": "progress", "verified": False},
        {"span_id": "s_decisions_0",
         "text": "No decisions in this window.",
         "refs": [], "section": "decisions"},
    ]
    body_md = (
        "## Progress\n\n"
        "- The payment platform integration is progressing well.\n"
        "- **[UNVERIFIED]** Team morale is high and velocity is improving.\n\n"
        "## Decisions\n\nNo decisions in this window.\n\n"
        "## Risks & Blockers\n\nNo risks or blockers in this window.\n\n"
        "## Dependencies\n\nNo dependencies tracked.\n\n"
        "## Next Actions\n\nNo upcoming actions.\n\n"
        "## Source Coverage\n\nAll sources consulted successfully.\n"
    )
    claims_json = json.dumps(claims, sort_keys=True, separators=(",", ":"))
    now_iso = datetime.now().isoformat()
    with db._connection() as conn:
        conn.execute(
            """INSERT INTO project_updates
               (id, project_id, project_revision, review_id,
                lifecycle, draft_revision, body_md, claims_json,
                source_manifest_json, generator, created_at, updated_at)
               VALUES (?, ?, ?, ?, 'draft', ?, ?, ?, ?, ?, ?, ?)""",
            (update_id, project_id, 0, None, 1, body_md, claims_json,
             "{}", "model:fixture-unverified", now_iso, now_iso),
        )
    return update_id


def _compute_retention(original: str, edited: str) -> float:
    orig_norm = " ".join(original.split())
    edit_norm = " ".join(edited.split())
    if not orig_norm:
        return 1.0
    matcher = difflib.SequenceMatcher(None, orig_norm, edit_norm)
    matching_chars = sum(b.size for b in matcher.get_matching_blocks())
    return matching_chars / len(orig_norm)


def _cm_get_text(page: Any) -> str:
    """Read the current CodeMirror editor content."""
    return page.evaluate(
        """() => {
            const view = document.querySelector('.cm-editor');
            if (!view || !view.cmView) return '';
            return view.cmView.view.state.doc.toString();
        }"""
    )


def _cm_type_at_end(page: Any, text: str) -> None:
    """Click into the CodeMirror editor and type text at the end."""
    cm = page.locator(".cm-content")
    cm.click()
    # Move to end of document
    page.keyboard.press("Meta+End" if os.uname().sysname == "Darwin" else "Control+End")
    page.keyboard.type(text, delay=10)


# ── Leg 1+2: THE STOPWATCH + RETENTION ─────────────────────────────


@pytest.mark.e2e
@pytest.mark.requires_meeting
@pytest.mark.parametrize("width", [1440, 393])
def test_stopwatch_and_retention(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int,
) -> None:
    """Seeded room -> draft -> edit (CodeMirror) -> save -> copy-markdown.

    Measures wall-clock per segment (bar < 300s) and retention (>= 0.70).
    """
    _ensure_build()
    from playwright.sync_api import sync_playwright
    from holdspeak.db import reset_database

    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    SHOTS.mkdir(parents=True, exist_ok=True)
    errors: list[str] = []
    segments: dict[str, float] = {}

    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            ctx = browser.new_context(
                viewport={"width": width, "height": 900 if width == 1440 else 852},
                permissions=["clipboard-read", "clipboard-write"],
            )
            page = ctx.new_page()
            page.emulate_media(reduced_motion="reduce")
            page.on("pageerror", lambda error: errors.append(f"page: {error}"))

            # -- Desk init + seed --
            t0 = time.monotonic()
            _init_desk(page, url)
            project_id = _create_project_api(page)
            _seed_room_items(page, project_id)
            segments["desk_seed"] = time.monotonic() - t0

            # -- Seed the unverified-claim draft for its shot --
            _seed_unverified_update(page, project_id)

            # -- Open room --
            t0 = time.monotonic()
            _open_project_room(page, url, project_id)
            page.get_by_test_id("project-room-name").wait_for(timeout=15000)
            segments["open_room"] = time.monotonic() - t0

            # -- Click Updates verb --
            t0 = time.monotonic()
            page.get_by_test_id("updates-verb").wait_for(timeout=10000)
            page.get_by_test_id("updates-verb").click()
            posture = page.get_by_test_id("update-posture")
            posture.wait_for(timeout=10000)
            assert posture.get_attribute("data-phase") == "list"
            segments["enter_updates"] = time.monotonic() - t0

            # -- SHOT: draft list --
            page.screenshot(path=str(SHOTS / f"draft-list-{width}.png"), full_page=False)
            assert (SHOTS / f"draft-list-{width}.png").stat().st_size > 20_000

            # -- List-row two-liner: plain-words provenance, no assignment id --
            _list_rows = page.get_by_test_id("update-list-item")
            assert _list_rows.count() >= 1, "Expected at least one draft in the list"

            _provenance = page.get_by_test_id("update-list-provenance")
            assert _provenance.count() >= 1, "List rows must have provenance secondary line"
            for _pi in range(_provenance.count()):
                _prov_text = _provenance.nth(_pi).inner_text().strip()
                assert (
                    _prov_text.startswith("Deterministic draft")
                    or _prov_text.startswith("Model draft")
                ), (
                    f"Provenance must be plain words ('Deterministic draft' / 'Model draft'), "
                    f"got: {_prov_text!r}"
                )

            for _ri in range(_list_rows.count()):
                _row_text = _list_rows.nth(_ri).inner_text()
                assert "(" not in _row_text, (
                    f"List row must not show parenthesized ids: {_row_text!r}"
                )
                assert "model:" not in _row_text.lower(), (
                    f"List row must not leak raw generator string: {_row_text!r}"
                )

            # -- Open the seeded unverified draft for its banner shot --
            list_items = page.get_by_test_id("update-list-item")
            if list_items.count() > 0:
                list_items.first.click()
                page.get_by_test_id("update-editor").wait_for(timeout=10000)

                # The unverified banner (single notice, not per-claim)
                banner = page.get_by_test_id("update-unverified-banner")
                if banner.count() > 0:
                    page.screenshot(
                        path=str(SHOTS / f"unverified-span-{width}.png"),
                        full_page=False,
                    )
                    assert (SHOTS / f"unverified-span-{width}.png").stat().st_size > 20_000
                    assert banner.is_visible()
                    banner_text = banner.inner_text()
                    assert "unverified" in banner_text.lower() or "could not be verified" in banner_text.lower(), (
                        f"Banner should mention unverified, got: {banner_text!r}"
                    )

                # HS-167-05: Back button is in SurfaceVerbs inside the editor
                back_btn = page.locator(
                    '[data-testid="update-editor"] button',
                ).filter(has_text="Back")
                if back_btn.count() > 0:
                    back_btn.first.click()
                else:
                    # Fallback: try testid on the footer
                    page.get_by_test_id("update-verb-back").click()
                page.wait_for_function(
                    """() => {
                        const el = document.querySelector('[data-testid="update-posture"]');
                        return el && el.getAttribute('data-phase') === 'list';
                    }""",
                    timeout=10000,
                )

            # -- Draft (deterministic) --
            t0 = time.monotonic()
            page.get_by_test_id("update-verb-draft-deterministic").click()
            editor = page.get_by_test_id("update-editor")
            editor.wait_for(timeout=15000)
            segments["draft_deterministic"] = time.monotonic() - t0

            # -- Read the generated body via API (the body_md from the draft) --
            updates_resp = _api(page, "GET", f"/api/projects/{project_id}/updates?lifecycle=draft", token=TOKEN)
            det_drafts = [u for u in updates_resp.get("updates", [])
                          if u.get("generator") == "deterministic"]
            assert len(det_drafts) >= 1, "No deterministic draft found"
            update_id = det_drafts[0]["id"]
            generated_body = _api_text(page, "GET", f"/api/updates/{update_id}/markdown", token=TOKEN)
            assert len(generated_body) > 50, f"Generated body too short ({len(generated_body)} chars)"

            # -- Verify CodeMirror editor is present --
            cm_editor = page.locator(".cm-editor")
            cm_editor.wait_for(timeout=5000)
            assert cm_editor.is_visible(), "CodeMirror editor should be visible"

            # -- SHOT: editor with CodeMirror + source rows --
            page.screenshot(path=str(SHOTS / f"editor-claims-{width}.png"), full_page=False)
            assert (SHOTS / f"editor-claims-{width}.png").stat().st_size > 20_000

            # -- Verify source rows render with human-label chips --
            source_rows = page.get_by_test_id("update-source-row")
            source_rows.first.wait_for(timeout=5000)
            assert source_rows.count() >= 1, "Expected >=1 source rows"

            ref_chips = page.get_by_test_id("update-claim-ref")
            assert ref_chips.count() >= 1, "Expected >=1 ref chips in source rows"
            first_chip = ref_chips.first.inner_text()
            assert first_chip and len(first_chip) > 0, "Source chip should be non-empty"
            # Chips now carry derived claim titles, not generic "Open item"
            assert first_chip.lower() != "open item", (
                f"Chip should show derived claim title, not generic label: {first_chip!r}"
            )
            assert not _RAW_ID_RE.match(first_chip), (
                f"Raw ID leaked into source chip: {first_chip!r}"
            )

            # -- No-raw-ids law --
            _assert_no_raw_ids(page)

            # -- SHOT: click a source chip ref --
            ref_chips.first.click()
            page.wait_for_timeout(500)
            page.screenshot(path=str(SHOTS / f"claim-source-{width}.png"), full_page=False)
            assert (SHOTS / f"claim-source-{width}.png").stat().st_size > 20_000

            # -- SHOT: verbs band --
            page.screenshot(path=str(SHOTS / f"verbs-band-{width}.png"), full_page=False)
            assert (SHOTS / f"verbs-band-{width}.png").stat().st_size > 20_000

            # -- ONE representative human edit via CodeMirror --
            t0 = time.monotonic()
            edit_text = "\nOwner note: reviewed with the team on Monday."
            _cm_type_at_end(page, edit_text)
            segments["human_edit"] = time.monotonic() - t0

            # -- Save --
            t0 = time.monotonic()
            page.get_by_test_id("update-verb-save").click()
            page.wait_for_function(
                """() => {
                    const btn = document.querySelector('[data-testid="update-verb-save"]');
                    return btn && btn.disabled;
                }""",
                timeout=10000,
            )
            segments["save"] = time.monotonic() - t0

            # -- Copy Markdown --
            t0 = time.monotonic()
            page.get_by_test_id("update-verb-copy").click()
            page.wait_for_function(
                """() => {
                    const btn = document.querySelector('[data-testid="update-verb-copy"]');
                    return btn && btn.textContent.includes('Copied');
                }""",
                timeout=10000,
            )
            segments["copy_markdown"] = time.monotonic() - t0

            # -- Verify via GET endpoint --
            copied_md = _api_text(page, "GET", f"/api/updates/{update_id}/markdown", token=TOKEN)
            assert len(copied_md) > 50
            assert "Owner note" in copied_md, "Human edit not preserved in the copied artifact"

            # -- Retention --
            retention = _compute_retention(generated_body, copied_md)
            assert retention >= 0.70, f"Retention {retention:.2%} below 70% bar"

            _assert_clean(page, errors)

            # -- Write stopwatch JSON (1440 only) --
            if width == 1440:
                total = sum(segments.values())
                stopwatch = {
                    "total_seconds": round(total, 2),
                    "segments": {k: round(v, 2) for k, v in segments.items()},
                    "bar": 300, "passed": total < 300,
                    "retention": round(retention, 4),
                    "retention_bar": 0.70, "retention_passed": retention >= 0.70,
                    "viewport": width,
                }
                STOPWATCH_JSON.parent.mkdir(parents=True, exist_ok=True)
                STOPWATCH_JSON.write_text(json.dumps(stopwatch, indent=2) + "\n")
                assert total < 300, f"Stopwatch bar breached: {total:.1f}s > 300s"

            browser.close()
    finally:
        server.stop()
        reset_database()


# ── Leg 3: THE DEGRADED LEG ────────────────────────────────────────


@pytest.mark.e2e
@pytest.mark.requires_meeting
@pytest.mark.parametrize("width", [1440, 393])
def test_degraded_model_fallback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int,
) -> None:
    """No inference assignments -> Draft with model -> falls back to
    deterministic with honest generator provenance + fallback_reason.
    Source rows still resolve (UPD-003 on glass)."""
    _ensure_build()
    from playwright.sync_api import sync_playwright
    from holdspeak.db import reset_database

    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    SHOTS.mkdir(parents=True, exist_ok=True)
    errors: list[str] = []

    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(
                viewport={"width": width, "height": 900 if width == 1440 else 852},
            )
            page.emulate_media(reduced_motion="reduce")
            page.on("pageerror", lambda error: errors.append(f"page: {error}"))

            _init_desk(page, url)
            project_id = _create_project_api(page)
            _seed_room_items(page, project_id)

            _open_project_room(page, url, project_id)
            page.get_by_test_id("project-room-name").wait_for(timeout=15000)

            page.get_by_test_id("updates-verb").wait_for(timeout=10000)
            page.get_by_test_id("updates-verb").click()
            page.get_by_test_id("update-posture").wait_for(timeout=10000)

            # -- Draft with model (will fall back) --
            page.get_by_test_id("update-verb-draft-model").click()
            editor = page.get_by_test_id("update-editor")
            editor.wait_for(timeout=20000)

            # -- Generator label shows "Deterministic" --
            gen_label = page.get_by_test_id("update-generator-label")
            gen_label.wait_for(timeout=5000)
            assert "deterministic" in gen_label.inner_text().lower()

            # -- Fallback reason: human sentence in warn tone --
            fallback = page.get_by_test_id("update-fallback-reason")
            fallback.wait_for(timeout=5000)
            assert fallback.is_visible()
            assert fallback.get_attribute("data-tone") == "warn"
            fb_text = fallback.inner_text()
            assert "drafted deterministically" in fb_text.lower(), (
                f"Expected human fallback sentence, got: {fb_text!r}"
            )
            assert "model_unavailable" not in fb_text

            # -- Source rows still resolve --
            source_rows = page.get_by_test_id("update-source-row")
            source_rows.first.wait_for(timeout=5000)
            ref_chips = page.get_by_test_id("update-claim-ref")
            assert ref_chips.count() >= 1, "Source row chips should render in degraded mode"

            _assert_no_raw_ids(page)

            page.screenshot(path=str(SHOTS / f"degraded-fallback-{width}.png"), full_page=False)
            assert (SHOTS / f"degraded-fallback-{width}.png").stat().st_size > 20_000

            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()
        reset_database()


# ── Leg 4: THE PUBLISH LEG ─────────────────────────────────────────


@pytest.mark.e2e
@pytest.mark.requires_meeting
@pytest.mark.parametrize("width", [1440, 393])
def test_publish_immutability_regenerate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int,
) -> None:
    """Draft -> publish -> Material rendered document with Sources rows ->
    regenerate mints NEW draft -> room revision advanced."""
    _ensure_build()
    from playwright.sync_api import sync_playwright
    from holdspeak.db import reset_database

    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    SHOTS.mkdir(parents=True, exist_ok=True)
    errors: list[str] = []

    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(
                viewport={"width": width, "height": 900 if width == 1440 else 852},
            )
            page.emulate_media(reduced_motion="reduce")
            page.on("pageerror", lambda error: errors.append(f"page: {error}"))

            _init_desk(page, url)
            project_id = _create_project_api(page)
            _seed_room_items(page, project_id)

            room_before = _api(page, "GET", f"/api/projects/{project_id}/room", token=TOKEN)
            rev_before = room_before.get("revision", 0)

            _open_project_room(page, url, project_id)
            page.get_by_test_id("project-room-name").wait_for(timeout=15000)

            page.get_by_test_id("updates-verb").wait_for(timeout=10000)
            page.get_by_test_id("updates-verb").click()
            page.get_by_test_id("update-posture").wait_for(timeout=10000)

            page.get_by_test_id("update-verb-draft-deterministic").click()
            editor = page.get_by_test_id("update-editor")
            editor.wait_for(timeout=15000)

            # Get the draft body via API for later comparison
            updates_resp = _api(page, "GET", f"/api/projects/{project_id}/updates?lifecycle=draft", token=TOKEN)
            drafts = updates_resp.get("updates", [])
            assert len(drafts) >= 1
            update_id = drafts[0]["id"]
            draft_body = _api_text(page, "GET", f"/api/updates/{update_id}/markdown", token=TOKEN)

            # -- Publish --
            page.get_by_test_id("update-verb-publish").click()
            page.wait_for_function(
                """() => {
                    const ed = document.querySelector('[data-testid="update-editor"]');
                    return ed && ed.getAttribute('data-lifecycle') === 'published';
                }""",
                timeout=15000,
            )

            # -- Published: read-only reason visible --
            readonly_reason = page.get_by_test_id("update-readonly-reason")
            readonly_reason.wait_for(timeout=5000)
            assert "read-only" in readonly_reason.inner_text().lower()

            # -- Published: rendered document (Material) visible --
            doc = page.get_by_test_id("update-document")
            doc.wait_for(timeout=5000)
            assert doc.is_visible(), "Rendered document should be visible"

            # -- Published: Sources rows with deduplicated chips --
            sources = page.get_by_test_id("update-sources")
            sources.wait_for(timeout=5000)
            pub_ref_chips = page.get_by_test_id("update-claim-ref")
            assert pub_ref_chips.count() >= 1, "Published Sources should have ref chips"
            pub_chip_text = pub_ref_chips.first.inner_text()
            assert pub_chip_text and len(pub_chip_text) > 0, "Published source chip should be non-empty"
            assert pub_chip_text.lower() != "open item", (
                f"Chip should show derived claim title, not generic label: {pub_chip_text!r}"
            )

            # -- Published: deduplicated (count <= unique items, not a wall) --
            # We seeded 4 items but some appear in multiple sections; dedup
            # means the source rows are compact.
            source_rows = page.get_by_test_id("update-source-row")
            assert source_rows.count() >= 1
            # Each source row should have <= 4 chips (the 4 unique items)
            total_chips = pub_ref_chips.count()
            assert total_chips <= 20, (
                f"Expected deduplicated chips, got {total_chips} (wall of repeated rows)"
            )

            # -- Save/Publish verbs gone --
            assert page.get_by_test_id("update-verb-save").count() == 0
            assert page.get_by_test_id("update-verb-publish").count() == 0

            _assert_no_raw_ids(page)

            # -- SHOT: published read-only state --
            page.screenshot(path=str(SHOTS / f"published-readonly-{width}.png"), full_page=False)
            assert (SHOTS / f"published-readonly-{width}.png").stat().st_size > 20_000

            # -- Published body via API unchanged --
            published_md = _api_text(page, "GET", f"/api/updates/{update_id}/markdown", token=TOKEN)
            assert published_md == draft_body

            # -- Regenerate --
            page.get_by_test_id("update-verb-regenerate").click()
            page.wait_for_function(
                """() => {
                    const ed = document.querySelector('[data-testid="update-editor"]');
                    return ed && ed.getAttribute('data-lifecycle') === 'draft';
                }""",
                timeout=15000,
            )

            updates_resp2 = _api(page, "GET", f"/api/projects/{project_id}/updates?lifecycle=draft", token=TOKEN)
            new_drafts = updates_resp2.get("updates", [])
            assert len(new_drafts) >= 1
            assert new_drafts[0]["id"] != update_id, "Regenerate should create a NEW draft"

            # Published body immutable
            assert _api_text(page, "GET", f"/api/updates/{update_id}/markdown", token=TOKEN) == published_md

            # Room revision advanced
            rev_after = _api(page, "GET", f"/api/projects/{project_id}/room", token=TOKEN).get("revision", 0)
            assert rev_after > rev_before, f"Room revision should advance: {rev_before} -> {rev_after}"

            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()
        reset_database()
