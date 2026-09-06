"""HS-176-02 / HS-176-03 — the Speak Loop's route half.

Every wire change stories 02 and 03 make to `web/routes/dictation/`:

- **R4, the teach routes made honest.** `recorded` is the ONE key both teach
  routes answer with; a refused teach writes nothing (no correction row, no
  `taught_from` flag, no `correction_id` linkage) and names its reason; the
  linked id is the one `CorrectionStore.record` returned, never the newest row.
- **R1/N3, the `text` kind.** The word-level diff runs server-side, in ONE
  place (`_helpers.diff_text_correction`), for both teach routes.
- **N2, the raw transcript** on both run responses, beside `final_text`.
- **R3, `N APPLIED` as a real count** — journal rows whose stored
  `corrections_applied` names the rule, not `reach_for_gist`'s similar
  transcripts.
- **R12/N1, the label sources** — the readiness route's `target.overrides`
  carries the six ids and their verbatim labels; never `auto`.
- **HS-176-03, the journal stream route** — the `source` clamp widened to the
  recorder's `VALID_SOURCES`, `before=<id>` pagination, `corrections_applied` +
  `taught_from` on the row, and no `learning` (R2).
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
from holdspeak.web.routes.dictation._helpers import diff_text_correction
from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks


@pytest.fixture
def persistent_db():
    temp_dir = Path(tempfile.mkdtemp())
    reset_database()
    database = Database(temp_dir / "hs176.db")
    yield database
    reset_database()
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def settings_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    target = tmp_path / "config.json"
    monkeypatch.setattr(config_module, "CONFIG_FILE", target)
    cfg = Config()
    cfg.dictation.pipeline.enabled = False
    cfg.dictation.pipeline.corrections_enabled = True
    cfg.save(path=target)
    return target


def _server(database: Database) -> MeetingWebServer:
    return MeetingWebServer(
        WebRuntimeCallbacks(
            on_bookmark=MagicMock(), on_stop=MagicMock(), get_state=MagicMock(return_value={})
        ),
        dictation_journal_repository=database.dictation_journal,
        dictation_corrections_repository=database.dictation_corrections,
    )


def _client(database: Database) -> TestClient:
    return TestClient(_server(database).app)


# ── the word-level diff: the three ruled outcomes (R1, D2(a)) ──────────────


def test_diff_one_span_yields_a_word_rule() -> None:
    """The Tuesday moment: one word wrong in a sentence -> a word rule."""
    out = diff_text_correction(
        "postgress needs a version bump before Charter ships",
        "PostgreSQL needs a version bump before Charter ships",
    )
    assert out["reason"] is None
    assert out["rule"] == {"key": "postgress", "value": "PostgreSQL", "shape": "word"}


def test_diff_no_difference_is_no_change_and_stores_nothing() -> None:
    out = diff_text_correction("ship the release notes", "ship the release notes")
    assert out == {"rule": None, "reason": "no_change"}


def test_diff_many_spans_yields_a_whole_phrase_rule() -> None:
    out = diff_text_correction(
        "send the note to dana on friday",
        "send the memo to Alex on monday",
    )
    assert out["reason"] is None
    assert out["rule"]["shape"] == "phrase"
    assert out["rule"]["key"] == "send the note to dana on friday"
    assert out["rule"]["value"] == "send the memo to Alex on monday"


def test_diff_span_over_half_the_tokens_yields_a_whole_phrase_rule() -> None:
    out = diff_text_correction("one two three four", "one alpha beta gamma delta")
    assert out["rule"]["shape"] == "phrase"
    assert out["rule"]["key"] == "one two three four"


def test_diff_strips_attached_punctuation_from_the_stored_span() -> None:
    """N3: `raw_text` is post-TextProcessor, so the token is `postgress,`."""
    out = diff_text_correction("i said postgress, again ok", "i said PostgreSQL, again ok")
    assert out["rule"] == {"key": "postgress", "value": "PostgreSQL", "shape": "word"}


def test_diff_key_is_lowercased_and_the_value_is_verbatim() -> None:
    out = diff_text_correction("call Postgress now please", "call PostgreSQL now please")
    assert out["rule"]["key"] == "postgress"
    assert out["rule"]["value"] == "PostgreSQL"


def test_diff_punctuation_only_edit_is_no_change() -> None:
    assert diff_text_correction("ship it.", "ship it,")["reason"] == "no_change"


def test_diff_pure_insertion_falls_back_to_a_whole_phrase_rule() -> None:
    """An insertion has no heard span, so it cannot be keyed as a word rule."""
    out = diff_text_correction("a b c d", "a b c d e")
    assert out["rule"]["shape"] == "phrase"
    assert out["rule"]["key"] == "a b c d"


def test_diff_empty_side_stores_nothing() -> None:
    assert diff_text_correction("", "something")["reason"] == "empty"
    assert diff_text_correction("something", "   ")["reason"] == "empty"


# ── POST /api/dictation/corrections — the fallback teach route ─────────────


def test_corrections_post_text_kind_diffs_and_returns_the_stored_rule(
    persistent_db: Database, settings_path: Path
) -> None:
    client = _client(persistent_db)
    resp = client.post(
        "/api/dictation/corrections",
        json={
            "kind": "text",
            "heard": "postgress needs a version bump",
            "said": "PostgreSQL needs a version bump",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["recorded"] is True
    assert body["kind"] == "text"
    assert body["key"] == "postgress"
    assert body["value"] == "PostgreSQL"
    assert isinstance(body["id"], int)
    stored = persistent_db.dictation_corrections.recent_corrections()
    assert [(r.kind, r.gist, r.value) for r in stored] == [("text", "postgress", "PostgreSQL")]


def test_corrections_post_text_kind_accepts_the_legacy_field_names(
    persistent_db: Database, settings_path: Path
) -> None:
    """`text`/`value` are aliases for `heard`/`said` — the existing shape works."""
    resp = _client(persistent_db).post(
        "/api/dictation/corrections",
        json={"kind": "text", "text": "the postgress box", "value": "the PostgreSQL box"},
    )
    assert resp.json()["key"] == "postgress"
    assert resp.json()["value"] == "PostgreSQL"


def test_corrections_post_text_kind_no_change_writes_nothing(
    persistent_db: Database, settings_path: Path
) -> None:
    resp = _client(persistent_db).post(
        "/api/dictation/corrections",
        json={"kind": "text", "heard": "ship the notes", "said": "ship the notes"},
    )
    assert resp.status_code == 200
    assert resp.json()["recorded"] is False
    assert resp.json()["reason"] == "no_change"
    assert persistent_db.dictation_corrections.recent_corrections() == []


def test_corrections_post_refusal_names_its_reason(
    persistent_db: Database, settings_path: Path
) -> None:
    client = _client(persistent_db)
    secret = client.post(
        "/api/dictation/corrections",
        json={"kind": "intent", "text": "token is sk-abcdef0123456789abcd", "value": "code_exercise"},
    ).json()
    assert secret["recorded"] is False and secret["reason"] == "secret"

    one_word = client.post(
        "/api/dictation/corrections",
        json={"kind": "intent", "text": "deploy", "value": "code_exercise"},
    ).json()
    assert one_word["recorded"] is False and one_word["reason"] == "one_word"
    assert persistent_db.dictation_corrections.recent_corrections() == []


def test_corrections_post_routing_kind_returns_the_stored_id(
    persistent_db: Database, settings_path: Path
) -> None:
    body = _client(persistent_db).post(
        "/api/dictation/corrections",
        json={"kind": "target", "text": "route this to codex", "value": "codex_cli"},
    ).json()
    assert body["recorded"] is True and body["kind"] == "target"
    assert body["id"] == persistent_db.dictation_corrections.recent_corrections()[0].id


def test_corrections_post_text_kind_requires_both_sides(
    persistent_db: Database, settings_path: Path
) -> None:
    client = _client(persistent_db)
    assert client.post("/api/dictation/corrections", json={"kind": "text", "said": "x"}).status_code == 400
    assert client.post("/api/dictation/corrections", json={"kind": "text", "heard": "x"}).status_code == 400


# ── POST /api/dictation/journal/{id}/correct — the primary teach route ─────


def test_journal_correct_refused_teach_writes_nothing(
    persistent_db: Database, settings_path: Path
) -> None:
    """R4: the refusal no longer flips `corrected` or links a stranger's id."""
    other = persistent_db.dictation_corrections.record_correction(
        kind="intent", gist="an unrelated rule", value="other_block"
    )
    entry = persistent_db.dictation_journal.record(
        source="dry_run", transcript="token is sk-abcdef0123456789abcd", final_text="x"
    )
    body = _client(persistent_db).post(
        f"/api/dictation/journal/{entry.id}/correct",
        json={"kind": "intent", "value": "agent_task_buildout"},
    ).json()
    assert body["recorded"] is False and body["taught"] is False
    assert body["corrected"] is False
    assert body["reason"] == "secret"
    assert body["correction_id"] is None
    row = persistent_db.dictation_journal.get(entry.id)
    assert row.corrected is False and row.correction_id is None
    # The stranger's rule is untouched and unlinked.
    assert [r.id for r in persistent_db.dictation_corrections.recent_corrections()] == [other.id]


