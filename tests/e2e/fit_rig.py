"""The fit rig of PHILO-15 lane 12 (the UGLY bounces of rehearsal 1A).

Kept as a rig by push 2 of the test diet (2026-10-12): its geometry legs live
in the app files (tests/e2e/test_meetings_glass.py B22, test_runs_on_glass.py
B27, test_today_glass.py B24); the browser file is parked
(tests/e2e/_parked/test_philo15_12_ugly_glass.py).
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from .glass_infra import _api, _boot, _ensure_build, _normal_chair, _settle
from tests._evidence import evidence_dir

TOKEN = "fit-glass"
SHOTS = evidence_dir("docs/internal/philo/phase-15/lane-12/shots")
SIZES = {1440: 900, 393: 852}
WIDTHS = list(SIZES)
T = 20_000
TITLE = "philo3_architect_meeting"
LONG_WORD = "Supercalifragilisticexpialidocious"
V2 = "Payments ledger cutover v2"
V3 = "Payments ledger cutover v3"
# A brief item row in Intelligence ▸ BRIEF (BriefView.tsx).
ITEM = "[data-testid=brief-sf-row], [data-testid=brief-tw-meetings], .intelligence-brief-rows li"
TOPICS = ["Local meeting ledger", "Summary retrieval after hub restart",
          "Recorded provider reply for isolated rig tests", "Named failure offense before ship"]
SUMMARY = ("Synthetic architect meeting covering three decisions: adopting SQLite for the local meeting "
           "ledger, keeping summary retrieval on the local desk after a hub restart, and using a recorded "
           "provider reply for isolated rig tests.")

# Every element inside `root` whose box ends past the root's right edge
# (1 px tolerance), and every element that ends past the viewport.
OVERFLOW_JS = """(root) => {
  const r = root.getBoundingClientRect();
  const vw = document.documentElement.clientWidth;
  const out = [];
  for (const e of root.querySelectorAll('*')) {
    const b = e.getBoundingClientRect();
    if (!b.width || !b.height) continue;
    const st = getComputedStyle(e);
    if (st.visibility === 'hidden' || st.display === 'none') continue;
    // The limit is the window's edge, or a nearer CLIPPING parent's edge
    // (overflow hidden/clip cuts the box: that is the bug, not an excuse).
    // A box inside a deliberate scroller (auto/scroll) is skipped.
    let limit = Math.min(r.right, vw), p = e.parentElement, scrolls = false;
    while (p && p !== root) {
      const ox = getComputedStyle(p).overflowX;
      if (/(auto|scroll)/.test(ox) && p.scrollWidth > p.clientWidth + 1) { scrolls = true; break; }
      if (/(hidden|clip)/.test(ox)) limit = Math.min(limit, p.getBoundingClientRect().right);
      p = p.parentElement;
    }
    if (scrolls) continue;
    if (b.right > limit + 1) {
      const chain = [];
      for (let a = e; a && a !== root.parentElement; a = a.parentElement) {
        const ab = a.getBoundingClientRect(), as = getComputedStyle(a);
        chain.push(`${a.tagName}.${String(a.className).split(' ').slice(0, 2).join('.')} w=${Math.round(ab.width)} r=${Math.round(ab.right)} sw=${a.scrollWidth} ox=${as.overflowX} disp=${as.display} gtc=${as.gridTemplateColumns.slice(0, 40)}`);
        if (chain.length > 12) break;
      }
      out.push({tag: e.tagName, cls: String(e.className).slice(0, 60), text: (e.textContent || '').trim().slice(0, 40),
                right: Math.round(b.right), limit: Math.round(limit), chain: out.length ? undefined : chain});
    }
  }
  return out;
}"""

# Every scroller in `root` (and root) that scrolls sideways: its content is
# wider than its box. (An ellipsis clips on purpose; a scroller should not.)
SIDEWAYS_JS = """(root) => [root, ...root.querySelectorAll('*')].filter((e) => {
  const ox = getComputedStyle(e).overflowX;
  return (ox === 'auto' || ox === 'scroll') && e.scrollWidth > e.clientWidth + 1 && e.clientWidth > 0
    && !['TEXTAREA', 'INPUT', 'SELECT'].includes(e.tagName);
}).map((e) => ({tag: e.tagName, cls: String(e.className).slice(0, 60), sw: e.scrollWidth, cw: e.clientWidth,
                text: (e.textContent || '').trim().slice(0, 40)}))"""

BOX_JS = "(e) => { const b = e.getBoundingClientRect(); return {x: b.left, y: b.top, w: b.width, h: b.height, r: b.right, btm: b.bottom}; }"


# Copied from tests/e2e/test_hs201_one_thing_glass.py, so the rig does not
# lean on a phase-named browser file.
def _quiet_concierge(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep the Runs on window (the Models window) off the real hardware
    scan (speed, not truth)."""
    import holdspeak.services.concierge_service as cs

    detection = {
        "engines": [],
        "hardware": {"capability": {"apple_silicon": True, "system": "darwin",
                                    "architecture": "arm64", "ram_gb": 36}},
        "runtimes": [],
        "checkedAt": "2026-09-19T09:41:00Z",
    }
    def detect(**kwargs: Any) -> dict[str, Any]:
        # PHILO-16 (C): Runs on draws the engines the library holds, so the
        # quiet scan still lists the owner's own endpoints (no hardware,
        # runtime, file or network scan): an engine added from the face
        # joins the column the way the real detection lists it.
        db = kwargs.get("db")
        engines: list[dict[str, Any]] = []
        for profile in (db.profiles.list() if db is not None else []):
            base = str(getattr(profile, "base_url", "") or "")
            if getattr(profile, "deleted", False) or not base:
                continue
            local = "127.0.0.1" in base or "localhost" in base
            engines.append({
                "id": f"{'local' if local else 'lan'}:{profile.id}",
                "kind": "local" if local else "lan",
                "name": str(getattr(profile, "model", "") or profile.name or profile.id),
                "host": "THIS DEVICE" if local else cs._host_for_base_url(base),
                "state": "READY",
                "baseUrl": base,
                **cs._detected_profile_fields(db, str(profile.id)),
            })
        return {**detection, "engines": engines}

    monkeypatch.setattr(cs, "detect", detect)
    monkeypatch.setattr(cs, "propose", lambda **_: {"rows": [], "receipt": {"groups": 0, "engines": 0, "waiting": 0}})


