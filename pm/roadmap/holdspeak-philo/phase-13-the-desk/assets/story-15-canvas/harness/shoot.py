"""PHILO-13-15 (C5) canvas: `Send to ▸` from any document window, drawn on the REAL product.

A REAL hub (scripts/graph_walk.py serve) on an isolated HOME (tempfile.mkdtemp under /tmp,
removed when the run ends), seeded through the product's producers (seed_db.py) and routes
(rig.seed_hub); the PRODUCT app as on main, served by vite with the C5 seats (seats-c5.mjs) and
the shim (c5.tsx, its stand-ins named in its header). Each width on its own hub and HOME.

Usage (from the worktree root):
  PLAYWRIGHT_BROWSERS_PATH=$HOME/Library/Caches/ms-playwright \\
    .venv/bin/python pm/roadmap/holdspeak-philo/phase-13-the-desk/assets/story-15-canvas/harness/shoot.py
ONLY_WIDTH=393 / ONLY=C5-3 limit the run; STACK_STATE=<dev.py state> reuses a stack (iteration only).
Exit 2 on a failed fence.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import board  # noqa: E402

SHOTS = Path(__file__).resolve().parents[1] / "shots"
MEET = "pullout:meeting:m-standup"
BARE = "pullout:meeting:m-bare"
FREEZE = "pullout:decision:d-freeze"
OTEL = "pullout:decision:d-otel"
ART = "pullout:artifact:art-cutover-reqs"
ROOM = "surface-project-memory"


def sends_on_hub(r: board.Runner, ref: str) -> int:
    """The hub's own send rows for one document (read through the real route, never the face)."""
    return r.ev("""async (ref) => { const t = new URLSearchParams(location.search).get('token');
      const res = await fetch('/api/channels/sends?document_ref=' + encodeURIComponent(ref), { headers: { Authorization: 'Bearer ' + t } });
      const j = await res.json(); return (j.sends || []).filter((s) => !String(s.id).startsWith('chs_c5_')).length; }""", ref)


# C5's own targets: the menus and the SEND wells (the 393 fence fails on these; others are recorded inherited).
OWN44 = r"""() => [...document.querySelectorAll('[role=menu] [role^=menuitem], [role=menu] button, [data-testid=send-well] button, [data-testid=send-well] select, [data-testid=send-well] [role=button]')]
  .map((t) => (t.getAttribute('aria-label') || t.innerText || t.getAttribute('placeholder') || t.className || '').toString().trim().replace(/\s+/g, ' ').slice(0, 32))"""


def picked_whole(win: str, phone: bool = False) -> list[str]:
    w = f"[id='{win}']"
    title = ".desk-screen-name" if phone else f"{w} > .desk-pullout-head .desk-pullout-title"
    return [title, f"{w} li.surface-ledger-row:has([data-testid=send-open]) .surface-primary",
            f"{w} [data-testid=send-open] [data-testid=send-preview-field] dd", f"{w} [data-testid=send-open] [data-testid=send-verbs] .btn--primary"]


