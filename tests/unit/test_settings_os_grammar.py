"""The Settings client gets its material from the surface kit."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
WEB = ROOT / "web/src"


def test_settings_imports_styles_only_from_the_surface_kit() -> None:
    paths = [WEB / "pages/cores/SettingsCore.tsx"]
    for folder in ("settings", "connections"):
        paths.extend(path for path in (WEB / "pages/cores" / folder).rglob("*.ts*") if "_parked" not in path.parts)
    for path in paths:
        for relative in re.findall(r'(?:import\s+[\s\S]*?from\s+|import\s*)[\'"]([^\'\"]+\.css)[\'\"]', path.read_text()):
            target = (path.parent / relative).resolve()
            assert target.is_relative_to(WEB / "desk/surface"), f"{path}: {relative} belongs in the kit"
