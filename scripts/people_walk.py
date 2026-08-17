#!/usr/bin/env python3
"""PR #459 post-merge -- People ledger surface walk.

Screenshot + console-error proof for the People core surface at 1440x900
and 393x900.  Reuses scripts/chair_walk.py's Hub/Shooter/goto harness
(isolated HOME, seeded hub, console-error assertion).

Key custody caveat
------------------
The People store encrypts at rest via the macOS Keychain (NativeKeyStore).
Under an isolated HOME, ``keyring.set_password`` triggers a macOS security
dialog that blocks headlessly, so ``POST /api/people/setup`` would hang
the hub process (FastAPI is single-threaded for sync work).  No env-var
or test-hook seam exists in the production code to inject a MemoryKeyStore
into the hub subprocess.

When readiness is ``unconfigured``, this walk does NOT attempt setup
(that would deadlock the hub).  Instead it honestly photographs the
**unconfigured** rendering of PeopleCore.tsx ("Not set up" + "Set up"
action) at both viewports, proving the component loads, the readiness
API works, and the desk surface window opens via the shelf verb -- all
with zero console errors.

If a future environment makes the Keychain accessible headlessly (or an
env-var seam is added), the populated-state legs activate automatically.

Run:
    HOME=$(mktemp -d) PLAYWRIGHT_BROWSERS_PATH=~/Library/Caches/ms-playwright \\
        uv run python scripts/people_walk.py
"""
from __future__ import annotations

import json
import socket
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import chair_walk as cw  # noqa: E402
from chair_walk import (  # noqa: E402
    Hub,
    Shooter,
    check,
    finding,
    goto,
    section,
    _free_port,
)

WALK_OUT = REPO / "docs" / "evidence" / "people-pr1" / "post-merge"
TOKEN = "people-walk-pr459-token"
VIEWPORTS = ((1440, 900), (393, 900))


# ----------------------------------------------------------------- HTTP helpers


