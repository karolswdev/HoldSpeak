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
import threading
import time
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


@pytest.mark.parametrize("width", list(SIZES))
def test_uncertain_send_reload_keeps_the_exact_command(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int) -> None:
    """A real folder send held BEFORE its durable row: reload must retain Retry.

    The only seam delays validation; the real renderer, admission, dispatch,
    receipts and filesystem run unchanged. A baseline run still presses the
    available Send after reload, so its two files establish the actual cost.
    """
    from playwright.sync_api import sync_playwright
    from holdspeak.db import get_database
    from holdspeak.services.channel_contract import FileChannel

    _ensure_build()
    server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
    db = get_database()
    entered, release = threading.Event(), threading.Event()
    real_check = FileChannel.check_before_dispatch
    checked = 0

    def held_check(channel: Any, target: Any, **kwargs: Any) -> str:
        nonlocal checked
        checked += 1
        if checked == 1:
            entered.set()
            assert release.wait(25), "the browser did not release its held validation"
        return real_check(channel, target, **kwargs)

    monkeypatch.setattr(FileChannel, "check_before_dispatch", held_check)
    shots = evidence_dir("docs/internal/TONIGHT-THREE-2026-10-17/send-reload")
    shots.mkdir(parents=True, exist_ok=True)
    submitted: list[dict[str, Any]] = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": width, "height": SIZES[width]})
        page.set_default_timeout(T)
        page.on("request", lambda r: submitted.append(r.post_data_json)
                if r.method == "POST" and r.url.endswith("/api/channels/send") else None)
        try:
            page.goto(f"{base}/?token={TOKEN}", wait_until="load")
            _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
            made = _api(page, "POST", "/api/thoughts", {
                "request_id": str(uuid.uuid4()), "raw_text": "The exact saved report stays here.", "source": {"kind": "typed"},
                "initial_note": {"title": "One report after reload", "body_markdown": "The exact saved report stays here.", "tags": []},
            }, token=TOKEN)
            ref = f"note:{made['thought']['working_note']['id']}"
            page.goto(f"{base}/?open={ref}", wait_until="load")
            _normal_chair(page)

            def open_send() -> Any:
                win = page.locator(".thought-workspace-window").first
                win.locator(".thought-note-body .cm-content").wait_for()
                # Q8 keeps Send… directly in the note footer at both sizes.
                # The Send well's own Send/Retry still owns dispatch.
                win.locator(".thought-note-foot").get_by_role("button", name="Send…", exact=True).click()
                well = win.locator("[data-testid=send-well]")
                well.locator("[data-testid=send-preview-body]").wait_for()
                return well

            well = open_send()
            original = well.locator("[data-testid=send-preview-body]").inner_text()
            well.locator("[data-testid=send-verb]").click()
            assert entered.wait(5), "the first request never reached pre-boundary validation"
            assert db.channel_sends.list_for_document(ref) == []
            page.reload(wait_until="load")
            # The current note keeps a later draft/save. Retry still belongs to
            # the first frozen press and must not send these newer words.
            draft = "The updated draft is kept after reload."
            editor = page.locator(".thought-note-body .cm-content").first
            editor.wait_for()
            editor.click()
            page.keyboard.press("ControlOrMeta+A")
            page.keyboard.type(draft)
            well = open_send()
            restored = well.locator("[data-testid=send-preview-body]").inner_text()
            retry = well.locator("[data-testid=send-retry]")
            retained = retry.count() == 1
            page.screenshot(path=str(shots / f"reload-{width}.png"))
            # Press the actual control in both versions; do not manufacture a
            # second command or claim a duplicate from source alone.
            (retry if retained else well.locator("[data-testid=send-verb]")).click()
            release.set()
            page.wait_for_function("""() => document.querySelector('[data-testid=send-sent]') !== null""")
            page.wait_for_timeout(600)
            rows = db.channel_sends.list_for_document(ref)
            with db._connection() as conn:
                operations = [dict(row) for row in conn.execute(
                    "SELECT operation_id,state FROM kernel_operations WHERE name='channel.send'")]
            files = [Path(row["file_path"]) for row in rows]
            facts = {"retained": retained, "submitted": submitted, "original": original, "restored": restored, "draft": draft,
                     "sends": [{"id": row["id"], "state": row["state"]} for row in rows], "operations": operations,
                     "files": [{"path": str(path), "text": path.read_text()} for path in files]}
            (shots / f"facts-{width}.json").write_text(json.dumps(facts, indent=2) + "\n")
            page.screenshot(path=str(shots / f"settled-{width}.png"))
            assert retained, facts
            assert submitted[0] == submitted[1], facts
            assert restored == original, facts
            assert len(rows) == len(operations) == len(files) == 1, facts
            assert rows[0]["state"] == "sent" and operations[0]["state"] == "succeeded", facts
            assert files[0].read_bytes() == bytes(rows[0]["payload"]), facts
            # Back restores the same saved document, rather than an empty editor.
            page.locator(".thought-send-foot").get_by_role("button", name="Back", exact=True).click()
            assert draft == page.locator(".thought-note-body .cm-content").inner_text()
            (shots / f"return-{width}.png").write_bytes(page.screenshot())
        finally:
            release.set()
            browser.close()
            server.stop()

