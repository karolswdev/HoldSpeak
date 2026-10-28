"""Record a real engine's replies to one phone-call turn (Calls, 2026-10-28).

    uv run python scripts/record_call_turn_reply.py [--base-url http://100.118.33.80:8080/v1] [--key local]

Sends a call's first pass the way the hub's thread loop does for a call (the
CALL prompt, the CALL palette's tool schemas, one spoken request) to a real
OpenAI-compatible engine (default: the home engine over Tailscale), and
writes its replies to ``tests/fixtures/call_turn_home.json``. Each tool call
is answered with a fixed result from the table below (the test's own hub
answers the replayed calls with its real records), until the engine answers
in text or six passes are made.

No owner material is sent: the request and the results are the fixed text below.
"""
from __future__ import annotations

import argparse
import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "call_turn_home.json"

QUESTION = "Add a task for me: nudge Tomás about the runbook by Friday."

RESULTS = {
    "memory.page": {"pages": []},
    "memory.search": {"results": []},
    "door.get": {"items": []},
    "door.add_item": {"id": "ai_recorded", "task": "Nudge Tomás about the runbook", "owner": "Me",
                      "due": "Friday", "status": "open"},
}


def _post(url: str, key: str, body: dict) -> dict:
    request = urllib.request.Request(url, data=json.dumps(body).encode(), method="POST", headers={
        "Content-Type": "application/json", "Authorization": f"Bearer {key}"})
    with urllib.request.urlopen(request, timeout=300) as response:  # noqa: S310 - the owner's engine
        return json.loads(response.read())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://100.118.33.80:8080/v1")
    parser.add_argument("--key", default="local")
    args = parser.parse_args()
    base = args.base_url.rstrip("/")

    from holdspeak.calls.service import CALL_PROMPT
    from holdspeak.mcp.palettes import CALL, resolve_palette
    from holdspeak.services.thread_tools import tool_schemas_for

    root = base[: -len("/v1")] if base.endswith("/v1") else base
    with urllib.request.urlopen(f"{root}/props", timeout=10) as response:  # noqa: S310
        props = json.loads(response.read())
    model = str(props.get("model_alias") or "")
    tools = tool_schemas_for(resolve_palette(CALL))
    messages: list[dict] = [{"role": "system", "content": CALL_PROMPT}, {"role": "user", "content": QUESTION}]
    passes = []
    for _ in range(6):
        reply = _post(f"{base}/chat/completions", args.key, {
            "model": model, "messages": messages, "tools": tools, "max_tokens": 1024, "temperature": 0.2})
        passes.append(reply)
        message = reply["choices"][0]["message"]
        calls = message.get("tool_calls") or []
        if not calls:
            break
        messages.append({"role": "assistant", "content": message.get("content") or "", "tool_calls": calls})
        for call in calls:
            name = call["function"]["name"]
            messages.append({"role": "tool", "tool_call_id": call["id"],
                             "content": json.dumps(RESULTS.get(name, {"ok": True}))})
    OUT.write_text(json.dumps({
        "recorded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "base_url": base,
        "model": model,
        "props_chat_template_caps": props.get("chat_template_caps"),
        "question": QUESTION,
        "tool_results_sent": RESULTS,
        "passes": passes,
    }, indent=2, ensure_ascii=False) + "\n")
    print(f"wrote {OUT} ({len(passes)} passes)")


if __name__ == "__main__":
    main()
