"""PHILO-15 lane 18 on a real hub: the rest of rehearsal 1B's first afternoon.

A real hub on an isolated HOME at 1440 and 393. Nothing leaves the machine:
gh, acli, claude and codex are stubs on PATH that are never run (every read
here is a file read), and the hand runs through the C3 launch rig.

- B31: gh's own ``hosts.yml`` names a login. The first-run Connections card
  and Settings › Connections read the same entry: SIGNED IN · karolswdev ·
  FROM GH CONFIG, with no check time; the footer says NOT CHECKED until a
  real probe (main: the card said SIGNED IN, Connections said NEVER CHECKED).
- B34/B35: two ready agents without hooks. With nothing selected the
  Conductor drawer offers Install hooks for each; the press reads
  HOOKS INSTALLED · CLAUDE CODE · hh:mm (main: no verb until a selection,
  no receipt for a success).
- B36: Claude Code's sign-in is unknown, Codex's is known. The drawer's
  Hand to agent line is on Codex and says CLAUDE CODE · SIGN-IN UNKNOWN.
- B56: an aftercare card with 2 to review leaves once both are handled
  (main: the card kept "2 to review").

Each test takes its shot BEFORE its assertions, so the same file run on
clean main records the before state. Shots: ``$LANE18_SHOTS`` or
``.tmp/evidence-shots/p15-18/``.
"""
from __future__ import annotations

import json
import os
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from tests._evidence import evidence_dir

from .glass_infra import _api, _boot, _ensure_build, _normal_chair, _settle

pytest.importorskip("playwright.sync_api", reason="the lane 18 glass needs Playwright")

TOKEN = "p15-18-rest"
SIZES = {1440: 900, 393: 852}
T = 20_000
SHOTS = Path(os.environ["LANE18_SHOTS"]) if os.environ.get("LANE18_SHOTS") else evidence_dir("p15-18")
SHOTS.mkdir(parents=True, exist_ok=True)


