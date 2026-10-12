"""HS-157-01 -- Qualified-ref grammar, aliases, round-trip, and fence.

Tests the central ``holdspeak.refs`` module that implements REF-001..004
from SRS_DOMAIN_DRIVER SS4.2.

Fence test (test_fence_no_feature_local_splitting)
--------------------------------------------------
Scans a NAMED LIST of Project Rooms modules for feature-local ref
splitting (``split(":")`` or ``startswith("<type>:")`` patterns) outside
the central module. The list starts with only ``holdspeak/refs.py``
(the module under test) and grows as P1+ adds files to the Project
Rooms feature.

**How a new module joins the list:** add its path (relative to the repo
root, e.g. ``holdspeak/services/project_steward_service.py``) to the
``PROJECT_ROOMS_MODULES`` list below. The fence then protects it from
feature-local ref operations. Legacy call sites (thread_service,
people_service, etc.) are NOT in the list and never fire the fence.
"""

from __future__ import annotations

import ast
import os
import re
from pathlib import Path

import pytest

from holdspeak.refs import (
    CITIZEN_TYPES,
    MalformedRefError,
    QualifiedRef,
    RefError,
    UnregisteredTypeError,
    _ALIASES,
    format,
    parse,
    resolve_alias,
)


# =====================================================================
# Grammar: every registered type parses correctly
# =====================================================================


@pytest.mark.parametrize("citizen_type", sorted(CITIZEN_TYPES))
def test_parse_registered_type(citizen_type: str) -> None:
    ref_str = f"{citizen_type}:some-opaque-id"
    ref = parse(ref_str)
    assert ref.type == citizen_type
    assert ref.id == "some-opaque-id"
    assert ref.is_registered is True


@pytest.mark.parametrize("citizen_type", sorted(CITIZEN_TYPES))
def test_str_roundtrip(citizen_type: str) -> None:
    """str(parse(s)) == s for every registered type."""
    ref_str = f"{citizen_type}:abc-123"
    assert str(parse(ref_str)) == ref_str


def test_parse_preserves_compound_id() -> None:
    """IDs may contain colons (e.g. meeting:abc:intel)."""
    ref = parse("meeting:abc:intel:extra")
    assert ref.type == "meeting"
    assert ref.id == "abc:intel:extra"


# =====================================================================
# Aliases (REF-003): both forms parse to the same canonical ref
# =====================================================================


def test_person_alias_resolves_to_people() -> None:
    canon = parse("people:rel-42")
    alias = parse("person:rel-42")
    assert canon == alias
    assert canon.type == "people"
    assert alias.type == "people"
    assert canon.is_registered is True


def test_door_alias_resolves_to_action_item() -> None:
    canon = parse("action_item:card-7")
    alias = parse("door:card-7")
    assert canon == alias
    assert canon.type == "action_item"
    assert alias.type == "action_item"
    assert canon.is_registered is True


def test_resolve_alias_identity() -> None:
    """Non-aliased types pass through unchanged."""
    assert resolve_alias("meeting") == "meeting"
    assert resolve_alias("unknown") == "unknown"


def test_resolve_alias_known() -> None:
    assert resolve_alias("person") == "people"
    assert resolve_alias("door") == "action_item"


# =====================================================================
# Round-trip: parse -> format -> parse for every registered type
# =====================================================================


@pytest.mark.parametrize("citizen_type", sorted(CITIZEN_TYPES))
def test_round_trip_parse_format_parse(citizen_type: str) -> None:
    """REF-002: round-trip without loss."""
    original_id = "opaque-123-test"
    ref1 = parse(f"{citizen_type}:{original_id}")
    formatted = format(ref1.type, ref1.id)
    ref2 = parse(formatted)
    assert ref1 == ref2
    assert formatted == f"{citizen_type}:{original_id}"


@pytest.mark.parametrize("alias,canonical", sorted(_ALIASES.items()))
def test_round_trip_through_alias(alias: str, canonical: str) -> None:
    """Parsing an alias and re-formatting yields the canonical form."""
    ref = parse(f"{alias}:id-99")
    formatted = format(ref.type, ref.id)
    assert formatted == f"{canonical}:id-99"
    ref2 = parse(formatted)
    assert ref2 == ref


# =====================================================================
# Unknown types: inspectable but refused (REF-004)
# =====================================================================


def test_unknown_type_parses_but_not_registered() -> None:
    ref = parse("gadget:xyz")
    assert ref.type == "gadget"
    assert ref.id == "xyz"
    assert ref.is_registered is False


def test_unknown_type_inspectable() -> None:
    """The unknown ref is a real object -- type, id, str all work."""
    ref = parse("unicorn:rainbow-42")
    assert ref.type == "unicorn"
    assert ref.id == "rainbow-42"
    assert str(ref) == "unicorn:rainbow-42"


def test_format_refuses_unknown_type() -> None:
    with pytest.raises(UnregisteredTypeError, match="not a registered"):
        format("gadget", "xyz")


def test_format_refuses_alias_type() -> None:
    """Aliases are not canonical names; format() rejects them."""
    with pytest.raises(UnregisteredTypeError, match="alias"):
        format("person", "rel-42")
    with pytest.raises(UnregisteredTypeError, match="alias"):
        format("door", "card-7")


# =====================================================================
# Malformed refs
# =====================================================================


def test_parse_empty_string() -> None:
    with pytest.raises(MalformedRefError):
        parse("")


def test_parse_none() -> None:
    with pytest.raises(MalformedRefError):
        parse(None)  # type: ignore[arg-type]


def test_parse_no_colon() -> None:
    with pytest.raises(MalformedRefError):
        parse("justaplainstring")


def test_parse_leading_colon() -> None:
    with pytest.raises(MalformedRefError):
        parse(":notype")


