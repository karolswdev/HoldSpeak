"""UX canon guard: the rules that are defects stay at zero.

The in-process scanner (scripts/ux_canon_scan.py) reads the live web/src tree.
A raw ``<button>`` (A1), a drawn counter (A8), a missing egress mark (A9), an
accent rail (DS6), a bare input with no microphone (mic) and A4 are each a
defect the owner sees, so each must be zero. The other rules (prose, raw ids,
emoji, B, C) are findings for the face lanes, not a gate.

The ceiling ratchet that needed a re-record on every face change is parked
(tests/_parked/fences/test_ux_canon_ratchet.py, 2026-11-09).
"""
from __future__ import annotations

import importlib.util
from functools import lru_cache
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts" / "ux_canon_scan.py"

ZERO_RULES = ("A1", "A4", "A8", "A9", "DS6", "mic")


def _load_scanner():
    """Import the scanner module from its script path."""
    spec = importlib.util.spec_from_file_location("ux_canon_scan", SCRIPT_PATH)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@lru_cache(maxsize=1)
def _get_scan() -> dict:
    return _load_scanner().scan(REPO_ROOT)


@pytest.mark.parametrize("rule", ZERO_RULES)
def test_a_defect_rule_stays_at_zero(rule):
    result = _get_scan()
    faces = sorted(face for face, counts in result["face_rule_counts"].items() if counts.get(rule))
    assert result["totals"]["per_rule"].get(rule, 0) == 0, (
        f"{rule} hits on these faces: {faces}. "
        "A1: use the library Button. A8: omit a zero counter at the source. "
        "A9: name the destination where egress happens. DS6: no left accent rail."
    )


def test_ds6_exempts_only_the_workbench_ink_divider():
    """PHILO-13-11: the 1px ink divider is a separator, not an accent rail.
    Only that exact token is exempt; any other border-left stays flagged."""
    import importlib.util, pathlib
    spec = importlib.util.spec_from_file_location(
        "ux_canon_scan", pathlib.Path(__file__).resolve().parents[2] / "scripts" / "ux_canon_scan.py")
    scan = importlib.util.module_from_spec(spec); spec.loader.exec_module(scan)
    def ds6(css):
        return [v for v in scan.scan_file("x.css", css, css.splitlines()) if v.rule == "DS6"]
    assert ds6(".a { border-left: 1px solid var(--wb-ink); }") == []
    assert ds6(".a { border-left: 3px solid var(--accent); }")
    assert ds6(".a { border-left: 2px solid var(--wb-ink); }")
    assert ds6(".a { border-left: 1px solid var(--wb-blue); }")
    assert ds6(".a { border-left: 1px solid #6688bb; }")


@pytest.mark.parametrize(("filename", "source", "rule"), [
    ("Button.tsx", "export const Button = () => <button>Save</button>;", "A1"),
    ("WorkbenchSelect.tsx", "export const Select = () => <select />;", "B"),
])
def test_picker_library_implementation_paths_are_exact(filename, source, rule):
    """Native library elements are valid only at their implementation path."""
    scanner = _load_scanner()

    def hits(path):
        return [v for v in scanner.scan_file(path, source, source.splitlines()) if v.rule == rule]

    assert hits(f"components/signal/{filename}") == []
    for path in (
        f"desk/components/{filename}",
        f"features/picker/{filename}",
        f"components/signal/Fake{filename}",
        f"components/signal/{filename}.copy.tsx",
    ):
        assert hits(path), f"face or lookalike path escaped {rule}: {path}"
