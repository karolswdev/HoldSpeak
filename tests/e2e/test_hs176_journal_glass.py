"""HS-176-03 — the Journal wing glass rig.

Artboard assertions on the settled boards (`assets/mockups/Journal*.dc.html`)
at 1440 and 393:

- **stream** — the day band, the row grammar (time · transcript ·
  `LANDED IN <label>` · `N MS` · the one APPLIED/TAUGHT slot · the human
  source badge), the four filter tokens, `Clear` present, NO caption count.
- **row-open** — one row opened in place keeps every verb (EditInPlace,
  `Replay` · `Copy` · `Delete`) — the 175 law, ruling R11.
- **filtered** — tapping `DICTATION` narrows the stream through the route's
  `source` param and the token reads active.
- **search-final** — a search hit that lives only in the corrected
  `final_text` wears `IN FINAL`, in the mark slot every row widens while the
  search runs (counsel C15).
- **live filter** — a pushed row the ACTIVE filter excludes never appears
  (counsel C2); crossing back to `ALL` loads it from the wire.
- **quiet** — an empty journal reads the token `NOTHING SPOKEN`, the four
  filter tokens are still there (no sparse rule, ruling R6), and `Clear` is
  withheld (a verb that does nothing is a lie, UX-CANON A.11).

The seed goes through the PRODUCT's own seams inside an isolated HOME: the
durable repository the live runtime resolves
(`web_runtime._dictation_journal_repo`) handed to `MeetingWebServer`, and the
real `DictationJournalRecorder.record` — the one write chokepoint, which
secret-filters, writes the named INSERT, prunes to retention and emits the
`dictation.journal.entry` frame. `taught_from` is set through the product's
own teach route (`POST /api/dictation/journal/{id}/correct`).

Shots land in
`pm/roadmap/holdspeak/phase-176-the-speak-loop/assets/story-03-shots/`.
"""
from __future__ import annotations

import os
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from .glass_infra import (
    _api,
    _assert_clean,
    _ensure_build,
    _normal_chair,
    _settle,
)

pytest.importorskip("playwright.sync_api", reason="Journal glass needs Playwright")

SHOTS = (
    Path(__file__).resolve().parents[2]
    / "pm/roadmap/holdspeak/phase-176-the-speak-loop/assets/story-03-shots"
)
SHOTS.mkdir(parents=True, exist_ok=True)

TOKEN = "hs176-journal"

#: Five rows across the four sources the recorder writes; one carries
#: `corrections_applied` (the `APPLIED` chip), one is taught FROM (`TAUGHT`).
SEED = [
    {
        "transcript": "Cut the Q4 scope to the payments path",
        "source": "dictation",
        "target": "claude_code",
        "ms": 44.0,
        "applied": [],
    },
    {
        "transcript": "Move the design review to Thursday",
        "source": "dry_run",
        "target": None,
        "ms": 33.0,
        "applied": [],
    },
    {
        "transcript": "Draft the release note for the metrics change",
        "source": "hotkey",
        "target": "editor",
        "ms": 55.0,
        "applied": [],
    },
    {
        "transcript": "Payments cut-over runbook needs a second reviewer",
        "source": "browser",
        "target": "browser",
        "ms": 62.0,
        "applied": [],
    },
    {
        "transcript": "Ship the Q4 platform in October",
        "source": "dictation",
        "target": "claude_code",
        "ms": 38.0,
        "applied": [7],
    },
]

#: The row the owner taught FROM — it wears `TAUGHT`, never `APPLIED`.
TAUGHT_TRANSCRIPT = "Move the design review to Thursday"


# ── Boot: glass_infra's isolated hub, plus the durable journal ─────


def _boot_with_journal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, *, token: str = TOKEN
) -> tuple[Any, str]:
    """`glass_infra._boot` with the product's durable journal repository.

    `_boot` leaves `dictation_journal_repository=None`, which makes the
    recorder a deliberate no-op (a bare server journals nothing). The Journal
    wing has nothing to draw without it, so this boot resolves the repository
    through the same factory the live runtime uses
    (`web_runtime._dictation_journal_repo`, `web_runtime.py:113-125`) — after
    HOME and the DB path are redirected into `tmp_path`, so the owner's real
    database is never opened.
    """
    import holdspeak.config as config_module
    import holdspeak.db.core as db_core
    from holdspeak.db import reset_database
    from holdspeak.web_runtime import _dictation_journal_repo
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
    monkeypatch.setattr(
        config_module, "CONFIG_FILE", home / ".holdspeak" / "config.json"
    )
    monkeypatch.setattr(db_core, "DEFAULT_DB_PATH", tmp_path / "holdspeak.db")
    reset_database()

    server = MeetingWebServer(
        WebRuntimeCallbacks(
            on_bookmark=lambda *_: None,
            on_stop=lambda: None,
            get_state=lambda: {},
        ),
        auth_token=token,
        dictation_journal_repository=_dictation_journal_repo(),
    )
    return server, server.start()


