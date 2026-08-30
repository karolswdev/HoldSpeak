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
SHOTS = REPO / "pm/roadmap/holdspeak/phase-153-the-practice/assets/story-01-shots"

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


def _save_shot(page: Any, name: str, width: int) -> None:
    SHOTS.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(SHOTS / f"{name}-{width}.png"))


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
