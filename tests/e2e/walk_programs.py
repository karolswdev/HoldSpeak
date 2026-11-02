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

import re
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


# ── the other two Programs faces (the coordinator, 2026-11-01) ──────────────

def _wanted(name: str) -> bool:
    only = os.environ.get("WALK_ONLY")
    return not only or name in only.split(",")


def _http(base: str, method: str, path: str, body: Any = None) -> Any:
    import json
    import urllib.request

    request = urllib.request.Request(base + path, method=method, data=json.dumps(body).encode() if body is not None else None,
                                     headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=60) as resp:
        raw = resp.read().decode()
    return json.loads(raw) if raw.strip().startswith(("{", "[")) else {}


def _serve(rig_dir: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Any, str]:
    """A real hub on a consistent copy of the rig's database (the engine off)."""
    hub_dir = tmp_path / "hub"
    hub_dir.mkdir()
    source = sqlite3.connect(str(rig_dir / "hub.db"))
    target = sqlite3.connect(str(hub_dir / "holdspeak.db"))
    source.backup(target)
    source.close()
    target.close()
    return _boot(hub_dir, monkeypatch, token=TOKEN)


def _page(pw_browser: Any, width: int) -> tuple[Any, Any, list[str]]:
    ctx = pw_browser.new_context(viewport={"width": width, "height": SIZES[width]})
    page = ctx.new_page()
    errors: list[str] = []
    page.on("pageerror", lambda exc: errors.append(str(exc)[:200]))
    return ctx, page, errors


def _shot(page: Any, name: str) -> None:
    SHOTS.mkdir(parents=True, exist_ok=True)
    page.mouse.move(2, 2)
    page.wait_for_timeout(600)
    page.screenshot(path=str(SHOTS / f"{name}.png"))


def _seed_list(rig_dir: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, str]:
    """One Program in each group of the list, a family and a split chain."""
    from tests.integration.test_desk_program_audit import REPORT_1, _audit, _report
    from tests.integration.test_program_run import _held_step

    rig = Rig(rig_dir)
    with rig.db._connection() as conn:
        conn.execute("INSERT INTO projects (id, name) VALUES ('proj-holdspeak', 'HoldSpeak')")
    made = lambda title, **more: rig.service.create(  # noqa: E731
        OWNER, title=title, goal=f"{title}.", repository=str(rig.repo), check_command=f"sh {FAKE_CHECK}",
        template=more.pop("template", "fast-cycle"), **more)["id"]
    ids: dict[str, str] = {}
    ids["drafting"] = made("Audit the README", template="audit", control="yolo")
    ids["drafting-steps"] = made("The hub stops stalling", project_id="proj-holdspeak")
    rig.service.plan(OWNER, ids["drafting-steps"], steps=[{"title": "Indexes", "brief": "Add them."},
                                                          {"title": "People routes", "brief": "Off the loop."}])
    ids["held"], step = _held_step(rig, "normal")
    rig.gate.hold_commit(step["launch_id"])
    rig.tick()
    ids["audit"] = _audit(rig, "secure", steps=1)
    _report(rig, monkeypatch, ids["audit"], 1, REPORT_1)
    fix = rig.service.decide(OWNER, ids["audit"], rig.step(ids["audit"], 1)["id"], kind="fix_program", choice="make")
    ids["fix"] = fix["fix_program_id"]
    ids["done"] = made("Atlas anchors", control="yolo", project_id="proj-holdspeak")
    rig.service.plan(OWNER, ids["done"], steps=[{"title": "Anchors", "brief": "Cite each anchor once."}])
    rig.service.start(OWNER, ids["done"])
    rig.agent.finish(rig.step(ids["done"], 1)["launch_id"], {"atlas.md": "a\n"})
    rig.tick(3)
    for reason in ("proof", "done_with_it", None):
        pid = made(f"Parked {reason or 'plain'}", control="yolo")
        rig.service.plan(OWNER, pid, steps=[{"title": "One", "brief": "Do one."}])
        rig.service.start(OWNER, pid)
        rig.tick()
        rig.service.park(OWNER, pid, reason=reason)
    ids["dream"] = rig.service.create(OWNER, title="Dreaming · HoldSpeak", template="dreaming", repository=str(rig.repo))["id"]
    first = made("Meeting recap in the Note")
    second = made("Calls window lists the last ten", origin_ref=f"after:{first}")
    made("Programs window exports to a Note", origin_ref=f"after:{second}")
    return ids