def _seed_journal(server: Any, *, taught: bool = True) -> dict[str, int]:
    """Write the five rows through the recorder — the product's chokepoint.

    `taught` flips `corrected` on one row through the repository seam the teach
    route itself calls (`db/journal.py:181-201`), so the boards' `TAUGHT` token
    has a row to sit on without a second teach.
    """
    ids: dict[str, int] = {}
    for spec in SEED:
        run = SimpleNamespace(
            final_text=spec["transcript"],
            stage_results=[],
            total_elapsed_ms=spec["ms"],
            warnings=[],
            intent=None,
            short_circuited=True,
            corrections_applied=list(spec["applied"]),
        )
        target = (
            SimpleNamespace(id=spec["target"], details={})
            if spec["target"]
            else None
        )
        stored = server.dictation_journal.record(
            run,
            source=spec["source"],
            transcript=spec["transcript"],
            target_profile=target,
        )
        assert stored is not None, f"the recorder wrote nothing for {spec['source']}"
        ids[str(spec["transcript"])] = int(stored.id)
    if taught:
        assert server.dictation_journal.repository.mark_corrected(
            ids[TAUGHT_TRANSCRIPT]
        )
    return ids


# ── Helpers ────────────────────────────────────────────────────────


def _init_desk(page: Any, url: str) -> None:
    page.goto(f"{url}/?token={TOKEN}", wait_until="load")
    _api(page, "PUT", "/api/setup/onboarding",
         {"disposition": "completed"}, token=TOKEN)
    _normal_chair(page)


def _open_journal(page: Any) -> None:
    """Stage the Speak surface, then cross to the Journal wing."""
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
    page.get_by_role("tab", name="Journal").click()
    page.locator(".speak-journal").wait_for(timeout=10000)
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


def _filter_token(page: Any, label: str) -> Any:
    return page.locator(".surface-filter-token").filter(has_text=label).first


def _assert_row_grammar(page: Any) -> None:
    """The board's row: the day band, the cells, the one mark slot, the badge."""
    rows = page.locator(".speak-journal .surface-ledger-row")
    assert rows.count() == len(SEED), f"rows: {rows.count()}"

    # The day band (TODAY) — the SurfaceStreamDay species, uppercase token.
    band = page.locator(".speak-journal .surface-stream-day-label").first
    assert band.count() > 0
    assert band.inner_text().strip().upper() == "TODAY", band.inner_text()

    body = page.locator(".speak-journal").inner_text()
    # Labels, never raw ids (canon E.4).
    assert "LANDED IN CLAUDE CODE" in body, body
    assert "LANDED IN EDITOR" in body, body
    assert "claude_code" not in body, body
    assert "dry_run" not in body, body
    # The latency cell is uppercase (the board's `38 MS`, never `38 ms`).
    assert "38 MS" in body, body
    assert " ms" not in body, body

    # Human source badges in the trailing slot, one per row.
    badges = page.locator(".speak-journal .surface-ledger-trailing").all_inner_texts()
    assert sorted(b.strip() for b in badges) == sorted(
        ["DICTATION", "DICTATION", "DRY RUN", "HOTKEY", "BROWSER"]
    ), badges

    # The APPLIED / TAUGHT slot exists on EVERY row (an empty one never moves
    # its neighbours), and each token appears exactly once, with no count.
    marks = page.locator(".speak-journal .journal-mark")
    assert marks.count() == len(SEED), marks.count()
    assert page.locator(".speak-journal .journal-mark", has_text="APPLIED").count() == 1
    assert page.locator(".speak-journal .journal-mark", has_text="TAUGHT").count() == 1
    assert "SIMILAR" not in body, body
    assert "LEARNED" not in body, body

    # No caption count on this wing — the footer says `N TODAY` once (A.7).
    caption = page.locator(".speak-journal .surface-ledger-count").inner_text()
    assert caption.strip() == "", caption

    # The four filter tokens, ALL active.
    tokens = page.locator(".speak-journal .surface-filter-token").all_inner_texts()
    assert [t.strip() for t in tokens] == ["ALL", "DICTATION", "BROWSER", "HOTKEY"], tokens
    assert _filter_token(page, "ALL").get_attribute("aria-pressed") == "true"

    # Clear is present once the ledger holds a row.
    assert page.get_by_role("button", name="Clear").count() == 1

    # Every verb is the library Button (A.1) — no raw <button> in the wing.
    raw = page.evaluate(
        """() => {
            const wing = document.querySelector('.speak-journal');
            if (!wing) return ['no wing'];
            return Array.from(wing.querySelectorAll('button'))
              .filter(b => !b.classList.contains('btn')
                        && !b.classList.contains('surface-ledger-line')
                        && !b.classList.contains('desk-mic'))
              .map(b => b.className || b.textContent);
        }"""
    )
    assert raw == [], raw


