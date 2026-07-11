"""HS-92-01 — one strict product language across the hub and both clients."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from holdspeak.product_language import (
    ControlMode,
    DecisionKind,
    DestinationClass,
    ProductLanguageError,
    ProductLanguageRegistry,
    load_product_language,
    product_label,
)


REPO = Path(__file__).resolve().parents[2]
REGISTRY_PATH = REPO / "docs" / "product-language.json"


def test_registry_is_versioned_complete_and_strict() -> None:
    registry = load_product_language(REGISTRY_PATH)

    assert registry.version == 1
    assert registry.label("recipe") == "Persona"
    assert registry.label("agent", plural=True) == "Personas"
    assert registry.label("directory") == "Zone"
    assert registry.label("kb") == "Knowledge"
    assert registry.label("chain") == "Sequence"
    assert registry.label("profile") == "Runs on"
    assert registry.label("connector") == "Integration"
    assert registry.destination_classes == tuple(DestinationClass)
    assert registry.decision_kinds == tuple(DecisionKind)
    assert registry.control_modes == tuple(ControlMode)
    assert registry.meeting_projections == (
        "summary",
        "action_items",
        "transcript",
        "topics",
    )
    with pytest.raises(ProductLanguageError, match="unknown product-language term"):
        registry.label("generic_thing")
    with pytest.raises(ProductLanguageError, match="unknown sync lifecycle value"):
        registry.lifecycle_value("sync", "pending")


def test_module_accessor_uses_the_same_registry() -> None:
    assert product_label("persona") == "Persona"
    assert product_label("recipe") == "Persona"
    assert product_label("coder", plural=True) == "Coder sessions"


def test_registry_rejects_alias_drift_and_unknown_canonical_values() -> None:
    raw = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    raw["legacy_aliases"]["old_thing"] = "not_a_term"
    with pytest.raises(ProductLanguageError, match="aliases target unknown terms"):
        ProductLanguageRegistry.from_dict(raw)

    raw = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    raw["destination_classes"].append("somewhere")
    with pytest.raises(ProductLanguageError, match="invalid product-language registry"):
        ProductLanguageRegistry.from_dict(raw)


def test_compatibility_exceptions_are_explicit_and_bounded() -> None:
    raw = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    exceptions = raw["compatibility_exceptions"]
    assert exceptions
    for exception in exceptions:
        assert exception["path"].startswith(("holdspeak/", "web/", "apple/"))
        assert exception["terms"]
        assert len(exception["reason"].strip()) >= 24


_EXACT_UNQUALIFIED = re.compile(
    r"^(?:profiles?|agents?|actions?|contexts?|targets?|pending|local)$",
    re.IGNORECASE,
)
_TS_VISIBLE = re.compile(
    r'(?:title|label|placeholder|aria-label|eyebrow)\s*=\s*["\']([^"\']+)["\']'
    r"|>\s*([^<{][^<{]*?)\s*<"
)
_SWIFT_VISIBLE = re.compile(r'(?:Text|Label|TextField|\.alert)\(\s*"([^"]+)"')


def test_primary_ui_has_no_new_unqualified_ambiguous_terms() -> None:
    """Guard visible literals, not compatibility identifiers or historical comments."""

    offenders: list[str] = []
    web_roots = [REPO / "web" / "src" / "desk", REPO / "web" / "src" / "pages"]
    swift_root = REPO / "apple" / "App" / "MeetingCapture"

    for root in web_roots:
        for path in sorted(root.rglob("*.tsx")):
            for line_no, line in enumerate(
                path.read_text(encoding="utf-8").splitlines(), 1
            ):
                for match in _TS_VISIBLE.finditer(line):
                    value = next((part for part in match.groups() if part), "").strip()
                    if _EXACT_UNQUALIFIED.fullmatch(value):
                        offenders.append(f"{path.relative_to(REPO)}:{line_no}: {value}")

    for path in sorted(swift_root.rglob("*.swift")):
        for line_no, line in enumerate(
            path.read_text(encoding="utf-8").splitlines(), 1
        ):
            for value in _SWIFT_VISIBLE.findall(line):
                if _EXACT_UNQUALIFIED.fullmatch(value.strip()):
                    offenders.append(
                        f"{path.relative_to(REPO)}:{line_no}: {value.strip()}"
                    )

    assert not offenders, (
        "Unqualified ambiguous product terms reached primary UI copy. Use the "
        "registry term or a qualified phrase:\n  " + "\n  ".join(offenders)
    )