MEET = "surface-meetings"  # the saved record is inside Meetings, with Back
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
        self.project_id: str | None = None
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
        if self.project_id and path.startswith(f"/api/projects/{self.project_id}/updates") and req.method == "GET" and self.hold:
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

    def _face_row_receipt(self, send: dict[str, Any], ref: str) -> dict[str, Any]:
        """Prove the real face, channel row, and kernel receipt agree once."""
        with self.db._connection() as conn:
            row = conn.execute(
                "SELECT o.operation_id, o.name, o.state, o.target_ref, "
                "r.state AS receipt_state, r.outcome AS receipt_outcome, r.result_ref, "
                "(SELECT COUNT(*) FROM kernel_receipts x WHERE x.operation_id = o.operation_id) AS receipts "
                "FROM kernel_operations o LEFT JOIN kernel_receipts r ON r.operation_id = o.operation_id "
                "WHERE o.operation_id = ?",
                (send["send_operation_id"],),
            ).fetchone()
        assert row is not None, send["send_operation_id"]
        receipt = dict(row)
        assert receipt["name"] == "channel.send" and receipt["receipts"] == 1, receipt
        assert (send["state"], receipt["state"], receipt["receipt_state"]) == ("sent", "succeeded", "succeeded"), (send, receipt)
        assert receipt["result_ref"] == f"channel_send:{send['id']}", (receipt, send["id"])
        assert receipt["target_ref"] in (f"document:{ref}", f"channel_send:{send['id']}"), (receipt, ref)
        return receipt

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
        self.page.locator(".desk-work-menu[role=menu]").first.wait_for(timeout=10_000)

    def _sub_row(self) -> Any:
        return self.page.locator(".desk-work-menu[role=menu] [role=menuitem][aria-haspopup=menu]:has-text('Send to')").first

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
        first = self.page.locator(".desk-work-menu[role=menu] [role^=menuitem]").first.inner_text()
        assert first.startswith("Send to"), first
        return self._open_send_to()

    def _rows(self) -> list[str]:
        sel = ".desk-work-menu[role=menu].desk-work-submenu [role^=menuitem]" if not self.phone else ".desk-work-menu[role=menu] [role^=menuitem]:not(.desk-menu-back)"
        return [x.strip() for x in self.page.locator(sel).all_inner_texts()]

    def _pick(self, text: str) -> None:
        self._tap(self.page.locator(f".desk-work-menu[role=menu] [role^=menuitem]:has-text('{text}')").last, 900)

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
        for sel in (".desk-work-menu[role=menu]", "[data-testid=send-well]"):
            f = _rendered_text_faults(self.page, sel, on_glass=True)
            assert not f["clipped"] and not f["overlaps"], f"{board}-{self.width} {sel}: {f}"
        if self.phone:
            small = self._ev(TARGETS44)
            if small:
                # A scrolled control can be behind its own sticky host bar.
                # The shared pointer rig must reach it by an ordinary wheel
                # and then prove all nine points; unrelated misses stay red.
                from ._doc_send_glass import pointer_pass

                recovery = pointer_pass(self.page, self.width, "[data-testid=send-well]")
                assert not recovery["missed"], recovery
                reached = {item["text"] for item in recovery["reached_by_scroll"]}
                small = [item for item in small if item["name"] not in reached]
                (SHOTS / f"{board}-scroll-targets-{self.width}.json").write_text(json.dumps(recovery, indent=2) + "\n")
            if small:
                self._shot(f"{board}-target-failure")
                owners = self._ev("""() => [...document.querySelectorAll('[data-testid=send-add-destination]')].map(e => {
                    const r=e.getBoundingClientRect(), h=document.elementFromPoint(r.left+r.width/2,r.top+r.height/2);
                    return {rect:{x:r.x,y:r.y,w:r.width,h:r.height},owner:h?.outerHTML.slice(0,1200),
                        ancestors:[...function*(e){while(e){yield e;e=e.parentElement}}(e)].slice(0,8).map(a=>({class:a.className,overflow:getComputedStyle(a).overflowY,position:getComputedStyle(a).position}))};
                })""")
                print("Send target owners:", owners)
            assert not small, f"{board}-393 targets under 44 x 44: {small}"

    def _whole(self, win: str, board: str, *, field: bool = True) -> None:
        """The arrival: the window name, the picked row, the preview's first field and Send, each WHOLE on screen."""
        w = f"[id='{win}']"
        sels = [".desk-screen-name" if self.phone else f"{w} > .desk-pullout-head .desk-pullout-title",
                f"{w} li.send-destination-item:has([data-testid=send-open]) .surface-primary"]
        if field:
            sels += [f"{w} [data-testid=send-open] [data-testid=send-preview-field] dd",
                     f"{w} [data-testid=send-verbs] .btn--primary"]
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
        self._session(width, lambda si, folder: self._room_second_read_fails(si, folder))

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

    def _real_session(self, width: int, run: Any) -> None:
        """Run a Send sheet case against the private Hub without route stand-ins."""
        from playwright.sync_api import sync_playwright
        import shutil
        import tempfile

        scratch = Path(tempfile.mkdtemp(prefix="s5-s6-real-", dir="/tmp"))
        folder = scratch / "Team updates"
        folder.mkdir()
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True, args=["--disable-smooth-scrolling"])
            ctx = browser.new_context(viewport={"width": width, "height": SIZES[width]}, device_scale_factor=1,
                                      has_touch=width <= 720, reduced_motion="reduce")
            page = ctx.new_page()
            self.page = page
            self.width = width
            self.phone = width <= 720
            page.set_default_timeout(T)
            errors: list[str] = []
            page.on("pageerror", lambda e: errors.append(str(e)[:200]))
            try:
                page.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
                _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
                _api(page, "POST", "/api/channels/destinations",
                     {"name": "Team updates", "channel": "file", "folder": str(folder)}, token=TOKEN)
                run(page, folder)
                assert not [e for e in errors if "ResizeObserver" not in e and "Failed to fetch" not in e], errors
            finally:
                browser.close()
        shutil.rmtree(scratch, ignore_errors=True)

    def _probe_send_button(self, page: Any, selector: str, *, require_visible: bool = True) -> dict[str, Any]:
        """Record viewport geometry and nine real pointer hits for one Send verb."""
        result = page.evaluate(
            """(sel) => {
              const target = document.querySelector(sel);
              if (!target) return {error: 'missing'};
              const r = target.getBoundingClientRect();
              const cx = r.left + r.width / 2, cy = r.top + r.height / 2;
              const wide = innerWidth > 420;
              const xs = wide ? [r.left + 2, cx, r.right - 2] : [cx - 20, cx, cx + 20];
              const ys = wide ? [r.top + 2, cy, r.bottom - 2] : [cy - 20, cy, cy + 20];
              const points = xs.flatMap(x => ys.map(y => [x, y]));
              const hits = points.map(([x, y]) => {
                const hit = document.elementFromPoint(x, y);
                return Boolean(hit && (hit === target || target.contains(hit)));
              });
              return {rect: {x: r.x, y: r.y, width: r.width, height: r.height},
                viewport: {width: innerWidth, height: innerHeight}, hits,
                visible: r.left >= 0 && r.top >= 0 && r.right <= innerWidth && r.bottom <= innerHeight};
            }""",
            selector,
        )
        assert result.get("error") is None, result
        if require_visible:
            assert result["visible"], result
        # The painted dense face is 28 px at the wide desk, so sample its own
        # inset rect there. On the narrow device retain the 44 px halo points
        # that the library Button promises. Both faces must hit at all nine
        # sampled points.
        assert all(result["hits"]), result
        return result

    @pytest.mark.e2e
    @pytest.mark.timeout(900)
    @pytest.mark.parametrize("width", [1440, 393])
    def test_s5_s6_real_send_sheet_note_edit_and_receipts(self, width: int) -> None:
        """S5/S6: real meeting and note sends use one sheet and exact file bytes."""
        self._real_session(width, lambda page, folder: self._s5_s6_real(page, folder, width))

    def _s5_s6_real(self, page: Any, folder: Path, width: int) -> None:
        meeting_ref = "meeting_summary:m-standup"
        meeting = page.locator(f"[id='{MEET}']")
        self._open_ref("meeting:m-standup", MEET)
        opening = meeting.locator("[data-testid=meeting-send]")
        opening.wait_for()
        opening.click()
        sheet = meeting.locator("[data-testid=send-sheet]")
        sheet.wait_for()
        team = meeting.locator("[data-testid=destination-row]:has([data-destination='Team updates'])")
        team.wait_for()

        inline_folder = folder.parent / "Inline destination"
        inline_folder.mkdir()
        sheet.locator("[data-testid=send-add-destination]").click()
        form = sheet.locator("[data-testid=dest-form]")
        form.wait_for()
        form.locator("[data-testid=dest-name]").fill("Inline destination")
        form.locator("[data-testid=dest-folder]").fill(str(inline_folder))
        form.locator("[data-testid=dest-save]").click()
        inline = meeting.locator("[data-testid=destination-row]:has([data-destination='Inline destination'])")
        inline.wait_for()
        assert inline.locator("[aria-pressed='true']").count() == 1
        assert inline.locator("[data-testid=send-open]").count() == 1

        team.locator(".send-destination-chip").click()
        opened_team = meeting.locator("[data-testid=send-open][data-destination='Team updates']")
        opened_team.locator("[data-testid=send-preview]").wait_for()
        send_selector = f"[id='{MEET}'] [data-testid=send-verbs] [data-testid=send-verb]"
        send = page.locator(send_selector)
        send.wait_for()
        geometry = self._probe_send_button(page, send_selector)
        preview_text = opened_team.locator("[data-testid=send-preview-body]").inner_text()
        page.screenshot(path=str(SHOTS / f"S5-meeting-ready-{width}.png"))
        send.click()
        try:
            # SurfaceFooter portals the receipt to the window foot, outside
            # the destination's send-open body.
            page.locator(f"[id='{MEET}'] [data-testid=send-sent]").wait_for(timeout=T)
        except Exception as exc:  # noqa: BLE001 - preserve the real face state
            state = page.locator(
                f"[id='{MEET}'] [data-testid^=send-][data-receipt='latest'],"
                f"[id='{MEET}'] [data-testid=send-lost],"
                f"[id='{MEET}'] [data-testid=send-refused]"
            ).all_inner_texts()
            raise AssertionError({"ui_state": state, "well": opened_team.inner_text(), "db": self.db.channel_sends.list_for_document(meeting_ref)}) from exc
        rows = self.db.channel_sends.list_for_document(meeting_ref)
        assert len(rows) == 1, rows
        meeting_row = rows[0]
        proof = json.loads(meeting_row["proof_json"] or "{}")
        meeting_path = Path(proof["path"])
        meeting_bytes = bytes(meeting_row["payload"])
        assert meeting_path.parent.resolve() == folder.resolve()
        assert meeting_path.read_bytes() == meeting_bytes
        self._face_row_receipt(meeting_row, meeting_ref)

        page.screenshot(path=str(SHOTS / f"S5-meeting-sent-{width}.png"))
        page.locator(f"[id='{MEET}'] [data-testid=send-back]").click()
        page.wait_for_function(
            """() => {
              const button = document.querySelector("[data-testid='meeting-send']");
              return button && document.activeElement === button;
            }""",
            timeout=T,
        )
        assert page.locator(f"[id='{MEET}'] [data-testid=meeting-send]").count() == 1

        # Edit from the frozen meeting preview. The real POST creates the note;
        # the ordinary note editor owns the text change before Send reads it.
        page.locator(f"[id='{MEET}'] [data-testid=meeting-send]").click()
        sheet = meeting.locator("[data-testid=send-sheet]")
        sheet.wait_for()
        team = meeting.locator("[data-testid=destination-row]:has([data-destination='Team updates'])")
        opened_team = meeting.locator("[data-testid=send-open][data-destination='Team updates']")
        # The restored selected chip is the product's authority. Wait for its
        # own well-read state; a second click would hide a real remount defect.
        try:
            team.locator("[aria-pressed='true']").wait_for(timeout=T)
        except Exception as exc:  # noqa: BLE001 - retain the real seam state
            hit = page.evaluate(
                """(sel) => {
                  const target = document.querySelector(sel);
                  if (!target) return {missing: true};
                  const r = target.getBoundingClientRect();
                  const x = r.left + r.width / 2, y = r.top + r.height / 2;
                  const top = document.elementFromPoint(x, y);
                  return {rect: {x: r.x, y: r.y, width: r.width, height: r.height},
                    point: {x, y}, top: top ? {tag: top.tagName, cls: String(top.className || ""), text: (top.textContent || "").trim().slice(0, 80)} : null,
                    owns: Boolean(top && (top === target || target.contains(top)))};
                }""",
                f"[id='{MEET}'] [data-destination='Team updates']",
            )
            raise AssertionError({
                "selected": team.locator("[aria-pressed='true']").count(),
                "chip": team.locator(".send-destination-chip").get_attribute("aria-pressed"),
                "chip_box": team.locator(".send-destination-chip").bounding_box(),
                "hit": hit,
                "workspace": page.evaluate("() => localStorage.getItem('hs.desk.workspace.v1')"),
                "rows": meeting.locator("[data-testid=destination-row]").all_inner_texts(),
            }) from exc
        try:
            opened_team.locator("[data-testid=send-preview]").wait_for(timeout=T)
        except Exception as exc:  # noqa: BLE001 - retain the real seam state
            destinations = _api(page, "GET", "/api/channels/destinations", token=TOKEN)
            raise AssertionError({
                "selected": team.locator("[aria-pressed='true']").count(),
                "open": opened_team.count(),
                "rows": meeting.locator("[data-testid=destination-row]").all_inner_texts(),
                "destinations": destinations,
            }) from exc
        with page.expect_response(lambda response: response.request.method == "POST" and response.url.endswith("/api/notes"), timeout=T) as note_response:
            opened_team.locator("[data-testid=send-edit]").click()
        made = note_response.value.json()
        note = made["note"]
        note_id = str(note["id"])
        assert note["title"] == "Ledger cutover sync summary (to send)", note
        note_win = page.locator(f"[id='pullout:note:{note_id}']")
        note_win.locator("[data-testid=send-sheet]").wait_for(timeout=T)
        assert note_win.locator(".desk-pullout-title").inner_text().startswith("Ledger cutover sync summary (to send)"), note

        note_win.locator("[data-testid=send-back]").click()
        editor = note_win.locator(".thought-note-body .cm-content")
        editor.wait_for(timeout=T)
        edited = "## Summary\n\nThe edited line is ready for the team."
        editor.click()
        page.keyboard.press("ControlOrMeta+A")
        page.keyboard.type(edited)
        deadline = time.monotonic() + 20
        while time.monotonic() < deadline:
            stored_note = _api(page, "GET", f"/api/notes/{note_id}", token=TOKEN)["note"]
            if stored_note["body_markdown"] == edited:
                break
            page.wait_for_timeout(300)
        stored_note = _api(page, "GET", f"/api/notes/{note_id}", token=TOKEN)["note"]
        assert stored_note["body_markdown"] == edited, stored_note

        note_win.get_by_role("button", name="Send…", exact=True).click()
        note_sheet = note_win.locator("[data-testid=send-sheet]")
        note_sheet.wait_for(timeout=T)
        note_open = note_win.locator("[data-testid=send-open][data-destination='Team updates']")
        note_open.locator("[data-testid=send-preview]").wait_for(timeout=T)
        assert "The edited line is ready for the team." in note_open.locator("[data-testid=send-preview-body]").inner_text()
        note_send_selector = f"[id='pullout:note:{note_id}'] [data-testid=send-verbs] [data-testid=send-verb]"
        note_send = page.locator(note_send_selector)
        note_send.wait_for()
        note_geometry = self._probe_send_button(page, note_send_selector, require_visible=False)
        note_send.click()
        page.locator(f"[id='pullout:note:{note_id}'] [data-testid=send-sent]").wait_for(timeout=T)
        note_ref = f"note:{note_id}"
        note_rows = self.db.channel_sends.list_for_document(note_ref)
        assert len(note_rows) == 1, note_rows
        note_row = note_rows[0]
        note_proof = json.loads(note_row["proof_json"] or "{}")
        note_path = Path(note_proof["path"])
        assert note_path.parent.resolve() == folder.resolve()
        expected_note_bytes = f"# {note['title']}\n\n{edited}\n".encode()
        assert bytes(note_row["payload"]) == expected_note_bytes
        assert note_path.read_bytes() == expected_note_bytes
        self._face_row_receipt(note_row, note_ref)

        # The original meeting source stays frozen and its own bytes remain unchanged.
        assert bytes(self.db.channel_sends.get(meeting_row["id"])["payload"]) == meeting_bytes

        # A fresh desk reads the durable row back into the shared Sent list.  The
        # row must be the same native send (one receipt), rather than a transient
        # face-only acknowledgement from the first window.
        # On the phone the window chrome's Back while the send face is open
        # returns to the ordinary note editor; the same chrome button then
        # closes that real note window before the reload read.
        note_win.locator("[data-testid=send-back]").click()
        note_win.locator(".desk-gadget-close").click()
        note_win.wait_for(state="detached", timeout=T)
        page.reload(wait_until="load")
        _normal_chair(page)
        meeting = page.locator(f"[id='{MEET}']")
        meeting.wait_for(timeout=T)
        meeting.locator("[data-testid=meeting-send]").click()
        reloaded_history = meeting.locator("[data-testid=send-history]")
        reloaded_history.wait_for(timeout=T)
        reloaded_rows = reloaded_history.locator("[data-testid=history-row]")
        assert reloaded_rows.count() == 1
        reloaded_text = reloaded_rows.first.inner_text()
        assert "Team updates" in reloaded_text and "SAVED" in reloaded_text, reloaded_text
        assert meeting.locator("[data-testid=send-history] [data-testid=history-word]").count() == 1
        page.screenshot(path=str(SHOTS / f"S5-history-reloaded-{width}.png"))
        facts = {
            "width": width, "meeting_ref": meeting_ref, "note_ref": note_ref,
            "meeting_preview": preview_text, "meeting_send": {"id": meeting_row["id"], "path": str(meeting_path), "bytes": meeting_bytes.decode()},
            "note": {"id": note_id, "title": note["title"], "edited": edited,
                     "send": {"id": note_row["id"], "path": str(note_path), "bytes": bytes(note_row["payload"]).decode(),
                              "expected_rendered_bytes": expected_note_bytes.decode()}},
            "geometry": {"meeting": geometry, "note": note_geometry},
            "inline_destination": {"folder": str(inline_folder), "selected": True},
            "reload_sent": {"rows": reloaded_rows.count(), "text": reloaded_text},
        }
        (SHOTS / f"S5-S6-facts-{width}.json").write_text(json.dumps(facts, indent=2) + "\n")
        page.screenshot(path=str(SHOTS / f"S6-note-sent-{width}.png"))

    def _room_second_read_fails(self, si: StandIns, folder: Path) -> None:
        page = self.page
        preview_wires: list[dict[str, Any]] = []

        def capture_preview(response: Any) -> None:
            if response.request.method != "POST" or "/api/channels/preview" not in response.url:
                return
            try:
                answer = response.json()
            except Exception:  # noqa: BLE001
                return
            if isinstance(answer, dict):
                preview_wires.append(answer)

        page.on("response", capture_preview)
        # Use the real update producer with an untouched model claim so this
        # existing Room handoff case exercises Send S8 at both canvas sizes
        # without inventing a hub fixture.
        from holdspeak.principals import Principal, PrincipalKind
        from holdspeak.services.project_service import ProjectService
        from holdspeak.services.project_update_service import ProjectUpdateService

        project_id = "p-send-s8"
        self.db.projects.create_project(project_id=project_id, name="Unchecked delivery")
        updates = ProjectUpdateService(self.db, project_service=ProjectService(self.db))
        owner = Principal(PrincipalKind.OWNER, "karol")
        model_body = "## Progress\n\n- **[UNVERIFIED]** The rollout is complete.\n"
        model_claims = json.dumps([{
            "span_id": "s_progress_0", "text": "The rollout is complete.",
            "refs": [], "section": "progress", "kind": "inference",
            "support": "unknown", "acceptance": "unreviewed", "verified": False,
        }])

        def model(_service: Any, _principal: Any, _det_claims: Any, _det_sections: Any,
                  _det_body_md: Any, known_names: Any = (), memory: Any = None) -> tuple[str, str, str, str, str]:
            return model_body, model_claims, "model:browser_s8", "192.0.2.123:8080", "s8-test-model"

        self.monkeypatch.setattr(ProjectUpdateService, "_draft_with_model", model)
        draft = updates.draft_update(owner, project_id, generator="model")
        updates.publish_update(owner, draft["id"])
        update_ref = f"project_update:{draft['id']}"
        from holdspeak.services.channel_contract import render_update
        rendered = render_update(self.db, draft["id"])
        assert rendered.preview_warning == "Not checked yet: no claim in this update was accepted", {
            "body": rendered.body_md, "claims": self.db.project_updates.get_update(draft["id"])["claims_json"],
        }
        si.project_id = project_id

        self._open_surface("open-project-memory", f"project:{project_id}", ROOM)
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
        page.locator(f"[id='{ROOM}'] [data-testid=send-well][data-doc='{update_ref}'] "
                     "[data-testid=send-open] [data-testid=send-preview]").wait_for(timeout=T)
        self._wait(900)
        assert page.locator(f"[id='{ROOM}'] [data-testid=room-latest-unreadable]").count() == 0
        self._glass("C5-17b")
        self._shot("C5-17b-room-second-read-retry")

        # S8: the published unchecked words remain in the frozen preview, the
        # warning is visible above them, and the owner's actual press sends to
        # the private FILE folder and leaves a saved receipt in the hub DB.
        well = page.locator(f"[id='{ROOM}'] [data-testid=send-well][data-doc='{update_ref}']")
        warning = "Not checked yet: no claim in this update was accepted"
        assert any((answer.get("preview") or {}).get("warning") == warning for answer in preview_wires), json.dumps(preview_wires, indent=2)
        fields = well.locator("[data-testid=send-preview-field]").all_inner_texts()
        assert any(warning in field for field in fields), fields
        preview_text = well.locator("[data-testid=send-preview-body]").inner_text()
        assert "The rollout is complete." in preview_text
        send = well.locator("[data-testid=send-verb]")
        assert send.is_enabled()
        self._shot("S8-unchecked-preview")
        send.click()
        sent = well.locator("[data-testid=send-sent]")
        sent.wait_for(timeout=T)
        self._wait(600)
        rows = self._db_sends(update_ref)
        assert len(rows) == 1 and rows[0]["state"] == "sent", rows
        assert rows[0]["proof"]["unchecked"] is True
        assert rows[0]["proof"]["warning"] == warning
        path = Path(rows[0]["proof"]["path"])
        assert path.parent.resolve() == folder.resolve() and path.read_text().endswith("The rollout is complete.\n"), path
        (SHOTS / f"S8-unchecked-facts-{self.width}.json").write_text(json.dumps({
            "width": self.width, "document_ref": update_ref, "warning": warning,
            "preview": preview_text, "receipt": rows[0], "path": str(path),
            "file": path.read_text(),
        }, indent=2) + "\n")
        self._shot("S8-unchecked-sent")


