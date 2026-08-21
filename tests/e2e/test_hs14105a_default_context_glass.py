"""HS-141-05A honest browser proof for default AI context.

The home and database are fresh. Notes are setup through their public API;
attachment/default commands and Thought births use the real browser HTTP path.
MCP parity uses the same application service. No context ledger or Thought row
is forged by the walk.
"""
from __future__ import annotations

import os
import re
import uuid
from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("playwright.sync_api", reason="glass walk needs Playwright")
pytest.importorskip("fastapi.testclient", reason="glass walk needs web dependencies")

ASSETS = Path(__file__).resolve().parents[2] / "pm/roadmap/holdspeak/phase-141-from-thought-to-work/assets/story-05a"
TOKEN = "hs14105a-default-context-glass"
EVERYDAY = "knowledge:hs-seed-everyday-context"


class _NoPolicyDispatchEngine:
    active_provider = "default-context-zero-dispatch"

    def __init__(self) -> None:
        self.calls = 0

    def run_prompt(self, **_kwargs: object) -> str:
        self.calls += 1
        return '{"kind":"refusal","reason":"policy must not dispatch"}'


def _api(page: Any, method: str, path: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
    result = page.evaluate(
        """async ([method, path, body]) => {
          const response = await fetch(path, {
            method,
            headers: {
              'authorization': 'Bearer hs14105a-default-context-glass',
              ...(body ? {'content-type': 'application/json'} : {}),
            },
            body: body ? JSON.stringify(body) : undefined,
          });
          return {status: response.status, payload: await response.json()};
        }""",
        [method, path, body],
    )
    assert result["status"] < 300, result
    return result["payload"]


def _shot(page: Any, name: str) -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(ASSETS / name), full_page=False)


def _clean(page: Any, errors: list[str]) -> None:
    assert not errors, errors
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
    assert page.evaluate("document.body.scrollWidth <= window.innerWidth")
    assert page.locator(".is-primary:visible").count() <= 1


def _finish(page: Any) -> None:
    finish = page.get_by_role("button", name="Finish instead", exact=True)
    if finish.count() and finish.first.is_visible():
        finish.first.click()
    else:
        page.get_by_role("button", name="More", exact=True).click()
        page.get_by_label("More thought actions").get_by_role("button", name="Finish instead").click()
    page.get_by_role("button", name="Resume refining").wait_for()


def _new_thought(page: Any, text: str) -> None:
    title = text.rstrip(".")
    created = _api(page, "POST", "/api/thoughts", {
        "request_id": str(uuid.uuid4()), "raw_text": text, "source": {"kind": "typed"},
        "initial_note": {"title": title, "body_markdown": text, "tags": []},
    })
    page.evaluate(
        "([id, receipt]) => sessionStorage.setItem(`hs.thought.default-context-receipt.${id}`, JSON.stringify(receipt))",
        [created["thought"]["id"], created["default_context_receipt"]],
    )
    base_url = page.url.split("?", 1)[0]
    page.goto(f"{base_url}?open=note%3A{created['thought']['working_note']['id']}", wait_until="load")
    page.get_by_role("region", name="Thought context").wait_for()