def test_parse_trailing_colon() -> None:
    """A trailing colon means the id part is empty -- still a regex match
    failure because the id group requires .+ (one or more chars)."""
    with pytest.raises(MalformedRefError):
        parse("meeting:")


def test_format_empty_id() -> None:
    with pytest.raises(MalformedRefError):
        format("meeting", "")


def test_error_hierarchy() -> None:
    """Both error classes inherit from RefError and ValueError."""
    assert issubclass(MalformedRefError, RefError)
    assert issubclass(UnregisteredTypeError, RefError)
    assert issubclass(RefError, ValueError)


# =====================================================================
# Registry completeness
# =====================================================================


def test_registry_contains_all_srs_citizens() -> None:
    """Verify every SRS SS3.2 citizen has a canonical type registered."""
    # Canonical mapping from SRS citizen names to ref types.
    srs_citizens = {
        "Meeting": "meeting",
        "Decision": "decision",
        "Door/follow-through": "action_item",
        "Person/participant": "people",
        "Thread": "thread",
        "Note": "note",
        "Artifact": "artifact",
        "Workbench": "workbench",
        "Agent/Recipe": "agent",
        "Repo/delivery system": "repo",
        "Watch": "watch",
        "Kernel/Desk object": "kernel",
        "Project": "project",  # HS-158-02: aggregate itself (SRS SS3.1)
    }
    for citizen_name, ref_type in srs_citizens.items():
        assert ref_type in CITIZEN_TYPES, (
            f"SRS SS3.2 citizen {citizen_name!r} has no registered type "
            f"{ref_type!r} in CITIZEN_TYPES"
        )


def test_aliases_resolve_to_registered_types() -> None:
    for alias, canonical in _ALIASES.items():
        assert canonical in CITIZEN_TYPES, (
            f"Alias {alias!r} -> {canonical!r} but {canonical!r} "
            f"is not in CITIZEN_TYPES"
        )
        assert alias not in CITIZEN_TYPES, (
            f"Alias {alias!r} should not also be a canonical type"
        )


# =====================================================================
# Fence: no feature-local ref splitting in Project Rooms modules
# =====================================================================

# Modules that are part of the Project Rooms feature. The fence scans
# only these; legacy modules (thread_service, people_service, etc.)
# are intentionally excluded so the fence doesn't light up on code
# that predates the central module.
#
# HOW A NEW MODULE JOINS THIS LIST: when you add a new Python file
# to the Project Rooms feature (e.g. holdspeak/services/project_steward_service.py),
# add its repo-relative path here. The fence then prevents feature-local
# ref operations in that file.
PROJECT_ROOMS_MODULES: list[str] = [
    "holdspeak/refs.py",
    "holdspeak/project_contracts.py",  # HS-157-05: counsel N-1
]

# The central module itself is ALLOWED to use these patterns.
_FENCE_EXEMPT = {"holdspeak/refs.py"}

# Known ref type prefixes (canonical + aliases) to detect feature-local
# string operations like startswith("meeting:"), split(":"), etc.
_ALL_TYPE_NAMES = sorted(CITIZEN_TYPES | frozenset(_ALIASES.keys()))

# Regex patterns that indicate feature-local ref splitting.
# These catch: .startswith("meeting:"), .split(":"), .removeprefix("people:"),
# f"meeting:{...}", "meeting:" + ..., etc.
_SPLIT_PATTERNS: list[re.Pattern[str]] = [
    # .startswith("<type>:")  or  .startsWith("<type>:")
    re.compile(
        r'\.\s*(?:startswith|startsWith|removeprefix)\s*\(\s*["\']('
        + "|".join(re.escape(t) for t in _ALL_TYPE_NAMES)
        + r'):'
    ),
    # .split(":") on a ref-shaped variable
    # This is intentionally broad -- if a Project Rooms module needs to
    # split on colons, it should use parse() instead.
    re.compile(r'\.split\s*\(\s*["\']:["\']'),
    # f-string emission: f"meeting:{..." or f"people:{..."
    re.compile(
        r'f["\']('
        + "|".join(re.escape(t) for t in _ALL_TYPE_NAMES)
        + r'):\{'
    ),
]


def test_fence_no_feature_local_splitting() -> None:
    """REF-001: newly touched Project Rooms code must use holdspeak.refs.

    This test scans every module in PROJECT_ROOMS_MODULES (except the
    central module itself) for feature-local ref operations. If a new
    Project Rooms module needs to parse or format refs, it must import
    from holdspeak.refs.

    Legacy modules are NOT in the list and never fire this fence.
    """
    repo_root = Path(__file__).resolve().parents[2]
    violations: list[str] = []

    for module_path in PROJECT_ROOMS_MODULES:
        if module_path in _FENCE_EXEMPT:
            continue
        full_path = repo_root / module_path
        if not full_path.exists():
            # Module not yet created -- skip silently.
            continue
        source = full_path.read_text(encoding="utf-8")
        for lineno, line in enumerate(source.splitlines(), start=1):
            # Skip comments and docstrings (rough heuristic: lines
            # starting with # after stripping).
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            for pattern in _SPLIT_PATTERNS:
                if pattern.search(line):
                    violations.append(f"{module_path}:{lineno}: {stripped}")

    assert not violations, (
        "Feature-local ref splitting found in Project Rooms modules. "
        "Use holdspeak.refs.parse() / format() instead:\n"
        + "\n".join(f"  {v}" for v in violations)
    )


def test_fence_central_module_is_exempt() -> None:
    """The central module itself is allowed to use ref patterns."""
    assert "holdspeak/refs.py" in _FENCE_EXEMPT
    assert "holdspeak/refs.py" in PROJECT_ROOMS_MODULES