# ══ lane e2e-high-1 ════════════════════════════════════════

H1_TOKEN = "philo11-05a-doc-send"

H1_SHOTS = evidence_dir("pm/roadmap/holdspeak-philo/phase-11-more-documents-on-the-channels/assets/story-05a-proof/shots")

# Send S3: the owner-facing Needs row is a separate face from the Send well,
# but it uses the same private Hub row, frozen preview and owner press.
S3_SHOTS = evidence_dir("docs/internal/TONIGHT-THREE-2026-10-20/send-s3")

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
        if chair == "The week":
            self._raise_week(page, page.viewport_size["width"], fresh=True)
        elif chair:
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

    def _agent(self, *, palette: str = "PROJECT", identity: str = AGENT_ID) -> Any:
        from starlette.testclient import TestClient

        client = TestClient(self.server.app, client=(REMOTE_HOST, 50000))
        headers = {"Authorization": f"Bearer {H1_TOKEN}"}
        assert client.put("/api/settings/remote", json={"enabled": True}, headers=headers).status_code == 200
        issued = client.post("/api/settings/remote/credentials", json={"identity": identity, "palette": palette},
                             headers=headers)
        assert issued.status_code == 200, issued.text
        agent = TestClient(self.server.app, client=(REMOTE_HOST, 50001))
        agent.headers.pop("x-holdspeak-token", None)
        agent.headers.update({"Authorization": f"Bearer {issued.json()['token']}"})
        return agent

    def _prepare_agent(self, document_ref: str, destination_id: str) -> tuple[Any, dict[str, Any]]:
        """Use the existing admitted agent MCP path; channel.prepare never sends."""
        from tests.unit.test_philo9_steward_admission import _tool

        agent = self._agent()
        is_error, answer = _tool(agent, "channel.prepare", {
            "document_ref": document_ref, "destination_id": destination_id,
        })
        assert is_error is False, answer
        send = answer["send"]
        assert send["state"] == "prepared"
        assert send["prepared_by"] == {"kind": "agent", "identity": AGENT_ID}
        return agent, answer

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
        # Betterment D4: Today is one page; the brief is its Since-yesterday
        # fold, and its Send well starts folded (one row; Send opens it).
        page.get_by_test_id("today-since-toggle").first.click()
        if not tab:
            page.get_by_test_id("brief-send-toggle").first.click()
        page.wait_for_timeout(900)
        _settle(page)