def test_journal_correct_links_the_id_record_returned(
    persistent_db: Database, settings_path: Path
) -> None:
    persistent_db.dictation_corrections.record_correction(
        kind="intent", gist="an older rule", value="older_block"
    )
    entry = persistent_db.dictation_journal.record(
        source="dictation", transcript="ship the billing rollout notes", final_text="x"
    )
    body = _client(persistent_db).post(
        f"/api/dictation/journal/{entry.id}/correct",
        json={"kind": "intent", "value": "action_item"},
    ).json()
    assert body["recorded"] is True and body["taught"] is True and body["corrected"] is True
    stored = [r for r in persistent_db.dictation_corrections.recent_corrections() if r.value == "action_item"]
    assert len(stored) == 1
    assert body["correction_id"] == stored[0].id
    row = persistent_db.dictation_journal.get(entry.id)
    assert row.corrected is True and row.correction_id == stored[0].id


def test_journal_correct_text_kind_diffs_heard_against_said(
    persistent_db: Database, settings_path: Path
) -> None:
    entry = persistent_db.dictation_journal.record(
        source="dictation",
        transcript="postgress needs a version bump",
        final_text="Postgress needs a version bump.",
    )
    body = _client(persistent_db).post(
        f"/api/dictation/journal/{entry.id}/correct",
        json={"kind": "text", "said": "PostgreSQL needs a version bump"},
    ).json()
    assert body["recorded"] is True
    assert body["key"] == "postgress" and body["value"] == "PostgreSQL"
    # A `text` rule is exact-phrase: it has no Jaccard reach to report.
    assert body["similar"] == 0
    assert persistent_db.dictation_journal.get(entry.id).correction_id == body["id"]


