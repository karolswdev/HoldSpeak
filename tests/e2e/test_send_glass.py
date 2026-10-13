"""The Send app, AS RENDERED: what only a real browser proves of `Send to ▸`.

Owner, 2026-10-12 (push 2 of the test diet): a browser test only for drag,
focus, keys, touch, hover or an exact geometry relation. This file keeps the
`Send to ▸` checks of PHILO-13-15 (C5) that need one, through the real hub on
an isolated HOME, at 1440 (mouse) and 393 (touch):

* the window menu opens by a right click (1440) or a CDP touch long press
  (393), and it leads with `Send to ▸`;
* 1440: the hovered submenu touches its parent panel (3 px or less, the tops
  overlap, inside the viewport);
* the pick: the window name, the picked row, the preview's first field and
  Send are each WHOLE on screen (inside the viewport, the point at the centre
  is the element's own); at 393 every menu row and SEND well target owns
  44 x 44 (nine points);
* the Room's own read of the linked update fails after the menu read: the
  pick shows CANNOT READ LATEST UPDATE with Retry in view, and the real Retry
  read recovers to the update's well. (T2 is owed here: the Room's send link
  needs a recorded published-update wire; until then it stays in a browser.)

Every other C5 board has a cheaper successor (each named in the PR that
parked tests/e2e/_parked/test_philo13_15_send_to_glass.py):
web/src/desk/__tests__/windowSend.philo1315.test.tsx (the rows, CHECKING,
CAN'T CHECK, OFFLINE, withheld, the push seam, Summary -> Digest, the
same-second tie, the artifact well), web/src/desk/surface/send/__tests__/
SendWell.test.tsx (SENDING, SAVED, FAILED, UNKNOWN, NOTHING SENT),
tests/unit/test_desk_palette_send.py (the real FILE send),
tests/integration/test_update_routes.py (the tie on the hub), and the desk
sweep (clipped, overlap, readable on every window and wing).

STAND-INS: `Slack #leads` and `PAY-118` are destinations added to the read by
a Playwright route; their preview is the hub's real render through the FILE
destination. NOTHING LEAVES THE MACHINE. `Team updates` is a REAL FILE
destination in a scratch folder.

Also here (lane e2e-high-1):

The SEND well in a real browser: the Chair's meeting rows, at 393 by touch.

Kept by the test diet (push 2, 2026-10-12), one file for the Send species.
What stays needs a real browser: at 393 the form picker is a 44 px target
and owns all nine points of it (touch geometry); the send from the Chair's
meeting row is pressed through to the hub's row and the kernel receipt.
Was tests/e2e/test_philo11_05a_brief_decision_send_glass.py; its brief,
decision and decision-record wells are
web/src/desk/surface/send/__tests__/SendWell.test.tsx (each face sends its
own document_ref) and room172proposals.test.tsx; the brief to Slack carries
no People data in tests/unit/test_brief_send_carries_no_people.py.

PHILO-11-05a -- the SEND well on the brief and decision faces, fenced AS
RENDERED through the real hub on an isolated HOME at 1440x900 and 393x852.

Built to the owner's ratified canvases (phase-11 story 03, "Yes..."): boards
A1-A6 (the brief on the Chair and in Intelligence -> BRIEF), B1-B5 (the
decision window, the Room's DECISIONS & COMMITMENTS rows, Intelligence ->
DECISIONS), T2 (PREVIEW CHANGED -> a fresh preview -> another press) and T3
(the Chair after its last brief item is triaged). Each face sends its OWN
``document_ref``; each fence reads the hub's send row and compares the face's
outcome with it in the same test.

Every fixture comes from a real producer: the brief from
``POST /api/brief/generate``; the desk decision from ``POST /api/decisions``
and its change from ``PUT /api/decisions/<id>``; the meeting-proposal record
from the decision_capture artifact through ``ProposalBridgeService`` (what the
intel queue runs) and ``POST /api/proposals/<id>/confirm``; a plain record from
``DecisionRecordService.create``; the prepared sends from ``channel.prepare``
(``POST /api/channels/sends``) by a remote agent credential issued through the
real Settings route. The recorded meeting itself is written through the
product's DB layer (no route records a meeting without audio; the canvas did
the same). Destinations are folders: nothing leaves the machine.
"""
from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from .glass_infra import _api, _boot, _ensure_build, _normal_chair, _rendered_text_faults, _settle, park_builtin_folder
from tests._evidence import evidence_dir
from ._doc_send_glass import Boards
from .chair_windows import open_chair_window

pytest.importorskip("playwright.sync_api", reason="the send glass needs Playwright")

TOKEN = "send-glass"
SHOTS = evidence_dir("pm/roadmap/holdspeak-philo/phase-13-the-desk/assets/story-15-shots")
SIZES = {1440: 900, 393: 852}
T = 20_000
MEET = "pullout:meeting:m-standup"
BARE = "pullout:meeting:m-bare"
FREEZE = "pullout:decision:d-freeze"
OTEL = "pullout:decision:d-otel"
ART = "pullout:artifact:art-cutover-reqs"
ROOM = "surface-project-memory"
BRIEF = "chair:brief"
STANDINS = [
    {"id": "chd_si_slack", "name": "Slack #leads", "channel": "slack",
     "account": {"key_ref": "slack_standin", "key_present": True}, "target": {"channel_label": "#leads"}},
    {"id": "chd_si_jira", "name": "PAY-118", "channel": "jira",
     "account": {"site": "acme.atlassian.net", "email": "owner@acme.test"}, "target": {"key": "PAY-118"},
     "connection": {"state": "connected"}},
]


