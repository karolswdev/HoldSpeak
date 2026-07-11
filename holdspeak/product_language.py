"""Canonical HoldSpeak product language with strict compatibility adapters.

``docs/product-language.json`` is the source of truth.  Wire and persistence
names deliberately remain stable; callers resolve those aliases to product
terms before presenting them to a person.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import json
from pathlib import Path
from typing import Any, Mapping


class ProductLanguageError(ValueError):
    """Raised when a product-language value is unknown or the registry drifts."""


class DestinationClass(str, Enum):
    THIS_DEVICE = "this_device"
    PAIRED_DEVICE = "paired_device"
    PRIVATE_ENDPOINT = "private_endpoint"
    EXTERNAL_SERVICE = "external_service"


class DecisionKind(str, Enum):
    REVIEW = "review"
    APPROVAL = "approval"
    GRANT = "grant"


class ControlMode(str, Enum):
    SAFE = "safe"
    NEUTRAL = "neutral"
    YOLO = "yolo"


@dataclass(frozen=True)
class ProductTerm:
    id: str
    singular: str
    plural: str
    category: str
    meaning: str


@dataclass(frozen=True)
class ProductLanguageRegistry:
    version: int
    terms: Mapping[str, ProductTerm]
    legacy_aliases: Mapping[str, str]
    lifecycle_axes: Mapping[str, tuple[str, ...]]
    destination_classes: tuple[DestinationClass, ...]
    decision_kinds: tuple[DecisionKind, ...]
    control_modes: tuple[ControlMode, ...]
    meeting_projections: tuple[str, ...]

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "ProductLanguageRegistry":
        try:
            version = int(raw["registry_version"])
            terms = {
                term_id: ProductTerm(id=term_id, **definition)
                for term_id, definition in raw["terms"].items()
            }
            aliases = dict(raw["legacy_aliases"])
            lifecycle_axes = {
                axis: tuple(values) for axis, values in raw["lifecycle_axes"].items()
            }
            destinations = tuple(
                DestinationClass(value) for value in raw["destination_classes"]
            )
            decisions = tuple(DecisionKind(value) for value in raw["decision_kinds"])
            modes = tuple(ControlMode(value) for value in raw["control_modes"])
            projections = tuple(str(value) for value in raw["meeting_projections"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ProductLanguageError(
                f"invalid product-language registry: {exc}"
            ) from exc

        if version != 1:
            raise ProductLanguageError(
                f"unsupported product-language registry version: {version}"
            )
        dangling = {
            alias: target for alias, target in aliases.items() if target not in terms
        }
        if dangling:
            raise ProductLanguageError(f"aliases target unknown terms: {dangling}")
        if len(set(aliases).intersection(terms)) > 0:
            raise ProductLanguageError("a legacy alias cannot shadow a canonical term")
        return cls(
            version=version,
            terms=terms,
            legacy_aliases=aliases,
            lifecycle_axes=lifecycle_axes,
            destination_classes=destinations,
            decision_kinds=decisions,
            control_modes=modes,
            meeting_projections=projections,
        )

    def canonical_term_id(self, value: str) -> str:
        normalized = str(value).strip().lower().replace("-", "_").replace(" ", "_")
        if normalized in self.terms:
            return normalized
        if normalized in self.legacy_aliases:
            return self.legacy_aliases[normalized]
        raise ProductLanguageError(f"unknown product-language term: {value!r}")

    def term(self, value: str) -> ProductTerm:
        return self.terms[self.canonical_term_id(value)]

    def label(self, value: str, *, plural: bool = False) -> str:
        term = self.term(value)
        return term.plural if plural else term.singular

    def lifecycle_value(self, axis: str, value: str) -> str:
        try:
            values = self.lifecycle_axes[axis]
        except KeyError as exc:
            raise ProductLanguageError(f"unknown lifecycle axis: {axis!r}") from exc
        if value not in values:
            raise ProductLanguageError(f"unknown {axis} lifecycle value: {value!r}")
        return value


def _registry_path() -> Path:
    source_tree = Path(__file__).resolve().parents[1] / "docs" / "product-language.json"
    if source_tree.exists():
        return source_tree
    packaged = Path(__file__).resolve().parent / "data" / "product-language.json"
    if packaged.exists():
        return packaged
    raise ProductLanguageError("docs/product-language.json is not available")


def load_product_language(path: Path | None = None) -> ProductLanguageRegistry:
    registry_path = path or _registry_path()
    try:
        raw = json.loads(registry_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ProductLanguageError(
            f"cannot read product-language registry: {exc}"
        ) from exc
    if not isinstance(raw, dict):
        raise ProductLanguageError("product-language registry must be a JSON object")
    return ProductLanguageRegistry.from_dict(raw)


PRODUCT_LANGUAGE = load_product_language()


def product_label(value: str, *, plural: bool = False) -> str:
    """Return a canonical UI label for a canonical id or legacy wire alias."""

    return PRODUCT_LANGUAGE.label(value, plural=plural)