def boards(r: board.Runner) -> None:
    ev, settle = r.ev, r.settle
    phone = r.phone
    r.scope44 = OWN44

    def open_win(js: str, win: str, ms=2800):
        ev(f"() => {js}")
        settle(ms)
        ev("(w) => window.__cOpen.focus(w)", win)
        settle(500)

    def send_to(win: str, read_first=True):
        if read_first:
            ev("(w) => window.__c5.docOf(w)", win)
            settle(900)
        r.window_menu(win)
        r.open_sub("Send to")

    def press_send(win: str):
        r.tap(r.page.locator(f"[id='{win}'] [data-testid=send-open] [data-testid=send-verbs] .btn--primary"), 1800)

    # ── C5-1 the window's menu leads with Send to ▸ (the meeting window) ──
    open_win("window.__cOpen.open('meeting:m-standup')", MEET)
    send_to(MEET)
    f = r.shoot("C5-1-window-menu-send-to", "Ledger cutover sync")
    if f is not None:
        rows = [x for m in f["menus"] for x in m["rows"]]
        if not any(x.startswith("Team updates") for x in rows) or not any(x.startswith("Slack #leads") for x in rows):
            r.fails.append(f"C5-1-{r.width}: the destinations are not the Send to rows ({rows})")
    # ── C5-3 the pick: the window's well, picked, its preview and Send in view; nothing sent ──
    r.pick_row("Slack #leads")
    settle(1500)
    n0 = sends_on_hub(r, "meeting_summary:m-standup")
    r.shoot("C5-3-picked-preview-in-view", "Ledger cutover sync", whole=picked_whole(MEET, phone),
            checks={"no send row before Send (hub)": n0 == 0}, extra={"hub_sends_before_send": n0})
    # ── C5-13 a second pick on the open well changes it in place ──
    send_to(MEET, read_first=False)
    r.pick_row("PAY-118")
    settle(1500)
    picked = ev("() => (document.querySelector(\"[id='pullout:meeting:m-standup'] [data-testid=send-open]\") || {}).dataset?.destination || null")
    r.shoot("C5-13-second-pick-in-place", "Ledger cutover sync", whole=picked_whole(MEET, phone),
            checks={"the open well changed its pick in place": picked == "PAY-118"}, extra={"picked": picked})
    # ── C5-14 Summary -> Digest keeps the destination ──
    # The form picker is a native <select> (CycleGadget): driven by select_option at both widths (as Phase 12's G8);
    # it proves the Digest state, not the gesture.
    cyc = r.page.locator(f"[id='{MEET}'] [data-testid=doc-forms] select").first
    cyc.select_option("meeting_digest")
    settle(1800)
    doc = ev("() => (document.querySelector(\"[id='pullout:meeting:m-standup'] [data-testid=send-well]\") || {}).dataset?.doc || null")
    picked = ev("() => (document.querySelector(\"[id='pullout:meeting:m-standup'] [data-testid=send-open]\") || {}).dataset?.destination || null")
    r.shoot("C5-14-digest-keeps-destination", "Ledger cutover sync", whole=picked_whole(MEET, phone),
            checks={"the form is Digest": doc == "meeting_digest:m-standup", "the destination is kept": picked == "PAY-118"}, extra={"doc": doc, "picked": picked})
    # ── C5-4 in flight: SENDING (stand-in Slack holds its answer) ──
    cyc.select_option("meeting_summary")
    settle(1800)
    send_to(MEET, read_first=False)
    r.pick_row("Slack #leads")
    settle(1500)
    press_send(MEET)
    f = r.shoot("C5-4-sending", "Ledger cutover sync", whole=picked_whole(MEET, phone)[:2])
    if f is not None and not ev("() => !!document.querySelector(\"[id='pullout:meeting:m-standup'] [data-testid=send-running]\")"):
        r.fails.append(f"C5-4-{r.width}: no SENDING receipt")
    # ── C5-5 settled: a REAL send to the FILE destination; the hub holds one row ──
    send_to(MEET, read_first=False)
    r.pick_row("Team updates")
    settle(1800)
    press_send(MEET)
    settle(1500)
    n1 = sends_on_hub(r, "meeting_summary:m-standup")
    f = r.shoot("C5-5-sent-file", "Ledger cutover sync", whole=picked_whole(MEET, phone)[:2],
                checks={"one send row on the hub after Send": n1 == 1}, extra={"hub_sends_after_send": n1})
    if f is not None and not ev("() => !!document.querySelector(\"[id='pullout:meeting:m-standup'] [data-testid=send-sent]\")"):
        r.fails.append(f"C5-5-{r.width}: no SENT receipt")
    r.close_all()

    # ── C5-6 failed and C5-7 unknown (decision windows; stand-in answers) ──
    ev("() => window.__c5.outcome('chd_c5_jira', 'failed')")
    open_win("window.__cOpen.open('decision:d-freeze')", FREEZE)
    send_to(FREEZE)
    r.pick_row("PAY-118")
    settle(1500)
    press_send(FREEZE)
    f = r.shoot("C5-6-failed", "Freeze the old ledger on Nov 5", whole=picked_whole(FREEZE, phone)[:2])
    if f is not None and not ev(f"() => !!document.querySelector(\"[id='{FREEZE}'] [data-testid=send-failed]\")"):
        r.fails.append(f"C5-6-{r.width}: no FAILED receipt")
    r.close_all()
    ev("() => window.__c5.outcome('chd_c5_slack', 'unknown')")
    open_win("window.__cOpen.open('decision:d-otel')", OTEL)
    send_to(OTEL)
    r.pick_row("Slack #leads")
    settle(1500)
    press_send(OTEL)
    f = r.shoot("C5-7-unknown", "Adopt OpenTelemetry for all services", whole=picked_whole(OTEL, phone)[:2])
    if f is not None and not ev(f"() => !!document.querySelector(\"[id='{OTEL}'] [data-testid=send-unknown]\")"):
        r.fails.append(f"C5-7-{r.width}: no UNKNOWN receipt")
    r.close_all()

    # ── C5-8 withheld: a meeting with no summary has no Send to ──
    open_win("window.__cOpen.open('meeting:m-bare')", BARE)
    ev("(w) => window.__c5.docOf(w)", BARE)
    settle(1200)
    r.window_menu(BARE)
    f = r.shoot("C5-8-withheld-no-summary", "Vendor call")
    if f is not None and any(x.startswith("Send to") for m in f["menus"] for x in m["rows"]):
        r.fails.append(f"C5-8-{r.width}: Send to is offered on a meeting with no summary")
    r.escape()
    r.close_all()

    # ── C5-2 the Object menu: the same composition, from the FRONT window's document ──
    open_win("window.__cOpen.open('artifact:art-cutover-reqs')", ART)
    if phone:
        r.tap(r.page.locator(".desk-verbbar [data-menu-id=go] button"), 700)
        sub = r.page.locator("[role=menu] [role=menuitem][aria-haspopup=menu]:has-text('Send to')").first
        sub.scroll_into_view_if_needed()
        r.tap(sub, 700)
    else:
        r.page.locator(".desk-verbbar [data-menu-id=object] button").first.click()
        settle(600)
        r.open_sub("Send to")
    f = r.shoot("C5-2-object-menu-send-to", "Cutover requirements")
    if f is not None and not any(x.startswith("Team updates") for m in f["menus"] for x in m["rows"]):
        r.fails.append(f"C5-2-{r.width}: the Object menu's Send to has no destination rows")
    # ── C5-12 the artifact window: its SEND well; library Buttons only ──
    r.pick_row("Team updates")
    settle(1800)
    raw_art = ev(f"() => [...document.querySelectorAll(\"[id='{ART}'] button\")].filter((b) => !/(^|\\s)(btn|btn--chrome)(\\s|$)/.test(String(b.className))).length")
    r.shoot("C5-12-artifact-window-well", "Cutover requirements", whole=picked_whole(ART, phone),
            checks={"no raw <button> in the artifact window": raw_art == 0}, extra={"raw_in_artifact": raw_art})
    r.close_all()

    # ── C5-9 no destination: Send to ▸ Add destination ──
    ev("() => window.__c5.mode({ none: true })")
    settle(800)
    open_win("window.__cOpen.open('decision:d-freeze')", FREEZE)
    send_to(FREEZE)
    f = r.shoot("C5-9-no-destination-add", "Freeze the old ledger on Nov 5")
    if f is not None and not any(x == "Add destination" for m in f["menus"] for x in m["rows"]):
        r.fails.append(f"C5-9-{r.width}: no Add destination row")
    r.escape()
    ev("() => window.__c5.mode({ none: false })")
    settle(800)
    r.close_all()

    # ── C5-10 the Room: the latest published update; CHECKING / CAN'T CHECK while the read is not known ──
    ev("() => window.__c5.hold('project:p-ledger', 'loading')")
    open_win("window.__cOpen.room('p-ledger')", ROOM, 3500)
    send_to(ROOM, read_first=False)
    f = r.shoot("C5-10a-room-checking", "Payments ledger cutover")
    r.escape()
    ev("() => window.__c5.hold('project:p-ledger', 'failed')")
    send_to(ROOM, read_first=False)
    f = r.shoot("C5-10b-room-cant-check", "Payments ledger cutover")
    # Condition 5: the pick under CAN'T CHECK (the failure still held) opens the well with the failure in view.
    r.pick_row("Team updates")
    settle(1500)
    w = "[id='surface-project-memory'] [data-testid=c5-room-read-failed]"
    r.shoot("C5-10c-room-pick-opens-failure", "Payments ledger cutover",
            whole=[f"{w} [data-testid=c5-latest-unreadable]", f"{w} [data-testid=c5-latest-unreadable-retry]"],
            checks={"the failure is still held at the pick": ev("() => window.__c5.facts()['project:p-ledger']?.state === 'failed'")})
    # Recovery: Retry reads again (the real read), then the picked update's well opens in view.
    r.tap(r.page.locator(f"{w} [data-testid=c5-latest-unreadable-retry]"), 3500)
    r.shoot("C5-11-room-retry-recovers", "Payments ledger cutover", whole=picked_whole(ROOM, phone)[1:],
            checks={"the failure line is gone": not ev(f"() => !!document.querySelector(\"{w}\")")})
    r.close_all()

    # ── C5-15 the Chair's Brief window ──
    ev("() => window.__cOpen.chair()")
    if phone:
        ev("() => import('/src/desk/chair/chairWindows.ts').then((m) => m.openChairWindow('chair:brief'))")
    else:
        ev("(w) => window.__cOpen.focus(w)", "chair:brief")
    settle(1200)
    send_to("chair:brief")
    r.pick_row("Slack #leads")
    settle(2000)
    r.shoot("C5-15-brief-window-picked", "Brief", whole=picked_whole("chair:brief", phone))

    # ── C5-16 offline: the rows are the last read; the well says what it cannot read ──
    open_win("window.__cOpen.open('decision:d-otel')", OTEL)
    ev("() => window.__c5.mode({ offline: true })")
    settle(900)
    send_to(OTEL, read_first=False)
    f = r.shoot("C5-16a-offline-menu", "Adopt OpenTelemetry for all services")
    if f is not None and not any(m["label"] and "Send to · OFFLINE" in (m["label"] or "") for m in f["menus"]) \
            and not any(x.startswith("Send to · OFFLINE") for m in f["menus"] for x in m["rows"]):
        r.fails.append(f"C5-16a-{r.width}: the row does not say OFFLINE ({f['menus']})")
    r.pick_row("Team updates")
    settle(2500)
    r.shoot("C5-16b-offline-well", "Adopt OpenTelemetry for all services")
    ev("() => window.__c5.mode({ offline: false })")
    settle(500)


if __name__ == "__main__":
    sys.exit(board.main(SHOTS, "C5", "c5", boards))
