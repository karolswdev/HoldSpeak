"""W5-WORDS: the Processes window names the engine of an inference run.

The kernel's placement for an inference dispatch is a hash
(`node:inference-<sha>`); the process view carries the engine's name as
`placement_label` (the profile's label, else the revision's model)."""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from types import SimpleNamespace

from holdspeak.kernel.inference_invoke import InferenceInvokeCodec


class _Db:
    def __init__(self, label: str | None, model: str = "qwen3.8-27b") -> None:
        self._conn = sqlite3.connect(":memory:")
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("CREATE TABLE model_profile_revisions (profile_id TEXT, revision INTEGER, label TEXT)")
        if label is not None:
            self._conn.execute("INSERT INTO model_profile_revisions VALUES ('engine-a', 1, 'Old name')")
            self._conn.execute("INSERT INTO model_profile_revisions VALUES ('engine-a', 2, ?)", (label,))
        revision = SimpleNamespace(destination_id="engine-a", model=model)
        self.deployment_revisions = SimpleNamespace(get=lambda rid: revision if rid == "dr_1" else None)

    @contextmanager
    def _connection(self):
        yield self._conn


def _operation(target_ref: str) -> dict:
    return {"operation_id": "op_1", "principal_identity": "owner", "state": "succeeded", "target_ref": target_ref}


def test_the_process_view_names_the_profile_label() -> None:
    codec = InferenceInvokeCodec(_Db("Studio engine"), store=None)
    assert codec.project_process("inv_1", _operation("deployment-revision:dr_1"))["placement_label"] == "Studio engine"


def test_without_a_profile_the_model_names_it() -> None:
    codec = InferenceInvokeCodec(_Db(None), store=None)
    assert codec.project_process("inv_1", _operation("deployment-revision:dr_1"))["placement_label"] == "qwen3.8-27b"


def test_an_unknown_revision_adds_no_label() -> None:
    codec = InferenceInvokeCodec(_Db("Studio engine"), store=None)
    assert "placement_label" not in codec.project_process("inv_1", _operation("deployment-revision:gone"))
