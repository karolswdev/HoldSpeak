"""HS-63-05: the backend density guard — the twin of the frontend guard.

`web_runtime.py` was the proof that a carve regrows without a lock: Phase 52
sliced the dictation orchestration out of it at 2,341 lines, and by Phase 63
it had regrown to 2,635 (the wake word, devices, and routing glue all landed
there). This phase carved it to a 555-line boot/run/config core over eight
single-concern mixins in `holdspeak/runtime/`, and `meeting_session.py`
(1,674: models + recording + transcription + intel + persistence +
mutations) to a package with a 795-line lifecycle core over five modules.
This guard locks both shapes mechanically.

When this guard fires: **carve, don't bump.** A module over budget wants to
be split along the same seams — a new mixin in `holdspeak/runtime/` or
`holdspeak/meeting_session/`, composed by the core class. Raising a budget
is a deliberate, reviewed decision, not a reflex (see
docs/internal/ARCHITECTURE_BACKEND_RUNTIME.md).

Named watch item (deliberately NOT guarded here): `holdspeak/web/routes/
meetings.py` sits at ~1,5xx lines. It is a route module from the Phase-26
carve, a different shape with a different budget conversation; if it keeps
growing it earns its own phase, not a silent bump into this guard.
"""

from __future__ import annotations

from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_HS = _REPO / "holdspeak"

# The runtime core is boot/run/config only (shipped at 555).
_RUNTIME_CORE_BUDGET = 650
# The session core is lifecycle + assembly (shipped at 795).
_SESSION_CORE_BUDGET = 850
# Every concern module is single-purpose (largest shipped: meeting_glue 552).
_MODULE_BUDGET = 600


def _lines(path: Path) -> int:
    return len(path.read_text(encoding="utf-8").splitlines())


def test_web_runtime_core_stays_boot_only() -> None:
    n = _lines(_HS / "web_runtime.py")
    assert n <= _RUNTIME_CORE_BUDGET, (
        f"holdspeak/web_runtime.py is {n} lines (budget {_RUNTIME_CORE_BUDGET}). "
        "The core is boot/run/config only — new runtime behavior belongs in a "
        "mixin under holdspeak/runtime/, composed by WebRuntime. Carve, don't bump."
    )


def test_meeting_session_core_stays_lifecycle_only() -> None:
    n = _lines(_HS / "meeting_session" / "session.py")
    assert n <= _SESSION_CORE_BUDGET, (
        f"holdspeak/meeting_session/session.py is {n} lines (budget "
        f"{_SESSION_CORE_BUDGET}). The core is lifecycle + assembly — new "
        "session behavior belongs in a mixin module beside it. Carve, don't bump."
    )


def test_runtime_modules_stay_single_concern() -> None:
    offenders = []
    for path in sorted((_HS / "runtime").glob("*.py")):
        n = _lines(path)
        if n > _MODULE_BUDGET:
            offenders.append(f"{path.relative_to(_REPO)}: {n} lines")
    assert not offenders, (
        f"runtime modules over the {_MODULE_BUDGET}-line budget — carve a new "
        "mixin, don't grow one:\n  " + "\n  ".join(offenders)
    )


def test_meeting_session_modules_stay_single_concern() -> None:
    offenders = []
    for path in sorted((_HS / "meeting_session").glob("*.py")):
        if path.name == "session.py":  # the core has its own budget above
            continue
        n = _lines(path)
        if n > _MODULE_BUDGET:
            offenders.append(f"{path.relative_to(_REPO)}: {n} lines")
    assert not offenders, (
        f"meeting_session modules over the {_MODULE_BUDGET}-line budget — carve "
        "a new mixin, don't grow one:\n  " + "\n  ".join(offenders)
    )


def test_guard_would_catch_a_regrown_module(tmp_path: Path) -> None:
    """Proven both ways: the check fires on an over-budget file."""
    fat = tmp_path / "fat.py"
    fat.write_text("\n".join(f"x{i} = {i}" for i in range(_MODULE_BUDGET + 1)))
    assert _lines(fat) > _MODULE_BUDGET
    lean = tmp_path / "lean.py"
    lean.write_text("x = 1\n")
    assert _lines(lean) <= _MODULE_BUDGET
