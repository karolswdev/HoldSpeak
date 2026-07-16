#!/usr/bin/env python3
"""Capture the HS-93-05 Web fault matrix against the production bundle.

Modeled on phase93_dictation_recovery_evidence.py (which keeps the timeout and
relaunch-retention captures). This runner forces each remaining Web-applicable
fault and asserts three things per fault:

  1. the editable draft survives,
  2. the failure copy names what failed, what is retained, and the next action,
  3. no API call failed EXCEPT the deliberately forced failure.

Faults covered here: permission denial (real browser permission), missing
model (real hub state: no transcriber wired), rejected token (401 on the API
call), unreachable hub (aborted request), delivery conflict (409) plus the
alternate Runs-on re-run, and the reconnect/exactly-once ledger matrix on the
real /api/dictation/remote route (dedup, changed payload, indeterminate
pending). Synthetic typed text only: implementation evidence, not
real-microphone or physical-device evidence.

    .venv/bin/python scripts/phase93_dictation_fault_matrix_evidence.py [output-directory]
"""
from __future__ import annotations

import json
import sys
import tempfile
import time
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from unittest.mock import MagicMock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from playwright.sync_api import Browser, Page, Route, sync_playwright  # noqa: E402

import holdspeak.config as config_module  # noqa: E402
from holdspeak.config import Config  # noqa: E402
from holdspeak.db import get_database, reset_database  # noqa: E402
from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks  # noqa: E402


DEFAULT_OUTPUT = (
    ROOT
    / "pm/roadmap/holdspeak/phase-93-effortless-holdspeak/evidence/hs-93-05"
)

SYNTHETIC_DRAFT = "Synthetic draft retained through a forced fault."


def post(url: str, path: str, body: dict[str, object]) -> tuple[int, dict[str, object]]:
    request = Request(
        f"{url}{path}",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=10) as response:  # noqa: S310 - isolated local server
            return response.status, json.loads(response.read())
    except HTTPError as exc:
        return exc.code, json.loads(exc.read())


class ApiFailureTracker:
    """Every >=400 API response and every failed API request on one page."""

    def __init__(self, page: Page) -> None:
        self.failures: list[tuple[int, str]] = []
        self.aborted: list[str] = []
        page.on("response", self._on_response)
        page.on("requestfailed", self._on_request_failed)

    def _on_response(self, response) -> None:
        path = urlparse(response.url).path
        if response.status >= 400 and path.startswith("/api/"):
            self.failures.append((response.status, path))

    def _on_request_failed(self, request) -> None:
        path = urlparse(request.url).path
        if path.startswith("/api/"):
            self.aborted.append(path)

    def assert_exactly(
        self,
        fault: str,
        *,
        failures: list[tuple[int, str]],
        aborted: list[str] | None = None,
    ) -> None:
        assert self.failures == failures, (
            f"{fault}: unexpected failed API responses {self.failures!r}, "
            f"expected {failures!r}"
        )
        assert self.aborted == (aborted or []), (
            f"{fault}: unexpected aborted API requests {self.aborted!r}"
        )


# ── the reconnect / exactly-once ledger matrix, on the real route ────────────


def prove_delivery_ledger_matrix(
    url: str, deliveries: list[tuple[str, str]]
) -> None:
    payload = {
        "text": "Synthetic exactly-once canary.",
        "target_mode": "focused",
        "raw": True,
        "delivery_id": "fault-matrix:delivery-1",
    }
    first_status, first = post(url, "/api/dictation/remote", payload)
    retry_status, retry = post(url, "/api/dictation/remote", payload)
    assert first_status == retry_status == 200
    assert first["deduplicated"] is False and retry["deduplicated"] is True
    assert deliveries == [(payload["text"], "focused")], "effect ran twice"

    changed = dict(payload, text="Different words under the same id.")
    conflict_status, conflict = post(url, "/api/dictation/remote", changed)
    assert conflict_status == 409
    assert conflict["failure_category"] == "delivery_conflict"
    assert deliveries == [(payload["text"], "focused")], "conflict replayed"

    stall = {
        "text": "stall-canary must never type twice",
        "target_mode": "focused",
        "raw": True,
        "delivery_id": "fault-matrix:stall-1",
    }
    pending_status, pending = post(url, "/api/dictation/remote", stall)
    again_status, again = post(url, "/api/dictation/remote", stall)
    assert pending_status == again_status == 425
    assert pending["error_code"] == again["error_code"] == "delivery_pending"
    assert deliveries == [(payload["text"], "focused")], "pending replayed"


