"""The mission-control state feed (WLA-13-02).

`dw state --json` emits a versioned, schema-stable subset of
roadmap state for external consumers — the Desk conveyor, the
Telegram interface, the HoldSpeak packs. `dw context --compact`
remains the CLI-facing view and may change shape; this feed may
not, without a `FEED_SCHEMA` bump. The schema is pinned by tests
(`dw-core-tests.py`) that fail on unannounced shape changes, and
the contract lives in docs/mission-control.md §1.

One deliberate addition over the contract's first sketch, amended
there in the same commit: a per-project `phases` array. The Desk
conveyor renders phases as the belt, and the actuator pack
validates create-targets against phases that may hold no stories
yet — neither works from `current_phase` alone.
"""

from __future__ import annotations

import json
from pathlib import Path

from .api import next_story
from .gitio import write_tree
from .model import DONE_STATUSES, Project, normalize_status, row_is_retired
from .parse import (
    discover_phases,
    discover_projects,
    header_status,
    parse_current_phase_dirname,
    parse_story_rows,
    phase_story_files,
    story_id_from_header,
    story_num_from_file,
    story_title,
)
from .paths import read_text
from .validate import project_warnings

FEED_SCHEMA = 1


def _phase_title(phase) -> str:
    status_file = phase.path / "current-phase-status.md"
    if status_file.exists():
        for line in read_text(status_file).splitlines():
            if line.startswith("# "):
                return line[2:].strip()
    return phase.path.name


def _project_state(project: Project, root: Path) -> dict:
    phases_out: list[dict] = []
    stories_out: list[dict] = []
    current_phase: dict | None = None
    pointer_state: dict | None = None
    found_state: dict | None = None
    pointer_dir = parse_current_phase_dirname(project)
    found = next_story(project, root)
    for phase in discover_phases(project):
        rows = parse_story_rows(phase.path / "current-phase-status.md")
        done = 0
        total = 0
        covered: set[int] = set()
        for row in rows:
            if row_is_retired(row):
                # Retired history is not on the belt.
                num = story_num_from_file(row.story_file)
                if num is not None:
                    covered.add(num)
                continue
            story_num = story_num_from_file(row.story_file)
            if story_num is not None:
                covered.add(story_num)
            evidence = (
                phase.path / f"evidence-story-{story_num:02d}.md"
                if story_num
                else None
            )
            if normalize_status(row.status) in DONE_STATUSES:
                done += 1
            total += 1
            stories_out.append(
                {
                    "story_id": row.story_id,
                    "title": row.title,
                    "status": row.status,
                    "phase": phase.number,
                    "evidence_exists": bool(evidence and evidence.exists()),
                }
            )
        # Story files no row covers are still receipts (WLA-16-02):
        # derive their entries from the files themselves.
        for num, story_path in phase_story_files(phase.path).items():
            if num in covered:
                continue
            raw_status = header_status(story_path) or ""
            if normalize_status(raw_status) in DONE_STATUSES:
                done += 1
            total += 1
            stories_out.append(
                {
                    "story_id": story_id_from_header(story_path) or story_path.stem,
                    "title": story_title(story_path),
                    "status": raw_status,
                    "phase": phase.number,
                    "evidence_exists": (phase.path / f"evidence-story-{num:02d}.md").exists(),
                }
            )
        phase_state = {
            "number": phase.number,
            "title": _phase_title(phase),
            "status": (
                "closed"
                if (phase.path / "final-summary.md").exists()
                else "open"
            ),
            "stories_done": done,
            "stories_total": total,
        }
        phases_out.append(phase_state)
        if phase.path.name == pointer_dir:
            pointer_state = phase_state
        if found and found.get("phase") == phase.number:
            found_state = phase_state
    # The README pointer is the methodology's own current-phase receipt
    # (WLA-16-03): it wins when it resolves, even onto a closed phase —
    # that is the truth of the tree, not a guess.
    current_phase = pointer_state or found_state
    if current_phase is None and phases_out:
        open_phases = [p for p in phases_out if p["status"] == "open"]
        current_phase = (open_phases or phases_out)[-1]
    return {
        "slug": project.slug,
        "prefix": project.prefix,
        "current_phase": current_phase,
        "next_story": (
            {
                "story_id": found["story_id"],
                "title": found["title"],
                "status": found["status"],
            }
            if found
            else None
        ),
        "phases": phases_out,
        "stories": stories_out,
        "warnings": len(project_warnings(project, root)),
    }


def build_state_feed(root: Path) -> dict:
    return {
        "feed_schema": FEED_SCHEMA,
        "generated_at_tree": write_tree(root) or "unknown",
        "projects": [
            _project_state(project, root)
            for project in discover_projects(root)
        ],
    }


def render_state_feed(root: Path) -> str:
    return json.dumps(build_state_feed(root), indent=2, sort_keys=True)