# ── Tests ──────────────────────────────────────────────────────────


@pytest.mark.e2e
@pytest.mark.requires_meeting
@pytest.mark.parametrize("width,height", [(1440, 900), (393, 852)])
def test_journal_stream(tmp_path, monkeypatch, width, height):
    """The stream board at both widths: the row grammar and the tokens."""
    _ensure_build()
    server, url = _boot_with_journal(tmp_path, monkeypatch)
    errors: list[str] = []
    try:
        _seed_journal(server)
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page()
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.set_viewport_size({"width": width, "height": height})
            _init_desk(page, url)
            _open_journal(page)

            if width == 1440:
                _assert_row_grammar(page)
            else:
                # At 393 the wing still draws one row grammar; the cells fall
                # under the transcript and nothing overflows.
                assert page.locator(".speak-journal .journal-cells").count() == len(SEED)
                assert page.locator(".speak-journal .surface-filter-token").count() == 4

            _shot(page, "stream", width)
            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()


@pytest.mark.e2e
@pytest.mark.requires_meeting
@pytest.mark.parametrize("width,height", [(1440, 900), (393, 852)])
def test_journal_row_open(tmp_path, monkeypatch, width, height):
    """The row-open board: the 175 law — a replacing face keeps its verbs."""
    _ensure_build()
    server, url = _boot_with_journal(tmp_path, monkeypatch)
    errors: list[str] = []
    try:
        _seed_journal(server)
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page()
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.set_viewport_size({"width": width, "height": height})
            _init_desk(page, url)
            _open_journal(page)

            line = page.locator(".speak-journal .surface-ledger-line").first
            line.click()
            page.locator(".speak-journal .surface-ledger-open").wait_for(timeout=5000)
            _settle(page)

            opened = page.locator(".speak-journal .surface-ledger-open")
            assert opened.locator(".surface-edit-in-place").count() > 0
            for verb in ("Replay", "Copy", "Delete"):
                assert opened.get_by_role("button", name=verb).count() == 1, verb
            # In-world, never a dialog (rule A.4).
            assert page.locator('[role="dialog"]').count() == 0

            _shot(page, "row-open", width)
            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()


@pytest.mark.e2e
@pytest.mark.requires_meeting
@pytest.mark.parametrize("width,height", [(1440, 900), (393, 852)])
def test_journal_filtered(tmp_path, monkeypatch, width, height):
    """The filtered board: DICTATION narrows the stream through the route."""
    _ensure_build()
    server, url = _boot_with_journal(tmp_path, monkeypatch)
    errors: list[str] = []
    try:
        _seed_journal(server)
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page()
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.set_viewport_size({"width": width, "height": height})
            _init_desk(page, url)
            _open_journal(page)

            _filter_token(page, "DICTATION").click()
            page.wait_for_function(
                "() => document.querySelectorAll("
                "'.speak-journal .surface-ledger-row').length === 2",
                timeout=8000,
            )
            _settle(page)

            active = _filter_token(page, "DICTATION")
            assert active.get_attribute("aria-pressed") == "true"
            assert active.get_attribute("data-filter-active") is not None
            assert _filter_token(page, "ALL").get_attribute("aria-pressed") == "false"

            badges = page.locator(
                ".speak-journal .surface-ledger-trailing"
            ).all_inner_texts()
            assert [b.strip() for b in badges] == ["DICTATION", "DICTATION"], badges
            # The tokens stay; no match count is drawn beside them (R6).
            assert page.locator(".speak-journal .surface-filter-token").count() == 4
            assert "/" not in page.locator(
                ".speak-journal .surface-ledger-head"
            ).inner_text()

            _shot(page, "filtered", width)
            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()


