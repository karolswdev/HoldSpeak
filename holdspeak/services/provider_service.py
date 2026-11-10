"""The provider adapters behind the declared provider rows (2026-11-09, ops/connections).

``holdspeak/provider_operations.py`` binds every ``provider.*`` row here. The
three adapters (``github_provider.py``, ``jira_provider.py``,
``confluence_provider.py``) stay the services; this holds no state and adds
no verb: it reads the adapter the hub composed at each call, and refuses by
name (``provider_not_configured``, 404) where there is none, as both
hand-written transports did.
"""
from __future__ import annotations

from typing import Any, Callable

from .errors import ServiceError

_LABELS = {"github": "GitHub", "jira": "Jira", "confluence": "Confluence"}


class ProviderService:
    """``adapters(name)``: the composed adapter for ``github``, ``jira`` or ``confluence``, or ``None``."""

    def __init__(self, adapters: Callable[[str], Any]) -> None:
        self._adapters = adapters

    def adapter(self, name: str) -> Any:
        found = self._adapters(name)
        if found is None:
            raise ServiceError("provider_not_configured", f"{_LABELS[name]} provider is not configured",
                               context={"status": 404})
        return found

    @property
    def github(self) -> Any:
        return self.adapter("github")

    @property
    def jira(self) -> Any:
        return self.adapter("jira")

    @property
    def confluence(self) -> Any:
        return self.adapter("confluence")

    def providers(self, principal: Any) -> list[dict[str, Any]]:
        """The provider manifests: native, then each composed adapter's. No CLI runs."""
        from .provider_manifest_service import collect_provider_manifests

        return collect_provider_manifests(github_adapter=self._adapters("github"), jira_adapter=self._adapters("jira"),
                                          confluence_adapter=self._adapters("confluence"), principal=principal)


def from_context(source: Any) -> ProviderService:
    """The hub's adapters (``<name>_provider`` on its context or root), read at each call."""
    return ProviderService(lambda name: getattr(source, f"{name}_provider", None))
