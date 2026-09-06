"""HS-526 — the Desk memory glass rig (relationship-aware retrieval).

The unscoped `open-project-memory` surface is the memory face: the Room
keeps its four questions (HS-169-03), so a Desk-wide query lives here and
nowhere else. Two boards at 1440 and 393:

- **results** — a query that matches a transcript segment recalls its
  parent Meeting, and the durable `meeting_artifact` edge brings the
  Artifact beside it wearing `Related · meeting artifact`. The matched
  words are marked, never injected as HTML.
- **empty** — a query with nothing behind it reads the library's one true
  line, and the search verb is still the library Button.

Each board is scanned against UX-CANON A: every verb is the library
Button (§A.1), no prose sentence (§A.3), no counter of zero (§A.8), and
no egress chip anywhere — memory is read locally, so a boundary badge
here would be decoration (§A.9).

The seed goes through the product's own seams inside the isolated HOME
`_boot` creates: `db.notes.upsert`, the meeting/segment rows the capture
path writes (whose content-synced FTS triggers are the index), and
`db.plugins.record_artifact` for the Artifact and its meeting edge.

Shots land in `HS526_SHOTS` (default: this session's scratchpad), never
in `pm/`.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import pytest

from .glass_infra import (
    _api,
    _assert_clean,
    _boot,
    _ensure_build,
    _normal_chair,
    _settle,
)

pytest.importorskip("playwright.sync_api", reason="Desk memory glass needs Playwright")

SHOTS = Path(
    os.environ.get(
        "HS526_SHOTS",
        "/private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/"
        "18afc54e-71d7-45d4-bcef-8b0a4ace77cd/scratchpad/shots526",
    )
)
SHOTS.mkdir(parents=True, exist_ok=True)

TOKEN = "hs526-memory"

#: The lexical seed term. The Artifact below never carries it: it can only
#: arrive through the durable Meeting→Artifact edge.
QUERY = "zephyr"
QUIET_QUERY = "unfindablequasar"


# ── Seed: the product's own seams, inside the isolated HOME ────────


def _seed() -> None:
    from holdspeak.db import get_database

    db = get_database()
    db.notes.upsert(
        note_id="hs526-n1",
        title="Zephyr rollout note",
        body_markdown="Zephyr rollout owners, gates, and the cut-over window.",
        last_modified="2026-02-03T09:00:00",
        created_at="2026-02-03T09:00:00",
    )
    with db._connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO meetings(id,started_at,ended_at,title,"
            " duration_seconds,intel_status,capture_status,provenance)"
            " VALUES ('hs526-m1','2026-02-01T09:00:00','2026-02-01T09:30:00',"
            "         'Launch review',1800.0,'disabled','finalized','desktop')"
        )
        conn.execute(
            "DELETE FROM segments WHERE meeting_id='hs526-m1'"
        )
        conn.execute(
            "INSERT INTO segments(meeting_id,text,speaker,start_time,end_time)"
            " VALUES ('hs526-m1','The zephyr rollout starts Friday','Ada',0,4)"
        )
    db.plugins.record_artifact(
        artifact_id="hs526-a1",
        meeting_id="hs526-m1",
        artifact_type="memo",
        title="Rollout checklist",
        body_markdown="Owners and gates",
        updated_at="2026-02-02T09:00:00",
    )


# ── Helpers ────────────────────────────────────────────────────────


def _init_desk(page: Any, url: str) -> None:
    page.goto(f"{url}/?token={TOKEN}", wait_until="load")
    _api(page, "PUT", "/api/setup/onboarding",
         {"disposition": "completed"}, token=TOKEN)
    _normal_chair(page)


def _open_desk_memory(page: Any) -> None:
    """Go → Desk memory: the surface staged with NO scope."""
    page.evaluate(
        """([key]) => {
          localStorage.removeItem("hs.desk.workspace.v1");
          sessionStorage.setItem(
            "hs.desk.staged-surface-open",
            JSON.stringify({key})
          );
        }""",
        ["open-project-memory"],
    )
    page.reload(wait_until="load")
    _normal_chair(page)
    page.locator(".desk-surface-window").first.wait_for(timeout=15000)
    page.get_by_role("searchbox", name="Search the Desk").wait_for(timeout=10000)
    _settle(page)


def _search_verb(page: Any) -> Any:
    """The face's own Search verb (the desk chrome has one too)."""
    return page.locator(".desk-surface-window").get_by_role(
        "button", name="Search", exact=True
    )


def _search(page: Any, query: str) -> None:
    page.get_by_role("searchbox", name="Search the Desk").fill(query)
    _search_verb(page).click()
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
    print(f"[hs526] {path}")
    return path


