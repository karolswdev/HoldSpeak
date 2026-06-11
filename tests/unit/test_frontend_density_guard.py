"""HS-54-04: the dictation frontend density guard.

The dictation cockpit was paid down from 6,101 coupled lines in two files
(`dictation.astro` 3,134 + `dictation-app.js` 2,967) to a thin page + section
partials + single-concern behavior modules. The page-density invariant lost
five phases running before that (P40/P45/P47/P48/P53 each grew the page), so
this guard locks the shipped shape mechanically.

When this guard fires: **carve, don't bump.** A file over budget wants to be
split along the same seams this decomposition used — a new section partial
under `web/src/components/dictation/`, or a new behavior module under
`web/src/scripts/dictation/`. Raising a budget is a deliberate, reviewed
decision, not a reflex (see docs/internal/ARCHITECTURE_WEB_FRONTEND.md).
"""

from __future__ import annotations

from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_WEB_SRC = _REPO / "web" / "src"

# The page is a thin composition: spine markup + spine styles only.
_PAGE_BUDGET = 300
# The script entry only documents the module map and imports init.
_ENTRY_BUDGET = 50
# Section partials, shared-style components, and behavior modules are
# single-concern; anything bigger wants a split.
_COMPONENT_BUDGET = 600
_MODULE_BUDGET = 600


def _lines(path: Path) -> int:
    return len(path.read_text(encoding="utf-8").splitlines())


def test_dictation_page_stays_a_thin_composition() -> None:
    page = _WEB_SRC / "pages" / "dictation.astro"
    n = _lines(page)
    assert n <= _PAGE_BUDGET, (
        f"web/src/pages/dictation.astro is {n} lines (budget {_PAGE_BUDGET}). "
        "The page is a thin composition — new markup belongs in a section "
        "partial under web/src/components/dictation/, not in the page."
    )


def test_dictation_script_entry_stays_thin() -> None:
    entry = _WEB_SRC / "scripts" / "dictation-app.js"
    n = _lines(entry)
    assert n <= _ENTRY_BUDGET, (
        f"web/src/scripts/dictation-app.js is {n} lines (budget {_ENTRY_BUDGET}). "
        "The entry only imports init.js — new behavior belongs in a module "
        "under web/src/scripts/dictation/."
    )


def test_dictation_components_stay_single_concern() -> None:
    offenders = []
    for path in sorted((_WEB_SRC / "components" / "dictation").glob("*.astro")):
        n = _lines(path)
        if n > _COMPONENT_BUDGET:
            offenders.append(f"{path.name}: {n} lines")
    assert not offenders, (
        f"Dictation components over the {_COMPONENT_BUDGET}-line budget — "
        "carve along a section or shared-style seam rather than growing one "
        "component:\n  " + "\n  ".join(offenders)
    )


def test_dictation_modules_stay_single_concern() -> None:
    offenders = []
    for path in sorted((_WEB_SRC / "scripts" / "dictation").glob("*.js")):
        n = _lines(path)
        if n > _MODULE_BUDGET:
            offenders.append(f"{path.name}: {n} lines")
    assert not offenders, (
        f"Dictation behavior modules over the {_MODULE_BUDGET}-line budget — "
        "split by concern (a new module + registerSection/loadSection for "
        "cross-module reloads) rather than growing one module:\n  "
        + "\n  ".join(offenders)
    )


def test_density_guard_actually_scans_the_carved_tree() -> None:
    """Sanity: the guard sees the real files (a green result isn't vacuous)."""
    components = list((_WEB_SRC / "components" / "dictation").glob("*.astro"))
    modules = list((_WEB_SRC / "scripts" / "dictation").glob("*.js"))
    assert len(components) >= 10, "expected the section partials to exist"
    assert len(modules) >= 10, "expected the behavior modules to exist"
    assert any(p.name == "core.js" for p in modules)
    assert any(p.name == "SharedStyles.astro" for p in components)