def _stubs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, *names: str) -> None:
    """Executables on PATH that the hub only looks up (never runs)."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(exist_ok=True)
    for name in names:
        stub = bin_dir / name
        stub.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
        stub.chmod(0o755)
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ.get('PATH', '')}")


def _no_owner_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ("GH_CONFIG_DIR", "XDG_CONFIG_HOME", "ANTHROPIC_API_KEY", "CLAUDE_CONFIG_DIR", "CODEX_HOME",
                 "GH_TOKEN", "GITHUB_TOKEN"):
        monkeypatch.delenv(name, raising=False)


def _page(pw: Any, base: str, width: int, *, onboarding: bool = True) -> tuple[Any, Any, list[str]]:
    browser = pw.chromium.launch(headless=True)
    ctx = browser.new_context(viewport={"width": width, "height": SIZES[width]}, device_scale_factor=2,
                              has_touch=width < 720, reduced_motion="reduce")
    page = ctx.new_page()
    page.set_default_timeout(30_000)
    errors: list[str] = []
    page.on("pageerror", lambda e: errors.append(str(e)[:200]))
    page.goto(f"{base}/?token={TOKEN}", wait_until="load")
    if onboarding:
        _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
    return browser, page, errors


def _shot(page: Any, name: str, width: int) -> None:
    page.wait_for_timeout(400)
    page.screenshot(path=str(SHOTS / f"{name}-{width}.png"), full_page=width < 720)


# ── B31 ────────────────────────────────────────────────────────────────


class TestOneSignInTruth:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        _ensure_build()
        _no_owner_credentials(monkeypatch)
        home = tmp_path / "home"
        gh = home / ".config" / "gh"
        gh.mkdir(parents=True)
        (gh / "hosts.yml").write_text(
            "github.com:\n    users:\n        karolswdev:\n    git_protocol: https\n    user: karolswdev\n",
            encoding="utf-8")
        _stubs(tmp_path, monkeypatch, "gh")
        server, self.base = _boot(tmp_path, monkeypatch, token=TOKEN)
        try:
            yield
        finally:
            server.stop()

    @pytest.mark.parametrize("width", list(SIZES))
    def test_first_run_and_connections_say_the_same_sign_in(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, errors = _page(pw, self.base, width, onboarding=False)
            try:
                page.get_by_test_id("firstrun").wait_for(timeout=30_000)
                card = page.get_by_test_id("firstrun-connections")
                card.get_by_text("gh · karolswdev").wait_for(timeout=T)
                card.scroll_into_view_if_needed()
                _shot(page, "b31-firstrun-connections", width)
                card_text = card.inner_text()
                # Astra r2: visible, not just in the DOM. The sign-in chip and
                # every word in it lie inside the card's box, nothing clipped.
                geo = card.get_by_test_id("firstrun-connection-signin").evaluate("""(el) => {
                  const card = el.closest('[data-testid=firstrun-connections]').getBoundingClientRect();
                  const chip = el.querySelector('.surface-state-chip');
                  const r = chip.getBoundingClientRect();
                  const range = document.createRange(); range.selectNodeContents(chip);
                  const words = [...range.getClientRects()].map((b) => [b.left, b.right, b.top, b.bottom]);
                  let clipped = false;
                  // Clipped = a clipping ancestor's box does not hold the chip's box.
                  for (let a = chip.parentElement; a; a = a.parentElement) {
                    const cs = getComputedStyle(a);
                    if (/(hidden|clip|auto|scroll)/.test(cs.overflowX + cs.overflowY)) {
                      const b = a.getBoundingClientRect();
                      if (r.left < b.left - 1 || r.right > b.right + 1 || r.top < b.top - 1 || r.bottom > b.bottom + 1) clipped = true;
                    }
                    if (a.matches('[data-testid=firstrun-connections]')) break;
                  }
                  return { card: [card.left, card.right], chip: [r.left, r.right], words, clipped,
                           text: chip.innerText };
                }""")
                assert not geo["clipped"], geo
                assert geo["chip"][0] >= geo["card"][0] - 1 and geo["chip"][1] <= geo["card"][1] + 1, geo
                assert all(w[0] >= geo["card"][0] - 1 and w[1] <= geo["card"][1] + 1 for w in geo["words"]), geo
                assert "GH CONFIG" in " ".join(geo["text"].upper().split()), geo

                _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
                page.evaluate("""() => sessionStorage.setItem("hs.desk.staged-surface-open",
                    JSON.stringify({key: "configure-settings", scope: "integration:destinations"}))""")
                page.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
                github = page.locator('[data-testid="connections-github"]')
                github.wait_for(timeout=T)
                github.scroll_into_view_if_needed()
                _shot(page, "b31-settings-connections", width)
                row = " ".join(github.inner_text().upper().split())
                foot = page.locator(".surface-footer-layout").filter(has_text=re.compile("CHECKED", re.I)).first.inner_text().upper()

                assert "SIGNED IN · KAROLSWDEV · FROM GH CONFIG" in " ".join(card_text.upper().split()), card_text
                assert "NEVER CHECKED" not in row, row
                assert "SIGNED IN · KAROLSWDEV · FROM GH CONFIG" in row, row
                # A configured account is no check: no CHECKED time anywhere (Astra r1 P2).
                assert "NOT CHECKED" in foot and not re.search(r"CHECKED\s+\d", foot), foot
                assert not re.search(r"CHECKED\s+\d", row), row
                assert not errors, errors
            finally:
                browser.close()


# ── B34 / B35 ──────────────────────────────────────────────────────────


class TestInstallHooksForEveryAgent:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        _ensure_build()
        _no_owner_credentials(monkeypatch)
        _stubs(tmp_path, monkeypatch, "claude", "codex")
        server, self.base = _boot(tmp_path, monkeypatch, token=TOKEN)
        self.home = tmp_path / "home"
        try:
            yield
        finally:
            server.stop()

    @pytest.mark.parametrize("width", list(SIZES))
    def test_install_hooks_is_a_verb_for_each_agent_and_says_it_worked(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, errors = _page(pw, self.base, width)
            try:
                page.goto(f"{self.base}/conductor?token={TOKEN}", wait_until="load")
                window = page.locator(".conductor-window")
                window.locator(".desk-icon, .object-list-row").first.wait_for(timeout=T)
                _settle(page)
                _shot(page, "b34-conductor-drawer", width)
                verbs = window.locator(".surface-footer-verbs button").all_inner_texts()

                assert "Install hooks · Claude Code" in verbs and "Install hooks · Codex" in verbs, verbs
                window.get_by_role("button", name="Install hooks · Claude Code").click()
                receipt = window.get_by_test_id("conductor-install-done")
                receipt.wait_for(timeout=T)
                _shot(page, "b35-hooks-installed", width)
                assert receipt.inner_text().startswith("HOOKS INSTALLED · CLAUDE CODE · "), receipt.inner_text()
                settings = json.loads((self.home / ".claude" / "settings.json").read_text())
                assert settings.get("hooks"), settings
                page.wait_for_function(
                    "() => ![...document.querySelectorAll('.conductor-window .surface-footer-verbs button')]"
                    ".some((b) => b.textContent.trim() === 'Install hooks · Claude Code')", timeout=T)
                assert not errors, errors
            finally:
                browser.close()


# ── B36 ────────────────────────────────────────────────────────────────


class TestTheKnownSignInDefault:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        from .test_philo14_c3_drop_to_hand_glass import ACTION_ID, PROJECT, _seed

        _ensure_build()
        _no_owner_credentials(monkeypatch)
        _stubs(tmp_path, monkeypatch, "claude", "codex")
        home = tmp_path / "home"
        (home / ".codex").mkdir(parents=True)
        # Codex's sign-in is KNOWN (a stored key; a placeholder, never used).
        (home / ".codex" / "auth.json").write_text(json.dumps({"OPENAI_API_KEY": "sk-placeholder"}))
        server, self.base = _boot(tmp_path, monkeypatch, token=TOKEN)
        from holdspeak.db import get_database
        from holdspeak.services import agent_hand_preview, agent_hand_service
        from tests.unit.test_agent_hand import _rig

        db = get_database()
        _seed(db)
        rig = _rig(tmp_path / "hand", db, monkeypatch, item=("action", ACTION_ID), project=PROJECT)
        with db._connection() as conn:
            conn.execute("INSERT INTO project_resources (project_id, resource_ref) VALUES (?, ?)",
                         (PROJECT, f"repository:{rig.source.source_id}"))
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
        self.project, self.action_id = PROJECT, ACTION_ID
        try:
            yield
        finally:
            rig.tmux.ended = True
            server.stop()

    @pytest.mark.parametrize("width", list(SIZES))
    def test_the_hand_goes_to_the_agent_whose_sign_in_is_known(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, errors = _page(pw, self.base, width)
            try:
                _api(page, "PUT", "/api/authority/control-mode", {"control_mode": "yolo"}, token=TOKEN)
                page.goto(f"{self.base}/?token={TOKEN}&open=project:{self.project}", wait_until="load")
                _normal_chair(page)
                drawer = page.locator(".drawer-window")
                drawer.locator(f"[data-object-id='action:{self.action_id}']").first.wait_for(timeout=T)
                _settle(page)
                drawer.locator(f"[data-object-id='action:{self.action_id}']").first.click()
                drawer.get_by_role("button", name="Hand to agent").click()
                line = drawer.get_by_test_id("hand-confirm")
                line.wait_for(timeout=T)
                page.wait_for_function(
                    "() => / · YOLO · hs\\//.test(document.querySelector('.drawer-window .confirm-line-fact')?.textContent || '')",
                    timeout=T)
                line.scroll_into_view_if_needed()
                _shot(page, "b36-confirm-line", width)
                # PHILO-15 16: the agent word is a flip button now; read the words, not the layout.
                fact = " ".join(drawer.locator(".confirm-line-fact").inner_text().split())

                assert fact.startswith("CODEX · YOLO · "), fact
                assert line.get_by_test_id("hand-confirm-skipped").inner_text() == "CLAUDE CODE · SIGN-IN UNKNOWN"
                assert not errors, errors
            finally:
                browser.close()


# ── B56 ────────────────────────────────────────────────────────────────

CARD_MEETING = "m-b56-ledger"


def _seed_meeting_with_proposals() -> list[str]:
    from holdspeak.db import get_database
    from holdspeak.intel.models import ActionItem
    from holdspeak.meeting_session import IntelSnapshot, MeetingState, TranscriptSegment

    db = get_database()
    start = (datetime.now() - timedelta(minutes=40)).replace(microsecond=0)
    db.meetings.save_meeting(MeetingState(
        id=CARD_MEETING, started_at=start, ended_at=start + timedelta(minutes=30), title="Payments ledger sync",
        segments=[TranscriptSegment(text="Keep the old ledger read-only for 30 days.", speaker="Me",
                                    start_time=1.0, end_time=4.0)],
        intel=IntelSnapshot(timestamp=1.0, topics=["ledger"], summary="Read-only for 30 days.",
                            action_items=[ActionItem(task="Add a contributing file", owner="Me")]),
        intel_status="completed"))
    ids = []
    for kind, text in (("decision", "Keep the old ledger read-only for 30 days."),
                       ("action", "Add a contributing file to the repository.")):
        proposal = db.proposals.create_proposal(
            meeting_id=CARD_MEETING, project_id=None, kind=kind, text=text, source_plugin="summary")
        assert proposal is not None
        ids.append(proposal.id)
    return ids


class TestALiveAftercareCard:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        keyfile = tmp_path / "people.key"
        keyfile.write_text("{}")
        keyfile.chmod(0o600)
        monkeypatch.setenv("HOLDSPEAK_PEOPLE_KEYSTORE_FILE", str(keyfile))
        _ensure_build()
        server, self.base = _boot(tmp_path, monkeypatch, token=TOKEN)
        self.server = server
        self.proposals = _seed_meeting_with_proposals()
        try:
            yield
        finally:
            server.stop()

    @pytest.mark.parametrize("width", list(SIZES))
    def test_the_card_leaves_when_nothing_is_left_to_review(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        from holdspeak.db import get_database
        from holdspeak.meeting_aftercare import build_aftercare_ready_event

        with sync_playwright() as pw:
            browser, page, errors = _page(pw, self.base, width)
            try:
                page.reload(wait_until="load")
                _normal_chair(page)
                page.wait_for_timeout(800)
                _settle(page)
                event = build_aftercare_ready_event(get_database(), CARD_MEETING)
                assert event and event["proposal_total"] == 2, event
                self.server.broadcast("aftercare_ready", event)
                card = page.locator(".ambient-aftercare")
                card.get_by_text("2 to review").wait_for(timeout=T)
                card.scroll_into_view_if_needed()
                _shot(page, "b56-card-2-to-review", width)

                # He handles both, as the Needs row or Review wing does (the hub's routes).
                _api(page, "POST", f"/api/proposals/{self.proposals[0]}/dismiss", token=TOKEN)
                page.wait_for_timeout(1500)
                after_one = card.inner_text() if card.count() else ""
                _api(page, "POST", f"/api/proposals/{self.proposals[1]}/dismiss", token=TOKEN)
                page.wait_for_timeout(2500)
                _shot(page, "b56-card-after-handled", width)

                assert "1 to review" in after_one, after_one
                assert page.locator(".ambient-aftercare").count() == 0
                assert not errors, errors
            finally:
                browser.close()


# ── B40 ────────────────────────────────────────────────────────────────

LONG_TASK = ("Add a contributing file to the rehearsal repository with the three rules: branch from main, "
             "one change per pull request, every pull request names its test")
B40_PROJECT = "p-b40-ledger"
B40_ACTION = "m-b40-a1"

LABELS = r"""(scope) => [...document.querySelectorAll(scope + ' .desk-icon-name')].map((e) => {
  const cs = getComputedStyle(e);
  const line = parseFloat(cs.lineHeight) || parseFloat(cs.fontSize) * 1.25;
  return { title: e.title, text: e.innerText, lines: Math.round(e.getBoundingClientRect().height / line),
           hidden: e.scrollHeight > e.clientHeight + 1 };
})"""


class TestTwoLineDrawerLabels:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        import holdspeak.agent_context as agent_context_pkg
        import holdspeak.delivery.factory_launch as factory_launch
        from holdspeak.agent_context import event_log

        _ensure_build()
        _no_owner_credentials(monkeypatch)
        state = tmp_path / "home" / ".holdspeak"
        state.mkdir(parents=True)
        monkeypatch.setattr(factory_launch, "DEFAULT_LAUNCHES_PATH", state / "agent_launches.json")
        monkeypatch.setattr(agent_context_pkg, "AGENT_CONTEXT_FILE", state / "agent_sessions.json")
        monkeypatch.setattr(event_log, "default_spool_dir", lambda: state / "agent-events")
        server, self.base = _boot(tmp_path, monkeypatch, token=TOKEN)
        self._seed(tmp_path / "home")
        try:
            yield
        finally:
            server.stop()

    @staticmethod
    def _seed(home: Path) -> None:
        """The rehearsal's Project drawer and Conductor: one long action item,
        and Codex at work on it (the hub's producers; no agent runs)."""
        from datetime import timezone

        import holdspeak.agent_context as agent_context_pkg
        from holdspeak.agent_context import event_log, ingest_agent_hook_event
        from holdspeak.db import get_database
        from holdspeak.delivery.factory_launch import LaunchLedger
        from holdspeak.meeting_session import IntelSnapshot, MeetingState, TranscriptSegment

        db = get_database()
        db.projects.create_project(project_id=B40_PROJECT, name="Payments ledger cutover", description="Nov 5.",
                                   keywords=["ledger"])
        start = datetime.now().replace(microsecond=0) - timedelta(hours=2)
        db.meetings.save_meeting(MeetingState(
            id="m-b40", started_at=start, ended_at=start + timedelta(minutes=30), title="Payments ledger sync",
            segments=[TranscriptSegment(text="Add the contributing file.", speaker="Me", start_time=1.0, end_time=4.0)],
            intel=IntelSnapshot(timestamp=1.0, topics=["ledger"], summary="Add the contributing file.", action_items=[{
                "id": B40_ACTION, "task": LONG_TASK, "owner": None, "due": None, "status": "pending",
                "review_state": "accepted", "source_timestamp": None, "created_at": start.isoformat()}]),
            intel_status="completed"))
        db.projects.associate_meeting_project(meeting_id="m-b40", project_id=B40_PROJECT, source="manual",
                                              confidence=1.0)
        with db._connection() as conn:
            item = str(conn.execute("SELECT id FROM action_items WHERE task=? LIMIT 1", (LONG_TASK,)).fetchone()[0])
        spool = {"state_path": agent_context_pkg.AGENT_CONTEXT_FILE, "events_spool_dir": event_log.default_spool_dir()}
        ingest_agent_hook_event(agent="codex", payload={
            "session_id": "c0dex000-b40", "cwd": str(home / "dev" / "rehearsal"),
            "hook_event_name": "PreToolUse", "tool_name": "Bash"}, **spool)
        attempt = db.work_attempts.create(
            source_id="src_b40", worktree_id="wt_b40", project="rehearsal", story_id=f"action-{item}",
            node_id="this-node", session_id="codex:c0dex000-b40", target_id="tgt_b40", kind="launch", exact=True,
            claimed_by="launch:codex-default", state="working", origin_ref=f"action:{item}")
        launched = (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat().replace("+00:00", "Z")
        LaunchLedger().record({
            "launch_schema": 1, "launch_id": "launch_b40", "state": "launched", "node_id": "this-node",
            "profile_id": "codex-default", "gate": "gated", "branch": f"hs/action-{item}", "session": "hs-launch_b40",
            "origin_ref": {"kind": "action", "id": item}, "attempt_id": attempt.attempt_id,
            "launched_at": launched, "control_mode": "normal", "instruction_state": "sent",
        })

    @staticmethod
    def _icons(page: Any, window: Any, group: str) -> None:
        if window.locator(".desk-icon").count() == 0:
            window.get_by_role("group", name=group).get_by_role("button", name="Icons").click()
        window.locator(".desk-icon").first.wait_for(timeout=T)
        page.wait_for_timeout(500)

    @staticmethod
    def _assert_two_lines(page: Any, scope: str, needle: str) -> None:
        labels = [label for label in page.evaluate(LABELS, scope) if needle in label["title"]]
        assert labels, page.evaluate(LABELS, scope)
        for label in labels:
            assert label["lines"] <= 2, label
            assert not label["hidden"], label
            if len(label["title"]) > 26:
                text = label["text"].replace("\n", " ")
                assert "…" in text and text.rstrip().endswith("test"), label
                assert text.startswith(label["title"].split(" ")[0]), label

    @pytest.mark.parametrize("width", list(SIZES))
    def test_the_drawer_and_the_conductor_labels_are_two_lines(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, errors = _page(pw, self.base, width)
            try:
                page.goto(f"{self.base}/?token={TOKEN}&open=project:{B40_PROJECT}", wait_until="load")
                _normal_chair(page)
                drawer = page.locator(".drawer-window")
                drawer.locator(f"[data-object-id='action:{B40_ACTION}']").first.wait_for(timeout=T)
                self._icons(page, drawer, "Drawer view")
                _settle(page)
                _shot(page, "b40-project-drawer", width)
                self._assert_two_lines(page, ".drawer-window:not(.conductor-window)", "contributing file")

                page.goto(f"{self.base}/conductor?token={TOKEN}", wait_until="load")
                _normal_chair(page)
                conductor = page.locator(".conductor-window")
                conductor.locator("[data-object-id='launch:launch_b40']").first.wait_for(timeout=T)
                self._icons(page, conductor, "Conductor view")
                _settle(page)
                _shot(page, "b40-conductor", width)
                self._assert_two_lines(page, ".conductor-window", "Codex:")
                assert not errors, errors
            finally:
                browser.close()


# ── B33 (Astra r1 P2): OFF is a choice, never a missing model ─────────


class TestSummariesOffInSettingsMeetings:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        _ensure_build()
        server, self.base = _boot(tmp_path, monkeypatch, token=TOKEN)
        from holdspeak.db import get_database
        from holdspeak.principals import Principal, PrincipalKind
        from holdspeak.services.inference_assignment_service import InferenceAssignmentService

        InferenceAssignmentService(get_database()).set_capability_off(
            Principal(PrincipalKind.OWNER, "b33-glass"), capability_id="meeting.deferred_analysis")
        try:
            yield
        finally:
            server.stop()

    @pytest.mark.parametrize("width", list(SIZES))
    def test_settings_meetings_says_summaries_off(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, errors = _page(pw, self.base, width)
            try:
                hub = _api(page, "GET", "/api/settings/hub", token=TOKEN)
                assert hub["meetings"]["summariesOff"] is True and hub["meetings"]["engineSet"] is False, hub
                page.evaluate("""() => sessionStorage.setItem("hs.desk.staged-surface-open",
                    JSON.stringify({key: "configure-settings", scope: "meetings"}))""")
                page.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
                off = page.get_by_test_id("settings-summaries-off")
                off.wait_for(timeout=T)
                off.scroll_into_view_if_needed()
                _shot(page, "b33-settings-meetings-off", width)
                assert off.inner_text().split("\n")[-1].strip().upper() == "SUMMARIES OFF"
                assert page.get_by_test_id("settings-no-model").count() == 0
                assert page.get_by_test_id("settings-choose-model").count() == 0
                assert not errors, errors
            finally:
                browser.close()
