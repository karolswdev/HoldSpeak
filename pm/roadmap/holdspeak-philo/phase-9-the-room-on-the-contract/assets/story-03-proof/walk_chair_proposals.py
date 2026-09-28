"""PHILO-9-03 (Muad'Dib's ruling, 2026-09-28): walk the Chair's two proposal
`Open` verbs once on a real isolated hub (`arrival-proposal-open` under MORE,
`arrival-source-open` in a row's SOURCES) and record what opens.

Run: HOME=$(mktemp -d) PLAYWRIGHT_BROWSERS_PATH=... .venv/bin/python -m pytest -q -s <this file>
Seed: a Room with one meeting and one `proposed` follow-through proposal bound
to the project (the hs172 glass's seed shape), so the Chair draws it."""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta

import pytest

from tests.e2e.glass_infra import _api, _boot, _ensure_build, _normal_chair, _settle

TOKEN = "philo9-03-walk"
NAME = "Payments ledger cutover"


@pytest.mark.parametrize("width", [1440, 393])
def test_walk_the_chairs_proposal_open_verbs(tmp_path, monkeypatch, width) -> None:
    from playwright.sync_api import sync_playwright

    from holdspeak.db import get_database

    _ensure_build()
    server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
    out: dict = {"width": width}
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": width, "height": 900 if width == 1440 else 852})
            page.goto(f"{base}/?token={TOKEN}", wait_until="load")
            _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
            pids = [_api(page, "POST", "/api/projects", {"name": n}, token=TOKEN)["project"]["id"]
                    for n in (NAME, "Vendor review")]
            now = datetime.now()
            with get_database()._connection() as conn:
                conn.execute(
                    "INSERT INTO meetings (id, started_at, ended_at, title, duration_seconds, intel_status, capture_status, provenance) "
                    "VALUES ('m-walk', ?, ?, 'Cutover sync', 1800.0, 'complete', 'finalized', 'desktop')",
                    ((now - timedelta(hours=1)).isoformat(), (now - timedelta(minutes=30)).isoformat()))
                prop = f"prop-{uuid.uuid4().hex[:12]}"
                conn.execute(
                    "INSERT INTO follow_through_proposals (id, meeting_id, project_id, kind, text, due_hint, "
                    " source_plugin, fingerprint, state, model_host, created_at) "
                    "VALUES (?, 'm-walk', ?, 'action', 'Marek owns the ledger freeze', 'Fri', 'decision_capture', ?, 'proposed', '', ?)",
                    (prop, pids[0], f"fp-{uuid.uuid4().hex[:16]}", now.isoformat()))
                conn.commit()
            _api(page, "POST", f"/api/projects/{pids[0]}/meetings/m-walk", {}, token=TOKEN)
            page.reload(wait_until="load")
            _normal_chair(page)
            page.wait_for_timeout(1500)
            _settle(page)
            out["proposal_id"] = prop
            out["chair_rows"] = page.locator("[data-testid=arrival-why]").all_inner_texts()
            for testid, opener in (("arrival-proposal-open", "MORE"), ("arrival-source-open", "SOURCES")):
                verb = page.locator(f"[data-testid={testid}]")
                if not verb.count():
                    # The verb sits behind its disclosure: open every one on the rows.
                    for d in page.locator(".chair [aria-expanded=false]").all():
                        try:
                            d.click(timeout=2000)
                        except Exception:
                            pass
                    page.wait_for_timeout(400)
                n = verb.count()
                rec: dict = {"present": n}
                if n:
                    verb.first.scroll_into_view_if_needed()
                    verb.first.click()
                    try:
                        page.locator("[data-testid=room-body]").wait_for(timeout=10_000)
                        win = page.locator(".desk-window:has([data-testid=room-body])").first
                        rec["opened"] = win.locator(".desk-window-title, [data-testid=window-title]").first.inner_text() \
                            if win.locator(".desk-window-title, [data-testid=window-title]").count() else win.inner_text()[:80]
                        rec["room_names_project"] = NAME in win.inner_text()
                        rec["proposal_in_room"] = "Marek owns the ledger freeze" in win.inner_text()
                    except Exception as exc:  # noqa: BLE001
                        rec["opened"] = f"no Room: {type(exc).__name__}"
                    page.screenshot(path=str(tmp_path / f"{testid}-{width}.png"))
                    page.keyboard.press("Escape")
                    page.reload(wait_until="load")
                    _normal_chair(page)
                    page.wait_for_timeout(1200)
                out[testid] = rec
            browser.close()
    finally:
        server.stop()
    print("WALK", json.dumps(out, ensure_ascii=False))
