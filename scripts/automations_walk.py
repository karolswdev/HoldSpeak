#!/usr/bin/env python3
"""PR #461 -- Automations + Resourceful surface walk.

Screenshot + console-error proof for the Workbench's new Automations
configuration (Event start mode) and Resourceful configuration (Idle
start mode) at 1440x900 and 393x900.

Reuses scripts/chair_walk.py's Hub/Shooter/goto (isolated HOME, seeded
hub, console-error assertion).

Seeds a real workbench via the product seed, then creates an automation
via the API (POST /api/workbenches/{id}/automations) and configures a
resourceful policy (PUT /api/workbenches/{id}/resourceful) so the
surfaces render with real state.

Run:
    HOME=$(mktemp -d) PLAYWRIGHT_BROWSERS_PATH=~/Library/Caches/ms-playwright \
        uv run python scripts/automations_walk.py
"""
from __future__ import annotations

import json
import sys
import tempfile
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import chair_walk as cw  # noqa: E402
from chair_walk import Hub, Shooter, check, finding, goto, section, _free_port  # noqa: E402

WALK_OUT = REPO / "docs/evidence/automations-pr461"
TOKEN = "pr461-automations-walk-token"
VIEWPORTS = ((1440, 900), (393, 900))
WORKBENCH_ID = "hs-seed-workbench"


# --------------------------------------------------------- API helpers


