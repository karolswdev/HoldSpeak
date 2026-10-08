"""PHILO-15 16, on a real hub: a Project knows its repository (B38), the hand
goes to either agent (B39), a meeting joins a Project (B37). 1440 and 393.

A real hub on an isolated HOME. GitHub is a `gh` double (the Door's own
fixture runner: auth, repo list, PR and CI reads). The hand runs through the
real routes and the hub's AgentHandService; only the process edge is the K2
launch rig (`tests/unit/test_agent_hand._rig`: git is real, tmux and the
agent are canned) and `gh repo clone` is a double that makes a real git clone
on disk. Nothing leaves the machine.

- The Door: a Project made with its GitHub repository; the drawer's Get Info
  (nothing selected) reads REPOSITORY · owner/name · NOT CLONED.
- The hand: the ConfirmLine names the clone (GITHUB.COM, CLONES owner/name),
  the owner flips the agent token to CODEX, Hand clones (CLONED) and
  launches Codex. At 393 the drawer's Hand to agent verb reaches the same line.
- Add to Project ▸ on the meeting record puts a loose meeting in the Project;
  the drawer then lists it.

Shots go to `.tmp/evidence-shots/p15-16/`.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

import pytest

from tests._evidence import evidence_dir

from .glass_infra import _api, _boot, _ensure_build, _normal_chair, _settle
from .test_hs169_door_glass import _GH_AUTH_CONNECTED, _make_gh_runner, _open_door, _write_gh_fixture

pytest.importorskip("playwright.sync_api", reason="the lane-16 glass needs Playwright")

TOKEN = "p15-16-repo"
SHOTS = evidence_dir("p15-16")
SIZES = {1440: 900, 393: 852}
T = 20_000
REPO = "karolswdev/holdspeak-dayone-rehearsal-1558"
PROJECT = "p-ledger"
ACTION_ID = "m-sync-a1"
ACTION = "Add a contributing file"
LOOSE = "m-loose"


def _seed(db: Any) -> None:
    from datetime import datetime, timedelta

    from holdspeak.meeting_session import IntelSnapshot, MeetingState, TranscriptSegment

    db.projects.create_project(project_id=PROJECT, name="Payments ledger cutover", description="Nov 5.",
                               keywords=["ledger"])
    start = datetime.now().replace(microsecond=0) - timedelta(hours=2)
    db.meetings.save_meeting(MeetingState(
        id="m-sync", started_at=start, ended_at=start + timedelta(minutes=30), title="Payments ledger sync",
        segments=[TranscriptSegment(text="Add a contributing file by Friday.", speaker="Me", start_time=1.0,
                                    end_time=4.0)],
        intel=IntelSnapshot(timestamp=1.0, topics=["cutover"], summary="Contributing file.", action_items=[{
            "id": ACTION_ID, "task": ACTION, "owner": None, "due": None, "status": "pending",
            "review_state": "accepted", "source_timestamp": None, "created_at": start.isoformat()}]),
        intel_status="completed"))
    db.projects.associate_meeting_project(meeting_id="m-sync", project_id=PROJECT, source="manual", confidence=1.0)
    later = start + timedelta(hours=1)
    db.meetings.save_meeting(MeetingState(
        id=LOOSE, started_at=later, ended_at=later + timedelta(minutes=20), title="Ledger rollback review",
        segments=[TranscriptSegment(text="We keep the rollback plan.", speaker="Me", start_time=1.0, end_time=3.0)],
        intel=IntelSnapshot(timestamp=1.0, topics=["rollback"], summary="Keep the rollback plan.", action_items=[]),
        intel_status="completed"))


class _FakeGh:
    """`gh repo clone <owner/name> <dir> -- --quiet`: a real git clone on disk."""

    def __init__(self) -> None:
        self.calls: list[list[str]] = []

    def __call__(self, argv: list[str], env: Any) -> Any:
        self.calls.append(list(argv))
        target = Path(argv[4])
        target.mkdir(parents=True)
        (target / "README.md").write_text("# rehearsal\n", encoding="utf-8")
        for args in (["init", "-b", "main"], ["config", "user.email", "t@example.test"],
                     ["config", "user.name", "T"], ["add", "-A"], ["commit", "-m", "seed"],
                     ["remote", "add", "origin", f"{argv[3]}.git"]):
            subprocess.run(["git", "-C", str(target), *args], check=True, capture_output=True)
        return subprocess.CompletedProcess(argv, 0, "", "")


class TestProjectRepositoryGlass:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        _ensure_build()
        fixture = tmp_path / "gh_fixture.json"
        _write_gh_fixture(
            fixture, auth=_GH_AUTH_CONNECTED,
            repo_list={"stdout": json.dumps([{"name": REPO.split("/")[1], "owner": {"login": "karolswdev"},
                                              "visibility": "private"}]), "returncode": 0},
            pr_list={"stdout": "[]", "returncode": 0},
            run_list={"stdout": "[]", "returncode": 0},
        )
        server, base = _boot(tmp_path, monkeypatch, token=TOKEN, gh_runner=_make_gh_runner(fixture))
        self.server, self.base, self.home = server, base, tmp_path / "home"
        from holdspeak.db import get_database
        from holdspeak.services import agent_hand_preview, agent_hand_service, project_repository
        from tests.unit.test_agent_hand import _rig

        db = get_database()
        _seed(db)
        self.gh = _FakeGh()
        monkeypatch.setattr(project_repository, "_gh_clone", self.gh)
        # The process edge only (the K2 rig, Codex); the hub's own service and routes run.
        rig = _rig(tmp_path / "hand", db, monkeypatch, item=("action", ACTION_ID), project=PROJECT, agent="codex")
        self.rig = rig
        monkeypatch.setattr(agent_hand_service, "default_agent_hand_service", lambda *a, **k: rig.hand)
        real_hand = agent_hand_service.AgentHandService.hand
        monkeypatch.setattr(agent_hand_service.AgentHandService, "hand",
                            lambda _self, *a, **k: real_hand(rig.hand, *a, **k))
        real_reads = agent_hand_preview.LaunchReads
        files = rig.repo.parent
        monkeypatch.setattr(agent_hand_preview, "LaunchReads", lambda *a, **k: real_reads(
            profiles_path=files / "profiles.json", registry_path=files / "sources.json",
            ledger_path=files / "launches.json", which=lambda name: f"/bin/{name}", runner=rig.tmux,
        ))
        try:
            yield
        finally:
            rig.tmux.ended = True
            server.stop()

    def _page(self, pw: Any, width: int) -> tuple[Any, Any, list[str]]:
        browser = pw.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": width, "height": SIZES[width]}, device_scale_factor=2,
                                  has_touch=width < 720, reduced_motion="reduce")
        page = ctx.new_page()
        page.set_default_timeout(45_000)
        errors: list[str] = []
        page.on("pageerror", lambda e: errors.append(str(e)[:200]))
        page.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
        _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
        _api(page, "PUT", "/api/authority/control-mode", {"control_mode": "yolo"}, token=TOKEN)
        return browser, page, errors

    def _drawer(self, page: Any, project_id: str) -> Any:
        page.goto(f"{self.base}/?token={TOKEN}&open=project:{project_id}", wait_until="load")
        _normal_chair(page)
        drawer = page.locator(".drawer-window")
        drawer.locator("[data-testid=drawer-facts]").wait_for(timeout=T)
        _settle(page)
        return drawer

    def _repository_fact(self, page: Any, drawer: Any) -> str:
        drawer.get_by_test_id("drawer-get-info").click()
        fact = page.locator(".drawer-info-window .object-info-fact[data-fact=repository] dd")
        fact.wait_for(timeout=T)
        page.wait_for_function(
            "() => (document.querySelector('.drawer-info-window .object-info-fact[data-fact=repository] dd')"
            "?.textContent || '').includes(' · ')", timeout=T)
        _settle(page)
        return fact.inner_text()

    # ── B38: the Door registers the repository ────────────────────────

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", [1440, 393])
    def test_the_door_registers_the_repository(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, width)
            try:
                _api(page, "POST", "/api/connections/github/recheck", token=TOKEN)
                _open_door(page, self.base)
                page.get_by_test_id("door-outcome-input").fill("Contributing rules for the rehearsal repo")
                page.get_by_test_id("door-trigger-github").click()
                pick = page.get_by_test_id(f"door-pick-{REPO}")
                pick.wait_for(timeout=T)
                pick.click()
                page.get_by_test_id("door-counts-github").or_(page.locator(".door-row-status")).first.wait_for(timeout=T)
                counts = page.get_by_test_id("door-counts-github")
                if counts.count():
                    # No counter of zero (Astra on #1000): the fixture has no open PR.
                    assert counts.inner_text() == "CI —", counts.inner_text()
                _settle(page)
                page.screenshot(path=str(SHOTS / f"16-door-picked-{width}.png"))
                page.get_by_test_id("door-create").click()
                page.get_by_test_id("door-root").wait_for(state="detached", timeout=T)
                projects = _api(page, "GET", "/api/projects", token=TOKEN)["projects"]
                made = next(p for p in projects if p["name"].startswith("Contributing rules"))
                state = _api(page, "GET", f"/api/projects/{made['id']}/repository", token=TOKEN)
                assert (state["repository"], state["registered"], state["cloned"]) == (REPO, True, False), state
                assert self.gh.calls == []  # registered at create time, never cloned there
                drawer = self._drawer(page, made["id"])
                assert self._repository_fact(page, drawer) == f"{REPO} · NOT CLONED"
                page.screenshot(path=str(SHOTS / f"16-getinfo-not-cloned-{width}.png"))
                assert page.evaluate("() => document.documentElement.scrollWidth <= window.innerWidth")
                assert not errors, errors
            finally:
                browser.close()

    # ── B39 + B38: the line flips to Codex; the first hand clones ─────

    def _assert_cloned_launch(self, page: Any, line: Any, width: int) -> None:
        line.get_by_role("button", name="Hand", exact=True).click()
        line.get_by_test_id("hand-confirm-receipt").wait_for(timeout=T)
        page.wait_for_function(
            "() => (document.querySelector('[data-testid=hand-confirm-clone]')?.dataset.state) === 'cloned'",
            timeout=30_000,
        )
        clone = line.get_by_test_id("hand-confirm-clone")
        assert f"CLONED · {REPO}".upper() in clone.inner_text().upper()
        self._fits(page, line, clone.locator(".surface-token").first)
        assert line.get_by_test_id("hand-confirm-receipt").inner_text().startswith("LAUNCHED")
        _settle(page)
        page.screenshot(path=str(SHOTS / f"16-cloned-launched-{width}.png"))
        # The clone, its receipt and the launch, on the hub.
        path = self.home / ".holdspeak" / "repositories" / "karolswdev" / REPO.split("/")[1] / REPO.split("/")[1]
        assert (path / ".git").exists()
        assert len(self.gh.calls) == 1 and self.gh.calls[0][:4] == ["gh", "repo", "clone", f"https://github.com/{REPO}"]
        launches = json.loads((self.rig.repo.parent / "launches.json").read_text())["launches"]
        assert [x.get("profile_id") for x in launches] == ["codex-default"], launches
        assert (path.parent / f"hs-action-{ACTION_ID}" / ".git").exists()
        (SHOTS / f"16-launch-{width}.json").write_text(json.dumps({
            "fact": line.locator(".confirm-line-fact").inner_text(),
            "clone": clone.inner_text(),
            "receipt": line.get_by_test_id("hand-confirm-receipt").inner_text(),
            "launch": {k: launches[0].get(k) for k in ("launch_id", "profile_id", "source_id", "origin_ref")},
        }, indent=2))

    @staticmethod
    def _fits(page: Any, line: Any, token: Any) -> None:
        """Astra r1 on #1000 (finding 5): the clone token's visible box is
        inside the line and the viewport (presence alone cannot see a clip)."""
        box, frame = token.bounding_box(), line.bounding_box()
        vw = page.viewport_size["width"]
        assert box and frame, (box, frame)
        assert box["x"] >= frame["x"] - 0.5 and box["x"] + box["width"] <= frame["x"] + frame["width"] + 0.5, (box, frame)
        assert box["x"] + box["width"] <= vw, (box, vw)
        # The text is not cut inside the token either.
        assert token.evaluate("el => el.scrollWidth <= el.clientWidth + 1"), token.inner_text()

    def _line_to_codex(self, page: Any, drawer: Any, width: int) -> Any:
        line = drawer.get_by_test_id("hand-confirm")
        line.wait_for(timeout=T)
        page.wait_for_function(
            "() => /^CLAUDE CODE · YOLO · hs\\//.test(document.querySelector('.drawer-window .confirm-line-fact')"
            "?.textContent || '')", timeout=T)
        to_clone = line.get_by_test_id("hand-confirm-clone")
        to_clone.wait_for(timeout=T)
        assert "GITHUB.COM" in to_clone.inner_text() and f"CLONES {REPO}".upper() in to_clone.inner_text().upper()
        assert "NO REPOSITORY" not in line.inner_text()
        _settle(page)
        self._fits(page, line, to_clone.locator(".surface-token").first)
        page.screenshot(path=str(SHOTS / f"16-confirm-claude-{width}.png"))
        line.get_by_test_id("hand-confirm-agent").click()
        page.wait_for_function(
            "() => /^CODEX · YOLO · hs\\//.test(document.querySelector('.drawer-window .confirm-line-fact')"
            "?.textContent || '')", timeout=T)
        assert "API.OPENAI.COM" in line.inner_text()
        assert not (self.home / ".holdspeak" / "repositories").exists()  # nothing cloned before the press
        _settle(page)
        self._fits(page, line, to_clone.locator(".surface-token").first)
        page.screenshot(path=str(SHOTS / f"16-confirm-codex-{width}.png"))
        return line

    @pytest.mark.e2e
    def test_drop_flip_to_codex_and_the_first_hand_clones_1440(self) -> None:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, 1440)
            try:
                _api(page, "POST", f"/api/projects/{PROJECT}/repository", {"repository": REPO}, token=TOKEN)
                state = _api(page, "GET", f"/api/projects/{PROJECT}/repository", token=TOKEN)
                assert (state["repository"], state["cloned"]) == (REPO, False), state
                drawer = self._drawer(page, PROJECT)
                from .test_philo14_c3_drop_to_hand_glass import TestDropToHandGlass

                TestDropToHandGlass._clear_of_conductor(page)
                source = drawer.locator(f"[data-object-id='action:{ACTION_ID}']").first
                source.wait_for(timeout=T)
                target = page.locator(".desk-screen [data-object-id='drawer:conductor']")
                sb, tb = source.bounding_box(), target.bounding_box()
                page.mouse.move(sb["x"] + sb["width"] / 2, sb["y"] + sb["height"] / 3)
                page.mouse.down()
                page.mouse.move(sb["x"] + sb["width"] / 2 - 20, sb["y"] + sb["height"] / 3 + 10, steps=4)
                page.mouse.move(tb["x"] + tb["width"] / 2, tb["y"] + tb["height"] / 3, steps=16)
                for dx in (1, 0, 1, 0):
                    page.wait_for_timeout(120)
                    page.mouse.move(tb["x"] + tb["width"] / 2 + dx, tb["y"] + tb["height"] / 3)
                page.wait_for_timeout(200)
                page.mouse.up()
                line = self._line_to_codex(page, drawer, 1440)
                self._assert_cloned_launch(page, line, 1440)
                line.get_by_role("button", name="Close").click()
                assert self._repository_fact(page, drawer) == f"{REPO} · CLONED"
                page.screenshot(path=str(SHOTS / "16-getinfo-cloned-1440.png"))
                assert not errors, errors
            finally:
                browser.close()

    @pytest.mark.e2e
    def test_the_verb_flips_to_codex_and_clones_393(self) -> None:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, 393)
            try:
                _api(page, "POST", f"/api/projects/{PROJECT}/repository", {"repository": REPO}, token=TOKEN)
                drawer = self._drawer(page, PROJECT)
                drawer.get_by_text(ACTION, exact=True).first.click()
                drawer.get_by_role("button", name="Hand to agent").click()
                line = self._line_to_codex(page, drawer, 393)
                assert page.evaluate("() => document.documentElement.scrollWidth <= window.innerWidth")
                self._assert_cloned_launch(page, line, 393)
                assert not errors, errors
            finally:
                browser.close()

    # ── B38: an older Project with a watched repository gets Register ──

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", [1440, 393])
    def test_an_older_project_registers_from_the_drawer(self, width: int) -> None:
        from holdspeak.db import get_database
        from playwright.sync_api import sync_playwright

        with get_database()._connection() as conn:
            conn.execute(
                "INSERT INTO connector_watches (id, connector_id, query_kind, query_json, project_id) "
                "VALUES ('w-old', 'gh', 'pulls', ?, ?)", (json.dumps({"repository": REPO}), PROJECT))
        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, width)
            try:
                drawer = self._drawer(page, PROJECT)
                register = drawer.get_by_test_id("drawer-register")
                register.wait_for(timeout=T)
                assert self._repository_fact(page, drawer) == f"{REPO} · NOT REGISTERED"
                page.screenshot(path=str(SHOTS / f"16-register-offered-{width}.png"))
                # The Project's Info carries the same Register (at 393 it covers the drawer).
                page.locator(".drawer-info-window [data-testid=info-register]").click()
                register.wait_for(state="detached", timeout=T)
                page.wait_for_function(
                    "() => (document.querySelector('.drawer-info-window .object-info-fact[data-fact=repository] dd')"
                    "?.textContent || '').endsWith('NOT CLONED')", timeout=T)
                _settle(page)
                page.screenshot(path=str(SHOTS / f"16-registered-{width}.png"))
                assert not errors, errors
            finally:
                browser.close()

    # ── B37: a meeting joins a Project ────────────────────────────────

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", [1440, 393])
    def test_add_to_project_from_the_meeting_record(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, width)
            try:
                page.goto(f"{self.base}/?token={TOKEN}&open=meeting:{LOOSE}", wait_until="load")
                _normal_chair(page)
                button = page.get_by_test_id("add-to-project-button").first
                button.wait_for(timeout=T)
                button.scroll_into_view_if_needed()
                _settle(page)
                page.screenshot(path=str(SHOTS / f"16-record-add-to-project-{width}.png"))
                button.click()
                menu = page.get_by_role("menu", name="Add to Project")
                menu.wait_for(timeout=T)
                _settle(page)
                page.screenshot(path=str(SHOTS / f"16-record-project-menu-{width}.png"))
                menu.get_by_text("Payments ledger cutover").click()
                receipt = page.get_by_test_id("add-to-project-receipt").first
                receipt.wait_for(timeout=T)
                assert receipt.inner_text() == "IN PAYMENTS LEDGER CUTOVER"
                _settle(page)
                page.screenshot(path=str(SHOTS / f"16-record-added-{width}.png"))
                linked = _api(page, "GET", f"/api/meetings/{LOOSE}/projects", token=TOKEN)["projects"]
                assert [p["project_id"] for p in linked] == [PROJECT]
                drawer = self._drawer(page, PROJECT)
                drawer.get_by_text("Ledger rollback review").first.wait_for(timeout=T)
                page.screenshot(path=str(SHOTS / f"16-drawer-lists-meeting-{width}.png"))
                assert page.evaluate("() => document.documentElement.scrollWidth <= window.innerWidth")
                assert not errors, errors
            finally:
                browser.close()
