# PARKED 2026-11-09: Explicit service calls replace dynamic MCP dispatch.
def _parked_body():
            method = getattr(service, name.rsplit(".", 1)[1])
            extra = {"repo": arguments.get("repo")} if name.endswith("clarify_repo_scope") else {}
            return method(principal, arguments["session_id"], arguments["proposal_id"], **extra)
