# PARKED: tool-name substrings confuse credential revocation with canonical-record promotion.

def test_canonical_promotion_names():
    from holdspeak.mcp.tools import TOOLS

    names = {str(tool["name"]) for tool in TOOLS}
    # ``phone.revoke`` revokes a paired device (#2051), not a canonical record;
    # ``briefing.revoke`` closes a briefing page link; ``decision.promote`` and
    # ``decision.promote_draft`` turn an accepted meeting decision into its
    # artifact, owner-only in the service (2026-11-09, ops/projects). None of
    # them promotes working context (the kinds below stay off MCP).
    # ``principals.agent.revoke`` and ``principals.self.revoke`` revoke an agent
    # credential (gate_operations.py, 2026-11-09), not a canonical record.
    assert not {name for name in names if "promot" in name or "revoke" in name} - {
        "phone.revoke", "briefing.revoke", "decision.promote", "decision.promote_draft",
        "principals.agent.revoke", "principals.self.revoke"}
