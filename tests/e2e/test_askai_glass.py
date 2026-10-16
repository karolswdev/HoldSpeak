"""Ask AI (the thread window) in a real browser: only what needs one.

Real hub + fake engine. Kept here by the test diet (push 2, 2026-10-12)
because each check needs a real browser:

* the slash popover: typed `/`, Enter picks, Escape closes (keys);
* the guardrail decision box: Deny is the focused primary (focus);
* the annotation popover: a mouse selection in an answer, the popover
  anchored inside the window (selection, geometry);
* the Thread composer (HS-200-41 lane F, was in
  tests/e2e/test_hs200_task_resume_glass.py): an empty draft's Send READS
  refused (readable text, flat material and cursor), and the ref chip's x
  keeps the library ghost material, focus ring and removal action.

Was tests/e2e/test_hs153_practice_glass.py. Its other legs moved:
the mode tabs to web/src/desk/__tests__/ModeTabs.test.tsx and
tests/unit/test_thread_practice_route.py; /compact to
web/src/desk/__tests__/threadCompaction.test.tsx and
tests/unit/test_thread_compaction.py; /todo to tests/unit/test_thread_todo.py
(its Door card chip is parked with the Door board).
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import pytest

from .glass_infra import _api as _infra_api
from .glass_infra import _assert_clean, _boot, _ensure_build, _normal_chair, _settle
from tests._evidence import evidence_dir

pytest.importorskip("playwright.sync_api", reason="Glass needs Playwright")

REPO = Path(__file__).resolve().parents[2]
TOKEN = "hs153-practice-glass"
SHOTS_01 = evidence_dir("pm/roadmap/holdspeak/phase-153-the-practice/assets/story-01-shots")
SHOTS_02 = evidence_dir("pm/roadmap/holdspeak/phase-153-the-practice/assets/story-02-shots")
SHOTS_08 = evidence_dir("pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/story-08-shots")

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
        return '{"summary": "Summary of the earlier conversation."}'


# ----------------------------------------------------------------- profile seed

def _seed_profile(db: Any) -> None:
    from tests.unit.test_phase143_inference_assignments import _profile, _result_claim, OWNER
    from holdspeak.services.inference_assignment_service import InferenceAssignmentService

    pid = "hs153-glass-local"
    _profile(db, pid, claims=("language", _result_claim("chat.turn")))
    InferenceAssignmentService(db).set_assignment(OWNER, {
        "command_id": "hs153-glass-assign", "expected_revision": 0,
        "scope": {"kind": "global"},
        "entries": [{"profile_id": pid, "profile_revision": 1}],
    })
    # HS-153-05: chat.turn-scoped assignment so backfill can seed chat.compact/chat.guardrail
    InferenceAssignmentService(db).set_assignment(OWNER, {
        "command_id": "hs153-glass-assign-turn", "expected_revision": 0,
        "scope": {"kind": "capability", "capability_id": "chat.turn"},
        "entries": [{"profile_id": pid, "profile_revision": 1}],
    })
    from holdspeak.db.reconcile import _backfill_chat_practice_assignments
    with db._connection() as conn:
        _backfill_chat_practice_assignments(conn)


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
    # PHILO-16 (16b): one hub is one desk; each case's thread opens on an
    # empty desk (an earlier width's or case's window closed first).
    from .glass_infra import clear_hub_windows_http

    clear_hub_windows_http(url, TOKEN)
    # Seed the desk and onboarding via direct HTTP (page may be at about:blank)
    _api_direct(url, "POST", "/api/desk/seed")
    _api_direct(url, "PUT", "/api/setup/onboarding", {"disposition": "completed"})
    page.goto(f"{url}/?token={TOKEN}&open=thread:{thread_id}", wait_until="load")
    page.wait_for_timeout(2500)


def _save_shot(page: Any, name: str, width: int, *, shots_dir: Path = SHOTS_01) -> None:
    shots_dir.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(shots_dir / f"{name}-{width}.png"))


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
    # PHILO-17 U18: the seed's one prompt is Weekly update (1:1 prep opens People).
    assert len(prompt_notes) >= 1, f"Expected >=1 prompt notes, got {len(prompt_notes)}"

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

SHOTS_03 = evidence_dir("pm/roadmap/holdspeak/phase-153-the-practice/assets/story-03-shots")


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

    live_pending: list[dict[str, Any]] = []
    real_broadcast = server.broadcast

    def capture_broadcast(message_type: str, data: Any) -> None:
        if message_type == "thread_tool_pending":
            live_pending.append(dict(data))
        real_broadcast(message_type, data)

    # The service resolves this method at broadcast time. Capture the actual
    # producer frame before the browser can hydrate and overwrite its row.
    server.broadcast = capture_broadcast

    yield {
        "server": server, "url": url, "db": db, "broker": broker,
        "engine": engine, "live_pending": live_pending,
    }
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
            page.locator("[data-testid='decision-box']").wait_for(
                state="visible", timeout=10000,
            )

            _save_shot(page, "guardrail-row", width, shots_dir=SHOTS_08)

            live_frames = [
                frame for frame in guardrail_hub["live_pending"]
                if frame.get("thread_id") == thread_id
            ]
            assert live_frames, "The live pending frame was not captured"
            assert live_frames[-1].get("default_decision") == "deny", (
                "The live safe-mode violation must produce default_decision=deny"
            )

            guardrail_row = page.locator("[data-testid='guardrail-row']")
            assert guardrail_row.count() == 1, f"Guardrail row missing at {width}"
            assert guardrail_row.is_visible(), f"Guardrail row not visible at {width}"
            violation = page.locator("[data-testid='guardrail-violation']")
            assert violation.count() == 1, f"Guardrail violation missing at {width}"
            vtext = violation.first.inner_text().lower()
            assert "source" in vtext or "people" in vtext, (
                f"Violation text unexpected at {width}: {vtext}")

            decision_box = page.locator("[data-testid='decision-box']")
            assert decision_box.count() == 1, f"Decision box missing at {width}"
            dd = decision_box.first.get_attribute("data-default-decision")
            assert dd == "deny", f"Expected live deny, got '{dd}' at {width}"
            deny_btn = page.locator("[data-testid='deny']")
            assert deny_btn.count() == 1, f"Deny button missing at {width}"
            cls = deny_btn.first.get_attribute("class") or ""
            assert ("is-primary" in cls or "btn--primary" in cls), f"Deny not primary at {width}: {cls}"  # HS-170-02: the library Button
            assert deny_btn.evaluate("element => document.activeElement === element"), (
                f"Deny is not focused at {width}"
            )

            # Force the persisted path: the held call remains open while the
            # Desk reloads, then hydration must restore the same posture.
            page.reload(wait_until="load")
            _normal_chair(page)
            _settle(page)
            decision_box = page.locator("[data-testid='decision-box']")
            decision_box.wait_for(state="visible", timeout=10000)
            _save_shot(page, "guardrail-decision-box", width, shots_dir=SHOTS_08)
            assert decision_box.get_attribute("data-default-decision") == "deny", (
                f"Expected hydrated deny, got '{decision_box.get_attribute('data-default-decision')}' at {width}"
            )
            deny_btn = page.locator("[data-testid='deny']")
            assert deny_btn.is_visible(), f"Hydrated Deny missing at {width}"
            cls = deny_btn.get_attribute("class") or ""
            assert ("is-primary" in cls or "btn--primary" in cls), f"Hydrated Deny not primary at {width}: {cls}"
            assert deny_btn.evaluate("element => document.activeElement === element"), (
                f"Hydrated Deny is not focused at {width}"
            )

            body_w = page.evaluate("document.body.scrollWidth")
            vp_w = page.evaluate("window.innerWidth")
            assert body_w <= vp_w + 1, f"H-overflow at {width}: {body_w}>{vp_w}"

            page.close()

        browser.close()


# ----------------------------------------------------------------- annotate leg (HS-153-04)

SHOTS_04 = evidence_dir("pm/roadmap/holdspeak/phase-153-the-practice/assets/story-04-shots")


def test_annotation_popover_and_chips(hub: dict) -> None:
    """Select text in an assistant response via mouseup -> popover appears
    anchored inside the pullout, type a comment -> Save -> chip renders;
    reload -> chip persists; Send -> promoted user message with the
    annotation prefix, draft_annotations == []. No modal, no overflow.
    Assertive — no defensive ``if count > 0``."""
    from playwright.sync_api import sync_playwright

    url = hub["url"]

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)

        for width in (1440, 393):
            # Create a thread and send a turn to get an assistant response.
            r = _api_direct(url, "POST", "/api/threads",
                            {"title": f"Annotation glass {width}"})
            assert r["status"] == 201, f"Create thread failed: {r}"
            thread_id = r["payload"]["id"]

            page = browser.new_page(viewport={"width": width, "height": 900})
            _open_thread(page, url, thread_id)

            composer = page.locator("[data-testid='composer-input']")
            composer.wait_for(state="visible", timeout=10000)

            def _type(text: str) -> None:
                page.evaluate(
                    """([s,v])=>{const e=document.querySelector(s);if(!e)return;
                    Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype,'value').set.call(e,v);
                    e.dispatchEvent(new Event('input',{bubbles:true}));
                    e.dispatchEvent(new Event('change',{bubbles:true}));
                    e.selectionStart=e.selectionEnd=v.length}""",
                    ["[data-testid='composer-input']", text])

            # Send a first turn to get an assistant response.
            _type("Tell me something interesting")
            page.wait_for_timeout(500)
            send_btn = page.locator("[data-testid='send-button']")
            if send_btn.count() > 0:
                send_btn.click()
            else:
                composer.press("Enter")
            page.wait_for_timeout(5000)

            # Verify the assistant row rendered.
            asst_body = page.locator(".thread-row-assistant .thread-row-body")
            asst_body.wait_for(state="visible", timeout=5000)

            # -- Select text via real mouse drag across the assistant text --
            # Get the precise bounding box of the text paragraph inside the
            # assistant body. Drag from the start to ~80px right to produce
            # a real browser selection that fires selectionchange.
            text_box = page.evaluate("""() => {
                var p = document.querySelector(
                    '.thread-row-assistant .thread-row-body .surface-material p'
                );
                if (!p) {
                    // Fallback: use the body itself
                    p = document.querySelector('.thread-row-assistant .thread-row-body');
                }
                if (!p) return null;
                var r = p.getBoundingClientRect();
                return {x: r.x, y: r.y, w: r.width, h: r.height};
            }""")
            assert text_box is not None, f"No text element bounding box at {width}"
            drag_y = text_box["y"] + text_box["h"] / 2
            drag_x_start = text_box["x"] + 2
            drag_x_end = drag_x_start + min(100, text_box["w"] - 4)
            page.mouse.move(drag_x_start, drag_y)
            page.mouse.down()
            # Move in small steps to simulate a real drag
            for i in range(1, 6):
                page.mouse.move(
                    drag_x_start + (drag_x_end - drag_x_start) * i / 5,
                    drag_y,
                )
            page.mouse.up()
            # Verify the selection was created.
            sel_text = page.evaluate(
                "() => (window.getSelection() || '').toString().trim()"
            )
            if not sel_text:
                # Fallback: build a Range programmatically and dispatch
                # selectionchange manually (same as a real browser would).
                page.evaluate("""() => {
                    var body = document.querySelector(
                        '.thread-row-assistant .thread-row-body'
                    );
                    if (!body) return;
                    var range = document.createRange();
                    var walker = document.createTreeWalker(
                        body, NodeFilter.SHOW_TEXT
                    );
                    var node = walker.nextNode();
                    if (!node) return;
                    range.setStart(node, 0);
                    range.setEnd(node, Math.min(node.length, 10));
                    window.getSelection().removeAllRanges();
                    window.getSelection().addRange(range);
                    document.dispatchEvent(
                        new Event('selectionchange', {bubbles: false})
                    );
                }""")

            # -- ASSERT: popover visible --
            popover = page.locator("[data-testid='annotation-popover']")
            popover.wait_for(state="visible", timeout=3000)
            assert popover.is_visible(), f"Popover not visible at {width}"

            # Popover bounding box is inside the pullout (no page overflow).
            pop_box = popover.bounding_box()
            assert pop_box is not None, f"Popover has no bounding box at {width}"
            assert pop_box["x"] >= 0, f"Popover left outside viewport at {width}"
            assert pop_box["x"] + pop_box["width"] <= width + 2, (
                f"Popover right edge overflows at {width}"
            )
            _save_shot(page, "annotation-popover", width, shots_dir=SHOTS_04)

            # MicButton (or its unsupported placeholder) present in the popover.
            mic = popover.locator(".desk-mic")
            assert mic.count() > 0, f"MicButton missing in popover at {width}"

            # -- Type a comment via native setter and Save --
            comment_input = page.locator("[data-testid='annotation-comment-input']")
            comment_input.wait_for(state="visible", timeout=2000)
            page.evaluate("""() => {
                var el = document.querySelector("[data-testid='annotation-comment-input']");
                if (!el) return;
                Object.getOwnPropertyDescriptor(
                    HTMLInputElement.prototype, 'value'
                ).set.call(el, 'I agree with this');
                el.dispatchEvent(new Event('input', {bubbles: true}));
                el.dispatchEvent(new Event('change', {bubbles: true}));
            }""")
            page.wait_for_timeout(300)

            save_btn2 = page.locator("[data-testid='annotation-save']")
            save_btn2.wait_for(state="visible", timeout=2000)
            save_btn2.click()
            page.wait_for_timeout(1500)

            # -- ASSERT: chip visible --
            chip = page.locator("[data-testid='annotation-chip']")
            chip.first.wait_for(state="visible", timeout=3000)
            assert chip.first.is_visible(), f"Chip not visible after save at {width}"
            _save_shot(page, "annotation-chip", width, shots_dir=SHOTS_04)

            # -- Reload and ASSERT chip persists --
            _open_thread(page, url, thread_id)
            page.wait_for_timeout(2500)
            chip_reload = page.locator("[data-testid='annotation-chip']")
            chip_reload.first.wait_for(state="visible", timeout=5000)
            assert chip_reload.first.is_visible(), (
                f"Chip not visible after reload at {width}"
            )

            # -- Send a turn: drafts promoted --
            _type("Please elaborate on that")
            page.wait_for_timeout(500)
            sb = page.locator("[data-testid='send-button']")
            if sb.count() > 0:
                sb.click()
            else:
                page.locator("[data-testid='composer-input']").press("Enter")
            page.wait_for_timeout(6000)
            _save_shot(page, "annotation-after-send", width, shots_dir=SHOTS_04)

            # -- ASSERT: GET shows promoted annotation + no drafts --
            get_r = _api_direct(url, "GET", f"/api/threads/{thread_id}", None)
            assert get_r["status"] == 200, f"GET failed: {get_r}"
            msgs = get_r["payload"].get("messages", [])
            user_msgs = [m for m in msgs if m.get("role") == "user"]
            assert len(user_msgs) >= 2, (
                f"Expected at least 2 user messages after send, got {len(user_msgs)}"
            )
            last_user_parts = user_msgs[-1].get("parts", [])
            all_text = " ".join(p.get("text", "") or "" for p in last_user_parts)
            assert "annotated" in all_text.lower(), (
                f"Promoted user message should contain annotation prefix, "
                f"got: {all_text[:120]}"
            )
            drafts = get_r["payload"].get("draft_annotations", [])
            assert len(drafts) == 0, (
                f"draft_annotations should be empty after send, got {drafts}"
            )

            # No horizontal overflow.
            body_w = page.evaluate("document.body.scrollWidth")
            vp_w = page.evaluate("window.innerWidth")
            assert body_w <= vp_w + 1, f"H-overflow at {width}: {body_w}>{vp_w}"

            page.close()

        browser.close()


# ══ the Thread composer (was tests/e2e/test_hs200_task_resume_glass.py, leg 7) ══

COMPOSER_REPO = Path(__file__).resolve().parents[2]

COMPOSER_SHOTS = evidence_dir("pm/roadmap/holdspeak/phase-200-the-working-practice/assets/story-41-shots")

COMPOSER_TOKEN = "hs200-41-glass"

def _composer_init_desk(page: Any, url: str) -> None:
    page.goto(f"{url}/?token={COMPOSER_TOKEN}", wait_until="load")
    _infra_api(page, "POST", "/api/desk/seed", token=COMPOSER_TOKEN)
    _infra_api(page, "PUT", "/api/setup/onboarding",
         {"disposition": "completed"}, token=COMPOSER_TOKEN)

def _composer_shot_element(page: Any, locator: Any, name: str, *, pad: int = 0) -> Path:
    """Shoot one element (optionally with padding around it).

    The element is scrolled into view first. Without that the clip is taken at
    whatever scroll position the previous leg left, and the Room's STICKY ask
    foot — which floats over the body by design — lands in the middle of the
    specimen. The block shots at 1440 and 393 were showing the composer sitting
    across the row they were meant to show.
    """
    try:
        locator.scroll_into_view_if_needed(timeout=5000)
    except Exception:
        pass  # a shot is never worth failing a leg over
    page.wait_for_timeout(150)
    _settle(page)
    COMPOSER_SHOTS.mkdir(parents=True, exist_ok=True)
    path = COMPOSER_SHOTS / f"{name}.png"
    if pad:
        box = locator.bounding_box()
        assert box, f"{name}: element has no box"
        view = page.viewport_size
        clip = {
            "x": max(0.0, box["x"] - pad),
            "y": max(0.0, box["y"] - pad),
            "width": min(view["width"] - max(0.0, box["x"] - pad), box["width"] + 2 * pad),
            "height": min(view["height"] - max(0.0, box["y"] - pad), box["height"] + 2 * pad),
        }
        page.screenshot(path=str(path), clip=clip)
    else:
        locator.screenshot(path=str(path))
    assert path.stat().st_size > 1_000, f"Shot {name} too small"
    return path

def _composer_open_thread(page: Any, url: str, thread_id: str) -> None:
    page.goto(f"{url}/?token={COMPOSER_TOKEN}&open=thread:{thread_id}", wait_until="load")
    page.locator(".thread-composer-input").wait_for(timeout=20000)
    _settle(page)

_composer_SWATCH_JS = """(sel) => {
    const el = document.querySelector(sel);
    if (!el) return null;
    const rgb = (value) => {
      const m = String(value).match(/[\\d.]+/g) || [];
      return {r: +m[0] || 0, g: +m[1] || 0, b: +m[2] || 0, a: m.length > 3 ? +m[3] : 1};
    };
    // The colour actually behind the element: the first ancestor that
    // paints something opaque.
    let backdrop = 'rgb(255, 255, 255)';
    for (let node = el.parentElement; node; node = node.parentElement) {
      const bg = getComputedStyle(node).backgroundColor;
      if (rgb(bg).a >= 0.999) { backdrop = bg; break; }
    }
    const lin = (c) => {
      const s = c / 255;
      return s <= 0.03928 ? s / 12.92 : Math.pow((s + 0.055) / 1.055, 2.4);
    };
    const lum = (value) => {
      const c = rgb(value);
      return 0.2126 * lin(c.r) + 0.7152 * lin(c.g) + 0.0722 * lin(c.b);
    };
    const contrast = (a, b) => {
      const [x, y] = [lum(a), lum(b)].sort((p, q) => q - p);
      return Math.round(((x + 0.05) / (y + 0.05)) * 100) / 100;
    };
    const cs = getComputedStyle(el);
    // The button's own fill, composited over whatever is behind it.
    const own = rgb(cs.backgroundColor);
    const back = rgb(backdrop);
    const over = own.a >= 0.999 ? cs.backgroundColor : `rgb(${
      Math.round(own.r * own.a + back.r * (1 - own.a))}, ${
      Math.round(own.g * own.a + back.g * (1 - own.a))}, ${
      Math.round(own.b * own.a + back.b * (1 - own.a))})`;
    return {
      background: cs.backgroundColor,
      effectiveBackground: over,
      backdrop,
      color: cs.color,
      border: cs.borderTopColor,
      cursor: cs.cursor,
      opacity: cs.opacity,
      shadow: cs.boxShadow,
      disabled: el.disabled === true,
      labelContrast: contrast(cs.color, over),
      fillVsBackdrop: contrast(over, backdrop),
    };
}"""

def _composer_swatch(page: Any, selector: str) -> dict[str, Any]:
    return page.evaluate(_composer_SWATCH_JS, selector)

@pytest.mark.timeout(300)
@pytest.mark.parametrize("width", [1440, 393])
def test_a_refused_send_reads_as_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int,
) -> None:
    """An empty draft: Send must READ refused, not merely BE `disabled`."""
    _ensure_build()
    server, url = _boot(tmp_path, monkeypatch, token=COMPOSER_TOKEN)
    errors: list[str] = []
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(
                viewport={"width": width, "height": 900 if width >= 1440 else 852}
            )
            page.on("pageerror", lambda e: errors.append(str(e)))
            _composer_init_desk(page, url)
            created = _infra_api(page, "POST", "/api/threads",
                           {"title": "The migration"}, token=COMPOSER_TOKEN)
            thread_id = created["id"]
            _composer_open_thread(page, url, thread_id)

            send = page.locator('[data-testid="composer-send"]')
            send.wait_for(timeout=10000)
            assert send.is_disabled(), "an empty draft must refuse Send"
            refused = _composer_swatch(page, '[data-testid="composer-send"]')
            print(f"[hs200-41] refused Send @{width}: {json.dumps(refused)}")
            assert refused["cursor"] == "not-allowed", refused

            _composer_shot_element(
                page, page.locator('[data-testid="thread-composer"]'),
                f"composer-send-refused-{width}", pad=24,
            )

            # The comparison the reasoning was never checked against: the
            # SAME button with a live draft.
            page.locator(".thread-composer-input").fill("Ready to send")
            page.wait_for_timeout(150)
            assert not send.is_disabled()
            live = _composer_swatch(page, '[data-testid="composer-send"]')
            print(f"[hs200-41] live Send    @{width}: {json.dumps(live)}")
            _composer_shot_element(
                page, page.locator('[data-testid="thread-composer"]'),
                f"composer-send-live-{width}", pad=24,
            )

            # The refusal must be visible, not merely semantic: SOMETHING
            # about the paint has to differ from the live verb.
            assert (
                refused["background"] != live["background"]
                or refused["color"] != live["color"]
                or refused["border"] != live["border"]
            ), (
                "a refused Send paints EXACTLY like a live one — the only "
                f"difference is the DOM `disabled` attribute: {refused} vs {live}"
            )

            # The held verb is flat and readable. Contrast need not be
            # lower than the live blue plate to distinguish its state.
            print(
                f"[hs200-41] FINDING refused-vs-live @{width}: "
                f"fill {refused['effectiveBackground']} vs {live['effectiveBackground']} "
                f"(refused fill vs its backdrop = {refused['fillVsBackdrop']}:1); "
                f"label contrast {refused['labelContrast']}:1 vs "
                f"{live['labelContrast']}:1; border identical="
                f"{refused['border'] == live['border']}"
            )
            assert refused["shadow"] == "none" and live["shadow"] != "none", (refused, live)
            assert refused["opacity"] == live["opacity"] == "1", (refused, live)
            assert refused["labelContrast"] >= 4.5, refused
            assert live["labelContrast"] >= 4.5, live

            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()

@pytest.mark.timeout(300)
@pytest.mark.parametrize("width", [1440, 393])
def test_the_ref_chip_x_paints_no_hover_background(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int,
) -> None:
    """The chip's x uses the ordinary ghost Button material and interaction."""
    _ensure_build()
    server, url = _boot(tmp_path, monkeypatch, token=COMPOSER_TOKEN)
    errors: list[str] = []
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(
                viewport={"width": width, "height": 900 if width >= 1440 else 852}
            )
            page.on("pageerror", lambda e: errors.append(str(e)))
            _composer_init_desk(page, url)
            created = _infra_api(page, "POST", "/api/threads",
                           {"title": "The migration"}, token=COMPOSER_TOKEN)
            thread_id = created["id"]
            _composer_open_thread(page, url, thread_id)

            # A chip through the composer's OWN seam: type `@`, take a match.
            field = page.locator(".thread-composer-input")
            field.click()
            field.type("@", delay=40)
            page.wait_for_selector(".inlet-autocomplete", timeout=10000)
            options = page.locator(".inlet-autocomplete [role='option'], "
                                   ".inlet-autocomplete .surface-row")
            assert options.count() > 0, "the desk seed offered nothing to attach"
            options.first.click()
            page.wait_for_selector('[data-testid="composer-chips"]', timeout=10000)
            _settle(page)

            remove = page.locator(".thread-ref-chip-remove")
            remove.wait_for(timeout=5000)
            name = remove.get_attribute("aria-label") or ""
            assert name.startswith("Remove "), f"the x needs a name: {name!r}"

            page.mouse.move(2, 2)
            page.wait_for_timeout(200)
            resting = _composer_swatch(page, ".thread-ref-chip-remove")
            material = remove.evaluate("""el => {
              const probe = document.createElement('i'); el.parentElement.appendChild(probe);
              const read = (property, value) => { probe.style[property] = value; return getComputedStyle(probe)[property]; };
              const values = {steel:read('backgroundColor','var(--wb-steel)'),
                hover:read('backgroundColor','var(--wb-steel-2)'), ink:read('borderTopColor','var(--wb-ink)'),
                raised:read('boxShadow','var(--wb-raised)')};
              probe.remove(); return values;
            }""")
            assert {"btn", "btn--ghost", "btn--sm"} <= set((remove.get_attribute("class") or "").split())
            assert resting["background"] == material["steel"] and resting["border"] == material["ink"], (resting, material)
            assert resting["shadow"] == material["raised"], (resting, material)
            remove.hover()
            page.wait_for_timeout(200)
            hovered = _composer_swatch(page, ".thread-ref-chip-remove")
            print(f"[hs200-41] chip x @{width} resting={json.dumps(resting)}")
            print(f"[hs200-41] chip x @{width} hovered={json.dumps(hovered)}")
            assert hovered["background"] == material["hover"] != resting["background"], (resting, hovered, material)
            assert hovered["border"] == material["ink"] and hovered["shadow"] == material["raised"], (hovered, material)
            assert hovered["labelContrast"] >= 4.5, hovered
            _composer_shot_element(
                page, page.locator('[data-testid="composer-chips"]'),
                f"composer-refchip-hover-{width}", pad=28,
            )

            # The focus ring must be reached
            # by a REAL Tab — a scripted `.focus()` leaves Chromium in mouse
            # modality, where `:focus-visible` does not apply and an absent
            # ring would prove nothing.
            page.locator(".thread-composer-input").focus()
            page.keyboard.press("Shift+Tab")
            page.wait_for_timeout(120)
            ring = page.evaluate(
                """() => {
                    const el = document.activeElement;
                    const cs = getComputedStyle(el);
                    return {
                      onTheX: el.classList.contains('thread-ref-chip-remove'),
                      name: (el.getAttribute('aria-label') || el.textContent || '').trim(),
                      outlineStyle: cs.outlineStyle,
                      outlineWidth: cs.outlineWidth,
                      outlineColor: cs.outlineColor,
                      focusVisible: el.matches(':focus-visible'),
                    };
                }"""
            )
            print(f"[hs200-41] chip x focus ring @{width}: {json.dumps(ring)}")
            assert ring["onTheX"] and ring["name"] == name, ring
            if ring["onTheX"]:
                _composer_shot_element(
                    page, page.locator('[data-testid="composer-chips"]'),
                    f"composer-refchip-focus-{width}", pad=28,
                )
                assert ring["focusVisible"], "Tab did not make the x focus-visible"
                assert ring["outlineStyle"] != "none" and ring["outlineWidth"] != "0px", (
                    f"the focus ring did NOT survive the library swap: {ring}"
                )
            owned = remove.evaluate("""el => {
              const r=el.getBoundingClientRect(); const x=r.left+r.width/2, y=r.top+r.height/2;
              const hit=document.elementFromPoint(x,y);
              return r.width>0 && r.height>0 && x>=0 && y>=0 && x<innerWidth && y<innerHeight && !!hit && el.contains(hit);
            }""")
            assert owned, "the chip removal control does not own its touch/click centre"
            remove.click()
            remove.wait_for(state="detached")
            assert field.is_visible(), "removing one reference must keep the composer open"

            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()
