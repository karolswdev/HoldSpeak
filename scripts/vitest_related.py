"""The web test files a change reaches, for scripts/quick_check.sh step 3.

    python scripts/vitest_related.py [--why] <web/src/... files>

Prints one test file per line (paths relative to web/, ready for
`vitest run`). With --why it prints, on stderr, one line per changed file:
how many files each rule chose and how the file was placed in its app.

The rule (2026-11-09, owner: test time and load "unacceptable"): one hop, no
transitive walk. Per changed file:
  (a) every test that imports it directly. A barrel edge is followed BY NAME
      (`import { CheckGadget } from "../surface"` depends on the module that
      exports CheckGadget), and a barrel or a module that only re-exports the
      file is the same hop, not a stop. `import * as`, a default import or a
      side-effect import of a barrel depends on every module it re-exports.
      Static, dynamic `import()`, `vi.mock("x")` and CSS `@import` are edges;
      `import type` is not (vitest erases it).
  (b) the per-app T2 files (`*.app.test.tsx`, the test diet) of the app the
      file belongs to: by folder (the nearest folder above it with app tests,
      short of a GENERIC folder) or by its entry in desk/applications.ts.
  (c) every test that names the file (a test that reads it by path).
A stylesheet selects (b) and (c) only. A changed test file runs itself.

Why so narrow (measured 2026-11-08, batch 23): the transitive walk with a
depth cap chose 204 files for 18 changed files, because hub modules
(DeskToolShelf, SessionPullout, AgentLane) and the app registry reach most of
the tree. What proves the rest: the web guards (quick_check.sh runs them on
every check), the desk sweep (every app at 1440 and 393), and the whole
vitest suite on main after the merge (check_web_baseline --run).
"""
from __future__ import annotations

import functools
import os
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




def resolve(spec: str, importer: Path, known: set[Path] | None = None) -> Path | None:
    """The file a relative specifier names, or None (a package or a miss).

    `known` (the graph's files) answers without a disk read per candidate.
    """
    if not spec.startswith("."):
        return None
    spec = spec.split("?", 1)[0]
    base = Path(os.path.normpath(importer.parent / spec))
    there = known.__contains__ if known is not None else Path.is_file
    for cand in (base, *(base.with_name(base.name + e) for e in EXTS),
                 *(base / f"index{e}" for e in EXTS)):
        if there(cand):
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


@functools.lru_cache(maxsize=4)
def graph_for(root: Path) -> "Graph":
    """One graph per tree per process (the tests ask many questions of it)."""
    return Graph(root)


class Graph:
    """The web/src import graph: file -> the files it depends on."""

    def __init__(self, root: Path) -> None:
        root = root.resolve()
        self.root = root
        # Parked modules are in the graph (live code may re-export one of
        # them); parked TESTS never run (vitest
        # excludes **/_parked/**), see is_test().
        self.files = [p for p in root.rglob("*") if p.suffix in EXTS and p.is_file()
                      and "node_modules" not in p.parts]
        self.known = set(self.files)
        self.reexports: dict[Path, dict[str, Path]] = {}  # barrel -> name -> source
        self.stars: dict[Path, list[Path]] = {}  # barrel -> `export *` sources
        self.barrels: set[Path] = set()
        self.edges: dict[Path, list[tuple[Path, set[str] | None]]] = {}
        self._parsed: dict[Path, str] = {}
        self.passthru: dict[Path, set[Path]] = {}  # module -> the modules it re-exports
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
                t = resolve(spec, f, self.known)
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
            t = resolve(spec, f, self.known)
            if t is None:
                continue
            names, whole = _names(clause)
            if kind == "export":
                n_reexport += 1
                self.passthru.setdefault(f, set()).add(t)
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
            t = resolve(spec, f, self.known)
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

    def direct_tests(self, p: Path, rev: dict[Path, set[Path]]) -> set[Path]:
        """The tests that import p: directly, through a barrel by name, or
        through a module that re-exports p (the same hop, not a stop)."""
        out: set[Path] = set()
        seen = {p}
        todo = [p]
        while todo:
            cur = todo.pop()
            for d in rev.get(cur, ()):
                if is_test(d):
                    out.add(d)
                elif d not in seen and cur in self.passthru.get(d, ()):
                    seen.add(d)
                    todo.append(d)
        return out


APP_TESTS = "**/*.app.test.tsx"  # the per-app T2 files (the test diet)
REGISTRY = "desk/applications.ts"
# Folders that hold many apps: the folder rule never stops on one of them,
# and a registry entry never owns one.
GENERIC = {"", "desk", "pages", "pages/cores", "features", "desk/components"}


def _generic(folder: Path) -> bool:
    return ("" if folder == Path(".") else folder.as_posix()) in GENERIC