def _seed(db: Any) -> dict[str, Any]:
    """The canvas's seed (story-15-canvas/harness/seed_db.py), through the real producers."""
    from holdspeak.meeting_session import IntelSnapshot, MeetingState, TranscriptSegment
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services.monday_brief_service import MondayBriefService
    from holdspeak.services.primitive_service import PrimitiveService
    from holdspeak.services.project_service import ProjectService
    from holdspeak.services.project_update_service import ProjectUpdateService

    now = datetime.now()
    owner = Principal(PrincipalKind.OWNER, "karol")
    db.projects.create_project(project_id="p-ledger", name="Payments ledger cutover",
                               description="Move settlement to the new ledger by Nov 5.", keywords=["ledger"])
    db.project_updates.insert_update(
        update_id="upd-ledger-1", project_id="p-ledger", project_revision=1, body_md="")
    updates = ProjectUpdateService(db, project_service=ProjectService(db))
    # PHILO-15 B64: the owner's text, saved through the editor's path, is his
    # reviewed words (an update with no verified claim is refused).
    updates.save_update(owner, "upd-ledger-1",
                        body_md="## Week 40\n\n- Dual-write is live in staging.\n- Cutover date holds: Nov 5.\n")
    updates.publish_update(owner, "upd-ledger-1")
    prim = PrimitiveService(db)
    prim.create_decision(owner, decision_id="d-freeze", title="Freeze the old ledger on Nov 5", status="accepted",
                         deciders=["karol"], context_markdown="Dual-write is stable.",
                         decision_markdown="Freeze writes to the old ledger on Nov 5.")
    prim.create_decision(owner, decision_id="d-otel", title="Adopt OpenTelemetry for all services", status="proposed",
                         decision_markdown="Use the OTel SDK in every service.")
    start = (now - timedelta(hours=2)).replace(microsecond=0)
    db.meetings.save_meeting(MeetingState(
        id="m-standup", started_at=start, ended_at=start + timedelta(minutes=30), title="Ledger cutover sync",
        segments=[TranscriptSegment(text="Dual-write is stable.", speaker="Me", start_time=1.0, end_time=4.0)],
        intel=IntelSnapshot(timestamp=1.0, topics=["cutover"],
                            summary="Dual-write is stable. The team agreed to freeze the old ledger on Nov 5.",
                            action_items=[{"id": "m-standup-a1", "task": "Write the rollback runbook", "owner": None,
                                           "due": None, "status": "pending", "review_state": "accepted",
                                           "source_timestamp": None, "created_at": start.isoformat()}]),
        intel_status="completed"))
    db.projects.associate_meeting_project(meeting_id="m-standup", project_id="p-ledger", source="manual", confidence=1.0)
    # The digest and the follow-up read the meeting's decisions (the aftercare producer).
    db.plugins.record_artifact(artifact_id="m-standup-decisions", meeting_id="m-standup", artifact_type="decisions",
                               title="Meeting decisions", plugin_id="p13-15-seed",
                               structured_json={"decisions": [{"decision": "Freeze the old ledger on Nov 5",
                                                               "rationale": "Agreed in the meeting."}]})
    from holdspeak.db.decisions import backfill_decisions

    with db._connection() as conn:
        backfill_decisions(conn)
    db.meetings.save_meeting(MeetingState(
        id="m-bare", started_at=(now - timedelta(hours=3)).replace(microsecond=0),
        ended_at=(now - timedelta(hours=2, minutes=40)).replace(microsecond=0), title="Vendor call",
        segments=[TranscriptSegment(text="Hello, can you hear me.", speaker="Me", start_time=1.0, end_time=3.0)],
        intel_status="disabled"))
    db.plugins.record_artifact(artifact_id="art-cutover-reqs", meeting_id="m-standup", artifact_type="requirements",
                               title="Cutover requirements",
                               body_markdown="### Cutover requirements\n\n- Freeze the old ledger on Nov 5.\n",
                               status="accepted", plugin_id="requirements_extractor", confidence=0.9)
    brief = MondayBriefService(db).generate(owner, now=now)
    return {"brief": brief.id}


# C1's ratified 44 x 44 rule (story-11-canvas/harness/shoot.py TARGETS44), scoped as the C5 canvas
# scoped it (its OWN44): the menus and the SEND wells. A target's box, grown to 44 x 44 about its
# centre, is sampled at nine points; each point is the target's own, or another layer above it.
TARGETS44 = r"""() => {
  const shown = (e) => { if (!e || e.closest('[hidden]')) return false; const r = e.getBoundingClientRect(); const cs = getComputedStyle(e);
    return r.width > 0 && r.height > 0 && cs.visibility !== 'hidden' && cs.display !== 'none' && Number(cs.opacity) > 0.05 && r.bottom > 0 && r.top < innerHeight && r.right > 0 && r.left < innerWidth; };
  const layer = (e) => e && e.closest('[role=menu], .desk-window-shell, .desk-menubar, .desk-dock');
  const vrect = (e) => { const r = e.getBoundingClientRect(); let t = r.top, l = r.left, b = r.bottom, ri = r.right;
    for (let a = e.parentElement; a; a = a.parentElement) { const cs = getComputedStyle(a);
      if (/(auto|scroll|hidden|clip)/.test(cs.overflowX + cs.overflowY)) { const ar = a.getBoundingClientRect(); t = Math.max(t, ar.top); l = Math.max(l, ar.left); b = Math.min(b, ar.bottom); ri = Math.min(ri, ar.right); } }
    t = Math.max(t, 0); l = Math.max(l, 0); b = Math.min(b, innerHeight); ri = Math.min(ri, innerWidth);
    return { t, l, b, r: ri, w: ri - l, h: b - t, full: Math.abs(ri - l - r.width) < 1.5 && Math.abs(b - t - r.height) < 1.5 }; };
  const nine = (x0, y0, x1, y1) => { const xs = [x0 + 2, (x0 + x1) / 2, x1 - 2], ys = [y0 + 2, (y0 + y1) / 2, y1 - 2]; return xs.flatMap((x) => ys.map((y) => [x, y])); };
  const probe = (t, x, y) => { const h = document.elementFromPoint(x, y); if (!h) return 'lost'; if (t === h || t.contains(h)) return 'own';
    const lt = layer(t), lh = layer(h); return (lh && lt && lh !== lt && !lt.contains(lh)) ? 'occluded' : 'lost'; };
  const out = [];
  const sel = '[role=menu] [role^=menuitem], [role=menu] button, [data-testid=send-well] button, [data-testid=send-well] select, [data-testid=send-well] [role=button]';
  for (const t of document.querySelectorAll(sel)) {
    if (!shown(t)) continue;
    if (t.parentElement && t.parentElement.closest('button, [role=button], a[href], [role=menuitem]')) continue;
    const v = vrect(t); if (!v.full) continue;
    const cx = (v.l + v.r) / 2, cy = (v.t + v.b) / 2, hw = Math.max(22, v.w / 2), hh = Math.max(22, v.h / 2);
    const res = nine(cx - hw, cy - hh, cx + hw, cy + hh).map(([x, y]) => probe(t, x, y));
    const own = res.filter((r) => r === 'own').length, occ = res.filter((r) => r === 'occluded').length;
    if (own + occ < 9) out.push({ name: (t.getAttribute('aria-label') || t.innerText || '').trim().replace(/\s+/g, ' ').slice(0, 32), w: Math.round(v.w), h: Math.round(v.h), own, occ });
  }
  return out;
}"""


