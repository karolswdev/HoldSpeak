"""HS-201-09 — connect an engine from the face.

Four fences for the four service-side truths story 09 needs:

1. the draft the FACE posts is exactly the draft the service accepts
   (rehearsal defect 1: the face posted five keys, the service demanded
   eight, and every "Add an engine..." ended in 400 "Provider draft is
   invalid.");
2. OFF on the summary group CLEARS the exact `meeting.deferred_analysis`
   assignment (defect 3: OFF changed nothing and the next import ran on
   the LAN again);
3. after that clear the summary projection says OFF, so a reopened
   Models shows the applied truth and not a fresh proposal (defect 4);
4. a TOOL INCOMPATIBLE repair carries a plain reason, not an issue code
   (defect 7).

Isolated HOME everywhere: every database is under ``tmp_path``.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from holdspeak.config import Config
from holdspeak.db import Database
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.errors import NotFound
from holdspeak.services.inference_acquisition_service import (
    InferenceAcquisitionApplicationService,
)
from holdspeak.services.inference_setup_service import InferenceSetupApplicationService
from holdspeak.services.model_library_service import ModelLibraryApplicationService

REPO = Path(__file__).resolve().parents[2]
DRAFT_MODULE = REPO / "web/src/features/concierge/endpointDraft.ts"
OWNER = Principal(PrincipalKind.OWNER, "hs201-09-owner")

# The one endpoint the rehearsal used; only its SHAPE matters here.
LAN_URL = "http://192.168.1.43:8080/v1"
LAN_MODEL = "Qwen3.6-35B-A3B-UD-Q5_K_XL.gguf"


def _face_draft_keys() -> set[str]:
    """The keys the FACE posts, read from the face's own declaration."""
    assert DRAFT_MODULE.exists(), f"{DRAFT_MODULE} does not exist"
    source = DRAFT_MODULE.read_text(encoding="utf-8")
    match = re.search(
        r"export const ENDPOINT_DRAFT_KEYS\s*=\s*\[(?P<body>.*?)\]", source, re.S
    )
    assert match is not None, "ENDPOINT_DRAFT_KEYS is not declared in endpointDraft.ts"
    return set(re.findall(r'"([^"]+)"', match.group("body")))


def _library(tmp_path: Path) -> ModelLibraryApplicationService:
    db = Database(tmp_path / "hs201-09.db")
    setup = InferenceSetupApplicationService(
        db, config_provider=Config, home_provider=lambda: tmp_path / "home"
    )
    acquisition = InferenceAcquisitionApplicationService(
        db,
        setup_service=setup,
        model_root=tmp_path / "custody",
        home_provider=lambda: tmp_path / "home",
    )
    return ModelLibraryApplicationService(
        db, setup_service=setup, acquisition_service=acquisition
    )


# ---- 1. the face's draft is the service's draft ------------------------------


def test_face_draft_keys_are_exactly_the_endpoint_drafts_the_service_accepts() -> None:
    """The face's declared keys equal the service's allowed endpoint set."""
    allowed = {
        "request_id",
        "profile_id",
        "expected_profile_revision",
        "label",
        "provider_family",
        "model",
        "endpoint",
        "requires_key",
    }
    assert _face_draft_keys() == allowed


