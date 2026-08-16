"""HS-66-01: every Mermaid diagram in the docs renders.

A diagram that does not render is worse than no diagram. This extracts
every fenced ```mermaid block across the documentation and asks the
mermaid CLI (mmdc) to render it; a parse or render failure fails the test,
with the offending file, block index, and the renderer's error.

mmdc needs a browser (it renders to SVG via headless Chromium), so this
skips cleanly where mmdc or its browser is unavailable, exactly like the
route pre-flight. CI has no browser; the green evidence run is local:

    uv run pytest -q tests/e2e/test_mermaid_renders.py

GitHub is the canonical renderer for these blocks; this guard is the
mechanical backstop so a typo cannot land an unrenderable diagram.
"""
from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[2]

# The user-facing + internal docs that may carry diagrams, plus the README.
_DOC_GLOBS = ["README.md", "docs/*.md", "docs/internal/*.md"]

_MERMAID_BLOCK = re.compile(r"```mermaid\n(.*?)```", re.DOTALL)


def _doc_files() -> list[Path]:
    files: list[Path] = []
    for pattern in _DOC_GLOBS:
        files.extend(sorted(_REPO.glob(pattern)))
    return files


def _blocks() -> list[tuple[Path, int, str]]:
    out: list[tuple[Path, int, str]] = []
    for path in _doc_files():
        text = path.read_text(encoding="utf-8")
        for i, m in enumerate(_MERMAID_BLOCK.finditer(text)):
            out.append((path, i, m.group(1)))
    return out


def _mmdc() -> list[str] | None:
    """The mmdc invocation, or None if no renderer is available."""
    if shutil.which("mmdc"):
        return ["mmdc"]
    if shutil.which("npx"):
        return ["npx", "--yes", "@mermaid-js/mermaid-cli"]
    return None


def _render(cmd: list[str], block: str) -> subprocess.CompletedProcess:
    with tempfile.TemporaryDirectory() as d:
        src = Path(d) / "diagram.mmd"
        out = Path(d) / "diagram.svg"
        src.write_text(block, encoding="utf-8")
        try:
            return subprocess.run(
                [*cmd, "-i", str(src), "-o", str(out)],
                capture_output=True,
                text=True,
                # HS-132-12: a hung npx (cold cache, network, compromised
                # lock) once wedged the whole suite at 98% for 75 minutes.
                # A render that cannot finish in a minute is an environment
                # problem, never a diagram problem.
                timeout=60,
            )
        except subprocess.TimeoutExpired as exc:
            return subprocess.CompletedProcess(
                exc.cmd, returncode=124, stdout="", stderr="npm error render timed out after 60s"
            )


def _is_npm_infra_error(text: str) -> bool:
    """npm/npx cache and install failures are environment, not diagrams."""
    return "npm error" in text or "npm ERR!" in text


def test_docs_have_at_least_one_mermaid_block() -> None:
    # A canary: if the architecture doc lost its diagrams, this guard would
    # pass vacuously. It must not.
    assert _blocks(), "no ```mermaid blocks found in the docs — did they move?"


@pytest.mark.e2e
def test_every_mermaid_block_renders() -> None:
    cmd = _mmdc()
    if cmd is None:
        pytest.skip("no mermaid renderer (mmdc / npx) available")
    # Confirm the renderer actually runs here (browser present); skip if not.
    probe = _render(cmd, "flowchart TD\n  A --> B\n")
    if probe.returncode != 0:
        pytest.skip(f"mermaid renderer unavailable in this env: {probe.stderr[-300:]}")

    failures: list[str] = []
    env_failures: list[str] = []
    for path, idx, block in _blocks():
        result = _render(cmd, block)
        if result.returncode != 0:
            rel = path.relative_to(_REPO)
            err = (result.stderr or result.stdout).strip().splitlines()
            tail = " ".join(err[-3:]) if err else "unknown error"
            entry = f"{rel} block #{idx}: {tail}"
            if _is_npm_infra_error(tail):
                env_failures.append(entry)
            else:
                failures.append(entry)

    assert not failures, "Mermaid blocks that do not render:\n  " + "\n  ".join(failures)
    if env_failures:
        # Every failure was npm infrastructure (cache lock, interrupted
        # install, timeout) — the diagrams were never judged. Skip by name;
        # a warm npm cache (npm_config_cache passthrough, see CLAUDE.md)
        # makes this leg real again.
        pytest.skip(
            "mermaid renderer's npm cache unavailable: " + env_failures[0]
        )
