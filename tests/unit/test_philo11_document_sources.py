"""PHILO-11-01 — the nine stored channel document sources."""
from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
import sys

import pytest

from holdspeak.db import get_database, reset_database
from holdspeak.services.channel_contract import ChannelRefused, render_document as contract_render_document
from holdspeak.services.document_sources import DOCUMENT_SOURCES, render_document

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _philo11_documents import OWNER, TRANSCRIPT_SENTINEL, mint_documents  # noqa: E402
from _philo12_artifacts import mint_meeting_synthesis  # noqa: E402


@pytest.fixture(autouse=True)
def _isolated_people_environment(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    # Record the prior environment even when the variable was absent. The
    # shared real producer selects this same seam for later source reads.
    monkeypatch.setenv("HOLDSPEAK_PEOPLE_KEYSTORE_FILE", str(tmp_path / "people.key"))


@pytest.fixture
def db(tmp_path: Path):
    reset_database()
    database = get_database(tmp_path / "holdspeak.db")
    yield database
    reset_database()


def mint_note(db, title: str = "Plan for the pilot", body: str = "We start on Monday.\n\n- Ask Avery") -> str:
    """PHILO-17 U08: a note as the owner writes it (the Thought's working note)."""
    from holdspeak.services.primitive_service import PrimitiveService

    return f"note:{PrimitiveService(db).create_note(OWNER, title=title, body_markdown=body)['id']}"


def test_a_note_sends_its_title_and_words(db) -> None:
    document = render_document(db, mint_note(db))
    assert document.title == "Plan for the pilot"
    assert document.body_md == "# Plan for the pilot\n\nWe start on Monday.\n\n- Ask Avery\n"
    assert document.label == "NOTE" and document.slug == "plan-for-the-pilot"


def test_a_thought_titled_by_its_first_words_says_them_once(db) -> None:
    words = "Pilot plan: we start on Monday"
    document = render_document(db, mint_note(db, title=words, body=f"{words}\nAvery owns the rollout"))
    assert document.body_md == f"# {words}\n\nAvery owns the rollout\n"
    assert render_document(db, mint_note(db, title=words, body=words)).body_md == f"# {words}\n"


def test_a_note_with_no_words_is_named_note_empty(db) -> None:
    with pytest.raises(ChannelRefused) as caught:
        render_document(db, mint_note(db, title="", body="  "))
    assert caught.value.code == "note_empty"


def test_registry_declares_the_nine_kinds() -> None:
    assert tuple(DOCUMENT_SOURCES) == (
        "project_update",
        "monday_brief",
        "desk_decision",
        "meeting_decision",
        "decision_record",
        "meeting_summary",
        "meeting_digest",
        "meeting_followup",
        "artifact",
        "note",
    )


def test_real_producers_render_all_nine_sources(db, tmp_path: Path) -> None:
    refs = mint_documents(
        db,
        OWNER,
        now=datetime(2026, 9, 29, 10, 0, 0),
        people_keystore_path=tmp_path / "people.key",
    )
    refs["artifact"] = mint_meeting_synthesis(db)
    refs["note"] = mint_note(db)
    rendered = {kind: render_document(db, ref) for kind, ref in refs.items()}

    assert set(rendered) == set(DOCUMENT_SOURCES)
    for kind, document in rendered.items():
        assert document.ref == refs[kind]
        assert document.title
        assert document.body_md.strip(), kind
        assert document.label.strip(), kind

    brief = rendered["monday_brief"].body_md
    # Inventory gap 5 (2026-10-03): the sent Brief carries no People data.
    assert "Avery" not in brief
    assert "You owe" not in brief and "## People" not in brief
    assert "Check the frozen bytes" in brief
    assert "acknowledged" not in brief.lower()
    assert "deferred" not in brief.lower()
    # PHILO-11-05a: the generated time is a readable date and time, the same
    # text in the preview and the sent bytes: no ISO `T`, no microseconds.
    generated = next(line for line in brief.splitlines() if line.startswith("Generated: "))
    assert re.fullmatch(r"Generated: \d{1,2} [A-Z][a-z]{2} \d{4}, \d{2}:\d{2}", generated), generated
    assert not re.search(r"\d{4}-\d{2}-\d{2}T|\d{2}:\d{2}:\d{2}\.\d+", brief), generated
    brief_id = refs["monday_brief"].split(":", 1)[1]
    with db._connection() as conn:
        shelved = conn.execute(
            """SELECT i.text FROM monday_brief_items AS i
               JOIN monday_brief_item_shelf AS s ON s.item_id = i.id
               WHERE i.brief_id = ? AND s.state = 'acknowledged'
               ORDER BY i.id LIMIT 1""",
            (brief_id,),
        ).fetchone()
    assert shelved is not None
    assert shelved["text"] in brief

    assert "# Published update" in rendered["project_update"].body_md
    assert "## Deciders" in rendered["desk_decision"].body_md
    assert "## Decision" in rendered["desk_decision"].body_md
    assert "## Consequences" in rendered["desk_decision"].body_md
    assert "Use one document registry" in rendered["meeting_decision"].body_md
    assert "Lifecycle: recorded" in rendered["meeting_decision"].body_md
    record_body = rendered["decision_record"].body_md
    assert "Lifecycle: superseded" in record_body
    assert "## Owner\nAvery" in record_body
    assert "## Review date\n2026-10-10" in record_body
    # PHILO-11-05a (Muad'Dib's ruling): sources by what a person recognizes;
    # the later decision by its words (no internal refs in sent text).
    assert "- Source review, 29 Sep 2026" in record_body
    assert "artifact" not in record_body and "philo11-meeting" not in record_body
    assert "## Superseded by\nUse one document registry (successor)" in record_body
    assert "## Summary" in rendered["meeting_summary"].body_md
    assert "The channel reads durable records." in rendered["meeting_summary"].body_md
    assert "## Topics" in rendered["meeting_summary"].body_md
    assert "## What we decided" in rendered["meeting_digest"].body_md
    assert "Use one document registry" in rendered["meeting_digest"].body_md
    assert "## Still open" in rendered["meeting_digest"].body_md
    assert "Follow-up" in rendered["meeting_followup"].body_md
    contract_brief = contract_render_document(db, refs["monday_brief"])
    assert "Avery" not in contract_brief.body_md
    for kind, ref in refs.items():
        assert contract_render_document(db, ref).body_md.strip(), kind


def test_monday_brief_never_names_people_state(
    db, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    refs = mint_documents(
        db,
        OWNER,
        now=datetime(2026, 9, 29, 10, 0, 0),
        people_keystore_path=tmp_path / "people-ready.key",
    )
    monkeypatch.setenv("HOLDSPEAK_PEOPLE_KEYSTORE_FILE", str(tmp_path / "people-missing.key"))

    body = render_document(db, refs["monday_brief"]).body_md

    # The sent Brief reads no People store: a closed store leaves no line.
    assert "PEOPLE" not in body


def test_meeting_sources_never_copy_transcript(db, tmp_path: Path) -> None:
    refs = mint_documents(
        db,
        OWNER,
        now=datetime(2026, 9, 29, 10, 0, 0),
        people_keystore_path=tmp_path / "people.key",
    )
    for kind in ("meeting_summary", "meeting_digest", "meeting_followup"):
        body = render_document(db, refs[kind]).body_md
        assert TRANSCRIPT_SENTINEL not in body


@pytest.mark.parametrize("kind", tuple(DOCUMENT_SOURCES))
def test_each_source_names_a_missing_record(db, kind: str) -> None:
    with pytest.raises(ChannelRefused) as caught:
        render_document(db, f"{kind}:missing")
    assert caught.value.code == "document_not_found"


@pytest.mark.parametrize(
    ("document_ref", "code"),
    [
        ("unknown_kind:source", "document_kind_unknown"),
        ("", "document_kind_unknown"),
        ("meeting_summary:missing", "document_not_found"),
    ],
)
def test_named_source_refusals(db, document_ref: str, code: str) -> None:
    with pytest.raises(ChannelRefused) as caught:
        render_document(db, document_ref)
    assert caught.value.code == code


def test_missing_meeting_summary_is_named_no_summary(db) -> None:
    from holdspeak.meeting_session import MeetingState

    db.meetings.save_meeting(
        MeetingState(id="quiet", started_at=datetime(2026, 9, 29, 10, 0, 0), title="Quiet")
    )
    with pytest.raises(ChannelRefused) as caught:
        render_document(db, "meeting_summary:quiet")
    assert caught.value.code == "no_summary"


@pytest.mark.parametrize("kind", ("meeting_digest", "meeting_followup"))
def test_empty_aftercare_is_named_no_summary(db, kind: str) -> None:
    from holdspeak.meeting_session import MeetingState

    db.meetings.save_meeting(
        MeetingState(id="quiet-aftercare", started_at=datetime(2026, 9, 29, 10, 0, 0), title="Quiet")
    )
    with pytest.raises(ChannelRefused) as caught:
        render_document(db, f"{kind}:quiet-aftercare")
    assert caught.value.code == "no_summary"


def test_project_update_refuses_unpublished_by_generic_name(db) -> None:
    db.projects.create_project(project_id="p", name="Project")
    db.project_updates.insert_update(
        update_id="draft", project_id="p", project_revision=1, body_md="Draft"
    )
    with pytest.raises(ChannelRefused) as caught:
        render_document(db, "project_update:draft")
    assert caught.value.code == "not_published"


def test_aftercare_document_markdown_is_not_truncated(db) -> None:
    refs = mint_documents(db, OWNER, now=datetime(2026, 9, 29, 10, 0, 0))
    db.plugins.record_artifact(
        artifact_id="philo11-long-decisions",
        meeting_id="philo11-meeting",
        artifact_type="decisions",
        title="Long meeting decisions",
        structured_json={
            "decisions": [
                {"decision": f"Long stored decision {index} " + "x" * 80, "rationale": None}
                for index in range(400)
            ]
        },
        plugin_id="philo11-fixture",
    )

    digest = render_document(db, refs["meeting_digest"]).body_md
    followup = render_document(db, refs["meeting_followup"]).body_md
    assert len(digest) > 3800
    assert len(followup) > 3800
    assert "Long stored decision 399" in digest
    assert "Long stored decision 399" in followup


# PHILO-11-05a (Muad'Dib's ruling): the rendered text is what gets SENT to
# other people. No internal id or ref may leave the machine in it: no
# proposal, record, meeting or segment ref, no source id of any kind, and no
# hex id of 8 or more characters.
_INTERNAL = re.compile(r"prop-|record-|meeting:|#segment|decision_[0-9a-f]|brief-|pupd_|chs_")
_HEX_ID = re.compile(r"\b(?=[0-9a-f]*[a-f])(?=[0-9a-f]*\d)[0-9a-f]{8,}\b")


def test_no_rendered_document_carries_an_internal_id(db, tmp_path: Path) -> None:
    refs = mint_documents(
        db,
        OWNER,
        now=datetime(2026, 9, 29, 10, 0, 0),
        people_keystore_path=tmp_path / "people.key",
    )
    refs["artifact"] = mint_meeting_synthesis(db)
    refs["note"] = mint_note(db)
    source_ids = {ref.split(":", 1)[1] for ref in refs.values()}
    artifact_source_ids: set[str] = set()
    with db._connection() as conn:
        source_ids |= {str(r[0]) for r in conn.execute("SELECT source_ref FROM decision_record_sources")}
        source_ids |= {str(r[0]) for r in conn.execute("SELECT id FROM decision_records")}
        artifact_source_ids = {str(r[0]) for r in conn.execute("SELECT source_ref FROM artifact_sources")}
    leaks: list[str] = []
    for kind, ref in refs.items():
        document = render_document(db, ref)
        # The body is the text that is sent; the title and label name the saved file.
        text = "\n".join((document.body_md, document.title, document.label))
        if kind == "artifact":
            text += "\n" + document.slug
        for pattern in (_INTERNAL, _HEX_ID):
            leaks += [f"{kind}: {m.group(0)!r}" for m in pattern.finditer(text)]
        leaks += [f"{kind}: source id {sid!r}" for sid in source_ids if sid and sid in text]
        if kind == "artifact":
            leaks += [f"{kind}: artifact lineage id {sid!r}" for sid in artifact_source_ids if sid and sid in text]
    assert not leaks, leaks


def test_a_decision_record_names_its_sources_as_a_person_recognizes_them(db, tmp_path: Path) -> None:
    refs = mint_documents(
        db,
        OWNER,
        now=datetime(2026, 9, 29, 10, 0, 0),
        people_keystore_path=tmp_path / "people.key",
    )
    body = render_document(db, refs["decision_record"]).body_md
    meeting = db.meetings.get_meeting(refs["meeting_summary"].split(":", 1)[1])
    assert "## Sources" in body
    assert f"{meeting.title}, {meeting.started_at:%-d %b %Y}" in body, body
