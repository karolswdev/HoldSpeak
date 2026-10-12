"""HS-48-02: integration tests for the inline "learned from N similar" signals.

The dry-run result, the journal entries, and the Memory list each carry a
truthful coverage count from the **one** matcher (the digest's Jaccard reach),
hidden when nothing matches, and the post-correction response states real
coverage + the `corrections_enabled` posture. No surface implies learning that
did not happen.
"""
from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

import holdspeak.config as config_module
from holdspeak.config import Config
from holdspeak.db import Database, reset_database
from holdspeak.plugins.dictation import assembly as assembly_module
from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks


class _StubRuntime:
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


@pytest.fixture
def persistent_db():
    temp_dir = Path(tempfile.mkdtemp())
    reset_database()
    database = Database(temp_dir / "trust.db")
    yield database
    reset_database()
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def settings_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    target = tmp_path / "config.json"
    monkeypatch.setattr(config_module, "CONFIG_FILE", target)
    return target


def _write_config(path: Path, *, pipeline=False, corrections=False) -> None:
    cfg = Config()
    cfg.dictation.pipeline.enabled = pipeline
    cfg.dictation.pipeline.corrections_enabled = corrections
    cfg.save(path=path)


def _client(database: Database) -> TestClient:
    server = MeetingWebServer(
        WebRuntimeCallbacks(
            on_bookmark=MagicMock(), on_stop=MagicMock(), get_state=MagicMock(return_value={})
        ),
        dictation_journal_repository=database.dictation_journal,
        dictation_corrections_repository=database.dictation_corrections,
    )
    return TestClient(server.app)


# ── Memory list ────────────────────────────────────────────────────────────

def test_corrections_list_carries_real_applications(
    persistent_db: Database, settings_path: Path
) -> None:
    """HS-176-02 (R3): the list's count is FIRINGS, not similar transcripts.

    It was `reach_for_gist` — a Jaccard reach that counted the teaching
    utterance itself, so a brand-new correction read `1 APPLIED` meaning zero
    applications. It is now the number of retained journal rows whose stored
    `corrections_applied` names the rule.
    """
    _write_config(settings_path)
    rule = persistent_db.dictation_corrections.record_correction(
        kind="intent", gist="follow up with sam about launch", value="action_item"
    )
    # Two similar transcripts the rule never fired on, and one it did.
    for t in ["follow up with sam about launch checklist", "follow up with sam about launch"]:
        persistent_db.dictation_journal.record(source="dictation", transcript=t, final_text=t)
    persistent_db.dictation_journal.record(
        source="dictation",
        transcript="water the plants",
        final_text="water the plants",
        corrections_applied=[rule.id],
    )
    body = _client(persistent_db).get("/api/dictation/corrections").json()
    item = next(i for i in body["items"] if i["id"] == rule.id)
    assert "similar" not in item  # reach_for_gist appears on no face
    assert item["applied"] == 1  # the one row it actually fired on


# ── journal entries ─────────────────────────────────────────────────────────

def test_journal_entries_carry_the_stored_firing_fact_not_a_would_match(
    persistent_db: Database, settings_path: Path
) -> None:
    """HS-176-03 (R2): the row's chip is a STORED per-run fact.

    `learning` / `best_correction_signal` was computed at read time over the
    whole journal, so it painted rows recorded BEFORE the correction was ever
    taught — and it flipped with the `corrections_enabled` toggle rather than
    with what happened. The row now carries `corrections_applied` (what fired on
    it) and `taught_from` (whether he taught FROM it), and nothing else.
    """
    rule = persistent_db.dictation_corrections.record_correction(
        kind="intent", gist="deploy the billing service", value="deploy_block"
    )
    fired = persistent_db.dictation_journal.record(
        source="dictation",
        transcript="deploy the billing service to staging",
        final_text="x",
        corrections_applied=[rule.id],
    )
    quiet = persistent_db.dictation_journal.record(
        source="dictation", transcript="buy more coffee", final_text="y"
    )

    for corrections in (False, True):
        _write_config(settings_path, corrections=corrections)
        rows = {i["id"]: i for i in _client(persistent_db).get("/api/dictation/journal").json()["items"]}
        assert all("learning" not in i for i in rows.values())
        # The stored fact does not move with the toggle.
        assert rows[fired.id]["corrections_applied"] == [rule.id]
        assert rows[quiet.id]["corrections_applied"] == []
        assert rows[fired.id]["taught_from"] is False


# ── dry-run result ───────────────────────────────────────────────────────────

