"""PHILO-16 (C) -- Runs on: the Models window as a Switchboard, on glass.

The old Concierge rig is parked (tests/_parked/philo16-concierge/). This rig
boots an isolated-HOME hub and a fake OpenAI-compatible server on
127.0.0.1, defines two engines through the real Model Library route (one at
a LAN address that the rig's network double answers from the fake server,
one on loopback), records a speech engine, and wires them through the real
assignment route. Detection, the fits, the probes, the writes and the CAS
are the product's own. The doubles: the LAN address (rewritten to the fake
server), a loopback scan that finds one more server, and a catalog download
whose acquisition the rig advances (no byte leaves this machine).

Shots (evidence_dir docs/internal/philo/phase-16/c-shots): the board with
three engines wired, after a drag-patch, a Try it result, a FOUND row and
after Use it, a download mid-bar; and the 393 list.
"""
from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

import pytest

from tests._evidence import evidence_dir

from .glass_infra import _api, _assert_clean, _boot, _normal_chair, _settle

SHOTS = evidence_dir("docs/internal/philo/phase-16/c-shots")
TOKEN = "glass-test"
LAN_BASE = "http://192.168.77.43:8080/v1"
pytestmark = [pytest.mark.e2e, pytest.mark.timeout(240, method="thread")]


class _FakeOpenAI(BaseHTTPRequestHandler):
    """A minimal OpenAI-compatible server: /models and chat completions."""

    MODEL = "qwen3.8-27b"

    def _json(self, payload: dict[str, Any]) -> None:
        body = json.dumps(payload).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802 - http.server contract
        if self.path.rstrip("/").endswith("/models"):
            self._json({"object": "list", "data": [{"id": self.MODEL, "object": "model"}]})
            return
        self.send_response(404)
        self.end_headers()

    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers.get("Content-Length") or 0)
        self.rfile.read(length)
        if "chat/completions" in self.path:
            self._json({
                "id": "fake", "object": "chat.completion", "model": self.MODEL,
                "choices": [{"index": 0, "finish_reason": "stop",
                             "message": {"role": "assistant", "content": "ready"}}],
                "usage": {"prompt_tokens": 8, "completion_tokens": 1, "total_tokens": 9},
            })
            return
        self.send_response(404)
        self.end_headers()

    def log_message(self, *_args: Any) -> None:
        return


def _serve(model: str = _FakeOpenAI.MODEL) -> ThreadingHTTPServer:
    handler = type("_Fake", (_FakeOpenAI,), {"MODEL": model})
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


def _doubles(monkeypatch: Any, lan_port: int, found_port: int) -> dict[str, int]:
    """The network doubles: the LAN address answers from the fake server; the
    loopback scan finds one more; a catalog download advances in place."""
    import holdspeak.inference_setup_catalog as catalog
    import holdspeak.services.concierge_service as cs
    import holdspeak.setup_runtime as setup_runtime
    from holdspeak.services.inference_acquisition_service import InferenceAcquisitionApplicationService

    real_discover = setup_runtime.discover_endpoint_models

    def discover(base_url: str, *args: Any, **kwargs: Any) -> Any:
        return real_discover(
            str(base_url).replace("192.168.77.43:8080", f"127.0.0.1:{lan_port}"), *args, **kwargs
        )

    monkeypatch.setattr(setup_runtime, "discover_endpoint_models", discover)

    real_detect = cs.detect

    def detect(**kwargs: Any) -> Any:
        kwargs["loopback_scan"] = lambda: [{
            "id": f"local:ollama:{found_port}:llama3.3", "model": "llama3.3",
            "base_url": f"http://127.0.0.1:{found_port}/v1", "engine": "ollama", "port": found_port,
        }]
        return real_detect(**kwargs)

    monkeypatch.setattr(cs, "detect", detect)

    preset = {
        "id": "preset_glass_vision", "kind": "local_artifact_preset", "activation": "download",
        "label": "Qwen 3.5 4B vision file", "source": {"download_bytes": 890_000_000},
    }
    monkeypatch.setattr(catalog, "applicable_presets", lambda **_: [preset])

    ticks = {"n": 0, "hold": 1}

    def download(**_: Any) -> dict[str, Any]:
        return {"jobId": "acq-glass", "presetId": preset["id"], "progress": {"received": 0, "total": 0}}

    monkeypatch.setattr(cs, "download", download)

    def get_acquisition(self: Any, principal: Any, job_id: str) -> dict[str, Any]:
        ticks["n"] += 1
        received = min(890_000_000, 890_000_000 * 0.42 if ticks["hold"] else 890_000_000)
        return {"acquisition": {
            "id": job_id, "preset_id": preset["id"],
            "state": "downloading" if ticks["hold"] else "ready",
            "verified_bytes": int(received), "transport_bytes": int(received),
            "bytes_total": 890_000_000,
        }}

    monkeypatch.setattr(InferenceAcquisitionApplicationService, "get_acquisition", get_acquisition)
    return ticks


