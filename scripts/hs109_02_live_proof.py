"""HS-109-02 — the live proof: a real decision carries its transcript moment.

Runs the REAL decision_capture (v0.2.0, timestamp-aware) against the REAL
`.43` endpoint on a REAL archived meeting with timestamped segments, persists
through the REAL record_artifact seam, and shows:

  - the extracted decision carries a verified `source_timestamp`;
  - the projected record upgrades to `date_basis=transcript_moment`
    with `provenance_label=reported`;
  - the repository resolver maps the moment to its segment (the jump);
  - a record without a moment stays honestly `meeting_date`.

Usage:
  uv run python scripts/hs109_02_live_proof.py [meeting_id]
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
        return json.loads(resp.read().decode())["choices"][0]["message"]["content"]


def main() -> int:
    meeting_id = sys.argv[1] if len(sys.argv) > 1 else "a9e12058"
    db = Database()
    meeting = db.meetings.get_meeting(meeting_id)
    if meeting is None:
        print(f"FAIL  meeting {meeting_id} not found")
        return 1
    segments = list(getattr(meeting, "segments", []) or [])
    seg_dicts = [
        {"start_time": getattr(s, "start_time", 0.0), "end_time": getattr(s, "end_time", 0.0),
         "text": s.text}
        for s in segments
    ]
    transcript = "\n".join(s.text for s in segments)
    print(f"meeting: {meeting_id} · segments={len(segments)}")

    plugin = DecisionCapturePlugin(intel_call=intel_call)
    result = plugin.run({
        "transcript": transcript,
        "transcript_segments": seg_dicts,
    })
    decisions = result.get("decisions") or []
    print(f"REAL .43 decision_capture v0.2.0: {result.get('summary')}")
    with_moment = [d for d in decisions if d.get("source_timestamp") is not None]
    for d in decisions:
        print(f"  ts={d.get('source_timestamp')}  {str(d.get('decision'))[:80]}")
    drops = result.get("provenance_drops") or []
    if drops:
        print(f"provenance_drops (named, honest): {json.dumps(drops)[:200]}")
    if not decisions:
        print("FAIL  no decisions extracted")
        return 1

    artifact_id = f"art-live-{meeting_id}-decisions-moment"
    db.plugins.record_artifact(
        artifact_id=artifact_id,
        meeting_id=meeting_id,
        artifact_type="decisions",
        title="Decisions (HS-109-02 live proof)",
        structured_json={"decisions": decisions},
        confidence=1.0,
        status="draft",
        plugin_id="decision_capture",
        plugin_version="0.2.0",
        sources=[("plugin_run", "hs109-02-live-proof")],
    )
    records = [r for r in db.decisions.list(meeting_id=meeting_id)
               if r.source_artifact_id == artifact_id]
    ok = True
    moments = [r for r in records if r.date_basis == "transcript_moment"]
    plain = [r for r in records if r.date_basis == "meeting_date"]
    for r in records:
        print(f"  record {r.id[:16]}… basis={r.date_basis} "
              f"label={getattr(r, 'provenance_label', None)} "
              f"ts={getattr(r, 'source_timestamp', None)}")
    print(f"{'PASS' if len(records) == len(decisions) else 'FAIL'}  "
          f"all {len(decisions)} decisions projected")
    ok &= len(records) == len(decisions)
    if with_moment:
        print(f"{'PASS' if moments else 'FAIL'}  a verified moment upgraded "
              f"date_basis to transcript_moment (reported)")
        ok &= bool(moments)
        ok &= all(getattr(r, "provenance_label", None) == "reported"
                  for r in moments)
        seg = db.decisions.resolve_decision_moment(moments[0].id)
        print(f"  jump: decision {moments[0].id[:12]}… → segment "
              f"{json.dumps(seg)[:140] if not hasattr(seg, 'text') else seg.text[:80]!r}")
        print(f"{'PASS' if seg else 'FAIL'}  the resolver maps the moment to "
              f"its segment")
        ok &= bool(seg)
    else:
        print("NOTE  the model returned no timestamps this run — honest "
              "absence path:")
        print(f"{'PASS' if plain and not moments else 'FAIL'}  every record "
              f"stays meeting_date, none invented")
        ok &= bool(plain) and not moments
    print(f"\n{'ALL PASS' if ok else 'FAILURES ABOVE'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