def test_dry_run_result_carries_signal_when_a_correction_matches(
    persistent_db: Database, settings_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_config(settings_path, pipeline=True, corrections=True)
    monkeypatch.setattr(assembly_module, "build_runtime", lambda **_k: _StubRuntime())
    monkeypatch.setattr(assembly_module, "DEFAULT_GLOBAL_BLOCKS_PATH", settings_path.parent / "blocks.yaml")
    # A prior corrected utterance + a journal history it reaches.
    persistent_db.dictation_corrections.record_correction(
        kind="intent", gist="send the launch checklist", value="action_item"
    )
    persistent_db.dictation_journal.record(
        source="dictation", transcript="send the launch checklist to the team", final_text="x"
    )
    client = _client(persistent_db)
    # An utterance similar to the correction -> a signal; reach is over the past.
    matched = client.post("/api/dictation/dry-run", json={"utterance": "send the launch checklist now"}).json()
    assert matched["learning"] and matched["learning"]["value"] == "action_item"
    assert matched["learning"]["similar"] >= 1
    # An unrelated utterance -> quiet.
    other = client.post("/api/dictation/dry-run", json={"utterance": "what is the weather today"}).json()
    assert other["learning"] is None


def test_dry_run_no_signal_when_corrections_disabled(
    persistent_db: Database, settings_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_config(settings_path, pipeline=True, corrections=False)
    monkeypatch.setattr(assembly_module, "build_runtime", lambda **_k: _StubRuntime())
    monkeypatch.setattr(assembly_module, "DEFAULT_GLOBAL_BLOCKS_PATH", settings_path.parent / "blocks.yaml")
    persistent_db.dictation_corrections.record_correction(
        kind="intent", gist="send the launch checklist", value="action_item"
    )
    body = _client(persistent_db).post(
        "/api/dictation/dry-run", json={"utterance": "send the launch checklist now"}
    ).json()
    assert body["learning"] is None  # disabled -> byte-identical, no claim


# ── post-correction confirmation ─────────────────────────────────────────────

def test_correct_response_states_real_coverage_and_posture(
    persistent_db: Database, settings_path: Path
) -> None:
    _write_config(settings_path, corrections=True)
    # Two similar utterances; correct the first.
    a = persistent_db.dictation_journal.record(
        source="dictation", transcript="follow up with priya about the rollout", final_text="x"
    )
    persistent_db.dictation_journal.record(
        source="dictation", transcript="follow up with priya about rollout", final_text="y"
    )
    resp = _client(persistent_db).post(
        f"/api/dictation/journal/{a.id}/correct", json={"kind": "intent", "value": "action_item"}
    ).json()
    assert resp["taught"] is True
    assert resp["similar"] == 2  # both rollout utterances are within reach
    assert resp["enabled"] is True


def test_correct_response_secret_filtered_teaches_nothing(
    persistent_db: Database, settings_path: Path
) -> None:
    _write_config(settings_path, corrections=True)
    # A secret-like transcript: the store rejects it, so nothing is taught.
    rec = persistent_db.dictation_journal.record(
        source="dictation", transcript="my api key is sk-ABCDEF1234567890ABCDEF12", final_text="x"
    )
    resp = _client(persistent_db).post(
        f"/api/dictation/journal/{rec.id}/correct", json={"kind": "intent", "value": "action_item"}
    ).json()
    assert resp["taught"] is False
    assert resp["similar"] == 0  # nothing taught -> no coverage claimed


# ── page content / global CSS guard ──────────────────────────────────────────

def test_trust_chip_css_is_global(persistent_db: Database, settings_path: Path) -> None:
    """Trust feedback is React-owned and lands in the ONE footer receipt
    bar (HS-111-02): the toast-banner species (InlineMessage/StatusPill)
    must never come back to this program.

    HS-132-12: HS-129-05 replaced Speak's own `speak-receipt` bar with the
    frame-owned SurfaceFooter receipt slot, and HS-117-08 moved the footer
    into cores/dictation/Readiness.tsx. The channel is still ONE, and the
    banner species is still barred from the whole deck.
    """
    repo = Path(__file__).resolve().parents[2]
    shell = (repo / "web/src/pages/cores/DictationCore.tsx").read_text()
    footer = (repo / "web/src/pages/cores/dictation/Readiness.tsx").read_text()
    deck_dir = repo / "web/src/pages/cores/dictation"
    deck = "\n".join(
        [shell]
        + [
            source.read_text()
            for source in sorted(deck_dir.glob("*.ts*"))
            if not source.name.endswith(".test.tsx")
        ]
    )
    # The ONE channel: every sub-component announces through the context,
    # and the announcement lands in the frame's single receipt slot.
    assert "ReceiptContext" in shell
    assert "ReceiptContext" in (repo / "web/src/pages/cores/dictation/shared.ts").read_text()
    assert "SurfaceFooter" in footer and "receipt={receiptSlot" in footer
    assert "InlineMessage" not in deck and "StatusPill" not in deck
    assert "dangerouslySetInnerHTML" not in deck
