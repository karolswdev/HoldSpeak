"""PHILO-10-02 round two (Codex Astra r1 finding 1): the UNKNOWN nudge on the real hub, at 1440 and 393.

The real hub, the real Room face (the built bundle), the real nudge.send: the gh
process edge times out, so the hub answers UNKNOWN (the step ``unknown``, the
kernel ``indeterminate``). The card then shows ``RESULT UNKNOWN · CHECK #612`` and
no Send verb -- after the press, after closing and reopening the card, and after
a page reload that reads the persisted step. The shots are for the owner's canvas
review in story 04 (a change on the ratified nudge card, forced by correctness).
"""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

import pytest

from tests._evidence import evidence_dir

from .glass_infra import _assert_clean, _boot, _ensure_build, _settle
from .test_hs173_health_glass import (
    TOKEN,
    _assert_no_raw_button,
    _init_desk,
    _open_room,
    _patch_resolve_review_people,
    _seed_nudge_project_and_step,
    _shot,
)

pytest.importorskip("playwright.sync_api", reason="Room glass needs Playwright")

SHOTS = evidence_dir("pm/roadmap/holdspeak-philo/phase-10-the-channels/assets/story-02-shots")
SHOTS.mkdir(parents=True, exist_ok=True)


def _timeout_gh(monkeypatch: pytest.MonkeyPatch) -> list[list[str]]:
    import holdspeak.services.channel_cli as channel_cli
    import holdspeak.services.project_steward_service as pss

    calls: list[list[str]] = []

    def gh(argv: Any, **_kwargs: Any) -> Any:
        calls.append(list(argv))
        raise subprocess.TimeoutExpired(list(argv), 30)

    monkeypatch.setattr(channel_cli, "CLI_RUNNER", gh)
    original = pss.ProjectStewardService.send_nudge

    def send_nudge(self: Any, principal: Any, step_id: str, text: str) -> dict:
        self._subprocess_runner = gh
        return original(self, principal, step_id, text)

    monkeypatch.setattr(pss.ProjectStewardService, "send_nudge", send_nudge)
    return calls


def _unknown_and_no_send(page: Any, where: str) -> None:
    row = page.locator('[data-testid="nudge-unknown-row"]')
    assert row.count() == 1, f"{where}: no UNKNOWN row"
    text = row.inner_text().upper()
    assert "RESULT UNKNOWN" in text and "CHECK #612" in text and "GITHUB.COM" in text, f"{where}: {text}"
    assert page.locator('[data-testid="nudge-send"]').count() == 0, f"{where}: Send is offered again"


def _open_card(page: Any) -> None:
    page.locator('[data-testid="nudge-verb"]').first.click()
    page.wait_for_timeout(400)
    _settle(page)


def _run(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int) -> None:
    calls = _timeout_gh(monkeypatch)
    _patch_resolve_review_people(monkeypatch)
    keyfile = tmp_path / "people.key"
    keyfile.write_text("{}")
    keyfile.chmod(0o600)
    monkeypatch.setenv("HOLDSPEAK_PEOPLE_KEYSTORE_FILE", str(keyfile))
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    errors: list[str] = []
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": width, "height": 900 if width >= 1440 else 852})
            page.on("pageerror", lambda e: errors.append(str(e)))
            _init_desk(page, url)
            project_id, _step_id = _seed_nudge_project_and_step(page)
            _open_room(page, url, project_id)
            page.get_by_test_id("room-body").wait_for(timeout=15000)
            _settle(page)
            _open_card(page)
            page.locator('[data-testid="nudge-send"]').click()
            page.locator('[data-testid="nudge-unknown-row"]').wait_for(timeout=15000)
            _settle(page)
            _unknown_and_no_send(page, "after the press")
            _assert_no_raw_button(page)
            _shot(page, f"nudge-unknown-1-after-send-{width}", width, SHOTS)
            _open_card(page)  # close
            _open_card(page)  # reopen: a remount of the card
            _unknown_and_no_send(page, "after closing and reopening the card")
            _open_room(page, url, project_id)  # a page reload: the Room reads the persisted step
            page.get_by_test_id("room-body").wait_for(timeout=15000)
            _settle(page)
            _open_card(page)
            _unknown_and_no_send(page, "after a reload (the persisted step)")
            _shot(page, f"nudge-unknown-2-after-reload-{width}", width, SHOTS)
            assert len([c for c in calls if c[:3] == ["gh", "pr", "comment"]]) == 1
            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()


def test_the_unknown_nudge_is_never_offered_again_1440(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _ensure_build()
    _run(tmp_path, monkeypatch, 1440)


def test_the_unknown_nudge_is_never_offered_again_393(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _ensure_build()
    _run(tmp_path, monkeypatch, 393)
