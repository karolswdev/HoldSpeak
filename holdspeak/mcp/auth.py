"""Environment-derived configuration and authority for the MCP sidecar."""
from __future__ import annotations

import os
from dataclasses import dataclass

from holdspeak.principals import Principal, PrincipalKind


@dataclass(frozen=True)
class MCPAuth:
    """Process-boundary principal for the MCP stdio sidecar.

    The sidecar runs as a child of the same user process that owns the
    HoldSpeak database.  No network authentication is performed: the
    process boundary IS the trust boundary, and the principal is always
    PrincipalKind.OWNER.

    When HOLDSPEAK_TOKEN is set, the identity label is 'mcp-token' (so
    observer events can distinguish token-bearing clients); otherwise it
    is 'local-mcp'.  Both are OWNER -- the token does not gate access.
    """

    principal: Principal


def resolve_auth(environ: dict[str, str] | None = None) -> MCPAuth:
    """Resolve the sidecar principal from the process environment."""
    env = os.environ if environ is None else environ
    token = str(env.get("HOLDSPEAK_TOKEN") or "").strip()
    identity = "mcp-token" if token else "local-mcp"
    return MCPAuth(principal=Principal(PrincipalKind.OWNER, identity))
