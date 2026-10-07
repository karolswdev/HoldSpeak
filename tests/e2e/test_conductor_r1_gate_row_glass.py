"""Conductor R1 (Astra on #916, condition a): a held tool call of a launch,
rendered. A real hub; a launch on its ledger; the agent's own credential
proposes a call outside the worktree through the real gate route, and the
YOLO mode holds it. On the Chair the Needs you row "Approve: <command>"
opens the system shade; Approve there decides the real proposal, and the
row leaves. A second hold is denied the same way.

PHILO-14 A5: the Needs-you window body is the smart drawer. The held call is
a `needs-row` whose fact is the whole command and whose lamp is HELD CALL;
its own verbs Approve and Deny (`needs-row-verb`, `data-verb`) decide the
real proposal from the row (the shade still lists it). A 198-char call the
hook cuts reads `… +90 CHARS` on the row and on the shade, and neither
offers Approve.
"""
from __future__ import annotations

import hashlib
import json
import time
import urllib.request
from pathlib import Path
from typing import Any

import pytest

from .glass_infra import _api, _assert_clean, _boot, _ensure_build, _normal_chair, _settle

pytest.importorskip("playwright.sync_api", reason="the gate row glass needs Playwright")

TOKEN = "r1-gate-row"
SESSION = "claude:glass-r1"


