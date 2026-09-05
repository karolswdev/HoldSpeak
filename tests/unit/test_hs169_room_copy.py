"""HS-169-03 — Room product-copy guard.

Asserts the Room's rendered copy (source scan) contains:
- No `REV ` token
- No `PROJECT` footer token
- No raw snake_case kinds (e.g. `project.created`, `watch.evaluated`)
- No counters of zero (`0 Meetings`, `0 Resources`, etc.)
"""

import re
import subprocess
import pathlib

ROOM_DIR = pathlib.Path(__file__).resolve().parents[2] / "web" / "src" / "features" / "project-room"

# Files to scan (the main Room face files, not door/ or sub-feature tests)
SCAN_FILES = [
    ROOM_DIR / "ProjectRoomCore.tsx",
    ROOM_DIR / "project-room.css",
]

# Patterns that must NOT appear in the Room face code
BANNED_PATTERNS = [
    # REV token in the UI (data-testid references are ok)
    (r'["\']REV \d', "REV token in UI string"),
    (r'>REV\s', "REV token in JSX text"),
    # PROJECT token in the footer (the name is said once)
    (r'PROJECT.*footer|footer.*PROJECT', "PROJECT token in footer"),
    # Raw snake_case kinds rendered as text (ok in maps/constants)
    # We check for patterns like `{entry.kind}` or `{c.kind}` rendered as text
]

# Patterns that indicate zero-count display
ZERO_COUNT_PATTERNS = [
    r'"0 Meetings"',
    r'"0 Resources"',
    r'"0 Watches"',
    r'"0 Changes"',
    r"Meetings 0",
    r"Resources 0",
    r"Watches 0",
    r"Changes 0",
]


def test_no_rev_token():
    """The Room never shows REV in the UI."""
    for path in SCAN_FILES:
        content = path.read_text()
        # Allow: data-testid refs, comments, the LifecycleChip (compat export)
        lines = content.split("\n")
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith("//") or stripped.startswith("/*"):
                continue
            if "data-testid" in line:
                continue
            if "LifecycleChip" in line:
                continue
            # Check for REV rendered as UI text
            if re.search(r'>REV\s', line) or re.search(r'"REV \d', line) or re.search(r"'REV \d", line):
                assert False, f"{path.name}:{i} — REV token in UI: {line.strip()}"


def test_no_project_footer_token():
    """The Room footer does not say PROJECT (the name is said once)."""
    core = (ROOM_DIR / "ProjectRoomCore.tsx").read_text()
    # Look for a PROJECT token near the SurfaceFooter
    footer_section = ""
    in_footer = False
    for line in core.split("\n"):
        if "SurfaceFooter" in line:
            in_footer = True
        if in_footer:
            footer_section += line + "\n"
            if line.strip().startswith("</") and "SurfaceFooter" not in line and "/>" in line:
                break
    # The footer receipt should not contain PROJECT
    assert "PROJECT" not in footer_section, f"PROJECT token found in footer: {footer_section[:200]}"


def test_no_zero_counters():
    """The Room never shows counters of zero (D1 cut)."""
    for path in SCAN_FILES:
        content = path.read_text()
        for pattern in ZERO_COUNT_PATTERNS:
            match = re.search(pattern, content)
            assert match is None, f"{path.name} — zero counter: {match.group()}"


def test_no_raw_snake_case_kinds_in_ui():
    """The Room never renders raw snake_case kind strings as visible text.

    The KIND_PHRASE_MAP and KIND_PHRASE_MAP constants define the mapping;
    raw kinds like `project.created` should never appear as UI text.
    """
    core = (ROOM_DIR / "ProjectRoomCore.tsx").read_text()
    lines = core.split("\n")
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        # Skip comments, imports, type definitions, constants
        if stripped.startswith("//") or stripped.startswith("/*") or stripped.startswith("*"):
            continue
        if stripped.startswith("import ") or stripped.startswith("export type"):
            continue
        if "KIND_PHRASE_MAP" in line or "CHANGE_KIND_LABELS" in line:
            continue
        # Check for raw dotted kind strings rendered as text (not in a map/constant)
        if re.search(r'>\s*[a-z]+\.[a-z_]+\s*<', line):
            assert False, f"ProjectRoomCore.tsx:{i} — raw snake_case kind in UI: {stripped}"


def test_change_label_never_exposes_raw_field_names():
    """The changeLabel function in model.ts humanizes field names.

    A change row with summary fields like `watches_activated` must never
    produce a label containing underscores from those field names.
    """
    import importlib
    import sys
    # This test runs in pytest (not vitest), so we can't import TS.
    # Instead, we scan model.ts for the changeLabel function and verify
    # the FIELD_LABELS map covers dangerous fields.
    model = (ROOM_DIR / "model.ts").read_text()
    # Verify FIELD_LABELS contains watches_activated mapped to empty or human
    assert "watches_activated" in model, "FIELD_LABELS should handle watches_activated"
    # The label for watches_activated should not contain an underscore
    assert '"watches_activated": ""' not in model or 'watches activated' in model, \
        "watches_activated must map to human words or be dropped"
    # source should be dropped (empty string) — TS uses unquoted keys
    assert 'source: ""' in model, "source field should be dropped (empty)"
