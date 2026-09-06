"""HS-176-05 — the desk answering the hand: the WHOLE loop on glass.

One hub session, no restart, the real routes (design D2(e)):

  1. `Talk`'s well lands an utterance through the dry-run route.
  2. `Wrong` unfolds the teach row; he edits the one word and `Teach`
     stores a `text` rule -- `queue for -> Q4`.
  3. He speaks the phrase again. The rule fires deterministically on the
     raw transcript and the RESULT row wears `APPLIED`.
  4. The Journal wing carries BOTH utterances: the second `APPLIED`, the
     first `TAUGHT`.
  5. The `Learned` wing carries the rule: `TEXT | queue for -> Q4 |
     1 APPLIED | Forget`.
  6. `Forget` removes it and the wing stands quiet: `NOTHING LEARNED`.
  7. `Review` on the Speak footer crosses to the JOURNAL wing (design
     D2(b).9) -- it opened the Configure door until 176.

The whole loop runs in ONE browser session against ONE hub: the
`CorrectionStore` is warm and the snapshot is taken fresh at the start of
every run, so a rule taught during one utterance applies to the next
with no restart (design D3).

Shots land in assets/story-05-shots/<state>-<width>.png, beside the
boards `Learned` / `LearnedQuiet` / `LearnedPhone` / `SpeakApplied`.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from .glass_infra import (
    _api,
    _assert_clean,
    _ensure_build,
    _normal_chair,
    _settle,
)

pytest.importorskip("playwright.sync_api", reason="Loop glass needs Playwright")

SHOTS = (
    Path(__file__).resolve().parents[2]
    / "pm/roadmap/holdspeak/phase-176-the-speak-loop/assets/story-05-shots"
)
SHOTS.mkdir(parents=True, exist_ok=True)

TOKEN = "hs176-loop"

#: The Tuesday sentence and the one word the transcript got wrong.
HEARD = "Ship the queue for platform on schedule"
SAID = "Ship the Q4 platform on schedule"
#: The next utterance carrying the same phrase — the rule must fire.
AGAIN = "Ship the queue for platform in October"
APPLIED_TEXT = "Ship the Q4 platform in October"


# ── the hub ────────────────────────────────────────────────────────


def _boot(tmp_path: Path, monkeypatch: Any) -> tuple[Any, str]:
    """A DURABLE hub in an isolated HOME.

    `glass_infra._boot` builds the bare server: an in-process correction
    ring with no row ids and a no-op journal recorder.  This loop needs
    both repositories, and for one honest reason — a ring correction has
    no id, so `corrections_applied` can name nothing and the `APPLIED`
    chip is (correctly) absent.  The owner's desk runs both, so the rig
    does, which also puts the face on the PRIMARY teach route.
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
        auth_token=TOKEN,
        dictation_journal_repository=database.dictation_journal,
        dictation_corrections_repository=database.dictation_corrections,
    )
    return server, server.start()


def _enable_corrections() -> None:
    """Beat 0 of the walk, paid here: every read of `corrections_enabled`
    falls back to False, so a hub whose config was never written makes the
    whole loop a silent no-op."""
    import holdspeak.config as config_module

    cfg = config_module.Config()
    cfg.dictation.pipeline.corrections_enabled = True
    cfg.save(path=config_module.CONFIG_FILE)


def _init_desk(page: Any, url: str) -> None:
    page.goto(f"{url}/?token={TOKEN}", wait_until="load")
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


def _shot(page: Any, name: str, width: int) -> Path:
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
    """Latch DRY RUN so a landing PREVIEWS and types nothing on the host."""
    page.locator(".gadget-check-token").filter(has_text="DRY RUN").click()


def _land(page: Any, text: str) -> Any:
    well = page.locator(".speak-well textarea")
    well.click()
    well.fill(text)
    well.press("Control+Enter")
    result = page.locator(".speak-result")
    result.wait_for(timeout=15000)
    _settle(page)
    return result


def _wing(page: Any, name: str) -> None:
    page.get_by_role("tab", name=name).click()


# ── the artboard assertions ────────────────────────────────────────


