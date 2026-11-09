# PARKED 2026-11-09 (pipe/test-mass): kills the real hub mid-send and boots a
# second one on the same database. Owner 2026-11-08: no pipeline restarts a
# real hub. Moved from tests/unit/test_send_email_channel.py (formerly
# test_philo10_email_channel.py); the _EmailHub rig and KEY live there.

@pytest.mark.timeout(240)
@pytest.mark.parametrize("hold", ["before", "after"], ids=["killed-before-the-wire", "killed-after-the-wire"])
def test_c2_r3_a_restart_during_an_email_send_ends_unknown_once_and_never_sends_again(
    tmp_path: Path, hold: str,
) -> None:
    home, wire_log = tmp_path / "home", tmp_path / "wire.jsonl"
    home.mkdir()
    first = _EmailHub(home, hold, wire_log)
    try:
        assert first.call("PUT", "/api/channels/email-keys/sendgrid", {"api_key": KEY, "provider": "sendgrid"})[0] == 200
        _s, made = first.call("POST", "/api/projects", {"name": "Payments ledger cutover"})
        _s, drafted = first.call("POST", f"/api/projects/{made['project']['id']}/updates/draft", {})
        update = drafted["update"]["id"]
        # PHILO-15 B64: an update with no verified claim is refused; the owner's saved line is reviewed.
        assert first.call("PUT", f"/api/updates/{update}", {"body_md": "## Progress\n\nThe ledger cutover is on track.\n"})[0] == 200
        assert first.call("POST", f"/api/updates/{update}/publish", {})[0] == 200
        status, saved = first.call("POST", "/api/channels/destinations", {
            "name": "Priya by email", "channel": "email", "provider": "sendgrid", "from_email": "karol@example.com",
            "to": ["priya@example.com"]})
        assert status == 200, saved
        _s, preview = first.call("POST", "/api/channels/preview", {"document_ref": f"project_update:{update}",
                                                                   "destination_id": saved["destination"]["id"]})
        body = {"document_ref": f"project_update:{update}", "destination_id": saved["destination"]["id"],
                "preview_digest": preview["payload_digest"], "command_id": f"restart-{hold}"}

        def pressing() -> None:
            try:
                first.call("POST", "/api/channels/send", body, timeout=120)
            except OSError:  # the process is killed under the caller
                pass

        threading.Thread(target=pressing, daemon=True).start()
        row = _until(lambda: next(iter(_rows(home, "SELECT * FROM channel_sends WHERE state='dispatching'")), None))
        if hold == "after":
            _until(lambda: wire_log.exists() and wire_log.read_text().strip())
    finally:
        first.kill()
    second = _EmailHub(home, "", wire_log)
    try:
        [settled] = _rows(home, "SELECT * FROM channel_sends WHERE id=?", row["id"])
        assert (settled["state"], settled["reason"]) == ("unknown", "interrupted"), settled
        [operation] = _rows(home, "SELECT o.state, r.outcome FROM kernel_operations o JOIN kernel_receipts r"
                                  " ON r.operation_id=o.operation_id WHERE o.operation_id=?", row["send_operation_id"])
        assert operation == {"state": "indeterminate", "outcome": "hub_restart_during_send"}, operation
        assert _rows(home, "SELECT outcome FROM project_update_deliveries WHERE update_id=?", update) == [
            {"outcome": "unknown"}]
        status, replayed = second.call("POST", "/api/channels/send", body)
        assert status == 200 and (replayed["outcome"], replayed["send"]["reason"]) == ("unknown", "interrupted")
        sent_lines = wire_log.read_text().splitlines() if wire_log.exists() else []
        assert len(sent_lines) == (1 if hold == "after" else 0)  # never sent again
        assert len(_rows(home, "SELECT 1 FROM project_update_deliveries WHERE update_id=?", update)) == 1
        for path in home.rglob("*"):
            if path.is_file():
                assert KEY_MARK.encode() not in path.read_bytes(), path
    finally:
        second.kill()


