"""The discovery-to-scaffold bridge: ``dw adopt --from-report``.

Adoption discovery produces machine-parseable tables (Proposed Phase
Index, Proposed First Stories). This module parses them — with
line-numbered errors, refusing partial scaffolds — and turns them into
the same phase/story mutation plans the CLI uses, behind a
preview-then-apply flow. Nothing is written without ``--apply``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from .model import STORY_ID_RE, Project, die
from .parse import discover_projects, get_phase, get_project, split_table_row
from .paths import read_text, rel, roadmap_dir, slugify
from .mutations import apply_plan, plan_phase_create, plan_story_create
from .validate import check_project

PHASE_TABLE_HEADER = "| Phase | Title | Goal | Why now |"
STORY_TABLE_HEADER = "| ID | Title | Acceptance evidence | Notes |"


@dataclass
class AdoptionReport:
    phases: list[dict[str, object]] = field(default_factory=list)
    stories: list[dict[str, object]] = field(default_factory=list)
    slug: str | None = None
    prefix: str | None = None


def _table_rows(lines: list[str], heading: str, header: str) -> list[tuple[int, list[str]]]:
    """Rows (1-based line number, cells) of the table under `heading`."""
    rows: list[tuple[int, list[str]]] = []
    in_section = False
    in_table = False
    for i, line in enumerate(lines, start=1):
        if line.strip().startswith("## "):
            if in_section:
                break
            in_section = line.strip().lower() == heading.lower()
            continue
        if not in_section:
            continue
        stripped = line.strip()
        if stripped.startswith("| ") and stripped.replace(" ", "") == header.replace(" ", ""):
            in_table = True
            continue
        if not in_table:
            continue
        if stripped.startswith("|---"):
            continue
        if not stripped.startswith("|"):
            break
        rows.append((i, split_table_row(line)))
    return rows


def parse_adoption_report(text: str) -> AdoptionReport:
    lines = text.splitlines()
    report = AdoptionReport()

    m = re.search(r"\*\*Roadmap root:\*\*\s*`?pm/roadmap/([^/`\s]+)/?`?", text)
    if m:
        report.slug = m.group(1)

    phase_rows = _table_rows(lines, "## Proposed Phase Index", PHASE_TABLE_HEADER)
    if not phase_rows:
        die(
            "no 'Proposed Phase Index' table found (expected header "
            f"'{PHASE_TABLE_HEADER}'); regenerate the report with the current "
            "adoption-discovery prompt"
        )
    seen_numbers: set[int] = set()
    for lineno, cells in phase_rows:
        if len(cells) != 4:
            die(f"malformed phase row at line {lineno}: expected 4 columns (Phase | Title | Goal | Why now), got {len(cells)}")
        raw_number, title, goal = cells[0], cells[1], cells[2]
        if not raw_number.isdigit():
            die(f"malformed phase row at line {lineno}: phase must be a number, got {raw_number!r}")
        number = int(raw_number)
        if number in seen_numbers:
            die(f"malformed phase row at line {lineno}: duplicate phase number {number}")
        if not title.strip() or title.strip() in {"…", "..."}:
            die(f"malformed phase row at line {lineno}: empty phase title")
        seen_numbers.add(number)
        report.phases.append({"number": number, "title": title.strip(), "goal": goal.strip()})

    story_rows = _table_rows(lines, "## Proposed First Stories", STORY_TABLE_HEADER)
    for lineno, cells in story_rows:
        if len(cells) != 4:
            die(f"malformed story row at line {lineno}: expected 4 columns (ID | Title | Acceptance evidence | Notes), got {len(cells)}")
        story_id, title = cells[0].strip().strip("`"), cells[1].strip()
        id_match = STORY_ID_RE.match(story_id)
        if not id_match:
            die(f"malformed story row at line {lineno}: ID {story_id!r} does not match PREFIX-phase-number")
        phase_number = int(id_match.group(2))
        if phase_number not in seen_numbers:
            die(f"malformed story row at line {lineno}: story {story_id} references phase {phase_number}, which is not in the phase index")
        if not title or title in {"…", "..."}:
            die(f"malformed story row at line {lineno}: empty story title")
        if report.prefix is None:
            report.prefix = id_match.group(1)
        report.stories.append({"id": story_id, "phase": phase_number, "title": title})

    return report


MINIMAL_README = """# {name} - Roadmap

**Last updated:** {date}.
**Current phase:** [{first_phase_dir}](./{first_phase_dir}/current-phase-status.md).
**Status:** active.

## Vision

Seeded from the adoption discovery report; refine as the roadmap grows.

## Phase index

| Phase | Goal (one line) | Status | Folder |
|---|---|---|---|

## Project metadata

- **Slug:** `{slug}`
- **Story ID prefix:** {prefix}
"""


def _ensure_project(
    root: Path,
    slug: str,
    name: str | None,
    prefix: str | None,
    first_phase_dir: str,
    apply: bool,
) -> tuple[Project, list[str]]:
    from datetime import date

    notes: list[str] = []
    project_dir = roadmap_dir(root) / slug
    readme = project_dir / "README.md"
    if not readme.exists():
        notes.append(f"create {rel(readme, root)} (minimal project README)")
        if apply:
            project_dir.mkdir(parents=True, exist_ok=True)
            readme.write_text(
                MINIMAL_README.format(
                    name=name or slug.replace("-", " ").title(),
                    date=date.today().isoformat(),
                    slug=slug,
                    prefix=prefix or "PRJ",
                    first_phase_dir=first_phase_dir,
                ),
                encoding="utf-8",
            )
    if not apply and not readme.exists():
        # Preview against a project that does not exist yet.
        return Project(slug, project_dir, prefix or "PRJ"), notes
    for project in discover_projects(root):
        if project.slug == slug:
            return project, notes
    return get_project(root, slug), notes


def run_adoption(
    root: Path,
    report_path: Path,
    slug: str | None = None,
    name: str | None = None,
    prefix: str | None = None,
    apply: bool = False,
) -> dict[str, object]:
    if not report_path.is_file():
        die(f"adoption report not found: {report_path}")
    report = parse_adoption_report(read_text(report_path))
    slug = slug or report.slug
    if not slug:
        die("could not determine the project slug; pass --project or add the Roadmap root line to the report")
    slug = slugify(slug)
    prefix = prefix or report.prefix

    first = report.phases[0]
    first_phase_dir = f"phase-{first['number']}-{slugify(str(first['title']))}"
    project, notes = _ensure_project(root, slug, name, prefix, first_phase_dir, apply)
    planned: list[str] = list(notes)
    applied: list[str] = []

    if not apply:
        for phase in report.phases:
            phase_dir = f"phase-{phase['number']}-{slugify(str(phase['title']))}"
            planned.append(f"create pm-phase {phase_dir}/ (goal: {phase['goal']})")
        for story in report.stories:
            planned.append(f"create story {story['id']} — {story['title']}")
        return {"mode": "preview", "project": slug, "planned": planned, "issues": []}

    for phase in report.phases:
        plan = plan_phase_create(
            root, project, int(phase["number"]), str(phase["title"]), goal=str(phase["goal"]) or None, status="planned"
        )
        result = apply_plan(plan, validate_after=False)
        applied.extend(result["changed"])
    for story in report.stories:
        phase = get_phase(project, str(story["phase"]))
        plan = plan_story_create(root, project, phase, str(story["title"]), status="backlog")
        result = apply_plan(plan, validate_after=False)
        applied.extend(result["changed"])

    issues = check_project(get_project(root, slug), root)
    return {"mode": "applied", "project": slug, "planned": planned, "applied": applied, "issues": issues}
