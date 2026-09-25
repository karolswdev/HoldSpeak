"""PHILO-7-02 -- the delegation grant on the Remote Access ledger, fenced AS RENDERED.

The owner-ratified canvas (``pm/roadmap/holdspeak-philo/phase-7-the-desk-on-
the-contract/assets/story-02-canvas/README.md``, set A) built into the real
Settings window, driven through the REAL hub, the REAL grant and credential
routes and the REAL kernel, at 1440 and 393. After each transition the fence
reads the RENDERED row: ``readable_text`` (visible, in the viewport, and the
element owns its own centre and corners -- nothing covers it), and pointer
ownership of every verb (``elementFromPoint`` AND a real ``pointermove`` at
the centre and four corners, inset 1 px; the footer receipt included; a scroll
to the body's bottom edge included). The words come from the one constant the
face imports (``GRANT_WORDS``), read here from the source, so the words and
their fences change together.

Red: the face as on main (no grant verb, the caption ``CREDENTIALS``, no
footer receipt) -- ``docs/internal/philo/phase-7/article-xi/red-face.txt``.
"""
from __future__ import annotations

import re
import sqlite3
from pathlib import Path
from typing import Any

import pytest

import holdspeak.principals as principals
from holdspeak.principals import AgentCredentialStore

from .glass_infra import REPO, _api, _api_allow_error, _boot, _ensure_build, _settle
from .test_hs174_remote_settings_glass import _navigate_to_settings_hub, _open_system_module
from tests._evidence import evidence_dir

pytest.importorskip("playwright.sync_api", reason="the grant glass needs Playwright")

TOKEN = "hs174-remote-settings"  # the HS-174 navigation helpers use this token
IDENTITY = "desk-agent"
SHOTS = evidence_dir("pm/roadmap/holdspeak-philo/phase-7-the-desk-on-the-contract/assets/story-02-shots")


def _words() -> dict[str, str]:
    """``GRANT_WORDS`` as the face declares it (web/src/pages/cores/SettingsCore.tsx)."""
    source = (REPO / "web" / "src" / "pages" / "cores" / "SettingsCore.tsx").read_text(encoding="utf-8")
    block = source.split("export const GRANT_WORDS = {", 1)[1].split("} as const;", 1)[0]
    return dict(re.findall(r'(\w+): "([^"]+)"', block))


W = _words() if "export const GRANT_WORDS" in (REPO / "web/src/pages/cores/SettingsCore.tsx").read_text() else {
    # The face as on main declares no words: the fences below fail on the rendered page.
    "allow": "Allow filing", "stop": "Stop filing", "live": "FILING ALLOWED", "stopped": "FILING STOPPED",
    "actStop": "STOP FILING", "revokeCredential": "Revoke credential", "noCredential": "NO CREDENTIAL", "agents": "AGENTS",
}

# ── the rendered-page probes ────────────────────────────────────────────

_OWNS_JS = """(el, target44) => {
  const r = el.getBoundingClientRect();
  const vw = window.innerWidth, vh = window.innerHeight;
  // At 393 a verb's target is 44 px tall around its face (UX-CANON C); at
  // 1440 the painted face. The centre and four corners, inset 1 px.
  const cy = r.top + r.height / 2;
  const box = target44 ? {l: r.left, r: r.right, t: cy - 22, b: cy + 22} : {l: r.left, r: r.right, t: r.top, b: r.bottom};
  const pts = [[(box.l + box.r) / 2, cy], [box.l + 1, box.t + 1],
               [box.r - 1, box.t + 1], [box.l + 1, box.b - 1], [box.r - 1, box.b - 1]];
  const style = getComputedStyle(el);
  return {
    rect: {x: r.left, y: r.top, w: r.width, h: r.height},
    visible: style.visibility !== 'hidden' && style.display !== 'none' && Number(style.opacity) > 0,
    inViewport: r.left >= 0 && r.top >= 0 && r.right <= vw && r.bottom <= vh && r.width > 0 && r.height > 0,
    points: pts.map(([x, y]) => { const hit = document.elementFromPoint(x, y); return {x, y, owned: !!hit && (hit === el || el.contains(hit))}; }),
    fontPx: parseFloat(style.fontSize),
  };
}"""


def _readable(locator: Any, want: str) -> None:
    """readable_text: the text is there, visible, in the viewport, and nothing covers it."""
    locator.first.wait_for(state="visible", timeout=8_000)
    text = (locator.first.inner_text() or "").strip()
    assert want in text, f"{want!r} not in {text!r}"
    # As the owner reads it: scrolled to, then nothing may cover it.
    locator.first.evaluate("(el) => el.scrollIntoView({block: 'center', inline: 'nearest'})")
    probe = locator.first.evaluate(_OWNS_JS, False)
    assert probe["visible"] and probe["inViewport"], f"{want!r}: not readable: {probe}"
    uncovered = [p for p in probe["points"] if not p["owned"]]
    assert not uncovered, f"{want!r}: covered at {uncovered}"


