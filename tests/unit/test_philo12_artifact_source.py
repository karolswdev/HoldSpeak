"""PHILO-12-01 — artifact source bytes and named refusals."""
from __future__ import annotations

import sqlite3
from pathlib import Path
import sys

import pytest

from holdspeak.db import get_database, reset_database
from holdspeak.runtime import composition
from holdspeak.services.channel_contract import ChannelRefused, SIZE_LIMITS
from holdspeak.services.document_sources import render_document

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _philo10_send import _boot, destination  # noqa: E402
from _philo12_artifacts import mint_ask_keep, mint_meeting_synthesis, mint_run_output
from test_philo5_the_loop import Hub  # noqa: E402


@pytest.fixture
def db(tmp_path: Path):
    reset_database()
    database = get_database(tmp_path / "holdspeak.db")
    yield database
    reset_database()


@pytest.fixture
def hub(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    yield _boot(tmp_path, monkeypatch)
    reset_database()
    composition.install(composition.bare(label="pytest"))


def test_real_producers_render_stored_artifact_body(db) -> None:
    refs = {
        "synthesis": mint_meeting_synthesis(db),
        "run": mint_run_output(db),
        "ask_keep": mint_ask_keep(db),
    }

    synthesis = render_document(db, refs["synthesis"])
    stored = db.plugins.get_artifact(refs["synthesis"].split(":", 1)[1])
    assert stored is not None
    expected_body = stored.body_markdown.split("\n\n- Source windows:", 1)[0]
    assert synthesis.body_md == expected_body
    assert "The synthesis producer stored this body." in synthesis.body_md
    assert "Source windows:" not in synthesis.body_md
    assert "Source plugin runs:" not in synthesis.body_md
    assert synthesis.label == "ARTIFACT · REQUIREMENTS"
    artifact_id = refs["synthesis"].split(":", 1)[1]
    assert artifact_id not in synthesis.title
    assert artifact_id not in synthesis.label
    assert artifact_id not in synthesis.slug

    assert render_document(db, refs["run"]).body_md == "The real run output body."
    assert render_document(db, refs["ask_keep"]).body_md == "The real Ask Keep body."


def test_authored_footer_lookalike_stays(db) -> None:
    db.plugins.record_artifact(
        artifact_id="philo12-authored",
        meeting_id="",
        artifact_type="plugin_output",
        title="Authored source",
        body_markdown="Authored text\n\n- Source windows: authored-window\n- Source plugin runs: authored-run",
        sources=[{"source_type": "ask", "source_ref": "authored"}],
    )

    document = render_document(db, "artifact:philo12-authored")

    assert "Source windows: authored-window" in document.body_md
    assert "Source plugin runs: authored-run" in document.body_md


def test_footer_lookalike_inside_code_stays(db) -> None:
    db.plugins.record_artifact(
        artifact_id="philo12-code",
        meeting_id="",
        artifact_type="plugin_output",
        title="Authored code",
        body_markdown=(
            "```text\n- Source windows: philo12-window\n"
            "- Source plugin runs: philo12-run\n```"
        ),
        sources=[{"source_type": "plugin_run", "source_ref": "philo12-run"}],
    )

    document = render_document(db, "artifact:philo12-code")

    assert "Source windows: philo12-window" in document.body_md
    assert "Source plugin runs: philo12-run" in document.body_md


@pytest.mark.parametrize(
    ("line", "replacement"),
    [
        ("windows", "different-window"),
        ("plugin runs", "different-run"),
    ],
)
def test_synthesis_footer_with_mismatched_lineage_stays_byte_for_byte(
    db, line: str, replacement: str
) -> None:
    ref = mint_meeting_synthesis(db)
    artifact_id = ref.split(":", 1)[1]
    stored = db.plugins.get_artifact(artifact_id)
    assert stored is not None
    lineage = {source["source_type"]: source["source_ref"] for source in stored.sources}
    original = (
        f"- Source windows: {lineage['intent_window']}"
        if line == "windows"
        else f"- Source plugin runs: {lineage['plugin_run']}"
    )
    altered = stored.body_markdown.replace(original, f"- Source {line}: {replacement}")
    assert altered != stored.body_markdown
    with db._connection() as conn:
        conn.execute("UPDATE artifacts SET body_markdown = ? WHERE id = ?", (altered, artifact_id))

    document = render_document(db, ref)

    assert document.body_md == altered


def test_synthesis_footer_with_duplicate_lineage_id_stays_byte_for_byte(db) -> None:
    ref = mint_meeting_synthesis(db)
    artifact_id = ref.split(":", 1)[1]
    stored = db.plugins.get_artifact(artifact_id)
    assert stored is not None
    lineage = {source["source_type"]: source["source_ref"] for source in stored.sources}
    original = f"- Source windows: {lineage['intent_window']}"
    altered = stored.body_markdown.replace(
        original,
        f"- Source windows: {lineage['intent_window']}, {lineage['intent_window']}",
    )
    assert altered != stored.body_markdown
    with db._connection() as conn:
        conn.execute("UPDATE artifacts SET body_markdown = ? WHERE id = ?", (altered, artifact_id))

    document = render_document(db, ref)

    assert document.body_md == altered


def test_synthesis_footer_removal_preserves_authored_prefix_bytes(db) -> None:
    ref = mint_meeting_synthesis(db)
    artifact_id = ref.split(":", 1)[1]
    stored = db.plugins.get_artifact(artifact_id)
    assert stored is not None
    footer_start = stored.body_markdown.index("\n\n- Source windows:")
    authored_prefix = (
        stored.body_markdown[:footer_start]
        + "\n\n```python\nprint('keep this code')\n```  \n"
    )
    altered = authored_prefix + stored.body_markdown[footer_start:]
    with db._connection() as conn:
        conn.execute("UPDATE artifacts SET body_markdown = ? WHERE id = ?", (altered, artifact_id))

    document = render_document(db, ref)

    assert document.body_md == authored_prefix


@pytest.mark.parametrize(
    ("artifact_id", "body", "code"),
    [
        ("philo12-empty", "   ", "artifact_body_missing"),
    ],
)
def test_artifact_body_refusals(db, artifact_id: str, body: str, code: str) -> None:
    db.plugins.record_artifact(
        artifact_id=artifact_id,
        meeting_id="",
        artifact_type="plugin_output",
        title="Body refusal",
        body_markdown=body,
    )

    with pytest.raises(ChannelRefused) as caught:
        render_document(db, f"artifact:{artifact_id}")

    assert caught.value.code == code


def test_artifact_not_text_checks_raw_stored_value(db) -> None:
    db.plugins.record_artifact(
        artifact_id="philo12-binary",
        meeting_id="",
        artifact_type="plugin_output",
        title="Binary body",
        body_markdown="placeholder",
    )
    with db._connection() as conn:
        conn.execute(
            "UPDATE artifacts SET body_markdown = ? WHERE id = ?",
            (sqlite3.Binary(b"\\x89PNG\\x00"), "philo12-binary"),
        )

    with pytest.raises(ChannelRefused) as caught:
        render_document(db, "artifact:philo12-binary")

    assert caught.value.code == "artifact_not_text"


@pytest.mark.parametrize(
    ("document_ref", "code"),
    [("artifact:missing", "document_not_found"), ("artifact:", "document_kind_unknown")],
)
def test_artifact_missing_id_is_named(db, document_ref: str, code: str) -> None:
    with pytest.raises(ChannelRefused) as caught:
        render_document(db, document_ref)

    assert caught.value.code == code


def test_artifact_size_uses_existing_channel_refusal(hub: Hub, tmp_path: Path) -> None:
    ref = mint_ask_keep(hub.db, body="x" * (SIZE_LIMITS["file"][0] + 1))
    destination_id = destination(hub, tmp_path / "artifact-out")

    response = hub.client.post(
        "/api/channels/preview",
        json={"document_ref": ref, "destination_id": destination_id},
    )

    assert response.status_code == 400, response.text
    assert response.json()["code"] == "payload_too_large:file"
