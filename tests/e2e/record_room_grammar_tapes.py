"""Record Room selection-seat reads from the existing isolated producer rig."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import record_room_wires as producer


def record(hub, _mp):
    pid = producer.rig._seed_brief_room(hub, "room-grammar10")
    note = hub.ok("POST", "/api/notes", {"title": "Cut-over brief", "body_markdown": "The cut-over runs on the read replica first."})
    return {
        "project_id": pid,
        "room": hub.ok("GET", f"/api/projects/{pid}/room"),
        "recall": hub.ok("GET", "/api/memory/recall?recent=1&filter=all"),
        "preview": hub.ok("POST", "/api/projects/door/preview", {"outcome": "Cut-over", "pasted": "https://github.com/karolswdev/HoldSpeak"}),
        "note": note,
    }


if __name__ == "__main__":
    data = producer._run("room-grammar10", record, gh_runner=producer.rig._gh_signed_in)
    dest = ROOT / "web/src/features/project-room/__tests__/room-wires/recall10.json"
    dest.write_text(json.dumps({"recordedBy": "tests/e2e/record_room_grammar_tapes.py", "engine_mode": "none", **data}, indent=2) + "\n")
    print(dest)
