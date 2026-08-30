"""HS-152-03 hub leg -- the People fence through the REAL hub, over HTTP.

Boots the real hub in an isolated HOME (never the owner's DB), seeds a local
v2 profile and a legacy cloud profile (a public OpenAI-compatible base URL,
exactly how a hosted model routes), and drives the thread routes the browser
uses: POST /api/threads, POST /turns, PATCH profile_override, GET detail.

What this proves beyond tests/unit/test_thread_people_fence.py: the route
factory (`holdspeak/web/routes/_thread_factory.py`) wires the in-process
MCP dispatch + the desk's control_mode into the ThreadService the hub
builds -- i.e. the Hands are live on the hub, not only in a unit rig.

Modes:
  DRY  (default)          the engine is a fake injected via the kernel
                          runner's _engine_factory; it asks for
                          people.readiness on pass 1 and answers on pass 2,
                          and records every messages list it is handed.
  LIVE (HS152_LIVE=1)     the local leg runs against .43 llama.cpp through a
                          legacy LAN profile row; Qwen3.6 emits native tool_calls,
                          no ToolQualification eval needed (probed 2026-08-30).

Run:
  uv run python pm/roadmap/holdspeak/phase-152-the-hands/assets/story-03-hub-leg.py
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parent
PAYLOADS = HERE / ("story-03-hub-payloads-live" if os.environ.get("HS152_LIVE") == "1" else "story-03-hub-payloads")
LIVE = os.environ.get("HS152_LIVE") == "1"

# Reuse the 151 metal helpers (capture server, hub_api, LAN seeding) verbatim.
_spec = importlib.util.spec_from_file_location(
    "hs151_metal", REPO / "pm/roadmap/holdspeak/phase-151-the-desk-chat/assets/story-08-metal.py",
)
hs151 = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(hs151)
hub_api = hs151.hub_api
TOKEN = hs151.TOKEN

PEOPLE_TOOL = "people.readiness"


class _FenceEngine:
    """DRY engine: tool call on a transcript without a tool message, text after."""

    active_provider = "fence-dry"
    active_model = "fence-model"

    def __init__(self) -> None:
        self.calls: list[list[dict[str, Any]]] = []
        self.tools_seen: list[int] = []

    def run_prompt_stream(self, *, messages=None, temperature=None, max_tokens=None, tools=None, **kw):
        from holdspeak.kernel.inference_stream import Delta

        msgs = [dict(m) for m in (messages or [])]
        self.calls.append(msgs)
        self.tools_seen.append(len(tools or []))
        if any(m.get("role") == "tool" for m in msgs):
            for w in ("Store", "checked."):
                yield Delta(kind="text", text=w + " ")
        else:
            yield Delta(kind="tool_calls", meta={"tool_calls": [
                {"id": "call_hub_1", "name": PEOPLE_TOOL, "arguments": "{}"},
            ]})
        yield Delta(kind="usage", meta={"prompt_tokens": 5, "completion_tokens": 2})
        yield Delta(kind="done")

    def run_prompt_messages(self, *, messages=None, **kw):
        return "Store checked. "

    def run_prompt(self, *, system_prompt="", user_prompt="", **kw):
        return "Store checked. "


def _wait_turn(url: str, tid: str, aid: str, timeout: float = 60.0) -> dict[str, Any]:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        _, detail = hub_api(url, "GET", f"/api/threads/{tid}")
        for m in detail.get("messages", []):
            if m.get("id") == aid and not m.get("streaming"):
                return detail
        time.sleep(0.2)
    raise TimeoutError("turn never completed")


def _joined(messages: list[dict[str, Any]]) -> str:
    return "\n---\n".join(str(m.get("content", "")) for m in messages)


def main() -> int:
    sys.path.insert(0, str(REPO))
    import holdspeak.config as config_module
    import holdspeak.db.core as db_core
    from holdspeak.db import reset_database, get_database
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    home = Path(tempfile.mkdtemp(prefix="hs152-hub-"))
    os.environ["HOME"] = str(home)
    config_module.CONFIG_FILE = home / ".holdspeak" / "config.json"
    db_core.DEFAULT_DB_PATH = home / "holdspeak.db"
    reset_database()
    PAYLOADS.mkdir(parents=True, exist_ok=True)

    server = MeetingWebServer(
        WebRuntimeCallbacks(on_bookmark=lambda *_: None, on_stop=lambda: None, get_state=lambda: {}),
        auth_token=TOKEN,
    )
    url = server.start()
    failures: list[str] = []

    def check(ok: bool, label: str) -> None:
        print(f"  {'PASS' if ok else 'FAIL'} {label}", flush=True)
        if not ok:
            failures.append(label)

    try:
        db = get_database()
        from tests.unit.test_phase143_inference_assignments import _profile, _result_claim, OWNER
        from holdspeak.services.inference_assignment_service import InferenceAssignmentService
        from holdspeak.services.thread_service import _PEOPLE_REDACTION

        # ── local leg profile ──
        if LIVE:
            # The production LAN path: a legacy openAI-compatible profile row
            # (private endpoint -> boundary private_network); the hub's own
            # engine factory builds the engine from the admitted revision.
            model = hs151.detect_model()
            db.profiles.upsert(
                profile_id="hs152-lan", name="HS-152 LAN (.43)", kind="openAICompatible",
                base_url=hs151.LAN_BASE, model=model, context_limit=32768, requires_key=False,
            )
            InferenceAssignmentService(db).set_assignment(OWNER, {
                "command_id": "hs152-assign-lan",
                "expected_revision": 0,
                "scope": {"kind": "capability", "capability_id": "chat.turn"},
                "entries": [{"profile_id": "legacy-hs152-lan", "profile_revision": 1}],
            })
            engine = None
            print(f"  LIVE .43 model: {model}", flush=True)
        else:
            _profile(db, "hs152-local", claims=("language", _result_claim("chat.turn")))
            InferenceAssignmentService(db).set_assignment(OWNER, {
                "command_id": "hs152-assign",
                "expected_revision": 0,
                "scope": {"kind": "capability", "capability_id": "chat.turn"},
                "entries": [{"profile_id": "hs152-local", "profile_revision": 1}],
            })
            from holdspeak.kernel.runtime import _service as _kernel_service
            engine = _FenceEngine()
            _kernel_service().inference_runner._engine_factory = lambda _rev, **_kw: engine

        # ── cloud profile: a legacy hosted row with a public base URL ──
        db.profiles.upsert(
            profile_id="hs152-cloud", name="HS-152 cloud (capture)", kind="openAICompatible",
            base_url="https://cloud.example.test/v1", model="capture-model",
            context_limit=32768, requires_key=False,
        )

        # ── Leg A: local turn calls a People tool through the hub ──
        print("\n== LEG A: local turn, people.* through the hub route ==", flush=True)
        st, thread = hub_api(url, "POST", "/api/threads", {"title": "HS-152-03 fence"})
        check(st == 201, f"POST /api/threads -> {st}")
        tid = thread["id"]
        st, turn = hub_api(url, "POST", f"/api/threads/{tid}/turns", {"text": "Is the People store ready?"})
        check(st == 201, f"POST /turns -> {st}")
        detail = _wait_turn(url, tid, turn["assistant_message_id"])
        (PAYLOADS / "leg-a-thread.json").write_text(json.dumps(detail, indent=2) + "\n")

        msgs = detail["messages"]
        tool_msgs = [m for m in msgs if m.get("role") == "tool"]
        asst = [m for m in msgs if m.get("id") == turn["assistant_message_id"]][0]
        tool_call_parts = [p for p in asst["parts"] if p["kind"] == "tool_call"]
        check(len(tool_call_parts) == 1, "assistant row carries one tool_call part (the hub wired dispatch)")
        check(len(tool_msgs) == 1, "one tool-role message persisted")
        people_part = tool_msgs[0]["parts"][0] if tool_msgs and tool_msgs[0]["parts"] else {}
        check(bool(people_part.get("sensitive")), "people.* result part is sensitive=1")
        people_text = str(people_part.get("text", ""))
        check(asst.get("egress_scope") in ("local", "private_network"), f"local egress ({asst.get('egress_scope')})")
        if engine is not None:
            check(engine.tools_seen[0] > 0, f"tool palette reached the engine ({engine.tools_seen[0]} tools)")
            check(len(engine.calls) == 2, f"two passes ({len(engine.calls)})")
            check(people_text in _joined(engine.calls[1]), "pass 2 carried People bytes verbatim on local egress")

        # ── Leg B: profile_override -> cloud; the fence holds ──
        print("\n== LEG B: profile_override -> cloud; later turn withholds ==", flush=True)
        st, _ = hub_api(url, "PATCH", f"/api/threads/{tid}", {"profile_override": "hs152-cloud"})
        check(st < 300, f"PATCH profile_override -> {st}")
        if engine is None:
            print("  LIVE: cloud.example.test is unroutable; the admitted egress is the proof", flush=True)
        st, turn2 = hub_api(url, "POST", f"/api/threads/{tid}/turns", {"text": "And now on the cloud?"})
        check(st == 201, f"POST /turns (cloud) -> {st}")
        detail2 = _wait_turn(url, tid, turn2["assistant_message_id"])
        (PAYLOADS / "leg-b-thread.json").write_text(json.dumps(detail2, indent=2) + "\n")
        asst2 = [m for m in detail2["messages"] if m.get("id") == turn2["assistant_message_id"]][0]
        check(asst2.get("egress_scope") == "cloud", f"override honored at admission: egress={asst2.get('egress_scope')}")
        if engine is not None:
            cloud_msgs = engine.calls[-1]
            (PAYLOADS / "leg-b-cloud-engine-messages.json").write_text(json.dumps(cloud_msgs, indent=2) + "\n")
            joined = _joined(cloud_msgs)
            check(_PEOPLE_REDACTION in joined, "cloud payload carries [people content withheld]")
            check(people_text not in joined, "cloud payload carries NO People bytes")
            check("_sensitive_texts" not in json.dumps(cloud_msgs), "no sentinel key leaks")

        # ── Leg C (LIVE only): a door.* EFFECT with a receipt + a control turn ──
        if engine is None:
            print("\n== LEG C: door.add_item effect on .43 (receipt) + control (no tool) ==", flush=True)
            st, thread3 = hub_api(url, "POST", "/api/threads", {"title": "HS-152-06 door effect"})
            tid3 = thread3["id"]
            st, turn3 = hub_api(url, "POST", f"/api/threads/{tid3}/turns", {
                "text": "Add an action item to my Door: 'Ship the Hands demo' due 2026-09-04. Use the door tool.",
            })
            check(st == 201, f"POST /turns (effect) -> {st}")
            detail3 = _wait_turn(url, tid3, turn3["assistant_message_id"], timeout=120)
            (PAYLOADS / "leg-c-thread.json").write_text(json.dumps(detail3, indent=2) + "\n")
            asst3 = [m for m in detail3["messages"] if m.get("id") == turn3["assistant_message_id"]][0]
            calls3 = [p for p in asst3["parts"] if p["kind"] == "tool_call"]
            names3 = [str((p.get("meta_json") or {}).get("name", "")) for p in calls3]
            check("door.add_item" in names3, f"the model reached for door.add_item ({names3})")
            tool3 = [m for m in detail3["messages"] if m.get("role") == "tool"]
            metas3 = [(m["parts"][0].get("meta_json") or {}) for m in tool3 if m.get("parts")]
            ok3 = [mm for mm in metas3 if mm.get("receipt_id") and mm.get("kind") not in (
                "tool_execution_failed", "tool_denied", "tool_timeout", "tool_unknown")]
            check(bool(ok3), f"the effect ran with a receipt ({[mm.get('receipt_id') for mm in metas3]})")
            with db._connection() as conn:
                row = conn.execute(
                    "SELECT id, source_type, source_ref FROM action_items WHERE source_type='thread' ORDER BY rowid DESC LIMIT 1",
                ).fetchone()
            check(row is not None, f"an action_items row with source_type='thread' exists ({dict(row) if row else None})")

            st, thread4 = hub_api(url, "POST", "/api/threads", {"title": "HS-152-06 control"})
            st, turn4 = hub_api(url, "POST", f"/api/threads/{thread4['id']}/turns", {"text": "Reply with exactly: hello desk"})
            detail4 = _wait_turn(url, thread4["id"], turn4["assistant_message_id"], timeout=120)
            asst4 = [m for m in detail4["messages"] if m.get("id") == turn4["assistant_message_id"]][0]
            check(not [p for p in asst4["parts"] if p["kind"] == "tool_call"], "control turn: no tool call")
            check(any(p["kind"] == "text" and p.get("text") for p in asst4["parts"]), "control turn: text answer")
    finally:
        server.stop()

    print("\n== FINDINGS ==", flush=True)
    for f in failures:
        print(f"FINDING  {f}", flush=True)
    print(f"mode={'LIVE' if LIVE else 'DRY'} payloads={PAYLOADS.relative_to(REPO)} failures={len(failures)}", flush=True)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
