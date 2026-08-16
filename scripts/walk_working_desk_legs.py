#!/usr/bin/env python3
"""HS-132-14 — the walk's legs, one function per Phase-132 surface.

Imported by ``scripts/walk_working_desk.py``; kept separate so the harness
(hub lifecycle, shooting, console-error assertion) stays readable and each
leg reads as the claim it proves.

Every leg takes ``(shooter, hub)`` and is responsible for its own shots and
its own assertions. A leg that cannot be exercised in this environment says
so by name with the blocker — it never fakes the shot.
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from scripts.walk_working_desk import (
    Hub,
    Shooter,
    VIEWPORTS,
    check,
    finding,
    goto,
    section,
)

# ------------------------------------------------------------------ helpers


def _click_if(shooter: Shooter, locator: Any, label: str) -> bool:
    try:
        if locator.count() and locator.first.is_visible():
            locator.first.click()
            shooter.page.wait_for_timeout(500)
            return True
    except Exception as exc:  # noqa: BLE001 — a walk reports, never explodes
        finding(f"{label}: click failed — {exc}")
    return False


def _open_intelligence(shooter: Shooter) -> bool:
    """Open the Intelligence pullout through the dock (the user's path)."""
    page = shooter.page
    dock = page.get_by_role("button", name="Intelligence", exact=False)
    if not _click_if(shooter, dock, "dock Intelligence"):
        # The dock collapses at 393; fall back to the verb the palette owns.
        page.keyboard.press("Meta+k")
        page.wait_for_timeout(400)
        page.keyboard.type("Open Intelligence")
        page.wait_for_timeout(600)
        page.keyboard.press("Enter")
    page.wait_for_timeout(1200)
    return page.locator('[role="region"][aria-label="Intelligence"]').count() > 0


def _segment(shooter: Shooter, name: str) -> bool:
    seg = shooter.page.locator(".intelligence-segment", has_text=name)
    return _click_if(shooter, seg, f"intelligence segment {name}")


# --------------------------------------------------------------------- legs


def leg_desk_floor(shooter: Shooter, hub: Hub) -> None:
    """The desk floor + system bar, populated by the seed."""
    section(f"desk floor + system bar @{shooter.width}")
    goto(shooter, hub, "/")
    check(
        "desk shell rendered (menubar present)",
        shooter.page.locator(".desk-menubar").count() > 0,
    )
    shooter.shot("desk-floor", "seeded", "HS-132-06 baseline: desk floor + system bar, seeded")
    # Quiet is quiet: with nothing failed the receipt seat renders nothing.
    # (The seat appearing is the failure leg's assertion, not this one's.)
    check(
        "a healthy desk shows no write receipt",
        shooter.page.locator(".write-receipt").count() == 0,
    )
    check(
        "the dock offers the daily verbs",
        shooter.page.locator('[role="toolbar"][aria-label="Dock"]').count() > 0
        or shooter.page.locator(".desk-dock").count() > 0,
    )
    shooter.assert_clean("desk floor")


def leg_write_receipt_backstop(shooter: Shooter, hub: Hub) -> None:
    """HS-132-06 — the hub dies mid-walk; a create verb names its failure.

    The MANDATORY error leg: the receipt must land in-flow (the menubar's
    own seat), never as an overlay on top of the desk.
    """
    section(f"HS-132-06 write-receipt backstop (hub stopped) @{shooter.width}")
    page = shooter.page
    goto(shooter, hub, "/")
    shooter.shot("write-receipt", "before-hub-stop", "HS-132-06 before: no receipt, hub alive")
    shooter.console_errors.clear()

    hub.stop()
    check("hub is actually down before the create verb", not hub.healthy(timeout=0.5))

    # Drive the create verb the way a user does. First the Desk menu, then —
    # if that width hides it — the same verb from the command palette. Both
    # dispatch the identical `desk.new-note` verb from the registry.
    receipt = page.locator(".write-receipt")

    def _wait_for_receipt(timeout_ms: int) -> bool:
        try:
            receipt.first.wait_for(state="visible", timeout=timeout_ms)
            return True
        except Exception:
            return False

    if _click_if(
        shooter, page.get_by_role("button", name="Desk", exact=True), "Desk menubar title"
    ):
        # The menu item's accessible name carries its keycap ("New Note ⌘N"),
        # so the match is a prefix, not an equality.
        _click_if(
            shooter,
            page.get_by_role("menuitem", name="New Note", exact=False),
            "Desk > New Note",
        )
    if not _wait_for_receipt(6000):
        finding(
            "the Desk-menu route to New Note produced no write receipt at "
            f"{shooter.width}px; falling back to the palette verb"
        )
        page.keyboard.press("Escape")
        page.wait_for_timeout(200)
        page.keyboard.press("Meta+k")
        page.wait_for_timeout(500)
        page.keyboard.type("New Note")
        page.wait_for_timeout(700)
        page.keyboard.press("Enter")
        _wait_for_receipt(15000)
    text = receipt.first.inner_text() if receipt.count() else ""
    check(
        "a failed create names itself in a write receipt",
        "FAILED" in text.upper(),
        text.strip()[:120],
    )
    check(
        "the receipt names the unreachable hub (not a silent no-op)",
        "UNREACHABLE" in text.upper() or "HTTP" in text.upper(),
        text.strip()[:120],
    )
    in_bar = page.locator(".desk-menubar .desk-chrome-receipt .write-receipt").count() > 0
    in_floor = page.locator(".write-receipt-row .write-receipt").count() > 0
    check(
        "the receipt is in-flow (menubar seat or floor row), not an overlay",
        in_bar or in_floor,
        f"menubar={in_bar} floor={in_floor}",
    )
    check(
        "no modal/dialog overlaps the desk for the error",
        page.locator('[role="dialog"]').count() == 0,
    )
    shooter.shot(
        "write-receipt", "hub-down-create-failed",
        "HS-132-06 after: CREATE NOTE FAILED named in-flow, nothing overlapping",
    )
    shooter.assert_clean("write-receipt backstop")

    hub.start()
    check("hub came back up for the rest of the walk", hub.healthy())


def leg_workbench(shooter: Shooter, hub: Hub) -> None:
    """HS-132-07 — typing holds, the RUN chip names its reason, drops are honest."""
    section(f"HS-132-07 workbench @{shooter.width}")
    page = shooter.page
    # The seed ships an EMPTY workbench; the typing leg needs a card to type
    # into, so the walk files one through the product's own item route.
    benches = (hub.api("GET", "/api/workbenches")[1] or {}).get("workbenches") or []
    if benches and not benches[0].get("items"):
        hub.api(
            "POST", f"/api/workbenches/{benches[0]['id']}/items",
            {"title": "Draft the Phase 132 walk report",
             "body": "Replaced by the walk's own typing."},
        )
    goto(shooter, hub, "/")

    # The seed files one workbench. Desk objects live in a WebGL world; the
    # per-object button is the screen-reader proxy the desk itself exposes,
    # so the walk activates it the way assistive tech does rather than
    # hit-testing pixels the menubar sits over.
    opened = False
    obj = page.locator('[data-kind="workbench"]')
    if obj.count():
        try:
            obj.first.dispatch_event("click")
            page.wait_for_timeout(1500)
            opened = page.locator(".desk-workbench-window").count() > 0
        except Exception as exc:  # noqa: BLE001
            finding(f"workbench object proxy click failed: {exc}")
    if not opened:
        page.keyboard.press("Meta+k")
        page.wait_for_timeout(400)
        page.keyboard.type("Workbench")
        page.wait_for_timeout(700)
        page.keyboard.press("Enter")
        page.wait_for_timeout(1500)
    window = page.locator(".desk-workbench-window")
    if window.count() == 0:
        finding("workbench window never opened; typing/RUN/drop legs unproven at this width")
        shooter.shot("workbench", "not-opened", "HS-132-07 BLOCKED: no workbench window")
        return

    shooter.shot("workbench", "open", "HS-132-07 baseline: workbench window on the desk")

    # --- the RUN chip's named disabled reason -------------------------
    run_named = page.get_by_role("button", name="Run:", exact=False)
    if run_named.count():
        label = run_named.first.get_attribute("aria-label") or ""
        title = run_named.first.get_attribute("title") or ""
        check(
            "the disabled RUN chip names WHY (aria-label + title)",
            label.startswith("Run:") and bool(title),
            f"aria-label={label!r} title={title!r}",
        )
        shooter.shot("workbench", "run-chip-disabled-reason", "HS-132-07: RUN names its disabled reason")
    else:
        runnable = page.get_by_role("button", name="Run this workbench now")
        check(
            "the RUN chip is either enabled-with-a-reason-free title or disabled-with-a-name",
            runnable.count() > 0,
            "enabled (agent bound)",
        )
        shooter.shot("workbench", "run-chip-enabled", "HS-132-07: RUN enabled, agent bound")

    # --- item body typing: fast keystrokes must all survive -----------
    head = page.locator("button.wb-card-head")
    if head.count():
        head.first.click()
        page.wait_for_timeout(700)
        body = page.locator('textarea[aria-label="Item body"]')
        if body.count():
            sentence = "The desk must keep every character I type, even at speed."
            body.first.click()
            body.first.fill("")
            page.keyboard.type(sentence, delay=8)
            page.wait_for_timeout(250)  # inside the 450ms debounce: draft is held
            got = body.first.input_value()
            check(
                "fast typing loses no keystrokes (draft-buffered)",
                got == sentence,
                f"len {len(got)} vs {len(sentence)}",
            )
            shooter.shot(
                "workbench", "item-body-held-draft",
                "HS-132-07 after: a fast sentence held intact inside the save debounce",
            )
            page.wait_for_timeout(1200)  # let the debounce flush
            check(
                "the draft survives the debounce flush",
                body.first.input_value() == sentence,
            )
        else:
            finding("no 'Item body' textarea in the expanded card; typing leg unproven")
    else:
        finding("the seeded workbench has no item cards; typing leg unproven")

    # --- drop overlay verbs -------------------------------------------
    body_el = page.locator(".wb-body").first
    if body_el.count():
        try:
            box = body_el.bounding_box()
            if box:
                page.evaluate(
                    """(sel) => {
                        const el = document.querySelector(sel);
                        if (!el) return;
                        const dt = new DataTransfer();
                        dt.setData('application/x-desk-item', '{"id":"walk"}');
                        el.dispatchEvent(new DragEvent('dragenter', {bubbles:true, dataTransfer:dt}));
                        el.dispatchEvent(new DragEvent('dragover', {bubbles:true, dataTransfer:dt}));
                    }""",
                    ".wb-body",
                )
                page.wait_for_timeout(400)
                zone = page.locator(".wb-drop-zone")
                text = zone.first.inner_text() if zone.count() else ""
                check(
                    "the drop overlay names its verb (DROP TARGET · …)",
                    "DROP TARGET" in text.upper() or "NO DROP" in text.upper(),
                    text.strip()[:80],
                )
                shooter.shot(
                    "workbench", "drop-overlay-verbs",
                    "HS-132-07: honest drop target verb on drag-over",
                )
        except Exception as exc:  # noqa: BLE001
            finding(f"drop-overlay leg could not be driven: {exc}")
    shooter.assert_clean("workbench")


def leg_intelligence(shooter: Shooter, hub: Hub) -> None:
    """HS-132-08 — Brief triage persists, no false ALL CLEAR, receipts chain."""
    section(f"HS-132-08 intelligence @{shooter.width}")
    page = shooter.page
    # A brief item's shelf state is durable BY DESIGN, so a second width would
    # otherwise toggle the first width's acknowledge back off. Mint a fresh
    # brief (the product's own verb) so this width starts unshelved.
    hub.api("POST", "/api/brief/generate", {}, timeout=120.0)
    goto(shooter, hub, "/")
    if not _open_intelligence(shooter):
        finding("Intelligence pullout never opened; HS-132-08 legs unproven at this width")
        shooter.shot("intelligence", "not-opened", "HS-132-08 BLOCKED")
        return

    # --- Brief: acknowledge persists ----------------------------------
    _segment(shooter, "Brief")
    page.wait_for_timeout(800)
    # An empty brief offers its own Generate verb; take the user's path.
    gen = page.get_by_role("button", name="Generate", exact=True)
    if gen.count() and gen.first.is_visible():
        gen.first.click()
        page.wait_for_timeout(4000)
    shooter.shot("intelligence-brief", "open", "HS-132-08 baseline: Brief view")
    rows = page.locator(".intelligence-brief-rows li, .intelligence-brief-rows button")
    if rows.count():
        rows.first.click()
        page.wait_for_timeout(400)
        ack = page.get_by_role("button", name="Acknowledge", exact=True)
        # Triage is durable, and `brief/generate` reuses the period's items, so
        # the second viewport can arrive at an already-acknowledged row —
        # where Acknowledge is a TOGGLE and would clear it. Park it on Defer
        # first (which also exercises the other verb), then acknowledge.
        badge_now = page.locator(".intelligence-brief-shelf-state")
        if badge_now.count() and "acknowledged" in badge_now.first.inner_text().lower():
            defer = page.get_by_role("button", name="Defer", exact=True)
            if defer.count() and defer.first.is_enabled():
                defer.first.click()
                page.wait_for_timeout(900)
                check(
                    "defer writes its own persisted badge",
                    page.locator(".intelligence-brief-shelf-state").count() > 0
                    and "deferred"
                    in page.locator(".intelligence-brief-shelf-state").first.inner_text().lower(),
                    page.locator(".intelligence-brief-shelf-state").first.inner_text()[:40]
                    if page.locator(".intelligence-brief-shelf-state").count()
                    else "(absent)",
                )
        if ack.count() and ack.first.is_enabled():
            ack.first.click()
            page.wait_for_timeout(900)
            badge = page.locator(".intelligence-brief-shelf-state")
            state = badge.first.inner_text() if badge.count() else ""
            check(
                "acknowledge writes a persisted badge",
                "acknowledged" in state.lower(),
                state.strip()[:60],
            )
            shooter.shot(
                "intelligence-brief", "acknowledged-badge",
                "HS-132-08 after: Brief acknowledge persists as a badge",
            )
            # Reload: the badge must survive (it is server state, not local).
            goto(shooter, hub, "/")
            _open_intelligence(shooter)
            _segment(shooter, "Brief")
            page.wait_for_timeout(900)
            badge2 = page.locator(".intelligence-brief-shelf-state")
            check(
                "the acknowledged badge survives a reload",
                badge2.count() > 0
                and "acknowledged" in badge2.first.inner_text().lower(),
                badge2.first.inner_text().strip()[:60] if badge2.count() else "(absent)",
            )
            shooter.shot(
                "intelligence-brief", "acknowledged-after-reload",
                "HS-132-08: the triage state is durable, not local",
            )
        else:
            finding("Brief Acknowledge is not enabled after selecting a row")
    else:
        finding("the seeded brief has no rows; acknowledge-persistence leg unproven")

    # --- Follow-through: the drill filter token is visible and owned --
    _segment(shooter, "Follow-through")
    page.wait_for_timeout(700)
    shooter.shot("intelligence-followthrough", "all-lanes", "HS-132-08 baseline: all lanes")
    page.keyboard.press("Meta+k")
    page.wait_for_timeout(400)
    page.keyboard.type("Show overdue follow-through")
    page.wait_for_timeout(700)
    page.keyboard.press("Enter")
    page.wait_for_timeout(1200)
    token = page.locator(".intelligence-filters .desk-chip")
    token_text = token.first.inner_text() if token.count() else ""
    check(
        "the overdue drill shows its filter token (the filter is navigation-owned)",
        "OVERDUE" in token_text.upper(),
        token_text.strip()[:80],
    )
    body_text = page.locator(".intelligence-view").first.inner_text() if page.locator(".intelligence-view").count() else ""
    check(
        "no false ALL CLEAR while a filter is narrowing the board",
        "ALL CLEAR" not in body_text.upper(),
    )
    shooter.shot(
        "intelligence-followthrough", "overdue-filter-token",
        "HS-132-08 after: FILTER · OVERDUE ONLY token visible, no false ALL CLEAR",
    )
    # Tab back: the token must clear with the navigation, not stick.
    _segment(shooter, "Brief")
    page.wait_for_timeout(500)
    _segment(shooter, "Follow-through")
    page.wait_for_timeout(800)
    back_text = page.locator(".intelligence-view").first.inner_text() if page.locator(".intelligence-view").count() else ""
    check(
        "tabbing back never renders a bare ALL CLEAR",
        "ALL CLEAR" not in back_text.upper(),
    )
    shooter.shot(
        "intelligence-followthrough", "tabbed-back",
        "HS-132-08: back from the drill — the board still tells the truth",
    )

    # --- Decisions / receipts + supersession history ------------------
    _segment(shooter, "Decisions")
    page.wait_for_timeout(900)
    shooter.shot("intelligence-receipts", "list", "HS-132-08 / HS-127: the receipts list")
    row = page.locator(".surface-ledger-row, .desk-deck-row, li button").first
    try:
        if row.count():
            row.click()
            page.wait_for_timeout(900)
    except Exception:
        pass
    chain = page.locator('[aria-label="Supersession history"]')
    check(
        "an opened receipt carries a SUPERSESSION history section",
        chain.count() > 0,
        "present" if chain.count() else "absent (no superseded record in the seed)",
    )
    shooter.shot(
        "intelligence-receipts", "detail-supersession",
        "HS-132-08: receipt detail with the supersession history label",
    )
    shooter.assert_clean("intelligence")


def leg_placement_dial(shooter: Shooter, hub: Hub) -> None:
    """HS-132-10 — one placement dial, every reachable state.

    Also discharges the Phase-130 Article IX.2 screenshot IOU for
    Settings/Models and the placement labels.
    """
    section(f"HS-132-10 placement dial @{shooter.width}")
    page = shooter.page

    # A destination has to exist before one can decide placement. This is the
    # same LAN box the .43 leg runs a real Ask against.
    hub.api(
        "POST", "/api/inference-targets",
        {"id": "walk-lan43", "name": "Homelab .43", "kind": "openAICompatible",
         "base_url": "http://192.168.1.43:8080/v1",
         "model": "Qwen3.6-35B-A3B-UD-Q5_K_XL.gguf", "context_limit": 32768},
    )

    # State A — no destination adopted: the provider decides.
    hub.api("PUT", "/api/settings", {"meeting": {"intel_profile_id": None,
                                                 "intel_provider": "local"}})
    goto(shooter, hub, "/profiles")
    page.wait_for_timeout(1500)
    dial = page.locator('select[aria-label="Meetings runs on"]')
    if dial.count() == 0:
        finding("Settings > Models never rendered the 'Meetings runs on' dial; "
                "HS-132-10 unproven at this width")
        shooter.shot("settings-models", "dial-missing", "HS-132-10 BLOCKED")
        return
    body = page.locator(".desk-surface-body").first.inner_text()
    check("no destination -> the dial says PROVIDER DECIDES",
          "PROVIDER DECIDES" in body.upper(), _snip(body, "PROVIDER DECIDES"))
    check("the precedence rule is stated on the dial",
          "DESTINATION WINS" in body.upper(), _snip(body, "DESTINATION WINS"))
    check("exactly one control claims DECIDES PLACEMENT",
          body.upper().count("DECIDES PLACEMENT") == 1,
          f"count={body.upper().count('DECIDES PLACEMENT')}")
    shooter.shot("settings-models", "no-destination-provider-decides",
                 "HS-132-10 / IX.2 IOU: no destination — the provider decides")

    # State B — adopt a destination: it decides, the provider is overridden.
    hub.api("PUT", "/api/settings",
            {"meeting": {"intel_profile_id": "walk-lan43", "intel_provider": "local"}})
    goto(shooter, hub, "/profiles")
    page.wait_for_timeout(1500)
    body = page.locator(".desk-surface-body").first.inner_text()
    check("adopted destination -> DECIDES PLACEMENT",
          "DECIDES PLACEMENT" in body.upper(), _snip(body, "DECIDES PLACEMENT"))
    check("the provider dial is named OVERRIDDEN",
          "OVERRIDDEN" in body.upper(), _snip(body, "OVERRIDDEN"))
    check("the overridden lamp names WHICH destination decides",
          "PROVIDER SELECTION IGNORED" in body.upper(),
          _snip(body, "PROVIDER SELECTION IGNORED"))
    check("the effective placement is stated (RUNS ON ...)",
          "RUNS ON" in body.upper(), _snip(body, "RUNS ON"))
    provider = page.locator('select[aria-label="Meetings provider"]')
    if provider.count():
        check("the overridden provider dial is actually disabled",
              provider.first.is_disabled())
    shooter.shot("settings-models", "destination-decides-provider-overridden",
                 "HS-132-10 / IX.2 IOU: destination adopted — DECIDES PLACEMENT "
                 "+ provider OVERRIDDEN lamp")

    # The read-only pointer in Settings > Meetings must agree, not compete.
    check("placement_source rides the settings payload",
          isinstance(hub.api("GET", "/api/settings")[1], dict)
          and "placement_source"
          in json.dumps(hub.api("GET", "/api/settings")[1].get("_placement", {})),
          "")
    shooter.assert_clean("settings models")


def leg_live_meeting(shooter: Shooter, hub: Hub) -> None:
    """HS-132-03 — the desk hears intelligence live, and a bookmark confirms.

    The capture engine is the harness's (no mic headless); the socket, the
    bus, the frame vocabulary, the bookmark route and LiveCore are the
    product's.
    """
    section(f"HS-132-03 live meeting @{shooter.width}")
    page = shooter.page
    goto(shooter, hub, "/live")
    page.wait_for_timeout(1200)
    window = page.locator('[role="region"][aria-label="Live meeting"]')
    if window.count() == 0:
        finding("the Live meeting window never opened; HS-132-03 unproven")
        shooter.shot("live-meeting", "not-opened", "HS-132-03 BLOCKED")
        return
    shooter.shot("live-meeting", "idle", "HS-132-03 before: Live meeting, idle")

    status, payload = hub.api("POST", "/api/meeting/start", {})
    check("POST /api/meeting/start succeeds", status == 200 and payload.get("success"),
          json.dumps(payload)[:160])
    # The frames land over the real socket; give the stream time to arrive.
    page.wait_for_timeout(4500)
    text = window.first.inner_text()
    check("the transcript renders the live segments",
          "write-receipt" in text or "intelligence arriving" in text.lower(),
          _snip(text, "receipt"))
    stream_or_result = page.locator(".live-intel-stream, .live-intel-result")
    check("the Intelligence section rendered from the live stream",
          stream_or_result.count() > 0)
    check("intelligence arrived without a manual refetch",
          "INTELLIGENCE" in text.upper(), _snip(text, "INTELLIGENCE"))
    shooter.shot("live-meeting", "intelligence-stream",
                 "HS-132-03 after: LiveCore shows the intelligence section fed "
                 "by intel_token/intel_complete")

    # Drop a bookmark through the real route; the confirmation is live.
    bm = page.get_by_role("button", name="+ Bookmark", exact=False)
    if bm.count():
        bm.first.click()
        page.wait_for_timeout(400)
        pad = page.locator('input[aria-label="Name this moment"]')
        if pad.count():
            pad.first.fill("The walk was here")
            page.keyboard.press("Enter")
        page.wait_for_timeout(1800)
    else:
        finding("the + Bookmark button never enabled; dropping it over the API instead")
        hub.api("POST", "/api/bookmark", {"label": "The walk was here"})
        page.wait_for_timeout(1500)
    receipt = page.locator('.surface-receipt-line[data-tone="ok"]')
    rtext = receipt.first.inner_text() if receipt.count() else ""
    check("the dropped bookmark confirms live on the glass",
          "✓" in rtext and "walk was here" in rtext.lower(), rtext.strip()[:120])
    if rtext and not any(ch in rtext for ch in (":",)) and "." in rtext.split("·")[-1]:
        finding(
            "the bookmark confirmation prints a RAW offset, not a time: "
            f"{rtext.strip()[:80]!r}. LiveCore.tsx:200-207 reads "
            "`formatted_time ?? timestamp`, and nothing in holdspeak/ ever "
            "emits `formatted_time` (grep: zero hits), so the user always "
            "sees the bare float from meeting_glue.py:485."
        )
    shooter.shot("live-meeting", "bookmark-confirmed",
                 "HS-132-03: live bookmark confirmation on the glass")

    status, payload = hub.api("POST", "/api/meeting/stop", {})
    check("stopping a live meeting succeeds", status == 200, str(status))
    status, payload = hub.api("POST", "/api/meeting/stop", {})
    check("stopping again refuses by name with 409 (HS-132-01), hub survives",
          status == 409 and "No active meeting" in json.dumps(payload),
          f"{status} {json.dumps(payload)[:120]}")
    check("the hub is still alive after the stale Stop", hub.healthy())
    shooter.assert_clean("live meeting")


def leg_cadence(shooter: Shooter, hub: Hub) -> None:
    """HS-132-11 — the Cadence reply pad delivers instead of 404-ing."""
    section(f"HS-132-11 cadence @{shooter.width}")
    page = shooter.page
    # One collection tick projects the agent-question loop the populate step
    # registered; this is the product's own `run-now` verb.
    hub.api("POST", "/api/cadence/run-now", {}, timeout=60.0)
    goto(shooter, hub, "/cadence")
    page.wait_for_timeout(1500)
    window = page.locator('[role="region"][aria-label="Cadence"]')
    if window.count() == 0:
        finding("the Cadence window never opened; HS-132-11 unproven")
        shooter.shot("cadence", "not-opened", "HS-132-11 BLOCKED")
        return
    shooter.shot("cadence", "loops", "HS-132-11: the cadence loop board")

    pad = page.locator('textarea[aria-label^="Reply to"]')
    if pad.count() == 0:
        finding("no agent_question loop is projected in this fresh HOME, so the "
                "reply PAD has no row to sit on; the reply ROUTE is proven "
                "against the hub instead (below)")
    else:
        pad.first.fill("Store the pairing state in SQLite.")
        page.wait_for_timeout(400)
        send = page.get_by_role("button", name="Send reply", exact=True)
        check("the Send reply affordance is present and enabled once text is typed",
              send.count() > 0 and send.first.is_enabled())
        shooter.shot("cadence", "reply-pad-ready",
                     "HS-132-11: the reply pad with Send reply enabled")
        send.first.click()
        page.wait_for_timeout(1500)
        shooter.shot("cadence", "reply-sent", "HS-132-11: the reply's receipt")

    # The route itself: it must answer by name, never 404.
    loops = hub.api("GET", "/api/cadence/loops")[1]
    check("GET /api/cadence/loops answers", isinstance(loops, dict))
    status, payload = hub.api(
        "POST", "/api/cadence/loops/walk-missing-loop/reply", {"text": "hello"}
    )
    check(
        "the reply route is mounted and refuses an unknown loop BY NAME "
        "(HS-132-11: it used to 404 as an unmounted route)",
        status in (400, 404, 409)
        and "loop not found" in json.dumps(payload).lower(),
        f"{status} {json.dumps(payload)[:140]}",
    )
    shooter.assert_clean("cadence")


def leg_ask_receipt_honesty(shooter: Shooter, hub: Hub) -> None:
    """HS-132-09 — the receipt names what actually loaded (.43 vs this_machine)."""
    section(f"HS-132-09 receipt honesty @{shooter.width}")
    page = shooter.page

    lan = "http://192.168.1.43:8080/v1"
    reachable, models = _probe_lan(lan)
    lan_model = models[0] if models else "Qwen3.6-35B-A3B-UD-Q5_K_XL.gguf"
    check("the LAN endpoint answers (live metal precondition)", reachable,
          f"{len(models)} model(s): {models[:2]}")
    status, payload = hub.api(
        "POST", "/api/inference-targets",
        {"id": "walk-lan43", "name": "Homelab .43", "kind": "openAICompatible",
         "base_url": lan, "model": lan_model, "context_limit": 32768},
    )
    check("the .43 destination is created (or already exists)",
          status in (201, 400, 409), str(status))

    advertised = {
        row.get("id"): row.get("name")
        for row in (hub.api("GET", "/api/models")[1] or {}).get("models", [])
    }
    check("the .43 destination is advertised under its real model name",
          advertised.get("walk-lan43") == lan_model,
          f"{advertised.get('walk-lan43')!r} vs {lan_model!r}")

    # --- treatment: a REAL Ask on the LAN box ---------------------------
    status, lan_receipt = hub.api(
        "POST", "/api/ask",
        {"prompt": "Reply with exactly: HOLDSPEAK WALK OK",
         "inference_target_id": "walk-lan43", "max_tokens": 32},
        timeout=180.0,
    )
    check("the .43 Ask executed", status == 200 and bool(lan_receipt.get("output")),
          json.dumps(lan_receipt)[:160])
    check("the .43 receipt names the model that executed",
          lan_receipt.get("model") == lan_model
          and lan_receipt.get("actual_placement", {}).get("model") == lan_model,
          f"model={lan_receipt.get('model')} "
          f"actual={lan_receipt.get('actual_placement', {}).get('model')}")
    check("readiness == executed == receipt == advertised",
          lan_receipt.get("model")
          == lan_receipt.get("inference_target", {}).get("model")
          == advertised.get("walk-lan43"),
          "")
    check("the .43 egress is private_network, never cloud",
          lan_receipt.get("egress", {}).get("scope") == "private_network",
          json.dumps(lan_receipt.get("egress")))
    (shooter.out).mkdir(parents=True, exist_ok=True)
    (shooter.out / "ask-receipt-lan43.json").write_text(
        json.dumps(lan_receipt, indent=2)[:20000]
    )

    # --- control: this_machine in a fresh HOME --------------------------
    status, local_receipt = hub.api(
        "POST", "/api/ask",
        {"prompt": "Reply with exactly: HOLDSPEAK WALK OK",
         "inference_target_id": "this_machine", "max_tokens": 32},
        timeout=180.0,
    )
    local_ok = status == 200 and bool(local_receipt.get("output"))
    if local_ok:
        check("the this_machine receipt names the model that executed",
              local_receipt.get("model")
              == local_receipt.get("actual_placement", {}).get("model"),
              str(local_receipt.get("model")))
    else:
        target = local_receipt.get("inference_target", {})
        check("this_machine REFUSES honestly (no local model in the fresh HOME)",
              local_receipt.get("code") == "inference_target_unavailable"
              and target.get("readiness", {}).get("available") is False,
              str(local_receipt.get("error"))[:140])
        check("the refusal still names the model it would have loaded",
              bool(target.get("model")), str(target.get("model")))
    (shooter.out / "ask-receipt-this-machine.json").write_text(
        json.dumps(local_receipt, indent=2)[:20000]
    )

    # --- the same truth on the glass: the AskPanel footer ---------------
    goto(shooter, hub, "/")
    page.keyboard.press("Meta+i")
    page.wait_for_timeout(1200)
    panel = page.locator('[role="region"][aria-label="Ask AI"]')
    if panel.count() == 0:
        page.keyboard.press("Meta+k")
        page.wait_for_timeout(400)
        page.keyboard.type("Ask AI")
        page.wait_for_timeout(600)
        page.keyboard.press("Enter")
        page.wait_for_timeout(1500)
        panel = page.locator('[role="region"][aria-label="Ask AI"]')
    if panel.count() == 0:
        finding("the Ask panel never opened; the RAN ON footer shot is unproven")
        shooter.shot("ask-panel", "not-opened", "HS-132-09 BLOCKED")
        return
    picker = page.locator('select[aria-label="Runs on"]')
    if picker.count():
        try:
            picker.first.select_option("walk-lan43")
            page.wait_for_timeout(400)
        except Exception as exc:  # noqa: BLE001
            finding(f"could not select the .43 destination in the Runs on picker: {exc}")
    shooter.shot("ask-panel", "destination-selected",
                 "HS-132-09: Ask pointed at the .43 destination")
    composer = page.locator(".desk-chat-composer textarea")
    if composer.count():
        composer.first.fill("Reply with exactly: HOLDSPEAK WALK OK")
        page.keyboard.press("Enter")
        for _ in range(60):
            page.wait_for_timeout(1000)
            foot = page.locator(".desk-ask .surface-footer-receipt").inner_text() \
                if page.locator(".desk-ask .surface-footer-receipt").count() else ""
            if "RAN ON" in foot.upper():
                break
        foot = page.locator(".desk-ask .surface-footer-receipt").inner_text() \
            if page.locator(".desk-ask .surface-footer-receipt").count() else ""
        check("the AskPanel footer says RAN ON and names the executed model",
              "RAN ON" in foot.upper() and lan_model.split(".")[0].lower() in foot.lower(),
              foot.strip()[:160])
        shooter.shot("ask-panel", "ran-on-lan43-footer",
                     "HS-132-09 on glass: RAN ON Homelab .43 · <the model that "
                     "executed>")
    else:
        finding("the Ask composer textarea was not found; footer shot unproven")
    shooter.assert_clean("ask panel")


def _snip(haystack: str, needle: str, width: int = 90) -> str:
    idx = haystack.upper().find(needle.upper())
    if idx < 0:
        return "(absent)"
    return haystack[max(0, idx - 20): idx + width].replace("\n", " / ")


def _probe_lan(url: str) -> tuple[bool, list[str]]:
    import urllib.request

    try:
        with urllib.request.urlopen(url.rstrip("/") + "/models", timeout=8) as resp:
            data = json.loads(resp.read().decode())
        rows = data.get("models") or data.get("data") or []
        names = [r.get("name") or r.get("id") or "" for r in rows]
        return True, [n for n in names if n]
    except Exception as exc:  # noqa: BLE001
        print(f"    (LAN probe error: {exc})", flush=True)
        return False, []



# ------------------------------------------------------------- orchestration

LEGS = {
    "desk": leg_desk_floor,
    "workbench": leg_workbench,
    "intelligence": leg_intelligence,
    "placement": leg_placement_dial,
    "live": leg_live_meeting,
    "cadence": leg_cadence,
    "ask": leg_ask_receipt_honesty,
    # the hub-stopping leg runs last at each width so nothing after it
    # inherits a dead hub
    "write-receipt": leg_write_receipt_backstop,
}


def run_walk(args: Any) -> int:
    from playwright.sync_api import sync_playwright

    from scripts.walk_working_desk import FAILS, FINDINGS, PASSES, SHOTS, _free_port

    out = Path(args.out)
    names = args.only or list(LEGS)
    hub = None
    owns_hub = args.hub_url is None
    if owns_hub:
        hub = Hub(args.port or _free_port(), args.token)
        hub.start()
    else:
        hub = Hub(int(args.hub_url.rsplit(":", 1)[-1]), args.token)
        hub.url = args.hub_url
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            try:
                for width, height in VIEWPORTS:
                    ctx = browser.new_context(
                        viewport={"width": width, "height": height},
                        device_scale_factor=2,
                    )
                    page = ctx.new_page()
                    shooter = Shooter(page, width, out)
                    try:
                        for name in names:
                            LEGS[name](shooter, hub)
                    finally:
                        ctx.close()
            finally:
                browser.close()
    finally:
        if owns_hub and hub is not None:
            hub.stop()

    from scripts import walk_working_desk as W

    print(f"\n{'=' * 60}")
    print(f"{W.PASSES} passed, {len(W.FAILS)} failed, {len(W.FINDINGS)} finding(s), {len(W.SHOTS)} shot(s)")
    for f in W.FAILS:
        print(f"  FAIL     {f}")
    for f in W.FINDINGS:
        print(f"  FINDING  {f}")
    return 1 if W.FAILS else 0
