"""Record a real engine's tool-calling replies for the Ask tool loop test (Betterment Q7).

    uv run python scripts/record_ask_tool_reply.py [--base-url http://192.168.1.43:8080/v1] [--key local]

Sends the Ask's first pass the way the hub's tool loop does (the Ask system
prompt, the ASK palette's tool schemas, one question) to a real
OpenAI-compatible engine, and writes its replies to
``tests/fixtures/ask_tool_turn_lan.json``. Each tool call the engine makes is
answered with a fixed result from the table below (the test's own hub answers
the replayed calls with its real records), until the engine answers in text or
four passes are made. The engine's ``/props`` answer is recorded too: it is
what the Check reads to learn that the server takes tool calls.

No owner material is sent: the question and the results are the fixed text below.
"""
from __future__ import annotations

import argparse
import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "ask_tool_turn_lan.json"

QUESTION = (
    "About: the meeting m-mira-1on1 (1:1 with Mira).\n\n"
    "What do I owe Mira this week? Make the feedback a task for Friday 2026-10-23."
)

RESULTS = {
    "memory.page": {"pages": []},
    "memory.search": {"results": []},
    "meeting.get": {"meeting": {
        "id": "m-mira-1on1", "title": "1:1 with Mira", "started_at": "2026-10-15T10:00:00",
        "summary": "Mira asked for feedback on her cutover design doc by Friday.",
        "action_items": [{"task": "Give Mira feedback on the cutover design doc", "owner": "Me", "due": "2026-10-23"}],
    }},
    "meeting.list": {"meetings": [{"id": "m-mira-1on1", "title": "1:1 with Mira", "started_at": "2026-10-15T10:00:00"}]},
    "door.add_item": {"id": "ai_recorded", "task": "Give Mira feedback on the cutover design doc",
                      "owner": "Me", "due": "2026-10-23", "status": "open"},
}


def _post(url: str, key: str, body: dict) -> dict:
    request = urllib.request.Request(url, data=json.dumps(body).encode(), method="POST", headers={
        "Content-Type": "application/json", "Authorization": f"Bearer {key}"})
    with urllib.request.urlopen(request, timeout=300) as response:  # noqa: S310 - the owner's engine
        return json.loads(response.read())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://192.168.1.43:8080/v1")
    parser.add_argument("--key", default="local")
    args = parser.parse_args()
    base = args.base_url.rstrip("/")

    from holdspeak.mcp.palettes import ASK, resolve_palette
    from holdspeak.services.ask_desk import DESK_PROMPT
    from holdspeak.services.thread_tools import tool_schemas_for

    root = base[: -len("/v1")] if base.endswith("/v1") else base
    with urllib.request.urlopen(f"{root}/props", timeout=10) as response:  # noqa: S310
        props = json.loads(response.read())
    model = str(props.get("model_alias") or "")
    tools = tool_schemas_for(resolve_palette(ASK))
    messages: list[dict] = [{"role": "system", "content": DESK_PROMPT}, {"role": "user", "content": QUESTION}]
    passes = []
    for _ in range(4):
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
    }, indent=2) + "\n")
    print(f"wrote {OUT} ({len(passes)} passes)")


if __name__ == "__main__":
    main()
