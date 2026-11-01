"""Record a real engine's replies to the split and the night's planning (PG-LANG LANG8, LANG12).

    uv run python scripts/record_program_night_reply.py [--base-url http://100.118.33.80:8080/v1] [--key local]

Builds the cases of ``tests/integration/program_night_seed.py`` on a scratch
rig database with THIS repository as the Program's repository (read only:
``git ls-files``, file sizes), and runs the hub's own calls
(``program_split.ask``, ``program_night.ask_item``) through the runner, with
a real OpenAI-compatible engine at the runner's engine seam (where the tests
put the recorded replies). Every exchange and the bytes of every path the
cases and the replies own go to ``tests/fixtures/program_night_reply.json``;
the tests replay the replies over a rig repository with those files at those
sizes. No owner material is sent: the words are journey J2's.
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

from holdspeak.services import program_night, program_sizing, program_split  # noqa: E402
from holdspeak.services.program_shaper import read_answer  # noqa: E402,F401
from tests.integration.program_night_seed import (  # noqa: E402
    NIGHT_ITEMS, SPLIT_STEP, make_dreaming, make_night, make_split,
)
from tests.integration.program_rig import OWNER, Rig  # noqa: E402

OUT = REPO / "tests" / "fixtures" / "program_night_reply.json"


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
    parser.add_argument("--only", choices=("split_night", "backlog"), default=None,
                        help="record one case group and keep the others as recorded")
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
            exchanges.append({"system_prompt": system_prompt, "user_prompt": user_prompt, "max_tokens": max_tokens,
                              "reply_text": text, "seconds": seconds, "usage": reply.get("usage"),
                              "model": reply.get("model") or args.model})
            print(f"exchange {len(exchanges)}", seconds, "s", reply.get("usage"), flush=True)
            return text

    cases: dict[str, dict] = {}
    with tempfile.TemporaryDirectory(prefix="program-night-") as tmp:
        rig = Rig(Path(tmp))
        _wire_live(rig, LiveEngine())
        if args.only != "backlog":
            _split_and_night(rig, cases, exchanges)
        if args.only != "split_night":
            _backlog(rig, cases, exchanges)
    if args.only and OUT.exists():
        cases = {**json.loads(OUT.read_text(encoding="utf-8"))["cases"], **cases}
    _write(args, cases)


def _split_and_night(rig: Rig, cases: dict, exchanges: list) -> None:
    pid, step_id = make_split(rig, repository=str(REPO))
    program, step = rig.service.store.get_program(pid), rig.service.store.get_step(step_id)
    size = program_split.step_size(rig.service, program, step, step.get("profile") or program["default_profile"],
                                   None)
    print("the step:", size["words"], flush=True)
    parts, engine, reason = program_split.ask(rig.service, OWNER, program, step, size)
    owned = set(SPLIT_STEP["owns"]) | {path for part in parts or [] for path in part["owns"]}
    cases["split"] = {"step": SPLIT_STEP, "size": size, "exchanges": list(exchanges), "parts": parts,
                      "engine": engine, "reason": reason,
                      "file_bytes": {path: program_sizing.path_bytes(str(REPO), path) for path in sorted(owned)}}
    print(json.dumps(parts, indent=1), flush=True)
    items = []
    night_pid, step_ids = make_night(rig, repository=str(REPO))
    night = rig.service.store.get_program(night_pid)
    for line, sid in zip(NIGHT_ITEMS, step_ids):
        before = len(exchanges)
        fields, engine, reason = program_night.ask_item(rig.service, OWNER, night, rig.service.store.get_step(sid))
        items.append({"line": line, "exchanges": exchanges[before:], "fields": fields, "engine": engine,
                      "reason": reason})
        print(line, "->", json.dumps(fields), flush=True)
    cases["night"] = {"items": items}


def _backlog(rig: Rig, cases: dict, exchanges: list) -> None:
    """J2's standing backlog (Door tasks with the word "dream"), read by rule."""
    from holdspeak.principals import Principal, PrincipalKind

    backlog = []
    dream_pid = make_dreaming(rig, repository=str(REPO))
    dream = rig.service.store.get_program(dream_pid)
    engine_principal = Principal(PrincipalKind.AGENT, "program-engine:night-backlog")
    for item in program_night.backlog_items(rig.service, dream):
        added = program_night.add_to_night(rig.service, engine_principal, kind="action", item_id=item["id"],
                                           program_id=dream_pid)
        before = len(exchanges)
        fields, engine, reason = program_night.ask_item(rig.service, OWNER, rig.service.store.get_program(dream_pid),
                                                        rig.service.store.get_step(added["step_id"]))
        backlog.append({"line": item["task"], "exchanges": exchanges[before:], "fields": fields, "engine": engine,
                        "reason": reason})
        print(item["task"], "->", json.dumps(fields), flush=True)
    owned_backlog = {path for row in backlog for path in (row["fields"] or {}).get("owns") or []}
    cases["backlog"] = {"items": backlog, "within": list(dream.get("within") or []),
                        "file_bytes": {path: program_sizing.path_bytes(str(REPO), path)
                                       for path in sorted(owned_backlog)}}


def _write(args: argparse.Namespace, cases: dict) -> None:
    OUT.write_text(json.dumps({
        "_source": "A real engine's replies to program.split@1 (holdspeak/services/program_split.py) and "
                   "program.night_item@1 (holdspeak/services/program_night.py) over the cases of "
                   "tests/integration/program_night_seed.py, recorded by scripts/record_program_night_reply.py "
                   "with this repository as the Program's repository. Never hand-edit it.",
        "recorded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "engine": {"base_url": args.base_url, "model": args.model},
        "cases": cases,
    }, indent=1, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