# ── browser faults ────────────────────────────────────────────────────────────


def capture_permission_denied(browser: Browser, url: str, output: Path) -> None:
    """Permission denial at the browser API boundary. A sandboxed headless
    macOS Chromium never resolves the OS microphone prompt, so the runner
    forces the exact DOMException the browser produces on a real denial;
    the component, copy, retained draft, and tracker calls are production."""
    context = browser.new_context(viewport={"width": 1200, "height": 900})
    context.add_init_script(
        "navigator.mediaDevices.getUserMedia = () => Promise.reject("
        "new DOMException('Permission denied', 'NotAllowedError'));"
    )
    page = context.new_page()
    tracker = ApiFailureTracker(page)
    page.goto(f"{url}/welcome", wait_until="domcontentloaded")
    editor = page.get_by_role("textbox", name="Your dictated text")
    editor.fill(SYNTHETIC_DRAFT)
    talk = page.get_by_role("button", name="Hold to dictate")
    talk.dispatch_event("pointerdown")
    page.get_by_text("Microphone access is off").wait_for()
    assert editor.input_value() == SYNTHETIC_DRAFT
    page.get_by_role("button", name="Copy").is_enabled()
    page.get_by_role("button", name="Keep as Note").is_enabled()
    page.get_by_role("link", name="Setup").wait_for()
    page.get_by_role(
        "button", name="Dictation unavailable until setup is fixed"
    ).wait_for()
    page.screenshot(
        path=str(output / "after-web-fault-permission-denied.png"), full_page=True
    )
    tracker.assert_exactly("permission_denied", failures=[])
    context.close()


_SEED_PENDING_VOICE = """
async () => {
  const samples = 16000;
  const buffer = new ArrayBuffer(44 + samples * 2);
  const view = new DataView(buffer);
  const word = (at, s) =>
    [...s].forEach((c, i) => view.setUint8(at + i, c.charCodeAt(0)));
  word(0, "RIFF"); view.setUint32(4, 36 + samples * 2, true); word(8, "WAVE");
  word(12, "fmt "); view.setUint32(16, 16, true); view.setUint16(20, 1, true);
  view.setUint16(22, 1, true); view.setUint32(24, 16000, true);
  view.setUint32(28, 32000, true); view.setUint16(32, 2, true);
  view.setUint16(34, 16, true); word(36, "data");
  view.setUint32(40, samples * 2, true);
  await new Promise((resolve, reject) => {
    const request = indexedDB.open("holdspeak-voice-recovery", 1);
    request.onupgradeneeded = () =>
      request.result.createObjectStore("captures", { keyPath: "scope" });
    request.onsuccess = () => {
      const db = request.result;
      const tx = db.transaction("captures", "readwrite");
      tx.objectStore("captures").put({
        version: 1,
        scope: "first-words",
        audio: buffer,
        updatedAt: new Date().toISOString(),
      });
      tx.oncomplete = () => { db.close(); resolve(null); };
      tx.onerror = () => reject(tx.error);
    };
    request.onerror = () => reject(request.error);
  });
}
"""