def _key(word: str) -> str:
    """An app name, compared loosely: `Open-Decisions` and `decision` match."""
    w = re.sub(r"[^a-z0-9]", "", word.lower())
    return w[:-1] if w.endswith("s") else w


def _app_key(test: Path) -> str:
    """`programs.list.app.test.tsx` -> `program`."""
    return _key(test.name.split(".")[0])


def registry(root: Path) -> list[tuple[set[str], Path | None]]:
    """(the names, the loaded module) of every entry in the app registry."""
    reg = root / REGISTRY
    try:
        src = reg.read_text(encoding="utf-8")
    except OSError:
        return []
    out: list[tuple[set[str], Path | None]] = []
    for chunk in re.split(r"(?m)^\s*action:\s*", src)[1:]:
        action = re.match(r"\"([^\"]+)\"", chunk)
        if not action:
            continue
        words = action.group(1).split("-")
        keys = {_key("".join(words[1:] or words))}
        win = re.search(r"windowId:\s*\"([^\"]+)\"", chunk)
        if win:
            keys.add(_key(win.group(1).removeprefix("surface-").split(":")[0]))
        walk = re.search(r"\bwalk:\s*\"([^\"]+)\"", chunk)
        if walk:
            keys.add(_key(walk.group(1)))
        load = re.search(r"import\(\s*\"([^\"]+)\"", chunk)
        target = resolve(load.group(1), reg) if load else None
        if target:
            keys.add(_key(re.sub(r"(Core|Window)$", "", target.stem)))
        out.append((keys - {""}, target))
    return out


def app_tests(p: Path, root: Path, apps: list[Path],
              entries: list[tuple[set[str], Path | None]]) -> tuple[set[Path], str]:
    """The per-app T2 files of the app a file belongs to, and how it was placed.

    Folder: the app tests in the nearest folder above the file (or its
    __tests__) that holds any, short of a GENERIC folder. Registry: the entry
    whose loaded module is the file, whose own folder holds the file, or whose
    name is a folder above it; its app tests are the ones named like it.
    """
    rel = p.relative_to(root)
    out: set[Path] = set()
    how: list[str] = []
    for parent in rel.parents:
        if _generic(parent):
            break
        here = {a for a in apps if a.parent == root / parent
                or a.parent == root / parent / "__tests__"}
        if here:
            out |= here
            how.append(f"folder {parent.as_posix()}")
            break
    folders = {_key(q.name) for q in rel.parents if not _generic(q)}
    shared = {t.parent for _, t in entries if t is not None}
    shared = {d for d in shared if sum(1 for _, t in entries if t and t.parent == d) > 1}
    for keys, target in entries:
        mine = target == p or (keys & folders) or (
            target is not None and target.parent not in shared
            and not _generic(target.parent.relative_to(root))
            and target.parent in p.parents)
        if not mine:
            continue
        named = {a for a in apps if _app_key(a) in keys}
        if named:
            out |= named
            how.append("registry " + "/".join(sorted(keys)))
    return out, ", ".join(how) or "no app"


def related(changed: list[str], *, root: Path = WEB / "src",
            why: list[str] | None = None, graph: Graph | None = None) -> list[str]:
    """The test files to run for the changed files (paths relative to web/).

    Per changed file: (a) the tests that import it directly (a barrel or a
    module that only re-exports it is the same hop); (b) the per-app T2 files
    of its app; (c) the tests that name its file. A stylesheet selects (b)
    and (c) only. A changed test file always runs.
    """
    root = root.resolve()
    base = root.parent
    graph = graph or graph_for(root)
    rev = graph.reverse(False)
    tests_all = sorted(f for f in graph.files if is_test(f))
    apps = sorted(f for f in root.glob(APP_TESTS) if "_parked" not in f.parts)
    entries = registry(root)
    out: set[Path] = set()
    for rel in changed:
        rel = rel[len("web/"):] if rel.startswith("web/") else rel
        p = (base / rel).resolve()
        if not p.is_file():
            continue
        if is_test(p):
            out.add(p)
            if why is not None:
                why.append(f"{rel}: a test file, runs itself")
            continue
        direct = set() if p.suffix == ".css" else graph.direct_tests(p, rev)
        app, how = app_tests(p, root, apps, entries)
        word = re.compile(r"(?<![\w.-])" + re.escape(p.name) + r"(?![\w-])")
        named = {t for t in tests_all if word.search(graph._src(t))}
        out |= direct | app | named
        if why is not None:
            why.append(f"{rel}: {len(direct)} import it, {len(app)} app files ({how}), "
                       f"{len(named)} name it")
    return sorted(str(t.relative_to(base)) for t in out)


def main(argv: list[str]) -> int:
    show = "--why" in argv
    files = [a for a in argv if not a.startswith("--")]
    why: list[str] | None = [] if show else None
    for f in related(files, why=why):
        print(f)
    for line in why or []:
        print(f"vitest_related: {line}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
