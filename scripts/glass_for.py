#!/usr/bin/env python3
"""Print the pytest command for the browser tests that cover a change.

    uv run python scripts/glass_for.py              # diff against origin/main
    uv run python scripts/glass_for.py --base HEAD~1
    uv run python scripts/glass_for.py web/src/desk/delivery.ts   # named paths
    eval "$(uv run python scripts/glass_for.py --quiet)"   # run the command
    uv run python scripts/glass_for.py --paths      # the test paths only (CI)

The full browser suite (tests/e2e) is the nightly run. Before a merge, run
only the browser tests that read the changed code. A browser test is picked
when one of these is true:

1. The changed file is the test file.
2. The test file names the changed file (rigs cite their sources:
   "DeskMenu.tsx", "door_service.py").
3. A word of the changed path is an AREA key, and the test file name has one
   of that area's words.

A change to the shared rig (tests/e2e/conftest.py, glass_infra.py) selects
the whole of tests/e2e. A change that selects nothing but touches the web or
the hub selects the SMOKE set.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
E2E = REPO / "tests" / "e2e"

# A word in a changed path -> words to look for in browser test file names.
AREAS: dict[str, tuple[str, ...]] = {
    "delivery": ("send", "delivery", "update"),
    "send": ("send",),
    "channel": ("send",),
    "destination": ("send",),
    "zone": ("zone", "list_rename", "desk_debts"),
    "list": ("list_rename", "desk_debts", "one_delete"),
    "delete": ("delete",),
    "menu": ("desk_debts", "dock", "palette"),
    "palette": ("palette",),
    "dock": ("dock",),
    "chair": ("chair", "arrival", "needs_you", "one_thing"),
    "door": ("door",),
    "room": ("room",),
    "project": ("room", "project_grant", "door"),
    "steward": ("steward", "room"),
    "meeting": ("meeting", "summary", "record", "decide", "prep"),
    "summary": ("summary",),
    "people": ("people",),
    "calendar": ("calendar", "arrival", "rhythm"),
    "rhythm": ("rhythm",),
    "thought": ("thought",),
    "refinement": ("thought", "refinement", "context"),
    "note": ("thought_note", "editor"),
    "editor": ("editor",),
    "thread": ("thread", "hands", "call"),
    "dictation": ("dictation", "journal", "speak", "loop"),
    "journal": ("journal",),
    "voice": ("voice", "speak", "capture"),
    "capture": ("capture", "one_tap", "record"),
    "inference": ("models", "assignments", "model_library", "connect_engine", "readiness"),
    "model": ("models", "model_library", "model_acquisition", "connect_engine"),
    "settings": ("settings",),
    "connection": ("connections", "sources", "jira", "github"),
    "jira": ("jira",),
    "github": ("github",),
    "confluence": ("confluence",),
    "window": ("window", "frame", "titlebar", "close", "open", "remembers", "park"),
    "frame": ("frame", "titlebar", "chair_glass"),
    "surface": ("species", "button", "type_floor", "faces"),
    "button": ("button", "species"),
    "memory": ("memory", "remembers"),
    "attention": ("attention", "needs_you"),
    "mesh": ("mesh",),
    "authority": ("grant", "policy", "unattended"),
    "grant": ("grant",),
}
SMOKE = ("test_graph_walk_smoke.py", "test_hs202_first_use_smoke.py", "test_route_preflight.py")
SHARED_RIG = {"tests/e2e/conftest.py", "tests/e2e/glass_infra.py"}
# File names too common to be a citation.
COMMON_NAMES = {"index.ts", "index.tsx", "__init__.py", "types.ts", "api.ts", "conftest.py", "core.py"}


def changed_paths(base: str) -> list[str]:
    out = subprocess.run(
        ["git", "diff", "--name-only", f"{base}...HEAD"], cwd=REPO, capture_output=True, text=True, check=True,
    ).stdout.split()
    out += subprocess.run(
        ["git", "diff", "--name-only", "HEAD"], cwd=REPO, capture_output=True, text=True, check=True,
    ).stdout.split()
    return sorted(set(out))


def words(path: str) -> set[str]:
    """The lower-case words of a path: split on separators and on camelCase."""
    spaced = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", path)
    found = {w.lower() for w in re.split(r"[^A-Za-z0-9]+", spaced) if w}
    return found | {w[:-1] for w in found if w.endswith("s")}


def select(paths: list[str]) -> tuple[list[str], dict[str, str]]:
    tests = sorted(p for p in E2E.glob("test_*.py") if p.name != "test_metal.py")
    text = {t: t.read_text(encoding="utf-8", errors="replace") for t in tests}
    why: dict[str, str] = {}
    touches_product = False
    for path in paths:
        if path in SHARED_RIG:
            return ["tests/e2e"], {"tests/e2e": f"{path} is the shared rig"}
        name = Path(path).name
        if path.startswith("tests/e2e/") and name.startswith("test_") and (REPO / path).exists():
            why.setdefault(path, "changed")
            continue
        if not path.startswith(("web/src/", "holdspeak/")):
            continue
        touches_product = True
        area_words = {w for key in words(path) if key in AREAS for w in AREAS[key]}
        for test in tests:
            rel = test.relative_to(REPO).as_posix()
            if name not in COMMON_NAMES and name in text[test]:
                why.setdefault(rel, f"names {name}")
            elif hit := next((w for w in sorted(area_words) if w in test.name), None):
                why.setdefault(rel, f"area '{hit}' ({path})")
    if not why and touches_product:
        why = {f"tests/e2e/{name}": "smoke (no browser test names the change)" for name in SMOKE}
    return sorted(why), why


def main(argv: list[str]) -> int:
    quiet = "--quiet" in argv
    only_paths = "--paths" in argv  # CI: print the test paths, nothing else
    args = [a for a in argv if a not in ("--quiet", "--paths")]
    base = "origin/main"
    if "--base" in args:
        i = args.index("--base")
        base = args[i + 1]
        del args[i:i + 2]
    paths = args or changed_paths(base)
    selected, why = select(paths)
    if only_paths:
        print(" ".join(selected))
        return 0
    if not selected:
        if not quiet:
            print(f"# {len(paths)} changed path(s); no browser test covers them.", file=sys.stderr)
        print("true")
        return 0
    if not quiet:
        print(f"# {len(paths)} changed path(s) -> {len(selected)} browser test file(s)", file=sys.stderr)
        for test in selected:
            print(f"#   {test}: {why[test]}", file=sys.stderr)
    print(
        "H=$(mktemp -d); PLAYWRIGHT_BROWSERS_PATH=${PLAYWRIGHT_BROWSERS_PATH:-$HOME/Library/Caches/ms-playwright} HOME=$H "
        "uv run pytest -q -n auto --dist worksteal " + " ".join(selected) + "; rm -rf $H"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
