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
    control_mode_label,
    control_mode_wire,
    destination_class_label,
    lifecycle_label,
    load_product_language,
    product_label,
)


REPO = Path(__file__).resolve().parents[2]
REGISTRY_PATH = REPO / "docs" / "product-language.json"


def test_module_accessor_uses_the_same_registry() -> None:
    assert product_label("persona") == "Mode"  # Betterment AG1
    assert product_label("recipe") == "Mode"  # Betterment AG1
    assert product_label("coder", plural=True) == "Agents"  # Betterment AG1
    assert control_mode_wire("Secure") == "safe"
    assert control_mode_wire("normal") == "neutral"
    assert control_mode_label("neutral") == "Normal"
    assert destination_class_label("this_device") == "This device"
    assert lifecycle_label("review", "unreviewed") == "Needs review"


def test_registry_rejects_alias_drift_and_unknown_canonical_values() -> None:
    raw = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    raw["legacy_aliases"]["old_thing"] = "not_a_term"
    with pytest.raises(ProductLanguageError, match="aliases target unknown terms"):
        ProductLanguageRegistry.from_dict(raw)

    raw = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    raw["destination_classes"].append("somewhere")
    with pytest.raises(ProductLanguageError, match="invalid product-language registry"):
        ProductLanguageRegistry.from_dict(raw)


# HS-100-10: "agent" became the registry's own product term (the
# Persona rename) and is no longer ambiguous.
_EXACT_UNQUALIFIED = re.compile(
    r"^(?:profiles?|actions?|contexts?|targets?|pending|local)$",
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
