"""HS-176-02 — the Speak face's teach loop, on glass.

The whole Tuesday loop through the REAL routes — no stubbed dry run, no
stubbed teach.  The hub is an isolated HOME; the pipeline runs with no
engine (the intent stage falls back, which is the honest state on a
bare desk) and the `text` correction is deterministic, so the loop the
boards draw runs end to end:

  1. land "Ship the queue for platform on schedule"
  2. `Wrong` -> the teach row, FIELD at TEXT, the well pre-filled with
     the RAW transcript                                  -> wrong
  3. FIELD at TARGET -> a pick over the six real profile ids
                                                         -> wrong-route
  4. edit one word, `Teach` -> TAUGHT · queue for -> Q4   -> taught
  5. a secret-shaped teach -> REFUSED · SECRET            -> refused
  6. speak it again -> the rule fires, APPLIED on the RESULT row, its
     well naming HEARD / SAID / TEXT                      -> applied

Shots land in assets/story-02-shots/<state>-<width>.png, beside the
boards SpeakWrong / SpeakWrongRoute / SpeakLearned / SpeakRefused /
SpeakApplied / SpeakLoopPhone.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from .glass_infra import (
    _api,
    _assert_clean,
    _normal_chair,
    _ensure_build,
    _settle,
)

pytest.importorskip("playwright.sync_api", reason="Speak glass needs Playwright")

SHOTS = (
    Path(__file__).resolve().parents[2]
    / "pm/roadmap/holdspeak/phase-176-the-speak-loop/assets/story-02-shots"
)
SHOTS.mkdir(parents=True, exist_ok=True)

TOKEN = "hs176-speak"

#: The Tuesday sentence and its one wrong span (the board's own words).
HEARD = "Ship the queue for platform on schedule"
SAID = "Ship the Q4 platform on schedule"
#: The same rule's next firing — the board's APPLIED sentence.
AGAIN = "Ship the queue for platform in October"
#: The teach that must be refused by name, writing nothing.
SECRET_HEARD = "Set the token to placeholder"
SECRET_SAID = "Set the token to sk-live4f2a9c1b2d3e4f"

#: The six ids the readiness route offers — `auto` is never among them.
TARGET_LABELS = [
    "Claude Code",
    "Codex CLI",
    "Terminal shell",
    "Browser",
    "Editor",
    "Chat",
]


# ── Helpers ────────────────────────────────────────────────────────


def _boot(tmp_path: Path, monkeypatch: Any, *, token: str = TOKEN) -> tuple[Any, str]:
    """Boot a DURABLE hub in an isolated HOME.

    `glass_infra._boot` builds the bare server every other rig wants: the
    correction store is the in-process ring and the journal recorder is a
    no-op.  This loop needs both DURABLE, and for one honest reason: a
    ring correction has no row id, so `corrections_applied` cannot name
    it and the `APPLIED` chip is (correctly) absent.  The owner's desk
    runs with both repositories attached, so the rig does too — which
    also puts the face on the PRIMARY teach route (the journal correct
    route) rather than its fallback.
    """
    import os

    import holdspeak.config as config_module
    import holdspeak.db.core as db_core
    from holdspeak.db import Database, reset_database
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    home = tmp_path / "home"
    home.mkdir(exist_ok=True)
    browser_cache = Path(
        os.environ.get(
            "PLAYWRIGHT_BROWSERS_PATH",
            Path.home() / "Library/Caches/ms-playwright",
        )
    )
    monkeypatch.setenv("PLAYWRIGHT_BROWSERS_PATH", str(browser_cache))
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setattr(config_module, "CONFIG_FILE", home / ".holdspeak" / "config.json")
    monkeypatch.setattr(db_core, "DEFAULT_DB_PATH", tmp_path / "holdspeak.db")
    reset_database()
    database = Database(tmp_path / "holdspeak.db")

    server = MeetingWebServer(
        WebRuntimeCallbacks(
            on_bookmark=lambda *_: None,
            on_stop=lambda: None,
            get_state=lambda: {},
        ),
        auth_token=token,
        dictation_journal_repository=database.dictation_journal,
        dictation_corrections_repository=database.dictation_corrections,
    )
    return server, server.start()


def _enable_corrections() -> None:
    """Turn the correction loop on in the ISOLATED home's config.

    Every read of `corrections_enabled` falls back to False, so a hub
    whose config was never written is a silent no-op — the walk's own
    beat-zero check, paid here so the rig proves the loop, not the
    fallback.
    """
    import holdspeak.config as config_module

    cfg = config_module.Config()
    cfg.dictation.pipeline.corrections_enabled = True
    cfg.save(path=config_module.CONFIG_FILE)


def _init_desk(page: Any, url: str) -> None:
    page.goto(f"{url}/?token={TOKEN}", wait_until="load")
    _api(page, "POST", "/api/desk/seed", token=TOKEN)
    _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
    _normal_chair(page)


def _stage_speak(page: Any) -> None:
    page.evaluate(
        """([key]) => {
          localStorage.removeItem("hs.desk.workspace.v1");
          sessionStorage.setItem(
            "hs.desk.staged-surface-open",
            JSON.stringify({key})
          );
        }""",
        ["dictate"],
    )
    page.reload(wait_until="load")
    _normal_chair(page)
    page.locator(".speak-face").wait_for(timeout=15000)
    _settle(page)


def _shot(page: Any, name: str, width: int, *, settle: bool = True) -> Path:
    """Shoot the Speak window.  The receipt fades at 5 s, so a receipt
    shot skips the animation settle and takes the frame it has."""
    if settle:
        _settle(page)
    path = SHOTS / f"{name}-{width}.png"
    target = page.locator(".desk-surface-window").first
    if target.count() > 0:
        target.screenshot(path=str(path))
    else:
        page.screenshot(path=str(path), full_page=False)
    assert path.stat().st_size > 2_000, f"Shot {name} too small ({path.stat().st_size})"
    return path


def _dry_run_on(page: Any) -> None:
    """Latch DRY RUN so a landing PREVIEWS and delivers nothing.

    The rig never types into the owner's machine: `deliver()` would go
    through /api/dictation/remote to the real typing path.
    """
    token = page.locator(".gadget-check-token").filter(has_text="DRY RUN")
    token.click()


def _land(page: Any, text: str) -> Any:
    """Type one utterance and land it through the real dry-run route."""
    well = page.locator(".speak-well textarea")
    well.click()
    well.fill(text)
    well.press("Control+Enter")
    result = page.locator(".speak-result")
    result.wait_for(timeout=15000)
    page.locator(".speak-result-text").filter(has_text=text.split()[0]).first.wait_for(
        timeout=15000
    )
    _settle(page)
    return result


def _walk(page: Any, width: int) -> None:
    """The five boards, in the order the owner meets them."""
    _dry_run_on(page)

    # ── 1. land, and press Wrong: the teach row unfolds in-world ──
    result = _land(page, HEARD)
    assert result.locator(".speak-result-text").inner_text().startswith("Ship the queue")
    result.get_by_role("button", name="Wrong").click()
    teach = page.locator(".speak-teach")
    teach.wait_for(timeout=8000)
    # never a modal (rule A.4)
    assert page.locator('[role="dialog"]').count() == 0
    assert "FIELD" in teach.inner_text()
    field = teach.get_by_label("Correction field")
    assert field.input_value() == "text", field.input_value()
    assert [o.strip() for o in field.locator("option").all_inner_texts()] == [
        "TEXT",
        "INTENT",
        "TARGET",
    ]
    # N2 — the well holds what the mic HEARD, not what landed
    said = teach.get_by_role("textbox", name="What you said")
    assert said.input_value() == HEARD, said.input_value()
    # ...and it holds ALL of it: the value he is asked to EDIT wraps, it
    # is never ellipsised away (the 393 bounce).
    assert said.evaluate("el => el.tagName") == "TEXTAREA"
    assert said.evaluate("el => el.scrollWidth <= el.clientWidth + 1"), (
        "the teach well truncates its value horizontally"
    )
    # the voice law: the well carries its own mic
    assert teach.locator(".desk-mic").count() >= 1
    _shot(page, "wrong", width)

    # ── 2. FIELD at TARGET: a pick over the six real ids ──
    field.select_option("target")
    pick = teach.get_by_label("Delivery target")
    pick.wait_for(timeout=5000)
    labels = [o.strip() for o in pick.locator("option").all_inner_texts()]
    assert labels == TARGET_LABELS, labels
    values = pick.locator("option").evaluate_all("els => els.map(e => e.value)")
    assert "auto" not in values, values
    # the face prints the label map's string verbatim
    pick.select_option("terminal_shell")
    assert teach.get_by_role("textbox", name="What you said").count() == 0
    _shot(page, "wrong-route", width)

    # ── 3. back to TEXT, edit the one word, Teach ──
    field.select_option("text")
    said = teach.get_by_role("textbox", name="What you said")
    said.wait_for(timeout=5000)
    said.fill(SAID)
    page.get_by_role("button", name="Teach correction").click()
    receipt = page.locator(".speak-receipt")
    receipt.wait_for(timeout=8000)
    text = receipt.inner_text()
    assert "TAUGHT" in text, text
    assert "queue for" in text and "Q4" in text, text
    # the teach row gave way to its receipt
    assert page.locator(".speak-teach").count() == 0
    # A.7 — said ONCE: the footer keeps its own status vocabulary and
    # never mirrors the outcome the row already carries.
    footer = page.locator(".surface-footer-layout").inner_text()
    assert "TAUGHT" not in footer, footer
    _shot(page, "taught", width, settle=False)

    # ── 4. a secret-shaped teach is refused BY NAME, writing nothing ──
    _land(page, SECRET_HEARD)
    page.locator(".speak-result").get_by_role("button", name="Wrong").click()
    page.locator(".speak-teach").wait_for(timeout=8000)
    page.get_by_role("textbox", name="What you said").fill(SECRET_SAID)
    page.get_by_role("button", name="Teach correction").click()
    receipt = page.locator(".speak-receipt")
    receipt.wait_for(timeout=8000)
    text = receipt.inner_text()
    assert "REFUSED" in text and "SECRET" in text, text
    assert "nothing written" in text, text
    footer = page.locator(".surface-footer-layout").inner_text()
    assert "REFUSED" not in footer, footer
    _shot(page, "refused", width, settle=False)
    # nothing was written: the store still holds exactly the one rule
    stored = _api(page, "GET", "/api/dictation/corrections", token=TOKEN)
    assert len(stored["items"]) == 1, stored["items"]

    # ── 5. speak it again: the rule fires, and says so ──
    result = _land(page, AGAIN)
    landed = result.locator(".speak-result-text").inner_text()
    assert landed == "Ship the Q4 platform in October", landed
    chip = result.get_by_role("button", name="Corrections applied")
    chip.wait_for(timeout=8000)
    assert chip.inner_text().strip() == "APPLIED"
    chip.click()
    body = page.locator(".speak-applied-body")
    body.wait_for(timeout=5000)
    disclosed = body.inner_text()
    for token in ("HEARD", "queue for", "SAID", "Q4", "TEXT"):
        assert token in disclosed, (token, disclosed)
    _shot(page, "applied", width)


# ── Tests ──────────────────────────────────────────────────────────


@pytest.mark.e2e
@pytest.mark.requires_meeting
def test_speak_teach_loop_1440(tmp_path, monkeypatch):
    """The teach loop at 1440, board by board."""
    _ensure_build()
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    _enable_corrections()
    errors: list[str] = []
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page()
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.set_viewport_size({"width": 1440, "height": 900})
            _init_desk(page, url)
            _stage_speak(page)
            _walk(page, 1440)
            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()


@pytest.mark.e2e
@pytest.mark.requires_meeting
def test_speak_teach_loop_393(tmp_path, monkeypatch):
    """The same loop at 393: the row wraps, nothing overflows."""
    _ensure_build()
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    _enable_corrections()
    errors: list[str] = []
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page()
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.set_viewport_size({"width": 393, "height": 852})
            _init_desk(page, url)
            _stage_speak(page)
            _walk(page, 393)
            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()


@pytest.mark.e2e
@pytest.mark.requires_meeting
def test_speak_teach_wire_is_the_real_one(tmp_path, monkeypatch):
    """The loop the face drives is the loop the routes actually run.

    Every assertion above rides the face; this one names the wire it
    rides, so a face that quietly stopped teaching would fail here too.
    """
    _ensure_build()
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    _enable_corrections()
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page()
            page.set_viewport_size({"width": 1440, "height": 900})
            _init_desk(page, url)

            # the readiness route is the target label source: six, no `auto`
            readiness = _api(page, "GET", "/api/dictation/readiness", token=TOKEN)
            overrides = readiness["target"]["overrides"]
            assert [o["label"] for o in overrides] == TARGET_LABELS
            assert "auto" not in [o["id"] for o in overrides]

            first = _api(page, "POST", "/api/dictation/dry-run", {"utterance": HEARD}, token=TOKEN)
            assert first["raw_text"] == HEARD
            assert first["corrections_applied"] == []

            taught = _api(
                page,
                "POST",
                f"/api/dictation/journal/{first['journal_id']}/correct",
                {"kind": "text", "heard": first["raw_text"], "said": SAID},
                token=TOKEN,
            )
            assert taught["recorded"] is True
            assert (taught["key"], taught["value"]) == ("queue for", "Q4")

            again = _api(page, "POST", "/api/dictation/dry-run", {"utterance": AGAIN}, token=TOKEN)
            assert again["final_text"] == "Ship the Q4 platform in October"
            assert again["corrections_applied"] == [taught["id"]]

            # `N APPLIED` is a real firing count, and the teaching row is
            # not one of them.
            items = _api(page, "GET", "/api/dictation/corrections", token=TOKEN)["items"]
            assert len(items) == 1 and items[0]["applied"] == 1
            assert items[0]["key"] == "queue for"

            browser.close()
    finally:
        server.stop()
