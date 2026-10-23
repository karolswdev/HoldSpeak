#!/usr/bin/env python3
"""Render the illustrated icon sources into the desk's existing PNG contract.

The SVGs in ``web/design/icons`` are the source of truth.  This script uses
the installed Playwright Chromium to make deterministic, transparent PNGs;
it does not add a runtime renderer or change any URL.  World art is exported
at its 64-unit size and at an optical 32-unit size.  System and Settings art
is exported at 32 units, except the existing 64 px Settings wallpaper asset,
whose dimension is part of the current contract.

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
from decimal import Decimal, InvalidOperation
from pathlib import Path


WEB = Path(__file__).resolve().parents[1]
REPO = WEB.parent
SVG_ROOT = WEB / "design" / "icons"
PNG_ROOT = WEB / "public" / "desk" / "sprites"
PARK_ROOT = SVG_ROOT / "_parked-pixel-2026-10-22"
STATE_SCRIPT = WEB / "scripts" / "gen-sprite-states.py"

# The multiplier is intentionally modest.  It helps a 32 px outline survive
# optical reduction while leaving the source fill/stroke choices intact.
OPTICAL_STROKE_MULTIPLIER = Decimal("1.15")


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
    Family("system", SVG_ROOT / "system", 32, PNG_ROOT / "system"),
    Family("settings", SVG_ROOT / "settings", 32, PNG_ROOT / "settings"),
)

_STATES = ("_sel", "_stale")
_STROKE_WIDTH_ATTR = re.compile(
    r"\bstroke-width\s*=\s*([\"'])(?P<value>(?:\d+(?:\.\d+)?|\.\d+)(?:px)?)\1"
)
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
        target_stems = active_base_stems(family.target_dir)
        if source_stems != target_stems:
            missing = ", ".join(sorted(target_stems - source_stems)) or "none"
            extra = ", ".join(sorted(source_stems - target_stems)) or "none"
            raise RuntimeError(
                f"{family.name} source/asset contract differs; "
                f"missing sources: {missing}; extra sources: {extra}"
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


def number_text(value: Decimal) -> str:
    rendered = format(value, "f").rstrip("0").rstrip(".")
    return rendered or "0"


def optical_svg(source: str) -> str:
    """Add optical-only rules without changing fills or classless strokes.

    The selectors target only explicit ``stroke-width`` presentation
    attributes.  A classless fill or a stroke inherited from a classless
    element is therefore not replaced by a blanket ``* { stroke: ... }``
    rule.  ``.detail`` is the one source-level opt-out the artists use for
    marks that do not survive the 32 px export.
    """

    values: set[str] = set()
    for match in _STROKE_WIDTH_ATTR.finditer(source):
        raw = match.group("value")
        values.add(raw)

    rules = [".detail { display: none !important; }"]
    for raw in sorted(values, key=lambda value: Decimal(value.removesuffix("px"))):
        try:
            base = Decimal(raw.removesuffix("px"))
        except InvalidOperation as exc:
            raise RuntimeError(f"invalid stroke-width value in SVG: {raw}") from exc
        scaled = number_text(base * OPTICAL_STROKE_MULTIPLIER)
        rules.append(f'[stroke-width="{raw}"] {{ stroke-width: {scaled}px; }}')
    style = "<style>" + " ".join(rules) + "</style>"
    root = re.search(r"<svg(?:\s[^>]*)?>", source, re.IGNORECASE)
    if root is None:
        raise RuntimeError("could not locate SVG root")
    return source[: root.end()] + style + source[root.end() :]


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
                    source = optical_svg(source)
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
    for folder in (PNG_ROOT, PNG_ROOT / "32", PNG_ROOT / "system", PNG_ROOT / "settings"):
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
