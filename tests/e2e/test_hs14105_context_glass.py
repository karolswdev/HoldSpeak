"""HS-141-05 real-glass proof for explicit Thought context.

Only the provider is deterministic. Seed, Note edits, Thought adoption,
context commands, kernel dispatch, review actions, persistence, and MCP all use
their production application seams. No attachment or review row is inserted by
this test.
"""
from __future__ import annotations

import os
import threading
import time
import uuid
from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("playwright.sync_api", reason="glass walk needs Playwright")
pytest.importorskip("fastapi.testclient", reason="glass walk needs web dependencies")

# This walk targets the retired pre-Workbench refinement card. The shipped
# replacement `test_hs141_thought_workbench_glass.py` covers the live context
# sheet, exact Workbench mutation fences, frozen-turn behavior, and both
# responsive widths; context service/MCP invariants remain covered below the
# browser seam by their dedicated suites.
pytestmark = pytest.mark.skip(reason="superseded by the Thought Workbench real-path glass")

ASSETS = Path(__file__).resolve().parents[2] / "pm/roadmap/holdspeak/phase-141-from-thought-to-work/assets/story-05"
TOKEN = "hs14105-context-glass"
MARKER_V1 = "ORCHID CLOCK belongs in the launch note"
MARKER_V2 = MARKER_V1 + ", version two"
MARKER_V3 = MARKER_V1 + ", version three"
MARKER_V4 = MARKER_V1 + ", version four"
EVERYDAY = "knowledge:hs-seed-everyday-context"


class _ExactContextEngine:
    active_provider = "deterministic-exact-context"

    def __init__(self) -> None:
        self.expected_material = ""
        self.entered = threading.Event()
        self.release = threading.Event()
        self.block = False
        self.calls = 0
        self.observed: list[str] = []

    def arm(self, material: str, *, block: bool = False) -> None:
        self.expected_material = material
        self.block = block
        self.entered = threading.Event()
        self.release = threading.Event()

    def run_prompt(self, *, user_prompt: str, **_kwargs: object) -> str:
        self.calls += 1
        self.observed.append(user_prompt)
        if (not self.expected_material or MARKER_V1 not in self.expected_material
                or self.expected_material not in user_prompt):
            # Negative control: a provider without the exact frozen block can
            # never manufacture the expected question.
            return '{"kind":"refusal","reason":"exact context missing"}'
        self.entered.set()
        if self.block:
            assert self.release.wait(10), "test provider was never released"
        return ('{"kind":"question","question":"Who owns ORCHID CLOCK?",'
                '"reason":"It makes the launch owner explicit."}')


def _shot(page: Any, name: str) -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(ASSETS / name), full_page=False)


