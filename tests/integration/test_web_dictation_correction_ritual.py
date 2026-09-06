"""HS-48-03: the one-tap right/wrong correction ritual.

The React ritual keeps "Right" client-only and lets "Wrong" disclose the
existing teach path. These assertions pin the typed source contract and
exercise the backend write it uses.
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
from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

_REPO = Path(__file__).resolve().parents[2]
_DECK_DIR = _REPO / "web/src/pages/cores/dictation"
# HS-132-12: HS-117-08 decomposed the cockpit — the ritual lived in
# dictation/ResultPanel.tsx and the wire it posts to in dictation/useSpeakDeck.ts.
# HS-176-04: 170 rebuilt the Speak face and left ResultPanel.tsx an orphan
# (not in the barrel, zero importers); it is parked under _parked/ (owner
# ruling: never delete).  The RESULT row and its teach path live in
# dictation/SpeakFace.tsx now, so this fence MOVES with the behaviour it
# pins rather than losing an assertion.
_RITUAL = _DECK_DIR / "SpeakFace.tsx"
_DECK_WIRE = _DECK_DIR / "useSpeakDeck.ts"


def _ritual_source() -> str:
    return _RITUAL.read_text()


def _wire_source() -> str:
    return _DECK_WIRE.read_text()


def _dictation_script() -> str:
    """The whole Dictation program: the shell plus every sub-component."""
    parts = [(_REPO / "web/src/pages/cores/DictationCore.tsx").read_text()]
    for source in sorted(_DECK_DIR.glob("*.ts*")):
        if source.name.endswith(".test.tsx"):
            continue
        parts.append(source.read_text())
    return "\n".join(parts)


@pytest.fixture
def settings_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    target = tmp_path / "config.json"
    monkeypatch.setattr(config_module, "CONFIG_FILE", target)
    return target


@pytest.fixture
def persistent_db():
    temp_dir = Path(tempfile.mkdtemp())
    reset_database()
    database = Database(temp_dir / "ritual.db")
    yield database
    reset_database()
    shutil.rmtree(temp_dir, ignore_errors=True)


def _client(database: Database) -> TestClient:
    server = MeetingWebServer(
        WebRuntimeCallbacks(
            on_bookmark=MagicMock(), on_stop=MagicMock(), get_state=MagicMock(return_value={})
        ),
        dictation_journal_repository=database.dictation_journal,
        dictation_corrections_repository=database.dictation_corrections,
    )
    return TestClient(server.app)


# ── the ritual ships + is wired into both surfaces ───────────────────────────

def test_ritual_component_is_shipped() -> None:
    ritual = _ritual_source()
    # HS-111-01 renamed the affirm verb Right → OK; the one-tap ritual,
    # the disclose path, and the teach POST are unchanged.
    for marker in ("Marked OK", "Wrong", "Correct this result", "Teach correction"):
        assert marker in ritual, marker
    wire = _wire_source()
    assert "/api/dictation/journal/" in wire and "/correct" in wire
    # HS-176-02: the fallback route is the one a run with no journal_id
    # takes (journal off, no repository, unknown source) — it is not dead
    # code and it is not allowed to quietly disappear.
    assert "/api/dictation/corrections" in wire


def test_teach_row_offers_the_three_correction_kinds() -> None:
    """HS-176-02: FIELD cycles TEXT · INTENT · TARGET, TEXT the default.

    The 170 row took FREE TEXT for kinds whose value must be a member of
    a closed set, so nothing the owner typed ever fired. The kinds are a
    pick now, and the words mistake — his actual Tuesday — has a field.
    """
    fields = (_DECK_DIR / "shared.ts").read_text()
    assert "CORRECTION_FIELDS" in fields
    for token in ('"TEXT"', '"INTENT"', '"TARGET"'):
        assert token in fields, token
    wire = _wire_source()
    # TEXT is the default: the Tuesday mistake is a words mistake.
    assert 'useState("text")' in wire
    ritual = _ritual_source()
    assert "FIELD" in ritual
    # the routing kinds are a PICK over the real enum, never a typed id
    assert "correctionOptions" in ritual and "correctionOptions" in wire
    # the label sources: the readiness overrides and the loaded blocks
    assert "overrides" in wire
    assert "/api/dictation/blocks" in wire


def test_teach_receipts_are_tokens_not_a_sentence() -> None:
    """HS-176-02 (rule A.3): the receipt is a token pair, never prose.

    The retired line is `useSpeakDeck.ts`'s "Taught · reaches similar
    dictations" — a sentence on the footer. What replaces it names what
    was stored, or names the refusal.
    """
    wire = _wire_source()
    shared = (_DECK_DIR / "shared.ts").read_text()
    assert "reaches similar dictations" not in wire
    assert '"TAUGHT"' in wire
    for token in ("NO CHANGE", "REFUSED · SECRET", "REFUSED · ONE WORD"):
        assert token in shared, token
    # R4: `recorded` is the key both routes answer with; `taught` is the
    # journal route's long-standing mirror. The face reads either.
    assert "reply.recorded ?? reply.taught" in wire
    # rule A.7 — one word, one meaning: LEARNED is never a receipt.
    assert "LEARNED" not in wire and "LEARNED" not in _ritual_source()
    # A.7 again — the name is said ONCE per face: the outcome lives in
    # the RESULT row's receipt and is never mirrored into the footer, so
    # `teach()` announces nothing at all.
    teach_body = wire.split("const teach = async () => {", 1)[1].split(
        "\n  };", 1
    )[0]
    assert "announce(" not in teach_body, teach_body


def test_applied_chip_reads_the_stored_fact_only() -> None:
    """HS-176-02 (R2/Article VI): the chip is a per-run stored fact.

    `learning` / `best_correction_signal` is a READ-TIME "would match"
    over the whole journal — it paints rows recorded before the
    correction existed. The chip and its well render from the run's own
    `corrections_applied` ids, resolved against the store.
    """
    wire = _wire_source()
    ritual = _ritual_source()
    assert "corrections_applied" in wire
    assert "best_correction_signal" not in wire and "learning" not in wire
    assert "APPLIED" in ritual
    # N2 — the TEXT well pre-fills from the RAW transcript, because that
    # is the string the rule is applied to (pipeline.py:98).
    assert "raw_text" in wire


def test_ritual_is_wired_into_dry_run_result() -> None:
    ritual = _ritual_source()
    assert 'setVerdict("right")' in ritual and 'setVerdict("wrong")' in ritual
    assert "journal_id" in _wire_source()


def test_ritual_is_focus_safe() -> None:
    # The standing dictation invariant: zero programmatic focus theft.
    assert ".focus()" not in _dictation_script()


def test_ritual_uses_shared_react_controls() -> None:
    # HS-111-08: no bespoke control species — the ritual composes the kit.
    # HS-176-04: on the rebuilt face the teach row is disclosed by the
    # verdict itself (a conditional role="group" region), not by the kit's
    # FoldGadget, so the FoldGadget marker is replaced by the species the
    # row actually composes.  The intent is unchanged: shared kit only,
    # no raw control and no bespoke disclosure.
    # HS-176-02: the TEXT well is the kit's PadGadget, not StringGadget.
    # The value he EDITS must WRAP rather than truncate (design P2 / the
    # phone board) and an `<input>` cannot wrap, so the row composes the
    # kit's one textarea face at a single grown row. Same intent, same
    # kit, one species swapped for the one that can hold the sentence.
    ritual = _ritual_source()
    for species in ("<Button", "<CycleGadget", "<PadGadget"):
        assert species in ritual, species
    for bespoke in ("<button", "<details", "<summary"):
        assert bespoke not in ritual, bespoke
    assert "dangerouslySetInnerHTML" not in _dictation_script()


def test_dry_run_moment_host_present(persistent_db: Database, settings_path: Path) -> None:
    Config().save(path=settings_path)
    response = _client(persistent_db).get("/dictation")
    assert '<div id="root"></div>' in response.text
    assert "Pipeline result" in _ritual_source()
    assert "/api/dictation/dry-run" in _wire_source()
    assert "autofocus" not in _dictation_script().lower()


# ── the path the ritual posts to still teaches (one decision, real write) ────

def test_ritual_correct_path_teaches_and_marks(persistent_db: Database, settings_path: Path) -> None:
    cfg = Config()
    cfg.dictation.pipeline.corrections_enabled = True
    cfg.save(path=settings_path)
    rec = persistent_db.dictation_journal.record(
        source="dictation", transcript="follow up with sam about launch", final_text="x"
    )
    # The "Wrong block -> action_item" one-tap path is a single POST.
    resp = _client(persistent_db).post(
        f"/api/dictation/journal/{rec.id}/correct", json={"kind": "intent", "value": "action_item"}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["corrected"] is True and body["taught"] is True
    # the entry is now flagged corrected (the ritual hides the ask for these)
    assert persistent_db.dictation_journal.get(rec.id).corrected is True
    # and the correction landed in the store (teachable across restarts)
    stored = persistent_db.dictation_corrections.recent_corrections()
    assert any(r.kind == "intent" and r.value == "action_item" for r in stored)


# ── HS-101 B3: edit the transcript record in place (the smallest write) ──────

def test_journal_transcript_edit_in_place(persistent_db: Database, settings_path: Path) -> None:
    Config().save(path=settings_path)
    rec = persistent_db.dictation_journal.record(
        source="dictation", transcript="ship the native winners brief", final_text="x"
    )
    client = _client(persistent_db)
    resp = client.put(
        f"/api/dictation/journal/{rec.id}", json={"transcript": "ship the Native Innards brief"}
    )
    assert resp.status_code == 200 and resp.json()["updated"] is True
    assert (
        persistent_db.dictation_journal.get(rec.id).transcript
        == "ship the Native Innards brief"
    )
    # an emptied record refuses rather than blanking (Article VI)
    refuse = client.put(f"/api/dictation/journal/{rec.id}", json={"transcript": "   "})
    assert refuse.status_code == 422
    # a missing entry names itself
    gone = client.put("/api/dictation/journal/999999", json={"transcript": "y"})
    assert gone.status_code == 404
    # editing never fakes a correction: the taught act stays separate
    assert persistent_db.dictation_journal.get(rec.id).corrected is False
