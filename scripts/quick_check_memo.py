"""The quick check's memo of green steps (2026-11-08, owner: "I still see a
ton of sequentiality"). Read and written only by scripts/quick_check.sh.

    python scripts/quick_check_memo.py plan <step>[=<selection-file>] ...
        one line per step: "<step> <key> <head of its last green with this
        key, or ->"; the key is the sha256 of the step's input set (and of its
        test selection, when one is named)
    python scripts/quick_check_memo.py record <step>=<key> ...
        records a GREEN of each step on the current head (a red never records)

The memo is .tmp/quick-check/green.json in the work tree: {step: {head, key,
at}}. A step whose key matches its last green is skipped.

An input set is the content of every file under the step's paths that git
sees (tracked and untracked, not ignored), as the work tree holds it now.
The sets are the brief's, widened where a step reads more (a narrow set would
skip a red):
  * build, vitest: web/ and the package manifests;
  * npm (the install before the build): web/package-lock.json and
    web/package.json;
  * web guards: also tests/fixtures/, docs/product-language.json and
    holdspeak/services/memory_grounding.py (the guards read them,
    scripts/quick_check.sh web_guards list);
  * desk sweep: web/, holdspeak/, tests/e2e/, tests/conftest.py and the
    manifests (the sweep runs the hub);
  * pytest, canon guards, repo guards, doc guards: the whole tree but pm/
    (the canon and repo guards scan web/ and docs/ too, for example
    tests/unit/test_interior_canon_guard.py and test_engines_name_guard.py).
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path


WEB = ["web/", "package.json", "package-lock.json"]
EVERYTHING = [".", ":(exclude)pm/", ":(exclude).tmp/"]
INPUTS: dict[str, list[str]] = {
    "build": WEB,
    # The install (2026-11-08): `npm ci` runs only when the lock file changed
    # since its last green, because lanes link the main checkout's
    # web/node_modules and a reinstall under a running lane breaks it.
    "npm": ["web/package-lock.json", "web/package.json"],
    "vitest": WEB,
    "web-guards": WEB + ["tests/fixtures/", "docs/product-language.json", "holdspeak/services/memory_grounding.py"],
    "sweep": WEB + ["holdspeak/", "tests/e2e/", "tests/conftest.py", "pyproject.toml", "uv.lock"],
    "pytest": EVERYTHING,
    "canon": EVERYTHING,
    "repo": EVERYTHING,
    "docguards": EVERYTHING,
}


def _git(*args: str) -> bytes:
    return subprocess.run(["git", *args], check=True, capture_output=True).stdout


def _z(out: bytes) -> list[str]:
    return [p for p in out.decode("utf-8", "surrogateescape").split("\0") if p]


_TREE: dict[tuple[str, ...], "hashlib._Hash"] = {}


def input_key(step: str, selection: str | None = None) -> str:
    spec = INPUTS[step]
    base = _TREE.get(tuple(spec))
    if base is None:
        base = _TREE[tuple(spec)] = _tree_digest(spec)
    digest = base.copy()
    if selection:
        digest.update(b"selection\0" + Path(selection).read_bytes())
    return digest.hexdigest()


def _tree_digest(spec: list[str]) -> "hashlib._Hash":
    blobs: dict[str, str] = {}
    # The index: mode, blob and path of every tracked file.
    for row in _z(_git("ls-files", "-s", "-z", "--", *spec)):
        meta, _, path = row.partition("\t")
        blobs[path] = meta.split()[1]
    # The work tree: modified and untracked files are hashed as they are now.
    loose = set(_z(_git("diff", "--name-only", "-z", "--", *spec)))
    loose |= set(_z(_git("ls-files", "-o", "--exclude-standard", "-z", "--", *spec)))
    present = sorted(p for p in loose if os.path.isfile(p) and not os.path.islink(p))
    for path in loose - set(present):
        blobs[path] = "link" if os.path.islink(path) else "gone"
    if present:
        out = subprocess.run(["git", "hash-object", "--stdin-paths"], input="\n".join(present).encode(),
                             check=True, capture_output=True).stdout.decode().split()
        blobs.update(zip(present, out))
    digest = hashlib.sha256()
    for path in sorted(blobs):
        digest.update(f"{path}\0{blobs[path]}\n".encode("utf-8", "surrogateescape"))
    return digest


def _memo_path() -> Path:
    return Path(".tmp/quick-check/green.json")


def _load() -> dict:
    try:
        return json.loads(_memo_path().read_text())
    except (OSError, ValueError):
        return {}


def main(argv: list[str]) -> int:
    if not argv or argv[0] not in ("plan", "record"):
        sys.stderr.write(__doc__ or "")
        return 2
    verb, args = argv[0], argv[1:]
    pairs = [arg.partition("=")[::2] for arg in args]
    if any(step not in INPUTS for step, _ in pairs):
        sys.stderr.write(f"quick_check_memo: the steps are {sorted(INPUTS)}\n")
        return 2
    memo = _load()
    if verb == "plan":
        for step, selection in pairs:
            key = input_key(step, selection or None)
            row = memo.get(step) or {}
            head = str(row.get("head", ""))[:9] if row.get("key") == key else "-"
            print(f"{step} {key} {head or '-'}")
        return 0
    head = _git("rev-parse", "HEAD").decode().strip()
    for step, key in pairs:
        memo[step] = {"head": head, "key": key, "at": time.strftime("%Y-%m-%dT%H:%M:%S")}
    path = _memo_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(f".{os.getpid()}.tmp")
    tmp.write_text(json.dumps(memo, indent=2, sort_keys=True) + "\n")
    tmp.replace(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
