#!/usr/bin/env python3
"""Capture HS-93-05 recovery evidence against the production Web bundle.

This is implementation evidence only: it uses synthetic typed text, not a real
microphone or physical iPhone/iPad. It proves browser relaunch retention, factual
failure actions, observed first-value mechanics, and reconnect deduplication on
the real Hub routes.

    .venv/bin/python scripts/phase93_dictation_recovery_evidence.py [output-directory]
"""
from __future__ import annotations

import json
import sys
import tempfile
import time
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from unittest.mock import MagicMock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from playwright.sync_api import Page, Route, sync_playwright  # noqa: E402

import holdspeak.config as config_module  # noqa: E402
from holdspeak.config import Config  # noqa: E402
from holdspeak.db import get_database, reset_database  # noqa: E402
from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks  # noqa: E402


DEFAULT_OUTPUT = (
    ROOT
    / "pm/roadmap/holdspeak/phase-93-effortless-holdspeak/evidence/hs-93-05"
)


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


def prove_first_value(url: str) -> None:
    status, started = post(
        url, "/api/setup/first-value/start", {"destination": "this_machine"}
    )
    assert status == 201
    attempt = str(started["attempt"]["id"])
    status, _ = post(
        url,
        f"/api/setup/first-value/{attempt}/event",
        {"event_id": f"{attempt}:1:capture_started", "kind": "capture_started"},
    )
    assert status == 201
    status, finished = post(
        url,
        f"/api/setup/first-value/{attempt}/finish",
        {
            "outcome": "success",
            "destination": "this_machine",
            "steps": 20,
            "decisions": 20,
        },
    )
    receipt = finished["attempt"]
    assert status == 200
    assert receipt["steps"] == 1 and receipt["decisions"] == 0
    assert receipt["event_count"] == 2 and receipt["elapsed_ms"] >= 0
    assert not {"text", "phrase", "transcript", "content", "audio"}.intersection(
        receipt
    )


def prove_reconnect_dedup(url: str, deliveries: list[tuple[str, str]]) -> None:
    payload = {
        "text": "Synthetic reconnect canary.",
        "target_mode": "focused",
        "raw": True,
        "delivery_id": "evidence-device:delivery-1",
    }
    first_status, first = post(url, "/api/dictation/remote", payload)
    retry_status, retry = post(url, "/api/dictation/remote", payload)
    assert first_status == retry_status == 200
    assert first["deduplicated"] is False
    assert retry["deduplicated"] is True
    assert retry["delivery_id"] == payload["delivery_id"]
    assert deliveries == [(payload["text"], "focused")]


def capture_first_words(page: Page, url: str, output: Path) -> None:
    page.goto(f"{url}/welcome", wait_until="domcontentloaded")
    editor = page.get_by_role("textbox", name="Your dictated text")
    editor.fill("Synthetic draft retained through a browser relaunch.")
    page.reload(wait_until="domcontentloaded")
    editor = page.get_by_role("textbox", name="Your dictated text")
    assert editor.input_value() == "Synthetic draft retained through a browser relaunch."
    page.get_by_text("Recovered your local draft after relaunch").wait_for()
    page.screenshot(path=str(output / "after-web-first-words-relaunch.png"))


def capture_dictation_failure(page: Page, url: str, output: Path) -> None:
    def timeout(route: Route) -> None:
        route.fulfill(
            status=504,
            content_type="application/json",
            body=json.dumps({"error": "Synthetic timeout"}),
        )

    page.route("**/api/dictation/dry-run", timeout)
    page.goto(f"{url}/dictation", wait_until="domcontentloaded")
    page.get_by_role("tab", name="Try it").click()
    editor = page.get_by_label("Utterance")
    editor.fill("Synthetic draft retained after a model timeout.")
    page.get_by_role("button", name="Run dry test").click()
    page.get_by_text("Transcription timed out").wait_for()
    assert editor.input_value() == "Synthetic draft retained after a model timeout."
    page.get_by_role("button", name="Copy").wait_for()
    page.get_by_role("button", name="Keep as Note").wait_for()
    page.screenshot(
        path=str(output / "after-web-dictation-timeout.png"), full_page=True
    )

    page.unroute("**/api/dictation/dry-run", timeout)
    page.reload(wait_until="domcontentloaded")
    page.get_by_role("tab", name="Try it").click()
    assert page.get_by_label("Utterance").input_value() == (
        "Synthetic draft retained after a model timeout."
    )
    page.get_by_text("Recovered your local dictation draft").wait_for()
    page.screenshot(
        path=str(output / "after-web-dictation-relaunch.png"), full_page=True
    )


def main(output_directory: str | None = None) -> int:
    output = Path(output_directory) if output_directory else DEFAULT_OUTPUT
    output.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="holdspeak-phase93-dictation-") as temp_dir:
        scratch = Path(temp_dir)
        config_module.CONFIG_FILE = scratch / "config.json"
        Config().save(config_module.CONFIG_FILE)
        reset_database()
        get_database(scratch / "holdspeak.db")
        deliveries: list[tuple[str, str]] = []

        callbacks = WebRuntimeCallbacks(
            on_bookmark=MagicMock(return_value={"timestamp": 0.0, "label": "evidence"}),
            on_stop=MagicMock(return_value={"status": "stopped"}),
            get_state=MagicMock(return_value={}),
            on_remote_dictation=lambda text, *, target="agent": deliveries.append(
                (text, target)
            ),
        )
        server = MeetingWebServer(callbacks, host="127.0.0.1")
        url = server.start()
        time.sleep(0.8)

        try:
            prove_first_value(url)
            prove_reconnect_dedup(url, deliveries)
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch()
                capture_first_words(
                    browser.new_page(viewport={"width": 1200, "height": 900}),
                    url,
                    output,
                )
                capture_dictation_failure(
                    browser.new_page(viewport={"width": 1200, "height": 900}),
                    url,
                    output,
                )
                browser.close()
        finally:
            server.stop()
            reset_database()

    print(f"HS-93-05 production Web recovery evidence -> {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else None))
