"""HS-176-02: the `text` correction kind, its seam, and the journal facts.

The Tuesday mistake is a WORDS mistake ("postgress" for PostgreSQL), which the
routing-only correction wire could not express. This file proves the third
kind end to end on the backend: the deterministic matcher's boundaries, the
transcript seam inside `DictationPipeline.run`, the store's new return and its
named refusals, the additive `corrections_applied` journal column, and the
`dictation.journal.entry` bus frame built from the stored row.
"""

from __future__ import annotations

import shutil
import sqlite3
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

from holdspeak.db import Database, reset_database
from holdspeak.plugins.dictation.contracts import IntentTag, StageResult, Utterance
from holdspeak.plugins.dictation.corrections import (
    CORRECTION_KINDS,
    Correction,
    CorrectionStore,
    apply_text_corrections,
    best_match_in,
    normalize_text_key,
)
from holdspeak.plugins.dictation.journal import (
    DictationJournalRecorder,
    passthrough_run,
)
from holdspeak.plugins.dictation.pipeline import DictationPipeline, PipelineRun


def _rule(key: str, value: str, *, seq: int = 1, rule_id: int | None = 1) -> Correction:
    return Correction(
        kind="text", key=normalize_text_key(key), value=value,
        sequence=seq, correction_id=rule_id,
    )


def _utt(text: str) -> Utterance:
    return Utterance(
        raw_text=text,
        audio_duration_s=1.0,
        transcribed_at=datetime(2026, 9, 6, tzinfo=timezone.utc),
    )


class _Stage:
    """A stage that records the utterance it was handed."""

    def __init__(self, sid: str = "probe", *, seen: list[str] | None = None,
                 intent: IntentTag | None = None) -> None:
        self.id = sid
        self.version = "0.1.0"
        self.requires_llm = False
        self.seen = seen if seen is not None else []
        self._intent = intent

    def run(self, utt: Utterance, prior: list[StageResult]) -> StageResult:
        self.seen.append(utt.raw_text)
        return StageResult(
            stage_id=self.id, text=utt.raw_text, intent=self._intent, elapsed_ms=0.0
        )


# ── the deterministic matcher ─────────────────────────────────────────────


def test_kinds_carry_text():
    assert CORRECTION_KINDS == ("intent", "target", "text")


def test_exact_phrase_replaces_and_names_the_rule():
    text, applied = apply_text_corrections(
        "postgress needs a version bump", [_rule("postgress", "PostgreSQL", rule_id=7)]
    )
    assert text == "PostgreSQL needs a version bump"
    assert applied == (7,)


@pytest.mark.parametrize(
    "source, expected",
    [
        ("postgress, the database", "PostgreSQL, the database"),   # trailing comma
        ("we use postgress.", "we use PostgreSQL."),               # trailing period
        ("postgress", "PostgreSQL"),                                # both edges
        ("about postgress", "about PostgreSQL"),                    # end of string
        ("(postgress)", "(PostgreSQL)"),                            # bracketed
    ],
)
def test_boundary_is_non_alphanumeric_or_string_edge(source, expected):
    text, applied = apply_text_corrections(source, [_rule("postgress", "PostgreSQL")])
    assert text == expected
    assert applied == (1,)


@pytest.mark.parametrize("source", ["postgressive tooling", "the postgresses", "xpostgress"])
def test_never_fires_inside_a_longer_word(source):
    text, applied = apply_text_corrections(source, [_rule("postgress", "PostgreSQL")])
    assert text == source
    assert applied == ()


def test_case_preserved_on_the_first_letter_only():
    rule = _rule("postgress", "postgreSQL")
    assert apply_text_corrections("Postgress ships", [rule])[0] == "PostgreSQL ships"
    assert apply_text_corrections("postgress ships", [rule])[0] == "postgreSQL ships"
    # An uppercase LATER letter in the heard text changes nothing: only the
    # first letter is preserved, the rest is written exactly as taught.
    assert apply_text_corrections("postGRESS ships", [rule])[0] == "postgreSQL ships"


