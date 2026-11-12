# Parked: answer tools read their request schema from the operation declaration.
TOOLS = [
{
        "name": "project.decide_proposal",
        "description": "Apply a decision verb (accept/edit_accept/defer/dismiss) to a review proposal.",
        "inputSchema": {
            "$id": "holdspeak://mcp/project.decide_proposal@1",
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project identifier."},
                "review_id": {"type": "string", "description": "Review window identifier."},
                "proposal_id": {"type": "string", "description": "Proposal identifier."},
                "verb": {
                    "type": "string",
                    "description": "Decision verb: accept, edit_accept, defer, or dismiss.",
                },
                "patch": {
                    "type": "object",
                    "description": "Optional patch for edit_accept verb.",
                },
                "deferred_until": {
                    "type": "string",
                    "description": "ISO-8601 date for defer verb.",
                },
                "command_id": {"type": "string", "description": "Idempotency key."},
            },
            "required": ["project_id", "review_id", "proposal_id", "verb"],
            "additionalProperties": False,
        },
    },
{
        "name": "project.accept_review",
        "description": "Atomically accept an open review. Bumps project revision, supersedes undecided proposals.",
        "inputSchema": {
            "$id": "holdspeak://mcp/project.accept_review@1",
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project identifier."},
                "review_id": {"type": "string", "description": "Review window identifier."},
                "command_id": {"type": "string", "description": "Idempotency key."},
            },
            "required": ["project_id", "review_id"],
            "additionalProperties": False,
        },
    },
{
        "name": "project.watch.retire",
        "description": "Retire a graduated watch (ACT-009). Retains history, stops evaluation.",
        "inputSchema": {
            "$id": "holdspeak://mcp/project.watch.retire@1",
            "type": "object",
            "properties": {
                "watch_id": {"type": "string", "description": "Watch identifier."},
            },
            "required": ["watch_id"],
            "additionalProperties": False,
        },
    }
]
