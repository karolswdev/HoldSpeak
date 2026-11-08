"""The parked Sequence and Workflow runs' projection kinds (parked 2026-11-08).

The runner is parked (``holdspeak/services/_parked/sequence_workflow_service.py``);
no new stage of these kinds is made. A real database can still hold a durable
stage from a run that stopped mid-publication, and recovery finalizes every
STAGED stage it finds. An unknown kind would stop the hub at start
(``projection_materializer_unknown``), so each kind stays registered and its
stage is discarded with the reason ``parked``: nothing is published.
"""
from __future__ import annotations

from typing import Any

from .projection_stager import ProjectionDiscarded

KINDS = ("sequence-step-output", "workflow-node-output", "sequence-run-result", "workflow-run-result")


def discard_parked(conn: Any, stage: Any, permit: Any) -> dict[str, Any]:
    permit.use(conn)
    raise ProjectionDiscarded("parked")


def register(stager: Any) -> None:
    for kind in KINDS:
        try:
            stager.register(kind, discard_parked)
        except ValueError:
            pass
