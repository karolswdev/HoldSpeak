"""Decks — named config permutations, good and deliberately bad.

A deck is a **sparse** config overlay under ``uat/decks/<name>.yaml``: the
conductor writes it as the run HOME's ``config.json`` and the product's own
``Config.load`` merges any missing field over its defaults. Decks state only
their delta — the product's defaults stay the single source of truth.

Decks are validated by round-tripping through ``Config.load`` in
``tests/uat/test_decks.py`` (a test may import ``holdspeak``; the conductor
never does) so a bad deck can't rot silently.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml


def decks_dir() -> Path:
    override = os.environ.get("UAT_DECKS_DIR")
    if override:
        return Path(override)
    return Path(__file__).resolve().parents[3] / "uat" / "decks"


class DeckError(ValueError):
    pass


class DeckRegistry:
    """Loads and resolves decks by name."""

    def __init__(self, directory: Path | None = None):
        self.directory = Path(directory) if directory else decks_dir()

    def _path(self, name: str) -> Path:
        return self.directory / f"{name}.yaml"

    def names(self) -> list[str]:
        if not self.directory.exists():
            return []
        return sorted(p.stem for p in self.directory.glob("*.yaml"))

    def load(self, name: str) -> dict[str, Any]:
        """The raw sparse overlay a deck names (its ``config`` block)."""
        path = self._path(name)
        if not path.exists():
            raise DeckError(f"unknown deck: {name!r} (looked in {self.directory})")
        try:
            doc = yaml.safe_load(path.read_text()) or {}
        except yaml.YAMLError as exc:
            raise DeckError(f"deck {name!r} is not valid YAML: {exc}") from exc
        if not isinstance(doc, dict):
            raise DeckError(f"deck {name!r} must be a mapping, got {type(doc).__name__}")
        overlay = doc.get("config", doc)
        if not isinstance(overlay, dict):
            raise DeckError(f"deck {name!r}: 'config' must be a mapping")
        return overlay

    def describe(self, name: str) -> dict[str, Any]:
        path = self._path(name)
        doc = yaml.safe_load(path.read_text()) or {} if path.exists() else {}
        return {
            "name": name,
            "title": doc.get("title", name),
            "description": doc.get("description", ""),
            "requires": doc.get("requires", []),
            "config": doc.get("config", {} if "config" in doc else doc),
        }

    def all(self) -> list[dict[str, Any]]:
        return [self.describe(n) for n in self.names()]