def _api(page: Any, method: str, path: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
    result = page.evaluate(
        """async ([method, path, body]) => {
          const response = await fetch(path, {
            method,
            headers: {
              'authorization': 'Bearer hs14105-context-glass',
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


def _cursors(thought: dict[str, Any]) -> dict[str, int]:
    return {
        "expected_aggregate_revision": thought["aggregate_revision"],
        "expected_working_revision": thought["working_revision"],
        "expected_attachment_revision": thought["attachment_revision"],
    }


def _clean(page: Any, errors: list[str]) -> None:
    assert not errors, errors
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
    assert page.evaluate("document.body.scrollWidth <= window.innerWidth")
    assert page.locator(".is-primary:visible").count() <= 1


@pytest.mark.e2e
@pytest.mark.requires_meeting
@pytest.mark.parametrize("width,label", [(1440, "1440"), (393, "393")])
def test_hs14105_real_context_walk(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int, label: str) -> None:
    from playwright.sync_api import sync_playwright
    import holdspeak.config as config_module
    import holdspeak.db.core as db_core
    from holdspeak.db import reset_database
    from holdspeak.kernel.runtime import _configure
    from holdspeak.mcp.families import thought as thought_family
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services.refinement_context_service import RefinementContextService
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
    engine = _ExactContextEngine()
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
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.on("request", lambda request: command_bodies.append(request.post_data or "")
                    if "/api/thoughts/" in request.url and
                    ("/context/" in request.url or request.url.endswith("/refine")) else None)
            page.goto(f"{url}/?token={TOKEN}", wait_until="load")

            # Explicit packaged seed through the real owner route.
            _api(page, "POST", "/api/desk/seed")
            seeded = _api(page, "GET", "/api/notes/hs-seed-about-me")["note"]
            _api(page, "PUT", "/api/notes/hs-seed-about-me", {
                "body_markdown": seeded["body_markdown"] + "\n\n" + MARKER_V1,
            })

            # Create and adopt through the ordinary browser flow.
            page.locator("textarea").first.fill("Ship ORCHID CLOCK with a named owner.")
            page.get_by_role("button", name="Keep as Note").click()
            page.get_by_role("button", name="Continue later").click()
            page.get_by_role("button", name="Develop this thought").click()
            page.get_by_role("button", name="Cancel").click()
            context = page.get_by_role("region", name="Thought context")
            assert context.get_by_text("AI context", exact=True).is_visible()
            assert "None" in context.inner_text()

            page.get_by_role("button", name="Attach", exact=True).click()
            picker = page.get_by_role("region", name="Attach context")
            picker.get_by_text("Pinned").wait_for()
            assert picker.get_by_text("Everyday context").is_visible()
            assert picker.get_by_role("button", name="Browse all notes").is_visible()
            for control in (picker.get_by_role("button", name="Everyday context, 5 notes"),
                            picker.get_by_role("button", name="Browse all notes")):
                assert control.evaluate("""el => {
                  const r = el.getBoundingClientRect();
                  const hit = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2);
                  return r.top >= 0 && r.bottom <= innerHeight && !!hit && (hit === el || el.contains(hit));
                }"""), "pinned context controls must be in-view and unobscured on open"
            if width == 393:
                assert page.evaluate("document.activeElement?.getAttribute('type') !== 'search'")
            _shot(page, f"hs-141-05-picker-{label}.png")
            picker.get_by_role("button", name="Everyday context, 5 notes").click()
            page.get_by_text("Everyday context · 5 notes").wait_for()
            page.get_by_text("Everyday context · 5 notes").click()
            for title in ("About me", "Current priorities", "How I like help", "People & vocabulary", "Meeting preferences"):
                assert context.get_by_text(title, exact=True).is_visible()
            _shot(page, f"hs-141-05-attached-{label}.png")

            notes = _api(page, "GET", "/api/notes")["notes"]
            working = next(note for note in notes if not str(note["id"]).startswith("hs-seed-"))
            owned = _api(page, "GET", f"/api/thoughts/for-note/{working['id']}")["thought"]
            frozen = RefinementContextService(database).materialize(
                owned["id"], owned["attachment_revision"], owned["attachment_sha256"]
            )
            assert frozen.material.startswith('<untrusted-refinement-context-json schema="holdspeak.context.v1">\n[')
            assert frozen.grounding_echo["titles"] == ["Everyday context"]
            assert MARKER_V1 in frozen.material
            assert "Who owns ORCHID CLOCK?" not in engine.run_prompt(user_prompt="negative control")

            # Run a phrase-gated turn on the already-open real Desk Thought.
            engine.arm(frozen.material)
            page.get_by_role("button", name="Keep refining").click()
            page.wait_for_timeout(1200)
            dispatched = _api(page, "GET", f"/api/thoughts/{owned['id']}")["thought"]
            assert engine.calls > 1, {"continuity": dispatched.get("continuity"), "observed": engine.observed}
            assert dispatched["continuity"]["state"] == "review_ready", {
                "continuity": dispatched["continuity"], "prompt": engine.observed[-1]
            }
            page.get_by_text("Who owns ORCHID CLOCK?").wait_for(timeout=20000)
            page.get_by_text("Used Everyday context · 5 notes").click()
            assert page.get_by_label("Refinement question").get_by_text("About me", exact=True).is_visible()
            _shot(page, f"hs-141-05-used-{label}.png")
            # Drift before the owner answer makes the returned aggregate stale,
            # while Answer itself remains the single owner-text primary.
            leaf = _api(page, "GET", "/api/notes/hs-seed-about-me")["note"]
            _api(page, "PUT", "/api/notes/hs-seed-about-me", {
                "body_markdown": leaf["body_markdown"].replace(MARKER_V1, MARKER_V2),
            })
            page.get_by_label("Answer").fill("Mina owns ORCHID CLOCK.")
            page.get_by_role("button", name="Answer").click()
            page.get_by_text("Answer added to your working note.").wait_for()

            # Source drift is visible and both UI and direct refine avoid a send.
            page.get_by_text("Everyday context changed. Update it before asking another question.").wait_for()
            assert page.get_by_role("button", name="Keep refining").count() == 0
            before = engine.calls
            stale = _api(page, "GET", f"/api/thoughts/{owned['id']}")["thought"]
            _api(page, "POST", f"/api/thoughts/{owned['id']}/refine", {"request_id": str(uuid.uuid4()), **_cursors(stale)})
            time.sleep(0.5)
            assert engine.calls == before
            _shot(page, f"hs-141-05-stale-{label}.png")

            page.locator(".is-primary", has_text="Update context").click()
            current = _api(page, "GET", f"/api/thoughts/{owned['id']}")["thought"]
            frozen_v2 = RefinementContextService(database).materialize(
                current["id"], current["attachment_revision"], current["attachment_sha256"]
            )
            assert MARKER_V2 in frozen_v2.material

            # Mutation after the committed dispatch hook cannot replace frozen bytes.
            engine.arm(frozen_v2.material, block=True)
            page.get_by_role("button", name="Keep refining").click()
            assert engine.entered.wait(5)
            leaf = _api(page, "GET", "/api/notes/hs-seed-about-me")["note"]
            _api(page, "PUT", "/api/notes/hs-seed-about-me", {
                "body_markdown": leaf["body_markdown"].replace(MARKER_V2, MARKER_V3),
            })
            engine.release.set()
            page.get_by_text("Who owns ORCHID CLOCK?").wait_for(timeout=10000)
            assert MARKER_V2 in engine.observed[-1] and MARKER_V3 not in engine.observed[-1]
            if width == 393:
                page.get_by_role("button", name="More").click()
                page.get_by_label("More thought actions").get_by_role("button", name="Reject").click()
            else:
                page.get_by_role("button", name="Reject").click()
            page.get_by_text("Refinement dismissed.").wait_for()

            # Refresh, then detach while a real provider call is delayed. The
            # superseded late result must never become another review.
            page.get_by_text("Everyday context changed. Update it before asking another question.").wait_for()
            page.locator(".is-primary", has_text="Update context").click()
            current = _api(page, "GET", f"/api/thoughts/{owned['id']}")["thought"]
            frozen_v3 = RefinementContextService(database).materialize(
                current["id"], current["attachment_revision"], current["attachment_sha256"]
            )
            engine.arm(frozen_v3.material, block=True)
            page.get_by_role("button", name="Keep refining").click()
            assert engine.entered.wait(5)
            detail = context.locator("details.thought-context-chip").first
            if detail.get_attribute("open") is None:
                context.get_by_text("Everyday context · 5 notes").click()
            context.get_by_role("button", name="Remove from this Thought").click()
            engine.release.set()
            page.wait_for_timeout(1200)
            assert page.get_by_label("Refinement question").count() == 0

            # MCP drives the same application authority; reload reflects every
            # authoritative change and no copied material crosses the command.
            owner = Principal(PrincipalKind.OWNER, "hs14105-glass")
            current = _api(page, "GET", f"/api/thoughts/{owned['id']}")["thought"]
            listing = thought_family.dispatch("thought.list_context", {"thought_id": owned["id"]}, owner)
            assert listing["pinned"][0]["ref"] == EVERYDAY
            attached = thought_family.dispatch("thought.attach_context", {
                "thought_id": owned["id"], "ref": EVERYDAY, "request_id": str(uuid.uuid4()), **_cursors(current)
            }, owner)["thought"]

            # Stop/start the real HTTP host over the same isolated database;
            # the same authoritative attachment revision and leaf versions return.
            restart_port = server.port
            server.stop()
            server = MeetingWebServer(callbacks, port=restart_port, auth_token=TOKEN)
            url = server.start()
            page.goto(f"{url}/?token={TOKEN}", wait_until="load")
            persisted = _api(page, "GET", f"/api/thoughts/{owned['id']}")["thought"]
            assert persisted["attachment_revision"] == attached["attachment_revision"]
            assert persisted["attachments"][0]["leaves"][0]["version_label"]
            leaf = _api(page, "GET", "/api/notes/hs-seed-about-me")["note"]
            _api(page, "PUT", "/api/notes/hs-seed-about-me", {
                "body_markdown": leaf["body_markdown"].replace(MARKER_V3, MARKER_V4),
            })
            stale_after_restart = _api(page, "GET", f"/api/thoughts/{owned['id']}")["thought"]
            assert stale_after_restart["attachments"][0]["state"] == "stale"
            refreshed = thought_family.dispatch("thought.refresh_context", {
                "thought_id": owned["id"], "ref": EVERYDAY, "request_id": str(uuid.uuid4()),
                **_cursors(stale_after_restart)
            }, owner)["thought"]
            assert refreshed["attachments"][0]["state"] == "current"
            detached = thought_family.dispatch("thought.detach_context", {
                "thought_id": owned["id"], "ref": EVERYDAY, "request_id": str(uuid.uuid4()), **_cursors(refreshed)
            }, owner)["thought"]
            assert detached["attachments"] == []
            page.reload(wait_until="load")
            assert _api(page, "GET", f"/api/thoughts/{owned['id']}")["thought"]["attachments"] == []
            assert command_bodies
            assert all(MARKER_V1 not in body and "body_markdown" not in body and "leaves" not in body
                       for body in command_bodies)
            _clean(page, errors)
            browser.close()
    finally:
        server.stop()
        reset_database()
