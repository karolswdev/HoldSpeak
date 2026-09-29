#!/usr/bin/env python3
"""PHILO-10-05: the equivalence run -- each face case and its .op twin, read from
the retained observations of ONE batch (default p10-merged): both widths and the
twin pass, and the durable outcome the face's own press answered equals the one
the MCP twin answered (outcome or refusal code, send state, reason, receipt
state and actor, operation name, channel, gh creates at the runner).
Exit 1 on any difference or any run that did not pass."""
import json
import sys
from pathlib import Path

SHOTS = Path(__file__).resolve().parent.parent / "story-05-shots"
label = sys.argv[1] if len(sys.argv) > 1 else "p10-merged"
root = SHOTS / label
rows = [l.split("\t") for l in (root / "runs.tsv").read_text().splitlines()[1:]]
obs = {(r[1], r[2]): json.loads((root / r[7] / "observation.json").read_text()) for r in rows}


def gh(o):
    calls = (o.get("after") or {}).get("cli_calls")
    return None if calls is None else sum(c["argv"][:3] == ["gh", "issue", "comment"] for c in calls)


def rows_of(payload):
    """The hub's stored rows a face read or a twin's durable read answered: (kind, channel, state, by)."""
    payload = payload or {}
    out = []
    for kind in ("destinations", "sends"):
        for r in payload.get(kind) or []:
            out.append((kind, r.get("channel"), r.get("state"), (r.get("prepared_by") or {}).get("kind")))
    return sorted(out, key=str)


def face_rows(o):
    reads = (o.get("after") or {}).get("api_reads") or []
    return rows_of(reads[0].get("payload")) if reads else []


def op_rows(o):
    after = o.get("after") or {}
    found = rows_of((after.get("op") or {}).get("response"))
    for read in after.get("op_reads") or []:
        found += rows_of(read.get("response"))
    return sorted(found, key=str)


def face_facts(o):
    body = ((o.get("after") or {}).get("trigger_response") or {}).get("body") or {}
    rec, send = body.get("receipt") or {}, body.get("send") or {}
    return {"outcome": body.get("outcome") or body.get("code"), "send.state": send.get("state"),
            "send.reason": send.get("reason"), "channel": send.get("channel"),
            "receipt.state": rec.get("state"), "receipt.actor_kind": rec.get("actor_kind"), "gh_creates": gh(o)}


def op_facts(o):
    t = o.get("trigger") or {}
    body = t.get("response") or t.get("refusal") or {}
    rec, send = body.get("receipt") or {}, body.get("send") or {}
    return {"outcome": body.get("outcome") or body.get("code"), "send.state": send.get("state"),
            "send.reason": send.get("reason"), "channel": send.get("channel"),
            "receipt.state": rec.get("state"), "receipt.actor_kind": rec.get("actor_kind"), "gh_creates": gh(o)}


bad = 0
faces = sorted({c for c, w in obs if w != "op" and (c + ".op", "op") in obs})
for cid in faces:
    twin = obs[(cid + ".op", "op")]
    verdicts = [obs[(cid, w)]["verdict"] for w in ("1440", "393")] + [twin["verdict"]]
    t = op_facts(twin)
    keys = [k for k in t if t[k] is not None]
    lines = []
    for w in ("1440", "393"):
        f = face_facts(obs[(cid, w)])
        diff = {k: (f.get(k), t[k]) for k in keys if f.get(k) is not None and f.get(k) != t[k]}
        shared = {k: t[k] for k in keys if f.get(k) is not None}
        lines.append((w, shared, diff))
    # The stored rows the face read vs the twin's durable read (destinations or sends).
    twin_rows = op_rows(twin)
    for w in ("1440", "393"):
        fr = face_rows(obs[(cid, w)])
        if fr and twin_rows and {r[0] for r in fr} & {r[0] for r in twin_rows}:
            kind = fr[0][0]
            a, b = [r for r in fr if r[0] == kind], [r for r in twin_rows if r[0] == kind]
            lines.append((w + " rows", {"rows": a}, {} if a == b else {"rows": (a, b)}))
    ok = all(v == "pass" for v in verdicts) and not any(d for _, _, d in lines)
    bad += not ok
    print(f"{'EQUAL' if ok else 'DIFF '} {cid}: verdicts {verdicts}")
    for w, shared, diff in lines:
        print(f"      {w}: shared {shared}" + (f"  DIFFERENT {diff}" if diff else ""))
print(f"{len(faces)} pairs; {bad} not equal")
sys.exit(1 if bad else 0)
