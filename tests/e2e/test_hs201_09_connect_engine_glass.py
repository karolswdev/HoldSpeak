"""HS-201-09 — connect an engine from the face, on the glass.

One walk through the real hub with a real browser and an isolated HOME,
against the REAL LAN engine at http://192.168.1.43:8080/v1 when it is
reachable and a local OpenAI-compatible stub when it is not (the rig
prints which one it used).  The microphone is never touched; nothing is
seeded into the model library — every step below is a click:

  Models  ->  Add an engine  ->  a bad address  ->  Check
          ->  the refusal's plain reason BESIDE the verb, on screen
          ->  the engine's address        ->  Check  ->  READY + the model
          ->  Use this for summaries      ->  summaryAssignment: assigned
          ->  Use these with Speech recognition still WAITING
          ->  OFF + Use these             ->  no exact assignment remains
          ->  reopen Models               ->  OFF, not a proposal
          ->  Go -> Models                ->  the door, without the deck

Shots at 1440 and 393 in assets/story-09-shots/; the 393 pass asserts
that no two children of a Models row intersect (the rehearsal's
`02a-choose-an-engine-393.png` overlap).
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

pytest.importorskip("playwright.sync_api", reason="HS-201-09 glass needs Playwright")

pytestmark = pytest.mark.timeout(900, method="thread")

SHOTS = REPO / "pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/story-09-shots"
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
    ".concierge-root .surface-ledger-line, .concierge-add-engine-row"
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


_GEOM_JS = """() => {
  const out = [];
  const line = document.querySelector("[data-testid='concierge-set-meetings']");
  if (!line) return ["no meetings row"];
  const cs = getComputedStyle(line);
  out.push(`line display=${cs.display} wrap=${cs.flexWrap} w=${line.clientWidth}`);
  const walk = (node, depth) => {
    for (const child of node.children) {
      const s = getComputedStyle(child);
      const r = child.getBoundingClientRect();
      out.push(
        `${" ".repeat(depth)}${child.className || child.tagName}` +
        ` display=${s.display} flex=${s.flex} ovf=${s.overflow}` +
        ` rect=${Math.round(r.x)},${Math.round(r.width)}` +
        ` scrollW=${child.scrollWidth} clientW=${child.clientWidth}`);
      if (s.display === "contents") walk(child, depth + 1);
    }
  };
  walk(line, 0);
  return out;
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
    page.locator("[data-testid='arrival-display']").wait_for(timeout=15_000)
    _settle(page)


# The SETUP row names whichever half of the meeting path is missing
# (meetingPathBlocker.ts:91-96), so the rig reads the verb by either key.
BLOCKER_VERB = (
    "[data-testid='arrival-blocker-verb-engines'],"
    "[data-testid='arrival-blocker-verb-summary']"
)


def _open_models_from_the_blocker(page: Any) -> None:
    page.locator(BLOCKER_VERB).first.click()
    page.locator("[data-testid='concierge-root']").wait_for(timeout=30_000)
    page.locator("[data-testid='concierge-set-list']").wait_for(timeout=30_000)
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
          const root = document.querySelector(".concierge-root");
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
    # `desk-mic` is the MicButton species (the voice law on every input),
    # not a hand-rolled verb.
    raw = page.evaluate(
        """() => [...document.querySelectorAll(
             ".concierge-root button, .concierge-footer button")]
             .filter((b) => {
               const c = b.className.split(" ");
               return !c.includes("btn") && !c.includes("desk-mic");
             })
             .map((b) => (b.textContent || b.className).slice(0, 40))"""
    )
    assert not raw, f"{name} at {width}: raw buttons {raw}"
    # One filled primary per WINDOW: the Models body plus its portaled
    # footer (the desk behind it owns its own faces' primaries).
    primaries = page.evaluate(
        """() => [...document.querySelectorAll(
             ".concierge-root .btn--primary, .concierge-footer .btn--primary")]
             .map((b) => (b.textContent || "").trim())"""
    )
    assert len(primaries) <= 1, f"{name} at {width}: primaries {primaries}"
    if width == 393:
        print("GEOM", page.evaluate(_GEOM_JS))
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

            _open_models_from_the_blocker(page)
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
            # Counsel finding 4b: plain words, never the socket's own.
            assert "errno" not in said.lower(), said
            assert "urlopen" not in said.lower(), said
            assert said == "Nothing answers at this address.", said
            print(f"REFUSED REASON {said}")
            # Counsel finding 4c: the host is named BEFORE the verb that
            # contacts it (Article III at the point of decision).
            egress = page.locator("[data-testid='concierge-add-egress']")
            egress.wait_for(timeout=10_000)
            assert "127.0.0.1" in (egress.text_content() or ""), egress.text_content()
            row_box = page.locator(
                "[data-testid='concierge-add-engine-row']"
            ).bounding_box()
            verb_box = page.locator("[data-testid='concierge-add-check']").bounding_box()
            reason_box = reason.bounding_box()
            assert reason_box is not None and verb_box is not None and row_box is not None
            # Inside the same row, not 400 px below the button (defect 1).
            assert reason_box["y"] < verb_box["y"] + verb_box["height"] + 40, (
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
            assert (submit.text_content() or "").strip() == "Use this for summaries"
            assert not submit.is_disabled()
            assert "192.168.1.43" in (
                page.locator("[data-testid='concierge-add-egress']").text_content() or ""
            ) or "127.0.0.1" in (
                page.locator("[data-testid='concierge-add-egress']").text_content() or ""
            ), source

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

            # ── ONE gesture finishes setup (counsel finding 1) ──
            # No second click: the window must close itself, and the
            # arrival must drop its SETUP row on the readiness signal.
            assert page.locator(BLOCKER_VERB).count() > 0, (
                "the SETUP row was already gone before the gesture"
            )
            submit.click()
            page.wait_for_function(
                """() => !document.querySelector("[data-testid='concierge-root']")""",
                timeout=60_000,
            )
            page.wait_for_function(
                """() => !document.querySelector(
                     "[data-testid='arrival-blocker-verb-engines']") &&
                   !document.querySelector(
                     "[data-testid='arrival-blocker-verb-summary']")""",
                timeout=60_000,
            )
            assigned = _api(page, "GET", "/api/concierge/detect", token=TOKEN)[
                "summaryAssignment"
            ]
            assert assigned["status"] == "assigned", assigned
            assert assigned["profileId"], assigned
            assert int(assigned["profileRevision"]) >= 1, assigned
            print(f"SUMMARY ASSIGNED {assigned} (one gesture, no Use these)")
            _settle(page)
            # The desk behind must no longer ask for an engine.
            desk_said = page.locator("[data-testid='arrival-blocker']")
            assert desk_said.count() == 0, desk_said.first.text_content()
            _open_models_from_the_blocker_or_go(page)
            assert "Choose an engine" not in (page.content() or "")
            _shot(page, "models-engine-connected", width)

            # ── an unrelated WAITING group never blocks the apply ──
            rows = _api(page, "POST", "/api/concierge/propose", token=TOKEN)["rows"]
            waiting = [r["group"] for r in rows if r["state"] == "WAITING"]
            assert waiting, f"no WAITING group on this desk: {rows}"
            print(f"WAITING GROUPS {waiting}")
            apply_verb = page.locator("[data-testid='concierge-apply']")
            assert not apply_verb.is_disabled(), waiting
            apply_verb.click()
            page.wait_for_function(
                """() => !document.querySelector("[data-testid='concierge-root']")""",
                timeout=60_000,
            )
            still = _api(page, "GET", "/api/concierge/detect", token=TOKEN)[
                "summaryAssignment"
            ]
            assert still["status"] == "assigned", still

            # ── OFF on the summary group clears the exact assignment ──
            _open_models_from_the_blocker_or_go(page)
            page.locator("[data-testid='concierge-picker-meetings']").click()
            page.locator("[data-testid='concierge-pick-meetings-off']").click()
            page.locator("[data-testid='concierge-apply']").click()
            page.wait_for_function(
                """() => !document.querySelector("[data-testid='concierge-root']")""",
                timeout=60_000,
            )
            off = _api(page, "GET", "/api/concierge/detect", token=TOKEN)[
                "summaryAssignment"
            ]
            assert off["status"] == "off", off
            assert off["profileId"] is None, off
            roster = _api(page, "GET", "/api/inference/assignments", token=TOKEN)
            summary_row = next(
                row
                for row in roster["task_overrides"]
                if row["id"] == SUMMARY_CAPABILITY
            )
            assert summary_row["has_override"] is False, summary_row
            print(f"SUMMARY OFF {off} / roster {summary_row['effective']['status']}")

            # ── reopen: OFF, not a fresh proposal ──
            _open_models_from_the_blocker_or_go(page)
            picker = page.locator("[data-testid='concierge-picker-meetings']")
            assert "—" in (picker.text_content() or ""), picker.text_content()

            # ── a named repair state carries its reason (defect 7) ──
            # Applying the set bound the LAN engine to the tool groups, and
            # the assignment authority answered with a blocking issue; the
            # row must say WHY in plain words, not in its issue code.
            incompatible = page.locator(
                "[data-testid='concierge-repair-reason-tool-incompatible']"
            )
            if incompatible.count() > 0:
                reason_text = (incompatible.first.text_content() or "").strip()
                assert reason_text, "TOOL INCOMPATIBLE said nothing"
                assert "_" not in reason_text, reason_text
                print(f"REPAIR REASON {reason_text}")
            else:
                print("REPAIR REASON none on this desk (no blocking issue)")
            _shot(page, "models-summary-off", width)

            # ── counsel finding 2: the obvious way back ON ──
            # Pick the engine detection still lists, press Use these. The
            # cleared assignment's tombstone revision must not refuse it.
            page.locator("[data-testid='concierge-picker-meetings']").click()
            page.locator(
                "[data-testid='concierge-picker-well-meetings'] "
                "[data-testid^='concierge-pick-meetings-']:not("
                "[data-testid='concierge-pick-meetings-off'])"
            ).first.click()
            _settle(page)
            page.locator("[data-testid='concierge-apply']").click()
            page.wait_for_function(
                """() => !document.querySelector("[data-testid='concierge-root']")""",
                timeout=60_000,
            )
            back_on = _api(page, "GET", "/api/concierge/detect", token=TOKEN)[
                "summaryAssignment"
            ]
            assert back_on["status"] == "assigned", back_on
            assert back_on["profileId"], back_on
            print(f"SUMMARY BACK ON {back_on}")

            # ── reopen: the applied engine, not a proposal ──
            _open_models_from_the_blocker_or_go(page)
            picker = page.locator("[data-testid='concierge-picker-meetings']")
            assert "—" not in (picker.text_content() or ""), picker.text_content()
            presets = page.locator("[data-testid^='concierge-download-']").count()
            repairs = page.locator("[data-testid^='concierge-repair-verb-']").count()
            print(f"FACE CENSUS presets={presets} repairs={repairs}")
            _shot(page, "models-engine-back-on", width)

            # ── the door: Go -> Models, no command deck ──
            page.locator("[data-testid='concierge-cancel']").click()
            page.wait_for_function(
                """() => !document.querySelector("[data-testid='concierge-root']")""",
                timeout=30_000,
            )
            page.locator(".desk-verbbar-title", has_text="Go").click()
            page.get_by_role("menuitem", name="Models", exact=True).click()
            page.locator("[data-testid='concierge-root']").wait_for(timeout=30_000)
            print("DOOR Go > Models opened the Models window")
            _shot(page, "models-from-the-go-menu", width)

            real = [e for e in errors if "ResizeObserver" not in e]
            assert not real, real
            browser.close()


def _open_models_from_the_blocker_or_go(page: Any) -> None:
    """Open Models again — from the SETUP row while it is there, else Go."""
    blocker = page.locator(BLOCKER_VERB)
    if blocker.count() > 0:
        blocker.first.click()
    else:
        page.locator(".desk-verbbar-title", has_text="Go").click()
        page.get_by_role("menuitem", name="Models", exact=True).click()
    page.locator("[data-testid='concierge-root']").wait_for(timeout=30_000)
    page.locator("[data-testid='concierge-set-list']").wait_for(timeout=30_000)
    _settle(page)
