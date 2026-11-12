# Parked: proposal answers use the declared family and composed service.
TOOLS = [
    _mcp_tool(
        "proposal.confirm",
        "Confirm a follow-through proposal, writing the decision record or action item through the kernel. Optionally amend text, owner, or due before confirming.",
        {
            "proposal_id": {"type": "string", "description": "Proposal identifier."},
            "text": {"type": "string", "description": "Amended text (optional; original kept when omitted)."},
            "owner": {"type": "string", "description": "Accountable owner (optional)."},
            "due": {"type": "string", "description": "ISO-8601 due date (optional)."},
        },
        ["proposal_id"],
    ),
    _mcp_tool(
        "proposal.dismiss",
        "Dismiss a follow-through proposal without creating any record.",
        {"proposal_id": {"type": "string", "description": "Proposal identifier."}},
        ["proposal_id"],
    ),
]
class _ParkedBody:
    def dispatch(name, args, principal, db):
        if name == "proposal.confirm":
            from holdspeak.services.proposal_bridge_service import ProposalBridgeService as _PBS2
            pbs = _PBS2(db)
            return pbs.confirm_proposal(principal, str(args.get("proposal_id") or ""), text=args.get("text"), owner=args.get("owner"), due=args.get("due"))
        if name == "proposal.dismiss":
            from holdspeak.services.proposal_bridge_service import ProposalBridgeService as _PBS3
            pbs = _PBS3(db)
            return pbs.dismiss_proposal(principal, str(args.get("proposal_id") or ""))
