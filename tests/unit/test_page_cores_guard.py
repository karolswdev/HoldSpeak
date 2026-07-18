"""HS-95-04 — the page-core mechanical locks.

Cores are host-agnostic surfaces (Constitution, Article I): they render in
a flat route wrapper AND inside a desk window from one implementation, so
they must never couple to either host:

- no router hooks or Link (the host owns navigation and scope);
- no flat page chrome (.page-wrap / PageHero / WorkroomBar);
- no window.location reads (scope arrives as a prop).
"""

from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CORES = REPO / "web" / "src" / "pages" / "cores"

FORBIDDEN = (
    "useLocation",
    "useNavigate",
    "useSearchParams",
    "react-router",
    "PageHero",
    "WorkroomBar",
    "page-wrap",
    "page-hero",
    "workroom-bar",
    "window.location",
)


def test_cores_exist() -> None:
    assert CORES.is_dir(), "the cores directory is the pattern's home"
    assert list(CORES.glob("*.tsx")), "at least one extracted core"


def test_cores_are_host_agnostic() -> None:
    for path in sorted(CORES.glob("*.tsx")):
        text = path.read_text(encoding="utf-8")
        for token in FORBIDDEN:
            assert token not in text, (
                f"{path.name} couples to a host: forbidden token {token!r}"
            )
