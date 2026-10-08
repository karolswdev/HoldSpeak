"""PHILO-15 20 (B63): a CUT held call is read whole and approved in Raw.

A real hub on an isolated HOME, the C2 lane seed, and a long held call minted
through the real gate route in the body the gate hook builds
(``coder_gate.redact_call``: the 120-char head, the length, and now the whole
REDACTED call of a cut hold). At 1440 the lane's rail offers Raw on the cut
call; Raw shows the whole command from the hub with Deny and Approve. At 393
the Needs row keeps Deny + Open; Open opens the lane on Raw, and Approve there
decides the real proposal.

Shots: docs/internal/philo/phase-15/20-shots/.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from .glass_infra import _api, _assert_clean, _boot, _ensure_build, _normal_chair, _settle
from .test_philo14_c2_lane_glass import KEY, TOKEN, _http, _open_lane, _seed

pytest.importorskip("playwright.sync_api", reason="the Raw glass needs Playwright")

SHOTS = Path(__file__).resolve().parents[2] / "docs" / "internal" / "philo" / "phase-15" / "20-shots"


def _mint_cut(url: str, worktree: str, command: str, proposal_id: str) -> dict:
    from holdspeak.coder_gate import redact_call

    status, issued = _http(url, "POST", "/api/principals/agents", TOKEN, {"identity": KEY})
    assert status == 201, issued
    call = redact_call({"command": command})
    assert call.full, "a cut call carries its whole redacted text"
    status, body = _http(url, "POST", "/api/gate/proposals", issued["credential"], {
        "id": proposal_id, "tool": "Bash", "args_sha256": call.sha256, "args_head": call.head,
        "args_len": call.length, "args_full": call.full, "cwd": worktree, "ttl_seconds": 3600,
        "classification": {"scope": "outside", "rule": "cwd_outside_worktree", "read_rule": "",
                           "push_branch": "", "root": worktree, "proposal_id": proposal_id,
                           "args_sha256": call.sha256},
    })
    assert status == 200 and body["state"] == "held", body
    return body


def _open_needs(page: Any) -> None:
    if page.locator("[data-testid='needs-drawer']").count():
        return
    icon = page.locator(".desk-screen [data-object-id='drawer:needs']")
    icon.focus()
    page.keyboard.press("Enter")
    page.locator("[data-testid='needs-drawer']").wait_for(timeout=10000)


@pytest.mark.timeout(240)
def test_raw_shows_a_cut_call_whole_and_approves_it_at_1440_and_393(tmp_path: Path, monkeypatch) -> None:
    _ensure_build()
    import holdspeak.agent_context as agent_context_pkg
    import holdspeak.delivery.factory_launch as factory_launch
    import holdspeak.delivery.registry as delivery_registry
    from holdspeak.agent_context import event_log
    from holdspeak.services import agent_responder

    SHOTS.mkdir(parents=True, exist_ok=True)
    state = tmp_path / "home" / ".holdspeak"
    state.mkdir(parents=True)
    monkeypatch.setattr(factory_launch, "DEFAULT_LAUNCHES_PATH", state / "agent_launches.json")
    monkeypatch.setattr(delivery_registry, "DEFAULT_REGISTRY_PATH", state / "delivery_sources.json")
    monkeypatch.setattr(agent_context_pkg, "AGENT_CONTEXT_FILE", state / "agent_sessions.json")
    monkeypatch.setattr(agent_responder, "DEFAULT_ANSWERS_PATH", state / "agent_answers.json")
    monkeypatch.setattr(event_log, "default_spool_dir", lambda: state / "agent-events")
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    errors: list[str] = []
    try:
        seed = _seed(tmp_path / "home")
        # The launch's registered session (as a Hand to agent leaves it once
        # its hook registered): Needs you reads a hold of THIS launch.
        factory_launch.LaunchLedger().update("launch_c2_runbook", session_key=KEY)
        clone = "/private/var/folders/q7/T/hs-r2/.holdspeak/repositories/karolswdev/holdspeak-dayone-rehearsal-1558"
        command = (
            f"cd {clone} && pwd && echo \"---BRANCH---\" && git branch --show-current && echo \"---STATUS---\" "
            "&& git status && echo \"---LOG---\" && git log --oneline -5"
        )
        _mint_cut(url, seed["worktree"], command, "toolu_cut_1440")
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser = pw.chromium.launch()

            # 1440: the lane's rail offers Raw on the cut call.
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.goto(f"{url}/?token={TOKEN}", wait_until="load")
            _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
            page.reload(wait_until="load")
            _normal_chair(page)
            _settle(page)
            _open_lane(page)
            raw_verb = page.locator("[data-testid='lane-rail'] [data-testid='lane-raw-cut']").first
            raw_verb.wait_for(timeout=15000)
            assert page.locator("[data-testid='lane-rail'] [data-testid='lane-approve']").count() == 0
            raw_verb.click()
            held = page.locator("[data-testid='lane-raw-held']").first
            held.wait_for(timeout=10000)
            shown = page.locator("[data-testid='lane-raw-command']").first
            shown.wait_for(timeout=10000)
            assert (shown.text_content() or "") == command
            assert (held.locator(".lw-caption").text_content() or "").startswith("HELD · OUTSIDE THE WORKTREE")
            assert held.locator("[data-testid='lane-raw-approve']").is_visible()
            assert held.locator("[data-testid='lane-raw-deny']").is_visible()
            page.wait_for_timeout(300)
            page.screenshot(path=str(SHOTS / "01-lane-raw-approve-1440.png"))
            with page.expect_response(lambda r: "/toolu_cut_1440/decide" in r.url) as got:
                held.locator("[data-testid='lane-raw-approve']").click()
            assert got.value.status == 200, got.value.text()
            assert _api(page, "GET", "/api/gate/proposals/toolu_cut_1440", token=TOKEN)["state"] == "approved"
            page.locator("[data-testid='lane-raw-held']").wait_for(state="detached", timeout=15000)
            page.close()

            # 393: the Needs row keeps Deny + Open; Open opens the lane on Raw.
            _mint_cut(url, seed["worktree"], command.replace("-5", "-3"), "toolu_cut_393")
            page = browser.new_page(viewport={"width": 393, "height": 852})
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.goto(f"{url}/?token={TOKEN}", wait_until="load")
            _normal_chair(page)
            _settle(page)
            _open_needs(page)
            row = page.locator("[data-testid='needs-drawer'] [data-testid='needs-row']", has_text="CUT · APPROVE IN RAW")
            row.wait_for(timeout=15000)
            assert row.locator("[data-verb='approve']").count() == 0
            assert row.locator("[data-verb='deny']").count() == 1
            page.wait_for_timeout(300)
            page.screenshot(path=str(SHOTS / "02-needs-cut-row-393.png"))
            row.locator("[data-verb='open']").click()
            held = page.locator("[data-testid='lane-raw-held']").first
            held.wait_for(timeout=15000)
            shown = page.locator("[data-testid='lane-raw-command']").first
            shown.wait_for(timeout=10000)
            assert (shown.text_content() or "") == command.replace("-5", "-3")
            assert page.evaluate("document.scrollingElement.scrollWidth <= window.innerWidth")
            approve = held.locator("[data-testid='lane-raw-approve']")
            box = approve.bounding_box()
            assert box and box["x"] >= 0 and box["x"] + box["width"] <= 393, box
            page.wait_for_timeout(300)
            page.screenshot(path=str(SHOTS / "03-lane-raw-approve-393.png"))
            with page.expect_response(lambda r: "/toolu_cut_393/decide" in r.url) as got:
                approve.click()
            assert got.value.status == 200, got.value.text()
            assert _api(page, "GET", "/api/gate/proposals/toolu_cut_393", token=TOKEN)["state"] == "approved"
            page.locator("[data-testid='lane-raw-held']").wait_for(state="detached", timeout=15000)
            page.wait_for_timeout(300)
            page.screenshot(path=str(SHOTS / "04-lane-raw-approved-393.png"))
            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()