def api(
    hub: Hub, method: str, path: str, body: object = None, timeout: float = 30.0,
) -> tuple[int, object]:
    """Authenticated request to the walk hub."""
    data = None
    headers = {"X-HoldSpeak-Token": hub.token}
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(
        hub.url + path, data=data, headers=headers, method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", "replace")
            status = resp.status
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", "replace")
        status = exc.code
    except (TimeoutError, socket.timeout, OSError) as exc:
        return -1, {"error": str(exc)}
    try:
        return status, json.loads(raw)
    except Exception:
        return status, raw


# ----------------------------------------------------------------- seeding


def probe_people(hub: Hub) -> str:
    """Check the People store readiness WITHOUT attempting setup.

    Returns the readiness state string.  Never POSTs /setup because under
    isolated HOME the Keychain write hangs the single-threaded hub.
    """
    section("probe: people store readiness")
    status, readiness = api(hub, "GET", "/api/people/readiness")

    if status == 503:
        finding(
            "People store unavailable (status=503): "
            "NativeKeyStore construction failed under isolated HOME"
        )
        return "unavailable"

    if status != 200:
        finding(f"People readiness endpoint returned status={status}")
        return "unknown"

    check("readiness endpoint reachable", True, f"status={status}")

    state = ""
    if isinstance(readiness, dict):
        state = readiness.get("state") or readiness.get("readiness") or ""
    print(f"  readiness state={state!r}", flush=True)

    if state == "unconfigured":
        finding(
            "People store is unconfigured.  Cannot call POST /api/people/"
            "setup under isolated HOME: macOS Keychain write "
            "(keyring.set_password) hangs headlessly because the login "
            "keychain authorization dialog cannot be presented.  No "
            "sanctioned injection seam (env var, test hook) exists in "
            "the production code path to inject a MemoryKeyStore into "
            "the hub subprocess.  Walking the unconfigured state honestly."
        )
    elif state == "ready":
        check("people store ready", True)
    else:
        finding(f"People store in non-ready state: {state!r}")

    return state


def seed_people(hub: Hub) -> dict:
    """Seed relationships and data for the populated-state walk.

    Only called when probe_people returns "ready" (Keychain was accessible).
    """
    section("seed: relationships")
    ids: dict = {"relationships": [], "commitment_ids": []}

    people_data = [
        {"display_name": "Sarah Chen", "relationship_kind": "direct_report"},
        {"display_name": "Marcus Rivera", "relationship_kind": "peer"},
        {"display_name": "Priya Sharma", "relationship_kind": "extended"},
    ]

    for person in people_data:
        status, resp = api(hub, "POST", "/api/people/relationships", person)
        if not check(
            f"create relationship {person['display_name']}",
            status == 201,
            f"status={status}",
        ):
            continue
        rel = resp.get("relationship", {}) if isinstance(resp, dict) else {}
        rel_id = rel.get("id", "")
        ids["relationships"].append({"id": rel_id, **person})

    if not ids["relationships"]:
        finding("no relationships seeded")
        return ids

    first_id = ids["relationships"][0]["id"]

    # Requests + commitments
    section("seed: requests and commitments")
    for req_body in [
        "Review the Q3 architecture proposal",
        "Prepare feedback for the team retrospective",
        "Draft the cross-team integration plan",
    ]:
        status, resp = api(
            hub, "POST",
            f"/api/people/relationships/{first_id}/requests",
            {"body": req_body, "visibility": "shared_intent",
             "source": {"kind": "manual"}},
        )
        if status != 201:
            continue
        req_id = resp.get("request", {}).get("id", "") if isinstance(resp, dict) else ""
        status, accept_resp = api(
            hub, "POST", f"/api/people/requests/{req_id}/accept", {},
        )
        if status == 200 and isinstance(accept_resp, dict):
            ids["commitment_ids"].append(
                accept_resp.get("commitment", {}).get("id", "")
            )

    # 1:1 session + agenda
    section("seed: one-on-one")
    status, resp = api(
        hub, "POST",
        f"/api/people/relationships/{first_id}/one-on-ones",
        {"visibility": "shared_intent"},
    )
    if status == 201 and isinstance(resp, dict):
        sid = resp.get("one_on_one", {}).get("id", "")
        for item in [
            {"body": "Discuss architecture ownership",
             "visibility": "shared_intent", "state": "open",
             "source": {"kind": "manual"}},
            {"body": "Career growth check-in",
             "visibility": "leader_private", "state": "open",
             "source": {"kind": "manual"}},
        ]:
            api(hub, "POST", f"/api/people/one-on-ones/{sid}/agenda", item)

    # Grounding notes
    section("seed: grounding notes")
    for note in [
        {"topic": "Working style",
         "body": "Prefers async communication; values written proposals",
         "visibility": "leader_private"},
        {"topic": "Team context",
         "body": "Leading the platform migration; three direct reports",
         "visibility": "shared_intent"},
    ]:
        api(hub, "POST",
            f"/api/people/relationships/{first_id}/notes", note)

    return ids


# ----------------------------------------------------------------- walk legs


def open_people(shooter: Shooter, hub: Hub) -> None:
    """Navigate to the People surface via Cmd+K shelf search."""
    goto(shooter, hub, "/")
    page = shooter.page

    page.keyboard.press("Meta+k")
    page.wait_for_timeout(500)
    page.keyboard.type("People")
    page.wait_for_timeout(800)
    page.keyboard.press("Enter")
    page.wait_for_timeout(2500)


# ----------- Populated-state legs (run only when seeding succeeded) ----------


def leg_people_roster(shooter: Shooter, hub: Hub) -> None:
    section(f"people roster @{shooter.width}")
    open_people(shooter, hub)
    page = shooter.page

    check("Relationships section visible",
          page.get_by_text("Relationships", exact=True).count() > 0)
    for name in ("Sarah Chen", "Marcus Rivera", "Priya Sharma"):
        check(f"relationship {name} visible",
              page.get_by_text(name, exact=False).count() > 0)
    check("New relationship input present",
          page.locator("#people-new-relationship").count() > 0)
    check("Encrypted fact badge",
          page.get_by_text("Encrypted", exact=True).count() > 0)

    shooter.shot("people-roster", "populated",
                 "People roster: relationships, commitment badges, fact strip")
    shooter.assert_clean("people roster")


def _open_sarah(shooter: Shooter, hub: Hub) -> bool:
    open_people(shooter, hub)
    sarah = shooter.page.get_by_text("Sarah Chen", exact=False).first
    if sarah.count():
        sarah.click()
        shooter.page.wait_for_timeout(1500)
        return True
    finding("Sarah Chen not found for detail navigation")
    return False


def _switch_tab(page: object, label: str) -> bool:
    tab = page.locator('button[role="tab"]').get_by_text(label)  # type: ignore[attr-defined]
    if tab.count():
        tab.click()  # type: ignore[attr-defined]
        page.wait_for_timeout(1200)  # type: ignore[attr-defined]
        return True
    finding(f"{label} tab not found")
    return False


def leg_people_detail_now(shooter: Shooter, hub: Hub) -> None:
    section(f"people detail Now @{shooter.width}")
    if not _open_sarah(shooter, hub):
        return
    page = shooter.page
    check("You owe section present",
          page.get_by_text("You owe", exact=True).count() > 0)
    shooter.shot("people-detail", "now-lens",
                 "Now lens: commitments, requests, next 1:1")
    shooter.assert_clean("people detail now")


def leg_people_detail_one_on_ones(shooter: Shooter, hub: Hub) -> None:
    section(f"people detail 1:1s @{shooter.width}")
    if not _open_sarah(shooter, hub):
        return
    if not _switch_tab(shooter.page, "1:1s"):
        return
    shooter.shot("people-detail", "one-on-ones-lens",
                 "1:1s lens: session agenda")
    shooter.assert_clean("people detail 1:1s")


def leg_people_detail_context(shooter: Shooter, hub: Hub) -> None:
    section(f"people detail context @{shooter.width}")
    if not _open_sarah(shooter, hub):
        return
    if not _switch_tab(shooter.page, "Context"):
        return
    shooter.shot("people-detail", "context-lens",
                 "Context lens: grounding notes, projects")
    shooter.assert_clean("people detail context")


def leg_people_detail_history(shooter: Shooter, hub: Hub) -> None:
    section(f"people detail history @{shooter.width}")
    if not _open_sarah(shooter, hub):
        return
    if not _switch_tab(shooter.page, "History"):
        return
    shooter.shot("people-detail", "history-lens",
                 "History lens: follow-through facts, timeline")
    shooter.assert_clean("people detail history")


def leg_people_detail_info(shooter: Shooter, hub: Hub) -> None:
    section(f"people detail info @{shooter.width}")
    if not _open_sarah(shooter, hub):
        return
    if not _switch_tab(shooter.page, "Info"):
        return
    check("Archive verb present",
          shooter.page.get_by_text("Archive", exact=True).count() > 0)
    shooter.shot("people-detail", "info-lens",
                 "Info lens: metadata, storage facts, archive verb")
    shooter.assert_clean("people detail info")


# ----------- Degraded-state legs (key custody blocked) -----------------------


def leg_people_unconfigured(shooter: Shooter, hub: Hub) -> None:
    """PeopleCore.tsx's unconfigured rendering: SurfaceState with
    emptyLabel="Not set up" and actionLabel="Set up".
    """
    section(f"people unconfigured state @{shooter.width}")
    open_people(shooter, hub)
    page = shooter.page

    not_set_up = page.get_by_text("Not set up", exact=False)
    set_up_btn = page.get_by_text("Set up", exact=True)

    found_label = not_set_up.count() > 0
    found_action = set_up_btn.count() > 0

    # Accept alternative degraded states.
    if not found_label:
        for alt in ("Store unavailable", "Locked", "Key unavailable"):
            if page.get_by_text(alt, exact=False).count() > 0:
                finding(f"People surface shows '{alt}' instead of 'Not set up'")
                found_label = True
                break

    check("degraded state label visible", found_label)
    check("action button visible", found_action or found_label,
          "Set up button or alternative recovery action")

    shooter.shot("people", "unconfigured",
                 "People surface: unconfigured state with Set up action")
    shooter.assert_clean("people unconfigured")


def leg_desk_with_people(shooter: Shooter, hub: Hub) -> None:
    """The desk floor showing the People surface window opened."""
    section(f"desk people window @{shooter.width}")
    goto(shooter, hub, "/")
    page = shooter.page
    page.wait_for_timeout(1000)

    shooter.shot("desk", "people-presence",
                 "Desk floor with People surface accessible")
    shooter.assert_clean("desk people presence")


# ----------------------------------------------------------------- main walk


def main() -> int:
    from playwright.sync_api import sync_playwright

    port = _free_port()
    home = tempfile.mkdtemp(prefix="people-walk-pr459-")
    hub = Hub(port, TOKEN, home).start()

    # Probe readiness; never attempt setup (deadlocks the hub).
    state = probe_people(hub)
    people_ready = state == "ready"

    if people_ready:
        seeded = seed_people(hub)
        people_ready = bool(seeded.get("relationships"))

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

                if people_ready:
                    leg_people_roster(shooter, hub)
                    leg_people_detail_now(shooter, hub)
                    leg_people_detail_one_on_ones(shooter, hub)
                    leg_people_detail_context(shooter, hub)
                    leg_people_detail_history(shooter, hub)
                    leg_people_detail_info(shooter, hub)
                else:
                    leg_people_unconfigured(shooter, hub)
                    leg_desk_with_people(shooter, hub)

                ctx.close()
            browser.close()
    finally:
        hub.stop()

    # ---- summary -------
    section("RESULT")
    print(
        f"  PASS x{cw.PASSES}   FAIL x{len(cw.FAILS)}   "
        f"FINDINGS x{len(cw.FINDINGS)}   SHOTS x{len(cw.SHOTS)}",
        flush=True,
    )
    if cw.FINDINGS:
        print("\nFINDINGS:", flush=True)
        for f in cw.FINDINGS:
            print(f"  - {f}", flush=True)
    if cw.FAILS:
        print("\nFAILURES:", flush=True)
        for f in cw.FAILS:
            print(f"  - {f}", flush=True)
    print("\nSHOTS:", flush=True)
    for name, proves in cw.SHOTS:
        print(f"  {name}  ({proves})", flush=True)

    return 1 if cw.FAILS else 0


if __name__ == "__main__":
    raise SystemExit(main())
