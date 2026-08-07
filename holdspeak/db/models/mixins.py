"""Shared model mixins for the HoldSpeak persistence layer."""
from __future__ import annotations

import dataclasses


class Serializable:
    """Mixin that derives ``to_dict()`` from ``dataclasses.fields()``.

    Models with custom serialization (key renames, JSON parsing, computed
    properties) override ``to_dict()`` on the concrete class; the mixin
    provides the default for simple field-copy models.
    """

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)
