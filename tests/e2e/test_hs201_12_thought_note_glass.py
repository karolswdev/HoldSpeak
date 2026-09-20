"""HS-201-12 — the Thought window is ONE clean note (the owner's first-use verdict).

Isolated HOME, no microphone: the owner's dictated-looking note is seeded
through the real API, and the window is walked at 1440 and 393 —
folded band 3 → Ask → answer → Add to note → Finish → reopen — with the
shots the story owes under assets/story-12-shots/.
"""
from __future__ import annotations

import os
import time
import uuid
from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("playwright.sync_api", reason="Thought glass needs Playwright")
pytest.importorskip("fastapi.testclient", reason="Thought glass needs web dependencies")

TOKEN = "hs201-12-thought-glass"
SHOTS = Path(__file__).resolve().parents[2] / (
    "pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/story-12-shots"
)
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
        [method, path, body, TOKEN],
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
    server = MeetingWebServer(callbacks, auth_token=TOKEN)
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
            page.goto(f"{url}/?token={TOKEN}", wait_until="load")
            _api(page, "POST", "/api/desk/seed")
            _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"})
            thought = _seed(page, OWNER_TITLE, OWNER_BODY)
            note_id = thought["working_note"]["id"]
            page.goto(f"{url}/?token={TOKEN}&open=note%3A{note_id}", wait_until="load")

            workspace = page.get_by_role("region", name="Thought", exact=True)
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
            kept = workspace.locator(".thought-note-foot .surface-footer-receipt-line")
            assert kept.inner_text().strip() == "KEPT"
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
            page.goto(f"{url}/?token={TOKEN}&open=note%3A{note_id}", wait_until="load")
            workspace = page.get_by_role("region", name="Thought", exact=True)
            workspace.wait_for(timeout=15000)
            assert page.get_by_text("KEPT · FINISHED", exact=False).count() == 1
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
            page.goto(f"{url}/?token={TOKEN}&open=note%3A{note_id}", wait_until="load")
            workspace = page.get_by_role("region", name="Thought", exact=True)
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
            page.goto(f"{url}/?token={TOKEN}", wait_until="load")
            _api(page, "POST", "/api/desk/seed")
            _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"})
            thought = _seed(page, long_title.strip(), long_body)
            page.goto(f"{url}/?token={TOKEN}&open=note%3A{thought['working_note']['id']}", wait_until="load")

            workspace = page.get_by_role("region", name="Thought", exact=True)
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


class _DraftEngine:
    """The prompt permits a synthesis instead of a question (refinement_coordinator.py:581)."""

    active_provider = "deterministic-thought-interview"

    def __init__(self) -> None:
        self.calls = 0

    def run_prompt(self, *, user_prompt: str, **_kwargs: object) -> str:
        self.calls += 1
        return ('{"kind":"synthesis","title":"A TIDIER TITLE FROM THE AI",'
                '"body_markdown":"The team disagrees about the freeze date.",'
                '"tags":["ai"]}')


OWNER_WORDS = "OWNER WORDS THAT MUST SURVIVE."
DRAFT_TEXT = "The team disagrees about the freeze date."


@pytest.mark.e2e
@pytest.mark.requires_meeting
@pytest.mark.parametrize("width", [1440, 393])
def test_thought_note_draft_is_appended_never_replaced(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int
) -> None:
    """Astra finding 1: `accept` REPLACES title, body and tags. Add appends."""
    from playwright.sync_api import sync_playwright

    server, url, _provider, engine = _boot(tmp_path, monkeypatch, engine=_DraftEngine())
    SHOTS.mkdir(parents=True, exist_ok=True)
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": width, "height": 900})
            page.emulate_media(reduced_motion="reduce")
            page.goto(f"{url}/?token={TOKEN}", wait_until="load")
            _api(page, "POST", "/api/desk/seed")
            _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"})
            thought = _seed(page, OWNER_TITLE, OWNER_WORDS)
            page.goto(f"{url}/?token={TOKEN}&open=note%3A{thought['working_note']['id']}", wait_until="load")

            workspace = page.get_by_role("region", name="Thought", exact=True)
            workspace.wait_for(timeout=15000)
            band = page.get_by_role("region", name="One question", exact=True)
            band.wait_for(timeout=15000)
            band.get_by_role("button", name="Ask", exact=True).click()

            page.get_by_text(DRAFT_TEXT, exact=True).wait_for(timeout=20000)
            assert "A DRAFT FROM YOUR NOTE" in band.inner_text().upper()
            assert page.get_by_role("textbox", name="Your answer").count() == 0
            assert band.get_by_role("button", name="Add to note", exact=True).count() == 1
            _no_empty_heading(page)
            page.screenshot(path=str(SHOTS / f"after-draft-{width}.png"), full_page=False)

            band.get_by_role("button", name="Add to note", exact=True).click()
            band.get_by_role("button", name="Ask", exact=True).wait_for(timeout=20000)
            kept = _api(page, "GET", f"/api/thoughts/{thought['id']}")["thought"]
            # The owner's words survive; the draft joins them; the title and
            # the tags are HIS, never the AI's.
            assert OWNER_WORDS in kept["working_note"]["body_markdown"], kept["working_note"]
            assert DRAFT_TEXT in kept["working_note"]["body_markdown"], kept["working_note"]
            assert kept["working_note"]["title"] == OWNER_TITLE, kept["working_note"]["title"]
            assert kept["working_note"]["tags"] == ["team"], kept["working_note"]["tags"]
            assert workspace.locator(".cm-thought-answer-reveal").count() >= 1
            assert engine.calls == 1
            _no_empty_heading(page)
            page.screenshot(path=str(SHOTS / f"after-draft-added-{width}.png"), full_page=False)
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
            page.goto(f"{url}/?token={TOKEN}", wait_until="load")
            _api(page, "POST", "/api/desk/seed")
            _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"})
            _api(page, "POST", "/api/notes", {"title": LONG_CONTEXT, "body_markdown": "The freeze holds.", "tags": []})
            thought = _seed(page, OWNER_TITLE, OWNER_BODY)
            page.goto(f"{url}/?token={TOKEN}&open=note%3A{thought['working_note']['id']}", wait_until="load")

            workspace = page.get_by_role("region", name="Thought", exact=True)
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
            kept = workspace.locator(".thought-note-foot .surface-footer-receipt-line")
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
            kept_box = workspace.locator(".thought-note-foot .surface-footer-receipt-line").bounding_box()
            assert kept_box and kept_box["width"] > 20, kept_box
            _no_horizontal_escape(page)
            page.screenshot(path=str(SHOTS / f"long-context-{width}.png"), full_page=False)
            browser.close()
    finally:
        server.stop()
