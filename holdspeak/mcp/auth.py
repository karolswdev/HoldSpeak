"""Environment-derived configuration and authority for the MCP sidecar."""
from __future__ import annotations

import os
from dataclasses import dataclass

from holdspeak.principals import Principal, PrincipalKind

DEFAULT_HOLDSPEAK_URL = "http://127.0.0.1:8765"


@dataclass(frozen=True)
class MCPAuth:
    """Connection configuration available to MCP tools.

    The sidecar operates on the local HoldSpeak store, so its bearer is never
    emitted over stdio or included in a tool result.  A supplied bearer marks
    the caller as the owner authenticated by the hub; loopback use without a
    bearer retains the local owner convenience principal.
    """

    url: str
    principal: Principal


def resolve_auth(environ: dict[str, str] | None = None) -> MCPAuth:
    """Resolve sidecar connection settings without exposing the bearer token."""
    env = os.environ if environ is None else environ
    url = str(env.get("HOLDSPEAK_URL") or DEFAULT_HOLDSPEAK_URL).rstrip("/")
    token = str(env.get("HOLDSPEAK_TOKEN") or "").strip()
    identity = "mcp-token" if token else "local-mcp"
    return MCPAuth(url=url, principal=Principal(PrincipalKind.OWNER, identity))