@pytest.mark.e2e
@pytest.mark.requires_meeting
@pytest.mark.parametrize("width,label", [(1440, "1440"), (393, "393")])
def test_hs14105a_default_context_walk(tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
                                       width: int, label: str) -> None:
    from playwright.sync_api import sync_playwright
    import holdspeak.config as config_module
    import holdspeak.db.core as db_core
    from holdspeak.db import reset_database
    from holdspeak.kernel.runtime import _configure
    from holdspeak.mcp.families import thought as thought_family
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    home = tmp_path / "home"
    home.mkdir()
    db_path = tmp_path / "holdspeak.db"
    model = tmp_path / "deterministic-this-machine.gguf"
    model.touch()
    browser_cache = Path(os.environ.get("PLAYWRIGHT_BROWSERS_PATH", Path.home() / "Library/Caches/ms-playwright"))
    monkeypatch.setenv("PLAYWRIGHT_BROWSERS_PATH", str(browser_cache))
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setattr(config_module, "CONFIG_FILE", home / ".holdspeak" / "config.json")
    monkeypatch.setattr(db_core, "DEFAULT_DB_PATH", db_path)
    monkeypatch.setattr("holdspeak.intel.providers.configured_local_meeting_model_path", lambda: str(model))
    reset_database()
    database = db_core.get_database()
    engine = _NoPolicyDispatchEngine()
    broker = _configure(database)
    monkeypatch.setattr(broker.inference_runner, "_engine_factory", lambda _revision, **_kw: engine)
    monkeypatch.setattr(thought_family, "get_database", lambda: database)
    callbacks = WebRuntimeCallbacks(on_bookmark=lambda *_: None, on_stop=lambda: None, get_state=lambda: {})
    server = MeetingWebServer(callbacks, auth_token=TOKEN)
    url = server.start()
    errors: list[str] = []
    command_bodies: list[str] = []
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": width, "height": 900})
            page.emulate_media(reduced_motion="reduce")
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.on("request", lambda request: command_bodies.append(request.post_data or "")
                    if request.url.endswith("/api/thoughts/default-context") and request.method == "PUT" else None)
            page.goto(f"{url}/?token={TOKEN}", wait_until="load")
            _api(page, "POST", "/api/desk/seed")
            _api(page, "POST", "/api/notes", {
                "id": "project-launch", "title": "Project launch",
                "body_markdown": "Launch owner and delivery constraints.", "tags": [],
            })

            # Adopt one ordinary Note, attach two refs through the live picker,
            # and replace the complete future policy in one explicit command.
            page.locator("textarea").first.fill("Set up reusable launch context.")
            page.get_by_role("button", name="Keep as Note").click()
            page.get_by_role("button", name="Continue later").click()
            page.get_by_role("button", name="Develop this thought").click()
            page.get_by_role("button", name="Cancel", exact=True).click()
            page.get_by_role("button", name="Attach", exact=True).click()
            picker = page.get_by_role("region", name="Attach context")
            assert picker.get_by_role("heading", name="On this Thought").is_visible()
            assert picker.get_by_role("heading", name="For new Thoughts").is_visible()
            assert picker.get_by_text("Attach context to use it by default.").is_visible()
            assert picker.get_by_role("button", name="Use these by default").count() == 0
            picker.get_by_role("button", name="Everyday context, 5 notes").click()
            page.get_by_text("Attached Everyday context").wait_for()
            page.get_by_role("button", name="Attach", exact=True).click()
            picker = page.get_by_role("region", name="Attach context")
            picker.get_by_role("button", name="Browse all notes").click()
            picker.get_by_role("button", name="Project launch, Note").click()
            page.get_by_text("Attached Project launch").wait_for()
            page.get_by_role("button", name="Attach", exact=True).click()
            picker = page.get_by_role("region", name="Attach context")
            picker.get_by_role("button", name="Use these by default").wait_for()
            assert picker.get_by_text("Everyday context", exact=True).count() >= 1
            assert picker.get_by_text("Project launch", exact=True).count() >= 1
            if width == 393:
                assert page.evaluate("document.activeElement?.getAttribute('type') !== 'search'")
            _shot(page, f"hs-141-05a-set-default-{label}.png")
            picker.get_by_role("button", name="Use these by default").click()
            page.get_by_text("Used Everyday context + Project launch for new Thoughts").wait_for()
            configured = _api(page, "GET", "/api/thoughts/default-context")["default_context"]
            assert set(configured["refs"]) == {EVERYDAY, "note:project-launch"}

            # A browser-created Thought opens with the authoritative frozen set
            # and the quiet application receipt on its first render.
            _finish(page)
            _new_thought(page, "A default-born launch thought.")
            page.get_by_text("Attached by default").wait_for()
            context = page.get_by_role("region", name="Thought context")
            assert context.get_by_text("Everyday context · 5 notes").is_visible()
            assert context.get_by_text("Project launch · 1 note").is_visible()
            assert context.get_by_text("Default", exact=True).count() == 2
            _shot(page, f"hs-141-05a-born-default-{label}.png")

            # Removing one selection is scoped to this Thought. The picker
            # still exposes the complete future set and Stop as a separate act.
            page.get_by_role("button", name="Attach", exact=True).click()
            picker = page.get_by_role("region", name="Attach context")
            picker.locator(".thought-context-policy-row", has_text="Project launch").get_by_role(
                "button", name="Remove from this Thought"
            ).click()
            page.get_by_text(re.compile(r"Removed .* from this Thought; the default for new Thoughts is unchanged\.")).wait_for()
            assert len(_api(page, "GET", "/api/thoughts/default-context")["default_context"]["refs"]) == 2

            # Source drift is fenced before provider dispatch. Both widths show
            # the named explanation and Update as the sole state primary.
            about = _api(page, "GET", "/api/notes/hs-seed-about-me")["note"]
            _api(page, "PUT", "/api/notes/hs-seed-about-me", {
                "body_markdown": about["body_markdown"] + "\n\nDefault context changed.",
            })
            page.get_by_role("button", name="Keep refining").click()
            page.get_by_text("Everyday context changed. Update it before asking another question.").wait_for()
            assert engine.calls == 0
            page.locator(".is-primary", has_text="Update context").wait_for()
            assert page.locator(".is-primary:visible").count() == 1
            assert page.locator(".is-primary:visible").inner_text() == "Update context"
            _shot(page, f"hs-141-05a-stale-{label}.png")
            page.locator(".is-primary:visible").click()

            # One invalid member skips the whole configured set for the next
            # Thought. The normal lifecycle primary remains and repair stays in
            # the same picker with last-known name plus Stop.
            _api(page, "DELETE", "/api/notes/project-launch")
            _finish(page)
            _new_thought(page, "A Thought while one default is unavailable.")
            page.get_by_text("Default AI context was not applied").wait_for()
            assert "None" in page.get_by_role("region", name="Thought context").inner_text()
            not_applied = page.locator(".thought-context-action-receipt", has_text="Default AI context was not applied")
            detail = not_applied.locator("p").inner_text()
            assert "Project launch" in detail and "could not be attached" in detail and "The whole set was skipped." in detail
            page.get_by_role("button", name="Attach", exact=True).click()
            picker = page.get_by_role("region", name="Attach context")
            assert picker.get_by_role("heading", name="On this Thought").is_visible()
            unavailable = picker.get_by_text("Project launch", exact=True)
            unavailable.scroll_into_view_if_needed()
            assert unavailable.is_visible()
            assert picker.get_by_text("Unavailable", exact=True).is_visible()
            stop_default = picker.get_by_role("button", name="Stop using by default")
            stop_default.scroll_into_view_if_needed()
            assert stop_default.is_visible()
            _shot(page, f"hs-141-05a-not-applied-{label}.png")
            picker.get_by_role("button", name="Stop using by default").click()
            page.get_by_text("New Thoughts start with no AI context. This Thought is unchanged.").wait_for()
            assert _api(page, "GET", "/api/thoughts/default-context")["default_context"]["refs"] == []

            # MCP uses the same default-policy authority. Reloaded browser
            # projection reflects its replacement without copied material.
            owner = Principal(PrincipalKind.OWNER, "hs14105a-glass")
            empty = thought_family.dispatch("thought.get_default_context", {}, owner)["default_context"]
            replaced = thought_family.dispatch("thought.replace_default_context", {
                "request_id": str(uuid.uuid4()), "expected_revision": empty["revision"], "refs": [EVERYDAY],
            }, owner)
            assert replaced["default_context"]["refs"] == [EVERYDAY]
            page.reload(wait_until="load")
            assert _api(page, "GET", "/api/thoughts/default-context")["default_context"]["refs"] == [EVERYDAY]
            assert command_bodies and all("body_markdown" not in body and "leaves" not in body and "title" not in body
                                          for body in command_bodies)
            assert engine.calls == 0
            _clean(page, errors)
            browser.close()
    finally:
        server.stop()
        reset_database()