def test_longest_key_wins_and_both_rules_may_apply():
    rules = [
        _rule("queue for", "Q4", seq=1, rule_id=1),
        _rule("queue", "line", seq=2, rule_id=2),
    ]
    text, applied = apply_text_corrections("the queue for the build", rules)
    # The longer key consumed the phrase; the shorter one no longer matches.
    assert text == "the Q4 the build"
    assert applied == (1,)
    # Both fire when both have somewhere to fire.
    text, applied = apply_text_corrections("the queue for a queue", rules)
    assert text == "the Q4 a line"
    assert sorted(applied) == [1, 2]


def test_match_tolerates_whitespace_runs():
    text, _ = apply_text_corrections("the queue\n  for the build", [_rule("queue for", "Q4")])
    assert text == "the Q4 the build"


def test_every_occurrence_is_replaced():
    text, applied = apply_text_corrections(
        "postgress and postgress", [_rule("postgress", "PostgreSQL")]
    )
    assert text == "PostgreSQL and PostgreSQL"
    assert applied == (1,)


def test_a_rule_without_a_durable_id_still_fires_but_names_nothing():
    text, applied = apply_text_corrections(
        "postgress", [_rule("postgress", "PostgreSQL", rule_id=None)]
    )
    assert text == "PostgreSQL"
    assert applied == ()  # no row exists to name; no id is ever fabricated


def test_routing_corrections_are_not_text_rules():
    routing = Correction(kind="target", key="postgress", value="browser", sequence=1)
    text, applied = apply_text_corrections("postgress", [routing])
    assert (text, applied) == ("postgress", ())


def test_best_match_in_is_untouched_and_still_serves_routing():
    store = CorrectionStore()
    store.record("target", "open the terminal", "terminal_shell")
    match = best_match_in(store.snapshot(), "target", "open the terminal", min_similarity=0.5)
    assert match is not None and match.value == "terminal_shell"
    # …and never answers for the text kind.
    assert best_match_in(store.snapshot(), "text", "open the terminal") is None


# ── the store: storage shape, the return, the named refusals ──────────────


def test_text_key_is_stored_stripped_and_lowercased():
    store = CorrectionStore()
    assert bool(store.record("text", "  Postgress,  ", " PostgreSQL. ")) is True
    stored = store.recent("text")[0]
    assert stored.key == "postgress"
    assert stored.value == "PostgreSQL"


def test_one_token_gist_is_refused_by_name_for_routing_kinds_only():
    store = CorrectionStore()
    assert store.record("intent", "deploy", "deploy_block").refusal == "one_word"
    assert store.record("target", "deploy", "browser").refusal == "one_word"
    assert len(store) == 0
    # A one-word key is legal for the exact-phrase kind.
    assert bool(store.record("text", "postgress", "PostgreSQL")) is True
    assert len(store) == 1


def test_secret_like_text_correction_is_refused_on_either_side():
    store = CorrectionStore()
    secret = "my key is sk-abcdef0123456789abcd"
    assert store.record("text", secret, "safe words").refusal == "secret"
    assert store.record("text", "safe words", secret).refusal == "secret"
    assert len(store) == 0


# ── durability ────────────────────────────────────────────────────────────


@pytest.fixture
def repo():
    temp_dir = Path(tempfile.mkdtemp())
    reset_database()
    database = Database(temp_dir / "store.db")
    yield database.dictation_corrections
    reset_database()
    shutil.rmtree(temp_dir, ignore_errors=True)


def test_text_correction_persists_and_rehydrates_with_its_id(repo):
    store = CorrectionStore(repository=repo)
    outcome = store.record("text", "Postgress", "PostgreSQL")
    assert outcome.correction_id is not None
    # The ring entry knows its durable id straight away…
    assert store.recent("text")[0].correction_id == outcome.correction_id
    # …and a fresh store (a restarted hub) rehydrates it with the same id.
    revived = CorrectionStore(repository=repo)
    rule = revived.recent("text")[0]
    assert (rule.kind, rule.key, rule.value) == ("text", "postgress", "PostgreSQL")
    assert rule.correction_id == outcome.correction_id
    assert apply_text_corrections("postgress ships", revived.snapshot()) == (
        "PostgreSQL ships",
        (outcome.correction_id,),
    )


# ── the pipeline seam ─────────────────────────────────────────────────────