def _assert_learned_board(page: Any) -> None:
    """The `Learned` board, element by element (design D2(c))."""
    wing = page.locator(".speak-learned")
    rows = wing.locator(".surface-ledger-row")
    assert rows.count() == 1, rows.count()
    row = rows.first

    # the lead slot is the kind emblem, on the ledger's 52px column
    assert row.locator(".learned-kind").inner_text().strip() == "TEXT"
    # the primary is the key; the value is beside it behind the arrow
    assert row.locator(".surface-ledger-primary").inner_text().strip() == "queue for"
    assert row.locator(".learned-value").inner_text().strip() == "Q4"
    assert "→" in row.locator(".learned-cells").inner_text()
    # a REAL firing count — the teaching utterance is not one of them
    assert row.locator(".learned-applied").inner_text().strip() == "1 APPLIED"

    body = wing.inner_text()
    # no wire words on the face (canon E.4)
    for wire in ("claude_code", "dry_run", "snake", "similar", "SIMILAR"):
        assert wire not in body, (wire, body)
    # `LEARNED` is said ONCE per face — the wing tab, never the body (A.7)
    assert "LEARNED" not in body, body
    # no caption count (ruling N5b): the tab is the name, the rows the count
    caption = wing.locator(".surface-ledger-count").inner_text()
    assert caption.strip() == "", caption

    # the trailing verb is the library Button, with the WORD (not the `x`
    # glyph). It is located by its slot, not by role+name: the ledger LINE is
    # itself a button whose accessible name contains the row's whole text,
    # and Playwright's `name=` is a substring match.
    forget = row.locator(".learned-forget .btn")
    assert forget.count() == 1, forget.count()
    assert forget.inner_text().strip() == "Forget", forget.inner_text()
    raw = page.evaluate(
        """() => {
            const wing = document.querySelector('.speak-learned');
            if (!wing) return ['no wing'];
            return Array.from(wing.querySelectorAll('button'))
              .filter(b => !b.classList.contains('btn')
                        && !b.classList.contains('surface-ledger-line')
                        && !b.classList.contains('desk-mic'))
              .map(b => b.className || b.textContent);
        }"""
    )
    assert raw == [], raw

    # the row's children never intersect (the geometry probe)
    overlaps = page.evaluate(
        """() => {
            const line = document.querySelector('.speak-learned .surface-ledger-line');
            if (!line) return ['no line'];
            const kids = Array.from(line.children)
              .map(el => [el.className, el.getBoundingClientRect()])
              .filter(([, r]) => r.width > 0 && r.height > 0);
            const bad = [];
            for (let i = 0; i < kids.length; i++)
              for (let j = i + 1; j < kids.length; j++) {
                const [an, a] = kids[i], [bn, b] = kids[j];
                const overlapX = Math.min(a.right, b.right) - Math.max(a.left, b.left);
                const overlapY = Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top);
                if (overlapX > 1 && overlapY > 1) bad.push(`${an} x ${bn}`);
              }
            return bad;
        }"""
    )
    assert overlaps == [], overlaps


def _assert_learned_quiet(page: Any) -> None:
    """The `LearnedQuiet` board: ONE token, no zero, no sentence."""
    wing = page.locator(".speak-learned")
    assert wing.locator(".surface-ledger-row").count() == 0
    body = wing.inner_text()
    assert "NOTHING LEARNED" in body, body
    assert "APPLIED" not in body, body
    assert "0" not in body, body
    # no prose: the empty state is one token, never a sentence (A.3)
    assert "." not in body, body


# ── the loop ───────────────────────────────────────────────────────


