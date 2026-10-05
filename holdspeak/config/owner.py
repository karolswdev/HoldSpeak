"""The owner's own name and the other names people call him (first run, C1).

The needs-you rule reads these names as "me": an action item whose owner is
one of them is the owner's own work (``needs_you_membership.owner_names``).
"""
from __future__ import annotations

from dataclasses import dataclass, field

#: Longest name or alias kept. A longer value is cut, never refused.
NAME_MAX = 80
#: Most aliases kept.
ALIASES_MAX = 12


def _clean(value: object) -> str:
    return " ".join(str(value or "").split())[:NAME_MAX]


def clean_aliases(values: object, name: str = "") -> list[str]:
    """Trimmed, non-empty, unique (case-insensitive), not the name itself."""
    if isinstance(values, str):
        values = values.split(",")
    if not isinstance(values, (list, tuple)):
        return []
    seen = {name.casefold()} if name else set()
    out: list[str] = []
    for raw in values:
        alias = _clean(raw)
        key = alias.casefold()
        if not alias or key in seen:
            continue
        seen.add(key)
        out.append(alias)
        if len(out) >= ALIASES_MAX:
            break
    return out


@dataclass
class OwnerConfig:
    """Who the owner is: his name and the other names for him."""

    name: str = ""
    aliases: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.name = _clean(self.name)
        self.aliases = clean_aliases(self.aliases, self.name)

    def names(self) -> list[str]:
        """The name and every alias, as written."""
        return ([self.name] if self.name else []) + list(self.aliases)