def test_every_stage_receives_the_corrected_utterance():
    seen: list[str] = []
    stage = _Stage(seen=seen)
    pipeline = DictationPipeline(
        [stage], corrections=[_rule("postgress", "PostgreSQL", rule_id=3)]
    )
    run = pipeline.run(_utt("postgress needs a bump"))
    assert seen == ["PostgreSQL needs a bump"]
    assert run.final_text == "PostgreSQL needs a bump"
    assert run.corrections_applied == (3,)


def test_the_text_kind_is_not_a_stage():
    stage = _Stage()
    pipeline = DictationPipeline([stage], corrections=[_rule("postgress", "PostgreSQL")])
    run = pipeline.run(_utt("postgress"))
    # One stage in, one StageResult out — the correction adds no stage record
    # and therefore no `stage_ms` entry.
    assert [r.stage_id for r in run.stage_results] == ["probe"]
    from holdspeak.plugins.dictation.journal import extract_stage_ms

    stage_ms, _ = extract_stage_ms(run)
    assert set(stage_ms) == {"probe"}


def test_pipeline_without_corrections_is_unchanged():
    seen: list[str] = []
    run = DictationPipeline([_Stage(seen=seen)]).run(_utt("postgress needs a bump"))
    assert seen == ["postgress needs a bump"]
    assert run.corrections_applied == ()


def test_pipeline_run_field_carries_a_default():
    run = PipelineRun(
        final_text="x", stage_results=[], intent=None, warnings=[],
        total_elapsed_ms=0.0, short_circuited=False,
    )
    assert run.corrections_applied == ()


def test_the_routing_nudge_names_its_rule():
    nudged = IntentTag(
        matched=True, block_id="deploy_block", confidence=0.85,
        raw_label="deploy", extras={"corrected": True},
    )
    routing = Correction(
        kind="intent", key="ship the release today", value="deploy_block",
        sequence=1, correction_id=9,
    )
    pipeline = DictationPipeline([_Stage(intent=nudged)], corrections=[routing])
    run = pipeline.run(_utt("ship the release today"))
    assert run.corrections_applied == (9,)


def test_an_unnudged_intent_names_nothing():
    plain = IntentTag(matched=True, block_id="deploy_block", confidence=0.9, raw_label="deploy")
    routing = Correction(
        kind="intent", key="ship the release today", value="deploy_block",
        sequence=1, correction_id=9,
    )
    pipeline = DictationPipeline([_Stage(intent=plain)], corrections=[routing])
    assert pipeline.run(_utt("ship the release today")).corrections_applied == ()


# ── the journal column, the count, and the bus frame ──────────────────────


@pytest.fixture
def journal_repo():
    temp_dir = Path(tempfile.mkdtemp())
    reset_database()
    database = Database(temp_dir / "journal.db")
    yield database.dictation_journal
    reset_database()
    shutil.rmtree(temp_dir, ignore_errors=True)


def test_corrections_applied_round_trips_as_a_json_id_list(journal_repo):
    stored = journal_repo.record(
        source="dictation", transcript="postgress", final_text="PostgreSQL",
        corrections_applied=[4, 7],
    )
    assert stored.corrections_applied == [4, 7]
    assert journal_repo.get(stored.id).corrections_applied == [4, 7]
    # The default is an empty list, never NULL.
    bare = journal_repo.record(source="dictation", transcript="a", final_text="a")
    assert bare.corrections_applied == []
    assert bare.corrected is False


def test_count_applied_counts_firings_not_resemblance(journal_repo):
    journal_repo.record(source="dictation", transcript="teaching one", final_text="teaching one")
    journal_repo.record(source="dictation", transcript="x", final_text="x", corrections_applied=[4])
    journal_repo.record(source="dictation", transcript="y", final_text="y", corrections_applied=[4, 12])
    assert journal_repo.count_applied(4) == 2
    assert journal_repo.count_applied(12) == 1
    # `12` is not a hit for `1` — the ids are compared, not the JSON text.
    assert journal_repo.count_applied(1) == 0