def capture_missing_model(browser: Browser, url: str, output: Path) -> None:
    """Real hub state: this runtime wires no transcriber, so the real
    /api/dictation/transcribe route answers 503. The capture rides the
    recovered-audio checkpoint (one scope-keyed WAV in IndexedDB, the
    production schema) because the sandboxed headless browser has no
    microphone: retry sends the retained audio to the real route."""
    page = browser.new_page(viewport={"width": 1200, "height": 900})
    tracker = ApiFailureTracker(page)
    page.goto(f"{url}/welcome", wait_until="domcontentloaded")
    page.evaluate(_SEED_PENDING_VOICE)
    page.reload(wait_until="domcontentloaded")
    page.get_by_text("Captured audio was recovered on this browser").wait_for()
    editor = page.get_by_role("textbox", name="Your dictated text")
    editor.fill(SYNTHETIC_DRAFT)
    page.get_by_role("button", name="Hold to retry dictation").dispatch_event(
        "pointerdown"
    )
    page.get_by_text("Local transcription is not ready").wait_for()
    assert editor.input_value() == SYNTHETIC_DRAFT
    page.get_by_role("link", name="Setup").wait_for()
    page.get_by_role(
        "button", name="Dictation unavailable until setup is fixed"
    ).wait_for()
    page.screenshot(
        path=str(output / "after-web-fault-missing-model.png"), full_page=True
    )
    tracker.assert_exactly(
        "missing_model", failures=[(503, "/api/dictation/transcribe")]
    )
    # The checkpointed audio survives the failed retry for a later attempt.
    retained = page.evaluate(
        """
        () => new Promise((resolve) => {
          const request = indexedDB.open("holdspeak-voice-recovery", 1);
          request.onsuccess = () => {
            const db = request.result;
            const tx = db.transaction("captures", "readonly");
            const get = tx.objectStore("captures").get("first-words");
            get.onsuccess = () => {
              const bytes = get.result?.audio?.byteLength ?? 0;
              db.close();
              resolve(bytes);
            };
            get.onerror = () => { db.close(); resolve(0); };
          };
          request.onerror = () => resolve(0);
        })
        """
    )
    assert int(retained) > 0, "the audio checkpoint must survive a failed retry"
    page.close()


def open_try_it(page: Page, url: str) -> None:
    page.goto(f"{url}/dictation", wait_until="domcontentloaded")
    page.get_by_role("tab", name="Try it").click()
    page.get_by_label("Utterance").fill(SYNTHETIC_DRAFT)
    page.get_by_role("button", name="Run dry test").click()


def capture_rejected_token(browser: Browser, url: str, output: Path) -> None:
    page = browser.new_page(viewport={"width": 1200, "height": 900})
    tracker = ApiFailureTracker(page)

    def reject(route: Route) -> None:
        route.fulfill(
            status=401,
            content_type="application/json",
            body=json.dumps({"error": "Synthetic rejected token"}),
        )

    page.route("**/api/dictation/dry-run", reject)
    open_try_it(page, url)
    page.get_by_text("This hub rejected the connection").wait_for()
    assert page.get_by_label("Utterance").input_value() == SYNTHETIC_DRAFT
    page.get_by_role("button", name="Copy").wait_for()
    page.get_by_role("button", name="Keep as Note").wait_for()
    page.get_by_role("link", name="Setup").wait_for()
    # A rejected token is not retryable and names no alternate destination.
    page.get_by_role("button", name="Run dry test").wait_for()
    assert page.get_by_role("combobox", name="Runs on").count() == 0
    page.screenshot(
        path=str(output / "after-web-fault-rejected-token.png"), full_page=True
    )
    tracker.assert_exactly(
        "rejected_token", failures=[(401, "/api/dictation/dry-run")]
    )
    page.close()


def capture_unreachable_hub(browser: Browser, url: str, output: Path) -> None:
    page = browser.new_page(viewport={"width": 1200, "height": 900})
    tracker = ApiFailureTracker(page)
    page.route(
        "**/api/dictation/dry-run",
        lambda route: route.abort("connectionrefused"),
    )
    open_try_it(page, url)
    page.get_by_text("The hub could not be reached").wait_for()
    assert page.get_by_label("Utterance").input_value() == SYNTHETIC_DRAFT
    page.get_by_role("button", name="Retry dry test").wait_for()
    page.get_by_role("button", name="Copy").wait_for()
    page.get_by_role("button", name="Keep as Note").wait_for()
    assert page.get_by_role("link", name="Setup").count() == 0
    page.screenshot(
        path=str(output / "after-web-fault-unreachable-hub.png"), full_page=True
    )
    tracker.assert_exactly(
        "unreachable_hub", failures=[], aborted=["/api/dictation/dry-run"]
    )
    page.close()


