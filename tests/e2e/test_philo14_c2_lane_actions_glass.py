"""PHILO-14 C2 R2: the lane's actions through the REAL producers and routes.

Astra's counsel on #933 (seven findings) reproduced each defect on a real hub
with an isolated tmux `cat` session as the agent's pane. These fences are her
probes, kept: a real hub on an isolated HOME, the C2 glass seed (launch,
attempt, session, hook events, drafted answer, PR), a real tmux session bound
to the agent's session by the hook ingest, the real steer / arm / kill /
gate routes, and the real hook for a cleared wait.

1. the lane's Answer goes to its own session after Panes picks another pane;
2. an answer to a wait a real UserPromptSubmit cleared is refused (409
   ``wait_not_current``) and the field leaves;
3. Normal: the lane shows ARM with the mode; an unarmed Answer says ARM FIRST
   and sends nothing; after ARM the Answer is delivered;
4. Stop on a real tmux session: the launch reads ``stopped_by_owner`` with the
   audit row, the session's wait ends, the face shows STOPPED and withdraws
   Answer and Stop;
5. a Re-brief's receipt stays when its well closes;
6. the lane's words are 12 px at 393;
7. an unread answers / attempt / usage collection is a NOT READ line;
8. a held call minted through the gate route is approved from the lane.
"""
from __future__ import annotations

import subprocess
import time
import uuid
from pathlib import Path
from typing import Any

import pytest

from .glass_infra import _api, _api_allow_error, _boot, _ensure_build, _normal_chair, _settle
from .test_philo14_c2_lane_glass import KEY, QUESTION, SESSION_ID, TOKEN, _open_lane, _seed, mint_held_call

pytest.importorskip("playwright.sync_api", reason="the lane glass needs Playwright")

LANE = "/api/agent/launches/launch_c2_runbook/lane"


def _tmux(*argv: str) -> str:
    return subprocess.run(["tmux", *argv], check=True, capture_output=True, text=True).stdout.strip()


def _pane_text(name: str) -> str:
    return subprocess.run(["tmux", "capture-pane", "-p", "-t", name], capture_output=True, text=True).stdout


@pytest.fixture
def lane(tmp_path: Path, monkeypatch, request):
    """(page, hook, mode, url, seed, pane_name): the lane open on a real hub."""
    _ensure_build()
    import holdspeak.agent_context as agent_context_pkg
    import holdspeak.delivery.factory_launch as factory_launch
    import holdspeak.delivery.registry as delivery_registry
    from holdspeak.agent_context import event_log
    from holdspeak.services import agent_responder

    state = tmp_path / "home" / ".holdspeak"
    state.mkdir(parents=True)
    monkeypatch.setattr(factory_launch, "DEFAULT_LAUNCHES_PATH", state / "agent_launches.json")
    monkeypatch.setattr(delivery_registry, "DEFAULT_REGISTRY_PATH", state / "delivery_sources.json")
    monkeypatch.setattr(agent_context_pkg, "AGENT_CONTEXT_FILE", state / "agent_sessions.json")
    monkeypatch.setattr(agent_responder, "DEFAULT_ANSWERS_PATH", state / "agent_answers.json")
    monkeypatch.setattr(event_log, "default_spool_dir", lambda: state / "agent-events")
    mode = getattr(request, "param", "neutral")
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    name = f"c2-{uuid.uuid4().hex[:8]}"
    try:
        seed = _seed(tmp_path / "home")
        pane = _tmux("new-session", "-d", "-P", "-F", "#{pane_id}", "-s", name, "-c", seed["worktree"], "cat")

        def hook(kind: str, **data: Any) -> Any:
            return agent_context_pkg.ingest_agent_hook_event(
                agent="claude",
                payload={"session_id": SESSION_ID, "cwd": seed["worktree"], "tmux_pane": pane,
                         "hook_event_name": kind, **data},
                state_path=agent_context_pkg.AGENT_CONTEXT_FILE, events_spool_dir=event_log.default_spool_dir(),
            )

        session = hook("Notification", message=QUESTION)
        agent_responder.AnswerStore().put_wait(KEY, {
            "wait_id": session.wait_id, "state": "drafted", "verdict": "real",
            "reason": "it names a person", "draft": "Jordan owns it. Avery reviews.", "at": 0,
        })
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            page.goto(f"{url}/?token={TOKEN}", wait_until="load")
            _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
            _api(page, "PUT", "/api/authority/control-mode", {"control_mode": mode}, token=TOKEN)
            page.reload(wait_until="load")
            _normal_chair(page)
            _settle(page)
            _open_lane(page)
            try:
                yield page, hook, url, seed, name
            finally:
                browser.close()
    finally:
        server.stop()
        subprocess.run(["tmux", "kill-session", "-t", name], capture_output=True)


