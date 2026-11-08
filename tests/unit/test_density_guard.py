"""HS-63-05: the backend and frontend density guards.

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

Phase 79 (HS-79-04) extended the lock to the three packages that phase
carved: `db/activity/` (six concern mixins over BaseRepository),
`web/routes/system/` (five routers + shared helpers), and
`web/routes/primitives/` (seven family routers + shared run helpers).
The old watch item — `web/routes/meetings.py` — was resolved by Phase 72's
split. The new named watch item (deliberately NOT guarded here):
`holdspeak/db/core.py` (~1,266 lines) is the schema DDL + migration matrix,
pinned by the schema snapshot test — a different budget conversation; if it
keeps growing it earns its own phase, not a silent bump into this guard.
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


# Phase 79 (HS-79-04): the three packages that phase carved. Composed
# __init__ files stay composition-only; every concern module stays under the
# shared budget. settings.py is ONE concern (the settings PUT validation
# matrix, shipped at 701) and carries its own named budget — raising it is a
# reviewed decision, not a reflex.
_INIT_BUDGET = 90
_SETTINGS_ROUTER_BUDGET = 800

_P79_PACKAGES = (
    _HS / "db" / "activity",
    _HS / "web" / "routes" / "system",
    _HS / "web" / "routes" / "primitives",
)


def test_phase79_package_inits_stay_composition_only() -> None:
    offenders = []
    for pkg in _P79_PACKAGES:
        n = _lines(pkg / "__init__.py")
        if n > _INIT_BUDGET:
            offenders.append(f"{(pkg / '__init__.py').relative_to(_REPO)}: {n} lines")
    assert not offenders, (
        f"package __init__ files over the {_INIT_BUDGET}-line budget — an "
        "__init__ composes and re-exports; behavior belongs in a concern "
        "module:\n  " + "\n  ".join(offenders)
    )


def test_phase79_package_modules_stay_single_concern() -> None:
    offenders = []
    for pkg in _P79_PACKAGES:
        for path in sorted(pkg.glob("*.py")):
            if path.name == "__init__.py":
                continue
            budget = (
                _SETTINGS_ROUTER_BUDGET
                if path == _HS / "web" / "routes" / "system" / "settings.py"
                else _MODULE_BUDGET
            )
            n = _lines(path)
            if n > budget:
                offenders.append(f"{path.relative_to(_REPO)}: {n} lines (budget {budget})")
    assert not offenders, (
        "Phase-79 package modules over budget — carve a new concern module, "
        "don't grow one:\n  " + "\n  ".join(offenders)
    )


# Phase-91 React frontend density and hard-cut guard (merged from
# test_frontend_density_guard.py, the twin of the backend guard above).
SRC = _REPO / "web/src"


def test_route_compositions_stay_reviewable() -> None:
    offenders = []
    for path in sorted((SRC / "pages").glob("*.tsx")):
        size = path.stat().st_size
        if size > 45_000:
            offenders.append(f"{path.name}: {size:,} bytes")
    assert not offenders, "Route composition wants a bounded feature module:\n  " + "\n  ".join(offenders)


def test_shared_components_stay_single_concern() -> None:
    offenders = []
    for path in sorted((SRC / "components").rglob("*.tsx")):
        if path.stat().st_size > 30_000:
            offenders.append(path.name)
    assert not offenders, f"Oversized shared React components: {offenders}"


def test_hard_cut_has_no_parallel_frontend_tree() -> None:
    assert not list(SRC.rglob("*.astro"))
    assert not (SRC / "scripts").exists() or not list((SRC / "scripts").rglob("*.*"))
    assert (SRC / "main.tsx").is_file()
    assert (SRC / "routes.tsx").is_file()
    assert (SRC / "runtime/RuntimeBus.tsx").is_file()


# The Settings window is a composition (2026-11-08): the frame, the section
# list and the shared store wiring. Each section lives in
# web/src/pages/cores/settings/<Section>.tsx and the one settings writer in
# settings/writer.ts. It was 2,900 lines before that split.
_SETTINGS_CORE_BUDGET = 600


def test_settings_core_stays_a_composition() -> None:
    n = _lines(SRC / "pages/cores/SettingsCore.tsx")
    assert n < _SETTINGS_CORE_BUDGET, (
        f"web/src/pages/cores/SettingsCore.tsx is {n} lines (budget "
        f"{_SETTINGS_CORE_BUDGET}). It composes the sections only; a section's "
        "rows, state and reads belong in web/src/pages/cores/settings/<Section>.tsx. "
        "Carve, don't bump."
    )


# The Room is a composition (2026-11-08): the window frame, the two wings,
# the postures' routing and the shared read and store wiring. Each section
# lives in web/src/features/project-room/core/<Section>.tsx. It was 2,591
# lines before that split.
_ROOM_CORE_BUDGET = 600


def test_room_core_stays_a_composition() -> None:
    n = _lines(SRC / "features/project-room/ProjectRoomCore.tsx")
    assert n < _ROOM_CORE_BUDGET, (
        f"web/src/features/project-room/ProjectRoomCore.tsx is {n} lines (budget "
        f"{_ROOM_CORE_BUDGET}). It composes the sections only; a section's rows, "
        "state and reads belong in web/src/features/project-room/core/<Section>.tsx. "
        "Carve, don't bump."
    )


def test_settings_files_live_in_the_settings_folder() -> None:
    """Every Settings file is in web/src/pages/cores/settings/ (2026-11-08).

    SettingsCore.tsx is the one Settings file at the top of pages/cores/; the
    older settingsPrefs, settingsWindow, settingsPeople (and the rest) moved
    into the folder beside the sections that use them. A new Settings file goes
    in the folder too.
    """
    cores = SRC / "pages/cores"
    strays = sorted(
        p.name for p in cores.iterdir()
        if p.is_file() and p.name.lower().startswith("settings") and p.name != "SettingsCore.tsx"
    )
    assert not strays, (
        f"Settings files at the top of web/src/pages/cores/: {strays}. "
        "Put them in web/src/pages/cores/settings/."
    )


# The Programs app tests are split by face (2026-11-08): one file per concern,
# sharing web/src/desk/programs/__tests__/programs.test-setup.tsx (the mocks,
# the recorded answers, the helpers). programs.app.test.tsx was 3,735 lines
# before that split. A new case goes in the file of its face; a file that
# outgrows the budget is split by concern, never bumped.
_PROGRAMS_TESTS = SRC / "desk/programs/__tests__"
_PROGRAMS_TEST_FILES = (
    "programs.list.app.test.tsx",
    "programs.needs.app.test.tsx",
    "programs.wizard.app.test.tsx",
    "programs.window.app.test.tsx",
    "programs.steps.app.test.tsx",
    "programs.text.app.test.tsx",
    "programs.plan.app.test.tsx",
    "programs.test-setup.tsx",
)
_PROGRAMS_TEST_BUDGET = 900


def test_programs_app_tests_stay_split_by_face() -> None:
    assert not (_PROGRAMS_TESTS / "programs.app.test.tsx").exists(), (
        "web/src/desk/programs/__tests__/programs.app.test.tsx is back. Put each "
        "case in the programs.<face>.app.test.tsx of its face."
    )
    offenders = []
    for name in _PROGRAMS_TEST_FILES:
        n = _lines(_PROGRAMS_TESTS / name)
        if n > _PROGRAMS_TEST_BUDGET:
            offenders.append(f"{name}: {n} lines (budget {_PROGRAMS_TEST_BUDGET})")
    assert not offenders, (
        "Programs app test files over budget. Split the file by concern; do not "
        "bump the budget:\n  " + "\n  ".join(offenders)
    )
