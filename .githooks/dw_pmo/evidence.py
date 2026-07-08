"""Evidence capture: verifiable command runs appended to evidence files.

``dw evidence capture <project> <phase> <story> -- <command>`` runs the
command and appends a deterministic block to the story's evidence file:

    ### Captured run — 2026-07-02T15:30:00Z

    - **Command:** `pmo-roadmap/tests/dw-core-tests.py`
    - **Cwd:** .
    - **Exit code:** 0
    - **Index-tree:** <git write-tree at capture time>

    ```text
    <combined stdout+stderr, byte-capped with an explicit marker>
    ```

Nonzero exit codes are recorded honestly (the CLI mirrors the command's
exit code so scripts notice). The capture touches ONLY the evidence
file: it creates the file when missing but never edits the phase table
or any other artifact — linking evidence is `dw story status`'s job.

The block heading's timestamp is the capture's identity: contract v2
can reference ``<evidence-path>#<timestamp>`` in its
``**Tests-ran capture:**`` fact to discharge the "Tests ran." rule
mechanically, and the gate verifies that block exists in the staged
evidence with exit code 0.
"""

from __future__ import annotations

import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from .model import Phase, Project, die
from .gitio import write_tree
from .parse import find_story
from .paths import read_text
from .render import render_evidence

TRUNCATION_MARKER = "[PMO_EVIDENCE_OUTPUT_TRUNCATED]"
DEFAULT_MAX_OUTPUT_BYTES = 20000

CAPTURE_HEADING_RE = re.compile(r"^### Captured run — (\S+)\s*$")
_EXIT_CODE_RE = re.compile(r"^- \*\*Exit code:\*\*\s*(-?\d+)\s*$")
_COMMAND_RE = re.compile(r"^- \*\*Command:\*\*\s*`(.*)`\s*$")


def render_capture_block(
    command_display: str,
    cwd_rel: str,
    exit_code: int,
    output: str,
    timestamp: str,
    index_tree: str,
    max_output_bytes: int = DEFAULT_MAX_OUTPUT_BYTES,
) -> str:
    raw = output.encode("utf-8")
    truncated = len(raw) > max_output_bytes
    if truncated:
        output = raw[:max_output_bytes].decode("utf-8", errors="replace")
    body = output.rstrip("\n")
    if truncated:
        body = body + "\n" + TRUNCATION_MARKER
    if not body:
        body = "(no output)"
    return (
        f"### Captured run — {timestamp}\n"
        "\n"
        f"- **Command:** `{command_display}`\n"
        f"- **Cwd:** {cwd_rel or '.'}\n"
        f"- **Exit code:** {exit_code}\n"
        f"- **Index-tree:** {index_tree}\n"
        "\n"
        "```text\n"
        f"{body}\n"
        "```\n"
    )


def evidence_path_for(phase: Phase, story_num: int) -> Path:
    """Prefer an existing evidence file (either padding); default padded."""
    padded = phase.path / f"evidence-story-{story_num:02d}.md"
    unpadded = phase.path / f"evidence-story-{story_num}.md"
    if not padded.exists() and unpadded.exists():
        return unpadded
    return padded


def parse_captured_runs(text: str) -> list[dict[str, object]]:
    """Return the captured-run blocks found in evidence text."""
    runs: list[dict[str, object]] = []
    lines = text.splitlines()
    for i, line in enumerate(lines):
        m = CAPTURE_HEADING_RE.match(line)
        if not m:
            continue
        run: dict[str, object] = {"timestamp": m.group(1), "exit_code": None, "command": ""}
        # Scan the whole header of this block (until the fenced output or
        # the next capture heading) — commands may span many lines.
        for follow in lines[i + 1 :]:
            if CAPTURE_HEADING_RE.match(follow) or follow.startswith("```"):
                break
            em = _EXIT_CODE_RE.match(follow)
            if em:
                run["exit_code"] = int(em.group(1))
            cm = _COMMAND_RE.match(follow)
            if cm:
                run["command"] = cm.group(1)
        runs.append(run)
    return runs


def find_captured_run(text: str, timestamp: str) -> dict[str, object] | None:
    for run in parse_captured_runs(text):
        if run["timestamp"] == timestamp:
            return run
    return None


def run_capture(
    root: Path,
    project: Project,
    phase: Phase,
    story_selector: str,
    argv: list[str],
    max_output_bytes: int = DEFAULT_MAX_OUTPUT_BYTES,
) -> tuple[int, Path, str]:
    """Run argv, append the captured block, return (exit, path, timestamp)."""
    if not argv:
        die("no command given; usage: dw evidence capture <project> <phase> <story> -- <command…>")
    row, story_num, _story_path = find_story(project, phase, story_selector)
    evidence_path = evidence_path_for(phase, story_num)

    if len(argv) == 1:
        popen_args: list[str] | str = ["sh", "-c", argv[0]]
        command_display = argv[0]
    else:
        popen_args = list(argv)
        command_display = " ".join(argv)

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    try:
        completed = subprocess.run(
            popen_args,
            cwd=str(root),
            # Never inherit stdin: under dw-mcp it is the JSON-RPC
            # pipe, and a stdin-reading child blocks forever on it
            # (and can eat protocol bytes). Captures are
            # non-interactive by design (WLA-12-08).
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        exit_code = completed.returncode
        output = completed.stdout or ""
    except OSError as exc:
        exit_code = 127
        output = f"(command could not be executed: {exc})"

    block = render_capture_block(
        command_display,
        ".",
        exit_code,
        output,
        timestamp,
        write_tree(root) or "unknown",
        max_output_bytes,
    )

    if evidence_path.exists():
        existing = read_text(evidence_path)
        content = existing.rstrip("\n") + "\n\n" + block
    else:
        content = render_evidence(row, story_num, block.rstrip("\n"))

    from .events import emit

    emit(
        root, "evidence_capture", project=project,
        story=row.story_id,
        detail={"exit_code": exit_code, "timestamp": timestamp},
    )

    # Deliberately single-file: capture never touches the phase table or
    # any artifact other than the evidence file itself.
    from .mutations import write_changes

    write_changes(root, {evidence_path: content})
    return exit_code, evidence_path, timestamp


def latest_passing_capture(text: str) -> dict[str, object] | None:
    for run in reversed(parse_captured_runs(text)):
        if run["exit_code"] == 0:
            return run
    return None
