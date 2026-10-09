"""HS-201-09 — connect an engine from the face, on the glass.

PHILO-16 (C): ported to Runs on (the Models window as a Switchboard). One
walk through the real hub with a real browser and an isolated HOME, against
the REAL LAN engine at http://192.168.1.43:8080/v1 when it is reachable and
a local OpenAI-compatible stub when it is not (the rig prints which one it
used). The microphone is never touched; nothing is seeded into the model
library: every step below is a gesture:

  Runs on (from the SETUP row)  ->  Add an engine  ->  a bad address
          ->  Check  ->  the refusal's plain reason BESIDE the verb
          ->  the engine's address  ->  Check  ->  READY + the model
          ->  Add  ->  the engine joins "What you have", no wire
          ->  patch it onto Default for AI work  ->  the SETUP row goes
          ->  patch it onto Meetings  ->  the exact summary row is written
          ->  Undo  ->  the summary row is cleared again
          ->  patch again  ->  the tombstone revision does not refuse it
          ->  Go -> Runs on  ->  the door, without the deck

The window stays open after every patch: the receipt and Undo are in its
foot. Shots at 1440 and 393 in assets/story-09-shots/; the 393 pass asserts
that no two children of the add row intersect.
"""
from __future__ import annotations

import json
import threading
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

import pytest

from .glass_infra import (
    REPO,
    _api,
    _boot,
    _ensure_build,
    _normal_chair,
    _settle,
)
from tests._evidence import evidence_dir
from .chair_windows import open_chair_window
from .runs_on import (
    close_runs_on,
    engine_key_for,
    patch,
    primaries,
    raw_buttons,
    wait_board,
    wait_receipt,
)

pytest.importorskip("playwright.sync_api", reason="HS-201-09 glass needs Playwright")

pytestmark = pytest.mark.timeout(900, method="thread")

SHOTS = evidence_dir("pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/story-09-shots")
TOKEN = "hs201-09-connect"
SUMMARY_CAPABILITY = "meeting.deferred_analysis"
LAN_URL = "http://192.168.1.43:8080/v1"
BAD_URL = "http://127.0.0.1:9/v1"  # discard port: always refuses

# The one intersection rule this face must obey at 393 (owner ruling:
# errors never overlap UI).  Flex items of one ledger line, expanded
# through `display: contents` wrappers, must not overlap each other.
_INTERSECTIONS_JS = """() => {
  const bad = [];
  const items = (line) => {
    const out = [];
    const walk = (node) => {
      for (const child of node.children) {
        if (getComputedStyle(child).display === "contents") walk(child);
        else out.push(child);
      }
    };
    walk(line);
    return out;
  };
  for (const line of document.querySelectorAll(
    "[data-testid='concierge-add-engine-row']"
  )) {
    const kids = items(line).filter((el) => {
      const r = el.getBoundingClientRect();
      return r.width > 0 && r.height > 0;
    });
    for (const kid of kids) {
      // The rehearsal's real overlap: a name that cannot break, in a box
      // the picker squeezed, with `overflow: visible` — the ink leaves the
      // box and lands on the control beside it while the BOXES never touch.
      if (
        getComputedStyle(kid).overflow === "visible" &&
        kid.scrollWidth > kid.clientWidth + 1
      ) {
        bad.push(
          `ink escapes ${kid.className || kid.tagName}` +
          ` scrollW=${kid.scrollWidth} clientW=${kid.clientWidth}` +
          ` :: ${(kid.textContent || "").slice(0, 40)}`
        );
      }
    }
    for (let i = 0; i < kids.length; i++) {
      for (let j = i + 1; j < kids.length; j++) {
        const a = kids[i].getBoundingClientRect();
        const b = kids[j].getBoundingClientRect();
        const overlap =
          a.left < b.right - 1 && b.left < a.right - 1 &&
          a.top < b.bottom - 1 && b.top < a.bottom - 1;
        if (overlap) {
          bad.push(
            `${kids[i].className || kids[i].tagName}` +
            ` x ${kids[j].className || kids[j].tagName}` +
            ` :: ${(kids[i].textContent || "").slice(0, 40)}` +
            ` | ${(kids[j].textContent || "").slice(0, 40)}`
          );
        }
      }
    }
  }
  return bad;
}"""


