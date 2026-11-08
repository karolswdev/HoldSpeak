#!/usr/bin/env python3
"""Which web/src modules does no entry point reach?

Roots: every <script type="module" src> in web/*.html. Edges: static imports,
side-effect imports, re-exports, import() calls and CSS @import. Bare
specifiers (packages) are not followed. Test files, fixtures, .d.ts, src/test/ and _parked/ are
never counted as reached or unreached.

  uv run python scripts/web_reachable.py            # unreached, by directory
  uv run python scripts/web_reachable.py --list     # one path per line
  uv run python scripts/web_reachable.py --why PATH # one import chain to PATH
"""
from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path

WEB = Path(__file__).resolve().parent.parent / "web"
SRC = WEB / "src"
EXTS = (".ts", ".tsx", ".js", ".jsx", ".mjs", ".css", ".json")
SPEC = re.compile(
    r"""(?:\bfrom\s*|\bimport\s*\(\s*|\bimport\s+|@import\s+(?:url\()?)["']([^"']+)["']""",
)
COMMENT = re.compile(r"/\*.*?\*/|(?<![:\"'`\\])//[^\n]*", re.S)


def is_test(path: Path) -> bool:
    rel = path.relative_to(SRC).as_posix()
    return (
        "__tests__/" in rel
        or "__fixtures__/" in rel
        or "/fixtures/" in rel
        or rel.startswith("test/")
        or rel.endswith(".d.ts")
        or re.search(r"\.(test|spec)\.[jt]sx?$", rel) is not None
    )


def is_parked(path: Path) -> bool:
    return "_parked" in path.relative_to(SRC).parts


def resolve(spec: str, importer: Path) -> Path | None:
    spec = spec.split("?", 1)[0]
    if spec.startswith("/"):
        base = WEB / spec.lstrip("/")
    elif spec.startswith("."):
        base = (importer.parent / spec).resolve()
    else:
        return None
    candidates = [base] + [base.with_name(base.name + e) for e in EXTS]
    candidates += [base / ("index" + e) for e in EXTS]
    # TS lets "./x.js" name "./x.ts".
    if base.suffix in (".js", ".jsx"):
        candidates += [base.with_suffix(e) for e in (".ts", ".tsx")]
    for c in candidates:
        if c.is_file():
            return c
    return None


def edges(path: Path) -> list[Path]:
    text = path.read_text(encoding="utf-8", errors="replace")
    if path.suffix != ".json":
        text = COMMENT.sub("", text)
    out = []
    for spec in SPEC.findall(text):
        target = resolve(spec, path)
        if target is not None:
            out.append(target)
    return out


def roots() -> list[Path]:
    found = []
    for html in sorted(WEB.glob("*.html")):
        for src in re.findall(r'<script[^>]*src="([^"]+)"', html.read_text()):
            target = resolve(src, html)
            if target is not None:
                found.append(target)
    return found


def walk(start: list[Path]) -> dict[Path, Path | None]:
    parent: dict[Path, Path | None] = {r: None for r in start}
    queue = list(start)
    while queue:
        node = queue.pop()
        for nxt in edges(node):
            if nxt not in parent:
                parent[nxt] = node
                queue.append(nxt)
    return parent


def lines(path: Path) -> int:
    return path.read_text(encoding="utf-8", errors="replace").count("\n")


def candidates() -> list[Path]:
    return sorted(
        p for p in SRC.rglob("*")
        if p.is_file() and p.suffix in EXTS and not is_test(p) and not is_parked(p)
    )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--list", action="store_true", help="print unreached paths only")
    ap.add_argument("--why", help="print one import chain from a root to this path")
    ap.add_argument("--depth", type=int, default=2, help="directory depth for grouping")
    args = ap.parse_args()
    parent = walk(roots())
    if args.why:
        node: Path | None = (WEB.parent / args.why).resolve()
        if node not in parent:
            print("unreached")
            return 1
        while node is not None:
            print(node.relative_to(WEB.parent).as_posix())
            node = parent[node]
        return 0
    files = candidates()
    unreached = [p for p in files if p not in parent]
    if args.list:
        for p in unreached:
            print(p.relative_to(WEB.parent).as_posix())
        return 0
    groups: dict[str, list[int]] = defaultdict(lambda: [0, 0, 0, 0])
    for p in files:
        key = "/".join(p.relative_to(SRC).parts[: args.depth][:-1] or ["."]) if len(p.relative_to(SRC).parts) > 1 else "."
        row = groups[key]
        n = lines(p)
        if p in parent:
            row[0] += 1; row[1] += n
        else:
            row[2] += 1; row[3] += n
    print(f"{'directory':40} {'reached':>8} {'lines':>8} {'unreached':>10} {'lines':>8}")
    tot = [0, 0, 0, 0]
    for key in sorted(groups):
        row = groups[key]
        tot = [a + b for a, b in zip(tot, row)]
        print(f"{key:40} {row[0]:>8} {row[1]:>8} {row[2]:>10} {row[3]:>8}")
    print(f"{'TOTAL':40} {tot[0]:>8} {tot[1]:>8} {tot[2]:>10} {tot[3]:>8}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