def test_reconcile_adds_the_column_to_an_older_database(tmp_path):
    """The additive column self-heals on open — no migration ladder."""
    db_path = tmp_path / "older.db"
    reset_database()
    Database(db_path)
    reset_database()
    conn = sqlite3.connect(str(db_path))
    conn.execute("ALTER TABLE dictation_journal RENAME TO dictation_journal_new")
    conn.execute(
        """
        CREATE TABLE dictation_journal (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            source TEXT NOT NULL,
            project_root TEXT,
            transcript TEXT NOT NULL DEFAULT '',
            intent TEXT,
            block_id TEXT,
            target_profile TEXT,
            final_text TEXT NOT NULL DEFAULT '',
            stage_ms TEXT NOT NULL DEFAULT '{}',
            total_ms REAL NOT NULL DEFAULT 0,
            rewrite_pass_ms TEXT NOT NULL DEFAULT '[]',
            confidence REAL,
            warnings TEXT NOT NULL DEFAULT '[]',
            corrected INTEGER NOT NULL DEFAULT 0,
            correction_id INTEGER
        )
        """
    )
    conn.execute("DROP TABLE dictation_journal_new")
    conn.execute(
        "INSERT INTO dictation_journal (source, transcript, final_text) "
        "VALUES ('dictation', 'old row', 'old row')"
    )
    conn.commit()
    conn.close()

    reset_database()
    database = Database(db_path)
    rows = database.dictation_journal.recent()
    assert [r.transcript for r in rows] == ["old row"]
    assert rows[0].corrections_applied == []
    fresh = database.dictation_journal.record(
        source="dictation", transcript="new", final_text="new", corrections_applied=[2]
    )
    assert fresh.corrections_applied == [2]
    reset_database()


def _run(final_text: str, applied: tuple[int, ...] = ()) -> PipelineRun:
    return PipelineRun(
        final_text=final_text, stage_results=[], intent=None, warnings=[],
        total_elapsed_ms=41.0, short_circuited=False, corrections_applied=applied,
    )


def test_recorder_writes_the_ids_and_pushes_one_frame(journal_repo):
    frames: list[tuple[str, dict]] = []
    recorder = DictationJournalRecorder(
        repository=journal_repo, broadcast=lambda t, d: frames.append((t, d))
    )
    stored = recorder.record(
        _run("PostgreSQL needs a bump", (3,)),
        source="dictation",
        transcript="postgress needs a bump",
        target_profile=SimpleNamespace(id="claude_code", details={}),
    )
    assert stored.corrections_applied == [3]
    assert len(frames) == 1
    kind, frame = frames[0]
    assert kind == "dictation.journal.entry"
    assert frame == {
        "id": stored.id,
        "created_at": stored.created_at,
        "source": "dictation",
        "transcript": "postgress needs a bump",
        "final_text": "PostgreSQL needs a bump",
        "total_ms": 41.0,
        "corrections_applied": [3],
        "taught_from": False,
        "intent_tag": None,
        "target_profile": "claude_code",
    }


def test_the_frame_carries_the_redacted_row_not_the_raw_text(journal_repo):
    frames: list[dict] = []
    recorder = DictationJournalRecorder(
        repository=journal_repo, broadcast=lambda t, d: frames.append(d)
    )
    secret = "my key is sk-abcdef0123456789abcd"
    recorder.record(_run(secret), source="dictation", transcript=secret)
    assert frames[0]["transcript"] == "[redacted: possible secret]"
    assert frames[0]["final_text"] == "[redacted: possible secret]"
    assert "sk-abcdef" not in str(frames[0])


def test_a_recorder_without_a_broadcast_pushes_nothing(journal_repo):
    recorder = DictationJournalRecorder(repository=journal_repo)
    assert recorder.record(_run("x"), source="dictation", transcript="x") is not None


def test_taught_from_rides_the_existing_corrected_column(journal_repo):
    frames: list[dict] = []
    recorder = DictationJournalRecorder(
        repository=journal_repo, broadcast=lambda t, d: frames.append(d)
    )
    stored = recorder.record(_run("x"), source="dictation", transcript="x")
    journal_repo.mark_corrected(stored.id, correction_id=5)
    row = journal_repo.get(stored.id)
    assert row.corrected is True and row.correction_id == 5
    # …and the two facts stay separate: nothing FIRED on the row he taught from.
    assert row.corrections_applied == []
    assert frames[0]["taught_from"] is False


