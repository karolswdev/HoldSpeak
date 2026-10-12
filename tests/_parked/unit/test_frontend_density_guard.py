"""Phase-91 React frontend density and hard-cut guard."""
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SRC = REPO / "web/src"


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