def _pointer_owned(page: Any, button: Any, label: str, *, scrolled: bool = False) -> None:
    target44 = page.viewport_size["width"] <= 420
    """elementFromPoint AND a real pointermove at the centre + four corners.

    The verb is first scrolled to the middle of its scroll container, unless
    the caller placed it (``scrolled``: the scroll-edge case).
    """
    if not scrolled:
        button.evaluate("(el) => el.scrollIntoView({block: 'center', inline: 'nearest'})")
    probe = button.evaluate(_OWNS_JS, target44)
    assert probe["inViewport"], f"{label}: outside the viewport {probe['rect']}"
    page.evaluate("""() => { window.__pm = null; document.addEventListener('pointermove', (e) => { window.__pm = e.target; }, {capture: true}); }""")
    for point in probe["points"]:
        assert point["owned"], f"{label}: elementFromPoint does not reach it at {point} (rect {probe['rect']})"
        page.mouse.move(point["x"], point["y"])
        reached = button.evaluate("(el) => !!window.__pm && (window.__pm === el || el.contains(window.__pm))")
        assert reached, f"{label}: a real pointermove at {point} lands elsewhere"


def _every_verb_owned(page: Any, width: int) -> None:
    buttons = _remote(page).locator("button")
    for i in range(buttons.count()):
        button = buttons.nth(i)
        assert "btn" in (button.get_attribute("class") or "") or button.evaluate("(el) => !!el.closest('.gadget-cycle, select')"), \
            f"a verb that is not the library Button: {button.inner_text()!r}"
        if "btn" in (button.get_attribute("class") or ""):
            _pointer_owned(page, button, f"{button.inner_text()!r} at {width}")
    foot = page.locator('[data-testid="foot-receipt"]')
    if foot.count():
        _pointer_owned(page, foot.first, f"the footer receipt at {width}")


def _no_small_text_and_no_desk_writes(page: Any) -> None:
    found = page.evaluate("""() => {
      const roots = [...document.querySelectorAll('.gadget-group')].filter(g => /Remote access/.test(g.textContent || ''));
      const foot = document.querySelector('.desk-surface-foot, .surface-footer');
      if (foot) roots.push(foot);
      const small = [], words = [];
      for (const root of roots) {
        const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
        while (walker.nextNode()) {
          const node = walker.currentNode, text = (node.textContent || '').trim();
          if (!text) continue;
          const el = node.parentElement; const r = el.getBoundingClientRect();
          if (r.width === 0 || r.height === 0) continue;
          if (/desk writes/i.test(text)) words.push(text);
          if (text.length > 1 && parseFloat(getComputedStyle(el).fontSize) < 12) small.push(text);
        }
      }
      return {small, words};
    }""")
    assert found["words"] == [], f"a verb or chip reads 'desk writes': {found['words']}"
    assert found["small"] == [], f"text under 12 px in Remote access or the footer: {found['small'][:5]}"


def _remote(page: Any) -> Any:
    return page.locator(".gadget-group", has=page.locator(".gadget-group-label", has_text="Remote access")).last


def _row(page: Any) -> Any:
    return _remote(page).locator(".surface-ledger-row", has=page.locator(".surface-ledger-primary", has_text=IDENTITY))


def _grant_rows(db_path: Path) -> list[tuple[str, str]]:
    conn = sqlite3.connect(str(db_path))
    try:
        return [tuple(r) for r in conn.execute(
            "SELECT state, revocation_reason FROM kernel_desk_delegations WHERE agent_identity=? ORDER BY created_at, rowid", (IDENTITY,))]
    finally:
        conn.close()


def _kernel_receipt(page: Any, operation_id: str) -> dict[str, Any]:
    read = _api(page, "GET", f"/api/kernel/read?refs=operation:{operation_id}&view=receipt", token=TOKEN)
    return read["objects"][0]