class StandIns:
    """The canvas's stand-ins as Playwright routes (S1, S2, S4). The FILE row is real."""

    def __init__(self, page: Any, file_id: str):
        self.page, self.file_id = page, file_id
        self.none = False
        self.offline = False
        self.outcome: dict[str, str] = {}
        self.hold: str | None = None          # None | "loading" | "failed" for the Room's updates read
        self.hold_file_answer = False         # a REAL FILE send whose answer is held (the hub has sent)
        self.held_answers: list[tuple[Any, Any]] = []
        self.held: list[Any] = []
        self.sends: list[dict[str, Any]] = []
        page.route(re.compile(r".*/api/.*"), self._route)

    def set_hold(self, how: str | None) -> None:
        self.hold = how
        held, self.held = self.held, []
        for r in held:        # a held read answers as failed when the hold changes
            try:
                r.abort("connectionfailed")
            except Exception:  # noqa: BLE001
                pass

    def release(self) -> None:
        self.hold_file_answer = False
        held, self.held_answers = self.held_answers, []
        for route, response in held:
            route.fulfill(response=response)

    def _route(self, route: Any) -> None:
        req = route.request
        url = req.url
        path = re.sub(r"^https?://[^/]+", "", url).split("?")[0]
        if self.offline:
            route.abort("connectionfailed")
            return
        if path.startswith("/api/projects/p-ledger/updates") and req.method == "GET" and self.hold:
            if self.hold == "loading":
                self.held.append(route)
                return
            route.abort("connectionfailed")
            return
        if path == "/api/channels/destinations" and req.method == "GET":
            if self.none:
                route.fulfill(json={"destinations": []})
                return
            r = route.fetch()
            body = r.json()
            body["destinations"] = list(body.get("destinations", [])) + [
                {"synced": False, "created_at": "2026-10-02T08:00:00+00:00", "state": "active", "parked_at": None, **d}
                for d in STANDINS]
            route.fulfill(response=r, json=body)
            return
        if path == "/api/channels/preview" and req.method == "POST":
            b = json.loads(req.post_data or "{}")
            if b.get("destination_id", "").startswith("chd_si_"):
                r = route.fetch(post_data=json.dumps({**b, "destination_id": self.file_id}))
                body = r.json()
                body["payload_digest"] = f"{body.get('payload_digest')}-{b['destination_id']}"
                route.fulfill(response=r, json=body)
                return
        if path == "/api/channels/send" and req.method == "POST" and self.hold_file_answer \
                and json.loads(req.post_data or "{}").get("destination_id") == self.file_id:
            # The hub performs the real send now; its answer reaches the face only on release().
            self.held_answers.append((route, route.fetch()))
            return
        if path == "/api/channels/send" and req.method == "POST":
            b = json.loads(req.post_data or "{}")
            sd = next((d for d in STANDINS if d["id"] == b.get("destination_id")), None)
            if sd:
                at = datetime.now().astimezone().isoformat()
                o = self.outcome.get(sd["id"], "sending")
                row = {
                    "id": f"chs_si_{uuid.uuid4().hex[:8]}", "document_ref": b["document_ref"], "destination_id": sd["id"],
                    "destination_name": sd["name"], "channel": sd["channel"], "account": sd["account"],
                    "target": sd["target"], "payload_digest": b.get("preview_digest"), "preview": {"text": ""},
                    "prepared_by": {"kind": "owner", "identity": "owner"}, "prepare_operation_id": None,
                    "created_at": at, "dispatch_started_at": at, "dispatch_seq": 900 + len(self.sends),
                    "state": "dispatching" if o == "sending" else o, "settled_at": None if o == "sending" else at,
                    "reason": {"failed": "transport_error", "unknown": "timeout"}.get(o), "proof": {},
                }
                self.sends.append(row)
                route.fulfill(json={"send": row, "operation_id": row["id"]})
                return
        if path == "/api/channels/sends" and req.method == "GET":
            ref = re.search(r"document_ref=([^&]+)", url)
            from urllib.parse import unquote
            ref_s = unquote(ref.group(1)) if ref else ""
            r = route.fetch()
            body = r.json() if r.ok else {}
            mine = [s for s in self.sends if s["document_ref"] == ref_s]
            route.fulfill(response=r, json={**body, "sends": list(body.get("sends", [])) + mine})
            return
        route.continue_()


