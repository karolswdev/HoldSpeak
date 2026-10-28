"""Processes (atlas pass 3, defect 8): each run reads by what it did for
the owner. The kernel's read gives every process a ``label`` from one map
(``holdspeak/kernel/process_words.py``); a name that is not in the map reads
as sentence words made from the operation name."""
from __future__ import annotations

from pathlib import Path

import pytest

from holdspeak import kernel
from holdspeak.db import Database
from holdspeak.kernel.process_words import PROCESS_WORDS, process_label
from holdspeak.kernel.runtime import _as_principal, _configure
from holdspeak.principals import Principal, PrincipalKind

AGENT = Principal(PrincipalKind.AGENT, "agent:proof")


@pytest.mark.parametrize(("kind", "words"), [
    ("setup.lan.scan", "Checked the LAN"),
    ("decision.create", "Made a decision"),
    ("connection.recheck", "Checked a connection"),
    ("channel.save_destination", "Saved a destination"),
    ("project.watch.something_new", "Project watch something new"),
    ("meeting.deferred-intel-job", "Summarized a meeting"),
    ("", ""),
])
def test_process_label_names_what_it_did(kind: str, words: str) -> None:
    assert process_label(kind) == words


def test_a_codec_kind_falls_back_to_the_operation_name() -> None:
    assert process_label("tool_call_hold", "tool.call") == "Ran an agent's tool"
    assert process_label("", "decision.create") == "Made a decision"
    assert process_label("authority_details", "project.unknown") == "Authority details"


def test_every_mapped_label_is_sentence_case_words() -> None:
    for kind, words in PROCESS_WORDS.items():
        assert words[:1].isupper() and "." not in words and "_" not in words, kind
        assert words != words.upper(), kind


def test_kernel_read_gives_each_process_its_label(tmp_path: Path, monkeypatch) -> None:
    import holdspeak.db.core as db_core

    database = Database(tmp_path / "kernel.db")
    monkeypatch.setattr(db_core, "_db", database)
    _configure(database, clock=lambda: 1_000.0)
    request = {
        "request_schema": 1, "request_id": "request-one", "idempotency_key": "key-one",
        "operation": {"name": "tool.call", "version": 1}, "subject_refs": ["story:HS-106-04"],
        "target": {"ref": "gate:proposal-one"},
        "arguments": {"proposal_id": "proposal-one", "tool": "Bash", "args_sha256": "a" * 64,
                      "args_head": "git status", "cwd": "/workspace", "ttl_seconds": 60},
        "placement": "node:node_proof",
    }
    with _as_principal(AGENT):
        handle = kernel.submit(request)
        objects = kernel.read([f"operation:{handle['operation_id']}"], "process", "committed")["objects"]
    # tool.call projects its own kind; the label is read by the name.
    assert objects[0]["process"]["kind"] == "tool_call_hold"
    assert objects[0]["process"]["label"] == "Ran an agent's tool"