# ── the engine: the real LAN box, else a local OpenAI-compatible stub ──


class _StubHandler(BaseHTTPRequestHandler):
    MODEL = "stub-openai-compatible"

    def do_GET(self) -> None:  # noqa: N802 - http.server contract
        if self.path.rstrip("/").endswith("/models"):
            body = json.dumps(
                {"object": "list", "data": [{"id": self.MODEL, "object": "model"}]}
            ).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        self.send_response(404)
        self.end_headers()

    def log_message(self, *_args: Any) -> None:  # keep the rig's output clean
        return


def _lan_model() -> str | None:
    """The real engine's first model id, or None when it is not reachable."""
    try:
        with urllib.request.urlopen(f"{LAN_URL}/models", timeout=3) as response:
            payload = json.loads(response.read().decode())
    except (urllib.error.URLError, OSError, ValueError, TimeoutError):
        return None
    rows = payload.get("data") if isinstance(payload, dict) else None
    for row in rows or []:
        if isinstance(row, dict) and str(row.get("id") or "").strip():
            return str(row["id"]).strip()
    return None


@pytest.fixture(scope="module")
def engine() -> Any:
    """(base_url, model_id, source) — the real LAN engine when reachable."""
    model = _lan_model()
    if model is not None:
        print(f"ENGINE real LAN {LAN_URL} model={model}")
        yield (LAN_URL, model, "real LAN engine")
        return
    server = ThreadingHTTPServer(("127.0.0.1", 0), _StubHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    url = f"http://127.0.0.1:{server.server_address[1]}/v1"
    print(f"ENGINE local stub {url} model={_StubHandler.MODEL}")
    try:
        yield (url, _StubHandler.MODEL, "local OpenAI-compatible stub")
    finally:
        server.shutdown()
        server.server_close()


# ── the walk ──


def _arrive(page: Any, base: str) -> None:
    page.goto(f"{base}/?token={TOKEN}", wait_until="load")
    _api(page, "POST", "/api/desk/seed", token=TOKEN)
    _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
    _normal_chair(page)
    # PHILO-14 A1 (#939): the Chair's windows start closed; the owner opens
    # Needs you (Window > Chair at 1440, Go at 393).
    open_chair_window(page, "Needs you")
    page.locator("[data-testid='arrival-display']").wait_for(timeout=15_000)
    _settle(page)


# The SETUP row names whichever half of the meeting path is missing
# (meetingPathBlocker.ts:91-96). PHILO-14 A5 (#935): the row is a drawer row
# and its verb is the drawer's SETUP verb.
BLOCKER_VERB = "[data-testid='needs-row-verb'][data-verb='setup']"
# The blocker row by its own identity (needsYou.ts: `blocker:<key>`), not by
# its verb: the row must go, not only its button.
BLOCKER_ROW = "li.needs-row[data-object-id^='blocker:']"


def _open_runs_on_from_the_blocker(page: Any) -> None:
    page.locator(BLOCKER_VERB).first.click()
    wait_board(page)
    _settle(page)


def _shot(page: Any, name: str, width: int) -> None:
    """One shot at the width this walk runs at.

    A desk window keeps the rect the narrow viewport clamped it to, so a
    single run cannot honestly shoot both widths: the walk runs twice.
    1440 shoots the desk with the window on it; 393 shoots the window
    itself (there it is taller than the viewport) and asserts the row
    geometry the rehearsal caught overlapping.
    """
    SHOTS.mkdir(parents=True, exist_ok=True)
    # The face's own head is the subject: a scrolled body hides the
    # NEEDS YOU rows the rehearsal shot (02a) caught overlapping.
    page.evaluate(
        """() => {
          const root = document.querySelector("[data-testid='runson-root']");
          for (let el = root; el; el = el.parentElement) {
            const o = getComputedStyle(el).overflowY;
            if ((o === "auto" || o === "scroll") &&
                el.scrollHeight > el.clientHeight) {
              el.scrollTop = 0;
              return;
            }
          }
        }"""
    )
    _settle(page)
    path = SHOTS / f"{name}-{width}.png"
    window = page.locator(".desk-surface-window")
    if width == 393 and window.count() > 0:
        window.first.screenshot(path=str(path))
    else:
        page.screenshot(path=str(path))
    assert path.stat().st_size > 2000, path

    # UX-CANON A1: every verb on this face is the library Button.
    raw = raw_buttons(page)
    assert not raw, f"{name} at {width}: raw buttons {raw}"
    # One filled primary per WINDOW (body plus its portaled foot).
    lead = primaries(page)
    assert len(lead) <= 1, f"{name} at {width}: primaries {lead}"
    if width == 393:
        overlaps = page.evaluate(_INTERSECTIONS_JS)
        assert not overlaps, f"{name} at 393: {overlaps}"
    print(f"SHOT {path}")


class TestConnectAnEngineFromTheFace:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Any:
        _ensure_build()
        self.server, self.base = _boot(tmp_path, monkeypatch, token=TOKEN)
        yield
        self.server.stop()

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", [1440, 393])
    def test_a_stranger_connects_an_engine_and_the_face_keeps_his_choice(
        self, engine: Any, width: int
    ) -> None:
        from playwright.sync_api import sync_playwright

        url, model, source = engine
        errors: list[str] = []
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(
                viewport={"width": width, "height": 900 if width == 1440 else 852}
            )
            page.emulate_media(reduced_motion="reduce")
            page.on("pageerror", lambda err: errors.append(str(err)))

            _arrive(page, self.base)

            # Nothing is assigned on this desk yet.
            before = _api(page, "GET", "/api/concierge/detect", token=TOKEN)
            assert before["summaryAssignment"]["status"] == "unassigned", before[
                "summaryAssignment"
            ]

            _open_runs_on_from_the_blocker(page)
            _shot(page, "models-cold", width)

            # ── Add an engine is the library Button ──
            add = page.locator("[data-testid='concierge-add-engine']")
            assert add.evaluate("el => el.tagName") == "BUTTON"
            assert "btn" in (add.get_attribute("class") or "")
            assert (add.text_content() or "").strip() == "Add an engine"
            add.click()

            field = page.locator(
                "[data-testid='concierge-add-engine-row'] input"
            ).first
            field.wait_for(timeout=10_000)

            # ── a bad address: the reason sits BESIDE the verb, on screen ──
            field.fill(BAD_URL)
            page.locator("[data-testid='concierge-add-check']").click()
            reason = page.locator("[data-testid='concierge-add-reason']")
            reason.wait_for(timeout=30_000)
            said = (reason.text_content() or "").strip()
            assert said, "the refused check said nothing"
            assert "errno" not in said.lower(), said
            assert "urlopen" not in said.lower(), said
            # A.3 (Astra r1 M8): tokens, never the server's sentence.
            assert said == "127.0.0.1:9", said
            assert "UNREACHABLE" in (page.locator("[data-testid='concierge-add-engine-row']").text_content() or "")
            print(f"REFUSED REASON {said}")
            # Article III: the host is named BEFORE the verb that contacts it.
            egress = page.locator("[data-testid='concierge-add-egress']")
            egress.wait_for(timeout=10_000)
            assert "127.0.0.1" in (egress.text_content() or ""), egress.text_content()
            row_box = page.locator(
                "[data-testid='concierge-add-engine-row']"
            ).bounding_box()
            verb_box = page.locator("[data-testid='concierge-add-check']").bounding_box()
            reason_box = reason.bounding_box()
            assert reason_box is not None and verb_box is not None and row_box is not None
            # Inside the same row, near its verb (defect 1).
            assert reason_box["y"] < verb_box["y"] + verb_box["height"] + 60, (
                verb_box,
                reason_box,
            )
            assert reason_box["y"] + reason_box["height"] <= row_box["y"] + row_box[
                "height"
            ] + 2
            assert page.locator("[data-testid='concierge-add-submit']").is_disabled()
            _shot(page, "add-engine-refused", width)

            # ── the engine's address: READY, and the model named ──
            field.fill(url)
            page.locator("[data-testid='concierge-add-check']").click()
            named = page.locator("[data-testid='concierge-add-model']")
            named.wait_for(timeout=60_000)
            assert (named.text_content() or "").strip() == model, source
            submit = page.locator("[data-testid='concierge-add-submit']")
            assert (submit.text_content() or "").strip() == "Add"
            assert not submit.is_disabled()

            # ── counsel finding 3: editing the address drops the READY ──
            field.fill(url.replace("/v1", "/v2"))
            page.wait_for_function(
                """() => !document.querySelector(
                     "[data-testid='concierge-add-model']")""",
                timeout=10_000,
            )
            assert submit.is_disabled(), "a stale READY survived an address edit"
            print("STALE CHECK dropped on address edit")
            field.fill(url)
            page.locator("[data-testid='concierge-add-check']").click()
            named.wait_for(timeout=60_000)
            assert (named.text_content() or "").strip() == model, source
            _shot(page, "add-engine-ready", width)

            # ── Add: the engine joins the column, with no wire ──
            assert page.locator(BLOCKER_ROW).count() > 0, (
                "the blocker row was already gone before the gesture"
            )
            submit.click()
            wait_receipt(page, r"^ADDED ")
            key = engine_key_for(url)
            plate = page.get_by_test_id(f"switchboard-engine-{key}")
            plate.wait_for(timeout=60_000)
            assert page.locator(
                f"[data-testid='switchboard-wire'][data-engine='{key}']"
            ).count() == 0
            print(f"ADDED {key} (no assignment)")

            # ── patch it onto Meetings: the exact summary row is written ──
            # (Meetings first: once the Default runs this engine, Meetings
            # follows it, and the phone list never offers the engine a job
            # already runs on.)
            patch(page, "meetings", key)
            assigned = _api(page, "GET", "/api/concierge/detect", token=TOKEN)[
                "summaryAssignment"
            ]
            assert assigned["status"] == "assigned", assigned
            assert assigned["profileId"] == key, assigned
            assert int(assigned["profileRevision"]) >= 1, assigned
            print(f"SUMMARY ASSIGNED {assigned}")

            # ── patch it onto the Default for AI work: the desk stops asking ──
            body = patch(page, "default", key)
            assert body["scope"] == {"kind": "global"}, body
            assert [e["profile_id"] for e in body["entries"]] == [key], body
            page.wait_for_function(
                """() => !document.querySelector(
                     "[data-testid='needs-row-verb'][data-verb='setup']") &&
                   !document.querySelector(
                     "li.needs-row[data-object-id^='blocker:']")""",
                timeout=60_000,
            )
            print("SETUP row gone; the window stays open")
            assert page.locator("[data-testid='runson-undo']").count() == 1
            _shot(page, "models-engine-connected", width)

            # ── Undo, twice: the Default, then Meetings and its summary row
            #    (inherited before, so cleared back to inheritance) ──
            page.locator("[data-testid='runson-undo']").click()
            wait_receipt(page, r"^UNDONE .*Default for AI work")
            page.locator("[data-testid='runson-undo']").click()
            wait_receipt(page, r"^UNDONE .*Meetings$")
            roster = _api(page, "GET", "/api/inference/assignments", token=TOKEN)
            summary_row = next(
                row for row in roster["task_overrides"] if row["id"] == SUMMARY_CAPABILITY
            )
            assert summary_row["has_override"] is False, summary_row
            print(f"SUMMARY UNDONE / roster {summary_row['effective']['status']}")
            _shot(page, "models-summary-undone", width)

            # ── counsel finding 2: back ON over the tombstone ──
            patch(page, "meetings", key)
            back_on = _api(page, "GET", "/api/concierge/detect", token=TOKEN)[
                "summaryAssignment"
            ]
            assert back_on["status"] == "assigned", back_on
            assert back_on["profileId"] == key, back_on
            print(f"SUMMARY BACK ON {back_on}")
            _shot(page, "models-engine-back-on", width)

            # ── the door: Go -> Runs on (1440); Go -> Settings -> Runs on (393,
            # whose short Go lists the places, PHILO-15 11) — no command deck ──
            close_runs_on(page)
            page.locator(".desk-verbbar-title", has_text="Go").click()
            if width == 393:
                page.get_by_role("menuitem", name="Settings", exact=True).first.click()
                row = page.locator(".surface-ledger-row", has_text="Runs on").first
                row.get_by_role("button", name="Open", exact=True).click()
            else:
                page.get_by_role("menuitem", name="Runs on", exact=True).first.click()
            wait_board(page)
            print("DOOR Go opened the Runs on window")
            _shot(page, "models-from-the-go-menu", width)

            real = [e for e in errors if "ResizeObserver" not in e]
            assert not real, real
            browser.close()
