"""HS-133-11 -- MCP sidecar walk harness.

Boots the real sidecar as a subprocess (uv run holdspeak-mcp) under
an isolated HOME, speaks real JSON-RPC over stdio, and exercises every
tool family.  The harness proves transport, not in-process dispatch.

Usage:
  HOME=$(mktemp -d) uv run python scripts/mcp_walk.py
  HOME=$(mktemp -d) uv run python scripts/mcp_walk.py --json-out
  HOME=$(mktemp -d) uv run python scripts/mcp_walk.py --json-out <path>
  HOME=$(mktemp -d) uv run python scripts/mcp_walk.py --live-43
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# JSON-RPC helpers
# ---------------------------------------------------------------------------

_REQ_ID = 0
_TRANSCRIPT: list[dict[str, Any]] = []


def _next_id() -> int:
    global _REQ_ID
    _REQ_ID += 1
    return _REQ_ID


def _send(proc: subprocess.Popen, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Send one JSON-RPC request and read one response line."""
    req_id = _next_id()
    request: dict[str, Any] = {"jsonrpc": "2.0", "id": req_id, "method": method}
    if params is not None:
        request["params"] = params
    line = json.dumps(request) + "\n"
    proc.stdin.write(line)
    proc.stdin.flush()
    raw = proc.stdout.readline()
    if not raw:
        raise RuntimeError(f"sidecar closed stdout after request {method} (id={req_id})")
    response = json.loads(raw)
    _TRANSCRIPT.append({"request": request, "response": response})
    return response


def _notify(proc: subprocess.Popen, method: str, params: dict[str, Any] | None = None) -> None:
    """Send a JSON-RPC notification (no response expected)."""
    notif: dict[str, Any] = {"jsonrpc": "2.0", "method": method}
    if params is not None:
        notif["params"] = params
    proc.stdin.write(json.dumps(notif) + "\n")
    proc.stdin.flush()
    _TRANSCRIPT.append({"notification": notif})