class TestSendGlass:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        _ensure_build()
        server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
        park_builtin_folder()  # the desk these boards were drawn on (glass_infra.park_builtin_folder)
        self.server, self.base, self.home = server, base, tmp_path / "home"
        self.monkeypatch = monkeypatch
        from holdspeak.db import get_database

        self.db = get_database()
        self.seed = _seed(self.db)
        try:
            yield
        finally:
            server.stop()

    # ── the rig ──────────────────────────────────────────────────────────

    def _db_sends(self, ref: str) -> list[dict[str, Any]]:
        """The hub's own send rows for one document, read from its DB (never the face)."""
        with self.db._connection() as conn:
            rows = conn.execute("SELECT id, state, proof_json FROM channel_sends WHERE document_ref = ?", (ref,)).fetchall()
        return [{"id": r[0], "state": r[1], "proof": json.loads(r[2] or "{}")} for r in rows]

    def _ev(self, js: str, arg: Any = None) -> Any:
        return self.page.evaluate(js, arg)

    def _wait(self, ms: int = 600) -> None:
        self.page.wait_for_timeout(ms)

    def _tap(self, loc: Any, ms: int = 700) -> None:
        loc = loc.first
        loc.scroll_into_view_if_needed()
        if self.phone:
            b = loc.bounding_box()
            self.page.touchscreen.tap(b["x"] + b["width"] / 2, b["y"] + b["height"] / 2)
        else:
            loc.click()
        self._wait(ms)

    def _long_press(self, x: float, y: float) -> None:
        cdp = self.page.context.new_cdp_session(self.page)
        cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": x, "y": y, "id": 1}]})
        self.page.wait_for_timeout(750)
        cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
        cdp.detach()
        self._wait(500)

    def _open_ref(self, ref: str, win: str) -> None:
        self.page.goto(f"{self.base}/?token={TOKEN}&open={ref}", wait_until="load")
        _normal_chair(self.page)
        self.page.locator(f"[id='{win}']").wait_for(timeout=T)
        self._wait(1500)

    def _open_surface(self, key: str, scope: str | None, win: str) -> None:
        self.page.goto(f"{self.base}/?token={TOKEN}", wait_until="load")   # no `open=` left from a pullout
        self._ev("""([k, s]) => { localStorage.removeItem('hs.desk.workspace.v1');
            sessionStorage.setItem('hs.desk.staged-surface-open', JSON.stringify(s ? {key: k, scope: s} : {key: k})); }""", [key, scope])
        self.page.reload(wait_until="load")
        _normal_chair(self.page)
        self.page.locator(f"[id='{win}']").wait_for(timeout=T)
        self._wait(1800)

    def _window_menu(self, win: str) -> None:
        head = self.page.locator(f"[id='{win}'] > .desk-pullout-head")
        t = head.locator(".desk-pullout-title").first
        b = t.bounding_box() if t.count() and t.is_visible() else head.first.bounding_box()
        x, y = b["x"] + min(b["width"] - 4, max(8, b["width"] / 2)), b["y"] + b["height"] / 2
        if self.phone:
            self._long_press(x, y)
        else:
            self.page.mouse.click(x, y, button="right")
            self._wait(500)
        self.page.locator("[role=menu]").first.wait_for(timeout=10_000)

    def _sub_row(self) -> Any:
        return self.page.locator("[role=menu] [role=menuitem][aria-haspopup=menu]:has-text('Send to')").first

    def _open_send_to(self) -> str:
        sub = self._sub_row()
        sub.wait_for(timeout=T)
        label = sub.inner_text().replace("»", "").strip()
        if self.phone:
            self._tap(sub, 700)
        else:
            sub.hover()
            self._wait(700)
            self._adjacent()
        return label

    def _send_to(self, win: str) -> str:
        self._window_menu(win)
        # The menu leads with Send to ▸, its own group.
        first = self.page.locator("[role=menu] [role^=menuitem]").first.inner_text()
        assert first.startswith("Send to"), first
        return self._open_send_to()

    def _rows(self) -> list[str]:
        sel = "[role=menu].desk-work-submenu [role^=menuitem]" if not self.phone else "[role=menu] [role^=menuitem]:not(.desk-menu-back)"
        return [x.strip() for x in self.page.locator(sel).all_inner_texts()]

    def _pick(self, text: str) -> None:
        self._tap(self.page.locator(f"[role=menu] [role^=menuitem]:has-text('{text}')").last, 900)

    def _escape(self) -> None:
        self.page.keyboard.press("Escape")
        self.page.keyboard.press("Escape")
        self._wait(300)

    def _adjacent(self) -> None:
        """1440: the submenu's edge touches its parent's edge (3 px or less); their tops overlap."""
        r = self._ev("""() => { const sub = document.querySelector('.desk-work-submenu');
            const par = sub && sub.parentElement.closest('.desk-work-menu');
            if (!sub || !par) return null; const a = sub.getBoundingClientRect(), b = par.getBoundingClientRect();
            return {gapR: Math.abs(a.left - b.right), gapL: Math.abs(a.right - b.left), overlap: Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top),
                    inView: a.left >= 0 && a.right <= innerWidth}; }""")
        assert r, "no submenu beside a parent panel"
        assert min(r["gapR"], r["gapL"]) <= 3 and r["overlap"] > 0 and r["inView"], r
        self.adjacent += 1

    def _glass(self, board: str) -> None:
        """The on-glass reader over every open menu and every SEND well: zero clipped, zero overlaps."""
        _settle(self.page)
        for sel in ("[role=menu]", "[data-testid=send-well]"):
            f = _rendered_text_faults(self.page, sel, on_glass=True)
            assert not f["clipped"] and not f["overlaps"], f"{board}-{self.width} {sel}: {f}"
        if self.phone:
            small = self._ev(TARGETS44)
            assert not small, f"{board}-393 targets under 44 x 44: {small}"

    def _whole(self, win: str, board: str, *, field: bool = True) -> None:
        """The arrival: the window name, the picked row, the preview's first field and Send, each WHOLE on screen."""
        w = f"[id='{win}']"
        sels = [".desk-screen-name" if self.phone else f"{w} > .desk-pullout-head .desk-pullout-title",
                f"{w} li.surface-ledger-row:has([data-testid=send-open]) .surface-primary"]
        if field:
            sels += [f"{w} [data-testid=send-open] [data-testid=send-preview-field] dd",
                     f"{w} [data-testid=send-open] [data-testid=send-verbs] .btn--primary"]
        for sel in sels:
            ok = self._ev("""(sel) => { const e = [...document.querySelectorAll(sel)].find((x) => x.checkVisibility());
                if (!e) return 'absent'; const r = e.getBoundingClientRect();
                if (r.top < 0 || r.left < 0 || r.bottom > innerHeight || r.right > innerWidth) return 'off screen ' + JSON.stringify(r);
                const hit = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2);
                return hit && (e.contains(hit) || hit.contains(e)) ? 'ok' : 'covered by ' + (hit?.className || hit?.tagName); }""", sel)
            assert ok == "ok", f"{board}-{self.width} {sel}: {ok}"

    def _shot(self, board: str) -> None:
        _settle(self.page)
        self.page.screenshot(path=str(SHOTS / f"{board}-{self.width}.png"))

    # ── the cases ────────────────────────────────────────────────────────

    @pytest.mark.e2e
    @pytest.mark.timeout(600)
    @pytest.mark.parametrize("width", [1440, 393])
    def test_the_window_menu_send_to_and_the_pick_in_view(self, width: int) -> None:
        """replaces: tests/e2e/test_philo13_15_send_to_glass.py::TestSendToGlass::test_send_to_from_every_document_window
        (the gesture and geometry legs: C5-1 the menu by right click or long press,
        the submenu beside its parent, C5-3 the pick whole in view, 44 x 44 at 393)."""
        self._session(width, lambda si, folder: self._menu_and_pick(), adjacent=True)

    @pytest.mark.e2e
    @pytest.mark.timeout(600)
    @pytest.mark.parametrize("width", [1440, 393])
    def test_room_pick_when_the_update_read_fails(self, width: int) -> None:
        """replaces: tests/e2e/test_philo13_15_send_to_glass.py::TestSendToGlass::test_room_pick_when_the_update_read_fails

        Astra C5 check, condition 1: the menu's latest-update read succeeds, the Room's own
        read of that update fails. The pick keeps the handoff and shows CANNOT READ LATEST
        UPDATE + Retry in the Room's SEND well; Retry (the real read) recovers to the well."""
        self._session(width, lambda si, folder: self._room_second_read_fails(si))

    def _menu_and_pick(self) -> None:
        page = self.page
        self._open_ref("meeting:m-standup", MEET)
        label = self._send_to(MEET)
        assert label == "Send to", label
        rows = self._rows()
        assert "Team updates · FILE" in rows and "Slack #leads · SLACK" in rows, rows
        self._glass("C5-1")
        self._shot("C5-1-window-menu-send-to")
        self._pick("Slack #leads")
        page.locator(f"[id='{MEET}'] [data-testid=send-open] [data-testid=send-preview]").wait_for(timeout=T)
        self._wait(900)
        assert self._db_sends("meeting_summary:m-standup") == []
        self._whole(MEET, "C5-3")
        self._glass("C5-3")
        self._shot("C5-3-picked-preview-in-view")

    def _session(self, width: int, run: Any, *, adjacent: bool = False) -> None:
        from playwright.sync_api import sync_playwright

        self.width, self.phone, self.adjacent = width, width <= 720, 0
        # A short scratch folder: on his desk the face shows ~/Documents/...; pytest's
        # tmp path (/private/var/folders/...) is longer than any real home folder.
        import shutil
        import tempfile

        scratch = Path(tempfile.mkdtemp(prefix="p13c5-", dir="/tmp"))
        folder = scratch / "Team updates"
        folder.mkdir()
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            ctx = browser.new_context(viewport={"width": width, "height": SIZES[width]}, device_scale_factor=1,
                                      has_touch=self.phone, reduced_motion="reduce")
            page = self.page = ctx.new_page()
            page.set_default_timeout(45_000)
            errors: list[str] = []
            page.on("pageerror", lambda e: errors.append(str(e)[:200]))
            try:
                page.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
                _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
                made = _api(page, "POST", "/api/channels/destinations",
                            {"name": "Team updates", "channel": "file", "folder": str(folder)}, token=TOKEN)
                si = self.si = StandIns(page, made["destination"]["id"])
                run(si, folder)
                if adjacent:
                    assert self.adjacent >= (1 if not self.phone else 0), self.adjacent
                assert not [e for e in errors if "ResizeObserver" not in e and "Failed to fetch" not in e], errors
            finally:
                browser.close()
                shutil.rmtree(scratch, ignore_errors=True)

    def _room_second_read_fails(self, si: StandIns) -> None:
        page = self.page
        self._open_surface("open-project-memory", "project:p-ledger", ROOM)
        assert self._send_to(ROOM) == "Send to"           # the menu's read: known, the latest update
        si.set_hold("failed")                              # the Room's own read of that update fails
        self._pick("Team updates")
        fail = page.locator(f"[id='{ROOM}'] [data-testid=room-latest-unreadable]")
        fail.wait_for(timeout=T)
        assert "CANNOT READ LATEST UPDATE" in fail.inner_text(), fail.inner_text()
        assert page.locator(f"[id='{ROOM}'] [data-testid=send-well][data-doc^='project_update:']").count() == 0
        self._wait(600)
        for sel in ("[data-testid=room-latest-unreadable]", "[data-testid=room-latest-unreadable-retry]"):
            box = page.locator(f"[id='{ROOM}'] {sel}").bounding_box()
            assert box and box["y"] >= 0 and box["y"] + box["height"] <= SIZES[self.width], (sel, box)
        self._glass("C5-17a")
        self._shot("C5-17a-room-second-read-fails")
        si.set_hold(None)
        self._tap(page.locator(f"[id='{ROOM}'] [data-testid=room-latest-unreadable-retry]"), 900)
        page.locator(f"[id='{ROOM}'] [data-testid=send-well][data-doc='project_update:upd-ledger-1'] "
                     "[data-testid=send-open] [data-testid=send-preview]").wait_for(timeout=T)
        self._wait(900)
        assert page.locator(f"[id='{ROOM}'] [data-testid=room-latest-unreadable]").count() == 0
        self._glass("C5-17b")
        self._shot("C5-17b-room-second-read-retry")
        assert self._db_sends("project_update:upd-ledger-1") == []


