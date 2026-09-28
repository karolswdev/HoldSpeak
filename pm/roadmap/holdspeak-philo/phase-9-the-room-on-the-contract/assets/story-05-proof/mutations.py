#!/usr/bin/env python3
"""PHILO-9-05: each mutation of the Phase 9 atlas turns tests/unit/test_philo9_atlas.py red.

The file is mutated in place, the fence runs (isolated HOME), the file is put
back byte for byte whatever the result. Exit 1 if a mutation stays green.
"""
from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[6]
ATLAS = REPO / "docs/internal/philo/graph/atlas-phase9.json"
STEWARD = REPO / "docs/internal/philo/graph/atlas-phase9-steward.json"


def _case(atlas, cid):
    return next(c for c in atlas["cases"] if c["id"] == cid)


def m1(a):  # drop the operation twin of the delivery face
    a["cases"] = [c for c in a["cases"] if c["id"] != "case.p9.update.delivered_row.op"]


def m2(a):  # a face case at one width only
    _case(a, "case.p9.grant.project_allowed")["viewports"] = [1440]


def m3(a):  # the route twin stops reading the receipt's actor
    exp = _case(a, "case.p9.grant_route.project_allowed")["expected"]["predicate"]["expect"][1]["row"]["match"]
    exp.pop("receipt.actor_kind")


def m4(a):  # an optional trigger (an optional step as the outcome)
    _case(a, "case.p9.grant.desk_reads_desk")["trigger"]["optional"] = True


def m5(a):  # a face case with no twin and no exclusion
    a["excluded"] = [e for e in a["excluded"] if e["id"] != "excluded.p9.grant_face_op"]


def m6(a):  # the pair names different recipients
    for step in [_case(a, "case.p9.update.delivered_row.op")["trigger"]]:
        step["args"]["delivered_to"] = "Tomas"
    _case(a, "case.p9.update.delivered_row.op")["expected"]["predicate"]["facts"][2]["value"] = "Tomas"


def m7(a):  # a general fence: a face case that skips the first-use gate
    _case(a, "case.p9.connections.never_checked_face")["setup"].pop(1)


def m8(a):  # the route twin's api step names a route the OpenAPI export lacks
    _case(a, "case.p9.grant_route.project_allowed")["trigger"]["path"] = "/api/settings/remote/grants/{project_id}"


def m9(a):  # the delivery face reads the words only (round one's shape)
    face = _case(a, "case.p9.update.delivered_row")
    face["expected"]["predicate"] = {"kind": "readable_text", "value": "Priya"}


def m10(steward):  # the Connections twin expects another state (Codex Astra r1 finding 3), in atlas-phase9-steward.json
    facts = _case(steward, "case.p9.connections.never_checked")["expected"]["predicate"]["facts"]
    for fact in facts:
        if isinstance(fact.get("contains"), dict) and fact["contains"].get("provider_id") == "github":
            fact["contains"]["state"] = "ready"


def main() -> int:
    originals = {ATLAS: ATLAS.read_bytes(), STEWARD: STEWARD.read_bytes()}
    original = originals[ATLAS]
    env0 = dict(os.environ, HOME=tempfile.mkdtemp())
    base = subprocess.run([str(REPO / ".venv/bin/python"), "-m", "pytest", "-q", "-p", "no:cacheprovider",
                           "tests/unit/test_philo9_atlas.py"], cwd=REPO, env=env0, capture_output=True, text=True)
    print(f"baseline (unmutated): {base.stdout.strip().splitlines()[-1]}")
    if base.returncode != 0:
        print("the unmutated fence is not green: no mutation reading counts")
        return 1
    missed = 0
    mutations = (m1, m2, m3, m4, m5, m6, m7, m8, m9, m10)
    for mutate in mutations:
        target = STEWARD if mutate is m10 else ATLAS
        atlas = json.loads(originals[target])
        mutate(atlas)
        target.write_text(json.dumps(atlas, indent=2) + "\n")
        try:
            env = dict(os.environ, HOME=tempfile.mkdtemp())
            proc = subprocess.run([str(REPO / ".venv/bin/python"), "-m", "pytest", "-q", "-p", "no:cacheprovider",
                                   "tests/unit/test_philo9_atlas.py"], cwd=REPO, env=env,
                                  capture_output=True, text=True)
        finally:
            for path, data in originals.items():
                path.write_bytes(data)
        tail = proc.stdout.strip().splitlines()[-1] if proc.stdout.strip() else proc.stderr[-200:]
        failed = [line.split(" - ")[0] for line in proc.stdout.splitlines() if line.startswith("FAILED")]
        red = proc.returncode != 0
        missed += not red
        print(f"{mutate.__name__} ({mutate.__doc__ or mutate.__code__.co_firstlineno}): "
              f"{'RED' if red else 'MISSED'} - {tail}; {failed[:3]}")
    assert all(path.read_bytes() == data for path, data in originals.items())
    print(f"{len(mutations) - missed} red, {missed} missed")
    return 1 if missed else 0


if __name__ == "__main__":
    raise SystemExit(main())
