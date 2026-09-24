"""HS-201-01 — the desk names the one thing the meeting path needs.

Cold, isolated HOME. Nothing is seeded into the model library, so the
`capability:meeting.deferred_analysis` head does not exist and the
meeting-intel queue would refuse with `no_assignment`
(`holdspeak/services/inference_route_plan_service.py:399-403`) — the very
refusal the charter walk found in the hub log with nothing on the glass
(`audits/face-walk-opus.md` defect 1).

Tests:
  1. test_chair_names_the_blocker — the Chair draws ONE row with ONE
     library Button (`No engine yet` while BOTH halves of the path are
     missing), the headline is not `Nothing needs you`, the Button opens
     Models, and REAL capability-scope assignments through the service
     move the face on the OPEN desk: `No engine for speech` once the
     summary half is fixed, then no row at all. 1440 + 393.
  2. test_meetings_window_over_a_failed_row — the Meetings window never
     reads `Nothing needs you` above a FAILED meeting. 1440 + 393.
  3. test_chip_and_trust_agree — the chrome egress chip and the Trust
     window state the same thing on a virgin desk. 1440 + 393.
"""
from __future__ import annotations

import re
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from .glass_infra import (
    REPO,
    _api,
    _assert_clean,
    _boot,
    _ensure_build,
    _normal_chair,
    _settle,
    assign_engine,
    engine_profile,
)
from tests._evidence import evidence_dir

pytest.importorskip("playwright.sync_api", reason="HS-201 glass needs Playwright")

SHOTS = evidence_dir("pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/story-01-shots")
TOKEN = "hs201-one-thing"
SUMMARY_CAPABILITY = "meeting.deferred_analysis"
SPEECH_CAPABILITY = "speech.transcribe"


