"""PHILO-13-15 (C5) -- `Send to ▸` from any document window, fenced AS RENDERED
through the real hub on an isolated HOME, at 1440 (mouse) and 393 (touch).

Built to the owner's ratified canvas (story-15-canvas, "Ratify, build it",
2026-10-03). Every board of the canvas README is one assert here:

* C5-1 the window menu leads with `Send to ▸`; its rows are `<name> · <CHANNEL>`;
* C5-3 the pick: the window's well, picked, the preview and Send whole in view;
  the hub's DB holds 0 send rows;
* C5-13 a second pick changes the open well in place; C5-14 Summary -> Digest
  keeps the destination;
* C5-4 SENDING, C5-5 a REAL FILE send (SAVED, the file read back from the
  HOME, 1 hub row), C5-6 FAILED, C5-7 UNKNOWN;
* C5-8 withheld (a meeting with no summary); C5-9 `Add destination`;
* C5-2 the Object menu (393: the Object group inside Go) and C5-12 the
  artifact window's own well (no raw <button>);
* C5-10a CHECKING, C5-10b CAN'T CHECK, C5-10c the pick opens the failure with
  Retry, C5-11 Retry (the real read) recovers to the latest published update;
* C5-15 the Chair's Brief window; C5-16a OFFLINE keeps the last rows, C5-16b the
  well says what it cannot read.

Every open menu and well is read by the on-glass reader (zero clipped text,
zero overlaps); every desktop submenu touches its parent panel (3 px or less,
tops overlapping); at 393 every C5 target owns 44 x 44, and every press is a
touch tap and every window menu a CDP long press.

STAND-INS (the canvas's S1/S2/S4, named so no assert claims more than it
shows): `Slack #leads` and `PAY-118` are destinations added to the read by a
Playwright route; their preview is the hub's real render through the FILE
destination; their Send is answered by the route with the outcome the board
names. `none`, `hold` and `offline` are route answers too. NOTHING LEAVES THE
MACHINE. `Team updates` is a REAL FILE destination in the scratch HOME.
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

pytest.importorskip("playwright.sync_api", reason="the send-to glass needs Playwright")

TOKEN = "philo13-15-send-to"
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


class TestSendToGlass:
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

    def _go_object_send_to(self) -> None:
        """393 (C7 Q3, canvas C7-10a/b): Go ▸ Object ▸ Send to ▸ -- two nested levels, each a tap;
        Object leads with Send to; the back row names the level it climbs from.

        Parked: PHILO-15 11 (B21) took Object ▸ out of Go at 393; no leg calls this now."""
        page = self.page
        self._tap(page.locator(".desk-verbbar [data-menu-id=go] button"), 900)
        self._tap(page.locator("[role=menu] [role=menuitem][aria-haspopup=menu]:has-text('Object')").first, 700)
        assert "Object" in page.locator(".desk-menu-back").inner_text()
        first = page.locator("[role=menu] [role^=menuitem]:not(.desk-menu-back)").first.inner_text()
        assert first.startswith("Send to"), first
        self._open_send_to()
        assert "Send to" in page.locator(".desk-menu-back").inner_text()

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

    def _press_send(self, win: str) -> None:
        self._tap(self.page.locator(f"[id='{win}'] [data-testid=send-open] [data-testid=send-verbs] .btn--primary"), 1800)

    # ── the case ─────────────────────────────────────────────────────────

    @pytest.mark.e2e
    @pytest.mark.timeout(900)
    @pytest.mark.parametrize("width", [1440, 393])
    def test_send_to_from_every_document_window(self, width: int) -> None:
        self._session(width, lambda si, folder: self._boards(si, folder), adjacent=True)

    @pytest.mark.e2e
    @pytest.mark.timeout(600)
    @pytest.mark.parametrize("width", [1440, 393])
    def test_room_pick_when_the_update_read_fails(self, width: int) -> None:
        """Astra C5 check, condition 1: the menu's latest-update read succeeds, the Room's own
        read of that update fails. The pick keeps the handoff and shows CANNOT READ LATEST
        UPDATE + Retry in the Room's SEND well; Retry (the real read) recovers to the well."""
        self._session(width, lambda si, folder: self._room_second_read_fails(si))

    @pytest.mark.e2e
    @pytest.mark.timeout(600)
    @pytest.mark.parametrize("width", [1440, 393])
    def test_a_summary_send_keeps_its_receipt_across_a_form_change(self, width: int) -> None:
        """Astra C5 check, condition 2: a REAL FILE send of the summary, its answer held; he
        switches to Digest; the answer is released. The window still shows the summary's result."""
        self._session(width, lambda si, folder: self._form_switch_mid_send(si, folder))

    @pytest.mark.e2e
    @pytest.mark.timeout(600)
    @pytest.mark.parametrize("width", [1440, 393])
    def test_the_same_second_tie_links_the_later_publication(self, width: int) -> None:
        """H-C5 (#752): two publications inside ONE second through the real routes (draft,
        regenerate, publish; then draft, publish). The higher draft revision is the earlier
        insert. The hub names the later insert in `latest_published_update_id`; Send to ▸
        from the Room opens THAT update's well."""
        self._session(width, lambda si, folder: self._same_second_tie(si))

    def _same_second_tie(self, si: StandIns) -> None:
        import holdspeak.db.updates as updates_db

        page = self.page
        instant = (datetime.now() + timedelta(days=1)).replace(microsecond=0).astimezone()

        class _OneSecond:                       # the repository's clock, frozen on one second
            @staticmethod
            def now(tz: Any = None) -> datetime:
                return instant.replace(tzinfo=None) if tz is None else instant.astimezone(tz)

        real_clock = updates_db.datetime
        self.monkeypatch.setattr(updates_db, "datetime", _OneSecond)
        post = lambda path, body=None: _api(page, "POST", path, body or {}, token=TOKEN)["update"]  # noqa: E731
        first = post("/api/projects/p-ledger/updates/draft", {"generator": "deterministic"})
        high = post(f"/api/updates/{first['id']}/regenerate", {"generator": "deterministic"})
        # PHILO-15 B64: an update with no verified claim is refused; the owner's saved line is reviewed.
        mine = {"body_md": "## Progress\n\nThe ledger cutover is on track.\n"}
        _api(page, "PUT", f"/api/updates/{high['id']}", mine, token=TOKEN)
        high = post(f"/api/updates/{high['id']}/publish")
        later = post("/api/projects/p-ledger/updates/draft", {"generator": "deterministic"})
        _api(page, "PUT", f"/api/updates/{later['id']}", mine, token=TOKEN)
        later = post(f"/api/updates/{later['id']}/publish")
        self.monkeypatch.setattr(updates_db, "datetime", real_clock)   # only the clock (undo() would also undo the rig's HOME)
        assert high["published_at"] == later["published_at"], (high["published_at"], later["published_at"])
        assert high["draft_revision"] > later["draft_revision"], (high, later)
        with self.db._connection() as conn:
            rowid = dict(conn.execute("SELECT id, rowid FROM project_updates WHERE id IN (?, ?)", (high["id"], later["id"])).fetchall())
        assert rowid[later["id"]] > rowid[high["id"]], rowid
        read = _api(page, "GET", "/api/projects/p-ledger/updates", token=TOKEN)
        assert read["latest_published_update_id"] == later["id"], read["latest_published_update_id"]

        self._open_surface("open-project-memory", "project:p-ledger", ROOM)
        assert self._send_to(ROOM) == "Send to"
        self._pick("Team updates")
        well = page.locator(f"[id='{ROOM}'] [data-testid=send-well][data-doc='project_update:{later['id']}']")
        well.locator("[data-testid=send-open] [data-testid=send-preview]").wait_for(timeout=T)
        assert page.locator(f"[id='{ROOM}'] [data-testid=send-well][data-doc='project_update:{high['id']}']").count() == 0
        self._wait(900)
        self._glass("C5-19")
        self._shot("C5-19-same-second-tie-later-publication")
        assert self._db_sends(f"project_update:{later['id']}") == []

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
                    assert self.adjacent >= (6 if not self.phone else 0), self.adjacent
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

    def _form_switch_mid_send(self, si: StandIns, folder: Path) -> None:
        page = self.page
        self._open_ref("meeting:m-standup", MEET)
        self._send_to(MEET)
        self._pick("Team updates")
        page.locator(f"[id='{MEET}'] [data-testid=send-open][data-destination='Team updates'] [data-testid=send-preview]").wait_for(timeout=T)
        si.hold_file_answer = True
        self._press_send(MEET)
        for _ in range(100):
            if si.held_answers:
                break
            self._wait(100)
        assert si.held_answers, "the send never reached the hub"
        rows = self._db_sends("meeting_summary:m-standup")
        assert len(rows) == 1 and rows[0]["state"] == "sent", rows      # the hub has sent
        page.locator(f"[id='{MEET}'] [data-testid=doc-forms] select").first.select_option("meeting_digest")
        page.wait_for_function(f"() => document.querySelector(\"[id='{MEET}'] [data-testid=send-well]\")?.dataset.doc === 'meeting_digest:m-standup'", timeout=T)
        si.release()
        receipt = page.locator(f"[id='{MEET}'] [data-testid=send-history] [data-testid=history-row]:has([data-form='meeting_summary'])")
        receipt.first.wait_for(timeout=T)
        text = receipt.first.inner_text()
        assert "Team updates" in text and "SUMMARY" in text and "SAVED" in text, text
        receipt.first.scroll_into_view_if_needed()
        self._wait(400)
        self._glass("C5-18")
        self._shot("C5-18-digest-keeps-summary-receipt")
        assert Path(rows[0]["proof"]["path"]).resolve().parent == folder.resolve()

    def _boards(self, si: StandIns, folder: Path) -> None:
        page = self.page
        # C5-1: the meeting window's menu leads with Send to ▸; the rows are the saved destinations.
        self._open_ref("meeting:m-standup", MEET)
        label = self._send_to(MEET)
        assert label == "Send to", label
        rows = self._rows()
        assert "Team updates · FILE" in rows and "Slack #leads · SLACK" in rows and "PAY-118 · JIRA" in rows, rows
        self._glass("C5-1")
        self._shot("C5-1-window-menu-send-to")
        # C5-3: the pick (gesture 3) -- the well, picked, its preview and Send in view; nothing sent.
        self._pick("Slack #leads")
        page.locator(f"[id='{MEET}'] [data-testid=send-open] [data-testid=send-preview]").wait_for(timeout=T)
        self._wait(900)
        assert self._db_sends("meeting_summary:m-standup") == []
        self._whole(MEET, "C5-3")
        self._glass("C5-3")
        self._shot("C5-3-picked-preview-in-view")
        well = page.locator(f"[id='{MEET}'] [data-testid=send-well]").element_handle()
        # C5-13: a second pick on the open well changes it in place (no remount).
        self._send_to(MEET)
        self._pick("PAY-118")
        page.wait_for_function(f"() => document.querySelector(\"[id='{MEET}'] [data-testid=send-open]\")?.dataset.destination === 'PAY-118'", timeout=T)
        assert self._ev("(w) => w.isConnected", well), "the well remounted"
        self._wait(900)
        self._whole(MEET, "C5-13")
        self._glass("C5-13")
        self._shot("C5-13-second-pick-in-place")
        # C5-14: Summary -> Digest keeps the destination (the native <select>; the state, not the gesture).
        page.locator(f"[id='{MEET}'] [data-testid=doc-forms] select").first.select_option("meeting_digest")
        page.wait_for_function(f"() => document.querySelector(\"[id='{MEET}'] [data-testid=send-well]\")?.dataset.doc === 'meeting_digest:m-standup'", timeout=T)
        page.locator(f"[id='{MEET}'] [data-testid=send-open][data-destination='PAY-118'] [data-testid=send-preview]").wait_for(timeout=T)
        self._whole(MEET, "C5-14")
        self._glass("C5-14")
        self._shot("C5-14-digest-keeps-destination")
        page.locator(f"[id='{MEET}'] [data-testid=doc-forms] select").first.select_option("meeting_summary")
        self._wait(1200)
        # C5-4: SENDING (the stand-in holds its answer).
        self._send_to(MEET)
        self._pick("Slack #leads")
        page.locator(f"[id='{MEET}'] [data-testid=send-open][data-destination='Slack #leads'] [data-testid=send-preview]").wait_for(timeout=T)
        self._press_send(MEET)
        page.locator(f"[id='{MEET}'] [data-testid=send-running]").wait_for(timeout=T)
        assert "SENDING" in page.locator(f"[id='{MEET}'] [data-testid=send-running]").inner_text()
        color = self._ev(f"() => getComputedStyle(document.querySelector(\"[id='{MEET}'] [data-testid=send-running] .surface-state-chip\")).color")
        # Phase 16 (COMPOSITOR §11): inside a window the accent is the kit's ember
        # ink (window-interior.css remaps --accent-text to --wb-ember-ink), so the
        # token is read where the chip is drawn, not at the desk root.
        accent_text = self._ev(f"() => {{ const p = document.createElement('span'); p.style.color = 'var(--accent-text)'; const host = document.querySelector(\"[id='{MEET}'] [data-testid=send-running]\"); host.appendChild(p); const c = getComputedStyle(p).color; p.remove(); return c; }}")
        assert color == accent_text, (color, accent_text)
        self._whole(MEET, "C5-4", field=False)
        self._glass("C5-4")
        self._shot("C5-4-sending")
        # C5-5: a REAL send to the FILE destination: SAVED, the file in the HOME, one hub row.
        self._send_to(MEET)
        self._pick("Team updates")
        page.locator(f"[id='{MEET}'] [data-testid=send-open][data-destination='Team updates'] [data-testid=send-preview]").wait_for(timeout=T)
        assert self._db_sends("meeting_summary:m-standup") == []
        self._press_send(MEET)
        page.locator(f"[id='{MEET}'] [data-testid=send-open] [data-testid=send-sent]").wait_for(timeout=T)
        rows_db = self._db_sends("meeting_summary:m-standup")
        assert len(rows_db) == 1 and rows_db[0]["state"] == "sent", rows_db
        written = Path(rows_db[0]["proof"]["path"])
        assert written.parent.resolve() == folder.resolve() and "freeze the old ledger" in written.read_text().lower(), written
        self._whole(MEET, "C5-5", field=False)
        self._glass("C5-5")
        self._shot("C5-5-sent-file")
        self._escape()
        if self.phone:
            # C7-10a-c: PHILO-15 11 (B21, owner ruling 2026-10-07) took Object ▸ out of
            # Go at 393; Send to ▸ is in the window's own menu there. Send to ▸ PAY-118
            # -> the meeting window's preview, whole on screen.
            self._send_to(MEET)
            self._glass("C7-10b")
            self._shot("C7-10b-window-send-to-rows")
            self._pick("PAY-118")
            page.locator(f"[id='{MEET}'] [data-testid=send-open][data-destination='PAY-118'] [data-testid=send-preview]").wait_for(timeout=T)
            self._wait(900)
            self._whole(MEET, "C7-10c")
            self._glass("C7-10c")
            self._shot("C7-10c-go-send-to-preview")

        # C5-6 FAILED and C5-7 UNKNOWN (decision windows; stand-in answers).
        si.outcome["chd_si_jira"] = "failed"
        self._open_ref("decision:d-freeze", FREEZE)
        self._send_to(FREEZE)
        self._pick("PAY-118")
        page.locator(f"[id='{FREEZE}'] [data-testid=send-open] [data-testid=send-preview]").wait_for(timeout=T)
        self._press_send(FREEZE)
        failed = page.locator(f"[id='{FREEZE}'] [data-testid=send-failed]")
        failed.wait_for(timeout=T)
        assert re.search(r"FAILED.*NOTHING SENT", failed.inner_text().replace("\n", " ")), failed.inner_text()
        self._glass("C5-6")
        self._shot("C5-6-failed")
        si.outcome["chd_si_slack"] = "unknown"
        self._open_ref("decision:d-otel", OTEL)
        self._send_to(OTEL)
        self._pick("Slack #leads")
        page.locator(f"[id='{OTEL}'] [data-testid=send-open] [data-testid=send-preview]").wait_for(timeout=T)
        self._press_send(OTEL)
        unknown = page.locator(f"[id='{OTEL}'] [data-testid=send-unknown]")
        unknown.wait_for(timeout=T)
        assert "UNKNOWN" in unknown.inner_text(), unknown.inner_text()
        self._glass("C5-7")
        self._shot("C5-7-unknown")
        assert self._db_sends("desk_decision:d-freeze") == [] and self._db_sends("desk_decision:d-otel") == []

        # C5-8: a meeting with no summary -- the window menu has no Send to.
        self._open_ref("meeting:m-bare", BARE)
        self._window_menu(BARE)
        self._wait(1500)
        items = [x.strip() for x in page.locator("[role=menu] [role^=menuitem]").all_inner_texts()]
        assert not any(x.startswith("Send to") for x in items), items
        self._glass("C5-8")
        self._shot("C5-8-withheld-no-summary")
        self._escape()

        # C5-2: the Object menu, the same composition from the FRONT window (the artifact).
        self._open_ref("artifact:art-cutover-reqs", ART)
        if self.phone:
            # PHILO-15 11 (B21): no Object ▸ in Go at 393; the window's own menu.
            self._send_to(ART)
        else:
            self._tap(page.locator(".desk-verbbar [data-menu-id=object] button"), 900)
            first = page.locator("[role=menu] [role^=menuitem]").first.inner_text()
            assert first.startswith("Send to"), first
            self._open_send_to()
        assert "Team updates · FILE" in self._rows(), self._rows()
        self._glass("C5-2")
        self._shot("C5-2-object-menu-send-to")
        # C5-12: the artifact window's own well, picked and in view; library Buttons only.
        self._pick("Team updates")
        page.locator(f"[id='{ART}'] [data-testid=send-well][data-doc='artifact:art-cutover-reqs'] [data-testid=send-preview]").wait_for(timeout=T)
        self._wait(900)
        raw = self._ev(f"() => [...document.querySelectorAll(\"[id='{ART}'] button\")].filter((b) => !/(^|\\s)btn(\\s|$|--)/.test(String(b.className))).length")
        assert raw == 0, raw
        self._whole(ART, "C5-12")
        self._glass("C5-12")
        self._shot("C5-12-artifact-window-well")

        # C5-9: no saved destination -- Send to ▸ Add destination.
        si.none = True
        self._open_ref("decision:d-freeze", FREEZE)
        self._send_to(FREEZE)
        page.locator("[role=menu] [role^=menuitem]:has-text('Add destination')").first.wait_for(timeout=T)
        assert self._rows() == ["Add destination"], self._rows()
        self._glass("C5-9")
        self._shot("C5-9-no-destination-add")
        self._escape()
        si.none = False

        # C5-10a/b/c and C5-11: the Room's latest published update.
        si.set_hold("loading")
        self._open_surface("open-project-memory", "project:p-ledger", ROOM)
        assert self._send_to(ROOM) == "Send to · CHECKING"
        self._glass("C5-10a")
        self._shot("C5-10a-room-checking")
        self._escape()
        si.set_hold("failed")
        self._wait(600)
        assert self._send_to(ROOM) == "Send to · CAN'T CHECK"
        assert "Team updates · FILE" in self._rows(), self._rows()
        self._glass("C5-10b")
        self._shot("C5-10b-room-cant-check")
        self._pick("Team updates")
        fail = page.locator(f"[id='{ROOM}'] [data-testid=room-latest-unreadable]")
        fail.wait_for(timeout=T)
        assert "CANNOT READ LATEST UPDATE" in fail.inner_text(), fail.inner_text()
        self._wait(600)
        for sel in ("[data-testid=room-latest-unreadable]", "[data-testid=room-latest-unreadable-retry]"):
            box = page.locator(f"[id='{ROOM}'] {sel}").bounding_box()
            assert box and box["y"] >= 0 and box["y"] + box["height"] <= SIZES[self.width], (sel, box)
        self._glass("C5-10c")
        self._shot("C5-10c-room-pick-opens-failure")
        si.set_hold(None)                     # Retry is the REAL read
        self._tap(page.locator(f"[id='{ROOM}'] [data-testid=room-latest-unreadable-retry]"), 900)
        page.locator(f"[id='{ROOM}'] [data-testid=send-well][data-doc='project_update:upd-ledger-1'] [data-testid=send-open] [data-testid=send-preview]").wait_for(timeout=T)
        self._wait(1200)
        assert page.locator(f"[id='{ROOM}'] [data-testid=room-latest-unreadable]").count() == 0
        w = f"[id='{ROOM}']"
        for sel in (f"{w} li.surface-ledger-row:has([data-testid=send-open]) .surface-primary",
                    f"{w} [data-testid=send-open] [data-testid=send-verbs] .btn--primary"):
            box = page.locator(sel).first.bounding_box()
            assert box and box["y"] >= 0 and box["y"] + box["height"] <= SIZES[self.width], (sel, box)
        self._glass("C5-11")
        self._shot("C5-11-room-retry-recovers")
        assert self._db_sends("project_update:upd-ledger-1") == []

        # C5-15: the Chair's Brief window picks into its own well (the exact brief id).
        page.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
        _normal_chair(page)
        if self.phone:
            page.evaluate("() => { localStorage.setItem('hs.chair.phone', 'chair:brief'); }")
        brief_win = page.locator(f"[id='{BRIEF}']")
        if not (brief_win.count() and brief_win.first.is_visible()):
            self._tap(page.locator(".desk-verbbar [data-menu-id=go] button" if self.phone else ".desk-verbbar [data-menu-id=window] button"), 700)
            if not self.phone:
                page.locator("[role=menu] [role=menuitem][aria-haspopup=menu]:has-text('Chair')").first.hover()
                self._wait(600)
            # PHILO-14 A1 (#939): at 393 the Chair's windows are Go's first rows.
            self._tap(page.locator("[role=menu] [role^=menuitem]:has-text('Brief')").last, 1200)
        brief_win.first.wait_for(state="visible", timeout=T)
        page.locator(f"[id='{BRIEF}'] [data-testid=send-well][data-doc='monday_brief:{self.seed['brief']}']").wait_for(timeout=T)
        self._send_to(BRIEF)
        self._pick("Team updates")
        page.locator(f"[id='{BRIEF}'] [data-testid=send-well][data-doc='monday_brief:{self.seed['brief']}'] [data-testid=send-open] [data-testid=send-preview]").wait_for(timeout=T)
        self._wait(900)
        self._whole(BRIEF, "C5-15")
        self._glass("C5-15")
        self._shot("C5-15-brief-window-picked")

        # C5-16a/b: offline -- the rows are the last read; the well says what it cannot read.
        self._open_ref("decision:d-otel", OTEL)
        self._send_to(OTEL)
        self._escape()
        si.offline = True
        self._wait(300)
        label = self._send_to(OTEL)
        self._wait(900)
        label = self._sub_row().inner_text().replace("»", "").strip() if not self.phone else (
            page.locator(".desk-menu-back").inner_text().replace("◂", "").strip())
        assert label == "Send to · OFFLINE", label
        assert "Team updates · FILE" in self._rows(), self._rows()
        self._glass("C5-16a")
        self._shot("C5-16a-offline-menu")
        self._pick("Team updates")
        page.locator(f"[id='{OTEL}'] [data-testid=sends-unreadable]").wait_for(timeout=T)
        page.locator(f"[id='{OTEL}'] [data-testid=preview-failed]").wait_for(timeout=T)
        assert "CANNOT READ SENDS" in page.locator(f"[id='{OTEL}'] [data-testid=sends-unreadable]").inner_text()
        self._glass("C5-16b")
        self._shot("C5-16b-offline-well")
        si.offline = False
