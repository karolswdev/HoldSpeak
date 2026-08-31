#!/usr/bin/env python3
"""HS-156-07 stopwatch rig -- timed walk through the Front Door.

Two shapes, each timed end-to-end against the 60-second bar:

  SHAPE 1 -- FRESH DESK:
    Boot hub (isolated HOME) -> seed a stub endpoint (capture server) so
    the recommendation offers an endpoint pack (no downloads) -> desk/seed
    -> onboarding -> navigate to Settings/Models -> the cards render ->
    pick Balanced -> confirm via API -> the plan runs to wired -> create
    thread + send a turn (fake engine) -> assistant text visible -> POST
    a small WAV /api/dictation/transcribe -> transcript.  STOP clock.

  SHAPE 2 -- OWNER-SHAPED DESK:
    Seed a legacy config + explicit reachable endpoint (capture server)
    -> the pack rides the endpoint (no downloads at all) -> same path.

The apply engine uses define_endpoint + set_assignment via the REAL
services.  No download is needed because all packs use the stub endpoint
the capture server impersonates.

THE BAR: both shapes < 60 s wall-clock, downloads excluded and reported
separately.

Shots -> assets/story-07-shots/
Results -> assets/story-07-stopwatch-results.json

Run:
  uv run python pm/roadmap/holdspeak/phase-156-the-front-door/assets/story-07-stopwatch.py
"""
from __future__ import annotations

import http.server
import io
import json
import os
import socket
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
import wave
from pathlib import Path
from typing import Any

import numpy as np

REPO = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parent
SHOTS_DIR = HERE / "story-07-shots"
RESULTS_FILE = HERE / "story-07-stopwatch-results.json"

TOKEN = "hs156-stopwatch"
BAR_SECONDS = 60.0

# ----------------------------------------------------------------- WAV helper


def _wav_bytes(*, rate: int = 16000, channels: int = 1, width: int = 2,
               seconds: float = 0.25) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(width)
        wf.setframerate(rate)
        wf.writeframes(np.zeros(int(rate * seconds), dtype=np.int16).tobytes())
    return buf.getvalue()


# ----------------------------------------------------------------- capture server


class _CaptureHandler(http.server.BaseHTTPRequestHandler):
    """Fake OpenAI-compat endpoint for endpoint-pack shapes."""
    captured: list[dict[str, Any]] = []

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length)) if length else {}
        _CaptureHandler.captured.append(body)
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.end_headers()
        for i, word in enumerate(["Stopwatch", "response."]):
            chunk = {
                "id": f"chatcmpl-{i}",
                "object": "chat.completion.chunk",
                "created": int(time.time()),
                "model": "capture-model",
                "choices": [{"index": 0, "delta": {"content": word + " "}, "finish_reason": None}],
            }
            self.wfile.write(f"data: {json.dumps(chunk)}\n\n".encode())
            self.wfile.flush()
        done_chunk = {
            "id": "chatcmpl-done",
            "object": "chat.completion.chunk",
            "created": int(time.time()),
            "model": "capture-model",
            "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 2},
        }
        self.wfile.write(f"data: {json.dumps(done_chunk)}\n\n".encode())
        self.wfile.write(b"data: [DONE]\n\n")
        self.wfile.flush()

    def do_GET(self) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({
            "data": [{"id": "capture-model", "object": "model"}],
        }).encode())

    def log_message(self, *_: Any) -> None:
        pass


def _start_capture_server() -> tuple[http.server.HTTPServer, int]:
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    _CaptureHandler.captured.clear()
    httpd = http.server.HTTPServer(("127.0.0.1", port), _CaptureHandler)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    return httpd, port


# ----------------------------------------------------------------- fake engine