class FitRig:
    """The PHILO-15 lane 12 rig: a real hub on an isolated HOME, one page per width."""

    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        _ensure_build()
        keyfile = tmp_path / "people.key"
        keyfile.write_text("{}")
        keyfile.chmod(0o600)
        monkeypatch.setenv("HOLDSPEAK_PEOPLE_KEYSTORE_FILE", str(keyfile))
        _quiet_concierge(monkeypatch)
        server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
        self.server, self.base, self.tmp = server, base, tmp_path
        SHOTS.mkdir(parents=True, exist_ok=True)
        self.facts: dict[str, Any] = {}
        try:
            yield
        finally:
            server.stop()

    # ── the rig ──────────────────────────────────────────────────────────

    def _open(self, pw: Any, width: int) -> tuple[Any, Any, list[str]]:
        browser = pw.chromium.launch(headless=True, args=["--disable-smooth-scrolling"])
        ctx = browser.new_context(viewport={"width": width, "height": SIZES[width]}, device_scale_factor=1)
        page = ctx.new_page()
        page.set_default_timeout(45_000)
        errors: list[str] = []
        page.on("pageerror", lambda e: errors.append(str(e)[:200]))
        page.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
        _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
        return browser, page, errors

    def _seed_meeting(self) -> None:
        from holdspeak.db import get_database
        from holdspeak.meeting_session.models import IntelSnapshot, MeetingState, TranscriptSegment

        now = datetime.now().replace(microsecond=0)
        seg = [TranscriptSegment(text="Decision one. Use SQLite for the local meeting ledger.", speaker="Recording",
                                 start_time=0.0, end_time=6.0)]
        get_database().meetings.save_meeting(MeetingState(
            id="p15-12-m", started_at=now - timedelta(hours=1), ended_at=now - timedelta(minutes=59),
            title=TITLE, segments=seg, intel_status="completed",
            intel=IntelSnapshot(timestamp=0.0, summary=SUMMARY, topics=TOPICS)))

    def _stage(self, page: Any, key: str, scope: str | None = None) -> None:
        page.evaluate("([key, scope]) => sessionStorage.setItem('hs.desk.staged-surface-open', JSON.stringify(scope ? {key, scope} : {key}))",
                      [key, scope])
        page.reload(wait_until="load")
        _normal_chair(page)

    def _shot(self, page: Any, name: str, width: int, target: Any = None) -> str:
        _settle(page)
        path = SHOTS / f"after-{name}-{width}.png"
        (target or page).screenshot(path=str(path))
        return str(path)

    def _write(self, name: str, width: int) -> None:
        (SHOTS / f"{name}-{width}.json").write_text(json.dumps(self.facts, indent=2, default=str))

    @staticmethod
    def _overflow(page: Any, root: Any) -> list[dict[str, Any]]:
        return root.evaluate(OVERFLOW_JS)
