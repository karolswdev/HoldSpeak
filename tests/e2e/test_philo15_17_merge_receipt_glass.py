"""PHILO-15 lane 17 (B50-B53): the merged PR on the Room receipt and in the
sent update, AS RENDERED at 1440x900 and 393x852.

The launch's PR #1 is open on the launch ledger; GitHub is faked at the
``gh pr view`` boundary (the rehearsal's real PR #1, as ``gh pr view`` read it
on 2026-10-07). Everything after it is the real follow-through on the real hub.

  * PR #1 is open on the Room; it is merged on the fake GitHub and the hub's
    own poll (1 s here, 120 s in the product) closes the item: the open Room
    shows the receipt with no press.
  * The Room receipt names the PR by its own title and number, with Open PR
    and its GITHUB.COM egress chip; it wraps, so every part is visible.
  * The published update carries ``Merged: <PR title> (PR #1) <link>``; the
    sent file carries it too and has no ``[UNVERIFIED]`` mark.
  * "Draft with model" names no LOCAL + CLOUD.
"""
from __future__ import annotations

import json
from types import SimpleNamespace
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest

from .glass_infra import _api, _boot, _ensure_build, _normal_chair, _settle
from tests._evidence import evidence_dir

pytestmark = pytest.mark.chair_windows_open

pytest.importorskip("playwright.sync_api", reason="the merge receipt glass needs Playwright")

TOKEN = "philo15-17-merge"
SHOTS = evidence_dir("docs/internal/philo/phase-15/17-shots")
SIZES = {1440: 900, 393: 852}
T = 30_000
PROJECT = "proj-philo1517abcd"
ACTION = "action_philo15_17"
TASK = "Add a contributing file to the rehearsal repository with the three rules"
PR_TITLE = "Add CONTRIBUTING.md with the three pull request rules"
PR_URL = "https://github.com/karolswdev/holdspeak-dayone-rehearsal-1558/pull/1"
ROW = f"Merged: {PR_TITLE} (PR #1) {PR_URL}"


class FakeGitHub:
    """GitHub at the ``gh pr view`` boundary: PR #1, open until the test
    merges it (the receipts' ``view_pr``, as the hub's poll calls it)."""

    def __init__(self) -> None:
        self.state = "open"
        self.merged_at = ""

    def view_pr(self, source_id: str, url: str):
        merged = self.state == "merged"
        return {
            "url": PR_URL, "number": 1, "title": PR_TITLE, "state": self.state,
            "merged_at": self.merged_at if merged else "", "merged_sha": "f" * 40 if merged else "",
            "head_sha": "e" * 40, "review_decision": "", "ci": "none", "checks": [],
        }, "live"

    def merge(self) -> None:
        self.merged_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        self.state = "merged"


def _seed(launches: Path) -> None:
    """The Project, its action item, and the agent's launch with PR #1 open
    (kept on the launch, as K4's first sweep leaves it). Its cleanup is
    already final, so the merge only closes the item and reads as merged."""
    from holdspeak.db import get_database

    db = get_database()
    now = datetime.now(timezone.utc)
    with db._connection() as conn:
        conn.execute("INSERT INTO projects (id, name) VALUES (?, ?)", (PROJECT, "Payments ledger cutover"))
        conn.execute(
            "INSERT INTO meetings (id, started_at, title) VALUES ('m-1517', ?, 'Payments ledger sync')",
            ((now - timedelta(hours=1)).isoformat(),),
        )
        conn.execute(
            "INSERT INTO meeting_projects (meeting_id, project_id, confidence) VALUES ('m-1517', ?, 0.9)",
            (PROJECT,),
        )
        conn.execute(
            "INSERT INTO action_items (id, meeting_id, task, owner, status) VALUES (?, 'm-1517', ?, 'Me', 'open')",
            (ACTION, TASK),
        )
        conn.commit()
    launches.parent.mkdir(parents=True, exist_ok=True)
    launches.write_text(json.dumps({"launches_schema": 1, "launches": [{
        "launch_id": "launch-1517", "state": "registered", "attempt_id": "att-1517",
        "worktree_id": "wt-1517", "source_id": "src-1517", "launched_at": (now - timedelta(minutes=40)).isoformat(),
        "origin_ref": {"kind": "action", "id": ACTION}, "profile_id": "codex-default",
        "follow_through": {
            "pr_state": "pr_open",
            "pr": {"url": PR_URL, "number": 1, "title": PR_TITLE, "state": "open"},
            "cleanup": {"session": "killed", "worktree": "worktree_kept_not_ours", "mcp": "released",
                        "gate": "not_armed"},
        },
    }]}), encoding="utf-8")


