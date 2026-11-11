# PARKED: the legacy refusal is a declared aftercare service operation.
class _ParkedBody:
    @router.post("/api/meetings/{meeting_id}/export/slack")
    def api_export_meeting_to_slack(meeting_id: str, request: Request) -> Any:
        # PHILO-11-02 D1: retain the legacy route as a named capability
        # refusal while Slack delivery moves to channel document operations.
        del meeting_id, request
        return _error(
            ValidationError("slack_moved_to_channel", code="slack_moved_to_channel"),
            "Slack export is parked",
        )