# ══ lane e2e-high-1 ════════════════════════════════════════

H1_TOKEN = "philo11-05a-doc-send"

H1_SHOTS = evidence_dir("pm/roadmap/holdspeak-philo/phase-11-more-documents-on-the-channels/assets/story-05a-proof/shots")

H1_SIZES = {1440: 900, 393: 852}

WIDTHS = list(H1_SIZES)

H1_T = 20_000

PROJECT = "Payments ledger cutover"

REMOTE_HOST = "192.0.2.123"  # TEST-NET-1: never loopback

AGENT_ID = "remote-project-agent"

# PHILO-13-11 (slice two): the Chair is four windows (.chair-window); the
# Intelligence and decision seats are the OTHER windows.
DD = ".desk-window:not(.chair-window) [data-seat=desk-decision]"         # the decision window

# The species' stamp (features/channels/channels.ts `stamp`), in the page's zone.
STAMP_JS = """(iso) => { const M = ["JAN","FEB","MAR","APR","MAY","JUN","JUL","AUG","SEP","OCT","NOV","DEC"];
  const d = new Date(iso); const p = (n) => String(n).padStart(2, "0");
  return `${M[d.getMonth()]} ${d.getDate()} ${p(d.getHours())}:${p(d.getMinutes())}`; }"""

def row(scope: str, name: str) -> str:
    return f"{scope} [data-testid=destination-row]:has([data-destination='{name}'])"

def opened(scope: str, name: str) -> str:
    return f"{scope} [data-testid=send-open][data-destination='{name}']"

