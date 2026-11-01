"""Record a real engine's replies to Program planning (PG-LANG LANG6).

    uv run python scripts/record_program_plan_reply.py [--base-url http://100.118.33.80:8080/v1] [--key local]
                                                       [--budget 64k] [--case j1]

Builds journey J1's Program (PROGRAM-JOURNEYS-2026-10-31.md, "Two paragraphs
to a shipped change": its two paragraphs, Build and review, the project
HoldSpeak) on a scratch rig database, with THIS repository as its
repository (read only: ``git ls-files``, ``git log``, file sizes), and runs
the hub's own planner (``holdspeak/services/program_planner.py``) through
the runner, with a real OpenAI-compatible engine at the runner's engine seam
(where the tests put the recorded replies): the prompt, the one retry, the
sizing and the one split call are the hub's. Every exchange (the
prompt, the reply, the time) and the bytes of every path the replies own
are written to ``tests/fixtures/program_plan_reply.json``; the tests replay
the replies through the runner over a rig repository with those files at
those sizes. No owner material is sent: the goal is the journey's text.
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

from holdspeak.services import program_planner, program_sizing  # noqa: E402
from holdspeak.services.program_text import parse_program_text  # noqa: E402
from tests.integration.program_plan_seed import CASES  # noqa: E402
from tests.integration.program_rig import OWNER, Rig  # noqa: E402

OUT = REPO / "tests" / "fixtures" / "program_plan_reply.json"


def _wire_live(rig: Rig, engine: object) -> None:
    """The runner's engine seam, as the tests wire it (``wire_engine``), with
    the live engine in place of the recorded replies."""
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
    parser.add_argument("--case", nargs="*", default=list(CASES), help="Record these cases; keep the others.")
    args = parser.parse_args()
    kept = json.loads(OUT.read_text(encoding="utf-8"))["cases"] if OUT.exists() else {}
    cases = {key: value for key, value in kept.items() if key not in args.case}
    for key in args.case:
        case = CASES[key]
        exchanges: list[dict] = []

        class LiveEngine:
            """The engine the hub's runner loads: a real OpenAI-compatible server."""

            active_provider = "openai_compatible"
            active_model = args.model

            def run_prompt(self, *, system_prompt: str, user_prompt: str, temperature=None, max_tokens=None,
                           response_format=None, **_kw) -> str:
                body = {"model": args.model, "temperature": temperature, "max_tokens": max_tokens,
                        "messages": [{"role": "system", "content": system_prompt},
                                     {"role": "user", "content": user_prompt}],
                        "response_format": response_format}
                request = urllib.request.Request(
                    args.base_url.rstrip("/") + "/chat/completions", data=json.dumps(body).encode(),
                    headers={"Content-Type": "application/json", "Authorization": f"Bearer {args.key}"})
                started = time.monotonic()
                with urllib.request.urlopen(request, timeout=600) as response:
                    reply = json.loads(response.read())
                text = reply["choices"][0]["message"]["content"]
                seconds = round(time.monotonic() - started, 2)
                exchanges.append({"system_prompt": system_prompt, "user_prompt": user_prompt, "max_tokens": max_tokens,
                                  "reply_text": text, "seconds": seconds, "usage": reply.get("usage"),
                                  "model": reply.get("model") or args.model})
                print(key, f"exchange {len(exchanges)}", seconds, "s", reply.get("usage"), flush=True)
                return text

        with tempfile.TemporaryDirectory(prefix="program-plan-") as tmp:
            rig = Rig(Path(tmp))
            from tests.integration.program_plan_seed import create

            pid = create(rig, case, repository=str(REPO))
            _wire_live(rig, LiveEngine())
            result = program_planner.plan(rig.service, OWNER, pid)
            # The face's Split on a row still too big: the same call with the
            # draft he sees and the step's place (one more engine call).
            split_result, split_from = None, len(exchanges)
            still = next((row for row in result.sizes if row["fits"] is False), None)
            if still is not None:
                split_result = program_planner.plan(rig.service, OWNER, pid, text=result.proposed_text,
                                                    split=still["place"])
        owned: set[str] = set()
        from holdspeak.services.program_shaper import read_answer

        for exchange in exchanges:

            answer, _error = read_answer(exchange["reply_text"])
            if answer and answer.get("text"):
                owned |= {path for step in parse_program_text(answer["text"]).steps for path in step.owns}
            for row in (answer or {}).get("programs") or []:
                owned |= {path for step in parse_program_text(str(row.get("text") or "")).steps for path in step.owns}
        cases[key] = {
            "goal": case["goal"], "title": case["title"], "budget": case.get("budget"),
            "exchanges": exchanges[:split_from],
            "split_exchanges": exchanges[split_from:],
            "split_result": {"place": still["place"], "proposed_text": split_result.proposed_text,
                             "sizes": split_result.sizes} if split_result is not None else None,
            "file_bytes": {path: program_sizing.path_bytes(str(REPO), path) for path in sorted(owned)},
            "result": {"proposed_text": result.proposed_text, "sizes": result.sizes, "say": result.say,
                       "split": result.split, "latency_ms": result.latency_ms, "attempts": result.attempts,
                       # JRN1: the Programs the draft proposes ([] for one goal).
                       "programs": [{"title": row["title"], "goal": row["goal"], "hands": row["hands"],
                                     "steps": row["steps"]} for row in result.programs]},
        }
        print(result.proposed_text)
        for row in result.sizes:
            print(row["place"], row["title"], row["words"])
    OUT.write_text(json.dumps({
        "_source": "A real engine's replies to the program.plan@1 prompt (holdspeak/services/program_planner.py) over "
                   "the journeys' Programs (tests/integration/program_plan_seed.py), recorded by "
                   "scripts/record_program_plan_reply.py with this repository as the Program's repository. "
                   "Never hand-edit it.",
        "recorded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "engine": {"base_url": args.base_url, "model": args.model},
        "cases": cases,
    }, indent=1, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
