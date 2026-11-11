# PARKED: status is a declared ActuatorProposalService operation.
class _ParkedBody:
    @router.get("/api/desk/actuators/status")
    def api_desk_actuators_status() -> Any:
        config = service._config_provider().meeting
        return {"webhook_configured": bool(config.companion_webhook_url), "github_configured": bool(config.companion_github_repo)}