@pytest.mark.e2e
@pytest.mark.requires_meeting
@pytest.mark.parametrize("width,height", [(1440, 900), (393, 852)])
def test_journal_quiet(tmp_path, monkeypatch, width, height):
    """The quiet board: NOTHING SPOKEN, the tokens present, no `Clear`."""
    _ensure_build()
    server, url = _boot_with_journal(tmp_path, monkeypatch)
    errors: list[str] = []
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page()
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.set_viewport_size({"width": width, "height": height})
            _init_desk(page, url)
            _open_journal(page)

            state = page.locator(".speak-journal .surface-state[data-kind='empty']")
            state.wait_for(timeout=8000)
            assert "NOTHING SPOKEN" in state.inner_text(), state.inner_text()
            assert "NOTHING MATCHES" not in state.inner_text()

            # The bar never returns null (no sparse rule) — he can still widen.
            assert page.locator(".speak-journal .surface-filter-token").count() == 4
            # A verb that does nothing is a lie (A.11).
            assert page.get_by_role("button", name="Clear").count() == 0

            _shot(page, "quiet", width)
            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()


@pytest.mark.e2e
@pytest.mark.requires_meeting
def test_journal_taught_row_wears_taught(tmp_path, monkeypatch):
    """`TAUGHT` marks the row he taught FROM — through the real teach route."""
    _ensure_build()
    server, url = _boot_with_journal(tmp_path, monkeypatch)
    errors: list[str] = []
    try:
        ids = _seed_journal(server, taught=False)
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page()
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.set_viewport_size({"width": 1440, "height": 900})
            _init_desk(page, url)

            entry_id = ids[TAUGHT_TRANSCRIPT]
            taught = _api(
                page,
                "POST",
                f"/api/dictation/journal/{entry_id}/correct",
                {"kind": "target", "value": "claude_code"},
                token=TOKEN,
            )
            assert taught.get("recorded") or taught.get("taught"), taught

            _open_journal(page)
            marked = page.locator(
                ".speak-journal .surface-ledger-row", has_text=TAUGHT_TRANSCRIPT
            )
            assert "TAUGHT" in marked.inner_text(), marked.inner_text()
            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()


@pytest.mark.e2e
@pytest.mark.requires_meeting
def test_journal_search_marks_a_final_text_only_hit(tmp_path, monkeypatch):
    """Counsel C15: the row shows the TRANSCRIPT, so a hit that lives only in
    `final_text` says so.

    Two rows carry the needle: one in its visible transcript, one only in the
    corrected `final_text` the row does not draw. The second wears
    `MATCHED · FINAL`; the first does not — and the slot is on BOTH, so the
    mark never moves its neighbours (canon D).
    """
    _ensure_build()
    server, url = _boot_with_journal(tmp_path, monkeypatch)
    errors: list[str] = []

    def _record(transcript: str, final_text: str) -> None:
        run = SimpleNamespace(
            final_text=final_text,
            stage_results=[],
            total_elapsed_ms=29.0,
            warnings=[],
            intent=None,
            short_circuited=True,
            corrections_applied=[5] if final_text != transcript else [],
        )
        stored = server.dictation_journal.record(
            run,
            source="dictation",
            transcript=transcript,
            target_profile=SimpleNamespace(id="claude_code", details={}),
        )
        assert stored is not None, transcript

    try:
        _seed_journal(server)
        # The real correction case: the transcript kept the misheard word, the
        # final text carries the corrected one.
        hidden = "postgress needs a bump before the cut-over"
        _record(hidden, "PostgreSQL needs a bump before the cut-over")
        visible = "The PostgreSQL bump is merged"
        _record(visible, visible)

        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page()
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.set_viewport_size({"width": 1440, "height": 900})
            _init_desk(page, url)
            _open_journal(page)

            # No search, no mark — and the shared slot keeps its idle width.
            assert page.locator(
                '.speak-journal .journal-cells[data-searching="true"]'
            ).count() == 0

            page.get_by_role(
                "textbox", name="Search the journal"
            ).fill("PostgreSQL")
            page.wait_for_function(
                "() => document.querySelectorAll("
                "'.speak-journal .surface-ledger-row').length === 2",
                timeout=8000,
            )
            _settle(page)

            # Every visible row's slot widens; the token marks the hidden hit.
            assert page.locator(
                '.speak-journal .journal-cells[data-searching="true"]'
            ).count() == 2
            marks = page.locator(
                ".speak-journal .surface-token", has_text="IN FINAL"
            )
            assert marks.count() == 1, marks.count()
            marked = page.locator(
                ".speak-journal .surface-ledger-row", has_text="IN FINAL"
            )
            assert hidden in marked.inner_text(), marked.inner_text()
            assert "PostgreSQL" not in marked.locator(
                ".surface-ledger-primary"
            ).inner_text()

            _shot(page, "search-final", 1440)
            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()


