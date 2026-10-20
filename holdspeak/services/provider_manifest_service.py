"""Provider manifest assembly shared by the HTTP and MCP surfaces.

The manifest is a wire contract.  Keep its provider inventory and readiness
assembly in the service layer so a transport cannot grow a second version.
"""
from __future__ import annotations

from typing import Any


# The native provider family is always available locally.  Its shape mirrors
# the provider adapter manifests used by the external connectors.
_NATIVE_PROVIDERS: list[dict[str, Any]] = [
    {
        "provider_id": "native",
        "transport": "local_domain",
        "capabilities": {
            "discover": False,
            "read": True,
            "subscribe": False,
            "effect": False,
        },
        "families": ["meetings", "decisions", "door"],
    },
]


def collect_provider_manifests(
    *,
    github_adapter: Any = None,
    jira_adapter: Any = None,
    confluence_adapter: Any = None,
    principal: Any = None,
) -> list[dict[str, Any]]:
    """Build the provider manifest list for HTTP and MCP.

    Adapters are optional: ``None`` means the provider is not configured and
    is omitted.  Readiness is derived by the adapter and does not run a CLI.
    """
    providers: list[dict[str, Any]] = list(_NATIVE_PROVIDERS)
    if github_adapter is not None:
        entry = github_adapter.manifest()
        if principal is not None and hasattr(github_adapter, "readiness"):
            entry["readiness"] = github_adapter.readiness(principal)
        providers.append(entry)
    if jira_adapter is not None:
        entry = jira_adapter.manifest()
        if principal is not None and hasattr(jira_adapter, "readiness"):
            entry["readiness"] = jira_adapter.readiness(principal)
        providers.append(entry)
    if confluence_adapter is not None:
        entry = confluence_adapter.manifest()
        if principal is not None and hasattr(confluence_adapter, "readiness"):
            entry["readiness"] = confluence_adapter.readiness(principal)
        providers.append(entry)
    return providers
