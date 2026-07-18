"""HS-95-08 — the no-exit mechanical lock (Constitution, Article I).

The desk never leaves the desk: no router imports, no route links, no
workroom-href bridges anywhere under web/src/desk. Surfaces open through
the shell dispatcher; external `<a>` links (receipts, PRs, assets) remain
legal. The routing table itself stays three real routes + demoted deep
links.
"""

from pathlib import Path
import re

REPO = Path(__file__).resolve().parents[2]
WEB = REPO / "web" / "src"
DESK = WEB / "desk"


def _sources(root: Path):
    for p in sorted(root.rglob("*")):
        if p.suffix not in {".ts", ".tsx"}:
            continue
        if ".test." in p.name or "__tests__" in str(p):
            continue
        yield p


def test_desk_components_never_navigate() -> None:
    for path in _sources(DESK):
        text = path.read_text(encoding="utf-8")
        rel = path.relative_to(REPO)
        assert "react-router" not in text, f"{rel}: router import on the desk"
        assert "<Link" not in text, f"{rel}: route link on the desk"
        assert "workroomHref(" not in text, f"{rel}: workroom href bridge"
        assert "window.location.href =" not in text, f"{rel}: raw navigation"
        assert "location.assign(" not in text, f"{rel}: raw navigation"


def test_routes_are_three_surfaces_plus_deep_links() -> None:
    text = (WEB / "routes.tsx").read_text(encoding="utf-8")
    product = text.split("PRODUCT_ROUTES: ProductRoute[] = [", 1)[1].split("];", 1)[0]
    rendered = re.findall(r'path: "([^"]+)"', product)
    assert rendered == ["/", "/welcome", "/presence"], rendered
    # Every legacy product path is demoted, present exactly once.
    demoted = re.findall(r'path: "(/[^"]*)",\n?\s*surface:', text.replace("\n", " "))
    for path in (
        "/setup", "/dictation", "/live", "/history", "/meetings",
        "/settings", "/activity", "/commands", "/cadence", "/studio",
        "/workbench", "/profiles", "/companion", "/docs/dictation-runtime",
        "/design/components",
    ):
        assert f'path: "{path}"' in text, f"missing demoted path {path}"


def test_flat_shell_is_gone() -> None:
    shell = (WEB / "components" / "AppShell.tsx").read_text(encoding="utf-8")
    assert "PRIMARY_NAV" not in shell
    assert "app-header" not in shell
    assert not (WEB / "pages" / "SettingsPage.tsx").exists()
    assert not (WEB / "pages" / "DictationPage.tsx").exists()
