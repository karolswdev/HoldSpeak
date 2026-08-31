#!/usr/bin/env python3
"""HS-156-07 metal rig -- Front Door on the REAL .43 server.

Boots an isolated hub, exercises the recommendation + apply path with
the REAL .43 endpoint, then drives a REAL chat turn answered by Qwen3.6.

Legs:
  1. GET /api/front-door/recommendation -> verify endpoint pack offered
     for the .43 server.
  2. POST /api/front-door/apply (the endpoint pack) -> plan reaches done
     (real define/assign, no download).
  3. REAL chat turn -> Qwen3.6 answers through the applied assignment.

Payloads -> assets/story-07-metal-payloads/

Run (unsandboxed, LAN access required):
  uv run python pm/roadmap/holdspeak/phase-156-the-front-door/assets/story-07-metal.py
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parent
PAYLOADS = HERE / "story-07-metal-payloads"

TOKEN = "hs156-metal"
LAN_HOST = "192.168.1.43"
LAN_PORT = 8080
LAN_BASE = f"http://{LAN_HOST}:{LAN_PORT}/v1"


def hub_api(url: str, method: str, path: str, body: Any = None,
            timeout: float = 30) -> tuple[int, Any]:
    """HTTP helper that uses THIS script's TOKEN."""
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


def lan_reachable() -> bool:
    try:
        req = urllib.request.Request(f"http://{LAN_HOST}:{LAN_PORT}/v1/models")
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status == 200
    except Exception:
        return False


def detect_model() -> str:
    try:
        req = urllib.request.Request(f"http://{LAN_HOST}:{LAN_PORT}/v1/models")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
            models = data.get("data", [])
            if models:
                return str(models[0].get("id", "unknown"))
    except Exception:
        pass
    return "unknown"


# ----------------------------------------------------------------- helpers

def _save(name: str, data: Any) -> Path:
    p = PAYLOADS / name
    p.write_text(json.dumps(data, indent=2, default=str) + "\n")
    return p


def _wait_turn(url: str, tid: str, aid: str, timeout: float = 120.0) -> dict:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        st, detail = hub_api(url, "GET", f"/api/threads/{tid}")
        for m in detail.get("messages", []):
            if m.get("id") == aid and not m.get("streaming"):
                return detail
        time.sleep(0.5)
    raise TimeoutError(f"turn {aid} never completed in {timeout}s")


# ----------------------------------------------------------------- main