def test_journal_correct_text_kind_no_change_writes_nothing(
    persistent_db: Database, settings_path: Path
) -> None:
    entry = persistent_db.dictation_journal.record(
        source="dictation", transcript="ship the release notes", final_text="x"
    )
    body = _client(persistent_db).post(
        f"/api/dictation/journal/{entry.id}/correct",
        json={"kind": "text", "said": "ship the release notes"},
    ).json()
    assert body["recorded"] is False and body["reason"] == "no_change"
    assert body["corrected"] is False
    assert persistent_db.dictation_journal.get(entry.id).corrected is False
    assert persistent_db.dictation_corrections.recent_corrections() == []


def test_journal_correct_text_kind_takes_an_explicit_heard(
    persistent_db: Database, settings_path: Path
) -> None:
    """The face sends the run's RAW transcript, which may differ from the row."""
    entry = persistent_db.dictation_journal.record(
        source="dictation", transcript="rewritten by a stage", final_text="x"
    )
    body = _client(persistent_db).post(
        f"/api/dictation/journal/{entry.id}/correct",
        json={"kind": "text", "heard": "the postgress box", "said": "the PostgreSQL box"},
    ).json()
    assert body["key"] == "postgress" and body["value"] == "PostgreSQL"


# ── GET /api/dictation/corrections — `applied` is a real count (R3) ────────


