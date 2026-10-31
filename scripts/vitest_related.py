"""The web test files a change reaches, for scripts/quick_check.sh step 3.

    python scripts/vitest_related.py [--why] [--plain] <web/src/... files>

Prints one test file per line (paths relative to web/, ready for
`vitest run`). With --why it prints, on stderr, how many files it chose for
each changed file and why.

Why not `vitest related` (2026-10-31): vitest follows every import
transitively. Feature code imports the species through the barrels
(`desk/surface/index.ts` and its siblings), and almost every test imports a
barrel, so a change to one species file or its stylesheet (gadgets.css) or to
a shared module selected all 431 test files: a 6-minute quick check.

The cut: the same reverse import walk, but a barrel edge is followed BY NAME.
A module that writes `import { CheckGadget } from "../surface"` depends on the
module that exports CheckGadget, not on all 40 modules the barrel re-exports.
Everything else stays conservative, so no direct dependent is dropped:
  * every non-barrel import (static, dynamic `import()`, side-effect
    `import "x"`, `vi.mock("x")`, CSS `@import`) is an edge, transitively;
  * `import * as`, a default import, `export * from` a barrel, a side-effect
    import of a barrel, or a name the barrel does not resolve depends on
    every module the barrel re-exports;
  * a change to the barrel file itself reaches every importer of it;
  * a changed test file always runs.
The barrel cut alone is not enough: the store imports the app registry
(desk/applications.ts), which imports every app, so a module used by one app
still reaches about 420 tests through `store`. So the second cut: when the
walk holds more than CAP (120) test files, run the tests within two imports of
the changed file (always: the tests that import it, and the tests of every
module that imports it), deeper rings while the total stays under CAP, every
per-app T2 file (`__tests__/*.app.test.tsx`) and every test that names the
file (a test that reads it by path). --why prints the reason.
`import type` and `export type` are erased before the test runs, so they are
not edges (vitest does not follow them either).

What this does not prove, and what does: a stylesheet change reaches only the
tests that render a component that imports it. The page-wide look of CSS is
proved by the desk sweep (every app at 1440 and 393) and the web guards
(containerQueryLaw, kitDelight, the words censuses), which run on every quick
check. The whole vitest suite still runs on main after the merge
(check_web_baseline --run). --plain prints vitest's own transitive set
(no barrel cut), for comparison.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web"
EXTS = (".ts", ".tsx", ".js", ".jsx", ".mjs", ".css", ".json")
TEST_RE = re.compile(r"\.test\.(ts|tsx|js|jsx)$")


def is_test(p: Path) -> bool:
    """A test file vitest runs (vitest excludes **/_parked/**)."""
    return bool(TEST_RE.search(p.name)) and "_parked" not in p.parts

_COMMENT = re.compile(r"/\*.*?\*/|//[^\n]*", re.S)
# import ... from "x" | export ... from "x": the clause holds only names,
# braces, commas, `*` and comments (multi-line specifier lists).
_FROM = re.compile(
    r"(?m)^\s*(import|export)\s+(type\s+)?((?:[\w\s{},*$]|//[^\n]*|/\*.*?\*/)*?)\s*from\s*[\"']([^\"']+)[\"']",
    re.S,
)
_BARE = re.compile(r"(?m)^\s*import\s+[\"']([^\"']+)[\"']")
_DYN = re.compile(r"(?:\bimport|\bvi\.(?:mock|doMock|importActual))\s*\(\s*[\"']([^\"']+)[\"']")
_CSS = re.compile(r"@import\s+(?:url\()?[\"']([^\"']+)[\"']")
_DECL = re.compile(
    r"(?m)^\s*export\s+(?:declare\s+)?(?:default\s+)?(?:async\s+)?"
    r"(?:const|let|var|function\*?|class|enum|interface|type|abstract\s+class)\s+([A-Za-z_$][\w$]*)"
)




def resolve(spec: str, importer: Path) -> Path | None:
    """The file a relative specifier names, or None (a package or a miss)."""
    if not spec.startswith("."):
        return None
    spec = spec.split("?", 1)[0]
    base = (importer.parent / spec).resolve()
    if base.is_file():
        return base
    for ext in EXTS:
        cand = base.with_name(base.name + ext)
        if cand.is_file():
            return cand
    for ext in EXTS:
        cand = base / f"index{ext}"
        if cand.is_file():
            return cand
    return None


def _names(clause: str) -> tuple[set[str], bool]:
    """(the value names a specifier clause binds, whether it binds them all).

    `{ A, type B, C as D }` binds {A, C}; `* as X`, a default import, or
    `*` binds everything.
    """
    clause = _COMMENT.sub(" ", clause).strip()
    whole = False
    names: set[str] = set()
    m = re.search(r"\{([^}]*)\}", clause, re.S)
    rest = clause[: m.start()] + clause[m.end():] if m else clause
    if m:
        for part in m.group(1).split(","):
            part = part.strip()
            if not part or part.startswith("type "):
                continue
            names.add(part.split(" as ")[0].strip())
    rest = rest.replace(",", " ").strip()
    if rest:  # `* as X`, `*`, or a default binding
        whole = True
    return names, whole


class Graph:
    """The web/src import graph: file -> the files it depends on."""

    def __init__(self, root: Path) -> None:
        self.root = root
        # Parked modules are in the graph (live code re-exports some of them,
        # desk/components/SystemShade.tsx); parked TESTS never run (vitest
        # excludes **/_parked/**), see is_test().
        self.files = [p for p in root.rglob("*") if p.suffix in EXTS and p.is_file()
                      and "node_modules" not in p.parts]
        self.reexports: dict[Path, dict[str, Path]] = {}  # barrel -> name -> source
        self.stars: dict[Path, list[Path]] = {}  # barrel -> `export *` sources
        self.barrels: set[Path] = set()
        self.edges: dict[Path, list[tuple[Path, set[str] | None]]] = {}
        self._parsed: dict[Path, str] = {}
        self._rev: dict[bool, dict[Path, set[Path]]] = {}
        for f in self.files:
            self._scan(f)

    def _src(self, f: Path) -> str:
        if f not in self._parsed:
            try:
                # Not comment-stripped: a commented import is an extra edge
                # (harmless); a stripped real one would drop a dependent.
                self._parsed[f] = f.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                self._parsed[f] = ""
        return self._parsed[f]

    def _scan(self, f: Path) -> None:
        if f.suffix == ".json":
            self.edges[f] = []
            return
        src = self._src(f)
        out: list[tuple[Path, set[str] | None]] = []
        if f.suffix == ".css":
            for spec in _CSS.findall(src):
                t = resolve(spec, f)
                if t:
                    out.append((t, None))
            self.edges[f] = out
            return
        names_out: dict[str, Path] = {}
        stars: list[Path] = []
        n_reexport = 0
        for kind, is_type, clause, spec in _FROM.findall(src):
            if is_type:
                continue
            t = resolve(spec, f)
            if t is None:
                continue
            names, whole = _names(clause)
            if kind == "export":
                n_reexport += 1
                if clause.strip() == "*" or clause.strip().startswith("* as"):
                    stars.append(t)
                for part in re.findall(r"\{([^}]*)\}", _COMMENT.sub(" ", clause), re.S)[:1]:
                    for p in part.split(","):
                        p = p.strip()
                        if p and not p.startswith("type "):
                            src_name, _, alias = p.partition(" as ")
                            names_out[(alias or src_name).strip()] = t
            if not names and not whole:
                # `import { type A } from` binds no value: erased
                continue
            out.append((t, None if whole else names))
        for spec in _BARE.findall(src) + _DYN.findall(src):
            t = resolve(spec, f)
            if t:
                out.append((t, None))
        self.edges[f] = out
        if f.stem == "index" and n_reexport and (names_out or stars):
            self.barrels.add(f)
            self.reexports[f] = names_out
            self.stars[f] = stars

    def exports_of(self, f: Path, seen: set[Path] | None = None) -> set[str]:
        """The value names a module exports (its own and its re-exports)."""
        seen = seen or set()
        if f in seen:
            return set()
        seen.add(f)
        src = self._src(f)
        names = set(_DECL.findall(src))
        for clause in re.findall(r"(?m)^\s*export\s+\{([^}]*)\}", src, re.S):
            for p in _COMMENT.sub(" ", clause).split(","):
                p = p.strip()
                if p and not p.startswith("type "):
                    src_name, _, alias = p.partition(" as ")
                    names.add((alias or src_name).strip())
        for t in self.stars.get(f, []):
            names |= self.exports_of(t, seen)
        return names

    def through(self, barrel: Path, names: set[str] | None, seen: frozenset = frozenset()) -> set[Path]:
        """The modules behind `names` of a barrel (every module when None).

        A name re-exported from a nested barrel resolves in that barrel.
        """
        if barrel in seen:
            return set()
        seen = seen | {barrel}
        every_src = set(self.reexports[barrel].values()) | set(self.stars[barrel])
        if names is None:
            out: set[Path] = set()
            for t in every_src:
                out |= self.through(t, None, seen) if t in self.barrels else {t}
            return out
        out = set()
        for n in names:
            if n in self.reexports[barrel]:
                srcs = [self.reexports[barrel][n]]
            else:
                srcs = [t for t in self.stars[barrel] if n in self.exports_of(t)]
                if not srcs:
                    return self.through(barrel, None, seen - {barrel})  # unplaced: all
            for t in srcs:
                out |= self.through(t, {n}, seen) if t in self.barrels else {t}
        return out

    def reverse(self, plain: bool) -> dict[Path, set[Path]]:
        """dependency -> its direct dependents (the barrel cut unless plain)."""
        if plain in self._rev:
            return self._rev[plain]
        rev: dict[Path, set[Path]] = {}
        self._rev[plain] = rev
        for f, deps in self.edges.items():
            reexported = set()
            if not plain and f in self.barrels:
                # A barrel's re-export edges are not followed under the cut:
                # a dependent reaches a module through it only by name.
                reexported = set(self.reexports[f].values()) | set(self.stars[f])
            for t, names in deps:
                if t in reexported:
                    continue
                rev.setdefault(t, set()).add(f)  # f depends on the file it names
                if not plain and t in self.barrels:
                    for m in self.through(t, names):
                        rev.setdefault(m, set()).add(f)
        return rev


CAP = 120  # above this many files, the walk is cut by depth (see related())
APP_TESTS = "**/__tests__/*.app.test.tsx"  # the per-app T2 files (the test diet)


def _depths(start: Path, rev: dict[Path, set[Path]]) -> dict[Path, int]:
    """Every dependent of start with its import distance (breadth first)."""
    dist = {start: 0}
    queue = [start]
    for cur in queue:
        for d in sorted(rev.get(cur, ())):
            if d not in dist:
                dist[d] = dist[cur] + 1
                queue.append(d)
    return dist


def related(changed: list[str], *, plain: bool = False, root: Path = WEB / "src",
            cap: int = CAP, why: list[str] | None = None,
            graph: Graph | None = None) -> list[str]:
    """The test files to run for the changed files (paths relative to web/).

    Per changed file: the whole reverse walk (the barrel cut unless plain).
    When that walk holds more than `cap` test files, it is cut by depth:
    the tests that import the file or a module that imports it (distance 2,
    always kept), deeper rings while the total stays under the cap, every
    per-app T2 file, and every test that names the file (a path reader).
    A changed test file always runs.
    """
    base = root.parent
    graph = graph or Graph(root)
    rev = graph.reverse(plain)
    tests_all = sorted(f for f in graph.files if is_test(f))
    apps = {f for f in root.glob(APP_TESTS) if "_parked" not in f.parts}
    out: set[Path] = set()
    for rel in changed:
        rel = rel[len("web/"):] if rel.startswith("web/") else rel
        p = (base / rel).resolve()
        if not p.is_file():
            continue
        if is_test(p):
            out.add(p)
        dist = _depths(p, rev)
        tests = {t: d for t, d in dist.items() if is_test(t)}
        if plain or len(tests) <= cap:
            out |= set(tests)
            if why is not None:
                why.append(f"{rel}: all {len(tests)} dependent test files")
            continue
        depth = 2
        while sum(1 for d in tests.values() if d <= depth + 1) <= cap:
            depth += 1
        near = {t for t, d in tests.items() if d <= depth}
        named = {t for t in tests_all if p.name in graph._src(t)}
        out |= near | apps | named
        if why is not None:
            why.append(
                f"{rel}: {len(tests)} dependent test files, over the cap of {cap}: "
                f"ran the {len(near)} within {depth} imports, the {len(apps)} app files "
                f"and the {len(named)} that name it"
            )
    return sorted(str(t.relative_to(base)) for t in out)


def main(argv: list[str]) -> int:
    plain = "--plain" in argv
    show = "--why" in argv
    files = [a for a in argv if not a.startswith("--")]
    why: list[str] | None = [] if show else None
    for f in related(files, plain=plain, why=why):
        print(f)
    for line in why or []:
        print(f"vitest_related: {line}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