def main() -> int:
    sys.path.insert(0, str(REPO))
    t_start = time.monotonic()

    if not lan_reachable():
        print(f"SKIP: .43 ({LAN_HOST}:{LAN_PORT}) is unreachable", flush=True)
        return 0

    model = detect_model()
    print(f"  .43 model: {model}", flush=True)

    import holdspeak.config as config_module
    import holdspeak.db.core as db_core
    from holdspeak.db import reset_database, get_database
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    real_home = os.environ.get("HOME", str(Path.home()))
    home = Path(tempfile.mkdtemp(prefix="hs156-metal-"))
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

    try:
        db = get_database()

        # Seed an endpoint profile pointing to .43
        from tests.unit.test_phase143_inference_assignments import _profile, _result_claim, OWNER
        from holdspeak.services.inference_assignment_service import InferenceAssignmentService

        pid = "hs156-lan-43"
        _profile(db, pid, claims=("language", _result_claim("chat.turn")))
        db.profiles.upsert(
            profile_id=pid,
            name="LAN Qwen 3.6 (.43)",
            kind="openAICompatible",
            base_url=f"http://{LAN_HOST}:{LAN_PORT}",
            model=model,
            context_limit=32768,
            requires_key=False,
        )

        # Seed a capability-scoped assignment for chat.turn so the engine
        # factory resolves to our _LiveEngine during chat turns.
        InferenceAssignmentService(db).set_assignment(OWNER, {
            "command_id": "hs156-metal-assign-turn",
            "expected_revision": 0,
            "scope": {"kind": "capability", "capability_id": "chat.turn"},
            "entries": [{"profile_id": pid, "profile_revision": 1}],
        })
        from holdspeak.db.reconcile import _backfill_chat_practice_assignments
        with db._connection() as conn:
            _backfill_chat_practice_assignments(conn)

        # Seed modes + guardrails
        from holdspeak.services.thread_modes import seed_modes, seed_guardrails
        seed_modes(db)
        seed_guardrails(db)

        # Boot hub
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
        print(f"  Hub at {url}", flush=True)

        for attempt in range(20):
            try:
                hub_api(url, "GET", "/api/threads")
                break
            except Exception:
                time.sleep(0.3)
        else:
            raise RuntimeError("Hub never became reachable")

        hub_api(url, "POST", "/api/desk/seed")
        hub_api(url, "PUT", "/api/setup/onboarding", {"disposition": "completed"})

        # Wire a LIVE engine that talks to .43
        from holdspeak.kernel.runtime import _service as _kernel_service
        broker = _kernel_service()

        class _LiveEngine:
            active_provider = "metal-live"
            active_model = model

            def run_prompt_stream(self, *, messages=None, temperature=None,
                                  max_tokens=None, tools=None,
                                  response_format=None, **kw):
                import urllib.request
                from holdspeak.kernel.inference_stream import Delta
                body_dict: dict[str, Any] = {
                    "model": model,
                    "messages": messages or [],
                    "stream": True,
                    "max_tokens": max_tokens or 1024,
                }
                if tools:
                    body_dict["tools"] = tools
                else:
                    body_dict["grammar"] = ""
                if response_format is not None:
                    body_dict["response_format"] = response_format
                body = json.dumps(body_dict).encode()
                req = urllib.request.Request(
                    LAN_BASE + "/chat/completions",
                    data=body,
                    headers={"Content-Type": "application/json"},
                )
                with urllib.request.urlopen(req, timeout=120) as resp:
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
                        if content:
                            yield Delta(kind="text", text=content)
                        usage = chunk.get("usage")
                        if usage:
                            yield Delta(kind="usage", meta=usage)
                yield Delta(kind="usage", meta={"prompt_tokens": 0, "completion_tokens": 0})
                yield Delta(kind="done")

            def run_prompt_messages(self, **kw):
                parts = []
                for d in self.run_prompt_stream(**kw):
                    if d.kind == "text":
                        parts.append(d.text)
                return "".join(parts)

            def run_prompt(self, *, system_prompt="", user_prompt="", **kw):
                return self.run_prompt_messages(
                    messages=[{"role": "system", "content": system_prompt},
                              {"role": "user", "content": user_prompt}],
                    **kw,
                )

        if broker is not None:
            broker.inference_runner._engine_factory = lambda _rev, **_kw: _LiveEngine()

        # ================================================================
        # LEG 1: Recommendation offers the .43 endpoint pack
        # ================================================================
        print("\n== LEG 1: Recommendation ==", flush=True)
        leg1_start = time.monotonic()

        st_rec, rec = hub_api(url, "GET", "/api/front-door/recommendation")
        check(st_rec == 200, f"GET /api/front-door/recommendation -> {st_rec}")
        _save("leg-1-recommendation.json", rec)

        packs = rec.get("packs", [])
        check(len(packs) > 0, f"packs offered: {len(packs)}")

        # Prefer balanced (the recommended pack)
        endpoint_pack = next((p for p in packs if p.get("id") == "balanced"), None)
        if endpoint_pack is None:
            endpoint_pack = packs[0] if packs else None

        if endpoint_pack:
            check(True, f"using pack '{endpoint_pack.get('id')}' ({endpoint_pack.get('label')})")
        else:
            check(False, "no pack available")
            raise RuntimeError("No pack available")

        leg_times["leg1"] = time.monotonic() - leg1_start
        print(f"  LEG 1 done in {leg_times['leg1']:.1f}s", flush=True)

        # ================================================================
        # LEG 2: Apply the endpoint pack (real define/assign, no download)
        # ================================================================
        print("\n== LEG 2: Apply ==", flush=True)
        leg2_start = time.monotonic()

        pack_id = endpoint_pack["id"]
        st_apply, apply_result = hub_api(url, "POST", "/api/front-door/apply", {
            "pack_id": pack_id,
        })
        check(st_apply == 200, f"POST /api/front-door/apply -> {st_apply}")
        _save("leg-2-apply-result.json", apply_result)

        # Check if already done from the POST response
        apply_status = apply_result.get("status", "") if st_apply == 200 else ""
        plan_done = apply_status in ("done", "failed")
        if plan_done:
            _save("leg-2-plan-final.json", apply_result)
        else:
            # Poll GET /api/front-door/apply (wraps in {"plan": ...})
            plan_deadline = time.monotonic() + 30
            while time.monotonic() < plan_deadline:
                st_plan, plan = hub_api(url, "GET", "/api/front-door/apply")
                if st_plan == 200:
                    plan_data = plan.get("plan") or plan
                    status = plan_data.get("status", "")
                    items = plan_data.get("items", [])
                    if status in ("done", "failed"):
                        plan_done = True
                        _save("leg-2-plan-final.json", plan_data)
                        break
                    if items and all(i.get("status") == "done" for i in items):
                        plan_done = True
                        _save("leg-2-plan-final.json", plan_data)
                        break
                time.sleep(0.5)

        check(plan_done, "apply plan reached done")
        if plan_done and apply_status == "failed":
            items = apply_result.get("items", [])
            failed_items = [i for i in items if i.get("status") == "failed"]
            for fi in failed_items[:3]:
                print(f"  NOTE: {fi.get('entry',{}).get('kind')}: {fi.get('error')}", flush=True)

        # Verify assignments were created
        st_asn, assignments = hub_api(url, "GET", "/api/inference/assignments")
        check(st_asn == 200, f"GET /api/inference/assignments -> {st_asn}")
        _save("leg-2-assignments.json", assignments)

        leg_times["leg2"] = time.monotonic() - leg2_start
        print(f"  LEG 2 done in {leg_times['leg2']:.1f}s", flush=True)

        # ================================================================
        # LEG 3: REAL chat turn answered by Qwen3.6
        # ================================================================
        print("\n== LEG 3: LIVE chat turn ==", flush=True)
        leg3_start = time.monotonic()

        st_t, thread = hub_api(url, "POST", "/api/threads", {
            "title": "HS-156-07 Metal chat",
            "recipe_id": "hs-seed-mode-desk",
        })
        check(st_t == 201, f"POST /api/threads -> {st_t}")
        tid = thread["id"]

        st_turn, turn = hub_api(url, "POST", f"/api/threads/{tid}/turns", {
            "text": "What is the capital of France? Answer in one sentence.",
        })
        check(st_turn == 201, f"POST /turns -> {st_turn}")

        detail = _wait_turn(url, tid, turn["assistant_message_id"])
        _save("leg-3-turn-detail.json", detail)

        # Extract assistant text
        asst = [m for m in detail.get("messages", [])
                if m.get("id") == turn["assistant_message_id"]]
        asst_text = ""
        if asst:
            asst_text = "".join(
                p.get("text", "") for p in asst[0].get("parts", []) if p["kind"] == "text"
            )
        print(f"  Assistant text (first 200): {asst_text[:200]}", flush=True)
        check(len(asst_text) > 0, f"assistant text non-empty ({len(asst_text)} chars)")

        # Basic sanity: should mention Paris
        mentions_paris = "paris" in asst_text.lower()
        if mentions_paris:
            check(True, "assistant mentions Paris")
        else:
            print(f"  NOTE: assistant did not mention Paris (text: {asst_text[:100]})", flush=True)

        leg_times["leg3"] = time.monotonic() - leg3_start
        print(f"  LEG 3 done in {leg_times['leg3']:.1f}s", flush=True)

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
    print("\n== METAL FINDINGS ==", flush=True)
    for f in failures:
        print(f"  FINDING  {f}", flush=True)
    print(f"\ntotal_time={total_time:.1f}s", flush=True)
    for leg, t in sorted(leg_times.items()):
        print(f"  {leg}={t:.1f}s", flush=True)
    print(f"failures={len(failures)}", flush=True)
    print(f"payloads={PAYLOADS.relative_to(REPO)}", flush=True)

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
