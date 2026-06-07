#!/usr/bin/env python3
"""HS-48-05 dogfood: the visible learning loop, end to end, no mic.

Drives the same HTTP endpoints the browser calls to prove the loop:

  1. dictate (dry-run) a few utterances -> each is journaled,
  2. read the "What HoldSpeak learned" digest -> honest, zeroed at the start,
  3. correct one journaled run in the moment -> it teaches (real coverage),
  4. read the digest again -> it reflects the correction with a real
     "learned from N similar" count from the same Jaccard matcher that routes.

Every number comes from `holdspeak/dictation_learning.py` over the journal +
corrections; nothing is hand-computed. No microphone, no real LLM: the runtime is
a deterministic stub (the same pattern the dry-run integration tests use), and a
temp config + temp DB keep the developer's real state untouched.

    .venv/bin/python scripts/dogfood_learning_loop.py
    .venv/bin/python scripts/dogfood_learning_loop.py <transcript.txt>
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))

# Two utterances overlap heavily (the matcher links them); two do not.
UTTERANCES = [
    "follow up with sam about the launch checklist",
    "follow up with sam about the launch plan",
    "remember to water the office plants",
    "write a quick note about the retry worker",
]


class _StubRuntime:
    """Deterministic stand-in for the local model (no LLM needed)."""

    backend = "stub"

    def load(self) -> None:
        pass

    def info(self) -> dict:
        return {"backend": "stub"}

    def classify(self, prompt, schema, *, max_tokens=128, temperature=0.0):
        block_id = schema.block_ids[0] if getattr(schema, "block_ids", None) else None
        return {"matched": block_id is not None, "block_id": block_id, "confidence": 0.9, "extras": {}}

    def rewrite(self, prompt, *, max_tokens=512, temperature=0.15):
        return "rewritten"


def main(argv: list[str]) -> int:
    from fastapi.testclient import TestClient

    import holdspeak.config as config_module
    from holdspeak.config import Config
    from holdspeak.db import Database, reset_database
    from holdspeak.plugins.dictation import assembly as assembly_module
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    out_path = Path(argv[0]) if argv else None
    lines: list[str] = []

    def say(msg: str) -> None:
        print(msg)
        lines.append(msg)

    tmp = Path(tempfile.mkdtemp())
    config_module.CONFIG_FILE = tmp / "config.json"
    cfg = Config()
    cfg.dictation.pipeline.enabled = True
    cfg.dictation.pipeline.corrections_enabled = True
    cfg.save(path=config_module.CONFIG_FILE)
    assembly_module.DEFAULT_GLOBAL_BLOCKS_PATH = tmp / "global-blocks.yaml"
    original_build_runtime = assembly_module.build_runtime
    assembly_module.build_runtime = lambda **_kwargs: _StubRuntime()

    reset_database()
    db = Database(tmp / "loop.db")

    say("HS-48-05 dogfood - the visible learning loop, end to end (no mic)")
    say("")
    try:
        server = MeetingWebServer(
            WebRuntimeCallbacks(
                on_bookmark=MagicMock(), on_stop=MagicMock(), get_state=MagicMock(return_value={})
            ),
            dictation_journal_repository=db.dictation_journal,
            dictation_corrections_repository=db.dictation_corrections,
        )
        client = TestClient(server.app)

        # 1. dictate (dry-run) -> each run is journaled.
        journal_ids: list[int] = []
        for text in UTTERANCES:
            r = client.post("/api/dictation/dry-run", json={"utterance": text})
            assert r.status_code == 200, r.text
            jid = r.json().get("journal_id")
            assert jid is not None, "dry-run did not journal the run"
            journal_ids.append(int(jid))
        say(f"1. dictated {len(UTTERANCES)} utterances (dry-run); all journaled")

        # 2. the digest starts honest: no corrections yet.
        d0 = client.get("/api/dictation/learning-digest?window=all").json()
        say("2. digest before correcting:")
        say(f"   corrections_made={d0['totals']['corrections_made']}  "
            f"dictations_corrected={d0['totals']['dictations_corrected']}  "
            f"similar_nudged={d0['totals']['similar_nudged']}")
        assert d0["totals"]["corrections_made"] == 0
        assert d0["totals"]["similar_nudged"] == 0

        # 3. correct one in the moment -> it teaches, with real coverage.
        target_id = journal_ids[0]
        r = client.post(
            f"/api/dictation/journal/{target_id}/correct",
            json={"kind": "intent", "value": "action_item"},
        )
        assert r.status_code == 200, r.text
        fix = r.json()
        say("")
        say(f"3. corrected the launch-checklist utterance -> intent: action_item")
        say(f"   taught={fix['taught']}  enabled={fix['enabled']}  similar={fix['similar']}")
        assert fix["taught"] is True
        assert fix["similar"] == 2  # the two launch utterances are within reach

        # 4. the digest now reflects it, honestly.
        d1 = client.get("/api/dictation/learning-digest?window=all").json()
        corr = d1["corrections"][0]
        say("")
        say("4. digest after correcting:")
        say(f"   corrections_made={d1['totals']['corrections_made']}  "
            f"dictations_corrected={d1['totals']['dictations_corrected']}  "
            f"similar_nudged={d1['totals']['similar_nudged']}")
        say(f"   by_block={d1['by_block']}")
        say(f"   correction reach: '{corr['gist']}' -> {corr['value']} "
            f"(learned from {corr['similar']} similar)")
        assert d1["totals"]["corrections_made"] == 1
        assert d1["totals"]["dictations_corrected"] == 1
        assert d1["totals"]["similar_nudged"] == 2
        assert d1["by_block"] == [{"block_id": "action_item", "count": 1}]
        assert corr["similar"] == 2

        say("")
        say("PASS: dictate -> correct in one call -> the digest shows honest, real "
            "'learned from N similar' counts from the matcher that nudges routing.")
    finally:
        assembly_module.build_runtime = original_build_runtime
        reset_database()

    if out_path is not None:
        out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"\nWrote transcript: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