def test_the_target_rules_own_id_reaches_the_row(journal_repo):
    recorder = DictationJournalRecorder(repository=journal_repo)
    stored = recorder.record(
        _run("x", (3,)),
        source="dictation",
        transcript="x",
        target_profile=SimpleNamespace(
            id="claude_code", details={"matched": "correction", "correction_id": 11}
        ),
    )
    assert stored.corrections_applied == [3, 11]


def test_the_pipeline_off_passthrough_still_records(journal_repo):
    """`passthrough_run` has no `corrections_applied` — the recorder must not raise."""
    recorder = DictationJournalRecorder(repository=journal_repo)
    stored = recorder.record(passthrough_run("bare text"), source="dictation", transcript="bare text")
    assert stored is not None
    assert stored.corrections_applied == []


# ── the N1 belt on the live typing path ───────────────────────────────────


def test_an_auto_target_correction_cannot_raise_on_the_apply_path():
    """`auto` clears the membership guard; `_profile` must not KeyError on it."""
    from holdspeak.target_profile import apply_target_correction, detect_target_profile

    profile = detect_target_profile({"app_name": "Safari"})
    taught = Correction(kind="target", key="ship the q4 platform", value="auto", sequence=1)
    corrected = apply_target_correction(
        profile, text="ship the q4 platform", corrections=[taught]
    )
    assert corrected.id == "auto"
    assert corrected.label == "auto"


def test_a_target_correction_carries_its_rule_id():
    from holdspeak.target_profile import apply_target_correction, detect_target_profile

    profile = detect_target_profile({"app_name": "Safari"})
    taught = Correction(
        kind="target", key="ship the q4 platform", value="claude_code",
        sequence=1, correction_id=11,
    )
    corrected = apply_target_correction(
        profile, text="ship the q4 platform", corrections=[taught]
    )
    assert corrected.id == "claude_code"
    assert corrected.details["correction_id"] == 11


# ── the scroll-to-load cursor ─────────────────────────────────────────────


def test_recent_pages_backwards_from_a_before_cursor(journal_repo):
    """`before` is the oldest id the caller holds: only older rows come back."""
    ids = [
        journal_repo.record(source="dictation", transcript=f"u{n}", final_text=f"u{n}").id
        for n in range(5)
    ]
    first_page = journal_repo.recent(limit=2)
    assert [r.id for r in first_page] == [ids[4], ids[3]]

    second_page = journal_repo.recent(limit=2, before=first_page[-1].id)
    assert [r.id for r in second_page] == [ids[2], ids[1]]

    last_page = journal_repo.recent(limit=2, before=second_page[-1].id)
    assert [r.id for r in last_page] == [ids[0]]

    # The cursor is exclusive, and it composes with the source filter.
    assert journal_repo.recent(before=ids[0]) == []
    journal_repo.record(source="browser", transcript="b", final_text="b")
    assert [r.id for r in journal_repo.recent(source="dictation", before=ids[2])] == [
        ids[1],
        ids[0],
    ]
    # Omitting it is byte-identical to the Phase 45 read.
    assert [r.id for r in journal_repo.recent(limit=5, source="dictation")] == ids[::-1]


# ── C3: `REFUSED · SECRET` refuses the shapes it promises to ──────────────
#
# The ratified board's own example (`assets/mockups/SpeakRefused.dc.html`) is
# `sk-live-4f2a9c`, and counsel reproduced that the guard let it through — the
# old rule wanted `sk-` + 16 LOWERCASE ALPHANUMERICS, and the hyphen after
# `live` ended the run at four. A `text` rule's value is stored in plaintext,
# shown on the Learned wing, and typed into every future matching utterance,
# so the shapes below are the ones a refusal has to know.