def _answer(page: Any, text: str) -> Any:
    field = page.get_by_role("textbox", name="Answer", exact=True)
    field.fill(text)
    with page.expect_response(lambda r: "/steer" in r.url and r.request.method == "POST") as got:
        field.press("Enter")
    return got.value


def _arm(page: Any) -> None:
    with page.expect_response(lambda r: r.url.endswith("/arm") and r.request.method == "POST") as got:
        page.locator("[data-testid='lane-arm']").get_by_role("button").click()
    assert got.value.status == 200, got.value.text()
    page.locator("[data-testid='lane-arm']").wait_for(state="detached", timeout=10000)


@pytest.mark.timeout(240)
def test_lane_actions_keep_launch_target_after_pane_picker(lane) -> None:
    page, _hook, _url, _seed_, name = lane
    other = f"{name}-other"
    _tmux("new-session", "-d", "-s", other, "cat")
    try:
        _arm(page)
        page.get_by_role("button", name="Panes", exact=True).click()
        page.locator(".desk-panepicker-item").filter(has_text=other).click()
        # The plain pane gets its own window; lane A keeps its question.
        page.locator(".is-session").wait_for(timeout=10000)
        assert page.locator("[data-testid='lane-ask'] .ask-well-question").inner_text() == QUESTION
        sent = _answer(page, "Jordan owns it, for launch A only.")
        assert sent.status == 200, sent.text()
        assert f"/api/coders/{KEY.replace(':', '%3A')}/steer" in sent.url
        deadline = time.monotonic() + 5
        while "for launch A only" not in _pane_text(name) and time.monotonic() < deadline:
            time.sleep(0.1)
        assert "for launch A only" in _pane_text(name)
        assert "for launch A only" not in _pane_text(other)
    finally:
        subprocess.run(["tmux", "kill-session", "-t", other], capture_output=True)


@pytest.mark.timeout(240)
def test_stale_wait_is_not_answerable(lane) -> None:
    page, hook, _url, _seed_, name = lane
    _arm(page)
    before = _api(page, "GET", LANE, token=TOKEN)["wait"]
    hook("UserPromptSubmit", prompt="Already answered elsewhere.")
    # The hub refuses an answer naming the cleared wait.
    status, body = _api_allow_error(page, "POST", f"/api/coders/{KEY}/steer",
                                    {"text": "A second answer.", "submit": True, "wait_id": before["wait_id"]}, token=TOKEN)
    assert status == 409 and body["status"] == "wait_not_current", body
    # An answer that names no wait at all is refused the same way.
    status, body = _api_allow_error(page, "POST", f"/api/coders/{KEY}/steer",
                                    {"text": "A third answer.", "submit": True, "kind": "answer"}, token=TOKEN)
    assert status == 409 and body["status"] == "wait_not_current", body
    time.sleep(0.5)
    assert "A second answer" not in _pane_text(name)
    assert "A third answer" not in _pane_text(name)
    # The face drops the field on its next read.
    page.locator("[data-testid='lane-ask']").wait_for(state="detached", timeout=15000)


