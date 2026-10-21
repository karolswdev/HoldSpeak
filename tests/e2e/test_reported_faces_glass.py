"""Owner-reported Agent and New Automation faces, including their saved PNGs."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pytest

from tests._evidence import evidence_dir
from .glass_infra import _api, _boot, _ensure_build, _normal_chair, _settle, clear_hub_windows
from .test_ui_feedback_glass import _save_feedback

SHOTS = evidence_dir("reported-faces")
TOKEN = "reported-faces-glass"
REPORT = "Added the rollback checkpoint. Checking the migration tests."


def _fit_and_hit(button: Any) -> None:
    facts = button.evaluate("""el => {
      const r=el.getBoundingClientRect();
      const owner=el.closest('[data-layer="window"]').getBoundingClientRect();
      const hits=[];
      for(const x of [r.left+2,r.left+r.width/2,r.right-2])
        for(const y of [r.top+2,r.top+r.height/2,r.bottom-2]) {
          const hit=document.elementFromPoint(x,y);hits.push(Boolean(hit&&(hit===el||el.contains(hit))));
        }
      return {width:r.width,height:r.height,hits,
        inside:r.left>=owner.left&&r.right<=owner.right+1&&r.top>=owner.top&&r.bottom<=owner.bottom+1};
    }""")
    assert facts["width"] >= 44 and facts["height"] >= 44, facts
    assert facts["inside"] and all(facts["hits"]), facts


@pytest.mark.e2e
@pytest.mark.parametrize("width", [1440, 393])
def test_reported_faces_and_saved_images(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int) -> None:
    import holdspeak.agent_context as agent_context
    import holdspeak.delivery.factory_launch as factory_launch
    from holdspeak.agent_context import event_log, ingest_agent_hook_event
    from playwright.sync_api import sync_playwright

    monkeypatch.setenv("HOLDSPEAK_UI_FEEDBACK", "1")
    state = tmp_path / "home/.holdspeak"
    state.mkdir(parents=True)
    monkeypatch.setattr(factory_launch, "DEFAULT_LAUNCHES_PATH", state / "agent_launches.json")
    monkeypatch.setattr(agent_context, "AGENT_CONTEXT_FILE", state / "agent_sessions.json")
    monkeypatch.setattr(event_log, "default_spool_dir", lambda: state / "agent-events")
    _ensure_build()
    server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
    from holdspeak.db import get_database
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services.primitive_service import PrimitiveService

    # A current decision exposes the real Friday runbook starter, as in the
    # owner's six-choice report, through the actual catalog source rules.
    PrimitiveService(get_database()).create_decision(
        Principal(PrincipalKind.OWNER, "glass"), decision_id="reported-cutover",
        title="Use the rollback checkpoint", decision_markdown="Keep the ledger checkpoint.",
    )
    repo = tmp_path / "home/dev/payments-ledger"
    (repo / ".git").mkdir(parents=True)
    transcript = tmp_path / "report.jsonl"
    transcript.write_text(json.dumps({"role": "assistant", "content": REPORT}) + "\n")
    spool = {"state_path": agent_context.AGENT_CONTEXT_FILE, "events_spool_dir": event_log.default_spool_dir()}
    for event in (
        {"hook_event_name": "Stop", "last_assistant_message": REPORT, "transcript_path": str(transcript)},
        {"hook_event_name": "PreToolUse", "tool_name": "Bash"},
    ):
        ingest_agent_hook_event(agent="codex", payload={"session_id": "reported-work", "cwd": str(repo), **event}, capture_messages=True, **spool)
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True, args=["--use-fake-device-for-media-stream", "--use-fake-ui-for-media-stream"])
            context = browser.new_context(viewport={"width": width, "height": 900 if width == 1440 else 852},
                                          device_scale_factor=1, has_touch=width < 720,
                                          reduced_motion="reduce", permissions=["microphone"])
            page = context.new_page()
            page.set_default_timeout(30_000)
            errors: list[str] = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.goto(f"{base}/?token={TOKEN}", wait_until="load")
            _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
            clear_hub_windows(page, TOKEN)
            page.goto(f"{base}/conductor?token={TOKEN}", wait_until="load")
            _normal_chair(page)
            page.locator(".conductor-window [data-object-id='coder:codex:reported-work']").get_by_test_id("conductor-open").click()
            agent = page.locator("[id='session'][data-layer='window']")
            agent.get_by_test_id("session-report").wait_for()
            assert REPORT in agent.inner_text()
            assert "Bash" in agent.get_by_test_id("session-activity").inner_text()
            portrait = agent.get_by_test_id("session-agent-portrait")
            page.wait_for_function("el => el.complete && el.naturalWidth > 0", arg=portrait.element_handle())
            assert "agent-codex" in str(portrait.get_attribute("src"))
            assert portrait.bounding_box()["width"] == 64
            assert not agent.locator("details.desk-session-details").evaluate("el => el.open")
            assert agent.locator(".desk-session-body").evaluate("el => el.scrollWidth <= el.clientWidth + 1")
            _settle(page)
            page.screenshot(path=str(SHOTS / f"agent-report-{width}.png"))
            agent.get_by_role("button", name=re.compile(r"^Give feedback on ")).click()
            page.locator("[data-ui-feedback]").get_by_text("RECORDING", exact=True).wait_for()
            page.wait_for_timeout(500)
            _save_feedback(page, width, shot_stem="reported-agent", window_id="session", draft=None,
                           png_regions={"portrait": portrait, "report": agent.get_by_test_id("session-report")})
            agent.locator(".desk-gadget-close").click()
            page.reload(wait_until="load")
            _normal_chair(page)

            page.get_by_role("button", name="Go", exact=True).first.click()
            page.locator("nav[aria-label='Go menu']").get_by_role("menuitem", name="Automations").first.click()
            page.get_by_test_id("automation-new").click()
            chooser = page.locator("[id='workbench:__new__'][data-layer='window']")
            scratch = chooser.get_by_test_id("automation-starter-scratch")
            scratch.wait_for()
            starters = _api(page, "GET", "/api/workbench-templates", token=TOKEN)["templates"]
            assert any(starter["id"] == "friday-runbook" for starter in starters)
            page.screenshot(path=str(SHOTS / f"new-automation-{width}.png"))
            for starter in starters:
                choice = chooser.get_by_test_id(f"automation-starter-{starter['id']}")
                _fit_and_hit(choice)
                page.wait_for_function("el => el.complete && el.naturalWidth > 0", arg=choice.locator("img").element_handle())
                description = choice.locator(".sr-only").bounding_box()
                assert description and description["width"] <= 1 and description["height"] <= 1, description
                assert choice.get_attribute("title") == starter["description"]
            _fit_and_hit(scratch)
            assert chooser.locator(".wb-body").evaluate("el => el.scrollWidth <= el.clientWidth + 1")
            page.screenshot(path=str(SHOTS / f"new-automation-{width}.png"))
            chooser.get_by_role("button", name="Give feedback on New Automation", exact=True).click()
            page.locator("[data-ui-feedback]").get_by_text("RECORDING", exact=True).wait_for()
            page.wait_for_timeout(500)
            _save_feedback(page, width, shot_stem="reported-automation", window_id="workbench:__new__", draft=None,
                           png_regions={"scratch": scratch, "choices": chooser.locator(".automation-starter-grid")})
            before = _api(page, "GET", "/api/workbenches", token=TOKEN)["workbenches"]
            with page.expect_response(lambda response: response.url.endswith("/api/workbench-templates/friday-team-update/instantiate") and response.request.method == "POST") as made:
                chooser.get_by_test_id("automation-starter-friday-team-update").click()
            assert made.value.ok, made.value.text()
            receipt = made.value.json()
            page.get_by_test_id("automation-window").wait_for()
            assert chooser.count() == 0
            after = _api(page, "GET", "/api/workbenches", token=TOKEN)["workbenches"]
            assert len(after) == len(before) + 1
            assert receipt["workbench"]["id"] in {row["id"] for row in after}
            assert not errors, errors
            browser.close()
    finally:
        server.stop()
