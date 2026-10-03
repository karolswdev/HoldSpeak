"""PHILO-13-18 (C8) -- the library DeskEditor wraps long lines, at every width.

Astra's B5 check (#739) found the Room's Update draft cut its summary, decision
and action lines at the right edge at 393 (assets/story-10-week/week-393/
after.png): the owners and due dates were not on the glass. Through the real
hub on an isolated HOME, a project's Update draft whose lines are the B5 week
(tests/fixtures/philo13_b5_week_summary_reply.json: the summary, the decision,
two actions with owner and due date) is opened at 393 touch and 1440 mouse:

  W1 the editor reader (glass_infra._rendered_text_faults, on_glass) finds no
     clipped text and no overlap in the editor;
  W2 nothing in the editor scrolls sideways;
  W3 every line's last words (the owner and the due date) are inside the
     editor's visible box.

Shots go to assets/story-18-shots/ (``.tmp/evidence-shots/`` unless
HOLDSPEAK_EVIDENCE_WRITE=1).
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest

from .glass_infra import _api, _boot, _ensure_build, _normal_chair, _rendered_text_faults, _settle
from tests._evidence import evidence_dir

pytest.importorskip("playwright.sync_api", reason="the editor wrap glass needs Playwright")

pytestmark = [pytest.mark.e2e, pytest.mark.timeout(300, method="thread")]

TOKEN = "philo13-18-wrap"
SHOTS = evidence_dir("pm/roadmap/holdspeak-philo/phase-13-the-desk/assets/story-18-shots")
SIZES = {1440: 900, 393: 852}
# The B5 week, as the drafted update writes it (one line per fact).
LINES = [
    "Summary: The ledger cutover is ready for the controlled migration, and the rollback path is tested end to end.",
    "Decision: Use the controlled migration window because the rollback path is tested (Ledger cutover sync).",
    "Action: Confirm the migration window with the payments team. Owner: Avery. Due: 2026-10-06.",
    "Action: Send the rollback checklist to every service owner on the ledger. Owner: Morgan. Due: 2026-10-07.",
]
ENDS = ["end to end.", "cutover sync).", "Due: 2026-10-06.", "Due: 2026-10-07."]


def _seed_draft(project_id: str) -> None:
    from holdspeak.db import get_database

    body = "## This week\n\n" + "\n\n".join(LINES) + "\n"
    now = datetime.now().isoformat()
    with get_database()._connection() as conn:
        conn.execute(
            """INSERT INTO project_updates
               (id, project_id, project_revision, review_id, lifecycle, draft_revision,
                body_md, claims_json, source_manifest_json, generator, created_at, updated_at)
               VALUES (?, ?, 0, NULL, 'draft', 1, ?, '[]', '{}', 'deterministic', ?, ?)""",
            ("pupd_p1318_wrap", project_id, body, now, now),
        )


_ENDS_JS = """(ends) => {
  const ed = document.querySelector('[data-testid="update-body-editor"] .cm-editor');
  const box = ed.getBoundingClientRect();
  const out = {box: [box.left, box.right].map(Math.round), missing: [], sideways: []};
  for (const end of ends) {
    const line = [...ed.querySelectorAll('.cm-line')].find((l) => l.textContent.includes(end));
    if (!line) { out.missing.push(end + ' (no line)'); continue; }
    const walker = document.createTreeWalker(line, NodeFilter.SHOW_TEXT);
    let hit = null;
    for (let n = walker.nextNode(); n; n = walker.nextNode()) {
      const i = n.textContent.indexOf(end.slice(-6));
      if (i >= 0) { const r = document.createRange(); r.setStart(n, i); r.setEnd(n, i + 6); hit = r.getBoundingClientRect(); }
    }
    if (!hit || hit.right > box.right + 1 || hit.left < box.left - 1)
      out.missing.push(end + ' at ' + (hit ? Math.round(hit.right) : 'none'));
  }
  for (const e of [ed, ...ed.querySelectorAll('*')])
    if (e.scrollWidth > e.clientWidth + 1 && ['auto', 'scroll'].includes(getComputedStyle(e).overflowX))
      out.sideways.push((e.className || e.tagName).toString().slice(0, 40) + ' ' + e.scrollWidth + '>' + e.clientWidth);
  return out;
}"""


@pytest.mark.parametrize("width", list(SIZES))
def test_the_update_draft_wraps(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int) -> None:
    from playwright.sync_api import sync_playwright

    _ensure_build()
    server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            ctx = browser.new_context(viewport={"width": width, "height": SIZES[width]},
                                      has_touch=width < 720, is_mobile=False)
            page = ctx.new_page()
            page.set_default_timeout(20_000)
            page.goto(f"{base}/?token={TOKEN}", wait_until="load")
            _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
            pid = _api(page, "POST", "/api/projects", {"name": "Payments ledger cutover",
                       "description": "B5 week", "command_id": "p1318-wrap"}, token=TOKEN)["project"]["id"]
            _seed_draft(pid)
            page.evaluate("""([k, s]) => sessionStorage.setItem('hs.desk.staged-surface-open',
                JSON.stringify({key: k, scope: s}))""", ["open-project-memory", f"project:{pid}"])
            page.reload(wait_until="load")
            _normal_chair(page)

            def press(loc: Any) -> None:
                loc.scroll_into_view_if_needed()
                if width < 720:
                    b = loc.bounding_box()
                    page.touchscreen.tap(b["x"] + b["width"] / 2, b["y"] + b["height"] / 2)
                else:
                    loc.click()

            press(page.locator('[data-testid="updates-verb"]').first)
            page.locator('[data-testid="update-list-item"]').first.wait_for()
            press(page.locator('[data-testid="update-list-item"]').first)
            editor = page.locator('[data-testid="update-body-editor"] .cm-editor')
            editor.wait_for()
            editor.scroll_into_view_if_needed()
            _settle(page)
            assert "Owner: Morgan" in editor.inner_text(), "the seeded draft is not in the editor"
            faults = _rendered_text_faults(page, '[data-testid="update-body-editor"]', on_glass=True)
            ends = page.evaluate(_ENDS_JS, ENDS)
            page.screenshot(path=str(SHOTS / f"update-editor-wrap-{width}.png"))
            (SHOTS / f"update-editor-wrap-{width}.json").write_text(
                json.dumps({"faults": faults, "ends": ends}, indent=1) + "\n")
            browser.close()
    finally:
        server.stop()

    assert faults["scopes"], "no visible update editor"
    assert not faults["clipped"] and not faults["overlaps"], f"W1 at {width}: {faults}"
    assert not ends["sideways"], f"W2 at {width}: the editor scrolls sideways: {ends['sideways']}"
    assert not ends["missing"], f"W3 at {width}: line ends off the editor ({ends['box']}): {ends['missing']}"
