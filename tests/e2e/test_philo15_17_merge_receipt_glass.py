"""PHILO-15 lane 17 (B50-B53): the merged PR on the Room receipt and in the
sent update, AS RENDERED at 1440x900 and 393x852.

The merge is K4's own receipt: ``FollowThroughService.complete`` with the
evidence the follow-through writes (the PR's url, number, title, merge
time), and the launch's follow-through state on the launch ledger. The PR is
the rehearsal's real PR #1 (as ``gh pr view`` read it on 2026-10-07).

  * The Room receipt names the PR by its own title and number, with Open PR
    and its GITHUB.COM egress chip.
  * The published update carries ``Merged: <PR title> (PR #1) <link>``; the
    sent file carries it too and has no ``[UNVERIFIED]`` mark.
  * "Draft with model" names no LOCAL + CLOUD.
"""
from __future__ import annotations

import json
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


def _seed(launches: Path) -> None:
    from holdspeak.db import get_database
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services.follow_through_service import FollowThroughService

    db = get_database()
    now = datetime.now(timezone.utc)
    merged_at = (now - timedelta(minutes=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
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
    evidence = {
        "pr_url": PR_URL, "pr_number": "1", "pr_title": PR_TITLE, "merged_sha": "f" * 40,
        "merged_at": merged_at, "attempt_id": "att-1517", "launch_id": "launch-1517",
    }
    FollowThroughService(db).complete(
        Principal(PrincipalKind.OWNER, "heartbeat-conductor"), ACTION, "done", {"evidence": evidence},
    )
    launches.parent.mkdir(parents=True, exist_ok=True)
    launches.write_text(json.dumps({"launches_schema": 1, "launches": [{
        "launch_id": "launch-1517", "state": "registered", "attempt_id": "att-1517",
        "worktree_id": "wt-1517", "source_id": "src-1517", "launched_at": (now - timedelta(minutes=40)).isoformat(),
        "origin_ref": {"kind": "action", "id": ACTION}, "profile_id": "codex-default",
        "follow_through": {
            "pr_state": "pr_merged", "close": "closed", "evidence": evidence, "done": True,
            "pr": {"url": PR_URL, "number": 1, "title": PR_TITLE, "state": "merged"},
            "cleanup": {"session": "killed", "worktree": "worktree_removed"},
        },
    }]}), encoding="utf-8")


class TestMergeReachesTheUpdate:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        from holdspeak.delivery import factory_launch

        _ensure_build()
        launches = tmp_path / "home" / ".holdspeak" / "agent_launches.json"
        monkeypatch.setattr(factory_launch, "DEFAULT_LAUNCHES_PATH", launches)
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

                # 1. The Room receipt: the PR's title and number, Open PR, egress.
                receipt = page.locator("[data-testid=room-merge-receipt]")
                receipt.wait_for()
                text = receipt.text_content() or ""
                assert text.startswith(f"DONE · {PR_TITLE} · PR #1 MERGED · "), text
                assert TASK not in text
                open_pr = page.locator("[data-testid=flight-open-pr]").last
                assert open_pr.get_attribute("aria-label") == f"Open PR #1: {PR_TITLE}"
                _settle(page)
                page.screenshot(path=str(SHOTS / f"17-room-receipt-{width}.png"))

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
                assert "UNVERIFIED" not in sent_text
                (SHOTS / f"17-sent-update-{width}.md").write_text(sent_text, encoding="utf-8")
            finally:
                browser.close()
