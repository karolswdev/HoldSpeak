"""First run: the optional steps the owner skipped (owner ruling 2026-10-06).

Calendar and Connections are optional on the first-run screen. A Skip press
writes the step here, so a reload does not bring the step back. Settings
still sets up a calendar or a connection later.
"""
from __future__ import annotations

from dataclasses import dataclass, field

#: The steps a Skip press can mark. Local AI, You and First words are the
#: product and have no Skip.
SKIPPABLE = ("calendar", "connections")


def clean_skipped(values: object) -> list[str]:
    """Known step names only, each once, in SKIPPABLE order."""
    if not isinstance(values, (list, tuple)):
        return []
    given = {str(value).strip().lower() for value in values}
    return [step for step in SKIPPABLE if step in given]


@dataclass
class FirstRunConfig:
    """The optional first-run steps the owner skipped."""

    skipped: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.skipped = clean_skipped(self.skipped)
