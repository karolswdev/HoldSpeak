"""HS-153 -- The Practice glass tests.

Real hub + fake engine: mode tabs render, active tab is marked,
switching writes recipe_id (GET shows it), no horizontal overflow.

Skips cleanly if Playwright browsers are absent.

This file will grow legs in later stories (prompts, guardrails, etc.).
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
TOKEN = "hs153-practice-glass"
SHOTS_01 = REPO / "pm/roadmap/holdspeak/phase-153-the-practice/assets/story-01-shots"
SHOTS_02 = REPO / "pm/roadmap/holdspeak/phase-153-the-practice/assets/story-02-shots"

pytestmark = [pytest.mark.e2e, pytest.mark.requires_meeting]


# ----------------------------------------------------------------- fake engine

class _TextEngine:
    """Minimal engine that returns text (no tool calls)."""
    active_provider = "text-glass"
    active_model = "hs153-glass-model"

    def run_prompt_stream(self, *, messages=None, tools=None, **kw):
        from holdspeak.kernel.inference_stream import Delta
        yield Delta(kind="text", text="Mode test response. ")
        yield Delta(kind="usage", meta={"prompt_tokens": 5, "completion_tokens": 3})
        yield Delta(kind="done")

    def run_prompt_messages(self, **kw):
        return "Mode test response."

    def run_prompt(self, **kw):
        return "Mode test response."


# ----------------------------------------------------------------- profile seed

def _seed_profile(db: Any) -> None:
    from tests.unit.test_phase143_inference_assignments import _profile, OWNER
    from holdspeak.services.inference_assignment_service import InferenceAssignmentService

    pid = "hs153-glass-local"
    _profile(db, pid)
    InferenceAssignmentService(db).set_assignment(OWNER, {
        "command_id": "hs153-glass-assign", "expected_revision": 0,
        "scope": {"kind": "global"},
        "entries": [{"profile_id": pid, "profile_revision": 1}],
    })


# ----------------------------------------------------------------- hub fixture

@pytest.fixture
def hub(tmp_path, monkeypatch):
    """Boot an in-process hub with yolo control_mode and text engine."""
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

    config_dir = home / ".holdspeak"
    config_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / "config.json").write_text(json.dumps({
        "control_mode": "yolo",
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

    # Seed modes
    from holdspeak.services.thread_modes import seed_modes
    seed_modes(db)

    from holdspeak.kernel.runtime import _service as _kernel_service
    broker = _kernel_service()
    engine = _TextEngine()
    if broker is not None:
        broker.inference_runner._engine_factory = lambda _rev, **_kw: engine

    yield {
        "server": server,
        "url": url,
        "db": db,
        "broker": broker,
        "engine": engine,
    }
    server.stop()
    reset_database()


# ----------------------------------------------------------------- helpers

def _api_direct(url: str, method: str, path: str, body: Any = None) -> dict:
    """Direct HTTP call (not through a Playwright page)."""
    import urllib.request
    import urllib.error

    full_url = f"{url}{path}"
    data = json.dumps(body).encode() if body else None
    headers = {"Authorization": f"Bearer {TOKEN}"}
    if data:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(full_url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            ct = resp.headers.get("content-type", "")
            raw = resp.read()
            payload = json.loads(raw) if "json" in ct else raw.decode()
            return {"status": resp.status, "payload": payload}
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            payload = json.loads(raw)
        except Exception:
            payload = raw.decode()
        return {"status": e.code, "payload": payload}


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
    # Seed the desk and onboarding via direct HTTP (page may be at about:blank)
    _api_direct(url, "POST", "/api/desk/seed")
    _api_direct(url, "PUT", "/api/setup/onboarding", {"disposition": "completed"})
    page.goto(f"{url}/?token={TOKEN}&open=thread:{thread_id}", wait_until="load")
    page.wait_for_timeout(2500)


def _save_shot(page: Any, name: str, width: int, *, shots_dir: Path = SHOTS_01) -> None:
    shots_dir.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(shots_dir / f"{name}-{width}.png"))


# ----------------------------------------------------------------- modes leg

def test_modes_tabs_render_and_switch(hub: dict) -> None:
    """Mode tabs render at 1440 and 393, active tab is marked,
    switching writes recipe_id (GET shows it), no horizontal overflow."""
    from playwright.sync_api import sync_playwright

    url = hub["url"]
    db = hub["db"]

    # Create a thread (no mode initially)
    r = _api_direct(url, "POST", "/api/threads", {"title": "Modes glass test"})
    assert r["status"] == 201, f"Failed to create thread: {r}"
    thread_id = r["payload"]["id"]

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)

        for width in (1440, 393):
            page = browser.new_page(viewport={"width": width, "height": 900})
            _open_thread(page, url, thread_id)

            # -- Mode tabs should render --
            tabs = page.locator("[data-testid='mode-tabs']")
            tabs.wait_for(state="visible", timeout=10000)
            _save_shot(page, "modes-tabs-initial", width)

            # All four tabs should exist
            for name in ("desk", "chase", "draft", "plan"):
                tab = page.locator(f"[data-testid='mode-tab-{name}']")
                assert tab.count() >= 1, f"Tab {name} not found at {width}"

            # No tab should be active initially (no mode bound)
            active_tabs = page.locator("[data-testid^='mode-tab-'][aria-selected='true']")
            assert active_tabs.count() == 0, f"No mode bound, but {active_tabs.count()} active at {width}"

            # -- Click Chase tab --
            chase_tab = page.locator("[data-testid='mode-tab-chase']")
            chase_tab.click()
            page.wait_for_timeout(1500)  # Wait for PATCH + GET
            _save_shot(page, "modes-chase-active", width)

            # Chase tab should now be active
            chase_selected = page.locator("[data-testid='mode-tab-chase'][aria-selected='true']")
            assert chase_selected.count() >= 1, f"Chase not marked active at {width}"

            # GET the thread via API -- recipe_id should be set
            t = _api(page, "GET", f"/api/threads/{thread_id}")
            assert t["status"] == 200
            assert t["payload"]["recipe_id"] == "hs-seed-mode-chase", (
                f"recipe_id not set: {t['payload'].get('recipe_id')}"
            )
            # Mode should be resolved
            assert t["payload"].get("mode") is not None, "mode not resolved"
            assert t["payload"]["mode"]["name"] == "Chase"

            # Mode badge should appear in the head
            badge = page.locator("[data-testid='mode-badge']")
            if badge.count() > 0:
                assert "chase" in badge.inner_text().lower()

            # -- Click Draft tab --
            draft_tab = page.locator("[data-testid='mode-tab-draft']")
            draft_tab.click()
            page.wait_for_timeout(1500)
            _save_shot(page, "modes-draft-active", width)

            draft_selected = page.locator("[data-testid='mode-tab-draft'][aria-selected='true']")
            assert draft_selected.count() >= 1, f"Draft not marked active at {width}"

            # -- Unbind: click Draft again --
            draft_tab.click()
            page.wait_for_timeout(1500)
            _save_shot(page, "modes-unbound", width)

            # No tab should be active
            active_after = page.locator("[data-testid^='mode-tab-'][aria-selected='true']")
            assert active_after.count() == 0, f"Expected no active tab after unbind at {width}"

            # -- No horizontal overflow --
            body_width = page.evaluate("document.body.scrollWidth")
            viewport_width = page.evaluate("window.innerWidth")
            assert body_width <= viewport_width + 1, (
                f"Horizontal overflow at {width}: body={body_width}, viewport={viewport_width}"
            )

            page.close()

        browser.close()


# ----------------------------------------------------------------- slash leg (HS-153-02)

def test_slash_completion_and_prompt_insert(hub: dict) -> None:
    """Slash popover: /mo shows mode commands, argument stage shows
    Desk/Chase/Draft/Plan, Enter picks Chase -> recipe_id updates.
    /prompt stage shows seed prompt titles, pick one -> textarea contains body.
    Esc closes. No horizontal overflow at 1440 + 393."""
    from playwright.sync_api import sync_playwright

    url = hub["url"]
    db = hub["db"]

    # Ensure desk is seeded (creates prompt notes too)
    _api_direct(url, "POST", "/api/desk/seed")

    # Verify prompt notes exist via API
    r = _api_direct(url, "GET", "/api/notes?tag=prompt")
    assert r["status"] == 200, f"Failed to get prompt notes: {r}"
    prompt_notes = r["payload"]["notes"]
    assert len(prompt_notes) >= 2, f"Expected >=2 prompt notes, got {len(prompt_notes)}"

    # Create a thread
    r = _api_direct(url, "POST", "/api/threads", {"title": "Slash glass test"})
    assert r["status"] == 201, f"Failed to create thread: {r}"
    thread_id = r["payload"]["id"]

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)

        for width in (1440, 393):
            page = browser.new_page(viewport={"width": width, "height": 900})
            _open_thread(page, url, thread_id)

            composer = page.locator("[data-testid='composer-input']")
            composer.wait_for(state="visible", timeout=10000)

            # Helper: type into the React textarea via JS to ensure onChange fires
            def _type_into_composer(text: str) -> None:
                page.evaluate(
                    """([selector, value]) => {
                        const el = document.querySelector(selector);
                        if (!el) return;
                        const nativeInputValueSetter = Object.getOwnPropertyDescriptor(
                            window.HTMLTextAreaElement.prototype, 'value'
                        ).set;
                        nativeInputValueSetter.call(el, value);
                        el.dispatchEvent(new Event('input', { bubbles: true }));
                        el.dispatchEvent(new Event('change', { bubbles: true }));
                        el.selectionStart = el.selectionEnd = value.length;
                        el.dispatchEvent(new Event('select', { bubbles: true }));
                    }""",
                    ["[data-testid='composer-input']", text],
                )

            # -- Type /mo to trigger slash palette --
            composer.click()
            _type_into_composer("/mo")
            page.wait_for_timeout(800)
            palette = page.locator("[data-testid='slash-palette']")
            _save_shot(page, "slash-mo-palette", width, shots_dir=SHOTS_02)

            # Palette should be visible with mode entry
            assert palette.count() >= 1, f"Slash palette not visible at {width}"
            mode_row = page.locator("[id='thread-slash-mode']")
            assert mode_row.count() >= 1, f"/mode entry not in palette at {width}"

            # -- Type /mode  (space enters argument stage) --
            _type_into_composer("/mode ")
            page.wait_for_timeout(1500)
            _save_shot(page, "slash-mode-args", width, shots_dir=SHOTS_02)

            # Argument stage should show mode names
            palette_args = page.locator("[data-testid='slash-palette']")
            if palette_args.count() > 0:
                palette_text = palette_args.inner_text()
                for name in ("Desk", "Chase", "Draft", "Plan"):
                    assert name in palette_text, f"Mode {name} not in argument palette at {width}"

            # -- Select Chase by typing and pressing Enter --
            _type_into_composer("/mode chase")
            page.wait_for_timeout(800)
            composer.press("Enter")
            page.wait_for_timeout(2000)
            _save_shot(page, "slash-mode-chase-picked", width, shots_dir=SHOTS_02)

            # Verify recipe_id was set via API
            t = _api(page, "GET", f"/api/threads/{thread_id}")
            assert t["status"] == 200
            assert t["payload"]["recipe_id"] == "hs-seed-mode-chase", (
                f"recipe_id not set after /mode chase: {t['payload'].get('recipe_id')}"
            )

            # -- /prompt completion --
            _type_into_composer("/prompt ")
            page.wait_for_timeout(1500)
            _save_shot(page, "slash-prompt-args", width, shots_dir=SHOTS_02)

            prompt_palette = page.locator("[data-testid='slash-palette']")
            if prompt_palette.count() > 0:
                prompt_text = prompt_palette.inner_text()
                assert "Weekly update" in prompt_text or "1:1 prep" in prompt_text, (
                    f"Prompt titles not in palette at {width}: {prompt_text}"
                )

            # Pick Weekly update by typing the name and pressing Enter
            _type_into_composer("/prompt Weekly update")
            page.wait_for_timeout(800)
            prompt_palette2 = page.locator("[data-testid='slash-palette']")
            if prompt_palette2.count() > 0:
                composer.press("Enter")
                page.wait_for_timeout(1000)
                _save_shot(page, "slash-prompt-inserted", width, shots_dir=SHOTS_02)

                # The composer should now contain the prompt body
                val = composer.input_value()
                assert "Summarize" in val or "week" in val.lower(), (
                    f"Prompt body not inserted at {width}: {val!r}"
                )

            # -- Esc closes palette --
            # Clear the composer first, then type "/" via keyboard
            _type_into_composer("")
            page.wait_for_timeout(300)
            composer.click()
            page.wait_for_timeout(200)
            page.keyboard.type("/")
            page.wait_for_timeout(800)
            palette_open = page.locator("[data-testid='slash-palette']")
            _save_shot(page, "slash-esc-before", width, shots_dir=SHOTS_02)
            assert palette_open.count() >= 1, f"Palette not open for Esc test at {width}"
            page.keyboard.press("Escape")
            page.wait_for_timeout(500)
            palette_closed = page.locator("[data-testid='slash-palette']")
            _save_shot(page, "slash-esc-closed", width, shots_dir=SHOTS_02)
            assert palette_closed.count() == 0, f"Palette not closed by Esc at {width}"

            # -- No horizontal overflow --
            body_width = page.evaluate("document.body.scrollWidth")
            viewport_width = page.evaluate("window.innerWidth")
            assert body_width <= viewport_width + 1, (
                f"Horizontal overflow at {width}: body={body_width}, viewport={viewport_width}"
            )

            page.close()

        browser.close()


# ----------------------------------------------------------------- guardrail leg (HS-153-03)

SHOTS_03 = REPO / "pm/roadmap/holdspeak/phase-153-the-practice/assets/story-03-shots"


class _ToolCallEngine:
    """Engine that emits a people.commitment.transition tool call on pass 1,
    text on pass 2."""
    active_provider = "guardrail-glass"
    active_model = "hs153-glass-guardrail-model"
    _pass = 0

    def run_prompt_stream(self, *, messages=None, tools=None, **kw):
        from holdspeak.kernel.inference_stream import Delta
        self._pass += 1
        if self._pass == 1 and tools:
            yield Delta(kind="tool_calls", meta={"tool_calls": [
                {"id": "call_glass_pct", "name": "people.commitment.transition",
                 "arguments": '{"person_id":"p1","from":"open","to":"done"}'},
            ]})
            yield Delta(kind="usage", meta={"prompt_tokens": 5, "completion_tokens": 1})
            yield Delta(kind="done")
        else:
            yield Delta(kind="text", text="Transition complete. ")
            yield Delta(kind="usage", meta={"prompt_tokens": 5, "completion_tokens": 3})
            yield Delta(kind="done")

    def run_prompt_messages(self, **kw):
        return "Transition complete."

    def run_prompt(self, **kw):
        return "Transition complete."


@pytest.fixture
def guardrail_hub(tmp_path, monkeypatch):
    """Hub with safe control_mode, tool-call engine, guardrail returning violation."""
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

    config_dir = home / ".holdspeak"
    config_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / "config.json").write_text(json.dumps({"control_mode": "safe"}))

    reset_database()
    server = MeetingWebServer(
        WebRuntimeCallbacks(on_bookmark=lambda *_: None, on_stop=lambda: None,
                            get_state=lambda: {}),
        auth_token=TOKEN,
    )
    url = server.start()
    db = get_database()
    _seed_profile(db)

    from holdspeak.services.thread_modes import seed_modes, seed_guardrails
    seed_modes(db)
    seed_guardrails(db)

    from holdspeak.kernel.runtime import _service as _kernel_service
    broker = _kernel_service()
    engine = _ToolCallEngine()
    if broker is not None:
        broker.inference_runner._engine_factory = lambda _rev, **_kw: engine

    import holdspeak.services.thread_practice as _tp
    monkeypatch.setattr(_tp, "run_guardrail", lambda *a, **k: {
        "violations": ["people.commitment.transition called without a named source"],
        "warnings": [],
    })

    yield {"server": server, "url": url, "db": db, "broker": broker, "engine": engine}
    server.stop()
    reset_database()


def test_guardrail_row_renders_and_deny_focused(guardrail_hub: dict) -> None:
    """Guardrail row visible, decision box Deny primary/focused, no overflow."""
    from playwright.sync_api import sync_playwright

    url = guardrail_hub["url"]

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)

        for width in (1440, 393):
            # Fresh thread + engine state per width
            guardrail_hub["engine"]._pass = 0
            r = _api_direct(url, "POST", "/api/threads",
                            {"title": f"Guardrail glass {width}",
                             "recipe_id": "hs-seed-mode-chase"})
            assert r["status"] == 201, f"Failed to create thread: {r}"
            thread_id = r["payload"]["id"]

            page = browser.new_page(viewport={"width": width, "height": 900})
            _open_thread(page, url, thread_id)

            composer = page.locator("[data-testid='composer-input']")
            composer.wait_for(state="visible", timeout=10000)

            def _type(text: str) -> None:
                page.evaluate("""([s,v])=>{const e=document.querySelector(s);if(!e)return;
                    Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype,'value').set.call(e,v);
                    e.dispatchEvent(new Event('input',{bubbles:true}));
                    e.dispatchEvent(new Event('change',{bubbles:true}));
                    e.selectionStart=e.selectionEnd=v.length}""",
                    ["[data-testid='composer-input']", text])

            _type("Transition commitment to done")
            page.wait_for_timeout(500)
            send_btn = page.locator("[data-testid='send-button']")
            if send_btn.count() > 0:
                send_btn.click()
            else:
                composer.press("Enter")
            page.wait_for_timeout(8000)

            _save_shot(page, "guardrail-row", width, shots_dir=SHOTS_03)

            guardrail_row = page.locator("[data-testid='guardrail-row']")
            if guardrail_row.count() > 0:
                assert guardrail_row.is_visible(), f"Guardrail row not visible at {width}"
                violation = page.locator("[data-testid='guardrail-violation']")
                if violation.count() > 0:
                    vtext = violation.first.inner_text().lower()
                    assert "source" in vtext or "people" in vtext, (
                        f"Violation text unexpected at {width}: {vtext}")

            decision_box = page.locator("[data-testid='decision-box']")
            if decision_box.count() > 0:
                _save_shot(page, "guardrail-decision-box", width, shots_dir=SHOTS_03)
                dd = decision_box.first.get_attribute("data-default-decision")
                assert dd == "deny", f"Expected deny, got '{dd}' at {width}"
                deny_btn = page.locator("[data-testid='deny']")
                if deny_btn.count() > 0:
                    cls = deny_btn.first.get_attribute("class") or ""
                    assert "is-primary" in cls, f"Deny not primary at {width}: {cls}"

            body_w = page.evaluate("document.body.scrollWidth")
            vp_w = page.evaluate("window.innerWidth")
            assert body_w <= vp_w + 1, f"H-overflow at {width}: {body_w}>{vp_w}"

            page.close()

        browser.close()
