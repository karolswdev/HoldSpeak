"""PHILO-16 R2 (Astra MUST on 3671b90aa): a replyless import_transcriber is refused first.

A declared import_transcriber boundary without `reply` used to read as "no
double": the hub booted with the REAL Transcriber, and a case ordered
[fixture import, boundary] uploaded the WAV through it before the boundary
step refused. The rig now refuses the case before the hub starts, and the
schema requires `reply` on that boundary.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from scripts import graph_walk

REPO = Path(__file__).resolve().parents[2]
SCHEMA = REPO / "docs/internal/philo/graph/atlas.schema.json"

IMPORT = {
    "kind": "fixture",
    "path": "tests/fixtures/philo3_architect_meeting.wav",
    "route": {"method": "POST", "path": "/api/meetings/import"},
    "field": "file",
    "capture_as": "meeting_id",
    "capture_path": "meeting_id",
    "adapter": "http-route",
    "expect_status": 202,
}
REPLYLESS = {
    "kind": "boundary",
    "substitute": "import_transcriber",
    "label": "a transcript double that names no transcript",
    "adapter": "labelled-substitution",
}


def _atlas(tmp_path: Path, boundary: dict) -> Path:
    case = {
        "id": "case.r2.import_before_boundary",
        "job": "j4",
        "edge_ids": [],
        "state_id": "state.r2",
        "applicability": "applicable",
        "preconditions": [],
        "setup": [IMPORT, boundary],
        "trigger": {"kind": "api", "method": "GET", "path": "/api/meetings", "body": None},
        "expected": {"predicate": {"kind": "protocol_field", "path": "/meetings/0/id",
                                   "value": "{meeting_id}"},
                     "observe_at": "protocol: GET /api/meetings"},
        "completion_bound_s": 5,
        "viewports": [],
    }
    path = tmp_path / "atlas.json"
    path.write_text(json.dumps({"schema_version": 1, "cases": [case], "states": []}))
    return path


@pytest.mark.parametrize("boundary", [REPLYLESS, {**REPLYLESS, "reply": ""}, {**REPLYLESS, "reply": "  "}])
def test_import_before_a_replyless_boundary_is_refused_before_any_upload(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, boundary: dict,
) -> None:
    hubs: list[object] = []
    uploads: list[object] = []

    class _NoHub:
        def __init__(self, *args, **kwargs) -> None:
            hubs.append((args, kwargs))
            raise AssertionError("a hub was started for a refused case")

    monkeypatch.setattr(graph_walk, "Hub", _NoHub)
    monkeypatch.setattr(graph_walk, "_multipart_upload",
                        lambda *a, **k: uploads.append(a) or {"status": 202})

    record = graph_walk.run_case(
        _atlas(tmp_path, boundary), "case.r2.import_before_boundary",
        brain="muaddib", viewport=1440, out=tmp_path / "out",
        engine="none", build=False, headless=True,
    )

    assert record["verdict"] == "blocked"
    assert any("import_transcriber boundary declares no `reply`" in n for n in record["notes"]), record["notes"]
    assert hubs == [] and uploads == []


def test_schema_requires_a_reply_on_an_import_transcriber_boundary() -> None:
    schema = json.loads(SCHEMA.read_text())
    step_validator = Draft202012Validator({"$defs": schema["$defs"], "$ref": "#/$defs/step"})
    assert list(step_validator.iter_errors(REPLYLESS))
    assert list(step_validator.iter_errors({**REPLYLESS, "reply": ""}))
    good = {**REPLYLESS, "reply": "tests/fixtures/philo16_import_transcript.json"}
    assert not list(step_validator.iter_errors(good))