WEBHOOK = "https://hooks.slack.com/services/T0P11/B0P11/philo11-05a-synthetic-credential"

SLACK = "Slack #leads"

class _Edge:
    """The recording HTTPS edge: every request is recorded, then answered with Slack's exact `200 ok`."""

    def __init__(self) -> None:
        self.requests: list[dict[str, Any]] = []

    def handler(self) -> Any:
        import http.client
        import io
        import urllib.request
        import urllib.response

        edge = self

        class Recording(urllib.request.BaseHandler):
            def https_open(self, req: Any) -> Any:
                edge.requests.append({"host": req.host, "url": req.full_url, "method": req.get_method(),
                                      "body": bytes(req.data or b"")})
                result = urllib.response.addinfourl(io.BytesIO(b"ok"), http.client.parse_headers(io.BytesIO(b"\r\n")),
                                                    req.full_url, 200)
                result.msg = "recorded"
                return result

        return Recording()

class _Rig:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        _ensure_build()
        self.tmp = tmp_path
        # The People store on a file key in this HOME (no macOS Keychain in an isolated HOME).
        keyfile = tmp_path / "people.key"
        keyfile.write_text("{}")
        keyfile.chmod(0o600)
        monkeypatch.setenv("HOLDSPEAK_PEOPLE_KEYSTORE_FILE", str(keyfile))
        # Slack's transport seams only, in the hub's own process (part B's pattern): a MEMORY
        # key store and a recording HTTPS edge that answers Slack's exact `200 ok`. The kernel
        # admission, the egress child and the real opener run; the OS keychain is never
        # reached (a guard fails the test if it is); nothing leaves the machine.
        import keyring
        from holdspeak.services import channel_slack

        self.keys = channel_slack.MemorySlackKeyStore()
        self.edge = _Edge()
        monkeypatch.setattr(channel_slack, "KEY_STORE", lambda: self.keys)
        monkeypatch.setattr(channel_slack, "HTTPS_HANDLER", self.edge.handler)
        monkeypatch.setattr(keyring, "get_keyring", lambda: (_ for _ in ()).throw(
            AssertionError("the glass reached the real keychain")))
        server, base = _boot(tmp_path, monkeypatch, token=H1_TOKEN)
        park_builtin_folder()  # the desk these boards were drawn on (glass_infra.park_builtin_folder)
        self.server, self.base = server, base
        try:
            yield
        finally:
            server.stop()

    # ── the rig ──────────────────────────────────────────────────────────

    def _open(self, pw: Any, width: int) -> tuple[Any, Any, list[str]]:
        # The wheel moves the page in one step (no smooth-scroll animation under the probe).
        browser = pw.chromium.launch(headless=True, args=["--disable-smooth-scrolling"])
        ctx = browser.new_context(viewport={"width": width, "height": H1_SIZES[width]}, device_scale_factor=1)
        page = ctx.new_page()
        page.set_default_timeout(45_000)
        errors: list[str] = []
        page.on("pageerror", lambda e: errors.append(str(e)[:200]))
        page.goto(f"{self.base}/?token={H1_TOKEN}", wait_until="load")
        _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=H1_TOKEN)
        return browser, page, errors

    def _reload(self, page: Any, chair: str | None = None) -> None:
        page.reload(wait_until="load")
        _normal_chair(page)
        page.wait_for_timeout(1200)
        # PHILO-14 A1 (#939): the Chair is the screen; its windows start closed.
        # The seat under test (Brief, The week) opens by the owner's gesture:
        # Window ▸ Chair ▸ <name> at 1440, Go ▸ <name> at 393.
        if chair:
            open_chair_window(page, chair)
            page.wait_for_timeout(600)
        _settle(page)

    def _dest(self, page: Any, name: str) -> tuple[str, Path]:
        folder = (self.tmp / "Reports" / name.replace(" ", "")).resolve()
        folder.mkdir(parents=True, exist_ok=True)
        did = _api(page, "POST", "/api/channels/destinations",
                   {"name": name, "channel": "file", "folder": str(folder)}, token=H1_TOKEN)["destination"]["id"]
        return did, folder

    @staticmethod
    def _sends(page: Any, ref: str) -> list[dict[str, Any]]:
        return _api(page, "GET", f"/api/channels/sends?document_ref={ref}", token=H1_TOKEN)["sends"]

    @staticmethod
    def _kernel(operation_id: str) -> dict[str, Any]:
        """The kernel's own record of an operation: its row and its ONE terminal receipt."""
        from holdspeak.db import get_database

        with get_database()._connection() as conn:
            row = conn.execute(
                "SELECT o.operation_id, o.name, o.state, o.principal_kind, o.principal_identity, o.target_ref,"
                " r.state AS receipt_state, r.outcome AS receipt_outcome, r.result_ref,"
                " (SELECT COUNT(*) FROM kernel_receipts x WHERE x.operation_id = o.operation_id) AS receipts"
                " FROM kernel_operations o LEFT JOIN kernel_receipts r ON r.operation_id = o.operation_id"
                " WHERE o.operation_id = ?", (operation_id,)).fetchone()
        assert row is not None, operation_id
        return dict(row)

    @staticmethod
    def _kernel_refusals(name: str, outcome: str) -> list[dict[str, Any]]:
        from holdspeak.db import get_database

        with get_database()._connection() as conn:
            return [dict(r) for r in conn.execute(
                "SELECT o.operation_id, o.name, o.state, o.target_ref, r.state AS receipt_state, r.outcome AS receipt_outcome"
                " FROM kernel_operations o JOIN kernel_receipts r ON r.operation_id = o.operation_id"
                " WHERE o.name = ? AND r.outcome = ?", (name, outcome))]

    def _face_row_receipt(self, send: dict[str, Any], ref: str, *, principal: str = "owner") -> dict[str, Any]:
        """face = row = receipt: the hub's send row and the kernel's receipt of its send
        operation agree (sent -> succeeded, the same document, one receipt)."""
        k = self._kernel(send["send_operation_id"])
        assert k["name"] == "channel.send" and k["receipts"] == 1, k
        assert (send["state"], k["state"], k["receipt_state"]) == ("sent", "succeeded", "succeeded"), (send, k)
        assert k["result_ref"] == f"channel_send:{send['id']}", (k, send["id"])
        assert k["target_ref"] in (f"document:{ref}", f"channel_send:{send['id']}"), (k, ref)
        assert k["principal_kind"] == principal, k
        return k

    @staticmethod
    def _slack(page: Any) -> str:
        """A Slack destination through the real routes: the held webhook save, then the destination."""
        key_ref = _api(page, "POST", "/api/channels/slack-webhooks", {"webhook_url": WEBHOOK}, token=H1_TOKEN)["key_ref"]
        return _api(page, "POST", "/api/channels/destinations",
                    {"name": SLACK, "channel": "slack", "key_ref": key_ref, "channel_label": "#leads"},
                    token=H1_TOKEN)["destination"]["id"]

    @staticmethod
    def _focus(page: Any) -> None:
        page.evaluate("window.dispatchEvent(new Event('focus'))")
        page.wait_for_timeout(800)

    @staticmethod
    def _stamp(page: Any, iso: str) -> str:
        return page.evaluate(STAMP_JS, iso)

    def _agent(self) -> Any:
        from starlette.testclient import TestClient

        client = TestClient(self.server.app, client=(REMOTE_HOST, 50000))
        headers = {"Authorization": f"Bearer {H1_TOKEN}"}
        assert client.put("/api/settings/remote", json={"enabled": True}, headers=headers).status_code == 200
        issued = client.post("/api/settings/remote/credentials", json={"identity": AGENT_ID, "palette": "PROJECT"},
                             headers=headers)
        assert issued.status_code == 200, issued.text
        agent = TestClient(self.server.app, client=(REMOTE_HOST, 50001))
        agent.headers.pop("x-holdspeak-token", None)
        agent.headers.update({"Authorization": f"Bearer {issued.json()['token']}"})
        return agent

    @staticmethod
    def _pick(page: Any, scope: str, name: str) -> None:
        if not page.locator(opened(scope, name)).count():
            page.locator(row(scope, name)).first.click()
        page.locator(f"{opened(scope, name)} [data-testid=send-preview], {opened(scope, name)} [data-testid=preview-refused], "
                     f"{opened(scope, name)} [data-testid=preview-failed]").first.wait_for(timeout=H1_T)
        page.wait_for_timeout(400)

    @staticmethod
    def _unpick(page: Any, scope: str, name: str) -> None:
        if page.locator(opened(scope, name)).count():
            page.locator(row(scope, name)).first.click()
            page.locator(opened(scope, name)).wait_for(state="detached", timeout=H1_T)
            page.wait_for_timeout(300)

    @staticmethod
    def _press(page: Any, scope: str, name: str, expect: str = "[data-receipt=latest][data-state=sent]") -> None:
        sel = f"{opened(scope, name)} [data-testid=send-verb]"
        page.wait_for_function("(s) => { const b = document.querySelector(s); return b && !b.disabled; }", arg=sel, timeout=H1_T)
        page.locator(sel).first.click()
        page.locator(f"{opened(scope, name)} {expect}").first.wait_for(timeout=H1_T)
        page.wait_for_timeout(700)

    @staticmethod
    def _text(page: Any, sel: str) -> str:
        return " ".join(page.locator(sel).first.inner_text().split())

    @staticmethod
    def _close_windows(page: Any) -> None:
        for _ in range(6):
            btn = page.locator(".desk-window:not(.chair-window) [aria-label^='Close ']")
            if not btn.count():
                break
            btn.last.click()
            page.wait_for_timeout(500)

    @staticmethod
    def _open_decision(page: Any, title: str, decision_id: str) -> None:
        page.locator("[aria-controls=desk-tool-shelf]").first.click()
        page.locator("[aria-controls=desk-palette-listbox]").fill(title)
        page.locator(f"[id='desk-palette-option-decision:{decision_id}']").click()
        page.locator(f"{DD} [data-testid=send-well]").wait_for(timeout=H1_T)
        page.wait_for_timeout(800)
        _settle(page)

    @staticmethod
    def _open_intelligence(page: Any, tab: str | None = None) -> None:
        page.locator("button.desk-dock-app").first.click()
        page.locator(".desk-window .intelligence-pullout").first.wait_for(timeout=H1_T)
        # PHILO-17: the window opens on Day; the Brief is a tab, and its Send
        # well starts folded (one row; Send opens it).
        page.locator(".intelligence-segment", has_text=tab or "Brief").first.click()
        if not tab:
            page.get_by_test_id("brief-send-toggle").first.click()
        page.wait_for_timeout(900)
        _settle(page)

