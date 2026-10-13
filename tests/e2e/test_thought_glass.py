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
from tests.e2e.chair_windows import open_chair_window
from tests.e2e.glass_infra import _normal_chair

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
    assert geo["lines"][1] == f"IN {DRAWER.upper()}", f"{label}: {geo['lines']}"


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
            # The capture verbs are in the Capture window. At 393 it opens on
            # demand from the Speak AppIcon (PHILO-13-11 R2); since PHILO-14 A1
            # (#939) the Chair's windows start closed at 1440 too, so he opens
            # it the same way at both widths.
            page.locator(".chair").wait_for()
            open_chair_window(page, "Capture")
            # The desk seeds its Inbox on first load; the thought is filed there.
            page.locator("[data-testid=arrival-develop-thought]").wait_for()
            status, answer = hub.api("PUT", "/api/directories/hs-seed-inbox", {"name": DRAWER})
            assert status == 200, (status, answer)
            page.locator("[data-testid=arrival-develop-thought]").click()
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
            page.wait_for_timeout(250)
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
# PHILO-3-04 (canvas ratified 2026-09-23) split the foot's receipt in two:
# line 1 is the write (`KEPT · <time>`, role=status), line 2 the filing
# state (`data-line="filing"`). The kept state is the WRITE line.
KEPT_LINE = '.thought-note-foot .surface-footer-receipt-line[role="status"]'
FILING_LINE = '.thought-note-foot .surface-footer-receipt-line[data-line="filing"]'
KEPT_WORDS = re.compile(r"^KEPT · \d{1,2}:\d{2}( [AP]M)?$")
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
    engine = engine or _OneQuestionEngine()
    broker = _configure(database)
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
            thought = _seed(page, OWNER_TITLE, OWNER_BODY)
            note_id = thought["working_note"]["id"]
            page.goto(f"{url}/?token={NOTE_TOKEN}&open=note%3A{note_id}", wait_until="load")

            workspace = page.locator(".desk-window.thought-workspace-window")
            workspace.wait_for(timeout=15000)
            band = page.get_by_role("region", name="One question", exact=True)
            band.wait_for(timeout=15000)

            # ── Band 3 is folded to one row; nothing else is on the screen ──
            assert band.get_by_role("button", name="Ask", exact=True).is_visible()
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

            # The context fact is said ONCE, in the Reads line of the foot.
            reads = workspace.locator(".thought-note-reads")
            assert reads.count() == 1
            assert page.get_by_text("Attached", exact=False).count() == 0
            page.screenshot(path=str(SHOTS / f"after-{width}.png"), full_page=False)

            # ── Change: an in-window well, and the Reads line is the receipt ──
            change = workspace.get_by_role("button", name="Change", exact=True)
            change.click()
            well = page.get_by_role("region", name="What the AI reads")
            well.wait_for(timeout=10000)
            assert well.evaluate("el => el.closest('.thought-workspace-window') !== null")
            assert well.evaluate(
                "el => [...el.querySelectorAll('button')].filter(node => "
                "!node.matches('.btn, [class*=\"desk-\"], [class*=\"surface-\"], [class*=\"gadget-\"]')).length"
            ) == 0
            token = well.get_by_role("checkbox").first
            token.wait_for(timeout=10000)
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
            assert page.get_by_role("region", name="What the AI reads").count() == 0
            _no_horizontal_escape(page)
            page.screenshot(path=str(SHOTS / f"after-change-{width}.png"), full_page=False)

            # ── Ask: the question and its pad are in frame, no tab to find ──
            band.get_by_role("button", name="Ask", exact=True).click()
            page.get_by_text(QUESTION, exact=True).wait_for(timeout=20000)
            answer = page.get_by_role("textbox", name="Your answer")
            answer.wait_for()
            window_box = workspace.bounding_box()
            assert window_box
            _in_frame(answer.bounding_box(), window_box, "answer pad")
            _in_frame(band.locator(".thought-note-ask-text").bounding_box(), window_box, "question")
            # A box inside a scrolled band still HAS a box: the band itself
            # must not need scrolling to reach the pad and its one verb.
            assert band.evaluate("el => el.scrollHeight <= el.clientHeight + 1")
            _in_frame(workspace.locator(".surface-footer").bounding_box(), window_box, "foot")
            assert workspace.locator(".gadget-chip-egress").count() >= 1
            assert workspace.locator(".btn--primary:visible").count() == 1
            _no_empty_heading(page)
            _no_horizontal_escape(page)
            page.screenshot(path=str(SHOTS / f"after-ask-{width}.png"), full_page=False)

            # ── One verb under the pad: the answer joins the note ──
            assert band.get_by_role("button", name="Add to note", exact=True).count() == 1
            assert band.get_by_role("button", name="Add & ask next").count() == 0
            answer.fill("Mina reads the plan differently. The freeze date settles it.")
            band.get_by_role("button", name="Add to note", exact=True).click()
            workspace.get_by_role("region", name="Note", exact=True).get_by_text(
                "Mina reads the plan differently.", exact=False
            ).wait_for(timeout=20000)
            # Band 3 folds back to its one row, and no chip is left behind.
            band.get_by_role("button", name="Ask", exact=True).wait_for(timeout=20000)
            assert page.get_by_role("textbox", name="Your answer").count() == 0
            assert page.get_by_text("Added to Note", exact=False).count() == 0
            assert workspace.locator(".cm-thought-answer-reveal").count() >= 1
            _no_empty_heading(page)
            page.screenshot(path=str(SHOTS / f"after-add-{width}.png"), full_page=False)

            # ── Astra finding 2 on the real hub: Finish with an UNADDED
            #    answer adds it first and then keeps, with no cursor conflict ──
            band.get_by_role("button", name="Ask", exact=True).click()
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
            # PHILO-3-04's two lines: the write says KEPT · <time>, the
            # filing line carries FINISHED.
            assert KEPT_WORDS.match(workspace.locator(KEPT_LINE).inner_text().strip())
            assert workspace.locator(FILING_LINE).inner_text().strip().endswith("· FINISHED")
            assert page.get_by_role("region", name="One question", exact=True).count() == 0
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
            provider["path"] = None
            page.goto(f"{url}/?token={NOTE_TOKEN}&open=note%3A{note_id}", wait_until="load")
            workspace = page.locator(".desk-window.thought-workspace-window")
            workspace.wait_for(timeout=15000)
            band = page.get_by_role("region", name="One question", exact=True)
            band.wait_for(timeout=15000)
            band.get_by_role("button", name="Choose an engine", exact=True).wait_for(timeout=15000)
            assert "NO ENGINE YET" in band.inner_text()
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
            band = page.get_by_role("region", name="One question", exact=True)
            band.wait_for(timeout=15000)
            window_box = workspace.bounding_box()
            assert window_box
            _in_frame(band.bounding_box(), window_box, "band 3 under a long note")
            _in_frame(workspace.locator(".surface-footer").bounding_box(), window_box, "foot under a long note")
            title = workspace.locator(".thought-note-title")
            assert title.evaluate("el => el.scrollHeight <= el.clientHeight + 1")
            # The note owns the scroll; the window itself never scrolls away.
            assert workspace.locator(".thought-note-body .cm-scroller").evaluate(
                "el => el.scrollHeight > el.clientHeight"
            )
            _no_horizontal_escape(page)

            band.get_by_role("button", name="Ask", exact=True).click()
            page.get_by_text(LONG_QUESTION, exact=True).wait_for(timeout=20000)
            answer = page.get_by_role("textbox", name="Your answer")
            answer.wait_for()
            deadline = time.time() + 2
            while time.time() < deadline and not answer.bounding_box():
                time.sleep(0.05)
            window_box = workspace.bounding_box()
            assert window_box
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
            workspace.get_by_role("button", name="Change", exact=True).click()
            well = page.get_by_role("region", name="What the AI reads")
            well.wait_for(timeout=10000)

            # The well SEARCHES the desk, not just six recent notes.
            find = well.get_by_role("textbox", name="Find a note")
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
            # Nothing the owner must press leaves the window…
            for name in ("Change", "Finish"):
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
            page.screenshot(path=str(SHOTS / f"long-context-open-well-{width}.png"), full_page=False)

            # …and with the well closed, the ordinary face keeps the whole
            # name readable in the foot, with the verbs in their places.
            well.press("Escape")
            assert page.get_by_role("region", name="What the AI reads").count() == 0
            _reads_full(workspace.locator(".thought-note-reads"), LONG_CONTEXT)
            window_box = workspace.bounding_box()
            assert window_box
            for name in ("Change", "Finish"):
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


