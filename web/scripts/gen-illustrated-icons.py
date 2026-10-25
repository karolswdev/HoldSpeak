#!/usr/bin/env python3
"""Render the illustrated icon sources into the desk's existing PNG contract.

The SVGs in ``web/design/icons`` are the source of truth.  This script uses
the installed Playwright Chromium to make deterministic, transparent PNGs;
it does not add a runtime renderer or change any URL.  World art is exported
at its 64-unit size and at an optical 32-unit size.  System and Settings art
is exported at 32 units, except the existing 64 px Settings wallpaper asset,
whose dimension is part of the current contract.

Direction D (owner pick 2026-10-24, docs/internal/betterment/ICONS-D-2026-10-24.md)
adds a third optical level.  ``web/scripts/gen-icons-d.py`` writes each source
with its 64-unit level as CSS custom properties; ``LEVELS`` below overrides
them per export size: the 32 pass draws the bevel at one pixel under a heavier
outline, and the 20 pass (world ``20/`` and ``system/20/``, for dense rows and
title-bar glyphs) drops the bevel, thickens the outline and lightens the greys.

Run the normal export only after the SVG source set is frozen::

    uv run --with pillow python web/scripts/gen-illustrated-icons.py

The normal export parks the current active PNGs once, writes the new base
images, and invokes ``gen-sprite-states.py`` with this same Python interpreter
so the real ``_sel`` and ``_stale`` state contract remains unchanged.  Use
``--check`` to render into a temporary directory and compare base PNG bytes
without changing the tree.
"""

from __future__ import annotations

import argparse
import hashlib
import re
import shutil
import struct
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path


WEB = Path(__file__).resolve().parents[1]
REPO = WEB.parent
SVG_ROOT = WEB / "design" / "icons"
PNG_ROOT = WEB / "public" / "desk" / "sprites"
PARK_ROOT = SVG_ROOT / "_parked-richer-2026-10-24" / "png"
STATE_SCRIPT = WEB / "scripts" / "gen-sprite-states.py"

# Direction D optical levels, keyed by export size.  The source sets the 64
# level (``--ow`` outline 1.5, ``--u`` bevel offset 3.25 = 2.5-unit bevel plus
# half the outline, ``--lw`` line weight 1).  ``.detail`` is trim that may
# vanish below 64.
_GREY, _GREY_LIGHT = "#9fb3c8", "#c9d7e6"
LEVELS = {
    64: "",
    # 32 px: one-pixel bevel (2 units) under a 2.2 outline.
    32: (
        "svg{--ow:2.2px!important;--u:3.1px!important;--nu:-3.1px!important}"
        ".detail{display:none!important}"
    ),
    # 20 px: no bevel, a 3-unit outline, heavier lines and lighter greys.
    20: (
        "svg{--ow:3px!important;--u:0px!important;--nu:0px!important;--lw:1.35!important}"
        ".detail{display:none!important}"
        f'[fill="{_GREY}"]{{fill:{_GREY_LIGHT}!important}}'
        f'[stroke="{_GREY}"]{{stroke:{_GREY_LIGHT}!important}}'
    ),
}


@dataclass(frozen=True)
class Family:
    name: str
    source_dir: Path
    size: int
    target_dir: Path
    optical: bool = False


FAMILIES = (
    Family("world64", SVG_ROOT / "world", 64, PNG_ROOT),
    Family("world32", SVG_ROOT / "world", 32, PNG_ROOT / "32", optical=True),
    Family("world20", SVG_ROOT / "world", 20, PNG_ROOT / "20", optical=True),
    Family("system", SVG_ROOT / "system", 32, PNG_ROOT / "system", optical=True),
    Family("system20", SVG_ROOT / "system", 20, PNG_ROOT / "system" / "20", optical=True),
    Family("settings", SVG_ROOT / "settings", 32, PNG_ROOT / "settings", optical=True),
)

_STATES = ("_sel", "_stale")
_EXTERNAL_REF = re.compile(
    r"(?:href|xlink:href)\s*=\s*([\"'])(?P<value>(?:https?:|//|file:)[^\"']*)\1"
    r"|url\(\s*([\"']?)(?:https?:|//|file:)",
    re.IGNORECASE,
)


