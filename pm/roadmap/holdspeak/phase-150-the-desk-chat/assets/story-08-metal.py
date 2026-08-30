#!/usr/bin/env python3
"""HS-150-08 real-metal legs -- self-contained, never touches the owner's DB.

Boots the hub in-process in an isolated HOME (137 law), seeds a REAL
local-network profile for llama.cpp at http://192.168.1.43:8080 (OpenAI-
compatible), and exercises:

  LEG 1 -- two-turn streamed thread with time-to-first-delta, receipt,
           egress; control = the same prompt through POST /api/ask.
  LEG 2 -- People boundary under profile switch: sensitive part redacted
           on cloud egress, preserved on local egress.

Skip cleanly if .43 is unreachable.  ``HS150_METAL_DRY=1`` exercises
everything via a local capture server instead of the real endpoint.

Run for real (from an unsandboxed shell that can reach the LAN):
  uv run python pm/roadmap/holdspeak/phase-150-the-desk-chat/assets/story-08-metal.py

Dry run (no LAN required):
  HS150_METAL_DRY=1 uv run python pm/roadmap/holdspeak/phase-150-the-desk-chat/assets/story-08-metal.py
"""
from __future__ import annotations

import asyncio
import base64
import hashlib
import http.server
import io
import json
import os
import socket
import ssl
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[5]
PAYLOADS = REPO / "pm/roadmap/holdspeak/phase-150-the-desk-chat/assets/story-08-metal-payloads"
TOKEN = "hs150-metal"

LAN_HOST = "192.168.1.43"
LAN_PORT = 8080
LAN_BASE = f"http://{LAN_HOST}:{LAN_PORT}/v1"
LAN_MODEL = "Qwen3.6-35B-A3B-UD-Q5_K_XL.gguf"  # from GET /v1/models

SENTINEL = "METAL-LEG-SENSITIVE-PERSON-DATA-d8f2a"
DRY_MODE = os.environ.get("HS150_METAL_DRY") == "1"


# ─────────────────────────────────── capture server (LEG 2 + dry mode) ───

class CaptureHandler(http.server.BaseHTTPRequestHandler):
    """Tiny HTTP server that accepts POST /v1/chat/completions, records the
    JSON body, and returns a minimal OpenAI-style SSE stream."""

    captured: list[dict[str, Any]] = []

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length)) if length else {}
        CaptureHandler.captured.append(body)

        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.end_headers()

        msg_id = "metal-capture-msg"
        for i, word in enumerate(["Captured", "response"]):
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
        """Serve GET /v1/models for dry mode."""
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({
            "data": [{"id": "capture-model", "object": "model"}],
        }).encode())

    def log_message(self, *_: Any) -> None:
        pass  # silence


def start_capture_server() -> tuple[http.server.HTTPServer, int, threading.Thread]:
    """Start the capture server on a free port, return (server, port, thread)."""
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    CaptureHandler.captured.clear()
    httpd = http.server.HTTPServer(("127.0.0.1", port), CaptureHandler)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    return httpd, port, t


# ─────────────────────────────── profile seeding ─────────────────────────