def _http(url: str, method: str, path: str, token: str, body: Any = None) -> tuple[int, Any]:
    request = urllib.request.Request(
        f"{url}{path}", method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return response.status, json.loads(response.read() or b"null")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode()[:400]


def _hold(url: str, credential: str, proposal_id: str, command: str, worktree: str) -> dict:
    """What the gate hook sends for one call outside the worktree."""
    args = json.dumps({"command": command}, separators=(",", ":"), sort_keys=True)
    digest = hashlib.sha256(args.encode()).hexdigest()
    status, body = _http(url, "POST", "/api/gate/proposals", credential, {
        "id": proposal_id, "tool": "Bash", "args_sha256": digest, "args_head": args[:120],
        "cwd": worktree, "ttl_seconds": 600,
        "classification": {"scope": "outside", "rule": "path_outside_worktree", "read_rule": "",
                           "push_branch": "", "root": worktree, "proposal_id": proposal_id,
                           "args_sha256": digest},
    })
    assert status == 200, body
    return body


def _open_needs(page: Any) -> None:
    """PHILO-14 A1: the default desk is the screen; Enter on its Needs you
    drawer opens the Needs-you window (the drawer)."""
    if page.locator("[data-testid='needs-drawer']").count():
        return
    icon = page.locator(".desk-screen [data-object-id='drawer:needs']")
    icon.focus()
    page.keyboard.press("Enter")
    page.locator("[data-testid='needs-drawer']").wait_for(timeout=10000)


def _row(page: Any, command: str) -> Any:
    return page.locator("[data-testid='needs-drawer'] [data-testid='needs-row']", has_text=command)


@pytest.mark.timeout(240)
def test_a_held_call_row_opens_the_shade_and_approve_and_deny_decide_it(tmp_path: Path, monkeypatch) -> None:
    _ensure_build()
    import holdspeak.delivery.factory_launch as factory_launch

    ledger_path = tmp_path / "home" / ".holdspeak" / "agent_launches.json"
    monkeypatch.setattr(factory_launch, "DEFAULT_LAUNCHES_PATH", ledger_path)
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    worktree = tmp_path / "wt"
    worktree.mkdir()
    factory_launch.LaunchLedger(ledger_path).record({
        "launch_schema": 1, "launch_id": "launch_glassr1", "state": "registered",
        "session_key": SESSION, "profile_id": "claude-default", "source_id": "src_none",
        "worktree_id": "wt_none", "branch": "hs/action-glass", "session": "hs-glass",
    })
    errors: list[str] = []
    try:
        status, issued = _http(url, "POST", "/api/principals/agents", TOKEN, {"identity": SESSION})
        assert status == 201, issued
        credential = issued["credential"]
        first = _hold(url, credential, "toolu_glass_approve", "ls /etc", str(worktree))
        assert first["state"] == "held", first
        assert first["policy_snapshot"]["reason_code"] == "yolo_outside_own_worktree"

        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.goto(f"{url}/?token={TOKEN}", wait_until="load")
            _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
            page.reload(wait_until="load")
            _normal_chair(page)
            _settle(page)
            _open_needs(page)

            # The row: the whole command, HELD CALL, and its own Approve.
            row = _row(page, "ls /etc")
            row.wait_for(timeout=15000)
            assert (row.locator(".needs-row-fact").text_content() or "") == "ls /etc"
            assert "HELD CALL" in (row.locator(".needs-row-lamp").text_content() or "")
            row.locator("[data-verb='approve']").click()
            deadline = time.monotonic() + 10
            state = ""
            while time.monotonic() < deadline:
                _status, read = _http(url, "GET", "/api/gate/proposals/toolu_glass_approve", TOKEN)
                state = read.get("state") if isinstance(read, dict) else ""
                if state == "approved":
                    break
                time.sleep(0.2)
            assert state == "approved"
            assert read["decided_by"] != "control-mode"  # the owner's press

            # Deny: a second hold, the same row and shade.
            second = _hold(url, credential, "toolu_glass_deny", "cat /etc/hosts", str(worktree))
            assert second["state"] == "held"
            page.keyboard.press("Escape")
            page.reload(wait_until="load")
            _normal_chair(page)
            _settle(page)
            _open_needs(page)
            assert _row(page, "ls /etc").count() == 0  # the approved call left
            row = _row(page, "cat /etc/hosts")
            row.wait_for(timeout=15000)
            row.locator("[data-verb='deny']").click()
            deadline = time.monotonic() + 10
            while time.monotonic() < deadline:
                _status, read = _http(url, "GET", "/api/gate/proposals/toolu_glass_deny", TOKEN)
                if isinstance(read, dict) and read.get("state") == "denied":
                    break
                time.sleep(0.2)
            assert read["state"] == "denied"

            # PHILO-14 A5 (Astra r2): a 198-char call the hook cuts. The body
            # is the hook's own (`coder_gate.redact_call`: the hash, the
            # 120-char head, the length of the shown command), through the
            # real gate route. Every approval surface reads `… +90 CHARS`
            # and none offers Approve.
            from holdspeak.coder_gate import redact_call

            base = "psql -h staging-ledger -U ops -d payments -c 'select count(*) from entries where ledger_id = "
            long_cmd = base + "7" * (198 - len(base) - 1) + "'"
            call = redact_call({"command": long_cmd})
            status, cut = _http(url, "POST", "/api/gate/proposals", credential, {
                "id": "toolu_glass_cut", "tool": "Bash", "args_sha256": call.sha256, "args_head": call.head,
                "args_len": call.length, "cwd": str(worktree), "ttl_seconds": 600,
                "classification": {"scope": "outside", "rule": "path_outside_worktree", "read_rule": "",
                                   "push_branch": "", "root": str(worktree), "proposal_id": "toolu_glass_cut",
                                   "args_sha256": call.sha256},
            })
            assert status == 200 and cut["state"] == "held", cut
            _status, listed = _http(url, "GET", "/api/gate/proposals?state=held", TOKEN)
            [card] = [p for p in listed["proposals"] if p["id"] == "toolu_glass_cut"]
            assert card["args_cut"] is True and card["args_hidden"] == 90, card
            page.reload(wait_until="load")
            _normal_chair(page)
            _settle(page)
            _open_needs(page)
            row = _row(page, "psql -h staging-ledger")
            row.wait_for(timeout=15000)
            fact = row.locator(".needs-row-fact").text_content() or ""
            assert fact.endswith("… +90 CHARS") and long_cmd.startswith(fact.removesuffix("… +90 CHARS")), fact
            assert row.locator("[data-verb='approve']").count() == 0
            assert row.locator("[data-verb='deny']").count() == 1 and row.locator("[data-verb='open']").count() == 1
            # The shade: the command shown whole-or-marked, Deny only.
            page.evaluate("() => window.dispatchEvent(new CustomEvent('hs-open-system-shade'))")
            card = page.locator(".desk-shade .desk-gate-item", has_text="psql -h staging-ledger").first
            card.wait_for(timeout=10000)
            assert (card.locator("[data-testid='shade-gate-command']").text_content() or "").endswith("… +90 CHARS")
            assert card.get_by_role("button", name="Approve").count() == 0
            assert card.get_by_role("button", name="Deny").count() == 1
            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()
