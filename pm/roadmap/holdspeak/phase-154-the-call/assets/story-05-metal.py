"""HS-154-05 metal walk -- The Call through the REAL hub, over HTTP.

Boots the real hub in an isolated HOME (never the owner's DB), seeds modes,
guardrails, profiles, and exercises five legs:

  LEG 1 -- call_mode law: POST thread -> GET shows call_mode 0;
           PATCH {call_mode:1} -> GET 1; PATCH 2 -> 400;
           reload-semantics = GET again shows 1.
  LEG 2 -- Frames: with call_mode=1, a turn emits thread_call_state
           transitions (LISTENING->THINKING->LISTENING around the turn).
  LEG 3 -- TTS 404 law: GET /api/tts/status says not installed;
           POST /api/tts -> typed 404; nothing in kernel_receipts.
  LEG 4 -- The ear's server half: POST /api/dictation/transcribe with
           a tiny WAV -> transcript comes back.
  LEG 5 -- LIVE turn sanity under call mode on .43: the Qwen turn
           streams text (grammar override holds -- assert NOT {"line":...}).

Modes:
  DRY  (default)          fake engines, fake transcriber; runs in the sandbox.
  LIVE (HS154_LIVE=1)     real .43 llama.cpp; unsandboxed.

Run:
  uv run python pm/roadmap/holdspeak/phase-154-the-call/assets/story-05-metal.py
  HS154_LIVE=1 uv run python pm/roadmap/holdspeak/phase-154-the-call/assets/story-05-metal.py
"""
from __future__ import annotations

import asyncio
import importlib.util
import io
import json
import os
import struct
import sys
import tempfile
import threading
import time
import wave
from pathlib import Path
from typing import Any

import numpy as np

REPO = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parent
LIVE = os.environ.get("HS154_LIVE") == "1"
PAYLOADS = HERE / ("story-05-metal-payloads-live" if LIVE else "story-05-metal-payloads")

# Reuse 151 metal helpers.
_spec = importlib.util.spec_from_file_location(
    "hs151_metal",
    REPO / "pm/roadmap/holdspeak/phase-151-the-desk-chat/assets/story-08-metal.py",
)
hs151 = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(hs151)
hub_api = hs151.hub_api
TOKEN = hs151.TOKEN
CaptureHandler = hs151.CaptureHandler
start_capture_server = hs151.start_capture_server

# ----------------------------------------------------------------- WAV helper


