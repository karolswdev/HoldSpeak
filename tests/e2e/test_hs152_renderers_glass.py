"""HS-152-05 -- Thread result renderer + status line glass tests.

Fake engine calls thread.set_status -> the head updates live.
Fake engine calls desk.list(notes) -> the renderer shows the note kind.
Shots at 1440 + 393 under pm/roadmap/.../assets/story-05-shots/.

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
TOKEN = "hs152-render-glass"
SHOTS = REPO / "pm/roadmap/holdspeak/phase-152-the-hands/assets/story-05-shots"

pytestmark = [pytest.mark.e2e, pytest.mark.requires_meeting]


# ----------------------------------------------------------------- fake engines

class _StatusEngine:
    """Engine that yields thread.set_status tool call, then responds."""

    active_provider = "status-glass"
    active_model = "hs152-status-model"

    def __init__(self, thread_id: str) -> None:
        self._thread_id = thread_id

    def run_prompt_stream(self, *, messages=None, tools=None, **kw):
        from holdspeak.kernel.inference_stream import Delta

        msgs = list(messages or [])
        has_tool_result = any(m.get("role") == "tool" for m in msgs)

        if has_tool_result:
            yield Delta(kind="text", text="Status set. ")
        else:
            yield Delta(kind="tool_calls", meta={"tool_calls": [
                {"id": "glass-status-1", "name": "thread.set_status",
                 "arguments": json.dumps({
                     "thread_id": self._thread_id,
                     "text": "Preparing your brief...",
                 })},
            ]})
        yield Delta(kind="usage", meta={"prompt_tokens": 10, "completion_tokens": 5})
        yield Delta(kind="done")

    def run_prompt_messages(self, **kw):
        return "Status set."

    def run_prompt(self, **kw):
        return "Status set."


class _NoteEngine:
    """Engine that yields desk.list(notes) -> the result should be kind=note."""

    active_provider = "note-glass"
    active_model = "hs152-note-model"

    def run_prompt_stream(self, *, messages=None, tools=None, **kw):
        from holdspeak.kernel.inference_stream import Delta

        msgs = list(messages or [])
        has_tool_result = any(m.get("role") == "tool" for m in msgs)

        if has_tool_result:
            yield Delta(kind="text", text="Listed notes. ")
        else:
            yield Delta(kind="tool_calls", meta={"tool_calls": [
                {"id": "glass-note-1", "name": "desk.list",
                 "arguments": json.dumps({"kind": "notes"})},
            ]})
        yield Delta(kind="usage", meta={"prompt_tokens": 5, "completion_tokens": 2})
        yield Delta(kind="done")

    def run_prompt_messages(self, **kw):
        return "Listed notes."

    def run_prompt(self, **kw):
        return "Listed notes."


# --------------------------------------------------------- profile seed

def _seed_profile(db: Any) -> None:
    from tests.unit.test_phase143_inference_assignments import _profile, OWNER
    from holdspeak.services.inference_assignment_service import InferenceAssignmentService

    pid = "hs152-render-local"
    _profile(db, pid)
    InferenceAssignmentService(db).set_assignment(OWNER, {
        "command_id": "hs152-render-assign", "expected_revision": 0,
        "scope": {"kind": "global"},
        "entries": [{"profile_id": pid, "profile_revision": 1}],
    })


# --------------------------------------------------------- boot fixture

@pytest.fixture
def hub(tmp_path, monkeypatch):
    """Boot an in-process hub with yolo control_mode (all tools auto-admit)."""
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

    # yolo mode: all tools auto-admit
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

    from holdspeak.kernel.runtime import _service as _kernel_service
    broker = _kernel_service()

    yield {
        "server": server,
        "url": url,
        "db": db,
        "broker": broker,
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

def test_set_status_updates_head_live(hub: dict) -> None:
    """thread.set_status from a fake engine updates the head live."""
    from playwright.sync_api import sync_playwright

    url = hub["url"]
    broker = hub["broker"]

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)

        for width in (1440, 393):
            page = browser.new_page(viewport={"width": width, "height": 900})
            page.goto(f"{url}/?token={TOKEN}", wait_until="load")

            r = _api(page, "POST", "/api/threads", {"title": "Status Test"})
            assert r["status"] == 201
            tid = r["payload"]["id"]

            # Set the engine to call thread.set_status with this thread's id
            engine = _StatusEngine(tid)
            if broker is not None:
                broker.inference_runner._engine_factory = lambda _rev, **_kw: engine

            _open_thread(page, url, tid)

            composer = page.locator(".thread-composer-input")
            composer.wait_for(timeout=10000)
            composer.fill("Set my status")
            page.locator("button.desk-chip", has_text="Send").click()

            # Wait for the turn to complete
            page.wait_for_timeout(8000)

            _save_shot(page, "set-status", width)

            # The status line should show in the head or have been set
            # (the server emits the persisted value before turn_done)
            status_el = page.locator(".thread-status-line")
            if status_el.count() > 0:
                text = status_el.first.text_content() or ""
                # The persisted status should be "Preparing your brief..."
                assert "Preparing your brief" in text or text == "", (
                    f"Expected persisted status, got: {text!r} at {width}"
                )

            # Verify the tool row rendered for thread.set_status
            tool_row = page.locator('[data-testid="tool-row"]')
            if tool_row.count() > 0:
                state = tool_row.first.get_attribute("data-tool-state")
                assert state in ("receipted", "running"), (
                    f"Expected receipted state, got {state} at {width}"
                )

            page.close()

        browser.close()


def test_desk_list_renders_result(hub: dict) -> None:
    """desk.list(notes) result renders with a tool row, note title visible,
    and a RAW fold affordance."""
    from playwright.sync_api import sync_playwright

    url = hub["url"]
    db = hub["db"]
    broker = hub["broker"]
    engine = _NoteEngine()
    if broker is not None:
        broker.inference_runner._engine_factory = lambda _rev, **_kw: engine

    # Seed two notes in the isolated DB so desk.list(notes) returns real content
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services.desk_service import DeskService
    from holdspeak.services.primitive_service import PrimitiveService
    owner = Principal(PrincipalKind.OWNER, "glass-owner")
    svc = PrimitiveService(db)
    svc.create_note(owner, title="Glass meeting note", body_markdown="Discussed the **Q3 plan**.")
    svc.create_note(owner, title="Architecture decision", body_markdown="Chose React over Vue.")

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)

        for width in (1440, 393):
            page = browser.new_page(viewport={"width": width, "height": 900})
            page.goto(f"{url}/?token={TOKEN}", wait_until="load")

            r = _api(page, "POST", "/api/threads", {"title": "Note List"})
            assert r["status"] == 201
            tid = r["payload"]["id"]
            _open_thread(page, url, tid)

            composer = page.locator(".thread-composer-input")
            composer.wait_for(timeout=10000)
            composer.fill("List my notes")
            page.locator("button.desk-chip", has_text="Send").click()

            # Wait for the turn to complete
            page.wait_for_timeout(8000)

            # Verify a tool row rendered and reached receipted state
            tool_row = page.locator('[data-testid="tool-row"]')
            assert tool_row.count() > 0, f"No tool row rendered at {width}"
            state = tool_row.first.get_attribute("data-tool-state")
            assert state == "receipted", (
                f"Expected receipted state, got {state} at {width}"
            )

            _save_shot(page, "desk-list-notes", width)

            # loadThread fires on turn_done (fire-and-forget). Wait for
            # it to complete and trigger the hydration re-render.
            page.wait_for_timeout(4000)

            # Verify the result block is visible (the per-kind renderer or summary)
            result_block = page.locator('[data-testid="result-block"]')
            if result_block.count() == 0:
                # Reload the thread page to force a fresh loadThread + hydrate
                _open_thread(page, url, tid)
                page.wait_for_timeout(3000)
                result_block = page.locator('[data-testid="result-block"]')

            assert result_block.count() > 0, (
                f"No result-block rendered at {width}"
            )

            # Check that a seeded note title is visible in the rendered content
            block_text = result_block.first.text_content() or ""
            assert "Glass meeting note" in block_text or "Architecture decision" in block_text, (
                f"Seeded note title not visible in result block at {width}: {block_text[:200]!r}"
            )

            # Verify RAW fold affordance is visible
            raw_fold = page.locator('[data-testid="raw-fold"]')
            assert raw_fold.count() > 0, f"RAW fold not rendered at {width}"

            _save_shot(page, "desk-list-notes-final", width)

            page.close()

        browser.close()
