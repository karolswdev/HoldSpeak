"""Record a real engine's reply to Find the tasks on a note (Betterment Q9).

    uv run python scripts/record_note_find_tasks_reply.py [--base-url http://192.168.1.43:8080/v1] [--key local]

Sends the meeting's own analysis prompt (holdspeak/intel/parsing.py
``_json_only_messages`` and ``intel_response_format``, the same messages
``MeetingIntel._analyze_once`` sends) with the Jun note of the asking
design (docs/internal/betterment/asking/DESIGN.md "The note") as the text, to
a real OpenAI-compatible engine, and writes its reply text to
``tests/fixtures/note_find_tasks_reply.json``. tests/unit/test_desk_note_outcomes.py
replays it through the real parser. No owner material is sent: the note is
the fixed text below.
"""
from __future__ import annotations

import argparse
import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from holdspeak.intel.parsing import _json_only_messages, intel_response_format

OUT = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "note_find_tasks_reply.json"

NOTE = ("Jun is nervous about the cutover weekend. Maybe pair him with Mira on call, "
        "and write the on-call handbook first.\nTheo could own the handbook.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://192.168.1.43:8080/v1")
    parser.add_argument("--key", default="local")
    parser.add_argument("--model", default="qwen3.8-27b")
    args = parser.parse_args()
    body = {
        "model": args.model,
        "messages": _json_only_messages(NOTE),
        "temperature": 0.2,
        "max_tokens": 1200,
        "response_format": intel_response_format(),
    }
    request = urllib.request.Request(
        args.base_url.rstrip("/") + "/chat/completions",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {args.key}"},
    )
    with urllib.request.urlopen(request, timeout=300) as response:
        reply = json.loads(response.read())
    text = reply["choices"][0]["message"]["content"]
    OUT.write_text(json.dumps({
        "_source": "A real engine's reply to the meeting analysis prompt over the Jun note, "
                   "recorded by scripts/record_note_find_tasks_reply.py. Never hand-edit it.",
        "recorded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "engine": {"base_url": args.base_url, "model": reply.get("model") or args.model},
        "note": NOTE,
        "reply_text": text,
    }, indent=1, ensure_ascii=False) + "\n")
    print(text)


if __name__ == "__main__":
    main()