def _define(page: Any, base_url: str, model: str, profile_id: str, label: str) -> tuple[str, int]:
    defined = _api(page, "POST", "/api/inference/model-library/define-endpoint", {
        "draft": {
            "request_id": f"glass-{profile_id}", "profile_id": profile_id,
            "expected_profile_revision": 0, "label": label,
            "provider_family": "openai_compatible", "model": model,
            "endpoint": base_url, "requires_key": False,
        },
        "secret": None,
    }, token=TOKEN)
    provider = defined["provider"]
    return str(provider["profile_id"]), int(provider["profile_revision"])


def _wire(page: Any, group: str | None, entries: list[tuple[str, int]]) -> None:
    roster = _api(page, "GET", "/api/inference/assignments", token=TOKEN)
    row = next(r for r in roster["rows"] if r["id"] == (group or "global"))
    _api(page, "POST", "/api/inference/assignments/set", {
        "command_id": f"glass-wire-{group or 'global'}",
        "expected_revision": row["expected_revision"],
        "scope": {"kind": "group", "group_id": group} if group else {"kind": "global"},
        "entries": [{"profile_id": p, "profile_revision": r} for p, r in entries],
    }, token=TOKEN)


def _speech_engine() -> None:
    from holdspeak.db import get_database
    from tests.unit.test_phase143_inference_assignments import _profile, _result_claim

    _profile(
        get_database(), "whisper-small",
        claims=("language", _result_claim("speech.transcribe")),
        modalities=("audio",),
    )


def _open_runs_on(page: Any) -> None:
    page.evaluate(
        """([key]) => sessionStorage.setItem("hs.desk.staged-surface-open", JSON.stringify({key}))""",
        ["open-concierge"],
    )
    page.reload(wait_until="load")
    _normal_chair(page)
    page.get_by_test_id("runson-root").wait_for(timeout=15_000)
    page.get_by_test_id("switchboard").wait_for(timeout=15_000)


def _window(page: Any) -> Any:
    return page.locator(".desk-surface-window").filter(has=page.get_by_test_id("runson-root")).first


def _shot(page: Any, name: str, width: int) -> Path:
    _settle(page)
    path = SHOTS / f"{name}-{width}.png"
    win = _window(page)
    (win if win.count() else page).screenshot(path=str(path), animations="disabled")
    assert path.stat().st_size > 2_000
    print("SHOT", path)
    return path


def _rig(tmp_path: Path, monkeypatch: Any) -> tuple[Any, str, list[ThreadingHTTPServer], dict[str, int]]:
    lan, found, local = _serve(), _serve("llama3.3"), _serve("qwen3.5-4b")
    ticks = _doubles(monkeypatch, lan.server_address[1], found.server_address[1])
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    return server, url, [lan, found, local], ticks


def _seed(page: Any, local_port: int) -> None:
    lan = _define(page, LAN_BASE, "qwen3.8-27b", "glass-lan-27b", "qwen3.8 27B")
    local = _define(page, f"http://127.0.0.1:{local_port}/v1", "qwen3.5-4b", "glass-mac-4b", "Qwen 3.5 4B")
    _speech_engine()
    _wire(page, None, [lan])
    _wire(page, "thoughts_notes", [local])
    _wire(page, "speech_recognition", [("whisper-small", 1)])


def _no_raw_buttons(page: Any) -> None:
    raw = page.get_by_test_id("runson-root").locator("button:not(.btn):not(.gadget-chip-egress)")
    assert raw.count() == 0, f"raw <button>: {raw.count()}"