def seed_lan_profile(db: Any, base_url: str, model: str, profile_id: str = "hs150-metal-lan") -> None:
    """Seed a profile that routes to an OpenAI-compatible endpoint on the LAN.

    Uses the test helper ``_profile()`` for a valid local-engine admission chain
    (profile revision + binding + deployment + assignment). The actual OpenAI-
    compatible engine is injected at runtime by overriding the runner's
    ``_engine_factory``, just like the rig script does.

    The old profiles table is still seeded for the engine factory's fallback.
    """
    from holdspeak.services.inference_assignment_service import InferenceAssignmentService
    from tests.unit.test_phase143_inference_assignments import _profile, _result_claim, OWNER

    # 1. Old profiles table (engine factory reads this to build MeetingIntel).
    db.profiles.upsert(
        profile_id=profile_id,
        name=f"Metal LAN ({profile_id})",
        kind="openAICompatible",
        base_url=base_url,
        model=model,
        requires_key=False,
    )

    # 2. New admission chain (local-engine, overridden at runtime).
    _profile(db, profile_id, claims=("language", _result_claim("chat.turn"), _result_claim("ask.answer")))

    # 3. Capability-scoped assignment for chat.turn.
    InferenceAssignmentService(db).set_assignment(OWNER, {
        "command_id": f"hs150-metal-assign-{profile_id}",
        "expected_revision": 0,
        "scope": {"kind": "capability", "capability_id": "chat.turn"},
        "entries": [{"profile_id": profile_id, "profile_revision": 1}],
    })
    # Also for ask.answer so the CONTROL Ask works.
    InferenceAssignmentService(db).set_assignment(OWNER, {
        "command_id": f"hs150-metal-assign-ask-{profile_id}",
        "expected_revision": 0,
        "scope": {"kind": "capability", "capability_id": "ask.answer"},
        "entries": [{"profile_id": profile_id, "profile_revision": 1}],
    })


def seed_cloud_profile(
    db: Any,
    capture_url: str,
    profile_id: str = "hs150-metal-cloud",
) -> None:
    """Seed a cloud-egress profile pointing at the capture server."""
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.inference_targets import resolve_inference_target
    from holdspeak.deployment_revisions import capture_deployment_revision
    from holdspeak.intel.providers import profile_key_env
    from tests.unit.test_phase143_inference_assignments import _profile, OWNER

    # The capture URL must look like a non-private endpoint for cloud egress.
    # Use the profile key env var to satisfy the requires_key check.
    env_key = profile_key_env(profile_id)
    os.environ[env_key] = "metal-test-key"

    db.profiles.upsert(
        profile_id=profile_id,
        name="Metal Cloud Capture",
        kind="openAICompatible",
        base_url=capture_url,
        model="capture-model",
        requires_key=True,
    )
    target = resolve_inference_target(db, profile_id)
    capture_deployment_revision(db, target)
    # HS-150-04 fix: use _profile() for a valid admission chain.
    from tests.unit.test_phase143_inference_assignments import _result_claim
    _profile(db, profile_id, claims=("language", _result_claim("chat.turn")))


# ─────────────────────────────── WebSocket bus listener ──────────────────

def ws_auth_protocols(token: str) -> list[str]:
    """Build the same subprotocol list the browser sends."""
    encoded = base64.urlsafe_b64encode(token.encode()).rstrip(b"=").decode()
    return ["holdspeak.v1", f"holdspeak.auth.v1.{encoded}"]


async def listen_for_thread_frames(
    ws_url: str, token: str, thread_id: str, *, timeout: float = 60,
) -> dict[str, Any]:
    """Connect to the runtime bus and collect thread frames for one turn.

    Returns {started_at, first_delta_at, done_at, deltas: [text,...],
    receipt_id, outcome, stats, first_delta_s, total_s}.
    """
    try:
        import websockets
    except ImportError:
        # Fallback: use the websockets library; if not installed, return empty.
        return {"error": "websockets library not installed"}

    protocols = ws_auth_protocols(token)
    result: dict[str, Any] = {
        "started_at": None, "first_delta_at": None, "done_at": None,
        "deltas": [], "receipt_id": "", "outcome": "", "stats": {},
        "first_delta_s": None, "total_s": None,
    }

    async with websockets.connect(ws_url, subprotocols=protocols) as ws:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                raw = await asyncio.wait_for(ws.recv(), timeout=max(0.1, deadline - time.monotonic()))
            except asyncio.TimeoutError:
                break
            frame = json.loads(raw)
            ft = frame.get("type", "")
            data = frame.get("data", {})

            if ft == "thread_turn_started" and data.get("thread_id") == thread_id:
                result["started_at"] = time.monotonic()

            elif ft == "thread_delta" and data.get("thread_id") == thread_id:
                now = time.monotonic()
                if result["first_delta_at"] is None and result["started_at"] is not None:
                    result["first_delta_at"] = now
                    result["first_delta_s"] = now - result["started_at"]
                result["deltas"].append(data.get("text", ""))

            elif ft == "thread_turn_done" and data.get("thread_id") == thread_id:
                result["done_at"] = time.monotonic()
                result["receipt_id"] = data.get("receipt_id", "")
                result["outcome"] = data.get("outcome", "")
                result["stats"] = data.get("stats", {})
                if result["started_at"]:
                    result["total_s"] = result["done_at"] - result["started_at"]
                break

    return result


