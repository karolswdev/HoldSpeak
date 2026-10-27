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

Was tests/e2e/test_hs170_concierge_glass.py. The test diet (push 2,
2026-10-12) kept the cases that DRAG a plate onto a job (a real browser's
drag); Astra's non-drag cases (inherited engine at 393, host moves, a failed
download, the summary override at 1440 and 393) are the vitest cases of
web/src/features/runson/__tests__/runsOn.test.tsx.
"""
from __future__ import annotations

import ipaddress
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

import pytest

from tests._evidence import evidence_dir

from .glass_infra import _api, _assert_clean, _boot, _normal_chair, _settle
from .fit_rig import BOX_JS, T, WIDTHS, FitRig, TOKEN as FIT_TOKEN
from .type_floor_rig import HIT_PROBE_JS, OWNERSHIP_JS

SHOTS = evidence_dir("docs/internal/philo/phase-16/c-shots")
TOKEN = "glass-test"
LAN_BASE = "http://192.168.77.43:8080/v1"
MODELS_LATENCY_S = 0.005
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
            # A real engine answers in milliseconds, never in under one: the
            # probe's measured latency (int ms) is then always > 0 and the
            # Try it result always carries its "· N MS" token. Without this the
            # token showed only under load (the tape flake, 2026-10-12).
            time.sleep(MODELS_LATENCY_S)
            self._json({"object": "list", "data": [{"id": self.MODEL, "object": "model"}]})
            return
        self.send_response(404)
        self.end_headers()

    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers.get("Content-Length") or 0)
        request = json.loads(self.rfile.read(length))
        if "chat/completions" in self.path:
            self.server.model_requests.append(request)
            # The current Try it runs the task's semantic adapter. Meeting
            # summaries require valid typed JSON; Answers keep a plain line.
            typed = (request.get("response_format") or {}).get("type") == "json_object"
            content = json.dumps({"topics": ["Settings fix"], "summary": "Ship the settings fix on Tuesday.",
                                  "action_items": [], "decisions": []}) if typed else "ready"
            self._json({
                "id": "fake", "object": "chat.completion", "model": self.MODEL,
                "choices": [{"index": 0, "finish_reason": "stop",
                             "message": {"role": "assistant", "content": content}}],
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
    server.model_requests = []
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


def _doubles(
    monkeypatch: Any,
    lan_port: int,
    found_port: int,
    *,
    include_loopback: bool = True,
) -> dict[str, int]:
    """The network doubles: the LAN address answers from the fake server; the
    loopback scan finds one more; a catalog download advances in place."""
    import holdspeak.inference_setup_catalog as catalog
    import holdspeak.services.concierge_service as cs
    import holdspeak.setup_runtime as setup_runtime
    import holdspeak.intel as intel
    from holdspeak.loopback_http import is_loopback_url, loopback_httpx_client
    from holdspeak.services.inference_acquisition_service import InferenceAcquisitionApplicationService

    ticks = {"n": 0, "hold": 1, "moved": 0}
    real_discover = setup_runtime.discover_endpoint_models

    def discover(base_url: str, *args: Any, **kwargs: Any) -> Any:
        url = str(base_url)
        for lan in ("192.168.77.43:8080", "192.168.77.44:8080"):
            url = url.replace(lan, f"127.0.0.1:{lan_port}")
        return real_discover(url, *args, **kwargs)

    monkeypatch.setattr(setup_runtime, "discover_endpoint_models", discover)

    real_openai = intel.OpenAI

    def fixture_openai(**kwargs: Any) -> Any:
        base = str(kwargs.get("base_url") or "")
        if base.rstrip("/") in {LAN_BASE, LAN_BASE.replace(".43:", ".44:")}:
            kwargs["base_url"] = f"http://127.0.0.1:{lan_port}/v1"
            kwargs["http_client"] = loopback_httpx_client(kwargs.get("timeout"))
        else:
            assert is_loopback_url(base), "Only fixture endpoints can create a model client"
        # Freeze/admission still names the LAN deployment. Only the physical
        # SDK transport reaches this process's local fake, with no proxy.
        return real_openai(**kwargs)

    monkeypatch.setattr(intel, "OpenAI", fixture_openai)

    real_detect = cs.detect

    def detect(**kwargs: Any) -> Any:
        if include_loopback:
            kwargs["loopback_scan"] = lambda: [{
                "id": f"local:ollama:{found_port}:llama3.3", "model": "llama3.3",
                "base_url": f"http://127.0.0.1:{found_port}/v1", "engine": "ollama", "port": found_port,
            }]
        else:
            # The LAN case must get its Found row from discover-lan, not from
            # the normal loopback detection read that opens the board.
            kwargs["loopback_scan"] = lambda: []
        result = real_detect(**kwargs)
        if ticks.get("moved"):
            # The same engine id, answered at another LAN address (a
            # re-defined endpoint seen by the next detection).
            for engine in result["engines"]:
                if engine.get("host") == "192.168.77.43":
                    engine["host"] = "192.168.77.44"
                    engine["baseUrl"] = str(engine.get("baseUrl", "")).replace("192.168.77.43", "192.168.77.44")
        return result

    monkeypatch.setattr(cs, "detect", detect)

    preset = {
        "id": "preset_glass_vision", "kind": "local_artifact_preset", "activation": "download",
        "label": "Qwen 3.5 4B vision file", "source": {"download_bytes": 890_000_000},
    }
    monkeypatch.setattr(catalog, "applicable_presets", lambda **_: [preset])


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


def _builder_tools_on(page: Any, *, token: str = TOKEN) -> None:
    """Betterment E5 (DECISIONS #8): the drag switchboard these tests drive is
    parked behind Builder tools (Settings > System; web/src/desk/builderTools.ts);
    What runs where is the default face. Turn the switch on for every load."""
    # Builder tools are a hub preference; seed it through the same Settings
    # writer as the real face, then reload so DeskApp hydrates the value.
    settings = _api(page, "GET", "/api/settings", token=token)
    settings.setdefault("ui", {})["builder_tools"] = True
    _api(page, "PUT", "/api/settings", settings, token=token)
    page.reload(wait_until="load")


def _assignment_board(page: Any) -> Any:
    """The jobs and saved engines, distinct from Found and Downloads."""
    return page.get_by_test_id("runson-assignments").get_by_test_id("switchboard")


def _found_board(page: Any) -> Any:
    return page.get_by_test_id("runson-found-engines").get_by_test_id("switchboard")


def _open_runs_on(page: Any) -> None:
    page.evaluate(
        """([key]) => sessionStorage.setItem("hs.desk.staged-surface-open", JSON.stringify({key}))""",
        ["open-concierge"],
    )
    page.reload(wait_until="load")
    _normal_chair(page)
    page.get_by_test_id("runson-root").wait_for(timeout=15_000)
    _assignment_board(page).wait_for(timeout=15_000)


def _ensure_wide_runs_on(page: Any) -> None:
    """Use the window's Zoom verb before asserting the three column board."""
    board = _assignment_board(page)
    if board.get_attribute("data-layout") == "board":
        return
    zoom = _window(page).locator("button[aria-label^='Zoom ']")
    zoom.wait_for(timeout=15_000)
    zoom.click()
    page.wait_for_function(
        "() => document.querySelector('[data-testid=runson-assignments] [data-testid=switchboard]')?.getAttribute('data-layout') === 'board'",
        timeout=15_000,
    )


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


def _rig(
    tmp_path: Path,
    monkeypatch: Any,
    *,
    include_loopback: bool = True,
) -> tuple[Any, str, list[ThreadingHTTPServer], dict[str, int]]:
    lan, found, local = _serve(), _serve("llama3.3"), _serve("qwen3.5-4b")
    ticks = _doubles(
        monkeypatch,
        lan.server_address[1],
        found.server_address[1],
        include_loopback=include_loopback,
    )
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    return server, url, [lan, found, local], ticks


def _seed(page: Any, local_port: int) -> tuple[tuple[str, int], tuple[str, int]]:
    lan = _define(page, LAN_BASE, "qwen3.8-27b", "glass-lan-27b", "qwen3.8 27B")
    local = _define(page, f"http://127.0.0.1:{local_port}/v1", "qwen3.5-4b", "glass-mac-4b", "Qwen 3.5 4B")
    _speech_engine()
    _wire(page, None, [lan])
    _wire(page, "thoughts_notes", [local])
    _wire(page, "speech_recognition", [("whisper-small", 1)])
    return lan, local


def _no_raw_buttons(page: Any) -> None:
    raw = page.get_by_test_id("runson-root").locator("button:not(.btn):not(.gadget-chip-egress)")
    assert raw.count() == 0, f"raw <button>: {raw.count()}"


def _whole_hit(control: Any) -> None:
    observed = control.evaluate("(el) => {" + OWNERSHIP_JS + HIT_PROBE_JS + "return hs202Probe(el, 44, 'Runs on'); }")
    assert not observed["occluded"] and not observed["covered"] and not observed["bad"], observed
    assert observed["w"] >= 44 and observed["h"] >= 44, observed


def _probe_task_once(page: Any, job: str, capability: str, profile_id: str, fake: Any, *, off_machine: bool) -> None:
    """One current Try gesture: the bound public sample and its real receipt."""
    before = _assignment_snapshot(_api(page, "GET", "/api/inference/assignments", token=TOKEN))
    physical_before = len(fake.model_requests)
    pressed: list[Any] = []

    def record(request: Any) -> None:
        if request.url.endswith("/api/concierge/probe") and request.method == "POST":
            pressed.append(request)

    page.on("request", record)
    try:
        with page.expect_response(lambda response: response.url.endswith("/api/concierge/probe")
                                  and response.request.method == "POST") as tried:
            page.get_by_test_id(f"runson-try-{job}").click()
    finally:
        page.remove_listener("request", record)
    assert tried.value.ok, tried.value.text()
    expected: dict[str, Any] = {"task": True, "capabilityId": capability, "expectedProfileIds": [profile_id]}
    if off_machine:
        expected["confirmOffMachine"] = True
    assert len(pressed) == 1 and pressed[0].post_data_json == expected, [request.post_data_json for request in pressed]
    answer = tried.value.json()
    assert answer["ok"] is True and answer["state"] == "READY" and answer["outcome"] == "succeeded", answer
    assert answer["operationId"] and answer["executionId"] and answer["routePlanId"], answer
    assert answer["legs"] and all(leg["profileId"] == profile_id for leg in answer["legs"]), answer
    assert answer["sampleInput"] and answer["sampleOutput"] and not answer["emptyOutput"], answer
    assert answer["latencyMs"] > 0, answer
    assert len(fake.model_requests) == physical_before + 1
    physical = fake.model_requests[-1]
    assert physical["model"] == answer["model"] and physical["messages"][-1]["content"] == answer["sampleInput"], physical
    state = page.get_by_test_id(f"runson-trial-state-{job}")
    state.filter(has_text="Completed").wait_for()
    assert state.inner_text().startswith("Completed · ") and f"{answer['latencyMs']} MS" in state.inner_text()
    assert page.get_by_test_id(f"runson-trial-input-{job}").text_content() == answer["sampleInput"]
    assert page.get_by_test_id(f"runson-trial-output-{job}").text_content() == answer["sampleOutput"]
    assert _assignment_snapshot(_api(page, "GET", "/api/inference/assignments", token=TOKEN)) == before
    assert page.get_by_test_id("runson-try-confirm").count() == 0


def _assignment_snapshot(payload: dict[str, Any]) -> str:
    """Keep the durable assignment facts comparable across the adoption read."""
    rows = []
    for row in payload.get("rows", []):
        assignment = row.get("assignment") or {}
        rows.append({
            "id": row.get("id"),
            "inherited_from": row.get("inherited_from"),
            "expected_revision": row.get("expected_revision"),
            "assignment_revision": assignment.get("revision"),
            "entries": [
                (entry.get("profile_id"), entry.get("profile_revision"))
                for entry in assignment.get("entries", [])
            ],
        })
    tasks = [
        (task.get("id"), task.get("has_override"))
        for task in payload.get("task_overrides", [])
    ]
    return json.dumps({"rows": rows, "tasks": tasks}, sort_keys=True)


def _library_profile_ids(page: Any) -> list[str]:
    library = _api(page, "GET", "/api/inference/model-library", token=TOKEN)
    return sorted(
        str(row.get("id"))
        for row in library.get("rows", [])
        if str(row.get("id", "")).startswith("profile:")
    )


def _install_lan_scanner_double(monkeypatch: Any) -> tuple[str, list[str], list[str]]:
    """Run the production LAN scanner against one injected fake target."""
    from holdspeak.services import lan_engine_discovery
    import holdspeak.setup_runtime as setup_runtime

    expected_url = "http://192.168.77.44:8080/v1"
    probe_urls: list[str] = []
    discover_urls: list[str] = []
    real_scan = lan_engine_discovery.scan_lan_engines
    real_discover = setup_runtime.discover_endpoint_models

    def probe(url: str) -> dict[str, Any]:
        probe_urls.append(url)
        # Every candidate is handled by this injected probe. Only the target
        # is allowed to call the existing /v1/models double; all other hosts
        # are refused without opening a socket.
        if url != expected_url:
            return {"ok": False, "models": []}
        discover_urls.append(url)
        return real_discover(url, timeout_seconds=1.0)

    def scan(*, principal: Any) -> dict[str, Any]:
        return real_scan(
            interfaces=[
                lan_engine_discovery.LanInterface(
                    ipaddress.IPv4Address("192.168.77.45"),
                    ipaddress.IPv4Network("192.168.77.40/29"),
                )
            ],
            ports=[(8080, "openai-compatible")],
            probe=probe,
            max_workers=8,
            principal=principal,
        )

    monkeypatch.setattr(lan_engine_discovery, "scan_lan_engines", scan)
    return expected_url, probe_urls, discover_urls


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
            _builder_tools_on(page)
            _api(page, "POST", "/api/desk/seed", token=TOKEN)
            _normal_chair(page)
            _seed(page, fakes[2].server_address[1])
            _open_runs_on(page)
            if width == 1440:
                _ensure_wide_runs_on(page)
            # The engines fill in once detection lands.
            _found_board(page).get_by_test_id("switchboard-found-cap").wait_for(timeout=15_000)
            assert page.locator('[role="dialog"]').count() == 0
            _no_raw_buttons(page)
            fact = page.get_by_test_id("runson-fact").inner_text()
            # PHILO-17 (U16): the one fact is what he has, never "7 jobs".
            assert "jobs" not in fact and (fact.endswith("engine") or fact.endswith("engines") or fact == "No engine yet"), fact
            # Each card leads with what he gets and where it runs; task ids
            # are the card's details (its title), never its face.
            # PHILO-17 refit: the engine is a pill and the arrow is not drawn;
            # the lead still reads whole as text.
            lead = page.locator("[data-testid='switchboard-job-meetings'] .switchboard-job-name").text_content() or ""
            if width == 1440:
                # The board draws the route in a soft pill. The arrow remains
                # in the lead's text content while the pill gives the visual
                # route its own bounded cell.
                assert lead.startswith("Meeting summaries → ") and " · on " in lead, lead
                where = page.locator("[data-testid='switchboard-job-meetings'] .switchboard-job-pill").inner_text()
                assert "Qwen3.8 27B" in where and " · ON " in where.upper() and "192.168.77.43" in where, where
                default_name = page.locator("[data-testid='switchboard-job-default'] .switchboard-job-name").text_content() or ""
                assert default_name == "Default engine → Qwen3.8 27B · on 192.168.77.43", default_name
            else:
                # The phone list: the outcome name, its engine and place under it.
                assert lead == "Meeting summaries", lead
                # PHILO-17 refit: the engine and place are the job's pill.
                where = page.locator("[data-testid='switchboard-job-meetings'] .switchboard-job-pill").inner_text()
                assert " · ON " in where.upper(), where
            jobs_text = _assignment_board(page).inner_text().upper()
            job_labels = {line.strip() for line in jobs_text.splitlines()}
            for gone in ("TASKS", "FOLLOWS DEFAULT", "EVERY JOB WITHOUT ITS OWN WIRE", "DICTATION INTENT"):
                assert gone not in job_labels, gone
            # Window grammar (2026-10-24): no headline inside the window; the
            # one fact is the status bar's first word (readable, 12 px or more).
            assert page.get_by_test_id("runson-fact").evaluate("e => !!e.closest('.kit-statusbar')")
            assert float(page.get_by_test_id("runson-fact").evaluate("e => parseFloat(getComputedStyle(e).fontSize)")) >= 12
            words = page.locator("[data-testid^='switchboard-job-']").evaluate_all(
                "els => els.map(e => e.getAttribute('data-state'))"
            )
            assert words and set(words) <= {"ready", "limited", "broken", "waiting", "off"}, words
            for retired in ("Use these", "Use this for summaries", "Adjust"):
                assert page.get_by_role("button", name=retired, exact=True).count() == 0

            if width == 1440:
                board = _assignment_board(page)
                assert board.get_attribute("data-layout") == "board"
                wires = page.get_by_test_id("switchboard-wire")
                assert wires.count() >= 3
                assert all(wires.nth(i).get_attribute("d") for i in range(wires.count()))
                _shot(page, "c1-board", width)

                # Drag the LAN engine onto Meetings: one write, a receipt, Undo.
                lan_plate = page.locator("[data-testid^='switchboard-engine-']").filter(has_text="qwen3.8 27B").first
                before_patch = _api(page, "GET", "/api/inference/assignments", token=TOKEN)
                before_meetings = next(row for row in before_patch["rows"] if row["id"] == "meetings")
                group_writes: list[Any] = []

                def record_patch(request: Any) -> None:
                    if request.method == "POST" and request.url.endswith("/api/inference/assignments/set"):
                        group_writes.append(request)

                page.on("request", record_patch)
                with page.expect_response(lambda r: r.url.endswith("/api/inference/assignments/set")) as written:
                    lan_plate.drag_to(page.get_by_test_id("switchboard-job-meetings"))
                page.remove_listener("request", record_patch)
                assert written.value.ok, written.value.text()
                assert len(group_writes) == 1
                body = written.value.request.post_data_json
                assert body["scope"] == {"kind": "group", "group_id": "meetings"}
                assert body["expected_revision"] == before_meetings["expected_revision"]
                assert body["entries"][0]["profile_id"] == "glass-lan-27b"
                receipt = page.get_by_test_id("runson-receipt")
                receipt.wait_for()
                page.wait_for_function(
                    "() => /^PATCHED .* · Meeting summaries → /.test(document.querySelector('[data-testid=runson-receipt]')?.textContent || '')"
                )
                page.get_by_test_id("runson-undo").wait_for()
                assert "192.168.77.43" in page.get_by_test_id("runson-egress").inner_text()
                # The meeting queue reads only the exact capability row: it is written too.
                tasks = _api(page, "GET", "/api/inference/assignments", token=TOKEN)["task_overrides"]
                summaries = next(t for t in tasks if t["id"] == "meeting.deferred_analysis")
                assert summaries["has_override"] is True, summaries
                _shot(page, "c2-patched", width)

                # The current row names the off-machine host beside the one
                # Try gesture; admission freezes the displayed profile ids.
                assert "192.168.77.43" in page.get_by_test_id("runson-trial-egress-meetings").inner_text()
                _probe_task_once(page, "meetings", "meeting.deferred_analysis", "glass-lan-27b", fakes[0], off_machine=True)
                _probe_task_once(page, "thoughts_notes", "ask.answer", "glass-mac-4b", fakes[2], off_machine=False)
                _shot(page, "c3-try-it", width)

                # FOUND → Use it: the engine joins the column with no wire.
                found = _found_board(page).locator(".switchboard-engine.is-found")
                found.wait_for()
                _shot(page, "c4-found", width)
                with page.expect_response(lambda r: r.url.endswith("/define-endpoint")) as used:
                    found.get_by_role("button", name="Use it").click()
                assert used.value.ok, used.value.text()
                page.wait_for_function(
                    "() => /^ADDED /.test(document.querySelector('[data-testid=runson-receipt]')?.textContent || '')"
                )
                found.wait_for(state="detached", timeout=15_000)
                _shot(page, "c5-after-use-it", width)

                # Download: the chip names the internet host; the bar fills on the plate.
                downloads = page.locator(".runson-downloads")
                if downloads.get_attribute("open") is None:
                    downloads.locator("summary").click()
                plate = page.locator("[data-testid='switchboard-engine-preset:preset_glass_vision']")
                plate.wait_for(state="visible")
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
                board = _assignment_board(page)
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
                page.get_by_text("Meeting summaries · engine").wait_for()
                # The list opens on the selected job's alternatives. Choose
                # the known loopback engine explicitly; the first tap is not
                # a stable contract because the list can contain other jobs.
                tap = page.get_by_test_id("switchboard-tap-glass-mac-4b")
                with page.expect_response(lambda r: r.url.endswith("/api/inference/assignments/set")) as written:
                    tap.click()
                assert written.value.ok, written.value.text()
                body = written.value.request.post_data_json
                assert body["scope"] == {"kind": "group", "group_id": "meetings"}
                assert body["entries"][0]["profile_id"] == "glass-mac-4b"
                _shot(page, "c2-list-patched", width)
                # With no primary verb, SurfaceFooter keeps the first action.
                # Runs on's Undo is that action at both widths.
                page.locator(".runson-foot").get_by_test_id("runson-undo").click()
                page.wait_for_function(
                    "() => /^UNDONE /.test(document.querySelector('[data-testid=runson-receipt]')?.textContent || '')"
                )
                after = _api(page, "GET", "/api/inference/assignments", token=TOKEN)
                meetings = next(row for row in after["rows"] if row["id"] == "meetings")
                assert meetings["inherited_from"] == "global", meetings
                summaries = next(task for task in after["task_overrides"] if task["id"] == "meeting.deferred_analysis")
                assert summaries["has_override"] is False, summaries
                assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
            # Optional local models and Meaning search live in this real
            # disclosure. A closed details descendant has no reachable row.
            downloads = page.locator(".runson-downloads")
            if downloads.get_attribute("open") is None:
                downloads.locator("summary").click()
            meaning = page.locator(".runson-meaning > *").first
            meaning.wait_for(state="visible")
            meaning.scroll_into_view_if_needed()
            _settle(page)
            clear = page.evaluate("""() => {
              const row = document.querySelector('.runson-meaning > *');
              const win = row && row.closest('.desk-surface-window');
              const foot = win && win.querySelector('.kit-statusbar');
              if (!row || !foot) return 'missing';
              const r = row.getBoundingClientRect(), f = foot.getBoundingClientRect();
              return r.height > 0 && r.bottom <= f.top + 1 ? true : `row ${r.top}-${r.bottom} foot ${f.top}`;
            }""")
            assert clear is True, clear
            if width == 393:
                _whole_hit(meaning.get_by_test_id("meaning-search-verb"))
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
    "case", ["lost_update", "meeting_undo", "stale_confirmation"]
)
def test_astra_review_real_producer(tmp_path: Path, monkeypatch: Any, case: str) -> None:
    server, url, fakes, ticks = _rig(tmp_path, monkeypatch)
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            page.goto(f"{url}/?token={TOKEN}", wait_until="load")
            _builder_tools_on(page)
            _api(page, "POST", "/api/desk/seed", token=TOKEN)
            _normal_chair(page)
            lan, local = _seed(page, fakes[2].server_address[1])
            _open_runs_on(page)
            _ensure_wide_runs_on(page)
            _found_board(page).get_by_test_id("switchboard-found-cap").wait_for(timeout=15_000)
            receipt = "() => document.querySelector('[data-testid=runson-receipt]')?.textContent || ''"

            if case == "stale_confirmation":
                # Try now admits the displayed route in one press. Hold its
                # transport while a real UI patch changes that route: the old
                # off-machine permission must not admit the new selection.
                shown = page.get_by_test_id("switchboard-job-meetings")
                assert "192.168.77.43" in shown.get_by_test_id("runson-trial-egress-meetings").inner_text()
                pending: list[Any] = []
                page.route("**/api/concierge/probe", lambda route: pending.append(route))
                with page.expect_request(lambda r: r.url.endswith("/api/concierge/probe")) as pressed:
                    shown.get_by_test_id("runson-try-meetings").click()
                body = pressed.value.post_data_json
                assert body == {"task": True, "capabilityId": "meeting.deferred_analysis",
                                "confirmOffMachine": True, "expectedProfileIds": ["glass-lan-27b"]}, body
                assert len(pending) == 1, pending
                dispatches: list[str] = []
                real_model_post = _FakeOpenAI.do_POST

                def record_model_post(handler: Any) -> None:
                    dispatches.append(handler.path)
                    real_model_post(handler)

                monkeypatch.setattr(_FakeOpenAI, "do_POST", record_model_post)
                with page.expect_response(lambda r: r.url.endswith("/api/inference/assignments/set")) as changed:
                    page.get_by_test_id("switchboard-engine-glass-mac-4b").drag_to(page.get_by_test_id("switchboard-job-meetings"))
                assert changed.value.ok, changed.value.text()
                # Meetings patches its group and its summary capability.
                # The receipt follows both writes, so admission sees the
                # completed change rather than an intermediate group write.
                page.wait_for_function(f"() => /^PATCHED /.test(({receipt})())")
                with page.expect_response(lambda r: r.url.endswith("/api/concierge/probe")) as refused:
                    pending[0].continue_()
                answer = refused.value.json()
                assert refused.value.ok, answer
                assert answer["state"] == "REFUSED" and answer["reasonCode"] == "route_probe_assignment_changed", answer
                assert answer["legs"] and all(leg["profileId"] == "glass-mac-4b" for leg in answer["legs"]), answer
                assert not answer.get("model") and dispatches == [], (answer, dispatches)
                page.get_by_test_id("runson-trial-state-meetings").filter(
                    has_text="Not tried · Route changed").wait_for()
                assert page.get_by_test_id("runson-try-confirm").count() == 0
                assert len(pending) == 1, pending
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


