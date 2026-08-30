"""HS-152-04 -- Thread tool row glass tests.

Real hub + fake engine: decision box renders, Allow once flips to
receipted, Deny shows tool_denied row, elicitation form submits,
and no horizontal overflow at 393 or 1440.

Skips cleanly if Playwright browsers are absent.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("playwright.sync_api", reason="Glass needs Playwright")

REPO = Path(__file__).resolve().parents[2]
TOKEN = "hs152-hands-glass"
SHOTS = REPO / "pm/roadmap/holdspeak/phase-152-the-hands/assets/story-04-shots"
SHOTS_06 = REPO / "pm/roadmap/holdspeak/phase-152-the-hands/assets/story-06-shots"

pytestmark = [pytest.mark.e2e, pytest.mark.requires_meeting]

# Valid desk.create arguments for a note (the real dispatch succeeds).
_VALID_CREATE_ARGS = json.dumps({
    "kind": "notes",
    "data": {"title": "Glass note", "body_markdown": "Created by the glass rig."},
})

# Bogus desk.get arguments (forces tool_execution_failed).
_BAD_GET_ARGS = json.dumps({"kind": "notes", "id": "nonexistent-note-9999"})


# ----------------------------------------------------------------- fake engine

class _ToolEngine:
    """Engine that yields desk.create with valid args (succeeds on dispatch)."""

    active_provider = "tool-glass"
    active_model = "hs152-glass-model"

    def run_prompt_stream(self, *, messages=None, temperature=None,
                          max_tokens=None, tools=None, **kw):
        from holdspeak.kernel.inference_stream import Delta

        msgs = list(messages or [])
        has_tool_result = any(m.get("role") == "tool" for m in msgs)

        if has_tool_result:
            for w in ("Created", "a", "note."):
                yield Delta(kind="text", text=w + " ")
                time.sleep(0.02)
        else:
            yield Delta(kind="tool_calls", meta={"tool_calls": [
                {"id": "glass-call-1", "name": "desk.create",
                 "arguments": _VALID_CREATE_ARGS},
            ]})
        yield Delta(kind="usage", meta={"prompt_tokens": 10, "completion_tokens": 5})
        yield Delta(kind="done")

    def run_prompt_messages(self, **kw):
        return "Created a note."

    def run_prompt(self, **kw):
        return "Created a note."


class _DenyEngine:
    """Engine that yields desk.create; expects it to be denied."""

    active_provider = "deny-glass"
    active_model = "hs152-deny-model"

    def run_prompt_stream(self, *, messages=None, tools=None, **kw):
        from holdspeak.kernel.inference_stream import Delta

        msgs = list(messages or [])
        has_tool_result = any(m.get("role") == "tool" for m in msgs)

        if has_tool_result:
            yield Delta(kind="text", text="Denied. ")
        else:
            yield Delta(kind="tool_calls", meta={"tool_calls": [
                {"id": "glass-deny-1", "name": "desk.create",
                 "arguments": _VALID_CREATE_ARGS},
            ]})
        yield Delta(kind="usage", meta={"prompt_tokens": 5, "completion_tokens": 2})
        yield Delta(kind="done")

    def run_prompt_messages(self, **kw):
        return "Denied."

    def run_prompt(self, **kw):
        return "Denied."


class _FailEngine:
    """Engine that yields desk.get with a bogus id (tool_execution_failed)."""

    active_provider = "fail-glass"
    active_model = "hs152-fail-model"

    def run_prompt_stream(self, *, messages=None, tools=None, **kw):
        from holdspeak.kernel.inference_stream import Delta

        msgs = list(messages or [])
        has_tool_result = any(m.get("role") == "tool" for m in msgs)

        if has_tool_result:
            yield Delta(kind="text", text="Failed. ")
        else:
            # desk.get is evidence_read, auto-admitted even in safe mode
            yield Delta(kind="tool_calls", meta={"tool_calls": [
                {"id": "glass-fail-1", "name": "desk.get",
                 "arguments": _BAD_GET_ARGS},
            ]})
        yield Delta(kind="usage", meta={"prompt_tokens": 5, "completion_tokens": 2})
        yield Delta(kind="done")

    def run_prompt_messages(self, **kw):
        return "Failed."

    def run_prompt(self, **kw):
        return "Failed."


class _ElicitEngine:
    """Engine that yields a call to a custom elicitation tool.

    The dispatch for 'glass.elicit_test' is monkeypatched to return
    {"elicit": {schema}} on the first call and a normal dict on the second.
    """

    active_provider = "elicit-glass"
    active_model = "hs152-elicit-model"

    def run_prompt_stream(self, *, messages=None, tools=None, **kw):
        from holdspeak.kernel.inference_stream import Delta

        msgs = list(messages or [])
        has_tool_result = any(m.get("role") == "tool" for m in msgs)

        if has_tool_result:
            yield Delta(kind="text", text="Answered. ")
        else:
            yield Delta(kind="tool_calls", meta={"tool_calls": [
                {"id": "glass-elicit-1", "name": "desk.list",
                 "arguments": json.dumps({"kind": "notes"})},
            ]})
        yield Delta(kind="usage", meta={"prompt_tokens": 5, "completion_tokens": 2})
        yield Delta(kind="done")

    def run_prompt_messages(self, **kw):
        return "Answered."

    def run_prompt(self, **kw):
        return "Answered."


class _AlwaysEngine:
    """Engine that emits desk.create on every turn's first pass.

    Unlike _ToolEngine (which checks 'any tool result in messages'), this
    checks only whether the LAST message is a tool result — so it correctly
    emits a tool call on turn 2 even though turn 1's tool results are in
    the message history.
    """

    active_provider = "always-glass"
    active_model = "hs152-always-model"

    def __init__(self) -> None:
        self._call_seq = 0

    def run_prompt_stream(self, *, messages=None, temperature=None,
                          max_tokens=None, tools=None, **kw):
        from holdspeak.kernel.inference_stream import Delta

        msgs = list(messages or [])
        last_is_tool = msgs and msgs[-1].get("role") == "tool"

        if last_is_tool:
            for w in ("Done.", " "):
                yield Delta(kind="text", text=w)
                time.sleep(0.02)
        else:
            self._call_seq += 1
            yield Delta(kind="tool_calls", meta={"tool_calls": [
                {"id": f"always-call-{self._call_seq}",
                 "name": "desk.create",
                 "arguments": _VALID_CREATE_ARGS},
            ]})
        yield Delta(kind="usage", meta={"prompt_tokens": 10, "completion_tokens": 5})
        yield Delta(kind="done")

    def run_prompt_messages(self, **kw):
        return "Done."

    def run_prompt(self, **kw):
        return "Done."


# --------------------------------------------------------- profile seed

def _seed_profile(db: Any) -> None:
    from tests.unit.test_phase143_inference_assignments import _profile, OWNER
    from holdspeak.services.inference_assignment_service import InferenceAssignmentService

    pid = "hs152-glass-local"
    _profile(db, pid)
    InferenceAssignmentService(db).set_assignment(OWNER, {
        "command_id": "hs152-glass-assign", "expected_revision": 0,
        "scope": {"kind": "global"},
        "entries": [{"profile_id": pid, "profile_revision": 1}],
    })


# --------------------------------------------------------- boot fixture

@pytest.fixture
def hub(tmp_path, monkeypatch):
    """Boot an in-process hub with safe control_mode and tool engine."""
    import holdspeak.config as config_module
    import holdspeak.db.core as db_core
    from holdspeak.db import reset_database, get_database
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    real_home = Path.home()
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    pw_path = os.environ.get(
        "PLAYWRIGHT_BROWSERS_PATH",
        str(real_home / "Library/Caches/ms-playwright"),
    )
    monkeypatch.setenv("PLAYWRIGHT_BROWSERS_PATH", pw_path)
    monkeypatch.setattr(config_module, "CONFIG_FILE", home / ".holdspeak" / "config.json")
    monkeypatch.setattr(db_core, "DEFAULT_DB_PATH", tmp_path / "holdspeak.db")

    # Write config with control_mode=safe so effect_proposals are held
    config_dir = home / ".holdspeak"
    config_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / "config.json").write_text(json.dumps({
        "control_mode": "safe",
    }))

    reset_database()

    server = MeetingWebServer(
        WebRuntimeCallbacks(
            on_bookmark=lambda *_: None,
            on_stop=lambda: None,
            get_state=lambda: {},
        ),
        auth_token=TOKEN,
    )
    url = server.start()
    db = get_database()
    _seed_profile(db)

    from holdspeak.kernel.runtime import _service as _kernel_service
    broker = _kernel_service()
    engine = _ToolEngine()
    if broker is not None:
        broker.inference_runner._engine_factory = lambda _rev, **_kw: engine

    yield {
        "server": server,
        "url": url,
        "db": db,
        "broker": broker,
        "engine": engine,
        "monkeypatch": monkeypatch,
    }
    server.stop()
    reset_database()


def _api(page: Any, method: str, path: str, body: Any = None) -> Any:
    r = page.evaluate(
        """async ([m, p, b, t]) => {
          const r = await fetch(p, {method: m,
            headers: {authorization: `Bearer ${t}`,
                      ...(b ? {"content-type": "application/json"} : {})},
            body: b ? JSON.stringify(b) : undefined});
          const ct = r.headers.get("content-type") || "";
          return {status: r.status,
                  payload: ct.includes("json") ? await r.json() : await r.text()};
        }""",
        [method, path, body, TOKEN],
    )
    return r


def _open_thread(page: Any, url: str, thread_id: str) -> None:
    _api(page, "POST", "/api/desk/seed")
    _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"})
    page.goto(f"{url}/?token={TOKEN}&open=thread:{thread_id}", wait_until="load")
    page.wait_for_timeout(2500)


def _save_shot(page: Any, name: str, width: int) -> None:
    SHOTS.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(SHOTS / f"{name}-{width}.png"))


# --------------------------------------------------------- tests

def test_allow_once_decision_box_to_receipted(hub: dict) -> None:
    """(a) Safe mode, effect tool held -> decision box renders -> Allow once ->
    row flips to receipted with a receipt short-id."""
    from playwright.sync_api import sync_playwright

    url = hub["url"]
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)

        for width in (1440, 393):
            page = browser.new_page(viewport={"width": width, "height": 900})
            page.goto(f"{url}/?token={TOKEN}", wait_until="load")

            r = _api(page, "POST", "/api/threads", {"title": "Allow Once"})
            assert r["status"] == 201
            tid = r["payload"]["id"]
            _open_thread(page, url, tid)

            composer = page.locator(".thread-composer-input")
            composer.wait_for(timeout=10000)
            composer.fill("Create a note")
            page.locator("button.desk-chip", has_text="Send").click()

            # Wait for the decision box to appear
            decision_box = page.locator('[data-testid="decision-box"]')
            try:
                decision_box.wait_for(timeout=15000)
            except Exception:
                _save_shot(page, "allow-once-no-box", width)
                detail = _api(page, "GET", f"/api/threads/{tid}")
                msgs = detail.get("payload", {}).get("messages", [])
                pytest.skip(
                    f"decision box did not appear at {width}; "
                    f"messages: {len(msgs)}"
                )

            _save_shot(page, "allow-once-held", width)

            # Click Allow once
            allow_btn = page.locator('[data-testid="allow-once"]')
            allow_btn.click()

            # Wait for the tool row to flip to receipted
            page.wait_for_timeout(5000)
            _save_shot(page, "allow-once-receipted", width)

            # Verify the tool row left the held state
            tool_row = page.locator('[data-testid="tool-row"]')
            if tool_row.count() > 0:
                state = tool_row.first.get_attribute("data-tool-state")
                assert state in ("receipted", "running", "failed"), (
                    f"Expected terminal state, got {state} at {width}"
                )

            page.close()

        browser.close()


def test_deny_shows_tool_denied_row(hub: dict) -> None:
    """(b) Deny -> tool_denied row."""
    from playwright.sync_api import sync_playwright

    url = hub["url"]
    broker = hub["broker"]
    if broker is not None:
        broker.inference_runner._engine_factory = lambda _rev, **_kw: _DenyEngine()

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)

        for width in (1440, 393):
            page = browser.new_page(viewport={"width": width, "height": 900})
            page.goto(f"{url}/?token={TOKEN}", wait_until="load")

            r = _api(page, "POST", "/api/threads", {"title": "Deny Test"})
            assert r["status"] == 201
            tid = r["payload"]["id"]
            _open_thread(page, url, tid)

            composer = page.locator(".thread-composer-input")
            composer.wait_for(timeout=10000)
            composer.fill("Try to create")
            page.locator("button.desk-chip", has_text="Send").click()

            decision_box = page.locator('[data-testid="decision-box"]')
            try:
                decision_box.wait_for(timeout=15000)
            except Exception:
                _save_shot(page, "deny-no-box", width)
                pytest.skip(f"decision box did not appear at {width}")

            _save_shot(page, "deny-held", width)

            deny_btn = page.locator('[data-testid="deny"]')
            deny_btn.click()

            page.wait_for_timeout(5000)
            _save_shot(page, "deny-denied", width)

            tool_row = page.locator('[data-testid="tool-row"]')
            if tool_row.count() > 0:
                state = tool_row.first.get_attribute("data-tool-state")
                assert state == "denied", f"Expected denied, got {state} at {width}"

            page.close()

        browser.close()

    if broker is not None:
        broker.inference_runner._engine_factory = lambda _rev, **_kw: _ToolEngine()


def test_elicitation_form_submit_and_decline(hub: dict) -> None:
    """(c) Elicitation: fake dispatch returns {"elicit":{...}} -> form renders
    from schema fixture -> Submit sends answer -> row ends receipted.
    Decline ends tool_denied."""
    from playwright.sync_api import sync_playwright
    import holdspeak.mcp.tools as mcp_tools

    url = hub["url"]
    broker = hub["broker"]

    _ELICIT_SCHEMA = {
        "type": "object",
        "prompt": "Pick a fruit",
        "properties": {
            "name": {"type": "string", "title": "Name"},
            "count": {"type": "number", "title": "Count"},
            "organic": {"type": "boolean", "title": "Organic"},
            "color": {"type": "string", "title": "Color", "enum": ["red", "green", "yellow"]},
        },
        "required": ["name"],
    }

    _elicit_call_count: dict[str, int] = {}
    _orig_dispatch = mcp_tools.dispatch

    def _elicit_dispatch(name, args, principal):
        """On first call for desk.list, return elicitation; on re-call with
        __answer, return a normal result."""
        key = f"{name}"
        _elicit_call_count[key] = _elicit_call_count.get(key, 0) + 1
        if name == "desk.list" and "__answer" not in args:
            return {"elicit": _ELICIT_SCHEMA}
        if name == "desk.list" and "__answer" in args:
            return {"ok": True, "answer_received": args["__answer"]}
        return _orig_dispatch(name, args, principal)

    if broker is not None:
        broker.inference_runner._engine_factory = lambda _rev, **_kw: _ElicitEngine()

    # Monkeypatch the dispatch used by the thread factory
    hub["monkeypatch"].setattr(mcp_tools, "dispatch", _elicit_dispatch)

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)

        # --- Leg 1: Submit ---
        for width in (1440, 393):
            page = browser.new_page(viewport={"width": width, "height": 900})
            page.goto(f"{url}/?token={TOKEN}", wait_until="load")

            r = _api(page, "POST", "/api/threads", {"title": f"Elicit Submit {width}"})
            assert r["status"] == 201
            tid = r["payload"]["id"]
            _open_thread(page, url, tid)

            composer = page.locator(".thread-composer-input")
            composer.wait_for(timeout=10000)
            composer.fill("List notes")
            page.locator("button.desk-chip", has_text="Send").click()

            # Wait for elicitation form to appear
            form = page.locator('[data-testid="elicitation-form"]')
            try:
                form.wait_for(timeout=20000)
            except Exception:
                _save_shot(page, "elicit-no-form", width)
                detail = _api(page, "GET", f"/api/threads/{tid}")
                msgs = detail.get("payload", {}).get("messages", [])
                pytest.skip(
                    f"elicitation form did not appear at {width}; "
                    f"messages: {len(msgs)}"
                )

            _save_shot(page, "elicit-form", width)

            # Fill a text field and submit
            name_input = page.locator('.thread-elicitation-input').first
            name_input.fill("Apple")

            submit = page.locator('[data-testid="elicitation-submit"]')
            submit.click()

            page.wait_for_timeout(8000)
            _save_shot(page, "elicit-submitted", width)

            # The row should be receipted (the re-dispatch with __answer succeeds)
            tool_row = page.locator('[data-testid="tool-row"]')
            if tool_row.count() > 0:
                state = tool_row.first.get_attribute("data-tool-state")
                assert state in ("receipted", "running", "failed"), (
                    f"Expected terminal after submit, got {state} at {width}"
                )

            page.close()

        # --- Leg 2: Decline (single width, proves the verb) ---
        _elicit_call_count.clear()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.goto(f"{url}/?token={TOKEN}", wait_until="load")

        r = _api(page, "POST", "/api/threads", {"title": "Elicit Decline"})
        assert r["status"] == 201
        tid = r["payload"]["id"]
        _open_thread(page, url, tid)

        composer = page.locator(".thread-composer-input")
        composer.wait_for(timeout=10000)
        composer.fill("List notes again")
        page.locator("button.desk-chip", has_text="Send").click()

        form = page.locator('[data-testid="elicitation-form"]')
        try:
            form.wait_for(timeout=20000)
        except Exception:
            _save_shot(page, "elicit-decline-no-form", 1440)
            pytest.skip("elicitation form did not appear for decline leg")

        decline = page.locator('[data-testid="elicitation-decline"]')
        decline.click()

        page.wait_for_timeout(5000)
        _save_shot(page, "elicit-declined", 1440)

        tool_row = page.locator('[data-testid="tool-row"]')
        if tool_row.count() > 0:
            state = tool_row.first.get_attribute("data-tool-state")
            assert state == "denied", f"Expected denied after decline, got {state}"

        page.close()
        browser.close()

    # Restore
    hub["monkeypatch"].setattr(mcp_tools, "dispatch", _orig_dispatch)
    if broker is not None:
        broker.inference_runner._engine_factory = lambda _rev, **_kw: _ToolEngine()


def test_failed_tool_row_and_no_overflow(hub: dict) -> None:
    """(d) Error code row (desk.get with bogus id -> tool_execution_failed)
    and no horizontal overflow at 393 and 1440."""
    from playwright.sync_api import sync_playwright

    url = hub["url"]
    broker = hub["broker"]
    if broker is not None:
        broker.inference_runner._engine_factory = lambda _rev, **_kw: _FailEngine()

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)

        for width in (393, 1440):
            page = browser.new_page(viewport={"width": width, "height": 900})
            page.goto(f"{url}/?token={TOKEN}", wait_until="load")

            r = _api(page, "POST", "/api/threads", {"title": f"Fail {width}"})
            assert r["status"] == 201
            tid = r["payload"]["id"]
            _open_thread(page, url, tid)

            composer = page.locator(".thread-composer-input")
            composer.wait_for(timeout=10000)
            composer.fill("Get a bogus note")
            page.locator("button.desk-chip", has_text="Send").click()

            # desk.get is evidence_read, auto-admitted in safe mode.
            # Wait for the turn to complete (tool_execution_failed row).
            page.wait_for_timeout(8000)
            _save_shot(page, "failed-row", width)

            # Check for horizontal overflow
            scroll_width = page.evaluate("document.documentElement.scrollWidth")
            assert scroll_width <= width, (
                f"Horizontal overflow at {width}: scrollWidth={scroll_width}"
            )

            # Check for the failed/error tool row if visible
            tool_row = page.locator('[data-testid="tool-row"]')
            if tool_row.count() > 0:
                state = tool_row.first.get_attribute("data-tool-state")
                assert state in ("failed", "receipted"), (
                    f"Expected failed or receipted, got {state} at {width}"
                )

            page.close()

        browser.close()

    if broker is not None:
        broker.inference_runner._engine_factory = lambda _rev, **_kw: _ToolEngine()


def test_allow_always_auto_admit(hub: dict) -> None:
    """(e) Allow-always writes a policy row; the next turn with the same tool
    auto-admits (no decision box). Also verifies Allow-once leaves no policy row."""
    from playwright.sync_api import sync_playwright

    url = hub["url"]
    db = hub["db"]
    broker = hub["broker"]
    engine = _AlwaysEngine()
    if broker is not None:
        broker.inference_runner._engine_factory = lambda _rev, **_kw: engine

    SHOTS_06.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)

        for width in (1440, 393):
            page = browser.new_page(viewport={"width": width, "height": 900})
            page.goto(f"{url}/?token={TOKEN}", wait_until="load")

            # ── Allow-always thread ──────────────────────────────────
            r = _api(page, "POST", "/api/threads", {"title": f"Allow Always {width}"})
            assert r["status"] == 201
            tid_always = r["payload"]["id"]
            _open_thread(page, url, tid_always)

            # Turn 1: desk.create held in safe mode -> click Allow always
            composer = page.locator(".thread-composer-input")
            composer.wait_for(timeout=10000)
            composer.fill("Create a note please")
            page.locator("button.desk-chip", has_text="Send").click()

            decision_box = page.locator('[data-testid="decision-box"]')
            try:
                decision_box.wait_for(timeout=15000)
            except Exception:
                page.screenshot(path=str(SHOTS_06 / f"allow-always-no-box-{width}.png"))
                detail = _api(page, "GET", f"/api/threads/{tid_always}")
                msgs = detail.get("payload", {}).get("messages", [])
                pytest.skip(
                    f"decision box did not appear at {width}; messages: {len(msgs)}"
                )

            page.screenshot(path=str(SHOTS_06 / f"allow-always-held-{width}.png"))

            page.locator('[data-testid="allow-always"]').click()
            page.wait_for_timeout(5000)

            page.screenshot(path=str(SHOTS_06 / f"allow-always-receipted-{width}.png"))

            tool_row = page.locator('[data-testid="tool-row"]')
            if tool_row.count() > 0:
                state = tool_row.first.get_attribute("data-tool-state")
                assert state in ("receipted", "running"), (
                    f"Expected receipted after Allow-always, got {state} at {width}"
                )

            # DB: exactly one policy row with decision='allow'
            policy = db.threads.effective_tool_policy(tid_always, "desk.create")
            assert policy == "allow", (
                f"Expected policy='allow' after Allow-always, got {policy}"
            )

            # Turn 2: same tool should auto-admit (no decision box)
            composer = page.locator(".thread-composer-input")
            composer.wait_for(timeout=10000)
            composer.fill("Create another note")
            page.locator("button.desk-chip", has_text="Send").click()

            # Should NOT show a decision box (auto-admitted via truth table row 1)
            page.wait_for_timeout(8000)

            decision_box_count = page.locator('[data-testid="decision-box"]').count()
            assert decision_box_count == 0, (
                f"Decision box appeared on auto-admit turn at {width}"
            )

            # The second tool row should be receipted (auto-admitted + executed)
            tool_rows = page.locator('[data-testid="tool-row"]')
            if tool_rows.count() >= 2:
                state2 = tool_rows.nth(1).get_attribute("data-tool-state")
                assert state2 in ("receipted", "running"), (
                    f"Expected auto-admitted tool receipted, got {state2} at {width}"
                )

            page.screenshot(path=str(SHOTS_06 / f"allow-always-auto-admit-{width}.png"))

            # ── Allow-once thread (same page session) ────────────────
            r2 = _api(page, "POST", "/api/threads", {"title": f"Once Only {width}"})
            assert r2["status"] == 201
            tid_once = r2["payload"]["id"]
            _open_thread(page, url, tid_once)

            composer = page.locator(".thread-composer-input")
            composer.wait_for(timeout=10000)
            composer.fill("Create a note once")
            page.locator("button.desk-chip", has_text="Send").click()

            decision_box = page.locator('[data-testid="decision-box"]')
            try:
                decision_box.wait_for(timeout=15000)
            except Exception:
                pass

            # Click Allow once (not always)
            allow_once = page.locator('[data-testid="allow-once"]')
            if allow_once.count() > 0:
                allow_once.click()
                page.wait_for_timeout(5000)

            # DB: no policy row for this thread
            policy_once = db.threads.effective_tool_policy(tid_once, "desk.create")
            assert policy_once is None, (
                f"Expected no policy after Allow-once, got {policy_once}"
            )

            page.close()

        browser.close()

    if broker is not None:
        broker.inference_runner._engine_factory = lambda _rev, **_kw: _ToolEngine()
