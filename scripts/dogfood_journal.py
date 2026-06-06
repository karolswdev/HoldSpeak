#!/usr/bin/env python3
"""HS-45-06: the dictation-journal dogfood — record → review → correct → replay.

Drives the **real** journal HTTP surface end-to-end, no mic and no LAN-LLM:

  1. dry-run a few utterances → the journal populates (one row each).
  2. review them via GET /api/dictation/journal (newest-first, latency, source).
  3. correct one in the moment (POST …/journal/{id}/correct) → it teaches a
     correction AND the entry flips `corrected`.
  4. replay that utterance (POST …/journal/{id}/replay) → the routing visibly
     changes to the corrected target — "it learned".
  5. invariant: with journal_enabled=false, the same dry-run writes NO row and
     returns byte-identical final text.

Prints `JOURNAL DOGFOOD OK` on success. Run:

    uv run python scripts/dogfood_journal.py
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path
from textwrap import dedent
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

_BLOCKS = dedent(
    """
    version: 1
    default_match_confidence: 0.6
    blocks:
      - id: quick_note
        description: a note block
        match: {examples: ["jot this down"]}
        inject: {mode: replace, template: "{raw_text}"}
    """
).strip()

# A mutable journal toggle so step 5 can flip it without rebuilding the server.
_STATE = {"journal_enabled": True}


def _check(cond: bool, msg: str) -> None:
    mark = "✓" if cond else "✗"
    print(f"  {mark} {msg}")
    if not cond:
        raise SystemExit(f"DOGFOOD FAILED: {msg}")


def main() -> int:
    import holdspeak.config as config_module
    from holdspeak.config import (
        Config,
        DictationConfig,
        DictationPipelineConfig,
        LLMRuntimeConfig,
    )
    from holdspeak.db import Database, reset_database
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks
    from fastapi.testclient import TestClient

    tmp = Path(tempfile.mkdtemp())
    config_module.CONFIG_FILE = tmp / "config.json"
    proj = tmp / "ledgerline"
    (proj / ".holdspeak").mkdir(parents=True)
    (proj / ".holdspeak" / "blocks.yaml").write_text(_BLOCKS, encoding="utf-8")
    (proj / "pyproject.toml").write_text('[project]\nname="ledgerline"\n', encoding="utf-8")

    Config.load = classmethod(  # type: ignore[assignment]
        lambda cls, *a, **k: Config(
            dictation=DictationConfig(
                pipeline=DictationPipelineConfig(
                    enabled=True,
                    stages=["kb-enricher"],  # runs offline (no runtime/LLM)
                    corrections_enabled=True,
                    journal_enabled=_STATE["journal_enabled"],
                ),
                runtime=LLMRuntimeConfig(),
            )
        )
    )
    reset_database()
    db = Database(tmp / "journal.db")
    server = MeetingWebServer(
        WebRuntimeCallbacks(
            on_bookmark=MagicMock(), on_stop=MagicMock(), get_state=MagicMock(return_value={})
        ),
        dictation_journal_repository=db.dictation_journal,
        dictation_corrections_repository=db.dictation_corrections,
    )
    client = TestClient(server.app)

    def dry(text: str):
        return client.post(
            "/api/dictation/dry-run", json={"utterance": text, "project_root": str(proj)}
        ).json()

    print("HoldSpeak dictation-journal dogfood\n")

    # 1. record — dry-run a few utterances.
    print("1. record")
    utterances = [
        "jot this down for the standup tomorrow",
        "send the weekly digest to the browser tab",
        "remind me to follow up with the vendor",
    ]
    for u in utterances:
        dry(u)
    listed = client.get("/api/dictation/journal").json()
    _check(listed["enabled"] is True, "journaling is on (local, default)")
    _check(listed["count"] == 3, f"three dry-runs journaled (count={listed['count']})")
    _check(
        all(it["source"] == "dry_run" for it in listed["items"]),
        "every entry tagged source=dry_run",
    )

    # 2. review — newest-first, with the per-stage latency captured.
    print("2. review")
    newest = listed["items"][0]
    _check(newest["transcript"] == utterances[-1], "newest-first ordering")
    _check("kb-enricher" in (newest["stage_ms"] or {}), "per-stage latency captured")

    # 3. correct in the moment — teach + flip the flag.
    print("3. correct (the moment of truth)")
    target_entry = next(i for i in listed["items"] if "browser" in i["transcript"])
    corr = client.post(
        f"/api/dictation/journal/{target_entry['id']}/correct",
        json={"kind": "target", "value": "browser"},
    ).json()
    _check(corr["corrected"] is True and corr["taught"] is True, "correction recorded + taught")
    after_correct = client.get("/api/dictation/journal").json()
    flagged = next(i for i in after_correct["items"] if i["id"] == target_entry["id"])
    _check(flagged["corrected"] is True, "journal entry flipped to corrected")

    # 4. replay — the routing visibly changed.
    print("4. replay (prove it learned)")
    replay = client.post(f"/api/dictation/journal/{target_entry['id']}/replay").json()
    _check(replay["after"]["target_profile"] == "browser", "replay routes to the corrected target")
    _check(replay["changed"] is True, "replay reports the routing changed")
    _check(
        db.dictation_journal.count() == 3,
        "replay created no new row (it's a preview)",
    )

    # 5. invariant — journal off ⇒ no row + byte-identical output.
    print("5. invariant: journal off ⇒ no new row, byte-identical output")
    on_result = dry("a brand new utterance to compare")
    count_after_on = db.dictation_journal.count()
    _STATE["journal_enabled"] = False
    off_result = dry("a brand new utterance to compare")
    _check(
        db.dictation_journal.count() == count_after_on,
        "journal-off wrote no row",
    )
    _check(
        on_result["final_text"] == off_result["final_text"],
        "typed output is byte-identical with journaling on vs off",
    )
    _STATE["journal_enabled"] = True

    print("\nJOURNAL DOGFOOD OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