@pytest.mark.parametrize("width", [1440, 393], ids=["desktop", "phone"])
def test_runs_on_switchboard(tmp_path: Path, monkeypatch: Any, width: int) -> None:
    server, url, fakes, ticks = _rig(tmp_path, monkeypatch)
    errors: list[str] = []
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": width, "height": 900 if width == 1440 else 852})
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.goto(f"{url}/?token={TOKEN}", wait_until="load")
            _api(page, "POST", "/api/desk/seed", token=TOKEN)
            _normal_chair(page)
            _seed(page, fakes[2].server_address[1])
            _open_runs_on(page)
            # The engines fill in once detection lands.
            page.get_by_test_id("switchboard-found-cap").wait_for(timeout=15_000)
            assert page.locator('[role="dialog"]').count() == 0
            _no_raw_buttons(page)
            fact = page.get_by_test_id("runson-fact").inner_text()
            assert fact.startswith("7 jobs"), fact
            assert float(page.get_by_test_id("runson-fact").evaluate("e => parseFloat(getComputedStyle(e).fontSize)")) >= 24
            words = page.locator("[data-testid^='switchboard-job-']").evaluate_all(
                "els => els.map(e => e.getAttribute('data-state'))"
            )
            assert words and set(words) <= {"ready", "limited", "broken", "waiting", "off"}, words
            for retired in ("Use these", "Use this for summaries", "Adjust"):
                assert page.get_by_role("button", name=retired, exact=True).count() == 0

            if width == 1440:
                board = page.get_by_test_id("switchboard")
                assert board.get_attribute("data-layout") == "board"
                wires = page.get_by_test_id("switchboard-wire")
                assert wires.count() >= 3
                assert all(wires.nth(i).get_attribute("d") for i in range(wires.count()))
                _shot(page, "c1-board", width)

                # Drag the LAN engine onto Meetings: one write, a receipt, Undo.
                lan_plate = page.locator("[data-testid^='switchboard-engine-']").filter(has_text="qwen3.8 27B").first
                with page.expect_response(lambda r: r.url.endswith("/api/inference/assignments/set")) as written:
                    lan_plate.drag_to(page.get_by_test_id("switchboard-job-meetings"))
                assert written.value.ok, written.value.text()
                body = written.value.request.post_data_json
                assert body["scope"] == {"kind": "group", "group_id": "meetings"}
                assert isinstance(body["expected_revision"], int)
                receipt = page.get_by_test_id("runson-receipt")
                receipt.wait_for()
                page.wait_for_function(
                    "() => /^PATCHED .* · Meetings → /.test(document.querySelector('[data-testid=runson-receipt]')?.textContent || '')"
                )
                page.get_by_test_id("runson-undo").wait_for()
                assert "192.168.77.43" in page.get_by_test_id("runson-egress").inner_text()
                # The meeting queue reads only the exact capability row: it is written too.
                tasks = _api(page, "GET", "/api/inference/assignments", token=TOKEN)["task_overrides"]
                summaries = next(t for t in tasks if t["id"] == "meeting.deferred_analysis")
                assert summaries["has_override"] is True, summaries
                _shot(page, "c2-patched", width)

                # Try it on Meetings: off-machine, so the press names the host first.
                page.get_by_test_id("runson-try-meetings").click()
                confirm = page.get_by_test_id("runson-try-confirm")
                confirm.wait_for()
                assert "192.168.77.43" in confirm.inner_text()
                confirm.click()
                page.get_by_test_id("switchboard-result-meetings").wait_for()
                page.wait_for_function(
                    "() => /^REACHED · qwen3\\.8 27B$/i.test(document.querySelector('[data-testid=switchboard-result-meetings]')?.textContent || '')"
                )
                # Thoughts & notes runs a real request through its route (the Ask probe).
                page.get_by_test_id("runson-try-thoughts_notes").click()
                # An endpoint profile's route names a network boundary even on
                # loopback, so the probe waits for the press (Article III).
                page.get_by_test_id("runson-try-confirm").click()
                thoughts = page.get_by_test_id("switchboard-result-thoughts_notes")
                thoughts.wait_for()
                page.wait_for_function(
                    "() => !/TRYING/.test(document.querySelector('[data-testid=switchboard-result-thoughts_notes]')?.textContent || 'TRYING')",
                    timeout=15_000,
                )
                assert thoughts.inner_text().upper().startswith("READY · "), thoughts.inner_text()
                _shot(page, "c3-try-it", width)

                # FOUND → Use it: the engine joins the column with no wire.
                found = page.locator(".switchboard-engine.is-found").first
                found.wait_for()
                _shot(page, "c4-found", width)
                with page.expect_response(lambda r: r.url.endswith("/define-endpoint")) as used:
                    found.get_by_role("button", name="Use it").click()
                assert used.value.ok, used.value.text()
                page.wait_for_function(
                    "() => /^ADDED /.test(document.querySelector('[data-testid=runson-receipt]')?.textContent || '')"
                )
                page.locator(".switchboard-engine.is-found").first.wait_for(state="detached", timeout=15_000)
                _shot(page, "c5-after-use-it", width)

                # Download: the chip names the internet host; the bar fills on the plate.
                plate = page.locator("[data-testid='switchboard-engine-preset:preset_glass_vision']")
                assert "HUGGINGFACE.CO" in plate.inner_text()
                assert "THIS DEVICE" not in plate.inner_text()
                plate.get_by_role("button", name="Download").click()
                bar = page.get_by_test_id("switchboard-bar-preset:preset_glass_vision")
                bar.wait_for(timeout=10_000)
                page.wait_for_function(
                    "() => Number(document.querySelector(\"[data-testid='switchboard-bar-preset:preset_glass_vision']\")?.getAttribute('aria-valuenow')) >= 40"
                )
                _shot(page, "c6-download-mid-bar", width)
                ticks["hold"] = 0
                page.wait_for_function(
                    "() => /^DOWNLOADED /.test(document.querySelector('[data-testid=runson-receipt]')?.textContent || '')",
                    timeout=10_000,
                )
            else:
                board = page.get_by_test_id("switchboard")
                assert board.get_attribute("data-layout") == "list"
                assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
                small = page.evaluate("""() => [...document.querySelectorAll('[data-testid=runson-root] .btn, [data-testid=switchboard] .switchboard-tap')]
                    .filter(e => e.offsetParent !== null)
                    .map(e => [e.textContent.trim().slice(0, 30), e.getBoundingClientRect().height])
                    .filter(([, h]) => h < 44)""")
                assert small == [], small
                _shot(page, "c1-list", width)
                # Open Meetings and tap an engine to patch it.
                page.get_by_test_id("switchboard-job-meetings").click()
                page.get_by_text("Meetings · runs on").wait_for()
                tap = page.locator("[data-testid^='switchboard-tap-']").first
                with page.expect_response(lambda r: r.url.endswith("/api/inference/assignments/set")) as written:
                    tap.click()
                assert written.value.ok, written.value.text()
                page.get_by_test_id("runson-undo").wait_for()
                assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
                _shot(page, "c2-list-patched", width)
            # Meaning search (ratified: a row under the board) scrolls into
            # the body, clear of the window's foot.
            meaning = page.locator(".runson-meaning > *").first
            meaning.scroll_into_view_if_needed()
            _settle(page)
            clear = page.evaluate("""() => {
              const row = document.querySelector('.runson-meaning > *');
              const win = row && row.closest('.desk-surface-window');
              const foot = win && win.querySelector('.surface-footer-layout');
              if (!row || !foot) return 'missing';
              const r = row.getBoundingClientRect(), f = foot.getBoundingClientRect();
              return r.height > 0 && r.bottom <= f.top + 1 ? true : `row ${r.top}-${r.bottom} foot ${f.top}`;
            }""")
            assert clear is True, clear
            _shot(page, "c7-meaning-search" if width == 1440 else "c3-meaning-search", width)
            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()
        for fake in fakes:
            fake.shutdown()


