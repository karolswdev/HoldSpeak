#!/usr/bin/env python3
"""Check public Markdown navigation without importing the HoldSpeak runtime.

Checks inline/reference links to local files and GitHub-style heading anchors.
External URLs and code examples are not fetched or executed. This is a
navigation check, not an ASD-STE100 language or conformance checker.
"""
from __future__ import annotations

import argparse
import html
import re
import sys
import unicodedata
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
FENCE = re.compile(r"^\s*(`{3,}|~{3,})")
INLINE_CODE = re.compile(r"(`+).*?\1")
INLINE_LINK = re.compile(
    r"!?\[[^\]\n]*\]\(\s*(?:<([^>\n]+)>|([^\s)]+))"
    r"(?:\s+[\"'][^\n]*?[\"'])?\s*\)"
)
REFERENCE = re.compile(r"^\s{0,3}\[[^\]]+\]:\s*(?:<([^>]+)>|(\S+))")
ATX = re.compile(r"^\s{0,3}#{1,6}\s+(.+?)(?:\s+#+\s*)?$")
HTML_ANCHOR = re.compile(r"\b(?:id|name)=[\"']([^\"']+)[\"']")


def prose_lines(text: str) -> list[tuple[int, str]]:
    """Retain source line numbers while omitting fenced code blocks."""
    lines = []
    fence = ""
    for number, line in enumerate(text.splitlines(), 1):
        match = FENCE.match(line)
        if match:
            marker = match.group(1)
            if not fence:
                fence = marker
            elif marker[0] == fence[0] and len(marker) >= len(fence):
                fence = ""
            continue
        if not fence:
            lines.append((number, line))
    return lines


def slug(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"!?\[([^\]]+)\]\([^)]*\)", r"\1", text)
    text = html.unescape(text).lower().strip()
    return "".join(
        ch for ch in text
        if ch in " _-" or unicodedata.category(ch)[0] in "LNM"
    ).replace(" ", "-")


def anchors(text: str) -> set[str]:
    found: set[str] = set()
    generated: set[str] = set()
    previous = ""
    previous_number = 0
    for number, line in prose_lines(text):
        found.update(HTML_ANCHOR.findall(line))
        match = ATX.match(line)
        title = match.group(1) if match else None
        if (
            title is None and previous.strip() and number == previous_number + 1
            and re.fullmatch(r"\s{0,3}(?:=+|-+)\s*", line)
        ):
            title = previous
        if title:
            base = slug(title)
            candidate = base
            suffix = 0
            while candidate in generated:
                suffix += 1
                candidate = f"{base}-{suffix}"
            generated.add(candidate)
            found.add(candidate)
        previous, previous_number = line, number
    return found


def links(text: str) -> list[tuple[int, str]]:
    found = []
    for number, line in prose_lines(text):
        line = INLINE_CODE.sub("", line)
        for match in INLINE_LINK.finditer(line):
            found.append((number, match.group(1) or match.group(2)))
        reference = REFERENCE.match(line)
        if reference:
            found.append((number, reference.group(1) or reference.group(2)))
    return found


def public_documents(root: Path) -> list[Path]:
    return [root / "README.md", root / "CONTRIBUTING.md", *sorted((root / "docs").glob("*.md"))]


def check_documents(paths: list[Path], root: Path) -> list[str]:
    errors = []
    cache: dict[Path, set[str]] = {}
    for path in paths:
        label = str(path.relative_to(root)) if path.is_relative_to(root) else str(path)
        if not path.is_file():
            errors.append(f"{label}: missing document")
            continue
        for number, target in links(path.read_text(encoding="utf-8")):
            try:
                url = urlsplit(html.unescape(target))
            except ValueError:
                errors.append(f"{label}:{number}: invalid link {target}")
                continue
            if url.scheme or url.netloc or url.path.startswith("/"):
                continue
            destination = (path.parent / unquote(url.path)).resolve() if url.path else path.resolve()
            if not destination.exists():
                errors.append(f"{label}:{number}: missing target {target}")
                continue
            if url.fragment and destination.suffix.lower() == ".md" and destination.is_file():
                if destination not in cache:
                    cache[destination] = anchors(destination.read_text(encoding="utf-8"))
                fragment = unquote(url.fragment)
                if fragment not in cache[destination]:
                    errors.append(f"{label}:{number}: missing heading {target}")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", help="Optional Markdown files; default: all public guides")
    args = parser.parse_args(argv)
    paths = [Path(p).resolve() for p in args.paths] if args.paths else public_documents(ROOT)
    errors = check_documents(paths, ROOT)
    for error in errors:
        print(error, file=sys.stderr)
    if errors:
        print(f"Documentation navigation: {len(errors)} error(s)", file=sys.stderr)
        return 1
    print(f"Documentation navigation: {len(paths)} files checked; local targets and Markdown headings resolve.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