@pytest.mark.e2e
@pytest.mark.requires_meeting
@pytest.mark.parametrize("width", [1440, 393])
def test_thought_workbench_real_glass(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int) -> None:
    from playwright.sync_api import sync_playwright
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
    engine = _InterviewEngine()
    broker = _configure(database)
    monkeypatch.setattr(broker.inference_runner, "_engine_factory", lambda _revision, **_kw: engine)
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
            band = page.get_by_role("region", name="One question", exact=True)
            band.wait_for(timeout=10000)
            ask = band.get_by_role("button", name="Ask", exact=True)
            ask.wait_for()
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

            window_box = workspace.bounding_box()
            assert window_box and window_box["y"] >= 48
            assert window_box["y"] + window_box["height"] <= 900
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
            engine.block_next = True
            ask.click()
            page.wait_for_function(
                "el => el?.textContent?.trim() === 'Stop'",
                arg=band.get_by_role("button").first.element_handle(),
                timeout=10000,
            )
            assert engine.started.wait(5)
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
            band.get_by_role("button", name="Ask", exact=True).wait_for(timeout=20000)
            assert page.get_by_text("STALE QUESTION MUST NOT APPEAR", exact=True).count() == 0

            # ── The one question, answered with the one verb ──
            band.get_by_role("button", name="Ask", exact=True).click()
            page.get_by_text("Who owns the launch?", exact=True).wait_for(timeout=20000)
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
            change = workspace.get_by_role("button", name="Change", exact=True)
            change.click()
            well = page.get_by_role("region", name="What the AI reads")
            well.wait_for(timeout=10000)
            assert well.evaluate("el => el.closest('.thought-workspace-window') !== null")
            well_box = well.bounding_box()
            assert well_box and well_box["y"] + well_box["height"] <= window_box["y"] + window_box["height"] + 1
            page.screenshot(path=f"/tmp/holdspeak-thought-context-well-{width}.png", full_page=False)
            well.press("Escape")
            assert page.get_by_role("region", name="What the AI reads").count() == 0
            page.wait_for_function("el => el === document.activeElement", arg=change.element_handle(), timeout=5000)

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