@pytest.mark.timeout(240)
def test_normal_answer_shows_arm_then_completes_on_lane(lane) -> None:
    page, _hook, _url, _seed_, name = lane
    arm = page.locator("[data-testid='lane-arm']")
    assert "ARM FIRST" in arm.inner_text() and "NORMAL" in arm.inner_text().upper()
    field = page.get_by_role("textbox", name="Answer", exact=True)
    field.fill("Jordan owns it.")
    requests: list[str] = []
    page.on("request", lambda r: requests.append(r.url) if "/steer" in r.url else None)
    field.press("Enter")
    page.locator("[data-testid='lane-receipt']").filter(has_text="ARM FIRST").wait_for(timeout=5000)
    assert requests == []
    _arm(page)
    sent = _answer(page, "Jordan owns it.")
    assert sent.status == 200 and sent.json()["status"] == "delivered", sent.text()
    page.locator("[data-testid='lane-receipt']").filter(has_text="SENT").wait_for(timeout=5000)


@pytest.mark.timeout(240)
def test_stop_records_a_stopped_launch(lane) -> None:
    page, _hook, _url, _seed_, name = lane
    # The agent's session has a second pane: Stop ends the whole session.
    _tmux("split-window", "-d", "-t", name, "cat")
    assert len(_tmux("list-panes", "-t", name, "-F", "#{pane_id}").split()) == 2
    page.locator("[data-testid='lane-stop']").click()
    confirm = page.locator("[data-testid='lane-stop-confirm']")
    assert confirm.inner_text() == "Stop · sure? (ends the agent's session)"
    calls: list[str] = []
    page.on("request", lambda r: calls.append(r.url) if r.method == "POST" and "/api/coders/" in r.url else None)
    confirm.click()
    page.locator("[data-testid='lane-receipt']").filter(has_text="ARM FIRST").wait_for(timeout=5000)
    assert calls == [], "Normal: Stop never arms by itself"
    page.locator("[data-testid='lane-arm-footer']").get_by_role("button").click()
    page.locator("[data-testid='lane-arm-footer']").wait_for(state="detached", timeout=10000)
    with page.expect_response(lambda r: r.url.endswith("/kill")) as got:
        page.locator("[data-testid='lane-stop-confirm']").click()
    assert got.value.status == 200 and got.value.json()["status"] == "killed", got.value.text()
    after = _api(page, "GET", LANE, token=TOKEN)
    assert after["launch"]["state"] == "stopped_by_owner"
    assert after["launch"]["stopped"]["audit_id"] is not None
    assert after["wait"] is None
    page.locator("[data-testid='lane-stopped']").wait_for(timeout=10000)
    assert page.locator("[data-testid='lane-ask']").count() == 0
    assert page.locator("[data-testid='lane-stop']").count() == 0
    assert subprocess.run(["tmux", "has-session", "-t", name], capture_output=True).returncode != 0


@pytest.mark.timeout(240)
def test_rebrief_receipt_survives_send(lane) -> None:
    page, hook, _url, _seed_, name = lane
    _arm(page)
    hook("UserPromptSubmit", prompt="Existing question answered.")
    page.locator("[data-testid='lane-ask']").wait_for(state="detached", timeout=15000)
    # PHILO-15 14 (#996): mid-turn a Re-brief is QUEUED · AFTER THIS TURN
    # (launch_rebrief.MID_TURN_EVENTS); the turn ends, so it is typed now: SENT.
    hook("Stop")
    # Re-brief types into the LAUNCH's own pane (FirstMessage.retarget reads the
    # launch record's tmux session), so the seeded launch names this rig's pane.
    from holdspeak.delivery.factory_launch import LaunchLedger

    LaunchLedger().update("launch_c2_runbook", session=name)
    page.locator("[data-testid='lane-rebrief']").click()
    field = page.get_by_role("textbox", name="Re-brief", exact=True)
    field.fill("Re-brief: Jordan owns it.")
    # PHILO-15 14 (#996): Re-brief posts the launch's own route
    # (laneStore.sendRebrief: /api/agent/launches/<id>/rebrief), not /steer.
    with page.expect_response(lambda r: r.url.endswith("/rebrief") and r.request.method == "POST") as got:
        field.press("Enter")
    assert got.value.status == 200, got.value.text()
    page.locator("[data-testid='lane-rebrief-well']").wait_for(state="detached", timeout=5000)
    receipt = page.locator("[data-testid='lane-receipt']")
    assert receipt.count() == 1 and "SENT" in receipt.inner_text() and "Jordan owns it" in receipt.inner_text()
    # It is still there after the next reads.
    page.wait_for_timeout(5500)
    assert "SENT" in page.locator("[data-testid='lane-receipt']").inner_text()


