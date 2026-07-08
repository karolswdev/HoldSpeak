"""dw doctor: the per-clone silent-failure detector.

Every load-bearing wiring step that historically failed silently —
`core.hooksPath` never set on a fresh clone, hooks missing next to the
CLI, the agent-docs block never pasted, python3 absent from PATH — is
checked and named here. Exit 0 means the rails are live.
"""

from __future__ import annotations

import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

from .agentdocs import agent_docs_status
from .gitio import run_git
from .model import DwError, Project
from .paths import roadmap_dir


@dataclass
class DoctorCheck:
    ok: bool
    name: str
    detail: str


def run_doctor(root: Path) -> list[DoctorCheck]:
    checks: list[DoctorCheck] = []

    python_path = shutil.which("python3")
    if python_path:
        version = ".".join(str(part) for part in sys.version_info[:3])
        checks.append(DoctorCheck(True, "python3", f"{python_path} ({version})"))
    else:
        checks.append(
            DoctorCheck(
                False,
                "python3",
                "python3 is not on PATH — the commit gate fails closed without it",
            )
        )

    hooks_path = (run_git(root, "config", "core.hooksPath") or "").strip()
    if hooks_path == ".githooks":
        checks.append(DoctorCheck(True, "core.hooksPath", ".githooks"))
    else:
        found = hooks_path or "(unset)"
        checks.append(
            DoctorCheck(
                False,
                "core.hooksPath",
                f"{found} — run `git config core.hooksPath .githooks` in this clone",
            )
        )

    for hook in ("pre-commit", "commit-msg", "post-commit"):
        path = root / ".githooks" / hook
        if path.is_file():
            checks.append(DoctorCheck(True, f"hook:{hook}", str(path.relative_to(root))))
        else:
            checks.append(
                DoctorCheck(
                    False,
                    f"hook:{hook}",
                    f".githooks/{hook} missing — re-run install.sh or update.sh",
                )
            )

    dw_path = root / ".githooks" / "dw"
    core_pkg = root / ".githooks" / "dw_pmo" / "__init__.py"
    if dw_path.is_file() and core_pkg.is_file():
        checks.append(DoctorCheck(True, "dw-cli", ".githooks/dw + .githooks/dw_pmo/"))
    else:
        checks.append(
            DoctorCheck(
                False,
                "dw-cli",
                "dw or its dw_pmo core is missing from .githooks/ — re-run install.sh or update.sh",
            )
        )

    docs_state, docs_path = agent_docs_status(root)
    if docs_state == "current":
        checks.append(DoctorCheck(True, "agent-docs", f"{docs_path.name} block is current"))  # type: ignore[union-attr]
    elif docs_state == "stale":
        checks.append(
            DoctorCheck(
                False,
                "agent-docs",
                f"{docs_path.name} block is stale — run `.githooks/dw agent-docs` (or update.sh)",  # type: ignore[union-attr]
            )
        )
    else:
        checks.append(
            DoctorCheck(
                False,
                "agent-docs",
                "no managed block in CLAUDE.md/AGENTS.md — run `.githooks/dw agent-docs`",
            )
        )

    try:
        rd = roadmap_dir(root)
        checks.append(DoctorCheck(True, "roadmap", str(rd.relative_to(root))))
    except DwError:
        checks.append(
            DoctorCheck(
                False,
                "roadmap",
                "no pm/roadmap tree found — bootstrap one (install.sh --project-slug … or dw phase create)",
            )
        )

    # Rider surfaces (WLA-12-07): which agent riders are wired here,
    # and do they match canon. Absent is a state, drifted is a finding.
    from .riderdocs import rider_report

    for ok, name, detail in rider_report(root):
        checks.append(DoctorCheck(ok, name, detail))

    return checks


def render_doctor(checks: list[DoctorCheck]) -> str:
    lines = []
    for check in checks:
        mark = "ok " if check.ok else "FAIL"
        lines.append(f"{mark}  {check.name}: {check.detail}")
    healthy = all(check.ok for check in checks)
    lines.append("")
    if healthy:
        lines.append("dw doctor: healthy. Canonical invocation: .githooks/dw <command>")
    else:
        failing = ", ".join(check.name for check in checks if not check.ok)
        lines.append(f"dw doctor: {failing} need attention (see lines above).")
    return "\n".join(lines) + "\n"
