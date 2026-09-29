#!/usr/bin/env python3
"""PHILO-10-05: each mutation of the Phase 10 atlas (or its runner script) turns
tests/unit/test_philo10_atlas.py red.

The file is mutated in place, the fence runs (isolated HOME), the file is put
back byte for byte whatever the result. The unmutated baseline runs first and
must be green. Exit 1 if the baseline is red or a mutation stays green.
Never run while an atlas batch reads the file.
"""
from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[6]
ATLAS = REPO / "docs/internal/philo/graph/atlas-phase10.json"


def _case(atlas, cid):
    return next(c for c in atlas["cases"] if c["id"] == cid)


def _drop_part(case, kind):
    pred = case["expected"]["predicate"]
    pred["predicates"] = [p for p in pred["predicates"] if p["kind"] != kind]


def m1(a):  # drop an operation twin (SENT)
    a["cases"] = [c for c in a["cases"] if c["id"] != "case.p10.send.sent.op"]


def m2(a):  # a face case at one width only
    _case(a, "case.p10.send.failed")["viewports"] = [1440]


def m3(a):  # a face case proves the face only (no hub half)
    _drop_part(_case(a, "case.p10.send.refused"), "protocol_reads")


def m4(a):  # a twin stops reading the kernel receipt
    case = _case(a, "case.p10.send.prepared.op")
    case["expected"]["reads"] = case["expected"]["reads"][1:]
    case["expected"]["predicate"]["facts"] = [f for f in case["expected"]["predicate"]["facts"]
                                              if f.get("source") != "read" or f.get("index") != 0]


def m5(a):  # the restart transition stops counting the one dispatch
    _drop_part(_case(a, "case.p10.send.unknown_after_restart"), "cli_calls")


def m6(a):  # the replay counts two creates
    for part in _case(a, "case.p10.send.replay_same_key.op")["expected"]["predicate"]["predicates"]:
        if part["kind"] == "cli_calls":
            part["count"] = 2


def m7(a):  # the pair names different outcomes (the FAILED twin reads unknown)
    twin = _case(a, "case.p10.send.failed.op")
    raw = json.dumps(twin).replace('"failed"', '"unknown"').replace("github_target_not_found", "github_exit_1")
    twin.clear(); twin.update(json.loads(raw))


def m8(a):  # the Discard confirm split across the before-capture (not one gesture)
    case = _case(a, "case.p10.send.discard_after_send")
    case["setup"].append(dict(case["trigger"]["then"][0]))
    case["trigger"].pop("then")


def m9(a):  # an optional trigger (an optional step as the outcome)
    _case(a, "case.p10.send.sending")["trigger"]["optional"] = True


def m10(a):  # a face case with no twin and no exclusion
    a["excluded"] = [e for e in a["excluded"] if e["id"] != "excluded.p10.face_only_op"]


def m11(a):  # a matrix state loses its case
    a["cases"] = [c for c in a["cases"] if c["id"] != "case.p10.send.no_destination"]
    for state in a["states"]:
        state["reachable_by"] = [r for r in state["reachable_by"] if r != "case.p10.send.no_destination"]


def m12(a):  # a general fence: a face case that skips the first-use gate
    _case(a, "case.p10.send.prepared")["setup"].pop(1)


def m13(a):  # an api step names a route the OpenAPI export lacks
    _case(a, "case.p10.send.refused")["setup"][-1]["path"] = "/api/channels/destination/{destination_id}"


def m14(a):  # the face and its twin read different runner scripts
    for step in _case(a, "case.p10.send.unknown.op")["setup"]:
        if step.get("substitute") == "cli_runner":
            step["reply"] = "tests/fixtures/philo10_atlas/gh-posted.json"


MUTATIONS = [m1, m2, m3, m4, m5, m6, m7, m8, m9, m10, m11, m12, m13, m14]


def run(env) -> subprocess.CompletedProcess:
    return subprocess.run([str(REPO / ".venv/bin/python"), "-m", "pytest", "-q", "-p", "no:cacheprovider",
                           f"--basetemp={env['HOME']}/pt", "tests/unit/test_philo10_atlas.py"],
                          cwd=REPO, env=env, capture_output=True, text=True)


def main() -> int:
    original = ATLAS.read_bytes()
    env = dict(os.environ, HOME=tempfile.mkdtemp())
    base = run(env)
    print(f"baseline (unmutated): {base.stdout.strip().splitlines()[-1]}")
    if base.returncode != 0:
        print("the unmutated fence is not green: no mutation reading counts")
        return 1
    missed = 0
    try:
        for mutate in MUTATIONS:
            atlas = json.loads(original)
            mutate(atlas)
            ATLAS.write_text(json.dumps(atlas, indent=2) + "\n")
            proc = run(dict(os.environ, HOME=tempfile.mkdtemp()))
            red = proc.returncode != 0
            missed += not red
            failed = [l.split("::")[-1][:90] for l in proc.stdout.splitlines() if l.startswith("FAILED")]
            print(f"{mutate.__name__:4s} {'RED   ' if red else 'MISSED'} {failed[:2]}")
            ATLAS.write_bytes(original)
    finally:
        ATLAS.write_bytes(original)
    print(f"{len(MUTATIONS)} mutations: {len(MUTATIONS) - missed} red, {missed} missed")
    return 1 if missed else 0


if __name__ == "__main__":
    raise SystemExit(main())
