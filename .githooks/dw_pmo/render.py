"""Template rendering and owned-region rewrites of roadmap Markdown.

Every function here is pure: it returns new file content and never
writes. Writing is the mutation layer's job.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

from .model import EVIDENCE_PLACEHOLDER, Phase, Project, StoryRow, die
from .parse import split_table_row
from .paths import read_text, template_dir


def render_phase_template(project: Project, number: int, title: str, goal: str) -> str:
    today = date.today().isoformat()
    templates = template_dir()
    if templates and (templates / "phase-status.md.tmpl").exists():
        text = read_text(templates / "phase-status.md.tmpl")
        replacements = {
            "{{DATE}}": today,
            "{{PHASE_N}}": str(number),
            "{{PHASE_TITLE}}": title,
            "{{PROJECT_PREFIX}}": project.prefix,
        }
        for old, new in replacements.items():
            text = text.replace(old, new)
        text = text.replace("{One short paragraph. What does this phase exist to achieve? Quote the\nroadmap or PMO plan. This section is **immutable** for the life of the\nphase.}", goal)
        lines = [
            line for line in text.splitlines()
            if "story-01-" not in line and f"{project.prefix}-{number}-01" not in line
        ]
        return "\n".join(lines).rstrip() + "\n"

    return f"""# Phase {number} - {title}

**Last updated:** {today}.

## Goal

{goal}

## Scope

- **In:** CLI-supported artifacts and workflow needed for this phase.
- **Out:** Related work not explicitly named by this phase.

## Exit criteria (evidence required)

- [ ] Exit criteria are defined before implementation begins.

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|

## Where we are

This phase has been scaffolded and is ready for story planning.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| Scope is underspecified | medium | Add concrete stories before implementation | A story cannot name testable acceptance criteria |

## Decisions made (this phase)

- {today} - Phase scaffolded with `dw phase create` - keeps roadmap structure consistent - CLI.

## Decisions deferred

- Detailed story breakdown - trigger before implementation begins - default is no code changes without stories.
"""


def render_story_template(project: Project, phase: Phase, number: int, title: str, status: str) -> str:
    story_id = f"{project.prefix}-{phase.number}-{number:02d}"
    templates = template_dir()
    if templates and (templates / "story.md.tmpl").exists():
        text = read_text(templates / "story.md.tmpl")
        for placeholder, value in {
            "{{STORY_ID}}": story_id,
            "{{STORY_TITLE}}": title,
            "{{PROJECT_SLUG}}": project.slug,
            "{{PHASE_N}}": str(phase.number),
            "{{STATUS}}": status,
        }.items():
            text = text.replace(placeholder, value)
        return text
    return f"""# {story_id} - {title}

- **Project:** {project.slug}
- **Phase:** {phase.number}
- **Status:** {status}
- **Depends on:** none
- **Unblocks:** (optional)
- **Owner:** unassigned

## Problem

Describe why this story exists and what it unlocks.

## Scope

- **In:** Concrete deliverables and file paths when known.
- **Out:** Related work this story does not cover.

## Acceptance criteria

- [ ] Define a verifiable acceptance criterion.

## Test plan

- **Unit:** n/a.
- **Integration:** n/a.
- **Manual / device:** n/a.

## Notes / open questions

Record unresolved decisions here before implementation starts.
"""


def render_evidence(row: StoryRow, story_num: int, body: str) -> str:
    today = date.today().isoformat()
    body = body.strip()
    if not body:
        body = f"- {EVIDENCE_PLACEHOLDER}"
    return f"""# Evidence - {row.story_id}

- **Story:** {row.story_id} - {row.title}
- **Status:** done
- **Date:** {today}

## Proof

{body}
"""


def render_final_summary(phase: Phase, summary_body: str) -> str:
    today = date.today().isoformat()
    return f"""# Phase {phase.number} Final Summary

**Status:** complete.
**Date:** {today}.

{summary_body}
"""


def evidence_link_for(story_num: int) -> str:
    return f"[evidence-story-{story_num:02d}](./evidence-story-{story_num:02d}.md)"


def replace_phase_index_content(readme: Path, new_row: str, phase_number: int) -> str:
    if not readme.exists():
        die(f"project README not found: {readme}")
    lines = read_text(readme).splitlines()
    header_idx = None
    for i, line in enumerate(lines):
        if line.startswith("| Phase | Goal (one line) | Status | Folder |"):
            header_idx = i
            break
    if header_idx is None:
        lines.extend(["", "## Phase index", "", "| Phase | Goal (one line) | Status | Folder |", "|---|---|---|---|", new_row])
        return "\n".join(lines) + "\n"

    start = header_idx + 2
    end = start
    rows: list[str] = []
    while end < len(lines) and lines[end].startswith("|"):
        cells = split_table_row(lines[end])
        if cells:
            if cells[0] == str(phase_number):
                die(f"phase {phase_number} already exists in {readme}")
            rows.append(lines[end])
        end += 1
    rows.append(new_row)

    def phase_key(row: str) -> int:
        cells = split_table_row(row)
        try:
            return int(cells[0])
        except (IndexError, ValueError):
            return 999999

    lines[header_idx + 2:end] = sorted(rows, key=phase_key)
    return "\n".join(lines) + "\n"


def replace_story_table_content(status_file: Path, new_row: str) -> str:
    lines = read_text(status_file).splitlines()
    header_idx = None
    for i, line in enumerate(lines):
        if line.startswith("| ID | Story | Status | Story file | Evidence |"):
            header_idx = i
            break
    if header_idx is None:
        die(f"story table not found: {status_file}")
    start = header_idx + 2
    end = start
    rows: list[str] = []
    while end < len(lines) and lines[end].startswith("|"):
        rows.append(lines[end])
        end += 1
    rows.append(new_row)
    lines[start:end] = rows
    return "\n".join(lines) + "\n"


def update_story_header_status_content(story_path: Path, status: str) -> str:
    if not story_path.exists():
        die(f"story file not found: {story_path}")
    lines = read_text(story_path).splitlines()
    changed = False
    for i, line in enumerate(lines):
        if line.startswith("- **Status:**"):
            lines[i] = f"- **Status:** {status}"
            changed = True
            break
    if not changed:
        die(f"story status header not found: {story_path}")
    return "\n".join(lines) + "\n"


def update_story_table_row_content(status_file: Path, story_id: str, status: str | None = None, evidence: str | None = None) -> str:
    lines = read_text(status_file).splitlines()
    changed = False
    for i, line in enumerate(lines):
        if not line.startswith("|"):
            continue
        cells = split_table_row(line)
        if len(cells) != 5 or cells[0] != story_id:
            continue
        if status is not None:
            cells[2] = status
        if evidence is not None:
            cells[4] = evidence
        lines[i] = f"| {cells[0]} | {cells[1]} | {cells[2]} | {cells[3]} | {cells[4]} |"
        changed = True
        break
    if not changed:
        die(f"story row not found in {status_file}: {story_id}")
    return "\n".join(lines) + "\n"


def update_phase_index_status_content(readme: Path, phase_number: int, status: str) -> str:
    lines = read_text(readme).splitlines()
    changed = False
    for i, line in enumerate(lines):
        cells = split_table_row(line)
        if len(cells) == 4 and cells[0] == str(phase_number):
            cells[2] = status
            lines[i] = f"| {cells[0]} | {cells[1]} | {cells[2]} | {cells[3]} |"
            changed = True
            break
    if not changed:
        die(f"phase {phase_number} row not found in {readme}")
    return "\n".join(lines) + "\n"