# ═══ merged from the e2e-high-2 lane ═══
# The Runs on app, AS RENDERED: what only a real browser proves of Runs on.
#
# Owner, 2026-10-12 (push 2 of the test diet): a browser test only for drag,
# focus, keys, touch, hover or an exact geometry relation.
#
# * PHILO-15 lane 12, B27: the footer receipt of a patch never runs into Undo
#   (its text boxes end left of Undo on any line they share), at 1440 and 393.
pytest.importorskip("playwright.sync_api", reason="the Runs on glass needs Playwright")



class TestTheRunsOnFooter(FitRig):
    """replaces: tests/e2e/test_philo15_12_ugly_glass.py::TestPhilo15Lane12Ugly::test_the_runs_on_receipt_never_runs_into_undo (moved whole)."""

    @pytest.mark.parametrize("width", WIDTHS)
    def test_the_runs_on_receipt_never_runs_into_undo(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        from .glass_infra import _normal_chair, engine_profile
        from .runs_on import patch, wait_board

        # One engine on the Default for AI work, the product's way; the
        # board then draws it and a patch writes the receipt beside Undo.
        engine_profile()
        from holdspeak.db import get_database
        from holdspeak.principals import Principal, PrincipalKind
        from holdspeak.services.inference_assignment_service import InferenceAssignmentService

        from tests.unit.test_phase143_inference_assignments import _profile

        # A second engine, so the patch is a change at both widths (the
        # phone list never offers the engine a job already runs on).
        _profile(get_database(), "lane12-second-engine")
        InferenceAssignmentService(get_database()).set_assignment(
            Principal(PrincipalKind.OWNER, "lane12-owner"),
            {"command_id": f"lane12-default-{width}", "expected_revision": 0, "scope": {"kind": "global"},
             "entries": [{"profile_id": "hs201-meeting-engine", "profile_revision": 1},
                         {"profile_id": "lane12-second-engine", "profile_revision": 1}]},
        )
        with sync_playwright() as pw:
            browser, page, errors = self._open(pw, width)
            _builder_tools_on(page, token=FIT_TOKEN)
            try:
                _normal_chair(page)
                self._stage(page, "open-concierge")
                wait_board(page)
                patch(page, "default", "lane12-second-engine")
                receipt = page.get_by_test_id("runson-receipt")
                # Undo is Runs on's first footer action and remains visible
                # in SurfaceFooter's compact layout.
                undo = page.locator(".runson-foot").get_by_test_id("runson-undo")
                undo.wait_for(timeout=T)
                page.wait_for_function(
                    "() => /^PATCHED /.test(document.querySelector('[data-testid=runson-receipt]')?.textContent || '') && !document.querySelector('[data-testid=runson-undo]')?.disabled"
                )
                _settle(page)
                rb, cb = receipt.evaluate(BOX_JS), undo.evaluate(BOX_JS)
                text = receipt.inner_text()
                # The text's own box (the span may be wider than its glyphs when it wraps).
                # W1-KIT: the phone status bar is one line whose facts end in
                # an ellipsis: the drawn ink stops at the facts' clip box.
                ink = receipt.evaluate("(e) => { const r = document.createRange(); r.selectNodeContents(e);"
                                       " const clip = e.closest('.kit-statusbar-items'); const cs = clip && getComputedStyle(clip).overflow === 'hidden' ? clip.getBoundingClientRect() : null;"
                                       " const rs = [...r.getClientRects()]; return rs.map((b) => ({x: b.left, r: cs ? Math.min(b.right, cs.right) : b.right, y: b.top, btm: b.bottom})); }")
                rb = receipt.evaluate("(e) => { const b = e.getBoundingClientRect(); const clip = e.closest('.kit-statusbar-items');"
                                      " const cs = clip && getComputedStyle(clip).overflow === 'hidden' ? clip.getBoundingClientRect() : null;"
                                      " return {x: b.left, y: b.top, r: cs ? Math.min(b.right, cs.right) : b.right, btm: b.bottom, w: b.width, h: b.height}; }")
                self.facts["B27"] = {"receipt": rb, "undo": cb, "text": text, "ink": ink}
                same_row = lambda b: not (b["btm"] <= cb["y"] or b["y"] >= cb["btm"])  # noqa: E731
                assert rb["r"] <= cb["x"] + 0.5 or not same_row(rb), self.facts["B27"]
                for line in ink:
                    if same_row(line):
                        assert line["r"] <= cb["x"] + 0.5, self.facts["B27"]
                assert text.upper().startswith("PATCHED "), text
                footer = page.locator(".kit-statusbar.runson-foot").first
                self._shot(page, "B27-runson-footer", width, footer)
                self._shot(page, "B27-runson", width)
                if width == 393:
                    before_undo = _api(page, "GET", "/api/inference/assignments", token=FIT_TOKEN)
                    default = next(row for row in before_undo["rows"] if row["id"] == "global")
                    assert default["assignment"]["entries"][0]["profile_id"] == "lane12-second-engine", default
                    _whole_hit(undo)
                    undo.click()
                    page.wait_for_function(
                        "() => /^UNDONE /.test(document.querySelector('[data-testid=runson-receipt]')?.textContent || '')"
                    )
                    after_undo = _api(page, "GET", "/api/inference/assignments", token=FIT_TOKEN)
                    restored = next(row for row in after_undo["rows"] if row["id"] == "global")
                    assert [entry["profile_id"] for entry in restored["assignment"]["entries"]] == [
                        "hs201-meeting-engine", "lane12-second-engine"], restored
                self._write("runson", width)
                assert not errors, errors
            finally:
                browser.close()


@pytest.mark.parametrize("width", [1440, 393], ids=["desktop", "phone"])
def test_runs_on_find_on_lan_found_then_use_it_real_scanner(
    tmp_path: Path,
    monkeypatch: Any,
    width: int,
) -> None:
    """The owner can find a new LAN model and add it without rewiring jobs."""
    server, url, fakes, _ticks = _rig(tmp_path, monkeypatch, include_loopback=False)
    expected_url, probe_urls, discover_urls = _install_lan_scanner_double(monkeypatch)
    expected_model = "qwen3.8-27b"
    expected_key = "lan:192.168.77.44:8080:qwen3.8-27b"
    # Betterment E3 (#1294): one engine for each model; the id is host + model.
    expected_profile_id = "engine-192-168-77-44-8080-qwen3-8-27b"
    errors: list[str] = []
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": width, "height": 900 if width == 1440 else 852})
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.goto(f"{url}/?token={TOKEN}", wait_until="load")
            _builder_tools_on(page)
            _api(page, "POST", "/api/desk/seed", token=TOKEN)
            _normal_chair(page)
            _seed(page, fakes[2].server_address[1])
            before_assignments = _assignment_snapshot(
                _api(page, "GET", "/api/inference/assignments", token=TOKEN)
            )
            before_profiles = _library_profile_ids(page)
            assert "profile:glass-lan-27b" in before_profiles
            _open_runs_on(page)
            if width == 1440:
                _ensure_wide_runs_on(page)

            # Detection found no new LAN row. The row below must come from the
            # explicit scanner request and its real model response.
            assert page.get_by_test_id("runson-found-engines").get_by_test_id(f"switchboard-engine-{expected_key}").count() == 0
            with page.expect_response(
                lambda response: response.url.endswith("/api/concierge/discover-lan"),
                timeout=30_000,
            ) as discovery:
                page.get_by_test_id("runson-find-lan").click()
            discovery_response = discovery.value
            assert discovery_response.ok, discovery_response.text()

            found = _found_board(page).get_by_test_id(f"switchboard-engine-{expected_key}")
            found.wait_for(timeout=30_000)
            found_text = found.inner_text()
            assert expected_model in found_text, found_text
            assert "192.168.77.44:8080" in found_text, found_text
            assert page.get_by_test_id("runson-receipt").inner_text() == "FOUND ON LAN"
            assert expected_url in probe_urls
            assert discover_urls == [expected_url]
            assert all(url.startswith("http://192.168.77.") and url.endswith(":8080/v1") for url in probe_urls)
            assert _assignment_snapshot(_api(page, "GET", "/api/inference/assignments", token=TOKEN)) == before_assignments
            assert _library_profile_ids(page) == before_profiles
            _shot(page, "p17-lan-found", width)

            with page.expect_response(
                lambda response: response.url.endswith("/api/inference/model-library/define-endpoint"),
                timeout=30_000,
            ) as used:
                found.get_by_role("button", name="Use it", exact=True).click()
            used_response = used.value
            assert used_response.ok, used_response.text()
            request_body = used_response.request.post_data_json
            assert request_body["draft"]["endpoint"] == expected_url
            assert request_body["draft"]["model"] == expected_model
            assert request_body["draft"]["profile_id"] == expected_profile_id
            page.wait_for_function(
                "() => /^ADDED /.test(document.querySelector('[data-testid=runson-receipt]')?.textContent || '')",
                timeout=30_000,
            )
            found.wait_for(state="detached", timeout=30_000)

            after_assignments = _assignment_snapshot(
                _api(page, "GET", "/api/inference/assignments", token=TOKEN)
            )
            assert after_assignments == before_assignments
            after_profiles = _library_profile_ids(page)
            assert len(after_profiles) == len(before_profiles) + 1
            assert after_profiles.count(f"profile:{expected_profile_id}") == 1
            assert after_profiles.count("profile:glass-lan-27b") == 1

            # The route's durable profile is the source of the next detection
            # read. Canonical profile identity and its private endpoint target
            # are both persisted in the isolated database.
            from holdspeak.db import get_database

            with get_database()._connection() as connection:
                profile = connection.execute(
                    "SELECT profile_id,model_or_artifact_identity FROM model_profile_revisions "
                    "WHERE profile_id=? ORDER BY revision DESC LIMIT 1",
                    (expected_profile_id,),
                ).fetchone()
                target = connection.execute(
                    "SELECT base_url,model FROM profiles WHERE id=? AND deleted=0",
                    (f"library_provider_{expected_profile_id}",),
                ).fetchone()
            assert profile is not None
            assert profile["profile_id"] == expected_profile_id
            assert profile["model_or_artifact_identity"] == expected_model
            assert target is not None
            assert target["base_url"] == expected_url
            assert target["model"] == expected_model
            _shot(page, "p17-lan-after-use-it", width)
            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()
        for fake in fakes:
            fake.shutdown()
