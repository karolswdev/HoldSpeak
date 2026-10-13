"""HS-48-01: a real-speech e2e for the learning loop's digest.

The phase's pitch is "it gets better at your voice, on your machine, and shows
you the proof." This test proves that loop with **actual synthesized speech**,
end to end through the same HTTP endpoints the browser uses:

    say -> per-utterance .wav -> Whisper (Transcriber) -> /api/dictation/dry-run
    (journals each run) -> /api/dictation/journal/{id}/correct (teaches) ->
    /api/dictation/learning-digest (the "What HoldSpeak learned" view)

Only the LLM is stood in for by a stub runtime — it does not touch the digest's
numbers, which come from the Jaccard matcher over the **real transcribed**
journal transcripts. So the "learned from N similar" count this asserts is the
genuine reach of a correction over speech the machine actually heard.

Opt-in (it shells out to macOS `say` and pulls the Whisper "base" model):

    HOLDSPEAK_SPOKEN_DICTATION_E2E=1 uv run pytest -q \
        tests/e2e/test_dictation_learning_digest_spoken_e2e.py -s
"""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest

if not os.environ.get("HOLDSPEAK_SPOKEN_DICTATION_E2E"):
    pytest.skip(
        "opt-in: set HOLDSPEAK_SPOKEN_DICTATION_E2E=1 to run the spoken-dictation "
        "learning-digest e2e (uses macOS `say` + the Whisper base model)",
        allow_module_level=True,
    )

# Two utterances that overlap heavily (the matcher should link them) plus one
# unrelated line that must stay out of reach. Kept plain so Whisper is reliable.
UTTERANCES = [
    "send the launch checklist to the team",
    "send the launch checklist to everyone",
    "remember to book the conference room",
]
VOICE = "Samantha"


class _StubRuntime:
    """Stands in for the local model so no LLM/model download is needed. It does
    not affect the digest — counts come from the transcribed journal."""

    backend = "stub"

    def load(self) -> None:  # pragma: no cover - trivial
        pass

    def info(self) -> dict:  # pragma: no cover - trivial
        return {"backend": "stub"}

    def classify(self, prompt, schema, *, max_tokens=128, temperature=0.0):
        block_id = schema.block_ids[0] if getattr(schema, "block_ids", None) else None
        return {"matched": block_id is not None, "block_id": block_id, "confidence": 0.9, "extras": {}}

    def rewrite(self, prompt, *, max_tokens=512, temperature=0.15):  # pragma: no cover
        return "rewritten"


def _say_to_wav(line: str, out_path: Path) -> None:
    subprocess.run(
        ["say", "-v", VOICE, "--data-format=LEI16@16000", "-o", str(out_path), line],
        check=True,
    )


def test_spoken_dictation_drives_the_learning_digest(tmp_path: Path) -> None:
    if shutil.which("say") is None:
        pytest.skip("macOS `say` not available")
    wavfile = pytest.importorskip("scipy.io.wavfile", reason="scipy required")
    np = pytest.importorskip("numpy")

    import holdspeak.config as config_module
    from holdspeak.config import Config
    from holdspeak.db import Database, reset_database
    from holdspeak.plugins.dictation import assembly as assembly_module
    from holdspeak.transcribe import Transcriber
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks
    from fastapi.testclient import TestClient

    # --- temp config: pipeline + journal + corrections all on ---------------
    config_module.CONFIG_FILE = tmp_path / "config.json"
    cfg = Config()
    cfg.dictation.pipeline.enabled = True
    cfg.dictation.pipeline.corrections_enabled = True
    cfg.save(path=config_module.CONFIG_FILE)
    assembly_module.DEFAULT_GLOBAL_BLOCKS_PATH = tmp_path / "global-blocks.yaml"
    original_build_runtime = assembly_module.build_runtime
    assembly_module.build_runtime = lambda **_kwargs: _StubRuntime()

    reset_database()
    db = Database(tmp_path / "spoken.db")

    try:
        # --- 1. say -> wav -> 2. Whisper -> real transcripts ----------------
        transcriber = Transcriber(model_name="base")
        transcripts: list[str] = []
        for idx, line in enumerate(UTTERANCES):
            wav_path = tmp_path / f"utt_{idx}.wav"
            _say_to_wav(line, wav_path)
            sr, audio = wavfile.read(wav_path)
            if audio.dtype == np.int16:
                audio = audio.astype(np.float32) / 32768.0
            text = transcriber.transcribe(audio.astype("float32")).strip()
            assert text, f"empty transcription for {line!r}"
            transcripts.append(text)
            print(f"[e2e] said {line!r} -> heard {text!r}")

        server = MeetingWebServer(
            WebRuntimeCallbacks(
                on_bookmark=MagicMock(), on_stop=MagicMock(), get_state=MagicMock(return_value={})
            ),
            dictation_journal_repository=db.dictation_journal,
            dictation_corrections_repository=db.dictation_corrections,
        )
        client = TestClient(server.app)

        # --- 3. dry-run each transcript through the real HTTP path (journals) -
        journal_ids: list[int] = []
        for text in transcripts:
            r = client.post("/api/dictation/dry-run", json={"utterance": text})
            assert r.status_code == 200, r.text
            jid = r.json().get("journal_id")
            assert jid is not None, "dry-run did not journal the run"
            journal_ids.append(int(jid))

        # --- 4. correct the FIRST launch utterance (teach intent -> block) ---
        r = client.post(
            f"/api/dictation/journal/{journal_ids[0]}/correct",
            json={"kind": "intent", "value": "action_item"},
        )
        assert r.status_code == 200, r.text
        assert r.json()["corrected"] is True
        assert r.json()["taught"] is True, "spoken correction was not taught"

        # --- 5. the digest must reflect the real spoken loop ----------------
        digest = client.get("/api/dictation/learning-digest?window=all").json()
        print(f"[e2e] digest totals: {digest['totals']}")
        print(f"[e2e] correction reach: {digest['corrections'][0]}")

        assert digest["enabled"] is True  # corrections actually route
        assert digest["totals"]["corrections_made"] == 1
        assert digest["totals"]["dictations_corrected"] == 1
        assert digest["by_kind"]["intent"] == 1
        assert digest["by_block"] == [{"block_id": "action_item", "count": 1}]
        # The two near-identical launch utterances are within reach of the
        # correction; the conference-room line is not. This is the honest count
        # over speech the machine actually heard.
        assert digest["corrections"][0]["similar"] >= 2, (
            f"expected the two launch utterances within reach; "
            f"heard {transcripts!r}, reach {digest['corrections'][0]['similar']}"
        )
        assert digest["totals"]["similar_nudged"] >= 2
    finally:
        assembly_module.build_runtime = original_build_runtime
        reset_database()
