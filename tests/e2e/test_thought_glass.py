"""The Thought window, rendered: exact geometry relations jsdom cannot read
(push 2 of the test diet, 2026-10-12: moved from
test_philo304_thought_foot_reflow.py, parked in tests/e2e/_parked/).

PHILO-3-04 counsel (Astra, RATIFY-WITH-CONDITIONS, condition 1) — the
Thought foot's receipt yields; it never pushes the verbs off the glass.

Above the 560 px container breakpoint the receipt column was `max-content`:
at a 600 px window `DID NOT SAVE · THE HUB DID NOT ACCEPT THE CHANGE` pushed
the verbs' right edge past the window and squeezed READS to zero width, and
a 58-character drawer name overflowed too. JSDOM cannot measure layout, so
this rig loads the BUILT foot on a real hub (its own isolated HOME), names
the drawer with 58 characters, fails the write at the browser boundary with
an HTTP 500, and measures the real geometry.

The Thought window in a real browser: only what needs one.

Kept by the test diet (push 2, 2026-10-12); each check needs a real browser:

* the one clean note (HS-201-12): the answer pad, the question and the foot
  stay inside the window at 1440 and 393 (geometry), Escape closes the
  Reads well; a long note, a long question and a long context name never
  clip (geometry);
* the custody walk (HS-141): a Note edit typed in CodeMirror while the AI
  runs (keys, Ctrl+S) suppresses the frozen question; the working save is
  409 then 200; Escape returns focus to Change; a hub restart redispatches
  nothing.

Was tests/e2e/test_hs201_12_thought_note_glass.py and
tests/e2e/test_hs141_thought_workbench_glass.py. The draft-append leg is
web/src/desk/thought-workspace/ThoughtWorkspaceWindow.test.tsx
("appends a returned draft to the note instead of replacing it").
"""
from __future__ import annotations

import json
import os
import re
import shutil
import tempfile
import threading
import time
import uuid
from pathlib import Path
from typing import Any

import pytest

from scripts.graph_walk import TOKEN, Hub
from tests._evidence import evidence_dir
from tests.e2e.chair_windows import go_group, open_chair_window
from tests.e2e.glass_infra import _normal_chair
from .glass_infra import _api as _gi_api, _boot as _gi_boot, _ensure_build, _settle  # the e2e-high-2 section

pytestmark = [pytest.mark.e2e, pytest.mark.timeout(300, method="thread")]

DRAWER = "Architecture decisions for the ingest queue cutover in Q4."  # 58 characters
CAUSE = "DID NOT SAVE · THE HUB DID NOT ACCEPT THE CHANGE"
WRITE = ".thought-note-foot .surface-footer-receipt-line:not([data-line])"

GEOMETRY_JS = """() => {
  const win = document.querySelector('.thought-workspace-window').getBoundingClientRect();
  const box = (sel) => { const e = document.querySelector(sel); if (!e) return null; const r = e.getBoundingClientRect(); return {left: r.left, right: r.right, width: r.width}; };
  const lines = [...document.querySelectorAll('.thought-note-foot .surface-footer-receipt-line')];
  const verbs = [...document.querySelectorAll('.thought-note-foot .surface-footer-verbs button')].map((b) => b.getBoundingClientRect());
  return {
    window: {left: win.left, right: win.right, width: win.width},
    reads: box('.thought-note-foot .surface-footer-egress'),
    reads_text: document.querySelector('.thought-note-reads')?.textContent,
    receipt: box('.thought-note-foot .surface-footer-receipt'),
    verbs_left: Math.min(...verbs.map((r) => r.left)),
    verbs_right: Math.max(...verbs.map((r) => r.right)),
    clipped: lines.filter((e) => e.scrollWidth > e.clientWidth + 1).map((e) => e.innerText),
    lines: lines.map((e) => e.innerText),
  };
}"""


def _assert_geometry(geo: dict, label: str) -> None:
    right = geo["window"]["right"]
    assert geo["verbs_right"] <= right + 0.5, f"{label}: verbs end at {geo['verbs_right']} past the window's {right}: {geo}"
    assert geo["reads"]["width"] >= 40, f"{label}: READS squeezed to {geo['reads']['width']} px: {geo}"
    assert geo["receipt"]["right"] <= geo["verbs_left"] + 0.5 or geo["receipt"]["left"] >= geo["reads"]["left"], f"{label}: {geo}"
    assert geo["receipt"]["right"] <= right + 0.5, f"{label}: receipt ends past the window: {geo}"
    assert not geo["clipped"], f"{label}: receipt text is clipped, not wrapped: {geo['clipped']}"
    assert geo["lines"][0] == CAUSE, f"{label}: {geo['lines']}"
    assert len(geo["lines"]) == 1, f"{label}: {geo['lines']}"
    assert DRAWER in geo["reads_text"], f"{label}: context was not attached: {geo}"


# The 600 px window is the narrow bound that failed (the receipt pushed the
# verbs off); a wider window only relaxes it, so 700 and the default width
# are not run (push 2). 393 is the phone.
@pytest.mark.parametrize(("viewport", "window_width"), [(1440, 600), (393, None)])
def test_the_receipt_yields_to_the_verbs(viewport: int, window_width: int | None) -> None:
    from playwright.sync_api import sync_playwright

    home = Path(tempfile.mkdtemp(prefix="philo304-reflow-home-"))
    profile = Path(tempfile.mkdtemp(prefix="philo304-reflow-profile-"))
    hub = Hub(home).start()
    try:
        with sync_playwright() as play:
            context = play.chromium.launch_persistent_context(
                str(profile), viewport={"width": viewport, "height": 900 if viewport >= 1000 else 852},
                base_url=hub.url)
            page = context.new_page()
            page.goto(f"{hub.url}/?token={TOKEN}")
            # The first-use gate, crossed the way every glass rig crosses it
            # (glass_infra._normal_chair): a fixed 8 s try missed a late gate
            # under load, and the gate then hid the menu bar and the Dock.
            _normal_chair(page)
            # Use the current Note producer. Capture's old Speak dock icon
            # is no longer a door on the four-tile phone dock.
            menu = "desk" if viewport > 720 else "go"
            page.locator(f".desk-verbbar-item[data-menu-id='{menu}'] button").click()
            if viewport <= 720:
                go_group(page, "New")
            label = "Write a thought" if viewport > 720 else "Note"
            page.locator(".desk-verbbar-menu [role='menuitem']").filter(has_text=label).first.click()
            page.locator('.thought-note-document').wait_for()
            status, listing = hub.api("GET", "/api/thoughts")
            assert status == 200 and len(listing["items"]) == 1, (status, listing)
            status, answer = hub.api("GET", f"/api/thoughts/{listing['items'][0]['id']}")
            assert status == 200, (status, answer)
            thought = answer["thought"]
            # The Reads slot exists only for real context. Give it the long
            # name whose width must survive the failed-save receipt.
            status, note = hub.api("POST", "/api/notes", {"title": DRAWER, "body_markdown": "The cutover holds.", "tags": []})
            assert status == 201, (status, note)
            status, attached = hub.api("POST", f"/api/thoughts/{thought['id']}/context/attach", {
                "request_id": str(uuid.uuid4()), "ref": f"note:{note['note']['id']}",
                "expected_aggregate_revision": thought["aggregate_revision"],
                "expected_working_revision": thought["working_revision"],
                "expected_attachment_revision": thought["attachment_revision"],
            })
            assert status == 200, (status, attached)
            page.goto(f"{hub.url}/?token={TOKEN}&open=note%3A{thought['working_note']['id']}", wait_until="load")
            body = page.locator('[aria-label="Note body"]')
            body.wait_for()
            if window_width:
                page.eval_on_selector(".thought-workspace-window", f"e => {{ e.style.width = '{window_width}px'; }}")
            page.route("**/api/thoughts/*/working", lambda route: route.fulfill(
                status=500, content_type="application/json", body='{"error":"refused"}'))
            body.fill("Drain the queue before the cutover.")
            page.wait_for_function(
                "([sel, want]) => { const e = document.querySelector(sel); return !!e && e.innerText === want; }",
                arg=[WRITE, CAUSE], timeout=15000)
            _reads_full(page.locator('.thought-note-reads'), DRAWER)
            geo = page.evaluate(GEOMETRY_JS)
            if window_width:
                assert abs(geo["window"]["width"] - window_width) < 1, geo
            context.close()
        _assert_geometry(geo, f"{viewport}/{window_width or 'default'}")
    finally:
        hub.stop()
        shutil.rmtree(profile, ignore_errors=True)
        shutil.rmtree(home, ignore_errors=True)


# ══ the clean note and the custody walk (was test_hs201_12_thought_note_glass.py and test_hs141_thought_workbench_glass.py) ══

NOTE_TOKEN = "hs201-12-thought-glass"
SHOTS = evidence_dir("pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/story-12-shots")
# The write receipt carries the hub's timestamp. Filing is no longer a
# second decorative line on the Note face (PHILO-17 words).
KEPT_LINE = '.thought-note-foot .surface-footer-receipt-line[role="status"]'
KEPT_WORDS = re.compile(r"^Saved \d{1,2}:\d{2}( [AP]M)?$")
# The owner's own shot (2026-09-20): a dictated note, a mid-sentence title.
OWNER_TITLE = "Well, there's just a little bit of misunderstanding here, I believe my team…"
OWNER_BODY = "Yeah, I have it that way and what about you?"
QUESTION = "Who is misunderstanding what, and what would settle it?"
LONG_QUESTION = (
    "Who exactly holds the other reading of the plan, on which line of it, "
    "and what single fact, said by one named person, would settle the "
    "disagreement for the whole team before the next review?"
)
LONG_WORD = "deadline"


class _OneQuestionEngine:
    active_provider = "deterministic-thought-interview"

    def __init__(self) -> None:
        self.calls = 0

    def run_prompt(self, *, user_prompt: str, **_kwargs: object) -> str:
        self.calls += 1
        question = LONG_QUESTION if LONG_WORD in user_prompt else QUESTION
        return ('{"kind":"question","question":"' + question + '",'
                '"reason":"One named person and one fact settle it."}')