def source_files(family: Family) -> list[Path]:
    if not family.source_dir.is_dir():
        raise RuntimeError(f"missing SVG source directory: {family.source_dir}")
    files = sorted(family.source_dir.glob("*.svg"))
    if not files:
        raise RuntimeError(f"no SVG sources found under {family.source_dir}")
    return files


def active_base_stems(folder: Path) -> set[str]:
    """Read the existing base PNG names without descending into parked trees."""

    return {
        path.stem
        for path in folder.glob("*.png")
        if path.is_file() and not path.stem.endswith(_STATES)
    }


def validate_source_set() -> list[tuple[Family, Path]]:
    jobs: list[tuple[Family, Path]] = []
    for family in FAMILIES:
        files = source_files(family)
        source_stems = {path.stem for path in files}
        target_stems = active_base_stems(family.target_dir) if family.target_dir.is_dir() else set()
        # Every shipped PNG keeps its source (a name is never lost). A new
        # source adds a name; a new size family is created by its first export.
        if target_stems - source_stems:
            missing = ", ".join(sorted(target_stems - source_stems))
            raise RuntimeError(
                f"{family.name} source/asset contract differs; missing sources: {missing}"
            )
        for path in files:
            validate_svg(path)
            jobs.append((family, path))
    return jobs


def png_dimensions(path: Path) -> tuple[int, int]:
    """Read the existing PNG IHDR without adding Pillow to the renderer."""

    data = path.read_bytes()
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        raise RuntimeError(f"{path} is not a readable PNG")
    return struct.unpack(">II", data[16:24])


def render_size(family: Family, source_path: Path) -> int:
    """Return the contract size, retaining the historical 64 px wallpaper."""

    if family.name == "settings" and source_path.stem == "wallpaper":
        target = family.target_dir / f"{source_path.stem}.png"
        width, height = png_dimensions(target)
        if (width, height) != (64, 64):
            raise RuntimeError(
                f"settings wallpaper contract is 64x64, found {width}x{height} in {target}"
            )
        return 64
    return family.size


def validate_svg(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    if not re.search(r"<svg(?:\s|>)", text, re.IGNORECASE):
        raise RuntimeError(f"{path} does not contain an SVG root")
    if _EXTERNAL_REF.search(text):
        raise RuntimeError(f"{path} contains an external SVG/font/image reference")
    if re.search(r"<text(?:\s|>)", text, re.IGNORECASE):
        raise RuntimeError(f"{path} contains <text>; icon exports must not depend on fonts")

    # Let Chromium parse the source, while keeping the script dependency-light.
    try:
        from xml.etree import ElementTree

        ElementTree.fromstring(text)
    except Exception as exc:  # noqa: BLE001 - report the source path clearly
        raise RuntimeError(f"invalid SVG XML in {path}: {exc}") from exc


def optical_svg(source: str, size: int) -> str:
    """Append the size's optical level (``LEVELS``) to the source.

    The rules override the source's own CSS custom properties and hide
    ``.detail``; fills and strokes are not otherwise replaced.  The rules are
    appended last so they win over the source's own ``<style>``.
    """

    rules = LEVELS.get(size, LEVELS[32])
    if not rules:
        return source
    end = source.lower().rfind("</svg>")
    if end < 0:
        raise RuntimeError("could not locate SVG end tag")
    return source[:end] + "<style>" + rules + "</style>" + source[end:]


def html_for_svg(source: str, size: int) -> str:
    # The page itself is transparent.  The SVG is self-contained and has no
    # text, fonts, random data, or external resources to make the raster vary.
    return (
        '<!doctype html><meta charset="utf-8">'
        f'<style>html,body{{margin:0;width:{size}px;height:{size}px;'
        "overflow:hidden;background:transparent}"
        f"svg{{display:block;width:{size}px;height:{size}px}}</style>"
        f"{source}"
    )


def render_jobs(jobs: list[tuple[Family, Path]], output_dir: Path) -> None:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise RuntimeError(
            "Playwright is required; run with the repository dev environment "
            "or `uv run --with playwright python ...`"
        ) from exc

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=True,
            args=["--disable-gpu", "--force-color-profile=srgb"],
        )
        try:
            contexts: dict[int, object] = {}
            pages: dict[int, object] = {}
            for family, source_path in jobs:
                size = render_size(family, source_path)
                context = contexts.get(size)
                if context is None:
                    context = browser.new_context(
                        viewport={"width": size, "height": size},
                        device_scale_factor=1,
                        color_scheme="light",
                        reduced_motion="reduce",
                    )
                    context.route("**/*", lambda route: route.abort())
                    contexts[size] = context
                    pages[size] = context.new_page()
                page = pages[size]
                source = source_path.read_text(encoding="utf-8")
                if family.optical:
                    source = optical_svg(source, size)
                page.set_content(html_for_svg(source, size))
                # Force the first paint before collecting the bytes. Chromium
                # can otherwise capture a just-committed SVG path at a
                # different antialias phase on immediate navigation.
                page.evaluate("document.documentElement.getBoundingClientRect().width")
                page.wait_for_timeout(50)
                page.screenshot(
                    path=None,
                    omit_background=True,
                    animations="disabled",
                    caret="hide",
                )
                png = page.screenshot(
                    path=None,
                    omit_background=True,
                    animations="disabled",
                    caret="hide",
                )
                destination = output_dir / family.name / f"{source_path.stem}.png"
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(png)
            for context in contexts.values():
                context.close()
        finally:
            browser.close()