class TestGrantGlass:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        _ensure_build()
        monkeypatch.setattr(principals, "agent_credentials", AgentCredentialStore())
        server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
        self.server, self.base, self.db_path = server, base, tmp_path / "holdspeak.db"
        try:
            yield
        finally:
            server.stop()

    def _page(self, pw: Any, width: int) -> tuple[Any, Any, list[str]]:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": width, "height": 900})
        page.emulate_media(reduced_motion="reduce")
        errors: list[str] = []
        page.on("pageerror", lambda err: errors.append(str(err)))
        return browser, page, errors

    def _open(self, page: Any) -> None:
        _navigate_to_settings_hub(page, self.base)
        _open_system_module(page)
        _settle(page)

    def _shot(self, page: Any, name: str, width: int) -> None:
        SHOTS.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(SHOTS / f"{name}-{width}.png"), full_page=False)

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", [1440, 393])
    def test_allow_stop_and_a_refused_stop_on_the_rendered_row(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, width)
            page.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
            _api(page, "PUT", "/api/settings/remote", {"enabled": True}, token=TOKEN)
            _api(page, "POST", "/api/settings/remote/credentials", {"identity": IDENTITY, "palette": "DESK"}, token=TOKEN)
            self._open(page)

            # Load, never granted: no chip; the Allow words; the AGENTS caption; the credential verb.
            row = _row(page)
            assert row.locator('[data-testid="grant-chip"]').count() == 0
            _readable(row.locator('[data-testid="grant-verb"]'), W["allow"])
            _readable(row.locator('[data-testid="credential-revoke"]'), W["revokeCredential"])
            _readable(_remote(page).locator(".surface-ledger-count"), W["agents"])
            _every_verb_owned(page, width)
            _no_small_text_and_no_desk_writes(page)
            self._shot(page, "1-never", width)

            # Allow.
            row.locator('[data-testid="grant-verb"]').click()
            chip = _row(page).locator('[data-testid="grant-chip"]')
            chip.wait_for(timeout=8_000)
            _readable(chip, W["live"])
            assert chip.get_attribute("data-state") == "success"
            _readable(_row(page).locator('[data-testid="grant-verb"]'), W["stop"])
            foot = page.locator('[data-testid="foot-receipt"]')
            _readable(foot, "ALLOWED")
            granted = _kernel_receipt(page, foot.get_attribute("data-operation-id"))
            assert (granted["operation"]["name"], granted["receipt"]["state"]) == ("delegation.grant", "succeeded")
            assert granted["receipt"]["result_ref"].startswith("desk-delegation:deskdeleg_")
            assert _grant_rows(self.db_path)[-1] == ("LIVE", "")
            _every_verb_owned(page, width)
            _no_small_text_and_no_desk_writes(page)
            self._shot(page, "2-allowed", width)

            # Stop.
            _row(page).locator('[data-testid="grant-verb"]').click()
            page.wait_for_function("(w) => document.querySelector('[data-testid=\"grant-chip\"]')?.textContent.includes(w)", arg=W["stopped"])
            chip = _row(page).locator('[data-testid="grant-chip"]')
            _readable(chip, W["stopped"])
            assert chip.get_attribute("data-state") == "idle"
            _readable(_row(page).locator('[data-testid="grant-verb"]'), W["allow"])
            _readable(foot, "STOPPED")
            stopped = _kernel_receipt(page, foot.get_attribute("data-operation-id"))
            assert stopped["operation"]["name"] == "delegation.revoke"
            assert _grant_rows(self.db_path)[-1] == ("REVOKED", "owner_revoked")
            self._shot(page, "3-stopped", width)

            # A refused Stop: another owner request revoked the grant first; the face still says LIVE.
            _row(page).locator('[data-testid="grant-verb"]').click()
            page.wait_for_function("(w) => document.querySelector('[data-testid=\"grant-chip\"]')?.textContent.includes(w)", arg=W["live"])
            _api(page, "DELETE", f"/api/settings/remote/delegations/{IDENTITY}", token=TOKEN)
            _row(page).locator('[data-testid="grant-verb"]').click()
            refused = _row(page).locator('[data-testid="grant-refused"]')
            refused.wait_for(timeout=8_000)
            assert refused.get_attribute("data-code") == "desk_delegation_required"
            _readable(refused, "CANNOT STOP")
            _readable(refused, "NO GRANT")
            _readable(foot, "REFUSED")
            # After the reread the chip agrees with the kernel (F15): STOPPED.
            _readable(_row(page).locator('[data-testid="grant-chip"]'), W["stopped"])
            foot.click()
            well = page.locator('[data-testid="grant-receipt"]')
            for word in ("REFUSED", W["actStop"], "NO GRANT", IDENTITY, "BY OWNER"):
                _readable(well, word)
            assert well.get_attribute("data-operation-id") == foot.get_attribute("data-operation-id")
            refusal = _kernel_receipt(page, well.get_attribute("data-operation-id"))
            assert (refusal["operation"]["name"], refusal["receipt"]["outcome"]) == ("delegation.revoke", "desk_delegation_required")
            assert page.locator("[role=dialog], .modal").count() == 0
            _every_verb_owned(page, width)
            _no_small_text_and_no_desk_writes(page)
            self._shot(page, "6-refused", width)
            assert errors == [], errors
            browser.close()

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", [1440, 393])
    def test_revoke_credential_ends_the_grant_first_and_the_receipt_survives_the_row(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, width)
            page.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
            _api(page, "PUT", "/api/settings/remote", {"enabled": True}, token=TOKEN)
            _api(page, "POST", "/api/settings/remote/credentials", {"identity": IDENTITY, "palette": "DESK"}, token=TOKEN)
            _api(page, "PUT", f"/api/settings/remote/delegations/{IDENTITY}", {}, token=TOKEN)
            self._open(page)
            _readable(_row(page).locator('[data-testid="grant-chip"]'), W["live"])
            _row(page).locator('[data-testid="credential-revoke"]').click()
            page.wait_for_function(f"() => ![...document.querySelectorAll('.surface-ledger-primary')].some(e => e.textContent.includes('{IDENTITY}'))")
            assert _remote(page).locator(".surface-ledger").count() == 0, "the ledger stayed with nothing to show"
            assert _grant_rows(self.db_path)[-1] == ("REVOKED", "credential_revoked")
            foot = page.locator('[data-testid="foot-receipt"]')
            _readable(foot, "STOPPED")
            _pointer_owned(page, foot.first, f"the footer receipt at {width}")
            foot.click()
            well = page.locator('[data-testid="grant-receipt"]')
            for word in ("SUCCEEDED", W["stopped"], IDENTITY, "BY OWNER"):
                _readable(well, word)
            receipt = _kernel_receipt(page, well.get_attribute("data-operation-id"))
            assert receipt["operation"]["name"] == "delegation.revoke" and receipt["receipt"]["state"] == "succeeded"
            self._shot(page, "7-credential-revoked", width)
            assert errors == [], errors
            browser.close()

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", [1440, 393])
    def test_a_grant_with_no_credential_shows_with_remote_off_and_stops(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, width)
            page.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
            _api(page, "PUT", "/api/settings/remote", {"enabled": True}, token=TOKEN)
            issued = _api(page, "POST", "/api/settings/remote/credentials", {"identity": IDENTITY, "palette": "DESK"}, token=TOKEN)
            _api(page, "POST", "/api/settings/remote/credentials", {"identity": "sweep-runner", "palette": "PROJECT"}, token=TOKEN)
            _api(page, "PUT", f"/api/settings/remote/delegations/{IDENTITY}", {}, token=TOKEN)
            status, _ = _api_allow_error(page, "DELETE", "/api/principals/self", token=issued["token"])
            assert status == 200
            _api(page, "PUT", "/api/settings/remote", {"enabled": False}, token=TOKEN)
            self._open(page)
            orphan = _remote(page).locator('[data-testid^="delegation-row-"]')
            _readable(orphan, IDENTITY)
            _readable(orphan, W["noCredential"])
            _readable(orphan.locator('[data-testid="grant-chip"]'), W["live"])
            _readable(orphan.locator('[data-testid="grant-verb"]'), W["stop"])
            # Remote OFF hides a credential row with no LIVE grant.
            assert _remote(page).locator(".surface-ledger-primary", has_text="sweep-runner").count() == 0
            _every_verb_owned(page, width)
            # The scroll-edge case: the verb at the bottom edge of the body is still owned.
            page.evaluate("() => { const b = document.querySelector('.desk-surface-body'); if (b) b.scrollTop = b.scrollHeight; }")
            _pointer_owned(page, orphan.locator('[data-testid="grant-verb"]').first, f"the orphan's Stop at the scroll edge, {width}", scrolled=True)
            issue_absent = _remote(page).locator('[data-testid="issue-credential-btn"]').count() == 0
            assert issue_absent  # remote OFF: no Issue credential
            self._shot(page, "5b-orphan-off", width)
            orphan.locator('[data-testid="grant-verb"]').click()
            page.wait_for_function("() => document.querySelectorAll('[data-testid^=\"delegation-row-\"]').length === 0")
            assert _remote(page).locator(".surface-ledger").count() == 0
            foot = page.locator('[data-testid="foot-receipt"]')
            _readable(foot, "STOPPED")
            _pointer_owned(page, foot.first, f"the footer receipt at {width}")
            assert _grant_rows(self.db_path)[-1] == ("REVOKED", "owner_revoked")
            _no_small_text_and_no_desk_writes(page)
            self._shot(page, "7-orphan-stopped", width)
            assert errors == [], errors
            browser.close()
