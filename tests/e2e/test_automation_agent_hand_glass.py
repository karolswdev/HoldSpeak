"""AG14: the hand automation sentence as rendered on the real desk."""
from __future__ import annotations

from pathlib import Path

import pytest

from .glass_infra import _api, _boot, _ensure_build, _normal_chair, _settle
from tests._evidence import evidence_dir
from tests.unit.test_agent_hand import _seed

pytest.importorskip("playwright.sync_api", reason="the hand automation glass needs Playwright")
pytestmark = [pytest.mark.e2e]

TOKEN = "automation-agent-hand-glass"
SHOTS = evidence_dir("automation-agent-hand")
SIZES = {1440: 900, 393: 852}
WB = "wb-ag14-glass"


@pytest.mark.parametrize("width", [1440, 393])
def test_hand_automation_do_with_review_controls_are_real_and_saved(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int,
) -> None:
    from playwright.sync_api import sync_playwright

    _ensure_build()
    server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
    try:
        from holdspeak.db import get_database

        db = get_database()
        _seed(db)
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={"width": width, "height": SIZES[width]},
                device_scale_factor=1,
                has_touch=width < 720,
                reduced_motion="reduce",
            )
            page = context.new_page()
            page.set_default_timeout(45_000)
            errors: list[str] = []
            page.on("pageerror", lambda error: errors.append(str(error)[:240]))
            try:
                page.goto(f"{base}/?token={TOKEN}", wait_until="load")
                _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
                made = _api(page, "POST", "/api/workbenches", {
                    "id": WB,
                    "name": "Agent hand review",
                    "instruction": "Complete each action and report the result.",
                    "sources": ["action:ai_1"],
                    "output_target": "today",
                    "do_kind": "hand_to_agent",
                    "agent_profile": "claude-default",
                    "review_by": "claude",
                }, token=TOKEN)["workbench"]
                assert made["id"] == WB
                page.goto(f"{base}/?token={TOKEN}&open=workbench:{WB}", wait_until="load")
                _normal_chair(page)
                window = page.get_by_test_id("automation-window")
                window.wait_for(timeout=45_000)
                _settle(page)

                do_line = page.get_by_test_id("automation-line-do")
                with_line = page.get_by_test_id("automation-line-with")
                review_line = page.get_by_test_id("automation-line-review")
                assert "Hand to an agent" in do_line.inner_text()
                assert "claude-default" in with_line.inner_text()
                assert "claude" in review_line.inner_text().lower()

                page.screenshot(path=str(SHOTS / f"do-with-review-{width}-closed.png"))
                review_line.get_by_role("button").first.click()
                editor = page.get_by_test_id("automation-review-editor")
                editor.wait_for(timeout=10_000)
                assert {"None", "Codex", "Claude Code", "pi"}.issubset(
                    set(editor.get_by_role("button").all_text_contents())
                )
                page.screenshot(path=str(SHOTS / f"do-with-review-{width}-open.png"))

                with page.expect_response(
                    lambda response: response.url.endswith(f"/api/workbenches/{WB}")
                    and response.request.method == "PUT"
                ) as saved:
                    editor.get_by_role("button", name="Codex", exact=True).click()
                assert saved.value.ok, saved.value.text()
                assert (saved.value.request.post_data_json or {}).get("review_by") == "codex"
                page.get_by_test_id("automation-line-review").get_by_text("codex", exact=True).wait_for(timeout=10_000)
                assert not errors, errors
            finally:
                browser.close()
    finally:
        server.stop()