class TestChairMeetingWells(_Rig):
    # ── C6b: the Chair's MEETINGS rows (both branches) ──

    @pytest.mark.e2e
    @pytest.mark.timeout(900)
    @pytest.mark.parametrize("width", WIDTHS)
    def test_the_chair_meeting_wells(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        from holdspeak.db import get_database
        from holdspeak.meeting_session.models import IntelSnapshot, MeetingState, TranscriptSegment

        shots = Boards(H1_SHOTS, width)
        with sync_playwright() as pw:
            browser, page, errors = self._open(pw, width)
            try:
                db = get_database()
                now = datetime.now().replace(microsecond=0)
                seg = [TranscriptSegment(text="Two write paths still hit the old ledger.", speaker="Me", start_time=4.0, end_time=9.0)]
                # The healthy branch: a recorded meeting with its stored summary.
                db.meetings.save_meeting(MeetingState(
                    id="c6-sync", started_at=now - timedelta(hours=2), ended_at=now - timedelta(hours=1, minutes=15),
                    title="Ledger cutover sync", segments=seg, intel_status="completed",
                    intel=IntelSnapshot(timestamp=0.0, summary="The team agreed to freeze the old ledger on Nov 3.",
                                        topics=["cutover"])))
                # The retained-summary branch: a stored summary, then a re-run that failed (the
                # intel queue's own enqueue -> claim -> fail); the Chair keeps the summary with its
                # status facts.
                db.meetings.save_meeting(MeetingState(
                    id="c6-retry", started_at=now - timedelta(hours=1), ended_at=now - timedelta(minutes=30),
                    title="Vendor escalation", segments=seg, intel_status="completed",
                    intel=IntelSnapshot(timestamp=0.0, summary="The vendor owes a fix for the export by Friday.",
                                        topics=["vendor"])))
                db.intel.enqueue_intel_job("c6-retry", transcript_hash="c6-retry-hash")
                claimed = db.intel.claim_next_intel_job(include_scheduled=True)
                assert claimed is not None and claimed.meeting_id == "c6-retry", claimed
                db.intel.fail_intel_job("c6-retry", "engine answered 500")
                team, team_dir = self._dest(page, "Team folder")
                self._reload(page, "The week")

                ok_row = "li.surface-ledger-row:has(> [data-testid=arrival-meeting-row]):has([data-send=well][data-doc$=':c6-sync'])"
                rt_row = "li.surface-ledger-row:has(> [data-testid=arrival-meeting-row]):has([data-send=well][data-doc$=':c6-retry'])"
                OK = f"{ok_row} [data-seat=meeting]"
                RT = f"{rt_row} [data-seat=meeting]"
                page.locator(f"{OK} [data-testid=destination-row]").first.wait_for(timeout=H1_T)
                page.locator(f"{RT} [data-testid=destination-row]").first.wait_for(timeout=H1_T)
                page.wait_for_timeout(600)

                # PHILO-13-11 (slice two): at 1440 The week is 36 % of the right column;
                # the meeting well is read with the window zoomed (board C1-4b).
                if width > 720:
                    page.get_by_role("button", name="Zoom The week").click()
                    page.wait_for_timeout(600)
                # C6b, the healthy branch: SUMMARY, then SEND with the form picker (44 px at 393).
                picker = f"{OK} [data-testid=doc-forms] select, {OK} [data-testid=doc-forms] .btn"
                c6 = shots.shoot(page, "C6b-chair-meetings-row-well", OK,
                                 [f"{ok_row} .meeting-summary-slab, {ok_row} [data-testid=meeting-summary-text]",
                                  f"{OK} [data-testid=doc-forms]", f"{OK} [data-testid=destination-row]"],
                                 seat=f"{ok_row} [data-testid=arrival-meeting-row]")
                assert "meeting_summary:c6-sync" in c6["wells"], c6["wells"]
                pick_box = page.evaluate("(s) => { const e = document.querySelector(s); const r = e.getBoundingClientRect(); return [r.width, r.height, e.tagName]; }", picker)
                c6["picker_box"] = pick_box
                picker_probe = [o for o in c6["pointer"]["owned"] if o["text"].startswith("Summary") or o["text"] == "Document"]
                c6["picker_owned"] = picker_probe
                assert picker_probe, c6["pointer"]
                if width == 393:
                    # G4 on the Chair: the picker is 44 px tall and owns all nine points of its target.
                    assert pick_box[1] >= 44, pick_box
                    assert all(min(o["target"]) >= 44 for o in picker_probe), picker_probe
                    # PHILO-13-11 (slice two, R2): the old law here scrolled the picker UNDER
                    # the Chair's sticky capture bar and proved the wheel brought it out. The
                    # capture bar is its own window now (on demand from Speak at 393): no bar
                    # floats over The week, so nothing can sit under it. Proven structurally,
                    # and the picker still owns all nine points of its 44 x 44 target.
                    bars_over_week = page.locator(".chair-window--week [data-testid=arrival-capture-bar]").count()
                    owned_nine = page.evaluate("""(sel) => { const p = document.querySelector(sel); p.scrollIntoView({block: 'center'});
                          const r = p.getBoundingClientRect();
                          const cx = r.left + r.width / 2, cy = r.top + r.height / 2, w = Math.max(44, r.width), h = Math.max(44, r.height);
                          const L = cx - w / 2 + 1, R = cx + w / 2 - 1, H1_T = cy - h / 2 + 1, B = cy + h / 2 - 1;
                          return [[cx, cy], [cx, H1_T], [R, cy], [cx, B], [L, cy], [L, H1_T], [R, H1_T], [L, B], [R, B]]
                            .map(([x, y]) => { const e = document.elementFromPoint(x, y); return !!e && p.contains(e); }); }""", picker)
                    c6["picker_after_scroll"] = {"capture_bars_over_the_week": bars_over_week, "nine_points_owned": owned_nine}
                    assert bars_over_week == 0 and all(owned_nine), c6["picker_after_scroll"]
                    shots.shoot(page, "C6f-chair-picker-scrolled-clear-393".replace("-393", ""), OK, [f"{OK} [data-testid=doc-forms]"], seat=None)

                # The send leg from the Chair row: face = hub row = kernel receipt.
                self._pick(page, OK, "Team folder")
                self._press(page, OK, "Team folder")
                mref = "meeting_summary:c6-sync"
                hub = self._sends(page, mref)
                assert [(s["document_ref"], s["state"]) for s in hub] == [(mref, "sent")], hub
                mpath = hub[0]["proof"]["path"]
                assert Path(mpath).parent == team_dir and "freeze the old ledger" in Path(mpath).read_text()
                c6s = shots.shoot(page, "C6c-chair-meetings-row-saved", OK,
                                  [f"{opened(OK, 'Team folder')} [data-receipt=latest]"], block="center")
                assert c6s["receipts"] == [{"text": f"✓ SAVED {mpath}", "state": "sent", "code": None}], c6s["receipts"]
                c6s["kernel_send"] = self._face_row_receipt(hub[0], mref)
                self._unpick(page, OK, "Team folder")

                # C6b, the retained-summary branch: the summary with its status facts, then SEND.
                c6r = shots.shoot(page, "C6e-chair-retained-summary-well", RT,
                                  [f"{rt_row} [data-testid=arrival-summary-status]", f"{RT} [data-testid=doc-forms]",
                                   f"{RT} [data-testid=destination-row]"],
                                  seat=f"{rt_row} [data-testid=arrival-meeting-row]")
                assert "meeting_summary:c6-retry" in c6r["wells"], c6r["wells"]
                assert "FAILED" in self._text(page, f"{rt_row} [data-testid=arrival-summary-status]")

                if width > 720:   # PHILO-13-11: the Chair's screen again (The week un-zoomed)
                    page.get_by_role("button", name="Zoom The week").click()
                    page.wait_for_timeout(400)
                shots.write("chair-meetings-slack", {"hub_sends": {"meeting": hub},
                                                     "edge_requests": len(self.edge.requests)})
                shots.assert_clean()
                assert not errors, errors
            finally:
                browser.close()
