"""HS-109-01 — the live proof, on the real archive and real metal.

Takes a REAL archived meeting, runs the REAL decision_capture plugin
against the LAN llama.cpp endpoint (192.168.1.43:8080), persists the
decisions artifact through the REAL seam (`db.plugins.record_artifact`),
and shows the chokepoint projection: decision records exist without any
manual reconcile call, and a second persistence is a no-op.

Usage:
  uv run python scripts/hs109_01_live_proof.py [meeting_id]
"""

from __future__ import annotations

import json
import sys
import urllib.request

from holdspeak.db import Database
from holdspeak.plugins.builtin.decision_capture import DecisionCapturePlugin

ENDPOINT = "http://192.168.1.43:8080/v1/chat/completions"


def intel_call(messages: list[dict[str, str]]) -> str:
    req = urllib.request.Request(
        ENDPOINT,
        data=json.dumps(
            {"messages": messages, "temperature": 0.2, "max_tokens": 800}
        ).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=180) as resp:
        body = json.loads(resp.read().decode())
    return body["choices"][0]["message"]["content"]


def snapshot(db: Database, meeting_id: str) -> list[dict[str, str]]:
    return [
        {"id": r.id, "text": r.text, "lifecycle": r.lifecycle,
         "date_basis": r.date_basis, "source_state": r.source_state}
        for r in db.decisions.list(meeting_id=meeting_id)
    ]


def main() -> int:
    meeting_id = sys.argv[1] if len(sys.argv) > 1 else "a9e12058"
    db = Database()
    meeting = db.meetings.get_meeting(meeting_id)
    if meeting is None:
        print(f"FAIL  meeting {meeting_id} not found")
        return 1
    segments = list(getattr(meeting, "segments", []) or [])
    transcript = "\n".join(seg.text for seg in segments)
    print(f"meeting: {meeting_id} · segments={len(segments)} · "
          f"transcript={len(transcript)} chars")

    plugin = DecisionCapturePlugin(intel_call=intel_call)
    result = plugin.run({"transcript": transcript})
    decisions = result.get("decisions") or []
    print(f"REAL .43 decision_capture: {result.get('summary')}")
    for d in decisions:
        print(f"  - {json.dumps(d)[:140]}")
    if not decisions:
        print("FAIL  the real model extracted no decisions")
        return 1

    artifact_id = f"art-live-{meeting_id}-decisions"
    before = snapshot(db, meeting_id)

    def persist() -> None:
        db.plugins.record_artifact(
            artifact_id=artifact_id,
            meeting_id=meeting_id,
            artifact_type="decisions",
            title="Decisions (HS-109-01 live proof)",
            structured_json={"decisions": decisions},
            confidence=1.0,
            status="draft",
            plugin_id="decision_capture",
            plugin_version="0.1.0",
            sources=[("plugin_run", "hs109-01-live-proof")],
        )

    persist()
    first = snapshot(db, meeting_id)
    persist()
    second = snapshot(db, meeting_id)

    new = [r for r in first if r["id"] not in {b["id"] for b in before}]
    print(f"\nprojected WITHOUT any manual reconcile call: {len(new)} new record(s)")
    for r in new:
        print(f"  {r['id'][:16]}…  '{r['text'][:70]}'  lifecycle={r['lifecycle']} "
              f"date_basis={r['date_basis']} source={r['source_state']}")
    ok_projected = len(new) == len(decisions)
    ok_idempotent = first == second
    print(f"{'PASS' if ok_projected else 'FAIL'}  every extracted decision projected "
          f"({len(new)}/{len(decisions)})")
    print(f"{'PASS' if ok_idempotent else 'FAIL'}  second persistence is a no-op "
          f"(records byte-identical)")
    return 0 if (ok_projected and ok_idempotent) else 1


if __name__ == "__main__":
    sys.exit(main())