def park_active_pngs() -> int:
    """Copy active PNGs once, preserving their relative sprite structure."""

    count = 0
    for folder in (PNG_ROOT, PNG_ROOT / "32", PNG_ROOT / "20", PNG_ROOT / "system", PNG_ROOT / "system" / "20", PNG_ROOT / "settings"):
        if not folder.is_dir():
            continue
        for source in sorted(folder.glob("*.png")):
            if not source.is_file():
                continue
            relative = source.relative_to(PNG_ROOT)
            destination = PARK_ROOT / relative
            if destination.exists():
                continue
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
            count += 1
    return count


def write_exports(jobs: list[tuple[Family, Path]], rendered: Path) -> None:
    target_for_family = {family.name: family.target_dir for family, _ in jobs}
    for family, source_path in jobs:
        rendered_path = rendered / family.name / f"{source_path.stem}.png"
        target = target_for_family[family.name] / f"{source_path.stem}.png"
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(rendered_path, target)


def compare_exports(jobs: list[tuple[Family, Path]], rendered: Path) -> int:
    mismatches = 0
    for family, source_path in jobs:
        rendered_path = rendered / family.name / f"{source_path.stem}.png"
        target = family.target_dir / f"{source_path.stem}.png"
        expected = rendered_path.read_bytes()
        actual = target.read_bytes() if target.exists() else None
        if actual != expected:
            actual_hash = hashlib.sha256(actual).hexdigest()[:12] if actual is not None else "missing"
            expected_hash = hashlib.sha256(expected).hexdigest()[:12]
            print(f"different: {target} (expected {expected_hash}, found {actual_hash})")
            mismatches += 1
    return mismatches


def run(check: bool) -> int:
    jobs = validate_source_set()
    with tempfile.TemporaryDirectory(prefix="holdspeak-illustrated-icons-") as temporary:
        rendered = Path(temporary)
        render_jobs(jobs, rendered)
        if check:
            mismatches = compare_exports(jobs, rendered)
            if mismatches:
                print(f"{mismatches} base PNG export(s) differ")
                return 1
            print(f"checked {len(jobs)} deterministic base PNG exports")
            return 0

        parked = park_active_pngs()
        write_exports(jobs, rendered)
        print(f"parked {parked} active PNG originals under {PARK_ROOT}")

    result = subprocess.run([sys.executable, str(STATE_SCRIPT)], cwd=REPO, check=False)
    if result.returncode:
        return result.returncode
    print("derived _sel and _stale world state PNGs with gen-sprite-states.py")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="render into a temporary directory and compare base PNG bytes",
    )
    args = parser.parse_args()
    try:
        return run(check=args.check)
    except RuntimeError as exc:
        print(f"gen-illustrated-icons: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
