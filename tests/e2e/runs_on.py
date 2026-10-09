"""PHILO-16 (C) -- the Runs on window (the Models window as a Switchboard),
for every browser test that drives it. One place for the gestures, so the
ported rigs ask the board the same way.

- ``open_runs_on``  stage the window and wait for the board.
- ``patch``         drag an engine onto a job (1440) or open the job and tap
                    the engine (the 393 list); waits for the write's answer.
- ``receipt``       the foot's receipt text.
- ``close_runs_on`` the window's own Close gadget.
"""
from __future__ import annotations

import re
from typing import Any

ROOT = "[data-testid='runson-root']"
RECEIPT = "[data-testid='runson-receipt']"


def engine_key_for(url: str) -> str:
    """The board key of an engine added at ``url`` (endpointDraft.ts
    `endpointProfileId`: ``engine-<host-port slug>``)."""
    host = re.sub(r"^[a-z]+://", "", url.strip(), flags=re.I).split("/")[0]
    slug = re.sub(r"[^a-z0-9]+", "-", host.lower()).strip("-")
    return f"engine-{slug or 'endpoint'}"[:96]


def open_runs_on(page: Any, *, scope: str | None = None, staged: bool = True) -> Any:
    """Open Runs on through the staged-surface seam and wait for the board."""
    if staged:
        page.evaluate(
            """([key, scope]) => sessionStorage.setItem(
                 "hs.desk.staged-surface-open",
                 JSON.stringify(scope ? {key, scope} : {key}))""",
            ["open-concierge", scope],
        )
        page.reload(wait_until="load")
        from .glass_infra import _normal_chair

        _normal_chair(page)
    page.locator(ROOT).wait_for(timeout=30_000)
    page.get_by_test_id("switchboard").wait_for(timeout=30_000)
    return page.locator(ROOT)


def wait_board(page: Any) -> Any:
    page.locator(ROOT).wait_for(timeout=30_000)
    page.get_by_test_id("switchboard").wait_for(timeout=30_000)
    return page.locator(ROOT)


def window(page: Any) -> Any:
    return page.locator(".desk-surface-window").filter(has=page.locator(ROOT)).first


def receipt(page: Any) -> str:
    node = page.locator(RECEIPT)
    return (node.text_content() or "") if node.count() else ""


def wait_receipt(page: Any, pattern: str, timeout: int = 60_000) -> str:
    page.wait_for_function(
        "([sel, pat]) => new RegExp(pat).test(document.querySelector(sel)?.textContent || '')",
        arg=[RECEIPT, pattern],
        timeout=timeout,
    )
    return receipt(page)


def patch(page: Any, job: str, engine_key: str, *, fallback: bool = False) -> dict[str, Any]:
    """Patch ``engine_key`` onto ``job`` the way the owner does at this width.
    Returns the body of the one ``/api/inference/assignments/set`` write."""
    board = page.get_by_test_id("switchboard")
    board.wait_for(timeout=30_000)
    plate = page.get_by_test_id(f"switchboard-engine-{engine_key}")
    with page.expect_response(
        lambda r: r.url.endswith("/api/inference/assignments/set"), timeout=60_000
    ) as written:
        if board.get_attribute("data-layout") == "list":
            page.get_by_test_id(f"switchboard-job-{job}").click()
            page.get_by_test_id(f"switchboard-tap-{engine_key}").click()
        else:
            plate.wait_for(timeout=30_000)
            if fallback:
                page.keyboard.down("Alt")
            plate.drag_to(page.get_by_test_id(f"switchboard-job-{job}"))
            if fallback:
                page.keyboard.up("Alt")
    assert written.value.ok, written.value.text()
    wait_receipt(page, r"^PATCHED ")
    return written.value.request.post_data_json


def close_runs_on(page: Any) -> None:
    window(page).get_by_role("button", name="Close Runs on").click()
    page.wait_for_function(f"() => !document.querySelector(\"{ROOT}\")", timeout=30_000)


def raw_buttons(page: Any) -> list[str]:
    """UX-CANON A1: every verb in the window is the library Button."""
    return page.evaluate(
        """() => [...document.querySelectorAll(
             "[data-testid='runson-root'] button, .runson-foot button")]
             .filter((b) => {
               const c = b.className.split(" ");
               return !c.includes("btn") && !c.includes("desk-mic")
                 && !c.includes("gadget-chip-egress");
             })
             .map((b) => (b.textContent || b.className).slice(0, 40))"""
    )


def primaries(page: Any) -> list[str]:
    return page.evaluate(
        """() => [...document.querySelectorAll(
             "[data-testid='runson-root'] .btn--primary, .runson-foot .btn--primary")]
             .map((b) => (b.textContent || "").trim())"""
    )