SECRET_SHAPES = [
    # the board's own example — the one that used to sail through
    "sk-live-4f2a9c",
    "sk-proj-Ab12Cd34Ef56",
    "sk-ant-api03-abcdef123456",
    "sk-abcdef0123456789abcd",
    "AKIAIOSFODNN7EXAMPLE",
    "ghp_16CharacterTokenHere",
    "gho_abcdef1234567890",
    "ghu_abcdef1234567890",
    "github_pat_11ABCDEFG0abcdefghij",
    "xoxb-123456789012-abcdefghijkl",
    "xoxp-1234-5678-abcdefghijkl",
    "glpat-ABCdef123456xyz",
    "AIzaSyD-9x8QwErTyUiOpAsDfGhJkLzXcVbN",
    "-----BEGIN RSA PRIVATE KEY-----",
    # the shapes the check already knew, kept
    "my api_key is in the vault",
    "the access-token rotates weekly",
    "authorization: bearer abcdefghijklmnopqrstuvwx",
]

# Ordinary sentences a Senior Architect really says on a Tuesday. Every one of
# them brushes the new prefixes (`risk-`, `Ask`, `Alaska`, `Asia-`), and none
# may be refused: a false SECRET silently eats a correction he meant to teach.
ORDINARY_SENTENCES = [
    "Ask Marta to take a risk-averse view of the Alaska vendor contract.",
    "Asia-Pacific rollout starts next quarter; put it on the calendar.",
    "postgress needs a version bump before Charter ships on Friday.",
]


@pytest.mark.parametrize("shape", SECRET_SHAPES)
def test_every_credential_shape_is_refused(shape: str):
    from holdspeak.project_doc_suggestions import looks_like_secret

    assert looks_like_secret(shape) is True


@pytest.mark.parametrize("sentence", ORDINARY_SENTENCES)
def test_ordinary_speech_is_never_mistaken_for_a_secret(sentence: str):
    from holdspeak.project_doc_suggestions import looks_like_secret

    assert looks_like_secret(sentence) is False


def test_the_boards_own_example_is_refused_by_the_correction_store():
    """End to end on the caller that made counsel raise it: the teach path."""
    store = CorrectionStore()
    outcome = store.record("text", "my key is sk-live-4f2a9c", "safe words")
    assert outcome.refusal == "secret"
    assert store.record("text", "safe words", "sk-live-4f2a9c").refusal == "secret"
    assert len(store) == 0


def test_the_journal_redacts_a_row_carrying_the_boards_example():
    """The other caller: a recorded row never carries the credential."""
    from holdspeak.plugins.dictation.journal import _REDACTED, filter_secret

    assert filter_secret("the key is sk-live-4f2a9c") == _REDACTED
    assert filter_secret("postgress needs a bump") == "postgress needs a bump"


# ── C4: the footer's `N TODAY` counts today ───────────────────────────────


def test_count_today_counts_the_local_calendar_day(journal_repo):
    """`count()` is the all-time retained total; `count_today()` is the token."""
    from datetime import timedelta

    journal_repo.record(source="dictation", transcript="now one", final_text="a")
    journal_repo.record(source="hotkey", transcript="now two", final_text="b")
    old = journal_repo.record(source="dictation", transcript="old", final_text="c")
    yesterday = (datetime.now() - timedelta(days=1)).isoformat()
    with journal_repo._connection() as conn:
        conn.execute(
            "UPDATE dictation_journal SET created_at = ? WHERE id = ?",
            (yesterday, old.id),
        )

    assert journal_repo.count() == 3
    assert journal_repo.count_today() == 2


def test_count_today_is_zero_on_an_empty_journal(journal_repo):
    assert journal_repo.count_today() == 0


def test_count_today_reads_an_offset_row_in_local_time(journal_repo):
    """A row carrying an explicit offset is converted before its day is taken."""
    stored = journal_repo.record(source="dictation", transcript="x", final_text="x")
    local_now = datetime.now().astimezone()
    with journal_repo._connection() as conn:
        conn.execute(
            "UPDATE dictation_journal SET created_at = ? WHERE id = ?",
            (local_now.astimezone(timezone.utc).isoformat(), stored.id),
        )
    # The same instant, written in UTC, is still TODAY where the desk is.
    assert journal_repo.count_today() == 1


def test_count_today_ignores_an_unparseable_stamp(journal_repo):
    stored = journal_repo.record(source="dictation", transcript="x", final_text="x")
    with journal_repo._connection() as conn:
        conn.execute(
            "UPDATE dictation_journal SET created_at = ? WHERE id = ?",
            ("not a timestamp", stored.id),
        )
    assert journal_repo.count_today() == 0