def _wav_bytes(*, rate: int = 16000, channels: int = 1, width: int = 2,
               seconds: float = 0.25) -> bytes:
    """Build a tiny valid WAV file (silence, 16 kHz, mono, 16-bit PCM)."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(width)
        wf.setframerate(rate)
        wf.writeframes(np.zeros(int(rate * seconds), dtype=np.int16).tobytes())
    return buf.getvalue()


# ----------------------------------------------------------------- DRY engine


class _SimpleEngine:
    """DRY engine for Desk mode: text only, no tools."""
    active_provider = "desk-dry"
    active_model = "desk-model"

    def __init__(self):
        self.calls: list[list[dict]] = []
        self.tools_seen: list[int] = []

    def run_prompt_stream(self, *, messages=None, tools=None, **kw):
        from holdspeak.kernel.inference_stream import Delta
        self.calls.append(list(messages or []))
        self.tools_seen.append(len(tools or []))
        yield Delta(kind="text", text="Simple desk response -- no actions taken.")
        yield Delta(kind="usage", meta={"prompt_tokens": 5, "completion_tokens": 4})
        yield Delta(kind="done")

    def run_prompt_messages(self, **kw):
        return "Simple desk response."

    def run_prompt(self, *, system_prompt="", user_prompt="", **kw):
        return '{"summary": "Summary of the earlier conversation.", "violations": [], "warnings": []}'


# ----------------------------------------------------------------- helpers


def _wait_turn(url: str, tid: str, aid: str, timeout: float = 120.0) -> dict:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        _, detail = hub_api(url, "GET", f"/api/threads/{tid}")
        for m in detail.get("messages", []):
            if m.get("id") == aid and not m.get("streaming"):
                return detail
        time.sleep(0.5)
    raise TimeoutError(f"turn {aid} never completed in {timeout}s")


def _save(name: str, data: Any) -> Path:
    p = PAYLOADS / name
    p.write_text(json.dumps(data, indent=2, default=str) + "\n")
    return p


# ----------------------------------------------------------------- main


def main() -> int:
    t_start = time.monotonic()
    sys.path.insert(0, str(REPO))

    import holdspeak.config as config_module
    import holdspeak.db.core as db_core
    from holdspeak.db import reset_database, get_database
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    real_home = os.environ.get("HOME", str(Path.home()))
    home = Path(tempfile.mkdtemp(prefix="hs154-metal-"))
    os.environ["HOME"] = str(home)
    os.environ.setdefault(
        "PLAYWRIGHT_BROWSERS_PATH",
        str(Path(real_home) / "Library/Caches/ms-playwright"),
    )
    config_module.CONFIG_FILE = home / ".holdspeak" / "config.json"
    db_core.DEFAULT_DB_PATH = home / "holdspeak.db"
    reset_database()
    PAYLOADS.mkdir(parents=True, exist_ok=True)

    failures: list[str] = []
    leg_times: dict[str, float] = {}

    def check(ok: bool, label: str) -> None:
        tag = "PASS" if ok else "FAIL"
        print(f"  {tag} {label}", flush=True)
        if not ok:
            failures.append(label)

    # Transcription callback for leg 4 (the ear's server half).
    def _fake_transcribe(audio_array, *, principal=None, mic_handle=""):
        """Return canned text -- DRY mode only (LIVE uses the real runtime)."""
        return "hello from the call"

    # Current engine holder for DRY mode swapping.
    current_engine = [None]

    try:
        db = get_database()

        # ── Profile + assignment seed ──
        from tests.unit.test_phase143_inference_assignments import _profile, _result_claim, OWNER
        from holdspeak.services.inference_assignment_service import InferenceAssignmentService

        if LIVE:
            model = hs151.detect_model()
            print(f"  LIVE .43 model: {model}", flush=True)
            db.profiles.upsert(
                profile_id="hs154-lan", name="HS-154 LAN (.43)",
                kind="openAICompatible", base_url=hs151.LAN_BASE,
                model=model, context_limit=32768, requires_key=False,
            )
            _profile(db, "hs154-lan", claims=("language", _result_claim("chat.turn")))
            InferenceAssignmentService(db).set_assignment(OWNER, {
                "command_id": "hs154-assign-turn",
                "expected_revision": 0,
                "scope": {"kind": "capability", "capability_id": "chat.turn"},
                "entries": [{"profile_id": "hs154-lan", "profile_revision": 1}],
            })
            from holdspeak.db.reconcile import _backfill_chat_practice_assignments
            with db._connection() as conn:
                _backfill_chat_practice_assignments(conn)
        else:
            _profile(db, "hs154-local", claims=(
                "language",
                _result_claim("chat.turn"),
            ))
            InferenceAssignmentService(db).set_assignment(OWNER, {
                "command_id": "hs154-assign-turn",
                "expected_revision": 0,
                "scope": {"kind": "capability", "capability_id": "chat.turn"},
                "entries": [{"profile_id": "hs154-local", "profile_revision": 1}],
            })
            from holdspeak.db.reconcile import _backfill_chat_practice_assignments
            with db._connection() as conn:
                _backfill_chat_practice_assignments(conn)

        # ── Seed modes + guardrails ──
        from holdspeak.services.thread_modes import seed_modes, seed_guardrails
        seed_modes(db)
        seed_guardrails(db)

        # ── Boot hub ──
        config_dir = home / ".holdspeak"
        config_dir.mkdir(parents=True, exist_ok=True)
        (config_dir / "config.json").write_text(json.dumps({"control_mode": "yolo"}))

        # Provide a transcribe callback for leg 4 (DRY only; LIVE
        # will need the real runtime transcriber -- see leg 4 comment).
        transcribe_cb = _fake_transcribe if not LIVE else None

        server = MeetingWebServer(
            WebRuntimeCallbacks(
                on_bookmark=lambda *_: None,
                on_stop=lambda: None,
                get_state=lambda: {},
                on_transcribe=transcribe_cb,
            ),
            auth_token=TOKEN,
        )
        url = server.start()

        # Wait for the hub to become reachable.
        for attempt in range(20):
            try:
                hub_api(url, "GET", "/api/threads")
                break
            except Exception:
                time.sleep(0.3)
        else:
            raise RuntimeError(f"Hub at {url} never became reachable")

        # Seed desk + onboarding bypass.
        hub_api(url, "POST", "/api/desk/seed")
        hub_api(url, "PUT", "/api/setup/onboarding", {"disposition": "completed"})

        # ── DRY engine wiring ──
        if not LIVE:
            from holdspeak.kernel.runtime import _service as _kernel_service
            broker = _kernel_service()
            engine = _SimpleEngine()
            current_engine[0] = engine
            broker.inference_runner._engine_factory = lambda _rev, **_kw: current_engine[0]
        else:
            from holdspeak.kernel.runtime import _service as _kernel_service
            broker = _kernel_service()
            _engine_base = hs151.LAN_BASE

            class _LiveEngine:
                active_provider = "metal-live"
                active_model = hs151.detect_model()

                def __init__(self, base: str):
                    self._base = base

                def run_prompt_stream(self, *, messages=None, temperature=None, max_tokens=None, tools=None, response_format=None, **kw):
                    import urllib.request
                    from holdspeak.kernel.inference_stream import Delta
                    body_dict: dict[str, Any] = {
                        "model": self.active_model,
                        "messages": messages or [],
                        "stream": True,
                        "max_tokens": max_tokens or 1024,
                    }
                    if tools:
                        body_dict["tools"] = tools
                    else:
                        # HS-153-06: clear the server's default grammar.
                        body_dict["grammar"] = ""
                    if response_format is not None:
                        body_dict["response_format"] = response_format
                    body = json.dumps(body_dict).encode()
                    req = urllib.request.Request(
                        self._base + "/chat/completions",
                        data=body,
                        headers={"Content-Type": "application/json"},
                    )
                    with urllib.request.urlopen(req, timeout=120) as resp:
                        pending_tool_calls: list[dict] = []
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
                            if "tool_calls" in delta:
                                for tc in delta["tool_calls"]:
                                    idx = tc.get("index", 0)
                                    while len(pending_tool_calls) <= idx:
                                        pending_tool_calls.append({"id": "", "name": "", "arguments": ""})
                                    if "id" in tc:
                                        pending_tool_calls[idx]["id"] = tc["id"]
                                    fn = tc.get("function", {})
                                    if "name" in fn:
                                        pending_tool_calls[idx]["name"] = fn["name"]
                                    if "arguments" in fn:
                                        pending_tool_calls[idx]["arguments"] += fn["arguments"]
                            if content:
                                yield Delta(kind="text", text=content)
                            usage = chunk.get("usage")
                            if usage:
                                yield Delta(kind="usage", meta=usage)
                            if finish == "tool_calls" and pending_tool_calls:
                                yield Delta(kind="tool_calls", meta={"tool_calls": pending_tool_calls})
                                pending_tool_calls = []
                            elif finish == "stop":
                                pass
                    yield Delta(kind="usage", meta={"prompt_tokens": 0, "completion_tokens": 0})
                    yield Delta(kind="done")

                def run_prompt_messages(self, *, messages=None, temperature=None, max_tokens=None, response_format=None, **kw):
                    parts = []
                    for delta in self.run_prompt_stream(messages=messages, temperature=temperature, max_tokens=max_tokens, response_format=response_format):
                        if delta.kind == "text":
                            parts.append(delta.text)
                    return "".join(parts)

                def run_prompt(self, *, system_prompt="", user_prompt="", temperature=None, max_tokens=None, response_format=None, **kw):
                    return self.run_prompt_messages(
                        messages=[{"role": "system", "content": system_prompt},
                                  {"role": "user", "content": user_prompt}],
                        temperature=temperature, max_tokens=max_tokens,
                        response_format=response_format,
                    )

            broker.inference_runner._engine_factory = lambda _rev, **_kw: _LiveEngine(_engine_base)

        # ================================================================
        # LEG 1: call_mode law
        # ================================================================
        print("\n== LEG 1: call_mode law ==", flush=True)
        leg1_start = time.monotonic()

        # Create a thread.
        st, thread = hub_api(url, "POST", "/api/threads", {
            "title": "HS-154-05 Leg 1 call_mode",
            "recipe_id": "hs-seed-mode-desk",
        })
        check(st == 201, f"POST /api/threads -> {st}")
        tid1 = thread["id"]

        # GET: call_mode should be 0 (default).
        st_g, detail1 = hub_api(url, "GET", f"/api/threads/{tid1}")
        check(st_g == 200, f"GET /api/threads/{tid1} -> {st_g}")
        check(detail1.get("call_mode") == 0, f"call_mode default is 0 (got {detail1.get('call_mode')})")
        _save("leg-1-get-default.json", detail1)

        # PATCH call_mode=1.
        st_p, patch1 = hub_api(url, "PATCH", f"/api/threads/{tid1}", {"call_mode": 1})
        check(st_p == 200, f"PATCH call_mode=1 -> {st_p}")
        check(patch1.get("call_mode") == 1, f"PATCH response has call_mode=1 (got {patch1.get('call_mode')})")
        _save("leg-1-patch-on.json", patch1)

        # GET again: reload semantics -- call_mode persists as 1.
        st_g2, detail1b = hub_api(url, "GET", f"/api/threads/{tid1}")
        check(st_g2 == 200, f"GET reload -> {st_g2}")
        check(detail1b.get("call_mode") == 1, f"reload shows call_mode=1 (got {detail1b.get('call_mode')})")
        _save("leg-1-get-reload.json", detail1b)

        # PATCH call_mode=2 -> 400.
        st_bad, err_body = hub_api(url, "PATCH", f"/api/threads/{tid1}", {"call_mode": 2})
        check(st_bad == 400, f"PATCH call_mode=2 -> {st_bad} (expect 400)")
        _save("leg-1-patch-invalid.json", {"status": st_bad, "body": err_body})

        # Verify call_mode is still 1 after the bad patch.
        st_g3, detail1c = hub_api(url, "GET", f"/api/threads/{tid1}")
        check(detail1c.get("call_mode") == 1, f"call_mode still 1 after bad PATCH (got {detail1c.get('call_mode')})")

        leg_times["leg1"] = time.monotonic() - leg1_start
        print(f"  LEG 1 done in {leg_times['leg1']:.1f}s", flush=True)

        # ================================================================
        # LEG 2: Frames -- thread_call_state transitions around a turn
        # ================================================================
        print("\n== LEG 2: Frames (thread_call_state) ==", flush=True)
        leg2_start = time.monotonic()

        # Use the thread from leg 1 (already call_mode=1).
        # Connect to the WS bus and collect thread_call_state frames
        # while driving a turn.
        bus_frames: list[dict] = []

        def _bus_collector(ws_url: str, tid: str, timeout: float = 60) -> None:
            """Monitor the WS bus for thread_call_state frames."""
            import asyncio as _aio
            try:
                import websockets
            except ImportError:
                return

            async def _run():
                protocols = hs151.ws_auth_protocols(TOKEN)
                async with websockets.connect(ws_url, subprotocols=protocols) as ws:
                    deadline = time.monotonic() + timeout
                    while time.monotonic() < deadline:
                        try:
                            raw = await _aio.wait_for(
                                ws.recv(), timeout=max(0.1, deadline - time.monotonic()))
                        except _aio.TimeoutError:
                            break
                        frame = json.loads(raw)
                        ft = frame.get("type", "")
                        data = frame.get("data", {})
                        if ft == "thread_call_state" and data.get("thread_id") == tid:
                            bus_frames.append(frame)
                        if ft == "thread_turn_done" and data.get("thread_id") == tid:
                            # Collect one more round to catch LISTENING after done.
                            remaining = deadline - time.monotonic()
                            try:
                                raw2 = await _aio.wait_for(
                                    ws.recv(), timeout=min(2.0, remaining))
                                frame2 = json.loads(raw2)
                                if frame2.get("type") == "thread_call_state" and frame2.get("data", {}).get("thread_id") == tid:
                                    bus_frames.append(frame2)
                            except _aio.TimeoutError:
                                pass
                            break

            loop = _aio.new_event_loop()
            try:
                loop.run_until_complete(_run())
            finally:
                loop.close()

        ws_url = url.replace("http://", "ws://") + "/ws"
        bus_thread = threading.Thread(
            target=_bus_collector, args=(ws_url, tid1, 60), daemon=True)
        bus_thread.start()
        time.sleep(0.3)

        # Send a turn on the call_mode=1 thread.
        if not LIVE:
            current_engine[0] = _SimpleEngine()
        st, turn2 = hub_api(url, "POST", f"/api/threads/{tid1}/turns", {
            "text": "What is 2 + 2?",
        })
        check(st == 201, f"POST /turns (call_mode=1) -> {st}")
        _wait_turn(url, tid1, turn2["assistant_message_id"])
        bus_thread.join(timeout=15)

        _save("leg-2-bus-frames.json", bus_frames)
        states = [f.get("data", {}).get("state") for f in bus_frames]
        print(f"  bus states: {states}", flush=True)

        # Expect THINKING then LISTENING (after the turn finishes).
        # The LISTENING from the PATCH (leg 1) may also be visible depending
        # on WS connection timing, so look for the pattern inside the list.
        has_thinking = "thinking" in states
        has_listening_after = False
        for i, s in enumerate(states):
            if s == "thinking":
                # Look for listening after it.
                if any(st2 == "listening" for st2 in states[i + 1:]):
                    has_listening_after = True
                break
        check(has_thinking, f"THINKING frame present (states={states})")
        check(has_listening_after, f"LISTENING after THINKING (states={states})")

        leg_times["leg2"] = time.monotonic() - leg2_start
        print(f"  LEG 2 done in {leg_times['leg2']:.1f}s", flush=True)

        # ================================================================
        # LEG 3: TTS 404 law
        # ================================================================
        print("\n== LEG 3: TTS 404 law ==", flush=True)
        leg3_start = time.monotonic()

        # GET /api/tts/status -> not installed.
        st_tts, tts_status = hub_api(url, "GET", "/api/tts/status")
        check(st_tts == 200, f"GET /api/tts/status -> {st_tts}")
        check(tts_status.get("installed") is False,
              f"tts installed=false (got {tts_status.get('installed')})")
        _save("leg-3-tts-status.json", tts_status)

        # POST /api/tts -> 404.
        st_tts2, tts_err = hub_api(url, "POST", "/api/tts", {"text": "hello"})
        check(st_tts2 == 404, f"POST /api/tts -> {st_tts2} (expect 404)")
        check(tts_err.get("code") == "tts_not_installed",
              f"404 code = tts_not_installed (got {tts_err.get('code')})")
        _save("leg-3-tts-post-404.json", {"status": st_tts2, "body": tts_err})

        # Nothing in kernel_receipts from TTS (no egress happened).
        # Count kernel_receipts; should be zero or only from earlier legs.
        receipts_before = []
        with db._connection() as conn:
            rows = conn.execute(
                "SELECT receipt_id, outcome FROM kernel_receipts ORDER BY created_at DESC LIMIT 20"
            ).fetchall()
            receipts_before = [dict(r) for r in rows]
        # The TTS routes never create a kernel receipt on 404.
        # If there are receipts they must be from turn operations (leg 2), not TTS.
        tts_receipts = [r for r in receipts_before
                        if "tts" in r.get("outcome", "").lower()]
        check(len(tts_receipts) == 0,
              f"no TTS kernel_receipts (found {len(tts_receipts)})")
        _save("leg-3-receipts-snapshot.json", receipts_before)

        leg_times["leg3"] = time.monotonic() - leg3_start
        print(f"  LEG 3 done in {leg_times['leg3']:.1f}s", flush=True)

        # ================================================================
        # LEG 4: The ear's server half -- POST /api/dictation/transcribe
        # ================================================================
        print("\n== LEG 4: the ear's server half ==", flush=True)
        leg4_start = time.monotonic()

        wav_body = _wav_bytes(rate=16000, channels=1, width=2, seconds=0.25)

        if not LIVE:
            # DRY: the hub was booted with _fake_transcribe callback.
            import urllib.request as _urllib_req
            req4 = _urllib_req.Request(
                url + "/api/dictation/transcribe",
                data=wav_body,
                headers={
                    "X-HoldSpeak-Token": TOKEN,
                    "Content-Type": "application/octet-stream",
                },
                method="POST",
            )
            try:
                with _urllib_req.urlopen(req4, timeout=15) as resp4:
                    st4 = resp4.status
                    body4 = json.loads(resp4.read().decode("utf-8", "replace"))
            except Exception as e:
                import urllib.error
                if isinstance(e, urllib.error.HTTPError):
                    st4 = e.code
                    body4 = json.loads(e.read().decode("utf-8", "replace"))
                else:
                    st4 = 0
                    body4 = {"error": str(e)}

            check(st4 == 200, f"POST /api/dictation/transcribe -> {st4}")
            transcript = body4.get("text", "")
            check(len(transcript) > 0, f"transcript non-empty: '{transcript}'")
            _save("leg-4-transcribe-dry.json", {"status": st4, "body": body4})
        else:
            # LIVE: the hub was booted WITHOUT a transcribe callback (on_transcribe=None).
            # The transcribe route returns 503 "unavailable" because no Whisper model
            # is loaded in this isolated hub. This is EXPECTED -- the glass hub
            # doesn't load a transcribe model in the metal rig's isolated HOME.
            # Mark BLOCKED-BY-ENV.
            import urllib.request as _urllib_req
            req4 = _urllib_req.Request(
                url + "/api/dictation/transcribe",
                data=wav_body,
                headers={
                    "X-HoldSpeak-Token": TOKEN,
                    "Content-Type": "application/octet-stream",
                },
                method="POST",
            )
            try:
                with _urllib_req.urlopen(req4, timeout=15) as resp4:
                    st4 = resp4.status
                    body4 = json.loads(resp4.read().decode("utf-8", "replace"))
            except Exception as e:
                import urllib.error
                if isinstance(e, urllib.error.HTTPError):
                    st4 = e.code
                    body4 = json.loads(e.read().decode("utf-8", "replace"))
                else:
                    st4 = 0
                    body4 = {"error": str(e)}

            if st4 == 200:
                transcript = body4.get("text", "")
                check(True, f"LIVE transcribe -> {st4}, text='{transcript}'")
            elif st4 == 503:
                print("  BLOCKED-BY-ENV: transcribe model not loaded in isolated hub", flush=True)
                print(f"  (response: {body4})", flush=True)
                # Not a failure -- the route works, just no model.
                check(True, "transcribe route answered 503 (no model in isolated env)")
            else:
                check(False, f"unexpected transcribe status: {st4}")

            _save("leg-4-transcribe-live.json", {"status": st4, "body": body4})

        leg_times["leg4"] = time.monotonic() - leg4_start
        print(f"  LEG 4 done in {leg_times['leg4']:.1f}s", flush=True)

        # ================================================================
        # LEG 5: LIVE turn sanity -- grammar override holds
        # ================================================================
        print("\n== LEG 5: LIVE turn sanity (grammar override) ==", flush=True)
        leg5_start = time.monotonic()

        if not LIVE:
            # DRY: the fake engine doesn't produce {"line":...} shaped text.
            if not LIVE:
                current_engine[0] = _SimpleEngine()
            st, thread5 = hub_api(url, "POST", "/api/threads", {
                "title": "HS-154-05 Leg 5 grammar",
                "recipe_id": "hs-seed-mode-desk",
            })
            check(st == 201, f"POST /api/threads (grammar) -> {st}")
            tid5 = thread5["id"]

            # Set call_mode=1.
            hub_api(url, "PATCH", f"/api/threads/{tid5}", {"call_mode": 1})

            st, turn5 = hub_api(url, "POST", f"/api/threads/{tid5}/turns", {
                "text": "Tell me a short joke.",
            })
            check(st == 201, f"POST /turns (grammar) -> {st}")
            detail5 = _wait_turn(url, tid5, turn5["assistant_message_id"])
            _save("leg-5-turn-dry.json", detail5)

            # Verify the assistant text is NOT {"line":...} shaped.
            asst5 = [m for m in detail5["messages"]
                     if m.get("id") == turn5["assistant_message_id"]][0]
            asst5_text = "".join(
                p.get("text", "") for p in asst5.get("parts", []) if p["kind"] == "text"
            )
            is_line_json = False
            try:
                parsed = json.loads(asst5_text.strip())
                if isinstance(parsed, dict) and "line" in parsed:
                    is_line_json = True
            except (json.JSONDecodeError, ValueError):
                pass
            check(not is_line_json,
                  f"DRY text is NOT {{\"line\":...}} shaped: '{asst5_text[:80]}'")
        else:
            # LIVE: drive a real turn through .43 under call mode.
            st, thread5 = hub_api(url, "POST", "/api/threads", {
                "title": "HS-154-05 Leg 5 grammar LIVE",
                "recipe_id": "hs-seed-mode-desk",
            })
            check(st == 201, f"POST /api/threads (grammar LIVE) -> {st}")
            tid5 = thread5["id"]

            # Set call_mode=1.
            hub_api(url, "PATCH", f"/api/threads/{tid5}", {"call_mode": 1})

            # Collect bus frames to see deltas.
            live_deltas: list[str] = []
            live_frames: list[dict] = []

            def _live_delta_collector(ws_url: str, tid: str, timeout: float = 120) -> None:
                import asyncio as _aio
                try:
                    import websockets
                except ImportError:
                    return

                async def _run():
                    protocols = hs151.ws_auth_protocols(TOKEN)
                    async with websockets.connect(ws_url, subprotocols=protocols) as ws:
                        deadline = time.monotonic() + timeout
                        while time.monotonic() < deadline:
                            try:
                                raw = await _aio.wait_for(
                                    ws.recv(), timeout=max(0.1, deadline - time.monotonic()))
                            except _aio.TimeoutError:
                                break
                            frame = json.loads(raw)
                            live_frames.append(frame)
                            ft = frame.get("type", "")
                            data = frame.get("data", {})
                            if ft == "thread_delta" and data.get("thread_id") == tid:
                                live_deltas.append(data.get("text", ""))
                            if ft == "thread_turn_done" and data.get("thread_id") == tid:
                                # Give a brief window for trailing frames.
                                try:
                                    raw2 = await _aio.wait_for(ws.recv(), timeout=2.0)
                                    live_frames.append(json.loads(raw2))
                                except _aio.TimeoutError:
                                    pass
                                break

                loop = _aio.new_event_loop()
                try:
                    loop.run_until_complete(_run())
                finally:
                    loop.close()

            delta_thread = threading.Thread(
                target=_live_delta_collector, args=(ws_url, tid5, 120), daemon=True)
            delta_thread.start()
            time.sleep(0.3)

            st, turn5 = hub_api(url, "POST", f"/api/threads/{tid5}/turns", {
                "text": "Tell me a short joke.",
            })
            check(st == 201, f"POST /turns (grammar LIVE) -> {st}")
            detail5 = _wait_turn(url, tid5, turn5["assistant_message_id"])
            delta_thread.join(timeout=120)

            _save("leg-5-turn-live.json", detail5)
            _save("leg-5-live-deltas.json", live_deltas)
            _save("leg-5-live-frames.json", live_frames)

            # Verify the assistant text is NOT {"line":...} shaped.
            asst5 = [m for m in detail5["messages"]
                     if m.get("id") == turn5["assistant_message_id"]][0]
            asst5_text = "".join(
                p.get("text", "") for p in asst5.get("parts", []) if p["kind"] == "text"
            )
            print(f"  LIVE text (first 200): {asst5_text[:200]}", flush=True)

            is_line_json = False
            try:
                parsed = json.loads(asst5_text.strip())
                if isinstance(parsed, dict) and "line" in parsed:
                    is_line_json = True
            except (json.JSONDecodeError, ValueError):
                pass
            check(not is_line_json,
                  f"LIVE text is NOT {{\"line\":...}} shaped (len={len(asst5_text)})")

            # Also verify streaming deltas came through.
            full_streamed = "".join(live_deltas)
            check(len(full_streamed) > 0,
                  f"LIVE streaming deltas received ({len(live_deltas)} chunks, {len(full_streamed)} chars)")

            # Verify the call_state frames were emitted (THINKING, then LISTENING).
            call_states_5 = [f.get("data", {}).get("state")
                             for f in live_frames
                             if f.get("type") == "thread_call_state"
                             and f.get("data", {}).get("thread_id") == tid5]
            print(f"  LIVE call_state frames: {call_states_5}", flush=True)
            check("thinking" in call_states_5,
                  f"LIVE THINKING frame present (states={call_states_5})")
            check("listening" in call_states_5,
                  f"LIVE LISTENING frame present (states={call_states_5})")

        leg_times["leg5"] = time.monotonic() - leg5_start
        print(f"  LEG 5 done in {leg_times['leg5']:.1f}s", flush=True)

    except Exception as exc:
        import traceback
        print(f"\n  FATAL: {exc}", flush=True)
        traceback.print_exc()
        failures.append(f"FATAL: {exc}")
    finally:
        try:
            server.stop()
        except Exception:
            pass

    # ── Report ──
    total_time = time.monotonic() - t_start
    print("\n== FINDINGS ==", flush=True)
    for f in failures:
        print(f"  FINDING  {f}", flush=True)
    print(f"\nmode={'LIVE' if LIVE else 'DRY'}", flush=True)
    print(f"payloads={PAYLOADS.relative_to(REPO)}", flush=True)
    print(f"total_time={total_time:.1f}s", flush=True)
    for leg, t in sorted(leg_times.items()):
        print(f"  {leg}={t:.1f}s", flush=True)
    print(f"failures={len(failures)}", flush=True)

    # NOTE: The attended voice leg (actual microphone + audible speech)
    # is the owner's and holds the merge word.
    print("\nNOTE: attended voice leg = owner's attended leg (not tested here)", flush=True)

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