def _api(page: Any, method: str, path: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
    result = page.evaluate(
        """async ([method, path, body, token]) => {
          const response = await fetch(path, {
            method,
            headers: {
              authorization: `Bearer ${token}`,
              ...(body ? {'content-type': 'application/json'} : {}),
            },
            body: body ? JSON.stringify(body) : undefined,
          });
          return {status: response.status, payload: await response.json()};
        }""",
        [method, path, body, NOTE_TOKEN],
    )
    assert result["status"] < 300, result
    return result["payload"]


def _seed(page: Any, title: str, body: str) -> dict[str, Any]:
    created = _api(page, "POST", "/api/thoughts", {
        "request_id": str(uuid.uuid4()),
        "raw_text": body,
        "source": {"kind": "voice"},
        "initial_note": {"title": title, "body_markdown": body, "tags": ["team"]},
    })
    return created["thought"]


def _note_action(page: Any, workspace: Any, name: str) -> Any:
    """Press a real Note footer verb, through More on the phone."""
    button = workspace.get_by_role("button", name=name, exact=True)
    if button.count() and button.is_visible():
        button.click()
        return button
    workspace.get_by_role("button", name="More actions", exact=True).click()
    action = page.get_by_role("menuitem", name=name, exact=True)
    action.click()
    return action


def _refine_note(page: Any, thought_id: str) -> None:
    """Seed an active deterministic interview through its real producer.

    Idle Note Ask now opens Ask AI. This geometry test needs the distinct
    interview continuation rendered in the Note, not the Ask AI window.
    """
    thought = _api(page, "GET", f"/api/thoughts/{thought_id}")["thought"]
    _api(page, "POST", f"/api/thoughts/{thought_id}/refine", {
        "request_id": str(uuid.uuid4()),
        "expected_aggregate_revision": thought["aggregate_revision"],
        "expected_working_revision": thought["working_revision"],
        "expected_attachment_revision": thought["attachment_revision"],
    })
    page.reload(wait_until="load")


def _no_empty_heading(page: Any) -> None:
    """The owner's shot: a kicker over an h2 that renders nothing."""
    assert page.evaluate(
        "[...document.querySelectorAll('h1,h2,h3,h4,h5,h6')].filter(n => !n.textContent.trim()).length"
    ) == 0


def _no_horizontal_escape(page: Any) -> None:
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    assert page.evaluate("document.body.scrollWidth <= innerWidth")


def _squash(value: str) -> str:
    return " ".join(value.split()).upper()


def _reads_full(locator: Any, name: str) -> None:
    """The whole name is ON the glass: no ellipsis, no hidden overflow."""
    text = _squash(locator.inner_text())
    assert _squash(name) in text, (name, text)
    style = locator.evaluate(
        "el => { const s = getComputedStyle(el); return {overflow: s.textOverflow, wrap: s.whiteSpace,"
        " w: el.scrollWidth - el.clientWidth, h: el.scrollHeight - el.clientHeight}; }"
    )
    assert style["wrap"] not in ("nowrap", "pre"), style
    assert style["w"] <= 1, style
    assert style["h"] <= 1, style


def _in_frame(box: dict[str, float] | None, window: dict[str, float], name: str) -> None:
    assert box, f"{name} has no box"
    assert box["y"] >= window["y"] - 1, (name, box, window)
    assert box["y"] + box["height"] <= window["y"] + window["height"] + 1, (name, box, window)


def _boot(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, *, engine: Any = None):
    import holdspeak.config as config_module
    import holdspeak.db.core as db_core
    from holdspeak.db import reset_database
    from holdspeak.kernel.runtime import _configure
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    home = tmp_path / "home"
    home.mkdir()
    model = tmp_path / "deterministic-this-machine.gguf"
    model.touch()
    browser_cache = Path(os.environ.get("PLAYWRIGHT_BROWSERS_PATH", Path.home() / "Library/Caches/ms-playwright"))
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("PLAYWRIGHT_BROWSERS_PATH", str(browser_cache))
    monkeypatch.setattr(config_module, "CONFIG_FILE", home / ".holdspeak" / "config.json")
    monkeypatch.setattr(db_core, "DEFAULT_DB_PATH", tmp_path / "holdspeak.db")
    provider = {"path": str(model)}
    monkeypatch.setattr("holdspeak.intel.providers.configured_local_meeting_model_path", lambda: provider["path"])
    reset_database()
    database = db_core.get_database()
    from tests.unit.test_phase143_inference_assignments import OWNER, _profile, _result_claim
    from types import SimpleNamespace

    _profile(database, "thought-glass-engine", claims=("language", "structured_output", _result_claim("thought.interview"), _result_claim("speech.intent_classify")), boundary="same_device")
    engine = engine or _OneQuestionEngine()
    broker = _configure(database)
    broker.inference_adoption_service.migrate_legacy_config(OWNER, SimpleNamespace(
        thoughts=SimpleNamespace(inference_target_id="thought-glass-engine"),
        dictation=SimpleNamespace(runtime=SimpleNamespace(profile_id="thought-glass-engine")),
    ))
    monkeypatch.setattr(broker.inference_runner, "_engine_factory", lambda _revision, **_kw: engine)
    callbacks = WebRuntimeCallbacks(on_bookmark=lambda *_: None, on_stop=lambda: None, get_state=lambda: {})
    server = MeetingWebServer(callbacks, auth_token=NOTE_TOKEN)
    return server, server.start(), provider, engine


@pytest.mark.e2e
@pytest.mark.requires_meeting
@pytest.mark.parametrize("width", [1440, 393])
def test_thought_note_is_one_clean_note(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int) -> None:
    from playwright.sync_api import sync_playwright

    server, url, provider, engine = _boot(tmp_path, monkeypatch)
    SHOTS.mkdir(parents=True, exist_ok=True)
    errors: list[str] = []
    console_errors: list[str] = []
    responses: list[tuple[str, int]] = []
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": width, "height": 900})
            page.emulate_media(reduced_motion="reduce")
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.on("console", lambda message: console_errors.append(message.text) if message.type == "error" else None)
            page.on("response", lambda response: responses.append((response.url, response.status)) if "/api/thoughts/" in response.url else None)
            page.goto(f"{url}/?token={NOTE_TOKEN}", wait_until="load")
            _api(page, "POST", "/api/desk/seed")
            _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"})
            _api(page, "POST", "/api/notes", {"title": "Team context", "body_markdown": "The team owns the freeze date.", "tags": []})
            thought = _seed(page, OWNER_TITLE, OWNER_BODY)
            note_id = thought["working_note"]["id"]
            page.goto(f"{url}/?token={NOTE_TOKEN}&open=note%3A{note_id}", wait_until="load")

            workspace = page.locator(".desk-window.thought-workspace-window")
            workspace.wait_for(timeout=15000)
            workspace.get_by_role("region", name="Note", exact=True).wait_for()

            # An idle ready Note is plain; Ask is a footer action.
            assert workspace.get_by_role("region", name="Ask about this note", exact=True).count() == 0
            if width > 720:
                assert workspace.get_by_role("button", name="Ask about this note", exact=True).is_visible()
            else:
                assert workspace.get_by_role("button", name="More actions", exact=True).is_visible()
            assert page.get_by_role("textbox", name="Your answer").count() == 0
            assert workspace.get_by_role("toolbar", name="Markdown formatting").count() == 0
            assert workspace.get_by_role("button", name="Info", exact=True).count() == 0
            assert workspace.get_by_role("button", name="Add tag", exact=True).count() == 0
            assert workspace.get_by_role("region", name="Interview", exact=True).count() == 0
            assert page.get_by_text("Filed", exact=True).count() == 0
            assert page.get_by_text("Saved", exact=True).count() == 0
            _no_empty_heading(page)
            _no_horizontal_escape(page)
            # Every verb is a library species: btn (Button), or a library
            # control's own element (the desk mic, the in-place editor).
            assert workspace.evaluate(
                "el => [...el.querySelectorAll('button')].filter(node => "
                "!node.matches('.btn, [class*=\"desk-\"], [class*=\"surface-\"], [class*=\"gadget-\"]')).length"
            ) == 0
            assert workspace.locator(".btn--primary:visible").count() == 1
            assert workspace.locator(".btn--primary:visible").inner_text().strip() == "Finish"

            # The title wraps: every character of it is drawn, never clipped.
            title = workspace.locator(".thought-note-title")
            assert title.evaluate("el => el.scrollHeight <= el.clientHeight + 1")
            assert title.evaluate("el => el.scrollWidth <= el.clientWidth + 1")
            assert OWNER_TITLE[-12:] in title.inner_text()

            # Empty context emits no invented Reads fact.
            reads = workspace.locator(".thought-note-reads")
            assert reads.count() == 0
            assert page.get_by_text("Attached", exact=False).count() == 0
            page.screenshot(path=str(SHOTS / f"after-{width}.png"), full_page=False)

            # Add a note opens an in-window context well.
            if width < 720:
                workspace.get_by_role("button", name="More actions", exact=True).click()
                assert page.get_by_role("menuitem", name="Ask about this note", exact=True).is_visible()
                page.get_by_role("menuitem", name="Add a note", exact=True).click()
            else:
                _note_action(page, workspace, "Add a note")
            well = page.get_by_role("region", name="Add notes", exact=True)
            well.wait_for(timeout=10000)
            assert well.evaluate("el => el.closest('.thought-workspace-window') !== null")
            assert well.evaluate(
                "el => [...el.querySelectorAll('button')].filter(node => "
                "!node.matches('.btn, [class*=\"desk-\"], [class*=\"surface-\"], [class*=\"gadget-\"]')).length"
            ) == 0
            well.get_by_role("textbox", name="Add notes", exact=True).fill("Team context")
            token = well.get_by_role("checkbox", name="Team context", exact=True)
            token.wait_for(state="attached", timeout=10000)
            chosen = token.get_attribute("aria-label")
            assert chosen, "the well drew a control with no name"
            # The token variant's own face takes the click (the input is its
            # state, not its target) — the owner presses the named token.
            well.locator("label.gadget-check-token").first.click()
            page.wait_for_function(
                "name => document.querySelector('.thought-note-reads')?.textContent?.includes(name)",
                arg=chosen,
                timeout=10000,
            )
            # The receipt is said ONCE, and it is never clipped at either width.
            assert workspace.locator(".thought-note-reads").count() == 1
            assert workspace.locator(".thought-note-reads").evaluate("el => el.scrollWidth <= el.clientWidth + 1")
            # …and the kept state keeps its own place beside it (the foot
            # stacks at 393 rather than pushing a fact off the glass).
            kept = workspace.locator(KEPT_LINE)
            assert KEPT_WORDS.match(kept.inner_text().strip()), kept.inner_text()
            kept_box = kept.bounding_box()
            assert kept_box and kept_box["width"] > 20, kept_box
            _in_frame(kept_box, workspace.bounding_box(), "kept receipt")
            assert page.get_by_text(f"Attached {chosen}", exact=True).count() == 0
            well.press("Escape")
            assert page.get_by_role("region", name="Add notes", exact=True).count() == 0
            _no_horizontal_escape(page)
            page.screenshot(path=str(SHOTS / f"after-change-{width}.png"), full_page=False)

            # ── Ask: the question and its pad are in frame, no tab to find ──
            _refine_note(page, thought["id"])
            band = page.get_by_role("region", name="Ask about this note", exact=True)
            page.get_by_text(QUESTION, exact=True).wait_for(timeout=20000)
            answer = page.get_by_role("textbox", name="Your answer")
            answer.wait_for()
            page.screenshot(path=str(SHOTS / f"after-ask-{width}.png"), full_page=False)
            window_box = workspace.bounding_box()
            assert window_box
            _in_frame(answer.bounding_box(), window_box, "answer pad")
            _in_frame(band.locator(".thought-note-ask-text").bounding_box(), window_box, "question")
            # A box inside a scrolled band still HAS a box: the band itself
            # must not need scrolling to reach the pad and its one verb.
            assert band.evaluate("el => el.scrollHeight <= el.clientHeight + 1")
            _in_frame(workspace.locator(".surface-footer").bounding_box(), window_box, "foot")
            assert band.get_by_test_id("engine-line").inner_text().startswith("Thought Glass Engine")
            assert workspace.locator(".gadget-chip-egress").count() >= 1
            assert workspace.locator(".btn--primary:visible").count() == 1
            _no_empty_heading(page)
            _no_horizontal_escape(page)

            # ── One verb under the pad: the answer joins the note ──
            assert band.get_by_role("button", name="Add to note", exact=True).count() == 1
            assert band.get_by_role("button", name="Add & ask next").count() == 0
            answer.fill("Mina reads the plan differently. The freeze date settles it.")
            band.get_by_role("button", name="Add to note", exact=True).click()
            workspace.get_by_role("region", name="Note", exact=True).get_by_text(
                "Mina reads the plan differently.", exact=False
            ).wait_for(timeout=20000)
            # The question band disappears after its answer joins the note.
            band.wait_for(state="detached", timeout=20000)
            assert page.get_by_role("textbox", name="Your answer").count() == 0
            assert page.get_by_text("Added to Note", exact=False).count() == 0
            assert workspace.locator(".cm-thought-answer-reveal").count() >= 1
            _no_empty_heading(page)
            page.screenshot(path=str(SHOTS / f"after-add-{width}.png"), full_page=False)

            # ── Astra finding 2 on the real hub: Finish with an UNADDED
            #    answer adds it first and then keeps, with no cursor conflict ──
            _refine_note(page, thought["id"])
            page.get_by_text(QUESTION, exact=True).wait_for(timeout=20000)
            second = page.get_by_role("textbox", name="Your answer")
            second.fill("The freeze date is the fact that settles it.")
            responses.clear()
            workspace.locator(".btn--primary:visible").click()
            workspace.get_by_role("button", name="Resume", exact=True).wait_for(timeout=20000)
            completions = [status for path, status in responses if path.endswith("/complete")]
            assert completions and all(status < 300 for status in completions), (completions, responses)
            assert not [status for _p, status in responses if status == 409], responses
            kept_note = _api(page, "GET", f"/api/thoughts/{thought['id']}")["thought"]
            assert "The freeze date is the fact that settles it." in kept_note["working_note"]["body_markdown"]
            assert kept_note["state"] == "completed", kept_note["state"]

            # ── …and the finished note is found again, and reopens ──
            page.goto(f"{url}/?token={NOTE_TOKEN}&open=note%3A{note_id}", wait_until="load")
            workspace = page.locator(".desk-window.thought-workspace-window")
            workspace.wait_for(timeout=15000)
            # The hub's write time remains visible; Resume carries state.
            assert KEPT_WORDS.match(workspace.locator(KEPT_LINE).inner_text().strip())
            assert workspace.locator('.surface-footer-receipt-line[data-line="filing"]').count() == 0
            assert page.get_by_role("region", name="Ask about this note", exact=True).count() == 0
            workspace.get_by_role("region", name="Note", exact=True).get_by_text(
                "Mina reads the plan differently.", exact=False
            ).wait_for(timeout=15000)
            resume = workspace.get_by_role("button", name="Resume", exact=True)
            resume.wait_for(timeout=15000)
            # A finished note names WHY it cannot be typed into, then resumes.
            assert workspace.locator(".thought-note-title.is-locked").count() == 1
            resume.click()
            workspace.get_by_role("button", name="Finish", exact=True).wait_for(timeout=20000)
            assert workspace.locator(".thought-note-title.is-locked").count() == 0
            assert workspace.get_by_role("button", name="Edit Title", exact=True).count() == 1

            # ── No engine: one row, one true token, one verb ──
            _api(page, "POST", "/api/inference/assignments/clear", {
                "command_id": str(uuid.uuid4()), "expected_revision": 1,
                "scope": {"kind": "capability", "capability_id": "thought.interview"},
                "capability_id": "thought.interview",
            })
            page.goto(f"{url}/?token={NOTE_TOKEN}&open=note%3A{note_id}", wait_until="load")
            workspace = page.locator(".desk-window.thought-workspace-window")
            workspace.wait_for(timeout=15000)
            band = page.get_by_role("region", name="Ask about this note", exact=True)
            band.wait_for(timeout=15000)
            band.get_by_role("button", name="Choose engine", exact=True).wait_for(timeout=15000)
            assert "No engine" in band.inner_text()
            assert band.get_by_role("button", name="Ask", exact=True).count() == 0
            assert workspace.locator(".btn--primary:visible").count() == 1
            _no_empty_heading(page)
            _no_horizontal_escape(page)
            page.screenshot(path=str(SHOTS / f"no-engine-{width}.png"), full_page=False)

            assert engine.calls >= 1
            assert not errors, errors
            unexpected = [message for message in console_errors if "409 (Conflict)" not in message]
            assert not unexpected, console_errors
            browser.close()
    finally:
        server.stop()


@pytest.mark.e2e
@pytest.mark.requires_meeting
@pytest.mark.parametrize("width", [1440, 393])
def test_thought_note_long_note_and_long_question_never_clip(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int
) -> None:
    """A 2000-word note and a long question keep bands 3 and 4 reachable."""
    from playwright.sync_api import sync_playwright

    server, url, _provider, _engine = _boot(tmp_path, monkeypatch)
    long_title = "A very long dictated title that keeps going " * 3
    long_body = f"The {LONG_WORD} moved again. " * 400  # ~2000 words
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": width, "height": 900})
            page.emulate_media(reduced_motion="reduce")
            page.goto(f"{url}/?token={NOTE_TOKEN}", wait_until="load")
            _api(page, "POST", "/api/desk/seed")
            _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"})
            thought = _seed(page, long_title.strip(), long_body)
            page.goto(f"{url}/?token={NOTE_TOKEN}&open=note%3A{thought['working_note']['id']}", wait_until="load")

            workspace = page.locator(".desk-window.thought-workspace-window")
            workspace.wait_for(timeout=15000)
            workspace.get_by_role("region", name="Note", exact=True).wait_for()
            assert workspace.get_by_role("region", name="Ask about this note", exact=True).count() == 0
            window_box = workspace.bounding_box()
            assert window_box
            _in_frame(workspace.locator(".surface-footer").bounding_box(), window_box, "foot under a long note")
            title = workspace.locator(".thought-note-title")
            assert title.evaluate("el => el.scrollHeight <= el.clientHeight + 1")
            # The note owns the scroll; the window itself never scrolls away.
            assert workspace.locator(".thought-note-body .cm-scroller").evaluate(
                "el => el.scrollHeight > el.clientHeight"
            )
            _no_horizontal_escape(page)

            _refine_note(page, thought["id"])
            band = page.get_by_role("region", name="Ask about this note", exact=True)
            page.get_by_text(LONG_QUESTION, exact=True).wait_for(timeout=20000)
            answer = page.get_by_role("textbox", name="Your answer")
            answer.wait_for()
            assert answer.is_visible()
            window_box = workspace.bounding_box()
            assert window_box
            page.screenshot(path=str(SHOTS / f"long-question-{width}.png"), full_page=False)
            _in_frame(answer.bounding_box(), window_box, "answer pad under a long question")
            _in_frame(workspace.locator(".surface-footer").bounding_box(), window_box, "foot under a long question")
            assert band.evaluate("el => el.scrollHeight <= el.clientHeight + 1")
            assert band.get_by_role("button", name="Add to note", exact=True).is_visible()
            _no_horizontal_escape(page)
            _no_empty_heading(page)
            browser.close()
    finally:
        server.stop()


LONG_CONTEXT = (
    "A very long piece of everyday context that the owner keeps for his team "
    "and for its many standing decisions about the freeze"
)


@pytest.mark.e2e
@pytest.mark.requires_meeting
@pytest.mark.parametrize("width", [1440, 393])
def test_thought_note_long_context_and_open_well_never_clip(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int
) -> None:
    """Astra finding 5: a long context name pushed Finish off the window."""
    from playwright.sync_api import sync_playwright

    server, url, _provider, _engine = _boot(tmp_path, monkeypatch)
    SHOTS.mkdir(parents=True, exist_ok=True)
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": width, "height": 900})
            page.emulate_media(reduced_motion="reduce")
            page.goto(f"{url}/?token={NOTE_TOKEN}", wait_until="load")
            _api(page, "POST", "/api/desk/seed")
            _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"})
            _api(page, "POST", "/api/notes", {"title": LONG_CONTEXT, "body_markdown": "The freeze holds.", "tags": []})
            thought = _seed(page, OWNER_TITLE, OWNER_BODY)
            page.goto(f"{url}/?token={NOTE_TOKEN}&open=note%3A{thought['working_note']['id']}", wait_until="load")

            workspace = page.locator(".desk-window.thought-workspace-window")
            workspace.wait_for(timeout=15000)
            _note_action(page, workspace, "Add a note")
            well = page.get_by_role("region", name="Add notes", exact=True)
            well.wait_for(timeout=10000)

            # The well SEARCHES the desk, not just six recent notes.
            find = well.get_by_role("textbox", name="Add notes", exact=True)
            find.fill("standing decisions")
            token = well.locator("label.gadget-check-token", has_text="standing decisions")
            token.first.wait_for(timeout=10000)
            token.first.click()
            page.wait_for_function(
                "name => document.querySelector('.thought-note-reads')?.title?.includes(name)",
                arg="standing decisions",
                timeout=10000,
            )

            window_box = workspace.bounding_box()
            assert window_box
            page.screenshot(path=str(SHOTS / f"long-context-open-well-{width}.png"), full_page=False)
            # Nothing the owner must press leaves the window…
            visible_verbs = ("Add a note", "Finish") if width > 720 else ("More actions", "Finish")
            for name in visible_verbs:
                box = workspace.get_by_role("button", name=name, exact=True).bounding_box()
                assert box, name
                assert box["x"] + box["width"] <= window_box["x"] + window_box["width"] + 1, (name, box, window_box)
                _in_frame(box, window_box, name)
            # …the kept state keeps its width…
            kept = workspace.locator(KEPT_LINE)
            kept_box = kept.bounding_box()
            assert kept_box and kept_box["width"] > 20, kept_box
            # …the whole context NAME is readable, at both widths: it wraps
            # instead of ellipsizing (Astra round 2 — a hover title is no
            # help on a touch screen), and nothing of it is cut off.
            reads = workspace.locator(".thought-note-reads")
            _reads_full(reads, LONG_CONTEXT)
            token_face = well.locator("label.gadget-check-token .gadget-check-token-face").first
            _reads_full(token_face, LONG_CONTEXT)
            # …and the OPEN well fits its own container at both widths.
            well_box = well.bounding_box()
            assert well_box and well_box["width"] <= window_box["width"] + 1, (well_box, window_box)
            assert well.evaluate("el => el.scrollWidth <= el.clientWidth + 1")
            _in_frame(well_box, window_box, "open well")
            _no_horizontal_escape(page)

            # …and with the well closed, the ordinary face keeps the whole
            # name readable in the foot, with the verbs in their places.
            well.press("Escape")
            assert page.get_by_role("region", name="Add notes", exact=True).count() == 0
            _reads_full(workspace.locator(".thought-note-reads"), LONG_CONTEXT)
            window_box = workspace.bounding_box()
            assert window_box
            for name in visible_verbs:
                _in_frame(workspace.get_by_role("button", name=name, exact=True).bounding_box(), window_box, name)
            kept_box = workspace.locator(KEPT_LINE).bounding_box()
            assert kept_box and kept_box["width"] > 20, kept_box
            _no_horizontal_escape(page)
            page.screenshot(path=str(SHOTS / f"long-context-{width}.png"), full_page=False)
            browser.close()
    finally:
        server.stop()


# ── the custody walk (was tests/e2e/test_hs141_thought_workbench_glass.py) ──
# The band composition is fenced above; this walk owns the CUSTODY half: a
# durable Note edit made while the AI runs suppresses the frozen question;
# the working save is 409-then-200 under the write fence; the raw capture
# never leaves the hub; a service restart never redispatches settled work.

WORKBENCH_TOKEN = "hs141-workbench-glass"


class _InterviewEngine:
    active_provider = "deterministic-thought-interview"

    def __init__(self) -> None:
        self.calls = 0
        self.block_next = False
        self.started = threading.Event()
        self.release = threading.Event()

    def run_prompt(self, *, user_prompt: str, **_kwargs: object) -> str:
        self.calls += 1
        assert "Launch ownership" in user_prompt
        if self.block_next:
            self.block_next = False
            self.started.set()
            assert self.release.wait(10), "blocked interview engine was never released"
            return ('{"kind":"question","question":"STALE QUESTION MUST NOT APPEAR",'
                    '"reason":"This result belongs to the pre-edit Note."}')
        return ('{"kind":"question","question":"Who owns the launch?",'
                '"reason":"A named owner makes the Note actionable."}')


def _workbench_api(page: Any, method: str, path: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
    result = page.evaluate(
        """async ([method, path, body]) => {
          const response = await fetch(path, {
            method,
            headers: {
              authorization: 'Bearer hs141-workbench-glass',
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


def _window_inside_worktop(page: Any, workspace: Any) -> dict[str, float]:
    """Measure the live chrome and Dock, rather than an obsolete top inset."""
    _settle(page)
    box = workspace.bounding_box()
    bounds = page.evaluate("""() => {
      const bar = document.querySelector('.desk-menubar').getBoundingClientRect();
      const dock = document.querySelector('.desk-dock').getBoundingClientRect();
      return {top:bar.bottom, bottom:dock.top, width:innerWidth};
    }""")
    assert box and box["width"] > 0 and box["height"] > 0, box
    assert bounds["top"] - 1 <= box["y"], (box, bounds)
    assert box["y"] + box["height"] <= bounds["bottom"] + 1, (box, bounds)
    assert 0 <= box["x"] and box["x"] + box["width"] <= bounds["width"] + 1, (box, bounds)
    return box


@pytest.mark.e2e
@pytest.mark.requires_meeting
@pytest.mark.parametrize("width", [1440, 393])
def test_thought_workbench_real_glass(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int) -> None:
    _ensure_build()
    from playwright.sync_api import sync_playwright
    import json
    import holdspeak.config as config_module
    import holdspeak.db.core as db_core
    from holdspeak.db import reset_database
    from holdspeak.kernel.runtime import _configure
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks
    from types import SimpleNamespace
    from tests.unit.test_phase143_inference_assignments import OWNER, _profile, _result_claim

    home = tmp_path / "home"
    home.mkdir()
    model = tmp_path / "deterministic-this-machine.gguf"
    model.touch()
    browser_cache = Path(os.environ.get("PLAYWRIGHT_BROWSERS_PATH", Path.home() / "Library/Caches/ms-playwright"))
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("PLAYWRIGHT_BROWSERS_PATH", str(browser_cache))
    monkeypatch.setattr(config_module, "CONFIG_FILE", home / ".holdspeak" / "config.json")
    monkeypatch.setattr(db_core, "DEFAULT_DB_PATH", tmp_path / "holdspeak.db")
    provider = {"path": str(model)}
    monkeypatch.setattr("holdspeak.intel.providers.configured_local_meeting_model_path", lambda: provider["path"])
    reset_database()
    database = db_core.get_database()
    engine = _InterviewEngine()
    broker = _configure(database)
    monkeypatch.setattr(broker.inference_runner, "_engine_factory", lambda _revision, **_kw: engine)
    _profile(database, "workbench-interview", claims=(
        "language", "structured_output", _result_claim("thought.interview"), _result_claim("speech.intent_classify"),
    ), boundary="same_device")
    broker.inference_adoption_service.migrate_legacy_config(OWNER, SimpleNamespace(
        thoughts=SimpleNamespace(inference_target_id="workbench-interview"),
        dictation=SimpleNamespace(runtime=SimpleNamespace(profile_id="workbench-interview")),
    ))
    callbacks = WebRuntimeCallbacks(on_bookmark=lambda *_: None, on_stop=lambda: None, get_state=lambda: {})
    server = MeetingWebServer(callbacks, auth_token=WORKBENCH_TOKEN)
    url = server.start()
    errors: list[str] = []
    console_errors: list[str] = []
    requests: list[str] = []
    responses: list[tuple[str, int]] = []
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": width, "height": 900})
            page.emulate_media(reduced_motion="reduce")
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.on("console", lambda message: console_errors.append(message.text) if message.type == "error" else None)
            page.on("request", lambda request: requests.append(request.url) if "/api/thoughts/" in request.url else None)
            page.on("response", lambda response: responses.append((response.url, response.status)) if "/api/thoughts/" in response.url else None)
            page.goto(f"{url}/?token={WORKBENCH_TOKEN}", wait_until="load")
            _workbench_api(page, "POST", "/api/desk/seed")
            _workbench_api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"})
            created = _workbench_api(page, "POST", "/api/thoughts", {
                "request_id": str(uuid.uuid4()),
                "raw_text": "RAW CUSTODY PHRASE — launch ownership first capture.",
                "source": {"kind": "typed"},
                "initial_note": {
                    "title": "Launch ownership",
                    "body_markdown": "Launch ownership needs one accountable person.",
                    "tags": ["launch"],
                },
            })
            thought = created["thought"]
            page.evaluate(
                "([id, receipt]) => sessionStorage.setItem(`hs.thought.default-context-receipt.${id}`, JSON.stringify(receipt))",
                [thought["id"], created["default_context_receipt"]],
            )
            page.goto(f"{url}/?token={WORKBENCH_TOKEN}&open=note%3A{thought['working_note']['id']}", wait_until="load")

            workspace = page.locator(".desk-window.thought-workspace-window")
            try:
                workspace.wait_for(timeout=10000)
            except Exception:
                page.screenshot(path=f"/tmp/holdspeak-thought-workbench-open-failure-{width}.png", full_page=False)
                raise AssertionError({"body": page.locator("body").inner_text(), "errors": errors,
                                      "console": console_errors, "requests": requests})
            page.get_by_role("region", name="Note", exact=True).wait_for()

            def start_refinement() -> dict[str, Any]:
                latest = _workbench_api(page, "GET", f"/api/thoughts/{thought['id']}")["thought"]
                projection = _workbench_api(page, "GET", f"/api/thoughts/{thought['id']}/workbench")
                _workbench_api(page, "POST", f"/api/thoughts/{thought['id']}/refine", {
                    "request_id": str(uuid.uuid4()),
                    "expected_aggregate_revision": latest["aggregate_revision"],
                    "expected_working_revision": latest["working_revision"],
                    "expected_attachment_revision": latest["attachment_revision"],
                    "workspace_cursor": projection["workspace_cursor"],
                })
                return projection["workspace_cursor"]

            # Idle Note Ask opens Ask AI. The real refinement producer seeds
            # this retained in-note continuation, whose live UI owns Stop/answer.
            engine.block_next = True
            prior_cursor = start_refinement()
            page.reload(wait_until="load")
            band = page.get_by_role("region", name="Ask about this note", exact=True)
            band.wait_for(timeout=10000)
            band.get_by_role("button", name="Stop", exact=True).wait_for(timeout=10000)
            assert workspace.locator(".btn--primary:visible").count() == 1
            assert workspace.locator(".btn--primary:visible").inner_text().strip() == "Finish"
            assert page.get_by_text("Good enough").count() == 0
            assert page.get_by_text("Keep refining").count() == 0
            assert page.get_by_text("Finish instead").count() == 0
            # Doctrine (a): the rail, the tabs and the second pane left this
            # window with the story-12 design; their absence is the proof.
            assert workspace.get_by_role("toolbar", name="Markdown formatting").count() == 0
            assert workspace.get_by_role("region", name="Interview", exact=True).count() == 0
            assert workspace.get_by_role("button", name="Info", exact=True).count() == 0

            window_box = _window_inside_worktop(page, workspace)
            note_box = page.get_by_role("region", name="Note", exact=True).bounding_box()
            band_box = band.bounding_box()
            foot_box = workspace.locator(".surface-footer").bounding_box()
            assert note_box and band_box and foot_box
            # One column, four bands, in order, all inside the window.
            assert note_box["y"] + note_box["height"] <= band_box["y"] + 1
            assert band_box["y"] + band_box["height"] <= foot_box["y"] + 1
            assert foot_box["y"] + foot_box["height"] <= window_box["y"] + window_box["height"] + 1
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
            assert page.evaluate("document.body.scrollWidth <= innerWidth")
            page.screenshot(path=f"/tmp/holdspeak-thought-workbench-idle-{width}.png", full_page=False)

            # A real durable Note edit while ASKING must suppress the frozen
            # result. The stale question never reaches owner-visible state.
            page.wait_for_function(
                "el => el?.textContent?.trim() === 'Stop'",
                arg=band.get_by_role("button", name="Stop", exact=True).element_handle(),
                timeout=10000,
            )
            assert engine.started.wait(5)
            # Replay the real pre-turn cursor once. The hub rejects that
            # cursor itself; the writer must re-read and save the same edit.
            stale_cursor_sent = False

            def stale_first_save(route: Any) -> None:
                nonlocal stale_cursor_sent
                if stale_cursor_sent:
                    route.continue_()
                    return
                stale_cursor_sent = True
                body = route.request.post_data_json
                body["workspace_cursor"] = prior_cursor
                route.continue_(post_data=json.dumps(body))

            page.route(f"**/api/thoughts/{thought['id']}/working", stale_first_save)
            note_editor = page.get_by_role("textbox", name="Note body")
            assert note_editor.get_attribute("contenteditable") == "true"
            note_editor.click()
            page.keyboard.press("Meta+ArrowDown")
            page.keyboard.press("Enter")
            page.keyboard.insert_text("Edited while asking.")
            assert "Edited while asking." in note_editor.inner_text()
            page.keyboard.press("Control+s")
            deadline = time.time() + 5
            edited = _workbench_api(page, "GET", f"/api/thoughts/{thought['id']}")["thought"]
            while "Edited while asking." not in edited["working_note"]["body_markdown"] and time.time() < deadline:
                time.sleep(0.05)
                edited = _workbench_api(page, "GET", f"/api/thoughts/{thought['id']}")["thought"]
            assert "Edited while asking." in edited["working_note"]["body_markdown"]
            working_statuses = [status for path, status in responses if path.endswith(f"/api/thoughts/{thought['id']}/working")]
            assert working_statuses[-2:] == [409, 200], working_statuses
            engine.release.set()
            page.wait_for_function("""async ([id, token]) => {
              const response = await fetch(`/api/thoughts/${id}/workbench`, {headers:{authorization:`Bearer ${token}`}});
              const projection = await response.json();
              return !['reserved','in_flight','awaiting_projection'].includes(projection.workspace_state);
            }""", arg=[thought["id"], WORKBENCH_TOKEN], timeout=20000)
            assert page.get_by_text("STALE QUESTION MUST NOT APPEAR", exact=True).count() == 0

            # ── The one question, answered with the one verb ──
            start_refinement()
            page.reload(wait_until="load")
            try:
                page.get_by_text("Who owns the launch?", exact=True).wait_for(timeout=20000)
            except Exception as cause:
                raise AssertionError({"calls": engine.calls, "workbench": _workbench_api(page, "GET", f"/api/thoughts/{thought['id']}/workbench"),
                                      "body": workspace.inner_text(), "errors": errors}) from cause
            answer = page.get_by_role("textbox", name="Your answer")
            answer.fill("Mina owns the launch.")
            page.screenshot(path=f"/tmp/holdspeak-thought-workbench-question-{width}.png", full_page=False)
            assert band.get_by_role("button", name="Add to note", exact=True).count() == 1
            assert band.get_by_role("button", name="Add & ask next").count() == 0
            assert workspace.locator(".btn--primary:visible").count() == 1
            band.get_by_role("button", name="Add to note", exact=True).click()
            page.get_by_role("region", name="Note", exact=True).get_by_text("Mina owns the launch.").wait_for(timeout=20000)
            assert workspace.locator(".thought-note-body .cm-scroller").evaluate("el => el.scrollWidth <= el.clientWidth + 1")
            # The answer is a pure write: no second turn was dispatched.
            time.sleep(0.35)
            assert engine.calls == 2, engine.calls

            # Raw capture stays on the hub: this window never asks for it.
            assert page.get_by_text("RAW CUSTODY PHRASE — launch ownership first capture.", exact=True).count() == 0
            assert not any(path.endswith(f"/api/thoughts/{thought['id']}/original") for path in requests)

            # The Reads well is in-window (no portal overlay) and Escape-safe.
            if width < 720:
                workspace.get_by_role("button", name="More actions", exact=True).click()
                change = page.get_by_role("menu", name="More actions", exact=True).get_by_role("menuitem", name="Add a note", exact=True)
            else:
                change = workspace.get_by_role("button", name="Add a note", exact=True)
            change.click()
            well = page.get_by_role("region", name="Add notes", exact=True)
            well.wait_for(timeout=10000)
            assert well.evaluate("el => el.closest('.thought-workspace-window') !== null")
            window_box = _window_inside_worktop(page, workspace)
            well_box = well.bounding_box()
            assert well_box and well_box["y"] + well_box["height"] <= window_box["y"] + window_box["height"] + 1
            page.screenshot(path=f"/tmp/holdspeak-thought-context-well-{width}.png", full_page=False)
            well.press("Escape")
            assert page.get_by_role("region", name="Add notes", exact=True).count() == 0
            return_name = "More actions" if width < 720 else "Add a note"
            return_door = workspace.get_by_role("button", name=return_name, exact=True)
            try:
                page.wait_for_function("el => el.isConnected && el === document.activeElement", arg=return_door.element_handle(), timeout=5000)
            except Exception as cause:
                active = page.evaluate("() => ({tag:document.activeElement?.tagName, name:document.activeElement?.getAttribute('aria-label'), class:document.activeElement?.className})")
                page.screenshot(path=f"/tmp/holdspeak-thought-context-return-failure-{width}.png", full_page=False)
                raise AssertionError({"expected_focus": return_name, "active": active}) from cause
            assert return_door.is_visible()
            assert page.get_by_role("menu", name="More actions", exact=True).count() == 0

            unexpected_before_restart = [
                message for message in console_errors
                if "server responded with a status of 409 (Conflict)" not in message
            ]
            assert not unexpected_before_restart, console_errors
            console_errors.clear()

            # Restart the real HTTP service on the same durable isolated HOME.
            # Reloading must project the settled work, never redispatch it.
            restart_port = server.port
            server.stop()
            server = MeetingWebServer(callbacks, port=restart_port, auth_token=WORKBENCH_TOKEN)
            assert server.start() == url
            page.reload(wait_until="load")
            page.locator(".desk-window.thought-workspace-window").wait_for(timeout=10000)
            page.get_by_role("region", name="Note", exact=True).get_by_text("Mina owns the launch.").wait_for()
            time.sleep(0.35)
            assert engine.calls == 2, "service restart redispatched settled work"
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
            workspace = page.locator(".desk-window.thought-workspace-window")
            assert workspace.locator(".btn--primary:visible").count() == 1
            page.screenshot(path=f"/tmp/holdspeak-thought-workbench-{width}.png", full_page=False)

            # The workbench read is one bounded projection, and no page/console
            # exception or horizontal escape is hidden by the screenshot.
            assert sum(path.endswith(f"/api/thoughts/{thought['id']}/workbench") for path in requests) >= 1
            assert not errors, errors
            unexpected_console = [
                message for message in console_errors
                if "ERR_CONNECTION_REFUSED" not in message
            ]
            assert not unexpected_console, console_errors
            browser.close()
    finally:
        server.stop()


# ═══ merged from the e2e-high-2 lane ═══
# The Thought app, AS RENDERED: what only a real browser proves of a thought.
#
# Owner, 2026-10-12 (push 2 of the test diet): a browser test only for drag,
# focus, keys, touch, hover or an exact geometry relation. Through the real hub
# on an isolated HOME at 1440x900 (keyboard):
#
# * ⌃T from a body window (focus on its title bar, in no field) opens a new
#   Thought window: one key press, one POST /api/notes.
# * The key does not fire inside a text field that owns it: with focus in the
#   Thought window's note (⌃T is the editor's own key) and in the palette's
#   search field, ⌃T writes no note. (jsdom lies about focus, so this fence is
#   on glass.)
#
# Cheaper successors of the rest of PHILO-13-16 (C6): the verb, its ⌃T keycap
# and the title rule in web/src/desk/__tests__/philo1316Capture.test.tsx; the
# 393 menu row in web/src/desk/components/window/phoneRing.test.tsx; a thought
# found by its own words in web/src/desk/__tests__/palette.philo1314.test.tsx;
# clip and overlap of the Thought window in the desk sweep.
pytest.importorskip("playwright.sync_api", reason="the Thought glass needs Playwright")


K_TOKEN = "thought-glass"
THOUGHT = ".desk-window.thought-workspace-window"


class TestThoughtKeys:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        _ensure_build()
        server, base = _gi_boot(tmp_path, monkeypatch, token=K_TOKEN)
        self.base = base
        try:
            yield
        finally:
            server.stop()

    def test_ctrl_t_opens_one_thought_and_never_inside_a_field(self) -> None:
        """replaces: tests/e2e/test_philo13_16_capture_glass.py::TestCaptureFromAnywhere::test_a_thought_from_anywhere_titled_by_its_words
        (the key and focus legs, 1440)."""
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True, args=["--disable-smooth-scrolling"])
            page = browser.new_context(viewport={"width": 1440, "height": 900}, device_scale_factor=1).new_page()
            page.set_default_timeout(30_000)
            errors: list[str] = []
            notes: list[str] = []
            page.on("pageerror", lambda e: errors.append(str(e)[:200]))
            page.on("request", lambda r: notes.append(r.url)
                    if r.method == "POST" and r.url.split("?")[0].endswith("/api/notes") else None)
            try:
                page.goto(f"{self.base}/?token={K_TOKEN}", wait_until="load")
                _gi_api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=K_TOKEN)
                page.reload(wait_until="load")
                _normal_chair(page)
                page.wait_for_timeout(1200)
                _settle(page)

                # A body window first: Today from the Dock, focus on its title bar.
                page.locator(".desk-dock-launch[aria-label^='Today']").click()
                today = page.locator(".desk-window[aria-label='Today']")
                today.wait_for()
                page.wait_for_timeout(600)
                today.locator(".desk-window-title").first.click()
                focus = page.evaluate("() => document.activeElement.matches('input,textarea,[contenteditable=true]')")
                assert not focus, "focus is in a field before the key"
                page.keyboard.press("Control+t")  # ONE key press
                page.locator(THOUGHT).wait_for()
                assert len(notes) == 1, ("one press, one note", notes)

                # Inside the note ⌃T is the editor's own key (it swaps two letters).
                field = page.locator(f"{THOUGHT} .thought-note-body .cm-content").first
                field.wait_for()
                field.click()
                page.keyboard.type("Ask Priya about the ledger ADR")
                page.locator(f"{THOUGHT} .thought-note-title", has_text="Ask Priya about the ledger ADR").wait_for(timeout=15_000)
                assert page.evaluate("() => document.activeElement.closest('.cm-content') !== null"), "focus is not in the note"
                page.keyboard.press("Control+t")
                page.wait_for_timeout(1200)
                assert len(notes) == 1 and page.locator(THOUGHT).count() == 1, ("⌃T inside the note opened a thought", notes)
                page.locator(f"{THOUGHT} .desk-gadget-close").first.click()
                page.locator(THOUGHT).wait_for(state="detached")
                _settle(page)

                # Inside the palette's search field.
                page.locator("[aria-controls=desk-tool-shelf]").first.click()
                page.locator("[aria-controls=desk-palette-listbox]").focus()
                page.keyboard.press("Control+t")
                page.wait_for_timeout(1200)
                assert len(notes) == 1 and page.locator(THOUGHT).count() == 0, (
                    "⌃T inside the palette search opened a thought", notes)
                assert not [e for e in errors if "ResizeObserver" not in e], errors
            finally:
                browser.close()


# ── moved whole from tests/e2e/test_thought_opens_at_once_glass.py and the PHILO-17 thought-send glass ──
SIZES = {1440: 900, 393: 852}
T = 20_000
OPENS_TOKEN = "thought-glass-opens"
OPENS_SHOTS = evidence_dir("tests/e2e/shots/thought-opens-at-once")
READ_DELAY_MS = 4000
OPENS_WITHIN_MS = 1500
OPENS_WORDS = "Ask Priya about the ledger ADR"
SECOND = "Hire a second SRE before Q1"

SLOW_READ = """(() => {
  const real = window.fetch.bind(window);
  window.fetch = (input, init) => {
    const url = typeof input === 'string' ? input : (input && input.url) || '';
    const method = ((init && init.method) || 'GET').toUpperCase();
    if (method === 'GET' && /\\/api\\/roadmaps(\\?|$)/.test(url))
      return new Promise((r) => setTimeout(r, %d)).then(() => real(input, init));
    return real(input, init);
  };
})()""" % READ_DELAY_MS

IN_FRONT = """(sel) => {
  const w = document.querySelector(sel); if (!w) return false;
  const r = w.getBoundingClientRect();
  const hit = (x, y) => { const e = document.elementFromPoint(x, y); return !!e && w.contains(e); };
  return hit(r.left + 40, r.top + 12) && hit(r.left + r.width / 2, r.top + 12) && hit(r.left + r.width / 2, r.top + r.height / 2);
}"""


class TestTheThoughtOpensAtOnce:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        _ensure_build()
        server, base = _gi_boot(tmp_path, monkeypatch, token=OPENS_TOKEN)
        self.base = base
        try:
            yield
        finally:
            server.stop()

    def _page(self, pw: Any, width: int) -> tuple[Any, Any, list[str], list[str]]:
        browser = pw.chromium.launch(headless=True, args=["--disable-smooth-scrolling"])
        ctx = browser.new_context(viewport={"width": width, "height": SIZES[width]},
                                  device_scale_factor=1, has_touch=width < 720)
        page = ctx.new_page()
        page.set_default_timeout(30_000)
        errors: list[str] = []
        notes: list[str] = []
        page.on("pageerror", lambda e: errors.append(str(e)[:200]))
        page.on("request", lambda r: notes.append(r.url)
                if r.method == "POST" and r.url.split("?")[0].endswith("/api/notes") else None)
        page.goto(f"{self.base}/?token={OPENS_TOKEN}", wait_until="load")
        _gi_api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=OPENS_TOKEN)
        self.seeded = {n["id"] for n in _gi_api(page, "GET", "/api/notes", token=OPENS_TOKEN)["notes"]}
        page.add_init_script(SLOW_READ)
        page.reload(wait_until="load")
        _normal_chair(page)
        page.wait_for_timeout(READ_DELAY_MS + 1500)  # the first desk read lands
        _settle(page)
        return browser, page, errors, notes

    @staticmethod
    def _press(page: Any, loc: Any, width: int) -> None:
        loc.scroll_into_view_if_needed()
        if width < 720:
            box = loc.bounding_box()
            assert box, "nothing to tap"
            page.touchscreen.tap(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
        else:
            loc.click()

    def _menu_thought(self, page: Any, width: int) -> None:
        menu = "desk" if width >= 720 else "go"
        self._press(page, page.locator(f".desk-verbbar-item[data-menu-id='{menu}'] button"), width)
        if width < 720:  # PHILO-15 11 (B21): Go ▸ New ▸ Thought at 393
            go_group(page, "New", lambda loc: self._press(page, loc, width))
        label = "Write a thought" if width >= 720 else "Note"
        item = page.locator(f".desk-verbbar-menu [role='menuitem']:has-text('{label}')").first
        item.wait_for()
        self._press(page, item, width)

    @staticmethod
    def _opens(page: Any, what: str) -> None:
        try:
            page.locator(THOUGHT).wait_for(timeout=OPENS_WITHIN_MS)
        except Exception as exc:
            raise AssertionError(f"{what}: no Thought window inside {OPENS_WITHIN_MS} ms") from exc
        assert page.evaluate(IN_FRONT, THOUGHT), (what, "the Thought window is not in front")

    def _thought_notes(self, page: Any) -> list[dict[str, Any]]:
        """The notes this walk made (the hub seeds its own notes on a new HOME)."""
        return [n for n in _gi_api(page, "GET", "/api/notes", token=OPENS_TOKEN)["notes"]
                if not n.get("deleted") and n["id"] not in self.seeded]

    @pytest.mark.parametrize("width", list(SIZES))
    def test_one_press_one_window_every_key(self, width: int) -> None:
        """replaces: tests/e2e/test_thought_opens_at_once_glass.py::TestTheThoughtOpensAtOnce::test_one_press_one_window_every_key (moved whole)."""
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, errors, notes = self._page(pw, width)
            try:
                proof: dict[str, Any] = {"width": width}

                # Six presses, no words: one note, one window.
                for press in range(6):
                    self._menu_thought(page, width)
                    self._opens(page, f"press {press + 1} at {width}")
                    page.wait_for_timeout(400)
                assert len(notes) == 1, ("six presses made more than one note", notes)
                assert page.locator(THOUGHT).count() == 1, "six presses, more than one Thought window"
                kept = self._thought_notes(page)
                assert len(kept) == 1, kept
                proof["six_presses"] = {"notes_posted": len(notes), "notes_on_hub": len(kept)}
                page.screenshot(path=str(OPENS_SHOTS / f"six-presses-{width}.png"))
                self._press(page, page.locator(f"{THOUGHT} .desk-gadget-close").first, width)
                page.locator(THOUGHT).wait_for(state="detached")
                page.wait_for_timeout(READ_DELAY_MS + 1500)  # the desk reads land

                if width >= 720:
                    # ⌃T from a body window, then the words with no wait: every key lands.
                    self._press(page, page.locator(".desk-dock-launch[aria-label^='Today']"), width)
                    intel = page.locator(".desk-window[aria-label='Today']")
                    intel.wait_for()
                    page.wait_for_timeout(600)
                    intel.locator(".desk-window-title").first.click()
                    page.keyboard.press("Control+t")
                    page.keyboard.type(OPENS_WORDS)  # no wait: the window is not there yet
                    self._opens(page, "⌃T at 1440")
                else:
                    self._menu_thought(page, width)
                    self._opens(page, "the menu verb at 393")
                    field = page.locator(f"{THOUGHT} .thought-note-body .cm-content").first
                    field.wait_for()
                    self._press(page, field, width)
                    page.keyboard.type(OPENS_WORDS)
                field = page.locator(f"{THOUGHT} .thought-note-body .cm-content").first
                field.wait_for()
                page.wait_for_function(
                    "(sel) => document.activeElement && document.activeElement.matches(sel)",
                    arg=f"{THOUGHT} .thought-note-body .cm-content", timeout=5_000)
                page.wait_for_timeout(300)
                assert field.inner_text().strip() == OPENS_WORDS, ("keys were lost", field.inner_text())
                assert len(notes) == 1, ("the empty thought was not used again", notes)
                page.keyboard.type(" today")  # the next key continues the same line
                page.locator(f"{THOUGHT} .thought-note-title", has_text=OPENS_WORDS).wait_for(timeout=15_000)
                assert field.inner_text().strip() == f"{OPENS_WORDS} today", field.inner_text()
                proof["typed"] = field.inner_text().strip()
                page.wait_for_timeout(1500)
                page.screenshot(path=str(OPENS_SHOTS / f"every-key-{width}.png"))

                # With words in it, the next press makes a new thought.
                self._press(page, page.locator(f"{THOUGHT} .desk-gadget-close").first, width)
                page.locator(THOUGHT).wait_for(state="detached")
                self._menu_thought(page, width)
                self._opens(page, f"the second thought at {width}")
                assert len(notes) == 2, ("a thought with words was used again", notes)
                field = page.locator(f"{THOUGHT} .thought-note-body .cm-content").first
                field.wait_for()
                if width < 720:
                    self._press(page, field, width)
                page.keyboard.type(SECOND)
                page.locator(f"{THOUGHT} .thought-note-title", has_text=SECOND).wait_for(timeout=15_000)
                page.wait_for_timeout(1500)

                titles = sorted(n["title"] for n in self._thought_notes(page))
                proof["titles_on_hub"] = titles
                assert titles == sorted([f"{OPENS_WORDS} today", SECOND]), titles
                assert "Thought" not in titles, titles
                page.screenshot(path=str(OPENS_SHOTS / f"second-thought-{width}.png"))

                (OPENS_SHOTS / f"proof-{width}.txt").write_text(f"{proof}\n")
                real = [e for e in errors if "ResizeObserver" not in e]
                assert not real, real
            finally:
                browser.close()

    # Astra's condition on #790: the second thought started before the first was saved.
    @pytest.mark.parametrize("width", list(SIZES))
    def test_a_second_thought_before_the_save_is_its_own_note(self, width: int) -> None:
        """replaces: tests/e2e/test_thought_opens_at_once_glass.py::TestTheThoughtOpensAtOnce::test_a_second_thought_before_the_save_is_its_own_note (moved whole)."""
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, errors, notes = self._page(pw, width)
            try:
                self._menu_thought(page, width)
                self._opens(page, f"the first thought at {width}")
                field = page.locator(f"{THOUGHT} .thought-note-body .cm-content").first
                field.wait_for()
                if width < 720:
                    self._press(page, field, width)
                page.keyboard.type("First thought")
                # At once: no wait for the save, no close.
                self._menu_thought(page, width)
                page.keyboard.type("Second thought")
                page.wait_for_function(
                    "(sel) => document.querySelectorAll(sel).length === 2", arg=THOUGHT, timeout=OPENS_WITHIN_MS + 1000)
                page.locator(f"{THOUGHT} .thought-note-title", has_text="Second thought").wait_for(timeout=15_000)
                page.wait_for_timeout(2500)  # both saves land
                page.screenshot(path=str(OPENS_SHOTS / f"second-before-save-{width}.png"))
                assert len(notes) == 2, ("the second thought did not get its own note", notes)
                kept = sorted((n["title"], n["body_markdown"].strip()) for n in self._thought_notes(page))
                assert kept == [("First thought", "First thought"), ("Second thought", "Second thought")], kept
                real = [e for e in errors if "ResizeObserver" not in e]
                assert not real, real
            finally:
                browser.close()


SEND_TOKEN = "thought-glass-send"
SEND_SHOTS = evidence_dir("tests/e2e/shots/philo17-thought-send")
SEND_WORDS = "Pilot plan: we start on Monday and Avery owns the rollout"


class TestTheThoughtSends:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        _ensure_build()
        server, base = _gi_boot(tmp_path, monkeypatch, token=SEND_TOKEN)
        self.base = base
        self.home = tmp_path / "home"
        from holdspeak.db import get_database

        self.db = get_database()
        try:
            yield
        finally:
            server.stop()

    def _menu_thought(self, page: Any, width: int) -> None:
        menu = "desk" if width >= 720 else "go"
        page.locator(f".desk-verbbar-item[data-menu-id='{menu}'] button").click()
        if width < 720:
            go_group(page, "New", lambda loc: loc.click())
        label = "Write a thought" if width >= 720 else "Note"
        item = page.locator(f".desk-verbbar-menu [role='menuitem']:has-text('{label}')").first
        item.wait_for()
        item.click()

    @staticmethod
    def _tap(page: Any, loc: Any) -> None:
        """A real pointer press at the verb's place (an inert well takes no press)."""
        loc.scroll_into_view_if_needed()
        box = loc.bounding_box()
        assert box, "the well's Send is not on the glass"
        if box:
            page.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)

    def _db_sends(self, note_ref: str) -> list[dict[str, Any]]:
        """The real isolated hub's rows, including its frozen transport bytes."""
        import json

        with self.db._connection() as conn:
            rows = conn.execute(
                "SELECT id, state, payload, proof_json FROM channel_sends WHERE document_ref=? ORDER BY rowid",
                (note_ref,),
            ).fetchall()
        return [{"id": r[0], "state": r[1], "payload": r[2], "proof": json.loads(r[3] or "{}")} for r in rows]

    def _saved_note(self, note_ref: str) -> tuple[int, str]:
        with self.db._connection() as conn:
            row = conn.execute(
                "SELECT t.working_revision, n.body_markdown FROM refinement_thoughts t "
                "JOIN notes n ON n.id=t.working_note_id WHERE t.working_note_id=?",
                (note_ref.removeprefix("note:"),),
            ).fetchone()
        assert row, note_ref
        return row[0], row[1]

    def _note_action(self, page: Any, win: Any, width: int, name: str) -> Any:
        foot = win.locator(".thought-note-foot")
        if width < 720:
            self._tap(page, foot.get_by_role("button", name="More actions", exact=True))
            action = page.get_by_role("menu", name="More actions", exact=True).get_by_role("menuitem", name=name, exact=True)
        else:
            action = foot.get_by_role("button", name=name, exact=True)
        action.wait_for(timeout=T)
        return action

    def _back(self, page: Any, win: Any, width: int, *, keyboard: bool = False) -> None:
        """Use the phone's actual frame Back, or the desktop host's Back."""
        back = (win.locator(".desk-gadget-close") if width < 720
                else win.locator(".thought-send-foot").get_by_role("button", name="Back", exact=True))
        if keyboard:
            back.focus()
            page.keyboard.press("Enter")
        else:
            self._tap(page, back)
        win.locator(".thought-note-body .cm-content").wait_for(timeout=T)
        assert win.locator("[data-testid=thought-send]").count() == 0
        name = "More actions" if width < 720 else "Send"
        door = win.locator(".thought-note-foot").get_by_role("button", name=name, exact=True)
        page.wait_for_function("(el) => el.isConnected && el === document.activeElement", arg=door.element_handle(), timeout=T)
        assert door.is_visible()
        assert not page.get_by_role("menu", name="More actions", exact=True).count()

    @staticmethod
    def _send_geometry(page: Any, win: Any, width: int) -> None:
        from tests.e2e.test_send_glass import TARGETS44

        geo = win.evaluate("""(win) => {
          const well = win.querySelector('[data-testid=thought-send]');
          const outer = well.getBoundingClientRect();
          const box = (sel) => { const r = well.querySelector(sel).getBoundingClientRect();
            return {top:r.top, bottom:r.bottom, left:r.left, right:r.right, width:r.width, height:r.height}; };
          const payload = well.querySelector('[data-testid=send-preview-body]');
          return {outer:{top:outer.top, bottom:outer.bottom, left:outer.left, right:outer.right},
            preview:box('[data-testid=send-preview-body]'), verb:box('[data-testid=send-verb]'),
            overflow:getComputedStyle(well).overflowY,
            payloadOverflow:getComputedStyle(payload).overflowY, payloadMax:getComputedStyle(payload).maxHeight,
            nested:[...well.querySelectorAll('*')].filter((el) =>
              ['auto','scroll'].includes(getComputedStyle(el).overflowY) && el.scrollHeight > el.clientHeight + 1)
              .map((el) => el.className)};
        }""")
        assert geo["overflow"] in ("auto", "scroll"), geo
        assert not geo["nested"], geo
        assert geo["payloadOverflow"] not in ("auto", "scroll") and geo["payloadMax"] == "none", geo
        for name in ("preview", "verb"):
            box, outer = geo[name], geo["outer"]
            assert box["height"] > 0 and box["width"] > 0, geo
            assert outer["top"] - 1 <= box["top"] < box["bottom"] <= outer["bottom"] + 1, geo
            assert outer["left"] - 1 <= box["left"] < box["right"] <= outer["right"] + 1, geo
        if width < 720:
            # The existing nine-point probe also covers the host's Back control.
            targets = TARGETS44.replace(
                "[data-testid=send-well] button,",
                ".thought-send-foot button, .thought-workspace-window .desk-gadget-close, [data-testid=send-well] button,",
            )
            assert not page.evaluate(targets), "Send or Back loses part of its 44px target"
        assert not page.evaluate("document.documentElement.scrollWidth > window.innerWidth"), "page scrolls sideways"

    @pytest.mark.parametrize("width", list(SIZES))
    def test_write_a_thought_then_send_it_to_a_folder(self, width: int) -> None:
        """Clipboard, Back focus, exact saved revision, target geometry and real folder dispatch."""
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True, args=["--disable-smooth-scrolling"])
            ctx = browser.new_context(viewport={"width": width, "height": SIZES[width]}, device_scale_factor=1)
            ctx.grant_permissions(["clipboard-read", "clipboard-write"])
            page = ctx.new_page()
            page.set_default_timeout(30_000)
            errors: list[str] = []
            page.on("pageerror", lambda e: errors.append(str(e)[:200]))
            try:
                page.goto(f"{self.base}/?token={SEND_TOKEN}", wait_until="load")
                _gi_api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=SEND_TOKEN)
                page.reload(wait_until="load")
                _normal_chair(page)
                page.wait_for_timeout(1200)
                _settle(page)

                # The frame opens before its authoritative workbench read.
                # Hold that read to exercise the real early-typing gap.
                opening_reads: list[Any] = []
                def hold_opening_read(route: Any) -> None:
                    opening_reads.append(route)
                    page.evaluate("window.__thoughtOpeningReadHeld = true")

                page.route("**/api/thoughts/*/workbench", hold_opening_read)
                with page.expect_request("**/api/thoughts/*/workbench") as opening_request:
                    self._menu_thought(page, width)
                assert opening_request.value.method == "GET"
                win = page.locator(THOUGHT)
                win.wait_for()
                win.locator(".thought-workspace-opening[aria-busy=true]").wait_for()
                page.wait_for_function("window.__thoughtOpeningReadHeld === true", timeout=T)
                assert opening_reads, "the initial workbench read was not held"
                page.keyboard.type(SEND_WORDS)  # the opening key buffer owns these words

                foot = win.locator(".thought-note-foot")
                door = foot.get_by_role("button", name="More actions" if width < 720 else "Send", exact=True)
                opening = win.evaluate("""win => ({
                    loading: Boolean(win.querySelector('.thought-workspace-opening[aria-busy=true]')),
                    editor: Boolean(win.querySelector('.thought-note-body .cm-content')),
                    footer: Boolean(win.querySelector('.thought-note-foot')),
                    focused: document.activeElement?.getAttribute('aria-label')
                })""")
                (SEND_SHOTS / f"thought-send-opening-{width}.json").write_text(json.dumps(opening, indent=2) + "\n")
                page.screenshot(path=str(SEND_SHOTS / f"thought-send-opening-{width}.png"))
                assert opening["loading"] and not opening["editor"] and not opening["footer"], opening
                for route in opening_reads:
                    route.continue_()
                page.unroute("**/api/thoughts/*/workbench")
                # A frame is not an editable document. Let the authoritative
                # read mount Note and hand the buffered keys to its own field.
                note = win.locator(".thought-note-body .cm-content").first
                note.wait_for(timeout=T)
                page.wait_for_function("""([el, words]) => el.isConnected
                    && el.getAttribute('contenteditable') === 'true'
                    && el.innerText === words && document.activeElement === el""",
                    arg=[note.element_handle(), SEND_WORDS], timeout=T)
                door.wait_for(timeout=T)
                assert door.is_visible()
                opening["ready"] = note.evaluate("""el => ({body: el.innerText,
                    editable: el.getAttribute('contenteditable'), focused: document.activeElement === el})""")
                (SEND_SHOTS / f"thought-send-opening-{width}.json").write_text(json.dumps(opening, indent=2) + "\n")
                _settle(page)
                page.screenshot(path=str(SEND_SHOTS / f"thought-send-ready-{width}.png"))

                # Copy copies the working text.
                self._note_action(page, win, width, "Copy").click()
                foot.get_by_text("COPIED").wait_for(timeout=T)
                assert page.evaluate("navigator.clipboard.readText()") == SEND_WORDS

                # Keyboard Send saves first, then owns the body. No dispatch yet.
                send = self._note_action(page, win, width, "Send")
                send.focus()
                page.keyboard.press("Enter")
                well = win.locator("[data-testid=send-well][data-doc^='note:']")
                well.wait_for(timeout=T)
                note_ref = well.get_attribute("data-doc")
                assert note_ref
                win_id = win.get_attribute("id")
                opened = well.locator("[data-testid=send-open][data-destination='HoldSpeak folder']")
                opened.locator("[data-testid=send-preview]").wait_for(timeout=T)
                assert win.get_by_role("region", name="Send note", exact=True).evaluate(
                    "el => el === document.activeElement || el.contains(document.activeElement)"
                ), "keyboard Send left focus outside its body"
                preview = " ".join(opened.locator("[data-testid=send-preview]").inner_text().split())
                assert "Monday" in preview, preview
                assert not self._db_sends(note_ref)
                assert win.locator(".thought-note-body, .thought-note-ask, .thought-note-foot, .thought-reads-well, .thought-action-well").count() == 0
                assert win.get_by_role("button", name=re.compile(r"^(Finish|Resume|Copy|Task|Project)$")).count() == 0
                self._send_geometry(page, win, width)
                page.screenshot(path=str(SEND_SHOTS / f"thought-send-picked-{width}.png"))

                # Pointer Back returns to this note and restores its visible Send door.
                self._back(page, win, width)
                assert win.get_attribute("id") == win_id
                revision, saved_body = self._saved_note(note_ref)
                assert saved_body.strip() == SEND_WORDS, saved_body

                # Back -> edit -> Send: a held save cannot reopen an old preview.
                held: list[Any] = []
                mode = {"saves": "hold"}

                def saves(route: Any) -> None:
                    if mode["saves"] == "hold":
                        held.append(route)
                    elif mode["saves"] == "fail":
                        route.abort()
                    else:
                        route.continue_()

                page.route("**/api/thoughts/*/working", saves)
                note = win.locator(".thought-note-body .cm-content").first
                note.click()
                page.keyboard.press("End")
                page.keyboard.type(" REVISED")
                self._tap(page, self._note_action(page, win, width, "Send"))
                for _ in range(100):  # the writer's held save reaches the route
                    if held:
                        break
                    page.wait_for_timeout(50)
                assert held, "the edit was never saved"
                assert not self._db_sends(note_ref), "Send dispatched while the edit was not saved"
                assert win.locator("[data-testid=thought-send], [data-testid=send-preview], [data-testid=send-verb]").count() == 0
                if width >= 720:
                    assert foot.get_by_role("button", name="Send", exact=True).is_disabled()
                else:
                    assert foot.get_by_role("button", name="More actions", exact=True).get_attribute("aria-expanded") == "false"
                assert self._saved_note(note_ref) == (revision, saved_body)
                page.screenshot(path=str(SEND_SHOTS / f"thought-send-waits-{width}.png"))
                mode["saves"] = "pass"
                for route in held:
                    route.continue_()
                # Only the successfully saved revision opens a fresh preview.
                well.wait_for(timeout=T)
                page.wait_for_function(
                    "(sel) => (document.querySelector(sel)?.innerText || '').includes('REVISED')",
                    arg=f"{THOUGHT} [data-testid=send-open][data-destination='HoldSpeak folder'] [data-testid=send-preview]",
                    timeout=T)
                revised_body = f"{SEND_WORDS} REVISED"
                assert self._saved_note(note_ref) == (revision + 1, revised_body)
                self._send_geometry(page, win, width)

                # His press: the file is saved, the receipt names the path.
                verb = opened.locator("[data-testid=send-verb]")
                page.wait_for_function("(e) => e && !e.disabled", arg=verb.element_handle(), timeout=T)
                self._tap(page, verb)
                receipt = opened.locator("[data-receipt=latest][data-state=sent]")
                receipt.wait_for(timeout=T)
                sends = self._db_sends(note_ref)
                sent = [s for s in sends if s["state"] == "sent"]
                assert len(sent) == len(sends) == 1, sends
                path = Path(sent[0]["proof"]["path"])
                assert path.is_relative_to(self.home) and path.is_file(), path
                assert path.read_bytes() == sent[0]["payload"] and revised_body in path.read_text(), path
                text = " ".join(receipt.inner_text().split())
                # The built-in folder names its path from HOME (~).
                assert text == f"✓ SAVED ~/Documents/HoldSpeak/Sent/{path.name}", text
                receipt.scroll_into_view_if_needed()
                page.screenshot(path=str(SEND_SHOTS / f"thought-send-saved-{width}.png"))

                # Keyboard Back returns too. A failed revision cannot reopen Send.
                self._back(page, win, width, keyboard=True)
                assert win.get_attribute("id") == win_id
                mode["saves"] = "fail"
                note.click()
                page.keyboard.press("End")
                page.keyboard.type(" LOST")
                foot.locator("[data-tone=danger]").first.wait_for(timeout=T)
                self._tap(page, self._note_action(page, win, width, "Send"))
                page.wait_for_timeout(600)
                after = self._db_sends(note_ref)
                assert len(after) == 1 and after[0]["id"] == sent[0]["id"], after
                assert win.locator("[data-testid=thought-send], [data-testid=send-preview], [data-testid=send-verb]").count() == 0
                assert self._saved_note(note_ref) == (revision + 1, revised_body)
                page.screenshot(path=str(SEND_SHOTS / f"thought-send-save-failed-{width}.png"))
                mode["saves"] = "pass"

                assert not page.evaluate("document.documentElement.scrollWidth > window.innerWidth"), "page scrolls sideways"
                assert not errors, errors
            finally:
                browser.close()