def test_corrections_list_serves_applied_not_similar(
    persistent_db: Database, settings_path: Path
) -> None:
    rule = persistent_db.dictation_corrections.record_correction(
        kind="intent", gist="follow up with sam about launch", value="action_item"
    )
    # Three similar transcripts, none of which the rule actually fired on.
    for t in [
        "follow up with sam about launch checklist",
        "follow up with sam about launch",
        "water the plants",
    ]:
        persistent_db.dictation_journal.record(source="dictation", transcript=t, final_text=t)
    body = _client(persistent_db).get("/api/dictation/corrections").json()
    item = next(i for i in body["items"] if i["id"] == rule.id)
    assert "similar" not in item, "reach_for_gist appears on no face (R3)"
    assert item["applied"] == 0, "no row records this rule firing"


def test_corrections_list_applied_counts_rows_that_name_the_rule(
    persistent_db: Database, settings_path: Path
) -> None:
    rule = persistent_db.dictation_corrections.record_correction(
        kind="text", gist="postgress", value="PostgreSQL"
    )
    other = persistent_db.dictation_corrections.record_correction(
        kind="text", gist="charter", value="Charter"
    )
    persistent_db.dictation_journal.record(
        source="dictation", transcript="a", final_text="a", corrections_applied=[rule.id]
    )
    persistent_db.dictation_journal.record(
        source="dictation",
        transcript="b",
        final_text="b",
        corrections_applied=[rule.id, other.id],
    )
    persistent_db.dictation_journal.record(source="dictation", transcript="c", final_text="c")
    by_id = {i["id"]: i for i in _client(persistent_db).get("/api/dictation/corrections").json()["items"]}
    assert by_id[rule.id]["applied"] == 2
    assert by_id[other.id]["applied"] == 1


# ── GET /api/dictation/journal — the stream route (HS-176-03) ──────────────


def test_journal_rows_carry_the_two_split_facts_and_no_learning(
    persistent_db: Database, settings_path: Path
) -> None:
    rule = persistent_db.dictation_corrections.record_correction(
        kind="text", gist="postgress", value="PostgreSQL"
    )
    fired = persistent_db.dictation_journal.record(
        source="dictation", transcript="postgress bump", final_text="PostgreSQL bump",
        corrections_applied=[rule.id],
    )
    taught = persistent_db.dictation_journal.record(
        source="dictation", transcript="postgress again", final_text="x"
    )
    persistent_db.dictation_journal.mark_corrected(taught.id, correction_id=rule.id)

    items = _client(persistent_db).get("/api/dictation/journal").json()["items"]
    rows = {i["id"]: i for i in items}
    assert all("learning" not in i for i in items), "R2: no read-time would-match"
    assert rows[fired.id]["corrections_applied"] == [rule.id]
    assert rows[fired.id]["taught_from"] is False
    assert rows[taught.id]["corrections_applied"] == []
    assert rows[taught.id]["taught_from"] is True


def test_journal_source_filter_accepts_every_recorder_source(
    persistent_db: Database, settings_path: Path
) -> None:
    """The old clamp dropped `browser` and `hotkey` into "no filter"."""
    from holdspeak.plugins.dictation.journal import VALID_SOURCES

    for source in VALID_SOURCES:
        persistent_db.dictation_journal.record(
            source=source, transcript=f"said on {source}", final_text="x"
        )
    client = _client(persistent_db)
    for source in VALID_SOURCES:
        items = client.get(f"/api/dictation/journal?source={source}").json()["items"]
        assert [i["source"] for i in items] == [source], source
    # An unknown source is not a filter (and never an error).
    assert len(client.get("/api/dictation/journal?source=nonsense").json()["items"]) == len(
        VALID_SOURCES
    )