class TestSendNeedsGlass(_Rig):
    """S3's real browser leg reuses the prepared-send rig above."""

    pass

    @pytest.mark.e2e
    @pytest.mark.timeout(600)
    @pytest.mark.chair_windows_open
    @pytest.mark.parametrize("width", WIDTHS)
    def test_saved_unknown_needs_retry_replays_the_original_operation(self, monkeypatch: pytest.MonkeyPatch, width: int) -> None:
        """A settled UNKNOWN survives reload and Try again never dispatches twice."""
        from playwright.sync_api import sync_playwright
        from holdspeak.services.channel_contract import FileChannel, Outcome
        from tests.unit.test_philo9_steward_admission import _tool

        calls = 0

        def unknown_dispatch(*_args: Any, **_kwargs: Any) -> Outcome:
            nonlocal calls
            calls += 1
            return Outcome("unknown", "timeout")

        monkeypatch.setattr(FileChannel, "dispatch", unknown_dispatch)
        with sync_playwright() as pw:
            browser, page, errors = self._open(pw, width)
            try:
                _normal_chair(page)
                project = _api(page, "POST", "/api/projects", {"name": "S3 browser unknown delivery"}, token=H1_TOKEN)
                project_id = project["project"]["id"]
                update = _api(page, "POST", f"/api/projects/{project_id}/updates/draft", {}, token=H1_TOKEN)
                update_id = update["update"]["id"]
                _api(page, "PUT", f"/api/updates/{update_id}", {
                    "body_md": "## Progress\n\nThe unknown browser proof keeps one operation.\n",
                }, token=H1_TOKEN)
                _api(page, "POST", f"/api/updates/{update_id}/publish", {}, token=H1_TOKEN)
                document_ref = f"project_update:{update_id}"
                destination_id, folder = self._dest(page, "S3 unknown folder")
                _agent, prepared_answer = self._prepare_agent(document_ref, destination_id)
                prepared = prepared_answer["send"]
                assert list(folder.iterdir()) == []

                owner_before = _api(page, "GET", "/api/desk/needs-you?fresh=1", token=H1_TOKEN)
                before_rows = [item for item in owner_before["items"] if item.get("kind") == "send"]
                assert len(before_rows) == 1 and before_rows[0]["sendId"] == prepared["id"], owner_before

                page.reload(wait_until="load")
                _normal_chair(page)
                row = page.locator("[data-testid='needs-row'][data-kind='send']").first
                row.wait_for(timeout=H1_T)
                posts: list[dict[str, Any]] = []
                page.on("request", lambda request: posts.append(request.post_data_json)
                        if request.method == "POST" and request.url.endswith("/api/channels/send") else None)
                row.locator("[data-verb='send']").click()
                page.wait_for_function(
                    """() => document.querySelector("[data-testid='needs-row'][data-kind='send'] [data-verb='try-again']") !== null""",
                    timeout=H1_T,
                )
                assert calls == 1 and len(posts) == 1, (calls, posts)
                first = self._sends(page, document_ref)
                assert len(first) == 1 and first[0]["state"] == "unknown", first
                first_kernel = self._kernel(first[0]["send_operation_id"])
                assert first_kernel["state"] == "indeterminate" and first_kernel["receipt_state"] == "indeterminate", first_kernel
                assert first_kernel["receipt_outcome"] == "unknown" and first_kernel["receipts"] == 1, first_kernel
                assert list(folder.iterdir()) == []
                page.screenshot(path=str(S3_SHOTS / f"needs-unknown-{width}.png"))

                # The owner reloads from the saved aggregate. Browser custody
                # is gone, but the row carries the kernel command provenance.
                page.reload(wait_until="load")
                _normal_chair(page)
                row = page.locator("[data-testid='needs-row'][data-kind='send']").first
                row.wait_for(timeout=H1_T)
                row.locator("[data-verb='try-again']").wait_for(timeout=H1_T)
                page.screenshot(path=str(S3_SHOTS / f"needs-unknown-reloaded-{width}.png"))
                assert calls == 1, "reload must not press a settled UNKNOWN send"
                row.locator("[data-verb='try-again']").click()
                deadline = time.monotonic() + 20
                while len(posts) < 2 and time.monotonic() < deadline:
                    page.wait_for_timeout(100)
                assert len(posts) == 2 and posts[0] == posts[1], posts
                assert calls == 1, "kernel replay must not dispatch the provider again"
                after = self._sends(page, document_ref)
                assert len(after) == 1 and after[0]["id"] == first[0]["id"] and after[0]["state"] == "unknown", after
                after_kernel = self._kernel(after[0]["send_operation_id"])
                assert after_kernel["operation_id"] == first_kernel["operation_id"]
                assert list(folder.iterdir()) == []

                privacy_agent = self._agent(palette="ALL", identity="privacy-agent")
                agent_error, agent_answer = _tool(privacy_agent, "desk.needs_you", {})
                assert agent_error is False and not [item for item in agent_answer.get("items", []) if item.get("kind") == "send"]
                agent_text = json.dumps(agent_answer)
                assert all(marker not in agent_text for marker in (first[0]["id"], "S3 unknown folder", prepared["preview"]["text"]))
                facts = {
                    "width": width, "document_ref": document_ref,
                    "owner_before": owner_before, "http_send_attempts": posts,
                    "provider_calls": calls, "send": after[0],
                    "receipt": after_kernel, "folder": {"path": str(folder), "files": [p.name for p in folder.iterdir()]},
                    "agent_send_rows": [],
                }
                (S3_SHOTS / f"needs-unknown-facts-{width}.json").write_text(json.dumps(facts, indent=2, default=str) + "\n")
                page.screenshot(path=str(S3_SHOTS / f"needs-unknown-retried-{width}.png"))
                assert not [error for error in errors if "ResizeObserver" not in error and "Failed to fetch" not in error], errors
            finally:
                browser.close()

    @pytest.mark.e2e
    @pytest.mark.timeout(600)
    @pytest.mark.chair_windows_open
    @pytest.mark.parametrize("width", WIDTHS)
    def test_an_admitted_agent_prepare_becomes_the_owner_needs_send(self, width: int) -> None:
        """S3: one real prepared row crosses the Needs face and leaves once.

        The source update, destination, admitted agent call, aggregate reads,
        owner press, file bytes and kernel receipt all use this Hub. The only
        external boundary is the local FileChannel itself.
        """
        from playwright.sync_api import sync_playwright
        from tests.unit.test_philo9_steward_admission import _tool

        with sync_playwright() as pw:
            browser, page, errors = self._open(pw, width)
            try:
                _normal_chair(page)
                project = _api(page, "POST", "/api/projects", {"name": "S3 browser private delivery"}, token=H1_TOKEN)
                project_id = project["project"]["id"]
                update = _api(page, "POST", f"/api/projects/{project_id}/updates/draft", {}, token=H1_TOKEN)
                update_id = update["update"]["id"]
                body = "## Progress\n\nThe browser proof keeps the frozen bytes.\n"
                _api(page, "PUT", f"/api/updates/{update_id}", {"body_md": body}, token=H1_TOKEN)
                _api(page, "POST", f"/api/updates/{update_id}/publish", {}, token=H1_TOKEN)
                document_ref = f"project_update:{update_id}"
                destination_id, folder = self._dest(page, "S3 private folder")
                agent, prepared_answer = self._prepare_agent(document_ref, destination_id)
                prepared = prepared_answer["send"]
                assert list(folder.iterdir()) == []

                # The owner aggregate and the admitted agent's aggregate read
                # the same Hub, with private send content withheld from MCP.
                owner_before = _api(page, "GET", "/api/desk/needs-you?fresh=1", token=H1_TOKEN)
                send_rows = [item for item in owner_before["items"] if item.get("kind") == "send"]
                assert len(send_rows) == 1, owner_before
                need = send_rows[0]
                assert need["id"] == f"send:{prepared['id']}"
                assert need["documentRef"] == document_ref
                assert need["destinationName"] == "S3 private folder"
                assert need["preparedBy"] == "Remote project agent"
                assert owner_before["count"] == len(owner_before["members"])
                assert any(c["kind"] == "send" and c["state"] == "available" for c in owner_before["coverage"])
                visibility_agent = self._agent(palette="ALL", identity="privacy-agent")
                agent_error, agent_answer = _tool(visibility_agent, "desk.needs_you", {})
                assert agent_error is False, agent_answer
                assert not [item for item in agent_answer.get("items", []) if item.get("kind") == "send"]
                agent_text = json.dumps(agent_answer)
                assert all(marker not in agent_text for marker in (
                    prepared["id"], "S3 private folder", prepared["preview"]["text"],
                ))

                # The owner reloads the actual face after the producer crossed
                # the boundary. No route answer is substituted in the browser.
                page.reload(wait_until="load")
                _normal_chair(page)
                row = page.locator("[data-testid='needs-row'][data-kind='send']").first
                row.wait_for(timeout=H1_T)
                row.scroll_into_view_if_needed()
                page.wait_for_function(
                    """(n) => {
                        const number = (selector) => {
                            const element = document.querySelector(selector);
                            if (n === 0 && !element) return 0;
                            const match = (element?.textContent || '').match(/\\d+/);
                            return match ? Number(match[0]) : null;
                        };
                        return number('[data-testid=arrival-display]') === n
                            && number('.desk-bell strong') === n;
                    }""",
                    arg=owner_before["count"], timeout=H1_T,
                )
                row_name = row.locator(".needs-row-name").inner_text()
                assert row_name == need["documentTitle"], (row_name, need)
                row_fact = row.locator(".needs-row-fact").inner_text()
                assert "REV 1" in row_fact and "S3 private folder" in row_fact
                assert "by Remote project agent" in row_fact
                assert row.locator("[data-verb='send']").count() == 1
                assert row.locator("[data-verb='look']").count() == 1
                assert row.locator("[data-testid='needs-send-discard']").count() == 1
                page.screenshot(path=str(S3_SHOTS / f"needs-prepared-{width}.png"))

                row.locator("[data-verb='look']").click()
                preview = page.locator("[data-testid='needs-send-preview']")
                preview.wait_for(timeout=H1_T)
                preview_text = preview.locator("[data-testid='send-preview-body']").inner_text().strip()
                expected_preview = " ".join(
                    re.sub(r"^#+\s*", "", line).strip()
                    for line in prepared["preview"]["text"].splitlines() if line.strip()
                )
                assert " ".join(preview_text.split()) == expected_preview
                display = str(prepared["target"].get("display") or prepared["target"]["folder"])
                folder_parts = [part for part in display.split("/") if part and part != "~"]
                folder_token = "/".join(folder_parts[-2:])
                assert folder_token in preview.inner_text()
                page.screenshot(path=str(S3_SHOTS / f"needs-preview-{width}.png"))

                posts: list[dict[str, Any]] = []
                page.on("request", lambda request: posts.append(request.post_data_json)
                        if request.method == "POST" and request.url.endswith("/api/channels/send") else None)
                row.locator("[data-verb='send']").click()
                page.wait_for_function(
                    """() => !document.querySelector("[data-testid='needs-row'][data-kind='send']")""",
                    timeout=H1_T,
                )
                assert len(posts) == 1 and posts[0]["send_id"] == prepared["id"]
                assert posts[0].get("command_id")
                page.screenshot(path=str(S3_SHOTS / f"needs-sent-{width}.png"))

                owner_after = _api(page, "GET", "/api/desk/needs-you?fresh=1", token=H1_TOKEN)
                assert not [item for item in owner_after["items"] if item.get("kind") == "send"], owner_after
                assert owner_after["count"] == len(owner_after["members"])
                page.wait_for_timeout(500)
                rendered_counts = page.evaluate("""() => ({
                    head: document.querySelector('[data-testid=arrival-display]')?.textContent || '',
                    bell: document.querySelector('.desk-bell strong')?.textContent || '',
                })""")
                assert owner_after["count"] == 0 or all(
                    str(owner_after["count"]) in rendered_counts[key] for key in ("head", "bell")
                ), (owner_after, rendered_counts)
                after_error, after_agent = _tool(visibility_agent, "desk.needs_you", {})
                assert after_error is False, after_agent
                assert not [item for item in after_agent.get("items", []) if item.get("kind") == "send"]

                sends = self._sends(page, document_ref)
                assert len(sends) == 1 and sends[0]["id"] == prepared["id"]
                assert sends[0]["state"] == "sent"
                sent_path = Path(sends[0]["proof"]["path"])
                assert sent_path.parent.resolve() == folder.resolve()
                assert sent_path.read_bytes() == prepared["preview"]["text"].encode()
                assert [item.name for item in folder.iterdir()] == [sent_path.name]
                receipt = self._face_row_receipt(sends[0], document_ref)
                assert receipt["receipt_outcome"] == "succeeded"
                facts = {
                    "width": width, "document_ref": document_ref,
                    "owner_before": owner_before, "agent_send_rows": [],
                    "http_send": posts[0], "send": sends[0], "receipt": receipt,
                    "file": {"path": str(sent_path), "bytes": sent_path.read_bytes().decode()},
                }
                (S3_SHOTS / f"needs-facts-{width}.json").write_text(json.dumps(facts, indent=2, default=str) + "\n")
                assert not [error for error in errors if "ResizeObserver" not in error and "Failed to fetch" not in error], errors
            finally:
                browser.close()