class TestMergeReachesTheUpdate:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        from holdspeak.delivery import factory_launch, follow_through
        from holdspeak.delivery.attempts import WorkAttemptService
        from holdspeak.delivery.factory_launch import LaunchLedger

        _ensure_build()
        launches = tmp_path / "home" / ".holdspeak" / "agent_launches.json"
        monkeypatch.setattr(factory_launch, "DEFAULT_LAUNCHES_PATH", launches)
        # The hub's own PR poll, every 1 s instead of 120 s, reads the fake
        # GitHub; everything after the gh boundary is the real follow-through.
        self.github = FakeGitHub()
        monkeypatch.setattr(follow_through, "POLL_SECONDS", 1)
        monkeypatch.setattr(follow_through, "default_follow_through", lambda db: follow_through.FollowThroughObserver(
            db, ledger=LaunchLedger(launches), registry=SimpleNamespace(get=lambda _id: None), receipts=self.github,
            attempts=WorkAttemptService(db.work_attempts), control_mode=lambda: "yolo",
        ))
        server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
        self.base, self.tmp = base, tmp_path
        _seed(launches)
        try:
            yield
        finally:
            server.stop()

    def _stage(self, page: Any, key: str, scope: str) -> None:
        page.evaluate("""([key, scope]) => sessionStorage.setItem("hs.desk.staged-surface-open",
            JSON.stringify({key, scope}))""", [key, scope])
        page.reload(wait_until="load")
        _normal_chair(page)

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", list(SIZES))
    def test_the_receipt_and_the_sent_update(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            ctx = browser.new_context(viewport={"width": width, "height": SIZES[width]},
                                      device_scale_factor=1, has_touch=width < 720)
            page = ctx.new_page()
            page.set_default_timeout(T)
            try:
                page.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
                _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
                self._stage(page, "open-project-memory", f"project:{PROJECT}")
                page.locator("[data-testid=room-body]").wait_for()

                # 0. PR #1 is open: no receipt yet; the item shows its PR.
                page.locator("text=PR #1 · OPEN").first.wait_for()
                assert page.locator("[data-testid=room-merge-receipt]").count() == 0
                _settle(page)
                page.screenshot(path=str(SHOTS / f"17-room-pr-open-{width}.png"))

                # 1. Merged on GitHub; nobody presses anything. The hub's poll
                #    reads it, closes the item, and the open Room re-reads.
                self.github.merge()
                receipt = page.locator("[data-testid=room-merge-receipt]")
                receipt.wait_for(timeout=15_000)
                text = receipt.text_content() or ""
                assert text.startswith(f"DONE · {PR_TITLE} · PR #1 MERGED · "), text
                assert TASK not in text
                open_pr = page.locator("[data-testid=flight-open-pr]").last
                assert open_pr.get_attribute("aria-label") == f"Open PR #1: {PR_TITLE}"
                _settle(page)
                page.screenshot(path=str(SHOTS / f"17-room-receipt-{width}.png"))
                # Every part is visible (wraps, never clips): title, number, time.
                box = receipt.evaluate("e => ({sw: e.scrollWidth, cw: e.clientWidth, ws: getComputedStyle(e).whiteSpace})")
                assert box["ws"] == "normal" and box["sw"] <= box["cw"] + 1, box

                # 2. Draft, mark one line as the model does, publish (the API).
                drafted = _api(page, "POST", f"/api/projects/{PROJECT}/updates/draft",
                               {"generator": "deterministic"}, token=TOKEN)["update"]
                uid, body = drafted["id"], drafted["body_md"]
                assert ROW in body, body
                marked = body.replace("## Dependencies\n\nNo dependencies tracked.",
                                      "## Dependencies\n\n- **[UNVERIFIED]** No dependencies tracked.", 1)
                assert "[UNVERIFIED]" in marked
                _api(page, "PUT", f"/api/updates/{uid}", {"body_md": marked}, token=TOKEN)
                _api(page, "POST", f"/api/updates/{uid}/publish", {}, token=TOKEN)
                folder = self.tmp / f"sent-{width}"
                folder.mkdir()
                _api(page, "POST", "/api/channels/destinations",
                     {"name": "Sent folder", "channel": "file", "folder": str(folder)}, token=TOKEN)

                # 3. The update: Draft with model names no LOCAL + CLOUD; send it.
                page.locator("[data-testid=updates-verb]").click()
                page.locator("[data-testid=update-posture]").wait_for()
                chip = page.locator("[data-testid=update-draft-model-action] .gadget-chip-egress")
                chip.wait_for()
                page.wait_for_timeout(500)
                assert "LOCAL + CLOUD" not in (chip.text_content() or "").upper()

                page.locator("[data-testid=update-list]").wait_for()
                page.locator(f"[data-testid=update-list-item]:has([data-update-id='{uid}'])").first.click()
                page.locator("[data-testid=send-well]").wait_for()
                row = "[data-testid=destination-row]:has([data-destination='Sent folder'])"
                opened = "[data-testid=send-open][data-destination='Sent folder']"
                if not page.locator(opened).count():
                    page.locator(row).first.click()
                page.locator(f"{opened} [data-testid=send-verb]").first.click()
                page.wait_for_function(
                    "(sel) => !!document.querySelector(sel + ' [data-receipt=latest]:not([data-state=dispatching])')",
                    arg=opened, timeout=T,
                )
                page.wait_for_timeout(600)
                label = page.locator("[data-testid=update-generator-label]")
                if label.count():
                    assert "IA_" not in (label.first.text_content() or "").upper()
                _settle(page)
                page.screenshot(path=str(SHOTS / f"17-sent-update-{width}.png"))

                [sent] = list(folder.glob("*.md"))
                sent_text = sent.read_text(encoding="utf-8")
                assert ROW in sent_text, sent_text
                assert sent_text.startswith("# Payments ledger cutover · Update · "), sent_text
                assert "UNVERIFIED" not in sent_text and "No dependencies tracked." not in sent_text
                assert sent_text.rstrip().endswith("1 claim not checked, kept on the desk.")
                assert "meeting_summary_unavailable" not in sent_text
                (SHOTS / f"17-sent-update-{width}.md").write_text(sent_text, encoding="utf-8")
            finally:
                browser.close()