@pytest.mark.e2e
@pytest.mark.requires_meeting
def test_journal_live_frame_obeys_the_active_filter(tmp_path, monkeypatch):
    """Counsel C2: a pushed row the ACTIVE filter excludes never appears.

    Filtered to BROWSER, a HOTKEY utterance is recorded through the real
    recorder and really is broadcast on the one socket — the wing must reject
    it, because the filter is the face's one honest claim about what it is
    showing. Ordering makes the negative deterministic: a BROWSER row is
    recorded AFTER the hotkey one on the same socket, so once the browser row
    has landed the hotkey frame has certainly been delivered and dropped.
    Crossing back to ALL then loads it from the wire.
    """
    _ensure_build()
    server, url = _boot_with_journal(tmp_path, monkeypatch)
    errors: list[str] = []

    def _record(text: str, source: str, target: str) -> None:
        run = SimpleNamespace(
            final_text=text,
            stage_results=[],
            total_elapsed_ms=31.0,
            warnings=[],
            intent=None,
            short_circuited=True,
            corrections_applied=[],
        )
        stored = server.dictation_journal.record(
            run,
            source=source,
            transcript=text,
            target_profile=SimpleNamespace(id=target, details={}),
        )
        assert stored is not None, source

    try:
        _seed_journal(server)
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page()
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.set_viewport_size({"width": 1440, "height": 900})
            _init_desk(page, url)
            _open_journal(page)

            _filter_token(page, "BROWSER").click()
            page.wait_for_function(
                "() => document.querySelectorAll("
                "'.speak-journal .surface-ledger-row').length === 1",
                timeout=8000,
            )

            spoken_on_the_hotkey = "Tail the steward log on the hotkey"
            typed_in_the_browser = "Draft the release note in the browser"
            _record(spoken_on_the_hotkey, "hotkey", "terminal_shell")
            _record(typed_in_the_browser, "browser", "claude_code")

            # The later BROWSER frame lands; the earlier HOTKEY one must not.
            page.locator(
                ".speak-journal .surface-ledger-row", has_text=typed_in_the_browser
            ).first.wait_for(timeout=8000)
            _settle(page)
            assert page.locator(
                ".speak-journal .surface-ledger-row", has_text=spoken_on_the_hotkey
            ).count() == 0
            badges = page.locator(
                ".speak-journal .surface-ledger-trailing"
            ).all_inner_texts()
            assert [b.strip() for b in badges] == ["BROWSER", "BROWSER"], badges

            # ALL takes every source, so the held row is there on the wire.
            _filter_token(page, "ALL").click()
            page.locator(
                ".speak-journal .surface-ledger-row", has_text=spoken_on_the_hotkey
            ).first.wait_for(timeout=8000)
            _settle(page)
            assert page.locator(
                ".speak-journal .surface-ledger-row", has_text=spoken_on_the_hotkey
            ).count() == 1

            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()


@pytest.mark.e2e
@pytest.mark.requires_meeting
def test_journal_pushes_without_a_reload(tmp_path, monkeypatch):
    """A row written while the wing is open ARRIVES — pushed, not polled.

    The whole seam, live: `DictationJournalRecorder.record` →
    `WebServer.broadcast` → `/ws` → `RuntimeBusProvider` → the Journal's
    `subscribe("dictation.journal.entry")` → prepend. No reload, no poll.
    """
    _ensure_build()
    server, url = _boot_with_journal(tmp_path, monkeypatch)
    errors: list[str] = []
    try:
        _seed_journal(server)
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page()
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.set_viewport_size({"width": 1440, "height": 900})
            _init_desk(page, url)
            _open_journal(page)
            assert page.locator(".speak-journal .surface-ledger-row").count() == len(SEED)

            live = "Tail the steward log for the failed run"
            run = SimpleNamespace(
                final_text=live,
                stage_results=[],
                total_elapsed_ms=47.0,
                warnings=[],
                intent=None,
                short_circuited=True,
                corrections_applied=[],
            )
            stored = server.dictation_journal.record(
                run,
                source="hotkey",
                transcript=live,
                target_profile=SimpleNamespace(id="terminal_shell", details={}),
            )
            assert stored is not None

            # It arrives on its own — the page is never reloaded here.
            page.locator(
                ".speak-journal .surface-ledger-row", has_text=live
            ).first.wait_for(timeout=8000)
            _settle(page)
            rows = page.locator(".speak-journal .surface-ledger-row")
            assert rows.count() == len(SEED) + 1, rows.count()
            # Newest first, and never doubled.
            assert live in rows.first.inner_text(), rows.first.inner_text()
            assert page.locator(
                ".speak-journal .surface-ledger-row", has_text=live
            ).count() == 1

            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()
