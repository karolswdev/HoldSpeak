"""PHILO-11-01 — the eight stored channel document sources."""
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


def test_registry_declares_the_eight_kinds() -> None:
    assert tuple(DOCUMENT_SOURCES) == (
        "project_update",
        "monday_brief",
        "desk_decision",
        "meeting_decision",
        "decision_record",
        "meeting_summary",
        "meeting_digest",
        "meeting_followup",
    )


def test_real_producers_render_all_eight_sources(db, tmp_path: Path) -> None:
    refs = mint_documents(
        db,
        OWNER,
        now=datetime(2026, 9, 29, 10, 0, 0),
        people_keystore_path=tmp_path / "people.key",
    )
    rendered = {kind: render_document(db, ref) for kind, ref in refs.items()}

    assert set(rendered) == set(DOCUMENT_SOURCES)
    for kind, document in rendered.items():
        assert document.ref == refs[kind]
        assert document.title
        assert document.body_md.strip(), kind
        assert document.label.strip(), kind

    brief = rendered["monday_brief"].body_md
    assert "Avery" in brief
    assert "You owe: 1" in brief
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
    assert "- meeting: philo11-meeting" in record_body
    assert "- artifact: philo11-decisions" in record_body
    assert "## Successor" in record_body
    assert "## Summary" in rendered["meeting_summary"].body_md
    assert "The channel reads durable records." in rendered["meeting_summary"].body_md
    assert "## Topics" in rendered["meeting_summary"].body_md
    assert "## What we decided" in rendered["meeting_digest"].body_md
    assert "Use one document registry" in rendered["meeting_digest"].body_md
    assert "## Still open" in rendered["meeting_digest"].body_md
    assert "Follow-up" in rendered["meeting_followup"].body_md
    contract_brief = contract_render_document(db, refs["monday_brief"])
    assert "Avery" in contract_brief.body_md
    for kind, ref in refs.items():
        assert contract_render_document(db, ref).body_md.strip(), kind


def test_monday_brief_names_unavailable_people_once(
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

    assert sum(line == "PEOPLE · UNAVAILABLE" for line in body.splitlines()) == 1


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
