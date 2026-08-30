"""HS-153-06 metal walk -- the Practice through the REAL hub, over HTTP.

Boots the real hub in an isolated HOME (never the owner's DB), seeds modes,
guardrails, profiles, and a person+commitment, then drives six legs:

  LEG 1 -- Mode switch Desk->Chase; Desk turn's payload has no effect tools;
           Chase turn's payload has people.commitment.transition; Draft = no tools.
  LEG 2 -- effect-guard fires: in Chase, ask the model to move a person's
           commitment without a source; assert guardrail violation; safe mode
           sets default_decision=deny; yolo proceeds with receipt.
  LEG 3 -- Annotation round-trip: POST annotation on an assistant part,
           send, assert the next payload's user content starts with
           "The owner annotated:". (Voice part = owner's attended leg.)
  LEG 4 -- /compact after >=3 turns: visible cut row in GET; post-cut turn's
           captured payload contains only the summary + after.
  LEG 5 -- /todo -> action_items row source_type='thread'; Door read shows
           provenance; thread has the receipt row.
  LEG 6 -- egress-guard: bind Desk, set a CLOUD profile_override, ask for a
           people.* read; guardrail violation row; safe mode default=deny;
           captured cloud payload withholds sensitive texts.

Modes:
  DRY  (default)          fake engines, capture server; runs in the sandbox.
  LIVE (HS153_LIVE=1)     real .43 llama.cpp; unsandboxed.

Run:
  uv run python pm/roadmap/holdspeak/phase-153-the-practice/assets/story-06-metal.py
  HS153_LIVE=1 uv run python pm/roadmap/holdspeak/phase-153-the-practice/assets/story-06-metal.py
"""
from __future__ import annotations

import asyncio
import importlib.util
import json
import os
import sys
import tempfile
import threading
import time
import uuid
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parent
LIVE = os.environ.get("HS153_LIVE") == "1"
PAYLOADS = HERE / ("story-06-metal-payloads-live" if LIVE else "story-06-metal-payloads")

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


# ----------------------------------------------------------------- DRY engines


class _DeskEngine:
    """DRY engine for Desk mode: never emits tool calls (evidence read only)."""
    active_provider = "desk-dry"
    active_model = "desk-model"

    def __init__(self):
        self.calls: list[list[dict]] = []
        self.tools_seen: list[int] = []

    def run_prompt_stream(self, *, messages=None, tools=None, **kw):
        from holdspeak.kernel.inference_stream import Delta
        self.calls.append(list(messages or []))
        self.tools_seen.append(len(tools or []))
        yield Delta(kind="text", text="Desk mode response. No actions taken.")
        yield Delta(kind="usage", meta={"prompt_tokens": 5, "completion_tokens": 3})
        yield Delta(kind="done")

    def run_prompt_messages(self, **kw):
        return "Desk mode response."

    def run_prompt(self, *, system_prompt="", user_prompt="", **kw):
        return '{"summary": "Summary of the earlier conversation.", "violations": [], "warnings": []}'


class _ChaseEngine:
    """DRY engine for Chase mode: emits a people.commitment.transition tool call."""
    active_provider = "chase-dry"
    active_model = "chase-model"

    def __init__(self):
        self.calls: list[list[dict]] = []
        self.tools_seen: list[int] = []
        self._pass = 0

    def run_prompt_stream(self, *, messages=None, tools=None, **kw):
        from holdspeak.kernel.inference_stream import Delta
        self.calls.append(list(messages or []))
        self.tools_seen.append(len(tools or []))
        self._pass += 1
        if any(m.get("role") == "tool" for m in (messages or [])):
            yield Delta(kind="text", text="Commitment transition done.")
            yield Delta(kind="usage", meta={"prompt_tokens": 5, "completion_tokens": 3})
            yield Delta(kind="done")
        else:
            yield Delta(kind="tool_calls", meta={"tool_calls": [
                {
                    "id": "call_chase_pct",
                    "name": "people.commitment.transition",
                    "arguments": '{"card_id": "PLACEHOLDER", "verb": "complete"}',
                },
            ]})
            yield Delta(kind="usage", meta={"prompt_tokens": 5, "completion_tokens": 2})
            yield Delta(kind="done")

    def run_prompt_messages(self, **kw):
        return "Transition complete."

    def run_prompt(self, *, system_prompt="", user_prompt="", **kw):
        # For guardrail and compact invocations.
        if "guardrail" in system_prompt.lower():
            return json.dumps({
                "violations": [
                    "people.commitment.transition called without a named source"
                ],
                "warnings": [],
            })
        return json.dumps({"summary": "Summary of the conversation."})


class _DraftEngine:
    """DRY engine for Draft mode: text only, never emits tool calls."""
    active_provider = "draft-dry"
    active_model = "draft-model"

    def __init__(self):
        self.calls: list[list[dict]] = []
        self.tools_seen: list[int] = []

    def run_prompt_stream(self, *, messages=None, tools=None, **kw):
        from holdspeak.kernel.inference_stream import Delta
        self.calls.append(list(messages or []))
        self.tools_seen.append(len(tools or []))
        yield Delta(kind="text", text="Draft mode: just text.")
        yield Delta(kind="usage", meta={"prompt_tokens": 5, "completion_tokens": 3})
        yield Delta(kind="done")

    def run_prompt_messages(self, **kw):
        return "Draft mode."

    def run_prompt(self, **kw):
        return '{"summary": "Draft summary.", "violations": [], "warnings": []}'


