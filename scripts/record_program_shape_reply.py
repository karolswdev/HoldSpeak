"""Record a real engine's replies to Program shaping (PG-LANG LANG3).

    uv run python scripts/record_program_shape_reply.py [--base-url http://karol:8080/v1] [--key local] [--only KEY ...]

Builds the seed Program of ``tests/integration/program_shape_seed.py`` on a
scratch rig, builds the ``program.shape@1`` prompt the hub sends
(``holdspeak/services/program_shaper.py``: the grammar card, the rules, the
frozen list, the vocabulary, the text with its lamps stripped, the
grounding, the sentence) for each recorded sentence, sends it to a real
OpenAI-compatible engine, and writes the reply texts to
``tests/fixtures/program_shape_reply.json``. The tests replay them through
the runner. No owner material is sent: the Program is the fixed seed.
"""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from holdspeak.services import program_shaper  # noqa: E402
from holdspeak.services.program_text import print_program  # noqa: E402
from tests.integration.program_rig import Rig  # noqa: E402
from tests.integration.program_shape_seed import SENTENCES, program, seed  # noqa: E402

OUT = REPO / "tests" / "fixtures" / "program_shape_reply.json"


def _send(args: argparse.Namespace, text: str, system: str, user: str) -> dict:
    body = {"model": args.model, "temperature": program_shaper.TEMPERATURE,
            "max_tokens": program_shaper.token_cap(text),
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "response_format": program_shaper.response_format()}
    request = urllib.request.Request(
        args.base_url.rstrip("/") + "/chat/completions", data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {args.key}"})
    started = time.monotonic()
    with urllib.request.urlopen(request, timeout=300) as response:
        reply = json.loads(response.read())
    return {"reply_text": reply["choices"][0]["message"]["content"], "seconds": round(time.monotonic() - started, 2),
            "usage": reply.get("usage"), "model": reply.get("model") or args.model}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://karol:8080/v1")
    parser.add_argument("--key", default="local")
    parser.add_argument("--model", default="qwen3.8-27b")
    parser.add_argument("--only", nargs="*", default=[], help="Record these sentence keys; keep the other replies.")
    args = parser.parse_args()
    kept = json.loads(OUT.read_text(encoding="utf-8"))["replies"] if args.only and OUT.exists() else {}
    with tempfile.TemporaryDirectory(prefix="program-shape-") as tmp:
        rig = Rig(Path(tmp))
        pid = seed(rig)
        wire = program(rig, pid)
        text = program_shaper.stripped_text(print_program(wire))
        ground = program_shaper.grounding(rig.service, wire)
        frozen = program_shaper.frozen_list(wire)
        replies = dict(kept)
        for key, sentence in SENTENCES.items():
            if args.only and key not in args.only:
                continue
            system, user = program_shaper.messages(sentence, text, frozen, ground)
            first = _send(args, text, system, user)
            entry = {"sentence": sentence, "system_prompt": system, "user_prompt": user, **first}
            # The hub's one retry: an answer the parser cannot read goes back
            # with the parser's words quoted (program_shaper.shape).
            _answer, error = program_shaper.read_answer(first["reply_text"])
            if error:
                _system, retry_user = program_shaper.messages(sentence, text, frozen, ground, error=error)
                entry["parse_error"] = error
                entry["retry"] = {"user_prompt": retry_user, **_send(args, text, system, retry_user)}
            replies[key] = entry
            print(key, entry["seconds"], "s", "(retried)" if error else "", "\n", entry["reply_text"], "\n")
    OUT.write_text(json.dumps({
        "_source": "A real engine's replies to the program.shape@1 prompt over the seed Program "
                   "(tests/integration/program_shape_seed.py), recorded by scripts/record_program_shape_reply.py. "
                   "Never hand-edit it.",
        "recorded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "engine": {"base_url": args.base_url, "model": args.model},
        "program_text": text,
        "replies": replies,
    }, indent=1, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
