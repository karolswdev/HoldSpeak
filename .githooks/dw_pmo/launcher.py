"""Global `dw` entry point for the packaged distribution.

Implements the distribution contract (docs/distribution.md): the
per-repo vendored rails are the only gating authority, so a globally
installed `dw` invoked inside an adopted repository execs
`.githooks/dw` unconditionally — even when the global version is
newer. Staleness is reported on stderr, never silently "fixed". The
global CLI acts in its own right only for the bootstrap verbs
(install / update / adopt-project / new-project / intake), which
operate on a target repo from outside its rails, and outside adopted
repositories (where it delegates to the packaged copy of bin/dw).
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

BOOTSTRAP_VERBS = {
    "install": "install.sh",
    "update": "update.sh",
    "adopt-project": "bootstrap/adopt-project.sh",
    "new-project": "bootstrap/new-project.sh",
    "intake": "bootstrap/session-intake.sh",
}

_VERSION_RE = re.compile(r'__version__\s*=\s*"([^"]+)"')


def payload_dir() -> Path | None:
    """Locate the pmo-roadmap payload for the running installation.

    Packaged layout: the payload ships as ``dw_pmo/_payload/``
    mirroring the source tree. Checkout layout: this file lives at
    ``pmo-roadmap/lib/dw_pmo/launcher.py`` and the payload is the
    ``pmo-roadmap`` directory itself — same relative turns either way.
    """
    here = Path(__file__).resolve().parent
    packaged = here / "_payload"
    if (packaged / "install.sh").is_file():
        return packaged
    checkout = here.parent.parent
    if (checkout / "install.sh").is_file() and (checkout / "hooks").is_dir():
        return checkout
    return None


def repo_dw(cwd: Path) -> Path | None:
    """The vendored CLI of the repository containing cwd, if any."""
    try:
        out = subprocess.check_output(
            ["git", "-C", str(cwd), "rev-parse", "--show-toplevel"],
            stdin=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    top = Path(out.strip())
    candidate = top / ".githooks" / "dw"
    return candidate if candidate.is_file() else None


def vendored_version(dw_path: Path) -> str | None:
    init = dw_path.parent / "dw_pmo" / "__init__.py"
    try:
        m = _VERSION_RE.search(init.read_text(encoding="utf-8"))
    except OSError:
        return None
    return m.group(1) if m else None


def _run(argv: list[str]) -> int:
    try:
        # stdin=None (inherit) is deliberate: this is the terminal
        # launcher handing the TTY to the real CLI, which may
        # prompt. Every other dw_pmo child gets DEVNULL (WLA-12-08).
        return subprocess.call(argv, stdin=None)
    except KeyboardInterrupt:
        return 130


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    from dw_pmo import __version__

    # Bootstrap verbs operate on a target repo from outside its rails;
    # they never defer.
    if args and args[0] in BOOTSTRAP_VERBS:
        payload = payload_dir()
        if payload is None:
            print("dw: cannot locate the packaged pmo-roadmap payload", file=sys.stderr)
            return 2
        script = payload / BOOTSTRAP_VERBS[args[0]]
        return _run(["bash", str(script), *args[1:]])

    # Defer-to-repo rule: inside an adopted repository the vendored
    # copy is the only truthful voice.
    vendored = repo_dw(Path.cwd())
    if vendored is not None:
        theirs = vendored_version(vendored)
        if theirs and theirs != __version__:
            print(
                f"dw: deferring to vendored rails v{theirs} (installed v{__version__}); "
                f"refresh with: dw update {vendored.parent.parent}",
                file=sys.stderr,
            )
        python = os.environ.get("PMO_GATE_PYTHON") or sys.executable
        return _run([python, str(vendored), *args])

    # Outside any adopted repo: delegate to the packaged bin/dw for
    # the roadmap commands (--version, help, etc.).
    payload = payload_dir()
    if payload is None:
        print("dw: cannot locate the packaged pmo-roadmap payload", file=sys.stderr)
        return 2
    return _run([sys.executable, str(payload / "bin" / "dw"), *args])


if __name__ == "__main__":
    sys.exit(main())