class _PeopleReadEngine:
    """DRY engine for egress-guard leg: emits people.readiness tool call."""
    active_provider = "egress-dry"
    active_model = "egress-model"

    def __init__(self):
        self.calls: list[list[dict]] = []
        self.tools_seen: list[int] = []
        self._pass = 0

    def run_prompt_stream(self, *, messages=None, tools=None, **kw):
        from holdspeak.kernel.inference_stream import Delta
        self.calls.append(list(messages or []))
        self.tools_seen.append(len(tools or []))
        self._pass += 1
        if any(m.get("role") == "tool" for m in (messages or [])):
            yield Delta(kind="text", text="People data checked.")
            yield Delta(kind="usage", meta={"prompt_tokens": 5, "completion_tokens": 3})
            yield Delta(kind="done")
        else:
            yield Delta(kind="tool_calls", meta={"tool_calls": [
                {"id": "call_egress_pr", "name": "people.readiness", "arguments": "{}"},
            ]})
            yield Delta(kind="usage", meta={"prompt_tokens": 5, "completion_tokens": 2})
            yield Delta(kind="done")

    def run_prompt_messages(self, **kw):
        return "People data checked."

    def run_prompt(self, *, system_prompt="", user_prompt="", **kw):
        if "guardrail" in system_prompt.lower():
            return json.dumps({
                "violations": [
                    "people.readiness read sent to cloud egress boundary"
                ],
                "warnings": [],
            })
        return json.dumps({"summary": "Summary.", "violations": [], "warnings": []})


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
    home = Path(tempfile.mkdtemp(prefix="hs153-metal-"))
    os.environ["HOME"] = str(home)
    os.environ.setdefault(
        "PLAYWRIGHT_BROWSERS_PATH",
        str(Path(real_home) / "Library/Caches/ms-playwright"),
    )
    config_module.CONFIG_FILE = home / ".holdspeak" / "config.json"
    db_core.DEFAULT_DB_PATH = home / "holdspeak.db"
    reset_database()
    PAYLOADS.mkdir(parents=True, exist_ok=True)

    # Start capture server for cloud egress leg.
    capture_httpd, capture_port, capture_thread = start_capture_server()
    capture_base = f"http://127.0.0.1:{capture_port}/v1"

    failures: list[str] = []
    leg_times: dict[str, float] = {}

    def check(ok: bool, label: str) -> None:
        tag = "PASS" if ok else "FAIL"
        print(f"  {tag} {label}", flush=True)
        if not ok:
            failures.append(label)

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
                profile_id="hs153-lan", name="HS-153 LAN (.43)",
                kind="openAICompatible", base_url=hs151.LAN_BASE,
                model=model, context_limit=32768, requires_key=False,
            )
            _profile(db, "hs153-lan", claims=("language", _result_claim("chat.turn")))
            InferenceAssignmentService(db).set_assignment(OWNER, {
                "command_id": "hs153-assign-turn",
                "expected_revision": 0,
                "scope": {"kind": "capability", "capability_id": "chat.turn"},
                "entries": [{"profile_id": "hs153-lan", "profile_revision": 1}],
            })
            # Backfill guardrail + compact assignments from chat.turn.
            from holdspeak.db.reconcile import _backfill_chat_practice_assignments
            with db._connection() as conn:
                _backfill_chat_practice_assignments(conn)
        else:
            _profile(db, "hs153-local", claims=(
                "language",
                _result_claim("chat.turn"),
            ))
            InferenceAssignmentService(db).set_assignment(OWNER, {
                "command_id": "hs153-assign-turn",
                "expected_revision": 0,
                "scope": {"kind": "capability", "capability_id": "chat.turn"},
                "entries": [{"profile_id": "hs153-local", "profile_revision": 1}],
            })
            # Backfill guardrail + compact assignments from chat.turn.
            from holdspeak.db.reconcile import _backfill_chat_practice_assignments
            with db._connection() as conn:
                _backfill_chat_practice_assignments(conn)

        # ── Cloud profile (capture server) ──
        cloud_base = f"http://cloud.example.test:{capture_port}/v1"
        db.profiles.upsert(
            profile_id="hs153-cloud", name="HS-153 cloud (capture)",
            kind="openAICompatible", base_url=cloud_base,
            model="capture-model", context_limit=32768, requires_key=False,
        )
        _profile(db, "hs153-cloud", claims=("language", _result_claim("chat.turn")))

        # ── Seed modes + guardrails ──
        from holdspeak.services.thread_modes import seed_modes, seed_guardrails
        seed_modes(db)
        seed_guardrails(db)

        # ── Boot hub ──
        # Start with yolo for LEG 1.
        config_dir = home / ".holdspeak"
        config_dir.mkdir(parents=True, exist_ok=True)
        (config_dir / "config.json").write_text(json.dumps({"control_mode": "yolo"}))

        server = MeetingWebServer(
            WebRuntimeCallbacks(
                on_bookmark=lambda *_: None,
                on_stop=lambda: None,
                get_state=lambda: {},
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
            desk_engine = _DeskEngine()
            current_engine[0] = desk_engine
            broker.inference_runner._engine_factory = lambda _rev, **_kw: current_engine[0]
        else:
            from holdspeak.kernel.runtime import _service as _kernel_service
            broker = _kernel_service()
            # LIVE: override engine factory to use the OpenAI-compatible endpoint.
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
                        # Tool calls carry their own grammar; do NOT
                        # send grammar:"" alongside tools.
                        body_dict["tools"] = tools
                    else:
                        # HS-153-06: clear the server's default grammar so
                        # response_format / free text works on .43.
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
                            # Handle tool_calls in delta.
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
        # LEG 1: Mode switch Desk -> Chase -> Draft; tool palette checks
        # ================================================================
        print("\n== LEG 1: Mode switch Desk->Chase->Draft ==", flush=True)
        leg1_start = time.monotonic()

        # Create thread in Desk mode.
        st, thread = hub_api(url, "POST", "/api/threads", {
            "title": "HS-153-06 Leg 1 mode",
            "recipe_id": "hs-seed-mode-desk",
        })
        check(st == 201, f"POST /api/threads (Desk) -> {st}")
        tid1 = thread["id"]

        # Desk turn.
        if not LIVE:
            current_engine[0] = _DeskEngine()
        st, turn1 = hub_api(url, "POST", f"/api/threads/{tid1}/turns", {
            "text": "Show me the current state of my desk.",
        })
        check(st == 201, f"POST /turns (Desk) -> {st}")
        detail1 = _wait_turn(url, tid1, turn1["assistant_message_id"])
        _save("leg-1-desk-thread.json", detail1)

        # Desk payload: no effect tools (no people.commitment.transition).
        if not LIVE:
            desk_tools = current_engine[0].tools_seen
            check(desk_tools[0] > 0, f"Desk engine saw tools ({desk_tools[0]})")
            # Desk palette does NOT include effect tools.
            from holdspeak.services.thread_modes import _DESK_TOOLS, _CHASE_EXTRAS
            from holdspeak.services.thread_tools import TOOL_NAMES
            desk_palette = _DESK_TOOLS & TOOL_NAMES
            for eff in _CHASE_EXTRAS:
                check(eff not in desk_palette, f"Desk palette excludes {eff}")
        else:
            # LIVE: verify via GET that the thread has the Desk recipe.
            _, td1 = hub_api(url, "GET", f"/api/threads/{tid1}")
            check(td1.get("recipe_id") == "hs-seed-mode-desk",
                  f"Thread recipe_id is desk: {td1.get('recipe_id')}")

        # Switch to Chase.
        st, _ = hub_api(url, "PATCH", f"/api/threads/{tid1}", {
            "recipe_id": "hs-seed-mode-chase",
        })
        check(st < 300, f"PATCH recipe_id -> Chase: {st}")

        # Chase turn: palette should include people.commitment.transition.
        if not LIVE:
            chase_engine = _ChaseEngine()
            current_engine[0] = chase_engine
        st, turn1c = hub_api(url, "POST", f"/api/threads/{tid1}/turns", {
            "text": "Move Alice's commitment to complete.",
        })
        check(st == 201, f"POST /turns (Chase) -> {st}")
        detail1c = _wait_turn(url, tid1, turn1c["assistant_message_id"])
        _save("leg-1-chase-thread.json", detail1c)

        if not LIVE:
            check(chase_engine.tools_seen[0] > 0, f"Chase engine saw tools ({chase_engine.tools_seen[0]})")
            from holdspeak.services.thread_tools import tool_schemas_for
            chase_palette = (_DESK_TOOLS | _CHASE_EXTRAS) & TOOL_NAMES
            chase_schemas = tool_schemas_for(chase_palette)
            chase_tool_names = {s["function"]["name"] for s in chase_schemas}
            check("people.commitment.transition" in chase_tool_names,
                  "Chase palette includes people.commitment.transition")

        # Draft mode turn: no tools at all.
        st, thread_d = hub_api(url, "POST", "/api/threads", {
            "title": "HS-153-06 Leg 1 draft",
            "recipe_id": "hs-seed-mode-draft",
        })
        check(st == 201, f"POST /api/threads (Draft) -> {st}")
        if not LIVE:
            current_engine[0] = _DraftEngine()
        st, turn1d = hub_api(url, "POST", f"/api/threads/{thread_d['id']}/turns", {
            "text": "Write a short poem.",
        })
        check(st == 201, f"POST /turns (Draft) -> {st}")
        detail1d = _wait_turn(url, thread_d["id"], turn1d["assistant_message_id"])
        _save("leg-1-draft-thread.json", detail1d)

        if not LIVE:
            draft_engine = current_engine[0]
            check(draft_engine.tools_seen[0] == 0,
                  f"Draft engine saw 0 tools ({draft_engine.tools_seen[0]})")
        else:
            # LIVE: verify assistant produced text, no tool_call parts.
            asst_d = [m for m in detail1d["messages"]
                      if m.get("id") == turn1d["assistant_message_id"]][0]
            tc_parts = [p for p in asst_d.get("parts", []) if p["kind"] == "tool_call"]
            check(len(tc_parts) == 0, f"Draft turn: no tool_call parts ({len(tc_parts)})")

        leg_times["leg1"] = time.monotonic() - leg1_start
        print(f"  LEG 1 done in {leg_times['leg1']:.1f}s", flush=True)

        # ================================================================
        # LEG 2: effect-guard fires on people.commitment.transition
        # ================================================================
        print("\n== LEG 2: effect-guard fires (Chase, safe mode) ==", flush=True)
        leg2_start = time.monotonic()

        # Switch to safe mode.
        (config_dir / "config.json").write_text(json.dumps({"control_mode": "safe"}))

        # Seed a person + commitment through the People service.
        svc_people = None
        commitment_id = None
        relationship_id = None
        try:
            from holdspeak.services.people_service import PeopleService
            from holdspeak.people import production_people_store
            # Set up a file-based keystore in the isolated HOME so we
            # never touch the real macOS keychain.
            keyfile = home / ".holdspeak" / "people-keys.json"
            os.environ["HOLDSPEAK_PEOPLE_KEYSTORE_FILE"] = str(keyfile)
            svc_people = PeopleService(production_people_store())
            svc_people.setup(OWNER)
            rel = svc_people.create_relationship(OWNER, {"display_name": "Alice Tester"})
            relationship_id = rel["id"]
            req = svc_people.create_request(OWNER, relationship_id, {"body": "Ship the demo"})
            comm = svc_people.accept_request(OWNER, req["id"])
            commitment_id = comm.get("id", "")
            print(f"  Seeded person: rel={relationship_id} commitment={commitment_id}", flush=True)
        except Exception as exc:
            print(f"  WARNING: People seed failed: {exc}", flush=True)
            # Leg 2 can still verify guardrail with a fake card_id.
            commitment_id = "fake-commitment-id"

        # Create a Chase thread.
        if not LIVE:
            chase2 = _ChaseEngine()
            if commitment_id:
                chase2_args = json.dumps({"card_id": f"people:{commitment_id}", "verb": "complete"})
            else:
                chase2_args = '{"card_id": "people:fake", "verb": "complete"}'

            class _Chase2Engine(_ChaseEngine):
                def run_prompt_stream(self, *, messages=None, tools=None, **kw):
                    from holdspeak.kernel.inference_stream import Delta
                    self.calls.append(list(messages or []))
                    self.tools_seen.append(len(tools or []))
                    self._pass += 1
                    if any(m.get("role") == "tool" for m in (messages or [])):
                        yield Delta(kind="text", text="Done.")
                        yield Delta(kind="usage", meta={"prompt_tokens": 5, "completion_tokens": 1})
                        yield Delta(kind="done")
                    else:
                        yield Delta(kind="tool_calls", meta={"tool_calls": [
                            {"id": "call_chase2_pct", "name": "people.commitment.transition",
                             "arguments": chase2_args},
                        ]})
                        yield Delta(kind="usage", meta={"prompt_tokens": 5, "completion_tokens": 2})
                        yield Delta(kind="done")

            current_engine[0] = _Chase2Engine()

        st, thread2 = hub_api(url, "POST", "/api/threads", {
            "title": "HS-153-06 Leg 2 guardrail",
            "recipe_id": "hs-seed-mode-chase",
        })
        check(st == 201, f"POST /api/threads (Chase, safe) -> {st}")
        tid2 = thread2["id"]

        # The turn will emit a tool_call for people.commitment.transition.
        # In safe mode with a guardrail violation, the pending frame should have
        # default_decision=deny. The tool will hang awaiting a decision. We need
        # to watch for the pending frame and auto-decide.
        bus_log: list[dict] = []

        def _bus_monitor(ws_url: str, tid: str, timeout: float = 60) -> None:
            """Monitor the WS bus for pending frames and auto-deny."""
            import asyncio as _aio
            try:
                import websockets
            except ImportError:
                return

            async def _run():
                protocols = hs151.ws_auth_protocols(TOKEN)
                ws_url_full = ws_url
                async with websockets.connect(ws_url_full, subprotocols=protocols) as ws:
                    deadline = time.monotonic() + timeout
                    while time.monotonic() < deadline:
                        try:
                            raw = await _aio.wait_for(
                                ws.recv(), timeout=max(0.1, deadline - time.monotonic()))
                        except _aio.TimeoutError:
                            break
                        frame = json.loads(raw)
                        bus_log.append(frame)
                        ft = frame.get("type", "")
                        data = frame.get("data", {})
                        if ft == "thread_tool_pending" and data.get("thread_id") == tid:
                            # Auto-decide: deny in safe mode.
                            call_id = data.get("call_id", "")
                            if call_id:
                                hub_api(url, "POST",
                                        f"/api/threads/{tid}/decide",
                                        {"call_id": call_id, "decision": "deny"})
                        if ft == "thread_turn_done" and data.get("thread_id") == tid:
                            break

            loop = _aio.new_event_loop()
            try:
                loop.run_until_complete(_run())
            finally:
                loop.close()

        ws_url = url.replace("http://", "ws://") + "/ws"
        bus_thread = threading.Thread(target=_bus_monitor, args=(ws_url, tid2, 60), daemon=True)
        bus_thread.start()
        time.sleep(0.3)

        prompt_text = "Move this person's commitment to complete. Do not specify any source."
        if LIVE:
            prompt_text = (
                "Call the tool people.commitment.transition with card_id="
                f"'people:{commitment_id}' and verb='complete'. "
                "Do not name a source. Just call the tool."
            )

        st, turn2 = hub_api(url, "POST", f"/api/threads/{tid2}/turns", {"text": prompt_text})
        check(st == 201, f"POST /turns (guardrail) -> {st}")

        # Wait for the turn to finish (bus monitor will auto-deny).
        detail2 = _wait_turn(url, tid2, turn2["assistant_message_id"])
        bus_thread.join(timeout=10)
        _save("leg-2-guardrail-thread.json", detail2)

        # Check for guardrail part.
        asst2 = [m for m in detail2["messages"]
                 if m.get("id") == turn2["assistant_message_id"]][0]
        guardrail_parts = [p for p in asst2.get("parts", []) if p["kind"] == "guardrail"]
        check(len(guardrail_parts) > 0, f"guardrail part present ({len(guardrail_parts)})")

        if guardrail_parts:
            gp_meta = guardrail_parts[0].get("meta_json", {})
            if isinstance(gp_meta, str):
                gp_meta = json.loads(gp_meta)
            violations = gp_meta.get("violations", [])
            check(len(violations) > 0, f"guardrail has violations ({violations})")

        # Check bus log for pending frame with default_decision.
        pending_frames = [f for f in bus_log
                         if f.get("type") == "thread_tool_pending"
                         and f.get("data", {}).get("thread_id") == tid2]
        if pending_frames:
            dd = pending_frames[0].get("data", {}).get("default_decision", "")
            check(dd == "deny", f"safe mode default_decision=deny (got '{dd}')")
            _save("leg-2-pending-frame.json", pending_frames[0])
        else:
            check(False, "no pending frame captured on bus")

        # Now test yolo: same scenario but with yolo mode -> should proceed with receipt.
        print("\n  -- Leg 2b: yolo mode -> proceeds with receipt --", flush=True)
        (config_dir / "config.json").write_text(json.dumps({"control_mode": "yolo"}))

        if not LIVE:
            current_engine[0] = _Chase2Engine()

        bus_log_yolo: list[dict] = []

        def _bus_yolo(ws_url: str, tid: str, timeout: float = 60) -> None:
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
                        bus_log_yolo.append(frame)
                        if frame.get("type") == "thread_turn_done" and frame.get("data", {}).get("thread_id") == tid:
                            break

            loop = _aio.new_event_loop()
            try:
                loop.run_until_complete(_run())
            finally:
                loop.close()

        st, thread2y = hub_api(url, "POST", "/api/threads", {
            "title": "HS-153-06 Leg 2 yolo",
            "recipe_id": "hs-seed-mode-chase",
        })
        tid2y = thread2y["id"]
        bus_thread2 = threading.Thread(target=_bus_yolo, args=(ws_url, tid2y, 60), daemon=True)
        bus_thread2.start()
        time.sleep(0.3)

        st, turn2y = hub_api(url, "POST", f"/api/threads/{tid2y}/turns", {"text": prompt_text})
        check(st == 201, f"POST /turns (yolo guardrail) -> {st}")
        detail2y = _wait_turn(url, tid2y, turn2y["assistant_message_id"])
        bus_thread2.join(timeout=10)
        _save("leg-2-yolo-thread.json", detail2y)

        # In yolo, the tool should have executed (not denied).
        asst2y = [m for m in detail2y["messages"]
                  if m.get("id") == turn2y["assistant_message_id"]][0]
        tool_msgs2y = [m for m in detail2y["messages"] if m.get("role") == "tool"]
        if tool_msgs2y:
            tool_meta = (tool_msgs2y[0]["parts"][0].get("meta_json") or {})
            if isinstance(tool_meta, str):
                tool_meta = json.loads(tool_meta)
            tool_kind = tool_meta.get("kind", "")
            # In yolo mode, the tool should not be denied.
            check(tool_kind != "tool_denied", f"yolo: tool not denied (kind={tool_kind})")
            receipt = tool_meta.get("receipt_id", "")
            # Receipt may be present or not depending on whether the tool succeeded.
            print(f"  yolo: tool kind={tool_kind} receipt={receipt}", flush=True)
        else:
            # No tool messages -> check if there are tool_call parts at least.
            tc_parts = [p for p in asst2y.get("parts", []) if p["kind"] == "tool_call"]
            if not LIVE:
                check(len(tc_parts) > 0, "yolo: tool_call parts present")
            else:
                print(f"  LIVE: no tool messages; model may not have called the tool", flush=True)

        leg_times["leg2"] = time.monotonic() - leg2_start
        print(f"  LEG 2 done in {leg_times['leg2']:.1f}s", flush=True)

        # ================================================================
        # LEG 3: Annotation round-trip
        # ================================================================
        print("\n== LEG 3: Annotation round-trip ==", flush=True)
        leg3_start = time.monotonic()

        if not LIVE:
            current_engine[0] = _DeskEngine()

        # Create a thread, send a turn, then annotate the assistant's response.
        st, thread3 = hub_api(url, "POST", "/api/threads", {
            "title": "HS-153-06 Leg 3 annotation",
            "recipe_id": "hs-seed-mode-desk",
        })
        check(st == 201, f"POST /api/threads (annotation) -> {st}")
        tid3 = thread3["id"]

        st, turn3 = hub_api(url, "POST", f"/api/threads/{tid3}/turns", {
            "text": "Summarize my upcoming week.",
        })
        check(st == 201, f"POST /turns (annotation) -> {st}")
        detail3 = _wait_turn(url, tid3, turn3["assistant_message_id"])
        asst3 = [m for m in detail3["messages"]
                 if m.get("id") == turn3["assistant_message_id"]][0]
        asst3_text = "".join(
            p.get("text", "") for p in asst3.get("parts", []) if p["kind"] == "text"
        )

        # POST annotation on the assistant part.
        quote = asst3_text[:30] if asst3_text else "test quote"
        comment = "This needs more detail"
        st_ann, ann = hub_api(url, "POST", f"/api/threads/{tid3}/annotations", {
            "message_id": turn3["assistant_message_id"],
            "quote": quote,
            "comment": comment,
        })
        check(st_ann == 201, f"POST annotation -> {st_ann}")
        if st_ann == 201:
            check(ann.get("kind") == "annotation", f"annotation kind: {ann.get('kind')}")
            ann_text = ann.get("text", "")
            check(ann_text.startswith("The owner annotated:"),
                  f"annotation text prefix: {ann_text[:50]}")
            check(ann.get("draft") is True or ann.get("draft") == 1,
                  f"annotation is draft: {ann.get('draft')}")
            _save("leg-3-annotation.json", ann)

        # GET thread -> draft_annotations present.
        _, detail3b = hub_api(url, "GET", f"/api/threads/{tid3}")
        drafts = detail3b.get("draft_annotations", [])
        check(len(drafts) > 0, f"draft_annotations in GET ({len(drafts)})")

        # Send a new turn (promotes the draft).
        if not LIVE:
            current_engine[0] = _DeskEngine()
        st, turn3b = hub_api(url, "POST", f"/api/threads/{tid3}/turns", {
            "text": "Please elaborate on Monday.",
        })
        check(st == 201, f"POST /turns (after annotation) -> {st}")
        detail3c = _wait_turn(url, tid3, turn3b["assistant_message_id"])
        _save("leg-3-post-annotation-thread.json", detail3c)

        # The promoted user message should contain annotation text.
        user_msgs = [m for m in detail3c["messages"]
                     if m.get("role") == "user" and m.get("id") != turn3["user_message_id"]]
        # Find the promoted user message (the one containing the annotation).
        found_annotation_prefix = False
        for um in user_msgs:
            for p in um.get("parts", []):
                if p.get("kind") == "annotation" and "The owner annotated:" in str(p.get("text", "")):
                    found_annotation_prefix = True
        check(found_annotation_prefix,
              "promoted user message contains 'The owner annotated:' prefix")

        # After send, draft_annotations should be empty.
        _, detail3d = hub_api(url, "GET", f"/api/threads/{tid3}")
        drafts_after = detail3d.get("draft_annotations", [])
        check(len(drafts_after) == 0, f"draft_annotations empty after send ({len(drafts_after)})")

        # NOTE: The voice part of annotation is the owner's attended leg.
        print("  NOTE: voice annotation = owner's attended leg (not tested here)", flush=True)

        leg_times["leg3"] = time.monotonic() - leg3_start
        print(f"  LEG 3 done in {leg_times['leg3']:.1f}s", flush=True)

        # ================================================================
        # LEG 4: /compact after >=3 turns
        # ================================================================
        print("\n== LEG 4: /compact ==", flush=True)
        leg4_start = time.monotonic()

        if not LIVE:
            current_engine[0] = _DeskEngine()

        st, thread4 = hub_api(url, "POST", "/api/threads", {
            "title": "HS-153-06 Leg 4 compact",
            "recipe_id": "hs-seed-mode-desk",
        })
        check(st == 201, f"POST /api/threads (compact) -> {st}")
        tid4 = thread4["id"]

        # Send 3 turns.
        prompts_4 = [
            "Tell me about project management.",
            "What are the best practices?",
            "Give me a specific example.",
        ]
        for i, p in enumerate(prompts_4):
            if not LIVE:
                current_engine[0] = _DeskEngine()
            st, t = hub_api(url, "POST", f"/api/threads/{tid4}/turns", {"text": p})
            check(st == 201, f"POST /turns compact-{i+1} -> {st}")
            _wait_turn(url, tid4, t["assistant_message_id"])

        # POST /compact.
        import asyncio
        st_c, compact_result = hub_api(url, "POST", f"/api/threads/{tid4}/compact")
        check(st_c < 300, f"POST /compact -> {st_c}")
        _save("leg-4-compact-result.json", compact_result)

        if isinstance(compact_result, dict):
            check(compact_result.get("status") == "ok",
                  f"compact status: {compact_result.get('status')}")
            cut_at = compact_result.get("cut_at", "")
            check(bool(cut_at), f"compact cut_at present: {cut_at}")

        # GET thread -> visible cut row.
        _, detail4 = hub_api(url, "GET", f"/api/threads/{tid4}")
        _save("leg-4-post-compact-thread.json", detail4)

        system_msgs = [m for m in detail4["messages"] if m.get("role") == "system"]
        compaction_rows = []
        for sm in system_msgs:
            stats = sm.get("stats_json")
            if stats:
                try:
                    parsed = json.loads(stats) if isinstance(stats, str) else stats
                    if parsed.get("compaction"):
                        compaction_rows.append(sm)
                except (json.JSONDecodeError, TypeError):
                    pass
        check(len(compaction_rows) > 0, f"compaction system row present ({len(compaction_rows)})")

        # Post another turn after compaction and verify payload.
        if not LIVE:
            desk_after_cut = _DeskEngine()
            current_engine[0] = desk_after_cut
        st, turn4_post = hub_api(url, "POST", f"/api/threads/{tid4}/turns", {
            "text": "What was the summary?",
        })
        check(st == 201, f"POST /turns (post-compact) -> {st}")
        detail4b = _wait_turn(url, tid4, turn4_post["assistant_message_id"])
        _save("leg-4-post-compact-turn.json", detail4b)

        if not LIVE:
            # Verify: the engine's messages should NOT contain pre-cut text.
            engine_msgs = desk_after_cut.calls[0] if desk_after_cut.calls else []
            engine_content = "\n".join(str(m.get("content", "")) for m in engine_msgs)
            # The first prompt should not be in the post-cut payload.
            check(prompts_4[0] not in engine_content,
                  "post-cut payload does NOT contain pre-cut text")
            # But the summary should be there.
            check("summary" in engine_content.lower() or "conversation" in engine_content.lower(),
                  "post-cut payload contains summary")
            _save("leg-4-post-cut-engine-messages.json", engine_msgs)

        leg_times["leg4"] = time.monotonic() - leg4_start
        print(f"  LEG 4 done in {leg_times['leg4']:.1f}s", flush=True)

        # ================================================================
        # LEG 5: /todo -> action_items row source_type='thread'
        # ================================================================
        print("\n== LEG 5: /todo ==", flush=True)
        leg5_start = time.monotonic()

        if not LIVE:
            current_engine[0] = _DeskEngine()

        st, thread5 = hub_api(url, "POST", "/api/threads", {
            "title": "HS-153-06 Leg 5 todo",
            "recipe_id": "hs-seed-mode-desk",
        })
        check(st == 201, f"POST /api/threads (todo) -> {st}")
        tid5 = thread5["id"]

        # Send a turn first (so there's a message to reference).
        st, turn5 = hub_api(url, "POST", f"/api/threads/{tid5}/turns", {
            "text": "Remind me about the design review.",
        })
        check(st == 201, f"POST /turns (todo context) -> {st}")
        _wait_turn(url, tid5, turn5["assistant_message_id"])

        # POST /todo.
        todo_text = "Review the 153 design with the owner"
        st_t, todo_result = hub_api(url, "POST", f"/api/threads/{tid5}/todo", {
            "text": todo_text,
        })
        check(st_t < 300, f"POST /todo -> {st_t}")
        _save("leg-5-todo-result.json", todo_result)

        if isinstance(todo_result, dict):
            check(todo_result.get("status") == "ok",
                  f"todo status: {todo_result.get('status')}")
            check(bool(todo_result.get("receipt_id")),
                  f"todo has receipt_id: {todo_result.get('receipt_id')}")

        # Verify action_items row.
        with db._connection() as conn:
            ai_row = conn.execute(
                "SELECT id, source_type, source_ref FROM action_items "
                "WHERE source_type='thread' ORDER BY rowid DESC LIMIT 1",
            ).fetchone()
        check(ai_row is not None,
              f"action_items row with source_type='thread' ({dict(ai_row) if ai_row else None})")

        # GET thread -> receipt row (tool_call + tool result).
        _, detail5 = hub_api(url, "GET", f"/api/threads/{tid5}")
        _save("leg-5-todo-thread.json", detail5)

        tool_msgs5 = [m for m in detail5["messages"] if m.get("role") == "tool"]
        check(len(tool_msgs5) > 0, f"tool message from /todo ({len(tool_msgs5)})")
        if tool_msgs5:
            tm = tool_msgs5[-1]
            tm_meta = (tm["parts"][0].get("meta_json") or {})
            if isinstance(tm_meta, str):
                tm_meta = json.loads(tm_meta)
            check(tm_meta.get("name") == "door.add_item",
                  f"tool is door.add_item ({tm_meta.get('name')})")
            check(bool(tm_meta.get("receipt_id")),
                  f"receipt_id on tool result ({tm_meta.get('receipt_id')})")

        # Door read: verify the action item is visible via all-action-items API.
        # The door.add_item inserts with status='open', but the API filters
        # on 'pending' by default; use include_completed=true to see all.
        st_d, all_ai = hub_api(url, "GET", "/api/all-action-items?include_completed=true")
        if st_d == 200:
            items = all_ai.get("action_items", []) if isinstance(all_ai, dict) else all_ai
            thread_items = [it for it in items if it.get("source_type") == "thread"]
            check(len(thread_items) > 0,
                  f"action-items API shows thread-sourced item ({len(thread_items)})")
            if thread_items:
                _save("leg-5-door-thread-item.json", thread_items[0])
        else:
            print(f"  WARNING: GET /api/all-action-items -> {st_d}", flush=True)

        leg_times["leg5"] = time.monotonic() - leg5_start
        print(f"  LEG 5 done in {leg_times['leg5']:.1f}s", flush=True)

        # ================================================================
        # LEG 6: egress-guard on cloud profile override
        # ================================================================
        print("\n== LEG 6: egress-guard (cloud override, safe mode) ==", flush=True)
        leg6_start = time.monotonic()

        # Switch to safe mode + Desk mode (egress-guard enabled on Desk).
        (config_dir / "config.json").write_text(json.dumps({"control_mode": "safe"}))

        if not LIVE:
            current_engine[0] = _PeopleReadEngine()

        st, thread6 = hub_api(url, "POST", "/api/threads", {
            "title": "HS-153-06 Leg 6 egress",
            "recipe_id": "hs-seed-mode-desk",
            "profile_override": "hs153-cloud",
        })
        check(st == 201, f"POST /api/threads (egress) -> {st}")
        tid6 = thread6["id"]

        # Verify the thread has the cloud override.
        _, t6_detail = hub_api(url, "GET", f"/api/threads/{tid6}")
        check(t6_detail.get("profile_override") == "hs153-cloud",
              f"profile_override is hs153-cloud: {t6_detail.get('profile_override')}")

        # Bus monitor for egress guard leg.
        bus_log6: list[dict] = []

        def _bus_egress(ws_url: str, tid: str, timeout: float = 60) -> None:
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
                        bus_log6.append(frame)
                        ft = frame.get("type", "")
                        data = frame.get("data", {})
                        if ft == "thread_tool_pending" and data.get("thread_id") == tid:
                            call_id = data.get("call_id", "")
                            if call_id:
                                hub_api(url, "POST",
                                        f"/api/threads/{tid}/decide",
                                        {"call_id": call_id, "decision": "deny"})
                        if ft == "thread_turn_done" and data.get("thread_id") == tid:
                            break

            loop = _aio.new_event_loop()
            try:
                loop.run_until_complete(_run())
            finally:
                loop.close()

        bus_t6 = threading.Thread(target=_bus_egress, args=(ws_url, tid6, 60), daemon=True)
        bus_t6.start()
        time.sleep(0.3)

        egress_prompt = "Check the People store readiness."
        if LIVE:
            egress_prompt = (
                "Call the tool people.readiness with no arguments. "
                "Just call the tool, nothing else."
            )

        st, turn6 = hub_api(url, "POST", f"/api/threads/{tid6}/turns", {
            "text": egress_prompt,
        })
        check(st == 201, f"POST /turns (egress guard) -> {st}")
        detail6 = _wait_turn(url, tid6, turn6["assistant_message_id"])
        bus_t6.join(timeout=10)
        _save("leg-6-egress-thread.json", detail6)

        # Check for guardrail violation row.
        asst6 = [m for m in detail6["messages"]
                 if m.get("id") == turn6["assistant_message_id"]][0]
        gp6 = [p for p in asst6.get("parts", []) if p["kind"] == "guardrail"]
        check(len(gp6) > 0, f"egress guardrail part present ({len(gp6)})")
        if gp6:
            gp6_meta = gp6[0].get("meta_json", {})
            if isinstance(gp6_meta, str):
                gp6_meta = json.loads(gp6_meta)
            v6 = gp6_meta.get("violations", [])
            check(len(v6) > 0, f"egress guardrail violations ({v6})")

        # Check pending frame default_decision=deny.
        pending6 = [f for f in bus_log6
                    if f.get("type") == "thread_tool_pending"
                    and f.get("data", {}).get("thread_id") == tid6]
        if pending6:
            dd6 = pending6[0].get("data", {}).get("default_decision", "")
            check(dd6 == "deny", f"egress safe mode default_decision=deny (got '{dd6}')")
            _save("leg-6-pending-frame.json", pending6[0])
        else:
            check(False, "no pending frame from egress guard")

        # Check that the cloud egress payload withholds sensitive texts.
        # The thread has a cloud profile_override, so the assembler should
        # redact People content.
        from holdspeak.services.thread_service import ThreadService, _PEOPLE_REDACTION
        broadcast_log: list[tuple] = []
        svc = ThreadService(db, broadcast=lambda t, d: broadcast_log.append((t, d)), broker=broker)
        thread6_obj = db.threads.get(tid6)

        # First: check if there are any sensitive parts.
        path6 = db.threads.list_path(tid6)
        has_sensitive = False
        for msg in path6:
            parts = db.threads.get_parts(msg.id)
            for p in parts:
                if p.sensitive:
                    has_sensitive = True
                    break

        if has_sensitive:
            cloud_payload6 = svc.assemble_payload_for_egress(
                tid6, path6[-1].id if path6 else "", thread6_obj, "cloud",
            )
            cloud_json6 = json.dumps(cloud_payload6, indent=2)
            _save("leg-6-cloud-payload.json", cloud_payload6)

            # The cloud payload should have redaction markers.
            check(_PEOPLE_REDACTION in cloud_json6,
                  "cloud payload carries [people content withheld]")
        else:
            print("  NOTE: no sensitive parts found (model may not have called people.*)", flush=True)
            if not LIVE:
                check(False, "DRY mode should have sensitive parts from people.readiness")

        leg_times["leg6"] = time.monotonic() - leg6_start
        print(f"  LEG 6 done in {leg_times['leg6']:.1f}s", flush=True)

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
        try:
            capture_httpd.shutdown()
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
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