#: One scan of the FACE against the canon rules it can break. The scope is
#: the surface body and its footer: the frame's own chrome (window lights,
#: the wing tabs) is the shell's species, not this face's verbs.
_CANON_JS = """() => {
  const win = document.querySelector(
    ".desk-surface-window .desk-surface-body, .desk-surface-body"
  );
  if (!win) return { error: "no surface body" };
  const foot = document.querySelector(".surface-footer-layout");
  const roots = foot ? [win, foot] : [win];
  const q = (sel) => roots.flatMap((r) => [...r.querySelectorAll(sel)]);
  // The library's own species on this face: Button (.btn), MicButton
  // (.desk-mic), and SurfaceRow's openable line (.surface-row-open,
  // Surface.tsx:188). Anything else here would be hand-rolled.
  const LIBRARY = ["btn", "desk-mic", "surface-row-open"];
  const rawButtons = q("button")
    .filter((b) => !LIBRARY.some((cls) => b.classList.contains(cls)))
    .map((b) => (b.className || "") + "|" + (b.textContent || "").trim().slice(0, 30));
  const sentences = [];
  const zeros = q(".surface-token, [data-chip]")
    .map((n) => (n.textContent || "").trim())
    .filter((t) => t === "0" || t.startsWith("0 "));
  const egress = q(".gadget-chip-egress").length;
  const fontSizes = new Set();
  for (const root of roots) {
    const walk = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    while (walk.nextNode()) {
      const text = (walk.currentNode.textContent || "").trim();
      if (text.length > 60 && text.endsWith(".")) sentences.push(text.slice(0, 80));
      const parent = walk.currentNode.parentElement;
      if (parent && text)
        fontSizes.add(Math.round(parseFloat(getComputedStyle(parent).fontSize)));
    }
  }
  return {
    rawButtons, sentences, zeros, egress,
    typeSteps: [...fontSizes].sort((a, b) => a - b),
  };
}"""


def _assert_canon(page: Any) -> dict[str, Any]:
    scan = page.evaluate(_CANON_JS)
    assert "error" not in scan, scan
    assert scan["rawButtons"] == [], f"raw <button> (A.1): {scan['rawButtons']}"
    assert scan["sentences"] == [], f"prose on the face (A.3): {scan['sentences']}"
    assert scan["zeros"] == [], f"counter of zero (A.8): {scan['zeros']}"
    assert scan["egress"] == 0, "memory reads locally: no egress chip (A.9)"
    assert len(scan["typeSteps"]) >= 3, f"type steps (§C): {scan['typeSteps']}"
    return scan


# ── Boards ─────────────────────────────────────────────────────────


@pytest.mark.e2e
@pytest.mark.requires_meeting
@pytest.mark.parametrize("width,height", [(1440, 900), (393, 852)])
def test_desk_memory_results(tmp_path, monkeypatch, width, height):
    """A transcript match recalls its Meeting and names the durable edge."""
    _ensure_build()
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    errors: list[str] = []
    try:
        _seed()
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page()
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.set_viewport_size({"width": width, "height": height})
            _init_desk(page, url)
            _open_desk_memory(page)
            _search(page, QUERY)

            rows = page.locator(".desk-surface-window .surface-row")
            rows.first.wait_for(timeout=10000)
            assert rows.count() >= 2, f"hits: {rows.count()}"
            # The parent Meeting, not the isolated segment.
            assert page.get_by_text("Launch review").count() >= 1
            # The Artifact arrived over the edge, and the edge is named.
            assert page.get_by_text("Rollout checklist").count() >= 1
            assert page.get_by_text("Related · meeting artifact").count() >= 1
            # The marker grammar is rendered, never injected.
            assert page.locator(".project-memory-highlight").count() >= 1

            scan = _assert_canon(page)
            print(f"[hs526] results@{width} type steps {scan['typeSteps']}")
            _shot(page, "desk-memory-results", width)
            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()


@pytest.mark.e2e
@pytest.mark.requires_meeting
@pytest.mark.parametrize("width,height", [(1440, 900), (393, 852)])
def test_desk_memory_empty(tmp_path, monkeypatch, width, height):
    """Nothing behind the query: one true line, the verb still lawful."""
    _ensure_build()
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    errors: list[str] = []
    try:
        _seed()
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page()
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.set_viewport_size({"width": width, "height": height})
            _init_desk(page, url)
            _open_desk_memory(page)
            _search(page, QUIET_QUERY)

            page.get_by_text("No matches").first.wait_for(timeout=10000)
            assert page.locator(".desk-surface-window .surface-row").count() == 0
            assert _search_verb(page).count() == 1

            _assert_canon(page)
            _shot(page, "desk-memory-empty", width)
            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()
