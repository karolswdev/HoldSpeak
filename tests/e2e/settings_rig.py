"""The Settings navigation helpers of the HS-174 remote-access glass.

Moved verbatim from ``test_hs174_remote_settings_glass.py`` (the test diet,
2026-10-11: that file is parked; its checks moved to
``web/src/desk/__tests__/settings.app.test.tsx`` and
``tests/integration/test_desk_settings.py``). The grant glasses
(``test_settings_glass.py``, ``test_philo9_07_project_grant_glass.py``)
still drive the System module through these.
"""
from __future__ import annotations

from typing import Any

from .glass_infra import _api

TOKEN = "hs174-remote-settings"


def _navigate_to_settings_hub(page: Any, url: str) -> None:
    page.goto(f"{url}/?token={TOKEN}", wait_until="load")
    _api(page, "POST", "/api/desk/seed", token=TOKEN)
    _api(page, "PUT", "/api/setup/onboarding",
         {"disposition": "completed"}, token=TOKEN)
    page.evaluate("""() => {
        sessionStorage.setItem(
            "hs.desk.staged-surface-open",
            JSON.stringify({key: "configure-settings"})
        );
    }""")
    page.goto(f"{url}/?token={TOKEN}", wait_until="load")
    page.locator(".prefs-hub-headline").wait_for(timeout=10_000)


def _open_system_module(page: Any) -> None:
    # PHILO-17 REFIT: the rows past Runs on and Accounts fold under More settings.
    more = page.locator("[data-testid='settings-more'][aria-expanded='false']")
    if more.count():
        more.click()
    system_row = page.locator(
        ".surface-ledger-row",
        has=page.locator(".surface-ledger-primary", has_text="System"),
    )
    system_row.locator(".btn", has_text="Open").click()
    # Wait for the module to load -- the Remote access group label
    page.locator(".gadget-group-label", has_text="Remote access").wait_for(timeout=8_000)
