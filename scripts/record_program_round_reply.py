"""Record a real engine's replies to the interview rounds (PG-LANG LANG9).

    uv run python scripts/record_program_round_reply.py [--base-url http://100.118.33.80:8080/v1] [--key local]

Builds journey J1's Program at station 3 (``tests/integration/
program_rounds_seed.py``: the recorded LANG6 draft applied) on a scratch rig
database and runs the hub's own rounds (``holdspeak/services/
program_rounds.py``) through the runner, with a real OpenAI-compatible
engine at the runner's engine seam (where the tests put the recorded
replies), in the face's own sequence (``SEQUENCE`` of the seed): the
Architecture round's question, his answer (the engine's first offered
choice) and its shaping call, the next question, Apply, Skip question, Done
with Architecture; Product's question, Skip round; Stack's question, Skip
round; Verification's question, his answer and its shaping call, Done.
Every exchange (the prompt, the reply, the time) is written to
``tests/fixtures/program_round_reply.json``. No owner material is sent: the
goal is the journey's text.
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

from holdspeak.services import program_rounds  # noqa: E402
from tests.integration.program_rig import OWNER, Rig  # noqa: E402
from tests.integration.program_rounds_seed import SEQUENCE, drafted  # noqa: E402

OUT = REPO / "tests" / "fixtures" / "program_round_reply.json"


def _wire_live(rig: Rig, engine: object) -> None:
    from holdspeak.inference_capabilities import process_inference_capability_registry
    from holdspeak.kernel.runtime import _configure
    from tests.unit.test_phase143_inference_assignments import _profile
    from tests.unit.test_phase200_readiness import _assign

    broker = _configure(rig.db)
    broker.inference_runner._engine_factory = lambda revision, **_kw: engine
    schema = process_inference_capability_registry().require("agent.plan")
    _profile(rig.db, "home-engine", claims=("language", f"result_schema:{schema.output_schema_sha256}"))
    _assign(rig.db, "agent.plan", ["home-engine"])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://100.118.33.80:8080/v1")
    parser.add_argument("--key", default="local")
    parser.add_argument("--model", default="qwen3.8-27b")
    args = parser.parse_args()
    exchanges: list[dict] = []

    class LiveEngine:
        active_provider = "openai_compatible"
        active_model = args.model

        def run_prompt(self, *, system_prompt: str, user_prompt: str, temperature=None, max_tokens=None,
                       response_format=None, **_kw) -> str:
            body = {"model": args.model, "temperature": temperature, "max_tokens": max_tokens,
                    "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
                    "response_format": response_format}
            request = urllib.request.Request(
                args.base_url.rstrip("/") + "/chat/completions", data=json.dumps(body).encode(),
                headers={"Content-Type": "application/json", "Authorization": f"Bearer {args.key}"})
            started = time.monotonic()
            with urllib.request.urlopen(request, timeout=600) as response:
                reply = json.loads(response.read())
            text = reply["choices"][0]["message"]["content"]
            seconds = round(time.monotonic() - started, 2)
            exchanges.append({"contract": (response_format or {}).get("json_schema", {}).get("name"),
                              "system_prompt": system_prompt, "user_prompt": user_prompt, "max_tokens": max_tokens,
                              "reply_text": text, "seconds": seconds, "usage": reply.get("usage"),
                              "model": reply.get("model") or args.model})
            print(f"exchange {len(exchanges)}", seconds, "s", reply.get("usage"), flush=True)
            return text

    steps: list[dict] = []

    def step(label: str, out: dict, start: int) -> dict:
        question = out.get("question")
        row = {"label": label, "exchanges": exchanges[start:]}
        if question:
            row["question"] = {key: question.get(key) for key in ("text", "why", "choices", "answer", "became")}
        if out.get("changes") is not None:
            row["changes"] = [{key: item.get(key) for key in ("op", "where", "field", "verdict", "after")}
                              for item in out["changes"]]
        row["seconds"] = out.get("seconds")
        steps.append(row)
        print(label, question.get("text") if question else out.get("state"), out.get("seconds"), flush=True)
        for item in row.get("changes") or []:
            print("  ", item["op"], item["where"], item["field"], item["verdict"], (item.get("after") or "")[:80])
        return out

    with tempfile.TemporaryDirectory(prefix="program-rounds-") as tmp:
        rig = Rig(Path(tmp))
        _wire_live(rig, LiveEngine())
        pid = drafted(rig)
        service = rig.service
        program_rounds.open_rounds(service, OWNER, pid)
        # The face's sequence (tests/integration/test_desk_program_rounds.py walks the same).
        outs: list[dict] = []
        for label, call in SEQUENCE:
            mark = len(exchanges)
            outs.append(step(label, call(service, pid, outs), mark))
    rounds = {"sequence": steps}
    OUT.write_text(json.dumps({
        "_source": "A real engine's replies to the program.round@1 and program.shape@1 prompts over journey J1 at "
                   "station 3 (tests/integration/program_rounds_seed.py), recorded by "
                   "scripts/record_program_round_reply.py. Never hand-edit it.",
        "recorded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "engine": {"base_url": args.base_url, "model": args.model},
        **rounds,
    }, indent=1, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
