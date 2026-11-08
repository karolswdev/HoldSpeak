"""The parked Sequence/Workflow run kinds stay registered and are discarded.

Recovery finalizes every durable STAGED stage. A stage of an unknown kind
stops the hub at start (``projection_materializer_unknown``), so the four
kinds of the parked runner stay registered; their stage is discarded with the
reason ``parked`` and nothing is published (2026-11-08).
"""
from __future__ import annotations

import pytest

from holdspeak.db import Database
from holdspeak.kernel.parked_run_projection import KINDS
from holdspeak.kernel.projection_stager import ProjectionDiscarded, _PublicationPermit
from holdspeak.kernel.runtime import _configure


def test_parked_run_kinds_stay_registered_and_discard(tmp_path) -> None:
    db = Database(tmp_path / "parked-runs.db")
    stager = _configure(db).projection_stager
    assert set(KINDS) == {"sequence-step-output", "workflow-node-output",
                          "sequence-run-result", "workflow-run-result"}
    for kind in KINDS:
        materializer = stager._materializers[kind]
        with db._connection() as conn:
            permit = _PublicationPermit(stager, conn)
            with pytest.raises(ProjectionDiscarded) as caught:
                materializer(conn, object(), permit)
            assert caught.value.reason == "parked"
            assert permit._used, kind
