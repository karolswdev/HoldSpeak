# PARKED: palette properties supersede the fixed count.
from holdspeak.mcp.families.project import PROJECT_PALETTE

def test_palette_size_is_69() -> None:
    """Includes suggested sources, Confluence, four Interview setup operations and
    (PHILO-9-01) the seven item and resource tools."""
    # PHILO-9-02: + project.mark_update_delivered; MCP M6: + provider.github_pr_get;
    # 2026-11-09 (ops/connections): + the Jira and Confluence remove, the Confluence add.
    assert len(PROJECT_PALETTE) == 69