def test_define_endpoint_accepts_the_face_draft(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A body with the face's keys is accepted and names a profile revision."""
    monkeypatch.setattr(
        "holdspeak.setup_runtime.discover_endpoint_models",
        lambda *_a, **_k: {"ok": True, "models": [LAN_MODEL]},
    )
    service = _library(tmp_path)
    body = {
        "request_id": "concierge-hs201-09",
        "profile_id": "engine-192-168-1-43-8080",
        "expected_profile_revision": 0,
        "label": "192.168.1.43:8080",
        "provider_family": "openai_compatible",
        "model": LAN_MODEL,
        "endpoint": LAN_URL,
        "requires_key": False,
    }
    assert set(body) == _face_draft_keys()

    receipt = service.define_endpoint(OWNER, body, None)

    assert receipt["provider"]["profile_id"] == "engine-192-168-1-43-8080"
    assert int(receipt["provider"]["profile_revision"]) >= 1
    assert receipt["receipt"]["assignments_unchanged"] is True


# ---- 2. OFF clears the exact summary assignment ------------------------------


def _fake_db() -> Any:
    db = MagicMock()
    conn = MagicMock()
    conn.__enter__ = MagicMock(return_value=conn)
    conn.__exit__ = MagicMock(return_value=False)
    db._connection = MagicMock(return_value=conn)
    return db


def test_apply_off_on_the_summary_group_clears_the_exact_capability() -> None:
    from holdspeak.services.concierge_service import apply

    svc = MagicMock()
    svc.get_assignment.return_value = {
        "revision": 3,
        "entries": [
            {
                "profile_id": "lan-43-qwen",
                "profile_revision": 2,
                "label": "Qwen3.6 35B A3B",
                "boundary": "private_network",
                "readiness": "ready",
            }
        ],
    }

    result = apply(
        rows=[{"group": "meetings", "engineId": "OFF", "state": "READY"}],
        engines=[],
        assignment_service=svc,
        principal=MagicMock(),
        db=_fake_db(),
    )

    assert svc.clear_assignment.called, "OFF on the summary group cleared nothing"
    body = svc.clear_assignment.call_args.args[1]
    assert body["scope"] == {
        "kind": "capability",
        "capability_id": "meeting.deferred_analysis",
    }
    assert body["capability_id"] == "meeting.deferred_analysis"
    assert body["expected_revision"] == 3
    row = result["results"][0]
    assert row["group"] == "meetings"
    assert row["state"] == "OFF"
    assert row["capabilityId"] == "meeting.deferred_analysis"


def test_apply_off_on_the_summary_group_with_nothing_assigned_clears_nothing() -> None:
    from holdspeak.services.concierge_service import apply

    svc = MagicMock()
    svc.get_assignment.side_effect = NotFound("inference assignment", "x")

    result = apply(
        rows=[{"group": "meetings", "engineId": "OFF", "state": "READY"}],
        engines=[],
        assignment_service=svc,
        principal=MagicMock(),
        db=_fake_db(),
    )

    assert not svc.clear_assignment.called
    assert result["results"][0]["state"] == "OFF"


# ---- 3. the projection says OFF after a clear --------------------------------


def _head_db(revision: int, cleared: int) -> Any:
    db = MagicMock()
    conn = MagicMock()
    conn.__enter__ = MagicMock(return_value=conn)
    conn.__exit__ = MagicMock(return_value=False)
    conn.execute.return_value.fetchone.return_value = {
        "revision": revision,
        "cleared": cleared,
    }
    db._connection = MagicMock(return_value=conn)
    return db


def test_summary_projection_says_off_after_the_assignment_was_cleared() -> None:
    from holdspeak.services.concierge_service import summary_assignment_projection

    svc = MagicMock()
    svc.get_assignment.side_effect = NotFound("inference assignment", "x")

    projection = summary_assignment_projection(
        assignment_service=svc, principal=MagicMock(), db=_head_db(4, 1)
    )

    assert projection["status"] == "off"
    assert projection["assignmentRevision"] == 4
    assert projection["profileId"] is None


def test_summary_projection_stays_unassigned_when_nothing_was_ever_written() -> None:
    from holdspeak.services.concierge_service import summary_assignment_projection

    svc = MagicMock()
    svc.get_assignment.side_effect = NotFound("inference assignment", "x")
    db = MagicMock()
    conn = MagicMock()
    conn.__enter__ = MagicMock(return_value=conn)
    conn.__exit__ = MagicMock(return_value=False)
    conn.execute.return_value.fetchone.return_value = None
    db._connection = MagicMock(return_value=conn)

    projection = summary_assignment_projection(
        assignment_service=svc, principal=MagicMock(), db=db
    )

    assert projection["status"] == "unassigned"
    assert projection["assignmentRevision"] == 0


# ---- 4. TOOL INCOMPATIBLE carries a plain reason -----------------------------


def test_tool_incompatible_repair_carries_a_plain_reason() -> None:
    from holdspeak.services.concierge_service import repairs

    svc = MagicMock()
    svc.assignment_summary.return_value = {
        "rows": [
            {
                "id": "agents_tools",
                "assignment": {
                    "entries": [
                        {"profile_id": "lan-43-qwen", "label": "Qwen3.6 35B A3B"}
                    ],
                    "issues": [
                        {
                            "code": "structured_tools_unqualified",
                            "severity": "blocking",
                        }
                    ],
                },
            }
        ]
    }

    rows = repairs(db=_fake_db(), assignment_service=svc, principal=MagicMock())

    incompatible = [r for r in rows if r["token"] == "TOOL INCOMPATIBLE"]
    assert incompatible, rows
    detail = incompatible[0]["detail"]
    assert detail and detail[0].isupper() and detail.endswith(".")
    assert "_" not in detail, f"an issue code reached the face: {detail!r}"
