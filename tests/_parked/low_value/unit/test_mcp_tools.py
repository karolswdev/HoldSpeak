# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_mcp_tools.py to restore.

# ruff: noqa


# --- test_retired_router_tools_are_absent_from_the_catalogue: P8: guards that router tools retired in an earlier phase stay absent from the catalogue
def test_retired_router_tools_are_absent_from_the_catalogue() -> None:
    names = {tool["name"] for tool in mcp_tools.TOOLS}
    retired = {
        "ask.models",
        "inference.download_and_use", "inference.use_existing_model",
        "destination.list", "destination.get", "destination.create",
        "destination.update", "destination.delete",
        "model_profile.list", "model_profile.get", "model_profile.create",
        "model_profile.bind", "model_profile.probe", "model_profile.unbind",
        "model_profile.delete",
        # Sequences and Workflows are parked (2026-11-08): Programs run work.
        "sequence.run", "sequence.cancel", "workflow.run", "workflow.cancel",
        # The watch fold (2026-11-08): the reactions family is parked.
        "watch.list", "watch.create", "watch.set_enabled", "watch.refresh", "watch.preview",
        "event.list", "reaction.presets", "reaction.list", "reaction.create",
        "reaction.set_enabled", "reaction.process",
        # One name (2026-11-08): the automation tools are automation.* only.
        "workbench.list", "workbench.get", "workbench.create", "workbench.update",
        "workbench.delete", "workbench.run", "workbench.results", "workbench.cancel",
    }
    assert not (names & retired)
    assert "inference.cancel_model_acquisition" in names
