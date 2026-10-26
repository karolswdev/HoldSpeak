"""The Speak window in a real browser: what only a browser can prove.

The push-2 test diet (2026-10-12) moved the Speak teach loop to its cheaper
successors: the hub half is tests/unit/test_desk_speak.py
(test_the_teach_loop_runs_on_the_real_routes), the face half is
web/src/desk/__tests__/speak.app.test.tsx ("the teach loop on the Speak
window, replayed from the hub"), and the layout of the Speak window at 1440 and
393 is the desk sweep (tests/e2e/test_desk_sweep.py).

What stays here is one geometry relation the sweep cannot reach (its hub has no
learned rule): at 393 the Learned row wraps and its children never intersect
(``_assert_learned_board``, "the geometry probe"). It needs a taught rule, so
the loop runs once, at 393, on one hub session, through the real routes.

Kept from tests/e2e/_parked/test_hs176_loop_glass.py::test_speak_loop_393.

The Speak window in a real browser: the hotkey custody block's geometry.

Kept by the test diet (push 2, 2026-10-12), one file for the Speak app. The
words and rows of each state are web/src/desk/__tests__/speak.app.test.tsx
(over the hub's recorded readiness answers); the five wires are
tests/unit/test_desk_speak.py. What stays here needs a real browser: in each
state the block never leaves the window, and every state chip shares ONE
right edge (an exact geometry relation), at 1440 and 393.
Was tests/e2e/test_hs200_voice_custody_glass.py.

HS-200-05 — the hotkey's custody block, on glass.

The defect this face answers: `web_runtime.py:538-559` recorded whether the
global hotkey listener installed and NOTHING read it (the curated status
payload at `runtime/activity.py:171` dropped both keys), so the owner pressed
Right Option, got silence, and had no way to learn the cause.

Everything below runs against a REAL booted hub under an isolated HOME, and
every row drawn is rendered by the real `SpeakFace` from the real
`GET /api/dictation/readiness` payload built by the real
`_helpers._hotkey_custody`.

Exactly two things are substituted, both at the PLATFORM seam, because a test
runner cannot revoke a macOS grant:

* the three permission probes (`_ax_is_process_trusted`,
  `_iohid_check_access`, `_av_authorization_status`) — the same seam the unit
  suite uses; each returns what macOS would have returned;
* the runtime's `on_get_status`, which on a real hub is
  `WebRuntime._get_runtime_status` — here a dict carrying the two keys that
  method now exposes.

Nothing about the route, the payload shape, the derivation
(`hotkeyCustody.ts`) or the face is faked.

The five states, at 1440 and 393:

1. **all-denied** — the full block: three rows, three paths.
2. **one-denied** — only the non-granted row draws; no decorative all-clear.
3. **not-asked** — `NOT ASKED`, the first-installer state (the app is not
   even listed in the pane yet).
4. **listener-failed** — the classified reason token beside a granted set.
5. **all-granted** — the block is ABSENT, reached by pressing the one verb
   (`Re-check`) after the grant was given, which is the ratified flow.

Shots land in
``pm/roadmap/holdspeak/phase-200-the-working-practice/assets/story-05-shots``.
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
    pick_wing,
)
from tests._evidence import evidence_dir

pytest.importorskip("playwright.sync_api", reason="this glass needs Playwright")



# ══ the learned loop (Speak) ═══════════════════════════════════════

SHOTS = evidence_dir("speak-glass")

SHOTS.mkdir(parents=True, exist_ok=True)

TOKEN = "speak-glass"

#: The Tuesday sentence and the one word the transcript got wrong.
HEARD = "Ship the queue for platform on schedule"

SAID = "Ship the Q4 platform on schedule"

#: The next utterance carrying the same phrase — the rule must fire.
AGAIN = "Ship the queue for platform in October"

APPLIED_TEXT = "Ship the Q4 platform in October"

def _boot(
    tmp_path: Path,
    monkeypatch: Any,
    *,
    on_transcribe: Any = None,
    token: str = TOKEN,
) -> tuple[Any, str]:
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
            on_transcribe=on_transcribe,
        ),
        auth_token=token,
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

def _init_desk(page: Any, url: str, *, token: str = TOKEN) -> None:
    page.goto(f"{url}/?token={token}", wait_until="load")
    _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=token)
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
    """Betterment C8: the DRY RUN latch is gone; `Try it here` (in `_land`)
    previews and types nothing on the host. Kept as a no-op for the callers."""

def _land(page: Any, text: str) -> Any:
    well = page.locator(".speak-well textarea")
    well.click()
    well.fill(text)
    # The result of the utterance before stays on the face until this one
    # lands. Waiting for `.speak-result` alone returned that old result when
    # the hub was slow (seen at 1440 under load: the first utterance's text
    # read as the second's). Wait for the text to change.
    shown = page.locator(".speak-result .speak-result-text")
    before = shown.first.inner_text() if shown.count() else None
    # Betterment C8: `Try it here` puts the result in the box, types nothing.
    page.get_by_test_id("speak-try-it-here").click()
    page.wait_for_function(
        """(before) => {
          const el = document.querySelector('.speak-result .speak-result-text');
          return !!el && (before === null || el.innerText !== before);
        }""",
        arg=before, timeout=15000,
    )
    result = page.locator(".speak-result")
    _settle(page)
    return result

def _wing(page: Any, name: str) -> None:
    pick_wing(page, name)

def _folded(page: Any) -> Any:
    """The one strip menu Button a wing strip folds into at 393 (PHILO-13-11,
    C1 §3a: a strip that does not fit the head's 44 px row). Tabs at 1440."""
    return page.locator(".desk-wings .surface-strip-menu")

def _wing_names(page: Any) -> list[str]:
    """Every face of the window, in order: the tabs, or the rows of the menu."""
    strip = _folded(page)
    if not strip.count():
        return [t.strip().upper() for t in page.locator(".desk-wings-tabs [role=tab]").all_inner_texts()]
    strip.click()
    menu = page.get_by_role("menu", name="Window faces", exact=True)
    menu.wait_for()
    names = [t.strip().upper() for t in menu.get_by_role("menuitemcheckbox").all_inner_texts()]
    # Escape closes the menu, not the window (test_philo13_18_strip_escape_glass).
    page.keyboard.press("Escape")
    menu.wait_for(state="detached")
    assert strip.get_attribute("aria-expanded") == "false"
    assert page.locator(".desk-window-shell[aria-label='Speak']").is_visible()
    return names

def _wing_is_on(page: Any, name: str) -> bool:
    """The named face is the current one: the selected tab, or the strip
    menu Button that names it."""
    strip = _folded(page)
    if strip.count():
        return strip.first.get_attribute("aria-label") == f"Window faces: {name}"
    return page.get_by_role("tab", name=name).get_attribute("aria-selected") == "true"

def _assert_learned_board(page: Any) -> None:
    """The `Learned` board, element by element (design D2(c))."""
    wing = page.locator(".speak-learned")
    rows = wing.locator(".surface-ledger-row")
    assert rows.count() == 1, rows.count()
    row = rows.first

    # the lead slot is the kind emblem, on the ledger's 52px column
    assert row.locator(".learned-kind").inner_text().strip() == "Text"
    # the primary is the key; the value is beside it behind the arrow
    assert row.locator(".surface-ledger-primary").inner_text().strip() == "queue for"
    assert row.locator(".learned-value").inner_text().strip() == "Q4"
    assert "→" in row.locator(".learned-cells").inner_text()
    # a REAL firing count — the teaching utterance is not one of them
    assert row.locator(".learned-applied").inner_text().strip() == "1 applied"

    body = wing.inner_text()
    # no wire words on the face (canon E.4)
    for wire in ("claude_code", "dry_run", "snake", "similar", "SIMILAR"):
        assert wire not in body, (wire, body)
    # `LEARNED` is said ONCE per face — the wing tab, never the body (A.7)
    assert "LEARNED" not in body, body
    # no caption count (ruling N5b): the tab is the name, the rows the count
    # Phase 16 kit: a Ledger with no count and no controls draws no head at
    # all (Surface.tsx SurfaceLedger), so the caption is absent or empty.
    captions = [c.strip() for c in wing.locator(".surface-ledger-count").all_inner_texts()]
    assert not any(captions), captions

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
              .filter(b => !b.classList.contains('btn') && !b.classList.contains('btn--chrome')
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
    assert "Nothing learned" in body, body
    assert "applied" not in body.lower(), body
    assert "0" not in body, body
    # no prose: the empty state is one token, never a sentence (A.3)
    assert "." not in body, body

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
    assert "Applied" in rows.nth(0).locator(".journal-mark").inner_text()
    assert "Taught" in rows.nth(1).locator(".journal-mark").inner_text()

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
    assert _wing_is_on(page, "Journal")
    # not the Configure door — that stays the gear's job
    assert page.locator(".surface-door").count() == 0

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
            # The five wings are always present (design D2(c), C11).
            # (the strip renders its labels uppercase — canon C's caption step)
            wings = _wing_names(page)
            # Folded, the menu also holds the configuration door, after the faces.
            door = ["CONFIGURE DICTATION"] if _folded(page).count() else []
            assert wings == [
                "SPEAK", "JOURNAL", "BLOCKS", "LEARNED", "COMMANDS"
            ] + door, wings
            _loop(page, width)
            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()

@pytest.mark.e2e
@pytest.mark.requires_meeting
def test_the_learned_row_wraps_without_overlap_at_393(tmp_path, monkeypatch):
    """The loop at 393: the Learned row wraps; its children never intersect."""
    _run(tmp_path, monkeypatch, 393, 852)


# ══ the hotkey custody block (was test_hs200_voice_custody_glass.py) ═══

CUSTODY_SHOTS = evidence_dir("pm/roadmap/holdspeak/phase-200-the-working-practice/assets/story-05-shots")

CUSTODY_SHOTS.mkdir(parents=True, exist_ok=True)

CUSTODY_TOKEN = "hs200-05-custody"

#: The platform values each state is built from — the real constants.
AX_TRUSTED, AX_NOT_TRUSTED = True, False

HID_GRANTED, HID_DENIED, HID_NEVER_ASKED = 0, 1, 2

AV_NEVER_ASKED, AV_DENIED, AV_GRANTED = 0, 2, 3

class _Platform:
    """The machine's answers, swappable between legs."""

    def __init__(self) -> None:
        self.ax = AX_TRUSTED
        self.hid = HID_GRANTED
        self.av = AV_GRANTED
        self.status: dict[str, Any] = {
            "global_hotkey_available": True,
            "global_hotkey_error": "",
        }

    def all_denied(self) -> None:
        self.ax, self.hid, self.av = AX_NOT_TRUSTED, HID_DENIED, AV_DENIED
        self.status = {"global_hotkey_available": False,
                       "global_hotkey_error": "OSError: permission denied by the operating system"}

    def one_denied(self) -> None:
        self.ax, self.hid, self.av = AX_TRUSTED, HID_DENIED, AV_GRANTED
        self.status = {"global_hotkey_available": True, "global_hotkey_error": ""}

    def never_asked(self) -> None:
        self.ax, self.hid, self.av = AX_NOT_TRUSTED, HID_NEVER_ASKED, AV_NEVER_ASKED
        self.status = {"global_hotkey_available": False, "global_hotkey_error": ""}

    def listener_failed(self) -> None:
        self.ax, self.hid, self.av = AX_TRUSTED, HID_GRANTED, AV_GRANTED
        self.status = {"global_hotkey_available": False,
                       "global_hotkey_error": "RuntimeError: pynput is not available."}

    def all_granted(self) -> None:
        self.ax, self.hid, self.av = AX_TRUSTED, HID_GRANTED, AV_GRANTED
        self.status = {"global_hotkey_available": True, "global_hotkey_error": ""}

def _custody_boot(tmp_path: Path, monkeypatch: Any) -> tuple[Any, str, _Platform]:
    """A real hub whose PLATFORM answers (only) are ours to script."""
    import os

    import holdspeak.config as config_module
    import holdspeak.db.core as db_core
    from holdspeak import desktop_permissions as perms
    from holdspeak.db import reset_database
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    home = tmp_path / "home"
    home.mkdir(exist_ok=True)
    browser_cache = Path(
        os.environ.get(
            "PLAYWRIGHT_BROWSERS_PATH", Path.home() / "Library/Caches/ms-playwright"
        )
    )
    monkeypatch.setenv("PLAYWRIGHT_BROWSERS_PATH", str(browser_cache))
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setattr(config_module, "CONFIG_FILE", home / ".holdspeak" / "config.json")
    monkeypatch.setattr(db_core, "DEFAULT_DB_PATH", tmp_path / "holdspeak.db")
    reset_database()

    machine = _Platform()
    # The platform seam, and ONLY the platform seam.
    monkeypatch.setattr(perms, "_is_macos", lambda: True)
    monkeypatch.setattr(perms, "_ax_is_process_trusted", lambda: machine.ax)
    monkeypatch.setattr(perms, "_iohid_check_access", lambda: machine.hid)
    monkeypatch.setattr(perms, "_av_authorization_status", lambda: machine.av)

    server = MeetingWebServer(
        WebRuntimeCallbacks(
            on_bookmark=lambda *_: None,
            on_stop=lambda: None,
            get_state=lambda: {},
            # On the owner's desk this is `WebRuntime._get_runtime_status`.
            on_get_status=lambda: dict(machine.status),
        ),
        auth_token=CUSTODY_TOKEN,
    )
    return server, server.start(), machine

def _custody_init_desk(page: Any, url: str) -> None:
    page.goto(f"{url}/?token={CUSTODY_TOKEN}", wait_until="load")
    _api(page, "POST", "/api/desk/seed", token=CUSTODY_TOKEN)
    _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=CUSTODY_TOKEN)
    _normal_chair(page)

def _custody_stage_speak(page: Any) -> None:
    page.evaluate(
        """([key]) => {
          localStorage.removeItem("hs.desk.workspace.v1");
          sessionStorage.setItem(
            "hs.desk.staged-surface-open", JSON.stringify({key})
          );
        }""",
        ["dictate"],
    )
    page.reload(wait_until="load")
    _normal_chair(page)
    page.locator(".speak-face").wait_for(timeout=20000)
    _settle(page)

def _custody_shot(page: Any, name: str, width: int) -> Path:
    _settle(page)
    path = CUSTODY_SHOTS / f"{name}-{width}.png"
    target = page.locator(".desk-surface-window").first
    if target.count() > 0:
        target.screenshot(path=str(path))
    else:
        page.screenshot(path=str(path), full_page=False)
    assert path.stat().st_size > 2_000, f"Shot {name} too small ({path.stat().st_size})"
    return path

def _no_overflow(block: Any, width: int) -> None:
    """Nothing in the block may scroll sideways — the 393 law.

    Three path tokens plus a state chip on one row is exactly the shape that
    clips, so every row is measured, not eyeballed.
    """
    assert block.evaluate("el => el.scrollWidth <= el.clientWidth + 1"), (
        f"the HOTKEY block overflows horizontally at {width}"
    )
    rows = block.locator(".speak-hotkey-row, .speak-hotkey-head")
    for i in range(rows.count()):
        row = rows.nth(i)
        assert row.evaluate("el => el.scrollWidth <= el.clientWidth + 1"), (
            f"a HOTKEY row overflows horizontally at {width}: "
            f"{row.inner_text()!r}"
        )

def _one_grammar(block: Any, width: int) -> None:
    """The same object is never drawn two ways (UX canon D, first rule).

    The first draft flex-wrapped the row, and the shots caught what no unit
    test could: at 640 the state chip sat right on the first row and wrapped
    to the LEFT on the next two, and at 393 the last row's chip fell out of
    the block entirely.  Every row's chip must exist, and every row's chip
    must share one right edge.
    """
    rows = block.locator(".speak-hotkey-row")
    edges: list[float] = []
    for i in range(rows.count()):
        row = rows.nth(i)
        chip = row.locator(".surface-state-chip")
        assert chip.count() == 1, (
            f"row {row.locator('.speak-hotkey-name').inner_text()!r} "
            f"has {chip.count()} state chips at {width}"
        )
        box = chip.bounding_box()
        row_box = row.bounding_box()
        assert box is not None and row_box is not None
        # Inside its own row, not spilled past it.
        assert box["x"] + box["width"] <= row_box["x"] + row_box["width"] + 1, (
            f"a state chip spills out of its row at {width}"
        )
        edges.append(round(box["x"] + box["width"], 1))
    if edges:
        assert max(edges) - min(edges) <= 1.0, (
            f"the state chips are drawn at {len(set(edges))} different right "
            f"edges at {width}: {edges}"
        )

def _walk(page: Any, machine: _Platform, width: int) -> None:
    """The five states, in the order a first-time installer meets them."""

    # ── 1. every grant refused: the full block ──
    machine.all_denied()
    _custody_stage_speak(page)
    block = page.locator('[data-testid="speak-hotkey"]')
    block.wait_for(timeout=15000)
    for pid in ("microphone", "input_monitoring", "accessibility"):
        row = page.locator(f'[data-testid="speak-permission-{pid}"]')
        assert row.count() == 1, f"{pid} row missing"
        text = row.inner_text()
        assert "SYSTEM SETTINGS" in text and "PRIVACY & SECURITY" in text, text
        assert "DENIED" in text.upper(), text
    assert "UNAVAILABLE" in block.inner_text().upper()
    # never a modal, never a sentence
    assert page.locator('[role="dialog"]').count() == 0
    _no_overflow(block, width)
    _one_grammar(block, width)
    _custody_shot(page, "all-denied", width)

    # ── 2. one refused: the granted two stay silent ──
    machine.one_denied()
    _custody_stage_speak(page)
    block = page.locator('[data-testid="speak-hotkey"]')
    block.wait_for(timeout=15000)
    assert page.locator('[data-testid="speak-permission-input_monitoring"]').count() == 1
    assert page.locator('[data-testid="speak-permission-microphone"]').count() == 0
    assert page.locator('[data-testid="speak-permission-accessibility"]').count() == 0
    # The listener DID install, and the key still will not work. The head chip
    # must not claim ACTIVE over a DENIED row (the shots caught that green).
    head = block.locator(".speak-hotkey-head")
    assert "BLOCKED" in head.inner_text().upper(), head.inner_text()
    assert "ACTIVE" not in head.inner_text().upper(), head.inner_text()
    _no_overflow(block, width)
    _one_grammar(block, width)
    _custody_shot(page, "one-denied", width)

    # ── 3. never asked: the first-installer state ──
    machine.never_asked()
    _custody_stage_speak(page)
    block = page.locator('[data-testid="speak-hotkey"]')
    block.wait_for(timeout=15000)
    assert "NOT ASKED" in block.inner_text().upper(), block.inner_text()
    # Accessibility has no not-determined answer; it reads DENIED beside them.
    assert "DENIED" in page.locator(
        '[data-testid="speak-permission-accessibility"]'
    ).inner_text().upper()
    _no_overflow(block, width)
    _one_grammar(block, width)
    _custody_shot(page, "not-asked", width)

    # ── 4. the listener itself failed, with every grant in hand ──
    machine.listener_failed()
    _custody_stage_speak(page)
    block = page.locator('[data-testid="speak-hotkey"]')
    block.wait_for(timeout=15000)
    reason = page.locator('[data-testid="speak-hotkey-reason"]')
    assert reason.inner_text() == "PYNPUT MISSING", reason.inner_text()
    # The raw exception never reaches the face (UX canon A10).
    assert "pynput is not available" not in block.inner_text()
    # A granted set draws no permission rows at all.
    assert page.locator('[data-testid^="speak-permission-"]').count() == 0
    _no_overflow(block, width)
    _one_grammar(block, width)
    _custody_shot(page, "listener-failed", width)

    # ── 5. he grants it and presses the ONE verb: the block goes away ──
    machine.all_granted()
    page.locator('[data-testid="speak-hotkey-recheck"]').click()
    page.locator('[data-testid="speak-hotkey"]').wait_for(state="detached", timeout=15000)
    assert page.locator('[data-testid="speak-hotkey"]').count() == 0
    # ...and nothing green took its place.
    assert "HOTKEY" not in page.locator(".speak-face").inner_text()
    _custody_shot(page, "all-granted", width)

@pytest.mark.e2e
@pytest.mark.requires_meeting
def test_hotkey_custody_block_1440(tmp_path, monkeypatch):
    """The five custody states at 1440."""
    _ensure_build()
    server, url, machine = _custody_boot(tmp_path, monkeypatch)
    errors: list[str] = []
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page()
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.set_viewport_size({"width": 1440, "height": 900})
            _custody_init_desk(page, url)
            _walk(page, machine, 1440)
            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()

@pytest.mark.e2e
@pytest.mark.requires_meeting
def test_hotkey_custody_block_393(tmp_path, monkeypatch):
    """The same five at 393, where the path tokens fight for room."""
    _ensure_build()
    server, url, machine = _custody_boot(tmp_path, monkeypatch)
    errors: list[str] = []
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page()
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.set_viewport_size({"width": 393, "height": 852})
            _custody_init_desk(page, url)
            _walk(page, machine, 393)
            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()


# Voice command: authenticated Talk → real stored note → the returned sticky.
def _voice_command_ready_speech(self: Any, principal: Any = None) -> dict[str, Any]:
    """The disk-read speech seam: this rig supplies a ready local model."""
    _ = self, principal
    return {
        "state": "ready",
        "files": [{"key": "whisper", "label": "Speech", "size_bytes": 1, "on_device": True}],
        "bytes_total": 0,
        "bytes_done": 0,
        "percent": 100,
        "egress": None,
        "speech": {"model": "base", "backend": "auto", "state": "on_device", "ready": True, "bytes": 0},
        "local_engine": {"ready": True},
        "meaning_search": "on",
        "error": "",
        "error_code": "",
    }


@pytest.mark.timeout(120, method="thread")
@pytest.mark.parametrize("width,height", [(1440, 900), (393, 852)])
def test_new_note_voice_command_creates_and_opens_the_returned_sticky(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int, height: int
) -> None:
    import os
    from holdspeak.services.local_ai_setup_service import LocalAISetupService

    # Readiness is a service read. It does not replace the command dispatcher,
    # the MCP operation, the database, or the browser's authenticated socket.
    monkeypatch.setattr(LocalAISetupService, "status", _voice_command_ready_speech)
    monkeypatch.setenv("PLAYWRIGHT_BROWSERS_PATH", os.environ.get(
        "PLAYWRIGHT_BROWSERS_PATH", str(Path.home() / "Library/Caches/ms-playwright")
    ))
    _ensure_build()

    server, url = _boot(
        tmp_path,
        monkeypatch,
        on_transcribe=lambda _audio, **_kwargs: "new note",
        token=TOKEN,
    )
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser = pw.chromium.launch(args=[
                "--use-fake-ui-for-media-stream",
                "--use-fake-device-for-media-stream",
                "--use-file-for-fake-audio-capture=" + str(Path(__file__).resolve().parents[2] / "tests/fixtures/core_path_smoke_16k.wav"),
            ])
            page = browser.new_page(viewport={"width": width, "height": height})
            _init_desk(page, url, token=TOKEN)
            _stage_speak(page)

            # The chair also owns a Talk button. The command must travel through
            # the Speak face's authenticated stream, so scope both controls to
            # that face rather than relying on DOM order.
            speak_face = page.locator(".speak-face")
            talk = speak_face.get_by_role("button", name="Talk")
            talk.wait_for(timeout=15_000)
            talk.click()
            stop = speak_face.get_by_role("button", name="Listening · Stop")
            stop.wait_for(timeout=15_000)
            page.wait_for_timeout(500)
            stop.click()

            sticky = page.locator("[id^='pullout:note:']").first
            sticky.wait_for(timeout=20_000)
            # The pullout id is the exact server-created note id carried by the
            # fired frame, and the API read proves that object was stored.
            note_id = sticky.get_attribute("id").removeprefix("pullout:note:")
            notes = page.evaluate(
                "async (token) => (await (await fetch('/api/notes', {headers: {Authorization: 'Bearer ' + token}})).json()).notes",
                TOKEN,
            )
            assert any(str(note.get("id")) == note_id for note in notes), notes
            assert page.locator(".speak-result").count() == 0
            _settle(page)
            shot = SHOTS / f"new-note-{width}.png"
            sticky.screenshot(path=str(shot))
            assert shot.stat().st_size > 2_000
            browser.close()
    finally:
        server.stop()