def _api(hub: Hub, method: str, path: str, body: dict | None = None) -> dict | None:
    """Call a hub API endpoint. Returns the parsed JSON or None on error."""
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(
        f"{hub.url}{path}",
        data=data,
        method=method,
        headers={
            "Content-Type": "application/json",
            "X-HoldSpeak-Token": hub.token,
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())
    except Exception as exc:  # noqa: BLE001
        finding(f"API {method} {path} failed: {exc}")
        return None


def seed_automation(hub: Hub) -> bool:
    """Create an automation via the workbench preset facade.

    Uses the 'github-review-requested' preset with a sample repository.
    The adapter is not available (no real GitHub credentials), so the
    automation will show status 'unavailable' -- this is correct and
    proves the UI handles the degraded state.
    """
    section("seed automation via API")
    result = _api(hub, "POST", f"/api/workbenches/{WORKBENCH_ID}/automations", {
        "preset_id": "github-review-requested",
        "repository": "acme/widget",
    })
    ok = result is not None and "automation" in result
    check("seed automation via POST /api/workbenches/{id}/automations", ok,
          f"status={'created' if ok else 'failed'}")
    if ok:
        auto = result["automation"]
        check("automation has provider", auto.get("provider") == "github")
        check("automation has repository", auto.get("repository") == "acme/widget")
    return ok


def seed_resourceful(hub: Hub) -> bool:
    """Configure the resourceful policy via PUT.

    The seeded workbench has no recipe_id, so the service rejects
    enabled=True ("Bind an agent before enabling"). We configure the
    policy with enabled=False to prove the UI renders all gadgets,
    chips, and routines. The PAUSED state is the honest empty state
    for a workbench that has not yet bound an agent.
    """
    section("seed resourceful policy via API")
    result = _api(hub, "PUT", f"/api/workbenches/{WORKBENCH_ID}/resourceful", {
        "enabled": False,
        "idle_after_minutes": 30,
        "cooldown_hours": 6,
        "nightly_target": 2,
        "night_only": True,
        "night_start_hour": 22,
        "night_end_hour": 7,
        "routines": ["loose_ideas", "failed_work"],
    })
    ok = result is not None and "policy" in result
    check("seed resourceful via PUT /api/workbenches/{id}/resourceful", ok,
          f"status={'configured' if ok else 'failed'}")
    if ok:
        policy = result["policy"]
        check("policy disabled (no recipe)", policy.get("enabled") is False)
        check("policy routines set", policy.get("routines") == ["loose_ideas", "failed_work"])
    return ok


# --------------------------------------------------------- walk legs


def _open_workbench_config(shooter: Shooter, hub: Hub) -> bool:
    """Navigate to the workbench and ensure the config panel is open.

    Returns True if the config panel is visible.
    """
    goto(shooter, hub, "/")
    page = shooter.page

    # Open workbench via command palette (Cmd+K, type "Workbench", Enter).
    page.keyboard.press("Meta+k")
    page.wait_for_timeout(400)
    page.keyboard.type("Workbench")
    page.wait_for_timeout(600)
    page.keyboard.press("Enter")
    page.wait_for_timeout(2000)

    # Check if the config panel is already visible. If not, click the
    # "Expand configuration" strip to open it.
    config_panel = page.locator(".wb-config-panel")
    if config_panel.count() == 0:
        expand_btn = page.locator('button[aria-label="Expand configuration"]')
        if expand_btn.count():
            expand_btn.first.click()
            page.wait_for_timeout(1000)
        else:
            finding("no config panel and no expand button found")
            return False

    visible = page.locator(".wb-config-panel").count() > 0
    check("config panel visible", visible)
    return visible


def _select_start_mode(page: object, mode: str) -> bool:
    """Click a start-mode radio button by its text label."""
    btn = page.locator(f'button[role="radio"]:has-text("{mode}")')  # type: ignore[attr-defined]
    if btn.count() == 0:
        finding(f"start mode '{mode}' button not found")
        return False
    btn.first.click()  # type: ignore[attr-defined]
    page.wait_for_timeout(1500)  # type: ignore[attr-defined]
    checked = btn.first.get_attribute("aria-checked")  # type: ignore[attr-defined]
    ok = checked == "true"
    check(f"start mode '{mode}' selected", ok, f"aria-checked={checked}")
    return ok


def leg_automations_populated(shooter: Shooter, hub: Hub) -> None:
    """The Automations section with a seeded automation (Event mode)."""
    section(f"automations populated @{shooter.width}")

    if not _open_workbench_config(shooter, hub):
        return

    page = shooter.page
    if not _select_start_mode(page, "Event"):
        return

    # Check the automation presets area is visible.
    presets = page.locator('[aria-label="Automation presets"]')
    check("automation presets visible", presets.count() > 0)

    # Check the safety disclosure text is visible.
    safety_intro = page.locator(".wb-automation-safety")
    check("automation safety disclosure visible", safety_intro.count() > 0)

    # Check the repository input.
    repo_area = page.locator(".wb-automation-repository")
    check("repository input area visible", repo_area.count() > 0)

    # Check the seeded automation row is visible.
    auto_row = page.locator(".wb-automation")
    has_auto = auto_row.count() > 0
    check("seeded automation row visible", has_auto)

    if has_auto:
        # Check provider badge.
        provider = page.locator(".wb-automation-provider")
        check("provider badge visible", provider.count() > 0,
              f"text={provider.first.text_content() if provider.count() else 'none'}")

        # Check status chip.
        status_chip = auto_row.first.locator(".desk-chip")
        check("status chip visible", status_chip.count() > 0)

        # Expand the automation to show detail.
        head = page.locator(".wb-automation-head")
        if head.count():
            head.first.click()
            page.wait_for_timeout(800)

            detail = page.locator(".wb-automation-detail")
            check("automation detail expanded", detail.count() > 0)

            # Check safety copy.
            safety = page.locator(".wb-automation-safety")
            check("safety disclaimer visible", safety.count() > 0)

            # Check verb buttons (Test match, Enable/Pause).
            verbs = page.locator(".wb-automation-verbs button")
            check("automation verb buttons visible", verbs.count() > 0,
                  f"count={verbs.count()}")

    # Scroll the automation row into view so the shot captures the real
    # content (provider badge, status chip, detail). On narrow viewports
    # the whole section fits; on wide viewports the window's internal
    # scroll can hide the row below the fold if we only scroll "STARTS
    # WHEN" into view.
    auto_target = page.locator(".wb-automation-head")
    if auto_target.count():
        auto_target.first.scroll_into_view_if_needed()
        page.wait_for_timeout(300)
    else:
        starts_when = page.locator('text="STARTS WHEN"')
        if starts_when.count():
            starts_when.first.scroll_into_view_if_needed()
            page.wait_for_timeout(300)

    shooter.shot("automations", "wide" if shooter.width >= 1000 else "narrow",
                 "Workbench Automations section with seeded GitHub automation")
    shooter.assert_clean("automations populated")


def leg_automations_empty(shooter: Shooter, hub: Hub) -> None:
    """The Automations empty state (no automations, no repo entered)."""
    section(f"automations empty state @{shooter.width}")

    # The empty state is visible when no repo is entered and no automations
    # exist for a fresh workbench. Since we already seeded one automation,
    # the list is populated -- but the empty state text ("No event triggers
    # yet") is still visible if there were no automations. We can still
    # verify the presets and requirement message are there.
    # Note: we already have a seeded automation so this leg verifies the
    # requirement message when the repo field is empty.

    if not _open_workbench_config(shooter, hub):
        return

    page = shooter.page
    if not _select_start_mode(page, "Event"):
        return

    # The requirement message should show when the repo field is empty.
    requirement = page.locator(".wb-automation-requirement")
    # Clear the repo field if it has content.
    repo_input = page.locator(".wb-automation-repository input")
    if repo_input.count():
        repo_input.first.fill("")
        page.wait_for_timeout(500)

    has_req = requirement.count() > 0
    check("repository requirement message visible", has_req,
          f"text={requirement.first.text_content() if has_req else 'not found'}")

    shooter.assert_clean("automations empty state")


def leg_resourceful_configured(shooter: Shooter, hub: Hub) -> None:
    """The Resourceful section with a configured policy (Idle mode)."""
    section(f"resourceful configured @{shooter.width}")

    if not _open_workbench_config(shooter, hub):
        return

    page = shooter.page
    if not _select_start_mode(page, "Idle"):
        return

    # Check the resourceful container.
    resourceful = page.locator(".wb-resourceful")
    check("resourceful container visible", resourceful.count() > 0)

    # Check the contract chips (showing policy values).
    contract = page.locator(".wb-resourceful-contract")
    check("resourceful contract chips visible", contract.count() > 0)

    if contract.count():
        chips = contract.first.locator(".desk-chip")
        check("contract has policy chips", chips.count() >= 3,
              f"count={chips.count()}")

    # Check gadget groups.
    gadget_group = page.locator(".gadget-group, .surface-gadget-group")
    check("gadget group (idle policy) visible", gadget_group.count() > 0)

    # Check routines.
    routines = page.locator(".wb-resourceful-routine")
    check("resourceful routines visible", routines.count() > 0,
          f"count={routines.count()}")

    # Check safety disclaimer.
    safety = page.locator(".wb-automation-safety")
    check("resourceful safety disclaimer visible", safety.count() > 0)

    # Check status.
    status = page.locator(".wb-resourceful-status")
    check("resourceful status visible", status.count() > 0,
          f"text={status.first.text_content() if status.count() else 'not found'}")

    # Check verb buttons.
    verbs = page.locator(".wb-automation-verbs button, .wb-automation-verbs .confirm-verb")
    check("resourceful verb buttons visible", verbs.count() > 0,
          f"count={verbs.count()}")

    # Scroll the routines into view so the shot captures the gadgets,
    # routine checkboxes, safety copy, and verb buttons -- the meat of
    # the Resourceful configuration.
    routines_target = page.locator(".wb-resourceful-routines")
    if routines_target.count():
        routines_target.first.scroll_into_view_if_needed()
        page.wait_for_timeout(300)
    else:
        starts_when = page.locator('text="STARTS WHEN"')
        if starts_when.count():
            starts_when.first.scroll_into_view_if_needed()
            page.wait_for_timeout(300)

    shooter.shot("resourceful", "wide" if shooter.width >= 1000 else "narrow",
                 "Workbench Resourceful section with configured policy")
    shooter.assert_clean("resourceful configured")


# ----------------------------------------------------------- main walk


def main() -> int:
    from playwright.sync_api import sync_playwright

    port = _free_port()
    home = tempfile.mkdtemp(prefix="pr461-walk-")
    hub = Hub(port, TOKEN, home).start()

    # Seed data via the API.
    auto_seeded = seed_automation(hub)
    if not auto_seeded:
        finding("automation seed failed; the populated-automation leg may be empty")

    res_seeded = seed_resourceful(hub)
    if not res_seeded:
        finding("resourceful seed failed; the resourceful-configured leg may be empty")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            for width, height in VIEWPORTS:
                section(f"===== viewport {width}x{height} =====")
                ctx = browser.new_context(
                    viewport={"width": width, "height": height},
                    device_scale_factor=2,
                )
                page = ctx.new_page()
                shooter = Shooter(page, width, WALK_OUT)

                leg_automations_populated(shooter, hub)
                leg_automations_empty(shooter, hub)
                leg_resourceful_configured(shooter, hub)

                ctx.close()
            browser.close()
    finally:
        hub.stop()

    # ---- summary -------
    section("RESULT")
    print(f"  PASS x{cw.PASSES}   FAIL x{len(cw.FAILS)}   "
          f"FINDINGS x{len(cw.FINDINGS)}   SHOTS x{len(cw.SHOTS)}", flush=True)
    for f in cw.FAILS:
        print(f"  FAIL  {f}", flush=True)
    for f in cw.FINDINGS:
        print(f"  FINDING  {f}", flush=True)
    for name, proves in cw.SHOTS:
        print(f"  shot  {name}  {proves}", flush=True)

    return 1 if cw.FAILS else 0


if __name__ == "__main__":
    raise SystemExit(main())
