"""PHILO-17 (evalerror) -- the owner's Evaluate on a source that cannot be
read reaches Needs you, on glass.

Before: ``POST /api/watches/{id}/evaluate`` answered 400 when gh was signed
out, but it never wrote ``last_error`` (only baseline did), so the source
still read as live and Needs you showed nothing wrong. Here, on a real hub at
1440 and 393 with an injected gh runner that answers as a signed-out gh
does, two live GitHub Watches in one Room are evaluated through the real
route and the hub's MCP transport (one ``project.watch.evaluate`` path):

  * before Evaluate, Needs you has no GitHub source row;
  * the route answers 400 ``connector_refresh_failed``; MCP gives the same code;
  * the HTTP message, the MCP error text, the stored error and the rendered
    Details hold none of the credentials the runner's stderr carried;
  * after it, one grouped row ``GitHub · 2 sources`` reads ``Not signed in``
    with one Reconnect, and the raw runner line stays out of the list.
"""
from __future__ import annotations

import json
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest

from .glass_infra import _FETCH_JS, _api, _assert_clean, _boot, _ensure_build, _normal_chair, _settle, seed_meeting_engines
from tests._evidence import evidence_dir

pytest.importorskip("playwright.sync_api", reason="the evaluate-error glass needs Playwright")

TOKEN = "philo17-evalerror"
SHOTS = evidence_dir("pm/roadmap/holdspeak-philo/phase-17/evalerror-shots")
SIZES = {1440: 900, 393: 852}
SIGNED_OUT = "To get started with GitHub CLI, please run:  gh auth login"
#: Astra r1 (1): synthetic credentials in the runner's stderr. None of them
#: may reach the stored error or the rendered Details.
CREDENTIAL_LINES = (
    "token ghp_AAAAbbbbCCCCddddEEEEffffGGGGhhhh1234",
    "Authorization: Basic dXNlcjpodW50ZXIycGFzcw==",
    "fetch https://octo:hunter2pass@github.com/acme/app.git",
    "GET https://api.github.com/x?token=qwertyuiop123",
    "acli ATATT3xFfGF0abcdefghijklmnopqrstuvwxyz0123456789",
)
SECRETS = ("ghp_AAAA", "dXNlcjpodW50ZXIycGFzcw", "hunter2pass", "qwertyuiop123", "ATATT3xFfGF0")
SOURCES = "[data-testid='needs-source-row']"
WATCHES = ("w-eval-a", "w-eval-b")