def test_journal_before_cursor_pages_older_entries(
    persistent_db: Database, settings_path: Path
) -> None:
    ids = [
        persistent_db.dictation_journal.record(
            source="dictation", transcript=f"line {n}", final_text="x"
        ).id
        for n in range(6)
    ]
    client = _client(persistent_db)
    first = client.get("/api/dictation/journal?limit=2").json()["items"]
    assert [i["id"] for i in first] == list(reversed(ids))[:2]
    oldest = first[-1]["id"]
    second = client.get(f"/api/dictation/journal?limit=2&before={oldest}").json()["items"]
    assert [i["id"] for i in second] == list(reversed(ids))[2:4]
    assert all(i["id"] < oldest for i in second)


# ── GET /api/dictation/readiness — the label sources (R12/N1) ──────────────


def test_readiness_target_carries_the_six_override_labels(
    persistent_db: Database, settings_path: Path
) -> None:
    from holdspeak.target_profile import TARGET_PROFILE_OVERRIDE_OPTIONS

    target = _client(persistent_db).get("/api/dictation/readiness").json()["target"]
    overrides = target["overrides"]
    assert [o["id"] for o in overrides] == [
        "claude_code",
        "codex_cli",
        "terminal_shell",
        "browser",
        "editor",
        "chat",
    ]
    assert "auto" not in {o["id"] for o in overrides}
    assert set(o["id"] for o in overrides) == TARGET_PROFILE_OVERRIDE_OPTIONS - {"auto"}
    # The label map's string, verbatim — `Terminal shell`, never `Terminal`.
    labels = {o["id"]: o["label"] for o in overrides}
    assert labels["terminal_shell"] == "Terminal shell"
    assert labels["claude_code"] == "Claude Code"
    assert labels["codex_cli"] == "Codex CLI"


def test_blocks_route_already_serves_the_intent_label_source(
    persistent_db: Database, settings_path: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The `intent` label source needs no new field: `Block.description` rides
    the blocks document `GET /api/dictation/blocks` already returns."""
    from holdspeak.plugins.dictation import assembly as assembly_module
    from holdspeak.web.routes.dictation import _helpers as helpers_module

    blocks = tmp_path / "blocks.yaml"
    blocks.write_text(
        "version: 1\n"
        "default_match_confidence: 0.6\n"
        "blocks:\n"
        "  - id: note_block\n"
        "    description: Jot a note\n"
        "    match: {examples: ['jot this down']}\n"
        "    inject: {mode: replace, template: '{text}'}\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(assembly_module, "DEFAULT_GLOBAL_BLOCKS_PATH", blocks)
    monkeypatch.setattr(helpers_module, "_resolve_blocks_target", lambda *a, **k: (blocks, None))
    document = _client(persistent_db).get("/api/dictation/blocks?scope=global").json()["document"]
    assert [(b["id"], b["description"]) for b in document["blocks"]] == [
        ("note_block", "Jot a note")
    ]


# ── the run response carries the raw transcript (N2) ───────────────────────


def test_pipeline_off_run_serves_the_raw_transcript_and_no_applied_ids(
    persistent_db: Database, settings_path: Path
) -> None:
    """The passthrough path: `raw_text` beside `final_text`, nothing fired."""
    body = _client(persistent_db).post(
        "/api/dictation/dry-run", json={"utterance": "postgress needs a bump"}
    ).json()
    assert body["runtime_status"] == "disabled"
    assert body["raw_text"] == "postgress needs a bump"
    assert body["final_text"] == "postgress needs a bump"
    assert body["corrections_applied"] == []