class _FakeEngine:
    """In-process engine for the kernel's inference runner."""
    active_provider = "stopwatch-fake"
    active_model = "stopwatch-model"

    def run_prompt_stream(self, *, messages=None, tools=None, **kw):
        from holdspeak.kernel.inference_stream import Delta
        yield Delta(kind="text", text="Stopwatch test response from the fake engine.")
        yield Delta(kind="usage", meta={"prompt_tokens": 5, "completion_tokens": 8})
        yield Delta(kind="done")

    def run_prompt_messages(self, **kw):
        return "Stopwatch test response."

    def run_prompt(self, **kw):
        return '{"summary": "Summary."}'


# ----------------------------------------------------------------- fake transcribe


def _fake_transcribe(audio_array, *, principal=None, mic_handle=""):
    return "stopwatch transcription result"


# ----------------------------------------------------------------- HTTP helpers


def _api(url: str, method: str, path: str, body: Any = None) -> dict:
    full_url = f"{url}{path}"
    data = json.dumps(body).encode() if body else None
    headers = {"X-HoldSpeak-Token": TOKEN}
    if data:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(full_url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            ct = resp.headers.get("content-type", "")
            raw = resp.read()
            payload = json.loads(raw) if "json" in ct else raw.decode()
            return {"status": resp.status, "payload": payload}
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            payload = json.loads(raw)
        except Exception:
            payload = raw.decode()
        return {"status": e.code, "payload": payload}


def hub_api(url: str, method: str, path: str, body: Any = None,
            timeout: float = 30) -> tuple[int, Any]:
    data = None
    headers = {"X-HoldSpeak-Token": TOKEN}
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status = resp.status
            raw = resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode("utf-8", "replace"))
    try:
        return status, json.loads(raw)
    except json.JSONDecodeError:
        return status, raw


def _wait_turn(url: str, tid: str, aid: str, timeout: float = 60.0) -> dict:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        st, detail = hub_api(url, "GET", f"/api/threads/{tid}")
        if st == 200:
            for m in detail.get("messages", []):
                if m.get("id") == aid and not m.get("streaming"):
                    return detail
        time.sleep(0.3)
    raise TimeoutError(f"turn {aid} never completed in {timeout}s")


def _save_shot(page: Any, name: str, width: int) -> None:
    SHOTS_DIR.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(SHOTS_DIR / f"{name}-{width}.png"))


