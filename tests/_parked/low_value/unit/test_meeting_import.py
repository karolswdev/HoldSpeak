# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_meeting_import.py to restore.

# ruff: noqa


# --- test_import_before_a_replyless_boundary_is_refused_before_any_upload: P2: tests the graph-walk test rig and its atlas schema, not the meeting import
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


# --- test_schema_requires_a_reply_on_an_import_transcriber_boundary: P2: tests the graph-walk test rig and its atlas schema, not the meeting import
def test_schema_requires_a_reply_on_an_import_transcriber_boundary() -> None:
    schema = json.loads(SCHEMA.read_text())
    step_validator = Draft202012Validator({"$defs": schema["$defs"], "$ref": "#/$defs/step"})
    assert list(step_validator.iter_errors(REPLYLESS))
    assert list(step_validator.iter_errors({**REPLYLESS, "reply": ""}))
    good = {**REPLYLESS, "reply": "tests/fixtures/philo16_import_transcript.json"}
    assert not list(step_validator.iter_errors(good))
