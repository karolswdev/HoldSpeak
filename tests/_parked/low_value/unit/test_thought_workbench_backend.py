# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_thought_workbench_backend.py to restore.

# ruff: noqa


# --- test_catalogue_has_eighteen_tools_and_workbench_original_resources: P1/P8: a tool count ('len(TOOLS) == 18') and a source scan for string literals
def test_catalogue_has_eighteen_tools_and_workbench_original_resources():
    assert len(thought_family.TOOLS) == 18
    tools = {tool["name"]:tool for tool in thought_family.TOOLS}
    assert all(tool["inputSchema"]["additionalProperties"] is False for tool in tools.values())
    assert tools["thought.answer_and_continue"]["inputSchema"]["required"][-1] == "workspace_cursor"
    for unchanged in ("thought.create","thought.adopt_note","thought.get_default_context",
                      "thought.replace_default_context","thought.list_context"):
        assert "workspace_cursor" not in tools[unchanged]["inputSchema"]["properties"]
    templates = {item["uriTemplate"] for item in resources.list_resources()["resourceTemplates"]}
    assert "holdspeak://thoughts/{thought_id}/workbench" in templates
    assert "holdspeak://thoughts/{thought_id}/original" in templates


# --- test_terminal_write_sites_and_dynamic_ingress_use_the_closed_vocabulary: P1/P8: a tool count ('len(TOOLS) == 18') and a source scan for string literals
def test_terminal_write_sites_and_dynamic_ingress_use_the_closed_vocabulary():
    source = Path("holdspeak/services/refinement_thought_service.py").read_text()
    persisted_literals = set(re.findall(r"terminal_code='([a-z_]+)'", source))
    assert persisted_literals <= set(_TERMINAL_CODE_CATEGORY)
    assert {"shutdown_before_dispatch","thought_missing_during_recovery",
            "restart_bound_outcome_unknown","refinement_result_stale","retry_plan_invalid",
            "retry_child_missing_after_plan","orphaned_before_dispatch_binding",
            "refinement_result_invalid","kernel_operation_missing","ask_result_unpublished"} <= persisted_literals
    assert _closed_terminal_code("new_unruled_provider_literal") == "unknown_terminal_code"
    assert _TERMINAL_CODE_CATEGORY["failed"] == "retryable"