@pytest.mark.timeout(240)
def test_lane_words_are_12px_at_393(lane) -> None:
    page = lane[0]
    page.set_viewport_size({"width": 393, "height": 852})
    page.wait_for_timeout(400)
    sizes = page.locator(".is-lane .lw-word, .is-lane .lane-word").evaluate_all(
        "(els) => [...new Set(els.map((e) => getComputedStyle(e).fontSize))]")
    assert sizes == ["12px"], sizes


@pytest.mark.timeout(240)
def test_unread_collections_remain_visible(lane, monkeypatch) -> None:
    page = lane[0]
    import holdspeak.agent_context as agent_context_pkg
    import holdspeak.web.routes.agent_hand as agent_hand
    from holdspeak.db import get_database
    from holdspeak.services import launch_lane as lane_mod

    db = get_database()
    secret = "ghp_" + "A1b2C3d4E5f6G7h8I9j0K1l2"

    def unread(*_a: Any, **_k: Any) -> Any:
        raise RuntimeError(f"collection read failed token={secret}")

    monkeypatch.setattr(db.steering, "list", unread)
    monkeypatch.setattr(db.work_attempts, "events", unread)
    monkeypatch.setattr(db.gate, "usage_for", unread)
    # The session and control reads fail too, each naming a secret.
    monkeypatch.setattr(lane_mod, "_session_view", unread)
    monkeypatch.setattr(agent_hand, "lane_control", unread)
    wire = _api(page, "GET", LANE, token=TOKEN)
    for part in ("answers", "attempt_events", "usage", "session", "control"):
        assert "not_read" in wire[part], (part, wire[part])
    import json as _json

    assert secret not in _json.dumps(wire) and secret[:12] not in _json.dumps(wire)
    for part in ("answers", "attempt", "usage", "session", "control"):
        page.locator(f"[data-testid='lane-not-read-{part}']").wait_for(timeout=15000)
    face = page.locator(".is-lane").inner_text()
    assert "NOT READ" in page.locator("[data-testid='lane-not-read-control']").inner_text()
    assert secret not in face and secret[:12] not in face


@pytest.mark.timeout(240)
def test_gate_call_from_the_route_is_approved_from_the_lane(lane) -> None:
    page, _hook, url, seed, _name = lane
    mint_held_call(url, seed["worktree"], command="cat /etc/review-file", proposal_id="toolu_review")
    row = page.locator(".lane-rail-entry").filter(has_text="cat /etc/review-file")
    row.wait_for(timeout=15000)
    with page.expect_response(lambda r: "/toolu_review/decide" in r.url) as got:
        row.locator("[data-testid='lane-approve']").click()
    assert got.value.status == 200, got.value.text()
    assert _api(page, "GET", "/api/gate/proposals/toolu_review", token=TOKEN)["state"] == "approved"
    status, _body = _api_allow_error(page, "POST", "/api/gate/proposals/toolu_review/decide",
                                     {"decision": "denied"}, token=TOKEN)
    assert status == 409