def _signed_out_gh(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
    cmd = args[0] if args else kwargs.get("args", [])
    return subprocess.CompletedProcess(args=cmd, returncode=4, stdout="",
                                       stderr="\n".join((SIGNED_OUT, *CREDENTIAL_LINES)))


def _insert_live_watch(watch_id: str, project_id: str, repository: str) -> None:
    """A graduated GitHub Watch (state active, as the Door makes it) read
    five minutes ago, no error: a live source. No next check, so the hub's
    own sweep leaves it alone."""
    from holdspeak.db import get_database

    checked = (datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(minutes=5)).isoformat()
    with get_database()._connection() as conn:
        conn.execute(
            "INSERT INTO connector_watches "
            "(id, connector_id, query_kind, name, query_json, snapshot_json, enabled, last_success_at, "
            " last_error, project_id, state, created_at, updated_at) "
            "VALUES (?, 'gh', 'pull_requests', ?, ?, '[]', 1, ?, NULL, ?, 'active', datetime('now'), datetime('now'))",
            (watch_id, f"gh {repository}", json.dumps({"repository": repository}, sort_keys=True),
             checked, project_id),
        )


def _github_failed(page: Any) -> list[dict[str, Any]]:
    wire = _api(page, "GET", "/api/desk/needs-you?fresh=1", token=TOKEN)
    return [c for c in wire["coverage"] if c.get("provider") == "github" and c["state"] == "failed"]


@pytest.mark.parametrize("width", list(SIZES))
def test_a_failed_evaluate_reaches_needs_you_as_its_grouped_row(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int,
) -> None:
    from playwright.sync_api import sync_playwright

    _ensure_build()
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN, gh_runner=_signed_out_gh)
    seed_meeting_engines()
    errors: list[str] = []
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            ctx = browser.new_context(viewport={"width": width, "height": SIZES[width]}, has_touch=width < 720)
            page = ctx.new_page()
            page.set_default_timeout(30_000)
            page.on("pageerror", lambda e: errors.append(str(e)[:200]))
            page.goto(f"{url}/?token={TOKEN}", wait_until="load")
            _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
            room = _api(page, "POST", "/api/projects", {
                "name": "Payments ledger", "description": "PHILO-17 evaluate error",
                "command_id": "p17-evalerror-room",
            }, token=TOKEN)["project"]["id"]
            for n, watch_id in enumerate(WATCHES):
                _insert_live_watch(watch_id, room, f"acme/repo-{n}")

            # Live sources: nothing for the owner yet.
            assert _github_failed(page) == []

            # The owner's Evaluate, through the real route. gh is signed out.
            # Astra r1 (3): the exact refusal on both transports.
            result = page.evaluate(_FETCH_JS, ["POST", f"/api/watches/{WATCHES[0]}/evaluate", {}, TOKEN])
            assert result["status"] == 400, result
            assert result["payload"]["code"] == "connector_refresh_failed", result
            mcp = _api(page, "POST", "/api/mcp", {
                "jsonrpc": "2.0", "id": "evalerror", "method": "tools/call",
                "params": {"name": "project.watch.evaluate", "arguments": {"watch_id": WATCHES[1]}},
            }, token=TOKEN)
            assert mcp["result"]["isError"] is True, mcp
            assert json.loads(mcp["result"]["content"][0]["text"])["code"] == "connector_refresh_failed", mcp
            # Neither answer gives the caller a secret (an agent reads MCP).
            assert "gh auth login" in json.dumps(result["payload"]), result
            assert [x for x in SECRETS if x in json.dumps(result["payload"])] == [], result
            assert [x for x in SECRETS if x in json.dumps(mcp)] == [], mcp

            # Stored: the cause, no secret.
            from holdspeak.db import get_database
            for watch_id in WATCHES:
                stored = get_database().automations.get_watch(watch_id)["last_error"]
                assert "gh auth login" in stored, stored
                assert [x for x in SECRETS if x in stored] == [], stored

            failed = _github_failed(page)
            assert sorted(c["source_id"] for c in failed) == [f"watch:{w}" for w in WATCHES], failed
            assert {c["cause"] for c in failed} == {"Not signed in"}, failed

            page.reload(wait_until="load")
            _normal_chair(page)
            page.locator(".desk-bell").click()
            page.get_by_test_id("needs-drawer").wait_for(timeout=15_000)
            page.locator(SOURCES).first.wait_for(timeout=15_000)
            _settle(page)

            names = [n.strip() for n in page.locator(f"{SOURCES} .needs-row-name").all_inner_texts()]
            assert names == ["GitHub · 2 sources"], names
            group = page.locator(SOURCES).filter(has_text="GitHub · 2 sources")
            assert group.locator(".needs-row-fact").inner_text().strip() == "Not signed in"
            assert group.get_by_role("button", name="Reconnect: GitHub · 2 sources").count() == 1
            assert "gh auth login" not in page.get_by_test_id("needs-list").inner_text()
            page.screenshot(path=str(SHOTS / f"evaluate-error-{width}.png"))

            # Details lists both sources; no secret is rendered.
            group.get_by_role("button", name="Details: GitHub · 2 sources").click()
            detail = page.get_by_test_id("needs-detail")
            detail.wait_for()
            assert detail.locator("li").count() == 2
            shown = page.get_by_test_id("needs-drawer").inner_text()
            assert [x for x in SECRETS if x in shown] == [], shown
            _settle(page)
            page.screenshot(path=str(SHOTS / f"evaluate-error-details-{width}.png"))
            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()