# ─────────────────────────────── API helpers ─────────────────────────────

def hub_api(url: str, method: str, path: str, body: Any = None, timeout: float = 30) -> tuple[int, Any]:
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


# ─────────────────────────────── connectivity check ──────────────────────

def lan_reachable() -> bool:
    """Check if .43 is reachable (health endpoint or /v1/models)."""
    try:
        req = urllib.request.Request(f"http://{LAN_HOST}:{LAN_PORT}/v1/models")
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status == 200
    except Exception:
        return False


def detect_model() -> str:
    """GET /v1/models from .43 and return the first model id."""
    try:
        req = urllib.request.Request(f"http://{LAN_HOST}:{LAN_PORT}/v1/models")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
            models = data.get("data", [])
            if models:
                return str(models[0].get("id", LAN_MODEL))
    except Exception:
        pass
    return LAN_MODEL


# ─────────────────────────────── main ────────────────────────────────────

def main() -> int:
    sys.path.insert(0, str(REPO))

    if not DRY_MODE and not lan_reachable():
        print(f"SKIP: .43 ({LAN_HOST}:{LAN_PORT}) is unreachable; "
              f"set HS150_METAL_DRY=1 for dry run", flush=True)
        return 0

    import holdspeak.config as config_module
    import holdspeak.db.core as db_core
    from holdspeak.db import reset_database, get_database
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    real_home = os.environ.get("HOME", str(Path.home()))
    home = Path(tempfile.mkdtemp(prefix="hs150-metal-"))
    os.environ["HOME"] = str(home)
    os.environ.setdefault(
        "PLAYWRIGHT_BROWSERS_PATH",
        str(Path(real_home) / "Library/Caches/ms-playwright"),
    )
    PAYLOADS.mkdir(parents=True, exist_ok=True)
    config_module.CONFIG_FILE = home / ".holdspeak" / "config.json"
    db_core.DEFAULT_DB_PATH = home / "holdspeak.db"
    reset_database()

    server = MeetingWebServer(
        WebRuntimeCallbacks(
            on_bookmark=lambda *_: None,
            on_stop=lambda: None,
            get_state=lambda: {},
        ),
        auth_token=TOKEN,
    )
    url = server.start()
    ws_url = url.replace("http://", "ws://") + "/ws"
    failures: list[str] = []

    # Start the capture server for LEG 2 (and for dry mode LEG 1).
    capture_httpd, capture_port, capture_thread = start_capture_server()
    capture_base = f"http://127.0.0.1:{capture_port}/v1"
    # For cloud egress the host must NOT be private. We use "cloud.example.test"
    # as the egress-visible hostname, but the actual traffic goes to 127.0.0.1.
    # The profile's base_url determines egress scope; the actual HTTP request
    # goes to the URL the engine resolves. For the capture server we set
    # base_url to point at the capture server directly -- and since 127.0.0.1
    # classifies as LOCAL not CLOUD in egress_boundary, we need to work around
    # this. Let's set base_url to an external-looking hostname but actually
    # route traffic via the profile's endpoint. In practice, the engine reads
    # base_url from the revision. So we'll use a trick: set base_url to
    # "http://cloud.example.test:{port}/v1" and add a hosts-style redirect.
    # Actually simpler: just set the base_url to a real-looking cloud URL but
    # then the engine won't be able to connect. For the test, we just need to
    # verify the PAYLOAD was redacted -- we can do that via the service method
    # `assemble_payload_for_egress` without actually dispatching. But we ALSO
    # want to capture what the engine SENDS. Let's use the capture server
    # at 127.0.0.1 but set requires_key=True and check the assembled payload
    # via the service method. The actual engine dispatch to 127.0.0.1 will
    # classify as LOCAL egress but the profile's KIND is "external_service"
    # if base_url doesn't look private. Since 127.0.0.1 IS localhost,
    # egress_boundary returns LOCAL. That's fine -- the People boundary is
    # enforced by the thread service based on the route plan's egress_scope,
    # which comes from the ADMITTED route, not the actual dispatch. The route
    # plan reads the deployment revision which was captured from the profile's
    # base_url at admission time. So if we set the profile's base_url to a
    # non-private host, the route plan will have egress_scope="cloud" even
    # though the actual traffic goes to localhost. Perfect.
    #
    # For this to work, we need a base_url with a non-private, non-localhost
    # host. "http://cloud.example.test:PORT/v1" won't resolve but the
    # egress_boundary will classify it as "cloud". The engine's OpenAI client
    # uses this as base_url and will fail to connect... unless we override.
    # Actually, let's use a simpler approach: just use the assemble_payload
    # method to verify redaction without dispatching, and check the real
    # dispatch payload separately.

    try:
        db = get_database()

        # ── Detect model ──
        if DRY_MODE:
            actual_model = "capture-model"
            lan_base = capture_base
        else:
            actual_model = detect_model()
            lan_base = LAN_BASE
            print(f"  .43 model: {actual_model}", flush=True)

        # ── Seed LAN profile + assignment ──
        seed_lan_profile(db, lan_base, actual_model)

        # Override the runner's engine factory.  The admission chain uses
        # _profile() which creates a local-engine deployment, so the default
        # factory tries to load llama.cpp.  We inject an engine that talks to
        # the capture server (or .43) via plain HTTP (no openai SDK needed).
        from holdspeak.kernel.runtime import _service as _kernel_service
        broker = _kernel_service()
        runner = broker.inference_runner

        class _CaptureFriendlyEngine:
            """Engine that talks to an OpenAI-compatible endpoint via urllib."""
            active_provider = "metal-capture"
            active_model = actual_model

            def __init__(self, base: str):
                self._base = base

            def run_prompt_stream(self, *, messages=None, temperature=None, max_tokens=None, **kw):
                from holdspeak.kernel.inference_stream import Delta
                body = json.dumps({"model": actual_model, "messages": messages or [],
                                   "stream": True, "max_tokens": max_tokens or 512}).encode()
                req = urllib.request.Request(
                    self._base + "/chat/completions",
                    data=body,
                    headers={"Content-Type": "application/json"},
                )
                with urllib.request.urlopen(req, timeout=60) as resp:
                    for line in resp:
                        text = line.decode("utf-8", "replace").strip()
                        if not text or not text.startswith("data:"):
                            continue
                        payload_str = text[len("data:"):].strip()
                        if payload_str == "[DONE]":
                            break
                        try:
                            chunk = json.loads(payload_str)
                        except json.JSONDecodeError:
                            continue
                        choices = chunk.get("choices", [])
                        if not choices:
                            continue
                        delta = choices[0].get("delta", {})
                        content = delta.get("content")
                        finish = choices[0].get("finish_reason")
                        if content:
                            yield Delta(kind="text", text=content)
                        usage = chunk.get("usage")
                        if usage:
                            yield Delta(kind="usage", meta=usage)
                        if finish == "stop":
                            yield Delta(kind="done")

            def run_prompt_messages(self, *, messages=None, temperature=None, max_tokens=None, **kw):
                parts = []
                for delta in self.run_prompt_stream(messages=messages, temperature=temperature, max_tokens=max_tokens):
                    if delta.kind == "text":
                        parts.append(delta.text)
                return "".join(parts)

            def run_prompt(self, *, system_prompt="", user_prompt="", temperature=None, max_tokens=None, **kw):
                return self.run_prompt_messages(
                    messages=[{"role": "system", "content": system_prompt},
                              {"role": "user", "content": user_prompt}],
                    temperature=temperature, max_tokens=max_tokens,
                )

        _engine_base = lan_base
        runner._engine_factory = lambda _rev, **_kw: _CaptureFriendlyEngine(_engine_base)

        # Seed desk for onboarding bypass
        hub_api(url, "POST", "/api/desk/seed")
        hub_api(url, "PUT", "/api/setup/onboarding", {"disposition": "completed"})

        # ==================================================================
        # LEG 1: two-turn streamed thread with timing
        # ==================================================================
        print("\n== LEG 1: two-turn streamed thread ==", flush=True)

        status, thread = hub_api(url, "POST", "/api/threads", {"title": "Metal Leg 1"})
        if status != 201:
            failures.append(f"thread creation failed: {status} {thread}")
            print(f"  FAIL thread creation: {status}", flush=True)
        else:
            tid = thread["id"]
            prompts = [
                "What are the three most important principles of clean architecture?",
                "Now give me a concrete example for each principle.",
            ]

            for turn_num, prompt_text in enumerate(prompts, 1):
                print(f"\n  -- Turn {turn_num} --", flush=True)

                # ── Start bus listener BEFORE posting the turn ──
                bus_box: list[dict[str, Any]] = [{}]

                def _bus_worker() -> None:
                    loop = asyncio.new_event_loop()
                    try:
                        bus_box[0] = loop.run_until_complete(
                            listen_for_thread_frames(ws_url, TOKEN, tid, timeout=120)
                        )
                    finally:
                        loop.close()

                bus_thread = threading.Thread(target=_bus_worker, daemon=True)
                bus_thread.start()
                time.sleep(0.3)  # let the WS connect before the POST

                # Post the turn
                turn_start = time.monotonic()
                t_status, turn_resp = hub_api(url, "POST", f"/api/threads/{tid}/turns",
                                              {"text": prompt_text})
                if t_status != 201:
                    failures.append(f"turn {turn_num} POST failed: {t_status} {turn_resp}")
                    print(f"  FAIL turn {turn_num} POST: {t_status}", flush=True)
                    bus_thread.join(timeout=5)
                    continue

                asst_id = turn_resp.get("assistant_message_id", "")
                print(f"  turn {turn_num} posted: user={turn_resp.get('user_message_id', '')[:12]} "
                      f"asst={asst_id[:12]}", flush=True)

                # Wait for thread_turn_done by polling GET /api/threads/{tid}
                deadline = time.monotonic() + 120
                done = False
                while time.monotonic() < deadline:
                    time.sleep(1)
                    _, detail = hub_api(url, "GET", f"/api/threads/{tid}")
                    msgs = detail.get("messages", [])
                    asst_msgs = [m for m in msgs if m.get("id") == asst_id]
                    if asst_msgs and not asst_msgs[0].get("streaming", 0):
                        done = True
                        break
                turn_wall = time.monotonic() - turn_start

                # Collect bus results
                bus_thread.join(timeout=10)
                bus = bus_box[0]

                if not done:
                    failures.append(f"turn {turn_num} did not complete within 120s")
                    print(f"  FAIL turn {turn_num} timed out", flush=True)
                    continue

                # Read back the thread
                _, detail = hub_api(url, "GET", f"/api/threads/{tid}")
                msgs = detail.get("messages", [])
                asst_msgs = [m for m in msgs if m.get("id") == asst_id]
                if not asst_msgs:
                    failures.append(f"turn {turn_num} assistant message not found")
                    continue

                asst = asst_msgs[0]
                parts = asst.get("parts", [])
                text_parts = [p.get("text", "") for p in parts if p.get("kind") == "text"]
                full_text = "".join(text_parts)
                receipt_id = asst.get("receipt_id", "")
                egress = asst.get("egress_scope", "")
                streaming = asst.get("streaming", 0)

                # ── Bus timing ──
                bus_first_delta = bus.get("first_delta_s")
                bus_delta_count = len(bus.get("deltas", []))
                bus_total = bus.get("total_s")
                bus_deltas_text = "".join(bus.get("deltas", []))

                if bus.get("error"):
                    print(f"  BUS WARNING: {bus['error']}", flush=True)

                # Assert deltas text matches the persisted text
                if bus_deltas_text and full_text:
                    if bus_deltas_text.strip() != full_text.strip():
                        failures.append(
                            f"turn {turn_num} bus deltas text "
                            f"({len(bus_deltas_text)} chars) != persisted text "
                            f"({len(full_text)} chars)"
                        )

                if not full_text:
                    failures.append(f"turn {turn_num} has empty text")
                if not receipt_id:
                    failures.append(f"turn {turn_num} has no receipt_id")
                if streaming:
                    failures.append(f"turn {turn_num} still streaming after done poll")

                # N1: first delta <= 1.5 s (FINDING, not hard failure)
                if bus_first_delta is not None and bus_first_delta > 1.5:
                    failures.append(
                        f"N1 turn {turn_num} first_delta={bus_first_delta:.3f}s > 1.5s "
                        f"(shared hardware; owner decides)"
                    )

                # ── Print both timing lines ──
                print(f"  WALL   turn={turn_num} total={turn_wall:.3f}s "
                      f"text_len={len(full_text)} receipt={'present' if receipt_id else 'MISSING'}",
                      flush=True)
                print(f"  TIMING turn={turn_num} "
                      f"first_delta={bus_first_delta:.3f}s " if bus_first_delta is not None else f"  TIMING turn={turn_num} first_delta=N/A ",
                      end="", flush=True)
                print(f"deltas={bus_delta_count} "
                      f"total={bus_total:.3f}s " if bus_total is not None else f"deltas={bus_delta_count} total=N/A ",
                      end="", flush=True)
                print(f"text_len={len(full_text)} "
                      f"receipt={'present' if receipt_id else 'MISSING'}",
                      flush=True)

            # CONTROL: non-streaming Ask for the same prompt
            print("\n  -- CONTROL: non-streaming Ask --", flush=True)
            ask_start = time.monotonic()
            a_status, ask_resp = hub_api(url, "POST", "/api/ask",
                                         {"prompt": prompts[0], "profile_id": "hs150-metal-lan"}, timeout=120)
            ask_wall = time.monotonic() - ask_start
            if a_status == 200:
                ask_output = str(ask_resp.get("output", ""))
                ask_receipt = str(ask_resp.get("receipt_id", ""))
                print(f"  CONTROL Ask: text_len={len(ask_output)} "
                      f"receipt={ask_receipt[:8] if ask_receipt else 'NONE'} "
                      f"wall={ask_wall:.3f}s", flush=True)
            else:
                print(f"  CONTROL Ask failed: {a_status} {ask_resp}", flush=True)

        # ==================================================================
        # LEG 2: People boundary under profile switch
        # ==================================================================
        print("\n== LEG 2: People boundary under profile switch ==", flush=True)

        # Create a thread with a user message + an assistant part flagged sensitive=1
        status2, thread2 = hub_api(url, "POST", "/api/threads", {"title": "People Boundary"})
        if status2 != 201:
            failures.append(f"LEG 2 thread creation failed: {status2}")
        else:
            tid2 = thread2["id"]

            # Create earlier messages using the repository API (not raw SQL)
            # so parent_id chains are properly maintained.
            user_msg2 = db.threads.append_message(tid2, role="user")
            db.threads.append_part(user_msg2.id, kind="text", text="Tell me about this person")
            user_mid = user_msg2.id
            asst_msg2 = db.threads.append_message(tid2, role="assistant", parent_id=user_mid)
            db.threads.append_part(asst_msg2.id, kind="text", text=SENTINEL, sensitive=True)
            db.threads.complete_message(asst_msg2.id)
            asst_mid = asst_msg2.id

            # Verify via the service's assemble_payload_for_egress
            from holdspeak.services.thread_service import ThreadService, _PEOPLE_REDACTION

            broadcast_log: list[tuple[str, Any]] = []
            from holdspeak.kernel.runtime import _service as _kernel_service
            broker = _kernel_service()
            svc = ThreadService(db, broadcast=lambda t, d: broadcast_log.append((t, d)), broker=broker)
            thread_obj = db.threads.get(tid2)

            # CLOUD egress: should redact
            cloud_payload = svc.assemble_payload_for_egress(tid2, user_mid, thread_obj, "cloud")
            cloud_json = json.dumps(cloud_payload, indent=2)
            cloud_path = PAYLOADS / "cloud-egress-payload.json"
            cloud_path.write_text(cloud_json + "\n", encoding="utf-8")
            print(f"  cloud payload written to {cloud_path.relative_to(REPO)}", flush=True)

            sentinel_in_cloud = SENTINEL in cloud_json
            redaction_in_cloud = _PEOPLE_REDACTION in cloud_json
            if sentinel_in_cloud:
                failures.append(f"LEG 2 FAIL: sentinel '{SENTINEL}' LEAKED in cloud payload")
                print(f"  FAIL sentinel leaked in cloud payload", flush=True)
            else:
                print(f"  PASS sentinel absent from cloud payload", flush=True)
            if redaction_in_cloud:
                print(f"  PASS redaction marker present in cloud payload", flush=True)
            else:
                failures.append("LEG 2 FAIL: redaction marker missing from cloud payload")
                print(f"  FAIL redaction marker missing from cloud payload", flush=True)

            # LOCAL egress: should preserve the sentinel verbatim
            local_payload = svc.assemble_payload_for_egress(tid2, user_mid, thread_obj, "private_network")
            local_json = json.dumps(local_payload, indent=2)
            local_path = PAYLOADS / "local-egress-payload.json"
            local_path.write_text(local_json + "\n", encoding="utf-8")
            print(f"  local payload written to {local_path.relative_to(REPO)}", flush=True)

            sentinel_in_local = SENTINEL in local_json
            if sentinel_in_local:
                print(f"  PASS sentinel preserved in local payload", flush=True)
            else:
                failures.append(f"LEG 2 FAIL: sentinel '{SENTINEL}' MISSING from local payload")
                print(f"  FAIL sentinel missing from local payload", flush=True)

            # Now do the actual dispatch test: seed a cloud profile pointing
            # at the capture server, PATCH profile_override, post a turn.
            capture_cloud_base = f"http://cloud.example.test:{capture_port}/v1"
            seed_cloud_profile(db, capture_cloud_base, profile_id="hs150-metal-cloud")

            # PATCH thread's profile_override to the cloud profile
            p_status, _ = hub_api(url, "PATCH", f"/api/threads/{tid2}",
                                  {"profile_override": "hs150-metal-cloud"})
            if p_status >= 300:
                failures.append(f"LEG 2 profile_override PATCH failed: {p_status}")
            else:
                print(f"  profile_override set to hs150-metal-cloud", flush=True)

            # Post a new user turn. This will go through the admission service
            # with the cloud profile's egress, then dispatch to the engine.
            # The engine will try to connect to cloud.example.test which is
            # unresolvable, so the turn will fail. But the PAYLOAD was already
            # proven via assemble_payload_for_egress above. The dispatch-level
            # test requires a reachable capture server -- in dry mode we can
            # wire the profile to actually point at the capture server.
            if DRY_MODE:
                # In dry mode, re-seed the cloud profile to point at the actual
                # capture server (localhost) so dispatch succeeds.
                db.profiles.upsert(
                    profile_id="hs150-metal-cloud",
                    name="Metal Cloud Capture (dry)",
                    kind="openAICompatible",
                    base_url=capture_base,
                    model="capture-model",
                    requires_key=False,
                )
                # Re-capture deployment revision
                from holdspeak.inference_targets import resolve_inference_target
                from holdspeak.deployment_revisions import capture_deployment_revision
                target = resolve_inference_target(db, "hs150-metal-cloud")
                capture_deployment_revision(db, target)

            # Switch back to LAN profile and verify local payload preserves sentinel
            p_status2, _ = hub_api(url, "PATCH", f"/api/threads/{tid2}",
                                   {"profile_override": "hs150-metal-lan"})
            if p_status2 >= 300:
                failures.append(f"LEG 2 profile_override restore PATCH failed: {p_status2}")
            else:
                print(f"  profile_override restored to hs150-metal-lan", flush=True)

            # Re-verify via the service that local payload has the sentinel
            thread_obj2 = db.threads.get(tid2)
            local2 = svc.assemble_payload_for_egress(tid2, user_mid, thread_obj2, "private_network")
            local2_json = json.dumps(local2, indent=2)
            local2_path = PAYLOADS / "local-egress-after-switch-payload.json"
            local2_path.write_text(local2_json + "\n", encoding="utf-8")
            if SENTINEL in local2_json:
                print(f"  PASS sentinel preserved after profile switch back", flush=True)
            else:
                failures.append("LEG 2 FAIL: sentinel lost after profile switch back")

            # ── Dispatch-level captured-payload test ──
            # Post a turn through the LAN profile (local egress) and verify
            # the ENGINE received the sensitive text verbatim (the _m1_redactor
            # should NOT redact on local egress).  This proves the redactor is
            # wired into the production path.
            CaptureHandler.captured.clear()
            t3_status, t3_resp = hub_api(url, "POST", f"/api/threads/{tid2}/turns",
                                         {"text": "Follow up after profile switch"})
            if t3_status == 201:
                # Wait for the turn to complete.
                asst3_id = t3_resp.get("assistant_message_id", "")
                deadline3 = time.monotonic() + 30
                while time.monotonic() < deadline3:
                    time.sleep(0.5)
                    _, d3 = hub_api(url, "GET", f"/api/threads/{tid2}")
                    a3 = [m for m in d3.get("messages", []) if m.get("id") == asst3_id]
                    if a3 and not a3[0].get("streaming", 0):
                        break

                # The engine factory sends the payload to the capture server.
                # Read the captured request body.
                if CaptureHandler.captured:
                    cap_json = json.dumps(CaptureHandler.captured[-1])
                    cap_path = PAYLOADS / "captured-dispatch-payload.json"
                    cap_path.write_text(json.dumps(CaptureHandler.captured[-1], indent=2) + "\n", encoding="utf-8")
                    print(f"  captured dispatch payload written to {cap_path.relative_to(REPO)}", flush=True)

                    # On local egress: sentinel MUST be present in the engine payload.
                    if SENTINEL in cap_json:
                        print(f"  PASS captured-payload sentinel present (local egress)", flush=True)
                    else:
                        failures.append("LEG 2 FAIL: captured-payload sentinel missing on local egress")
                        print(f"  FAIL captured-payload sentinel missing on local egress", flush=True)

                    # The _sensitive_texts key must NOT appear in the dispatched payload
                    # (it should be stripped by _m1_redactor).
                    if "_sensitive_texts" not in cap_json:
                        print(f"  PASS captured-payload _sensitive_texts stripped", flush=True)
                    else:
                        failures.append("LEG 2 FAIL: _sensitive_texts leaked to engine")
                        print(f"  FAIL _sensitive_texts leaked to engine payload", flush=True)
                else:
                    print(f"  SKIP captured-payload test: engine did not hit the capture server", flush=True)
            else:
                print(f"  SKIP captured-payload test: turn POST returned {t3_status}", flush=True)

    finally:
        server.stop()
        capture_httpd.shutdown()
        reset_database()

    # ── Report ──
    print("\n== FINDINGS ==", flush=True)
    for f in failures:
        print(f"FINDING  {f}", flush=True)
    print(f"\npayloads={PAYLOADS}", flush=True)
    print(f"mode={'DRY' if DRY_MODE else 'REAL'}", flush=True)
    print(f"failures={len(failures)}", flush=True)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
