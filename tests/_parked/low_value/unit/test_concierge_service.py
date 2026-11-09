# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_concierge_service.py to restore.

# ruff: noqa


# --- test_apply_writes_receipt: P2: asserts a MagicMock connection's execute was called at least once; test_a_written_limited_group_is_an_applied_receipt reads the real receipt
def test_apply_writes_receipt():
    """Apply writes one kernel receipt."""
    from holdspeak.services.concierge_service import apply, STATE_READY

    mock_svc = MagicMock()
    mock_svc.get_assignment.side_effect = Exception("not found")
    mock_svc.set_assignment.return_value = {"revision": 1}

    db = FakeDB()

    rows = [
        {"group": "thoughts_notes", "engineId": "lan:qwen", "state": STATE_READY},
    ]
    engines = [
        {"id": "lan:qwen", "kind": "lan", "profileId": "qwen-profile"},
    ]

    result = apply(
        rows=rows,
        engines=engines,
        assignment_service=mock_svc,
        principal=MagicMock(),
        db=db,
    )

    assert result["receipt"].startswith("concierge-apply-")
    # Verify the DB was asked to write
    conn = db._conn_mock.__enter__()
    assert conn.execute.call_count >= 1


# --- test_download_returns_job_shape: P6/P7: key presence on a MagicMock answer plus called_once; the next test checks the job id and progress values
def test_download_returns_job_shape():
    """Download returns the job id + progress shape."""
    from holdspeak.services.concierge_service import download

    mock_lib_svc = MagicMock()
    mock_lib_svc.download.return_value = {
        "receipt": {"kind": "catalog_download"},
    }

    result = download(
        preset_id="qwen-0.8b-preset",
        model_library_service=mock_lib_svc,
        principal=MagicMock(),
        catalog_revision=1,
    )

    assert "presetId" in result
    assert result["presetId"] == "qwen-0.8b-preset"
    assert "progress" in result
    assert "received" in result["progress"]
    assert "total" in result["progress"]
    mock_lib_svc.download.assert_called_once()


# --- test_propose_has_no_internal_chat_row: P1/P5: filters a constant list; test_propose_reads_ready... asserts chat_practice is not a row
def test_propose_has_no_internal_chat_row():
    """PHILO-15 10 (Astra r1, finding 5): "Chat" held only chat compaction and
    the chat guardrail, internal works; desk chat (chat.turn) is in Thoughts &
    notes. The internal group is no longer an owner row."""
    from holdspeak.services.concierge_service import ASSIGNMENT_GROUPS

    assert [g for g in ASSIGNMENT_GROUPS if g[0] == "chat_practice"] == []