def _loop(page: Any, width: int) -> None:
    _dry_run_on(page)

    # ── 1. land, judge, teach ──────────────────────────────────────
    result = _land(page, HEARD)
    result.get_by_role("button", name="Wrong").click()
    teach = page.locator(".speak-teach")
    teach.wait_for(timeout=8000)
    said = teach.get_by_role("textbox", name="What you said")
    assert said.input_value() == HEARD, said.input_value()
    said.fill(SAID)
    page.get_by_role("button", name="Teach correction").click()
    receipt = page.locator(".speak-receipt")
    receipt.wait_for(timeout=8000)
    assert "TAUGHT" in receipt.inner_text(), receipt.inner_text()

    # ── 2. speak it again, in the SAME session: the rule fires ─────
    result = _land(page, AGAIN)
    landed = result.locator(".speak-result-text").inner_text()
    assert landed == APPLIED_TEXT, landed
    chip = result.get_by_role("button", name="Corrections applied")
    chip.wait_for(timeout=8000)
    assert chip.inner_text().strip() == "APPLIED"
    # ONE mic authority on this face (ruling R13): the well carries none
    assert page.locator(".speak-well .desk-mic").count() == 0
    _shot(page, "loop-speak", width)

    # ── 3. the Journal wing: both utterances, the two marks ────────
    _wing(page, "Journal")
    page.locator(".speak-journal").wait_for(timeout=10000)
    rows = page.locator(".speak-journal .surface-ledger-row")
    rows.first.wait_for(timeout=10000)
    _settle(page)
    assert rows.count() == 2, rows.count()
    # newest first: the second utterance wears APPLIED, the first TAUGHT
    assert "APPLIED" in rows.nth(0).locator(".journal-mark").inner_text()
    assert "TAUGHT" in rows.nth(1).locator(".journal-mark").inner_text()

    # ── 4. the Learned wing: the rule the desk now knows ───────────
    _wing(page, "Learned")
    page.locator(".speak-learned").wait_for(timeout=10000)
    page.locator(".speak-learned .surface-ledger-row").first.wait_for(timeout=10000)
    _settle(page)
    _assert_learned_board(page)
    _shot(page, "learned", width)

    # ── 5. Forget: the rule goes, the wing stands quiet ────────────
    row = page.locator(".speak-learned .surface-ledger-row").first
    forget = row.locator(".learned-forget .btn")
    forget.click()
    # one step, in-world: the verb arms itself, no modal (rule A.4)
    assert page.locator('[role="dialog"]').count() == 0
    assert forget.inner_text().strip() == "Forget?", forget.inner_text()
    forget.click()
    page.locator('.speak-learned .surface-state[data-kind="empty"]').wait_for(
        timeout=8000
    )
    _assert_learned_quiet(page)
    _shot(page, "learned-quiet", width)
    # the wire agrees: the store is empty
    assert _api(page, "GET", "/api/dictation/corrections", token=TOKEN)["items"] == []

    # ── 6. `Review` reviews: it crosses to the JOURNAL wing ────────
    page.get_by_role("button", name="Review").click()
    page.locator(".speak-journal").wait_for(timeout=8000)
    assert (
        page.get_by_role("tab", name="Journal").get_attribute("aria-selected") == "true"
    )
    # not the Configure door — that stays the gear's job
    assert page.locator(".surface-door").count() == 0


# ── Tests ──────────────────────────────────────────────────────────


def _run(tmp_path, monkeypatch, width: int, height: int) -> None:
    _ensure_build()
    server, url = _boot(tmp_path, monkeypatch)
    _enable_corrections()
    errors: list[str] = []
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page()
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.set_viewport_size({"width": width, "height": height})
            _init_desk(page, url)
            _stage_speak(page)
            # The four wings are always present (design D2(c)).
            # (the strip renders its labels uppercase — canon C's caption step)
            wings = [
                t.strip().upper()
                for t in page.locator(".desk-wings-tabs [role=tab]").all_inner_texts()
            ]
            assert wings == ["SPEAK", "JOURNAL", "BLOCKS", "LEARNED"], wings
            _loop(page, width)
            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()


@pytest.mark.e2e
@pytest.mark.requires_meeting
def test_speak_loop_1440(tmp_path, monkeypatch):
    """The full loop at 1440, one session, no restart."""
    _run(tmp_path, monkeypatch, 1440, 900)


@pytest.mark.e2e
@pytest.mark.requires_meeting
def test_speak_loop_393(tmp_path, monkeypatch):
    """The same loop at 393: the Learned row wraps, nothing overflows."""
    _run(tmp_path, monkeypatch, 393, 852)
