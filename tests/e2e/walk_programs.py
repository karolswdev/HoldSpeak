"""A live state walk of the Program window (the owner's PROACTIVE NOT REACTIVE
ruling, 2026-10-25): one Program in each state, made by the real engine on
the Programs rig (``tests/integration/program_rig``), served by a real hub
(``glass_infra._boot``, the engine off so each state holds still) and shot
in a real browser at 1440 and 393.

Not collected by the suite (the file name has no ``test_`` prefix). Run it by
name, under the lock, with an isolated HOME:

    uv run python scripts/test_lock.py -- uv run pytest -q tests/e2e/walk_programs.py

The shots land in ``.tmp/walk-programs/<state>-<width>.png``. Each shot is
judged by eye against the canon (direction A; no empty section; no counter of
zero; no chevron; every verb the library Button; nothing wider than its
parent; one wait sentence). The walk itself fails only when a window does
not draw, has page-wide sideways scroll, or draws a raw <button>.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Callable

import pytest

from tests.e2e.glass_infra import _boot, _normal_chair, clear_hub_windows_http
from tests.integration.program_rig import FAKE_CHECK, OWNER, Rig

ROOT = Path(__file__).resolve().parents[2]
SHOTS = ROOT / ".tmp" / "walk-programs"
TOKEN = "walk-programs"
SIZES = {1440: 900, 393: 852}


def _drafting_empty(tmp: Path) -> tuple[Rig, str]:
    rig = Rig(tmp)
    pid = rig.service.create(OWNER, title="Proof audit · README", goal="Audit the README for stale claims. Read only.",
                             repository=str(rig.repo), template="audit", control="yolo")["id"]
    return rig, pid


def _drafting_steps(tmp: Path) -> tuple[Rig, str]:
    rig = Rig(tmp)
    pid = rig.service.create(OWNER, title="The hub stops stalling", goal="Every route answers under 100 ms while a "
                             "meeting records. The People routes go off the loop first.",
                             repository=str(rig.repo), check_command=f"sh {FAKE_CHECK}", template="build-and-review",
                             control="normal")["id"]
    rig.service.plan(OWNER, pid, steps=[
        {"title": "Indexes", "brief": "Add the three indexes.", "owns": ["holdspeak/db/schema.py"]},
        {"title": "People routes", "brief": "31 handlers through run_in_threadpool.",
         "owns": ["holdspeak/web/routes/people.py"]},
        {"title": "The fan-out", "brief": "One frame per change.", "after": [1, 2]},
    ])
    return rig, pid


def _held_commit(tmp: Path) -> tuple[Rig, str]:
    from tests.integration.test_program_run import _held_step

    rig = Rig(tmp)
    pid, step = _held_step(rig, "normal")
    rig.gate.hold_commit(step["launch_id"])
    rig.tick()
    return rig, pid


def _todo(tmp: Path) -> tuple[Rig, str]:
    rig = Rig(tmp)
    pid = rig.service.create(OWNER, title="Atlas at 393", goal="Atlas reads at 393.", repository=str(rig.repo),
                             check_command=f"sh {FAKE_CHECK}", template="fast-cycle", control="normal")["id"]
    rig.service.plan(OWNER, pid, steps=[{"title": "Atlas anchors", "brief": "Cite each anchor once."},
                                        {"title": "Atlas index", "brief": "Index the anchors."},
                                        {"title": "Atlas links", "brief": "Link the index.", "after": [2]}])
    rig.service.require(OWNER, pid, text="The atlas reads well at 393", kind="word", step_id=rig.step(pid, 1)["id"],
                        spec={"walk": ["Open the atlas at 393", "Read the first section"]})
    rig.service.start(OWNER, pid)
    rig.tick()
    other = rig.step(pid, 2)
    rig.states[other["launch_id"]] = {"state": "ended", "turn_id": None}
    rig.tick()
    return rig, pid


def _race_parked(tmp: Path) -> tuple[Rig, str]:
    from tests.integration.test_program_race import RED_CHECK, _race, _red_rounds

    rig = Rig(tmp)
    pid = _race(rig, check=RED_CHECK)
    rig.service.start(OWNER, pid)
    _red_rounds(rig, pid)
    return rig, pid


def _audit_findings(tmp: Path, monkeypatch: Any) -> tuple[Rig, str]:
    from tests.integration.test_desk_program_audit import REPORT_1, REPORT_2, _audit, _report

    rig = Rig(tmp)
    pid = _audit(rig, "secure")
    _report(rig, monkeypatch, pid, 1, REPORT_1)
    two = rig.step(pid, 2)
    rig.words[two["launch_id"]] = REPORT_2
    rig.agent.end_turn(two["launch_id"])
    rig.tick()
    return rig, pid


def _lesson(tmp: Path) -> tuple[Rig, str]:
    from tests.integration.test_desk_program_lessons import _go_red, _program, _red_check

    rig = Rig(tmp)
    pid = _program(rig, _red_check(tmp))
    _go_red(rig, pid, 1)
    _go_red(rig, pid, 2)
    return rig, pid


def _done_delivery(tmp: Path) -> tuple[Rig, str]:
    from tests.integration.test_program_delivery import _done

    return _done(tmp, control="secure")


def _parked_reason(tmp: Path) -> tuple[Rig, str]:
    rig = Rig(tmp)
    pid = rig.service.create(OWNER, title="Proof run 3", goal="Three steps at YOLO with zero presses.",
                             repository=str(rig.repo), check_command=f"sh {FAKE_CHECK}", template="fast-cycle",
                             control="yolo")["id"]
    rig.service.plan(OWNER, pid, steps=[{"title": f"Part {n}", "brief": f"Write part {n}."} for n in (1, 2, 3)])
    rig.service.start(OWNER, pid)
    rig.agent.finish(rig.step(pid, 1)["launch_id"], {"part1.txt": "1\n"})
    rig.tick(3)
    rig.service.park(OWNER, pid, reason="proof")
    return rig, pid


def _dreaming(tmp: Path) -> tuple[Rig, str]:
    rig = Rig(tmp)
    pid = rig.service.create(OWNER, title="Dreaming · HoldSpeak", template="dreaming", repository=str(rig.repo))["id"]
    return rig, pid


STATES_ALL: list[tuple[str, Callable[..., tuple[Rig, str]]]] = [
    ("drafting-empty", _drafting_empty),
    ("drafting-steps", _drafting_steps),
    ("held-commit", _held_commit),
    ("todo", _todo),
    ("race-parked", _race_parked),
    ("audit-findings", _audit_findings),
    ("lesson", _lesson),
    ("done-delivery", _done_delivery),
    ("parked-reason", _parked_reason),
    ("dreaming", _dreaming),
]

def _hub_open(base: str, wid: str) -> None:
    import json
    import urllib.parse
    import urllib.request

    request = urllib.request.Request(
        f"{base}/api/desk/windows/{urllib.parse.quote(wid, safe='')}/open", data=json.dumps({}).encode(),
        method="POST", headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=30) as resp:
        assert resp.status < 300, resp.status


import os

#: WALK_ONLY=drafting-empty,lesson walks those alone.
STATES = [row for row in STATES_ALL if not os.environ.get("WALK_ONLY") or row[0] in os.environ["WALK_ONLY"].split(",")]

def _close_others(base: str, wid: str) -> None:
    import json
    import urllib.parse
    import urllib.request

    headers = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}
    with urllib.request.urlopen(urllib.request.Request(f"{base}/api/desk/windows", headers=headers), timeout=30) as resp:
        listed = json.loads(resp.read())
    for window in listed.get("windows") or []:
        if window["id"] != wid:
            urllib.request.urlopen(urllib.request.Request(
                f"{base}/api/desk/windows/{urllib.parse.quote(window['id'], safe='')}/close", data=b"{}",
                method="POST", headers=headers), timeout=30).read()


_NO_RAW_BUTTON_JS = """(wid) => {
  const win = document.getElementById(wid);
  if (!win) return ["no window"];
  return [...win.querySelectorAll("button")].filter((b) => !b.className.match(/\\bbtn\\b|gadget|kit-|surface-|pg-|edit-in-place|window|titlebar|fold/))
    .map((b) => (b.className || "(no class)") + " · " + (b.textContent || "").trim().slice(0, 40));
}"""


@pytest.fixture(scope="module")
def pw_browser():
    from playwright.sync_api import sync_playwright

    pw = sync_playwright().start()
    browser = pw.chromium.launch()
    try:
        yield browser
    finally:
        browser.close()
        pw.stop()


@pytest.mark.timeout(600)
@pytest.mark.parametrize("name,seed", STATES, ids=[name for name, _ in STATES])
def test_walk(name: str, seed: Callable[..., tuple[Rig, str]], tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
              pw_browser: Any) -> None:
    rig_dir = tmp_path / "rig"
    rig, pid = seed(rig_dir, monkeypatch) if name == "audit-findings" else seed(rig_dir)
    # The hub reads the rig's database: a consistent copy, WAL included.
    hub_dir = tmp_path / "hub"
    hub_dir.mkdir()
    source = sqlite3.connect(str(rig_dir / "hub.db"))
    target = sqlite3.connect(str(hub_dir / "holdspeak.db"))
    source.backup(target)
    source.close()
    target.close()
    server, base = _boot(hub_dir, monkeypatch, token=TOKEN)
    SHOTS.mkdir(parents=True, exist_ok=True)
    try:
        wid = f"pullout:program:{pid}"
        for width, height in SIZES.items():
            ctx = pw_browser.new_context(viewport={"width": width, "height": height})
            page = ctx.new_page()
            errors: list[str] = []
            page.on("pageerror", lambda exc: errors.append(str(exc)[:200]))
            clear_hub_windows_http(base, TOKEN)
            _hub_open(base, wid)
            page.goto(f"{base}/?token={TOKEN}", wait_until="load")
            _normal_chair(page)
            page.wait_for_timeout(800)
            _close_others(base, wid)  # the desk opens Today on arrival; the walk looks at the Program alone
            win = page.locator(f'[id="{wid}"]')
            win.wait_for(timeout=30_000)
            page.locator(f'[id="{wid}"] [data-testid=program-status]').wait_for(timeout=30_000)
            page.wait_for_timeout(1200)
            page.mouse.move(2, 2)
            page.screenshot(path=str(SHOTS / f"{name}-{width}.png"))
            win.screenshot(path=str(SHOTS / f"{name}-{width}-window.png"))
            sideways = page.evaluate("() => document.documentElement.scrollWidth - document.documentElement.clientWidth")
            raw = page.evaluate(_NO_RAW_BUTTON_JS, wid)
            ctx.close()
            assert not errors, (name, width, errors)
            assert sideways <= 1, (name, width, sideways)
            assert raw == [], (name, width, raw)
    finally:
        server.stop()