def _quiet_concierge(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep the Models window off the real hardware scan (speed, not truth)."""
    import holdspeak.services.concierge_service as cs

    detection = {
        "engines": [],
        "hardware": {"capability": {"apple_silicon": True, "system": "darwin",
                                    "architecture": "arm64", "ram_gb": 36}},
        "runtimes": [],
        "checkedAt": "2026-09-19T09:41:00Z",
    }
    monkeypatch.setattr(cs, "detect", lambda **_: detection)
    monkeypatch.setattr(cs, "propose", lambda **_: {"rows": [], "receipt": {"groups": 0, "engines": 0, "waiting": 0}})


def _clear_speech_head() -> None:
    """Make the cold desk cold, the product's way.

    The startup migration creates a `capability:speech.transcribe` head on
    a HOME where a local speech runtime is importable
    (`tests/unit/test_phase151_fired_session_admission.py:107-113` names
    the same accident), so a rig that wants the virgin state clears it
    through the real service -- a raw DELETE of the head leaves the
    revision ledger behind it, and the next save collides on it.
    """
    from holdspeak.db import get_database
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services.errors import NotFound
    from holdspeak.services.inference_assignment_service import InferenceAssignmentService

    service = InferenceAssignmentService(get_database())
    owner = Principal(PrincipalKind.OWNER, "hs201-owner")
    scope = {"kind": "capability", "capability_id": SPEECH_CAPABILITY}
    try:
        current = service.get_assignment(owner, scope)
    except NotFound:
        return
    service.clear_assignment(owner, {
        "command_id": "hs201-clear-speech",
        "expected_revision": int(current["revision"]),
        "scope": scope,
        "capability_id": SPEECH_CAPABILITY,
    })


def _settings_updated(page: Any) -> None:
    """Fire the product's own "setup changed" signal on the open page.

    `RETURN_TO_TASK_EVENT` is `holdspeak:settings-updated`
    (`web/src/desk/returnToTask.ts:37`); `announceTaskReturn` dispatches
    exactly this event on `window` (`:113`), and the Models face calls it
    after a successful apply
    (`web/src/features/concierge/useConciergeController.ts:507`). Faces
    holding an unfinished task re-read on it -- the Chair's SETUP row is
    one.
    """
    page.evaluate(
        "() => window.dispatchEvent(new Event('holdspeak:settings-updated'))"
    )


def _seed_failed_meeting() -> None:
    """One finalized meeting whose intelligence failed."""
    from holdspeak.db import get_database

    db = get_database()
    now = datetime.now()
    with db._connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO meetings "
            "(id, started_at, ended_at, title, duration_seconds, "
            " intel_status, capture_status, provenance) "
            "VALUES (?, ?, ?, ?, ?, 'error', 'finalized', 'desktop')",
            (
                "m-failed",
                (now - timedelta(hours=2)).isoformat(),
                (now - timedelta(hours=1, minutes=30)).isoformat(),
                "Platform sync",
                1800.0,
            ),
        )
        conn.commit()


def _open_surface(page: Any, key: str) -> None:
    page.evaluate(
        """([key]) => {
          sessionStorage.setItem(
            "hs.desk.staged-surface-open", JSON.stringify({key})
          );
        }""",
        [key],
    )
    page.reload(wait_until="load")
    _normal_chair(page)


def _arrive(page: Any, base: str) -> None:
    page.goto(f"{base}/?token={TOKEN}", wait_until="load")
    _api(page, "POST", "/api/desk/seed", token=TOKEN)
    _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
    _normal_chair(page)
    page.locator("[data-testid='arrival-display']").wait_for(timeout=10_000)
    _settle(page)


class TestOneThing:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        _ensure_build()
        _quiet_concierge(monkeypatch)
        self.server, self.base = _boot(tmp_path, monkeypatch, token=TOKEN)
        _clear_speech_head()
        yield
        self.server.stop()

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", [1440, 393])
    def test_chair_names_the_blocker(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        SHOTS.mkdir(parents=True, exist_ok=True)
        suffix = str(width)
        errors: list[str] = []
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": width, "height": 900})
            page.emulate_media(reduced_motion="reduce")
            page.on("pageerror", lambda err: errors.append(str(err)))

            _arrive(page, self.base)

            # ── the product's own truth: no capability head ──
            roster = _api(page, "GET", "/api/inference/assignments", token=TOKEN)
            summary_row = next(
                row for row in roster["task_overrides"]
                if row["id"] == SUMMARY_CAPABILITY
            )
            assert summary_row["has_override"] is False, summary_row
            assert summary_row["effective"]["status"] == "no_assignment", summary_row
            speech_row = next(
                row for row in roster["task_overrides"]
                if row["id"] == SPEECH_CAPABILITY
            )
            assert speech_row["effective"]["status"] == "no_assignment", speech_row

            # ── neither engine is one state: ONE row, ONE filled Button
            #    (counsel fix round, second pass, ruling 2) ──
            section = page.locator("[data-testid='arrival-blocker']")
            section.wait_for(timeout=10_000)
            page.wait_for_function(
                """() => {
                  const el = document.querySelector("[data-testid='arrival-blocker']");
                  return el && el.textContent.includes("No engine yet");
                }""",
                timeout=10_000,
            )
            rows = page.locator("[data-testid='arrival-blocker-row']")
            assert rows.count() == 1, f"{rows.count()} blocker rows at {width}"
            said = section.text_content() or ""
            assert "No engine yet" in said, said
            assert "No engine for speech" not in said, said
            assert "No engine for summaries" not in said, said
            verbs = section.locator("button")
            assert verbs.count() == 1, f"{verbs.count()} verbs at {width}"
            assert (verbs.first.text_content() or "").strip() == "Choose an engine"
            # UX-CANON A1: the library Button, never a raw element
            assert "btn" in (verbs.first.get_attribute("class") or "")
            # The SETUP verb never adds a FILLED primary: the ratified law
            # gives that to the attention band, and this face is quiet
            # (full-suite fallout; test_hs200_attention_glass.py:463, :694).
            assert page.locator(".btn--primary").count() == 0, (
                f"{page.locator('.btn--primary').count()} filled primaries at {width}"
            )

            # ── the headline does not lie over it ──
            headline = page.locator("[data-testid='arrival-display']").text_content() or ""
            assert headline.strip() != "Nothing needs you", headline

            page.screenshot(path=str(SHOTS / f"chair-blocker-{suffix}.png"), full_page=True)

            # ── the Button opens Models ──
            page.locator("[data-testid='arrival-blocker-verb-engines']").click()
            page.locator("[data-testid='concierge-root']").wait_for(timeout=15_000)
            # Close it again so the "row is gone" shot is the Chair itself.
            page.locator("[data-testid='concierge-cancel']").click()
            _settle(page)

            # ── the shot of the row the repair must clear ──
            page.screenshot(path=str(SHOTS / f"chair-before-repair-{suffix}.png"), full_page=True)
            section.screenshot(path=str(SHOTS / f"chair-no-engine-yet-{suffix}.png"))

            # ── assign the engines the product's way, ONE at a time; the
            #    face follows on the OPEN desk, with no navigation
            #    (counsel fix round, Astra finding 1: the old rig
            #    re-arrived here, so the machine passed while the owner's
            #    open Desk kept asking) ──
            engine_profile()
            assign_engine(SUMMARY_CAPABILITY, 1)

            # The product's OWN return signal, not a synthetic focus
            # (counsel round 2, condition 1): `holdspeak:settings-updated`
            # is what Models announces the moment it applies a set
            # (`web/src/features/concierge/useConciergeController.ts:507`
            # -> `announceTaskReturn`, `web/src/desk/returnToTask.ts:113`,
            # the event named at `:37`). This rig stubs the Concierge scan
            # (`_quiet_concierge`), so the Models face has no row to apply;
            # the rig therefore fires the same signal Models fires, on the
            # same open page. No reload, no goto, no remount.
            _settings_updated(page)
            page.wait_for_function(
                """() => {
                  const el = document.querySelector("[data-testid='arrival-blocker']");
                  return el && el.textContent.includes("No engine for speech");
                }""",
                timeout=15_000,
            )
            # With exactly one half missing, the row names that half.
            said = section.text_content() or ""
            assert "No engine yet" not in said, said
            assert page.locator("[data-testid='arrival-blocker-row']").count() == 1
            _settle(page)
            section.screenshot(path=str(SHOTS / f"chair-speech-row-{suffix}.png"))

            assign_engine(SPEECH_CAPABILITY, 2)
            roster = _api(page, "GET", "/api/inference/assignments", token=TOKEN)
            for capability in (SUMMARY_CAPABILITY, SPEECH_CAPABILITY):
                fixed = next(
                    row for row in roster["task_overrides"] if row["id"] == capability
                )
                assert fixed["has_override"] is True, fixed
                assert fixed["effective"]["status"] == "assigned", fixed

            _settings_updated(page)
            page.wait_for_function(
                """() => !document.querySelector("[data-testid='arrival-blocker']")""",
                timeout=15_000,
            )
            assert page.locator("[data-testid='arrival-blocker']").count() == 0, (
                f"blocker row survived the assignment on the OPEN desk at {width}"
            )
            headline = page.locator("[data-testid='arrival-display']").text_content() or ""
            assert headline.strip() == "Nothing needs you", headline

            page.screenshot(path=str(SHOTS / f"chair-assigned-{suffix}.png"), full_page=True)

            _assert_clean(page, errors)
            page.close()
            browser.close()

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", [1440, 393])
    def test_meetings_window_over_a_failed_row(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        SHOTS.mkdir(parents=True, exist_ok=True)
        _seed_failed_meeting()
        errors: list[str] = []
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": width, "height": 900})
            page.emulate_media(reduced_motion="reduce")
            page.on("pageerror", lambda err: errors.append(str(err)))

            _arrive(page, self.base)
            _open_surface(page, "review-meetings")

            headline = page.locator("[data-testid='meetings-headline']")
            headline.wait_for(timeout=15_000)
            page.wait_for_function(
                """() => {
                  const el = document.querySelector("[data-testid='meetings-headline']");
                  return el && el.textContent && el.textContent.trim().length > 0;
                }""",
                timeout=15_000,
            )
            _settle(page)
            text = (headline.text_content() or "").strip()
            assert text != "Nothing needs you", text
            assert text == "1 meeting failed", text

            page.screenshot(
                path=str(SHOTS / f"meetings-failed-{width}.png"), full_page=True
            )
            _assert_clean(page, errors)
            page.close()
            browser.close()

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", [1440, 393])
    def test_chip_and_trust_agree(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        SHOTS.mkdir(parents=True, exist_ok=True)
        errors: list[str] = []
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": width, "height": 900})
            page.emulate_media(reduced_motion="reduce")
            page.on("pageerror", lambda err: errors.append(str(err)))

            _arrive(page, self.base)

            # The product's own trust block: zero destinations enabled.
            setup = _api(page, "GET", "/api/setup/status", token=TOKEN)
            destinations = setup["trust"]["destinations"]
            assert not [d for d in destinations if d["enabled"]], destinations
            # ...while the permission that used to drive the chip is ON.
            assert setup["trust"]["actuators_enabled"] is True, setup["trust"]

            chip = page.locator(".egress-badge").first
            chip.wait_for(timeout=10_000)
            chip_text = (chip.text_content() or "").strip()
            assert "EXTERNAL REACH" not in chip_text.upper(), chip_text
            assert "THIS DEVICE" in chip_text.upper(), chip_text

            chip.click()
            window = page.locator(".desk-trust-window")
            window.wait_for(timeout=10_000)
            _settle(page)
            trust_text = window.text_content() or ""
            assert "All data stays on this device" in trust_text, trust_text
            assert "None" in trust_text, trust_text

            page.screenshot(
                path=str(SHOTS / f"chip-and-trust-{width}.png"), full_page=True
            )
            _assert_clean(page, errors)
            page.close()
            browser.close()

    # ── an unknown is never drawn as a clear desk (Astra finding 3) ──
    @pytest.mark.e2e
    @pytest.mark.parametrize("width", [1440, 393])
    def test_unknown_setup_is_its_own_row(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        SHOTS.mkdir(parents=True, exist_ok=True)
        errors: list[str] = []
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": width, "height": 900})
            page.emulate_media(reduced_motion="reduce")
            page.on("pageerror", lambda err: errors.append(str(err)))

            # The roster read fails. The Chair knows nothing about the
            # meeting path, and an unknown is not a clear desk.
            page.route(
                "**/api/inference/assignments",
                lambda route: route.abort(),
            )
            _arrive(page, self.base)

            section = page.locator("[data-testid='arrival-blocker']")
            section.wait_for(timeout=15_000)
            page.wait_for_function(
                """() => {
                  const el = document.querySelector("[data-testid='arrival-blocker']");
                  return el && el.textContent.includes("Could not read setup");
                }""",
                timeout=15_000,
            )
            rows = page.locator("[data-testid='arrival-blocker-row']")
            assert rows.count() == 1, f"{rows.count()} rows at {width}"
            verbs = section.locator("button")
            assert verbs.count() == 1, f"{verbs.count()} verbs at {width}"
            assert "btn" in (verbs.first.get_attribute("class") or "")
            headline = page.locator("[data-testid='arrival-display']").text_content() or ""
            assert headline.strip() != "Nothing needs you", headline
            _settle(page)

            page.screenshot(
                path=str(SHOTS / f"chair-unknown-setup-{width}.png"), full_page=True
            )
            _assert_clean(page, errors)
            page.close()
            browser.close()

    # ── inbound exposure is its own token (Astra finding 4) ──
    @pytest.mark.e2e
    @pytest.mark.parametrize("width", [1440, 393])
    def test_open_to_network_is_its_own_token(
        self, width: int, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from playwright.sync_api import sync_playwright

        import holdspeak.setup_status as setup_status

        SHOTS.mkdir(parents=True, exist_ok=True)
        real_trust_block = setup_status._trust_block

        def open_hub(config, *, web_bind="127.0.0.1", database=None):
            # The same hub, stated as it would be with an off-loopback
            # bind and no token: `web_bind` and `auth_token_set` are the
            # two fields the face reads (`setup_status.py:176-177`).
            block = real_trust_block(config, web_bind="192.168.1.43", database=database)
            block["auth_token_set"] = False
            return block

        monkeypatch.setattr(setup_status, "_trust_block", open_hub)

        errors: list[str] = []
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": width, "height": 900})
            page.emulate_media(reduced_motion="reduce")
            page.on("pageerror", lambda err: errors.append(str(err)))

            _arrive(page, self.base)

            setup = _api(page, "GET", "/api/setup/status", token=TOKEN)
            assert setup["trust"]["web_bind"] == "192.168.1.43", setup["trust"]
            assert setup["trust"]["auth_token_set"] is False, setup["trust"]
            assert not [d for d in setup["trust"]["destinations"] if d["enabled"]]

            token = page.locator("[data-testid='chrome-inbound']")
            token.wait_for(timeout=15_000)
            # The words are on the desktop bar and in the accessible name
            # at every width (counsel round 2, condition 2).
            assert "OPEN TO NETWORK" in (token.get_attribute("aria-label") or "").upper()
            if width > 720:
                assert "OPEN TO NETWORK" in (token.text_content() or "").upper()
            # The bar holds its own width: nothing is pushed off the edge.
            assert page.evaluate(
                "() => document.documentElement.scrollWidth <= window.innerWidth"
            ), f"the menubar overflows at {width}"
            # Search stays on the bar, whole (counsel round 2, condition
            # 2: the token used to push it off the edge). The desk's right
            # cluster overhangs the viewport by ~3px on this bar with or
            # without the token; the token may not make that worse.
            search = page.evaluate(
                """() => {
                  const el = document.querySelector('.desk-tools-launch');
                  if (!el) return null;
                  const r = el.getBoundingClientRect();
                  return {left: r.left, right: r.right, width: r.width};
                }"""
            )
            assert search is not None, "Search is not on the bar"
            assert search["width"] > 0, search
            assert search["right"] <= width + 3.5, (width, search)
            assert search["left"] >= -0.5, (width, search)
            # ...and the egress chip still answers only for egress.
            chip = page.locator(".egress-badge").first
            assert "THIS DEVICE" in (chip.text_content() or "").upper()

            chip.click()
            window = page.locator(".desk-trust-window")
            window.wait_for(timeout=10_000)
            _settle(page)
            line = page.locator("[data-testid='trust-inbound']").text_content() or ""
            assert "yes" in line, line
            assert "Token: not set" in line, line

            page.screenshot(
                path=str(SHOTS / f"open-to-network-{width}.png"), full_page=True
            )
            _assert_clean(page, errors)
            page.close()
            browser.close()


# ── HS-201-11: a quiet desk for the sitting ────────────────────────────
#
# The rehearsal's hub printed 34 tracebacks across two runs and the page
# logged eight 404s for shipped sound files on every desk load
# (audits/rehearsal-07-opus.md defects 6 and 8). This fence reads the
# WIRE and the CONSOLE of a cold arrival: no 4xx, no 5xx, no console
# error, and the head does not speak an all-clear over a row that asks.

QUIET_SHOTS = evidence_dir("pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/story-11-shots")

_SFX_REF = re.compile(r"""([^"'`]*)desk/sfx/""")


def _sfx_bases() -> set[str]:
    """Every path prefix the BUILT bundle asks the desk sounds for.

    The emitted chunks are hashed and replaced wholesale by a rebuild, so
    a scan that lands mid-build reads an empty or vanishing directory.
    That is a rebuild, not a missing reference: try again.
    """
    built = REPO / "holdspeak" / "static" / "_built" / "assets"
    for attempt in range(5):
        found: set[str] = set()
        for path in built.glob("*.js"):
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except FileNotFoundError:
                continue
            found.update(_SFX_REF.findall(text))
        if found:
            return {prefix + "desk/sfx/" for prefix in found}
        if attempt < 4:
            time.sleep(3)
    raise AssertionError("no sound reference in the built bundle")


def _seed_plain_meeting() -> None:
    """One finalized meeting whose summary ran and which holds NO action."""
    from holdspeak.db import get_database

    db = get_database()
    now = datetime.now()
    with db._connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO meetings "
            "(id, started_at, ended_at, title, duration_seconds, "
            " intel_status, capture_status, provenance) "
            "VALUES (?, ?, ?, ?, ?, 'ready', 'finalized', 'desktop')",
            (
                "m-plain",
                (now - timedelta(minutes=20)).isoformat(),
                (now - timedelta(minutes=19)).isoformat(),
                "Sprint planning rehearsal",
                60.0,
            ),
        )
        conn.commit()


class TestQuietDesk:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        _ensure_build()
        _quiet_concierge(monkeypatch)
        self.server, self.base = _boot(tmp_path, monkeypatch, token=TOKEN)
        _clear_speech_head()
        yield
        self.server.stop()

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", [1440, 393])
    def test_cold_arrival_is_quiet(self, width: int) -> None:
        """No failed request and no console error on a cold desk load."""
        from playwright.sync_api import sync_playwright

        QUIET_SHOTS.mkdir(parents=True, exist_ok=True)
        errors: list[str] = []
        console: list[str] = []
        failed: list[str] = []
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": width, "height": 900})
            # NOT reduced motion: `sfx.play` is a no-op under
            # `prefers-reduced-motion: reduce` (web/src/lib/sfx.ts,
            # `isMuted`), so a reduced-motion page never asks for a sound
            # file and this fence would read a clean wire while the owner's
            # desk logged eight 404s. `_settle` still waits out the
            # animations before the shot.
            page.emulate_media(reduced_motion="no-preference")
            page.on("pageerror", lambda err: errors.append(str(err)))
            page.on(
                "console",
                lambda msg: console.append(f"{msg.type}: {msg.text}")
                if msg.type == "error"
                else None,
            )
            page.on(
                "response",
                lambda response: failed.append(f"{response.status} {response.url}")
                if response.status >= 400
                else None,
            )

            _arrive(page, self.base)

            # The sounds load on the first gesture, not at boot: open a
            # desk window, which is what `sfx("latch")` rides
            # (web/src/desk/store/windowFactory.ts:48). Without the fix
            # this is where eight `/desk/sfx/*.ogg` 404s land.
            _open_surface(page, "review-meetings")
            page.locator("[data-testid='meetings-headline']").wait_for(timeout=15_000)
            _settle(page)
            page.wait_for_timeout(1_500)

            assert not failed, failed
            assert not console, console

            # ── the six desk sounds (defect 8) ──
            # `play()` is a no-op until a gesture the mic owns, so this
            # fence does not wait for one: it reads the URL the SHIPPED
            # bundle asks for and makes the hub answer it. The rehearsal's
            # eight failures were `/desk/sfx/*.ogg`, root-relative, while
            # the bundle (and its public art) is mounted under `/_built`
            # (holdspeak/web_server.py:1376).
            bases = _sfx_bases()
            assert len(bases) == 1, bases
            base = bases.pop()
            assert base != "/", base
            for name in ("key-down", "key-up", "latch", "land", "file", "error"):
                for extension in ("ogg", "wav"):
                    url = f"{self.base}{base}{name}.{extension}"
                    status = page.evaluate(
                        "(u) => fetch(u).then(r => r.status)", url
                    )
                    assert status == 200, f"{status} {url}"

            page.screenshot(
                path=str(QUIET_SHOTS / f"quiet-arrival-{width}.png"), full_page=True
            )
            _assert_clean(page, errors)
            page.close()
            browser.close()

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", [1440, 393])
    def test_the_calendar_offer_never_moves_the_count(self, width: int) -> None:
        """The SETUP row asks; the calendar row offers. The head says one."""
        from playwright.sync_api import sync_playwright

        QUIET_SHOTS.mkdir(parents=True, exist_ok=True)
        errors: list[str] = []
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": width, "height": 900})
            page.emulate_media(reduced_motion="reduce")
            page.on("pageerror", lambda err: errors.append(str(err)))

            _arrive(page, self.base)

            # The desk is cold: no engine for the meeting path, no calendar.
            door = _api(page, "GET", "/api/door", token=TOKEN)
            assert door["calendar_configured"] is False, door.get("calendar_configured")

            section = page.locator("[data-testid='arrival-blocker']")
            section.wait_for(timeout=15_000)
            calendar = page.locator("[data-testid='arrival-connect-calendar']")
            calendar.wait_for(timeout=15_000)
            assert "Connect calendar" in (calendar.text_content() or "")

            # ONE row asks (SETUP). The calendar row is an OFFER beside it
            # and never moves the count (owner's ruling: a desk with no
            # calendar must not say `1 need you` for ever, tenet 3).
            assert page.locator("[data-testid='arrival-blocker-row']").count() == 1
            page.wait_for_function(
                """() => {
                  const el = document.querySelector("[data-testid='arrival-display']");
                  return el && el.textContent.trim() === "1 need you";
                }""",
                timeout=15_000,
            )
            headline = (
                page.locator("[data-testid='arrival-display']").text_content() or ""
            ).strip()
            assert headline == "1 need you", headline
            # One all-clear per screen: this screen has none to print.
            assert page.get_by_text("Nothing needs you").count() == 0

            _settle(page)
            page.screenshot(
                path=str(QUIET_SHOTS / f"head-over-setup-and-offer-{width}.png"),
                full_page=True,
            )
            _assert_clean(page, errors)
            page.close()
            browser.close()

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", [1440, 393])
    def test_no_open_actions_filter_over_a_meeting_with_no_action(self, width: int) -> None:
        """A filter that can match nothing is not drawn."""
        from playwright.sync_api import sync_playwright

        QUIET_SHOTS.mkdir(parents=True, exist_ok=True)
        _seed_plain_meeting()
        errors: list[str] = []
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": width, "height": 900})
            page.emulate_media(reduced_motion="reduce")
            page.on("pageerror", lambda err: errors.append(str(err)))

            _arrive(page, self.base)
            _open_surface(page, "review-meetings")
            page.locator("[data-testid='meetings-headline']").wait_for(timeout=15_000)
            page.get_by_text("Sprint planning rehearsal").first.wait_for(timeout=15_000)

            # The product's own truth: the meeting holds no open action.
            actions = _api(page, "GET", "/api/all-action-items", token=TOKEN)
            assert actions["action_items"] == [], actions

            _settle(page)
            assert page.locator("[data-testid='meetings-facets']").count() == 0
            assert page.get_by_text("HAS OPEN ACTIONS").count() == 0

            page.screenshot(
                path=str(QUIET_SHOTS / f"no-open-actions-filter-{width}.png"),
                full_page=True,
            )
            _assert_clean(page, errors)
            page.close()
            browser.close()