def capture_delivery_conflict(browser: Browser, url: str, output: Path) -> None:
    """One forced 409, then the alternate Runs-on action re-runs for real:
    the picker saves the destination through the real /api/settings route and
    the second dry-run reaches the real pipeline."""
    page = browser.new_page(viewport={"width": 1200, "height": 900})
    tracker = ApiFailureTracker(page)
    calls = {"count": 0}

    def conflict_once(route: Route) -> None:
        calls["count"] += 1
        if calls["count"] == 1:
            route.fulfill(
                status=409,
                content_type="application/json",
                body=json.dumps(
                    {
                        "error": "Synthetic delivery conflict",
                        "failure_category": "delivery_conflict",
                    }
                ),
            )
        else:
            route.continue_()

    page.route("**/api/dictation/dry-run", conflict_once)
    settings_puts: list[str] = []
    page.on(
        "request",
        lambda request: settings_puts.append(request.post_data or "")
        if request.method == "PUT" and urlparse(request.url).path == "/api/settings"
        else None,
    )
    open_try_it(page, url)
    page.get_by_text("Delivery did not complete").wait_for()
    assert page.get_by_label("Utterance").input_value() == SYNTHETIC_DRAFT
    page.get_by_role("button", name="Retry dry test").wait_for()
    page.get_by_role("button", name="Copy").wait_for()
    page.get_by_role("button", name="Keep as Note").wait_for()
    picker = page.get_by_role("combobox", name="Runs on")
    picker.wait_for()
    page.screenshot(
        path=str(output / "after-web-fault-delivery-conflict.png"), full_page=True
    )

    # The alternate Runs-on action: pick this device, which saves the runtime
    # destination through the real settings route and re-runs the dry test.
    picker.select_option("this_machine")
    page.get_by_role("button", name="Right").wait_for(timeout=30_000)
    assert page.get_by_label("Utterance").input_value() == SYNTHETIC_DRAFT
    assert calls["count"] == 2, "the alternate Runs-on pick must re-run once"
    assert len(settings_puts) == 1, f"expected one destination save: {settings_puts!r}"
    saved = json.loads(settings_puts[0])
    assert saved == {"dictation": {"runtime": {"profile_id": None}}}, saved
    page.screenshot(
        path=str(output / "after-web-fault-delivery-conflict-rerun.png"),
        full_page=True,
    )
    tracker.assert_exactly(
        "delivery_conflict", failures=[(409, "/api/dictation/dry-run")]
    )
    page.close()


def main(output_directory: str | None = None) -> int:
    output = Path(output_directory) if output_directory else DEFAULT_OUTPUT
    output.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="holdspeak-phase93-faults-") as temp_dir:
        scratch = Path(temp_dir)
        config_module.CONFIG_FILE = scratch / "config.json"
        Config().save(config_module.CONFIG_FILE)
        reset_database()
        get_database(scratch / "holdspeak.db")
        deliveries: list[tuple[str, str]] = []

        def delivery_hook(text: str, *, target: str = "agent") -> None:
            if "stall-canary" in text:
                raise RuntimeError("target stopped mid-delivery")
            deliveries.append((text, target))

        callbacks = WebRuntimeCallbacks(
            on_bookmark=MagicMock(return_value={"timestamp": 0.0, "label": "evidence"}),
            on_stop=MagicMock(return_value={"status": "stopped"}),
            get_state=MagicMock(return_value={}),
            on_remote_dictation=delivery_hook,
        )
        server = MeetingWebServer(callbacks, host="127.0.0.1")
        url = server.start()
        time.sleep(0.8)

        try:
            prove_delivery_ledger_matrix(url, deliveries)
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch()
                capture_permission_denied(browser, url, output)
                capture_missing_model(browser, url, output)
                capture_rejected_token(browser, url, output)
                capture_unreachable_hub(browser, url, output)
                capture_delivery_conflict(browser, url, output)
                browser.close()
        finally:
            server.stop()
            reset_database()

    print(f"HS-93-05 Web fault matrix evidence -> {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else None))