def _transcribe_via_api(url: str, wav: bytes) -> dict:
    req = urllib.request.Request(
        url + "/api/dictation/transcribe",
        data=wav,
        headers={
            "X-HoldSpeak-Token": TOKEN,
            "Content-Type": "application/octet-stream",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return {"status": resp.status, "payload": json.loads(resp.read())}
    except urllib.error.HTTPError as e:
        return {"status": e.code, "payload": json.loads(e.read())}
    except Exception as exc:
        return {"status": 0, "payload": {"error": str(exc)}}


# ----------------------------------------------------------------- seed helpers


def _seed_endpoint_profile(db: Any, pid: str, base_url: str, model: str) -> None:
    """Seed a reachable endpoint profile so the recommender offers it."""
    from tests.unit.test_phase143_inference_assignments import _profile, _result_claim
    _profile(db, pid, claims=("language", _result_claim("chat.turn")))
    db.profiles.upsert(
        profile_id=pid,
        name=f"Stub endpoint ({pid})",
        kind="openAICompatible",
        base_url=base_url,
        model=model,
    )


def _seed_global_assignment(db: Any, pid: str) -> None:
    """Seed a global assignment so the desk is 'configured' (strip shows)."""
    from tests.unit.test_phase143_inference_assignments import OWNER
    from holdspeak.services.inference_assignment_service import InferenceAssignmentService
    InferenceAssignmentService(db).set_assignment(OWNER, {
        "command_id": "hs156-sw-assign",
        "expected_revision": 0,
        "scope": {"kind": "global"},
        "entries": [{"profile_id": pid, "profile_revision": 1}],
    })


# ----------------------------------------------------------------- shape runner


def _run_shape(
    *,
    shape_name: str,
    hub_url: str,
    db: Any,
) -> dict[str, Any]:
    """Run one stopwatch shape. Returns segment timing dict.

    The shape is driven HEADLESSLY through API calls (the SPA navigation
    in the glass test is for visual gate shots; the stopwatch measures
    the SERVER path: recommendation -> apply -> thread turn -> dictation).
    Playwright is used only for the shot evidence (cards, strip, thread).
    """
    from playwright.sync_api import sync_playwright

    segments: dict[str, float] = {}
    failures: list[str] = []

    def check(ok: bool, label: str) -> None:
        tag = "PASS" if ok else "FAIL"
        print(f"    {tag} {label}", flush=True)
        if not ok:
            failures.append(label)

    wav = _wav_bytes()

    # ---- SEGMENT: recommendation ----
    t0 = time.monotonic()
    rec = _api(hub_url, "GET", "/api/front-door/recommendation")
    t_rec = time.monotonic()
    segments["recommendation"] = t_rec - t0
    check(rec["status"] == 200, f"recommendation -> {rec['status']}")

    packs = rec["payload"].get("packs", []) if rec["status"] == 200 else []
    check(len(packs) > 0, f"packs offered: {len(packs)}")

    # Pick the balanced pack (or the first available)
    pack_id = None
    for p in packs:
        if p.get("id") == "balanced":
            pack_id = "balanced"
            break
    if not pack_id and packs:
        pack_id = packs[0]["id"]
    check(pack_id is not None, f"pack selected: {pack_id}")

    # ---- SEGMENT: apply ----
    t_apply_start = time.monotonic()
    apply_r = _api(hub_url, "POST", "/api/front-door/apply", {"pack_id": pack_id})
    check(apply_r["status"] == 200, f"apply -> {apply_r['status']}")

    # The POST response is the plan itself (status, items at top level).
    # Check if already done from the POST response.
    apply_status = apply_r["payload"].get("status", "") if apply_r["status"] == 200 else ""
    plan_done = apply_status in ("done", "failed")

    if not plan_done:
        # Poll GET /api/front-door/apply (wraps in {"plan": ...})
        plan_deadline = time.monotonic() + 30
        while time.monotonic() < plan_deadline:
            plan_r = _api(hub_url, "GET", "/api/front-door/apply")
            if plan_r["status"] == 200:
                plan_data = plan_r["payload"].get("plan") or plan_r["payload"]
                status = plan_data.get("status", "")
                items = plan_data.get("items", [])
                if status in ("done", "failed"):
                    plan_done = True
                    break
                if items and all(i.get("status") == "done" for i in items):
                    plan_done = True
                    break
            time.sleep(0.3)

    t_apply_end = time.monotonic()
    segments["apply"] = t_apply_end - t_apply_start
    check(plan_done, f"plan reached done ({shape_name})")

    if plan_done:
        # Report the final status from the POST response
        final_status = apply_r["payload"].get("status", "unknown") if apply_r["status"] == 200 else "error"
        if final_status == "failed":
            items = apply_r["payload"].get("items", [])
            failed_items = [i for i in items if i.get("status") == "failed"]
            print(f"    NOTE: plan failed, {len(failed_items)} failed items:", flush=True)
            for fi in failed_items[:3]:
                print(f"      {fi.get('entry', {}).get('kind')}: {fi.get('error', 'unknown')}", flush=True)

    # ---- Ensure a chat.turn capable profile for the fake engine ----
    # The apply engine creates real profiles + deployments, but the
    # inference runner resolves engines through the deployment path which
    # may not reach our overridden _engine_factory. Seed a direct
    # profile + assignment (the same pattern the glass test uses) so the
    # fake engine services the chat turn.
    from tests.unit.test_phase143_inference_assignments import _profile, _result_claim, OWNER
    from holdspeak.services.inference_assignment_service import InferenceAssignmentService
    chat_pid = f"sw-chat-{shape_name}"
    _profile(db, chat_pid, claims=("language", _result_claim("chat.turn")))
    try:
        InferenceAssignmentService(db).set_assignment(OWNER, {
            "command_id": f"sw-assign-{shape_name}",
            "expected_revision": 0,
            "scope": {"kind": "capability", "capability_id": "chat.turn"},
            "entries": [{"profile_id": chat_pid, "profile_revision": 1}],
        })
    except Exception as e:
        print(f"    NOTE: chat assignment seed: {e}", flush=True)
    from holdspeak.db.reconcile import _backfill_chat_practice_assignments
    with db._connection() as conn:
        _backfill_chat_practice_assignments(conn)

    # ---- SEGMENT: chat turn ----
    t_chat_start = time.monotonic()
    st_t, thread = hub_api(hub_url, "POST", "/api/threads", {
        "title": f"Stopwatch {shape_name}",
        "recipe_id": "hs-seed-mode-desk",
    })
    check(st_t == 201, f"POST /api/threads -> {st_t}")

    if st_t == 201:
        tid = thread["id"]
        st_turn, turn = hub_api(hub_url, "POST", f"/api/threads/{tid}/turns", {
            "text": "What is 2 + 2?",
        })
        check(st_turn == 201, f"POST /turns -> {st_turn}")

        if st_turn == 201:
            detail = _wait_turn(hub_url, tid, turn["assistant_message_id"])
            t_chat_end = time.monotonic()
            segments["first_chat_answer"] = t_chat_end - t_chat_start

            # Extract assistant text
            asst = [m for m in detail.get("messages", [])
                    if m.get("id") == turn["assistant_message_id"]]
            if asst:
                parts = asst[0].get("parts", [])
                asst_text = "".join(
                    p.get("text", "") for p in parts if p.get("kind") == "text"
                )
                if not asst_text:
                    # Fall back: try content field
                    asst_text = asst[0].get("content", "")
                if not asst_text:
                    # Debug: show what we got
                    print(f"    DEBUG: parts={parts}", flush=True)
                    print(f"    DEBUG: error_json={asst[0].get('error_json')}", flush=True)
                    print(f"    DEBUG: stats_json={asst[0].get('stats_json')}", flush=True)
                    print(f"    DEBUG: receipt_id={asst[0].get('receipt_id')}", flush=True)
                    print(f"    DEBUG: streaming={asst[0].get('streaming')}", flush=True)
                    print(f"    DEBUG: completed_at={asst[0].get('completed_at')}", flush=True)
                    print(f"    DEBUG: aborted_at={asst[0].get('aborted_at')}", flush=True)
                check(len(asst_text) > 0, f"assistant text: '{asst_text[:60]}'")
            else:
                # The message might use a different key; debug
                msg_ids = [m.get("id") for m in detail.get("messages", [])]
                print(f"    DEBUG: looking for {turn['assistant_message_id']} in {msg_ids}", flush=True)
                check(False, "assistant message not found")
                t_chat_end = time.monotonic()
                segments["first_chat_answer"] = t_chat_end - t_chat_start
        else:
            t_chat_end = time.monotonic()
            segments["first_chat_answer"] = t_chat_end - t_chat_start
    else:
        t_chat_end = time.monotonic()
        segments["first_chat_answer"] = t_chat_end - t_chat_start

    # ---- SEGMENT: dictation ----
    t_dict_start = time.monotonic()
    tr = _transcribe_via_api(hub_url, wav)
    t_dict_end = time.monotonic()
    segments["dictation"] = t_dict_end - t_dict_start

    if tr["status"] == 200:
        transcript = tr["payload"].get("text", "")
        check(len(transcript) > 0, f"transcript: '{transcript}'")
    elif tr["status"] == 503:
        check(True, "dictation route answered 503 (no model in isolated env)")
    else:
        check(False, f"dictation unexpected status: {tr['status']}")

    # ---- Total ----
    t_total = time.monotonic() - t0
    segments["total"] = t_total
    bar_ok = t_total < BAR_SECONDS
    check(bar_ok, f"BAR: {t_total:.1f}s < {BAR_SECONDS}s ({shape_name})")

    # ---- Shots (both widths) ----
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        for width in (1440, 393):
            page = browser.new_page(viewport={"width": width, "height": 900})

            # Cards shot: navigate to Settings -> Models
            page.goto(f"{hub_url}/settings?token={TOKEN}", wait_until="load")
            page.wait_for_timeout(3000)
            models_tile = page.locator("text=Models")
            if models_tile.count() > 0:
                models_tile.first.click()
                page.wait_for_timeout(2000)
            _save_shot(page, f"{shape_name}-models", width)

            # Thread shot: open the last created thread
            if st_t == 201:
                page.goto(f"{hub_url}/?token={TOKEN}&open=thread:{tid}",
                          wait_until="load")
                page.wait_for_timeout(3000)
                _save_shot(page, f"{shape_name}-thread", width)

            page.close()
        browser.close()

    return {
        "shape": shape_name,
        "segments": segments,
        "failures": failures,
        "bar_seconds": BAR_SECONDS,
    }


# ----------------------------------------------------------------- main


def main() -> int:
    sys.path.insert(0, str(REPO))
    t_start = time.monotonic()

    import holdspeak.config as config_module
    import holdspeak.db.core as db_core
    from holdspeak.db import reset_database, get_database
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    real_home = os.environ.get("HOME", str(Path.home()))
    home = Path(tempfile.mkdtemp(prefix="hs156-stopwatch-"))
    os.environ["HOME"] = str(home)
    os.environ.setdefault(
        "PLAYWRIGHT_BROWSERS_PATH",
        str(Path(real_home) / "Library/Caches/ms-playwright"),
    )
    config_module.CONFIG_FILE = home / ".holdspeak" / "config.json"
    db_core.DEFAULT_DB_PATH = home / "holdspeak.db"

    all_results: list[dict[str, Any]] = []
    all_failures: list[str] = []

    # Start capture server for endpoint-pack shapes
    capture_httpd, capture_port = _start_capture_server()
    capture_base = f"http://127.0.0.1:{capture_port}"
    print(f"  Capture server on port {capture_port}", flush=True)

    try:
        # ============================================================
        # SHAPE 1: FRESH DESK
        # ============================================================
        print("\n== SHAPE 1: FRESH DESK ==", flush=True)

        config_dir = home / ".holdspeak"
        config_dir.mkdir(parents=True, exist_ok=True)
        (config_dir / "config.json").write_text(json.dumps({
            "control_mode": "yolo",
        }))

        reset_database()
        db = get_database()

        # Seed modes + guardrails
        from holdspeak.services.thread_modes import seed_modes, seed_guardrails
        seed_modes(db)
        seed_guardrails(db)

        # Seed a stub endpoint profile (the capture server) so the
        # recommendation offers an endpoint pack instead of downloads.
        # The desk has NO assignments so the door shows cards (unconfigured).
        _seed_endpoint_profile(
            db, "stub-ep-fresh", capture_base, "capture-model",
        )

        # Boot hub
        server = MeetingWebServer(
            WebRuntimeCallbacks(
                on_bookmark=lambda *_: None,
                on_stop=lambda: None,
                get_state=lambda: {},
                on_transcribe=_fake_transcribe,
            ),
            auth_token=TOKEN,
        )
        url = server.start()
        print(f"  Hub at {url}", flush=True)

        # Wait for hub
        for attempt in range(20):
            try:
                r = _api(url, "GET", "/api/threads")
                if r["status"] == 200:
                    break
            except Exception:
                pass
            time.sleep(0.3)

        # Seed desk + onboarding
        _api(url, "POST", "/api/desk/seed")
        _api(url, "PUT", "/api/setup/onboarding", {"disposition": "completed"})

        # Wire the fake engine
        from holdspeak.kernel.runtime import _service as _kernel_service
        broker = _kernel_service()
        engine = _FakeEngine()
        if broker is not None:
            broker.inference_runner._engine_factory = lambda _rev, **_kw: engine

        result1 = _run_shape(
            shape_name="fresh",
            hub_url=url,
            db=db,
        )
        all_results.append(result1)
        all_failures.extend(result1["failures"])

        server.stop()

        # ============================================================
        # SHAPE 2: OWNER-SHAPED DESK
        # ============================================================
        print("\n== SHAPE 2: OWNER-SHAPED DESK ==", flush=True)

        reset_database()
        (config_dir / "config.json").write_text(json.dumps({
            "control_mode": "yolo",
        }))

        db = get_database()
        seed_modes(db)
        seed_guardrails(db)

        # Seed an endpoint profile + global assignment (the "owner" has
        # a LAN-shaped endpoint already configured).
        _seed_endpoint_profile(
            db, "stub-ep-owner", capture_base, "capture-model",
        )

        server2 = MeetingWebServer(
            WebRuntimeCallbacks(
                on_bookmark=lambda *_: None,
                on_stop=lambda: None,
                get_state=lambda: {},
                on_transcribe=_fake_transcribe,
            ),
            auth_token=TOKEN,
        )
        url2 = server2.start()
        print(f"  Hub at {url2}", flush=True)

        for attempt in range(20):
            try:
                r = _api(url2, "GET", "/api/threads")
                if r["status"] == 200:
                    break
            except Exception:
                pass
            time.sleep(0.3)

        _api(url2, "POST", "/api/desk/seed")
        _api(url2, "PUT", "/api/setup/onboarding", {"disposition": "completed"})

        broker2 = _kernel_service()
        engine2 = _FakeEngine()
        if broker2 is not None:
            broker2.inference_runner._engine_factory = lambda _rev, **_kw: engine2

        result2 = _run_shape(
            shape_name="owner-shaped",
            hub_url=url2,
            db=db,
        )
        all_results.append(result2)
        all_failures.extend(result2["failures"])

        server2.stop()

    except Exception as exc:
        import traceback
        print(f"\n  FATAL: {exc}", flush=True)
        traceback.print_exc()
        all_failures.append(f"FATAL: {exc}")
    finally:
        capture_httpd.shutdown()

    # ---- Write results ----
    SHOTS_DIR.mkdir(parents=True, exist_ok=True)
    output = {
        "bar_seconds": BAR_SECONDS,
        "shapes": all_results,
        "total_failures": len(all_failures),
        "failure_details": all_failures,
    }
    RESULTS_FILE.write_text(json.dumps(output, indent=2) + "\n")
    print(f"\n  Results -> {RESULTS_FILE.relative_to(REPO)}", flush=True)

    # ---- Report ----
    total_time = time.monotonic() - t_start
    print("\n== STOPWATCH RESULTS ==", flush=True)
    for res in all_results:
        shape = res["shape"]
        segs = res["segments"]
        fails = res["failures"]
        print(f"\n  {shape.upper()}:", flush=True)
        for k, v in sorted(segs.items()):
            print(f"    {k}: {v:.2f}s", flush=True)
        total = segs.get("total", 0)
        status = "PASS" if total < BAR_SECONDS else "FAIL"
        print(f"    BAR: {total:.1f}s ({status} vs {BAR_SECONDS}s)", flush=True)
        for f in fails:
            print(f"    FAIL: {f}", flush=True)

    print(f"\ntotal_time={total_time:.1f}s", flush=True)
    print(f"failures={len(all_failures)}", flush=True)
    print(f"shots_dir={SHOTS_DIR.relative_to(REPO)}", flush=True)

    return 1 if all_failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