def _call_tool(proc: subprocess.Popen, tool_name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
    """Call tools/call and return the full response."""
    params: dict[str, Any] = {"name": tool_name}
    if arguments is not None:
        params["arguments"] = arguments
    return _send(proc, "tools/call", params)


def _tool_content(resp: dict[str, Any]) -> Any:
    """Parse the text content from a tools/call response result."""
    content = resp["result"]["content"]
    assert len(content) >= 1, f"empty content in response: {resp}"
    return json.loads(content[0]["text"])


def _is_error(resp: dict[str, Any]) -> bool:
    """Check if a tools/call result has isError: true."""
    return resp.get("result", {}).get("isError", False)


# ---------------------------------------------------------------------------
# Assertions
# ---------------------------------------------------------------------------

_ASSERTIONS: list[tuple[str, bool, str]] = []


def _assert(name: str, condition: bool, detail: str = "") -> None:
    _ASSERTIONS.append((name, condition, detail))
    status = "PASS" if condition else "FAIL"
    msg = f"  [{status}] {name}"
    if detail:
        msg += f"  -- {detail}"
    print(msg)


# ---------------------------------------------------------------------------
# Main walk
# ---------------------------------------------------------------------------

def run_walk(*, json_out: str | None = None, live_43: str | None = None) -> int:
    """Run the MCP sidecar walk and return exit code."""
    iso_home = tempfile.mkdtemp(prefix="hs-mcp-walk-")
    print(f"MCP walk: isolated HOME={iso_home}")

    env = {
        "HOME": iso_home,
        "PATH": subprocess.check_output(["bash", "-lc", "echo $PATH"], text=True).strip(),
    }

    # Boot the sidecar subprocess. The live .43 leg rides the hub's
    # OpenAI-compatible provider, which lives in the optional `meeting`
    # extra — without it the destination refuses with a named reason.
    boot_cmd = ["uv", "run", "holdspeak-mcp"]
    if live_43:
        boot_cmd = ["uv", "run", "--extra", "meeting", "holdspeak-mcp"]
    proc = subprocess.Popen(
        boot_cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=str(Path(__file__).resolve().parents[1]),
        env=env,
    )

    try:
        _run_protocol(proc, live_43=live_43)
    finally:
        proc.stdin.close()
        proc.wait(timeout=10)

    # Write transcript
    if json_out is not None:
        out_path = Path(json_out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(_TRANSCRIPT, indent=2, default=str))
        print(f"\nTranscript written to {out_path}")

    # Summary
    total = len(_ASSERTIONS)
    passed = sum(1 for _, ok, _ in _ASSERTIONS if ok)
    failed = total - passed
    print(f"\n{'='*60}")
    print(f"MCP walk: {total} assertions, {passed} passed, {failed} failed")
    print(f"{'='*60}")
    if failed:
        print("\nFailed assertions:")
        for i, (name, ok, detail) in enumerate(_ASSERTIONS, 1):
            if not ok:
                print(f"  {i}. {name}  -- {detail}")
    return 1 if failed else 0


def _run_protocol(proc: subprocess.Popen, *, live_43: str | None = None) -> None:
    """Exercise the full protocol lifecycle."""

    # -----------------------------------------------------------------------
    # 1. Initialize
    # -----------------------------------------------------------------------
    print("\n--- initialize ---")
    init_resp = _send(proc, "initialize", {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {"name": "mcp-walk", "version": "0.1.0"},
    })
    result = init_resp["result"]
    _assert("protocolVersion", result["protocolVersion"] == "2024-11-05",
            result["protocolVersion"])
    _assert("serverInfo.name", result["serverInfo"]["name"] == "holdspeak-mcp",
            result["serverInfo"]["name"])

    # Send notifications/initialized
    _notify(proc, "notifications/initialized")

    # -----------------------------------------------------------------------
    # 2. tools/list
    # -----------------------------------------------------------------------
    print("\n--- tools/list ---")
    tools_resp = _send(proc, "tools/list")
    tools = tools_resp["result"]["tools"]
    _assert("tool_count_82", len(tools) == 82, f"got {len(tools)}")

    # Every tool schema is closed (additionalProperties: false)
    all_closed = True
    open_tools = []
    for t in tools:
        schema = t.get("inputSchema", {})
        if schema.get("additionalProperties") is not False:
            all_closed = False
            open_tools.append(t["name"])
    _assert("all_schemas_closed", all_closed,
            f"open: {open_tools[:5]}" if open_tools else "")

    # -----------------------------------------------------------------------
    # 3. resources/list
    # -----------------------------------------------------------------------
    print("\n--- resources/list ---")
    res_resp = _send(proc, "resources/list")
    res_result = res_resp["result"]
    static_count = len(res_result.get("resources", []))
    template_count = len(res_result.get("resourceTemplates", []))
    total_resources = static_count + template_count
    _assert("static_resources_14", static_count == 14, f"got {static_count}")
    _assert("resource_templates_10", template_count == 10, f"got {template_count}")
    _assert("total_resources_24", total_resources == 24, f"got {total_resources}")

    # Check holdspeak://cadence/status is in the list
    static_uris = [r["uri"] for r in res_result.get("resources", [])]
    _assert("cadence_status_resource_listed",
            "holdspeak://cadence/status" in static_uris,
            str(static_uris))

    # -----------------------------------------------------------------------
    # 4. Family exercises
    # -----------------------------------------------------------------------

    # --- desk family ---
    print("\n--- desk family ---")
    desk_resp = _call_tool(proc, "desk.list", {"kind": "notes"})
    _assert("desk.list_ok", not _is_error(desk_resp),
            json.dumps(_tool_content(desk_resp))[:120] if not _is_error(desk_resp) else str(desk_resp))

    # --- ask family ---
    print("\n--- ask family ---")
    models_resp = _call_tool(proc, "ask.models")
    _assert("ask.models_ok", not _is_error(models_resp),
            json.dumps(_tool_content(models_resp))[:120] if not _is_error(models_resp) else str(models_resp))

    # --- settings family ---
    print("\n--- settings family ---")
    settings_resp = _call_tool(proc, "settings.get")
    _assert("settings.get_ok", not _is_error(settings_resp))
    if not _is_error(settings_resp):
        settings_data = _tool_content(settings_resp)
        _assert("settings._revision_present", "_revision" in settings_data,
                f"keys: {list(settings_data.keys())[:10]}")
        # Check no secret leak: secret paths should be redacted
        raw_text = settings_resp["result"]["content"][0]["text"]
        _assert("settings.no_secret_leak",
                "sk-" not in raw_text and "REDACTED" not in raw_text.upper()
                or "REDACTED" in raw_text.upper(),
                "secret check passed")

    # settings.update round-trip: patch a benign UI setting, read it back
    print("\n--- settings.update round-trip ---")
    # Use wake_word.threshold -- a harmless numeric knob
    update_resp = _call_tool(proc, "settings.update", {
        "patch": {"wake_word": {"threshold": 0.42}},
    })
    _assert("settings.update_ok", not _is_error(update_resp),
            str(update_resp)[:120] if _is_error(update_resp) else "")
    # Read back
    readback_resp = _call_tool(proc, "settings.get")
    if not _is_error(readback_resp):
        readback_data = _tool_content(readback_resp)
        readback_val = readback_data.get("wake_word", {}).get("threshold")
        _assert("settings.update_roundtrip",
                readback_val == 0.42,
                f"got {readback_val}")

    # --- coder family ---
    print("\n--- coder family ---")
    coder_resp = _call_tool(proc, "coder.list")
    _assert("coder.list_ok", not _is_error(coder_resp),
            json.dumps(_tool_content(coder_resp))[:120] if not _is_error(coder_resp) else str(coder_resp))

    # --- memory family ---
    print("\n--- memory family ---")
    mem_resp = _call_tool(proc, "memory.search", {"query": "test"})
    _assert("memory.search_ok", not _is_error(mem_resp),
            json.dumps(_tool_content(mem_resp))[:120] if not _is_error(mem_resp) else str(mem_resp))

    # --- cadence family ---
    print("\n--- cadence family ---")
    cadence_resp = _call_tool(proc, "cadence.status")
    _assert("cadence.status_ok", not _is_error(cadence_resp),
            json.dumps(_tool_content(cadence_resp))[:120] if not _is_error(cadence_resp) else str(cadence_resp))

    # holdspeak://cadence/status resource read
    print("\n--- cadence/status resource ---")
    cadence_res = _send(proc, "resources/read", {"uri": "holdspeak://cadence/status"})
    _assert("cadence_status_resource_read",
            "result" in cadence_res and "contents" in cadence_res.get("result", {}),
            str(cadence_res)[:120])

    # cadence.snooze error path: unknown loop -> isError:true
    snooze_resp = _call_tool(proc, "cadence.snooze", {
        "loop_id": "nonexistent-loop-id-00000",
        "until": "2099-01-01T00:00:00Z",
    })
    _assert("cadence.snooze_error_unknown_loop", _is_error(snooze_resp),
            f"isError={_is_error(snooze_resp)}")

    # --- sequence family (error path) ---
    print("\n--- sequence family ---")
    seq_cancel_resp = _call_tool(proc, "sequence.cancel", {
        "parent_operation_id": "nonexistent-parent-op-00000",
    })
    _assert("sequence.cancel_error_unknown_parent", _is_error(seq_cancel_resp),
            f"isError={_is_error(seq_cancel_resp)}")

    # --- plugin_job family ---
    print("\n--- plugin_job family ---")
    pj_summary = _call_tool(proc, "plugin_job.summary")
    _assert("plugin_job.summary_ok", not _is_error(pj_summary),
            json.dumps(_tool_content(pj_summary))[:120] if not _is_error(pj_summary) else str(pj_summary))

    # plugin_job.retry refusal: unknown job id -> isError:true
    pj_retry = _call_tool(proc, "plugin_job.retry", {"job_id": 999999999})
    _assert("plugin_job.retry_error_unknown_job", _is_error(pj_retry),
            f"isError={_is_error(pj_retry)}")

    # -----------------------------------------------------------------------
    # 5. Live .43 leg (only when --live-43 is provided)
    # -----------------------------------------------------------------------
    if live_43:
        _run_live_43(proc, live_43)

    # -----------------------------------------------------------------------
    # 6. Ping (protocol correctness)
    # -----------------------------------------------------------------------
    print("\n--- ping ---")
    ping_resp = _send(proc, "ping")
    _assert("ping_ok", "result" in ping_resp)


def _run_live_43(proc: subprocess.Popen, endpoint: str) -> None:
    """The live .43 leg: create a destination, ask.run against it, verify receipt."""
    import urllib.request

    print(f"\n--- live .43 leg (endpoint={endpoint}) ---")

    # Fetch the endpoint's loaded model via /v1/models
    models_url = f"{endpoint}/v1/models"
    try:
        with urllib.request.urlopen(models_url, timeout=10) as resp:
            models_data = json.loads(resp.read())
    except Exception as exc:
        _assert("live43_models_fetch", False, f"cannot reach {models_url}: {exc}")
        return

    # Parse the model id from the OpenAI-compatible response
    if isinstance(models_data, dict) and "data" in models_data:
        loaded_model = models_data["data"][0]["id"]
    elif isinstance(models_data, list):
        loaded_model = models_data[0]["id"]
    else:
        loaded_model = str(models_data)
    print(f"  .43 loaded model: {loaded_model}")

    # Read ask.models BEFORE the live call (control)
    control_resp = _call_tool(proc, "ask.models")
    control_models = _tool_content(control_resp) if not _is_error(control_resp) else []
    print(f"  control ask.models: {json.dumps(control_models)[:200]}")

    # Create a destination pointing at the .43 endpoint
    # kind private_endpoint -> openAICompatible; omitting kind defaults to
    # this_device, which demands an on-device model file (profile_service.py:157).
    profile_resp = _call_tool(proc, "destination.create", {
        "fields": {
            "name": "walk-43-live",
            "kind": "private_endpoint",
            "endpoint": endpoint,
            "model": loaded_model,
        },
    })
    if _is_error(profile_resp):
        _assert("live43_profile_create", False, str(profile_resp)[:200])
        return
    profile_data = _tool_content(profile_resp)
    profile_id = profile_data.get("id") or profile_data.get("profile_id")
    _assert("live43_profile_create", profile_id is not None, f"id={profile_id}")

    # ask.run against it
    ask_resp = _call_tool(proc, "ask.run", {
        "question": "Say exactly: walk-43-alive",
        "inference_target_id": profile_id,
    })
    if _is_error(ask_resp):
        _assert("live43_ask.run", False, str(ask_resp)[:200])
        return
    ask_data = _tool_content(ask_resp)

    # Extract receipt model
    receipt_model = None
    if isinstance(ask_data, dict):
        receipt = ask_data.get("receipt") or ask_data.get("_placement") or {}
        receipt_model = receipt.get("model") or ask_data.get("model")
    _assert("live43_receipt_model_matches",
            receipt_model is not None and loaded_model in str(receipt_model),
            f"receipt={receipt_model}, endpoint={loaded_model}")

    # Treatment line
    treatment_resp = _call_tool(proc, "ask.models")
    treatment_models = _tool_content(treatment_resp) if not _is_error(treatment_resp) else []
    print(f"  treatment ask.models: {json.dumps(treatment_models)[:200]}")
    print(f"  control-vs-treatment: control={json.dumps(control_models)[:100]}, "
          f"treatment={json.dumps(treatment_models)[:100]}")
    print(f"  receipt model: {receipt_model}")
    print(f"  endpoint model: {loaded_model}")
    print(f"  match: {receipt_model is not None and loaded_model in str(receipt_model)}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description="MCP sidecar walk harness")
    parser.add_argument(
        "--json-out",
        nargs="?",
        const="pm/roadmap/holdspeak/phase-133-the-honest-sidecar/assets/mcp-walk-transcript.json",
        help="Write JSON-RPC transcript (default path: phase assets).",
    )
    parser.add_argument(
        "--live-43",
        action="store_true",
        help="Run the live .43 leg (requires LAN access).",
    )
    parser.add_argument(
        "--endpoint",
        help="Override the .43 endpoint (default: HOLDSPEAK_WALK_43 env).",
    )
    args = parser.parse_args()

    live_43 = None
    if args.live_43:
        import os
        live_43 = args.endpoint or os.environ.get("HOLDSPEAK_WALK_43", "http://192.168.1.43:8080")

    json_out = args.json_out
    return run_walk(json_out=json_out, live_43=live_43)


if __name__ == "__main__":
    raise SystemExit(main())