@pytest.mark.timeout(900)
@pytest.mark.skipif(not _wanted("list"), reason="WALK_ONLY names other faces")
def test_walk_list(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, pw_browser: Any) -> None:
    """The Programs list: every group, a family fold, a split chain, and the
    Find, Project and Person filters, at 1440 and 393."""
    ids = _seed_list(tmp_path / "rig", monkeypatch)
    server, base = _serve(tmp_path / "rig", tmp_path, monkeypatch)
    try:
        _http(base, "POST", "/api/people/setup", {})
        alice = _http(base, "POST", "/api/people/relationships",
                      {"display_name": "Alice Park", "relationship_kind": "direct_report"})["relationship"]["id"]
        _http(base, "PATCH", f"/api/programs/{ids['drafting-steps']}", {"for_person_id": alice})
        wid = "surface-programs"
        for width in SIZES:
            ctx, page, errors = _page(pw_browser, width)
            clear_hub_windows_http(base, TOKEN)
            _hub_open(base, wid)
            page.goto(f"{base}/?token={TOKEN}", wait_until="load")
            _normal_chair(page)
            page.wait_for_timeout(800)
            _close_others(base, wid)
            win = page.locator(f'[id="{wid}"]')
            win.locator("[data-testid=programs-list]").wait_for(timeout=30_000)
            _shot(page, f"list-{width}")
            win.screenshot(path=str(SHOTS / f"list-{width}-window.png"))
            for fold in ("programs-family-fold", "programs-parked-fold"):
                found = win.locator(f"[data-testid={fold}]")
                if found.count():
                    found.first.locator("button, summary").first.click()
            _shot(page, f"list-folds-{width}")
            win.screenshot(path=str(SHOTS / f"list-folds-{width}-window.png"))
            find = win.locator("[data-testid=programs-find] input")
            if find.count():
                find.fill("audit")
                _shot(page, f"list-find-{width}")
                find.fill("")
            for menu, sub, pick, shot in (("programs-project", "Project", "HoldSpeak", "project"),
                                          ("programs-person", "Person", "Alice Park", "person")):
                opener = win.locator(f"[data-testid={menu}]")
                if opener.count() and opener.is_visible():
                    opener.click()
                else:
                    # At 393 Project and Person live under More (its submenus).
                    win.locator("[data-testid=programs-more]").click()
                    page.get_by_role("menuitem", name=re.compile(rf"^{sub}")).first.click()
                page.get_by_role("menuitem", name=pick).first.click()
                page.wait_for_timeout(400)
                _shot(page, f"list-{shot}-{width}")
                # The filter is on: only that program's rows (the status names the filter).
                assert pick.split()[0] in win.locator("[data-testid=programs-status]").inner_text() or shot == "person", shot
            sideways = page.evaluate("() => document.documentElement.scrollWidth - document.documentElement.clientWidth")
            ctx.close()
            assert not errors, (width, errors)
            assert sideways <= 1, (width, sideways)
    finally:
        server.stop()


class _Responder:
    """A desk agent's question (the responder's reads and its pane delivery,
    the process edge; tests/unit/test_reach_send_and_question.py)."""

    def __init__(self) -> None:
        from types import SimpleNamespace

        self.typed: list[tuple[str, str]] = []
        self.session = SimpleNamespace(
            agent="claude", session_id="s-1", question="Which branch should I base the fix on?",
            wait_started_at="2026-11-01T12:00:00+00:00", updated_at="2026-11-01T12:00:00+00:00",
            state="waiting", wait_kind="answer")

    def _sessions(self) -> list[Any]:
        return [self.session]

    @staticmethod
    def _key(session: Any) -> str:
        return f"{session.agent}:{session.session_id}"

    def _launch_for(self, key: str) -> dict[str, Any]:
        return {"launch_id": "L-1", "session_key": key, "title": "Fix the flaky test", "state": "working"}

    def _deliver(self, launch: Any, key: str, agent: str, text: str, *, submit: bool = True) -> dict[str, Any]:
        self.typed.append((key, text))
        return {"status": "delivered"}


