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
class ProductLanguageException:
    id: str
    registry_version: int
    kind: str
    path: str
    terms: tuple[str, ...]
    reason: str


@dataclass(frozen=True)
class ProductCopyPattern:
    id: str
    pattern: str
    reason: str


@dataclass(frozen=True)
class ProductCopyContract:
    version: int
    classifications: tuple[str, ...]
    generic_consequential_verbs: tuple[str, ...]
    prohibited_operational_patterns: tuple[ProductCopyPattern, ...]
    failure_requirements: tuple[str, ...]
    primary_surfaces: Mapping[str, tuple[str, ...]]
    exceptions: tuple[Mapping[str, Any], ...]


@dataclass(frozen=True)
class ProductLanguageRegistry:
    version: int
    terms: Mapping[str, ProductTerm]
    legacy_aliases: Mapping[str, str]
    lifecycle_axes: Mapping[str, tuple[str, ...]]
    destination_classes: tuple[DestinationClass, ...]
    decision_kinds: tuple[DecisionKind, ...]
    control_modes: tuple[ControlMode, ...]
    control_mode_labels: Mapping[ControlMode, str]
    control_mode_descriptions: Mapping[ControlMode, str]
    destination_class_labels: Mapping[DestinationClass, str]
    lifecycle_labels: Mapping[str, Mapping[str, str]]
    meeting_projections: tuple[str, ...]
    guarded_terms: tuple[str, ...]
    copy_contract: ProductCopyContract
    compatibility_exceptions: tuple[ProductLanguageException, ...]

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
            mode_labels = {
                ControlMode(key): str(value)
                for key, value in raw["control_mode_labels"].items()
            }
            mode_descriptions = {
                ControlMode(key): str(value)
                for key, value in raw["control_mode_descriptions"].items()
            }
            destination_labels = {
                DestinationClass(key): str(value)
                for key, value in raw["destination_class_labels"].items()
            }
            lifecycle_labels = {
                str(axis): {str(key): str(value) for key, value in labels.items()}
                for axis, labels in raw["lifecycle_labels"].items()
            }
            projections = tuple(str(value) for value in raw["meeting_projections"])
            guarded_terms = tuple(str(value) for value in raw["guarded_terms"])
            copy_raw = raw["copy_contract"]
            copy_contract = ProductCopyContract(
                version=int(copy_raw["version"]),
                classifications=tuple(str(value) for value in copy_raw["classifications"]),
                generic_consequential_verbs=tuple(
                    str(value) for value in copy_raw["generic_consequential_verbs"]
                ),
                prohibited_operational_patterns=tuple(
                    ProductCopyPattern(
                        id=str(item["id"]),
                        pattern=str(item["pattern"]),
                        reason=str(item["reason"]),
                    )
                    for item in copy_raw["prohibited_operational_patterns"]
                ),
                failure_requirements=tuple(
                    str(value) for value in copy_raw["failure_requirements"]
                ),
                primary_surfaces={
                    str(client): tuple(str(path) for path in paths)
                    for client, paths in copy_raw["primary_surfaces"].items()
                },
                exceptions=tuple(dict(item) for item in copy_raw["exceptions"]),
            )
            compatibility_exceptions = tuple(
                ProductLanguageException(
                    id=str(item["id"]),
                    registry_version=int(item["registry_version"]),
                    kind=str(item["kind"]),
                    path=str(item["path"]),
                    terms=tuple(str(term) for term in item["terms"]),
                    reason=str(item["reason"]),
                )
                for item in raw["compatibility_exceptions"]
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ProductLanguageError(
                f"invalid product-language registry: {exc}"
            ) from exc

        if version != 2:
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
        if set(mode_labels) != set(modes) or set(mode_descriptions) != set(modes):
            raise ProductLanguageError("control-mode labels must cover every wire value")
        if set(destination_labels) != set(destinations):
            raise ProductLanguageError("destination labels must cover every class")
        if set(lifecycle_labels) != set(lifecycle_axes) or any(
            set(lifecycle_labels[axis]) != set(values)
            for axis, values in lifecycle_axes.items()
        ):
            raise ProductLanguageError("lifecycle labels must cover every axis value")
        if copy_contract.version != 1:
            raise ProductLanguageError(
                f"unsupported product-copy contract version: {copy_contract.version}"
            )
        exception_ids = [item.id for item in compatibility_exceptions]
        if len(exception_ids) != len(set(exception_ids)) or any(
            item.registry_version != version for item in compatibility_exceptions
        ):
            raise ProductLanguageError(
                "compatibility exceptions must have unique ids for this registry version"
            )
        return cls(
            version=version,
            terms=terms,
            legacy_aliases=aliases,
            lifecycle_axes=lifecycle_axes,
            destination_classes=destinations,
            decision_kinds=decisions,
            control_modes=modes,
            control_mode_labels=mode_labels,
            control_mode_descriptions=mode_descriptions,
            destination_class_labels=destination_labels,
            lifecycle_labels=lifecycle_labels,
            meeting_projections=projections,
            guarded_terms=guarded_terms,
            copy_contract=copy_contract,
            compatibility_exceptions=compatibility_exceptions,
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

    def lifecycle_label(self, axis: str, value: str) -> str:
        canonical = self.lifecycle_value(axis, value)
        return self.lifecycle_labels[axis][canonical]

    def control_mode(self, value: str | ControlMode) -> ControlMode:
        normalized = str(value.value if isinstance(value, ControlMode) else value).strip()
        lowered = normalized.lower()
        aliases = {label.lower(): mode for mode, label in self.control_mode_labels.items()}
        try:
            return ControlMode(lowered)
        except ValueError:
            if lowered in aliases:
                return aliases[lowered]
        raise ProductLanguageError(f"unknown control mode: {value!r}")

    def control_mode_label(self, value: str | ControlMode) -> str:
        return self.control_mode_labels[self.control_mode(value)]

    def control_mode_description(self, value: str | ControlMode) -> str:
        return self.control_mode_descriptions[self.control_mode(value)]

    def destination_label(self, value: str | DestinationClass) -> str:
        try:
            destination = (
                value if isinstance(value, DestinationClass) else DestinationClass(value)
            )
        except ValueError as exc:
            raise ProductLanguageError(f"unknown destination class: {value!r}") from exc
        return self.destination_class_labels[destination]


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


def control_mode_label(value: str | ControlMode) -> str:
    """Render a product label while preserving the versioned wire value."""

    return PRODUCT_LANGUAGE.control_mode_label(value)


def control_mode_wire(value: str | ControlMode) -> str:
    """Adapt Secure/Normal labels or legacy wire values to the stable wire."""

    return PRODUCT_LANGUAGE.control_mode(value).value


def destination_class_label(value: str | DestinationClass) -> str:
    return PRODUCT_LANGUAGE.destination_label(value)


def lifecycle_label(axis: str, value: str) -> str:
    return PRODUCT_LANGUAGE.lifecycle_label(axis, value)
