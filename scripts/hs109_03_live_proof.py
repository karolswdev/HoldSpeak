"""HS-109-03 — the live proof: a real decision becomes a real artifact.

On the REAL archive, through the REAL routes (the assembled app), with the
model-assisted leg generating on the REAL `.43` runtime profile through the
registered `inference.run@1` operation:

  1. Accept the real BLUE LANTERN decision (owner gesture, receipt).
  2. Deterministic promote → ADR citing `decision:<id>`; promote again →
     the SAME artifact (idempotent). Lineage queryable both ways.
  3. Model-assisted draft on `.43` → a `draft` artifact, the kernel
     receipt read back naming outcome and result ref.
  4. Supersede by a real successor → derived artifact marked; re-promotion
     refuses BY NAME, naming the successor.

Usage:
  uv run python scripts/hs109_03_live_proof.py
"""

from __future__ import annotations

import sys
import time
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

import holdspeak.db as hsdb
from holdspeak.db import Database
from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

TARGET_43 = "profile_03617b8c9250"


def main() -> int:
    ok = True
    db = Database()
    hsdb.get_database = lambda *a, **k: db  # the real archive behind the real app

    callbacks = WebRuntimeCallbacks(
        on_bookmark=MagicMock(), on_stop=MagicMock(),
        get_state=MagicMock(return_value={"id": "hs109-03-live"}),
    )
    client = TestClient(
        MeetingWebServer(callbacks, host="127.0.0.1",
                         auth_token="owner-secret").app
    )
    client.headers["Authorization"] = "Bearer owner-secret"

    # Rerunnable forever: supersession is permanent (by design), so the walk
    # mints its own two decisions through the REAL chokepoint each session —
    # clearly named, cleaned up at the end — instead of consuming the
    # archive's records.
    nonce = time.strftime("%Y%m%dT%H%M%S")
    fixture_artifact = f"art-beats-walk-{nonce}"
    db.plugins.record_artifact(
        artifact_id=fixture_artifact,
        meeting_id="a9e12058",
        artifact_type="decisions",
        title=f"Decisions (HS-109 beats walk {nonce})",
        structured_json={"decisions": [
            {"decision": f"Beats walk {nonce}: adopt the long memory",
             "rationale": "walk fixture"},
            {"decision": f"Beats walk {nonce}: supersede the trial adoption",
             "rationale": "walk fixture"},
        ]},
        confidence=1.0,
        status="draft",
        plugin_id="decision_capture",
        plugin_version="0.2.0",
        sources=[("plugin_run", f"hs109-beats-{nonce}")],
    )
    records = [r for r in db.decisions.list(meeting_id="a9e12058")
               if r.source_artifact_id == fixture_artifact]
    if len(records) < 2:
        print("FAIL  the fixture artifact did not project two records")
        return 1
    blue, successor = records[0], records[1]
    print(f"decision: {blue.id} '{blue.text[:60]}' lifecycle={blue.lifecycle}")

    if blue.lifecycle == "recorded":
        acc = client.post(f"/api/decisions/{blue.id}/accept")
        print(f"accept → {acc.status_code} receipt={acc.json().get('receipt_id', acc.json())}")
    if successor.lifecycle == "recorded":
        client.post(f"/api/decisions/{successor.id}/accept")

    p1 = client.post(f"/api/decisions/{blue.id}/promote/adr")
    a1 = p1.json().get("artifact", {})
    p2 = client.post(f"/api/decisions/{blue.id}/promote/adr")
    a2 = p2.json().get("artifact", {})
    print(f"deterministic promote → {p1.status_code} artifact={a1.get('id')} "
          f"status={a1.get('status')}")
    same = a1.get("id") == a2.get("id") and p2.status_code == 200
    print(f"{'PASS' if same else 'FAIL'}  double promotion is one artifact")
    ok &= same

    sources = db.plugins.get_artifact(a1["id"]).sources
    cites = any(s.get("source_type") == "decision" and s.get("source_ref") == blue.id
                for s in sources)
    both_ways = [a.id for a in
                 db.plugins.list_artifacts_by_source("decision", blue.id)]
    detail = client.get(f"/api/decisions/{blue.id}").json()
    derived = [a["id"] for a in detail["lineage"]["derived_artifacts"]]
    print(f"{'PASS' if cites else 'FAIL'}  artifact_sources cite decision:{blue.id[:12]}…")
    print(f"{'PASS' if a1['id'] in both_ways and a1['id'] in derived else 'FAIL'}  "
          f"lineage queryable both ways")
    ok &= cites and a1["id"] in both_ways and a1["id"] in derived

    m = client.post(
        f"/api/decisions/{blue.id}/promote/decision_announcement/draft-with-model",
        json={"inference_target_id": TARGET_43},
    )
    mj = m.json()
    print(f"model-assisted on .43 → {m.status_code} "
          f"artifact={mj.get('artifact', {}).get('id')} "
          f"status={mj.get('artifact', {}).get('status')} "
          f"target={mj.get('inference_target', {}).get('id')}")
    body = str(mj.get("artifact", {}).get("body_markdown", ""))
    print(f"  generated head: {body[:120]!r}")
    from holdspeak.kernel.runtime import _configure
    broker = _configure(db)
    receipt = broker.store.receipt(mj.get("operation_id", ""))
    op = broker.store.operation(mj.get("operation_id", ""))
    print(f"  kernel receipt: op={op.get('name') if op else None} "
          f"outcome={receipt.get('outcome') if receipt else None} "
          f"result_ref={receipt.get('result_ref') if receipt else None}")
    model_ok = (m.status_code == 200
                and mj.get("artifact", {}).get("status") == "draft"
                and receipt and receipt.get("outcome") == "succeeded"
                and len(body) > 40)
    print(f"{'PASS' if model_ok else 'FAIL'}  real generation behind real admission "
          f"with a real receipt")
    ok &= bool(model_ok)

    sup = client.post(f"/api/decisions/{blue.id}/supersede",
                      json={"superseded_by": successor.id})
    print(f"supersede → {sup.status_code}")
    marked = db.plugins.get_artifact(a1["id"]).status
    print(f"  derived artifact status after supersession: {marked}")
    rp = client.post(f"/api/decisions/{blue.id}/promote/adr")
    rj = rp.json()
    names = successor.id in str(rj)
    print(f"re-promotion → {rp.status_code} detail={str(rj)[:140]}")
    print(f"{'PASS' if sup.status_code == 200 and marked == 'rejected' else 'FAIL'}  "
          f"supersession propagates to the derived artifact")
    print(f"{'PASS' if rp.status_code >= 400 and names else 'FAIL'}  "
          f"re-promotion refuses naming the successor")
    ok &= sup.status_code == 200 and marked == "rejected"
    ok &= rp.status_code >= 400 and names

    # Leave the archive tidy: the fixture and everything derived from it.
    for artifact in db.plugins.list_artifacts_by_source("decision", blue.id):
        db.plugins.delete_artifact(artifact.id)
    if mj.get("artifact", {}).get("id"):
        db.plugins.delete_artifact(mj["artifact"]["id"])
    db.plugins.delete_artifact(fixture_artifact)
    with db._connection() as conn:
        conn.execute(
            "UPDATE decisions SET deleted = 1 WHERE source_artifact_id = ?",
            (fixture_artifact,),
        )
    print("walk fixtures cleaned up")
    print(f"\n{'ALL PASS' if ok else 'FAILURES ABOVE'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