@pytest.mark.timeout(900)
@pytest.mark.skipif(not _wanted("briefing"), reason="WALK_ONLY names other faces")
def test_walk_briefing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, pw_browser: Any) -> None:
    """The briefing page at his phone's width first, then 1440: one page with
    three held items of different kinds, a prepared send, a desk agent's
    question, a decided page and an expired one."""
    from holdspeak.services import briefing_sources
    from tests.integration.test_desk_program_audit import REPORT_1, _audit, _report
    from tests.integration.test_desk_program_lessons import _go_red, _program, _red_check
    from tests.integration.test_program_run import _held_step

    rig = Rig(tmp_path / "rig")
    held, step = _held_step(rig, "normal")
    rig.gate.hold_commit(step["launch_id"])
    rig.tick()
    audit = _audit(rig, "secure", steps=1)
    _report(rig, monkeypatch, audit, 1, REPORT_1)
    lesson = _program(rig, _red_check(tmp_path / "rig"))
    _go_red(rig, lesson, 1)
    _go_red(rig, lesson, 2)
    turn = lambda pid, kind: next(row for row in rig.program(pid)["your_turn_items"] if row["kind"] == kind)  # noqa: E731
    refs = [f"program:{held}:{turn(held, 'commit')['id']}", f"program:{audit}:{turn(audit, 'audit_file')['id']}",
            f"program:{lesson}:{turn(lesson, 'lesson')['id']}"]
    responder = _Responder()
    monkeypatch.setattr(briefing_sources.CoderQuestionSource, "_responder", lambda self: responder)
    monkeypatch.setattr("holdspeak.agent_context.models.is_blocked", lambda session: True)
    monkeypatch.setattr("holdspeak.agent_context.models.wait_kind", lambda session: session.wait_kind)
    server, base = _serve(tmp_path / "rig", tmp_path, monkeypatch)
    try:
        pages: dict[str, str] = {}
        pages["three"] = _http(base, "POST", "/api/reach/packages", {"refs": refs, "kind": "digest"})["path"]
        # A prepared send to a file destination (the real producers).
        project = _http(base, "POST", "/api/projects", {"name": "Payments ledger cutover"})["project"]["id"]
        update = _http(base, "POST", f"/api/projects/{project}/updates/draft", {})["update"]["id"]
        _http(base, "PUT", f"/api/updates/{update}", {"body_md": "The ledger cutover is on track for Friday."})
        _http(base, "POST", f"/api/updates/{update}/publish", {})
        folder = tmp_path / "team"
        folder.mkdir()
        dest = _http(base, "POST", "/api/channels/destinations",
                     {"name": "Team folder", "channel": "file", "folder": str(folder)})["destination"]["id"]
        send = _http(base, "POST", "/api/channels/sends",
                     {"document_ref": f"project_update:{update}", "destination_id": dest})["send"]["id"]
        pages["send"] = _http(base, "POST", "/api/reach/packages", {"refs": [f"send:{send}"]})["path"]
        pages["question"] = _http(base, "POST", "/api/reach/packages", {"refs": ["coder:claude:s-1"]})["path"]
        expired = _http(base, "POST", "/api/reach/packages", {"refs": [f"program:{held}:{turn(held, 'commit')['id']}"]})
        _http(base, "POST", f"/api/reach/packages/{expired['id']}/revoke", {})
        pages["expired"] = expired["path"]
        for width in (393, 1440):
            for name, path in pages.items():
                ctx, page, errors = _page(pw_browser, width)
                page.goto(base + path, wait_until="load")
                page.locator("[data-testid=briefing-page], [data-testid=briefing-expired], main").first.wait_for(timeout=30_000)
                page.wait_for_timeout(800)
                _shot(page, f"briefing-{name}-{width}")
                page.screenshot(path=str(SHOTS / f"briefing-{name}-{width}-full.png"), full_page=True)
                sideways = page.evaluate("() => document.documentElement.scrollWidth - document.documentElement.clientWidth")
                ctx.close()
                assert not errors, (name, width, errors)
                assert sideways <= 1, (name, width, sideways)
        # The decided page: his press on the send's page (the real channel.send), at 393 then 1440.
        for width in (393, 1440):
            ctx, page, errors = _page(pw_browser, width)
            page.goto(base + pages["send"], wait_until="load")
            choice = page.locator("[data-testid=briefing-choice-send]")
            if width == 393:  # the press happens once; the 1440 read shows the decided page
                choice.wait_for(timeout=30_000)
                choice.click()
            page.locator("[data-testid=briefing-outcome]").wait_for(timeout=30_000)
            _shot(page, f"briefing-decided-{width}")
            ctx.close()
            assert not errors, (width, errors)
        # The three-item page as he scrolls it on the phone: each item in view,
        # and at every scroll position at most one tray is pinned at the bottom.
        ctx, page, errors = _page(pw_browser, 393)
        page.goto(base + pages["three"], wait_until="load")
        page.locator("[data-testid=briefing-question]").first.wait_for(timeout=30_000)
        for index in range(3):
            page.locator("[data-testid=briefing-question]").nth(index).scroll_into_view_if_needed()
            page.wait_for_timeout(500)
            _shot(page, f"briefing-three-item{index + 1}-393")
        height = page.evaluate("() => document.documentElement.scrollHeight")
        for top in range(0, height, 200):
            page.evaluate("(y) => window.scrollTo(0, y)", top)
            page.wait_for_timeout(60)
            pinned = page.evaluate("""() => [...document.querySelectorAll('.briefing-tray')].filter((tray) => {
                const box = tray.getBoundingClientRect(); const own = tray.parentElement.getBoundingClientRect();
                return box.bottom >= innerHeight - 1 && box.top < innerHeight && own.bottom > innerHeight + 1;
            }).length""")
            assert pinned <= 1, (top, pinned)
        text = page.evaluate("() => document.body.innerText")
        assert not re.search(r"\b([2-9]|\d\d) waits on you", text), "the page's status line says N waits"
        ctx.close()
        assert not errors, errors
        # On the three-item page, one press settles that item alone (the File row).
        ctx, page, errors = _page(pw_browser, 393)
        page.goto(base + pages["three"], wait_until="load")
        page.locator("[data-testid=briefing-choice-file]").first.click()
        page.wait_for_timeout(1200)
        _shot(page, "briefing-three-one-settled-393")
        page.screenshot(path=str(SHOTS / "briefing-three-one-settled-393-full.png"), full_page=True)
        ctx.close()
        assert not errors, errors
    finally:
        server.stop()