# ── Astra round 1 (08e19c07b): the five reproduced transitions, on the real
#    producer (her assertions, ported) ──


@pytest.mark.parametrize(
    "case", ["lost_update", "meeting_undo", "inherited_mobile", "stale_confirmation", "download_failure"]
)
def test_astra_review_real_producer(tmp_path: Path, monkeypatch: Any, case: str) -> None:
    server, url, fakes, ticks = _rig(tmp_path, monkeypatch)
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": 393 if case == "inherited_mobile" else 1440, "height": 900})
            page.goto(f"{url}/?token={TOKEN}", wait_until="load")
            _api(page, "POST", "/api/desk/seed", token=TOKEN)
            _normal_chair(page)
            _seed(page, fakes[2].server_address[1])
            _open_runs_on(page)
            page.get_by_test_id("switchboard-found-cap").wait_for(timeout=15_000)
            receipt = "() => document.querySelector('[data-testid=runson-receipt]')?.textContent || ''"

            if case == "inherited_mobile":
                page.get_by_test_id("switchboard-job-meetings").click()
                row = next(r for r in _api(page, "GET", "/api/inference/assignments", token=TOKEN)["rows"] if r["id"] == "meetings")
                assert row["inherited_from"] == "global"
                current = page.locator(".switchboard.is-list > .switchboard-engine")
                assert current.filter(has_text="qwen3.8 27B").count() == 1, (
                    "The inherited engine must appear under Meetings runs on, not only as an Or alternative"
                )
                assert "FOLLOWS DEFAULT" in (current.filter(has_text="qwen3.8 27B").first.text_content() or "")
                assert page.get_by_test_id("switchboard-tap-glass-lan-27b").count() == 0
                return

            if case == "stale_confirmation":
                # Press Try on Meetings (it follows the LAN default), then
                # patch Meetings to the loopback engine; the old press must go.
                page.get_by_test_id("runson-try-meetings").click()
                confirm = page.get_by_test_id("runson-try-confirm")
                confirm.wait_for()
                assert "192.168.77.43" in confirm.inner_text()
                probes: list[str] = []
                page.on("request", lambda r: probes.append(r.post_data or "") if r.url.endswith("/api/concierge/probe") else None)
                with page.expect_response(lambda r: r.url.endswith("/api/inference/assignments/set")):
                    page.get_by_test_id("switchboard-engine-glass-mac-4b").drag_to(page.get_by_test_id("switchboard-job-meetings"))
                # The new engine is on this machine: no press is needed, and
                # no press for the old host survives.
                page.wait_for_function("() => !document.querySelector('[data-testid=runson-try-confirm]')")
                assert probes == [], probes
                return

            if case == "download_failure":
                from holdspeak.services.inference_acquisition_service import InferenceAcquisitionApplicationService

                def failed(self: Any, principal: Any, job_id: str) -> dict[str, Any]:
                    return {"acquisition": {
                        "id": job_id, "preset_id": "preset_glass_vision", "state": "failed",
                        "verified_bytes": 0, "transport_bytes": 0, "bytes_total": 890_000_000,
                        "error": {"code": "model_download_network", "message": "The network stopped."},
                    }}

                monkeypatch.setattr(InferenceAcquisitionApplicationService, "get_acquisition", failed)
                plate = page.locator("[data-testid='switchboard-engine-preset:preset_glass_vision']")
                plate.get_by_role("button", name="Download").click()
                page.wait_for_function(f"() => /DOWNLOAD STOPPED .* · NETWORK$/.test(({receipt})())", timeout=15_000)
                lamp = page.locator("[data-testid='switchboard-lamp-preset:preset_glass_vision']")
                assert lamp.get_attribute("data-lamp") == "broken"
                assert "STOPPED · NETWORK" in plate.inner_text()
                assert "NOT DOWNLOADED" not in plate.inner_text()
                return

            job = "thoughts_notes" if case == "lost_update" else "meetings"
            before = _api(page, "GET", "/api/inference/assignments", token=TOKEN)
            lan_plate = page.get_by_test_id("switchboard-engine-glass-lan-27b")
            with page.expect_response(lambda r: r.url.endswith("/api/inference/assignments/set")) as patched:
                lan_plate.drag_to(page.get_by_test_id(f"switchboard-job-{job}"))
            assert patched.value.ok, patched.value.text()
            page.wait_for_function(f"() => /^PATCHED /.test(({receipt})())")
            if case == "lost_update":
                roster = _api(page, "GET", "/api/inference/assignments", token=TOKEN)
                row = next(r for r in roster["rows"] if r["id"] == job)
                writer_b = _api(page, "POST", "/api/inference/assignments/set", {
                    "command_id": "astra-writer-b", "expected_revision": row["expected_revision"],
                    "scope": {"kind": "group", "group_id": job},
                    "entries": [{"profile_id": "glass-mac-4b", "profile_revision": 1},
                                {"profile_id": "glass-lan-27b", "profile_revision": 1}],
                }, token=TOKEN)
                assert writer_b["revision"] == row["expected_revision"] + 1
            page.get_by_test_id("runson-undo").click()
            page.wait_for_function(f"() => /^(UNDONE|CHANGED ELSEWHERE)/.test(({receipt})())")
            after = _api(page, "GET", "/api/inference/assignments", token=TOKEN)
            said = page.get_by_test_id("runson-receipt").inner_text()
            if case == "lost_update":
                row = next(r for r in after["rows"] if r["id"] == job)
                observed = [e["profile_id"] for e in row["assignment"]["entries"]]
                assert observed == ["glass-mac-4b", "glass-lan-27b"], "Undo must not overwrite the intervening writer's chain"
                assert said.upper().startswith("CHANGED ELSEWHERE"), said
                assert page.get_by_test_id("runson-undo").count() == 0
            else:
                prior = next(r for r in before["task_overrides"] if r["id"] == "meeting.deferred_analysis")
                current = next(r for r in after["task_overrides"] if r["id"] == "meeting.deferred_analysis")
                assert not prior["has_override"]
                assert not current["has_override"], "Undo of first Meetings patch must remove its exact summary override"
                meetings = next(r for r in after["rows"] if r["id"] == "meetings")
                assert meetings["inherited_from"] == "global", meetings
                assert said.upper().startswith("UNDONE"), said
            browser.close()
    finally:
        server.stop()
        for fake in fakes:
            fake.shutdown()
